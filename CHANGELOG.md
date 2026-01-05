# Changelog

Tüm önemli değişiklikler bu dosyada belgelenir.

Format [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) standardına uygundur,
ve bu proje [Semantic Versioning](https://semver.org/spec/v2.0.0.html) kullanır.

## [0.1.0] - 2024-01-05

### Eklenenler

- Asenkron logging desteği (QueueHandler ve QueueListener)
- Distributed tracing desteği (trace_id, span_id, parent_span_id)
- Trace context yönetimi (ContextVar tabanlı, thread-safe ve async-safe)
- Çoklu formatter desteği (JSONFormatter, PrettyFormatter, CompactFormatter)
- AsyncConsoleHandler - Console'a asenkron log yazma
- AsyncRotatingFileHandler - Dosya rotation ve gzip compression
- AsyncSMTPHandler - Email bildirimleri ve rate limiting
- Decorator'lar (@log_function, @log_exception, @log_performance, log_context)
- Production-ready logger setup fonksiyonları
- Thread-safe ve memory-safe implementasyon
- Kapsamlı test suite (159 test, %100 başarı)
- Türkçe dokümantasyon

### Özellikler

- **Asenkron Logging**: Ana thread'i bloklamayan, yüksek performanslı logging
- **Distributed Tracing**: Microservice mimarileri için trace context desteği
- **Thread Safety**: Concurrent işlemlerde güvenli kullanım
- **Memory Safety**: Memory leak ve file descriptor leak koruması
- **Production Ready**: API ve microservice ortamlarında test edilmiş
- **Yüksek Performans**: 47,000+ log/saniye throughput

### Dokümantasyon

- Basit kullanım kılavuzu
- Detaylı kullanım dokümantasyonu
- API referansı
- Çalışma mantığı açıklaması
- Davranış şekli ve best practices
- Troubleshooting rehberi

### Testler

- 159 test case
- Unit testler
- Integration testler
- Thread safety testleri
- Edge case testleri
- Stress testleri
- Resource leak testleri
- Failure recovery testleri

[0.1.0]: https://github.com/yourusername/microlog/releases/tag/v0.1.0

