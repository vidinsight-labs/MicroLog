#!/usr/bin/env python3
"""
Tüm örnekleri çalıştır
"""

import subprocess
import sys
from pathlib import Path

# Examples dizinini oluştur
Path("logs").mkdir(exist_ok=True)

examples = [
    "basic_usage.py",
    "file_logging.py",
    "decorators_example.py",
    "production_example.py",
    "async_context_example.py",
]

print("=" * 70)
print("MICROLOG ÖRNEKLERİ ÇALIŞTIRILIYOR")
print("=" * 70)

for example in examples:
    print(f"\n{'='*70}")
    print(f"Çalıştırılıyor: {example}")
    print('='*70)
    
    try:
        result = subprocess.run(
            [sys.executable, f"examples/{example}"],
            cwd=".",
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.stdout:
            print(result.stdout)
        
        if result.stderr:
            print("STDERR:", result.stderr, file=sys.stderr)
        
        if result.returncode != 0:
            print(f"❌ Hata: {example} başarısız (kod: {result.returncode})")
        else:
            print(f"✅ {example} başarıyla tamamlandı")
    
    except subprocess.TimeoutExpired:
        print(f"⏱️  {example} timeout (30 saniye)")
    except Exception as e:
        print(f"❌ {example} hatası: {e}")

print("\n" + "=" * 70)
print("TÜM ÖRNEKLER TAMAMLANDI")
print("=" * 70)

