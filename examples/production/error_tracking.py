"""
Örnek: Error Tracking

Exception logging ve error tracking.
Stack trace formatlama ve error aggregation.

Kullanım:
    python examples/production/error_tracking.py

Çıktı:
    Exception'lar detaylı şekilde loglanır ve error tracking için hazırlanır.
"""

import os
import time
from microlog import setup_file_logger


def risky_operation(data: dict):
    """Riskli işlem - exception oluşturabilir"""
    if "key" not in data:
        raise KeyError(f"Required key 'key' not found in data: {data}")
    
    if data["key"] == 0:
        raise ValueError("Division by zero would occur")
    
    return 100 / data["key"]


def process_with_error_handling(data: dict):
    """Error handling ile işlem"""
    logger = setup_file_logger(
        name="error-tracker",
        service_name="error-service",
        filename="errors.log",
        format_type="json"
    )
    
    try:
        result = risky_operation(data)
        logger.info(
            "İşlem başarılı",
            extra={
                "operation": "risky_operation",
                "result": result,
                "input_data": data
            }
        )
        return result
        
    except KeyError as e:
        logger.error(
            "Eksik veri hatası",
            extra={
                "operation": "risky_operation",
                "error_type": "KeyError",
                "error_message": str(e),
                "input_data": data
            },
            exc_info=True
        )
        raise
        
    except ValueError as e:
        logger.error(
            "Geçersiz değer hatası",
            extra={
                "operation": "risky_operation",
                "error_type": "ValueError",
                "error_message": str(e),
                "input_data": data
            },
            exc_info=True
        )
        raise
        
    except Exception as e:
        logger.exception(
            "Beklenmeyen hata",
            extra={
                "operation": "risky_operation",
                "error_type": type(e).__name__,
                "input_data": data
            }
        )
        raise


def main():
    """Error tracking örnekleri"""
    
    # Log dosyası yolu
    log_file = "errors.log"
    
    # Eğer eski log dosyası varsa sil
    if os.path.exists(log_file):
        os.remove(log_file)
    
    logger, handlers = setup_file_logger(
        name="error-tracker",
        service_name="error-service",
        filename=log_file,
        format_type="json",
        return_handlers=True
    )
    
    print("Error Tracking Örneği")
    print("=" * 60)
    print()
    
    # 1. KeyError örneği
    print("1. KeyError - eksik veri:")
    try:
        process_with_error_handling({"value": 10})
    except KeyError:
        pass
    print()
    
    # 2. ValueError örneği
    print("2. ValueError - geçersiz değer:")
    try:
        process_with_error_handling({"key": 0})
    except ValueError:
        pass
    print()
    
    # 3. Başarılı işlem
    print("3. Başarılı işlem:")
    try:
        result = process_with_error_handling({"key": 5})
        print(f"   Sonuç: {result}")
    except Exception:
        pass
    print()
    
    # 4. Nested exception
    print("4. Nested exception:")
    try:
        try:
            result = 10 / 0
        except ZeroDivisionError:
            logger.exception("İç exception", extra={"level": "inner"})
            raise ValueError("Dış exception") from None
    except ValueError:
        logger.exception("Dış exception", extra={"level": "outer"})
    print()
    
    # 5. Exception with context
    print("5. Exception with context:")
    try:
        data = {"key": "invalid"}
        result = int(data["key"])
    except (KeyError, ValueError) as e:
        logger.exception(
            "Veri dönüşüm hatası",
            extra={
                "operation": "data_conversion",
                "input_data": data,
                "error_type": type(e).__name__,
                "error_message": str(e)
            }
        )
    print()
    
    # Graceful shutdown: Handler'ı kapat (queue'daki loglar flush edilir)
    for handler in handlers:
        handler.stop()
    
    print(f"Error logları '{log_file}' dosyasına yazıldı.")
    print()
    print("Error Tracking Özellikleri:")
    print("- Exception type ve message loglanır")
    print("- Stack trace otomatik eklenir")
    print("- Context bilgileri (operation, input_data) eklenir")
    print("- JSON format log aggregation sistemleri için hazır")


if __name__ == "__main__":
    main()

