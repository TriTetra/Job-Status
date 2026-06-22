# 🤖 ApplyPilot - Automated Job Discovery System

**Profesyonel iş arama ve analiz sistemi!**

> **Son Tarama:** 2026-06-22  
> **Bulunan İşler:** 562  
> **Perfect Match:** 30 iş  
> **Durum:** ✅ Production Ready

---

## 📊 Sistem Özellikleri

### ✅ Ne Yapıyor:
- 🔍 **Otomatik İş Bulma:** LinkedIn, Indeed, Glassdoor'da arama
- ⭐ **Akıllı Puanlama:** GPT-4o-mini ile 1-10 arası skor
- 🎯 **Gelişmiş Filtreleme:** 8 otomatik filtre
- 📊 **Süper Detaylı Excel:** 6 sayfa, 18+ kolon
- 📈 **Skill Analizi:** Hangi beceriler popüler
- 💾 **Otomatik Yedekleme:** Her taramada DB backup
- 📝 **Tarama Geçmişi:** JSON log sistemi

### 💰 Maliyet:
- ~**$0.73** / 500+ iş
- ~**25-30 dakika** süre

### 🌍 Kapsam:
- **Global:** ABD, Kanada, Avrupa, UK
- **Lokal:** Türkiye, Özbekistan
- **Remote:** Öncelikli

---

## 🗂️ Dizin Yapısı

```
applypilot-jobs/
├── 📁 scripts/                 # Tüm scriptler
│   ├── run_full_scan.py        # Ana tarama scripti
│   ├── filter_jobs.py          # Otomatik filtreleme
│   ├── export_to_excel_advanced.py  # Detaylı Excel
│   ├── schedule_info.py        # Tarama zamanı bilgisi
│   └── setup_package.py        # Paylaşım paketi
│
├── 📁 reports/                 # Tarama raporları
│   ├── 2026-06-22/
│   │   ├── applypilot_advanced_*.xlsx
│   │   └── summary.txt
│   └── latest.txt              # En son rapor
│
├── 📁 logs/                    # Çalıştırma logları
│   ├── 2026-06-22.log
│   └── run_history.json        # Tüm tarama geçmişi
│
├── 📁 backups/                 # DB yedekleri
│   └── db_2026-06-22_*.sqlite
│
├── 📁 config/                  # Ayarlar (opsiyonel)
│
├── 📄 run_scan.bat             # Windows: Çift tıkla çalıştır
├── 📄 README.md                # Bu dosya
├── 📄 CHANGELOG.md             # Tarama geçmişi
└── 📄 venv/                    # Python sanal ortamı
```

---

## 🚀 Hızlı Başlangıç

### İlk Kurulum (Sadece 1 kez):

```bash
# 1. Virtual environment aktif et
.\venv\Scripts\Activate.ps1

# 2. Bağımlılıkları kontrol et
pip install openpyxl

# 3. Config dosyalarını kontrol et
ls ~/.applypilot/
# Görmeli: searches.yaml, config.yaml, .env
```

### Her Tarama İçin:

#### **Yöntem 1: Tek Tıkla (En Kolay!)** 🖱️

1. `run_scan.bat` dosyasına çift tıkla
2. 25-30 dakika bekle
3. `reports/latest.txt` dosyasını aç
4. Excel raporunu incele!

#### **Yöntem 2: Manuel (Daha Fazla Kontrol)** 💻

```bash
# Virtual environment aktif et
.\venv\Scripts\Activate.ps1

# Tam tarama çalıştır
python scripts/run_full_scan.py
```

---

## 📅 Önerilen Tarama Programı

### **3 Günde Bir Tarama:**

| Gün | Zaman | Neden |
|-----|-------|-------|
| **Pazartesi** | 09:00 | Yeni hafta işleri |
| **Perşembe** | 09:00 | Hafta ortası güncellemeleri |
| **Pazar** | 18:00 | Hafta sonu hazırlık |

### **Ne Zaman Tarama Yapmalı?**

```bash
# Kontrol et
python scripts/schedule_info.py
```

Çıktı:
- ⏳ Henüz erken → Bekle
- ✅ Tam zamanı → Tarama yap
- ⚠️ Gecikmiş → Hemen yap!

---

