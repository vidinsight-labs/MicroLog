"""
Örnek: Hello World - İlk Adımlar

MicroLog'un temel özelliklerini gösteren kapsamlı başlangıç örneği.

Bu örnek:
- Logger oluşturma
- Tüm log seviyeleri (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Extra alanlar ile loglama
- Exception logging

Kullanım:
    python examples/quickstart/hello_world.py

Çıktı:
    Renkli ve formatlanmış log mesajları console'a yazılır.
"""

from microlog import setup_logger


def main():
    """Ana fonksiyon - tüm temel özellikleri gösterir."""
    
    # 1. Logger oluştur - return_handlers=True ile handler'ları da alıyoruz
    logger, handlers = setup_logger("hello-world", service_name="my-service", return_handlers=True)
    
    print("=" * 60)
    print("MicroLog Hello World Örneği")
    print("=" * 60)
    print()
    
    # 2. Tüm log seviyeleri
    print("Log Seviyeleri:")
    logger.debug("Bu bir DEBUG mesajıdır")
    logger.info("Bu bir INFO mesajıdır")
    logger.warning("Bu bir WARNING mesajıdır")
    logger.error("Bu bir ERROR mesajıdır")
    logger.critical("Bu bir CRITICAL mesajıdır")
    print()
    
    # 3. Extra alanlar ile loglama
    print("Extra Alanlar ile Loglama:")
    logger.info(
        "Kullanıcı giriş yaptı",
        extra={
            "user_id": "usr-123",
            "email": "user@example.com",
            "ip_address": "192.168.1.1"
        }
    )
    print()
    
    # 4. Exception logging
    print("Exception Logging:")
    try:
        # Hata oluştur
        result = 10 / 0
    except ZeroDivisionError:
        # Exception detayları ile logla
        logger.exception("Sıfıra bölme hatası oluştu")
    print()
    
    # 5. İşlem loglama örneği
    print("İşlem Loglama:")
    logger.info("İşlem başlatıldı", extra={"operation": "data_processing"})
    
    # Simüle edilmiş işlem
    import time
    time.sleep(0.1)
    
    logger.info(
        "İşlem tamamlandı",
        extra={
            "operation": "data_processing",
            "duration_ms": 100,
            "records_processed": 42
        }
    )
    print()
    
    # Graceful shutdown: Handler'ları kapat (queue'daki loglar flush edilir)
    for handler in handlers:
        handler.stop()
    
    print("=" * 60)
    print("Örnek tamamlandı!")
    print("=" * 60)


if __name__ == "__main__":
    main()

