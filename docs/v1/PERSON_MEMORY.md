# Kişi hafızası — tasarım ve yol haritası

**Durum:** öneri (2026-11-23). Araştırma: [`reports/Kişi hafızası ve kariyer modeli.md`](../../reports/Kişi%20hafızası%20ve%20kariyer%20modeli.md); puanlama modeli: [`reports/İş puanlama algoritması araştırması.md`](../../reports/İş%20puanlama%20algoritması%20araştırması.md).

**Amaç:** Aplio kişiyi tek bir yerden, zamanla birlikte tanısın. CV, beceri, başvuru, karar, öğrenme — her değişiklik git gibi geçmişiyle saklansın. Bütün modüller aynı hafızadan okusun ve oraya yazsın. Puan, kararlarından ve sonuçlarından öğrensin.

---

## 1. Bugün nerede duruyoruz (kod denetimi)

| Sorun | Nerede | Sonuç |
|---|---|---|
| Kişi bilgisi altı yere dağılmış | `users.profile_data`, `users.goals`, `user_settings.profile/skills/preferences` (CLI dönemi), `career_preferences`, `user_roles`, `evidence_items`, `career_graph_nodes` | Puanlama, `user_settings`'te beceri varsa onu, yoksa kanıtı kullanıyor (`scan.load_profile`): iki doğruluk kaynağı |
| Beceri = var/yok | `evidence/aggregation.py` (zamandan bağımsız ağırlıklı ortalama), `model_v8.skill_match` (`s in have`) | GitHub'da kanıtlı beceri ile CV'de bir kez geçen aynı; eski beceri yeni gibi |
| Beceri grafiği kullanılmıyor | `infra/seeds/v1/skills/skill_graph.yaml` (68 düğüm, 136 `transfers_to` kenarı) | PyTorch bilen TensorFlow isteyen ilandan sıfır kredi alıyor |
| Unvan eşleşmesi gevşek | `model_v8.title_match` | Hedef "Backend Engineer" iken her "… Engineer" ilanı "yakın rol" (0,6): "Cryogenics Engineer" 79 / Strong |
| Kariyer grafiği donuk | `onboarding/career_graph.py` | Onboarding'de bir kez kuruluyor, sonra güncellenmiyor; yalnız Briefing istatistiği okuyor |
| Öğrenme yok | `opportunities.record_decision`, `applications.history` | Shortlist / Skip / Applied ve sonuçlar hiçbir modeli değiştirmiyor; Skip'in nedeni sorulmuyor |
| Gönderilen CV bilinmiyor | `applications.resume_version` (serbest metin), `resume_documents.version` | Hangi CV'nin hangi sonucu aldığı öğrenilemez |
| Durum günlüğü var, niyet yok | `db/legacy/timeline.py` (alan düzeyinde eski/yeni değer) | "Neden?" sorusu cevapsız |
| Kırık menü | `lib/nav-items.ts` → `/evidence`, `/learning`, `/resume` | Web'de bu sayfalar yok (404); API uçları (`routers/evidence.py`, `resume.py`) var |

Test veritabanında (sentetik, 4 beceriyle) ölçüm: açık ilanların %3'ü LLM ile okunmuş, ortanca beceri karşılama %20, 323 eşleşmenin 298'i SKIP. Profil zayıfken her şey kötü görünüyor ve sistem bunu söylemiyor.

---

## 2. Mimari: tek olay günlüğü, modül başına projeksiyon

```
                         ┌──────────────────────────────┐
  kullanıcı / ajanlar ──►│  person_events (append-only) │──► projection_checkpoints (outbox imleci)
   (her yazma yolu)      │  niyet + actor + iki saat    │        │
                         └──────────────┬───────────────┘        ├─► embeddings / reflection (LLM)
                   aynı transaction'da  │                        ├─► Briefing özeti
                                        ▼                        └─► Telegram bildirimi
   ┌────────────────┬────────────────┬──────────────────┬─────────────────┬──────────────────┐
   │ person_facts   │ skill_beliefs  │ preference_post. │ chance_calib.   │ cv_commits/refs  │
   │ (iki saatli)   │ (log-odds,     │ (GLMix sapması)  │ (Beta-Binomial) │ (git: blob/      │
   │                │  sönümlü)      │                  │                 │  commit/ref/tag) │
   └───────┬────────┴───────┬────────┴────────┬─────────┴────────┬────────┴────────┬─────────┘
           ▼                ▼                 ▼                  ▼                 ▼
       Profil / "Aplio   Puanlama v8,     Opportunities,     Applications,     Resume,
       seni nasıl        Search, Market   Search sırası      şans aralığı      Learning
       tanıyor"
```

