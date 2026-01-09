"""
Örnek: Async Temel Kullanım

Async fonksiyonlarda logging.
async with trace() kullanımı ve async handler'lar.

Kullanım:
    python examples/async/async_basic.py

Çıktı:
    Async fonksiyonlarda log mesajları ve trace context çalışır.
"""

import asyncio
from microlog import setup_logger, trace, get_current_context


async def async_operation(name: str, duration: float):
    """Async işlem simülasyonu"""
    logger = setup_logger("async-app", service_name="async-service")
    
    ctx = get_current_context()
    logger.info(
        f"Async işlem başladı: {name}",
        extra={
            "operation": name,
            "trace_id": ctx.trace_id if ctx else None
        }
    )
    
    # Simüle edilmiş async işlem
    await asyncio.sleep(duration)
    
    logger.info(
        f"Async işlem tamamlandı: {name}",
        extra={
            "operation": name,
            "duration": duration
        }
    )
    
    return f"{name} completed"


async def async_with_trace():
    """Async trace context kullanımı"""
    logger = setup_logger("async-app", service_name="async-service")
    
    # Async trace context
    async with trace(correlation_id="async-req-123") as ctx:
        logger.info("Async trace context başlatıldı")
        
        # Async işlemler
        await async_operation("task-1", 0.1)
        await async_operation("task-2", 0.05)
        
        logger.info(
            "Tüm async işlemler tamamlandı",
            extra={"trace_id": ctx.trace_id}
        )


async def concurrent_operations():
    """Eşzamanlı async işlemler"""
    logger = setup_logger("async-app", service_name="async-service")
    
    async with trace(correlation_id="concurrent-req-456") as ctx:
        logger.info("Eşzamanlı işlemler başlatıldı")
        
        # Eşzamanlı çalıştır
        tasks = [
            async_operation(f"task-{i}", 0.1)
            for i in range(3)
        ]
        
        results = await asyncio.gather(*tasks)
        
        logger.info(
            "Eşzamanlı işlemler tamamlandı",
            extra={
                "results_count": len(results),
                "trace_id": ctx.trace_id
            }
        )
        
        return results


def main():
    """Ana fonksiyon"""
    # Ana logger oluştur - handler'ları toplamak için
    main_logger, handlers = setup_logger("async-main", service_name="async-service", return_handlers=True)
    
    print("Async Temel Kullanım Örneği")
    print("=" * 60)
    print()
    
    # 1. Basit async işlem
    print("1. Basit async işlem:")
    asyncio.run(async_operation("simple-task", 0.05))
    print()
    
    # 2. Async trace context
    print("2. Async trace context:")
    asyncio.run(async_with_trace())
    print()
    
    # 3. Eşzamanlı işlemler
    print("3. Eşzamanlı async işlemler:")
    results = asyncio.run(concurrent_operations())
    print(f"   Sonuçlar: {results}")
    print()
    
    # Graceful shutdown: Handler'ları kapat (queue'daki loglar flush edilir)
    # Not: Diğer fonksiyonlardaki logger'lar atexit ile otomatik kapanacak
    for handler in handlers:
        handler.stop()
    
    print("=" * 60)
    print("Örnek tamamlandı!")


if __name__ == "__main__":
    main()

