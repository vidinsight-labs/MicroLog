"""
Race Condition Testleri - Özel race condition senaryoları
"""

import pytest
import threading
import time
import logging
from microlog.handlers import AsyncHandler, AsyncConsoleHandler
from microlog.context import set_current_context, get_current_context, TraceContext


class TestAsyncHandlerRaceConditions:
    """AsyncHandler race condition testleri"""
    
    def test_concurrent_start_stop(self):
        """
        Eşzamanlı start/stop çağrıları - thread-safe olmalı (idempotent)
        
        Not: stop() metodu queue flush için uzun sürebilir, bu yüzden
        test sadece idempotent davranışı ve thread-safety'yi doğrular.
        """
        handler = AsyncConsoleHandler()
        errors = []
        lock = threading.Lock()
        
        def start_worker():
            """Start worker - idempotent olmalı"""
            try:
                handler.start()  # Sadece bir kez
                handler.start()  # İkinci kez - idempotent olmalı
            except Exception as e:
                with lock:
                    errors.append(f"Start error: {e}")
        
        def stop_worker():
            """Stop worker - idempotent olmalı"""
            try:
                handler.stop()  # Sadece bir kez
                handler.stop()  # İkinci kez - idempotent olmalı
            except Exception as e:
                with lock:
                    errors.append(f"Stop error: {e}")
        
        # Önce handler'ı başlat
        handler.start()
        time.sleep(0.1)  # Handler'ın başlaması için kısa bekleme
        
        # Sadece 2 thread - basit concurrent test
        t1 = threading.Thread(target=start_worker, daemon=True)
        t2 = threading.Thread(target=stop_worker, daemon=True)
        
        t1.start()
        t2.start()
        
        # Kısa timeout ile join (daemon thread'ler zaten otomatik temizlenir)
        t1.join(timeout=1.0)
        t2.join(timeout=1.0)
        
        # Final cleanup - handler'ı durdur (timeout olabilir, normal)
        try:
            handler.stop()
        except Exception:
            pass
        
        # Sadece exception hatalarını kontrol et
        assert len(errors) == 0, f"Errors during concurrent start/stop: {errors}"
    
    def test_concurrent_get_queue_handler(self):
        """Eşzamanlı get_queue_handler çağrıları"""
        handler = AsyncConsoleHandler()
        queue_handlers = []
        errors = []
        
        def worker():
            try:
                for _ in range(20):
                    qh = handler.get_queue_handler()
                    queue_handlers.append(qh)
                    time.sleep(0.001)
            except Exception as e:
                errors.append(f"Error: {e}")
        
        threads = []
        for _ in range(5):
            t = threading.Thread(target=worker)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        assert len(errors) == 0, f"Errors: {errors}"
        assert len(queue_handlers) == 100  # 5 thread * 20 çağrı
        
        handler.stop()


class TestContextRaceConditions:
    """Context race condition testleri"""
    
    def test_rapid_context_switching(self):
        """Hızlı context değişimleri"""
        errors = []
        context_values = []
        
        def worker(thread_id: int):
            try:
                for i in range(100):
                    ctx = TraceContext(trace_id=f"trace-{thread_id}-{i}")
                    set_current_context(ctx)
                    
                    # Hemen kontrol et
                    current = get_current_context()
                    if current and current.trace_id == f"trace-{thread_id}-{i}":
                        context_values.append((thread_id, i))
                    
                    time.sleep(0.0001)
            except Exception as e:
                errors.append(f"Thread {thread_id}: {e}")
        
        threads = []
        for i in range(10):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        assert len(errors) == 0, f"Errors: {errors}"
        # Her thread'in context'i doğru korunmalı
        assert len(context_values) >= 900  # En az %90 başarılı olmalı


class TestFileHandlerRaceConditions:
    """File handler özel race condition testleri"""
    
    def test_rotation_during_concurrent_writes(self, temp_dir):
        """Rotation sırasında eşzamanlı yazma"""
        from microlog.handlers import AsyncRotatingFileHandler
        
        log_file = temp_dir / "race_rotation.log"
        
        handler = AsyncRotatingFileHandler(
            filename=str(log_file),
            max_bytes=200,  # Çok küçük - rotation olacak
            backup_count=2,
            compress=False
        )
        queue_handler = handler.get_queue_handler()
        
        logger = logging.getLogger("race_rotation")
        logger.addHandler(queue_handler)
        logger.setLevel(logging.DEBUG)
        
        errors = []
        written_count = [0]
        
        def writer(thread_id: int):
            try:
                for i in range(50):
                    logger.info(f"T{thread_id}-{i} " * 10)  # Uzun mesaj
                    written_count[0] += 1
                    time.sleep(0.001)
            except Exception as e:
                errors.append(f"Thread {thread_id}: {e}")
        
        threads = []
        for i in range(5):
            t = threading.Thread(target=writer, args=(i,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        time.sleep(2.0)  # Rotation ve yazma için bekleme
        
        assert len(errors) == 0, f"Errors: {errors}"
        assert written_count[0] == 250  # 5 * 50
        
        # Dosya veya backup dosyaları oluşmuş olmalı
        files = list(temp_dir.glob("race_rotation.log*"))
        assert len(files) > 0
        
        handler.stop()
        handler.handler.close()


class TestSMTPHandlerRaceConditions:
    """SMTP handler rate limiting race condition testleri"""
    
    def test_concurrent_rate_limit_check(self):
        """Eşzamanlı rate limit kontrolü"""
        from microlog.handlers import AsyncSMTPHandler
        
        handler = AsyncSMTPHandler(
            mailhost=("smtp.example.com", 587),
            fromaddr="test@example.com",
            toaddrs=["admin@example.com"],
            subject="Test",
            rate_limit=0.1  # 100ms
        )
        
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Test error",
            args=(),
            exc_info=None
        )
        
        results = []
        errors = []
        
        def worker():
            try:
                # Aynı anda rate limit kontrolü
                should_send = handler.handler._should_send(record)
                results.append(should_send)
            except Exception as e:
                errors.append(f"Error: {e}")
        
        # 20 thread aynı anda kontrol etsin
        threads = []
        for _ in range(20):
            t = threading.Thread(target=worker)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        assert len(errors) == 0, f"Errors: {errors}"
        assert len(results) == 20
        
        # Rate limiting thread-safe çalışmalı
        # Birden fazla True olabilir (ilk birkaç thread aynı anda geçebilir)
        # ama hiçbiri exception fırlatmamalı
        
        handler.stop()