**Kurallar**
1. Her yazma yolu `memory.record(person_id, type, payload, actor=…)` çağırır; olay ve ilgili güncel tablo **aynı transaction'da** yazılır (tam event-sourcing değil — Azure kılavuzunun "profil = CRUD" uyarısına uygun "olay + projeksiyon").
2. Olay **niyet** taşır ("maaş düşük diye geçildi"), durum değil ("skor=41").
3. `actor`: `user` · `agent:<ad>` · `import:<kaynak>`. Kullanıcı düzeltmesi her zaman ajan çıkarımını ezer; replay halüsinasyonu gerçeğe çeviremez.
4. Modüller başka modülün tablosuna yazmaz; yalnız olay yazar, kendi projeksiyonunu okur.
5. Hafızada silme yok, **geçersiz kılma** var (`valid_to`). Tek istisna yasal silme (bölüm 6).

**Tablolar (taslak)**

```sql
person_events(seq bigserial PK, person_id, stream, stream_version, type, schema_ver,
              payload jsonb, actor, confidence, source_ref jsonb,
              valid_from timestamptz, recorded_at timestamptz default now(),
              causation_id, correlation_id, UNIQUE(person_id, stream, stream_version))
projection_checkpoints(consumer PK, last_seq)
person_facts(id, person_id, kind, subject, value jsonb, actor, confidence,
             valid_from, valid_to, source_event bigint)          -- EXCLUDE USING gist (btree_gist)
skill_beliefs(person_id, skill_key, log_odds, last_evidence_at, sources jsonb, updated_seq)
job_impressions(person_id, url, surface, rank, score, shown_at)   -- "görmedi" ≠ "beğenmedi"
cv_blobs(hash PK, content jsonb) · cv_commits(id, person_id, parents[], tree_hash, message, actor, at)
cv_refs(person_id, name, commit_id)                               -- main + rol ailesi dalları; CAS ile ilerler
```

Postgres sürümü: üretimdeki sürüm doğrulanmalı (yerel compose 16). `WITHOUT OVERLAPS` PG18'de geldi; ona dayanma, `EXCLUDE USING gist` kullan.

**Olay türleri (ilk set):** `ProfileStated`, `PreferenceChanged`, `WeightsChanged`, `CvUploaded`, `CvCommitted`, `CvTagged`, `SkillEvidenceAdded`, `SkillCorrected`, `JobShown`, `JobOpened`, `JobShortlisted`, `JobSkipped{reasons[]}`, `ApplicationSubmitted{cv_commit, channel}`, `StageChanged`, `OutcomeObserved{kind: response|interview|offer|reject|ghosted}`, `LearningGoalSet`, `GoalCompleted`, `ReflectionCreated{evidence_ids[]}`, `MemoryForgotten`.

---

## 3. Modüller hafızayla nasıl konuşur

