"""
Örnek: HTTP Headers ile Trace Context

HTTP header'lardan trace context oluşturma.
from_headers() ve to_headers() kullanımı.

Kullanım:
    python examples/trace/http_headers_trace.py

Çıktı:
    HTTP header'lardan trace context oluşturulur ve header'lara dönüştürülür.
"""

from microlog import setup_logger, trace, get_current_context
from microlog.context import TraceContext


def simulate_http_request(headers: dict):
    """HTTP request simülasyonu"""
    logger = setup_logger("myapp", service_name="api-service")
    
    # Header'lardan trace context oluştur
    with trace(headers=headers) as ctx:
        logger.info(
            "HTTP isteği alındı",
            extra={
                "trace_id": ctx.trace_id,
                "span_id": ctx.span_id,
                "parent_span_id": ctx.parent_span_id,
                "correlation_id": ctx.correlation_id
            }
        )
        
        # İşlem yap
        logger.info("İstek işleniyor")
        
        # Response header'larına trace bilgisi ekle
        response_headers = ctx.to_headers()
        logger.info(
            "Yanıt hazırlandı",
            extra={"response_headers": response_headers}
        )
        
        return response_headers


def simulate_downstream_service(headers: dict):
    """Downstream servis simülasyonu"""
    logger = setup_logger("myapp", service_name="downstream-service")
    
    # Gelen header'lardan trace context oluştur
    with trace(headers=headers) as ctx:
        logger.info(
            "Downstream servis çağrıldı",
            extra={
                "trace_id": ctx.trace_id,
                "span_id": ctx.span_id,
                "parent_span_id": ctx.parent_span_id
            }
        )
        
        # Aynı trace_id, yeni span_id
        logger.info("Downstream işlem tamamlandı")
        
        # Response header'ları
        return ctx.to_headers()


def main():
    logger, handlers = setup_logger("myapp", service_name="main-service", return_handlers=True)
    
    print("HTTP Headers ile Trace Context Örneği")
    print("=" * 60)
    print()
    
    # 1. İlk request - yeni trace başlat
    print("1. İlk HTTP Request (yeni trace):")
    initial_headers = {
        "X-Correlation-Id": "req-123",
        "X-Session-Id": "session-456"
    }
    
    response_headers = simulate_http_request(initial_headers)
    print(f"   Response Headers: {response_headers}")
    print()
    
    # 2. Downstream servis - parent trace'i devam ettir
    print("2. Downstream Servis (parent trace devam ediyor):")
    downstream_headers = simulate_downstream_service(response_headers)
    print(f"   Downstream Response Headers: {downstream_headers}")
    print()
    
    # 3. Manuel TraceContext oluşturma
    print("3. Manuel TraceContext oluşturma:")
    ctx = TraceContext(
        trace_id="custom-trace-123",
        correlation_id="custom-req-456",
        session_id="custom-session-789"
    )
    
    headers = ctx.to_headers()
    print(f"   Headers: {headers}")
    print()
    
    # 4. Header'lardan TraceContext oluşturma
    print("4. Header'lardan TraceContext oluşturma:")
    new_ctx = TraceContext.from_headers(headers)
    print(f"   Trace ID: {new_ctx.trace_id}")
    print(f"   Span ID: {new_ctx.span_id}")
    print(f"   Parent Span ID: {new_ctx.parent_span_id}")
    print(f"   Correlation ID: {new_ctx.correlation_id}")
    print()
    
    # 5. Case-insensitive header desteği
    print("5. Case-insensitive header desteği:")
    mixed_case_headers = {
        "x-trace-id": "trace-123",
        "X-SPAN-ID": "span-456",
        "X-Correlation-Id": "corr-789"
    }
    
    ctx_from_mixed = TraceContext.from_headers(mixed_case_headers)
    print(f"   Trace ID: {ctx_from_mixed.trace_id}")
    print(f"   Parent Span ID: {ctx_from_mixed.parent_span_id}")
    print(f"   Correlation ID: {ctx_from_mixed.correlation_id}")
    
    # Graceful shutdown: Handler'ları kapat (queue'daki loglar flush edilir)
    for handler in handlers:
        handler.stop()


if __name__ == "__main__":
    main()

