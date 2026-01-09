"""
Örnek: Basit Logging

En basit logging kullanımını gösterir.
setup_logger() ile logger oluşturma ve tüm log seviyeleri.

Kullanım:
    python examples/basic/simple_logging.py

Çıktı:
    14:32:01 │ INFO     │ myapp            │ Uygulama başlatıldı
    14:32:02 │ WARNING  │ myapp            │ Dikkat: Yüksek bellek kullanımı
    14:32:03 │ ERROR    │ myapp            │ Bir hata oluştu
"""

from microlog import setup_logger


def main():
    # Logger oluştur - return_handlers=True ile handler'ları da alıyoruz
    logger, handlers = setup_logger("myapp", return_handlers=True)
    
    # Farklı log seviyeleri
    logger.debug("Debug mesajı - detaylı bilgi")
    logger.info("Uygulama başlatıldı")
    logger.warning("Dikkat: Yüksek bellek kullanımı")
    logger.error("Bir hata oluştu")
    logger.critical("Kritik hata! Uygulama durdurulmalı")
    
    # Graceful shutdown: Handler'ları kapat (queue'daki loglar flush edilir)
    for handler in handlers:
        handler.stop()


if __name__ == "__main__":
    main()

