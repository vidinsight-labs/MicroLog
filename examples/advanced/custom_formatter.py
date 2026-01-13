"""
Örnek: Özel Formatter

Özel formatter oluşturma.
Yardımcı fonksiyonlar kullanımı ve custom format implementasyonu.

Kullanım:
    python examples/advanced/custom_formatter.py

Çıktı:
    Özel formatter ile formatlanmış log mesajları.
"""

import logging
from datetime import datetime
from microlog import setup_logger, HandlerConfig
from microlog.handlers import AsyncConsoleHandler
from microlog.formatters import get_extra_fields, get_record_timestamp


class CustomFormatter(logging.Formatter):
    """Özel formatter - minimal format"""
    
    def __init__(self, service_name: str = None):
        super().__init__()
        self.service_name = service_name
    
    def format(self, record: logging.LogRecord) -> str:
        """Özel format implementasyonu"""
        # Timestamp
        dt = get_record_timestamp(record, use_utc=True)
        timestamp = dt.strftime("%Y-%m-%d %H:%M:%S")
        
        # Level (kısaltılmış)
        level_map = {
            "DEBUG": "DBG",
            "INFO": "INF",
            "WARNING": "WRN",
            "ERROR": "ERR",
            "CRITICAL": "CRT"
        }
        level = level_map.get(record.levelname, record.levelname[:3])
        
        # Service
        service = self.service_name or record.name
        
        # Message
        message = record.getMessage()
        
        # Extra alanlar (yardımcı fonksiyon kullanımı)
        extras = get_extra_fields(record)
        extra_str = " ".join([f"{k}={v}" for k, v in extras.items()])
        
        # Format: [TIMESTAMP] LEVEL SERVICE: MESSAGE | extra
        line = f"[{timestamp}] {level} {service}: {message}"
        if extra_str:
            line += f" | {extra_str}"
        
        # Exception
        if record.exc_info:
            exc_text = self.formatException(record.exc_info)
            line += f"\n{exc_text}"
        
        return line


class CSVFormatter(logging.Formatter):
    """CSV format formatter"""
    
    def __init__(self, service_name: str = None):
        super().__init__()
        self.service_name = service_name
    
    def format(self, record: logging.LogRecord) -> str:
        """CSV format"""
        import csv
        from io import StringIO
        
        dt = get_record_timestamp(record, use_utc=True)
        timestamp = dt.isoformat()
        service = self.service_name or record.name
        level = record.levelname
        message = record.getMessage()
        
        # Extra alanları JSON string olarak ekle
        extras = get_extra_fields(record)
        import json
        extra_json = json.dumps(extras) if extras else ""
        
        # CSV format
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow([
            timestamp,
            level,
            service,
            message,
            extra_json
        ])
        
        return output.getvalue().strip()


def main():
    """Özel formatter örnekleri"""
    
    print("Özel Formatter Örneği")
    print("=" * 60)
    print()
    
    # Handler'ları toplamak için liste
    all_handlers = []
    
    # 1. Custom minimal formatter
    print("1. Custom Minimal Formatter:")
    logger1, handlers1 = setup_logger(
        name="custom-app",
        service_name="custom-service",
        handlers=[
            HandlerConfig(
                handler=AsyncConsoleHandler(),
                formatter=CustomFormatter(service_name="custom-service")
            )
        ],
        return_handlers=True
    )
    all_handlers.extend(handlers1)
    
    logger1.info("Minimal format log mesajı")
    logger1.warning("Uyarı mesajı", extra={"code": "W001"})
    logger1.error("Hata mesajı", extra={"error_code": "E001", "retry": 3})
    print()
    
    # 2. CSV formatter
    print("2. CSV Formatter:")
    logger2, handlers2 = setup_logger(
        name="csv-app",
        service_name="csv-service",
        handlers=[
            HandlerConfig(
                handler=AsyncConsoleHandler(),
                formatter=CSVFormatter(service_name="csv-service")
            )
        ],
        return_handlers=True
    )
    all_handlers.extend(handlers2)
    
    logger2.info("CSV format log mesajı", extra={"order_id": "ORD-123"})
    logger2.error("CSV format hata", extra={"error": "timeout"})
    print()
    
    # 3. Yardımcı fonksiyonlar kullanımı
    print("3. Yardımcı Fonksiyonlar:")
    from microlog.formatters import serialize_value
    
    # serialize_value örneği
    test_data = {
        "string": "value",
        "number": 42,
        "list": [1, 2, 3],
        "nested": {"key": "value"},
        "datetime": datetime.now()
    }
    
    serialized = serialize_value(test_data)
    print(f"   Serialize edilmiş data: {serialized}")
    print()
    
    # Graceful shutdown: Tüm handler'ları kapat (queue'daki loglar flush edilir)
    for handler in all_handlers:
        handler.stop()
    
    print("=" * 60)
    print("Örnek tamamlandı!")


if __name__ == "__main__":
    main()

