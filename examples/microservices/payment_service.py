"""
Örnek: Payment Service

Payment servisi.
Trace context propagation ve distributed tracing örneği.

Kullanım:
    python examples/microservices/payment_service.py

Bu örnek Payment Service'in nasıl trace context aldığını
ve işlediğini gösterir.
"""

from microlog import setup_logger, trace, get_current_context


def main():
    """Payment Service simülasyonu"""
    logger, handlers = setup_logger("payment-service", service_name="payment-service", return_handlers=True)
    
    print("Payment Service Örneği")
    print("=" * 60)
    print()
    
    # Order Service'den gelen header'lar (simüle edilmiş)
    incoming_headers = {
        "X-Trace-Id": "trace-123",
        "X-Span-Id": "span-789",
        "X-Parent-Span-Id": "span-456",
        "X-Correlation-Id": "order-789"
    }
    
    print("1. Order Service'den gelen header'lar:")
    print(f"   {incoming_headers}")
    print()
    
    # Header'lardan trace context oluştur
    print("2. Header'lardan trace context oluşturuluyor:")
    with trace(headers=incoming_headers) as ctx:
        logger.info(
            "Payment Service: Request alındı",
            extra={
                "method": "POST",
                "path": "/api/payments",
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
        
        # Ödeme işleme
        logger.info("Payment Service: Ödeme işleniyor", extra={"order_id": "ORD-123"})
        import time
        time.sleep(0.05)
        
        # Ödeme tamamlandı
        logger.info("Payment Service: Ödeme tamamlandı", extra={"order_id": "ORD-123"})
        
        # Response header'larına trace ekle
        response_headers = ctx.to_headers()
        logger.info(
            "Payment Service: Response hazırlandı",
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

