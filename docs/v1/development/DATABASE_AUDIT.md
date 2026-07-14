# Database Audit — Ne Nerede Saklanıyor?

Mevcut sistemde hangi verinin nerede yaşadığını, neyin DB'ye kaydedilmediğini ve bunun ne anlama geldiğini gösteren tam bir envanter.

---

## Mevcut Depolama Haritası

### 1. `~/.applypilot/applypilot.db` — ApplyPilot'un SQLite DB'si

Bu repo'nun **kendi kontrolünde olmayan** bir veritabanı. Sadece ApplyPilot CLI yazıyor, biz sadece okuyoruz (tek istisna: `filter_jobs.py` `fit_score` sütununu günceller).

**Ne saklanır:**

| Sütun | Tip | Kim yazar |
|---|---|---|
| `url` | TEXT (PK) | ApplyPilot |
| `title` | TEXT | ApplyPilot |
| `company` | TEXT | ApplyPilot |
| `location` | TEXT | ApplyPilot |
| `description` | TEXT | ApplyPilot |
| `full_description` | TEXT | ApplyPilot |
| `fit_score` | INTEGER (1-10) | ApplyPilot + `filter_jobs.py` (düşürür) |
| `score_reasoning` | TEXT | ApplyPilot (LLM açıklaması) |
| `salary` | TEXT | ApplyPilot |
| `site` | TEXT | ApplyPilot |
| `discovered_at` | TEXT | ApplyPilot |
| `application_url` | TEXT | ApplyPilot |

**Ne saklanmaz** (her çalıştırmada yeniden hesaplanır veya kaybolur):
- Career OS'un `career_score`, `acceptance_probability`, `fit_score`, `career_value`, `market_demand`
- Skill eşleşme sonuçları (matched_skills, missing_skills, match_pct)
- Başvuru durumu (applied, interview, rejected)

---

### 2. `reports/<tarih>/applypilot_advanced_*.xlsx` — Excel Dosyaları

Her scan sonunda sıfırdan oluşturulur. **Kalıcı değil, türetilmiş veri.**

**Ne saklanır (hesaplanmış, Excel içinde):**

| Excel Sütunu | Kaynak |
|---|---|
| Posted date | `applypilot.db → discovered_at` |
| Job Title, Site, Location | `applypilot.db` |
| Remote? | `location` string'inden regex ile çıkarılır |
| Salary Range | `salary` string'inden parse edilir |
| Fit Score | `applypilot.db → fit_score` |
| Why This Score? | `applypilot.db → score_reasoning` |
| Top Requirements | `full_description`'dan regex ile çıkarılır |
| ✅ Your Skills | `full_description` × `YOUR_SKILLS` listesi → her çalıştırmada hesaplanır |
| ❌ Missing Skills | Aynı |
| Match % | Aynı |
| Years Exp | `full_description`'dan regex ile çıkarılır |
| Sponsorship? | `location = "Remote"` → "Likely" heuristic |
| Apply Link | `application_url` |
| Notes | **BOŞ** — kullanıcı elle doldurur |

**Kritik sorun:** Kullanıcı "Notes" sütununa "Applied 2026-07-10" yazdığında bu Excel dosyasında kalır. Bir sonraki scan yeni bir Excel üretir; o note gider. `track_applications.py` en son Excel'i okuyup `JOB_APPLICATIONS.md`'yi günceller ama yine de geçici.

---

### 3. `career_os_output/*.txt` — Strateji Çıktıları

`apply_strategy.py` çalıştığında üretilir. **Hiçbir yere kalıcı olarak kaydedilmez.**

**Ne saklanır (txt dosyalarında):**

| Dosya | İçerik |
|---|---|
| `apply_today_*.txt` | career_score, acceptance_probability, recommendation, job URL |
| `apply_this_week_*.txt` | Aynı, daha uzun liste |
| `prioritized_applications_*.txt` | career_score, expected_value, company_size dağılımı |
| `learning_plan_*.txt` | 8 haftalık roadmap, hangi skill, kaç saat, hangi kaynak |
| `summary_*.txt` | avg_fit, avg_acceptance, avg_career_score, top gaps |

**Kritik sorun:** Career OS bir işe 78.3 career_score verdi. Bu sayı bir `.txt` dosyasında yaşıyor. Bir sonraki `apply_strategy.py` çalıştığında aynı iş farklı skorlanabilir (ya da listeye hiç girmeyebilir). Geçmişe bakış yok, trend analizi yok, skor değişimlerini takip etmek imkansız.

---

### 4. `logs/run_history.json` — Scan Geçmişi

`run_full_scan.py` her çalışmasında append eder. Son 100 kaydı tutar.

**Ne saklanır:**

```json
{
  "timestamp": "2026-07-13T10:00:00",
  "duration_seconds": 142.3,
  "success": true,
  "stats": {
    "total": 562,
    "recent": 45,
    "by_score": {"8": 30, "7": 121, "6": 89, ...}
  }
}
```

**Ne saklanmaz:** Hangi işlerin yeni geldiği, hangi işlerin bu scanla ortaya çıktığı, skor değişimleri.

---

### 5. `cold_emails/` — E-posta Taslakları

`cold_email_generator.py` çalıştığında `cold_emails/*.txt` ve `_MASTER_LIST_*.json` üretir.

**Ne saklanır:**
- Her iş için ilk email + 3 follow-up taslağı (düz txt dosyası)
- `_MASTER_LIST_*.json` — tüm e-postaların yapısal özeti

**Ne saklanmaz:** Hangi emailin gönderilip gönderilmediği, yanıt gelip gelmediği, hangi tarihte gönderildiği.

