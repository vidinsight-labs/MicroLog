# MicroLog Örnekleri

Bu klasör, MicroLog kütüphanesinin tüm özelliklerini gösteren kapsamlı örnekleri içerir.

## 📊 Genel Bakış

**Toplam: 35 örnek** - 8 kategori altında organize edilmiştir.

| Kategori | Örnek Sayısı | Açıklama |
|----------|--------------|----------|
| [Quickstart](#quickstart) | 2 | Hızlı başlangıç örnekleri |
| [Basic](#basic) | 5 | Temel kullanım örnekleri |
| [Trace](#trace) | 6 | Distributed tracing örnekleri |
| [Advanced](#advanced) | 8 | Gelişmiş özellikler |
| [Web](#web) | 3 | Web framework entegrasyonları |
| [Async](#async) | 3 | Asenkron kullanım örnekleri |
| [Microservices](#microservices) | 4 | Mikroservis mimarisi örnekleri |
| [Production](#production) | 4 | Production-ready yapılandırmalar |

---

## 🚀 Quickstart

**2 örnek** - Hızlı başlangıç için en basit örnekler

### Örnekler

1. **minimal_example.py** - En minimal kullanım (3 satır kod)
2. **hello_world.py** - Kapsamlı ilk adımlar örneği

**Kullanım:**
```bash
python examples/quickstart/minimal_example.py
python examples/quickstart/hello_world.py
```

**Daha fazla:** [quickstart/README.md](quickstart/README.md)

---

## 📝 Basic

**5 örnek** - Temel logging özellikleri

### Örnekler

1. **simple_logging.py** - Basit logging kullanımı ve log seviyeleri
2. **console_logging.py** - Renkli console çıktısı ve extra alanlar
3. **file_logging.py** - Dosyaya loglama, JSON format, rotation
4. **multiple_handlers.py** - Birden fazla handler (console + file)
5. **compact_format.py** - CompactFormatter kullanımı (minimal format)

**Kullanım:**
```bash
python examples/basic/simple_logging.py
python examples/basic/console_logging.py
python examples/basic/file_logging.py
python examples/basic/multiple_handlers.py
python examples/basic/compact_format.py
```

**Daha fazla:** [basic/README.md](basic/README.md)

---

## 🔍 Trace

**6 örnek** - Distributed tracing ve trace context yönetimi

### Örnekler

1. **basic_trace.py** - Basit trace context kullanımı
2. **nested_trace.py** - Parent-child span ilişkisi
3. **http_headers_trace.py** - HTTP header entegrasyonu
4. **trace_with_decorator.py** - `@with_trace` decorator kullanımı
5. **manual_context.py** - Manuel context yönetimi (set/clear/get)
6. **trace_vs_correlation.py** - trace_id vs correlation_id farkı ve kullanımı

**Kullanım:**
```bash
python examples/trace/basic_trace.py
python examples/trace/nested_trace.py
python examples/trace/http_headers_trace.py
python examples/trace/trace_with_decorator.py
python examples/trace/manual_context.py
python examples/trace/trace_vs_correlation.py
```

**Önemli Notlar:**
- **trace_id**: Tek bir HTTP request'in tüm servislerdeki akışını takip eder
- **correlation_id**: Business correlation için (order_id, payment_id, etc.)
- **span_id**: Her operation için benzersiz span ID
- **parent_span_id**: Parent-child ilişkisi için

**Daha fazla:** [trace/README.md](trace/README.md)

---

## 🔧 Advanced

**8 örnek** - Gelişmiş özellikler ve özelleştirme

### Örnekler

1. **multiple_loggers.py** - Birden fazla logger yönetimi
2. **custom_formatter.py** - Özel formatter oluşturma
3. **custom_handler.py** - AsyncHandler'dan türetme
4. **context_manager.py** - Context manager pattern
5. **thread_safety.py** - Thread-safe kullanım
6. **signal_handling.py** - Graceful shutdown (SIGTERM/SIGINT)
7. **configure_logger.py** - Mevcut logger'ı yapılandırma
8. **create_formatter.py** - Formatter factory fonksiyonu

**Kullanım:**
```bash
python examples/advanced/multiple_loggers.py
python examples/advanced/custom_formatter.py
python examples/advanced/custom_handler.py
python examples/advanced/context_manager.py
python examples/advanced/thread_safety.py
python examples/advanced/signal_handling.py
python examples/advanced/configure_logger.py
python examples/advanced/create_formatter.py
```

**Daha fazla:** [advanced/README.md](advanced/README.md)

---

## 🌐 Web

**3 örnek** - Web framework entegrasyonları

### Örnekler

1. **flask_integration.py** - Flask middleware ve trace context
2. **fastapi_integration.py** - FastAPI middleware ve async support
3. **django_integration.py** - Django middleware yapısı

**Not:** Bu örnekler framework bağımlılıkları gerektirir.

**Kurulum:**
```bash
# Flask için
pip install flask

# FastAPI için
pip install fastapi uvicorn

# Django için
pip install django
```

**Kullanım:**
```bash
python examples/web/flask_integration.py
python examples/web/fastapi_integration.py
# Django için: Django projesi içinde kullanılmalı
```

**Daha fazla:** [web/README.md](web/README.md)

---

## ⚡ Async

**3 örnek** - Asenkron kullanım örnekleri

### Örnekler

1. **async_basic.py** - Async/await ile temel kullanım
2. **async_tasks.py** - Async task'lar ve trace context
3. **async_web.py** - Async web framework (aiohttp) entegrasyonu

**Kullanım:**
```bash
python examples/async/async_basic.py
python examples/async/async_tasks.py
python examples/async/async_web.py  # aiohttp gerektirir
```

**Daha fazla:** [async/README.md](async/README.md)

---

## 🏗️ Microservices

**4 örnek** - Mikroservis mimarisi ve distributed tracing

### Örnekler

1. **api_gateway.py** - API Gateway pattern ve trace başlatma
2. **order_service.py** - Order service ve header'dan trace alma
3. **payment_service.py** - Payment service ve trace propagation
4. **full_microservice_flow.py** - Tam mikroservis akışı (3 servis)

**Kullanım:**
```bash
python examples/microservices/api_gateway.py
python examples/microservices/order_service.py
python examples/microservices/payment_service.py
python examples/microservices/full_microservice_flow.py
```

**Daha fazla:** [microservices/README.md](microservices/README.md)

---

## 🚀 Production

**4 örnek** - Production-ready yapılandırmalar

### Örnekler

1. **production_config.py** - Production yapılandırması (JSON format, rotation)
2. **structured_logging.py** - Structured logging ve extra alanlar
3. **error_tracking.py** - Error tracking ve exception handling
4. **performance_logging.py** - Performance logging ve timing

**Kullanım:**
```bash
python examples/production/production_config.py
python examples/production/structured_logging.py
python examples/production/error_tracking.py
python examples/production/performance_logging.py
```

**Daha fazla:** [production/README.md](production/README.md)

---

## 🎯 Öğrenme Yolu

### Yeni Başlayanlar İçin

1. **Quickstart** → `minimal_example.py` ile başlayın
2. **Basic** → Temel özellikleri öğrenin
3. **Trace** → Distributed tracing'i anlayın
4. **Web/Async** → Framework entegrasyonlarını inceleyin

### İleri Seviye

1. **Advanced** → Özelleştirme ve gelişmiş özellikler
2. **Microservices** → Distributed tracing pattern'leri
3. **Production** → Production-ready yapılandırmalar

---

## 🔑 Temel Kavramlar

### Trace ID vs Correlation ID

- **trace_id**: Tek bir HTTP request'in tüm servislerdeki akışını takip eder
  - Her yeni request için YENİ trace_id
  - Aynı request içinde tüm servislerde AYNI
  - Distributed tracing için kullanılır

- **correlation_id**: Business correlation için (order_id, payment_id, etc.)
  - Farklı request'lerde AYNI olabilir (aynı order için)
  - Business mantığına göre belirlenir
  - "Bu order için tüm işlemleri bul" sorguları için

**Detaylı örnek:** `examples/trace/trace_vs_correlation.py`

### Graceful Shutdown

Tüm örnekler `return_handlers=True` kullanarak graceful shutdown yapar:

```python
logger, handlers = setup_logger("myapp", return_handlers=True)

# ... logging işlemleri ...

# Graceful shutdown
for handler in handlers:
    handler.stop()
```

Bu sayede queue'daki tüm loglar flush edilir.

---

## 📚 Ek Kaynaklar

- [Ana Dokümantasyon](../../docs/)
- [Quickstart Guide](../../docs/quickstart.md)
- [Trace Context Guide](../../docs/trace-context.md)
- [Formatters Guide](../../docs/formatters.md)
- [Handlers Guide](../../docs/handlers.md)

---

## 🐛 Sorun Giderme

### Örnekler çalışmıyor

1. **PYTHONPATH ayarlayın:**
   ```bash
   export PYTHONPATH=$PYTHONPATH:/path/to/MicroLog/src
   ```

2. **Bağımlılıkları kontrol edin:**
   - Web framework örnekleri için framework kurulu olmalı
   - Async örnekleri için Python 3.7+ gerekir

3. **Log dosyaları:**
   - Bazı örnekler log dosyası oluşturur
   - Dosya izinlerini kontrol edin

### Loglar görünmüyor

- Async handler'lar queue kullanır
- `handler.stop()` çağrıldığından emin olun
- Veya `time.sleep(0.2)` ekleyin (eski yöntem)

---

## 📝 Katkıda Bulunma

Yeni örnek eklemek için:

1. Uygun kategori klasörüne ekleyin
2. `return_handlers=True` kullanın
3. Graceful shutdown yapın
4. Docstring ekleyin
5. README'yi güncelleyin

---

## 📄 Lisans

Bu örnekler MicroLog projesinin bir parçasıdır ve aynı lisans altında dağıtılmaktadır.

