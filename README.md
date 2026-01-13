# MicroLog

MicroLog, Python için yüksek performanslı asenkron logging kütüphanesidir. Distributed tracing desteği, esnek formatter'lar ve thread-safe yapısı ile mikroservis mimarileri ve production ortamları için tasarlanmıştır.

---

# MicroLog

MicroLog is a high-performance asynchronous logging library for Python. Designed for microservice architectures and production environments with distributed tracing support, flexible formatters, and thread-safe structure.

---

## Özellikler / Features

### Asenkron Logging / Asynchronous Logging
- Non-blocking log yazma işlemleri
- Queue tabanlı arka plan işleme
- Ana thread'i bloklamaz
- Yüksek performans

### Formatter'lar / Formatters
- **JSONFormatter**: Yapılandırılmış JSON formatı (ELK, Datadog, Splunk için)
- **PrettyFormatter**: Renkli terminal çıktısı (geliştirme ortamı için)
- **CompactFormatter**: Minimal tek satır format (log dosyaları için)

### Distributed Tracing / Distributed Tracing
- Trace context yönetimi
- Parent-child span ilişkileri
- HTTP header entegrasyonu
- Correlation ID desteği
- Otomatik trace ID propagasyonu

### Dosya Yönetimi / File Management
- Otomatik dosya rotation
- Gzip sıkıştırma desteği
- Yedek dosya yönetimi
- Yapılandırılabilir dosya boyutu limitleri

### Thread Safety / Thread Safety
- Thread-safe log yazma
- ContextVar ve thread-local storage desteği
- Async/await uyumluluğu

### Web Framework Entegrasyonları / Web Framework Integrations
- Flask middleware desteği
- FastAPI middleware desteği
- Django middleware yapısı
- Async web framework desteği

---

## Kurulum / Installation

### Pip ile / With Pip

```bash
pip install microlog
```

### Kaynak Koddan / From Source

```bash
git clone https://github.com/yourusername/MicroLog.git
cd MicroLog
pip install -e .
```

---

## Hızlı Başlangıç / Quick Start

### Basit Kullanım / Simple Usage

```python
from microlog import setup_logger

# Logger oluştur / Create logger
logger = setup_logger("myapp")

# Log yaz / Write log
logger.info("Uygulama başlatıldı")
logger.warning("Dikkat: Yüksek bellek kullanımı")
logger.error("Bir hata oluştu")
```

### Console Logger (Renkli Çıktı) / Console Logger (Colored Output)

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

### File Logger (JSON Format) / File Logger (JSON Format)

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

### Trace Context ile Loglama / Logging with Trace Context

```python
from microlog import setup_logger, trace

logger = setup_logger("myapp", service_name="api-service")

# Trace context ile / With trace context
with trace(correlation_id="req-123") as ctx:
    logger.info("İstek alındı")
    logger.info("İşlem başlatıldı", extra={"trace_id": ctx.trace_id})
```

### Decorator ile Trace / Trace with Decorator

```python
from microlog import setup_logger, with_trace

logger = setup_logger("myapp")

@with_trace(correlation_id="order-456")
def process_order(order_id: str):
    logger.info("Sipariş işleniyor", extra={"order_id": order_id})
    # İşlem devam eder / Process continues
```

---

## Temel Kavramlar / Core Concepts

### Logger Kurulumu / Logger Setup

MicroLog üç ana fonksiyon sağlar:

1. **setup_logger()**: Esnek logger kurulumu
2. **setup_console_logger()**: Sadece console handler
3. **setup_file_logger()**: Sadece file handler

### Handler'lar / Handlers

- **AsyncConsoleHandler**: Asenkron konsol çıktısı
- **AsyncRotatingFileHandler**: Asenkron dosya yazma + rotation

### Formatter'lar / Formatters

- **JSONFormatter**: Production ortamları için yapılandırılmış JSON
- **PrettyFormatter**: Geliştirme ortamları için renkli çıktı
- **CompactFormatter**: Minimal format, düşük dosya boyutu

### Trace Context / Trace Context

Trace context, distributed tracing için kullanılır:

- **trace_id**: Tek bir request'in tüm servislerdeki akışını takip eder
- **span_id**: Her operation için benzersiz span ID
- **parent_span_id**: Parent-child ilişkisi
- **correlation_id**: Business correlation (order_id, payment_id, etc.)

