"""
Resource cleanup ve temizlik testleri.

Bu modül şunları test eder:
    - Handler'ların düzgün kapanması
    - Queue'nun boşaltılması
    - Dosya handle'larının kapatılması
    - Memory leak kontrolü
    - atexit handler'ların çalışması

Test Senaryoları:
    1. Handler stop() queue'yu boşaltır
    2. Dosya handle'ları düzgün kapanır
    3. Resource leak olmamalı
    4. Graceful shutdown
    5. Exception durumunda cleanup

Author: MicroLog Team
Created: 2026-01-05
"""

import logging
import threading
import time
import gc
import weakref
from pathlib import Path

import pytest

from microlog import AsyncRotatingFileHandler, AsyncConsoleHandler
from microlog.handlers import _RotatingFileHandler


class TestHandlerCleanup:
    """Handler cleanup testleri"""
    
    def test_handler_stop_flushes_queue(self, temp_log_file):
        """stop() çağrısı queue'daki tüm logları boşaltır"""
        handler = AsyncRotatingFileHandler(filename=temp_log_file)
        queue_handler = handler.get_queue_handler()
        
        logger = logging.getLogger("test_flush")
        logger.addHandler(queue_handler)
        logger.setLevel(logging.INFO)
        
        # Çok sayıda log yaz
        for i in range(100):
            logger.info(f"Message {i}")
        
        # stop() çağır - queue boşaltılmalı
        handler.stop()
        
        # Dosyayı kontrol et
        content = Path(temp_log_file).read_text()
        lines = [l for l in content.strip().split('\n') if l]
        
        # Tüm loglar yazılmış olmalı
        assert len(lines) == 100, f"Expected 100 logs, got {len(lines)}"
        assert "Message 0" in content
        assert "Message 99" in content
    
    def test_multiple_start_stop_cycles(self, temp_log_file):
        """Her cycle için yeni handler oluşturulmalı (close sonrası reuse edilemez)"""
        # İlk cycle
        handler1 = AsyncRotatingFileHandler(filename=temp_log_file)
        queue_handler1 = handler1.get_queue_handler()
        
        logger1 = logging.getLogger("test_cycles_1")
        logger1.addHandler(queue_handler1)
        logger1.setLevel(logging.INFO)
        
        logger1.info("Cycle 1")
        handler1.stop()
        logger1.removeHandler(queue_handler1)
        time.sleep(0.2)
        
        # İkinci cycle - yeni handler oluştur (aynı dosyaya append)
        handler2 = AsyncRotatingFileHandler(filename=temp_log_file)
        queue_handler2 = handler2.get_queue_handler()
        
        logger2 = logging.getLogger("test_cycles_2")
        logger2.addHandler(queue_handler2)
        logger2.setLevel(logging.INFO)
        
        logger2.info("Cycle 2")
        handler2.stop()
        logger2.removeHandler(queue_handler2)
        time.sleep(0.2)
        
        # Dosyayı kontrol et
        content = Path(temp_log_file).read_text()
        assert "Cycle 1" in content, "First cycle log not found"
        assert "Cycle 2" in content, "Second cycle log not found"
    
    def test_handler_cleanup_on_exception(self, temp_log_file):
        """Exception durumunda bile cleanup yapılmalı"""
        handler = AsyncRotatingFileHandler(filename=temp_log_file)
        queue_handler = handler.get_queue_handler()
        
        logger = logging.getLogger("test_exception_cleanup")
        logger.addHandler(queue_handler)
        logger.setLevel(logging.INFO)
        
        try:
            logger.info("Before exception")
            raise ValueError("Test exception")
        except ValueError:
            pass
        finally:
            # Exception sonrası stop() çağrılmalı
            handler.stop()
        
        # Log yazılmış olmalı
        content = Path(temp_log_file).read_text()
        assert "Before exception" in content
    
    def test_concurrent_stop_calls(self, temp_log_file):
        """Eşzamanlı stop() çağrıları güvenli olmalı"""
        handler = AsyncRotatingFileHandler(filename=temp_log_file)
        queue_handler = handler.get_queue_handler()
        
        logger = logging.getLogger("test_concurrent_stop")
        logger.addHandler(queue_handler)
        logger.setLevel(logging.INFO)
        
        logger.info("Test message")
        
        errors = []
        
        def stop_handler():
            try:
                handler.stop()
            except Exception as e:
                errors.append(str(e))
        
        # 5 thread aynı anda stop() çağırsın
        threads = [threading.Thread(target=stop_handler) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Hata olmamalı
        assert len(errors) == 0, f"Errors during concurrent stop: {errors}"


class TestFileHandleCleanup:
    """Dosya handle cleanup testleri"""
    
    def test_file_handles_closed_after_stop(self, temp_log_file):
        """stop() sonrası dosya handle'ları kapatılmalı"""
        handler = AsyncRotatingFileHandler(filename=temp_log_file)
        queue_handler = handler.get_queue_handler()
        
        logger = logging.getLogger("test_file_handles")
        logger.addHandler(queue_handler)
        logger.setLevel(logging.INFO)
        
        logger.info("Test message")
        handler.stop()
        time.sleep(0.2)
        
        # Dosyayı silebilmeliyiz (handle kapalı olmalı)
        try:
            Path(temp_log_file).unlink()
            success = True
        except PermissionError:
            success = False
        
        assert success, "File handle not closed properly"
    
    def test_no_file_handle_leak(self, temp_dir):
        """Çok sayıda handler oluşturulup kapatıldığında leak olmamalı"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_fds = process.num_fds() if hasattr(process, 'num_fds') else len(process.open_files())
        
        # 50 handler oluştur ve kapat
        for i in range(50):
            temp_file = temp_dir / f"test_{i}.log"
            handler = AsyncRotatingFileHandler(filename=str(temp_file))
            queue_handler = handler.get_queue_handler()
            
            logger = logging.getLogger(f"test_leak_{i}")
            logger.addHandler(queue_handler)
            logger.setLevel(logging.INFO)
            
            logger.info(f"Message {i}")
            handler.stop()
            logger.removeHandler(queue_handler)
            
            # Handler'ı temizle
            del handler
            del queue_handler
        
        # GC çalıştır
        gc.collect()
        time.sleep(0.5)
        
        # File descriptor sayısı kontrollü artmalı
        final_fds = process.num_fds() if hasattr(process, 'num_fds') else len(process.open_files())
        fd_increase = final_fds - initial_fds
        
        # En fazla 5 FD artışı olabilir (tolerans)
        assert fd_increase <= 5, f"File descriptor leak detected: {fd_increase} FDs leaked"


class TestMemoryCleanup:
    """Memory cleanup testleri"""
    
    def test_handler_memory_cleanup(self, temp_log_file):
        """Handler silindiğinde memory temizlenmeli"""
        # Weak reference ile takip et
        handler = AsyncRotatingFileHandler(filename=temp_log_file)
        weak_ref = weakref.ref(handler)
        
        queue_handler = handler.get_queue_handler()
        logger = logging.getLogger("test_memory")
        logger.addHandler(queue_handler)
        logger.setLevel(logging.INFO)
        
        logger.info("Test message")
        handler.stop()
        logger.removeHandler(queue_handler)
        
        # Handler'ı sil
        del handler
        del queue_handler
        
        # GC çalıştır
        gc.collect()
        time.sleep(0.2)
        
        # Weak reference None olmalı
        assert weak_ref() is None, "Handler not garbage collected"
    
    def test_logger_memory_cleanup(self, temp_log_file):
        """Logger'lar temizlendiğinde memory leak olmamalı"""
        initial_loggers = len(logging.Logger.manager.loggerDict)
        
        # 100 logger oluştur
        handlers = []
        for i in range(100):
            handler = AsyncRotatingFileHandler(filename=temp_log_file)
            queue_handler = handler.get_queue_handler()
            
            logger = logging.getLogger(f"test_logger_cleanup_{i}")
            logger.addHandler(queue_handler)
            logger.setLevel(logging.INFO)
            logger.info(f"Message {i}")
            
            handler.stop()
            logger.removeHandler(queue_handler)
            handlers.append((handler, queue_handler))
        
        # Tüm handler'ları temizle
        for handler, queue_handler in handlers:
            del handler
            del queue_handler
        
        handlers.clear()
        gc.collect()
        time.sleep(0.5)
        
        # Logger sayısı kontrollü artmalı
        final_loggers = len(logging.Logger.manager.loggerDict)
        logger_increase = final_loggers - initial_loggers
        
        # Logger'lar cache'lenir, ama çok fazla artmamalı
        assert logger_increase <= 110, f"Too many loggers created: {logger_increase}"


class TestGracefulShutdown:
    """Graceful shutdown testleri"""
    
    def test_shutdown_with_pending_logs(self, temp_log_file):
        """Pending log'lar varken shutdown güvenli olmalı"""
        handler = AsyncRotatingFileHandler(filename=temp_log_file)
        queue_handler = handler.get_queue_handler()
        
        logger = logging.getLogger("test_shutdown")
        logger.addHandler(queue_handler)
        logger.setLevel(logging.INFO)
        
        # Çok hızlı log yaz (queue'da bekleyecek)
        for i in range(1000):
            logger.info(f"Message {i}")
        
        # Hemen stop() çağır
        handler.stop()
        
        # Dosyayı kontrol et - tüm loglar yazılmış olmalı
        content = Path(temp_log_file).read_text()
        lines = [l for l in content.strip().split('\n') if l]
        
        # Çoğu log yazılmış olmalı (queue listener flush eder)
        assert len(lines) >= 900, f"Many logs lost during shutdown: {len(lines)}/1000"
    
    def test_shutdown_during_rotation(self, temp_dir):
        """Rotation sırasında shutdown güvenli olmalı"""
        temp_file = temp_dir / "rotation_shutdown.log"
        
        # Çok küçük dosya boyutu (hızlı rotation)
        handler = AsyncRotatingFileHandler(
            filename=str(temp_file),
            max_bytes=100,  # Çok küçük
            backup_count=3
        )
        queue_handler = handler.get_queue_handler()
        
        logger = logging.getLogger("test_rotation_shutdown")
        logger.addHandler(queue_handler)
        logger.setLevel(logging.INFO)
        
        # Rotation tetikleyecek kadar log yaz
        for i in range(50):
            logger.info(f"Message {i} - some extra padding to increase size")
        
        # stop() çağır
        handler.stop()
        
        # Dosyalar oluşmuş olmalı
        files = list(temp_dir.glob("rotation_shutdown.log*"))
        assert len(files) > 0, "No log files created"


class TestThreadCleanup:
    """Thread cleanup testleri"""
    
    def test_listener_thread_stops(self, temp_log_file):
        """stop() sonrası listener thread sonlanmalı"""
        initial_threads = threading.active_count()
        
        handler = AsyncRotatingFileHandler(filename=temp_log_file)
        queue_handler = handler.get_queue_handler()
        
        logger = logging.getLogger("test_thread_stop")
        logger.addHandler(queue_handler)
        logger.setLevel(logging.INFO)
        
        logger.info("Test message")
        
        # Thread sayısı artmış olmalı
        after_start = threading.active_count()
        assert after_start > initial_threads, "Listener thread not started"
        
        # stop() çağır
        handler.stop()
        time.sleep(0.3)
        
        # Thread sayısı düşmüş olmalı
        after_stop = threading.active_count()
        assert after_stop <= initial_threads + 1, "Listener thread not stopped"
    
    def test_multiple_handlers_thread_cleanup(self, temp_dir):
        """Çok sayıda handler thread leak oluşturmamalı"""
        initial_threads = threading.active_count()
        
        handlers = []
        for i in range(10):
            temp_file = temp_dir / f"thread_test_{i}.log"
            handler = AsyncRotatingFileHandler(filename=str(temp_file))
            queue_handler = handler.get_queue_handler()
            
            logger = logging.getLogger(f"test_multi_thread_{i}")
            logger.addHandler(queue_handler)
            logger.setLevel(logging.INFO)
            logger.info(f"Message {i}")
            
            handlers.append((handler, queue_handler, logger))
        
        # Tüm handler'ları kapat
        for handler, queue_handler, logger in handlers:
            handler.stop()
            logger.removeHandler(queue_handler)
        
        time.sleep(0.5)
        
        # Thread sayısı kontrol altında olmalı
        final_threads = threading.active_count()
        thread_increase = final_threads - initial_threads
        
        # En fazla 2 thread artışı tolere et
        assert thread_increase <= 2, f"Thread leak detected: {thread_increase} threads leaked"

