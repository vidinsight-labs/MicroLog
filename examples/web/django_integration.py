"""
Örnek: Django Entegrasyonu

Django uygulaması ile MicroLog entegrasyonu.
Middleware ve settings yapılandırması.

Kullanım:
    Bu örnek Django projesi yapısını gösterir.
    Gerçek Django projesinde kullanmak için:
    1. middleware.py dosyasını Django projenize ekleyin
    2. settings.py'de MIDDLEWARE listesine ekleyin
    3. Logger'ı views.py'de kullanın

Not: Django kurulu olmalıdır (pip install django)
"""

# Bu dosya Django entegrasyonu için örnek kod içerir
# Gerçek Django projesinde kullanmak için aşağıdaki yapıyı takip edin

"""
# 1. middleware.py (Django projenizde oluşturun)

from django.utils.deprecation import MiddlewareMixin
from microlog import setup_logger, trace, get_current_context

# Django uygulamasında logger genellikle modül seviyesinde oluşturulur
# return_handlers kullanmak isteğe bağlıdır (Django shutdown hook'larında kullanılabilir)
logger, handlers = setup_logger("django-app", service_name="django-api", return_handlers=True)


class TraceMiddleware(MiddlewareMixin):
    \"\"\"Django middleware ile trace context\"\"\"
    
    def process_request(self, request):
        # Django request header'larını dict'e çevir
        headers = {
            k.replace("HTTP_", "").replace("_", "-").title(): v
            for k, v in request.META.items()
            if k.startswith("HTTP_")
        }
        
        # Trace context oluştur
        request.trace_context = trace(headers=headers)
        request.trace_context.__enter__()
        
        # Request logging
        ctx = get_current_context()
        logger.info(
            "Request alındı",
            extra={
                "method": request.method,
                "path": request.path,
                "trace_id": ctx.trace_id if ctx else None
            }
        )
    
    def process_response(self, request, response):
        ctx = get_current_context()
        
        # Response header'larına trace bilgisi ekle
        if ctx:
            for key, value in ctx.to_headers().items():
                response[key] = value
            
            logger.info(
                "Response hazırlandı",
                extra={
                    "status_code": response.status_code,
                    "trace_id": ctx.trace_id
                }
            )
        
        # Trace context'i temizle
        if hasattr(request, "trace_context"):
            request.trace_context.__exit__(None, None, None)
        
        return response


# 2. settings.py (Django projenizde)

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'your_app.middleware.TraceMiddleware',  # MicroLog middleware ekleyin
]


# 3. views.py (Django projenizde)

from django.http import JsonResponse
from microlog import setup_logger, get_current_context

# Django views'de logger genellikle modül seviyesinde oluşturulur
# return_handlers kullanmak isteğe bağlıdır (Django shutdown hook'larında kullanılabilir)
logger, handlers = setup_logger("django-app", service_name="django-api", return_handlers=True)


def index(request):
    \"\"\"Ana sayfa view\"\"\"
    ctx = get_current_context()
    logger.info("Ana sayfa ziyaret edildi")
    
    return JsonResponse({
        "message": "Django + MicroLog",
        "trace_id": ctx.trace_id if ctx else None
    })


def create_order(request):
    \"\"\"Sipariş oluşturma view\"\"\"
    ctx = get_current_context()
    
    try:
        import json
        data = json.loads(request.body)
        order_id = data.get("order_id", "ORD-001")
        
        logger.info(
            "Sipariş oluşturma isteği",
            extra={
                "order_id": order_id,
                "trace_id": ctx.trace_id if ctx else None
            }
        )
        
        logger.info("Sipariş oluşturuldu", extra={"order_id": order_id})
        
        return JsonResponse({
            "status": "success",
            "order_id": order_id,
            "trace_id": ctx.trace_id if ctx else None
        })
        
    except Exception as e:
        logger.exception("Sipariş oluşturma hatası")
        return JsonResponse({"error": str(e)}, status=500)
"""


def main():
    """Django entegrasyonu örnekleri"""
    print("Django Entegrasyonu Örneği")
    print("=" * 60)
    print()
    print("Bu örnek Django projesi yapısını gösterir.")
    print("Gerçek Django projesinde kullanmak için:")
    print()
    print("1. middleware.py dosyasını Django projenize ekleyin")
    print("2. settings.py'de MIDDLEWARE listesine ekleyin")
    print("3. Logger'ı views.py'de kullanın")
    print()
    print("Detaylı kod yukarıdaki docstring'de bulunmaktadır.")


if __name__ == "__main__":
    main()

