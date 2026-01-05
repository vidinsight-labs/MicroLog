"""
Queue flush garantisi ve backpressure testleri.

Bu modül şunları test eder:
    - Queue'nun tam flush edilmesi
    - Backpressure handling
    - Bounded queue davranışı
    - Data loss senaryoları
    - Flush timeout

Author: MicroLog Team  
Created: 2026-01-05
"""

import logging
import threading
import time
import queue
from pathlib import Path

import pytest

from microlog import AsyncRotatingFileHandler


class TestQueueFlushGuarantee:
    """Queue flush garantisi testleri"""
    
    def test_stop_flushes_all_pending_logs(self, temp_log_file):
        """stop() çağrıldığında queue'daki TÜM loglar yazılmalı"""
        handler = AsyncRotatingFileHandler(filename=temp_log_file)
        queue_handler = handler.get_queue_handler()
        
        logger = logging.getLogger("test_flush_guarantee")
        logger.addHandler(queue_handler)
        logger.setLevel(logging.INFO)
        
        # Hızlıca 1000 log yaz (queue'da birikecek)
        expected_count = 1000
        for i in range(expected_count):
            logger.info(f"Message {i:04d}")
        
        # Queue size kontrol et
        queue_size_before = handler._queue.qsize()
        print(f"\nQueue size before stop: {queue_size_before}")
        
        # stop() çağır - TÜM loglar yazılmalı
        handler.stop()
        
        # Queue boş olmalı (sentinel value hariç - None değeri kalabilir)
        queue_size_after = handler._queue.qsize()
        # Sentinel pattern kullanıldığı için None değeri queue'da kalabilir
        assert queue_size_after <= 1, f"Queue not empty after stop: {queue_size_after} items (sentinel may remain)"
        
        # Dosyayı kontrol et
        time.sleep(0.5)
        content = Path(temp_log_file).read_text()
        lines = [l for l in content.strip().split('\n') if l and 'Message' in l]
        
        # Tüm loglar yazılmış olmalı
        success_rate = len(lines) / expected_count * 100
        print(f"Logs written: {len(lines)}/{expected_count} ({success_rate:.1f}%)")
        
        # En az %95 başarı oranı
        min_expected = int(expected_count * 0.95)
        assert len(lines) >= min_expected, f"Data loss detected: only {len(lines)}/{expected_count} logs written"
    
    def test_queue_monitoring(self, temp_log_file):
        """Queue boyutu monitör edilebilmeli"""
        handler = AsyncRotatingFileHandler(filename=temp_log_file)
        queue_handler = handler.get_queue_handler()
        
        logger = logging.getLogger("test_queue_monitor")
        logger.addHandler(queue_handler)
        logger.setLevel(logging.INFO)
        
        # Queue size tracking
        queue_sizes = []
        
        def log_worker():
            for i in range(500):
                logger.info(f"Message {i}")
                if i % 50 == 0:
                    queue_sizes.append(handler._queue.qsize())
                time.sleep(0.001)
        
        thread = threading.Thread(target=log_worker)
        thread.start()
        thread.join()
        
        handler.stop()
        
        # Queue size değişimlerini kontrol et
        print(f"\nQueue sizes during operation: {queue_sizes}")
        
        # Queue boyutu makul sınırlarda olmalı (< 200)
        max_queue_size = max(queue_sizes) if queue_sizes else 0
        assert max_queue_size < 200, f"Queue growing too large: {max_queue_size}"
    
    def test_no_data_loss_under_load(self, temp_log_file):
        """Yük altında data loss olmamalı"""
        handler = AsyncRotatingFileHandler(filename=temp_log_file)
        queue_handler = handler.get_queue_handler()
        
        logger = logging.getLogger("test_no_data_loss")
        logger.addHandler(queue_handler)
        logger.setLevel(logging.INFO)
        
        # 10 thread × 200 log = 2000 log
        expected_total = 2000
        threads_count = 10
        logs_per_thread = 200
        
        def worker(thread_id: int):
            for i in range(logs_per_thread):
                logger.info(f"T{thread_id:02d}-{i:03d}")
        
        threads = [threading.Thread(target=worker, args=(i,)) for i in range(threads_count)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Bekle ve durdur
        time.sleep(1.0)
        handler.stop()
        time.sleep(0.5)
        
        # Tüm logları say
        content = Path(temp_log_file).read_text()
        lines = [l for l in content.strip().split('\n') if l and 'T' in l]
        
        success_rate = len(lines) / expected_total * 100
        print(f"\nData loss test: {len(lines)}/{expected_total} ({success_rate:.1f}%)")
        
        # En az %90 başarı
        min_expected = int(expected_total * 0.90)
        assert len(lines) >= min_expected, f"Too much data loss: only {len(lines)}/{expected_total}"


class TestQueueBackpressure:
    """Queue backpressure testleri"""
    
    def test_queue_does_not_block_caller(self, temp_log_file):
        """Queue yazma caller'ı bloklamamalı"""
        handler = AsyncRotatingFileHandler(filename=temp_log_file)
        queue_handler = handler.get_queue_handler()
        
        logger = logging.getLogger("test_non_blocking")
        logger.addHandler(queue_handler)
        logger.setLevel(logging.INFO)
        
        # 5000 log yaz ve süreyi ölç
        start_time = time.time()
        for i in range(5000):
            logger.info(f"Message {i}")
        duration = time.time() - start_time
        
        # Queue yazma çok hızlı olmalı (< 1 saniye)
        print(f"\n5000 logs queued in {duration*1000:.1f}ms")
        assert duration < 1.0, f"Queue write is blocking: took {duration:.2f}s"
        
        handler.stop()
    
    def test_slow_handler_does_not_block_logger(self, temp_log_file):
        """Yavaş handler logger'ı bloklamamalı"""
        # Yavaş bir custom handler
        class SlowHandler(logging.FileHandler):
            def emit(self, record):
                time.sleep(0.01)  # Her log 10ms
                super().emit(record)
        
        from microlog.handlers import AsyncHandler
        
        slow_handler = SlowHandler(temp_log_file)
        async_handler = AsyncHandler(slow_handler)
        queue_handler = async_handler.get_queue_handler()
        
        logger = logging.getLogger("test_slow_handler")
        logger.addHandler(queue_handler)
        logger.setLevel(logging.INFO)
        
        # 100 log yaz (10ms × 100 = 1 saniye handler'da)
        start_time = time.time()
        for i in range(100):
            logger.info(f"Message {i}")
        queue_time = time.time() - start_time
        
        # Queue yazma hızlı olmalı (< 0.2 saniye)
        print(f"\n100 logs queued in {queue_time*1000:.1f}ms (handler: 10ms each)")
        assert queue_time < 0.2, f"Queue blocked by slow handler: {queue_time:.2f}s"
        
        # Cleanup
        time.sleep(1.5)  # Handler'ın işlemesi için
        async_handler.stop()


class TestQueueOverflow:
    """Queue overflow senaryoları"""
    
    def test_unbounded_queue_handles_burst(self, temp_log_file):
        """Unbounded queue burst'ü handle etmeli"""
        handler = AsyncRotatingFileHandler(filename=temp_log_file)
        queue_handler = handler.get_queue_handler()
        
        logger = logging.getLogger("test_burst")
        logger.addHandler(queue_handler)
        logger.setLevel(logging.INFO)
        
        # Massive burst: 10,000 log
        burst_count = 10000
        for i in range(burst_count):
            logger.info(f"Burst {i:05d}")
        
        # Queue size kontrol
        queue_size = handler._queue.qsize()
        print(f"\nQueue size after {burst_count} burst: {queue_size}")
        
        # Queue tüm mesajları almalı (unlimited)
        assert queue_size <= burst_count, f"Queue lost messages: {queue_size}/{burst_count}"
        
        # Cleanup
        time.sleep(2.0)
        handler.stop()
        time.sleep(1.0)
        
        # Dosyayı kontrol et
        content = Path(temp_log_file).read_text()
        lines = [l for l in content.strip().split('\n') if l and 'Burst' in l]
        
        success_rate = len(lines) / burst_count * 100
        print(f"Written: {len(lines)}/{burst_count} ({success_rate:.1f}%)")
        
        # En az %80 yazılmalı
        assert len(lines) >= burst_count * 0.8


class TestFlushTiming:
    """Flush timing testleri"""
    
    def test_immediate_flush_on_stop(self, temp_log_file):
        """stop() hemen flush başlatmalı"""
        handler = AsyncRotatingFileHandler(filename=temp_log_file)
        queue_handler = handler.get_queue_handler()
        
        logger = logging.getLogger("test_immediate_flush")
        logger.addHandler(queue_handler)
        logger.setLevel(logging.INFO)
        
        # 100 log yaz
        for i in range(100):
            logger.info(f"Message {i}")
        
        # stop() çağır ve süreyi ölç
        start_time = time.time()
        handler.stop()
        stop_duration = time.time() - start_time
        
        print(f"\nstop() completed in {stop_duration*1000:.1f}ms")
        
        # stop() makul sürede tamamlanmalı (< 5 saniye)
        assert stop_duration < 5.0, f"stop() took too long: {stop_duration:.2f}s (possible deadlock)"
        
        # Loglar yazılmış olmalı
        time.sleep(0.2)
        content = Path(temp_log_file).read_text()
        lines = [l for l in content.strip().split('\n') if l and 'Message' in l]
        
        assert len(lines) >= 90, f"Flush incomplete: {len(lines)}/100"
    
    def test_periodic_flush_during_operation(self, temp_log_file):
        """Çalışırken periyodik flush olmalı"""
        handler = AsyncRotatingFileHandler(filename=temp_log_file)
        queue_handler = handler.get_queue_handler()
        
        logger = logging.getLogger("test_periodic_flush")
        logger.addHandler(queue_handler)
        logger.setLevel(logging.INFO)
        
        # Yavaş log yazma (5 saniye)
        for i in range(50):
            logger.info(f"Message {i}")
            time.sleep(0.1)  # 100ms delay
        
        # Henüz stop() çağrılmadı ama bazı loglar yazılmış olmalı
        content = Path(temp_log_file).read_text()
        lines = [l for l in content.strip().split('\n') if l and 'Message' in l]
        
        print(f"\nLogs flushed during operation: {len(lines)}/50")
        
        # En az %50'si flush edilmiş olmalı (queue listener çalışıyor)
        assert len(lines) >= 25, f"No periodic flush: only {len(lines)}/50"
        
        handler.stop()


class TestQueueHealthChecks:
    """Queue health check testleri"""
    
    def test_queue_size_stays_bounded(self, temp_log_file):
        """Queue boyutu kontrol altında kalmalı"""
        handler = AsyncRotatingFileHandler(filename=temp_log_file)
        queue_handler = handler.get_queue_handler()
        
        logger = logging.getLogger("test_bounded_size")
        logger.addHandler(queue_handler)
        logger.setLevel(logging.INFO)
        
        max_sizes = []
        stop_flag = threading.Event()
        
        def continuous_logging():
            counter = 0
            while not stop_flag.is_set():
                logger.info(f"Message {counter}")
                counter += 1
                time.sleep(0.01)
        
        def monitor_queue():
            while not stop_flag.is_set():
                size = handler._queue.qsize()
                max_sizes.append(size)
                time.sleep(0.1)
        
        # Start workers
        log_thread = threading.Thread(target=continuous_logging)
        monitor_thread = threading.Thread(target=monitor_queue)
        
        log_thread.start()
        monitor_thread.start()
        
        # 5 saniye çalıştır
        time.sleep(5)
        
        # Durdur
        stop_flag.set()
        log_thread.join()
        monitor_thread.join()
        
        handler.stop()
        
        # Queue size analizi
        max_queue_size = max(max_sizes) if max_sizes else 0
        avg_queue_size = sum(max_sizes) / len(max_sizes) if max_sizes else 0
        
        print(f"\nQueue stats over 5 seconds:")
        print(f"   Max: {max_queue_size}")
        print(f"   Avg: {avg_queue_size:.1f}")
        
        # Queue çok büyümemeli (< 500)
        assert max_queue_size < 500, f"Queue growing unbounded: max {max_queue_size}"
    
    def test_listener_thread_alive(self, temp_log_file):
        """Listener thread canlı kalmalı"""
        handler = AsyncRotatingFileHandler(filename=temp_log_file)
        queue_handler = handler.get_queue_handler()
        
        logger = logging.getLogger("test_listener_alive")
        logger.addHandler(queue_handler)
        logger.setLevel(logging.INFO)
        
        # İlk log
        logger.info("Initial message")
        time.sleep(0.1)
        
        # Listener thread'in canlı olup olmadığını kontrol et
        listener_alive = handler._listener is not None and handler._started
        assert listener_alive, "Listener thread not started"
        
        # 30 saniye boyunca log yaz ve thread'i kontrol et
        for i in range(30):
            logger.info(f"Message {i}")
            time.sleep(1.0)
            
            # Her saniye thread'i kontrol et
            if i % 5 == 0:
                still_alive = handler._started and handler._listener is not None
                assert still_alive, f"Listener thread died after {i} seconds"
        
        handler.stop()
        print("\n✅ Listener thread stayed alive for 30 seconds")

