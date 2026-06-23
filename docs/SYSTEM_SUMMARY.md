# ApplyPilot System - Complete Summary

Profesyonel iş bulma ve takip sistemi - mimari özeti.

> [../README.md](../README.md) iki sistemin (ApplyPilot + Career OS) nasıl
> bağlandığını ve hızlı başlangıcı anlatır. Bu dosya ise ApplyPilot'un
> operasyonel detaylarına (filtreler, Excel kolonları, iş akışı, özelleştirme)
> iner — günlük kullanımda referans olarak buraya dön.

## Sistem genel bakış

### Ne yapıyor?

ApplyPilot, otomatik iş bulma, puanlama, filtreleme ve takip sistemidir.

```
Discover (LinkedIn, Indeed, Glassdoor) -> Score (LLM, 1-10) -> Filter (8 kural) -> Excel (6 sayfa, 18 kolon)
                                                                                          |
                                                                                          v
                                                                  JOB APPLICATION TRACKER
                                                                  - Markdown: docs/tracking/JOB_APPLICATIONS.md (basit)
                                                                  - GitHub Issues: Kanban board (ileri seviye)
                                                                  - Excel Notes: tabloda durum takibi
```

## Dizin yapısı

```
applypilot-jobs/
├── scripts/
│   ├── scan/
│   │   ├── run_full_scan.py            Ana tarama (discover -> score -> filter -> excel)
│   │   ├── filter_jobs.py              8 otomatik filtre
│   │   ├── export_to_excel_advanced.py 6 sayfa, 18 kolon Excel
│   │   └── schedule_info.py            Sonraki tarama zamanı
│   ├── strategy/
│   │   ├── apply_strategy.py
│   │   ├── cold_email_generator.py
│   │   ├── skills_gap_analyzer.py
│   │   └── extract_requirements.py     İş gereksinimleri analizi
│   ├── tracking/
│   │   ├── track_applications.py       Başvuru takibi (Excel -> Markdown)
│   │   └── sync_to_github.py           GitHub Issues senkronizasyonu
│   └── packaging/
│       └── setup_package.py            Paylaşım paketi oluşturma
│
├── career_os/            Strateji motoru
├── tests/                career_os için manuel doğrulama scriptleri
├── personal/             CV dosyaları (gitignored)
│
├── docs/
│   ├── README.md                    Dokümantasyon indeksi
│   ├── SYSTEM_SUMMARY.md            Bu dosya
│   ├── setup/
│   │   ├── QUICK_START.md
│   │   ├── GITHUB_GUIDE.md
│   │   └── WINDOWS_SCHEDULER_GUIDE.md
│   ├── usage/
│   │   ├── USAGE.md
│   │   └── APPLY_NOW.md
│   ├── tracking/
│   │   ├── JOB_APPLICATIONS.md
│   │   └── APPLICATION_TRACKER.md
│   └── strategy/
│       └── 2_MONTH_ACTION_PLAN.md
│
├── reports/
│   ├── YYYY-MM-DD/
│   │   ├── applypilot_advanced_*.xlsx
│   │   └── summary.txt
│   └── latest.txt
│
├── logs/                YYYY-MM-DD.log, run_history.json
├── backups/              DB yedekleri (son 10)
│
├── run_scan.bat
├── CHANGELOG.md
├── README.md
└── .gitignore            .env, CV ve DB dosyalarını korur
```

## Hızlı başlangıç (3 adım)

### 1. İlk tarama

```bash
run_scan.bat
# veya
python scripts/scan/run_full_scan.py
```

### 2. Excel'i aç ve incele

```
reports/<tarih>/applypilot_advanced_*.xlsx
-> "Perfect Match (8+)" sayfası
```

### 3. Başvur

- Apply Link'e tıkla -> LinkedIn/Indeed
- Notes kolonuna: `Applied <tarih>`
- Takip et: `python scripts/tracking/track_applications.py`

## Sistem özellikleri

### Otomatik iş bulma

| Özellik | Detay |
|---------|-------|
| Siteler | LinkedIn, Indeed, Glassdoor |
| Sorgular | `~/.applypilot/searches.yaml` içinde tanımlı (`applypilot init` ile oluşur; bu repoda kopyası yok) |
| Kapsam | Global + Türkiye |
| Sıklık | Önerilen: her 3 günde bir |

### AI skorlama

