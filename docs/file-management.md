# Dosya Yönetimi - Log Dosyaları

MicroLog, log dosyalarını otomatik olarak yönetir. Bu doküman, dosyaların nasıl oluşturulduğunu, isimlendirildiğini ve yönetildiğini açıklar.

## Hızlı Özet

- **Aktif dosya**: `filename` parametresi ile belirlenir (örn: `app.log`)
- **Backup dosyaları**: `backup_count` kadar eski dosya saklanır
- **Toplam dosya sayısı**: 1 aktif + `backup_count` backup = **`backup_count + 1` dosya**
- **Rotation**: `max_bytes` aşıldığında otomatik olur
- **Sıkıştırma**: `compress=True` ise backup'lar `.gz` ile sıkıştırılır

---

## Dosya Oluşturma

### Temel Kullanım

```python
from microlog import setup_file_logger

logger = setup_file_logger(
    name="myapp",
    filename="app.log",        # Dosya adı
    max_bytes=10 * 1024 * 1024, # 10MB
    backup_count=5,             # 5 backup dosyası
    compress=True                # Sıkıştır
)
```

**Sonuç:**
- İlk log yazımında `app.log` dosyası oluşturulur
- Dizin yoksa otomatik oluşturulur (`/var/log/myapp/` → otomatik oluşur)

---

## Dosya İsimlendirme

### Aktif Dosya

```
app.log          # Aktif dosya (yazma devam ediyor)
```

### Backup Dosyaları

Rotation sonrası eski dosyalar numaralandırılır:

```
app.log.1        # En yeni backup
app.log.2        # İkinci backup
app.log.3        # Üçüncü backup
app.log.4        # Dördüncü backup
app.log.5        # En eski backup (backup_count=5)
```

### Sıkıştırılmış Dosyalar

`compress=True` ise backup'lar gzip ile sıkıştırılır:

```
app.log          # Aktif (sıkıştırılmamış)
app.log.1.gz     # En yeni backup (sıkıştırılmış)
app.log.2.gz     # İkinci backup (sıkıştırılmış)
app.log.3.gz     # Üçüncü backup (sıkıştırılmış)
app.log.4.gz     # Dördüncü backup (sıkıştırılmış)
app.log.5.gz     # En eski backup (sıkıştırılmış)
```

---

## Dosya Sayısı

### Toplam Dosya Sayısı

```
Toplam = 1 (aktif) + backup_count (backup)
```

**Örnekler:**

| backup_count | Toplam Dosya | Açıklama |
|--------------|--------------|----------|
| 0 | 1 | Sadece aktif dosya, backup yok |
| 1 | 2 | 1 aktif + 1 backup |
| 5 | 6 | 1 aktif + 5 backup |
| 10 | 11 | 1 aktif + 10 backup |

### Örnek Senaryo

```python
handler = AsyncRotatingFileHandler(
    filename="app.log",
    backup_count=5
)
```

**Dosya yapısı:**
```
app.log          # Aktif (yazılıyor)
app.log.1        # En yeni backup
app.log.2        # İkinci backup
app.log.3        # Üçüncü backup
app.log.4        # Dördüncü backup
app.log.5        # En eski backup
```

**Toplam: 6 dosya** (1 aktif + 5 backup)

---

## Rotation (Döndürme)

### Ne Zaman Rotation Olur?

Rotation, **her log yazımında** dosya boyutu kontrol edilir ve `max_bytes` aşıldığında tetiklenir.

```python
handler = AsyncRotatingFileHandler(
    filename="app.log",
    max_bytes=10 * 1024 * 1024,  # 10MB
    backup_count=5
)
```

**Rotation süreci:**
1. `app.log` dosyası 10MB'a ulaştı
2. `app.log` → `app.log.1` olarak kaydedilir (veya `app.log.1.gz` if compress=True)
3. Eski backup'lar kaydırılır: `app.log.1` → `app.log.2`, `app.log.2` → `app.log.3`, ...
4. En eski backup silinir: `app.log.5` silinir
5. Yeni `app.log` dosyası oluşturulur (boş)

