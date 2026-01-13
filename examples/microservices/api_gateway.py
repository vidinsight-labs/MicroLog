"""
Örnek: API Gateway

API Gateway örneği.
Trace context oluşturma ve downstream servislere header gönderme.

Kullanım:
    python examples/microservices/api_gateway.py

Bu örnek API Gateway'in nasıl trace context oluşturduğunu
ve downstream servislere nasıl gönderdiğini gösterir.
"""

from microlog import setup_logger, trace, get_current_context


def simulate_http_request(url: str, headers: dict, method: str = "GET", data: dict = None):
    """HTTP isteği simülasyonu"""
    # Gerçek kullanımda: requests.post(url, headers=headers, json=data)
    # Burada sadece simüle ediyoruz
    return {
        "status": 200,
        "headers": headers,
        "data": data or {}
    }


def main():
    """API Gateway simülasyonu"""
    logger, handlers = setup_logger("api-gateway", service_name="api-gateway", return_handlers=True)
    
    print("API Gateway Örneği")
    print("=" * 60)
    print()
    
    # 1. Yeni request - trace context oluştur
    print("1. Yeni request - trace context oluşturuluyor:")
    with trace(correlation_id="order-123", user_id="usr-456") as ctx:
        logger.info(
            "API Gateway: Request alındı",
            extra={
                "method": "POST",
                "path": "/api/orders",
                "trace_id": ctx.trace_id,
                "span_id": ctx.span_id,
                "correlation_id": ctx.correlation_id
            }
        )
        
        # Trace header'larını hazırla
        trace_headers = ctx.to_headers()
        print(f"   Trace ID: {ctx.trace_id}")
        print(f"   Span ID: {ctx.span_id}")
        print(f"   Headers: {trace_headers}")
        print()
        
        # 2. Order Service'e istek gönder
        print("2. Order Service'e istek gönderiliyor:")
        order_response = simulate_http_request(
            url="http://order-service/api/orders",
            headers=trace_headers,
            method="POST",
            data={"order_id": "ORD-123", "amount": 99.99}
        )
        
        logger.info(
            "API Gateway: Order Service'den yanıt alındı",
            extra={
                "status": order_response["status"],
                "trace_id": ctx.trace_id
            }
        )
        print(f"   Order Service yanıtı: {order_response['status']}")
        print()
        
        # 3. Response header'larına trace ekle
        print("3. Response header'larına trace bilgisi ekleniyor:")
        response_headers = ctx.to_headers()
        logger.info(
            "API Gateway: Response hazırlandı",
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

