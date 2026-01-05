"""
MicroLog Metrics and Observability

Prometheus metrics integration for monitoring logging health.

Author: MicroLog Team
License: MIT
"""

import logging
import threading
import time
from typing import Dict, Optional

# Try to import prometheus_client (optional dependency)
try:
    from prometheus_client import Counter, Gauge, Histogram, CollectorRegistry, REGISTRY
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    # Create dummy classes if prometheus not available
    class Counter:
        def __init__(self, *args, **kwargs):
            pass
        def labels(self, *args, **kwargs):
            return self
        def inc(self, *args, **kwargs):
            pass
    
    class Gauge:
        def __init__(self, *args, **kwargs):
            pass
        def labels(self, *args, **kwargs):
            return self
        def set(self, *args, **kwargs):
            pass
        def inc(self, *args, **kwargs):
            pass
        def dec(self, *args, **kwargs):
            pass
    
    class Histogram:
        def __init__(self, *args, **kwargs):
            pass
        def labels(self, *args, **kwargs):
            return self
        def observe(self, *args, **kwargs):
            pass
    
    class CollectorRegistry:
        pass
    
    REGISTRY = None


class MetricsHandler(logging.Handler):
    """
    Prometheus metrics toplamak için logging handler.
    
    Log event'lerini metriğe dönüştürür:
    - logs_total: Log sayısı (level, service label'ları ile)
    - log_errors_total: Error log sayısı
    - log_handler_duration_seconds: Handler latency
    
    Example:
        >>> from microlog import setup_logger
        >>> from microlog.metrics import MetricsHandler
        >>> 
        >>> logger = setup_logger("myapp")
        >>> logger.addHandler(MetricsHandler(service_name="myapp"))
        >>> 
        >>> logger.info("Test log")  # Metric: logs_total{level="INFO",service="myapp"} 1
    """
    
    _instance: Optional['MetricsHandler'] = None
    _lock = threading.Lock()
    
    def __init__(
        self,
        service_name: str = "unknown",
        registry: Optional['CollectorRegistry'] = None
    ):
        """
        Args:
            service_name: Service adı (metric label için)
            registry: Custom Prometheus registry (default: global REGISTRY)
        """
        super().__init__()
        
        if not PROMETHEUS_AVAILABLE:
            # Prometheus yok, sessizce no-op
            self._enabled = False
            return
        
        self._enabled = True
        self.service_name = service_name
        self.registry = registry or REGISTRY
        
        # Metrics (singleton pattern - her metric bir kez oluşturulmalı)
        with MetricsHandler._lock:
            if MetricsHandler._instance is None:
                self._setup_metrics()
                MetricsHandler._instance = self
            else:
                # Mevcut instance'dan metrics'leri al
                existing = MetricsHandler._instance
                self.logs_total = existing.logs_total
                self.log_errors_total = existing.log_errors_total
                self.log_handler_duration = existing.log_handler_duration
                self.log_queue_size = existing.log_queue_size
    
    def _setup_metrics(self):
        """Prometheus metrics'lerini oluşturur."""
        # Total logs counter
        self.logs_total = Counter(
            'microlog_logs_total',
            'Total number of logs emitted',
            ['level', 'service'],
            registry=self.registry
        )
        
        # Error logs counter
        self.log_errors_total = Counter(
            'microlog_errors_total',
            'Total number of error/critical logs',
            ['service'],
            registry=self.registry
        )
        
        # Handler latency histogram
        self.log_handler_duration = Histogram(
            'microlog_handler_duration_seconds',
            'Time spent in log handler',
            ['handler', 'service'],
            registry=self.registry
        )
        
        # Queue size gauge (updated externally)
        self.log_queue_size = Gauge(
            'microlog_queue_size',
            'Current size of log queue',
            ['handler', 'service'],
            registry=self.registry
        )
    
    def emit(self, record: logging.LogRecord):
        """
        Log record'ı metriğe dönüştürür.
        
        Args:
            record: LogRecord instance
        """
        if not self._enabled:
            return
        
        try:
            start = time.time()
            
            # Total logs
            self.logs_total.labels(
                level=record.levelname,
                service=self.service_name
            ).inc()
            
            # Error logs (ERROR ve CRITICAL)
            if record.levelno >= logging.ERROR:
                self.log_errors_total.labels(
                    service=self.service_name
                ).inc()
            
            # Handler latency
            duration = time.time() - start
            self.log_handler_duration.labels(
                handler='metrics',
                service=self.service_name
            ).observe(duration)
            
        except Exception:
            # Metric hatalarını yoksay (logging'i bozmasın)
            self.handleError(record)


