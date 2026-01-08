# Handlers - Log Çıktı Hedefleri

MicroLog, asenkron logging için özel handler'lar sağlar. Handler'lar, log mesajlarını farklı hedeflere (console, dosya) yönlendirir ve ana thread'i bloklamadan arka planda işler.

## İçindekiler

- [AsyncHandler (Base Class)](#asynchandler-base-class)
- [AsyncConsoleHandler](#asyncconsolehandler)
- [AsyncRotatingFileHandler](#asynrotatingfilehandler)
- [Handler Yaşam Döngüsü](#handler-yaşam-döngüsü)
- [Best Practices](#best-practices)
- [Sorun Giderme](#sorun-giderme)

---

## AsyncHandler (Base Class)

Tüm asenkron handler'ların temel sınıfı. Queue tabanlı asenkron mimari sağlar.

### Mimari

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Ana Thread  │────▶│   Queue     │────▶│  Listener   │
│ (log.info)  │     │ (buffer)    │     │ (arka plan) │
└─────────────┘     └─────────────┘     └─────────────┘
     │                                        │
     │ Hemen döner                            │ Asenkron yazar
     ▼                                        ▼
Uygulama devam                         Console/File
```

### Özellikler

- ✅ **Non-blocking**: Ana thread bloklanmaz
- ✅ **Thread-safe**: Birden fazla thread'den güvenli kullanım
- ✅ **Otomatik cleanup**: `atexit` ile program kapanırken temizlik
- ✅ **Context manager**: `with` statement desteği
- ✅ **Async context manager**: `async with` desteği

### Temel Metodlar

```python
class AsyncHandler:
    def start(self) -> None:
        """Asenkron listener'ı başlatır."""
    
    def stop(self) -> None:
        """Listener'ı durdurur ve queue'daki tüm logları yazar."""
    
    def get_queue_handler(self) -> QueueHandler:
        """Logger'a eklenecek QueueHandler'ı döndürür (otomatik start)."""
    
    @property
    def handler(self) -> logging.Handler:
        """Gerçek handler'ı döndürür (formatter ayarlamak için)."""
```

### Kullanım Örnekleri

#### Temel Kullanım

```python
from microlog.handlers import AsyncConsoleHandler

handler = AsyncConsoleHandler()
queue_handler = handler.get_queue_handler()  # Otomatik başlatır

logger = logging.getLogger("myapp")
logger.addHandler(queue_handler)
logger.setLevel(logging.INFO)

logger.info("Log mesajı")
# ... uygulama devam eder, log arka planda yazılır

handler.stop()  # Queue'daki tüm loglar yazılır
```

#### Context Manager ile

```python
from microlog.handlers import AsyncRotatingFileHandler

with AsyncRotatingFileHandler(filename="app.log") as handler:
    logger.addHandler(handler.get_queue_handler())
    logger.info("Log mesajı")
    # Handler otomatik kapanır
```

#### Async Context Manager ile

```python
import asyncio
from microlog.handlers import AsyncRotatingFileHandler

async def main():
    async with AsyncRotatingFileHandler(filename="app.log") as handler:
        logger.addHandler(handler.get_queue_handler())
        logger.info("Async log mesajı")
        # Handler non-blocking şekilde kapanır

asyncio.run(main())
```

#### Formatter Ayarlama

```python
from microlog.handlers import AsyncConsoleHandler
from microlog.formatters import JSONFormatter

handler = AsyncConsoleHandler()
handler.handler.setFormatter(JSONFormatter(service_name="myapp"))
handler.handler.setLevel(logging.DEBUG)

logger.addHandler(handler.get_queue_handler())
```

---

## AsyncConsoleHandler

Asenkron konsol (stdout/stderr) handler. Terminal çıktısı için idealdir.

### Özellikler

- ✅ Asenkron yazma (ana thread bloklanmaz)
- ✅ İsteğe bağlı ERROR+ için stderr'e yönlendirme
- ✅ Özelleştirilebilir stream'ler
- ✅ Log seviyesi filtresi

### Parametreler

```python
AsyncConsoleHandler(
    stream: Any = None,           # Çıktı stream'i (default: stdout)
    level: int = logging.DEBUG,   # Minimum log seviyesi
    error_stream: Any = None,     # Error stream (default: stderr)
    split_errors: bool = False    # ERROR+ logları stderr'e yönlendir
)
```

### Kullanım Örnekleri

#### Temel Kullanım

```python
from microlog.handlers import AsyncConsoleHandler

handler = AsyncConsoleHandler()
logger.addHandler(handler.get_queue_handler())
logger.info("Console'a yazılır")
```

#### ERROR+ için stderr Yönlendirme

```python
handler = AsyncConsoleHandler(split_errors=True)

logger.debug("stdout'a yazılır")
logger.info("stdout'a yazılır")
logger.warning("stdout'a yazılır")
logger.error("stderr'e yazılır")  # ERROR ve üstü
logger.critical("stderr'e yazılır")
```

**Kullanım Senaryosu:**
```bash
# Normal loglar stdout'a, error'lar stderr'e
python app.py > app.log 2> errors.log
```

#### Özel Stream

```python
import sys
from io import StringIO

# StringIO'ya yaz (test için)
output = StringIO()
handler = AsyncConsoleHandler(stream=output)

logger.addHandler(handler.get_queue_handler())
logger.info("Test mesajı")

handler.stop()
content = output.getvalue()
assert "Test mesajı" in content
```

#### Log Seviyesi Filtresi

```python
handler = AsyncConsoleHandler(level=logging.WARNING)

logger.debug("Görünmez")      # DEBUG < WARNING
logger.info("Görünmez")        # INFO < WARNING
logger.warning("Görünür")      # WARNING >= WARNING
logger.error("Görünür")       # ERROR >= WARNING
```

#### setup_console_logger ile

```python
from microlog import setup_console_logger

logger = setup_console_logger(
    name="myapp",
    service_name="api-service",
    use_colors=True
)
# AsyncConsoleHandler otomatik oluşturulur ve yapılandırılır
```

---

## AsyncRotatingFileHandler

Asenkron dönen (rotating) dosya handler. Production log dosyaları için idealdir.

### Özellikler

- ✅ Asenkron dosya yazma
- ✅ Otomatik dosya döndürme (rotation)
- ✅ Gzip sıkıştırma desteği
- ✅ Thread-safe rotation
- ✅ Otomatik dizin oluşturma
- ✅ Backup dosya yönetimi

### Parametreler

```python
AsyncRotatingFileHandler(
    filename: str,                      # Log dosyası yolu
    max_bytes: int = 10 * 1024 * 1024,  # Maksimum dosya boyutu (10MB)
    backup_count: int = 5,              # Saklanacak eski dosya sayısı
    compress: bool = True,               # Eski dosyaları gzip ile sıkıştır
    encoding: str = "utf-8",            # Dosya encoding'i
    level: int = logging.DEBUG           # Minimum log seviyesi
)
```

### Dosya Rotation Mantığı

1. **Dosya boyutu kontrolü**: Her log yazımında dosya boyutu kontrol edilir
2. **Rotation tetiklenir**: `max_bytes` aşıldığında
3. **Backup kaydırma**: Eski backup'lar bir sonraki numaraya kaydırılır
4. **Sıkıştırma**: `compress=True` ise eski dosya gzip ile sıkıştırılır
5. **Eski dosya silme**: `backup_count` limitini aşan dosyalar silinir
6. **Yeni dosya açma**: Yeni log dosyası açılır

### Dosya Adlandırma

```
app.log          # Aktif dosya
app.log.1        # En yeni backup
app.log.2        # İkinci backup
app.log.3        # Üçüncü backup
...
app.log.5        # En eski backup (backup_count=5)

# compress=True ise:
app.log.1.gz     # Sıkıştırılmış backup
app.log.2.gz
...
```

### Kullanım Örnekleri

#### Temel Kullanım

```python
from microlog.handlers import AsyncRotatingFileHandler

handler = AsyncRotatingFileHandler(
    filename="app.log",
    max_bytes=10 * 1024 * 1024,  # 10MB
    backup_count=5
)

logger.addHandler(handler.get_queue_handler())
logger.info("Dosyaya yazılır")
```

#### Sıkıştırma ile

```python
handler = AsyncRotatingFileHandler(
    filename="app.log",
    max_bytes=50 * 1024 * 1024,  # 50MB
    backup_count=10,
    compress=True  # Eski dosyalar .gz olarak saklanır
)
```

#### Sıkıştırma Olmadan

```python
handler = AsyncRotatingFileHandler(
    filename="app.log",
    compress=False  # Eski dosyalar düz metin olarak kalır
)
```

#### Özel Encoding

```python
handler = AsyncRotatingFileHandler(
    filename="app.log",
    encoding="utf-8"  # veya "latin-1", "cp1252", vb.
)
```

#### setup_file_logger ile

```python
from microlog import setup_file_logger

logger = setup_file_logger(
    name="myapp",
    filename="app.log",
    max_bytes=50 * 1024 * 1024,
    backup_count=10,
    compress=True,
    format_type="json"
)
# AsyncRotatingFileHandler otomatik oluşturulur ve yapılandırılır
```

### Rotation Örnekleri

#### Rotation Senaryosu

```python
handler = AsyncRotatingFileHandler(
    filename="app.log",
    max_bytes=1024,  # 1KB (test için küçük)
    backup_count=3
)

logger.addHandler(handler.get_queue_handler())

# 1KB'dan fazla log yaz
for i in range(1000):
    logger.info(f"Log message {i}")

handler.stop()

# Dosya yapısı:
# app.log          (yeni, boş veya küçük)
# app.log.1.gz     (eski, sıkıştırılmış)
# app.log.2.gz     (daha eski)
# app.log.3.gz     (en eski)
```

#### backup_count=1 Edge Case

```python
handler = AsyncRotatingFileHandler(
    filename="app.log",
    max_bytes=1024,
    backup_count=1  # Sadece 1 backup
)

# Rotation sonrası:
# app.log          (yeni)
# app.log.1.gz     (eski, tek backup)
```

### Thread Safety

`AsyncRotatingFileHandler` thread-safe'dir. Birden fazla thread'den aynı anda log yazabilirsiniz:

```python
import threading

handler = AsyncRotatingFileHandler(filename="app.log")
logger.addHandler(handler.get_queue_handler())

def worker(thread_id):
    for i in range(100):
        logger.info(f"Thread {thread_id}: Message {i}")

threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
for t in threads:
    t.start()
for t in threads:
    t.join()

handler.stop()
```

---

## Handler Yaşam Döngüsü

### Başlatma

Handler'lar iki şekilde başlatılabilir:

1. **Manuel başlatma:**
```python
handler = AsyncConsoleHandler()
handler.start()  # Manuel başlat
queue_handler = handler.get_queue_handler()
```

2. **Otomatik başlatma:**
```python
handler = AsyncConsoleHandler()
queue_handler = handler.get_queue_handler()  # Otomatik başlatır
```

### Durdurma

Handler'ları düzgün kapatmak önemlidir:

1. **Manuel durdurma:**
```python
handler.stop()  # Queue'daki tüm loglar yazılır
```

2. **Context manager:**
```python
with AsyncRotatingFileHandler(filename="app.log") as handler:
    # ... kullanım
    # Otomatik stop()
```

3. **atexit (otomatik):**
```python
handler = AsyncRotatingFileHandler(filename="app.log")
# Program kapanırken otomatik stop() çağrılır
```

### stop() Metodu Ne Yapar?

1. **QueueListener'ı durdurur**: Sentinel pattern ile queue boşalır
2. **Listener thread'i bekler**: Maksimum 5 saniye
3. **Handler'ı flush eder**: 3 kez flush (güvenlik için)
4. **Handler'ı kapatır**: `close()` çağrılır

### Örnek: Uygulama Kapanışı

```python
import atexit
from microlog.handlers import AsyncRotatingFileHandler

handler = AsyncRotatingFileHandler(filename="app.log")
logger.addHandler(handler.get_queue_handler())

# atexit zaten kayıtlı, ama manuel de ekleyebilirsiniz
atexit.register(handler.stop)

# ... uygulama çalışır ...

# Program kapanırken:
# 1. atexit.register() çağrılır
# 2. handler.stop() çağrılır
# 3. Queue'daki tüm loglar yazılır
# 4. Handler kapanır
```

---

## Best Practices

### 1. Handler'ları Düzgün Kapatma

```python
# ✅ İyi: Context manager
with AsyncRotatingFileHandler(filename="app.log") as handler:
    logger.addHandler(handler.get_queue_handler())
    logger.info("Log")
    # Otomatik kapanır

# ✅ İyi: Manuel stop
handler = AsyncRotatingFileHandler(filename="app.log")
try:
    logger.addHandler(handler.get_queue_handler())
    logger.info("Log")
finally:
    handler.stop()

# ❌ Kötü: Handler kapatılmadan program kapanıyor
handler = AsyncRotatingFileHandler(filename="app.log")
logger.addHandler(handler.get_queue_handler())
logger.info("Log")
# stop() çağrılmadı - bazı loglar kaybolabilir
```

### 2. Production Yapılandırması

```python
# Production için önerilen yapılandırma
handler = AsyncRotatingFileHandler(
    filename="/var/log/myapp/app.log",
    max_bytes=50 * 1024 * 1024,  # 50MB
    backup_count=10,              # 10 backup (500MB toplam)
    compress=True,                # Disk tasarrufu
    encoding="utf-8"
)
```

### 3. Development Yapılandırması

```python
# Development için console handler
handler = AsyncConsoleHandler(
    level=logging.DEBUG,
    split_errors=True  # ERROR'lar stderr'e
)
```

### 4. Çoklu Handler Kullanımı

```python
from microlog import setup_logger, HandlerConfig
from microlog.handlers import AsyncConsoleHandler, AsyncRotatingFileHandler
from microlog.formatters import PrettyFormatter, JSONFormatter

# Console: Pretty (renkli)
# File: JSON (production)
logger = setup_logger(
    name="myapp",
    handlers=[
        HandlerConfig(
            handler=AsyncConsoleHandler(),
            formatter=PrettyFormatter(service_name="myapp", use_colors=True)
        ),
        HandlerConfig(
            handler=AsyncRotatingFileHandler(
                filename="app.log",
                max_bytes=10 * 1024 * 1024
            ),
            formatter=JSONFormatter(service_name="myapp")
        )
    ]
)
```

### 5. Handler Seviyesi Filtreleme

```python
# Handler seviyesi logger seviyesinden bağımsız
logger.setLevel(logging.DEBUG)  # Logger: DEBUG ve üstü

# Console: Sadece INFO ve üstü
console_handler = AsyncConsoleHandler(level=logging.INFO)

# File: Tüm seviyeler
file_handler = AsyncRotatingFileHandler(
    filename="app.log",
    level=logging.DEBUG
)

logger.addHandler(console_handler.get_queue_handler())
logger.addHandler(file_handler.get_queue_handler())

logger.debug("Sadece dosyaya yazılır")
logger.info("Hem console'a hem dosyaya yazılır")
```

### 6. Rotation Stratejisi

```python
# Yüksek hacimli uygulama
handler = AsyncRotatingFileHandler(
    filename="app.log",
    max_bytes=100 * 1024 * 1024,  # 100MB
    backup_count=20,               # 20 backup (2GB toplam)
    compress=True                  # Disk tasarrufu
)

# Düşük hacimli uygulama
handler = AsyncRotatingFileHandler(
    filename="app.log",
    max_bytes=5 * 1024 * 1024,    # 5MB
    backup_count=5,                # 5 backup (25MB toplam)
    compress=False                 # Sıkıştırma gerekmez
)
```

### 7. Async Uygulamalarda Kullanım

```python
import asyncio
from microlog.handlers import AsyncRotatingFileHandler

async def main():
    async with AsyncRotatingFileHandler(filename="app.log") as handler:
        logger.addHandler(handler.get_queue_handler())
        
        # Async işlemler
        await process_data()
        logger.info("İşlem tamamlandı")
        # Handler non-blocking şekilde kapanır

asyncio.run(main())
```

### 8. Test Ortamında Kullanım

```python
import pytest
from io import StringIO
from microlog.handlers import AsyncConsoleHandler

def test_logging():
    # StringIO'ya yaz (test için)
    output = StringIO()
    handler = AsyncConsoleHandler(stream=output)
    
    logger = logging.getLogger("test")
    logger.addHandler(handler.get_queue_handler())
    logger.setLevel(logging.INFO)
    
    logger.info("Test mesajı")
    handler.stop()  # Queue'yu flush et
    
    content = output.getvalue()
    assert "Test mesajı" in content
```

### 9. Graceful Shutdown

```python
import signal
from microlog.handlers import AsyncRotatingFileHandler

handler = AsyncRotatingFileHandler(filename="app.log")
logger.addHandler(handler.get_queue_handler())

def signal_handler(sig, frame):
    """SIGTERM/SIGINT geldiğinde handler'ı kapat"""
    logger.info("Shutdown signal alındı")
    handler.stop()  # Queue'daki loglar yazılır
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)
```

### 10. Handler Referans Yönetimi

```python
# Handler'ları bir yerde topla (cleanup için)
class App:
    def __init__(self):
        self.handlers = []
        
        console = AsyncConsoleHandler()
        self.handlers.append(console)
        logger.addHandler(console.get_queue_handler())
        
        file = AsyncRotatingFileHandler(filename="app.log")
        self.handlers.append(file)
        logger.addHandler(file.get_queue_handler())
    
    def shutdown(self):
        """Tüm handler'ları kapat"""
        for handler in self.handlers:
            handler.stop()
```

---

## Sorun Giderme

### Handler Kapanmıyor

**Sorun:** Handler'lar program kapanırken düzgün kapanmıyor.

**Çözüm:**
```python
# 1. Context manager kullan
with AsyncRotatingFileHandler(filename="app.log") as handler:
    # ...

# 2. Manuel stop
handler.stop()

# 3. atexit kontrolü
import atexit
atexit.register(handler.stop)
```

### Loglar Görünmüyor

**Sorun:** Log mesajları dosyada veya console'da görünmüyor.

**Çözüm:**
1. **Handler başlatıldı mı?**
```python
handler = AsyncConsoleHandler()
queue_handler = handler.get_queue_handler()  # Otomatik başlatır
logger.addHandler(queue_handler)
```

2. **Log seviyesi kontrolü:**
```python
logger.setLevel(logging.DEBUG)
handler.handler.setLevel(logging.DEBUG)
```

3. **Handler stop edilmeden önce bekle:**
```python
import time
logger.info("Log mesajı")
time.sleep(0.1)  # QueueListener'ın işlemesi için bekle
handler.stop()   # Veya program kapanırken otomatik
```

### Rotation Çalışmıyor

**Sorun:** Dosya boyutu aşıldı ama rotation olmadı.

**Çözüm:**
1. **max_bytes kontrolü:**
```python
handler = AsyncRotatingFileHandler(
    filename="app.log",
    max_bytes=1024  # 1KB (test için)
)
```

2. **Dosya boyutu kontrolü:**
```python
import os
size = os.path.getsize("app.log")
print(f"Dosya boyutu: {size} bytes")
```

3. **Rotation manuel tetikleme:**
```python
# Rotation sadece log yazımında tetiklenir
# Manuel rotation yok, ama test için küçük max_bytes kullan
```

### Dosya İzin Hatası

**Sorun:** Log dosyası yazılamıyor (permission denied).

**Çözüm:**
```python
# 1. Dizin oluşturulur (otomatik)
handler = AsyncRotatingFileHandler(
    filename="/var/log/myapp/app.log"  # Dizin yoksa oluşturulur
)

# 2. İzin kontrolü
import os
log_dir = "/var/log/myapp"
os.makedirs(log_dir, mode=0o755, exist_ok=True)
```

### Queue Taşması

**Sorun:** Çok fazla log yazılıyor, queue doluyor.

**Çözüm:**
```python
# Queue sınırsız boyutta (-1), ama yine de dikkatli olun
# Çok yüksek hacimli uygulamalarda:
# 1. Log seviyesini yükselt (DEBUG -> INFO)
# 2. Handler sayısını azalt
# 3. Log yazma hızını sınırla (rate limiting)
```

### Thread Safety Sorunları

**Sorun:** Birden fazla thread'den log yazarken sorunlar oluyor.

**Çözüm:**
```python
# AsyncHandler thread-safe'dir
# Aynı handler'ı birden fazla thread'den kullanabilirsiniz
handler = AsyncRotatingFileHandler(filename="app.log")
queue_handler = handler.get_queue_handler()

# Thread 1
logger1 = logging.getLogger("thread1")
logger1.addHandler(queue_handler)

# Thread 2
logger2 = logging.getLogger("thread2")
logger2.addHandler(queue_handler)

# Her iki thread de güvenli şekilde log yazabilir
```

### Memory Leak

**Sorun:** Handler'lar kapatılmıyor, memory leak oluşuyor.

**Çözüm:**
```python
# 1. Handler'ları mutlaka kapat
handler.stop()

# 2. Weak reference kullan (gelişmiş)
import weakref
handler = AsyncRotatingFileHandler(filename="app.log")
weak_ref = weakref.ref(handler)
handler.stop()
handler = None
gc.collect()
assert weak_ref() is None  # Garbage collected
```

---

## API Referansı

### AsyncHandler

```python
class AsyncHandler:
    def __init__(self, handler: logging.Handler)
    def start(self) -> None
    def stop(self) -> None
    def get_queue_handler(self) -> QueueHandler
    @property
    def handler(self) -> logging.Handler
    def __enter__(self)
    def __exit__(self, exc_type, exc_val, exc_tb)
    async def __aenter__(self)
    async def __aexit__(self, exc_type, exc_val, exc_tb)
```

### AsyncConsoleHandler

```python
class AsyncConsoleHandler(AsyncHandler):
    def __init__(
        self,
        stream: Any = None,
        level: int = logging.DEBUG,
        error_stream: Any = None,
        split_errors: bool = False
    )
```

### AsyncRotatingFileHandler

```python
class AsyncRotatingFileHandler(AsyncHandler):
    def __init__(
        self,
        filename: str,
        max_bytes: int = 10 * 1024 * 1024,
        backup_count: int = 5,
        compress: bool = True,
        encoding: str = "utf-8",
        level: int = logging.DEBUG
    )
    
    # Public attributes
    filename: str
    max_bytes: int
    backup_count: int
```

---

## Sonraki Adımlar

- [Quick Start Guide](quickstart.md) - Hızlı başlangıç
- [Formatters Documentation](formatters.md) - Log formatları
- [Trace Context Guide](trace-context.md) - Distributed tracing
- [API Reference](api-reference.md) - Tüm API detayları

