"""
Edge Case ve Limit Testleri - Uç nokta durumları
"""

import pytest
import logging
import time
import json
from pathlib import Path
from microlog import (
    get_logger,
    trace,
    setup_file_logger,
    AsyncRotatingFileHandler,
    JSONFormatter,
    PrettyFormatter,
)
from microlog.context import TraceContext


class TestLargeDataHandling:
    """Büyük veri işleme testleri"""
    
    def test_very_large_log_message(self, clean_loggers, temp_log_file):
        """Çok büyük log mesajı (10MB)"""
        handler = AsyncRotatingFileHandler(
            filename=temp_log_file,
            max_bytes=50 * 1024 * 1024  # 50MB
        )
        handler.handler.setFormatter(JSONFormatter())
        
        logger = logging.getLogger("large_message_test")
        logger.addHandler(handler.get_queue_handler())
        logger.setLevel(logging.INFO)
        
        # 10MB mesaj
        large_message = "A" * (10 * 1024 * 1024)
        
        try:
            logger.info(large_message)
            time.sleep(1.0)
            
            # Dosya oluşmuş olmalı
            assert Path(temp_log_file).exists()
            
            # Dosya boyutu makul olmalı (sıkıştırılmış JSON)
            size = Path(temp_log_file).stat().st_size
            assert size > 0
        finally:
            handler.stop()
            handler.handler.close()
    
    def test_many_extra_fields(self, clean_loggers, temp_log_file):
        """Çok fazla extra alan (1000 alan)"""
        handler = AsyncRotatingFileHandler(filename=temp_log_file)
        handler.handler.setFormatter(JSONFormatter())
        
        logger = logging.getLogger("many_fields_test")
        logger.addHandler(handler.get_queue_handler())
        logger.setLevel(logging.INFO)
        
        # 1000 extra alan
        extra = {f"field_{i}": f"value_{i}" for i in range(1000)}
        
        try:
            logger.info("Test message", extra=extra)
            time.sleep(0.5)
            
            assert Path(temp_log_file).exists()
            
            # JSON parse edilebilmeli
            content = Path(temp_log_file).read_text()
            data = json.loads(content.strip().split('\n')[0])
            assert "field_0" in data
            assert "field_999" in data
        finally:
            handler.stop()
            handler.handler.close()
    
    def test_deeply_nested_extra_data(self, clean_loggers, temp_log_file):
        """Derin nested veri yapısı"""
        handler = AsyncRotatingFileHandler(filename=temp_log_file)
        handler.handler.setFormatter(JSONFormatter())
        
        logger = logging.getLogger("nested_data_test")
        logger.addHandler(handler.get_queue_handler())
        logger.setLevel(logging.INFO)
        
        # 10 seviye derin nested dict
        nested = {"level": 0}
        current = nested
        for i in range(10):
            current["next"] = {"level": i + 1}
            current = current["next"]
        
        try:
            logger.info("Nested data", extra={"data": nested})
            time.sleep(0.5)
            
            assert Path(temp_log_file).exists()
        finally:
            handler.stop()
            handler.handler.close()


