# Formatters - Log Formatları

MicroLog, farklı kullanım senaryoları için üç formatter sağlar: **JSONFormatter**, **PrettyFormatter** ve **CompactFormatter**. Bu doküman, her formatter'ın özelliklerini, parametrelerini ve kullanım örneklerini detaylı olarak açıklar.

## İçindekiler

- [JSONFormatter](#jsonformatter)
- [PrettyFormatter](#prettyformatter)
- [CompactFormatter](#compactformatter)
- [create_formatter Factory Fonksiyonu](#create_formatter-factory-fonksiyonu)
- [Formatter Seçimi](#formatter-seçimi)
- [Özelleştirme](#özelleştirme)
- [Best Practices](#best-practices)

---

## JSONFormatter

Yapılandırılmış JSON formatı. Log aggregation sistemleri (ELK Stack, Datadog, Splunk, CloudWatch) için idealdir.

### Özellikler

- ✅ ISO 8601 veya Unix timestamp
- ✅ Extra alanlar otomatik eklenir
- ✅ Exception detayları (type, message, traceback)
- ✅ Thread-safe (record.created kullanır)
- ✅ Opsiyonel lokasyon bilgisi (file, line, function)
- ✅ JSON serialization hata koruması

### Parametreler

```python
JSONFormatter(
    service_name: Optional[str] = None,      # Servis adı (default: logger name)
    include_extra: bool = True,               # Extra alanları dahil et
    timestamp_format: str = "iso",           # "iso" veya "unix"
    include_location: bool = False            # Dosya/satır bilgisi ekle
)
```

### Kullanım Örnekleri

#### Temel Kullanım

```python
from microlog import setup_logger, HandlerConfig
from microlog.handlers import AsyncRotatingFileHandler
from microlog.formatters import JSONFormatter

formatter = JSONFormatter(service_name="order-service")

logger = setup_logger(
    name="myapp",
    handlers=[
        HandlerConfig(
            handler=AsyncRotatingFileHandler(filename="app.log"),
            formatter=formatter
        )
    ]
)

logger.info("Sipariş oluşturuldu", extra={
    "order_id": "ORD-123",
    "user_id": "usr-456",
    "amount": 99.99
})
```

**Çıktı:**
```json
{
  "timestamp": "2025-01-07T14:32:01.123456+00:00",
  "level": "INFO",
  "service": "order-service",
  "message": "Sipariş oluşturuldu",
  "order_id": "ORD-123",
  "user_id": "usr-456",
  "amount": 99.99
}
```

#### Lokasyon Bilgisi ile

```python
formatter = JSONFormatter(
    service_name="api-service",
    include_location=True  # Dosya, satır ve fonksiyon bilgisi ekler
)

logger.info("API çağrısı yapıldı")
```

**Çıktı:**
```json
{
  "timestamp": "2025-01-07T14:32:01.123456+00:00",
  "level": "INFO",
  "service": "api-service",
  "message": "API çağrısı yapıldı",
  "location": {
    "file": "api.py",
    "line": 42,
    "function": "handle_request"
  }
}
```

#### Unix Timestamp Formatı

```python
formatter = JSONFormatter(
    service_name="analytics",
    timestamp_format="unix"  # Unix timestamp (float)
)

logger.info("Event logged")
```

**Çıktı:**
```json
{
  "timestamp": "1704634321.123456",
  "level": "INFO",
  "service": "analytics",
  "message": "Event logged"
}
```

#### Exception Loglama

```python
formatter = JSONFormatter(service_name="error-service")

try:
    risky_operation()
except Exception:
    logger.exception("İşlem başarısız")
```

**Çıktı:**
```json
{
  "timestamp": "2025-01-07T14:32:01.123456+00:00",
  "level": "ERROR",
  "service": "error-service",
  "message": "İşlem başarısız",
  "exception": {
    "type": "ValueError",
    "message": "Invalid input",
    "traceback": "Traceback (most recent call last):\n  File \"app.py\", line 42, in risky_operation\n    raise ValueError(\"Invalid input\")\nValueError: Invalid input"
  }
}
```

#### Extra Alanları Devre Dışı Bırakma

```python
formatter = JSONFormatter(
    service_name="minimal-service",
    include_extra=False  # Sadece temel alanlar
)

logger.info("Log mesajı", extra={"key": "value"})  # extra alanı eklenmez
```

**Çıktı:**
```json
{
  "timestamp": "2025-01-07T14:32:01.123456+00:00",
  "level": "INFO",
  "service": "minimal-service",
  "message": "Log mesajı"
}
```

### JSON Serialization

JSONFormatter, tüm değerleri otomatik olarak JSON-safe formata dönüştürür:

- **Primitif tipler**: `str`, `int`, `float`, `bool`, `None` → olduğu gibi
- **Liste/Tuple**: Liste olarak serialize edilir
- **Dict**: JSON object olarak
- **Set/Frozenset**: Liste olarak
- **Datetime**: ISO 8601 string
- **Bytes**: UTF-8 decode edilir (başarısız olursa `<bytes len=N>` formatında)
- **Diğer tipler**: `str()` ile string'e çevrilir
- **Recursive yapılar**: Maksimum 10 derinlik koruması

**Örnek:**
```python
logger.info("Complex data", extra={
    "numbers": [1, 2, 3],
    "metadata": {"key": "value"},
    "timestamp": datetime.now(),
    "tags": {"python", "logging"}
})
```

**Çıktı:**
```json
{
  "timestamp": "2025-01-07T14:32:01.123456+00:00",
  "level": "INFO",
  "service": "myapp",
  "message": "Complex data",
  "numbers": [1, 2, 3],
  "metadata": {"key": "value"},
  "timestamp": "2025-01-07T14:32:01.123456+00:00",
  "tags": ["python", "logging"]
}
```

---

## PrettyFormatter

Terminal için renkli ve okunabilir log formatı. Geliştirme ortamında kullanım için idealdir.

### Özellikler

- ✅ ANSI renk kodları (opsiyonel)
- ✅ Okunabilir tablo formatı
- ✅ Extra alanlar key=value formatında
- ✅ Exception traceback renkli gösterim
- ✅ UTC veya local timezone desteği
- ✅ Tarih gösterimi (opsiyonel)

### Parametreler

```python
PrettyFormatter(
    service_name: Optional[str] = None,  # Servis adı (default: logger name)
    use_colors: bool = True,              # ANSI renkleri kullan
    use_utc: bool = False,                # UTC zaman kullan (default: local)
    show_date: bool = False                # Tarih göster (default: sadece saat)
)
```

### Renk Kodları

| Level    | Renk      | ANSI Kodu |
|----------|-----------|-----------|
| DEBUG    | Cyan      | `\033[36m` |
| INFO     | Green     | `\033[32m` |
| WARNING  | Yellow    | `\033[33m` |
| ERROR    | Red       | `\033[31m` |
| CRITICAL | Magenta   | `\033[35;1m` (Bold) |

### Kullanım Örnekleri

#### Temel Kullanım (Renkli)

```python
from microlog import setup_console_logger

logger = setup_console_logger(
    name="myapp",
    service_name="order-service",
    use_colors=True
)

logger.debug("Debug mesajı")
logger.info("Bilgi mesajı")
logger.warning("Uyarı mesajı")
logger.error("Hata mesajı")
logger.critical("Kritik hata")
```

**Çıktı (renkli):**
```
14:32:01 │ DEBUG    │ order-service   │ Debug mesajı
14:32:02 │ INFO     │ order-service   │ Bilgi mesajı
14:32:03 │ WARNING  │ order-service   │ Uyarı mesajı
14:32:04 │ ERROR    │ order-service   │ Hata mesajı
14:32:05 │ CRITICAL │ order-service   │ Kritik hata
```

#### Extra Alanlar ile

```python
logger.info("Sipariş oluşturuldu", extra={
    "order_id": "ORD-123",
    "user_id": "usr-456",
    "amount": 99.99
})
```

**Çıktı:**
```
14:32:01 │ INFO     │ order-service   │ Sipariş oluşturuldu │ order_id=ORD-123 user_id=usr-456 amount=99.99
```

#### Renksiz Mod (CI/CD için)

```python
from microlog.formatters import PrettyFormatter
from microlog import setup_logger, HandlerConfig
from microlog.handlers import AsyncConsoleHandler

formatter = PrettyFormatter(
    service_name="ci-service",
    use_colors=False  # ANSI kodları yok
)

logger = setup_logger(
    name="myapp",
    handlers=[
        HandlerConfig(
            handler=AsyncConsoleHandler(),
            formatter=formatter
        )
    ]
)
```

**Çıktı (renksiz):**
```
14:32:01 │ INFO     │ ci-service      │ Log mesajı
```

#### UTC Zaman ile

```python
formatter = PrettyFormatter(
    service_name="api-service",
    use_utc=True  # UTC zaman kullan
)

logger.info("UTC zaman ile log")
```

**Çıktı:**
```
12:32:01 │ INFO     │ api-service     │ UTC zaman ile log
```

#### Tarih Gösterimi

```python
formatter = PrettyFormatter(
    service_name="audit-service",
    show_date=True  # Tarih + saat
)

logger.info("Audit log")
```

**Çıktı:**
```
2025-01-07 14:32:01 │ INFO     │ audit-service   │ Audit log
```

#### Exception Gösterimi

```python
try:
    risky_operation()
except Exception:
    logger.exception("İşlem başarısız")
```

**Çıktı (renkli):**
```
14:32:01 │ ERROR    │ order-service   │ İşlem başarısız
Traceback (most recent call last):
  File "app.py", line 42, in risky_operation
    raise ValueError("Invalid input")
ValueError: Invalid input
```

### Format Yapısı

```
[ZAMAN] │ [LEVEL] │ [SERVICE] │ [MESAJ] │ [EXTRA_ALANLAR]
```

- **ZAMAN**: `HH:MM:SS` (veya `YYYY-MM-DD HH:MM:SS` if `show_date=True`)
- **LEVEL**: 8 karakter genişliğinde, renkli
- **SERVICE**: 15 karakter genişliğinde, bold
- **MESAJ**: Log mesajı
- **EXTRA_ALANLAR**: `key=value` formatında, dim renk

---

## CompactFormatter

Minimal tek satır format. Production log dosyaları için idealdir. Dosya boyutunu küçük tutar.

### Özellikler

- ✅ Minimal format (tek satır)
- ✅ Boşluk içeren değerler için quote desteği
- ✅ Exception bilgisi (type ve kısa mesaj)
- ✅ Opsiyonel timestamp
- ✅ Dosya boyutu optimizasyonu

### Parametreler

```python
CompactFormatter(
    service_name: Optional[str] = None,  # Servis adı (default: logger name)
    include_timestamp: bool = False        # Zaman damgası ekle (default: hayır)
)
```

### Kullanım Örnekleri

#### Temel Kullanım

```python
from microlog import setup_file_logger

logger = setup_file_logger(
    name="myapp",
    filename="app.log",
    format_type="compact"
)

logger.info("Sipariş oluşturuldu", extra={
    "order_id": "ORD-123",
    "user_id": "usr-456"
})
```

**Çıktı:**
```
INFO myapp Sipariş oluşturuldu order_id=ORD-123 user_id=usr-456
```

#### Timestamp ile

```python
from microlog.formatters import CompactFormatter
from microlog import setup_logger, HandlerConfig
from microlog.handlers import AsyncRotatingFileHandler

formatter = CompactFormatter(
    service_name="api-service",
    include_timestamp=True
)

logger = setup_logger(
    name="myapp",
    handlers=[
        HandlerConfig(
            handler=AsyncRotatingFileHandler(filename="app.log"),
            formatter=formatter
        )
    ]
)

logger.info("Event logged")
```

**Çıktı:**
```
20250107T143201 INFO api-service Event logged
```

#### Boşluk İçeren Değerler

```python
logger.info("Kullanıcı giriş yaptı", extra={
    "user_name": "John Doe",
    "message": "Welcome back"
})
```

**Çıktı:**
```
INFO myapp Kullanıcı giriş yaptı user_name="John Doe" message="Welcome back"
```

#### Exception Bilgisi

```python
try:
    risky_operation()
except Exception:
    logger.exception("İşlem başarısız")
```

**Çıktı:**
```
ERROR myapp İşlem başarısız exc_type=ValueError exc_msg="Invalid input"
```

**Not:** Exception mesajı 100 karakter ile sınırlandırılır ve yeni satırlar boşlukla değiştirilir.

### Format Yapısı

```
[ZAMAN] LEVEL SERVICE MESAJ key1=value1 key2="value with spaces" exc_type=Type exc_msg="message"
```

- **ZAMAN**: Opsiyonel, `YYYYMMDDTHHMMSS` formatında (UTC)
- **LEVEL**: Log seviyesi (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- **SERVICE**: Servis adı
- **MESAJ**: Log mesajı
- **EXTRA_ALANLAR**: `key=value` formatında
- **EXCEPTION**: `exc_type=Type exc_msg="message"` formatında

---

## create_formatter Factory Fonksiyonu

Formatter oluşturmayı kolaylaştıran factory fonksiyonu.

### Kullanım

```python
from microlog.formatters import create_formatter

# JSON formatter
formatter = create_formatter(
    format_type="json",
    service_name="api-service",
    include_location=True
)

# Pretty formatter
formatter = create_formatter(
    format_type="pretty",
    service_name="dev-service",
    use_colors=True,
    use_utc=False
)

# Compact formatter
formatter = create_formatter(
    format_type="compact",
    service_name="prod-service",
    include_timestamp=True
)
```

### Parametreler

```python
create_formatter(
    format_type: str = "json",           # "json", "pretty", veya "compact"
    service_name: Optional[str] = None,   # Servis adı
    **kwargs                             # Formatter'a özel parametreler
) -> logging.Formatter
```

### Örnekler

#### Dinamik Formatter Seçimi

```python
import os
from microlog.formatters import create_formatter

# Ortam değişkenine göre formatter seç
env = os.getenv("LOG_FORMAT", "json")

formatter = create_formatter(
    format_type=env,
    service_name="myapp",
    use_colors=(env == "pretty")  # Sadece pretty için renk
)
```

#### Yapılandırma Dosyasından

```python
import json
from microlog.formatters import create_formatter

with open("config.json") as f:
    config = json.load(f)

formatter = create_formatter(
    format_type=config["log_format"],
    service_name=config["service_name"],
    **config.get("formatter_options", {})
)
```

---

## Formatter Seçimi

### Ne Zaman Hangi Formatter?

| Senaryo | Önerilen Formatter | Neden |
|---------|-------------------|-------|
| **Development** | `PrettyFormatter` | Renkli, okunabilir çıktı |
| **Production (JSON)** | `JSONFormatter` | Log aggregation sistemleri için |
| **Production (Compact)** | `CompactFormatter` | Minimal dosya boyutu |
| **CI/CD Pipeline** | `PrettyFormatter` (renksiz) | Okunabilir ama ANSI kodları yok |
| **Docker Container** | `JSONFormatter` | stdout/stderr için JSON |
| **File Logging** | `JSONFormatter` veya `CompactFormatter` | Dosya boyutu ve parse kolaylığı |

### Karşılaştırma

#### Dosya Boyutu

```
CompactFormatter < JSONFormatter < PrettyFormatter
```

#### Parse Kolaylığı

```
JSONFormatter > CompactFormatter > PrettyFormatter
```

#### Okunabilirlik (Terminal)

```
PrettyFormatter > CompactFormatter > JSONFormatter
```

#### Log Aggregation Uyumluluğu

```
JSONFormatter > CompactFormatter > PrettyFormatter
```

---

## Özelleştirme

### Özel Formatter Oluşturma

MicroLog formatter'ları `logging.Formatter`'dan türetilir. Kendi formatter'ınızı oluşturabilirsiniz:

```python
import logging
from microlog.formatters import get_extra_fields, get_record_timestamp

class CustomFormatter(logging.Formatter):
    """Özel formatter örneği"""
    
    def __init__(self, service_name: str = None):
        super().__init__()
        self.service_name = service_name
    
    def format(self, record: logging.LogRecord) -> str:
        """Log kaydını özel formata dönüştür"""
        dt = get_record_timestamp(record, use_utc=True)
        service = self.service_name or record.name
        message = record.getMessage()
        extras = get_extra_fields(record)
        
        # Özel format
        parts = [
            dt.strftime("%Y-%m-%d %H:%M:%S"),
            f"[{record.levelname}]",
            f"<{service}>",
            message
        ]
        
        # Extra alanları ekle
        if extras:
            extra_str = " ".join(f"{k}={v}" for k, v in extras.items())
            parts.append(f"({extra_str})")
        
        return " ".join(parts)
```

**Kullanım:**
```python
from microlog import setup_logger, HandlerConfig
from microlog.handlers import AsyncConsoleHandler

formatter = CustomFormatter(service_name="custom-service")

logger = setup_logger(
    name="myapp",
    handlers=[
        HandlerConfig(
            handler=AsyncConsoleHandler(),
            formatter=formatter
        )
    ]
)

logger.info("Özel formatter ile log")
```

**Çıktı:**
```
2025-01-07 14:32:01 [INFO] <custom-service> Özel formatter ile log
```

### Yardımcı Fonksiyonlar

MicroLog, formatter geliştirmek için yardımcı fonksiyonlar sağlar:

```python
from microlog.formatters import (
    get_record_timestamp,      # Timestamp al
    serialize_value,           # JSON-safe serialize
    get_extra_fields,          # Extra alanları al
    format_exception_info      # Exception bilgisi formatla
)
```

**Örnek:**
```python
from microlog.formatters import get_extra_fields, serialize_value

class MyFormatter(logging.Formatter):
    def format(self, record):
        extras = get_extra_fields(record)  # Extra alanları al
        # ... formatla
```

---

## Best Practices

### 1. Production için JSONFormatter

```python
# Production ortamı
formatter = JSONFormatter(
    service_name="api-service",
    timestamp_format="iso",
    include_location=False  # Gereksiz bilgi ekleme
)
```

### 2. Development için PrettyFormatter

```python
# Development ortamı
formatter = PrettyFormatter(
    service_name="dev-service",
    use_colors=True,
    use_utc=False,  # Local time daha okunabilir
    show_date=False  # Sadece saat yeterli
)
```

### 3. Dosya Boyutu Optimizasyonu

```python
# Büyük log dosyaları için CompactFormatter
formatter = CompactFormatter(
    service_name="high-volume-service",
    include_timestamp=False  # Timestamp eklemeyerek boyut küçült
)
```

### 4. Trace Context ile Kullanım

Formatter'lar trace context bilgilerini otomatik ekler (TraceContextFilter sayesinde):

```python
from microlog import trace, setup_logger

logger = setup_logger("myapp")

with trace(correlation_id="req-123") as ctx:
    logger.info("İstek alındı")
    # trace_id ve span_id otomatik eklenir
```

**JSONFormatter çıktısı:**
```json
{
  "timestamp": "...",
  "level": "INFO",
  "service": "myapp",
  "message": "İstek alındı",
  "trace_id": "abc123...",
  "span_id": "def456...",
  "correlation_id": "req-123"
}
```

### 5. Exception Loglama

```python
# Doğru kullanım
try:
    risky_operation()
except Exception:
    logger.exception("İşlem başarısız")  # exc_info otomatik eklenir

# Yanlış kullanım
try:
    risky_operation()
except Exception as e:
    logger.error(f"İşlem başarısız: {e}")  # Traceback yok
```

### 6. Extra Alanlar

```python
# İyi: Yapılandırılmış extra alanlar
logger.info("Sipariş oluşturuldu", extra={
    "order_id": "ORD-123",
    "user_id": "usr-456",
    "amount": 99.99,
    "currency": "USD"
})

# Kötü: Mesaj içinde bilgi
logger.info(f"Sipariş oluşturuldu: order_id=ORD-123, user_id=usr-456")
```

### 7. Formatter'ı Handler ile Kullanım

```python
from microlog import setup_logger, HandlerConfig
from microlog.handlers import AsyncConsoleHandler, AsyncRotatingFileHandler
from microlog.formatters import JSONFormatter, PrettyFormatter

# Console: Pretty, File: JSON
logger = setup_logger(
    name="myapp",
    handlers=[
        HandlerConfig(
            handler=AsyncConsoleHandler(),
            formatter=PrettyFormatter(service_name="myapp", use_colors=True)
        ),
        HandlerConfig(
            handler=AsyncRotatingFileHandler(filename="app.log"),
            formatter=JSONFormatter(service_name="myapp")
        )
    ]
)
```

### 8. Ortam Bazlı Yapılandırma

```python
import os
from microlog.formatters import create_formatter

# Ortam değişkenine göre formatter seç
env = os.getenv("ENVIRONMENT", "development")

if env == "production":
    formatter = create_formatter(
        "json",
        service_name="api-service",
        include_location=False
    )
elif env == "development":
    formatter = create_formatter(
        "pretty",
        service_name="dev-service",
        use_colors=True
    )
else:
    formatter = create_formatter(
        "compact",
        service_name="test-service"
    )
```

---

## Sorun Giderme

### JSON Serialization Hatası

**Sorun:** Bazı değerler JSON'a serialize edilemiyor.

**Çözüm:** JSONFormatter otomatik fallback sağlar. Yine de sorun yaşıyorsanız:

```python
# Değerleri önceden serialize et
from microlog.formatters import serialize_value

data = {
    "complex_obj": serialize_value(complex_object)
}
logger.info("Log", extra=data)
```

### Renkler Terminal'de Görünmüyor

**Sorun:** PrettyFormatter renkleri görünmüyor.

**Çözüm:** Terminal'iniz ANSI renk kodlarını desteklemiyor olabilir:

```python
formatter = PrettyFormatter(
    service_name="myapp",
    use_colors=False  # Renkleri kapat
)
```

### Timestamp Tutarsızlığı

**Sorun:** Farklı formatter'larda farklı timestamp'ler görünüyor.

**Çözüm:** Tüm formatter'lar `record.created` kullanır (format anı değil). Bu normaldir ve thread-safe'dir.

### Extra Alanlar Eklenmiyor

**Sorun:** `extra` parametresi ile eklenen alanlar görünmüyor.

**Çözüm:** `include_extra=False` olabilir veya alan adı reserved olabilir:

```python
# Reserved alanlar: name, msg, args, levelname, levelno, pathname, filename, ...
# Bu alanlar otomatik filtrelenir
```

---

## API Referansı

### JSONFormatter

```python
class JSONFormatter(logging.Formatter):
    def __init__(
        self,
        service_name: Optional[str] = None,
        include_extra: bool = True,
        timestamp_format: str = "iso",
        include_location: bool = False
    )
```

### PrettyFormatter

```python
class PrettyFormatter(logging.Formatter):
    def __init__(
        self,
        service_name: Optional[str] = None,
        use_colors: bool = True,
        use_utc: bool = False,
        show_date: bool = False
    )
```

### CompactFormatter

```python
class CompactFormatter(logging.Formatter):
    def __init__(
        self,
        service_name: Optional[str] = None,
        include_timestamp: bool = False
    )
```

### create_formatter

```python
def create_formatter(
    format_type: str = "json",
    service_name: Optional[str] = None,
    **kwargs
) -> logging.Formatter
```

---

## Sonraki Adımlar

- [Quick Start Guide](quickstart.md) - Hızlı başlangıç
- [Handlers Documentation](handlers.md) - Handler'lar hakkında
- [Trace Context Guide](trace-context.md) - Distributed tracing
- [API Reference](api-reference.md) - Tüm API detayları