## 📊 Excel Raporu Detayları

### **6 Sayfa:**

| # | Sayfa | Açıklama |
|---|-------|----------|
| 📊 | **Executive Summary** | Genel bakış, istatistikler, grafikler |
| 🎯 | **Perfect Match (8+)** | 30 perfect iş - EN DETAYLI! |
| ✅ | **Good Match (7)** | 121 iyi iş |
| 📈 | **Skills Analysis** | Hangi beceriler ne kadar popüler |
| 🏢 | **By Company** | Site bazlı gruplandırma |
| 📁 | **Full Database** | Tüm işler (yedek) |

### **Her İş İçin 18 Kolon:**

1. **Posted Date** - İlan tarihi
2. **Job Title** - İş unvanı
3. **Company** - Şirket
4. **Site** - LinkedIn/Indeed/Glassdoor
5. **Location** - Lokasyon
6. **Remote?** - Remote/Hybrid/Onsite
7. **Salary Range** - Maaş aralığı
8. **Fit Score** - 1-10 (renkli!)
9. **Why This Score?** - AI açıklaması
10. **Top Requirements** - İstenen beceriler
11. **✅ Your Skills** - Eşleşen becerileriniz
12. **❌ Missing Skills** - Eksik beceriler
13. **Match %** - Eşleşme yüzdesi
14. **Years Exp** - İstenen deneyim
15. **Sponsorship?** - Sponsorship tahmini
16. **Description** - İş açıklaması özeti
17. **Apply Link** - Tıklanabilir başvuru linki
18. **Notes** - Kendi notların (boş)

### **Renklendirme:**
- 🟢 **Skor 8-10:** Yeşil (BAŞVUR!)
- 🟡 **Skor 7:** Sarı (İNCELE!)
- 🔵 **Remote işler:** Mavi arka plan
- 💰 **Maaş >$100k:** Kalın
- ✅ **Match >70%:** Yeşil border

---

## 🎯 Başvuru İş Akışı

### **1. Excel'i Aç**
```
reports/2026-06-22/applypilot_advanced_*.xlsx
```

### **2. "Perfect Match (8+)" Sayfasına Git**
- 30 perfect iş listesi
- Her detay hazır!

### **3. Her İş İçin:**

1. ✅ **Top Requirements** kolonunu oku
2. ✅ **Match %** kontrol et (>70% = mükemmel!)
3. ✅ **Your Skills** kolonundan hangi becerilerin eşleştiğini gör
4. ✅ **Apply Link**'e tıkla
5. ✅ LinkedIn/Indeed'de başvur
6. ✅ **Notes** kolonuna başvuru tarihini yaz

### **4. Cover Letter Şablonu:**

```
Subject: Application for [Job Title] - ML Engineer with Computer Vision Experience

Dear Hiring Team,

I'm excited to apply for the [Job Title] position at [Company]. Your focus on 
[specific requirement from job] aligns perfectly with my experience.

In my recent role at KOU STORM UAV, I:
• Built YOLOv8 object detection systems achieving 92% mAP
• Optimized real-time inference to 40ms latency on edge devices
• Deployed ML models in production handling 20+ FPS

Key skills matching your requirements:
[Copy from "Your Skills" column in Excel]

I'm particularly drawn to [company-specific detail] and would love to discuss 
how my background in [your strength] could contribute to [company goal].

Available immediately and happy to discuss visa sponsorship.

Best regards,
Abdullokh Abdukodirov
[Your Contact Info]
```

---

## ⚙️ Yapılandırma

### **Arama Sorgularını Değiştir:**

```bash
# Dosyayı aç
notepad ~/.applypilot/searches.yaml

# Yeni sorgu ekle
queries:
  - query: "Your New Search Term"
    tier: 1  # 1=yüksek öncelik, 3=düşük
```

### **Profil Ayarlarını Güncelle:**

```bash
notepad ~/.applypilot/config.yaml

# Değiştir:
# - target_role
# - core_skills
# - avoid list
```

### **LLM Modelini Değiştir:**

```bash
notepad ~/.applypilot/.env

# Değiştir:
LLM_MODEL=openai/gpt-4o-mini           # Mevcut (ucuz, hızlı)
# LLM_MODEL=anthropic/claude-3-5-haiku-20241022  # Daha iyi kalite
# LLM_MODEL=anthropic/claude-sonnet-4-6          # En iyi (pahalı)
```