class QueueMetricsCollector:
    """
    AsyncHandler queue'larını monitor eder ve metrics toplar.
    
    Background thread olarak çalışır ve queue size'ları periyodik update eder.
    
    Example:
        >>> from microlog import AsyncRotatingFileHandler
        >>> from microlog.metrics import QueueMetricsCollector
        >>> 
        >>> handler = AsyncRotatingFileHandler(filename="app.log")
        >>> collector = QueueMetricsCollector(service_name="myapp")
        >>> collector.register_handler("file", handler)
        >>> collector.start()
        >>> 
        >>> # Queue metrics otomatik toplanır
        >>> # microlog_queue_size{handler="file",service="myapp"}
    """
    
    def __init__(
        self,
        service_name: str = "unknown",
        interval_seconds: float = 5.0,
        registry: Optional['CollectorRegistry'] = None
    ):
        """
        Args:
            service_name: Service adı
            interval_seconds: Metric update interval
            registry: Custom Prometheus registry
        """
        self.service_name = service_name
        self.interval_seconds = interval_seconds
        self.registry = registry or REGISTRY
        
        self._handlers: Dict[str, any] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        
        # Metrics
        if PROMETHEUS_AVAILABLE:
            self.queue_size_gauge = Gauge(
                'microlog_queue_size',
                'Current size of log queue',
                ['handler', 'service'],
                registry=self.registry
            )
        else:
            self.queue_size_gauge = None
    
    def register_handler(self, name: str, handler):
        """
        Handler'ı register eder (metrics için).
        
        Args:
            name: Handler adı (örn: "file", "smtp")
            handler: AsyncHandler instance
        """
        with self._lock:
            self._handlers[name] = handler
    
    def unregister_handler(self, name: str):
        """Handler'ı unregister eder."""
        with self._lock:
            self._handlers.pop(name, None)
    
    def start(self):
        """Background thread'i başlatır."""
        with self._lock:
            if not self._running and PROMETHEUS_AVAILABLE:
                self._running = True
                self._thread = threading.Thread(
                    target=self._collect_loop,
                    daemon=True,
                    name="QueueMetricsCollector"
                )
                self._thread.start()
    
    def stop(self):
        """Background thread'i durdurur."""
        with self._lock:
            self._running = False
            if self._thread:
                self._thread.join(timeout=2.0)
                self._thread = None
    
    def _collect_loop(self):
        """Background loop: queue size'ları periyodik toplar."""
        while self._running:
            try:
                with self._lock:
                    for name, handler in self._handlers.items():
                        # AsyncHandler'ın queue'suna eriş
                        if hasattr(handler, '_queue'):
                            qsize = handler._queue.qsize()
                            self.queue_size_gauge.labels(
                                handler=name,
                                service=self.service_name
                            ).set(qsize)
                
                time.sleep(self.interval_seconds)
                
            except Exception:
                # Sessizce devam et
                time.sleep(self.interval_seconds)


def setup_metrics(
    logger: logging.Logger,
    service_name: str = "unknown",
    registry: Optional['CollectorRegistry'] = None
) -> Optional[MetricsHandler]:
    """
    Logger'a metrics handler ekler (convenience function).
    
    Args:
        logger: Logger instance
        service_name: Service adı
        registry: Custom Prometheus registry
        
    Returns:
        MetricsHandler instance (veya None, prometheus yoksa)
        
    Example:
        >>> from microlog import setup_logger
        >>> from microlog.metrics import setup_metrics
        >>> 
        >>> logger = setup_logger("myapp")
        >>> setup_metrics(logger, service_name="myapp")
        >>> 
        >>> # Artık loglar otomatik metriğe dönüşür
    """
    if not PROMETHEUS_AVAILABLE:
        return None
    
    handler = MetricsHandler(service_name=service_name, registry=registry)
    handler.setLevel(logging.DEBUG)  # Tüm seviyeleri topla
    logger.addHandler(handler)
    
    return handler


__all__ = [
    "MetricsHandler",
    "QueueMetricsCollector",
    "setup_metrics",
    "PROMETHEUS_AVAILABLE",
]