### Rotation Örneği

**Başlangıç:**
```
app.log (10MB)  ← Aktif, dolu
```

**Rotation sonrası:**
```
app.log (0MB)   ← Yeni, boş
app.log.1.gz    ← Eski app.log (sıkıştırılmış)
app.log.2.gz    ← Eski app.log.1
app.log.3.gz    ← Eski app.log.2
app.log.4.gz    ← Eski app.log.3
app.log.5.gz    ← Eski app.log.4
# app.log.5.gz silindi (backup_count=5 limiti)
```

---

## Parametreler ve Etkileri

### filename

**Ne yapar:** Log dosyasının adını ve yolunu belirler.

```python
filename="app.log"                    # Mevcut dizinde
filename="/var/log/myapp/app.log"     # Tam yol
filename="logs/app.log"                # Alt dizinde
```

**Etkiler:**
- Dizin yoksa **otomatik oluşturulur**
- Dosya yoksa **otomatik oluşturulur**
- İlk log yazımında dosya açılır

### max_bytes

**Ne yapar:** Rotation tetiklenme eşiğini belirler.

```python
max_bytes=10 * 1024 * 1024    # 10MB
max_bytes=50 * 1024 * 1024    # 50MB
max_bytes=1024 * 1024         # 1MB
```

**Etkiler:**
- Dosya bu boyuta ulaştığında rotation olur
- `0` veya negatif ise rotation **devre dışı** (sınırsız büyüme)

### backup_count

**Ne yapar:** Kaç tane eski dosya saklanacağını belirler.

```python
backup_count=5     # 5 backup dosyası
backup_count=10    # 10 backup dosyası
backup_count=1     # 1 backup dosyası
backup_count=0     # Backup yok (sadece aktif dosya)
```

**Etkiler:**
- Toplam dosya sayısı = `1 + backup_count`
- Limit aşıldığında en eski backup **otomatik silinir**

### compress

**Ne yapar:** Backup dosyalarının sıkıştırılıp sıkıştırılmayacağını belirler.

```python
compress=True   # Backup'lar .gz ile sıkıştırılır
compress=False  # Backup'lar düz metin olarak kalır
```

**Etkiler:**
- `True`: Disk alanı tasarrufu (yaklaşık %70-90)
- `False`: Daha hızlı erişim, daha fazla disk kullanımı

**Dosya isimleri:**
- `compress=True` → `app.log.1.gz`, `app.log.2.gz`, ...
- `compress=False` → `app.log.1`, `app.log.2`, ...

---

## Örnek Senaryolar

### Senaryo 1: Küçük Uygulama

```python
handler = AsyncRotatingFileHandler(
    filename="app.log",
    max_bytes=5 * 1024 * 1024,   # 5MB
    backup_count=3,               # 3 backup
    compress=True
)
```

**Dosya yapısı:**
```
app.log          # Aktif
app.log.1.gz    # En yeni
app.log.2.gz    # İkinci
app.log.3.gz    # En eski
```

**Toplam: 4 dosya** (1 aktif + 3 backup)

### Senaryo 2: Yüksek Hacimli Uygulama

```python
handler = AsyncRotatingFileHandler(
    filename="/var/log/api/app.log",
    max_bytes=100 * 1024 * 1024,  # 100MB
    backup_count=20,                # 20 backup
    compress=True
)
```

**Dosya yapısı:**
```
/var/log/api/app.log          # Aktif
/var/log/api/app.log.1.gz     # En yeni
/var/log/api/app.log.2.gz     # ...
...
/var/log/api/app.log.20.gz    # En eski
```

**Toplam: 21 dosya** (1 aktif + 20 backup)  
**Maksimum disk kullanımı:** ~2GB (100MB × 20 backup, sıkıştırılmış)

### Senaryo 3: Backup Olmadan

