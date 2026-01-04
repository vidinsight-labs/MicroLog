#!/usr/bin/env python3
"""
Gelişmiş Özellikler Örneği - Denenmemiş özellikler
"""

import sys
import logging
from io import StringIO
from microlog import get_logger, trace, setup_logger
from microlog.handlers import AsyncConsoleHandler
from microlog.formatter import JSONFormatter
from microlog.context import TraceContext

print("=" * 70)
print("GELİŞMİŞ ÖZELLİKLER ÖRNEĞİ")
print("=" * 70)

# 1. SplitStreamHandler - ERROR+ için stderr'e yönlendirme
print("\n" + "=" * 70)
print("1. SPLIT STREAM HANDLER (ERROR+ stderr'e)")
print("=" * 70)

stdout_capture = StringIO()
stderr_capture = StringIO()

handler = AsyncConsoleHandler(
    stream=stdout_capture,
    error_stream=stderr_capture,
    split_errors=True  # ERROR+ stderr'e
)
handler.handler.setFormatter(JSONFormatter(service_name="split-test"))

logger = logging.getLogger("split_test")
logger.addHandler(handler.get_queue_handler())
logger.setLevel(logging.DEBUG)

# Farklı seviyelerde loglar
logger.debug("Debug mesajı")
logger.info("Info mesajı")
logger.warning("Warning mesajı")
logger.error("Error mesajı")
logger.critical("Critical mesajı")

import time
time.sleep(0.5)  # Queue işlenmesi için

stdout_content = stdout_capture.getvalue()
stderr_content = stderr_capture.getvalue()

print(f"\n📤 STDOUT ({len(stdout_content)} bytes):")
print(stdout_content[:300] if stdout_content else "(boş)")

print(f"\n📥 STDERR ({len(stderr_content)} bytes):")
print(stderr_content[:300] if stderr_content else "(boş)")

handler.stop()

# 2. Unix Timestamp Format
print("\n" + "=" * 70)
print("2. UNIX TIMESTAMP FORMAT")
print("=" * 70)

handler2 = AsyncConsoleHandler()
formatter = JSONFormatter(
    service_name="unix-timestamp-test",
    timestamp_format="unix"  # Unix timestamp
)
handler2.handler.setFormatter(formatter)

logger2 = logging.getLogger("unix_test")
logger2.addHandler(handler2.get_queue_handler())
logger2.setLevel(logging.INFO)

logger2.info("Unix timestamp formatında log")

time.sleep(0.3)
handler2.stop()

# 3. include_extra=False
print("\n" + "=" * 70)
print("3. INCLUDE_EXTRA=FALSE")
print("=" * 70)

handler3 = AsyncConsoleHandler()
formatter3 = JSONFormatter(
    service_name="no-extra-test",
    include_extra=False  # Extra alanları ekleme
)
handler3.handler.setFormatter(formatter3)

logger3 = logging.getLogger("no_extra_test")
logger3.addHandler(handler3.get_queue_handler())
logger3.setLevel(logging.INFO)

logger3.info("Extra alanlar olmadan", extra={"user_id": "usr-123", "order_id": "ord-456"})

time.sleep(0.3)
handler3.stop()

# 4. HTTP Header'dan Trace Context
print("\n" + "=" * 70)
print("4. HTTP HEADER'DAN TRACE CONTEXT")
print("=" * 70)

# Simüle edilmiş HTTP request headers
request_headers = {
    "X-Trace-ID": "incoming-trace-123",
    "X-Span-ID": "incoming-span-456",
    "X-Correlation-ID": "order-789",
    "X-Session-ID": "session-abc"
}

print(f"Gelen request headers: {request_headers}")

# Header'lardan context oluştur
with trace(headers=request_headers) as ctx:
    logger4 = get_logger(service_name="http-header-test")
    logger4.info("Request işleniyor", extra={"endpoint": "/api/orders"})
    
    print(f"\nOluşturulan context:")
    print(f"  Trace ID: {ctx.trace_id}")
    print(f"  Span ID: {ctx.span_id}")
    print(f"  Parent Span ID: {ctx.parent_span_id}")
    print(f"  Correlation ID: {ctx.correlation_id}")
    print(f"  Session ID: {ctx.session_id}")
    
    # Child span oluştur
    with trace(parent=ctx) as child:
        logger4.info("Child işlem", extra={"operation": "sub-task"})
        print(f"\nChild context:")
        print(f"  Trace ID: {child.trace_id} (aynı olmalı)")
        print(f"  Span ID: {child.span_id} (yeni)")
        print(f"  Parent Span ID: {child.parent_span_id} (parent'ın span_id)")

# 5. Handler Level Filtering
print("\n" + "=" * 70)
print("5. HANDLER LEVEL FILTERING")
print("=" * 70)

# Sadece ERROR+ için handler
error_handler = AsyncConsoleHandler(level=logging.ERROR)
error_handler.handler.setFormatter(JSONFormatter(service_name="error-only"))

# Tüm seviyeler için handler
all_handler = AsyncConsoleHandler(level=logging.DEBUG)
all_handler.handler.setFormatter(JSONFormatter(service_name="all-levels"))

logger5 = logging.getLogger("level_filter_test")
logger5.addHandler(error_handler.get_queue_handler())
logger5.addHandler(all_handler.get_queue_handler())
logger5.setLevel(logging.DEBUG)

logger5.debug("Debug mesajı (sadece all_handler'da)")
logger5.info("Info mesajı (sadece all_handler'da)")
logger5.warning("Warning mesajı (sadece all_handler'da)")
logger5.error("Error mesajı (her iki handler'da)")
logger5.critical("Critical mesajı (her iki handler'da)")

time.sleep(0.5)
error_handler.stop()
all_handler.stop()

# 6. Multiple Handler Kombinasyonu
print("\n" + "=" * 70)
print("6. MULTIPLE HANDLER KOMBİNASYONU")
print("=" * 70)

from microlog.handlers import AsyncRotatingFileHandler
from microlog.formatter import PrettyFormatter, CompactFormatter

# Console (Pretty)
console_handler = AsyncConsoleHandler()
console_handler.handler.setFormatter(PrettyFormatter(service_name="multi-handler"))

# File (JSON)
file_handler = AsyncRotatingFileHandler(
    filename="logs/multi_handler.log",
    max_bytes=1024 * 1024  # 1MB
)
file_handler.handler.setFormatter(JSONFormatter(service_name="multi-handler"))

logger6 = logging.getLogger("multi_handler_test")
logger6.addHandler(console_handler.get_queue_handler())
logger6.addHandler(file_handler.get_queue_handler())
logger6.setLevel(logging.INFO)

with trace(correlation_id="multi-test") as ctx:
    logger6.info("Her iki handler'a yazılıyor", extra={"test": True})
    logger6.warning("Uyarı mesajı", extra={"level": "warning"})
    logger6.error("Hata mesajı", extra={"error": "test"})

time.sleep(0.5)

print(f"\n✅ Log dosyası oluşturuldu: logs/multi_handler.log")

console_handler.stop()
file_handler.stop()
file_handler.handler.close()

print("\n" + "=" * 70)
print("✅ TÜM GELİŞMİŞ ÖZELLİKLER TEST EDİLDİ")
print("=" * 70)

