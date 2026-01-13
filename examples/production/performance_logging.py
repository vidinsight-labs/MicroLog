"""
Örnek: Performance Logging

Performance metrikleri.
Timing bilgileri ve resource usage logging.

Kullanım:
    python examples/production/performance_logging.py

Çıktı:
    Performance metrikleri ile loglar yazılır.
"""

import os
import time
from contextlib import contextmanager
from microlog import setup_file_logger


@contextmanager
def log_performance(operation: str, logger):
    """Performance logging context manager"""
    start_time = time.time()
    start_memory = _get_memory_usage()
    
    try:
        yield
    finally:
        duration_ms = (time.time() - start_time) * 1000
        end_memory = _get_memory_usage()
        memory_delta = end_memory - start_memory
        
        logger.info(
            "İşlem tamamlandı",
            extra={
                "operation": operation,
                "duration_ms": round(duration_ms, 2),
                "memory_start_mb": round(start_memory, 2),
                "memory_end_mb": round(end_memory, 2),
                "memory_delta_mb": round(memory_delta, 2),
                "status": "success"
            }
        )


def _get_memory_usage():
    """Bellek kullanımını MB cinsinden döndürür"""
    try:
        import psutil
        import os
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024
    except ImportError:
        # psutil yoksa simüle edilmiş değer
        return 0.0


def process_large_dataset(dataset_size: int):
    """Büyük veri seti işleme - performance logging ile"""
    logger = setup_file_logger(
        name="performance-tracker",
        service_name="performance-service",
        filename="performance.log",
        format_type="json"
    )
    
    with log_performance("process_large_dataset", logger):
        logger.info(
            "Veri seti işleme başladı",
            extra={
                "operation": "process_large_dataset",
                "dataset_size": dataset_size,
                "estimated_duration_ms": dataset_size * 0.1
            }
        )
        
        # Simüle edilmiş işlem
        time.sleep(dataset_size * 0.001)
        
        logger.info(
            "Veri seti işleme tamamlandı",
            extra={
                "operation": "process_large_dataset",
                "dataset_size": dataset_size,
                "records_processed": dataset_size
            }
        )


def database_query(query: str, params: dict):
    """Veritabanı sorgusu - performance logging ile"""
    logger = setup_file_logger(
        name="performance-tracker",
        service_name="performance-service",
        filename="performance.log",
        format_type="json"
    )
    
    start_time = time.time()
    
    logger.info(
        "Veritabanı sorgusu başlatıldı",
        extra={
            "operation": "database_query",
            "query": query,
            "params": params
        }
    )
    
    # Simüle edilmiş sorgu
    time.sleep(0.05)
    
    duration_ms = (time.time() - start_time) * 1000
    
    # Yavaş sorgu kontrolü
    if duration_ms > 100:
        logger.warning(
            "Yavaş sorgu tespit edildi",
            extra={
                "operation": "database_query",
                "query": query,
                "duration_ms": round(duration_ms, 2),
                "threshold_ms": 100
            }
        )
    else:
        logger.info(
            "Veritabanı sorgusu tamamlandı",
            extra={
                "operation": "database_query",
                "query": query,
                "duration_ms": round(duration_ms, 2),
                "rows_returned": 42
            }
        )


def api_request(url: str, method: str):
    """API isteği - performance logging ile"""
    logger = setup_file_logger(
        name="performance-tracker",
        service_name="performance-service",
        filename="performance.log",
        format_type="json"
    )
    
    start_time = time.time()
    
    logger.info(
        "API isteği başlatıldı",
        extra={
            "operation": "api_request",
            "url": url,
            "method": method
        }
    )
    
    # Simüle edilmiş API çağrısı
    time.sleep(0.1)
    
    duration_ms = (time.time() - start_time) * 1000
    status_code = 200
    
    logger.info(
        "API isteği tamamlandı",
        extra={
            "operation": "api_request",
            "url": url,
            "method": method,
            "status_code": status_code,
            "duration_ms": round(duration_ms, 2),
            "response_size_bytes": 1024
        }
    )


def main():
    """Performance logging örnekleri"""
    
    # Log dosyası yolu
    log_file = "performance.log"
    
    # Eğer eski log dosyası varsa sil
    if os.path.exists(log_file):
        os.remove(log_file)
    
    # Ana logger oluştur - return_handlers=True ile handler'ları da alıyoruz
    logger, handlers = setup_file_logger(
        name="performance-tracker",
        service_name="performance-service",
        filename=log_file,
        format_type="json",
        return_handlers=True
    )
    
    print("Performance Logging Örneği")
    print("=" * 60)
    print()
    
    # 1. Büyük veri seti işleme
    print("1. Büyük veri seti işleme:")
    process_large_dataset(100)
    print()
    
    # 2. Veritabanı sorgusu
    print("2. Veritabanı sorgusu:")
    database_query("SELECT * FROM orders WHERE status = ?", {"status": "pending"})
    print()
    
    # 3. Yavaş sorgu
    print("3. Yavaş sorgu (uyarı):")
    time.sleep(0.15)  # Yavaş sorgu simülasyonu
    database_query("SELECT * FROM large_table", {})
    print()
    
    # 4. API isteği
    print("4. API isteği:")
    api_request("https://api.example.com/orders", "POST")
    print()
    
    # 5. Context manager ile performance logging
    print("5. Context manager ile performance logging:")
    with log_performance("batch_processing", logger):
        logger.info("Batch işleme başladı", extra={"batch_size": 1000})
        time.sleep(0.1)
        logger.info("Batch işleme tamamlandı", extra={"records_processed": 1000})
    print()
    
    # Graceful shutdown: Handler'ı kapat (queue'daki loglar flush edilir)
    # Not: process_large_dataset ve database_query içindeki logger'lar atexit ile otomatik kapanacak
    for handler in handlers:
        handler.stop()
    
    print(f"Performance logları '{log_file}' dosyasına yazıldı.")
    print()
    print("Performance Logging Özellikleri:")
    print("- Timing bilgileri (duration_ms) otomatik eklenir")
    print("- Yavaş işlemler otomatik tespit edilir")
    print("- Resource usage (memory) takip edilir")
    print("- JSON format log aggregation sistemleri için hazır")


if __name__ == "__main__":
    main()

