"""
Örnek: Async Web Server

Async web server örneği.
Aiohttp ile entegrasyon ve async request handling.

Kullanım:
    python examples/async/async_web.py

Not: Aiohttp kurulu olmalıdır (pip install aiohttp)

Bu örnek aiohttp kullanarak async web server gösterir.
Gerçek kullanımda FastAPI veya başka async framework kullanılabilir.
"""

import asyncio
from aiohttp import web
from microlog import setup_logger, trace, get_current_context

# Logger oluştur - return_handlers=True ile handler'ları da alıyoruz
logger, handlers = setup_logger("async-web", service_name="async-api", return_handlers=True)


async def handle_index(request):
    """Ana sayfa handler"""
    ctx = get_current_context()
    logger.info("Ana sayfa ziyaret edildi")
    
    return web.json_response({
        "message": "Async Web Server + MicroLog",
        "trace_id": ctx.trace_id if ctx else None
    })


async def handle_orders(request):
    """Sipariş endpoint handler"""
    ctx = get_current_context()
    
    try:
        data = await request.json()
        order_id = data.get("order_id", "ORD-001")
        
        logger.info(
            "Sipariş oluşturma isteği",
            extra={
                "order_id": order_id,
                "trace_id": ctx.trace_id if ctx else None
            }
        )
        
        # Simüle edilmiş async işlem
        await asyncio.sleep(0.1)
        
        logger.info("Sipariş oluşturuldu", extra={"order_id": order_id})
        
        return web.json_response({
            "status": "success",
            "order_id": order_id,
            "trace_id": ctx.trace_id if ctx else None
        })
        
    except Exception as e:
        logger.exception("Sipariş oluşturma hatası")
        return web.json_response(
            {"error": str(e)},
            status=500
        )


async def handle_health(request):
    """Health check handler"""
    logger.debug("Health check çağrıldı")
    return web.json_response({"status": "healthy"})


@web.middleware
async def trace_middleware(request, handler):
    """Trace context middleware"""
    # HTTP header'lardan trace context oluştur
    headers = dict(request.headers)
    
    async with trace(headers=headers) as ctx:
        # Request logging
        logger.info(
            "Request alındı",
            extra={
                "method": request.method,
                "path": request.path_qs,
                "trace_id": ctx.trace_id,
                "span_id": ctx.span_id
            }
        )
        
        # Request'i işle
        response = await handler(request)
        
        # Response header'larına trace bilgisi ekle
        for key, value in ctx.to_headers().items():
            response.headers[key] = value
        
        # Response logging
        logger.info(
            "Response hazırlandı",
            extra={
                "status": response.status,
                "trace_id": ctx.trace_id
            }
        )
        
        return response


def create_app():
    """Aiohttp uygulaması oluştur"""
    app = web.Application(middlewares=[trace_middleware])
    
    # Route'lar
    app.router.add_get("/", handle_index)
    app.router.add_post("/orders", handle_orders)
    app.router.add_get("/health", handle_health)
    
    return app


def main():
    """Uygulamayı çalıştır"""
    print("Async Web Server Örneği")
    print("=" * 60)
    print()
    print("Aiohttp ile async web server başlatılıyor...")
    print("http://localhost:8080 adresinde çalışacak")
    print()
    print("Test endpoint'leri:")
    print("  GET  http://localhost:8080/")
    print("  POST http://localhost:8080/orders")
    print("  GET  http://localhost:8080/health")
    print()
    print("Çıkmak için Ctrl+C")
    print()
    
    app = create_app()
    
    try:
        web.run_app(app, host="localhost", port=8080)
    except KeyboardInterrupt:
        print("\nServer durduruldu")
        # Graceful shutdown: Handler'ları kapat (queue'daki loglar flush edilir)
        for handler in handlers:
            handler.stop()


if __name__ == "__main__":
    main()

