#!/usr/bin/env python3
"""
Async Context Manager Örneği - trace() async desteği
"""

import asyncio
from microlog import get_logger, trace

logger = get_logger(service_name="async-example")

print("=" * 60)
print("ASYNC CONTEXT MANAGER ÖRNEĞİ")
print("=" * 60)

async def async_operation(operation_id: str):
    """Async işlem"""
    async with trace(correlation_id=operation_id) as ctx:
        logger.info(f"Async işlem başladı: {operation_id}")
        await asyncio.sleep(0.1)
        logger.info(f"Async işlem tamamlandı: {operation_id}")
        return ctx.trace_id

async def main():
    """Ana async fonksiyon"""
    print("\n1. Tek Async İşlem")
    print("-" * 60)
    trace_id = await async_operation("OP-001")
    print(f"Trace ID: {trace_id}")
    
    print("\n2. Paralel Async İşlemler")
    print("-" * 60)
    tasks = [
        async_operation(f"OP-{i:03d}")
        for i in range(1, 6)
    ]
    trace_ids = await asyncio.gather(*tasks)
    print(f"Tamamlanan işlemler: {len(trace_ids)}")
    print(f"Trace ID'ler: {trace_ids[:3]}...")  # İlk 3'ü göster

if __name__ == "__main__":
    asyncio.run(main())
    print("\n✅ Async context manager örneği tamamlandı!")

