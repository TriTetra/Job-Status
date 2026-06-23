"""
ApplyPilot Setup Package Creator
---------------------------------
Tüm ayarları ve konfigürasyonları bir pakete toplayıp başka birine
verebilmek için hazırlar.

Kullanım:
    python scripts/packaging/setup_package.py
"""

import shutil
import zipfile
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent.parent


def create_package():
    """Tüm ayarları bir pakete topla"""

    print("ApplyPilot Kurulum Paketi Oluşturuluyor...")
    print("=" * 80)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    package_dir = PROJECT_ROOT / f"applypilot_package_{timestamp}"
    package_dir.mkdir(exist_ok=True)

    # 1. Proje dosyaları
    print("\n1. Proje dosyaları kopyalanıyor...")
    files_to_copy = [
        "README.md",
        "requirements.txt",
        "scripts/scan/filter_jobs.py",
        "scripts/scan/export_to_excel_advanced.py",
        "scripts/strategy/extract_requirements.py",
    ]

    for relative_path in files_to_copy:
        src = PROJECT_ROOT / relative_path
        if src.exists():
            dst = package_dir / Path(relative_path).name
            shutil.copy(src, dst)
            print(f"   OK: {relative_path}")
        else:
            print(f"   SKIP (not found): {relative_path}")

    # 2. Config klasörü oluştur
    print("\n2. Config dosyaları kopyalanıyor...")
    config_dir = package_dir / "config_templates"
    config_dir.mkdir(exist_ok=True)

    home_applypilot = Path.home() / ".applypilot"

    config_files = {
        "searches.yaml": "Arama sorguları",
        "config.yaml": "Profil ayarları",
        ".env": "LLM ayarları",
        "resume.txt": "CV (text format)",
    }

    for file, desc in config_files.items():
        src = home_applypilot / file
        if src.exists():
            dst = config_dir / file
            shutil.copy(src, dst)
            print(f"   OK: {file} - {desc}")

    # 3. Kurulum talimatları
    print("\n3. Kurulum talimatları yazılıyor...")

    setup_instructions = """# ApplyPilot Kurulum Talimatları

## 1. ApplyPilot'u kur

```bash
python -m venv venv
.\\venv\\Scripts\\Activate.ps1   # Windows PowerShell
pip install -r requirements.txt
```

## 2. Config dosyalarını kopyala

```bash
mkdir -p ~/.applypilot
cp config_templates/searches.yaml ~/.applypilot/
cp config_templates/config.yaml ~/.applypilot/
cp config_templates/.env ~/.applypilot/
cp config_templates/resume.txt ~/.applypilot/
```

## 3. API anahtarını güncelle

`.env` dosyasındaki API anahtarı kişiseldir — kendi OpenRouter anahtarınla
değiştir (https://openrouter.ai).

## 4. Profili özelleştir

`config.yaml` içindeki name, email, skills ve target_role alanlarını kendine
göre düzenle.

## 5. Test et

```bash
./venv/Scripts/applypilot.exe doctor
./venv/Scripts/applypilot.exe run discover --workers 1
```

## 6. Kullan

```bash
./venv/Scripts/applypilot.exe run discover score --min-score 8
python filter_jobs.py
python export_to_excel_advanced.py
```

---

## Önemli notlar

1. API anahtarını paylaşma — kendi OpenRouter hesabını kullan
2. `config.yaml`'daki tüm bilgileri kendine göre değiştir
3. `resume.txt` dosyasını kendi CV'inle değiştir
4. `searches.yaml`'daki arama sorgularını istediğin gibi düzenle

## Sistem özellikleri

- Otomatik arama sorguları (İngilizce + Türkçe), sayı `searches.yaml`'a göre değişir
- GPT-4o-mini ile AI skorlama
- 8 otomatik filtre (bkz. filter_jobs.py)
- Excel rapor oluşturma
- Gereksinim analizi (extract_requirements.py)
"""

    (package_dir / "SETUP_INSTRUCTIONS.md").write_text(setup_instructions, encoding='utf-8')
    print("   OK: SETUP_INSTRUCTIONS.md")

    # 4. Zip oluştur
    print("\n4. ZIP paketi oluşturuluyor...")
    zip_path = PROJECT_ROOT / f"applypilot_package_{timestamp}.zip"

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in package_dir.rglob('*'):
            if file.is_file():
                zipf.write(file, file.relative_to(package_dir.parent))

    print(f"   OK: {zip_path.name}")

    # Özet
    print("\n" + "=" * 80)
    print("PAKET OLUŞTURULDU")
    print("=" * 80)
    print(f"\nPaket: {zip_path}")
    print(f"Klasör: {package_dir}")
    print("\nNasıl paylaşılır:")
    print(f"   1. {zip_path.name} dosyasını gönder")
    print("   2. SETUP_INSTRUCTIONS.md'yi okusunlar")
    print("   3. Kendi API anahtarlarını eklesinler")
    print("   4. Profili kendilerine göre düzenlesinler")
    print("\nÖNEMLİ: API anahtarını paylaşma.")
    print("=" * 80)


if __name__ == "__main__":
    create_package()
