"""
Örnek: Yapılandırılmış Logging

Yapılandırılmış logging.
Extra alanlar best practices ve log aggregation hazırlığı.

Kullanım:
    python examples/production/structured_logging.py

Çıktı:
    Yapılandırılmış JSON loglar console'a ve dosyaya yazılır.
"""

import os
import time
from microlog import setup_logger, HandlerConfig
from microlog.handlers import AsyncConsoleHandler, AsyncRotatingFileHandler
from microlog.formatters import JSONFormatter


def process_order(order_id: str, user_id: str, amount: float):
    """Sipariş işleme fonksiyonu - yapılandırılmış logging örneği"""
    logger = setup_logger("order-processor", service_name="order-service")
    
    # Yapılandırılmış log - tüm önemli bilgiler extra alanlarda
    logger.info(
        "Sipariş işleme başlatıldı",
        extra={
            "order_id": order_id,
            "user_id": user_id,
            "amount": amount,
            "currency": "USD",
            "operation": "process_order",
            "component": "order-processor"
        }
    )
    
    # Simüle edilmiş işlem
    time.sleep(0.05)
    
    # İşlem tamamlandı - sonuç bilgileri ile
    logger.info(
        "Sipariş işleme tamamlandı",
        extra={
            "order_id": order_id,
            "user_id": user_id,
            "status": "completed",
            "duration_ms": 50,
            "operation": "process_order"
        }
    )
    
    return {"status": "success", "order_id": order_id}


def handle_api_request(request_id: str, method: str, path: str, status_code: int):
    """API request handler - yapılandırılmış logging örneği"""
    logger = setup_logger("api-server", service_name="api-service")
    
    # Request log - tüm HTTP bilgileri
    logger.info(
        "API request işlendi",
        extra={
            "request_id": request_id,
            "method": method,
            "path": path,
            "status_code": status_code,
            "operation": "handle_request",
            "component": "api-server"
        }
    )
    
    # Status code'a göre log seviyesi
    if status_code >= 500:
        logger.error(
            "API request hatası",
            extra={
                "request_id": request_id,
                "status_code": status_code,
                "error_type": "server_error"
            }
        )
    elif status_code >= 400:
        logger.warning(
            "API request uyarısı",
            extra={
                "request_id": request_id,
                "status_code": status_code,
                "error_type": "client_error"
            }
        )


def main():
    """Yapılandırılmış logging örnekleri"""
    
    # Log dosyası yolu
    log_file = "structured.log"
    
    # Eğer eski log dosyası varsa sil
    if os.path.exists(log_file):
        os.remove(log_file)
    
    # Yapılandırılmış logger - JSON format - return_handlers=True ile handler'ları da alıyoruz
    logger, handlers = setup_logger(
        name="structured-app",
        service_name="structured-service",
        handlers=[
            HandlerConfig(
                handler=AsyncRotatingFileHandler(
                    filename=log_file,
                    max_bytes=10 * 1024 * 1024,
                    backup_count=5,
                    compress=True
                ),
                formatter=JSONFormatter(
                    service_name="structured-service",
                    include_location=False
                )
            )
        ],
        return_handlers=True
    )
    
    print("Yapılandırılmış Logging Örneği")
    print("=" * 60)
    print()
    
    # 1. Sipariş işleme örneği
    print("1. Sipariş işleme - yapılandırılmış log:")
    process_order("ORD-123", "usr-456", 99.99)
    print()
    
    # 2. API request örneği
    print("2. API request - yapılandırılmış log:")
    handle_api_request("req-001", "POST", "/api/orders", 201)
    handle_api_request("req-002", "GET", "/api/orders/123", 404)
    handle_api_request("req-003", "POST", "/api/payments", 500)
    print()
    
    # 3. Best practices örneği
    print("3. Best practices - tutarlı alan isimleri:")
    logger.info(
        "İşlem başarılı",
        extra={
            "operation": "data_sync",
            "component": "sync-service",
            "duration_ms": 125,
            "records_processed": 1000,
            "status": "success"
        }
    )
    
    logger.warning(
        "Yavaş işlem tespit edildi",
        extra={
            "operation": "data_sync",
            "component": "sync-service",
            "duration_ms": 2500,
            "threshold_ms": 1000,
            "status": "slow"
        }
    )
    
    # Graceful shutdown: Handler'ları kapat (queue'daki loglar flush edilir)
    for handler in handlers:
        handler.stop()
    
    print(f"Yapılandırılmış loglar '{log_file}' dosyasına yazıldı.")
    print()
    print("Best Practices:")
    print("- Tutarlı alan isimleri kullanın (snake_case)")
    print("- Her log mesajına operation ve component ekleyin")
    print("- Durum bilgilerini status alanı ile belirtin")
    print("- Timing bilgilerini duration_ms ile ekleyin")


if __name__ == "__main__":
    main()

