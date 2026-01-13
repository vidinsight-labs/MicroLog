"""
Örnek: File Logging

Dosyaya loglama, JSON format ve dosya rotation.
setup_file_logger kullanımı.

Kullanım:
    python examples/basic/file_logging.py

Çıktı:
    app.log dosyasına JSON formatında loglar yazılır.
    Dosya boyutu limitine ulaşınca otomatik rotation yapılır.
"""

import os
from microlog import setup_file_logger


def main():
    # Log dosyası yolu
    log_file = "app.log"
    
    # Eğer eski log dosyası varsa sil (temiz başlangıç için)
    if os.path.exists(log_file):
        os.remove(log_file)
    
    # JSON formatında file logger oluştur - return_handlers=True ile handler'ı da alıyoruz
    logger, handlers = setup_file_logger(
        name="myapp",
        service_name="data-service",
        filename=log_file,
        format_type="json",
        max_bytes=10 * 1024 * 1024,  # 10MB
        backup_count=5,
        compress=True,
        return_handlers=True
    )
    
    # Log mesajları
    logger.info("Uygulama başlatıldı")
    
    logger.info(
        "Veri işleme başladı",
        extra={
            "batch_id": "batch-001",
            "record_count": 1000,
            "source": "database"
        }
    )
    
    logger.warning(
        "Yavaş sorgu tespit edildi",
        extra={
            "query": "SELECT * FROM users",
            "duration_ms": 2500,
            "threshold_ms": 1000
        }
    )
    
    logger.error(
        "Veritabanı bağlantı hatası",
        extra={
            "host": "db.example.com",
            "port": 5432,
            "error": "Connection timeout"
        }
    )
    
    # Exception logging
    try:
        result = 10 / 0
    except ZeroDivisionError:
        logger.exception("Hesaplama hatası")
    
    # Graceful shutdown: Handler'ı kapat (queue'daki loglar flush edilir)
    for handler in handlers:
        handler.stop()
    
    print(f"Loglar '{log_file}' dosyasına yazıldı.")
    print("Dosyayı kontrol edebilirsiniz.")


if __name__ == "__main__":
    main()

