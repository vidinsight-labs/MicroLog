"""
Örnek: Async Tasks

Asyncio task'ları ve concurrent logging.
Async decorator kullanımı.

Kullanım:
    python examples/async/async_tasks.py

Çıktı:
    Async task'lar ve decorator ile otomatik trace context.
"""

import asyncio
from microlog import setup_logger, get_current_context
from microlog.decorators import with_trace


# Async fonksiyon - decorator ile
@with_trace(correlation_id="async-task-process")
async def process_data(data: dict):
    """Veri işleme fonksiyonu"""
    logger = setup_logger("async-app", service_name="data-service")
    
    ctx = get_current_context()
    logger.info(
        "Veri işleme başladı",
        extra={
            "data_size": len(data),
            "trace_id": ctx.trace_id if ctx else None
        }
    )
    
    # Simüle edilmiş işlem
    await asyncio.sleep(0.1)
    
    processed = {k: v * 2 for k, v in data.items()}
    
    logger.info("Veri işleme tamamlandı", extra={"processed_count": len(processed)})
    return processed


@with_trace(session_id="async-session")
async def fetch_data(source: str):
    """Veri çekme fonksiyonu"""
    logger = setup_logger("async-app", service_name="fetch-service")
    
    ctx = get_current_context()
    logger.info(
        "Veri çekiliyor",
        extra={
            "source": source,
            "trace_id": ctx.trace_id if ctx else None,
            "session_id": ctx.session_id if ctx else None
        }
    )
    
    # Simüle edilmiş async fetch
    await asyncio.sleep(0.15)
    
    data = {"key1": 10, "key2": 20, "key3": 30}
    
    logger.info("Veri çekildi", extra={"source": source, "items_count": len(data)})
    return data


async def process_with_tasks():
    """Task'lar ile işlem"""
    logger = setup_logger("async-app", service_name="task-service")
    
    from microlog import trace
    
    async with trace(correlation_id="task-batch-001") as ctx:
        logger.info("Task batch başlatıldı")
        
        # Task'lar oluştur
        task1 = asyncio.create_task(fetch_data("database"))
        task2 = asyncio.create_task(fetch_data("api"))
        
        # Task'ları bekle
        data1 = await task1
        data2 = await task2
        
        logger.info("Tüm veriler çekildi")
        
        # Verileri işle
        task3 = asyncio.create_task(process_data(data1))
        task4 = asyncio.create_task(process_data(data2))
        
        results = await asyncio.gather(task3, task4)
        
        logger.info(
            "Tüm işlemler tamamlandı",
            extra={
                "results_count": len(results),
                "trace_id": ctx.trace_id
            }
        )
        
        return results


async def concurrent_with_trace():
    """Eşzamanlı işlemler trace context ile"""
    logger = setup_logger("async-app", service_name="concurrent-service")
    
    from microlog import trace
    
    async with trace(correlation_id="concurrent-batch") as parent_ctx:
        logger.info("Eşzamanlı batch başlatıldı")
        
        # Birden fazla async işlem
        async def worker(worker_id: int):
            # Child span oluştur
            async with trace(parent=parent_ctx) as child_ctx:
                logger.info(
                    f"Worker {worker_id} başladı",
                    extra={
                        "worker_id": worker_id,
                        "trace_id": child_ctx.trace_id,
                        "span_id": child_ctx.span_id,
                        "parent_span_id": child_ctx.parent_span_id
                    }
                )
                
                await asyncio.sleep(0.1)
                
                logger.info(f"Worker {worker_id} tamamlandı")
                return f"worker-{worker_id}-result"
        
        # Eşzamanlı worker'lar
        workers = [worker(i) for i in range(5)]
        results = await asyncio.gather(*workers)
        
        logger.info(
            "Eşzamanlı batch tamamlandı",
            extra={
                "results_count": len(results),
                "trace_id": parent_ctx.trace_id
            }
        )
        
        return results


def main():
    """Ana fonksiyon"""
    # Ana logger oluştur - handler'ları toplamak için
    main_logger, handlers = setup_logger("async-main", service_name="async-service", return_handlers=True)
    
    print("Async Tasks Örneği")
    print("=" * 60)
    print()
    
    # 1. Decorator ile async fonksiyon
    print("1. Decorator ile async fonksiyon:")
    result = asyncio.run(process_data({"a": 1, "b": 2}))
    print(f"   Sonuç: {result}")
    print()
    
    # 2. Task'lar ile işlem
    print("2. Task'lar ile işlem:")
    results = asyncio.run(process_with_tasks())
    print(f"   Sonuç sayısı: {len(results)}")
    print()
    
    # 3. Eşzamanlı işlemler trace context ile
    print("3. Eşzamanlı işlemler trace context ile:")
    results = asyncio.run(concurrent_with_trace())
    print(f"   Worker sonuçları: {len(results)}")
    print()
    
    # Graceful shutdown: Handler'ları kapat (queue'daki loglar flush edilir)
    # Not: Diğer fonksiyonlardaki logger'lar atexit ile otomatik kapanacak
    for handler in handlers:
        handler.stop()
    
    print("=" * 60)
    print("Örnek tamamlandı!")


if __name__ == "__main__":
    main()