---

### 6. `docs/tracking/JOB_APPLICATIONS.md` — Başvuru Takibi

`track_applications.py` günceller. Ama kaynak Excel'den okur, elle de düzenlenir.

**Sorun:** Bu bir markdown dosyası. Bir işin durumunu (applied → interview → rejected) sorgulamak, tarih bazlı raporlamak, "kaç günde yanıt geldi" hesaplamak mümkün değil. Üstelik bir sonraki scan'de Excel değişirse senkron bozulabilir.

---

### 7. `backups/db_*.sqlite` — Veritabanı Yedekleri

`~/.applypilot/applypilot.db`'nin kopyaları. Son 10 yedek tutulur. Bunlar sadece felaket kurtarma içindir, sorgulama amaçlı değil.

---

## Özet: Neyin DB'ye Girmesi Gerekiyor?

| Veri | Şu an nerede | Sorun |
|---|---|---|
| Career OS skorları | `.txt` dosyaları | Kalıcı değil, tarihsel karşılaştırma yok |
| Skill match sonuçları | Excel (runtime'da hesaplanıyor) | Her export'ta sıfırdan hesaplanıyor |
| Başvuru durumu (applied/interview/rejected) | Excel Notes + Markdown | Sorgulama imkansız, senkron kopuyor |
| E-posta gönderim geçmişi | `.txt` + `.json` dosyaları | Hangi email ne zaman gönderildi takip yok |
| Scan geçmişi (iş bazında) | Sadece aggregate `run_history.json` | "Bu iş 3 scan önce 8 puandı" bilgisi yok |
| Skor değişim geçmişi | Yok | fit_score üzerine yazılıyor, eski değer gidiyor |

---

## Önerilen Mimari: Tek Bir Local SQLite

Proje kökünde `data/career_os.db` adında ikinci bir SQLite. ApplyPilot'un DB'sine dokunmuyoruz, oradan sadece okuyoruz. Kendi verimizi buraya yazıyoruz.

### Tablolar

```sql
-- Her tarama sonrası Career OS'un hesapladığı skorlar
CREATE TABLE career_scores (
    url           TEXT NOT NULL,
    scanned_at    TEXT NOT NULL,        -- ISO timestamp
    career_score  REAL,
    fit_score     REAL,
    acceptance_probability REAL,
    career_value  REAL,
    market_demand REAL,
    expected_value REAL,
    recommendation TEXT,
    skill_gaps    TEXT,                 -- JSON array
    PRIMARY KEY (url, scanned_at)
);

-- Başvuru durumu takibi
CREATE TABLE applications (
    url           TEXT PRIMARY KEY,
    title         TEXT,
    company       TEXT,
    applied_at    TEXT,                 -- NULL = henüz başvurulmadı
    status        TEXT DEFAULT 'to_apply',
    -- to_apply | applied | response | interview | offer | rejected
    notes         TEXT,
    salary_offered INTEGER,
    response_days INTEGER,             -- Başvurudan yanıta kaç gün
    updated_at    TEXT
);

-- E-posta takibi
CREATE TABLE emails (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    url           TEXT NOT NULL,
    template_type TEXT,
    sequence_num  INTEGER DEFAULT 0,   -- 0=ilk, 1=follow-up-1, 2=follow-up-2
    generated_at  TEXT,
    sent_at       TEXT,                -- NULL = henüz gönderilmedi
    subject       TEXT,
    body          TEXT
);

-- Tarama geçmişi (iş bazında)
CREATE TABLE scan_history (
    url           TEXT NOT NULL,
    scanned_at    TEXT NOT NULL,
    applypilot_score INTEGER,
    discovered_in_this_scan INTEGER DEFAULT 0,  -- Bu scan'de yeni mi geldi?
    PRIMARY KEY (url, scanned_at)
);
```

### Bu Mimari Neyi Mümkün Kılar?

```sql
-- Bir işin skor geçmişi
SELECT scanned_at, career_score, acceptance_probability
FROM career_scores WHERE url = 'https://...'
ORDER BY scanned_at;

-- Başvuru pipeline'ı
SELECT status, COUNT(*) FROM applications GROUP BY status;

-- Yanıt süresi analizi
SELECT AVG(response_days) FROM applications WHERE response_days IS NOT NULL;

-- Bu hafta başvurulacaklar (hem career_score >= 70 hem de henüz başvurulmamış)
SELECT a.url, a.title, cs.career_score
FROM applications a
JOIN career_scores cs ON a.url = cs.url
WHERE a.status = 'to_apply' AND cs.career_score >= 70
ORDER BY cs.career_score DESC;

-- Hangi scan'de kaç yeni iş keşfedildi
SELECT DATE(scanned_at), COUNT(*) FROM scan_history
WHERE discovered_in_this_scan = 1
GROUP BY DATE(scanned_at);
```

---

## Geçiş Planı

Bu değişiklik **mevcut sistemi kırmaz**. ApplyPilot'un DB'si olduğu gibi kalır. Sadece şunlar değişir:

1. `apply_strategy.py` → txt dosyaları yazmaya devam eder **+** `career_scores` tablosuna insert atar
2. `run_full_scan.py` → `scan_history` tablosunu günceller
3. `track_applications.py` → Excel'den değil `applications` tablosundan okur/yazar
4. `cold_email_generator.py` → `emails` tablosuna kaydeder
5. Yeni: basit bir `status.py` CLI → `SELECT`'lerle anlık dashboard verir

Excel tamamen ortadan kalkmak zorunda değil — üretmeye devam edebilir ama kaynak Excel değil DB olur.
