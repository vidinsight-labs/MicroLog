#!/usr/bin/env python3
"""
Gzip Compression Örneği - Dosya sıkıştırma
"""

import time
from pathlib import Path
from microlog import setup_file_logger

print("=" * 70)
print("GZIP COMPRESSION ÖRNEĞİ")
print("=" * 70)

# Compression ile logger
compressed_logger = setup_file_logger(
    name="compressed_logger",
    service_name="compression-test",
    filename="logs/compressed.log",
    max_bytes=500,  # Küçük limit - hızlı rotation
    backup_count=3,
    compress=True,  # Gzip compression aktif
    format_type="json"
)

print("✅ Compression aktif logger oluşturuldu")
print("   - max_bytes: 500 bytes")
print("   - backup_count: 3")
print("   - compress: True")

# Compression olmadan logger
uncompressed_logger = setup_file_logger(
    name="uncompressed_logger",
    service_name="compression-test",
    filename="logs/uncompressed.log",
    max_bytes=500,
    backup_count=3,
    compress=False,  # Compression kapalı
    format_type="json"
)

print("\n✅ Compression kapalı logger oluşturuldu")

# Çok fazla log yaz (rotation tetiklemek için)
print("\n📝 Log yazılıyor (rotation tetiklemek için)...")

for i in range(100):
    compressed_logger.info(f"Compressed log message {i} " * 10)
    uncompressed_logger.info(f"Uncompressed log message {i} " * 10)

time.sleep(2.0)  # Rotation ve compression için bekleme

# Dosyaları kontrol et
compressed_dir = Path("logs")
compressed_files = list(compressed_dir.glob("compressed.log*"))
uncompressed_files = list(compressed_dir.glob("uncompressed.log*"))

print(f"\n📊 SONUÇLAR:")
print(f"\nCompressed dosyalar ({len(compressed_files)}):")
total_compressed = 0
for f in sorted(compressed_files):
    size = f.stat().st_size
    total_compressed += size
    is_gz = ".gz" in f.name
    print(f"  {f.name}: {size:,} bytes {'(gzip)' if is_gz else ''}")

print(f"\nUncompressed dosyalar ({len(uncompressed_files)}):")
total_uncompressed = 0
for f in sorted(uncompressed_files):
    size = f.stat().st_size
    total_uncompressed += size
    print(f"  {f.name}: {size:,} bytes")

if total_compressed > 0 and total_uncompressed > 0:
    compression_ratio = (1 - total_compressed / total_uncompressed) * 100
    print(f"\n💾 Sıkıştırma Oranı: {compression_ratio:.1f}%")
    print(f"   Compressed: {total_compressed:,} bytes")
    print(f"   Uncompressed: {total_uncompressed:,} bytes")

# Handler'ları durdur
for handler in compressed_logger.handlers:
    if hasattr(handler, 'stop'):
        handler.stop()
    if hasattr(handler, 'handler') and hasattr(handler.handler, 'close'):
        handler.handler.close()

for handler in uncompressed_logger.handlers:
    if hasattr(handler, 'stop'):
        handler.stop()
    if hasattr(handler, 'handler') and hasattr(handler.handler, 'close'):
        handler.handler.close()

print("\n✅ Compression örneği tamamlandı!")