| Modül | Okur | Yazar | Hafızaya katkısı |
|---|---|---|---|
| Puanlama (`jobs/scoring/model_v8.py`) | `skill_beliefs` (sönümlü), kapılar, tercih sapması, şans kalibrasyonu | — | Kişiye göre puan |
| Opportunities / Search | aynı + `job_impressions` | `JobShown`, `JobOpened`, `JobShortlisted`, `JobSkipped{reasons}` | Hızlı gelen tercih etiketleri |
| Applications | CV etiketleri, şans aralığı | `ApplicationSubmitted{cv_commit}`, `StageChanged`, `OutcomeObserved` | Şans modelinin etiketleri, sansür bilgisi |
| Resume | `cv_*`, kanıt kalemleri | `CvCommitted`, `CvTagged` | Hangi iddianın hangi kanıta dayandığı |
| Learning | beceri açıkları (ΔΓ) | `LearningGoalSet`, `SkillEvidenceAdded`, `GoalCompleted` | Yeni kanıt → inanç → yeniden puan |
| Evidence (GitHub, CV, portfolyo) | — | `SkillEvidenceAdded{source, reliability}` | Beceri inancının girdisi |
| Briefing | son olaylar, reflection'lar | `ReflectionCreated` | Kaynak gösteren içgörü |
| Telegram | outbox imleci | `NotificationSent` | Tekrarsız bildirim |
| LLM istemleri (derin okuma, CV uyarlama) | çekirdek profil bloğu + 1–2k token tarihli gerçek (pgvector + tsvector, RRF) | — | Kişiyi bilen ama az veri gönderen istem |

---

## 4. Modeller (araştırmadan, v8'e bağlanış)

**Beceri inancı** — log-odds, kanıt toplanır, her kanıt kendi yaşıyla söner:
- Güvenilirlik: öz-beyan 0,3 · sonuç yazan CV maddesi 0,5 · kendi repo (import/API düzeyi) 0,8 · üçüncü taraf doğrulama 1,0 (öz-değerlendirme–performans r≈.29, Zell & Krizan 2014).
- Sönüm: `w(t) = taban + (w0 − taban)·2^(−t/h)`; araç/API h≈12 ay, taban 0,4; kavram h≈24–36 ay (2025 Psych. Bulletin meta-analizi: kullanılmayan beceride kazanımın yarısı 6,5–13 ayda gidiyor). Pazar eskimesi ayrı: `market_skills` trendinden.
- Kısmi kredi: `skill_graph.yaml` kenarları (≥0,6), asimetrik (ebeveyn ≠ çocuk).
- v8: `skill_match` ikili yerine sürekli kapsama alır. **Uyarı:** `c_must` düşer; 0,55 orta noktası etiketli değerlendirme setiyle yeniden ayarlanır.

**Tercih** — LinkedIn GLMix deseni: v8 sabit offset, kişisel sapma Gaussian önselle (σ=0,5) büzülür; değer V'ye en fazla ±0,15 dokunur, Bied Γ formülü aynı kalır. Etiket ağırlıkları XING RecSys 2017: Skip −10, Shortlist/Apply +5, insan yanıtı +20. Görünür kişiselleşme ≈30–50 karardan sonra. Günlük Thompson örneklemesi (liste gün içinde oynamaz) + 10'da 1 keşif yuvası (etiketli).

**Skip nedenleri** — tek dokunuşluk çipler: rol uymuyor · beceri uymuyor · kıdem yanlış · maaş düşük · konum / vize · çalışma şekli · şirket · zaten başvurdum. Nedenli Skip, nedensizden çok daha bilgilendirici (Chen & Pu: kullanıcının kendi eleştirisi daha az çabayla doğruluğa ulaşıyor).

