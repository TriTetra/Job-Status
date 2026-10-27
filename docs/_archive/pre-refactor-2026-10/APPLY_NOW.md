# Başvuru Kılavuzu

ApplyPilot'un bulduğu işleri Career OS ile analiz edip başvuru stratejisi
oluşturmanın tek-komutluk akışı.

## Hızlı başlangıç

### 1. Strateji oluştur

```bash
python scripts/strategy/apply_strategy.py
```

Script şunu yapar ([scripts/strategy/apply_strategy.py](../../scripts/strategy/apply_strategy.py)):

1. ApplyPilot'un veritabanından skoru 7+ olan işleri yükler
2. `career_os/data/applypilot_loader.py`'deki sabit profile karşı Career OS
   analizini çalıştırır
3. Sonuçları `career_os_output/` altına dosyalar halinde yazar

Çıktı:

```
career_os_output/
├── apply_today_<tarih>.txt          En yüksek skorlu 10 iş
├── apply_this_week_<tarih>.txt      En yüksek skorlu 20 iş
├── prioritized_applications_<tarih>.txt   Şirket büyüklüğüne göre dengelenmiş 15 iş
├── learning_plan_<tarih>.txt        ROI'ye göre sıralı 8 haftalık plan
└── summary_<tarih>.txt              Çalışmanın özet istatistikleri
```

### 2. Bugün başvur

```bash
cat career_os_output/apply_today_*.txt
```

Her satırda iş başlığı, URL, lokasyon, career score, acceptance probability ve
bir öneri (`APPLY` / `CONSIDER` / `SKIP`) bulunur. Her iş için: URL'yi aç, başvur,
`../tracking/JOB_APPLICATIONS.md`'ye kaydet.

### 3. Başvuruları takip et

`../tracking/JOB_APPLICATIONS.md` dosyasını elle güncelleyin. Format örneği dosyanın
içinde var.

## Dosyaların anlamı

### apply_today / apply_this_week

`career_score`'a göre sıralanmış, en üstteki 10 veya 20 iş. `career_score`,
fit (%30), acceptance probability (%25), career value (%25) ve market demand
(%20) ağırlıklarının toplamıdır
([opportunity_scorer.py](../../career_os/intelligence/opportunity_scorer.py)).

### prioritized_applications

Beklenen değere (fit × acceptance × career value) göre sıralanmış, ama tek bir
şirket büyüklüğüne aşırı yığılmaması için çeşitlendirilmiş 15 işlik bir portföy.
Diversifikasyon mantığı `CareerDecisionEngine.prioritize_applications`'ta.

### learning_plan

Eksik skill'leri ROI'ye (öğrenme maliyetine oranlı kariyer etkisi) göre sıralayıp
haftalık 10 saatlik bir tempoyla 8 haftaya yayan plan
([gap_analyzer.py](../../career_os/intelligence/gap_analyzer.py)). Her görev için
önerilen kaynaklar ve bir doğrulama projesi de listelenir.

## Acceptance probability nasıl hesaplanıyor?

Gerçek bir geri bildirim verisi yok — bu, kod içindeki sabit ağırlıklarla
hesaplanan bir tahmin, ölçülmüş bir oran değil. Faktörler
([opportunity_scorer.py](../../career_os/intelligence/opportunity_scorer.py)
`_estimate_acceptance`):

- Şirket büyüklüğü: big tech çarpanı 0.25, large 0.45, midsize 0.7, startup 1.2
- Deneyim farkı: gerekli yılın 0.8-1.5 katı arasındaysa tam puan, altındaysa
  üstel düşüş
- Remote eşleşmesi: %30 bonus
- Visa sponsorluğu gerekiyorsa ve şirket sponsor olmuyorsa: %60 ceza
- Tahmini rekabet: remote, yüksek maaş ve büyük şirket rekabeti artırır

Bu sayıyı "gerçek kabul şansı" olarak değil, "bu işe göreceli olarak ne kadar
öncelik vermeli" şeklinde okuyun.

## Günlük / haftalık rutin

**Günlük (30 dakika):** Sabah `apply_today_*.txt`'den 5 işe, akşam kalan 5'e
başvur; `../tracking/JOB_APPLICATIONS.md`'yi güncelle.

**Haftalık (2 saat):** Pazartesi `apply_strategy.py`'yi yeniden çalıştır ve
haftanın 20 işini gözden geçir. Salı-Cuma günde 5 başvuru ve gerekirse
follow-up email. Hafta sonu öğrenme planındaki görevle ilerle.

## Sorun giderme

**"career_os_output/ klasörü yok"** — Script ilk çalıştığında kendisi oluşturur;
çalışma dizininin proje köküne işaret ettiğinden emin olun (`pwd`).

**"Job'lar yüklenmiyor"** — ApplyPilot veritabanı henüz oluşmamış olabilir:

```bash
ls ~/.applypilot/applypilot.db
# Yoksa:
run_scan.bat
```
