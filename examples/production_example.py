#!/usr/bin/env python3
"""
Production Örneği - Gerçek dünya senaryosu
"""

import time
from microlog import setup_production_logger, trace, get_logger
from microlog.decorators import log_function, log_exception

# Production logger: Console + File (JSON)
logger = setup_production_logger(
    name="order-service",
    service_name="order-service",
    console=True,
    file_path="logs/production.log",
    json_format=True
)

print("=" * 60)
print("PRODUCTION ÖRNEĞİ - Sipariş İşleme Servisi")
print("=" * 60)

@log_function(logger=logger, log_args=True)
@log_exception(logger=logger)
def validate_order(order_id: str, amount: float, user_id: str):
    """Sipariş doğrulama"""
    if amount <= 0:
        raise ValueError(f"Geçersiz tutar: {amount}")
    if not user_id:
        raise ValueError("Kullanıcı ID gerekli")
    
    logger.info("Sipariş doğrulandı", extra={"order_id": order_id})
    return True

@log_function(logger=logger)
@log_exception(logger=logger)
def process_payment(order_id: str, amount: float):
    """Ödeme işleme"""
    logger.info("Ödeme işleniyor", extra={"order_id": order_id, "amount": amount})
    time.sleep(0.1)  # Simüle edilmiş işlem
    logger.info("Ödeme başarılı", extra={"order_id": order_id})
    return {"transaction_id": "TXN-123", "status": "success"}

@log_function(logger=logger)
def send_confirmation(order_id: str, email: str):
    """Onay emaili gönder"""
    logger.info("Onay emaili gönderiliyor", extra={"order_id": order_id, "email": email})
    return True

def process_order(order_id: str, amount: float, user_id: str, email: str):
    """Ana sipariş işleme fonksiyonu"""
    with trace(
        correlation_id=order_id,
        user_id=user_id,
        order_id=order_id
    ) as ctx:
        logger.info("Sipariş işleme başladı", extra={
            "order_id": order_id,
            "amount": amount,
            "trace_id": ctx.trace_id
        })
        
        # 1. Doğrulama
        validate_order(order_id, amount, user_id)
        
        # 2. Ödeme
        payment_result = process_payment(order_id, amount)
        
        # 3. Onay
        send_confirmation(order_id, email)
        
        logger.info("Sipariş başarıyla işlendi", extra={
            "order_id": order_id,
            "transaction_id": payment_result["transaction_id"]
        })
        
        return {"status": "success", "trace_id": ctx.trace_id}

# Senaryo 1: Başarılı sipariş
print("\n📦 Senaryo 1: Başarılı Sipariş")
print("-" * 60)
result1 = process_order(
    order_id="ORD-001",
    amount=99.99,
    user_id="usr-123",
    email="user@example.com"
)
print(f"Sonuç: {result1}")

# Senaryo 2: Hatalı sipariş (negatif tutar)
print("\n❌ Senaryo 2: Hatalı Sipariş (Negatif Tutar)")
print("-" * 60)
try:
    process_order(
        order_id="ORD-002",
        amount=-10.0,  # Hatalı!
        user_id="usr-456",
        email="user2@example.com"
    )
except ValueError as e:
    print(f"Hata yakalandı: {e}")

# Senaryo 3: Eksik kullanıcı ID
print("\n❌ Senaryo 3: Eksik Kullanıcı ID")
print("-" * 60)
try:
    process_order(
        order_id="ORD-003",
        amount=50.0,
        user_id="",  # Hatalı!
        email="user3@example.com"
    )
except ValueError as e:
    print(f"Hata yakalandı: {e}")

time.sleep(1.0)  # Logların yazılması için

print("\n✅ Production örneği tamamlandı!")
print(f"📄 Log dosyası: logs/production.log")

