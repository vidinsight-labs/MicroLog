"""
Signal handling testleri.

Bu modül şunları test eder:
    - SIGTERM graceful shutdown
    - Signal handler içinde logging
    - Interrupt handling
    - Cleanup on signals

Author: MicroLog Team
Created: 2026-01-05
"""

import logging
import signal
import threading
import time
import os
from pathlib import Path

import pytest

from microlog import AsyncRotatingFileHandler


class TestSignalHandling:
    """Signal handling testleri"""
    
    def test_graceful_shutdown_on_sigterm(self, temp_log_file):
        """SIGTERM sinyali graceful shutdown tetiklemeli"""
        handler = AsyncRotatingFileHandler(filename=temp_log_file)
        queue_handler = handler.get_queue_handler()
        
        logger = logging.getLogger("test_sigterm")
        logger.addHandler(queue_handler)
        logger.setLevel(logging.INFO)
        
        # Logları yaz
        for i in range(50):
            logger.info(f"Message {i}")
        
        # SIGTERM handler simüle et
        def cleanup_handler(signum, frame):
            logger.info("SIGTERM received, shutting down...")
            handler.stop()
        
        # Handler'ı kaydet
        old_handler = signal.signal(signal.SIGTERM, cleanup_handler)
        
        try:
            # Kendimize SIGTERM gönder
            os.kill(os.getpid(), signal.SIGTERM)
            time.sleep(0.5)
            
            # Dosyayı kontrol et
            content = Path(temp_log_file).read_text()
            lines = [l for l in content.strip().split('\n') if l]
            
            # SIGTERM mesajı yazılmış olmalı
            assert any("SIGTERM received" in l for l in lines), "SIGTERM handler not executed"
            
            # Çoğu log yazılmış olmalı
            assert len(lines) >= 45, f"Only {len(lines)}/50 logs written"
            
        finally:
            # Eski handler'ı geri yükle
            signal.signal(signal.SIGTERM, old_handler)
    
    def test_logging_from_signal_handler_safe(self, temp_log_file):
        """Signal handler içinden logging güvenli olmalı"""
        handler = AsyncRotatingFileHandler(filename=temp_log_file)
        queue_handler = handler.get_queue_handler()
        
        logger = logging.getLogger("test_signal_logging")
        logger.addHandler(queue_handler)
        logger.setLevel(logging.INFO)
        
        signal_received = [False]
        
        def signal_handler(signum, frame):
            signal_received[0] = True
            # Signal handler içinden log - deadlock olmamalı
            try:
                logger.info("Signal handler logging")
            except Exception as e:
                pytest.fail(f"Logging from signal handler failed: {e}")
        
        old_handler = signal.signal(signal.SIGUSR1, signal_handler)
        
        try:
            # Normal log
            logger.info("Before signal")
            
            # Signal gönder
            os.kill(os.getpid(), signal.SIGUSR1)
            time.sleep(0.2)
            
            # Normal log devam
            logger.info("After signal")
            
            handler.stop()
            time.sleep(0.2)
            
            # Kontrol
            assert signal_received[0], "Signal not received"
            
            content = Path(temp_log_file).read_text()
            assert "Signal handler logging" in content
            assert "Before signal" in content
            assert "After signal" in content
            
        finally:
            signal.signal(signal.SIGUSR1, old_handler)
    
    def test_interrupt_during_logging(self, temp_log_file):
        """Logging sırasında interrupt güvenli olmalı"""
        handler = AsyncRotatingFileHandler(filename=temp_log_file)
        queue_handler = handler.get_queue_handler()
        
        logger = logging.getLogger("test_interrupt")
        logger.addHandler(queue_handler)
        logger.setLevel(logging.INFO)
        
        interrupted = [False]
        
        def interrupt_handler(signum, frame):
            interrupted[0] = True
            logger.info("Interrupted!")
        
        old_handler = signal.signal(signal.SIGINT, interrupt_handler)
        
        try:
            # Log yazarken interrupt
            for i in range(100):
                logger.info(f"Message {i}")
                if i == 50:
                    os.kill(os.getpid(), signal.SIGINT)
                time.sleep(0.01)
            
            handler.stop()
            time.sleep(0.2)
            
            assert interrupted[0], "Interrupt not handled"
            
            content = Path(temp_log_file).read_text()
            assert "Interrupted!" in content
            
        finally:
            signal.signal(signal.SIGINT, old_handler)


