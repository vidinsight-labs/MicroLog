# Web Framework Entegrasyonları

Bu klasör, MicroLog'un popüler web framework'leri ile entegrasyon örneklerini içerir.

## Örnekler

### 1. flask_integration.py
Flask uygulaması ile MicroLog entegrasyonu. Middleware ile trace context ve request-response logging.

### 2. fastapi_integration.py
FastAPI uygulaması ile MicroLog entegrasyonu. Async middleware ve dependency injection ile logger.

### 3. django_integration.py
Django uygulaması ile MicroLog entegrasyonu. Middleware ve settings yapılandırması.

## Kullanım

Her örneği çalıştırmak için:

```bash
# Flask
python examples/web/flask_integration.py

# FastAPI (uvicorn gerekli)
uvicorn examples.web.fastapi_integration:app --reload

# Django (django gerekli)
python examples/web/django_integration.py
```

## Notlar

- Bu örnekler framework'lerin kurulu olmasını gerektirir
- Production kullanımı için ek yapılandırmalar gerekebilir
- Trace context otomatik olarak HTTP header'lardan oluşturulur

## Sonraki Adımlar

Web framework entegrasyonunu öğrendikten sonra:
- Async: `examples/async/`
- Mikroservis: `examples/microservices/`

