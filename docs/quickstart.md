# MicroLog Quick Start Guide

MicroLog, Python için yüksek performanslı asenkron logging kütüphanesidir. Bu kılavuz, hızlıca başlamanız için gerekli bilgileri içerir.

## Kurulum

```bash
pip install microlog
```

veya kaynak koddan:

```bash
git clone https://github.com/yourusername/MicroLog.git
cd MicroLog
pip install -e .
```

## Hızlı Başlangıç

### 1. Basit Kullanım

En basit kullanım şekli:

```python
from microlog import setup_logger

# Logger oluştur
logger = setup_logger("myapp")

# Log yaz
logger.info("Uygulama başlatıldı")
logger.warning("Dikkat: Yüksek bellek kullanımı")
logger.error("Bir hata oluştu")
```

**Çıktı:**
```
14:32:01 │ INFO     │ myapp            │ Uygulama başlatıldı
14:32:02 │ WARNING  │ myapp            │ Dikkat: Yüksek bellek kullanımı
14:32:03 │ ERROR    │ myapp            │ Bir hata oluştu
```

### 2. Console Logger (Renkli Çıktı)

Geliştirme ortamı için renkli console çıktısı:

```python
from microlog import setup_console_logger

logger = setup_console_logger(
    name="myapp",
    service_name="order-service",
    use_colors=True
)

logger.info("Sipariş oluşturuldu", extra={"order_id": "ORD-123"})
logger.error("Ödeme başarısız", extra={"error_code": "PAY-001"})
```

### 3. File Logger (JSON Format)

Production ortamı için dosyaya JSON formatında loglama:

```python
from microlog import setup_file_logger

logger = setup_file_logger(
    name="myapp",
    filename="app.log",
    format_type="json",
    max_bytes=10 * 1024 * 1024,  # 10MB
    backup_count=5
)

logger.info("İşlem tamamlandı", extra={
    "user_id": "usr-456",
    "duration_ms": 125
})
```

**app.log çıktısı:**
```json
{"timestamp":"2025-01-07T14:32:01.123456+00:00","level":"INFO","service":"myapp","message":"İşlem tamamlandı","user_id":"usr-456","duration_ms":125}
```

### 4. Trace Context ile Loglama

Distributed tracing için trace context kullanımı:

```python
from microlog import setup_logger, trace

logger = setup_logger("myapp")

# Trace context ile işlem
with trace(correlation_id="req-123", user_id="usr-456") as ctx:
    logger.info("İstek alındı")
    
    # trace_id ve span_id otomatik eklenir
    logger.info("İşlem başlatıldı")
    
    # Child span oluştur
    with trace(parent=ctx) as child:
        logger.info("Alt işlem tamamlandı")
    
    logger.info("İşlem tamamlandı")
```

**Çıktı (trace bilgileri otomatik eklenir):**
```json
{"timestamp":"...","level":"INFO","service":"myapp","message":"İstek alındı","trace_id":"abc123...","span_id":"def456...","correlation_id":"req-123","user_id":"usr-456"}
```

### 5. Decorator ile Trace

Fonksiyonlara otomatik trace context ekleme:

```python
from microlog import setup_logger
from microlog.decorators import with_trace

logger = setup_logger("myapp")

@with_trace(correlation_id="order-789")
def process_order(order_id: str):
    logger.info(f"Sipariş işleniyor: {order_id}")
    # trace_id ve correlation_id otomatik eklenir
    return "success"

# Async fonksiyonlar için de çalışır
@with_trace(session_id="session-123")
async def async_process(data):
    logger.info("Async işlem başladı")
    await do_work()
    return "done"
```

### 6. Özel Handler ve Formatter

Gelişmiş yapılandırma:

```python
from microlog import setup_logger, HandlerConfig
from microlog.handlers import AsyncConsoleHandler, AsyncRotatingFileHandler
from microlog.formatters import JSONFormatter, PrettyFormatter

logger = setup_logger(
    name="myapp",
    handlers=[
        # Console - renkli çıktı
        HandlerConfig(
            handler=AsyncConsoleHandler(),
            formatter=PrettyFormatter(service_name="myapp", use_colors=True)
        ),
        # File - JSON format
        HandlerConfig(
            handler=AsyncRotatingFileHandler(
                filename="app.log",
                max_bytes=10 * 1024 * 1024,
                backup_count=5
            ),
            formatter=JSONFormatter(service_name="myapp")
        )
    ]
)

logger.info("Log hem console'a hem dosyaya yazılır")
```

