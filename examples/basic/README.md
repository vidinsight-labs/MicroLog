# Temel Kullanım Örnekleri

Bu klasör, MicroLog'un temel özelliklerini gösteren örnekleri içerir.

## Örnekler

### 1. simple_logging.py
En basit logging kullanımı. setup_logger ile başlangıç ve tüm log seviyeleri.

### 2. console_logging.py
Renkli console çıktısı. setup_console_logger kullanımı ve extra alanlar.

### 3. file_logging.py
Dosyaya loglama. JSON format ve dosya rotation örneği.

### 4. multiple_handlers.py
Birden fazla handler kullanımı. Console + File handler birlikte.

## Kullanım

Her örneği çalıştırmak için:

```bash
python examples/basic/simple_logging.py
python examples/basic/console_logging.py
python examples/basic/file_logging.py
python examples/basic/multiple_handlers.py
```

## Sonraki Adımlar

Temel kullanımı öğrendikten sonra:
- Trace Context: `examples/trace/`
- Web Framework: `examples/web/`
