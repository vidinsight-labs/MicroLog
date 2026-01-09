# Mikroservis Örnekleri

Bu klasör, MicroLog'un mikroservis mimarisinde distributed tracing kullanımını gösteren örnekleri içerir.

## Örnekler

### 1. api_gateway.py
API Gateway örneği. Trace context oluşturma ve downstream servislere header gönderme.

### 2. order_service.py
Order servisi. Header'lardan trace alma ve payment servisine istek gönderme.

### 3. payment_service.py
Payment servisi. Trace context propagation ve distributed tracing örneği.

### 4. full_microservice_flow.py
Tam mikroservis akışı. 3 servis arası iletişim ve trace görselleştirme.

## Kullanım

Her örneği çalıştırmak için:

```bash
python examples/microservices/api_gateway.py
python examples/microservices/order_service.py
python examples/microservices/payment_service.py
python examples/microservices/full_microservice_flow.py
```

## Notlar

- Bu örnekler simüle edilmiş HTTP istekleri kullanır
- Gerçek kullanımda HTTP client (requests, httpx) kullanılır
- Trace context HTTP header'ları ile yayılır
- Her servis aynı trace_id'yi kullanır, farklı span_id'ler oluşturur

## Sonraki Adımlar

Mikroservis kullanımını öğrendikten sonra:
- Production: `examples/production/`
- Advanced: `examples/advanced/`