**Şans kalibrasyonu** — üç aşama: (1) Beta-Binomial taban kaydırması, önsel sözde-sayı 20–50, etiket "herhangi bir insan yanıtı" (görüşme değil; çok seyrek); (2) yüzlerce sonuçtan sonra Bayesian Platt (eğim 1'e büzülür); (3) tam kişisel model. Yanıtsız başvuru ret değil sansürlü: log-normal yanıt süresi (medyan ~6 gün), 21. gün "muhtemelen sessiz", 45. gün kapalı. Şans her zaman **aralık** olarak gösterilir.

**CV (git)** — `main` = ana CV; her rol ailesi bir dal; her başvuru gönderilen commit'i etiketler (öğrenmenin tek bağlantısı bu). Kanıt kapısı: kanıtı olmayan iddia CV'ye giremez (Huntr: AI kullananların %63'ü CV'ye doğru olmayan şey eklendiğini söylüyor). Varyant karşılaştırması kazanan ilan etmez: %4 ile %8'i ayırmak varyant başına 300+ başvuru ister; belirsizlik gösterilir.

**Learning** — sıradaki beceri = hedef ilanlarda toplam ΔΓ (o beceriyle yeniden puanlanınca) ÷ öğrenme maliyeti, açgözlü seçim. İlerleme saatle değil kanıtla. Sıradaki rol: 3–5 seçenek, her birinin beceri açığıyla (en iyi yöntem bile doğru rolü ilk 10'da %43 buluyor).

---

## 5. Yol haritası

Sıra mantığı: **geri dönüp üretilemeyen veri önce** — gösterim, karar ve gönderilen-CV kaydı. Modeller bu verinin üstüne kurulur.

| Faz | İçerik | Bitti sayılır |
|---|---|---|
| **0. Temizlik** | Unvan eşleşmesi hatası (genel kelimeler tek başına eşleşmesin); tek doğruluk kaynağı: puanlama yalnız web profilini okusun, `user_settings` beceri/profil emekliye; kırık menü bağlantıları (sayfalar yapılana kadar gizle); 50 ilanlık etiketli değerlendirme seti + "ilk 10'un kaçı iyi" ölçümü | Cryogenics örneği düşüyor; değerlendirme betiği çalışıyor |
| **1. Kayıt** | `person_events` + `memory.record()`; mevcut yazma yollarından olay (karar, başvuru durumu, CV yükleme, kanıt, tercih, ağırlık); `job_impressions` (Opportunities + Search, sıra ile); Skip neden çipleri; başvuruya CV sürümü etiketi | Her karar ve gösterim günlükte; testler |
| **2. Beceri inancı** | `skill_beliefs` projeksiyonu (güvenilirlik + sönüm + grafik kısmi kredi); v8 sürekli kapsama; profil zayıflık uyarısı (Briefing + Settings) | Değerlendirme setinde ilk 10 iyileşiyor |
| **3. Öğrenen sıralama** | Tercih sapması (GLMix, ±0,15), günlük Thompson + keşif yuvası; şans kalibrasyonu (Beta-Binomial, "insan yanıtı"); sessizlik sansürü 21/45 gün; "Neden üstte?" açıklamasına kişisel katkı satırı | 30+ karardan sonra görünür değişim, açıklanabilir |
| **4. CV git + Resume sayfası** | `cv_blobs/commits/refs`; ana CV + rol dalları; diff görünümü; kanıt kapısı; başvuruda commit etiketi | Her başvurunun gönderdiği CV bilinir |
| **5. Learning sayfası** | ΔΓ ile sıradaki beceri; hedef + kanıtla ilerleme; 3–5 sıradaki rol | Öğrenilen beceri puanlara yansır |
| **6. Hafızanın yüzü** | "Aplio seni nasıl tanıyor": beyan vs çıkarım, düzelt / unut; git ağacı gibi zaman çizelgesi (CV, beceri, başvuru); Briefing'de kaynaklı reflection'lar (önem toplamı 150'yi geçince); LLM bağlam kurucu | Kullanıcı her çıkarımın kaynağını görebilir |

Gizlilik baştan: her satır `person_id` ile; hesap silme = sert silme; seçici "unut" = `MemoryForgotten` olayı + önceki payload'ların temizlenmesi; kripto-parçalama yalnız yedekler ve CV PDF'leri için. KVKK ayrıca incelenmedi.

---

## 6. Açık sorular ve riskler

- Katsayıların çoğu (güvenilirlik, sönüm tabanı, kısmi kredi, ±0,15) **kanıtla sınırlanmış tasarım tercihi**, ölçülmüş etki değil — değerlendirme seti ve kişinin kendi verisiyle ayarlanmalı.
- Türkiye'den AB'ye başvuran aday için huni verisi yok; tek kaynak Aplio'nun kendi kaydı.
- Görüşme bir yılda bir avuç kez olur: şans modeli aylarca önsel ağırlıklı kalır.
- Bellek kıyaslamaları (Mem0, Zep) satıcıların kendi ölçümleri.
- Event sourcing maliyetli: şema evrimi upcaster'la; olayı yerinde değiştirmek son çare.
