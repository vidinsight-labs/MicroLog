"""
Örnek: Basit Trace Context

Basit trace context kullanımını gösterir.
with trace() context manager ve trace ID'lerin otomatik eklenmesi.

Kullanım:
    python examples/trace/basic_trace.py

Çıktı:
    Log mesajlarına trace_id ve span_id otomatik olarak eklenir.
"""

from microlog import setup_logger, trace, get_current_context


def main():
    # Logger oluştur - return_handlers=True ile handler'ları da alıyoruz
    logger, handlers = setup_logger("myapp", service_name="trace-service", return_handlers=True)
    
    print("Basit Trace Context Örneği")
    print("=" * 60)
    print()
    
    # Trace context olmadan log
    print("1. Trace context olmadan:")
    logger.info("Normal log mesajı")
    print()
    
    # Trace context ile log
    print("2. Trace context ile:")
    with trace(correlation_id="req-123") as ctx:
        # Context bilgilerini göster
        print(f"   Trace ID: {ctx.trace_id}")
        print(f"   Span ID: {ctx.span_id}")
        print(f"   Correlation ID: {ctx.correlation_id}")
        print()
        
        # Log mesajları - trace bilgileri otomatik eklenir
        logger.info("İstek alındı")
        logger.info("İşlem başlatıldı")
        
        # Mevcut context'i al
        current = get_current_context()
        logger.info(
            "Context bilgisi",
            extra={
                "trace_id": current.trace_id,
                "span_id": current.span_id
            }
        )
    
    # Trace context dışında
    print("3. Trace context dışında:")
    logger.info("Trace context olmadan log")
    print()
    
    # Farklı correlation ID ile
    print("4. Farklı correlation ID ile:")
    with trace(correlation_id="req-456", user_id="usr-789") as ctx:
        logger.info("Yeni istek", extra={"user_id": ctx.extra.get("user_id")})
    
    # Graceful shutdown: Handler'ları kapat (queue'daki loglar flush edilir)
    for handler in handlers:
        handler.stop()


if __name__ == "__main__":
    main()

