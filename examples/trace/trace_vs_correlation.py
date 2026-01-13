"""
Örnek: trace_id vs correlation_id - Fark ve Kullanım

Bu örnek trace_id ve correlation_id arasındaki farkı açıkça gösterir:

TRACE_ID:
- Tek bir HTTP request'in tüm servislerdeki akışını takip eder
- Tüm servislerde AYNI kalır (distributed tracing)
- Her yeni request için YENİ trace_id oluşturulur
- Örnek: Bir kullanıcı "Sipariş Oluştur" butonuna bastığında başlayan tek bir request

CORRELATION_ID:
- Business correlation için kullanılır (order_id, payment_id, user_id, etc.)
- Farklı request'lerde AYNI olabilir (aynı order için farklı işlemler)
- Business mantığına göre belirlenir
- Örnek: Aynı order_id için "create", "update", "cancel" request'leri

Kullanım:
    python examples/trace/trace_vs_correlation.py

Çıktı:
    Aynı order_id (correlation_id) için 3 farklı request (3 farklı trace_id)
    Her request'in farklı servislerdeki akışı aynı trace_id ile takip edilir
"""

import time
from microlog import setup_logger, trace, get_current_context


def simulate_service_call(service_name: str, parent_ctx, operation: str):
    """Servis çağrısı simülasyonu"""
    logger = setup_logger(service_name, service_name=service_name)
    
    # Parent context'ten child span oluştur
    with trace(parent=parent_ctx) as child_ctx:
        logger.info(
            f"{service_name}: {operation}",
            extra={
                "trace_id": child_ctx.trace_id,      # AYNI trace_id
                "span_id": child_ctx.span_id,       # YENİ span_id
                "parent_span_id": child_ctx.parent_span_id,
                "correlation_id": child_ctx.correlation_id  # AYNI correlation_id
            }
        )
        time.sleep(0.01)
        return child_ctx


def process_order_request(request_type: str, order_id: str):
    """
    Order işleme request'i
    
    Her request için:
    - YENİ trace_id oluşturulur (yeni HTTP request)
    - AYNI correlation_id kullanılır (aynı order_id)
    """
    logger, handlers = setup_logger("api-gateway", service_name="api-gateway", return_handlers=True)
    
    print(f"\n{'='*70}")
    print(f"REQUEST: {request_type.upper()} - Order ID: {order_id}")
    print(f"{'='*70}")
    
    # Yeni request = Yeni trace_id
    # Aynı order = Aynı correlation_id
    with trace(correlation_id=order_id) as gateway_ctx:
        print(f"\nAPI GATEWAY (Entry Point):")
        print(f"   trace_id:      {gateway_ctx.trace_id}  ← YENİ (her request için)")
        print(f"   span_id:        {gateway_ctx.span_id}")
        print(f"   correlation_id: {gateway_ctx.correlation_id}  ← AYNI (aynı order)")
        
        logger.info(
            f"API Gateway: {request_type} request received",
            extra={
                "request_type": request_type,
                "order_id": order_id,
                "trace_id": gateway_ctx.trace_id,
                "span_id": gateway_ctx.span_id,
                "correlation_id": gateway_ctx.correlation_id
            }
        )
        
        # Order Service'e istek gönder
        print(f"\nORDER SERVICE:")
        order_ctx = simulate_service_call("order-service", gateway_ctx, request_type)
        print(f"   trace_id:      {order_ctx.trace_id}  ← AYNI trace_id")
        print(f"   span_id:        {order_ctx.span_id}  ← YENİ span_id")
        print(f"   parent_span_id: {order_ctx.parent_span_id}  ← Gateway'in span_id")
        print(f"   correlation_id: {order_ctx.correlation_id}  ← AYNI correlation_id")
        
        # Payment Service'e istek gönder
        print(f"\nPAYMENT SERVICE:")
        payment_ctx = simulate_service_call("payment-service", order_ctx, request_type)
        print(f"   trace_id:      {payment_ctx.trace_id}  ← AYNI trace_id")
        print(f"   span_id:        {payment_ctx.span_id}  ← YENİ span_id")
        print(f"   parent_span_id: {payment_ctx.parent_span_id}  ← Order Service'in span_id")
        print(f"   correlation_id: {payment_ctx.correlation_id}  ← AYNI correlation_id")
        
        # Inventory Service'e istek gönder
        print(f"\nINVENTORY SERVICE:")
        inventory_ctx = simulate_service_call("inventory-service", order_ctx, request_type)
        print(f"   trace_id:      {inventory_ctx.trace_id}  ← AYNI trace_id")
        print(f"   span_id:        {inventory_ctx.span_id}  ← YENİ span_id")
        print(f"   parent_span_id: {inventory_ctx.parent_span_id}  ← Order Service'in span_id")
        print(f"   correlation_id: {inventory_ctx.correlation_id}  ← AYNI correlation_id")
        
        logger.info(
            f"API Gateway: {request_type} completed",
            extra={
                "request_type": request_type,
                "order_id": order_id,
                "trace_id": gateway_ctx.trace_id,
                "correlation_id": gateway_ctx.correlation_id
            }
        )
    
    for handler in handlers:
        handler.stop()


