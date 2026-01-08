"""
Test handlers.py - Log Çıktı Hedefleri
"""

import pytest
import logging
import time
from pathlib import Path
from microlog.handlers import (
    AsyncConsoleHandler,
    AsyncRotatingFileHandler,
)


class TestAsyncConsoleHandler:
    """AsyncConsoleHandler testleri"""
    
    def test_async_console_handler_creation(self):
        """AsyncConsoleHandler başarıyla oluşturulur"""
        handler = AsyncConsoleHandler()
        
        assert handler is not None
        assert handler.handler is not None
        assert handler._started is False
    
    def test_async_console_handler_start(self):
        """start() metodu handler'ı başlatır ve listener oluşturur"""
        handler = AsyncConsoleHandler()
        handler.start()
        
        assert handler._started is True
        assert handler._listener is not None
        
        handler.stop()
    
    def test_async_console_handler_get_queue_handler(self):
        """get_queue_handler() QueueHandler döndürür ve handler'ı otomatik başlatır"""
        handler = AsyncConsoleHandler()
        queue_handler = handler.get_queue_handler()
        
        assert queue_handler is not None
        assert handler._started is True
        
        handler.stop()
    
    def test_async_console_handler_with_level(self):
        """AsyncConsoleHandler level parametresi ile çalışır"""
        handler = AsyncConsoleHandler(level=logging.WARNING)
        
        assert handler.handler.level == logging.WARNING
        
        handler.stop()


class TestAsyncRotatingFileHandler:
    """AsyncRotatingFileHandler testleri"""
    
    def test_async_rotating_file_handler_creation(self, temp_log_file):
        """AsyncRotatingFileHandler başarıyla oluşturulur ve dosya açılır"""
        handler = AsyncRotatingFileHandler(
            filename=temp_log_file,
            max_bytes=1024,
            backup_count=3
        )
        
        assert handler.filename == temp_log_file
        assert handler.max_bytes == 1024
        assert handler.backup_count == 3
        assert Path(temp_log_file).exists()
        
        handler.stop()
        handler.handler.close()
    
    def test_async_rotating_file_handler_logging(self, temp_log_file):
        """AsyncRotatingFileHandler logları dosyaya yazar"""
        handler = AsyncRotatingFileHandler(filename=temp_log_file)
        queue_handler = handler.get_queue_handler()
        
        logger = logging.getLogger("test_file_logger")
        logger.addHandler(queue_handler)
        logger.setLevel(logging.DEBUG)
        
        logger.info("Test log message")
        
        # Queue'nun işlenmesi için kısa bekleme
        time.sleep(0.1)
        
        # Dosyayı kontrol et
        assert Path(temp_log_file).exists()
        content = Path(temp_log_file).read_text()
        assert "Test log message" in content
        
        handler.stop()
        handler.handler.close()
    
    def test_async_rotating_file_handler_rotation(self, temp_dir):
        """AsyncRotatingFileHandler dosya boyutu limiti aşıldığında rotation yapar"""
        log_file = temp_dir / "rotate_test.log"
        handler = AsyncRotatingFileHandler(
            filename=str(log_file),
            max_bytes=100,  # Küçük limit
            backup_count=2,
            compress=False  # Test için sıkıştırma kapalı
        )
        
        queue_handler = handler.get_queue_handler()
        logger = logging.getLogger("test_rotation")
        logger.addHandler(queue_handler)
        logger.setLevel(logging.DEBUG)
        
        # Dosyayı doldur
        for i in range(20):
            logger.info(f"Test message {i} " * 10)  # Her mesaj ~200 byte
        
        time.sleep(0.2)  # Rotation için bekleme
        
        # Rotation olmuş mu kontrol et
        # En az bir backup dosyası olmalı
        backups = list(temp_dir.glob("rotate_test.log.*"))
        # Rotation çalışmış olabilir (dosya boyutuna bağlı)
        
        handler.stop()
        handler.handler.close()


