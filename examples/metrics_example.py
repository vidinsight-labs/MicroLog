#!/usr/bin/env python3
"""
Metrics ve Observability Örneği

Prometheus metrics ile logging monitoring.
"""

import logging
import os
import sys
import time

# MicroLog'u import et
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from microlog import (
    setup_logger,
    trace,
    setup_metrics,
    PROMETHEUS_AVAILABLE,
    MetricsHandler,
    QueueMetricsCollector
)

print("=" * 60)
print("METRICS & OBSERVABILITY EXAMPLE")
print("=" * 60)

# Prometheus kontrolü
if not PROMETHEUS_AVAILABLE:
    print("\n⚠️  WARNING: prometheus_client not installed!")
    print("Install with: pip install prometheus-client")
    print("\nMetrics will be no-op (silent fallback)")
else:
    print("\n✅ prometheus_client available")

# Örnek 1: Basic Metrics Setup
print("\n📊 Örnek 1: Basic Metrics Setup")
print("-" * 60)

logger = setup_logger("metrics-app", level=logging.DEBUG)

# Metrics handler ekle
metrics_handler = setup_metrics(logger, service_name="metrics-app")

if metrics_handler:
    print("✅ Metrics handler eklendi")
else:
    print("⚠️  Metrics handler eklenemedi (prometheus yok)")

# Test logs - metrics toplanacak
logger.debug("Debug log - metric: logs_total{level=DEBUG}")
logger.info("Info log - metric: logs_total{level=INFO}")
logger.warning("Warning log - metric: logs_total{level=WARNING}")
logger.error("Error log - metric: logs_total{level=ERROR} + errors_total")
logger.critical("Critical log - metric: logs_total{level=CRITICAL} + errors_total")

print("✅ 5 log yazıldı, metrics toplandı")

# Örnek 2: Trace Context ile Metrics
print("\n🔍 Örnek 2: Trace Context ile Metrics")
print("-" * 60)

for i in range(10):
    with trace(trace_id=f"trace-{i:03d}"):
        logger.info(f"Traced log {i}")

print("✅ 10 traced log yazıldı")

# Örnek 3: Queue Metrics Collector
print("\n📈 Örnek 3: Queue Metrics Collector")
print("-" * 60)

if PROMETHEUS_AVAILABLE:
    from microlog import AsyncRotatingFileHandler
    
    # File handler oluştur
    file_handler = AsyncRotatingFileHandler(
        filename="logs/metrics_test.log",
        max_bytes=1000000
    )
    file_handler.start()
    
    # Queue metrics collector
    collector = QueueMetricsCollector(service_name="metrics-app")
    collector.register_handler("file", file_handler)
    collector.start()
    
    print("✅ Queue metrics collector başlatıldı")
    
    # Log burst - queue size değişecek
    logger2 = logging.getLogger("burst-logger")
    logger2.addHandler(file_handler.get_queue_handler())
    logger2.setLevel(logging.INFO)
    
    print("  Burst logging: 100 log/sec...")
    for i in range(100):
        logger2.info(f"Burst log {i}")
    
    time.sleep(2.0)  # Metrics collector'ın toplaması için bekle
    
    print("✅ Queue metrics toplandı")
    
    # Cleanup
    collector.stop()
    file_handler.stop()
else:
    print("⚠️  Prometheus yok, queue metrics atlandı")

# Örnek 4: Metrics Export (HTTP Endpoint)
print("\n🌐 Örnek 4: Metrics HTTP Endpoint")
print("-" * 60)

if PROMETHEUS_AVAILABLE:
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    
    # Metrics'leri text formatına çevir
    metrics_output = generate_latest().decode('utf-8')
    
    print("Prometheus metrics (örnek):")
    print("-" * 40)
    # İlk 20 satır göster
    for line in metrics_output.split('\n')[:20]:
        if line and not line.startswith('#'):
            print(f"  {line}")
    
    print("  ...")
    print("-" * 40)
    print("\n💡 Production'da bu metrics HTTP endpoint'ten expose edilir:")
    print("   GET /metrics -> prometheus scrape eder")
    
    # HTTP server örneği (commented out)
    print("\n📝 HTTP Server Örneği:")
    print("""
from prometheus_client import start_http_server

# Metrics endpoint'i başlat (port 8000)
start_http_server(8000)

# Şimdi Prometheus bu endpoint'i scrape edebilir:
# curl http://localhost:8000/metrics
""")
else:
    print("⚠️  Prometheus yok, metrics export atlandı")

# Özet
print("\n" + "=" * 60)
print("METRICS ÖZETİ")
print("=" * 60)

if PROMETHEUS_AVAILABLE:
    print("""
✅ Toplanan Metrics:
  1. microlog_logs_total{level, service}      - Toplam log sayısı
  2. microlog_errors_total{service}           - Error/critical log sayısı
  3. microlog_handler_duration_seconds{...}   - Handler latency
  4. microlog_queue_size{handler, service}    - Queue size

🔧 Production Setup:
  1. pip install prometheus-client
  2. from prometheus_client import start_http_server
  3. start_http_server(8000)
  4. Prometheus config: scrape_configs -> targets: ['app:8000']

📊 Grafana Dashboard:
  - Log rate (logs/sec)
  - Error rate (errors/sec)
  - Handler latency (p50, p95, p99)
  - Queue backlog (qsize over time)
""")
else:
    print("""
⚠️  Prometheus client yüklü değil

📦 Kurulum:
  pip install prometheus-client

✅ Kurulum sonrası tüm metrics otomatik toplanacak
""")

print("\n✅ Metrics örneği tamamlandı!")

