# Detaylı Kullanım

Bu dokümantasyon, MicroLog'un tüm özelliklerini ve gelişmiş kullanım senaryolarını açıklar.

## İçindekiler

1. [Logger Kurulumu](#logger-kurulumu)
2. [Trace Context Detayları](#trace-context-detayları)
3. [Formatter'lar](#formatterlar)
4. [Handler'lar](#handlerlar)
5. [Decorator'lar](#decoratorlar)
6. [Production Senaryoları](#production-senaryoları)
7. [Gelişmiş Özellikler](#gelişmiş-özellikler)

---

## Logger Kurulumu

### setup_logger

```python
from microlog import setup_logger, JSONFormatter
import logging

# Basit kullanım
logger = setup_logger("myapp")

# Seviye belirterek
logger = setup_logger("myapp", level=logging.DEBUG)

# JSON formatında
logger = setup_logger(
    name="myapp",
    level=logging.INFO,
    formatter=JSONFormatter(service_name="myapp")
)

# Custom handler ile
from microlog import AsyncConsoleHandler
handler = AsyncConsoleHandler()
logger = setup_logger(
    name="myapp",
    handlers=[handler.get_queue_handler()]
)
```

**Parametreler:**
- `name`: Logger adı (default: "root")
- `level`: Log seviyesi (default: INFO)
- `service_name`: Servis adı (formatter'lara geçilir)
- `handlers`: Handler listesi (default: console handler)
- `formatter`: Formatter (default: PrettyFormatter)
- `add_trace_filter`: Trace context filter ekle (default: True)

### setup_file_logger

```python
from microlog import setup_file_logger

logger = setup_file_logger(
    name="myapp",
    filename="logs/app.log",
    max_bytes=10_000_000,  # 10 MB
    backup_count=5,
    compress=True,
    level=logging.INFO
)
```

**Parametreler:**
- `name`: Logger adı
- `filename`: Log dosyası yolu
- `max_bytes`: Rotation için maksimum dosya boyutu
- `backup_count`: Saklanacak backup dosya sayısı
- `compress`: Rotation sonrası gzip compression (default: False)
- `level`: Log seviyesi (default: INFO)

### setup_production_logger

```python
from microlog import setup_production_logger

logger = setup_production_logger(
    name="myapp",
    log_file="logs/production.log",
    level=logging.INFO
)
```

Production için optimize edilmiş kurulum (JSON format, file rotation, compression).

---

## Trace Context Detayları

### Trace Oluşturma

```python
from microlog import trace

# Basit trace
with trace(trace_id="req-123"):
    logger.info("İşlem")

# Tüm parametrelerle
with trace(
    trace_id="req-123",
    parent_span_id="span-456",
    correlation_id="corr-789",
    session_id="session-abc"
) as ctx:
    logger.info("İşlem")
    print(f"Span ID: {ctx.span_id}")
```

### Async Context (AsyncIO)

```python
import asyncio
from microlog import trace

async def process_request(request_id):
    async with trace(trace_id=request_id):
        logger.info("Async işlem başladı")
        await do_work()
        logger.info("Async işlem tamamlandı")

asyncio.run(process_request("req-123"))
```

### HTTP Header'lardan Trace

```python
from microlog import trace, from_headers

headers = {
    "X-Trace-ID": "trace-123",
    "X-Span-ID": "span-456",
    "X-Parent-Span-ID": "parent-789"
}

with trace(**from_headers(headers)):
    logger.info("İstek işleniyor")
```

### Trace Context Erişimi

```python
from microlog import trace, get_current_context

with trace(trace_id="req-123") as ctx:
    # Context bilgilerine erişim
    print(f"Trace ID: {ctx.trace_id}")
    print(f"Span ID: {ctx.span_id}")
    print(f"Parent Span ID: {ctx.parent_span_id}")
    
    # Veya get_current_context ile
    current = get_current_context()
    print(f"Current Trace ID: {current.trace_id}")
```

---

## Formatter'lar

### JSONFormatter

```python
from microlog import setup_logger, JSONFormatter
import logging

logger = setup_logger(
    name="myapp",
    formatter=JSONFormatter(
        service_name="myapp",
        include_extra=True,
        use_unix_timestamp=True
    )
)

logger.info("Mesaj", extra={"user_id": 123})
# Çıktı: {"timestamp": 1704067200, "level": "INFO", "message": "Mesaj", ...}
```

**Parametreler:**
- `service_name`: Servis adı
- `include_extra`: Extra field'ları dahil et (default: True)
- `use_unix_timestamp`: Unix timestamp kullan (default: False)
- `datefmt`: Tarih formatı

### PrettyFormatter

```python
from microlog import setup_logger, PrettyFormatter

logger = setup_logger(
    name="myapp",
    formatter=PrettyFormatter(service_name="myapp")
)

logger.info("Mesaj")
# Çıktı: [2024-01-01 12:00:00] INFO myapp: Mesaj
```

### CompactFormatter

```python
from microlog import setup_logger, CompactFormatter

logger = setup_logger(
    name="myapp",
    formatter=CompactFormatter()
)

logger.info("Mesaj")
# Çıktı: 12:00:00 INFO: Mesaj
```

### Custom Formatter

```python
from microlog.formatter import BaseFormatter
import json

class CustomFormatter(BaseFormatter):
    def format(self, record):
        return json.dumps({
            "time": self.format_time(record),
            "level": record.levelname,
            "msg": record.getMessage(),
            "custom": "value"
        })

logger = setup_logger("myapp", formatter=CustomFormatter())
```

---

## Handler'lar

### AsyncConsoleHandler

```python
from microlog import AsyncConsoleHandler, JSONFormatter
import logging

handler = AsyncConsoleHandler(level=logging.INFO)
handler.get_queue_handler().setFormatter(JSONFormatter())

logger = logging.getLogger("myapp")
logger.setLevel(logging.INFO)
logger.addHandler(handler.get_queue_handler())

handler.start()  # Async listener'ı başlat

# Kullanım
logger.info("Console'a yazıldı")

# Temizlik
handler.stop()
```

### AsyncRotatingFileHandler

```python
from microlog import AsyncRotatingFileHandler, JSONFormatter
import logging

handler = AsyncRotatingFileHandler(
    filename="logs/app.log",
    max_bytes=10_000_000,  # 10 MB
    backup_count=5,
    compress=True  # Gzip compression
)

formatter = JSONFormatter()
handler.get_queue_handler().setFormatter(formatter)

logger = logging.getLogger("myapp")
logger.setLevel(logging.INFO)
logger.addHandler(handler.get_queue_handler())

handler.start()

# Kullanım
logger.info("Dosyaya yazıldı")

# Temizlik (tüm pending loglar flush edilir)
handler.stop()
```

**Parametreler:**
- `filename`: Log dosyası yolu
- `max_bytes`: Rotation için maksimum dosya boyutu
- `backup_count`: Saklanacak backup dosya sayısı
- `compress`: Rotation sonrası gzip compression (default: False)
- `level`: Minimum log seviyesi (default: NOTSET)

### AsyncSMTPHandler

```python
from microlog import AsyncSMTPHandler, JSONFormatter
import logging

handler = AsyncSMTPHandler(
    mailhost=("smtp.example.com", 587),
    fromaddr="alerts@example.com",
    toaddrs=["admin@example.com"],
    subject="Uygulama Hatası",
    credentials=("user", "password"),
    rate_limit_seconds=300  # 5 dakikada bir email
)

formatter = JSONFormatter()
handler.get_queue_handler().setFormatter(formatter)

logger = logging.getLogger("myapp")
logger.setLevel(logging.ERROR)  # Sadece ERROR ve üzeri
logger.addHandler(handler.get_queue_handler())

handler.start()

# Sadece ERROR ve CRITICAL seviyelerinde email gönderilir
logger.error("Kritik hata!", exc_info=True)

handler.stop()
```

**Parametreler:**
- `mailhost`: SMTP sunucu adresi ve port
- `fromaddr`: Gönderen email adresi
- `toaddrs`: Alıcı email adresleri (liste)
- `subject`: Email konusu
- `credentials`: (username, password) tuple
- `rate_limit_seconds`: Email gönderme rate limit

### Multiple Handler

```python
from microlog import AsyncConsoleHandler, AsyncRotatingFileHandler, JSONFormatter
import logging

# Console handler (INFO ve üzeri)
console_handler = AsyncConsoleHandler(level=logging.INFO)
console_handler.get_queue_handler().setFormatter(JSONFormatter())

# File handler (WARNING ve üzeri)
file_handler = AsyncRotatingFileHandler(
    filename="logs/errors.log",
    level=logging.WARNING,
    max_bytes=10_000_000,
    backup_count=5
)
file_handler.get_queue_handler().setFormatter(JSONFormatter())

logger = logging.getLogger("myapp")
logger.setLevel(logging.INFO)
logger.addHandler(console_handler.get_queue_handler())
logger.addHandler(file_handler.get_queue_handler())

# Handler'ları başlat
console_handler.start()
file_handler.start()

# Kullanım
logger.info("Console ve dosyaya yazılır")
logger.warning("Console ve dosyaya yazılır")
logger.error("Console ve dosyaya yazılır")

# Temizlik
console_handler.stop()
file_handler.stop()
```

---

## Decorator'lar

### @log_function

```python
from microlog import log_function
import logging

@log_function(level=logging.INFO)
def calculate_total(items):
    """Toplam hesaplama"""
    total = sum(item.price for item in items)
    return total

# Otomatik olarak şunlar loglanır:
# - Fonksiyon çağrısı (parametrelerle)
# - Fonksiyon tamamlanması (return value ile)
```

**Parametreler:**
- `level`: Log seviyesi (default: INFO)
- `log_args`: Parametreleri logla (default: True)
- `log_result`: Return value'yu logla (default: True)

### @log_exception

```python
from microlog import log_exception
import logging

@log_exception(level=logging.ERROR)
def risky_operation():
    """Riskli işlem"""
    if random.random() < 0.5:
        raise ValueError("Rastgele hata")
    return "Başarılı"

# Exception oluşursa otomatik loglanır
```

**Parametreler:**
- `level`: Log seviyesi (default: ERROR)
- `reraise`: Exception'ı tekrar fırlat (default: True)

### @log_performance

```python
from microlog import log_performance
import logging

@log_performance(level=logging.INFO)
def slow_operation():
    """Yavaş işlem"""
    time.sleep(1)
    return "Tamamlandı"

# İşlem süresi otomatik loglanır
```

**Parametreler:**
- `level`: Log seviyesi (default: INFO)
- `threshold_seconds`: Minimum süre (default: 0)

### Kombine Kullanım

```python
from microlog import log_function, log_exception, log_performance

@log_function()
@log_exception()
@log_performance()
def complex_operation(data):
    """Karmaşık işlem"""
    # Tüm decorator'lar birlikte çalışır
    return process(data)
```

---

## Production Senaryoları

### API Servisi

```python
from flask import Flask, request, g
from microlog import setup_logger, trace, JSONFormatter
import logging
import uuid

app = Flask(__name__)

logger = setup_logger(
    name="api-service",
    level=logging.INFO,
    formatter=JSONFormatter(service_name="api-service")
)

@app.before_request
def before_request():
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    g.request_id = request_id

@app.route("/api/users/<user_id>")
def get_user(user_id):
    with trace(trace_id=g.request_id):
        logger.info("İstek alındı", extra={
            "user_id": user_id,
            "method": request.method,
            "path": request.path
        })
        # ... işlemler ...
        return jsonify({"status": "ok"})
```

### Microservice

```python
from microlog import setup_file_logger, trace

logger = setup_file_logger(
    name="order-service",
    filename="logs/order-service.log",
    max_bytes=50_000_000,
    backup_count=10,
    compress=True
)

def process_order(order_id):
    with trace(trace_id=f"order-{order_id}"):
        logger.info("Sipariş işleniyor", extra={"order_id": order_id})
        # ... işlemler ...
```

### Background Worker

```python
from microlog import AsyncRotatingFileHandler, JSONFormatter
import logging
import atexit

handler = AsyncRotatingFileHandler(
    filename="logs/worker.log",
    max_bytes=10_000_000,
    backup_count=5
)
handler.get_queue_handler().setFormatter(JSONFormatter(service_name="worker"))
handler.start()

logger = logging.getLogger("worker")
logger.addHandler(handler.get_queue_handler())
logger.setLevel(logging.INFO)

def process_job(job_id):
    with trace(trace_id=f"job-{job_id}"):
        logger.info("Job başladı", extra={"job_id": job_id})
        # ... işlemler ...

atexit.register(lambda: handler.stop())
```

### Long-Running Service

```python
from microlog import setup_production_logger
import signal
import sys

logger = setup_production_logger(
    name="daemon-service",
    log_file="logs/daemon.log",
    level=logging.INFO
)

def signal_handler(signum, frame):
    logger.info("Shutdown sinyali alındı", extra={"signal": signum})
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

while True:
    with trace(trace_id=generate_id()):
        logger.info("Döngü iterasyonu")
        # ... işlemler ...
```

---

## Gelişmiş Özellikler

### Handler Seviyesi Filtreleme

```python
from microlog import AsyncConsoleHandler, AsyncRotatingFileHandler

# Console'a sadece INFO ve üzeri
console_handler = AsyncConsoleHandler(level=logging.INFO)

# Dosyaya sadece WARNING ve üzeri
file_handler = AsyncRotatingFileHandler(
    filename="logs/errors.log",
    level=logging.WARNING
)
```

### Custom Filter

```python
import logging

class CustomFilter(logging.Filter):
    def filter(self, record):
        # Sadece belirli mesajları geçir
        return "important" in record.getMessage()

logger = logging.getLogger("myapp")
logger.addFilter(CustomFilter())
```

### Context Manager (log_context)

```python
from microlog import log_context

with log_context("Veritabanı işlemi", level=logging.INFO):
    logger.info("Bağlantı açıldı")
    # ... işlemler ...
    logger.info("İşlem tamamlandı")
```

---

## Sonraki Adımlar

- **[API Referansı](API_REFERANSI.md)** - Tüm fonksiyonlar ve parametreler
- **[Çalışma Mantığı](CALISMA_MANTIGI.md)** - İç mimari ve nasıl çalışıyor
- **[Davranış Şekli](DAVRANIS_SEKLI.md)** - Davranışlar ve best practices

