# Async Örnekleri

Bu klasör, MicroLog'un asenkron (async) kullanım örneklerini içerir.

## Örnekler

### 1. async_basic.py
Async fonksiyonlarda logging. async with trace() kullanımı ve async handler'lar.

### 2. async_tasks.py
Asyncio task'ları. Concurrent logging ve async decorator kullanımı.

### 3. async_web.py
Async web server örneği. Aiohttp ile entegrasyon ve async request handling.

## Kullanım

Her örneği çalıştırmak için:

```bash
python examples/async/async_basic.py
python examples/async/async_tasks.py
python examples/async/async_web.py
```

## Notlar

- Async handler'lar otomatik olarak queue kullanır
- Trace context async context manager ile çalışır
- Async fonksiyonlarda @with_trace decorator kullanılabilir

## Sonraki Adımlar

Async kullanımı öğrendikten sonra:
- Mikroservis: `examples/microservices/`
- Production: `examples/production/`

