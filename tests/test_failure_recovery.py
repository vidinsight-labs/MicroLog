"""
Hata durumu ve recovery testleri.

Bu modül şunları test eder:
    - Disk dolu durumu
    - Dosya permission hataları
    - Network timeout (SMTP)
    - Bozuk dosya recovery
    - Handler hataları ve recovery

Test Senaryoları:
    1. Disk full handling
    2. Permission denied recovery
    3. Network failure handling
    4. Corrupted file recovery
    5. Graceful degradation

Author: MicroLog Team
Created: 2026-01-05
"""

import logging
import os
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from microlog import (
    AsyncRotatingFileHandler,
    AsyncSMTPHandler,
    setup_logger
)
from microlog.handlers import _RotatingFileHandler


class TestDiskSpaceHandling:
    """Disk dolu durumu testleri"""
    
    def test_disk_full_error_handling(self, temp_log_file):
        """Disk dolu durumunda graceful handling"""
        handler = AsyncRotatingFileHandler(filename=temp_log_file)
        queue_handler = handler.get_queue_handler()
        
        logger = logging.getLogger("test_disk_full")
        logger.addHandler(queue_handler)
        logger.setLevel(logging.INFO)
        
        # İlk birkaç log normal yazılsın
        logger.info("Message 1")
        logger.info("Message 2")
        
        # Disk full simüle et
        original_write = os.write
        write_count = [0]
        
        def mock_write(fd, data):
            write_count[0] += 1
            if write_count[0] > 5:  # İlk 5 yazımdan sonra hata ver
                raise OSError(28, "No space left on device")
            return original_write(fd, data)
        
        with patch('os.write', side_effect=mock_write):
            # Hata oluşmalı ama crash olmamalı
            try:
                for i in range(10):
                    logger.info(f"Message {i + 3}")
                    time.sleep(0.01)
            except Exception as e:
                pytest.fail(f"Should not raise exception: {e}")
        
        handler.stop()
        
        # En azından ilk loglar yazılmış olmalı
        if Path(temp_log_file).exists():
            content = Path(temp_log_file).read_text()
            assert "Message 1" in content or "Message 2" in content
    
    def test_rotation_with_insufficient_space(self, temp_dir):
        """Yetersiz disk alanında rotation"""
        temp_file = temp_dir / "space_test.log"
        
        handler = AsyncRotatingFileHandler(
            filename=str(temp_file),
            max_bytes=1000,
            backup_count=3
        )
        queue_handler = handler.get_queue_handler()
        
        logger = logging.getLogger("test_rotation_space")
        logger.addHandler(queue_handler)
        logger.setLevel(logging.INFO)
        
        # Normal yazımlar
        for i in range(20):
            logger.info(f"Message {i} - padding to trigger rotation")
        
        # Rotation sırasında disk full simüle et
        original_rename = os.rename
        rename_count = [0]
        
        def mock_rename(src, dst):
            rename_count[0] += 1
            if rename_count[0] > 2:
                raise OSError(28, "No space left on device")
            return original_rename(src, dst)
        
        with patch('os.rename', side_effect=mock_rename):
            try:
                for i in range(20):
                    logger.info(f"After-error message {i} - padding")
                    time.sleep(0.01)
            except Exception as e:
                pytest.fail(f"Should not crash: {e}")
        
        handler.stop()
        
        # Dosya hala var olmalı
        assert temp_file.exists(), "Log file should still exist"


