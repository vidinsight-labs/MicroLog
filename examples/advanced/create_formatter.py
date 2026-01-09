"""
Örnek: Formatter Factory

create_formatter kullanımı.
Factory pattern ile formatter oluşturma.

Kullanım:
    python examples/advanced/create_formatter.py

Çıktı:
    Factory fonksiyonu ile farklı formatter'lar oluşturulur.
"""

import os
from microlog import setup_logger, HandlerConfig
from microlog.handlers import AsyncConsoleHandler, AsyncRotatingFileHandler
from microlog.formatters import create_formatter


def main():
    print("Formatter Factory Örneği")
    print("=" * 60)
    print()
    
    # Log dosyası yolu
    log_file = "factory.log"
    if os.path.exists(log_file):
        os.remove(log_file)
    
    # Handler'ları toplamak için liste
    all_handlers = []
    
    # 1. JSON Formatter (factory ile)
    print("1. JSON Formatter (factory ile):")
    json_formatter = create_formatter(
        format_type="json",
        service_name="factory-service",
        include_location=False
    )
    
    logger1, handlers1 = setup_logger(
        name="json-app",
        service_name="factory-service",
        handlers=[
            HandlerConfig(
                handler=AsyncRotatingFileHandler(
                    filename=log_file,
                    max_bytes=10 * 1024 * 1024,
                    backup_count=5
                ),
                formatter=json_formatter
            )
        ],
        return_handlers=True
    )
    all_handlers.extend(handlers1)
    
    logger1.info("JSON formatter ile log", extra={"test": "json"})
    print("   ✓ JSON formatter oluşturuldu")
    print()
    
    # 2. Pretty Formatter (factory ile)
    print("2. Pretty Formatter (factory ile):")
    pretty_formatter = create_formatter(
        format_type="pretty",
        service_name="factory-service",
        use_colors=True,
        use_utc=False,
        show_date=False
    )
    
    logger2, handlers2 = setup_logger(
        name="pretty-app",
        service_name="factory-service",
        handlers=[
            HandlerConfig(
                handler=AsyncConsoleHandler(),
                formatter=pretty_formatter
            )
        ],
        return_handlers=True
    )
    all_handlers.extend(handlers2)
    
    logger2.info("Pretty formatter ile log", extra={"test": "pretty"})
    print("   ✓ Pretty formatter oluşturuldu")
    print()
    
    # 3. Compact Formatter (factory ile)
    print("3. Compact Formatter (factory ile):")
    compact_formatter = create_formatter(
        format_type="compact",
        service_name="factory-service",
        include_timestamp=True
    )
    
    logger3, handlers3 = setup_logger(
        name="compact-app",
        service_name="factory-service",
        handlers=[
            HandlerConfig(
                handler=AsyncConsoleHandler(),
                formatter=compact_formatter
            )
        ],
        return_handlers=True
    )
    all_handlers.extend(handlers3)
    
    logger3.info("Compact formatter ile log", extra={"test": "compact"})
    print("   ✓ Compact formatter oluşturuldu")
    print()
    
    # 4. Dinamik formatter seçimi
    print("4. Dinamik Formatter Seçimi:")
    # Ortam değişkenine göre formatter seç
    env_format = os.getenv("LOG_FORMAT", "json")
    
    # PrettyFormatter için use_colors parametresi geçerli
    # Diğer formatter'lar için geçersiz parametre geçmemeliyiz
    if env_format == "pretty":
        dynamic_formatter = create_formatter(
            format_type=env_format,
            service_name="dynamic-service",
            use_colors=True
        )
    else:
        dynamic_formatter = create_formatter(
            format_type=env_format,
            service_name="dynamic-service"
        )
    
    logger4, handlers4 = setup_logger(
        name="dynamic-app",
        service_name="dynamic-service",
        handlers=[
            HandlerConfig(
                handler=AsyncConsoleHandler(),
                formatter=dynamic_formatter
            )
        ],
        return_handlers=True
    )
    all_handlers.extend(handlers4)
    
    logger4.info(
        f"Dinamik formatter: {env_format}",
        extra={"format_type": env_format}
    )
    print(f"   ✓ Dinamik formatter seçildi: {env_format}")
    print()
    
    # Graceful shutdown: Tüm handler'ları kapat
    for handler in all_handlers:
        handler.stop()
    
    print("=" * 60)
    print("Örnek tamamlandı!")
    print()
    print("create_formatter Avantajları:")
    print("- Factory pattern ile merkezi formatter yönetimi")
    print("- Dinamik formatter seçimi")
    print("- Yapılandırma dosyalarından kolay kullanım")
    print("- Ortam değişkenlerine göre formatter seçimi")


if __name__ == "__main__":
    main()

