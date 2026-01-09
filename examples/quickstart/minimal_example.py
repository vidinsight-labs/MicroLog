"""
Örnek: Minimal Kullanım

En basit MicroLog kullanımı. Sadece 3 satır kod ile logging başlatma.

Bu örnek:
- setup_logger() ile logger oluşturma
- Temel log mesajları yazma

Kullanım:
    python examples/quickstart/minimal_example.py

Çıktı:
    14:32:01 │ INFO     │ myapp            │ Merhaba MicroLog!
    14:32:02 │ INFO     │ myapp            │ Logging çalışıyor
"""

from microlog import setup_logger


def main():
    # Logger oluştur - return_handlers=True ile handler'ları da alıyoruz
    logger, handlers = setup_logger("myapp", return_handlers=True)

    # Log yaz (iki satır)
    logger.info("Merhaba MicroLog!")
    logger.info("Logging çalışıyor")

    # Graceful shutdown: Handler'ları kapat (queue'daki loglar flush edilir)
    for handler in handlers:
        handler.stop()


if __name__ == "__main__":
    main()