#!/usr/bin/env python3
"""
Configuration File Kullanım Örneği

YAML/JSON configuration dosyalarından logger oluşturma.
"""

import os
import sys

# MicroLog'u import et
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from microlog import setup_from_config, load_config, trace
import logging

print("=" * 60)
print("CONFIGURATION FILE EXAMPLE")
print("=" * 60)

# Örnek 1: YAML dosyasından logger oluştur
print("\n📄 Örnek 1: YAML Config File")
print("-" * 60)

try:
    logger = setup_from_config("examples/config.yaml")
    
    logger.info("YAML config ile logger oluşturuldu")
    logger.debug("Debug mesajı (görünmeyebilir)")
    logger.warning("Uyarı mesajı")
    
    with trace(trace_id="yaml-test"):
        logger.info("Trace context ile log")
    
    print("✅ YAML config başarılı")
    
except FileNotFoundError:
    print("⚠️  config.yaml bulunamadı, atlanıyor")
except Exception as e:
    print(f"❌ Hata: {e}")

# Örnek 2: Environment variable'dan config yükle
print("\n🌍 Örnek 2: Environment Variable Config")
print("-" * 60)

# Config path'i environment variable'a set et
os.environ["MICROLOG_CONFIG"] = "examples/config.yaml"

try:
    from microlog import load_config_from_env
    
    config = load_config_from_env()
    if config:
        logger2 = setup_from_config(config, logger_name="env-logger")
        logger2.info("Environment variable'dan config yüklendi")
        print("✅ Environment config başarılı")
    else:
        print("⚠️  MICROLOG_CONFIG environment variable bulunamadı")
        
except Exception as e:
    print(f"❌ Hata: {e}")

# Örnek 3: Programmatik config (dict)
print("\n⚙️  Örnek 3: Programmatic Config (Dict)")
print("-" * 60)

config_dict = {
    "logging": {
        "name": "dict-logger",
        "level": "DEBUG",
        "service_name": "dict-service",
        "formatter": {
            "type": "pretty",
            "service_name": "dict-service"
        },
        "handlers": [
            {
                "type": "console",
                "level": "DEBUG"
            }
        ]
    }
}

try:
    logger3 = setup_from_config(config_dict)
    logger3.debug("Dict config ile DEBUG log")
    logger3.info("Dict config ile INFO log")
    logger3.error("Dict config ile ERROR log")
    print("✅ Dict config başarılı")
    
except Exception as e:
    print(f"❌ Hata: {e}")

# Örnek 4: Production config (commented out - requires SMTP setup)
print("\n🏭 Örnek 4: Production Config")
print("-" * 60)
print("Production config için: examples/config_production.yaml")
print("(SMTP ayarları gerektirir, bu örnekte atlandı)")

import time
time.sleep(1.0)  # Logların yazılması için bekle

print("\n✅ Configuration örneği tamamlandı!")
print("\n📖 Detaylı bilgi için:")
print("  - docs/DETAYLI_KULLANIM.md")
print("  - docs/API_REFERANSI.md")

