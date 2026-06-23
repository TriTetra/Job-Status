# ApplyPilot - Hızlı Başlangıç

Sıfırdan kuruluma ve ilk taramayı çalıştırmaya kadar her adım.

## Önkoşullar

`applypilot` paketi sadece `pip install` ile gelmiyor; aşağıdakilerin de
sistemde kurulu olması gerekiyor (`applypilot doctor` bunları kontrol eder):

- Python 3.11+
- Google Chrome veya Chromium (iş ilanı scraping için)
- Node.js (`npx` komutu PATH'te olmalı)
- Claude Code CLI (`claude` komutu PATH'te olmalı) — CV/cover letter hazırlama
  adımları için

Bunlardan biri eksikse `applypilot doctor` adım 4'te hangisinin eksik
olduğunu söyler.

## Kurulum (ilk kez)

### 1. Virtual environment oluştur ve aktif et

```bash
cd ~/Desktop/applypilot-jobs

python -m venv venv

source venv/Scripts/activate   # Git Bash
# veya
.\venv\Scripts\Activate.ps1    # PowerShell
```

### 2. Bağımlılıkları kur

```bash
pip install -r requirements.txt
```

### 3. ApplyPilot'u ilk kez kur (`init` sihirbazı)

```bash
applypilot init
```

Bu komut `~/.applypilot/` altında `profile.json`, `resume.txt`, `searches.yaml`
ve `.env` dosyalarını **senin girdiğin bilgilerle** oluşturur. Bu repo bu
dosyaların hiçbirinin bir kopyasını tutmuyor — hepsi `applypilot init` ile
senin makinende üretiliyor.

### 4. API anahtarını gir

`init` sihirbazı sırasında veya sonrasında `~/.applypilot/.env` dosyasını aç,
LLM API anahtarını gir (OpenRouter: https://openrouter.ai, veya doğrudan
OpenAI/Anthropic). Şablon için bu repodaki [.env.example](../../.env.example)'a
bak.

### 5. Kurulumu doğrula

```bash
applypilot doctor
```

`profile.json`, `resume.txt`, `searches.yaml`, LLM API key ve Chrome/Node.js/
Claude Code CLI bağımlılıklarının hepsinin "OK" göstermesi gerekiyor.

### 6. Career OS profili (opsiyonel, sadece career_os/ kullanacaksan)

`career_os/`'un kullandığı `config.yaml`, `applypilot init`'in oluşturduğu
dosyalardan **farklı** ve **ayrı** bir dosya — ApplyPilot'un kendisi bunu hiç
okumuyor, sadece bu repodaki `career_os/data/applypilot_loader.py` okuyor.

```bash
cp config.yaml.example config.yaml
notepad config.yaml   # kendi bilgilerini gir
```

Bu adımı atlarsan ApplyPilot taraması (aşağıdaki "İlk tarama" bölümü) yine de
çalışır — `config.yaml` sadece `scripts/strategy/apply_strategy.py` gibi
Career OS script'leri için gerekli.

## İlk tarama

### Yöntem 1: Tek tıkla

1. `run_scan.bat` dosyasına çift tıkla
2. 25-30 dakika bekle
3. `reports/latest.txt` dosyasını aç

### Yöntem 2: Manuel

```bash
python scripts/scan/run_full_scan.py
```

## Sonuçları incele

1. Excel'i aç: `reports/<tarih>/applypilot_advanced_*.xlsx`
2. "Perfect Match (8+)" sayfasına git
3. "Apply Link" kolonuna tıkla, LinkedIn/Indeed'de başvur
4. "Notes" kolonuna başvuru tarihini yaz

## Sonraki taramalar

Ne zaman bir tarama daha yapman gerektiğini görmek için:

```bash
python scripts/scan/schedule_info.py
```

Önerilen sıklık: her 3 günde bir. Manuel olarak `run_scan.bat`'a çift tıklayarak,
ya da [WINDOWS_SCHEDULER_GUIDE.md](WINDOWS_SCHEDULER_GUIDE.md)'deki
adımlarla otomatikleştirerek çalıştırabilirsin.

## Önemli dosyalar

| Dosya | Ne için |
|-------|---------|
| `run_scan.bat` | Tek tıkla tarama |
| `reports/latest.txt` | En son raporun yolu |
| `logs/*.log` | Çalışma logları |
| `~/.applypilot/searches.yaml` | Gerçek arama sorguları (bu repoda kopyası yok, `applypilot init` ile oluşur) |
| `config.yaml` | Career OS profili (bu repoda, `config.yaml.example`'dan kopyalanır) |
| `README.md` | Tam dokümantasyon |
| `CHANGELOG.md` | Tarama geçmişi |

## Hızlı yardım

### "Çalışmıyor"

1. Virtual environment aktif mi?
   ```bash
   source venv/Scripts/activate
   ```
2. Bağımlılıklar kurulu mu?
   ```bash
   pip install -r requirements.txt
   ```
3. ApplyPilot kurulumu tamam mı?
   ```bash
   applypilot doctor
   ```
   Eksik olan her şeyi (profile.json, resume.txt, searches.yaml, API key,
   Chrome, Node.js, Claude Code CLI) burada görürsün.

### "career_os ModuleNotFoundError ya da config.yaml not found"

`config.yaml` adım 6'da oluşturulmadıysa Career OS script'leri
(`apply_strategy.py` gibi) çalışmaz; ApplyPilot taraması bundan etkilenmez.

## İlk tarama sonrası

1. Excel'i aç ve incele
2. Perfect Match (8+) işlere başvur
3. Good Match (7) işleri değerlendir
4. `CHANGELOG.md`'ye not ekle
5. 3 gün sonra için bir tarama daha planla

Otomatik tarama kurmak için [WINDOWS_SCHEDULER_GUIDE.md](WINDOWS_SCHEDULER_GUIDE.md)'yi oku.
