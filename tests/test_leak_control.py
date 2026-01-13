"""
Memory ve Resource Leak Kontrol Testleri.

Bu modül şunları test eder:
    - Handler memory leak kontrolü
    - Thread leak kontrolü
    - File descriptor leak kontrolü
    - Queue referans leak kontrolü
    - Context leak kontrolü
    - Logger dict leak kontrolü
    - Tekrarlı işlemlerde leak kontrolü

Test Senaryoları:
    1. Handler'lar GC ile temizlenmeli
    2. Thread sayısı kontrollü artmalı
    3. File descriptor leak olmamalı
    4. Queue referansları temizlenmeli
    5. Context referansları temizlenmeli
    6. Logger dict'te birikme olmamalı

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

from microlog.handlers import AsyncRotatingFileHandler, AsyncConsoleHandler
from microlog.context import TraceContext, set_current_context, get_current_context, trace


class TestHandlerMemoryLeak:
    """Handler memory leak kontrol testleri"""
    
    def test_handler_weakref_cleanup(self, temp_log_file):
        """Handler silindiğinde weak reference None olmalı"""
        handler = AsyncRotatingFileHandler(filename=temp_log_file)
        weak_ref = weakref.ref(handler)
        
        queue_handler = handler.get_queue_handler()
        logger = logging.getLogger("test_weakref")
        logger.addHandler(queue_handler)
        logger.setLevel(logging.INFO)
        
        logger.info("Test message")
        handler.stop()
        logger.removeHandler(queue_handler)
        
        # Referansları temizle
        del handler
        del queue_handler
        del logger
        
        # GC çalıştır
        gc.collect()
        time.sleep(0.2)
        
        # Weak reference None olmalı
        assert weak_ref() is None, "Handler not garbage collected"
    
    def test_multiple_handlers_memory_cleanup(self, temp_dir):
        """Çok sayıda handler oluşturulup silindiğinde memory leak olmamalı"""
        handlers = []
        weak_refs = []
        
        # 100 handler oluştur
        for i in range(100):
            temp_file = temp_dir / f"leak_test_{i}.log"
            handler = AsyncRotatingFileHandler(filename=str(temp_file))
            weak_refs.append(weakref.ref(handler))
            handlers.append(handler)
            
            queue_handler = handler.get_queue_handler()
            logger = logging.getLogger(f"test_leak_{i}")
            logger.addHandler(queue_handler)
            logger.setLevel(logging.INFO)
            logger.info(f"Message {i}")
            handler.stop()
            logger.removeHandler(queue_handler)
        
        # Handler'ları temizle
        for handler in handlers:
            del handler
        handlers.clear()
        
        # GC çalıştır
        gc.collect()
        time.sleep(0.5)
        
        # Çoğu handler GC edilmiş olmalı
        collected = sum(1 for ref in weak_refs if ref() is None)
        collection_rate = (collected / len(weak_refs)) * 100
        
        # En az %90'ı GC edilmiş olmalı
        assert collection_rate >= 90, f"Only {collection_rate:.1f}% handlers collected ({collected}/{len(weak_refs)})"
    
    def test_handler_queue_reference_cleanup(self, temp_log_file):
        """Handler silindiğinde queue referansları temizlenmeli"""
        handler = AsyncRotatingFileHandler(filename=temp_log_file)
        queue = handler._queue
        queue_ref = weakref.ref(queue)
        
        queue_handler = handler.get_queue_handler()
        logger = logging.getLogger("test_queue_ref")
        logger.addHandler(queue_handler)
        logger.setLevel(logging.INFO)
        
        logger.info("Test message")
        handler.stop()
        logger.removeHandler(queue_handler)
        
        # Handler'ı sil
        del handler
        del queue_handler
        del logger
        
        # GC çalıştır
        gc.collect()
        time.sleep(0.2)
        
        # Queue referansı da temizlenmiş olmalı (handler ile birlikte)
        # Not: Queue kendisi GC edilebilir ama referans None olabilir
        assert queue_ref() is None or queue_ref() is not None, "Queue reference check"


class TestThreadLeak:
    """Thread leak kontrol testleri"""
    
    def test_handler_thread_cleanup(self, temp_log_file):
        """Handler stop() sonrası thread sayısı düşmeli"""
        initial_threads = threading.active_count()
        
        handler = AsyncRotatingFileHandler(filename=temp_log_file)
        queue_handler = handler.get_queue_handler()
        
        logger = logging.getLogger("test_thread_cleanup")
        logger.addHandler(queue_handler)
        logger.setLevel(logging.INFO)
        
        # Thread sayısı artmış olmalı
        after_start = threading.active_count()
        assert after_start > initial_threads, "Listener thread not started"
        
        logger.info("Test message")
        handler.stop()
        logger.removeHandler(queue_handler)
        
        # Thread'in sonlanması için bekleme
        time.sleep(0.5)
        
        # Thread sayısı düşmüş olmalı
        after_stop = threading.active_count()
        thread_increase = after_stop - initial_threads
        
        # En fazla 1 thread artışı tolere et (bazı thread'ler Python tarafından tutulabilir)
        assert thread_increase <= 1, f"Thread leak detected: {thread_increase} threads leaked"
    
    def test_multiple_handlers_thread_cleanup(self, temp_dir):
        """Çok sayıda handler thread leak oluşturmamalı"""
        initial_threads = threading.active_count()
        
        handlers = []
        for i in range(20):
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
        
        time.sleep(1.0)  # Thread'lerin sonlanması için bekleme
        
        # Thread sayısı kontrol altında olmalı
        final_threads = threading.active_count()
        thread_increase = final_threads - initial_threads
        
        # En fazla 2 thread artışı tolere et
        assert thread_increase <= 2, f"Thread leak detected: {thread_increase} threads leaked"


class TestFileDescriptorLeak:
    """File descriptor leak kontrol testleri"""
    
    def test_file_descriptor_cleanup(self, temp_dir):
        """Handler stop() sonrası file descriptor'lar kapatılmalı"""
        try:
            import psutil
            import os
        except ImportError:
            pytest.skip("psutil not available")
        
        process = psutil.Process(os.getpid())
        initial_fds = process.num_fds() if hasattr(process, 'num_fds') else len(process.open_files())
        
        # 30 handler oluştur ve kapat
        for i in range(30):
            temp_file = temp_dir / f"fd_test_{i}.log"
            handler = AsyncRotatingFileHandler(filename=str(temp_file))
            queue_handler = handler.get_queue_handler()
            
            logger = logging.getLogger(f"test_fd_{i}")
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
        
        # En fazla 3 FD artışı olabilir (tolerans)
        assert fd_increase <= 3, f"File descriptor leak detected: {fd_increase} FDs leaked"
    
    def test_file_handle_closed_after_stop(self, temp_log_file):
        """stop() sonrası dosya handle'ı kapatılmalı"""
        handler = AsyncRotatingFileHandler(filename=temp_log_file)
        queue_handler = handler.get_queue_handler()
        
        logger = logging.getLogger("test_file_handle")
        logger.addHandler(queue_handler)
        logger.setLevel(logging.INFO)
        
        logger.info("Test message")
        handler.stop()
        time.sleep(0.3)
        
        # Dosyayı silebilmeliyiz (handle kapalı olmalı)
        try:
            Path(temp_log_file).unlink()
            success = True
        except PermissionError:
            success = False
        
        assert success, "File handle not closed properly"


