# ⚡ ApplyPilot - Quick Start Guide

**5 dakikada başla!** 🚀

---

## 🎯 İlk Tarama (Şimdi!)

### **Yöntem 1: Tek Tıkla** (Tavsiye Edilen)

1. **`run_scan.bat`** dosyasına çift tıkla
2. ☕ Kahve al (25-30 dakika bekle)
3. ✅ Bitti! `reports/latest.txt` dosyasını aç

### **Yöntem 2: Manuel**

```bash
# 1. Terminal aç (Git Bash veya PowerShell)
cd ~/Desktop/applypilot-jobs

# 2. Virtual environment aktif et
source venv/Scripts/activate  # Git Bash
# VEYA
.\venv\Scripts\Activate.ps1   # PowerShell

# 3. Tarama başlat
python scripts/run_full_scan.py
```

---

## 📊 Sonuçları İncele

### **1. Excel'i Aç:**

```
reports/2026-06-22/applypilot_advanced_*.xlsx
```

### **2. "Perfect Match (8+)" Sayfasına Git**

- 30 perfect iş göreceksin
- Her detay hazır!

### **3. Başvurmaya Başla!**

- "Apply Link" kolonuna tıkla
- LinkedIn/Indeed'de başvur
- "Notes" kolonuna başvuru tarihini yaz

---

## 🔄 Sonraki Taramalar

### **Ne Zaman?**

```bash
# Kontrol et
python scripts/schedule_info.py
```

**Tavsiye:** Her **3 günde** bir (Pazartesi, Perşembe, Pazar)

### **Nasıl?**

- **Manuel:** `run_scan.bat` çift tıkla
- **Otomatik:** `WINDOWS_SCHEDULER_GUIDE.md` dosyasını oku

---

## 📁 Önemli Dosyalar

| Dosya | Ne İçin? |
|-------|----------|
| `run_scan.bat` | 🖱️ Tek tıkla tarama |
| `reports/latest.txt` | 📊 En son rapor nerede |
| `logs/*.log` | 📝 Çalışma logları |
| `README.md` | 📖 Tam dokümantasyon |
| `CHANGELOG.md` | 📋 Tarama geçmişi |

---

## 🆘 Hızlı Yardım

### ❌ "Çalışmıyor!"

1. Virtual environment aktif mi?
   ```bash
   source venv/Scripts/activate
   ```

2. openpyxl kurulu mu?
   ```bash
   pip install openpyxl
   ```

3. Config dosyaları yerinde mi?
   ```bash
   ls ~/.applypilot/
   # Görmeli: searches.yaml, config.yaml, .env
   ```

### 📧 Daha Fazla Yardım

README.md'yi oku veya:
- Email: abdullahabdulkadir0@gmail.com

---

## 🎉 İlk Tarama Sonrası

1. ✅ Excel'i aç ve incele
2. ✅ Perfect Match (8+) işlere başvur
3. ✅ Good Match (7) işleri değerlendir
4. ✅ CHANGELOG.md'ye not ekle
5. ✅ 3 gün sonra için tarama zamanla

---

**Başarılar! 🚀**

> 💡 **Tip:** Otomatik tarama için `WINDOWS_SCHEDULER_GUIDE.md`'yi oku!
