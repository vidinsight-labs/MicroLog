#!/usr/bin/env python3
"""
Temel Kullanım Örneği - MicroLog'un temel özellikleri
"""

from microlog import get_logger, trace, setup_console_logger

# Logger oluştur
logger = get_logger(service_name="basic-example")

print("=" * 60)
print("1. TEMEL LOGGING")
print("=" * 60)

logger.debug("Bu bir debug mesajı")
logger.info("Uygulama başlatıldı")
logger.warning("Bu bir uyarı mesajı")
logger.error("Bu bir hata mesajı (simüle)")

print("\n" + "=" * 60)
print("2. TRACE CONTEXT İLE LOGGING")
print("=" * 60)

with trace(correlation_id="order-123", user_id="usr-456") as ctx:
    logger.info("Sipariş işleniyor", extra={"order_id": "ORD-789", "amount": 99.99})
    logger.debug("Sipariş doğrulama adımı", extra={"step": "validation"})
    
    print(f"\nTrace ID: {ctx.trace_id}")
    print(f"Span ID: {ctx.span_id}")
    print(f"Headers: {ctx.headers()}")

print("\n" + "=" * 60)
print("3. NESTED TRACE CONTEXT")
print("=" * 60)

with trace(trace_id="parent-trace") as parent:
    logger.info("Parent işlem başladı")
    
    with trace(parent=parent) as child:
        logger.info("Child işlem", extra={"operation": "sub-task"})
        print(f"Child parent_span_id: {child.parent_span_id}")
    
    logger.info("Parent işlem devam ediyor")

print("\n" + "=" * 60)
print("4. EXTRA ALANLAR")
print("=" * 60)

logger.info(
    "Kullanıcı işlemi",
    extra={
        "user_id": "usr-123",
        "action": "login",
        "ip_address": "192.168.1.1",
        "timestamp": "2024-01-15T10:30:00Z"
    }
)

print("\n✅ Temel kullanım örneği tamamlandı!")

