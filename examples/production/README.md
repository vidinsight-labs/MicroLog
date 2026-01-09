# Production Örnekleri

Bu klasör, MicroLog'un production ortamında kullanımı için örnekleri içerir.

## Örnekler

### 1. production_config.py
Production yapılandırması. JSON formatter, file rotation ve error handling.

### 2. structured_logging.py
Yapılandırılmış logging. Extra alanlar best practices ve log aggregation hazırlığı.

### 3. error_tracking.py
Exception logging. Error tracking ve stack trace formatlama.

### 4. performance_logging.py
Performance metrikleri. Timing bilgileri ve resource usage logging.

## Kullanım

Her örneği çalıştırmak için:

```bash
python examples/production/production_config.py
python examples/production/structured_logging.py
python examples/production/error_tracking.py
python examples/production/performance_logging.py
```

## Notlar

- Production örnekleri JSON format kullanır (log aggregation için)
- File rotation otomatik yapılır
- Error handling ve recovery mekanizmaları gösterilir
- Performance metrikleri logging ile entegre edilir

## Sonraki Adımlar

Production kullanımını öğrendikten sonra:
- Advanced: `examples/advanced/`
- Testing: `examples/testing/`