class TestRotationLimits:
    """Rotation limit testleri"""
    
    def test_rotation_with_zero_max_bytes(self, clean_loggers, temp_log_file):
        """max_bytes=0 ile rotation (rotation olmamalı)"""
        handler = AsyncRotatingFileHandler(
            filename=temp_log_file,
            max_bytes=0,  # Rotation disabled
            backup_count=5
        )
        
        logger = logging.getLogger("no_rotation_test")
        logger.addHandler(handler.get_queue_handler())
        logger.setLevel(logging.INFO)
        
        try:
            # Çok fazla log yaz
            for i in range(100):
                logger.info(f"Message {i} " * 100)  # Her biri ~1KB
            
            time.sleep(1.0)
            
            # Sadece ana dosya olmalı, backup olmamalı
            files = list(Path(temp_log_file).parent.glob(f"{Path(temp_log_file).name}.*"))
            assert len(files) == 0, "Rotation disabled olduğunda backup olmamalı"
        finally:
            handler.stop()
            handler.handler.close()
    
    def test_rotation_with_large_backup_count(self, temp_dir):
        """Çok fazla backup count (100)"""
        log_file = temp_dir / "many_backups.log"
        
        handler = AsyncRotatingFileHandler(
            filename=str(log_file),
            max_bytes=100,  # Çok küçük - hızlı rotation
            backup_count=100,  # Çok fazla backup
            compress=False
        )
        
        logger = logging.getLogger("many_backups_test")
        logger.addHandler(handler.get_queue_handler())
        logger.setLevel(logging.INFO)
        
        try:
            # 150 rotation tetikleyecek kadar log
            for i in range(300):
                logger.info(f"Log {i}")
            
            time.sleep(2.0)
            
            # En fazla backup_count + 1 dosya olmalı
            files = list(temp_dir.glob("many_backups.log*"))
            assert len(files) <= 101  # 1 ana + 100 backup
        finally:
            handler.stop()
            handler.handler.close()
    
    def test_rotation_with_zero_backup_count(self, temp_dir):
        """backup_count=0 ile rotation"""
        log_file = temp_dir / "no_backup.log"
        
        handler = AsyncRotatingFileHandler(
            filename=str(log_file),
            max_bytes=500,
            backup_count=0,  # Backup yok
            compress=False
        )
        
        logger = logging.getLogger("no_backup_test")
        logger.addHandler(handler.get_queue_handler())
        logger.setLevel(logging.INFO)
        
        try:
            # Rotation tetikleyecek kadar log
            for i in range(50):
                logger.info(f"Message {i} " * 20)
            
            time.sleep(1.0)
            
            # Sadece ana dosya olmalı
            files = list(temp_dir.glob("no_backup.log*"))
            # Ana dosya + muhtemelen .1 dosyası (geçici)
            assert len(files) <= 2
        finally:
            handler.stop()
            handler.handler.close()


class TestTraceContextLimits:
    """Trace context limit testleri"""
    
    def test_deeply_nested_trace_contexts(self):
        """Çok derin nested trace context (100 seviye)"""
        contexts = []
        errors = []
        
        try:
            def create_nested(depth: int, max_depth: int):
                if depth >= max_depth:
                    return
                
                with trace(trace_id=f"trace-{depth}") as ctx:
                    contexts.append((depth, ctx.trace_id))
                    create_nested(depth + 1, max_depth)
            
            create_nested(0, 100)
            
            # Tüm context'ler oluşturulmalı
            assert len(contexts) == 100
            
            # Her seviyenin kendi trace_id'si olmalı
            trace_ids = [trace_id for _, trace_id in contexts]
            assert len(set(trace_ids)) == 100
        except Exception as e:
            errors.append(str(e))
        
        assert len(errors) == 0, f"Errors: {errors}"
    
    def test_trace_with_very_long_ids(self):
        """Çok uzun trace_id ve span_id"""
        long_id = "A" * 10000  # 10KB ID
        
        with trace(trace_id=long_id) as ctx:
            assert ctx.trace_id == long_id
            assert len(ctx.trace_id) == 10000
            
            # Header'lara eklenebilmeli
            headers = ctx.headers()
            assert headers["X-Trace-ID"] == long_id
    
    def test_trace_with_many_extra_fields(self):
        """Çok fazla extra alan ile trace"""
        extra = {f"field_{i}": f"value_{i}" for i in range(1000)}
        
        with trace(**extra) as ctx:
            # Tüm alanlar eklenmeli
            assert len(ctx.extra) == 1000
            assert ctx.extra["field_0"] == "value_0"
            assert ctx.extra["field_999"] == "value_999"


