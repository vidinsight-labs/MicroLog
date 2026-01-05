#!/usr/bin/env python3
"""
Context Manager Örneği

Handler'lar için sync ve async context manager kullanımı.
"""

import asyncio
import logging
import os
import sys

# MicroLog'u import et
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from microlog import AsyncRotatingFileHandler, JSONFormatter, trace

print("=" * 60)
print("CONTEXT MANAGER EXAMPLE")
print("=" * 60)

# Örnek 1: Sync Context Manager
print("\n🔄 Örnek 1: Sync Context Manager")
print("-" * 60)

with AsyncRotatingFileHandler(filename="logs/context_sync.log", max_bytes=1000000) as handler:
    handler.get_queue_handler().setFormatter(JSONFormatter(service_name="sync-service"))
    
    logger = logging.getLogger("sync-logger")
    logger.setLevel(logging.INFO)
    logger.addHandler(handler.get_queue_handler())
    
    logger.info("Handler otomatik başlatıldı (with __enter__)")
    
    with trace(trace_id="sync-trace-001"):
        logger.info("Sync context manager içinde log")
        logger.warning("Bu log da yazılacak")

# __exit__ otomatik çağrıldı, handler.stop() yapıldı
print("✅ Sync context manager - handler otomatik durduruldu")

# Örnek 2: Async Context Manager
print("\n⚡ Örnek 2: Async Context Manager")
print("-" * 60)

async def async_logging_example():
    """Async context manager örneği."""
    async with AsyncRotatingFileHandler(filename="logs/context_async.log", max_bytes=1000000) as handler:
        handler.get_queue_handler().setFormatter(JSONFormatter(service_name="async-service"))
        
        logger = logging.getLogger("async-logger")
        logger.setLevel(logging.INFO)
        logger.addHandler(handler.get_queue_handler())
        
        logger.info("Handler otomatik başlatıldı (async with __aenter__)")
        
        # Simulate async operations
        for i in range(5):
            with trace(trace_id=f"async-trace-{i:03d}"):
                logger.info(f"Async operation {i}")
                await asyncio.sleep(0.1)  # Simulate async work
        
        logger.info("Async işlemler tamamlandı")
    
    # __aexit__ otomatik çağrıldı, handler.stop() yapıldı
    print("✅ Async context manager - handler otomatik durduruldu")

# Run async example
asyncio.run(async_logging_example())

# Örnek 3: Multiple Handlers with Context Managers
print("\n📚 Örnek 3: Multiple Handlers")
print("-" * 60)

from microlog import AsyncConsoleHandler, PrettyFormatter

with AsyncConsoleHandler() as console_handler, \
     AsyncRotatingFileHandler(filename="logs/context_multi.log", max_bytes=1000000) as file_handler:
    
    # Configure formatters
    console_handler.get_queue_handler().setFormatter(PrettyFormatter(service_name="multi-service"))
    file_handler.get_queue_handler().setFormatter(JSONFormatter(service_name="multi-service"))
    
    # Setup logger
    logger = logging.getLogger("multi-logger")
    logger.setLevel(logging.INFO)
    logger.addHandler(console_handler.get_queue_handler())
    logger.addHandler(file_handler.get_queue_handler())
    
    with trace(trace_id="multi-trace"):
        logger.info("Multiple handler'lar aynı anda")
        logger.warning("Console'a pretty, dosyaya JSON yazılıyor")
        logger.error("Her iki handler da bu mesajı alacak")

print("✅ Multiple handlers - hepsi otomatik durduruldu")

# Örnek 4: Error Handling in Context Manager
print("\n⚠️  Örnek 4: Error Handling")
print("-" * 60)

try:
    with AsyncRotatingFileHandler(filename="logs/context_error.log", max_bytes=1000000) as handler:
        logger = logging.getLogger("error-logger")
        logger.setLevel(logging.INFO)
        logger.addHandler(handler.get_queue_handler())
        
        logger.info("Before error")
        
        # Simulate error
        raise ValueError("Simulated error!")
        
except ValueError as e:
    print(f"✅ Hata yakalandı: {e}")
    print("   Handler yine de düzgün durduruldu (__exit__ garantisi)")

print("\n✅ Context manager örneği tamamlandı!")
print("\n📖 Avantajlar:")
print("  1. Otomatik cleanup - handler.start/stop() unutma riski yok")
print("  2. Exception safety - hata olsa bile kaynaklar temizlenir")
print("  3. Async/await desteği - modern Python best practices")
print("  4. Clean code - with block daha okunabilir")

