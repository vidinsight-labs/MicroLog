"""
Örnek: Order Service

Order servisi.
Header'lardan trace alma ve payment servisine istek gönderme.

Kullanım:
    python examples/microservices/order_service.py

Bu örnek Order Service'in nasıl trace context aldığını
ve Payment Service'e nasıl gönderdiğini gösterir.
"""

from microlog import setup_logger, trace, get_current_context


def simulate_http_request(url: str, headers: dict, method: str = "GET", data: dict = None):
    """HTTP isteği simülasyonu"""
    return {
        "status": 200,
        "headers": headers,
        "data": data or {}
    }


def main():
    """Order Service simülasyonu"""
    logger, handlers = setup_logger("order-service", service_name="order-service", return_handlers=True)
    
    print("Order Service Örneği")
    print("=" * 60)
    print()
    
    # API Gateway'den gelen header'lar (simüle edilmiş)
    incoming_headers = {
        "X-Trace-Id": "trace-123",
        "X-Span-Id": "span-456",
        "X-Correlation-Id": "order-789",
        "X-Session-Id": "session-abc"
    }
    
    print("1. API Gateway'den gelen header'lar:")
    print(f"   {incoming_headers}")
    print()
    
    # Header'lardan trace context oluştur
    print("2. Header'lardan trace context oluşturuluyor:")
    with trace(headers=incoming_headers) as ctx:
        logger.info(
            "Order Service: Request alındı",
            extra={
                "method": "POST",
                "path": "/api/orders",
                "trace_id": ctx.trace_id,
                "span_id": ctx.span_id,
                "parent_span_id": ctx.parent_span_id,
                "correlation_id": ctx.correlation_id
            }
        )
        
        print(f"   Trace ID: {ctx.trace_id} (aynı)")
        print(f"   Span ID: {ctx.span_id} (yeni)")
        print(f"   Parent Span ID: {ctx.parent_span_id}")
        print()
        
        # Sipariş işleme
        logger.info("Order Service: Sipariş işleniyor", extra={"order_id": "ORD-123"})
        import time
        time.sleep(0.05)
        
        # Payment Service'e istek gönder
        print("3. Payment Service'e istek gönderiliyor:")
        trace_headers = ctx.to_headers()
        payment_response = simulate_http_request(
            url="http://payment-service/api/payments",
            headers=trace_headers,
            method="POST",
            data={"order_id": "ORD-123", "amount": 99.99}
        )
        
        logger.info(
            "Order Service: Payment Service'den yanıt alındı",
            extra={
                "status": payment_response["status"],
                "trace_id": ctx.trace_id
            }
        )
        print(f"   Payment Service yanıtı: {payment_response['status']}")
        print()
        
        # Sipariş tamamlandı
        logger.info("Order Service: Sipariş tamamlandı", extra={"order_id": "ORD-123"})
        
        # Response header'larına trace ekle
        response_headers = ctx.to_headers()
        logger.info(
            "Order Service: Response hazırlandı",
            extra={
                "trace_id": ctx.trace_id,
                "response_headers": response_headers
            }
        )
        print(f"   Response Headers: {response_headers}")
        print()
    
    # Graceful shutdown: Handler'ları kapat (queue'daki loglar flush edilir)
    for handler in handlers:
        handler.stop()
    
    print("=" * 60)
    print("Örnek tamamlandı!")


if __name__ == "__main__":
    main()