class TestPermissionErrors:
    """Permission hata testleri"""
    
    def test_readonly_file_handling(self, temp_log_file):
        """Read-only dosyaya yazma hatası"""
        # Önce handler oluştur ve ilk log yaz
        handler = AsyncRotatingFileHandler(filename=temp_log_file)
        queue_handler = handler.get_queue_handler()
        
        logger = logging.getLogger("test_readonly")
        logger.addHandler(queue_handler)
        logger.setLevel(logging.INFO)
        
        logger.info("Initial message")
        time.sleep(0.2)
        handler.stop()
        
        # Dosyayı read-only yap
        os.chmod(temp_log_file, 0o444)
        
        try:
            # Yeni handler oluşturmaya çalış - başarısız olmalı ama crash olmamalı
            try:
                handler2 = AsyncRotatingFileHandler(filename=temp_log_file)
                queue_handler2 = handler2.get_queue_handler()
                
                logger2 = logging.getLogger("test_readonly_2")
                logger2.addHandler(queue_handler2)
                logger2.setLevel(logging.INFO)
                
                # Yazma denemesi
                logger2.info("This should fail")
                time.sleep(0.2)
                handler2.stop()
                
                # Dosya değişmemiş olmalı
                content = Path(temp_log_file).read_text()
                assert "This should fail" not in content
            except PermissionError:
                # Permission error bekleniyor, crash olmamalı
                pass
            
        finally:
            # Cleanup için permission geri al
            os.chmod(temp_log_file, 0o644)
    
    def test_directory_permission_error(self, temp_dir):
        """Dizin permission hatası"""
        # Read-only dizin
        readonly_dir = temp_dir / "readonly"
        readonly_dir.mkdir()
        
        log_file = readonly_dir / "test.log"
        
        # İlk dosya oluştur (permission varken)
        log_file.write_text("Initial\n")
        
        # Dizini read-only yap
        os.chmod(readonly_dir, 0o555)
        
        try:
            handler = AsyncRotatingFileHandler(
                filename=str(log_file),
                max_bytes=100,
                backup_count=2
            )
            queue_handler = handler.get_queue_handler()
            
            logger = logging.getLogger("test_dir_perm")
            logger.addHandler(queue_handler)
            logger.setLevel(logging.INFO)
            
            # Rotation tetikleyen loglar - rotation başarısız olabilir
            for i in range(50):
                logger.info(f"Message {i} - padding to trigger rotation attempt")
                time.sleep(0.01)
            
            handler.stop()
            
            # Crash olmamalı
            assert True, "Should handle permission errors gracefully"
            
        finally:
            # Cleanup
            os.chmod(readonly_dir, 0o755)


class TestNetworkFailures:
    """Network hata testleri (SMTP)"""
    
    def test_smtp_connection_timeout(self):
        """SMTP connection timeout handling"""
        # Mock SMTP ile timeout simüle et
        with patch('smtplib.SMTP') as mock_smtp:
            mock_smtp.side_effect = TimeoutError("Connection timeout")
            
            handler = AsyncSMTPHandler(
                mailhost=("smtp.example.com", 587),
                fromaddr="test@example.com",
                toaddrs=["dest@example.com"],
                subject="Test"
            )
            
            queue_handler = handler.get_queue_handler()
            
            logger = logging.getLogger("test_smtp_timeout")
            logger.addHandler(queue_handler)
            logger.setLevel(logging.ERROR)
            
            # Email gönderilmeye çalışılacak ama timeout olacak
            # Crash olmamalı
            try:
                logger.error("This should timeout but not crash")
                time.sleep(0.5)
                
                handler.stop()
                assert True, "Should handle timeout gracefully"
            except Exception as e:
                pytest.fail(f"Should not raise: {e}")
    
    def test_smtp_authentication_failure(self):
        """SMTP authentication failure handling"""
        # Mock SMTP ile auth failure simüle et
        with patch('smtplib.SMTP') as mock_smtp:
            mock_instance = MagicMock()
            mock_instance.login.side_effect = Exception("Authentication failed")
            mock_smtp.return_value.__enter__.return_value = mock_instance
            
            handler = AsyncSMTPHandler(
                mailhost=("smtp.example.com", 587),
                fromaddr="test@example.com",
                toaddrs=["dest@example.com"],
                subject="Test",
                credentials=("user", "wrong_password")
            )
            
            queue_handler = handler.get_queue_handler()
            
            logger = logging.getLogger("test_smtp_auth")
            logger.addHandler(queue_handler)
            logger.setLevel(logging.ERROR)
            
            try:
                logger.error("Auth should fail")
                time.sleep(0.5)
                handler.stop()
                assert True, "Should handle auth failure gracefully"
            except Exception as e:
                pytest.fail(f"Should not crash: {e}")
    
    def test_smtp_rate_limiting_recovery(self):
        """SMTP rate limiting sonrası recovery"""
        with patch('smtplib.SMTP') as mock_smtp:
            mock_instance = MagicMock()
            send_count = [0]
            
            def mock_send(from_addr, to_addrs, msg):
                send_count[0] += 1
                if send_count[0] <= 3:
                    raise Exception("Rate limit exceeded")
                return {}  # Success
            
            mock_instance.sendmail.side_effect = mock_send
            mock_smtp.return_value.__enter__.return_value = mock_instance
            
            handler = AsyncSMTPHandler(
                mailhost=("smtp.example.com", 587),
                fromaddr="test@example.com",
                toaddrs=["dest@example.com"],
                subject="Test"
            )
            
            queue_handler = handler.get_queue_handler()
            
            logger = logging.getLogger("test_smtp_rate")
            logger.addHandler(queue_handler)
            logger.setLevel(logging.ERROR)
            
            # Birkaç email gönder
            for i in range(5):
                logger.error(f"Email {i}")
                time.sleep(0.2)
            
            handler.stop()
            
            # İlk birkaç başarısız oldu, sonrakiler başarılı olmalı
            # En az 2 başarılı send olmalı
            assert send_count[0] >= 2, f"Only {send_count[0]} send attempts"


