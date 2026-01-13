from setuptools import setup, find_packages
from os import path

this_directory = path.abspath(path.dirname(__file__))

with open(path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="vi-microlog",
    version="0.1.0",
    author="VidInsight Yazılım ve Teknoloji Anonim Şirketi",
    author_email="info@vidinsight.com",
    description="MicroLog, Python için yüksek performanslı asenkron logging kütüphanesidir.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/vidinsight/microlog",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    license="MIT",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Logging",
    ],
    python_requires=">=3.7",
    install_requires=[],
)

"""
Bu dosya bir python paketini yüklemek, dağıtmak ve PyPI'ye yüklemek için kullanılan yapılandırma
dosyasıdır. "setuptools" kütüphanesi tarafından kullanılır.

Ne işe yarar?
- Paket kurulumu: pip install . veya pip install -e .
- Paket dağıtımı: python setup.py sdist bdist_wheel (wheel/source distribution)
- PyPI yükleme: twine upload dist/*
- Metadata sağlama: Paket bilgileri (isim, versiyon, yazar, vb.)

Hangi bölümlerden oluşur?

1. Hazırlık Bölümü (Import ve Veri Hazırlama)
   - setuptools import: setup() fonksiyonu ve find_packages() yardımcı fonksiyonu
   - os.path import: Dosya yolları için
   - README.md okuma: PyPI'de gösterilecek uzun açıklama için

2. setup() Fonksiyonunun Elemanları:

   2.1. Temel Kimlik Bilgileri (Zorunlu)
   - name: Paket adı (PyPI'de görünecek, pip install microlog)
   - version: SemVer formatında versiyon numarası (0.1.0, 1.2.3, vb.)
   - description: Tek satır kısa açıklama (PyPI'de paket listesinde görünür)

   2.2. Yazar ve İletişim Bilgileri
   - author: Paket yazarı veya organizasyon adı
   - author_email: İletişim e-posta adresi

   2.3. Açıklama ve Dokümantasyon
   - long_description: README.md içeriği (PyPI'de detay sayfasında görünür)
   - long_description_content_type: README formatı (text/markdown veya text/plain)

   2.4. Paket Yapısı (Kritik)
   - packages: Yüklenecek Python paketlerini belirler (find_packages ile otomatik bulma)
   - package_dir: Paket dizini eşlemesi ({"": "src"} = src/ dizinindeki paketleri bul)

   2.5. Lisans Bilgisi
   - license: Lisans tipi (MIT, Apache-2.0, GPL-3.0, vb.)

   2.6. Bağımlılıklar
   - install_requires: Paket kurulurken otomatik yüklenecek zorunlu bağımlılıklar
   - python_requires: Minimum Python versiyonu gereksinimi

   2.7. Classifiers (PyPI Kategorileri)
   - Development Status: Geliştirme durumu (Alpha, Beta, Stable)
   - License: Lisans bilgisi
   - Programming Language: Desteklenen Python versiyonları
   - Topic: Paket konuları (Logging, Libraries, vb.)

   2.8. URL ve Proje Linkleri
   - url: Ana proje URL'si (GitHub, GitLab, vb.)

Kurulum Sırasında Ne Olur?
1. setup.py okunur ve metadata çıkarılır
2. Paket yapısı analiz edilir (packages, package_dir)
3. Bağımlılıklar kontrol edilir ve yüklenir (install_requires)
4. Python versiyonu kontrol edilir (python_requires)
5. Paket dosyaları site-packages'e kopyalanır
6. Metadata kaydedilir (.dist-info veya .egg-info)
"""