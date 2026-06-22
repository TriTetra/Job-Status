"""
ApplyPilot Setup Package Creator
---------------------------------
Bu script tüm ayarlarını ve konfigürasyonlarını bir pakete toplayıp
başka birine verebilmen için hazırlar.

Kullanım:
    python setup_package.py
"""

import shutil
import zipfile
from pathlib import Path
from datetime import datetime


def create_package():
    """Tüm ayarları bir pakete topla"""

    print("📦 ApplyPilot Kurulum Paketi Oluşturuluyor...")
    print("=" * 80)

    # Paket klasörü oluştur
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    package_dir = Path(f"applypilot_package_{timestamp}")
    package_dir.mkdir(exist_ok=True)

    # 1. Proje dosyaları
    print("\n1️⃣ Proje dosyaları kopyalanıyor...")
    files_to_copy = [
        "README.md",
        "filter_jobs.py",
        "export_to_excel.py",
        "extract_requirements.py",
        "requirements.txt",  # Bunu oluşturacağız
    ]

    for file in files_to_copy:
        if Path(file).exists():
            shutil.copy(file, package_dir / file)
            print(f"   ✅ {file}")

    # 2. Config klasörü oluştur
    print("\n2️⃣ Config dosyaları kopyalanıyor...")
    config_dir = package_dir / "config_templates"
    config_dir.mkdir(exist_ok=True)

    home_applypilot = Path.home() / ".applypilot"

    config_files = {
        "searches.yaml": "Arama sorguları (27 sorgu)",
        "config.yaml": "Profil ayarları",
        ".env": "LLM ayarları (GPT-4o-mini)",
        "resume.txt": "CV (text format)",
    }

    for file, desc in config_files.items():
        src = home_applypilot / file
        if src.exists():
            dst = config_dir / file
            shutil.copy(src, dst)
            print(f"   ✅ {file} - {desc}")

    # 3. Kurulum talimatları
    print("\n3️⃣ Kurulum talimatları yazılıyor...")

    setup_instructions = """
# 🚀 ApplyPilot Kurulum Talimatları

## 1️⃣ ApplyPilot'u Kur

```bash
# Virtual environment oluştur
python -m venv venv

# Aktif et (Windows PowerShell)
.\\venv\\Scripts\\Activate.ps1

# ApplyPilot ve bağımlılıkları kur
pip install applypilot openpyxl
```

## 2️⃣ Config Dosyalarını Kopyala

```bash
# .applypilot klasörünü oluştur (yoksa)
mkdir -p ~/.applypilot

# Config dosyalarını kopyala
cp config_templates/searches.yaml ~/.applypilot/
cp config_templates/config.yaml ~/.applypilot/
cp config_templates/.env ~/.applypilot/
cp config_templates/resume.txt ~/.applypilot/
```

## 3️⃣ API Anahtarını Güncelle

**ÖNEMLİ:** `.env` dosyasındaki API anahtarı kişiseldir!

```bash
# ~/.applypilot/.env dosyasını düzenle
# Kendi OpenRouter API anahtarını ekle
```

## 4️⃣ Profili Özelleştir

```bash
# ~/.applypilot/config.yaml dosyasını düzenle
# - name: Kendi adın
# - email: Kendi emailin
# - skills: Kendi becerilerini
# - target_role: Hedef rolün
```

## 5️⃣ Test Et

```bash
# Sistem kontrolü
./venv/Scripts/applypilot.exe doctor

# İlk arama (küçük test)
./venv/Scripts/applypilot.exe run discover --workers 1
```

## 6️⃣ Kullan

```bash
# Tam iş akışı
./venv/Scripts/applypilot.exe run discover score --min-score 8
python filter_jobs.py
python export_to_excel.py
```

---

## ⚠️ ÖNEMLİ NOTLAR:

1. **API Anahtarı:** Kendi OpenRouter hesabı aç (https://openrouter.ai)
2. **Profil:** `config.yaml`'daki tüm bilgileri kendinize göre değiştir
3. **CV:** `resume.txt` dosyasını kendi CV'inle değiştir
4. **Arama Sorguları:** İsterseniz `searches.yaml`'daki sorguları değiştir

---

## 🎯 SİSTEM ÖZELLİKLERİ:

✅ 27 otomatik arama sorgusu (İngilizce + Türkçe)
✅ GPT-4o-mini ile akıllı puanlama
✅ 8 farklı otomatik filtre
✅ Excel rapor oluşturma
✅ Gereksinim analizi
✅ Tam dokümantasyon

---

Kolay gelsin! 🚀
"""

    (package_dir / "SETUP_INSTRUCTIONS.md").write_text(setup_instructions, encoding='utf-8')
    print("   ✅ SETUP_INSTRUCTIONS.md")

    # 4. requirements.txt oluştur
    print("\n4️⃣ requirements.txt oluşturuluyor...")
    requirements = """applypilot>=0.3.0
openpyxl>=3.1.0
"""
    (package_dir / "requirements.txt").write_text(requirements, encoding='utf-8')
    print("   ✅ requirements.txt")

    # 5. Zip oluştur
    print("\n5️⃣ ZIP paketi oluşturuluyor...")
    zip_name = f"applypilot_package_{timestamp}.zip"

    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in package_dir.rglob('*'):
            if file.is_file():
                zipf.write(file, file.relative_to(package_dir.parent))

    print(f"   ✅ {zip_name}")

    # Özet
    print("\n" + "=" * 80)
    print("✅ PAKET OLUŞTURULDU!")
    print("=" * 80)
    print(f"\n📦 Paket: {zip_name}")
    print(f"📁 Klasör: {package_dir}")
    print()
    print("📤 NASIL PAYLAŞILİR:")
    print(f"   1. {zip_name} dosyasını gönder")
    print("   2. SETUP_INSTRUCTIONS.md'yi okusunlar")
    print("   3. Kendi API anahtarlarını eklesinler")
    print("   4. Profili kendilerine göre düzenlesinler")
    print()
    print("⚠️  ÖNEMLİ: API anahtarını paylaşma!")
    print("=" * 80)


if __name__ == "__main__":
    create_package()
