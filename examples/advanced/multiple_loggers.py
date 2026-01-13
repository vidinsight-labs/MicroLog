"""
Örnek: Multiple Loggers

Farklı logger'lar.
Modül bazlı logging ve logger hiyerarşisi.

Kullanım:
    python examples/advanced/multiple_loggers.py

Çıktı:
    Farklı logger'lar farklı handler'lar ve formatter'lar ile çalışır.
"""

from microlog import setup_logger, setup_console_logger, setup_file_logger


def database_module():
    """Veritabanı modülü - kendi logger'ı"""
    logger = setup_file_logger(
        name="database",
        service_name="db-module",
        filename="database.log",
        format_type="json"
    )
    
    logger.info("Veritabanı bağlantısı kuruldu")
    logger.debug("Sorgu çalıştırıldı", extra={"query": "SELECT * FROM users"})
    logger.warning("Yavaş sorgu", extra={"duration_ms": 1500})


def api_module():
    """API modülü - kendi logger'ı"""
    logger = setup_console_logger(
        name="api",
        service_name="api-module",
        use_colors=True
    )
    
    logger.info("API request alındı", extra={"method": "POST", "path": "/orders"})
    logger.error("API hatası", extra={"status_code": 500})


def business_logic_module():
    """İş mantığı modülü - kendi logger'ı"""
    logger = setup_logger(
        name="business",
        service_name="business-module"
    )
    
    logger.info("İş mantığı çalıştı", extra={"operation": "process_order"})
    logger.warning("İş kuralı uyarısı", extra={"rule": "stock_check"})


def main():
    """Multiple logger örnekleri"""
    
    print("Multiple Loggers Örneği")
    print("=" * 60)
    print()
    
    # Ana logger - return_handlers=True ile handler'ları da alıyoruz
    main_logger, main_handlers = setup_logger(
        name="main-app",
        service_name="main-service",
        return_handlers=True
    )
    
    main_logger.info("Uygulama başlatıldı")
    print()
    
    # 1. Veritabanı modülü
    print("1. Veritabanı Modülü (file logger):")
    database_module()
    print()
    
    # 2. API modülü
    print("2. API Modülü (console logger):")
    api_module()
    print()
    
    # 3. İş mantığı modülü
    print("3. İş Mantığı Modülü (default logger):")
    business_logic_module()
    print()
    
    # 4. Logger hiyerarşisi
    print("4. Logger Hiyerarşisi:")
    parent_logger = setup_logger("parent")
    child_logger = setup_logger("parent.child")
    grandchild_logger = setup_logger("parent.child.grandchild")
    
    parent_logger.info("Parent logger mesajı")
    child_logger.info("Child logger mesajı")
    grandchild_logger.info("Grandchild logger mesajı")
    print()
    
    # 5. Farklı seviyeler
    print("5. Farklı Log Seviyeleri:")
    debug_logger = setup_logger("debug-app")
    debug_logger.setLevel(10)  # DEBUG level
    
    debug_logger.debug("Debug mesajı")
    debug_logger.info("Info mesajı")
    debug_logger.warning("Warning mesajı")
    print()
    
    # Graceful shutdown: Ana handler'ları kapat (queue'daki loglar flush edilir)
    # Not: database_module, api_module, business_logic_module içindeki logger'lar
    #      atexit ile otomatik kapanacak
    for handler in main_handlers:
        handler.stop()
    
    print("=" * 60)
    print("Örnek tamamlandı!")
    print()
    print("Logger Hiyerarşisi Notları:")
    print("- Logger isimleri nokta ile ayrılabilir (parent.child)")
    print("- Her modül kendi logger'ını kullanabilir")
    print("- Farklı handler'lar ve formatter'lar kullanılabilir")


if __name__ == "__main__":
    main()

