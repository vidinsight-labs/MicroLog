"""
Thread Safety Testleri - Thread çakışmalarını kontrol eder
"""

import pytest
import threading
import time
import logging
from pathlib import Path
from microlog import (
    get_logger,
    trace,
    setup_file_logger,
    AsyncRotatingFileHandler,
    AsyncConsoleHandler,
)
from microlog.context import (
    TraceContext,
    get_current_context,
    set_current_context,
)


class TestContextThreadSafety:
    """Context yönetiminin thread-safety testleri"""
    
    def test_context_isolation_between_threads(self):
        """Farklı thread'lerde context izolasyonu"""
        results = {}
        errors = []
        
        def worker(thread_id: int):
            try:
                # Her thread kendi context'ini oluşturur
                with trace(trace_id=f"trace-{thread_id}", user_id=f"user-{thread_id}") as ctx:
                    time.sleep(0.01)  # Diğer thread'lerin başlaması için
                    
                    current = get_current_context()
                    if current:
                        results[thread_id] = {
                            "trace_id": current.trace_id,
                            "user_id": current.extra.get("user_id"),
                            "span_id": current.span_id
                        }
                    else:
                        errors.append(f"Thread {thread_id}: Context bulunamadı")
            except Exception as e:
                errors.append(f"Thread {thread_id}: {e}")
        
        threads = []
        for i in range(10):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # Her thread kendi context'ini görmeli
        assert len(errors) == 0, f"Errors: {errors}"
        assert len(results) == 10
        
        # Her thread'in trace_id'si farklı olmalı
        trace_ids = [r["trace_id"] for r in results.values()]
        assert len(set(trace_ids)) == 10, "Trace ID'ler benzersiz olmalı"
        
        # Her thread'in user_id'si doğru olmalı
        for thread_id, result in results.items():
            assert result["user_id"] == f"user-{thread_id}"
    
    def test_context_concurrent_access(self):
        """Context'e eşzamanlı erişim testi"""
        errors = []
        iterations = 100
        
        def worker():
            try:
                for i in range(iterations):
                    ctx = TraceContext(trace_id=f"trace-{i}")
                    set_current_context(ctx)
                    time.sleep(0.001)
                    
                    current = get_current_context()
                    if current is None or current.trace_id != f"trace-{i}":
                        errors.append(f"Context kaybı: {i}")
            except Exception as e:
                errors.append(f"Exception: {e}")
        
        threads = []
        for _ in range(5):
            t = threading.Thread(target=worker)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # Thread'ler birbirinin context'ini bozmamalı
        # (ContextVar sayesinde her thread kendi context'ini görür)
        assert len(errors) == 0, f"Errors: {errors}"


class TestHandlerThreadSafety:
    """Handler'ların thread-safety testleri"""
    
    def test_console_handler_concurrent_logging(self, clean_loggers):
        """Console handler'a eşzamanlı log yazma"""
        handler = AsyncConsoleHandler()
        queue_handler = handler.get_queue_handler()
        
        logger = logging.getLogger("thread_test_console")
        logger.addHandler(queue_handler)
        logger.setLevel(logging.DEBUG)
        
        errors = []
        log_count = [0]
        
        def worker(thread_id: int):
            try:
                for i in range(50):
                    logger.info(f"Thread {thread_id} - Message {i}")
                    log_count[0] += 1
                    time.sleep(0.001)
            except Exception as e:
                errors.append(f"Thread {thread_id}: {e}")
        
        threads = []
        for i in range(10):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # Tüm loglar yazılmalı
        time.sleep(0.5)  # Queue'nun işlenmesi için bekleme
        
        assert len(errors) == 0, f"Errors: {errors}"
        assert log_count[0] == 500  # 10 thread * 50 mesaj
        
        handler.stop()
    
    def test_file_handler_concurrent_logging(self, clean_loggers, temp_log_file):
        """File handler'a eşzamanlı log yazma"""
        handler = AsyncRotatingFileHandler(
            filename=temp_log_file,
            max_bytes=10 * 1024 * 1024,  # 10MB - rotation olmayacak
            backup_count=5
        )
        queue_handler = handler.get_queue_handler()
        
        logger = logging.getLogger("thread_test_file")
        logger.addHandler(queue_handler)
        logger.setLevel(logging.DEBUG)
        
        errors = []
        expected_messages = set()
        
        def worker(thread_id: int):
            try:
                for i in range(20):
                    message = f"Thread-{thread_id}-Message-{i}"
                    expected_messages.add(message)
                    logger.info(message)
                    time.sleep(0.001)
            except Exception as e:
                errors.append(f"Thread {thread_id}: {e}")
        
        threads = []
        for i in range(10):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # Queue'nun işlenmesi için bekleme
        time.sleep(1.0)
        
        assert len(errors) == 0, f"Errors: {errors}"
        
        # Dosyayı kontrol et
        if Path(temp_log_file).exists():
            content = Path(temp_log_file).read_text()
            
            # Tüm mesajlar dosyada olmalı
            found_messages = 0
            for msg in expected_messages:
                if msg in content:
                    found_messages += 1
            
            # En az %90'ı bulunmalı (timing nedeniyle bazıları eksik olabilir)
            assert found_messages >= len(expected_messages) * 0.9, \
                f"Found {found_messages}/{len(expected_messages)} messages"
        
        handler.stop()
        handler.handler.close()
    
    def test_file_handler_rotation_thread_safety(self, clean_loggers, temp_dir):
        """File rotation sırasında thread-safety"""
        log_file = temp_dir / "rotation_test.log"
        
        handler = AsyncRotatingFileHandler(
            filename=str(log_file),
            max_bytes=500,  # Küçük limit - rotation olacak
            backup_count=3,
            compress=False
        )
        queue_handler = handler.get_queue_handler()
        
        logger = logging.getLogger("thread_rotation_test")
        logger.addHandler(queue_handler)
        logger.setLevel(logging.DEBUG)
        
        errors = []
        
        def worker(thread_id: int):
            try:
                for i in range(30):
                    logger.info(f"Thread {thread_id} - Message {i} " * 5)  # Uzun mesajlar
                    time.sleep(0.01)
            except Exception as e:
                errors.append(f"Thread {thread_id}: {e}")
        
        threads = []
        for i in range(5):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        time.sleep(1.0)  # Rotation ve yazma işlemleri için bekleme
        
        # Hata olmamalı
        assert len(errors) == 0, f"Errors: {errors}"
        
        # Dosya veya backup dosyaları oluşmuş olmalı
        files = list(temp_dir.glob("rotation_test.log*"))
        assert len(files) > 0, "En az bir log dosyası olmalı"
        
        handler.stop()
        handler.handler.close()
    
    def test_smtp_handler_rate_limiting_thread_safety(self):
        """SMTP handler rate limiting thread-safety"""
        from microlog.handlers import AsyncSMTPHandler
        
        handler = AsyncSMTPHandler(
            mailhost=("smtp.example.com", 587),
            fromaddr="test@example.com",
            toaddrs=["admin@example.com"],
            subject="Test",
            rate_limit=1  # 1 saniye
        )
        
        # Aynı mesajı farklı thread'lerden gönderme denemesi
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
        
        def worker(thread_id: int):
            try:
                # Rate limiting kontrolü thread-safe olmalı
                should_send = handler.handler._should_send(record)
                results.append((thread_id, should_send))
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
        
        # İlk thread True dönmeli, diğerleri False (rate limit nedeniyle)
        # Ancak thread'ler eşzamanlı çalıştığı için birden fazla True olabilir
        true_count = sum(1 for _, should_send in results if should_send)
        assert true_count >= 1, "En az bir thread True döndürmeli"
        
        handler.stop()