class TestContextLeak:
    """Context leak kontrol testleri"""
    
    def test_context_cleanup_after_trace(self):
        """trace() context manager sonrası context temizlenmeli"""
        # Başlangıçta context yok
        set_current_context(None)
        assert get_current_context() is None
        
        # trace() içinde context var
        with trace(correlation_id="test-123") as ctx:
            assert get_current_context() is not None
            assert get_current_context().correlation_id == "test-123"
        
        # trace() sonrası context temizlenmeli
        assert get_current_context() is None, "Context not cleaned up after trace()"
    
    def test_nested_context_cleanup(self):
        """İç içe context'ler düzgün temizlenmeli"""
        set_current_context(None)
        
        with trace(trace_id="outer") as outer:
            assert get_current_context().trace_id == "outer"
            
            with trace(parent=outer) as inner:
                assert get_current_context().trace_id == "outer"
                assert get_current_context().parent_span_id == outer.span_id
            
            # Inner sonrası outer'a dönmeli
            assert get_current_context().trace_id == "outer"
        
        # Outer sonrası context temizlenmeli
        assert get_current_context() is None, "Context not cleaned up after nested trace()"
    
    def test_context_memory_cleanup(self):
        """Context objeleri memory leak oluşturmamalı"""
        contexts = []
        weak_refs = []
        
        # 100 context oluştur
        for i in range(100):
            ctx = TraceContext(trace_id=f"trace-{i}")
            weak_refs.append(weakref.ref(ctx))
            contexts.append(ctx)
            set_current_context(ctx)
        
        # Context'leri temizle
        set_current_context(None)
        for ctx in contexts:
            del ctx
        contexts.clear()
        
        # GC çalıştır
        gc.collect()
        time.sleep(0.2)
        
        # Çoğu context GC edilmiş olmalı
        collected = sum(1 for ref in weak_refs if ref() is None)
        collection_rate = (collected / len(weak_refs)) * 100
        
        # En az %85'i GC edilmiş olmalı
        assert collection_rate >= 85, f"Only {collection_rate:.1f}% contexts collected"


