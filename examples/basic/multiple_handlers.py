"""
Örnek: Multiple Handlers

Birden fazla handler kullanımı.
Console ve File handler'ları birlikte kullanma.
Farklı formatter'lar (Pretty + JSON).

Kullanım:
    python examples/basic/multiple_handlers.py

Çıktı:
    Loglar hem console'a (renkli) hem dosyaya (JSON) yazılır.
"""

import os
from microlog import setup_logger, HandlerConfig
from microlog.handlers import AsyncConsoleHandler, AsyncRotatingFileHandler
from microlog.formatters import JSONFormatter, PrettyFormatter


def main():
    # Log dosyası yolu
    log_file = "app_multi.log"
    
    # Eğer eski log dosyası varsa sil
    if os.path.exists(log_file):
        os.remove(log_file)
    
    # Birden fazla handler ile logger oluştur
    # return_handlers=True ile handler'ları da alıyoruz (graceful shutdown için)
    logger, handlers = setup_logger(
        name="myapp",
        service_name="multi-handler-service",
        handlers=[
            # Console handler - renkli çıktı
            HandlerConfig(
                handler=AsyncConsoleHandler(),
                formatter=PrettyFormatter(
                    service_name="multi-handler-service",
                    use_colors=True
                )
            ),
            # File handler - JSON format
            HandlerConfig(
                handler=AsyncRotatingFileHandler(
                    filename=log_file,
                    max_bytes=10 * 1024 * 1024,  # 10MB
                    backup_count=5,
                    compress=True
                ),
                formatter=JSONFormatter(
                    service_name="multi-handler-service"
                )
            )
        ],
        return_handlers=True  # Handler'ları da döndür
    )
    
    print("Loglar hem console'a hem dosyaya yazılacak...")
    print()
    
    # Log mesajları
    logger.info("Uygulama başlatıldı")
    
    logger.info(
        "Kullanıcı işlemi başlatıldı",
        extra={
            "user_id": "usr-123",
            "action": "login",
            "ip_address": "192.168.1.100"
        }
    )
    
    logger.warning(
        "Rate limit uyarısı",
        extra={
            "user_id": "usr-123",
            "requests_per_minute": 95,
            "limit": 100
        }
    )
    
    logger.error(
        "İşlem başarısız",
        extra={
            "user_id": "usr-123",
            "error_code": "ERR-001",
            "retry_count": 3
        }
    )
    
    # Exception logging
    try:
        data = {"key": "value"}
        value = data["nonexistent"]
    except KeyError:
        logger.exception("Veri erişim hatası")
    
    # Graceful shutdown: Handler'ları kapat (queue'daki loglar flush edilir)
    # Not: atexit zaten handler'ları kapatıyor, ama manuel de yapabiliriz
    for handler in handlers:
        handler.stop()
    
    print()
    print(f"Console çıktısı yukarıda görüldü.")
    print(f"JSON formatındaki loglar '{log_file}' dosyasına yazıldı.")
    print()
    print("Not: return_handlers=True ile handler'ları aldık ve")
    print("     manuel olarak stop() çağırdık. Bu sayede time.sleep()")
    print("     gerekmeden tüm loglar yazıldı.")


if __name__ == "__main__":
    main()

