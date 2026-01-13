# Trace Context - Distributed Tracing

MicroLog, distributed tracing için trace context yönetimi sağlar. Bu sayede mikroservis mimarisinde log mesajlarını birbirine bağlayabilir, istek akışını takip edebilirsiniz.

## İçindekiler

- [TraceContext Sınıfı](#tracecontext-sınıfı)
- [trace Context Manager](#trace-context-manager)
- [Context Yönetimi](#context-yönetimi)
- [HTTP Header Entegrasyonu](#http-header-entegrasyonu)
- [Distributed Tracing](#distributed-tracing)
- [Decorator Kullanımı](#decorator-kullanımı)
- [Best Practices](#best-practices)
- [Sorun Giderme](#sorun-giderme)

---

## TraceContext Sınıfı

`TraceContext`, bir işlem (request, task, span) için trace bilgilerini tutan dataclass'tır.

### Alanlar

```python
@dataclass
class TraceContext:
    trace_id: str                    # Ana trace ID (16 haneli hex)
    span_id: str                     # Mevcut span ID (16 haneli hex)
    parent_span_id: Optional[str]    # Parent span ID (child span için)
    correlation_id: Optional[str]    # İş kolu correlation ID (örn: order_id)
    session_id: Optional[str]        # Kullanıcı session ID
    started_at: str                 # ISO 8601 UTC timestamp
    extra: Dict[str, Any]           # Ek alanlar
```

### Özellikler

- ✅ **Otomatik ID üretimi**: `trace_id` ve `span_id` otomatik oluşturulur
- ✅ **Child span desteği**: Parent-child ilişkisi kurulabilir
- ✅ **HTTP header dönüşümü**: `to_headers()` ve `from_headers()`
- ✅ **Dict dönüşümü**: `to_dict()` ile JSON serialization
- ✅ **Thread-safe**: ContextVar ve thread-local storage

### Kullanım Örnekleri

#### Temel Oluşturma

```python
from microlog.context import TraceContext

# Otomatik ID'ler ile
ctx = TraceContext()
print(ctx.trace_id)  # "a1b2c3d4e5f6g7h8"
print(ctx.span_id)   # "i9j0k1l2m3n4o5p6"
```

#### Özel Değerlerle

```python
ctx = TraceContext(
    trace_id="custom-trace-123",
    span_id="custom-span-456",
    correlation_id="order-789",
    session_id="session-abc",
    extra={
        "user_id": "usr-123",
        "tenant_id": "acme"
    }
)
```

#### Child Span Oluşturma

```python
parent = TraceContext(
    trace_id="trace-123",
    span_id="span-456"
)

child = parent.child_span()

print(child.trace_id)        # "trace-123" (aynı)
print(child.span_id)         # "new-span-789" (yeni)
print(child.parent_span_id)  # "span-456" (parent'ın span_id'si)
```

#### Dict'e Dönüştürme

```python
ctx = TraceContext(
    trace_id="trace-123",
    correlation_id="order-789",
    extra={"user_id": "usr-123"}
)

data = ctx.to_dict()
# {
#     "trace_id": "trace-123",
#     "span_id": "...",
#     "started_at": "2025-01-07T14:32:01.123456+00:00",
#     "correlation_id": "order-789",
#     "user_id": "usr-123"
# }
```

---

## trace Context Manager

`trace` context manager, trace context'i otomatik yönetir. Sync ve async kullanımı destekler.

### Özellikler

- ✅ **Otomatik başlatma/bitirme**: Context otomatik ayarlanır ve temizlenir
- ✅ **Nested context**: İç içe kullanımda parent-child ilişkisi
- ✅ **HTTP header desteği**: Header'lardan otomatik context oluşturma
- ✅ **Async desteği**: `async with` ile kullanılabilir

### Kullanım Örnekleri

#### Temel Kullanım

```python
from microlog import trace, get_current_context

with trace() as ctx:
    # Context otomatik ayarlandı
    current = get_current_context()
    assert current.trace_id == ctx.trace_id
    
    logger.info("Log mesajı")  # trace_id otomatik eklenir

# Context otomatik temizlendi
assert get_current_context() is None
```

#### Parametrelerle

```python
with trace(
    trace_id="custom-trace",
    correlation_id="order-123",
    session_id="session-456",
    user_id="usr-789"  # extra alan
) as ctx:
    assert ctx.trace_id == "custom-trace"
    assert ctx.correlation_id == "order-123"
    assert ctx.extra["user_id"] == "usr-789"
```

#### Nested Context (Parent-Child)

```python
with trace(trace_id="parent-trace") as parent:
    parent_span_id = parent.span_id
    
    logger.info("Parent span")
    
    # Child span oluştur
    with trace(parent=parent) as child:
        # Aynı trace_id, yeni span_id
        assert child.trace_id == "parent-trace"
        assert child.span_id != parent_span_id
        assert child.parent_span_id == parent_span_id
        
        logger.info("Child span")
    
    # Parent context'e dönüldü
    current = get_current_context()
    assert current.span_id == parent_span_id
```

#### HTTP Header'lardan

```python
# HTTP request'ten header'ları al
headers = {
    "X-Trace-Id": "trace-123",
    "X-Span-Id": "span-456",
    "X-Correlation-Id": "order-789"
}

with trace(headers=headers) as ctx:
    # Parent trace_id korunur, yeni span oluşturulur
    assert ctx.trace_id == "trace-123"
    assert ctx.parent_span_id == "span-456"  # Parent span
    assert ctx.correlation_id == "order-789"
```

#### Async Kullanım

```python
import asyncio
from microlog import trace

async def process_request():
    async with trace(correlation_id="req-123") as ctx:
        logger.info("Async işlem başladı")
        await do_async_work()
        logger.info("Async işlem tamamlandı")

asyncio.run(process_request())
```

---

## Context Yönetimi

### Manuel Context Yönetimi

```python
from microlog.context import (
    TraceContext,
    get_current_context,
    set_current_context,
    clear_current_context
)

# Context oluştur
ctx = TraceContext(
    trace_id="trace-123",
    correlation_id="order-789"
)

# Aktif yap
set_current_context(ctx)

# Kullan
current = get_current_context()
assert current.trace_id == "trace-123"

# Temizle
clear_current_context()
assert get_current_context() is None
```

### Context Stack (Nested)

```python
# Outer context
with trace(correlation_id="outer") as outer:
    outer_span = get_current_context().span_id
    
    # Inner context
    with trace(correlation_id="inner") as inner:
        inner_span = get_current_context().span_id
        assert get_current_context().correlation_id == "inner"
    
    # Outer context'e dönüldü
    assert get_current_context().span_id == outer_span
    assert get_current_context().correlation_id == "outer"
```

### Thread Safety

Context yönetimi thread-safe'dir. Her thread kendi context'ine sahiptir:

```python
import threading
from microlog import trace, get_current_context

def worker(thread_id):
    with trace(correlation_id=f"thread-{thread_id}") as ctx:
        # Her thread kendi context'ine sahip
        current = get_current_context()
        assert current.correlation_id == f"thread-{thread_id}"

threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
for t in threads:
    t.start()
for t in threads:
    t.join()
```

---

## HTTP Header Entegrasyonu

### Header'dan Context Oluşturma

```python
from microlog.context import TraceContext

# HTTP request header'ları
headers = {
    "X-Trace-Id": "trace-123",
    "X-Span-Id": "span-456",
    "X-Correlation-Id": "order-789",
    "X-Session-Id": "session-abc"
}

# Context oluştur
ctx = TraceContext.from_headers(headers)

print(ctx.trace_id)        # "trace-123"
print(ctx.parent_span_id)  # "span-456" (parent span)
print(ctx.correlation_id)  # "order-789"
```

**Not:** `from_headers()` yeni bir `span_id` oluşturur ve mevcut `X-Span-Id`'yi `parent_span_id` olarak kullanır.

### Context'i Header'a Dönüştürme

```python
ctx = TraceContext(
    trace_id="trace-123",
    span_id="span-456",
    correlation_id="order-789",
    session_id="session-abc"
)

headers = ctx.to_headers()
# {
#     "X-Trace-Id": "trace-123",
#     "X-Span-Id": "span-456",
#     "X-Correlation-Id": "order-789",
#     "X-Session-Id": "session-abc"
# }

# HTTP response'a ekle
response.headers.update(headers)
```

### Web Framework Entegrasyonu

#### Flask

```python
from flask import Flask, request, g
from microlog import trace, get_current_context

app = Flask(__name__)

@app.before_request
def setup_trace():
    """Her request için trace context oluştur"""
    with trace(headers=dict(request.headers)) as ctx:
        g.trace_context = ctx

@app.route("/orders", methods=["POST"])
def create_order():
    ctx = get_current_context()
    logger.info("Sipariş oluşturma isteği", extra={
        "trace_id": ctx.trace_id,
        "correlation_id": ctx.correlation_id
    })
    
    # Alt servise trace bilgisini gönder
    headers = ctx.to_headers()
    response = call_downstream_service(headers)
    
    return {"order_id": "ORD-123"}

@app.after_request
def add_trace_headers(response):
    """Response'a trace header'ları ekle"""
    ctx = get_current_context()
    if ctx:
        response.headers.update(ctx.to_headers())
    return response
```

#### FastAPI

```python
from fastapi import FastAPI, Request
from microlog import trace, get_current_context

app = FastAPI()

@app.middleware("http")
async def trace_middleware(request: Request, call_next):
    """Her request için trace context oluştur"""
    headers = dict(request.headers)
    
    async with trace(headers=headers) as ctx:
        response = await call_next(request)
        
        # Response header'larına trace bilgisi ekle
        for key, value in ctx.to_headers().items():
            response.headers[key] = value
        
        return response

@app.post("/orders")
async def create_order():
    ctx = get_current_context()
    logger.info("Sipariş oluşturma isteği")
    return {"order_id": "ORD-123"}
```

#### Django

```python
from django.utils.deprecation import MiddlewareMixin
from microlog import trace, get_current_context

class TraceMiddleware(MiddlewareMixin):
    """Django middleware ile trace context"""
    
    def process_request(self, request):
        headers = {
            k.replace("HTTP_", "").replace("_", "-").title(): v
            for k, v in request.META.items()
            if k.startswith("HTTP_")
        }
        
        request.trace_context = trace(headers=headers)
        request.trace_context.__enter__()
    
    def process_response(self, request, response):
        if hasattr(request, "trace_context"):
            ctx = get_current_context()
            if ctx:
                for key, value in ctx.to_headers().items():
                    response[key] = value
            request.trace_context.__exit__(None, None, None)
        return response
```

---

## Distributed Tracing

### Mikroservis Mimarisi

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   API GW    │────▶│  Order Svc  │────▶│ Payment Svc │
│ trace-123   │     │ trace-123   │     │ trace-123   │
│ span-001    │     │ span-002    │     │ span-003    │
└─────────────┘     └─────────────┘     └─────────────┘
     │                    │                    │
     │ X-Trace-Id         │ X-Trace-Id         │
     │ X-Span-Id          │ X-Span-Id          │
     └────────────────────┴────────────────────┘
```

### Örnek: Mikroservis İletişimi

#### API Gateway

```python
from microlog import trace, get_current_context
import requests

@app.route("/orders", methods=["POST"])
def create_order():
    # Yeni trace başlat
    with trace(correlation_id=request.json.get("order_id")) as ctx:
        logger.info("İstek alındı")
        
        # Order Service'e istek gönder
        headers = ctx.to_headers()
        response = requests.post(
            "http://order-service/api/orders",
            json=request.json,
            headers=headers
        )
        
        logger.info("Yanıt alındı", extra={"status": response.status_code})
        return response.json()
```

#### Order Service

```python
@app.route("/api/orders", methods=["POST"])
def process_order():
    # Header'lardan trace context oluştur
    with trace(headers=dict(request.headers)) as ctx:
        logger.info("Sipariş işleniyor")
        
        # Payment Service'e istek gönder
        headers = ctx.to_headers()
        payment_response = requests.post(
            "http://payment-service/api/payments",
            json={"amount": 100},
            headers=headers
        )
        
        logger.info("Ödeme tamamlandı")
        return {"order_id": "ORD-123"}
```

#### Payment Service

```python
@app.route("/api/payments", methods=["POST"])
def process_payment():
    # Header'lardan trace context oluştur
    with trace(headers=dict(request.headers)) as ctx:
        logger.info("Ödeme işleniyor")
        
        # Aynı trace_id, yeni span_id
        # parent_span_id = Order Service'in span_id'si
        
        return {"payment_id": "PAY-123"}
```

### Trace Görselleştirme

Log aggregation sistemlerinde (ELK, Datadog, Jaeger) trace görselleştirme:

```json
{
  "timestamp": "2025-01-07T14:32:01.123456+00:00",
  "level": "INFO",
  "service": "order-service",
  "message": "Sipariş işleniyor",
  "trace_id": "trace-123",
  "span_id": "span-002",
  "parent_span_id": "span-001",
  "correlation_id": "order-789"
}
```

**Trace Tree:**
```
trace-123
├── span-001 (API Gateway)
│   └── span-002 (Order Service)
│       └── span-003 (Payment Service)
```

---

## Decorator Kullanımı

### with_trace Decorator

Fonksiyonlara otomatik trace context ekler:

```python
from microlog.decorators import with_trace
from microlog import get_current_context

@with_trace(correlation_id="order-123")
def process_order(order_id: str):
    ctx = get_current_context()
    logger.info(f"Sipariş işleniyor: {order_id}")
    # trace_id ve correlation_id otomatik eklenir
    return "success"

# Kullanım
result = process_order("ORD-123")
```

### Async Fonksiyonlar

```python
@with_trace(session_id="session-123")
async def async_process(data):
    ctx = get_current_context()
    logger.info("Async işlem başladı")
    await do_work()
    return "done"

# Kullanım
result = await async_process({"key": "value"})
```

### Nested Decorators

```python
@with_trace(correlation_id="outer")
def outer_function():
    @with_trace(correlation_id="inner")
    def inner_function():
        ctx = get_current_context()
        assert ctx.correlation_id == "inner"
        return "inner"
    
    result = inner_function()
    ctx = get_current_context()
    assert ctx.correlation_id == "outer"
    return result
```

---

## Best Practices

### 1. Her Request için Trace Başlat

```python
# ✅ İyi: Her request için yeni trace
@app.before_request
def setup_trace():
    with trace(headers=dict(request.headers)) as ctx:
        g.trace_context = ctx

# ❌ Kötü: Trace context yok
@app.route("/orders")
def create_order():
    logger.info("Sipariş oluşturuldu")  # trace_id yok
```

### 2. Correlation ID Kullan

```python
# ✅ İyi: İş kolu correlation ID
with trace(correlation_id=order_id) as ctx:
    logger.info("Sipariş işleniyor")

# ❌ Kötü: Sadece trace_id
with trace() as ctx:
    logger.info("Sipariş işleniyor")  # Hangi sipariş?
```

### 3. Child Span Oluştur

```python
# ✅ İyi: Alt işlemler için child span
with trace(correlation_id="order-123") as parent:
    logger.info("Sipariş başlatıldı")
    
    with trace(parent=parent) as child:
        logger.info("Ödeme işleniyor")  # Child span
    
    with trace(parent=parent) as child2:
        logger.info("Stok güncelleniyor")  # Başka child span

# ❌ Kötü: Tüm işlemler aynı span'de
with trace(correlation_id="order-123") as ctx:
    logger.info("Sipariş başlatıldı")
    logger.info("Ödeme işlendi")
    logger.info("Stok güncellendi")
```

### 4. HTTP Header'ları Yay

```python
# ✅ İyi: Alt servislere trace bilgisini gönder
with trace(headers=request.headers) as ctx:
    headers = ctx.to_headers()
    response = requests.post(
        "http://downstream-service/api",
        headers=headers
    )

# ❌ Kötü: Trace bilgisi kaybolur
response = requests.post(
    "http://downstream-service/api"
    # trace_id yok
)
```

### 5. Response Header'larına Ekle

```python
# ✅ İyi: Response'a trace bilgisi ekle
@app.after_request
def add_trace_headers(response):
    ctx = get_current_context()
    if ctx:
        response.headers.update(ctx.to_headers())
    return response
```

### 6. Exception Handling

```python
# ✅ İyi: Exception'da da trace korunur
with trace(correlation_id="order-123") as ctx:
    try:
        process_order()
    except Exception:
        logger.exception("İşlem başarısız")  # trace_id hala var
        raise
```

### 7. Async İşlemler

```python
# ✅ İyi: Async context manager
async def process_data():
    async with trace(correlation_id="data-123") as ctx:
        await do_async_work()
        logger.info("İşlem tamamlandı")
```

### 8. Log Extra Alanları

```python
# ✅ İyi: Trace bilgilerini log'a ekle
ctx = get_current_context()
logger.info("İşlem tamamlandı", extra={
    "trace_id": ctx.trace_id,
    "span_id": ctx.span_id,
    "correlation_id": ctx.correlation_id
})

# ❌ Kötü: Trace bilgisi yok (TraceContextFilter otomatik ekler ama)
logger.info("İşlem tamamlandı")
```

---

## Sorun Giderme

### Context Görünmüyor

**Sorun:** `get_current_context()` `None` döndürüyor.

**Çözüm:**
```python
# 1. Context manager kullan
with trace() as ctx:
    current = get_current_context()
    assert current is not None

# 2. Manuel ayarla
from microlog.context import set_current_context
ctx = TraceContext()
set_current_context(ctx)
```

### Trace ID Log'a Eklenmiyor

**Sorun:** Log mesajlarında `trace_id` görünmüyor.

**Çözüm:**
```python
# 1. TraceContextFilter eklendi mi?
logger = setup_logger("myapp", add_trace_filter=True)  # Default: True

# 2. Context aktif mi?
with trace() as ctx:
    logger.info("Log mesajı")  # trace_id otomatik eklenir
```

### Nested Context Sorunları

**Sorun:** İç içe context'lerde parent context kayboluyor.

**Çözüm:**
```python
# ✅ Doğru: parent parametresi kullan
with trace(correlation_id="parent") as parent:
    with trace(parent=parent) as child:
        # Parent-child ilişkisi korunur
        pass

# ❌ Yanlış: Yeni trace başlatılıyor
with trace(correlation_id="parent") as parent:
    with trace(correlation_id="child"):
        # Parent kaybolur
        pass
```

### HTTP Header Case Sensitivity

**Sorun:** Header'lar case-sensitive, bazı framework'ler farklı format kullanıyor.

**Çözüm:**
```python
# from_headers() case-insensitive
headers = {
    "x-trace-id": "trace-123",      # lowercase
    "X-Trace-Id": "trace-123",      # mixed
    "X-TRACE-ID": "trace-123"       # uppercase
}
# Hepsi çalışır
```

### Thread Safety Sorunları

**Sorun:** Birden fazla thread'de context karışıyor.

**Çözüm:**
```python
# ContextVar ve thread-local kullanılıyor, otomatik thread-safe
# Her thread kendi context'ine sahip
import threading

def worker():
    with trace(correlation_id=f"thread-{threading.current_thread().ident}"):
        # Thread-safe
        pass
```

### Async Context Manager Sorunları

**Sorun:** Async context manager çalışmıyor.

**Çözüm:**
```python
# ✅ Doğru: async with kullan
async def process():
    async with trace() as ctx:
        await do_work()

# ❌ Yanlış: sync with async fonksiyonda
async def process():
    with trace() as ctx:  # Çalışır ama async context manager kullan
        await do_work()
```

---

## API Referansı

### TraceContext

```python
@dataclass
class TraceContext:
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    correlation_id: Optional[str]
    session_id: Optional[str]
    started_at: str
    extra: Dict[str, Any]
    
    def child_span(self) -> TraceContext
    def to_dict(self) -> Dict[str, Any]
    def to_headers(self) -> Dict[str, str]
    
    @classmethod
    def from_headers(cls, headers: Dict[str, str]) -> TraceContext
```

### trace Context Manager

```python
class trace:
    def __init__(
        self,
        trace_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        session_id: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        parent: Optional[TraceContext] = None,
        **extra: Any
    )
    
    def __enter__(self) -> TraceContext
    def __exit__(self, exc_type, exc_val, exc_tb) -> None
    async def __aenter__(self) -> TraceContext
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None
```

### Context Yönetimi Fonksiyonları

```python
def get_current_context() -> Optional[TraceContext]
def set_current_context(ctx: Optional[TraceContext]) -> None
def clear_current_context() -> None
def create_trace(**kwargs: Any) -> TraceContext
```

---

## Sonraki Adımlar

- [Quick Start Guide](quickstart.md) - Hızlı başlangıç
- [Handlers Documentation](handlers.md) - Handler'lar hakkında
- [Formatters Documentation](formatters.md) - Log formatları
- [API Reference](api-reference.md) - Tüm API detayları