---

## Örnekler / Examples

Proje, 35+ örnek içerir ve 8 kategori altında organize edilmiştir:

### Quickstart (2 örnek)
- `minimal_example.py`: En minimal kullanım
- `hello_world.py`: Kapsamlı başlangıç örneği

### Basic (5 örnek)
- Basit logging kullanımı
- Console ve file logging
- Multiple handler'lar
- Format örnekleri

### Trace (6 örnek)
- Basit trace context
- Nested trace (parent-child)
- HTTP header entegrasyonu
- Decorator kullanımı
- Manuel context yönetimi

### Advanced (8 örnek)
- Multiple logger yönetimi
- Custom formatter ve handler
- Thread safety
- Signal handling
- Context manager pattern

### Web (3 örnek)
- Flask entegrasyonu
- FastAPI entegrasyonu
- Django entegrasyonu

### Async (3 örnek)
- Async/await kullanımı
- Async task'lar
- Async web framework

### Microservices (4 örnek)
- API Gateway pattern
- Service-to-service tracing
- Full microservice flow

### Production (4 örnek)
- Production yapılandırması
- Structured logging
- Error tracking
- Performance logging

Tüm örnekler için: [examples/README.md](examples/README.md)

---

## Dokümantasyon / Documentation

Detaylı dokümantasyon `docs/` klasöründe bulunmaktadır:

- [Quickstart Guide](docs/quickstart.md)
- [Trace Context Guide](docs/trace-context.md)
- [Formatters Guide](docs/formatters.md)
- [Handlers Guide](docs/handlers.md)
- [File Management](docs/file-management.md)

---

## Proje Yapısı / Project Structure

```
MicroLog/
├── src/
│   └── microlog/
│       ├── __init__.py          # Ana export'lar
│       ├── core.py              # Logger kurulum fonksiyonları
│       ├── handlers.py          # Async handler'lar
│       ├── formatters.py         # Formatter'lar
│       ├── context.py            # Trace context yönetimi
│       └── decorators.py         # Decorator'lar
├── examples/                     # 35+ örnek
│   ├── quickstart/              # Hızlı başlangıç
│   ├── basic/                   # Temel kullanım
│   ├── trace/                   # Distributed tracing
│   ├── advanced/                # Gelişmiş özellikler
│   ├── web/                     # Web framework entegrasyonları
│   ├── async/                   # Async kullanım
│   ├── microservices/           # Mikroservis örnekleri
│   └── production/              # Production yapılandırmaları
├── docs/                        # Dokümantasyon
│   ├── quickstart.md
│   ├── trace-context.md
│   ├── formatters.md
│   ├── handlers.md
│   └── file-management.md
└── tests/                       # Test dosyaları
```

---

## Kullanım Senaryoları / Use Cases

### Mikroservis Mimarisi / Microservice Architecture

```python
# API Gateway
from microlog import setup_logger, trace

logger = setup_logger("api-gateway", service_name="gateway")

def handle_request(request):
    with trace(correlation_id=request.headers.get("X-Request-ID")):
        logger.info("Request received", extra={"path": request.path})
        # Diğer servislere istek gönder / Send request to other services
```

### Production Logging / Production Logging

```python
from microlog import setup_file_logger

logger = setup_file_logger(
    name="production-app",
    filename="/var/log/app.log",
    format_type="json",
    max_bytes=50 * 1024 * 1024,  # 50MB
    backup_count=10,
    compress=True
)

logger.info("Application started", extra={
    "version": "1.0.0",
    "environment": "production"
})
```

### Geliştirme Ortamı / Development Environment

```python
from microlog import setup_console_logger

logger = setup_console_logger(
    name="dev-app",
    use_colors=True,
    service_name="dev-service"
)

logger.debug("Debug bilgisi")
logger.info("Bilgi mesajı")
logger.warning("Uyarı mesajı")
logger.error("Hata mesajı")
```

---

## Graceful Shutdown / Graceful Shutdown

Handler'ları düzgün şekilde kapatmak için:

