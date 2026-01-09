"""
Örnek: Özel Handler

AsyncHandler'dan türetme.
Özel handler oluşturma örneği.

Kullanım:
    python examples/advanced/custom_handler.py

Çıktı:
    Özel handler ile log mesajları işlenir.
"""

import logging
from microlog.handlers import AsyncHandler
from microlog import setup_logger, HandlerConfig
from microlog.formatters import PrettyFormatter


class CustomEmailHandler(AsyncHandler):
    """
    Özel handler örneği - Email gönderme simülasyonu.
    Gerçek uygulamada SMTP handler olabilir.
    """
    
    def __init__(self, email_address: str, level: int = logging.ERROR):
        """
        Args:
            email_address: Email adresi
            level: Minimum log seviyesi (sadece ERROR ve üstü)
        """
        # Özel StreamHandler oluştur (gerçekte SMTP handler olurdu)
        handler = logging.StreamHandler()
        handler.setLevel(level)
        
        super().__init__(handler)
        self.email_address = email_address
    
    def format_message_for_email(self, record: logging.LogRecord) -> str:
        """Log kaydını email formatına dönüştür"""
        return (
            f"Subject: {record.levelname} - {record.getMessage()}\n"
            f"Service: {record.name}\n"
            f"Time: {record.created}\n"
            f"Message: {record.getMessage()}\n"
        )


class CustomDatabaseHandler(AsyncHandler):
    """
    Özel handler örneği - Veritabanına log yazma simülasyonu.
    Gerçek uygulamada veritabanı bağlantısı olurdu.
    """
    
    def __init__(self, table_name: str = "logs", level: int = logging.INFO):
        """
        Args:
            table_name: Veritabanı tablo adı
            level: Minimum log seviyesi
        """
        handler = logging.StreamHandler()  # Simülasyon için StreamHandler
        handler.setLevel(level)
        
        super().__init__(handler)
        self.table_name = table_name
        self.logs_buffer = []  # Simülasyon için buffer
    
    def format_message_for_db(self, record: logging.LogRecord) -> dict:
        """Log kaydını veritabanı formatına dönüştür"""
        return {
            "level": record.levelname,
            "message": record.getMessage(),
            "service": record.name,
            "timestamp": record.created,
            "extra": getattr(record, "extra", {})
        }


def main():
    print("Özel Handler Örneği")
    print("=" * 60)
    print()
    
    # 1. Email Handler örneği
    print("1. Custom Email Handler:")
    email_handler = CustomEmailHandler(
        email_address="admin@example.com",
        level=logging.ERROR  # Sadece ERROR ve üstü
    )
    
    logger1, handlers1 = setup_logger(
        name="email-app",
        service_name="email-service",
        handlers=[
            HandlerConfig(
                handler=email_handler,
                formatter=PrettyFormatter(service_name="email-service")
            )
        ],
        return_handlers=True
    )
    
    logger1.info("Bu mesaj email'e gitmez (INFO < ERROR)")
    logger1.error("Bu mesaj email'e gider (ERROR >= ERROR)")
    logger1.critical("Bu mesaj email'e gider (CRITICAL >= ERROR)")
    print(f"   Email handler oluşturuldu: {email_handler.email_address}")
    print()
    
    # 2. Database Handler örneği
    print("2. Custom Database Handler:")
    db_handler = CustomDatabaseHandler(
        table_name="application_logs",
        level=logging.INFO
    )
    
    logger2, handlers2 = setup_logger(
        name="db-app",
        service_name="db-service",
        handlers=[
            HandlerConfig(
                handler=db_handler,
                formatter=PrettyFormatter(service_name="db-service")
            )
        ],
        return_handlers=True
    )
    
    logger2.info("Veritabanına yazılacak log", extra={"user_id": "usr-123"})
    logger2.warning("Uyarı logu", extra={"code": "W001"})
    print(f"   Database handler oluşturuldu: {db_handler.table_name}")
    print()
    
    # 3. Birden fazla özel handler
    print("3. Birden Fazla Özel Handler:")
    logger3, handlers3 = setup_logger(
        name="multi-handler-app",
        service_name="multi-service",
        handlers=[
            HandlerConfig(
                handler=CustomEmailHandler("admin@example.com", level=logging.ERROR),
                formatter=PrettyFormatter(service_name="multi-service")
            ),
            HandlerConfig(
                handler=CustomDatabaseHandler("logs", level=logging.INFO),
                formatter=PrettyFormatter(service_name="multi-service")
            )
        ],
        return_handlers=True
    )
    
    logger3.info("Bu mesaj sadece DB'ye gider")
    logger3.error("Bu mesaj hem email'e hem DB'ye gider")
    print("   ✓ Birden fazla özel handler çalışıyor")
    print()
    
    # Graceful shutdown: Tüm handler'ları kapat
    all_handlers = handlers1 + handlers2 + handlers3
    for handler in all_handlers:
        handler.stop()
    
    print("=" * 60)
    print("Örnek tamamlandı!")
    print()
    print("Özel Handler Oluşturma:")
    print("- AsyncHandler'dan türetin")
    print("- logging.Handler'ı AsyncHandler'a geçirin")
    print("- Özel formatlama ve işleme ekleyebilirsiniz")
    print("- Thread-safe ve async çalışır")


if __name__ == "__main__":
    main()