### 7. Exception Loglama

Exception'ları detaylı loglama:

```python
from microlog import setup_logger

logger = setup_logger("myapp")

try:
    result = risky_operation()
except Exception:
    # Exception detayları otomatik eklenir
    logger.exception("İşlem başarısız oldu")
```

**Çıktı:**
```json
{
  "timestamp": "...",
  "level": "ERROR",
  "service": "myapp",
  "message": "İşlem başarısız oldu",
  "exception": {
    "type": "ValueError",
    "message": "Invalid input",
    "traceback": "Traceback (most recent call last):\n..."
  }
}
```

## Format Tipleri

### JSON Formatter

Production ve log aggregation için:

```python
from microlog import setup_file_logger

logger = setup_file_logger(
    name="myapp",
    filename="app.log",
    format_type="json"
)
```

### Pretty Formatter

Geliştirme için renkli, okunabilir format:

```python
from microlog import setup_console_logger

logger = setup_console_logger(
    name="myapp",
    use_colors=True
)
```

### Compact Formatter

Minimal tek satır format:

```python
from microlog import setup_file_logger

logger = setup_file_logger(
    name="myapp",
    filename="app.log",
    format_type="compact"
)
```

## Handler Yönetimi

### Handler'ı Durdurma

Uygulama kapanırken handler'ları düzgün kapatmak:

```python
from microlog import setup_logger
from microlog.handlers import AsyncRotatingFileHandler

handler = AsyncRotatingFileHandler(filename="app.log")
logger = setup_logger("myapp", handlers=[HandlerConfig(handler=handler)])

# ... log yazma işlemleri ...

# Uygulama kapanırken
handler.stop()  # Queue'daki tüm loglar yazılır
```

### Context Manager Kullanımı

Otomatik cleanup için:

```python
from microlog.handlers import AsyncRotatingFileHandler

with AsyncRotatingFileHandler(filename="app.log") as handler:
    logger.addHandler(handler.get_queue_handler())
    logger.info("Log yazıldı")
    # Handler otomatik kapanır
```

## Trace Context Yönetimi

### Manuel Context Oluşturma

```python
from microlog.context import TraceContext, set_current_context, get_current_context

# Context oluştur
ctx = TraceContext(
    trace_id="custom-trace-123",
    correlation_id="req-456",
    session_id="session-789"
)

# Aktif yap
set_current_context(ctx)

# Kullan
logger.info("Log mesajı")  # trace_id otomatik eklenir

# Temizle
set_current_context(None)
```

### HTTP Header'lardan Context

```python
from microlog import trace

# HTTP request'ten header'ları al
headers = request.headers  # {"X-Trace-Id": "...", "X-Span-Id": "..."}

with trace(headers=headers) as ctx:
    logger.info("İstek işleniyor")
    # Parent trace_id korunur, yeni span oluşturulur
```

### Context'i HTTP Header'a Dönüştürme

```python
from microlog.context import TraceContext

ctx = TraceContext(
    trace_id="trace-123",
    span_id="span-456",
    correlation_id="req-789"
)

headers = ctx.to_headers()
# {"X-Trace-Id": "trace-123", "X-Span-Id": "span-456", "X-Correlation-Id": "req-789"}

# HTTP response'a ekle
response.headers.update(headers)
```

## İleri Seviye Kullanım

### Mevcut Logger'ı Yapılandırma

```python
import logging
from microlog import configure_logger, HandlerConfig
from microlog.handlers import AsyncConsoleHandler
from microlog.formatters import JSONFormatter

# Mevcut logger
logger = logging.getLogger("existing_logger")

# MicroLog ile yapılandır
configure_logger(
    logger,
    level=logging.DEBUG,
    service_name="my-service",
    handlers=[
        HandlerConfig(
            handler=AsyncConsoleHandler(),
            formatter=JSONFormatter(service_name="my-service")
        )
    ]
)
```

### Extra Alanlar

Log mesajlarına ek bilgi ekleme:

```python
logger.info(
    "Sipariş oluşturuldu",
    extra={
        "order_id": "ORD-123",
        "user_id": "usr-456",
        "amount": 99.99,
        "currency": "USD"
    }
)
```

