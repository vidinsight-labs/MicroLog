# MicroLog Örnekleri

Bu dizinde MicroLog kütüphanesinin farklı kullanım senaryolarını gösteren örnekler bulunmaktadır.

## Örnekler

### 1. basic_usage.py
Temel kullanım örnekleri:
- Logger oluşturma
- Trace context kullanımı
- Nested trace context
- Extra alanlar

**Çalıştırma:**
```bash
PYTHONPATH=src:$PYTHONPATH python examples/basic_usage.py
```

### 2. file_logging.py
Dosya logging örnekleri:
- JSON formatında logging
- Pretty formatında logging
- Dosya handler kullanımı

**Çalıştırma:**
```bash
PYTHONPATH=src:$PYTHONPATH python examples/file_logging.py
```

**Çıktı:** `logs/json_example.log` ve `logs/pretty_example.log`

### 3. decorators_example.py
Decorator örnekleri:
- `@log_function` - Fonksiyon çağrılarını logla
- `@log_exception` - Exception'ları yakala ve logla
- `@log_performance` - Performans ölçümü
- `log_context` - Context manager ile logging

**Çalıştırma:**
```bash
PYTHONPATH=src:$PYTHONPATH python examples/decorators_example.py
```

### 4. production_example.py
Production ortamı örneği:
- Gerçek dünya senaryosu (sipariş işleme)
- Console + File logging
- JSON format
- Error handling
- Trace context ile request tracking

**Çalıştırma:**
```bash
PYTHONPATH=src:$PYTHONPATH python examples/production_example.py
```

**Çıktı:** `logs/production.log`

### 5. async_context_example.py
Async context manager örneği:
- Async/await ile trace context kullanımı
- Paralel async işlemler
- Her async task için ayrı trace context

**Çalıştırma:**
```bash
PYTHONPATH=src:$PYTHONPATH python examples/async_context_example.py
```

## Tüm Örnekleri Çalıştırma

```bash
PYTHONPATH=src:$PYTHONPATH python examples/run_all_examples.py
```

## Özellikler

### ✅ Test Edilen Özellikler

1. **Temel Logging**
   - Debug, Info, Warning, Error seviyeleri
   - Extra alanlar
   - Service name

2. **Trace Context**
   - Trace ID ve Span ID yönetimi
   - Correlation ID
   - Nested contexts
   - Header generation

3. **Formatters**
   - JSON (machine-readable)
   - Pretty (human-readable, renkli)
   - Compact (minimal)

4. **Handlers**
   - Async Console Handler
   - Async Rotating File Handler
   - Async SMTP Handler (rate limiting)

5. **Decorators**
   - `@log_function` - Otomatik fonksiyon logging
   - `@log_exception` - Exception yakalama
   - `@log_performance` - Performans ölçümü
   - `log_context` - Context manager

6. **Async Support**
   - Async context manager (`async with trace()`)
   - Async/await uyumlu
   - Paralel işlemler

7. **Production Features**
   - File rotation
   - Gzip compression
   - Thread-safe operations
   - Rate limiting

## Log Dosyaları

Örnekler çalıştırıldığında `logs/` dizininde şu dosyalar oluşur:

- `json_example.log` - JSON formatında loglar
- `pretty_example.log` - Pretty formatında loglar
- `production.log` - Production örneği logları

## Notlar

- Tüm örnekler `PYTHONPATH=src:$PYTHONPATH` ile çalıştırılmalıdır
- Log dosyaları `logs/` dizininde oluşturulur
- Async örnekler Python 3.7+ gerektirir
- Production örneği gerçek bir mikroservis senaryosunu simüle eder

