# API Referansı

Bu dokümantasyon, MicroLog'un tüm API'lerini, fonksiyonlarını, classlarını ve parametrelerini detaylı olarak açıklar.

## İçindekiler

1. [Core Functions](#core-functions)
2. [Context Management](#context-management)
3. [Handlers](#handlers)
4. [Formatters](#formatters)
5. [Decorators](#decorators)
6. [Utility Functions](#utility-functions)

---

## Core Functions

### setup_logger

Logger oluşturur ve yapılandırır.

```python
def setup_logger(
    name: str = "root",
    level: int = logging.INFO,
    service_name: Optional[str] = None,
    handlers: Optional[List[logging.Handler]] = None,
    formatter: Optional[logging.Formatter] = None,
    add_trace_filter: bool = True
) -> logging.Logger
```

**Parametreler:**
- `name` (str): Logger adı (default: "root")
- `level` (int): Log seviyesi (default: logging.INFO)
- `service_name` (Optional[str]): Servis adı (formatter'lara geçilir)
- `handlers` (Optional[List[Handler]]): Handler listesi (default: console handler)
- `formatter` (Optional[Formatter]): Formatter (default: PrettyFormatter)
- `add_trace_filter` (bool): Trace context filter ekle (default: True)

**Dönüş:**
- `logging.Logger`: Yapılandırılmış Logger instance

**Örnek:**
```python
logger = setup_logger("myapp", level=logging.DEBUG)
```

---

### setup_file_logger

Dosya logging için logger oluşturur.

```python
def setup_file_logger(
    name: str,
    filename: str,
    max_bytes: int = 10_000_000,
    backup_count: int = 5,
    compress: bool = False,
    level: int = logging.INFO
) -> logging.Logger
```

**Parametreler:**
- `name` (str): Logger adı
- `filename` (str): Log dosyası yolu
- `max_bytes` (int): Rotation için maksimum dosya boyutu (default: 10_000_000)
- `backup_count` (int): Saklanacak backup dosya sayısı (default: 5)
- `compress` (bool): Rotation sonrası gzip compression (default: False)
- `level` (int): Log seviyesi (default: logging.INFO)

**Dönüş:**
- `logging.Logger`: Yapılandırılmış Logger instance

**Örnek:**
```python
logger = setup_file_logger(
    name="myapp",
    filename="logs/app.log",
    max_bytes=50_000_000,
    backup_count=10,
    compress=True
)
```

---

### setup_production_logger

Production için optimize edilmiş logger oluşturur.

```python
def setup_production_logger(
    name: str,
    log_file: str,
    level: int = logging.INFO
) -> logging.Logger
```

**Parametreler:**
- `name` (str): Logger adı
- `log_file` (str): Log dosyası yolu
- `level` (int): Log seviyesi (default: logging.INFO)

**Dönüş:**
- `logging.Logger`: Yapılandırılmış Logger instance

**Örnek:**
```python
logger = setup_production_logger("myapp", "logs/production.log")
```

---

### setup_console_logger

Console logging için logger oluşturur.

```python
def setup_console_logger(
    name: str = "root",
    level: int = logging.INFO,
    formatter: Optional[logging.Formatter] = None
) -> logging.Logger
```

**Parametreler:**
- `name` (str): Logger adı (default: "root")
- `level` (int): Log seviyesi (default: logging.INFO)
- `formatter` (Optional[Formatter]): Formatter (default: PrettyFormatter)

**Dönüş:**
- `logging.Logger`: Yapılandırılmış Logger instance

---

### get_logger

Mevcut logger'ı döndürür veya yeni oluşturur.

```python
def get_logger(name: str = "root") -> logging.Logger
```

**Parametreler:**
- `name` (str): Logger adı (default: "root")

**Dönüş:**
- `logging.Logger`: Logger instance

---

## Context Management

### trace

Trace context manager oluşturur.

```python
def trace(
    trace_id: Optional[str] = None,
    span_id: Optional[str] = None,
    parent_span_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
    session_id: Optional[str] = None
) -> TraceContextManager
```

**Parametreler:**
- `trace_id` (Optional[str]): Trace ID (yoksa otomatik oluşturulur)
- `span_id` (Optional[str]): Span ID (yoksa otomatik oluşturulur)
- `parent_span_id` (Optional[str]): Parent span ID
- `correlation_id` (Optional[str]): Correlation ID
- `session_id` (Optional[str]): Session ID

**Dönüş:**
- `TraceContextManager`: Context manager instance

**Örnek:**
```python
with trace(trace_id="req-123") as ctx:
    logger.info("İşlem")
    print(ctx.span_id)
```

**Async Kullanım:**
```python
async with trace(trace_id="req-123"):
    logger.info("Async işlem")
```

---

### get_current_context

Aktif trace context'i döndürür.

```python
def get_current_context() -> Optional[TraceContext]
```

**Dönüş:**
- `Optional[TraceContext]`: Aktif context veya None

**Örnek:**
```python
ctx = get_current_context()
if ctx:
    print(f"Trace ID: {ctx.trace_id}")
```

---

### from_headers

HTTP header'lardan trace context parametrelerini çıkarır.

```python
def from_headers(headers: Dict[str, str]) -> Dict[str, str]
```

**Parametreler:**
- `headers` (Dict[str, str]): HTTP header dictionary

**Dönüş:**
- `Dict[str, str]`: Trace context parametreleri

**Örnek:**
```python
headers = {
    "X-Trace-ID": "trace-123",
    "X-Span-ID": "span-456"
}
with trace(**from_headers(headers)):
    logger.info("İstek")
```

---

### TraceContext

Trace context data class.

```python
class TraceContext:
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    correlation_id: Optional[str]
    session_id: Optional[str]
    
    def to_dict() -> Dict[str, Any]
```

**Metodlar:**
- `to_dict()`: Context'i dictionary'ye dönüştürür

---

## Handlers

### AsyncHandler

Asenkron handler base class.

```python
class AsyncHandler:
    def __init__(self, handler: logging.Handler, level: int = logging.NOTSET)
    def start() -> None
    def stop() -> None
    def get_queue_handler() -> QueueHandler
```

**Metodlar:**
- `start()`: Async listener'ı başlatır
- `stop()`: Async listener'ı durdurur ve kaynakları temizler
- `get_queue_handler()`: QueueHandler döndürür

---

### AsyncConsoleHandler

Console için asenkron handler.

```python
class AsyncConsoleHandler(AsyncHandler):
    def __init__(
        self,
        level: int = logging.NOTSET,
        stream: Optional[TextIO] = None
    )
```

**Parametreler:**
- `level` (int): Minimum log seviyesi (default: NOTSET)
- `stream` (Optional[TextIO]): Output stream (default: sys.stderr)

**Örnek:**
```python
handler = AsyncConsoleHandler(level=logging.INFO)
handler.start()
logger.addHandler(handler.get_queue_handler())
```

---

### AsyncRotatingFileHandler

Dosya rotation için asenkron handler.

```python
class AsyncRotatingFileHandler(AsyncHandler):
    def __init__(
        self,
        filename: str,
        max_bytes: int = 10_000_000,
        backup_count: int = 5,
        compress: bool = False,
        level: int = logging.NOTSET
    )
```

**Parametreler:**
- `filename` (str): Log dosyası yolu
- `max_bytes` (int): Rotation için maksimum dosya boyutu (default: 10_000_000)
- `backup_count` (int): Saklanacak backup dosya sayısı (default: 5)
- `compress` (bool): Rotation sonrası gzip compression (default: False)
- `level` (int): Minimum log seviyesi (default: NOTSET)

**Örnek:**
```python
handler = AsyncRotatingFileHandler(
    filename="logs/app.log",
    max_bytes=10_000_000,
    backup_count=5,
    compress=True
)
handler.start()
logger.addHandler(handler.get_queue_handler())
```

---

### AsyncSMTPHandler

Email bildirimleri için asenkron handler.

```python
class AsyncSMTPHandler(AsyncHandler):
    def __init__(
        self,
        mailhost: Union[str, Tuple[str, int]],
        fromaddr: str,
        toaddrs: List[str],
        subject: str,
        credentials: Optional[Tuple[str, str]] = None,
        rate_limit_seconds: int = 300,
        level: int = logging.NOTSET
    )
```

**Parametreler:**
- `mailhost` (Union[str, Tuple[str, int]]): SMTP sunucu adresi ve port
- `fromaddr` (str): Gönderen email adresi
- `toaddrs` (List[str]): Alıcı email adresleri
- `subject` (str): Email konusu
- `credentials` (Optional[Tuple[str, str]]): (username, password) tuple
- `rate_limit_seconds` (int): Email gönderme rate limit (default: 300)
- `level` (int): Minimum log seviyesi (default: NOTSET)

**Örnek:**
```python
handler = AsyncSMTPHandler(
    mailhost=("smtp.example.com", 587),
    fromaddr="alerts@example.com",
    toaddrs=["admin@example.com"],
    subject="Uygulama Hatası",
    credentials=("user", "password"),
    rate_limit_seconds=300
)
handler.start()
logger.addHandler(handler.get_queue_handler())
```

---

## Formatters

### BaseFormatter

Formatter base class.

```python
class BaseFormatter(logging.Formatter):
    def __init__(
        self,
        service_name: Optional[str] = None,
        datefmt: Optional[str] = None
    )
    def format_time(record: logging.LogRecord) -> str
```

---

### JSONFormatter

JSON formatında log formatter.

```python
class JSONFormatter(BaseFormatter):
    def __init__(
        self,
        service_name: Optional[str] = None,
        include_extra: bool = True,
        use_unix_timestamp: bool = False,
        datefmt: Optional[str] = None
    )
```

**Parametreler:**
- `service_name` (Optional[str]): Servis adı
- `include_extra` (bool): Extra field'ları dahil et (default: True)
- `use_unix_timestamp` (bool): Unix timestamp kullan (default: False)
- `datefmt` (Optional[str]): Tarih formatı

**Örnek:**
```python
formatter = JSONFormatter(
    service_name="myapp",
    include_extra=True,
    use_unix_timestamp=True
)
```

---

### PrettyFormatter

Okunabilir formatında log formatter.

```python
class PrettyFormatter(BaseFormatter):
    def __init__(
        self,
        service_name: Optional[str] = None,
        datefmt: Optional[str] = None
    )
```

**Parametreler:**
- `service_name` (Optional[str]): Servis adı
- `datefmt` (Optional[str]): Tarih formatı

**Örnek:**
```python
formatter = PrettyFormatter(service_name="myapp")
```

---

### CompactFormatter

Minimal formatında log formatter.

```python
class CompactFormatter(BaseFormatter):
    def __init__(self, datefmt: Optional[str] = None)
```

**Parametreler:**
- `datefmt` (Optional[str]): Tarih formatı

**Örnek:**
```python
formatter = CompactFormatter()
```

---

## Decorators

### log_function

Fonksiyon çağrılarını otomatik loglar.

```python
def log_function(
    level: int = logging.INFO,
    log_args: bool = True,
    log_result: bool = True
) -> Callable
```

**Parametreler:**
- `level` (int): Log seviyesi (default: INFO)
- `log_args` (bool): Parametreleri logla (default: True)
- `log_result` (bool): Return value'yu logla (default: True)

**Örnek:**
```python
@log_function(level=logging.INFO)
def calculate_total(items):
    return sum(item.price for item in items)
```

---

### log_exception

Exception'ları otomatik loglar.

```python
def log_exception(
    level: int = logging.ERROR,
    reraise: bool = True
) -> Callable
```

**Parametreler:**
- `level` (int): Log seviyesi (default: ERROR)
- `reraise` (bool): Exception'ı tekrar fırlat (default: True)

**Örnek:**
```python
@log_exception(level=logging.ERROR)
def risky_operation():
    if random.random() < 0.5:
        raise ValueError("Hata")
    return "Başarılı"
```

---

### log_performance

Fonksiyon performansını loglar.

```python
def log_performance(
    level: int = logging.INFO,
    threshold_seconds: float = 0.0
) -> Callable
```

**Parametreler:**
- `level` (int): Log seviyesi (default: INFO)
- `threshold_seconds` (float): Minimum süre (default: 0.0)

**Örnek:**
```python
@log_performance(level=logging.INFO, threshold_seconds=1.0)
def slow_operation():
    time.sleep(2)
    return "Tamamlandı"
```

---

### log_context

Context manager ile kod bloğunu loglar.

```python
def log_context(
    message: str,
    level: int = logging.INFO
) -> ContextManager
```

**Parametreler:**
- `message` (str): Context mesajı
- `level` (int): Log seviyesi (default: INFO)

**Örnek:**
```python
with log_context("Veritabanı işlemi"):
    logger.info("Bağlantı açıldı")
    # ... işlemler ...
```

---

## Utility Functions

### TraceContextFilter

Log kayıtlarına trace context bilgilerini ekler.

```python
class TraceContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool
```

**Kullanım:**
```python
filter = TraceContextFilter()
logger.addFilter(filter)
```

---

## Sonraki Adımlar

- **[Çalışma Mantığı](CALISMA_MANTIGI.md)** - İç mimari ve nasıl çalışıyor
- **[Davranış Şekli](DAVRANIS_SEKLI.md)** - Davranışlar ve best practices

