#!/usr/bin/env python3
"""
Dosya Logging Örneği - JSON ve Pretty formatlar
"""

import time
from pathlib import Path
from microlog import setup_file_logger, trace

print("=" * 60)
print("DOSYA LOGGING ÖRNEĞİ")
print("=" * 60)

# JSON formatında dosya logger
json_logger = setup_file_logger(
    name="json_logger",
    service_name="file-example",
    filename="logs/json_example.log",
    format_type="json"
)

print("JSON logger oluşturuldu: logs/json_example.log")

# Pretty formatında dosya logger
pretty_logger = setup_file_logger(
    name="pretty_logger",
    service_name="file-example",
    filename="logs/pretty_example.log",
    format_type="pretty"
)

print("Pretty logger oluşturuldu: logs/pretty_example.log")

# Log mesajları
with trace(correlation_id="file-test-001") as ctx:
    json_logger.info("JSON formatında log", extra={"test": True, "number": 42})
    pretty_logger.info("Pretty formatında log", extra={"test": True, "number": 42})
    
    json_logger.warning("Uyarı mesajı", extra={"level": "warning"})
    pretty_logger.warning("Uyarı mesajı", extra={"level": "warning"})
    
    json_logger.error("Hata mesajı", extra={"error_code": "E001"})
    pretty_logger.error("Hata mesajı", extra={"error_code": "E001"})

time.sleep(0.5)  # Logların yazılması için bekleme

# Dosyaları kontrol et
json_file = Path("logs/json_example.log")
pretty_file = Path("logs/pretty_example.log")

if json_file.exists():
    print(f"\n✅ JSON log dosyası oluşturuldu: {json_file.stat().st_size} bytes")
    print("\nİlk satır:")
    print(json_file.read_text().split('\n')[0][:200] + "...")

if pretty_file.exists():
    print(f"\n✅ Pretty log dosyası oluşturuldu: {pretty_file.stat().st_size} bytes")
    print("\nİlk satır:")
    print(pretty_file.read_text().split('\n')[0][:200] + "...")

print("\n✅ Dosya logging örneği tamamlandı!")