class TestCorruptedFileRecovery:
    """Bozuk dosya recovery testleri"""
    
    def test_corrupted_log_file_recovery(self, temp_log_file):
        """Bozuk log dosyası recovery"""
        # Önce normal log yaz
        handler = AsyncRotatingFileHandler(filename=temp_log_file)
        queue_handler = handler.get_queue_handler()
        
        logger = logging.getLogger("test_corrupt")
        logger.addHandler(queue_handler)
        logger.setLevel(logging.INFO)
        
        logger.info("Message 1")
        handler.stop()
        time.sleep(0.2)
        
        # Dosyayı boz (binary data ekle)
        with open(temp_log_file, 'ab') as f:
            f.write(b'\x00\x00\xFF\xFF\xAA\xBB')
        
        # Yeni handler oluştur ve devam et
        handler2 = AsyncRotatingFileHandler(filename=temp_log_file)
        queue_handler2 = handler2.get_queue_handler()
        
        logger2 = logging.getLogger("test_corrupt_2")
        logger2.addHandler(queue_handler2)
        logger2.setLevel(logging.INFO)
        
        try:
            logger2.info("Message 2 after corruption")
            handler2.stop()
            time.sleep(0.2)
            
            # Dosya var olmalı
            assert Path(temp_log_file).exists()
            
        except Exception as e:
            pytest.fail(f"Should handle corrupted file: {e}")
    
    def test_missing_backup_file_recovery(self, temp_dir):
        """Eksik backup dosyası recovery"""
        temp_file = temp_dir / "backup_test.log"
        
        handler = AsyncRotatingFileHandler(
            filename=str(temp_file),
            max_bytes=500,
            backup_count=3
        )
        queue_handler = handler.get_queue_handler()
        
        logger = logging.getLogger("test_backup_missing")
        logger.addHandler(queue_handler)
        logger.setLevel(logging.INFO)
        
        # Rotation tetikle
        for i in range(50):
            logger.info(f"Message {i} - padding to trigger rotation")
        
        time.sleep(0.5)
        
        # Backup dosyalarından birini sil
        backup1 = Path(str(temp_file) + ".1")
        if backup1.exists():
            backup1.unlink()
        
        # Devam et - crash olmamalı
        try:
            for i in range(50):
                logger.info(f"After deletion message {i}")
            
            handler.stop()
            assert True, "Should handle missing backup file"
            
        except Exception as e:
            pytest.fail(f"Should not crash: {e}")