def main():
    """
    Ana senaryo: Aynı order_id için 3 farklı request
    
    Senaryo:
    - Order ID: ORD-12345 (correlation_id)
    - 3 farklı request: CREATE, UPDATE, CANCEL
    - Her request farklı trace_id'ye sahip
    - Hepsi aynı correlation_id'ye sahip (aynı order)
    """
    print("\n" + "="*70)
    print("TRACE_ID vs CORRELATION_ID - FARK VE KULLANIM")
    print("="*70)
    print("\n📚 AÇIKLAMA:")
    print("   trace_id:      Tek bir HTTP request'in tüm servislerdeki akışını takip eder")
    print("                   Her yeni request için YENİ trace_id oluşturulur")
    print("                   Tüm servislerde AYNI kalır (distributed tracing)")
    print()
    print("   correlation_id: Business correlation için (order_id, payment_id, etc.)")
    print("                   Farklı request'lerde AYNI olabilir (aynı order için)")
    print("                   Business mantığına göre belirlenir")
    print()
    print("="*70)
    print("SENARYO: Aynı Order (ORD-12345) için 3 farklı request")
    print("="*70)
    
    # Senaryo: Aynı order için 3 farklı request
    order_id = "ORD-12345"
    
    # Request 1: CREATE
    process_order_request("CREATE", order_id)
    
    time.sleep(0.1)  # Request'ler arası kısa bekleme
    
    # Request 2: UPDATE (aynı order, farklı request)
    process_order_request("UPDATE", order_id)
    
    time.sleep(0.1)
    
    # Request 3: CANCEL (aynı order, farklı request)
    process_order_request("CANCEL", order_id)
    
    print(f"\n{'='*70}")
    print("ÖZET:")
    print(f"{'='*70}")
    print(f"\ntrace_id:")
    print(f"   - Her request için FARKLI (3 request = 3 farklı trace_id)")
    print(f"   - Aynı request içinde tüm servislerde AYNI")
    print(f"   - Distributed tracing için kullanılır")
    print(f"   - Log aggregation sistemlerinde trace görselleştirme")
    print()
    print(f"correlation_id:")
    print(f"   - Business ID (order_id, payment_id, etc.)")
    print(f"   - Tüm request'lerde AYNI (aynı order için)")
    print(f"   - Business correlation için kullanılır")
    print(f"   - 'Bu order için tüm işlemleri bul' sorguları için")
    print()
    print(f"LOG SORGULAMA ÖRNEKLERİ:")
    print(f"   - 'trace_id=abc123' → Tek bir request'in tüm loglarını bul")
    print(f"   - 'correlation_id=ORD-12345' → Bu order için TÜM request'lerin loglarını bul")
    print(f"   - 'trace_id=abc123 AND correlation_id=ORD-12345' → Spesifik request")
    print()
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()