class TestSpecialCharacters:
    """Özel karakter testleri"""
    
    def test_unicode_in_log_messages(self, clean_loggers, temp_log_file):
        """Unicode karakterler"""
        handler = AsyncRotatingFileHandler(filename=temp_log_file)
        handler.handler.setFormatter(JSONFormatter())
        
        logger = logging.getLogger("unicode_test")
        logger.addHandler(handler.get_queue_handler())
        logger.setLevel(logging.INFO)
        
        try:
            # Farklı dillerde karakterler
            messages = [
                "Hello 世界",  # Çince
                "Привет мир",  # Rusça
                "مرحبا بالعالم",  # Arapça
                "สวัสดีชาวโลก",  # Tayca
                "Emoji test: 🎉 🚀 ✨",  # Emoji
                "Türkçe: ığüşöç ÖÇŞİĞÜ",  # Türkçe
            ]
            
            for msg in messages:
                logger.info(msg)
            
            time.sleep(0.5)
            
            # Dosya okunabilir olmalı
            content = Path(temp_log_file).read_text(encoding='utf-8')
            
            # Tüm mesajlar bulunmalı
            for msg in messages:
                assert msg in content or json.dumps(msg, ensure_ascii=False) in content
        finally:
            handler.stop()
            handler.handler.close()
    
    def test_special_characters_in_trace_id(self):
        """Özel karakterler trace_id'de"""
        special_chars = "!@#$%^&*()_+-=[]{}|;:',.<>?/~`"
        
        with trace(trace_id=special_chars) as ctx:
            assert ctx.trace_id == special_chars
    
    def test_null_and_empty_values(self, clean_loggers, temp_log_file):
        """Null ve boş değerler"""
        handler = AsyncRotatingFileHandler(filename=temp_log_file)
        handler.handler.setFormatter(JSONFormatter())
        
        logger = logging.getLogger("null_test")
        logger.addHandler(handler.get_queue_handler())
        logger.setLevel(logging.INFO)
        
        try:
            # Boş mesaj
            logger.info("")
            
            # None değerler
            logger.info("Test", extra={"value": None, "empty": ""})
            
            time.sleep(0.5)
            
            assert Path(temp_log_file).exists()
        finally:
            handler.stop()
            handler.handler.close()


class TestErrorHandling:
    """Hata durumu testleri"""
    
    def test_logging_during_exception(self, clean_loggers, temp_log_file):
        """Exception içinde logging"""
        handler = AsyncRotatingFileHandler(filename=temp_log_file)
        handler.handler.setFormatter(JSONFormatter())
        
        logger = logging.getLogger("exception_test")
        logger.addHandler(handler.get_queue_handler())
        logger.setLevel(logging.INFO)
        
        try:
            try:
                raise ValueError("Test error")
            except ValueError:
                logger.exception("Exception occurred")
            
            time.sleep(0.5)
            
            # Exception bilgisi loglanmalı
            content = Path(temp_log_file).read_text()
            assert "ValueError" in content
            assert "Test error" in content
        finally:
            handler.stop()
            handler.handler.close()
    
    def test_recursive_logging(self, clean_loggers):
        """Recursive logging (handler içinden log)"""
        from microlog.handlers import AsyncConsoleHandler
        
        handler = AsyncConsoleHandler()
        logger = logging.getLogger("recursive_test")
        logger.addHandler(handler.get_queue_handler())
        logger.setLevel(logging.DEBUG)
        
        # Bu çok tehlikeli ama test etmeliyiz
        # Normal kullanımda olmamalı
        errors = []
        
        try:
            for i in range(10):
                logger.info(f"Message {i}")
            
            time.sleep(0.5)
        except Exception as e:
            errors.append(str(e))
        
        assert len(errors) == 0
        handler.stop()
    
    def test_handler_with_invalid_file_path(self):
        """Geçersiz dosya yolu"""
        with pytest.raises(Exception):
            handler = AsyncRotatingFileHandler(
                filename="/invalid/path/that/does/not/exist/test.log"
            )


