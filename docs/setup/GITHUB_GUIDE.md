# GitHub Integration Guide

ApplyPilot'u GitHub'a push etmek ve iş takibini GitHub üzerinden yapmak için.

## Adım 1: GitHub repository oluştur

1. https://github.com/new adresine git
2. Repository name: `applypilot-jobs` (veya istediğin)
3. Description: kısa bir açıklama
4. Visibility: **Private** öneriliyor — kişisel bilgiler içeriyor. Public sadece
   kod paylaşımı amaçlıysa tercih edilmeli.
5. "Initialize this repository" kutusunu boş bırak
6. Create repository

## Adım 2: Push to GitHub

```bash
cd ~/Desktop/applypilot-jobs

git remote add origin https://github.com/YOUR_USERNAME/applypilot-jobs.git
git branch -M main
git push -u origin main
```

İlk push'tan sonra kontrol et: `.gitignore` hassas dosyaları (`.env`,
`config.yaml`, `*.db`, CV dosyaları) korumalı.

## Adım 3: İş takip sistemi

### Seçenek 1: Markdown (basit, önerilen)

`docs/tracking/JOB_APPLICATIONS.md` dosyasını kullan:

1. Excel'den işlere başvur
2. Notes kolonuna yaz: `Applied 2026-06-23`
3. Tracker'ı güncelle: `python scripts/tracking/track_applications.py`
4. Git commit:
   ```bash
   git add docs/tracking/JOB_APPLICATIONS.md
   git commit -m "Update: Applied to 5 jobs"
   git push
   ```

Avantajları: basit, Git geçmişiyle takip edilir, offline çalışır.

### Seçenek 2: GitHub Issues (ileri seviye)

Her iş için bir GitHub Issue oluşturur.

**Kurulum:**

```bash
pip install PyGithub

# GitHub -> Settings -> Developer settings -> Personal access tokens (classic)
# Scope: repo (full)
export GITHUB_TOKEN=your_github_pat

# scripts/tracking/sync_to_github.py içindeki REPO_NAME değerini güncelle
```

**Kullanım:**

```bash
python scripts/tracking/sync_to_github.py
```

Her perfect-match iş için bir Issue açar, `score-8+`, `remote`, `ml-ai` gibi
label'lar ekler, tüm detayları issue body'sine yazar.

### Seçenek 3: GitHub Projects (Kanban board)

1. Repo'da Projects sekmesine git, New project, template: Board
2. Name: `Job Applications`

**Önerilen kolonlar:**

| Kolon | Açıklama |
|-------|----------|
| To Apply | Başvurulacaklar |
| Applied | Başvuruldu |
| Response | Cevap geldi |
| Interview | Görüşme |
| Offer | Teklif aldım |
| Rejected | Reddedildi |

Issue'ları projeye ekle (Issue -> Projects -> Add to project), durum
değiştikçe sürükle-bırak ile kolon değiştir.

## İş akışı önerisi

**Günlük:**
```bash
# Excel'de Notes kolonunu güncelle
python scripts/tracking/track_applications.py
git add docs/tracking/JOB_APPLICATIONS.md
git commit -m "Daily update: 3 applied, 1 response"
git push
```

**Her 3 günde bir (yeni tarama sonrası):**
```bash
python scripts/scan/run_full_scan.py
python scripts/tracking/sync_to_github.py   # opsiyonel
# CHANGELOG.md'yi manuel güncelle
git add .
git commit -m "Scan: 45 new jobs found"
git push
```

## Label sistemi

**Score:** `score-8+`, `score-7`

**Type:** `ml-ai`, `backend`, `full-stack`, `data`

**Location:** `remote`, `hybrid`, `onsite`

**Status:** `to-apply`, `applied`, `response`, `interview`, `offer`, `rejected`

**Priority:** `high-priority`, `low-priority`

## Analytics

GitHub'ın kendi analytics araçları:

- Insights -> Pulse: haftalık aktivite
- Insights -> Contributors: kim ne yaptı
- Projects -> Insights: issue akışı, cycle time
- Issues -> Milestones: haftalık hedefler

## Güvenlik

**Asla commit etme:** `.env`, `config.yaml`, `resume.txt`/`.pdf`, `*.db`,
`logs/*.log`.

**Kontrol et:** `git status` çıktısında "Untracked files" altında bu
dosyaların görünmediğinden emin ol — `.gitignore` zaten bunları kapsıyor.

## İpuçları

**Branch stratejisi:**

```bash
git checkout -b feature/improve-filters
# değişiklikleri yap
git add .
git commit -m "Add new filter for contract jobs"
git push -u origin feature/improve-filters
# GitHub'da Pull Request aç, kendin review edip merge et
```

**GitHub Actions ile otomatik tarama:** `.github/workflows/auto-scan.yml`:

```yaml
name: Auto Scan

on:
  schedule:
    - cron: '0 9 * * 1,4,0'  # Pazartesi, Perşembe, Pazar 09:00

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run ApplyPilot
        run: python scripts/scan/run_full_scan.py
      - name: Commit results
        run: |
          git config user.name "ApplyPilot Bot"
          git add reports/ logs/
          git commit -m "Auto-scan $(date +%Y-%m-%d)"
          git push
```

**Commit message konvansiyonu:** `Scan update`, `Application update`,
`New feature`, `Bug fix`, `Documentation`, `Configuration`.

## Kontrol listesi

- [ ] GitHub repo oluşturuldu
- [ ] İlk push yapıldı
- [ ] README görünüyor
- [ ] `.gitignore` çalışıyor (`.env` commit edilmedi)
- [ ] `docs/tracking/JOB_APPLICATIONS.md` takibi yapılıyor
- [ ] GitHub Issues/Projects kurulumu (opsiyonel)
- [ ] Label'lar oluşturuldu (opsiyonel)
