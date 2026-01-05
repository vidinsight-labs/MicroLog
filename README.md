
<img width="1584" height="396" alt="LinkedIn Banner Design" src="https://github.com/user-attachments/assets/8692e053-14f7-4e7a-8320-24a518e275ba" />

# MicroLog - Modern Python Logging Kütüphanesi

MicroLog, production ortamları için tasarlanmış, thread-safe, asenkron Python logging kütüphanesidir. Distributed tracing desteği, yüksek performans ve kolay kullanım sunar.

## Özellikler

- **Asenkron Logging** - Ana thread'i bloklamaz
- **Distributed Tracing** - `trace_id`, `span_id`, `parent_span_id` desteği
- **Çoklu Formatter** - JSON, Pretty, Compact formatlar
- **Dosya Rotation** - Boyut bazlı rotation + gzip compression
- **Email Bildirimleri** - SMTP handler ile rate limiting
- **Thread-Safe** - Concurrent işlemlerde güvenli
- **Yüksek Performans** - 47,000+ log/saniye
- **Production-Ready** - 159 test ile doğrulanmış

## Kurulum

```bash
# Projeyi klonlayın
git clone <repository-url>
cd MicroLog

# Geliştirme modunda kurulum
pip install -e .

# Veya direkt kullanım (src dizinini PYTHONPATH'e ekleyin)
export PYTHONPATH=$(pwd)/src:$PYTHONPATH
```

## Hızlı Başlangıç

```python
from microlog import setup_logger, trace
import logging

# Logger oluştur
logger = setup_logger("myapp", level=logging.INFO)

# Basit logging
logger.info("Uygulama başlatıldı")

# Trace context ile
with trace(trace_id="req-123"):
    logger.info("İstek işleniyor")
```

## Dokümantasyon

- **[Basit Kullanım](docs/BASIT_KULLANIM.md)** - Hızlı başlangıç ve temel örnekler
- **[Detaylı Kullanım](docs/DETAYLI_KULLANIM.md)** - Tüm özellikler ve gelişmiş kullanım
- **[API Referansı](docs/API_REFERANSI.md)** - Tüm fonksiyonlar, classlar ve parametreler
- **[Çalışma Mantığı](docs/CALISMA_MANTIGI.md)** - İç mimari ve nasıl çalışıyor
- **[Davranış Şekli](docs/DAVRANIS_SEKLI.md)** - Davranışlar, edge cases ve best practices

## Test Durumu

- **159 test** - Tüm testler geçiyor (%100)
- **Thread safety** - Doğrulandı
- **Memory stability** - Leak yok
- **Performance** - 47,000+ log/saniye
- **Production ready** - API ve microservice ortamlarında test edildi

## Örnekler

Detaylı örnekler için `examples/` dizinine bakın:

- `basic_usage.py` - Temel kullanım
- `file_logging.py` - Dosya logging
- `decorators_example.py` - Decorator kullanımı
- `production_example.py` - Production senaryosu
- `async_context_example.py` - AsyncIO kullanımı
- `advanced_features.py` - Gelişmiş özellikler
- `compression_example.py` - Compression örneği

## Katkıda Bulunma

Katkılarınızı bekliyoruz. Lütfen issue açmadan veya PR göndermeden önce testlerin geçtiğinden emin olun.

## Destek

Sorularınız için issue açabilir veya dokümantasyona bakabilirsiniz.

---

MicroLog ile güvenli, performanslı ve kolay logging yapabilirsiniz.
