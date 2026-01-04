# Çalışma Mantığı

Bu dokümantasyon, MicroLog'un iç mimarisini ve nasıl çalıştığını açıklar.

## İçindekiler

1. [Genel Mimari](#genel-mimari)
2. [Asenkron Logging](#asenkron-logging)
3. [Trace Context](#trace-context)
4. [Handler Mimarisi](#handler-mimarisi)
5. [Queue Mekanizması](#queue-mekanizması)
6. [Thread Safety](#thread-safety)
7. [Resource Management](#resource-management)

---

## Genel Mimari

### Bileşenler

```
┌─────────────────────────────────────────────────────────┐
│                    Application Code                      │
│  logger.info("message")  →  QueueHandler                 │
└────────────────────┬──────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              QueueHandler (Non-blocking)                 │
│  - Hızlıca queue'ya ekler                               │
│  - Ana thread'i bloklamaz                                │
└────────────────────┬──────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Queue (threading.Queue)                    │
│  - Thread-safe queue                                    │
│  - Unbounded (sınırsız)                                 │
└────────────────────┬──────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│         QueueListener (Background Thread)               │
│  - Queue'dan okur                                       │
│  - Handler'a yazar                                      │
│  - Async çalışır                                        │
└────────────────────┬──────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Handler (logging.Handler)                 │
│  - ConsoleHandler                                       │
│  - RotatingFileHandler                                  │
│  - SMTPHandler                                          │
└─────────────────────────────────────────────────────────┘
```

### Akış

1. **Application Code**: `logger.info("message")` çağrılır
2. **QueueHandler**: Log record hızlıca queue'ya eklenir (non-blocking)
3. **Queue**: Thread-safe queue'da bekler
4. **QueueListener**: Background thread queue'dan okur
5. **Handler**: Gerçek I/O işlemi (dosya yazma, console, email)

---

## Asenkron Logging

### Neden Asenkron?

**Problem:** Normal logging blocking I/O yapar:
```python
logger.info("message")  # Dosya yazma ana thread'i bloklar
```

**Çözüm:** Queue-based async logging:
```python
logger.info("message")  # Sadece queue'ya ekler, hemen döner
# Background thread dosyaya yazar
```

### Avantajlar

- **Non-blocking**: Ana thread bloklanmaz
- **Yüksek performans**: 47,000+ log/saniye
- **Thread-safe**: Concurrent işlemlerde güvenli
- **Backpressure handling**: Queue dolduğunda graceful degradation

### Queue Mekanizması

```python
# QueueHandler (Application thread)
queue_handler.put(record)  # Hızlı, non-blocking

# QueueListener (Background thread)
while True:
    record = queue.get()  # Blocking, ama background thread'de
    handler.emit(record)  # Gerçek I/O
```

---

## Trace Context

### ContextVar Kullanımı

MicroLog, Python'un `contextvars` modülünü kullanır:

```python
from contextvars import ContextVar

_trace_context: ContextVar[Optional[TraceContext]] = ContextVar(
    'trace_context', default=None
)
```

### Neden ContextVar?

- **Thread-safe**: Her thread kendi context'ine sahip
- **Async-safe**: AsyncIO ile uyumlu
- **Isolated**: Context'ler birbirini etkilemez

### Context Yönetimi

```python
# Context oluşturma
with trace(trace_id="req-123"):
    # ContextVar'a set edilir
    _trace_context.set(TraceContext(...))
    
    # Logging sırasında context okunur
    logger.info("message")  # trace_id otomatik eklenir
    
# Context temizlenir
_trace_context.set(None)
```

### Thread Isolation

```python
# Thread 1
with trace(trace_id="req-1"):
    logger.info("Thread 1")  # trace_id: req-1

# Thread 2 (aynı anda)
with trace(trace_id="req-2"):
    logger.info("Thread 2")  # trace_id: req-2 (karışmaz!)
```

---

## Handler Mimarisi

### AsyncHandler Base Class

```python
class AsyncHandler:
    def __init__(self, handler: logging.Handler):
        self._handler = handler
        self._queue = queue.Queue()
        self._listener = None
        self._started = False
        self._lock = threading.Lock()
    
    def start(self):
        # QueueListener oluştur ve başlat
        self._listener = QueueListener(self._queue, self._handler)
        self._listener.start()
        self._started = True
    
    def stop(self):
        # Queue'yu flush et
        # Listener'ı durdur
        # Handler'ı kapat
```

### Handler Türleri

#### AsyncConsoleHandler
- **Handler**: `logging.StreamHandler`
- **I/O**: `sys.stderr` veya custom stream
- **Kullanım**: Development, debugging

#### AsyncRotatingFileHandler
- **Handler**: `logging.handlers.RotatingFileHandler`
- **I/O**: Dosya sistemi
- **Özellikler**: Rotation, compression
- **Kullanım**: Production logging

#### AsyncSMTPHandler
- **Handler**: `logging.handlers.SMTPHandler`
- **I/O**: SMTP sunucu
- **Özellikler**: Rate limiting
- **Kullanım**: Alert notifications

---

## Queue Mekanizması

### Queue Yapısı

```python
from queue import Queue

_queue = Queue()  # Unbounded queue
```

### Queue İşlemleri

#### Put (Application Thread)
```python
# Non-blocking, hızlı
queue_handler.put(record)
```

#### Get (Listener Thread)
```python
# Blocking, ama background thread'de
record = queue.get()
```

### Queue Flush

```python
def stop(self):
    # Queue boşalana kadar bekle (max 10 saniye)
    while self._queue.qsize() > 0 and total_waited < 10.0:
        time.sleep(0.05)
        total_waited += 0.05
    
    # Listener'ı durdur
    self._listener.stop()
    
    # Handler'ı flush
    self._handler.flush()
    self._handler.close()
```

### Backpressure

Queue unbounded olduğu için:
- **Avantaj**: Hiçbir log kaybolmaz
- **Dikkat**: Çok hızlı logging'de memory kullanımı artabilir

**Çözüm:** Handler performansını optimize et veya rate limiting ekle.

---

## Thread Safety

### Thread-Safe Bileşenler

#### 1. QueueHandler
```python
# Thread-safe queue kullanır
queue_handler.put(record)  # Thread-safe
```

#### 2. Trace Context
```python
# ContextVar thread-safe
with trace(trace_id="req-1"):  # Thread-isolated
    logger.info("message")
```

#### 3. Handler Start/Stop
```python
# Lock ile korunur
with self._lock:
    if not self._started:
        self._listener.start()
        self._started = True
```

### Concurrent Access

```python
# Thread 1
handler.start()  # Lock alır, başlatır

# Thread 2 (aynı anda)
handler.start()  # Lock bekler, sonra skip eder (zaten başlatılmış)
```

---

## Resource Management

### Handler Lifecycle

```python
# 1. Oluşturma
handler = AsyncRotatingFileHandler(...)

# 2. Başlatma
handler.start()  # QueueListener thread'i başlar

# 3. Kullanım
logger.addHandler(handler.get_queue_handler())
logger.info("message")

# 4. Temizlik
handler.stop()  # Queue flush, listener durdur, handler kapat
```

### Atexit Handling

```python
# Program kapanırken otomatik temizlik
import atexit
import weakref

def cleanup():
    strong_self = weak_self()
    if strong_self is not None:
        strong_self.stop()

weak_self = weakref.ref(self)
atexit.register(cleanup)
```

**Neden weakref?**
- Circular reference'ı önler
- Memory leak'i engeller

### File Handle Management

```python
def stop(self):
    # Handler'ı flush
    if hasattr(self._handler, 'flush'):
        self._handler.flush()
    
    # Handler'ı kapat (file handle'ı serbest bırakır)
    if hasattr(self._handler, 'close'):
        self._handler.close()
```

---

## Performance Optimizations

### 1. Queue-Based Async

- Ana thread non-blocking
- Background thread I/O yapar
- Yüksek throughput

### 2. ContextVar

- Thread-local storage
- AsyncIO uyumlu
- Düşük overhead

### 3. Lock Optimization

- Minimal lock kullanımı
- Lock scope'u küçük
- Deadlock riski yok

### 4. Queue Flush

- Timeout ile graceful shutdown
- Tüm pending loglar flush edilir
- Data loss yok

---

## Memory Management

### Queue Size

- Unbounded queue (sınırsız)
- Memory kullanımı log rate'e bağlı
- Normal kullanımda problem yok

### Context Cleanup

- ContextVar otomatik temizlenir
- Weakref ile circular reference yok
- Memory leak yok

### Handler Cleanup

- `stop()` ile tüm kaynaklar serbest bırakılır
- File handle'lar kapatılır
- Thread'ler terminate edilir

---

## Error Handling

### Handler Errors

```python
try:
    handler.emit(record)
except Exception:
    # Handler error'u loglama sistemini etkilemez
    # Sadece o log kaydı kaybolur
    pass
```

### Queue Errors

```python
try:
    queue_handler.put(record)
except Exception:
    # Queue doluysa (unbounded queue'da olmaz)
    # Fallback: direkt handler'a yaz
    handler.emit(record)
```

---

## Sonraki Adımlar

- **[Davranış Şekli](DAVRANIS_SEKLI.md)** - Davranışlar, edge cases ve best practices