```python
handler = AsyncRotatingFileHandler(
    filename="app.log",
    max_bytes=10 * 1024 * 1024,
    backup_count=0,    # Backup yok
    compress=False
)
```

**Dosya yapısı:**
```
app.log    # Aktif (rotation sonrası eski dosya silinir)
```

**Toplam: 1 dosya** (sadece aktif)

---

## Dosya Yönetimi Kuralları

### 1. Dizin Oluşturma

```python
filename="/var/log/myapp/app.log"
```

**Sonuç:**
- `/var/log/myapp/` dizini yoksa **otomatik oluşturulur**
- İzin hatası varsa exception fırlatılır

### 2. Dosya Oluşturma

```python
handler = AsyncRotatingFileHandler(filename="app.log")
```

**Sonuç:**
- Handler oluşturulduğunda dosya **hemen açılır** (append mode)
- İlk log yazımında dosya zaten hazırdır

### 3. Rotation Sırası

Rotation sırasında dosyalar şu sırayla işlenir:

1. **Eski backup'ları kaydır** (geriye doğru):
   - `app.log.4` → `app.log.5`
   - `app.log.3` → `app.log.4`
   - `app.log.2` → `app.log.3`
   - `app.log.1` → `app.log.2`

2. **Aktif dosyayı backup yap**:
   - `app.log` → `app.log.1` (veya `app.log.1.gz`)

3. **En eski backup'ı sil**:
   - `app.log.5` silinir (limit aşıldı)

4. **Yeni dosya aç**:
   - Yeni `app.log` oluşturulur (boş)

### 4. Thread Safety

- Rotation **thread-safe**'dir
- Birden fazla thread aynı anda log yazabilir
- Lock mekanizması ile race condition önlenir

---

## Sık Sorulan Sorular

### Kaç dosya oluşur?

**Cevap:** `1 + backup_count` dosya

- 1 aktif dosya (`app.log`)
- `backup_count` kadar backup dosyası (`app.log.1`, `app.log.2`, ...)

### Dosya isimleri neye bağlı?

**Cevap:** `filename` parametresine bağlı

- `filename="app.log"` → `app.log`, `app.log.1`, `app.log.2`, ...
- `filename="/var/log/api.log"` → `/var/log/api.log`, `/var/log/api.log.1`, ...

### Rotation ne zaman olur?

**Cevap:** `max_bytes` aşıldığında

- Her log yazımında dosya boyutu kontrol edilir
- `max_bytes` aşıldığında rotation tetiklenir

### Sıkıştırma ne zaman uygulanır?

**Cevap:** Rotation sırasında

- Aktif dosya (`app.log`) sıkıştırılmaz
- Backup dosyaları (`app.log.1`, `app.log.2`, ...) rotation sırasında sıkıştırılır

### En eski dosya ne zaman silinir?

**Cevap:** `backup_count` limiti aşıldığında

- Rotation sonrası `backup_count + 1` dosya olursa
- En eski backup (`app.log.{backup_count}`) otomatik silinir

---

## Özet Tablo

| Parametre | Varsayılan | Ne Yapar | Etkisi |
|-----------|------------|----------|--------|
| `filename` | - | Dosya adı/yolu | Dizin otomatik oluşturulur |
| `max_bytes` | 10MB | Rotation eşiği | Bu boyuta ulaşınca rotation |
| `backup_count` | 5 | Backup sayısı | Toplam dosya = 1 + backup_count |
| `compress` | True | Sıkıştırma | Backup'lar .gz olur |
| `encoding` | utf-8 | Dosya encoding | Karakter kodlaması |

**Formül:**
```
Toplam Dosya = 1 (aktif) + backup_count (backup)
Maksimum Disk = max_bytes × (backup_count + 1) × (compress ? 0.3 : 1.0)
```

---

## Sonraki Adımlar

- [Handlers Documentation](handlers.md) - Handler detayları
- [Quick Start Guide](quickstart.md) - Hızlı başlangıç
- [Formatters Documentation](formatters.md) - Log formatları