---

## 📈 Gelişmiş Kullanım

### **Sadece Belirli Adımları Çalıştır:**

```bash
# Sadece yeni iş bulma
./venv/Scripts/applypilot.exe run discover --hours-old 72

# Sadece puanlama
./venv/Scripts/applypilot.exe run score --min-score 7

# Sadece filtreleme
python scripts/filter_jobs.py

# Sadece Excel oluştur
python scripts/export_to_excel_advanced.py
```

### **Tarama Geçmişini Görüntüle:**

```bash
# JSON formatında
cat logs/run_history.json

# Son 5 tarama
python -c "import json; data=json.load(open('logs/run_history.json')); [print(f\"{r['timestamp']}: {r['stats']['total']} jobs\") for r in data[-5:]]"
```

### **Veritabanını İncele:**

```bash
sqlite3 ~/.applypilot/applypilot.db

# Örnek sorgular:
SELECT COUNT(*) FROM jobs WHERE fit_score >= 8;
SELECT title, fit_score FROM jobs WHERE fit_score >= 8 ORDER BY fit_score DESC;
```

---

## 🔧 Sorun Giderme

### ❌ "Veritabanı bulunamadı"
```bash
# Önce bir tarama yap
./venv/Scripts/applypilot.exe run discover score
```

### ❌ "Module not found: openpyxl"
```bash
pip install openpyxl
```

### ❌ "LLM rate limit"
```bash
# .env dosyasını kontrol et
cat ~/.applypilot/.env
# Model: openai/gpt-4o-mini olmalı
```

### ❌ "Unicode hatası"
```bash
# PowerShell'de:
$env:PYTHONIOENCODING='utf-8'
python scripts/export_to_excel_advanced.py
```

---

## 📊 Sistem İstatistikleri

### **İlk Tarama (2026-06-22):**
- ✅ 562 iş tarandı
- ✅ 30 perfect match (8+ skor)
- ✅ 121 good match (7 skor)
- ⏱️ 30 dakika
- 💰 $0.73

### **Filtreleme Etkinliği:**
- 🔴 ~102 iş elendi (Senior, Freelance, vb.)
- 🟢 181 kaliteli iş kaldı
- 📈 %32 başarı oranı

### **En Çok Aranan Beceriler:**
1. Python
2. Machine Learning
3. PyTorch
4. AWS/Cloud
5. Backend Development

---

## 🤝 Paylaşım

Sistemi başkasıyla paylaşmak için:

```bash
python scripts/setup_package.py
```

Bu şunları oluşturur:
- 📦 ZIP paketi (tüm scriptler + config şablonları)
- 📄 Kurulum talimatları
- ⚠️ API anahtarları DAHİL DEĞİL (güvenlik)

---

## 📝 Notlar

### 💡 İpuçları:
1. **Her 3 günde bir tara** - İşler genelde 72 saatte güncellenir
2. **8+ puanlılara öncelik ver** - En uygun olanlar
3. **7 puanlıları da değerlendir** - Özellikle ML/AI ve Backend
4. **Notes kolonunu kullan** - Başvuru takibi için
5. **CHANGELOG.md'yi güncelle** - Her taramadan sonra

### ⚠️ Dikkat:
- **Aynı işe tekrar başvurma** - ApplyPilot URL'ye göre deduplicate ediyor
- **3 günden kısa aralıklarla tarama yapma** - Yeni iş gelmez, maliyet artar
- **Config değişikliklerini test et** - Küçük tarama ile dene

---

## 🎉 Başarı Hikayeleri

### İlk Tarama:
- ❌ 3+ saat sürdü (Gemini rate limit)
- ❌ 6 uygun iş

### Optimize Sonrası:
- ✅ 25 dakika
- ✅ 181 uygun iş
- ✅ **30x daha fazla kaliteli iş!**
- ✅ **9x daha hızlı!**

---

## 📧 İletişim

Sorular için: abdullahabdulkadir0@gmail.com

---

**Kolay gelsin! 🚀**

---

> 💡 **Pro Tip:** Windows Task Scheduler'a ekle, otomatik çalışsın!
