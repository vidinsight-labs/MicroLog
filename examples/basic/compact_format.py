"""
Örnek: Compact Format

CompactFormatter kullanımı.
Minimal tek satır format - dosya boyutu optimizasyonu.

Kullanım:
    python examples/basic/compact_format.py

Çıktı:
    app_compact.log dosyasına minimal formatında loglar yazılır.
    Format: LEVEL SERVICE MESSAGE key1=value1 key2=value2
"""

import os
from microlog import setup_file_logger


def main():
    # Log dosyası yolu
    log_file = "app_compact.log"
    
    # Eğer eski log dosyası varsa sil (temiz başlangıç için)
    if os.path.exists(log_file):
        os.remove(log_file)
    
    # Compact formatında file logger oluştur - return_handlers=True ile handler'ı da alıyoruz
    logger, handlers = setup_file_logger(
        name="myapp",
        service_name="compact-service",
        filename=log_file,
        format_type="compact",  # Compact format
        max_bytes=10 * 1024 * 1024,  # 10MB
        backup_count=5,
        compress=True,
        return_handlers=True
    )
    
    print("Compact Format Örneği")
    print("=" * 60)
    print()
    
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
    print()
    print("Compact Format Özellikleri:")
    print("- Minimal format (tek satır)")
    print("- Dosya boyutu optimizasyonu")
    print("- Boşluk içeren değerler için quote desteği")
    print("- Exception bilgisi (type ve kısa mesaj)")
    print()
    print("Dosyayı kontrol edebilirsiniz.")


if __name__ == "__main__":
    main()

