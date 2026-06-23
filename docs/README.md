# Dokümantasyon İndeksi

Bu klasördeki her doküman dört kategoriden birine giriyor: kurulum (`setup/`),
günlük kullanım (`usage/`), başvuru takibi (`tracking/`) ve iş arama stratejisi
(`strategy/`). Mimariye dair tek başvuru kaynağı [SYSTEM_SUMMARY.md](SYSTEM_SUMMARY.md).

## Nereden başlamalı?

1. Sistemi ilk kez kuruyorsan: [setup/QUICK_START.md](setup/QUICK_START.md)
2. İlk tarama bitti, ne yapacağını öğrenmek istiyorsan: [usage/APPLY_NOW.md](usage/APPLY_NOW.md)
3. Mimariyi/tüm akışı anlamak istiyorsan: [SYSTEM_SUMMARY.md](SYSTEM_SUMMARY.md)

## setup/ — Kurulum ve otomasyon

| Dosya | İçerik |
|---|---|
| [QUICK_START.md](setup/QUICK_START.md) | İlk taramayı çalıştırma, sonuçları okuma, 5 dakikalık kurulum |
| [WINDOWS_SCHEDULER_GUIDE.md](setup/WINDOWS_SCHEDULER_GUIDE.md) | `run_full_scan.py`'yi Windows Task Scheduler ile her 3 günde bir otomatik çalıştırma |
| [GITHUB_GUIDE.md](setup/GITHUB_GUIDE.md) | Repoyu GitHub'a push etme, başvuru takibini GitHub Issues/Projects ile yapma |

## usage/ — Günlük kullanım

| Dosya | İçerik |
|---|---|
| [USAGE.md](usage/USAGE.md) | Career OS'un ne eklediği, kullanım seçenekleri (CLI/Python), sorun giderme |
| [APPLY_NOW.md](usage/APPLY_NOW.md) | `apply_strategy.py` çalıştırıldıktan sonra üretilen dosyaların nasıl okunacağı |

## tracking/ — Başvuru takibi (canlı veri)

| Dosya | İçerik |
|---|---|
| [JOB_APPLICATIONS.md](tracking/JOB_APPLICATIONS.md) | Tek tek başvuru kayıtları — elle güncellenen ana tracker |
| [APPLICATION_TRACKER.md](tracking/APPLICATION_TRACKER.md) | 8 haftalık sprint için haftalık hedef/metrik şablonu |

Bu ikisi şablon/canlı veri olduğu için diğer kategorilerden farklı: "nasıl
çalışır" değil, "şu anki durum ne" sorusuna cevap veriyor.

## strategy/ — İş arama stratejisi

| Dosya | İçerik |
|---|---|
| [2_MONTH_ACTION_PLAN.md](strategy/2_MONTH_ACTION_PLAN.md) | 8 haftalık, çok kanallı (başvuru + cold email + LinkedIn) iş arama planı |

Bu doküman araçla ilgili değil — iş arama sürecinin kendisiyle ilgili.

## Kök dizinde kalanlar

`docs/` dışında, repo kökünde sadece iki doküman var:

- [../README.md](../README.md) — projenin genel girişi, iki sistemin (ApplyPilot + Career OS) nasıl bağlandığı
- [../CHANGELOG.md](../CHANGELOG.md) — her taramanın kayıt defteri

Kod mimarisi için: [../career_os/README.md](../career_os/README.md)
