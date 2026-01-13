"""
Örnek: FastAPI Entegrasyonu

FastAPI uygulaması ile MicroLog entegrasyonu.
Async middleware ve dependency injection ile logger.

Kullanım:
    uvicorn examples.web.fastapi_integration:app --reload

Not: FastAPI ve uvicorn kurulu olmalıdır (pip install fastapi uvicorn)
"""

import asyncio
from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
from microlog import setup_logger, trace, get_current_context

# Logger oluştur - return_handlers=True ile handler'ları da alıyoruz
# Not: Web server örneklerinde handler'lar server çalışırken açık kalmalı
#      Bu yüzden handler'ları kapatmak için özel bir shutdown hook gerekebilir
logger, handlers = setup_logger("fastapi-app", service_name="fastapi-api", return_handlers=True)

# FastAPI uygulaması
app = FastAPI(title="FastAPI + MicroLog Example")


@app.middleware("http")
async def trace_middleware(request: Request, call_next):
    """Her request için trace context oluştur"""
    # HTTP header'lardan trace context oluştur
    headers = dict(request.headers)
    
    async with trace(headers=headers) as ctx:
        # Request logging
        logger.info(
            "Request alındı",
            extra={
                "method": request.method,
                "path": request.url.path,
                "trace_id": ctx.trace_id,
                "span_id": ctx.span_id
            }
        )
        
        # Request'i işle
        response = await call_next(request)
        
        # Response header'larına trace bilgisi ekle
        for key, value in ctx.to_headers().items():
            response.headers[key] = value
        
        # Response logging
        logger.info(
            "Response hazırlandı",
            extra={
                "status_code": response.status_code,
                "trace_id": ctx.trace_id
            }
        )
        
        return response


def get_logger():
    """Logger dependency"""
    return logger


@app.get("/")
async def index(logger=Depends(get_logger)):
    """Ana sayfa"""
    ctx = get_current_context()
    logger.info("Ana sayfa ziyaret edildi")
    
    return {
        "message": "FastAPI + MicroLog",
        "trace_id": ctx.trace_id if ctx else None
    }


@app.post("/orders")
async def create_order(request: Request, logger=Depends(get_logger)):
    """Sipariş oluşturma endpoint'i"""
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
        
        return {
            "status": "success",
            "order_id": order_id,
            "trace_id": ctx.trace_id if ctx else None
        }
        
    except Exception as e:
        logger.exception("Sipariş oluşturma hatası")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.get("/health")
async def health(logger=Depends(get_logger)):
    """Health check endpoint'i"""
    logger.debug("Health check çağrıldı")
    return {"status": "healthy"}


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """404 hata handler'ı"""
    logger.warning("404 hatası", extra={"path": request.url.path})
    return JSONResponse(
        status_code=404,
        content={"error": "Not found"}
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """500 hata handler'ı"""
    logger.error("500 hatası", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )


def main():
    """Uygulamayı çalıştır"""
    print("FastAPI uygulaması başlatılıyor...")
    print("Uvicorn ile çalıştırın:")
    print("  uvicorn examples.web.fastapi_integration:app --reload")
    print()
    print("Test endpoint'leri:")
    print("  GET  http://localhost:8000/")
    print("  POST http://localhost:8000/orders")
    print("  GET  http://localhost:8000/health")
    print()
    print("API Docs: http://localhost:8000/docs")


if __name__ == "__main__":
    main()