```python
from microlog import setup_logger

logger, handlers = setup_logger("myapp", return_handlers=True)

# Logging işlemleri / Logging operations
logger.info("Application running")

# Graceful shutdown
for handler in handlers:
    handler.stop()
```

Bu sayede queue'daki tüm loglar flush edilir ve kaynaklar temizlenir.

---

## Thread Safety / Thread Safety

MicroLog thread-safe'dir ve aynı anda birden fazla thread'den güvenli şekilde kullanılabilir:

```python
import threading
from microlog import setup_logger, trace

logger = setup_logger("threaded-app")

def worker(worker_id: int):
    with trace(correlation_id=f"worker-{worker_id}"):
        logger.info(f"Worker {worker_id} started")
        # İşlem devam eder / Process continues

# Birden fazla thread / Multiple threads
threads = []
for i in range(5):
    t = threading.Thread(target=worker, args=(i,))
    threads.append(t)
    t.start()

for t in threads:
    t.join()
```

---

## Async/Await Desteği / Async/Await Support

MicroLog async/await ile uyumludur:

```python
import asyncio
from microlog import setup_logger, trace

logger = setup_logger("async-app")

async def async_task():
    async with trace(correlation_id="async-task"):
        logger.info("Async task started")
        await asyncio.sleep(1)
        logger.info("Async task completed")

asyncio.run(async_task())
```

---

## Özelleştirme / Customization

### Custom Formatter / Custom Formatter

```python
from microlog import setup_logger, HandlerConfig
from microlog.handlers import AsyncConsoleHandler
import logging

class CustomFormatter(logging.Formatter):
    def format(self, record):
        return f"[{record.levelname}] {record.getMessage()}"

logger = setup_logger(
    "myapp",
    handlers=[
        HandlerConfig(
            handler=AsyncConsoleHandler(),
            formatter=CustomFormatter()
        )
    ]
)
```

### Custom Handler / Custom Handler

```python
from microlog.handlers import AsyncHandler
import logging

class CustomHandler(AsyncHandler):
    def __init__(self):
        # Gerçek handler'ı oluştur / Create real handler
        real_handler = logging.StreamHandler()
        super().__init__(real_handler)
```

---

## Test / Testing

Test dosyaları `tests/` klasöründe bulunmaktadır:

```bash
# Testleri çalıştır / Run tests
pytest tests/
```

---

## Katkıda Bulunma / Contributing

Katkılarınızı bekliyoruz! Lütfen:

1. Fork yapın / Fork the repository
2. Feature branch oluşturun / Create a feature branch
3. Değişikliklerinizi commit edin / Commit your changes
4. Branch'inizi push edin / Push to the branch
5. Pull Request oluşturun / Create a Pull Request

---

## Lisans / License

Bu proje MIT lisansı altında lisanslanmıştır.

This project is licensed under the MIT License.

---

## Destek / Support

Sorularınız ve önerileriniz için:

- GitHub Issues: [Issues](https://github.com/yourusername/MicroLog/issues)
- Dokümantasyon: [docs/](docs/)

---

## Sürüm Geçmişi / Version History

- **v1.0.0**: İlk stabil sürüm
  - Asenkron logging desteği
  - Distributed tracing
  - Üç formatter (JSON, Pretty, Compact)
  - Web framework entegrasyonları
  - 35+ örnek

---

## Özellikler ve İyileştirmeler / Features and Improvements

### Gelecek Özellikler / Future Features

- [ ] SMTP handler desteği
- [ ] Syslog handler desteği
- [ ] Metrics entegrasyonu
- [ ] Log sampling
- [ ] Context propagation için daha fazla protokol desteği

---

## Notlar / Notes

- Python 3.7+ gerektirir
- Tüm async handler'lar otomatik olarak atexit ile temizlenir
- Trace context, ContextVar kullanarak thread-safe çalışır
- File handler'lar otomatik olarak dizin oluşturur

---

## Referanslar / References

- [Python Logging Documentation](https://docs.python.org/3/library/logging.html)
- [OpenTelemetry](https://opentelemetry.io/)
- [Distributed Tracing Best Practices](https://opentelemetry.io/docs/concepts/signals/traces/)

---

**MicroLog** - Yüksek performanslı asenkron logging kütüphanesi

**MicroLog** - High-performance asynchronous logging library
