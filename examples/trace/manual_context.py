"""
Örnek: Manuel Context Yönetimi

set_current_context, clear_current_context ve create_trace kullanımı.
Manuel trace context oluşturma ve yönetimi.

Kullanım:
    python examples/trace/manual_context.py

Çıktı:
    Manuel context yönetimi ile trace bilgileri loglanır.
"""

from microlog import setup_logger, get_current_context
from microlog.context import (
    TraceContext,
    set_current_context,
    clear_current_context,
    create_trace
)


def main():
    # Logger oluştur - return_handlers=True ile handler'ları da alıyoruz
    logger, handlers = setup_logger("myapp", service_name="context-service", return_handlers=True)
    
    print("Manuel Context Yönetimi Örneği")
    print("=" * 60)
    print()
    
    # 1. create_trace ile context oluşturma
    print("1. create_trace ile context oluşturma:")
    ctx1 = create_trace(
        trace_id="custom-trace-123",
        correlation_id="req-456",
        session_id="session-789",
        extra={"user_id": "usr-999"}  # Extra alanlar extra dict içinde
    )
    
    print(f"   Trace ID: {ctx1.trace_id}")
    print(f"   Span ID: {ctx1.span_id}")
    print(f"   Correlation ID: {ctx1.correlation_id}")
    print()
    
    # 2. set_current_context ile context ayarlama
    print("2. set_current_context ile context ayarlama:")
    set_current_context(ctx1)
    
    current = get_current_context()
    logger.info(
        "Manuel context ile log",
        extra={
            "trace_id": current.trace_id if current else None,
            "correlation_id": current.correlation_id if current else None
        }
    )
    print(f"   Mevcut context: {current.trace_id if current else None}")
    print()
    
    # 3. Yeni context oluştur ve değiştir
    print("3. Yeni context oluştur ve değiştir:")
    ctx2 = create_trace(
        trace_id="new-trace-456",
        correlation_id="req-789"
    )
    
    set_current_context(ctx2)
    current = get_current_context()
    logger.info("Yeni context ile log", extra={"trace_id": current.trace_id if current else None})
    print(f"   Yeni context: {current.trace_id if current else None}")
    print()
    
    # 4. clear_current_context ile temizleme
    print("4. clear_current_context ile temizleme:")
    clear_current_context()
    
    current = get_current_context()
    logger.info("Context temizlendikten sonra log", extra={"trace_id": current.trace_id if current else None})
    print(f"   Mevcut context: {current}")
    print()
    
    # 5. TraceContext direkt oluşturma
    print("5. TraceContext direkt oluşturma:")
    ctx3 = TraceContext(
        trace_id="direct-trace-789",
        span_id="direct-span-123",
        correlation_id="req-direct",
        session_id="session-direct",
        extra={"custom_field": "custom_value"}
    )
    
    set_current_context(ctx3)
    current = get_current_context()
    logger.info(
        "Direkt TraceContext ile log",
        extra={
            "trace_id": current.trace_id if current else None,
            "custom_field": current.extra.get("custom_field") if current else None
        }
    )
    print(f"   Direkt context: {current.trace_id if current else None}")
    print()
    
    # 6. Context stack simülasyonu
    print("6. Context Stack Simülasyonu:")
    contexts = [
        create_trace(trace_id=f"trace-{i}", correlation_id=f"req-{i}")
        for i in range(3)
    ]
    
    for i, ctx in enumerate(contexts):
        set_current_context(ctx)
        current = get_current_context()
        logger.info(f"Context {i+1} aktif", extra={"trace_id": current.trace_id if current else None})
        print(f"   Context {i+1}: {current.trace_id if current else None}")
    
    # Son context'i temizle
    clear_current_context()
    print("   Tüm context'ler temizlendi")
    print()
    
    # Graceful shutdown: Handler'ları kapat (queue'daki loglar flush edilir)
    for handler in handlers:
        handler.stop()
    
    print("=" * 60)
    print("Örnek tamamlandı!")
    print()
    print("Manuel Context Yönetimi:")
    print("- create_trace: Yeni TraceContext oluşturur")
    print("- set_current_context: Aktif context'i ayarlar")
    print("- clear_current_context: Aktif context'i temizler")
    print("- get_current_context: Mevcut context'i alır")
    print("- TraceContext: Direkt context oluşturma")


if __name__ == "__main__":
    main()

