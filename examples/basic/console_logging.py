"""
Örnek: Console Logging

Renkli console çıktısı ve extra alanlar ile loglama.
setup_console_logger kullanımı.

Kullanım:
    python examples/basic/console_logging.py

Çıktı:
    Renkli ve formatlanmış log mesajları console'a yazılır.
    Extra alanlar otomatik olarak log mesajına eklenir.
"""

from microlog import setup_console_logger


def main():
    # Renkli console logger oluştur - return_handlers=True ile handler'ı da alıyoruz
    logger, handlers = setup_console_logger(
        name="myapp",
        service_name="order-service",
        use_colors=True,
        return_handlers=True
    )
    
    # Basit log mesajları
    logger.info("Sipariş sistemi başlatıldı")
    logger.warning("Stok seviyesi düşük")
    
    # Extra alanlar ile loglama
    logger.info(
        "Sipariş oluşturuldu",
        extra={
            "order_id": "ORD-12345",
            "user_id": "usr-789",
            "amount": 99.99,
            "currency": "USD"
        }
    )
    
    logger.error(
        "Ödeme başarısız",
        extra={
            "order_id": "ORD-12345",
            "error_code": "PAY-001",
            "error_message": "Yetersiz bakiye"
        }
    )
    
    # Renksiz console logger (production benzeri)
    logger_plain, handlers_plain = setup_console_logger(
        name="myapp",
        service_name="order-service",
        use_colors=False,
        return_handlers=True
    )
    
    logger_plain.info("Renksiz çıktı - production için uygun")
    
    # Graceful shutdown: Tüm handler'ları kapat
    for handler in handlers + handlers_plain:
        handler.stop()


if __name__ == "__main__":
    main()