| Özellik | Detay |
|---------|-------|
| Model | GPT-4o-mini (varsayılan, `.env`'den değiştirilebilir) |
| Skorlama | 1-10 ölçeği |
| Kriterler | Skill eşleşmesi, deneyim seviyesi, iş tipi |
| Çıktı | Skor + gerekçe |

### Otomatik filtreleme (8 filtre)

`scripts/scan/filter_jobs.py` içindeki sırayla:

| # | Filtre | Kapsam |
|---|--------|--------|
| 1 | Seniority | Senior/Lead/Principal/Staff/Director |
| 2 | Rol tipi | Standalone Frontend |
| 3 | İstihdam tipi | Freelance/Contract |
| 4 | Seviye | Intern/Internship |
| 5 | Tech stack | Standalone JavaScript Developer |
| 6 | Uzmanlık | Analytics Engineer |
| 7 | Lokasyon | Paris onsite |
| 8 | Deneyim | 4+ yıl gerektiren ilanlar |

### Excel export (6 sayfa, 18 kolon)

Sayfalar: Executive Summary, Perfect Match (8+), Good Match (7), Skills
Analysis, By Company, Full Database.

Kolonlar (18): Posted Date, Job Title, Company, Site, Location, Remote?,
Salary Range, Fit Score, Why This Score?, Top 10 Requirements, Your Matching
Skills, Missing Skills, Match %, Years Experience, Sponsorship?, Description,
Apply Link, Notes.

### Başvuru takibi

**Markdown (önerilen):** `tracking/JOB_APPLICATIONS.md`, manuel ya da Excel'den
senkronize, Git ile geçmiş takibi, offline çalışır.

**GitHub Issues (ileri seviye):** her iş bir Issue, label sistemi, GitHub
Projects ile Kanban board. Detay: [setup/GITHUB_GUIDE.md](setup/GITHUB_GUIDE.md).

### Otomasyon

- Son 10 taramanın yedeği
- JSON çalışma geçmişi
- Özet raporlar
- Windows Task Scheduler entegrasyonu ([setup/WINDOWS_SCHEDULER_GUIDE.md](setup/WINDOWS_SCHEDULER_GUIDE.md))

## İlk taramadan ölçülen sonuçlar (2026-06-22)

Bu sayılar tek bir gerçek çalıştırmadan geliyor; her tarama farklı sonuç verir.

```
Girdi: ~/.applypilot/searches.yaml'daki sorgular, 3 site, 72 saatlik pencere

Discovery: 562 iş bulundu, ~5 dakika
Scoring: GPT-4o-mini, $0.40, ~15 dakika
Filtering: 8 otomatik filtre, ~102 iş elendi, <1 saniye
Excel export: 6 sayfa, 18 kolon, ~5 saniye

Toplam: ~25-30 dakika, ~$0.73, 181 kaliteli iş (30 perfect, 151 good)
```

| Metrik | Değer |
|--------|-------|
| Toplam iş | 562 |
| Filtreleme sonrası | 181 (%32) |
| Perfect Match (8+) | 30 (%5.3) |
| Good Match (7) | 151 (%26.9) |

Bu rakamlar tek bir taramaya ait; "her taramada bu kadar bulunur" garantisi
değildir, çünkü `~/.applypilot/searches.yaml`'daki sorgu sayısı ve içeriği
zamanla değişebilir.

## İş akışı

### Her 3 günde bir

```bash
run_scan.bat   # veya Windows Task Scheduler

# Excel'i incele: reports/YYYY-MM-DD/applypilot_advanced_*.xlsx
# Apply Link kolonundan başvur
# Notes kolonunu güncelle, sonra:
python scripts/tracking/track_applications.py

git add docs/tracking/JOB_APPLICATIONS.md
git commit -m "Update: 5 applied"
git push
```

### Günlük

```bash
python scripts/tracking/track_applications.py
python scripts/scan/schedule_info.py
```

## Özelleştirme

**Arama sorgularını değiştir:**

```bash
notepad ~/.applypilot/searches.yaml
```

**Filtreleri değiştir:**

```bash
notepad scripts/scan/filter_jobs.py
```

**AI modelini değiştir:**

```bash
notepad ~/.applypilot/.env

LLM_MODEL=openai/gpt-4o-mini              # varsayılan, hızlı ve ucuz
LLM_MODEL=anthropic/claude-3-5-haiku-20241022
LLM_MODEL=anthropic/claude-sonnet-4-6     # en kaliteli, en pahalı
```

## Dokümantasyon

Tüm dokümanların tam listesi ve açıklaması için [docs/README.md](README.md)'ye
bak. Bu dosyayla en çok ilişkili olanlar:

| Dosya | Amaç |
|------|------|
| `../README.md` | Genel proje dokümantasyonu |
| `setup/QUICK_START.md` | İlk tarama kurulumu |
| `setup/GITHUB_GUIDE.md` | GitHub entegrasyonu |
| `setup/WINDOWS_SCHEDULER_GUIDE.md` | Otomasyon kurulumu |
| `../CHANGELOG.md` | Tarama geçmişi |
| `tracking/JOB_APPLICATIONS.md` | İş takip tablosu |
| `SYSTEM_SUMMARY.md` | Bu dosya |

## Sonraki adımlar

**Hemen:** Excel'i aç, Perfect Match (8+) işlere başvur, takip sistemini güncelle.

**Bu hafta:** 15-20 işe başvur, isteğe bağlı GitHub kurulumu, Windows otomasyonu
ayarla, `CHANGELOG.md`'yi güncelle.

**Sürekli:** Her 3 günde bir tarama çalıştır, başvuruları günlük takip et,
filtreleri ihtiyaca göre ayarla.
