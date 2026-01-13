"""
Örnek: Tam Mikroservis Akışı

Tam mikroservis akışı.
3 servis arası iletişim ve trace görselleştirme.

Kullanım:
    python examples/microservices/full_microservice_flow.py

Bu örnek API Gateway -> Order Service -> Payment Service
akışını simüle eder ve distributed tracing'i gösterir.
"""

from microlog import setup_logger, trace, get_current_context


def simulate_service_call(service_name: str, url: str, headers: dict, data: dict = None):
    """Servis çağrısı simülasyonu"""
    logger = setup_logger(service_name, service_name=service_name)
    
    # Header'lardan trace context oluştur
    with trace(headers=headers) as ctx:
        logger.info(
            f"{service_name}: Request alındı",
            extra={
                "url": url,
                "trace_id": ctx.trace_id,
                "span_id": ctx.span_id,
                "parent_span_id": ctx.parent_span_id
            }
        )
        
        # Simüle edilmiş işlem (gerçek uygulamada HTTP çağrısı olurdu)
        import time
        time.sleep(0.05)
        
        logger.info(f"{service_name}: İşlem tamamlandı")
        
        # Response header'ları
        return ctx.to_headers()


def main():
    """Tam mikroservis akışı simülasyonu"""
    logger, handlers = setup_logger("api-gateway", service_name="api-gateway", return_handlers=True)
    
    print("Tam Mikroservis Akışı Örneği")
    print("=" * 60)
    print()
    
    # 1. API Gateway - Yeni trace başlat
    print("1. API Gateway - Yeni trace başlatılıyor:")
    with trace(correlation_id="order-123", user_id="usr-456") as gateway_ctx:
        logger.info(
            "API Gateway: Request alındı",
            extra={
                "method": "POST",
                "path": "/api/orders",
                "trace_id": gateway_ctx.trace_id,
                "span_id": gateway_ctx.span_id
            }
        )
        
        print(f"   Trace ID: {gateway_ctx.trace_id}")
        print(f"   Gateway Span ID: {gateway_ctx.span_id}")
        print()
        
        # 2. Order Service'e istek gönder
        print("2. Order Service çağrılıyor:")
        gateway_headers = gateway_ctx.to_headers()
        order_headers = simulate_service_call(
            service_name="order-service",
            url="http://order-service/api/orders",
            headers=gateway_headers,
            data={"order_id": "ORD-123", "amount": 99.99}
        )
        
        print(f"   Order Service Span ID: {order_headers.get('X-Span-Id')}")
        print(f"   Parent Span ID: {order_headers.get('X-Parent-Span-Id')}")
        print()
        
        # 3. Payment Service'e istek gönder (Order Service'den)
        print("3. Payment Service çağrılıyor:")
        payment_headers = simulate_service_call(
            service_name="payment-service",
            url="http://payment-service/api/payments",
            headers=order_headers,
            data={"order_id": "ORD-123", "amount": 99.99}
        )
        
        print(f"   Payment Service Span ID: {payment_headers.get('X-Span-Id')}")
        print(f"   Parent Span ID: {payment_headers.get('X-Parent-Span-Id')}")
        print()
        
        # 4. Trace görselleştirme
        print("4. Trace Görselleştirme:")
        print(f"   Trace ID: {gateway_ctx.trace_id}")
        print(f"   Trace Tree:")
        print(f"   ├── {gateway_ctx.span_id} (API Gateway)")
        print(f"   │   └── {order_headers.get('X-Span-Id')} (Order Service)")
        print(f"   │       └── {payment_headers.get('X-Span-Id')} (Payment Service)")
        print()
        
        logger.info(
            "API Gateway: Tüm işlemler tamamlandı",
            extra={
                "trace_id": gateway_ctx.trace_id,
                "order_span_id": order_headers.get('X-Span-Id'),
                "payment_span_id": payment_headers.get('X-Span-Id')
            }
        )
    
    # Graceful shutdown: Handler'ları kapat (queue'daki loglar flush edilir)
    # Not: simulate_service_call içindeki logger'lar atexit ile otomatik kapanacak
    for handler in handlers:
        handler.stop()
    
    print("=" * 60)
    print("Örnek tamamlandı!")
    print()
    print("Distributed Tracing Özeti:")
    print("- Tüm servisler aynı trace_id'yi kullanır")
    print("- Her servis kendi span_id'sini oluşturur")
    print("- Parent-child ilişkisi parent_span_id ile kurulur")
    print("- Trace görselleştirme için log aggregation sistemleri kullanılabilir")


if __name__ == "__main__":
    main()

