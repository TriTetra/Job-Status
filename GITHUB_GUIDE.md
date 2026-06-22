# 🚀 GitHub Integration Guide

ApplyPilot'u GitHub'a push et ve iş takibi için kullan!

---

## 📝 **ADIM 1: GitHub Repository Oluştur**

### **1.1 GitHub'da Yeni Repo:**

1. GitHub'a git: https://github.com/new
2. **Repository name:** `applypilot-jobs` (veya istediğin)
3. **Description:** `🤖 Automated job discovery and tracking system`
4. **Visibility:** 
   - ✅ **Private** (ÖNERİLEN - kişisel bilgiler var)
   - ❌ Public (sadece kod paylaşımı için)
5. **❌ Initialize this repository** (boş bırak!)
6. **Create repository** tıkla

### **1.2 Repository URL'yi Kopyala:**

```
https://github.com/YOUR_USERNAME/applypilot-jobs.git
```

---

## 📤 **ADIM 2: Push to GitHub**

```bash
cd ~/Desktop/applypilot-jobs

# Remote ekle (URL'yi kendininkiyle değiştir!)
git remote add origin https://github.com/YOUR_USERNAME/applypilot-jobs.git

# Push
git branch -M main
git push -u origin main
```

**İlk push sonrası:**

✅ GitHub'da kodun görünecek!  
✅ .gitignore sensitive data'yı koruyor  
✅ README otomatik render oluyor  

---

## 🎯 **ADIM 3: İş Takip Sistemi**

### **Seçenek 1: Markdown (Basit)** ✅ **ÖNERİLEN**

`JOB_APPLICATIONS.md` dosyası kullan:

1. **Excel'den işlere başvur**
2. **Notes kolonuna yaz:** `Applied 2026-06-23`
3. **Tracker güncelle:**
   ```bash
   python scripts/track_applications.py
   ```
4. **Git commit:**
   ```bash
   git add JOB_APPLICATIONS.md
   git commit -m "📝 Update: Applied to 5 jobs"
   git push
   ```

**Avantajları:**
- ✅ Basit
- ✅ Markdown format (GitHub güzel gösterir)
- ✅ Git history ile takip
- ✅ Offline çalışır

---

### **Seçenek 2: GitHub Issues (Gelişmiş)** 🔥

Her iş için GitHub Issue oluştur:

#### **Setup:**

```bash
# PyGithub kur
pip install PyGithub

# GitHub Personal Access Token oluştur
# GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
# Scopes: repo (full)

# Token'ı environment variable yap
export GITHUB_TOKEN=your_github_pat_xxxxx

# Config'i düzenle
nano scripts/sync_to_github.py
# REPO_NAME = "YOUR_USERNAME/applypilot-jobs" kısmını değiştir
```

#### **Kullanım:**

```bash
# İşleri GitHub Issues'a aktar
python scripts/sync_to_github.py
```

**Ne yapar:**
- ✅ Her perfect match iş → 1 GitHub Issue
- ✅ Labels: `score-8+`, `remote`, `ml-ai`, `backend`, vb.
- ✅ Tüm detaylar issue body'de
- ✅ Kanban board ile takip!

**GitHub Issues'da göreceksin:**
```
#1 AI/ML Engineer - Remote [score-8+] [remote] [ml-ai]
#2 Junior AI Engineer - Computer Vision [score-8+] [remote] [ml-ai]
...
```

---

### **Seçenek 3: GitHub Projects (Kanban Board)** 🎯

En güçlü seçenek!

#### **Setup:**

1. GitHub repo'da **Projects** sekmesine git
2. **New project** tıkla
3. Template: **Board**
4. Name: `Job Applications`
5. **Create**

#### **Board Kolonları:**

| Kolon | Açıklama |
|-------|----------|
| 📝 **To Apply** | Başvurulacaklar |
| ✉️ **Applied** | Başvuruldu |
| 📧 **Response** | Cevap geldi |
| 📞 **Interview** | Görüşme |
| ✅ **Offer** | Teklif aldım |
| ❌ **Rejected** | Reddedildi |

#### **Kullanım:**

1. **Issues'ı Project'e ekle:**
   - Issue'ya git → Projects → Add to project
   - Veya otomatik: Project settings → Workflows

2. **Drag & Drop:**
   - Başvuru yaptın → To Apply'dan Applied'a sürükle
   - Cevap geldi → Response'a sürükle

3. **Not ekle:**
   - Issue'ya comment yaz
   - Timeline otomatik takip ediyor