class TestHandlerErrorRecovery:
    """Handler hata recovery testleri"""
    
    def test_formatter_exception_handling(self, temp_log_file):
        """Formatter exception handling"""
        handler = AsyncRotatingFileHandler(filename=temp_log_file)
        
        # Bozuk formatter
        class BrokenFormatter(logging.Formatter):
            def format(self, record):
                if "error" in record.getMessage():
                    raise ValueError("Formatter error")
                return super().format(record)
        
        handler.handler.setFormatter(BrokenFormatter())
        queue_handler = handler.get_queue_handler()
        
        logger = logging.getLogger("test_formatter_error")
        logger.addHandler(queue_handler)
        logger.setLevel(logging.INFO)
        
        try:
            # Normal log
            logger.info("Normal message")
            
            # Formatter error tetikleyen log
            logger.info("This causes error in formatter")
            
            # Devam et
            logger.info("After error")
            
            handler.stop()
            time.sleep(0.2)
            
            # En azından bazı loglar yazılmış olmalı
            content = Path(temp_log_file).read_text()
            assert "Normal message" in content
            
        except Exception as e:
            pytest.fail(f"Should handle formatter errors: {e}")
    
    def test_handler_emit_exception(self, temp_log_file):
        """Handler emit exception handling - crash olmamalı"""
        from microlog.handlers import AsyncHandler
        
        # Normal handler oluştur
        file_handler = logging.FileHandler(temp_log_file)
        
        # emit metodunu override et - her zaman fail
        def always_fail_emit(record):
            raise IOError("Simulated emit failure")
        
        file_handler.emit = always_fail_emit
        
        # AsyncHandler ile sar
        async_handler = AsyncHandler(file_handler)
        queue_handler = async_handler.get_queue_handler()
        
        logger = logging.getLogger("test_emit_error")
        logger.addHandler(queue_handler)
        logger.setLevel(logging.INFO)
        
        # Log yaz - emit başarısız olacak ama crash olmamalı
        try:
            for i in range(5):
                logger.info(f"Message {i}")
                time.sleep(0.05)
            
            async_handler.stop()
            time.sleep(0.2)
            
            # Crash olmadı - test başarılı
            assert True, "Handler emit errors handled gracefully"
            
        except Exception as e:
            pytest.fail(f"Should not crash on emit errors: {e}")


class TestGracefulDegradation:
    """Graceful degradation testleri"""
    
    def test_continue_after_handler_failure(self, temp_dir):
        """Bir handler başarısız olsa bile diğerleri çalışmalı"""
        temp_file1 = temp_dir / "good.log"
        
        # İyi handler
        handler1 = AsyncRotatingFileHandler(filename=str(temp_file1))
        queue_handler1 = handler1.get_queue_handler()
        
        # Kötü handler (emit başarısız olur)
        class BadHandler(logging.Handler):
            def emit(self, record):
                raise Exception("Handler error")
            
            def handleError(self, record):
                pass  # Hataları sessizce yakala
        
        from microlog.handlers import AsyncHandler
        bad_handler_instance = BadHandler()
        handler2 = AsyncHandler(bad_handler_instance)
        queue_handler2 = handler2.get_queue_handler()
        
        logger = logging.getLogger("test_multi_handler")
        logger.addHandler(queue_handler1)
        logger.addHandler(queue_handler2)
        logger.setLevel(logging.INFO)
        
        # Log yaz - kötü handler başarısız olacak ama iyi handler çalışmaya devam edecek
        for i in range(10):
            logger.info(f"Message {i}")
            time.sleep(0.05)
        
        handler1.stop()
        handler2.stop()
        time.sleep(0.2)
        
        # İyi handler çalışmış olmalı
        content = temp_file1.read_text()
        lines = [l for l in content.strip().split('\n') if l]
        assert len(lines) >= 8, f"Good handler should work: {len(lines)} logs"
    
    def test_partial_logging_on_error(self, temp_log_file):
        """Kısmi hatalarda partial logging devam etmeli"""
        handler = AsyncRotatingFileHandler(filename=temp_log_file)
        queue_handler = handler.get_queue_handler()
        
        logger = logging.getLogger("test_partial")
        logger.addHandler(queue_handler)
        logger.setLevel(logging.INFO)
        
        # Normal başla
        for i in range(5):
            logger.info(f"Before error {i}")
        
        time.sleep(0.2)
        
        # Dosyayı geçici olarak read-only yap
        os.chmod(temp_log_file, 0o444)
        
        try:
            # Bunlar başarısız olabilir
            for i in range(5):
                logger.info(f"During error {i}")
                time.sleep(0.05)
        except:
            pass
        
        # Permission geri ver
        os.chmod(temp_log_file, 0o644)
        
        # Devam et
        for i in range(5):
            logger.info(f"After error {i}")
        
        handler.stop()
        time.sleep(0.2)
        
        # İlk ve son loglar yazılmış olmalı
        content = Path(temp_log_file).read_text()
        
        # En azından ilk loglar var olmalı
        before_count = sum(1 for i in range(5) if f"Before error {i}" in content)
        assert before_count >= 3, f"Only {before_count}/5 before logs found"

