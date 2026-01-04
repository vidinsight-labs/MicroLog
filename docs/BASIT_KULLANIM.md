# Basit Kullanım

Bu dokümantasyon, MicroLog'u hızlıca kullanmaya başlamanız için temel örnekler sunar.

## İçindekiler

1. [Hızlı Başlangıç](#hızlı-başlangıç)
2. [Temel Logging](#temel-logging)
3. [Trace Context](#trace-context)
4. [Dosya Logging](#dosya-logging)
5. [Decorator Kullanımı](#decorator-kullanımı)

---

## Hızlı Başlangıç

### En Basit Kullanım

```python
from microlog import setup_logger
import logging

# Logger oluştur
logger = setup_logger("myapp")

# Log yaz
logger.info("Merhaba MicroLog!")
```

### Log Seviyesi Belirleme

```python
from microlog import setup_logger
import logging

# DEBUG seviyesinde logger
logger = setup_logger("myapp", level=logging.DEBUG)

logger.debug("Debug mesajı")
logger.info("Bilgi mesajı")
logger.warning("Uyarı mesajı")
logger.error("Hata mesajı")
```

---

## Temel Logging

### Basit Mesajlar

```python
from microlog import setup_logger
import logging

logger = setup_logger("myapp", level=logging.INFO)

# Farklı seviyelerde log
logger.debug("Detaylı bilgi")      # Geliştirme için
logger.info("Bilgilendirme")        # Normal işlemler
logger.warning("Uyarı")             # Dikkat gerektiren
logger.error("Hata")                # Hatalar
logger.critical("Kritik hata")       # Sistem çöküşü riski
```

### Exception Logging

```python
try:
    risky_operation()
except Exception as e:
    # Stack trace ile birlikte logla
    logger.error("İşlem başarısız", exc_info=True)
```

### Ekstra Bilgiler Ekleme

```python
logger.info("Kullanıcı girişi", extra={
    "user_id": 123,
    "ip_address": "192.168.1.1"
})
```

---

## Trace Context

### Basit Trace

```python
from microlog import setup_logger, trace
import logging

logger = setup_logger("myapp")

# Trace context ile
with trace(trace_id="request-123"):
    logger.info("İşlem başladı")
    # trace_id otomatik olarak loglara eklenir
```

### Request ID ile

```python
import uuid

def handle_request():
    request_id = str(uuid.uuid4())
    
    with trace(trace_id=request_id):
        logger.info("İstek alındı")
        # ... işlemler ...
        logger.info("İstek tamamlandı")
```

### Nested Trace (İç İçe)

```python
with trace(trace_id="parent-request") as parent:
    logger.info("Ana işlem")
    
    # Alt işlem
    with trace(trace_id=parent.trace_id, parent_span_id=parent.span_id):
        logger.info("Alt işlem")
```

---

## Dosya Logging

### Basit Dosya Logging

```python
from microlog import setup_file_logger

# Otomatik rotation ile
logger = setup_file_logger(
    name="myapp",
    filename="logs/app.log",
    max_bytes=10_000_000,  # 10 MB
    backup_count=5
)

logger.info("Dosyaya yazıldı")
```

### Compression ile

```python
from microlog import setup_file_logger

logger = setup_file_logger(
    name="myapp",
    filename="logs/app.log",
    max_bytes=10_000_000,
    backup_count=5,
    compress=True  # Gzip compression
)
```

---

## Decorator Kullanımı

### @log_function

```python
from microlog import log_function
import logging

@log_function(level=logging.INFO)
def calculate_total(items):
    total = sum(item.price for item in items)
    return total

# Otomatik olarak fonksiyon çağrısı ve sonucu loglanır
result = calculate_total(items)
```

### @log_exception

```python
from microlog import log_exception
import logging

@log_exception(level=logging.ERROR)
def risky_operation():
    if random.random() < 0.5:
        raise ValueError("Hata")
    return "Başarılı"

# Exception oluşursa otomatik loglanır
risky_operation()
```

### @log_performance

```python
from microlog import log_performance
import logging

@log_performance(level=logging.INFO)
def slow_operation():
    time.sleep(1)
    return "Tamamlandı"

# İşlem süresi otomatik loglanır
slow_operation()
```

---

## Örnek: Basit API Servisi

```python
from flask import Flask
from microlog import setup_logger, trace
import logging
import uuid

app = Flask(__name__)
logger = setup_logger("api-service", level=logging.INFO)

@app.route("/api/users/<user_id>")
def get_user(user_id):
    request_id = str(uuid.uuid4())
    
    with trace(trace_id=request_id):
        logger.info("Kullanıcı bilgisi isteniyor", extra={"user_id": user_id})
        
        try:
            user = fetch_user(user_id)
            logger.info("Kullanıcı bulundu", extra={"user_id": user_id})
            return jsonify(user)
        except Exception as e:
            logger.error("Hata oluştu", exc_info=True, extra={"user_id": user_id})
            return jsonify({"error": "Internal error"}), 500
```

---

## Sonraki Adımlar

- **[Detaylı Kullanım](DETAYLI_KULLANIM.md)** - Tüm özellikler ve gelişmiş kullanım
- **[API Referansı](API_REFERANSI.md)** - Tüm fonksiyonlar ve parametreler
- **[Çalışma Mantığı](CALISMA_MANTIGI.md)** - Nasıl çalışıyor
- **[Davranış Şekli](DAVRANIS_SEKLI.md)** - Davranışlar ve best practices