**Görünüm:**
```
┌───────────┬──────────┬──────────┬───────────┬─────────┬──────────┐
│ To Apply  │ Applied  │ Response │ Interview │ Offer   │ Rejected │
├───────────┼──────────┼──────────┼───────────┼─────────┼──────────┤
│ Issue #1  │ Issue #5 │          │           │         │ Issue #8 │
│ Issue #2  │ Issue #6 │          │           │         │          │
│ Issue #3  │ Issue #7 │          │           │         │          │
│ Issue #4  │          │          │           │         │          │
└───────────┴──────────┴──────────┴───────────┴─────────┴──────────┘
```

---

## 📊 **İŞ AKIŞI ÖNERİSİ:**

### **Günlük:**

```bash
# 1. Excel'de Notes güncelle
# "Applied 2026-06-23" veya "Rejected - overqualified"

# 2. Tracker güncelle
python scripts/track_applications.py

# 3. Git push
git add JOB_APPLICATIONS.md
git commit -m "📝 Daily update: 3 applied, 1 response"
git push
```

### **3 Günde Bir (Yeni Tarama):**

```bash
# 1. Yeni tarama
python scripts/run_full_scan.py

# 2. GitHub Issues oluştur (opsiyonel)
python scripts/sync_to_github.py

# 3. CHANGELOG güncelle
# Manuel: yeni işler, istatistikler

# 4. Git commit
git add .
git commit -m "📊 Scan #2: 45 new jobs found"
git push
```

---

## 🎯 **LABELS SİSTEMİ**

GitHub Issues için önerilen labels:

### **Score:**
- `score-8+` - Perfect match
- `score-7` - Good match

### **Type:**
- `ml-ai` - Machine Learning / AI
- `backend` - Backend Engineer
- `full-stack` - Full Stack
- `data` - Data Engineer

### **Location:**
- `remote` - Remote work
- `hybrid` - Hybrid
- `onsite` - Onsite

### **Status:**
- `to-apply` - Başvurulacak
- `applied` - Başvuruldu
- `response` - Cevap geldi
- `interview` - Görüşme
- `offer` - Teklif
- `rejected` - Reddedildi

### **Priority:**
- `high-priority` - Öncelikli
- `low-priority` - Düşük öncelik

---

## 📈 **ANALYTICS**

GitHub'da otomatik analytics:

- **Insights → Pulse:** Haftalık aktivite
- **Insights → Contributors:** Kim ne yaptı (sen!)
- **Projects → Insights:** Issue flow, cycle time
- **Issues → Milestones:** Haftalık hedefler

---

## 🔐 **GÜVENLİK**

### **❌ Asla Commit Etme:**

- `.env` - API keys
- `config.yaml` - Kişisel bilgiler
- `resume.txt/pdf` - CV
- `*.db` - Veritabanı
- `logs/*.log` - Loglar

### **✅ .gitignore Koruması:**

Zaten ayarlandı! Ama kontrol et:

```bash
git status
# "Untracked files" kısmında .env veya config.yaml OLMAMALI!
```

---

## 💡 **PRO TIPS**

### **1. Branch Strategy:**

```bash
# Feature branch oluştur
git checkout -b feature/improve-filters

# Değişiklikleri yap...

# Commit & push
git add .
git commit -m "✨ Add new filter for contract jobs"
git push -u origin feature/improve-filters

# GitHub'da Pull Request aç
# Merge after review (by yourself!)
```

### **2. GitHub Actions (Otomatik Tarama):**

`.github/workflows/auto-scan.yml` oluştur:

```yaml
name: Auto Scan

on:
  schedule:
    - cron: '0 9 * * 1,4,0'  # Mon, Thu, Sun at 9 AM

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run ApplyPilot
        run: |
          python scripts/run_full_scan.py
      - name: Commit results
        run: |
          git config user.name "ApplyPilot Bot"
          git add reports/ logs/
          git commit -m "🤖 Auto-scan $(date +%Y-%m-%d)"
          git push
```

### **3. Commit Message Konvansiyonu:**

```
📊 Scan update
📝 Application update
✨ New feature
🐛 Bug fix
📚 Documentation
🔧 Configuration
```

---

## 📋 **CHECKLIST**

Kurulum tamamlandıktan sonra:

- [ ] GitHub repo oluşturuldu
- [ ] İlk push yapıldı
- [ ] README görünüyor
- [ ] .gitignore çalışıyor (.env commit edilmedi)
- [ ] JOB_APPLICATIONS.md tracking yapılıyor
- [ ] GitHub Issues/Projects setup (opsiyonel)
- [ ] Labels oluşturuldu (opsiyonel)

---

**GitHub integration tamamlandı! Artık version control + iş takibi tek yerde! 🎉**
