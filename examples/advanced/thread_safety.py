"""
Örnek: Thread Safety

Multi-threaded logging.
Thread-safe handler'lar ve concurrent logging örneği.

Kullanım:
    python examples/advanced/thread_safety.py

Çıktı:
    Birden fazla thread'den aynı anda logging yapılır.
"""

import time
import threading
from microlog import setup_logger, trace, get_current_context


def worker_thread(thread_id: int, logger):
    """Worker thread fonksiyonu"""
    # Her thread kendi trace context'i ile
    with trace(correlation_id=f"thread-{thread_id}") as ctx:
        logger.info(
            f"Thread {thread_id} başladı",
            extra={
                "thread_id": thread_id,
                "trace_id": ctx.trace_id,
                "span_id": ctx.span_id
            }
        )
        
        # Simüle edilmiş işlem
        for i in range(3):
            time.sleep(0.01)
            logger.info(
                f"Thread {thread_id} - işlem {i+1}",
                extra={
                    "thread_id": thread_id,
                    "iteration": i+1,
                    "trace_id": ctx.trace_id
                }
            )
        
        logger.info(
            f"Thread {thread_id} tamamlandı",
            extra={
                "thread_id": thread_id,
                "trace_id": ctx.trace_id
            }
        )


def concurrent_logging():
    """Eşzamanlı logging"""
    logger = setup_logger("thread-app", service_name="thread-service")
    
    # Birden fazla thread oluştur
    threads = []
    for i in range(5):
        thread = threading.Thread(
            target=worker_thread,
            args=(i, logger)
        )
        threads.append(thread)
        thread.start()
    
    # Tüm thread'lerin bitmesini bekle
    for thread in threads:
        thread.join()
    
    logger.info("Tüm thread'ler tamamlandı")


def shared_logger_test():
    """Paylaşılan logger testi"""
    logger = setup_logger("shared-app", service_name="shared-service")
    
    def worker(worker_id: int):
        for i in range(5):
            logger.info(
                f"Worker {worker_id} - mesaj {i+1}",
                extra={"worker_id": worker_id, "message_num": i+1}
            )
            time.sleep(0.005)
    
    # 10 worker thread
    threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
    
    for thread in threads:
        thread.start()
    
    for thread in threads:
        thread.join()
    
    logger.info("Paylaşılan logger testi tamamlandı")


def trace_context_thread_safety():
    """Trace context thread safety testi"""
    logger = setup_logger("trace-thread-app", service_name="trace-thread-service")
    
    def worker_with_trace(worker_id: int):
        # Her thread kendi trace context'i
        with trace(correlation_id=f"worker-{worker_id}") as ctx:
            current = get_current_context()
            assert current is not None
            assert current.trace_id == ctx.trace_id
            
            logger.info(
                f"Worker {worker_id} trace context ile",
                extra={
                    "worker_id": worker_id,
                    "trace_id": ctx.trace_id,
                    "span_id": ctx.span_id
                }
            )
    
    threads = [threading.Thread(target=worker_with_trace, args=(i,)) for i in range(5)]
    
    for thread in threads:
        thread.start()
    
    for thread in threads:
        thread.join()
    
    logger.info("Trace context thread safety testi tamamlandı")


def main():
    """Thread safety örnekleri"""
    # Ana logger oluştur - handler'ları toplamak için
    main_logger, handlers = setup_logger("thread-main", service_name="thread-service", return_handlers=True)
    
    print("Thread Safety Örneği")
    print("=" * 60)
    print()
    
    # 1. Eşzamanlı logging
    print("1. Eşzamanlı Logging (5 thread):")
    concurrent_logging()
    print()
    
    # 2. Paylaşılan logger testi
    print("2. Paylaşılan Logger Testi (10 worker):")
    shared_logger_test()
    print()
    
    # 3. Trace context thread safety
    print("3. Trace Context Thread Safety:")
    trace_context_thread_safety()
    print()
    
    # Graceful shutdown: Handler'ları kapat (queue'daki loglar flush edilir)
    # Not: concurrent_logging, shared_logger_test, trace_context_thread_safety
    #      içindeki logger'lar atexit ile otomatik kapanacak
    for handler in handlers:
        handler.stop()
    
    print("=" * 60)
    print("Örnek tamamlandı!")
    print()
    print("Thread Safety Özellikleri:")
    print("- Handler'lar thread-safe")
    print("- Her thread kendi trace context'ine sahip")
    print("- Concurrent logging güvenli")
    print("- Queue-based async handler'lar thread-safe")


if __name__ == "__main__":
    main()

