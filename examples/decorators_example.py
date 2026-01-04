#!/usr/bin/env python3
"""
Decorator Örnekleri - Otomatik logging
"""

import time
from microlog import get_logger
from microlog.decorators import log_function, log_exception, log_performance, log_context

logger = get_logger(service_name="decorator-example")

print("=" * 60)
print("1. @log_function DECORATOR")
print("=" * 60)

@log_function(logger=logger, log_args=True, log_result=True)
def process_order(order_id: str, amount: float):
    """Sipariş işleme fonksiyonu"""
    return {"status": "processed", "order_id": order_id, "amount": amount}

result = process_order("ORD-123", 99.99)
print(f"Sonuç: {result}")

print("\n" + "=" * 60)
print("2. @log_exception DECORATOR")
print("=" * 60)

@log_exception(logger=logger, reraise=True)
def risky_operation(value: int):
    """Risky operation"""
    if value < 0:
        raise ValueError("Negatif değer kabul edilmez!")
    return value * 2

try:
    risky_operation(-5)
except ValueError as e:
    print(f"Yakalanan hata: {e}")

print("\n" + "=" * 60)
print("3. @log_performance DECORATOR")
print("=" * 60)

@log_performance(logger=logger, threshold=0.1)  # 100ms'den uzun sürenleri logla
def slow_operation():
    """Yavaş işlem"""
    time.sleep(0.15)  # 150ms
    return "Tamamlandı"

@log_performance(logger=logger, threshold=0.1)
def fast_operation():
    """Hızlı işlem"""
    time.sleep(0.05)  # 50ms - threshold altında
    return "Tamamlandı"

slow_operation()  # Loglanmalı
fast_operation()  # Loglanmamalı (threshold altında)

print("\n" + "=" * 60)
print("4. log_context CONTEXT MANAGER")
print("=" * 60)

with log_context("Batch işleme", logger=logger):
    time.sleep(0.1)
    logger.info("İşlem 1 tamamlandı")
    logger.info("İşlem 2 tamamlandı")

print("\n✅ Decorator örnekleri tamamlandı!")