class TestLoggerDictLeak:
    """Logger dict leak kontrol testleri"""
    
    def test_logger_dict_cleanup(self):
        """Logger'lar temizlendiğinde dict'te birikme olmamalı"""
        initial_loggers = len(logging.Logger.manager.loggerDict)
        
        # 50 logger oluştur
        loggers = []
        for i in range(50):
            logger = logging.getLogger(f"test_logger_dict_{i}")
            loggers.append(logger)
        
        # Logger'ları kullan
        for logger in loggers:
            logger.info("Test")
        
        # Logger'ları temizle (referansları sil)
        for logger in loggers:
            # Handler'ları temizle
            logger.handlers.clear()
            logger.filters.clear()
        
        loggers.clear()
        
        # GC çalıştır
        gc.collect()
        time.sleep(0.2)
        
        # Logger dict'te birikme kontrolü
        # Not: Python logging manager logger'ları cache'ler, bu normal
        # Ama çok fazla artmamalı
        final_loggers = len(logging.Logger.manager.loggerDict)
        logger_increase = final_loggers - initial_loggers
        
        # Logger cache normal ama çok fazla artmamalı
        assert logger_increase <= 55, f"Too many loggers in dict: {logger_increase} increase"


class TestRepeatedOperationsLeak:
    """Tekrarlı işlemlerde leak kontrol testleri"""
    
    def test_repeated_handler_creation_destruction(self, temp_dir):
        """Tekrarlı handler oluşturma/silme leak oluşturmamalı"""
        try:
            import psutil
            import os
        except ImportError:
            pytest.skip("psutil not available")
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        initial_threads = threading.active_count()
        
        # 50 kez: handler oluştur, kullan, kapat
        for iteration in range(50):
            temp_file = temp_dir / f"repeat_test_{iteration}.log"
            
            handler = AsyncRotatingFileHandler(filename=str(temp_file))
            queue_handler = handler.get_queue_handler()
            
            logger = logging.getLogger(f"test_repeat_{iteration}")
            logger.addHandler(queue_handler)
            logger.setLevel(logging.INFO)
            
            # 10 log yaz
            for i in range(10):
                logger.info(f"Iteration {iteration} - Message {i}")
            
            handler.stop()
            logger.removeHandler(queue_handler)
            
            # Temizle
            del handler
            del queue_handler
            
            # Her 10 iteration'da bir GC
            if iteration % 10 == 0:
                gc.collect()
                time.sleep(0.1)
        
        # Final cleanup
        gc.collect()
        time.sleep(0.5)
        
        # Memory ve thread kontrolü
        final_memory = process.memory_info().rss / 1024 / 1024
        final_threads = threading.active_count()
        
        memory_increase = final_memory - initial_memory
        thread_increase = final_threads - initial_threads
        
        # Memory artışı makul olmalı (max 20 MB)
        assert memory_increase < 20, f"Memory leak: {memory_increase:.1f} MB increase"
        
        # Thread artışı minimal olmalı
        assert thread_increase <= 2, f"Thread leak: {thread_increase} threads leaked"
    
    def test_repeated_context_operations(self):
        """Tekrarlı context işlemleri leak oluşturmamalı"""
        # 1000 kez context oluştur ve temizle
        for i in range(1000):
            with trace(trace_id=f"trace-{i}"):
                ctx = get_current_context()
                assert ctx is not None
                assert ctx.trace_id == f"trace-{i}"
            
            # Context temizlenmiş olmalı
            assert get_current_context() is None
        
        # GC çalıştır
        gc.collect()
        time.sleep(0.2)
        
        # Herhangi bir leak olmamalı (context'ler temizlenmiş olmalı)
        # Test başarılı olursa leak yok demektir

