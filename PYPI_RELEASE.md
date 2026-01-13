# PyPI'ye Yükleme Rehberi

Bu doküman, MicroLog paketini PyPI'ye yükleme adımlarını içerir.

## ✅ Hazırlık Kontrol Listesi

- [x] `pyproject.toml` - Build system ve metadata tanımlı
- [x] `setup.py` - Geriye uyumluluk için mevcut
- [x] `LICENSE` - MIT lisansı mevcut
- [x] `README.md` - Dokümantasyon mevcut
- [x] `src/microlog/__init__.py` - Paket yapısı hazır
- [x] `__version__` - Versiyon tanımlı
- [x] Metadata - Tüm gerekli bilgiler mevcut

## 📦 Adım 1: Build Araçlarını Yükleyin

```bash
pip install build twine
```

## 🔨 Adım 2: Paketi Build Edin

```bash
# Temizlik (opsiyonel)
rm -rf build/ dist/ *.egg-info

# Build
python -m build
```

Bu komut şunları oluşturur:
- `dist/microlog-0.1.0.tar.gz` - Source distribution
- `dist/microlog-0.1.0-py3-none-any.whl` - Wheel distribution

## ✅ Adım 3: Build'i Test Edin

```bash
# Test PyPI'ye yükleyin (önce test edin!)
twine upload --repository testpypi dist/*

# Veya lokal test
pip install dist/microlog-0.1.0-py3-none-any.whl
python -c "import microlog; print(microlog.__version__)"
```

## 🔐 Adım 4: PyPI API Token Oluşturun

1. https://pypi.org/manage/account/token/ adresine gidin
2. "Add API token" butonuna tıklayın
3. Token adı verin (örn: "microlog-upload")
4. Scope: "Entire account" veya sadece proje
5. Token'ı kopyalayın (sadece bir kez gösterilir!)

## 📤 Adım 5: PyPI'ye Yükleyin

### Yöntem 1: Token ile (Önerilen)

```bash
twine upload dist/*
# Username: __token__
# Password: pypi-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Yöntem 2: .pypirc Dosyası ile

```bash
# .pypirc.example dosyasını ~/.pypirc olarak kopyalayın
cp .pypirc.example ~/.pypirc
# Token'ı düzenleyin

# Yükleme
twine upload dist/*
```

### Yöntem 3: Test PyPI'ye Önce Test Edin

```bash
# Test PyPI'ye yükle
twine upload --repository testpypi dist/*

# Test et
pip install --index-url https://test.pypi.org/simple/ microlog

# Her şey tamam ise gerçek PyPI'ye yükle
twine upload dist/*
```

## 🎉 Adım 6: Doğrulama

```bash
# PyPI'den yükleyin
pip install microlog

# Test edin
python -c "from microlog import setup_logger; logger = setup_logger('test'); logger.info('PyPI test!')"
```

## 📝 Versiyon Güncelleme

Yeni versiyon yüklemek için:

1. `pyproject.toml`'da versiyonu güncelleyin:
   ```toml
   version = "0.1.1"
   ```

2. `src/microlog/__init__.py`'de versiyonu güncelleyin:
   ```python
   __version__ = "0.1.1"
   ```

3. `setup.py`'de versiyonu güncelleyin (eğer kullanıyorsanız):
   ```python
   version="0.1.1",
   ```

4. Build ve yükleme:
   ```bash
   python -m build
   twine upload dist/*
   ```

## ⚠️ Önemli Notlar

1. **Paket adı kontrolü**: `microlog` adı PyPI'de müsait mi kontrol edin
   - https://pypi.org/project/microlog/

2. **Test PyPI kullanın**: İlk yüklemede mutlaka testpypi kullanın

3. **Versiyon numarası**: Her yüklemede versiyon numarasını artırın

4. **Metadata kontrolü**: PyPI'de görünecek bilgileri kontrol edin

5. **README formatı**: Markdown formatının doğru render edildiğini kontrol edin

## 🐛 Sorun Giderme

### "Package already exists" hatası
- Versiyon numarasını artırın

### "Invalid metadata" hatası
- `pyproject.toml` formatını kontrol edin
- `python -m build` ile build edin

### "Authentication failed" hatası
- Token'ın doğru olduğundan emin olun
- `__token__` kullanıyorsanız başında `pypi-` olmalı

## 📚 Kaynaklar

- [PyPI Documentation](https://packaging.python.org/en/latest/guides/distributing-packages-using-setuptools/)
- [Twine Documentation](https://twine.readthedocs.io/)
- [Python Packaging Guide](https://packaging.python.org/)