### Log Seviyeleri

```python
logger.debug("Debug mesajı")
logger.info("Bilgi mesajı")
logger.warning("Uyarı mesajı")
logger.error("Hata mesajı")
logger.critical("Kritik hata mesajı")
```

## Best Practices

### 1. Handler'ları Düzgün Kapatma

```python
import atexit
from microlog.handlers import AsyncRotatingFileHandler

handler = AsyncRotatingFileHandler(filename="app.log")
logger.addHandler(handler.get_queue_handler())

# atexit ile otomatik kapanma (zaten yapılıyor, ama manuel de yapabilirsiniz)
atexit.register(handler.stop)
```

### 2. Production Yapılandırması

```python
from microlog import setup_file_logger

# Production için JSON format, dosya rotation
logger = setup_file_logger(
    name="myapp",
    filename="/var/log/myapp/app.log",
    format_type="json",
    max_bytes=50 * 1024 * 1024,  # 50MB
    backup_count=10,
    compress=True
)
```

### 3. Development Yapılandırması

```python
from microlog import setup_console_logger

# Development için renkli console
logger = setup_console_logger(
    name="myapp",
    use_colors=True,
    level=logging.DEBUG
)
```

### 4. Trace Context ile Distributed Tracing

```python
from microlog import trace, setup_logger

logger = setup_logger("api-service")

def handle_request(request):
    # HTTP header'lardan trace context oluştur
    with trace(headers=request.headers) as ctx:
        logger.info("İstek alındı")
        
        # Alt servislere trace bilgisini gönder
        headers = ctx.to_headers()
        response = call_downstream_service(headers)
        
        logger.info("Yanıt alındı", extra={"status": response.status})
```

## Örnekler

### Web Uygulaması Örneği

```python
from flask import Flask, request
from microlog import setup_logger, trace
from microlog.context import get_current_context

app = Flask(__name__)
logger = setup_logger("webapp", service_name="api-server")

@app.route("/orders", methods=["POST"])
def create_order():
    # HTTP header'lardan trace context
    with trace(headers=dict(request.headers)):
        logger.info("Sipariş oluşturma isteği alındı")
        
        # Trace bilgilerini log'a ekle
        ctx = get_current_context()
        logger.info("İşlem başlatıldı", extra={
            "trace_id": ctx.trace_id,
            "correlation_id": ctx.correlation_id
        })
        
        # İşlem yap
        order = process_order(request.json)
        
        logger.info("Sipariş oluşturuldu", extra={"order_id": order.id})
        return {"order_id": order.id}
```

### Async Uygulama Örneği

```python
import asyncio
from microlog import setup_logger, trace
from microlog.decorators import with_trace

logger = setup_logger("async-app")

@with_trace(correlation_id="async-task")
async def process_data(data):
    logger.info("Async işlem başladı")
    
    async with trace(session_id="session-123"):
        logger.info("Alt işlem başladı")
        result = await do_work(data)
        logger.info("Alt işlem tamamlandı")
    
    logger.info("Async işlem tamamlandı")
    return result

# Kullanım
asyncio.run(process_data({"key": "value"}))
```

## Sorun Giderme

### Handler'lar Kapanmıyor

Handler'ları manuel olarak kapatın:

```python
handler.stop()  # Queue'daki loglar yazılır ve handler kapanır
```

### Loglar Görünmüyor

1. Log seviyesini kontrol edin:
```python
logger.setLevel(logging.DEBUG)
```

2. Handler'ın başlatıldığından emin olun:
```python
queue_handler = handler.get_queue_handler()  # Otomatik başlatır
```

### Trace Context Çalışmıyor

Trace filter'ın eklendiğinden emin olun:

```python
logger = setup_logger("myapp", add_trace_filter=True)  # Default: True
```

## Sonraki Adımlar

- [API Referansı](api-reference.md) - Tüm API detayları
- [Yapılandırma Kılavuzu](configuration.md) - Detaylı yapılandırma seçenekleri
- [Best Practices](best-practices.md) - Production için öneriler
- [Örnekler](examples.md) - Daha fazla kullanım örneği

## Destek

Sorularınız için:
- GitHub Issues: https://github.com/yourusername/MicroLog/issues
- Dokümantasyon: https://microlog.readthedocs.io

