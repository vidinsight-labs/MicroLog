"""
Örnek: Signal Handling

Signal handling (SIGTERM, SIGINT).
Graceful shutdown ve handler cleanup.

Kullanım:
    python examples/advanced/signal_handling.py

Çıktı:
    Signal'lar yakalanır ve handler'lar düzgün şekilde kapatılır.
    Ctrl+C ile test edebilirsiniz.
"""

import os
import time
import signal
import sys
from microlog import setup_file_logger
from microlog.handlers import AsyncRotatingFileHandler


def signal_handler(signum, frame):
    """Signal handler"""
    logger = setup_file_logger(
        name="signal-app",
        service_name="signal-service",
        filename="signal.log",
        format_type="json"
    )
    
    signal_name = signal.Signals(signum).name
    logger.warning(
        f"Signal alındı: {signal_name}",
        extra={
            "signal": signal_name,
            "signal_number": signum
        }
    )
    
    print(f"\nSignal alındı: {signal_name}")
    print("Graceful shutdown başlatılıyor...")
    
    # Handler'ları kapat (örnek için)
    # Gerçek uygulamada handler referanslarını saklamanız gerekir
    sys.exit(0)


def long_running_process():
    """Uzun süren işlem - signal handling ile"""
    log_file = "signal.log"
    
    if os.path.exists(log_file):
        os.remove(log_file)
    
    logger, handlers = setup_file_logger(
        name="signal-app",
        service_name="signal-service",
        filename=log_file,
        format_type="json",
        return_handlers=True
    )
    
    # Signal handler'ları kaydet
    signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Termination signal
    
    logger.info("Uygulama başlatıldı", extra={"pid": os.getpid()})
    print("Uygulama çalışıyor...")
    print("Ctrl+C ile durdurabilirsiniz")
    print()
    
    try:
        # Simüle edilmiş uzun süren işlem
        for i in range(100):
            logger.info(
                f"İşlem devam ediyor - iterasyon {i+1}",
                extra={
                    "iteration": i+1,
                    "total": 100
                }
            )
            time.sleep(0.1)
            
            # Her 10 iterasyonda bir bilgi ver
            if (i + 1) % 10 == 0:
                print(f"İlerleme: {i+1}/100")
        
        logger.info("Uygulama normal şekilde tamamlandı")
        print("\nUygulama tamamlandı!")
        
    except KeyboardInterrupt:
        # KeyboardInterrupt da signal handler tarafından yakalanır
        pass
    
    # Graceful shutdown: Handler'ı kapat (queue'daki loglar flush edilir)
    # Not: Signal handler içindeki logger atexit ile otomatik kapanacak
    for handler in handlers:
        handler.stop()


def main():
    """Signal handling örneği"""
    
    print("Signal Handling Örneği")
    print("=" * 60)
    print()
    print("Bu örnek signal handling gösterir.")
    print("Uzun süren işlem başlatılıyor...")
    print("Ctrl+C ile durdurabilirsiniz.")
    print()
    
    # Kısa süreli test için
    print("Kısa test modu (5 saniye):")
    long_running_process()
    
    print()
    print("=" * 60)
    print("Örnek tamamlandı!")
    print()
    print("Signal Handling Notları:")
    print("- SIGINT (Ctrl+C) ve SIGTERM yakalanır")
    print("- Handler'lar graceful shutdown yapar")
    print("- Log mesajları signal'dan önce yazılır")
    print("- Production'da signal handling önemlidir")


if __name__ == "__main__":
    main()

