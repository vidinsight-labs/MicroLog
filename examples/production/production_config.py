"""
Örnek: Production Yapılandırması

Production yapılandırması.
JSON formatter, file rotation ve error handling.

Kullanım:
    python examples/production/production_config.py

Çıktı:
    app.log dosyasına JSON formatında loglar yazılır.
    Dosya rotation otomatik yapılır.
"""

import os
from microlog import setup_file_logger


def main():
    """Production logger yapılandırması"""
    
    # Log dosyası yolu
    log_file = "app_production.log"
    
    # Eğer eski log dosyası varsa sil (temiz başlangıç için)
    if os.path.exists(log_file):
        os.remove(log_file)
    
    # Production logger oluştur - return_handlers=True ile handler'ı da alıyoruz
    logger, handlers = setup_file_logger(
        name="production-app",
        service_name="production-service",
        filename=log_file,
        format_type="json",
        max_bytes=10 * 1024 * 1024,  # 10MB
        backup_count=10,
        compress=True,
        level=20,  # INFO level
        return_handlers=True
    )
    
    print("Production Logger Yapılandırması")
    print("=" * 60)
    print()
    print(f"Log dosyası: {log_file}")
    print("Format: JSON")
    print("Max dosya boyutu: 10MB")
    print("Backup sayısı: 10")
    print("Sıkıştırma: Aktif")
    print()
    
    # Production log mesajları
    logger.info("Uygulama başlatıldı", extra={
        "version": "1.0.0",
        "environment": "production",
        "host": "prod-server-01"
    })
    
    logger.info("Veritabanı bağlantısı kuruldu", extra={
        "db_host": "db.production.com",
        "db_name": "production_db",
        "connection_time_ms": 45
    })
    
    logger.warning("Yavaş sorgu tespit edildi", extra={
        "query": "SELECT * FROM orders WHERE status = ?",
        "duration_ms": 1250,
        "threshold_ms": 1000,
        "rows_returned": 5000
    })
    
    logger.error("Dış servis çağrısı başarısız", extra={
        "service": "payment-gateway",
        "endpoint": "/api/process",
        "status_code": 503,
        "retry_count": 3,
        "error": "Service unavailable"
    })
    
    # Exception logging
    try:
        result = 10 / 0
    except ZeroDivisionError:
        logger.exception("Kritik hata oluştu", extra={
            "component": "order-processor",
            "operation": "calculate_total"
        })
    
    # Graceful shutdown: Handler'ı kapat (queue'daki loglar flush edilir)
    for handler in handlers:
        handler.stop()
    
    print(f"Loglar '{log_file}' dosyasına yazıldı.")
    print("Dosyayı kontrol edebilirsiniz.")


if __name__ == "__main__":
    main()

