"""
Örnek: Context Manager

Handler context manager.
Resource cleanup ve graceful shutdown.

Kullanım:
    python examples/advanced/context_manager.py

Çıktı:
    Context manager ile handler'lar otomatik olarak yönetilir.
"""

from microlog import setup_logger, HandlerConfig
from microlog.handlers import AsyncRotatingFileHandler


def with_context_manager():
    """Context manager ile handler kullanımı"""
    log_file = "context_manager.log"
    
    # Context manager ile handler
    with AsyncRotatingFileHandler(
        filename=log_file,
        max_bytes=10 * 1024 * 1024,
        backup_count=5,
        compress=True
    ) as handler:
        # Context manager içinde return_handlers kullanmak zorunlu değil
        # çünkü context manager zaten handler'ı yönetiyor
        logger = setup_logger(
            name="context-app",
            service_name="context-service",
            handlers=[
                HandlerConfig(
                    handler=handler,
                    formatter=None  # Default formatter
                )
            ]
        )
        
        logger.info("Context manager içinde log mesajı")
        logger.info("Handler otomatik olarak yönetiliyor")
        
        # Handler otomatik olarak kapanacak
        print("Context manager içindeyiz, handler aktif")
    
    print("Context manager dışına çıktık, handler otomatik kapatıldı")


def manual_handler_management():
    """Manuel handler yönetimi"""
    log_file = "manual_handler.log"
    
    handler = AsyncRotatingFileHandler(
        filename=log_file,
        max_bytes=10 * 1024 * 1024,
        backup_count=5
    )
    
    # Manuel handler yönetiminde return_handlers kullanmak zorunlu değil
    # çünkü handler zaten manuel olarak yönetiliyor
    logger = setup_logger(
        name="manual-app",
        service_name="manual-service",
        handlers=[HandlerConfig(handler=handler)]
    )
    
    logger.info("Manuel handler ile log mesajı")
    
    # Manuel olarak kapat
    handler.stop()
    print("Handler manuel olarak kapatıldı")


def multiple_handlers_context():
    """Birden fazla handler context manager ile"""
    from microlog.handlers import AsyncConsoleHandler
    
    log_file = "multiple_context.log"
    
    # İki handler context manager ile
    with AsyncConsoleHandler() as console_handler, \
         AsyncRotatingFileHandler(filename=log_file) as file_handler:
        
        # Context manager içinde return_handlers kullanmak zorunlu değil
        # çünkü context manager zaten handler'ları yönetiyor
        logger = setup_logger(
            name="multiple-app",
            service_name="multiple-service",
            handlers=[
                HandlerConfig(handler=console_handler),
                HandlerConfig(handler=file_handler)
            ]
        )
        
        logger.info("Birden fazla handler context manager ile")
        logger.info("Her iki handler da otomatik yönetiliyor")
        
        print("Context manager içindeyiz")
    
    print("Context manager dışına çıktık, tüm handler'lar kapatıldı")


def main():
    """Context manager örnekleri"""
    
    print("Context Manager Örneği")
    print("=" * 60)
    print()
    
    # 1. Context manager ile handler
    print("1. Context Manager ile Handler:")
    with_context_manager()
    print()
    
    # 2. Manuel handler yönetimi
    print("2. Manuel Handler Yönetimi:")
    manual_handler_management()
    print()
    
    # 3. Birden fazla handler
    print("3. Birden Fazla Handler Context Manager ile:")
    multiple_handlers_context()
    print()
    
    # Not: Context manager örneklerinde handler'lar otomatik kapanıyor
    # Bu örnekte time.sleep() gerekmez çünkü context manager kullanılıyor
    
    print("=" * 60)
    print("Örnek tamamlandı!")
    print()
    print("Context Manager Avantajları:")
    print("- Handler'lar otomatik olarak kapatılır")
    print("- Resource leak'ler önlenir")
    print("- Exception durumunda bile cleanup yapılır")
    print("- Kod daha temiz ve güvenli olur")


if __name__ == "__main__":
    main()

