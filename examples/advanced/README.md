# Gelişmiş Örnekler

Bu klasör, MicroLog'un gelişmiş özelliklerini gösteren örnekleri içerir.

## Örnekler

### 1. custom_formatter.py
Özel formatter oluşturma. Yardımcı fonksiyonlar kullanımı ve custom format implementasyonu.

### 2. multiple_loggers.py
Farklı logger'lar. Modül bazlı logging ve logger hiyerarşisi.

### 3. context_manager.py
Handler context manager. Resource cleanup ve graceful shutdown.

### 4. thread_safety.py
Multi-threaded logging. Thread-safe handler'lar ve concurrent logging örneği.

### 5. signal_handling.py
Signal handling (SIGTERM, SIGINT). Graceful shutdown ve handler cleanup.

## Kullanım

Her örneği çalıştırmak için:

```bash
python examples/advanced/custom_formatter.py
python examples/advanced/multiple_loggers.py
python examples/advanced/context_manager.py
python examples/advanced/thread_safety.py
python examples/advanced/signal_handling.py
```

## Notlar

- Bu örnekler gelişmiş kullanım senaryolarını gösterir
- Production ortamında dikkatli kullanılmalıdır
- Thread safety ve signal handling önemli konulardır

## Sonraki Adımlar

Gelişmiş özellikleri öğrendikten sonra:
- Testing: `examples/testing/`
- Scenarios: `examples/scenarios/`