class TestCleanupOnExit:
    """Exit cleanup testleri"""
    
    def test_atexit_handler_flushes_logs(self, temp_log_file):
        """atexit handler logları flush etmeli"""
        handler = AsyncRotatingFileHandler(filename=temp_log_file)
        queue_handler = handler.get_queue_handler()
        
        logger = logging.getLogger("test_atexit")
        logger.addHandler(queue_handler)
        logger.setLevel(logging.INFO)
        
        # Loglar yaz
        for i in range(100):
            logger.info(f"Message {i}")
        
        # stop() çağır (atexit simülasyonu)
        handler.stop()
        time.sleep(0.5)
        
        # Tüm loglar yazılmış olmalı
        content = Path(temp_log_file).read_text()
        lines = [l for l in content.strip().split('\n') if l and 'Message' in l]
        
        assert len(lines) >= 95, f"atexit didn't flush all logs: {len(lines)}/100"
    
    def test_multiple_handlers_cleanup_on_exit(self, temp_dir):
        """Birden fazla handler temizlenmeli"""
        handlers = []
        
        for i in range(5):
            log_file = temp_dir / f"handler_{i}.log"
            handler = AsyncRotatingFileHandler(filename=str(log_file))
            queue_handler = handler.get_queue_handler()
            
            logger = logging.getLogger(f"test_multi_exit_{i}")
            logger.addHandler(queue_handler)
            logger.setLevel(logging.INFO)
            
            logger.info(f"Handler {i} message")
            handlers.append(handler)
        
        # Tüm handler'ları kapat (exit simülasyonu)
        for handler in handlers:
            handler.stop()
        
        time.sleep(0.5)
        
        # Tüm dosyalar oluşmuş olmalı
        files = list(temp_dir.glob("handler_*.log"))
        assert len(files) == 5, f"Only {len(files)}/5 handlers flushed"
        
        # Her dosyada log olmalı
        for i, f in enumerate(sorted(files)):
            content = f.read_text()
            assert f"Handler {i} message" in content


class TestThreadSafeSignals:
    """Thread-safe signal handling"""
    
    def test_signal_during_concurrent_logging(self, temp_log_file):
        """Concurrent logging sırasında signal güvenli olmalı"""
        handler = AsyncRotatingFileHandler(filename=temp_log_file)
        queue_handler = handler.get_queue_handler()
        
        logger = logging.getLogger("test_concurrent_signal")
        logger.addHandler(queue_handler)
        logger.setLevel(logging.INFO)
        
        stop_flag = threading.Event()
        signal_received = [False]
        errors = []
        
        def worker(thread_id: int):
            try:
                counter = 0
                while not stop_flag.is_set():
                    logger.info(f"T{thread_id}-{counter}")
                    counter += 1
                    time.sleep(0.01)
            except Exception as e:
                errors.append(f"T{thread_id}: {e}")
        
        def signal_handler(signum, frame):
            signal_received[0] = True
            logger.info("Signal during concurrent logging")
            stop_flag.set()
        
        old_handler = signal.signal(signal.SIGUSR1, signal_handler)
        
        try:
            # 5 worker başlat
            threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
            for t in threads:
                t.start()
            
            # 1 saniye sonra signal gönder
            time.sleep(1.0)
            os.kill(os.getpid(), signal.SIGUSR1)
            
            # Thread'leri bekle
            for t in threads:
                t.join(timeout=2.0)
            
            handler.stop()
            time.sleep(0.2)
            
            # Kontrol
            assert signal_received[0], "Signal not received"
            assert len(errors) == 0, f"Errors: {errors}"
            
            content = Path(temp_log_file).read_text()
            assert "Signal during concurrent logging" in content
            
        finally:
            signal.signal(signal.SIGUSR1, old_handler)
            stop_flag.set()


class TestSignalReentrancy:
    """Signal reentrancy testleri"""
    
    def test_nested_signal_handlers(self, temp_log_file):
        """Nested signal handler'lar güvenli olmalı"""
        handler = AsyncRotatingFileHandler(filename=temp_log_file)
        queue_handler = handler.get_queue_handler()
        
        logger = logging.getLogger("test_nested_signals")
        logger.addHandler(queue_handler)
        logger.setLevel(logging.INFO)
        
        signal1_count = [0]
        signal2_count = [0]
        
        def handler1(signum, frame):
            signal1_count[0] += 1
            logger.info(f"Handler1 called (count: {signal1_count[0]})")
            # İkinci signal gönder
            if signal1_count[0] == 1:
                os.kill(os.getpid(), signal.SIGUSR2)
        
        def handler2(signum, frame):
            signal2_count[0] += 1
            logger.info(f"Handler2 called (count: {signal2_count[0]})")
        
        old_handler1 = signal.signal(signal.SIGUSR1, handler1)
        old_handler2 = signal.signal(signal.SIGUSR2, handler2)
        
        try:
            # İlk signal
            os.kill(os.getpid(), signal.SIGUSR1)
            time.sleep(0.5)
            
            handler.stop()
            time.sleep(0.2)
            
            # Her iki handler da çağrılmış olmalı
            assert signal1_count[0] >= 1, "Handler1 not called"
            assert signal2_count[0] >= 1, "Handler2 not called"
            
            content = Path(temp_log_file).read_text()
            assert "Handler1 called" in content
            assert "Handler2 called" in content
            
        finally:
            signal.signal(signal.SIGUSR1, old_handler1)
            signal.signal(signal.SIGUSR2, old_handler2)
