"""
Örnek: Trace Context ile Decorator

@with_trace decorator kullanımı.
Sync ve async fonksiyonlarda otomatik trace context.

Kullanım:
    python examples/trace/trace_with_decorator.py

Çıktı:
    Decorator ile sarmalanmış fonksiyonlar otomatik trace context alır.
"""

import asyncio
from microlog import setup_logger, get_current_context
from microlog.decorators import with_trace


# Sync fonksiyon - decorator ile
@with_trace(correlation_id="order-process")
def process_order(order_id: str, amount: float):
    """Sipariş işleme fonksiyonu"""
    logger = setup_logger("myapp", service_name="order-service")
    
    # Trace context otomatik olarak aktif
    ctx = get_current_context()
    logger.info(
        "Sipariş işleniyor",
        extra={
            "order_id": order_id,
            "amount": amount,
            "trace_id": ctx.trace_id if ctx else None
        }
    )
    
    # Simüle edilmiş işlem (gerçek uygulamada async işlem olurdu)
    import time
    time.sleep(0.1)
    
    logger.info("Sipariş tamamlandı", extra={"order_id": order_id})
    return {"status": "success", "order_id": order_id}


# Async fonksiyon - decorator ile
@with_trace(session_id="async-session")
async def async_process_data(data: dict):
    """Async veri işleme fonksiyonu"""
    logger = setup_logger("myapp", service_name="data-service")
    
    ctx = get_current_context()
    logger.info(
        "Async veri işleme başladı",
        extra={
            "data_size": len(data),
            "trace_id": ctx.trace_id if ctx else None,
            "session_id": ctx.session_id if ctx else None
        }
    )
    
    # Simüle edilmiş async işlem
    await asyncio.sleep(0.1)
    
    logger.info("Async veri işleme tamamlandı")
    return {"processed": True}


# Decorator olmadan fonksiyon
def process_without_trace(item: str):
    """Trace context olmadan işlem"""
    logger = setup_logger("myapp", service_name="no-trace-service")
    logger.info("Trace context olmadan işlem", extra={"item": item})


def main():
    logger, handlers = setup_logger("myapp", service_name="main-service", return_handlers=True)
    
    print("Trace Context ile Decorator Örneği")
    print("=" * 60)
    print()
    
    # 1. Sync fonksiyon - decorator ile
    print("1. Sync fonksiyon - @with_trace decorator ile:")
    result = process_order("ORD-123", 99.99)
    print(f"   Sonuç: {result}")
    print()
    
    # 2. Async fonksiyon - decorator ile
    print("2. Async fonksiyon - @with_trace decorator ile:")
    async def run_async():
        result = await async_process_data({"key": "value", "count": 42})
        return result
    
    result = asyncio.run(run_async())
    print(f"   Sonuç: {result}")
    print()
    
    # 3. Decorator olmadan
    print("3. Decorator olmadan:")
    process_without_trace("item-123")
    print()
    
    # 4. Manuel trace context ile
    print("4. Manuel trace context ile:")
    from microlog import trace
    
    with trace(correlation_id="manual-trace") as ctx:
        logger.info("Manuel trace context ile log")
        print(f"   Trace ID: {ctx.trace_id}")
    
    # Graceful shutdown: Handler'ları kapat (queue'daki loglar flush edilir)
    for handler in handlers:
        handler.stop()


if __name__ == "__main__":
    main()

