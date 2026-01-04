# Davranış Şekli

Bu dokümantasyon, MicroLog'un davranışlarını, edge case'leri ve best practices'i açıklar.

## İçindekiler

1. [Log Seviyeleri ve Filtreleme](#log-seviyeleri-ve-filtreleme)
2. [Trace Context Davranışları](#trace-context-davranışları)
3. [Handler Davranışları](#handler-davranışları)
4. [Edge Cases](#edge-cases)
5. [Best Practices](#best-practices)
6. [Troubleshooting](#troubleshooting)

---

## Log Seviyeleri ve Filtreleme

### Log Seviyesi Hiyerarşisi

```
DEBUG < INFO < WARNING < ERROR < CRITICAL
```

### Seviye Filtreleme

```python
logger.setLevel(logging.WARNING)

logger.debug("Görünmez")      # Filtrelenir
logger.info("Görünmez")        # Filtrelenir
logger.warning("Görünür")      # Loglanır
logger.error("Görünür")        # Loglanır
logger.critical("Görünür")     # Loglanır
```

### Handler Seviyesi

```python
# Logger seviyesi: INFO
logger.setLevel(logging.INFO)

# Handler seviyesi: WARNING
handler = AsyncConsoleHandler(level=logging.WARNING)

# Sonuç: Sadece WARNING ve üzeri loglanır
logger.info("Görünmez")        # Logger seviyesi OK, ama handler filtrelenir
logger.warning("Görünür")      # Loglanır
```

### Çoklu Handler

```python
# Console: INFO ve üzeri
console_handler = AsyncConsoleHandler(level=logging.INFO)

# File: WARNING ve üzeri
file_handler = AsyncRotatingFileHandler(level=logging.WARNING)

logger.info("message")
# Console'a yazılır
# Dosyaya yazılmaz

logger.warning("message")
# Console'a yazılır
# Dosyaya yazılır
```

---

## Trace Context Davranışları

### Context Oluşturma

```python
# trace_id yoksa otomatik oluşturulur
with trace():
    logger.info("message")  # trace_id: otomatik UUID

# trace_id belirtilirse kullanılır
with trace(trace_id="custom-123"):
    logger.info("message")  # trace_id: "custom-123"
```

### Span ID Oluşturma

```python
# span_id yoksa otomatik oluşturulur
with trace(trace_id="req-123") as ctx:
    print(ctx.span_id)  # Otomatik UUID

# span_id belirtilirse kullanılır
with trace(trace_id="req-123", span_id="custom-span"):
    print(ctx.span_id)  # "custom-span"
```

### Nested Context

```python
with trace(trace_id="parent") as parent:
    print(f"Parent span: {parent.span_id}")
    
    # Child context
    with trace(
        trace_id=parent.trace_id,
        parent_span_id=parent.span_id
    ) as child:
        print(f"Child span: {child.span_id}")
        print(f"Parent span: {child.parent_span_id}")  # parent.span_id
```

### Context Isolation

```python
# Thread 1
def thread1():
    with trace(trace_id="req-1"):
        logger.info("Thread 1")  # trace_id: req-1

# Thread 2 (aynı anda)
def thread2():
    with trace(trace_id="req-2"):
        logger.info("Thread 2")  # trace_id: req-2 (karışmaz!)

# Context'ler birbirini etkilemez
```

### Async Context

```python
async def async_function():
    async with trace(trace_id="async-req"):
        logger.info("Async işlem")
        await do_work()
        logger.info("Async tamamlandı")

# AsyncIO ile uyumlu
```

---

## Handler Davranışları

### Start/Stop Davranışı

```python
handler = AsyncRotatingFileHandler(...)

# Start: QueueListener thread'i başlar
handler.start()

# Stop: Queue flush, listener durdur, handler kapat
handler.stop()

# Tekrar start: Yeni listener başlatılır
handler.start()
```

### Concurrent Start/Stop

```python
# Thread 1
handler.start()  # Lock alır, başlatır

# Thread 2 (aynı anda)
handler.start()  # Lock bekler, skip eder (zaten başlatılmış)

# Thread-safe!
```

### Queue Flush Davranışı

```python
handler.stop()
# 1. Queue boşalana kadar bekle (max 10 saniye)
# 2. Listener'ı durdur
# 3. Handler'ı flush
# 4. Handler'ı kapat

# Tüm pending loglar flush edilir
```

### Rotation Davranışı

```python
handler = AsyncRotatingFileHandler(
    filename="logs/app.log",
    max_bytes=10_000_000,  # 10 MB
    backup_count=5
)

# Dosya 10 MB'a ulaştığında:
# 1. app.log → app.log.1
# 2. Yeni app.log oluşturulur
# 3. app.log.1 → app.log.2 (varsa)
# 4. En eski dosya silinir (backup_count aşılırsa)
```

### Compression Davranışı

```python
handler = AsyncRotatingFileHandler(
    filename="logs/app.log",
    max_bytes=10_000_000,
    backup_count=5,
    compress=True  # Gzip compression
)

# Rotation sonrası:
# app.log.1 → app.log.1.gz (gzip compressed)
```

### SMTP Rate Limiting

```python
handler = AsyncSMTPHandler(
    ...,
    rate_limit_seconds=300  # 5 dakika
)

# İlk ERROR log: Email gönderilir
logger.error("Hata 1")

# 5 dakika içinde başka ERROR log: Email gönderilmez
logger.error("Hata 2")  # Rate limit

# 5 dakika sonra: Email gönderilir
logger.error("Hata 3")
```

---

## Edge Cases

### 1. Handler Start Edilmeden Kullanım

```python
handler = AsyncRotatingFileHandler(...)
logger.addHandler(handler.get_queue_handler())

# Yanlış: Start edilmeden kullanım
logger.info("message")  # Queue'ya eklenir ama işlenmez

# Doğru: Start edildikten sonra kullanım
handler.start()
logger.info("message")  # İşlenir
```

### 2. Handler Stop Edilmeden Program Kapanma

```python
handler = AsyncRotatingFileHandler(...)
handler.start()

# Yanlış: Stop edilmeden program kapanırsa
# Bazı loglar kaybolabilir

# Doğru: Atexit ile otomatik temizlik
import atexit
atexit.register(lambda: handler.stop())
```

### 3. Çok Hızlı Logging

```python
# 100,000 log/saniye
for i in range(100000):
    logger.info(f"Log {i}")

# Queue dolabilir (unbounded ama memory sınırlı)
# Çözüm: Rate limiting veya batch logging
```

### 4. Disk Full

```python
# Disk doluysa
handler = AsyncRotatingFileHandler(filename="logs/app.log")
handler.start()

logger.info("message")
# Handler error oluşur
# Log kaybolur ama uygulama çalışmaya devam eder
```

### 5. Permission Error

```python
# Dosya yazma izni yoksa
handler = AsyncRotatingFileHandler(filename="/root/app.log")
handler.start()

logger.info("message")
# PermissionError oluşur
# Log kaybolur ama uygulama çalışmaya devam eder
```

### 6. Trace Context Olmadan Logging

```python
# Trace context yoksa
logger.info("message")
# trace_id, span_id eklenmez
# Normal log olarak yazılır
```

### 7. Nested Trace Context Limit

```python
# Çok derin nested context
with trace(trace_id="level-1"):
    with trace(trace_id="level-1", parent_span_id=ctx.span_id):
        with trace(trace_id="level-1", parent_span_id=ctx.span_id):
            # ... 100 level ...
            logger.info("message")  # Çalışır ama karmaşık olur
```

---

## Best Practices

### 1. Logger İsimlendirme

```python
# İyi: Modül veya servis adı
logger = setup_logger("order-service")
logger = setup_logger("payment-processor")

# Kötü: Generic isimler
logger = setup_logger("app")
logger = setup_logger("logger")
```

### 2. Log Seviyeleri

```python
# Doğru kullanım
logger.debug("Detaylı debug bilgisi")      # Geliştirme
logger.info("Normal işlem")                 # Production
logger.warning("Potansiyel problem")         # Dikkat gerektiren
logger.error("Hata oluştu")                 # Hatalar
logger.critical("Sistem çöküşü riski")      # Kritik durumlar
```

### 3. Trace Context Kullanımı

```python
# Doğru: Her request için trace context
with trace(trace_id=request_id):
    logger.info("İşlem başladı")

# Yanlış: Trace context olmadan
logger.info("İşlem başladı")  # Trace bilgisi yok
```

### 4. Extra Fields

```python
# Doğru: Structured logging
logger.info("Kullanıcı girişi", extra={
    "user_id": 123,
    "ip_address": "192.168.1.1"
})

# Yanlış: String interpolation
logger.info(f"Kullanıcı {user_id} giriş yaptı")  # Parse edilemez
```

### 5. Handler Temizliği

```python
# Doğru: Program kapanırken temizlik
import atexit
atexit.register(lambda: handler.stop())

# Veya try/finally
try:
    handler.start()
    # ... kullanım ...
finally:
    handler.stop()
```

### 6. Production Ayarları

```python
# Doğru: Production için JSON format
logger = setup_logger(
    name="myapp",
    formatter=JSONFormatter(service_name="myapp")
)

# Doğru: Dosya rotation
handler = AsyncRotatingFileHandler(
    filename="logs/app.log",
    max_bytes=50_000_000,  # 50 MB
    backup_count=10,
    compress=True
)
```

### 7. Error Handling

```python
# Doğru: Exception logging
try:
    risky_operation()
except Exception as e:
    logger.error("İşlem başarısız", exc_info=True, extra={
        "operation": "risky_operation",
        "error": str(e)
    })
```

### 8. Performance

```python
# Doğru: Async logging (non-blocking)
logger.info("message")  # Hızlı, non-blocking

# Yanlış: Blocking I/O
with open("log.txt", "a") as f:
    f.write("message")  # Yavaş, blocking
```

---

## Troubleshooting

### Problem: Loglar görünmüyor

**Nedenler:**
1. Logger seviyesi çok yüksek
2. Handler start edilmemiş
3. Handler seviyesi çok yüksek

**Çözüm:**
```python
# Logger seviyesini kontrol et
logger.setLevel(logging.DEBUG)

# Handler'ın başlatıldığından emin ol
handler.start()

# Handler seviyesini kontrol et
handler = AsyncConsoleHandler(level=logging.DEBUG)
```

### Problem: Trace ID görünmüyor

**Nedenler:**
1. Trace context oluşturulmamış
2. TraceContextFilter eklenmemiş

**Çözüm:**
```python
# Trace context oluştur
with trace(trace_id="req-123"):
    logger.info("message")

# TraceContextFilter otomatik eklenir (setup_logger ile)
```

### Problem: Dosya rotation çalışmıyor

**Nedenler:**
1. max_bytes çok büyük
2. Dosya yazma izni yok
3. Disk dolu

**Çözüm:**
```python
# max_bytes değerini kontrol et
handler = AsyncRotatingFileHandler(
    filename="logs/app.log",
    max_bytes=1_000_000,  # 1 MB (test için)
    backup_count=5
)

# İzinleri kontrol et
import os
print(os.access("logs", os.W_OK))  # True olmalı
```

### Problem: Memory leak şüphesi

**Nedenler:**
1. Handler stop edilmemiş
2. Çok hızlı logging (queue doluyor)

**Çözüm:**
```python
# Handler'ı düzgün kapat
handler.stop()

# Atexit ile otomatik temizlik
import atexit
atexit.register(lambda: handler.stop())

# Queue size'ı kontrol et
print(handler._queue.qsize())
```

### Problem: Thread safety sorunları

**Nedenler:**
1. Custom handler thread-safe değil
2. Handler paylaşımı

**Çözüm:**
- MicroLog thread-safe, ama custom handler'larınız thread-safe olmalı
- Trace context her thread için izole edilir
- Handler'ları paylaşırken dikkatli olun

---

## Sonuç

MicroLog, production ortamları için tasarlanmış, thread-safe, performanslı bir logging kütüphanesidir. Bu dokümantasyondaki best practices'i takip ederek güvenli ve etkili logging yapabilirsiniz.