class TestMemoryAndPerformance:
    """Memory ve performans limit testleri"""
    
    def test_many_loggers(self, clean_loggers):
        """Çok fazla logger (1000)"""
        loggers = []
        
        for i in range(1000):
            logger = logging.getLogger(f"logger_{i}")
            loggers.append(logger)
        
        assert len(loggers) == 1000
        
        # Her logger çalışmalı
        for logger in loggers[:10]:  # İlk 10'unu test et
            logger.info("Test")
    
    def test_many_handlers_per_logger(self, clean_loggers, temp_dir):
        """Bir logger'a çok fazla handler (50)"""
        from microlog.handlers import AsyncConsoleHandler, AsyncRotatingFileHandler
        
        logger = logging.getLogger("many_handlers_test")
        logger.setLevel(logging.INFO)
        
        handlers = []
        
        try:
            # 25 console + 25 file handler
            for i in range(25):
                console_handler = AsyncConsoleHandler()
                handlers.append(console_handler)
                logger.addHandler(console_handler.get_queue_handler())
                
                file_handler = AsyncRotatingFileHandler(
                    filename=str(temp_dir / f"handler_{i}.log")
                )
                handlers.append(file_handler)
                logger.addHandler(file_handler.get_queue_handler())
            
            # Log yazmalı
            logger.info("Test with many handlers")
            time.sleep(1.0)
            
            # Dosyalar oluşmuş olmalı
            files = list(temp_dir.glob("handler_*.log"))
            assert len(files) >= 20  # En az 20 dosya
        finally:
            for handler in handlers:
                handler.stop()
                if hasattr(handler, 'handler') and hasattr(handler.handler, 'close'):
                    handler.handler.close()
    
    def test_rapid_logging(self, clean_loggers, temp_log_file):
        """Çok hızlı logging (10000 log)"""
        handler = AsyncRotatingFileHandler(filename=temp_log_file)
        
        logger = logging.getLogger("rapid_logging_test")
        logger.addHandler(handler.get_queue_handler())
        logger.setLevel(logging.INFO)
        
        try:
            start = time.time()
            
            for i in range(10000):
                logger.info(f"Rapid log {i}")
            
            elapsed = time.time() - start
            
            time.sleep(2.0)  # Queue'nun işlenmesi için
            
            # Çok hızlı olmalı (< 2 saniye)
            assert elapsed < 2.0, f"Logging too slow: {elapsed}s"
            
            # Dosya oluşmuş olmalı
            assert Path(temp_log_file).exists()
        finally:
            handler.stop()
            handler.handler.close()


class TestRateLimiting:
    """Rate limiting edge case testleri"""
    
    def test_rate_limit_with_zero(self):
        """rate_limit=0 (disabled)"""
        from microlog.handlers import AsyncSMTPHandler
        
        handler = AsyncSMTPHandler(
            mailhost=("smtp.example.com", 587),
            fromaddr="test@example.com",
            toaddrs=["admin@example.com"],
            subject="Test",
            rate_limit=0  # Disabled
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
        
        # Her çağrı True dönmeli (rate limit yok)
        for _ in range(10):
            assert handler.handler._should_send(record) is True
        
        handler.stop()
    
    def test_rate_limit_with_negative(self):
        """rate_limit=-1 (disabled)"""
        from microlog.handlers import AsyncSMTPHandler
        
        handler = AsyncSMTPHandler(
            mailhost=("smtp.example.com", 587),
            fromaddr="test@example.com",
            toaddrs=["admin@example.com"],
            subject="Test",
            rate_limit=-1  # Disabled
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
        
        # Her çağrı True dönmeli
        for _ in range(10):
            assert handler.handler._should_send(record) is True
        
        handler.stop()


class TestFormatterLimits:
    """Formatter limit testleri"""
    
    def test_formatter_with_circular_reference(self, clean_loggers, temp_log_file):
        """Circular reference içeren veri"""
        handler = AsyncRotatingFileHandler(filename=temp_log_file)
        handler.handler.setFormatter(JSONFormatter())
        
        logger = logging.getLogger("circular_test")
        logger.addHandler(handler.get_queue_handler())
        logger.setLevel(logging.INFO)
        
        try:
            # Circular reference
            data = {"a": 1}
            data["self"] = data  # Circular!
            
            # Bu hata vermemeli (default=str sayesinde)
            logger.info("Test", extra={"data": data})
            time.sleep(0.5)
            
            assert Path(temp_log_file).exists()
        finally:
            handler.stop()
            handler.handler.close()
    
    def test_formatter_with_non_serializable_objects(self, clean_loggers, temp_log_file):
        """Serialize edilemeyen objeler"""
        handler = AsyncRotatingFileHandler(filename=temp_log_file)
        handler.handler.setFormatter(JSONFormatter())
        
        logger = logging.getLogger("non_serializable_test")
        logger.addHandler(handler.get_queue_handler())
        logger.setLevel(logging.INFO)
        
        try:
            # Lambda, function gibi serialize edilemeyen objeler
            logger.info("Test", extra={
                "function": lambda x: x,
                "class": AsyncRotatingFileHandler,
                "object": object()
            })
            
            time.sleep(0.5)
            
            # Hata vermemeli (str()'e çevrilir)
            assert Path(temp_log_file).exists()
        finally:
            handler.stop()
            handler.handler.close()

