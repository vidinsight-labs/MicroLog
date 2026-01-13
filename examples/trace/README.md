# Trace Context Örnekleri

Bu klasör, MicroLog'un distributed tracing özelliklerini gösteren örnekleri içerir.

## Örnekler

### 1. basic_trace.py
Basit trace context kullanımı. with trace() context manager ve trace ID'lerin otomatik eklenmesi.

### 2. nested_trace.py
Parent-child span ilişkisi. Nested context örneği ve child span oluşturma.

### 3. trace_with_decorator.py
@with_trace decorator kullanımı. Sync ve async fonksiyonlarda otomatik trace.

### 4. http_headers_trace.py
HTTP header'lardan trace oluşturma. from_headers() ve to_headers() kullanımı.

## Kullanım

Her örneği çalıştırmak için:

```bash
python examples/trace/basic_trace.py
python examples/trace/nested_trace.py
python examples/trace/trace_with_decorator.py
python examples/trace/http_headers_trace.py
```

## Sonraki Adımlar

Trace context'i öğrendikten sonra:
- Web Framework: `examples/web/`
- Mikroservis: `examples/microservices/`

