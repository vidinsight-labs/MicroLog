"""
Örnek: Flask Entegrasyonu

Flask uygulaması ile MicroLog entegrasyonu.
Middleware ile trace context ve request-response logging.

Kullanım:
    python examples/web/flask_integration.py

Not: Flask kurulu olmalıdır (pip install flask)
"""

from flask import Flask, request, jsonify, g
from microlog import setup_logger, trace, get_current_context

# Logger oluştur - return_handlers=True ile handler'ları da alıyoruz
logger, handlers = setup_logger("flask-app", service_name="flask-api", return_handlers=True)

# Flask uygulaması
app = Flask(__name__)


@app.before_request
def setup_trace_context():
    """Her request için trace context oluştur"""
    # HTTP header'lardan trace context oluştur
    headers = dict(request.headers)
    
    with trace(headers=headers) as ctx:
        # Context'i Flask g objesine kaydet
        g.trace_context = ctx
        logger.info(
            "Request alındı",
            extra={
                "method": request.method,
                "path": request.path,
                "trace_id": ctx.trace_id,
                "span_id": ctx.span_id
            }
        )


@app.after_request
def add_trace_headers(response):
    """Response'a trace header'ları ekle"""
    ctx = get_current_context()
    if ctx:
        # Trace header'larını response'a ekle
        for key, value in ctx.to_headers().items():
            response.headers[key] = value
        
        logger.info(
            "Response hazırlandı",
            extra={
                "status_code": response.status_code,
                "trace_id": ctx.trace_id
            }
        )
    
    return response


@app.route("/")
def index():
    """Ana sayfa"""
    ctx = get_current_context()
    logger.info("Ana sayfa ziyaret edildi")
    
    return jsonify({
        "message": "Flask + MicroLog",
        "trace_id": ctx.trace_id if ctx else None
    })


@app.route("/orders", methods=["POST"])
def create_order():
    """Sipariş oluşturma endpoint'i"""
    ctx = get_current_context()
    
    try:
        data = request.get_json()
        order_id = data.get("order_id", "ORD-001")
        
        logger.info(
            "Sipariş oluşturma isteği",
            extra={
                "order_id": order_id,
                "trace_id": ctx.trace_id if ctx else None
            }
        )
        
        # Simüle edilmiş işlem (gerçek uygulamada async işlem olurdu)
        import time
        time.sleep(0.1)
        
        logger.info("Sipariş oluşturuldu", extra={"order_id": order_id})
        
        return jsonify({
            "status": "success",
            "order_id": order_id,
            "trace_id": ctx.trace_id if ctx else None
        }), 201
        
    except Exception as e:
        logger.exception("Sipariş oluşturma hatası")
        return jsonify({"error": str(e)}), 500


@app.route("/health")
def health():
    """Health check endpoint'i"""
    logger.debug("Health check çağrıldı")
    return jsonify({"status": "healthy"})


@app.errorhandler(404)
def not_found(error):
    """404 hata handler'ı"""
    logger.warning("404 hatası", extra={"path": request.path})
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    """500 hata handler'ı"""
    logger.error("500 hatası", exc_info=error)
    return jsonify({"error": "Internal server error"}), 500


def main():
    """Uygulamayı çalıştır"""
    print("Flask uygulaması başlatılıyor...")
    print("http://localhost:5000 adresinde çalışacak")
    print()
    print("Test endpoint'leri:")
    print("  GET  http://localhost:5000/")
    print("  POST http://localhost:5000/orders")
    print("  GET  http://localhost:5000/health")
    print()
    print("Çıkmak için Ctrl+C")
    print()
    
    app.run(debug=True, port=5000)


if __name__ == "__main__":
    main()