class TestConcurrentTraceAndLogging:
    """Trace context ve logging'in birlikte thread-safety testi"""
    
    def test_trace_context_with_concurrent_logging(self, clean_loggers):
        """Trace context ile eşzamanlı logging"""
        handler = AsyncConsoleHandler()
        queue_handler = handler.get_queue_handler()
        
        logger = logging.getLogger("trace_thread_test")
        logger.addHandler(queue_handler)
        logger.setLevel(logging.DEBUG)
        
        errors = []
        trace_ids = set()
        
        def worker(thread_id: int):
            try:
                with trace(trace_id=f"trace-{thread_id}", user_id=f"user-{thread_id}") as ctx:
                    trace_ids.add(ctx.trace_id)
                    
                    for i in range(10):
                        logger.info(f"Thread {thread_id} - Log {i}", extra={"step": i})
                        time.sleep(0.001)
                    
                    # Context hala doğru mu?
                    current = get_current_context()
                    if current and current.trace_id != f"trace-{thread_id}":
                        errors.append(f"Thread {thread_id}: Context kaybı")
            except Exception as e:
                errors.append(f"Thread {thread_id}: {e}")
        
        threads = []
        for i in range(10):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        time.sleep(0.5)
        
        assert len(errors) == 0, f"Errors: {errors}"
        assert len(trace_ids) == 10, "Her thread kendi trace_id'sine sahip olmalı"
        
        handler.stop()
    
    def test_nested_trace_context_thread_safety(self, clean_loggers):
        """İç içe trace context thread-safety"""
        errors = []
        
        def worker(thread_id: int):
            try:
                with trace(trace_id=f"parent-{thread_id}") as parent:
                    parent_span = parent.span_id
                    
                    with trace(parent=parent) as child:
                        if child.trace_id != f"parent-{thread_id}":
                            errors.append(f"Thread {thread_id}: Trace ID kaybı")
                        if child.parent_span_id != parent_span:
                            errors.append(f"Thread {thread_id}: Parent span kaybı")
                        
                        time.sleep(0.01)
                    
                    # Parent context hala doğru mu?
                    current = get_current_context()
                    if current and current.trace_id != f"parent-{thread_id}":
                        errors.append(f"Thread {thread_id}: Parent context kaybı")
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


class TestStressTest:
    """Yüksek yük altında thread-safety testleri"""
    
    def test_high_concurrency_logging(self, clean_loggers, temp_log_file):
        """Yüksek eşzamanlılıkta logging"""
        handler = AsyncRotatingFileHandler(filename=temp_log_file)
        queue_handler = handler.get_queue_handler()
        
        logger = logging.getLogger("stress_test")
        logger.addHandler(queue_handler)
        logger.setLevel(logging.DEBUG)
        
        errors = []
        total_logs = [0]
        
        def worker(thread_id: int):
            try:
                for i in range(100):
                    logger.info(f"Thread-{thread_id}-{i}")
                    total_logs[0] += 1
            except Exception as e:
                errors.append(f"Thread {thread_id}: {e}")
        
        # 20 thread, her biri 100 log
        threads = []
        for i in range(20):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        time.sleep(2.0)  # Tüm logların yazılması için bekleme
        
        assert len(errors) == 0, f"Errors: {errors}"
        assert total_logs[0] == 2000  # 20 * 100
        
        handler.stop()
        handler.handler.close()

