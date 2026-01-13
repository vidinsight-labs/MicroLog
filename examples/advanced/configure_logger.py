"""
Örnek: Mevcut Logger'ı Yapılandırma

configure_logger kullanımı.
Mevcut logging.Logger'ı MicroLog ile yapılandırma.

Kullanım:
    python examples/advanced/configure_logger.py

Çıktı:
    Mevcut logger MicroLog handler'ları ile yapılandırılır.
"""

import logging
from microlog import configure_logger, HandlerConfig
from microlog.handlers import AsyncConsoleHandler, AsyncRotatingFileHandler
from microlog.formatters import JSONFormatter, PrettyFormatter


def main():
    print("Mevcut Logger'ı Yapılandırma Örneği")
    print("=" * 60)
    print()
    
    # 1. Mevcut logger oluştur (standart logging ile)
    print("1. Mevcut logger oluşturuluyor:")
    existing_logger = logging.getLogger("existing-app")
    existing_logger.setLevel(logging.DEBUG)
    
    print(f"   Logger adı: {existing_logger.name}")
    print(f"   Mevcut handler sayısı: {len(existing_logger.handlers)}")
    print()
    
    # 2. MicroLog ile yapılandır
    print("2. MicroLog ile yapılandırılıyor:")
    configure_logger(
        logger=existing_logger,
        level=logging.INFO,
        service_name="configured-service",
        handlers=[
            HandlerConfig(
                handler=AsyncConsoleHandler(),
                formatter=PrettyFormatter(
                    service_name="configured-service",
                    use_colors=True
                )
            ),
            HandlerConfig(
                handler=AsyncRotatingFileHandler(
                    filename="configured.log",
                    max_bytes=10 * 1024 * 1024,
                    backup_count=5,
                    compress=True
                ),
                formatter=JSONFormatter(
                    service_name="configured-service"
                )
            )
        ],
        add_trace_filter=True
    )
    
    print(f"   Yeni handler sayısı: {len(existing_logger.handlers)}")
    print()
    
    # 3. Logger'ı kullan
    print("3. Logger kullanımı:")
    existing_logger.info("Mevcut logger ile log mesajı")
    
    existing_logger.info(
        "Yapılandırılmış log",
        extra={
            "user_id": "usr-123",
            "action": "configure",
            "status": "success"
        }
    )
    
    existing_logger.warning("Uyarı mesajı", extra={"code": "W001"})
    existing_logger.error("Hata mesajı", extra={"code": "E001"})
    print()
    
    # 4. Handler'ları al ve kapat
    print("4. Handler'ları kapatılıyor:")
    # configure_logger return_handlers desteklemiyor, manuel olarak alalım
    async_handlers = [
        h for h in existing_logger.handlers
        if hasattr(h, 'queue')  # QueueHandler kontrolü
    ]
    
    # Handler referanslarını bulmak için setup_logger kullanabiliriz
    # Ama bu örnekte sadece logger kullanımını gösteriyoruz
    print("   Handler'lar atexit ile otomatik kapanacak")
    print()
    
    print("=" * 60)
    print("Örnek tamamlandı!")
    print()
    print("configure_logger Kullanım Senaryoları:")
    print("- Mevcut logging.Logger'ı MicroLog'a geçirme")
    print("- Üçüncü parti kütüphanelerin logger'larını yapılandırma")
    print("- Logger yapılandırmasını merkezi bir yerden yönetme")


if __name__ == "__main__":
    main()

