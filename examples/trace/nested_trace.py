"""
Örnek: Nested Trace Context

Parent-child span ilişkisi ve nested context kullanımı.
Child span oluşturma örneği.

Kullanım:
    python examples/trace/nested_trace.py

Çıktı:
    Parent ve child span'lerin trace_id'leri aynı, span_id'leri farklı.
    parent_span_id ilişkisi kurulur.
"""

from microlog import setup_logger, trace, get_current_context


def process_payment(order_id: str):
    """Ödeme işlemi - child span örneği"""
    logger = setup_logger("myapp", service_name="payment-service")
    
    # Parent context'i al
    parent_ctx = get_current_context()
    
    if parent_ctx:
        # Child span oluştur
        with trace(parent=parent_ctx) as child_ctx:
            logger.info(
                "Ödeme işleniyor",
                extra={
                    "order_id": order_id,
                    "trace_id": child_ctx.trace_id,
                    "span_id": child_ctx.span_id,
                    "parent_span_id": child_ctx.parent_span_id
                }
            )
            
            # Simüle edilmiş işlem (gerçek uygulamada async işlem olurdu)
            import time
            time.sleep(0.05)
            
            logger.info("Ödeme tamamlandı", extra={"order_id": order_id})


def update_inventory(order_id: str):
    """Stok güncelleme - başka bir child span"""
    logger = setup_logger("myapp", service_name="inventory-service")
    
    parent_ctx = get_current_context()
    
    if parent_ctx:
        with trace(parent=parent_ctx) as child_ctx:
            logger.info(
                "Stok güncelleniyor",
                extra={
                    "order_id": order_id,
                    "trace_id": child_ctx.trace_id,
                    "span_id": child_ctx.span_id,
                    "parent_span_id": child_ctx.parent_span_id
                }
            )
            
            import time
            time.sleep(0.03)
            
            logger.info("Stok güncellendi", extra={"order_id": order_id})


def main():
    logger, handlers = setup_logger("myapp", service_name="order-service", return_handlers=True)
    
    print("Nested Trace Context Örneği")
    print("=" * 60)
    print()
    
    # Parent trace context
    with trace(correlation_id="order-123") as parent_ctx:
        print(f"Parent Trace ID: {parent_ctx.trace_id}")
        print(f"Parent Span ID: {parent_ctx.span_id}")
        print()
        
        logger.info("Sipariş oluşturuldu", extra={"order_id": "ORD-123"})
        
        # Child span 1: Ödeme işlemi
        print("Child Span 1: Ödeme İşlemi")
        process_payment("ORD-123")
        print()
        
        # Child span 2: Stok güncelleme
        print("Child Span 2: Stok Güncelleme")
        update_inventory("ORD-123")
        print()
        
        logger.info("Sipariş tamamlandı", extra={"order_id": "ORD-123"})
        
        # Context bilgilerini göster
        current = get_current_context()
        print(f"Son Context - Trace ID: {current.trace_id}")
        print(f"Son Context - Span ID: {current.span_id}")
        print()
    
    # Graceful shutdown: Handler'ları kapat (queue'daki loglar flush edilir)
    for handler in handlers:
        handler.stop()


if __name__ == "__main__":
    main()

