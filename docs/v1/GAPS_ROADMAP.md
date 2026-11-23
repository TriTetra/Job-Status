# Kapsam ve iş akışı açıkları: iki fazlı plan

**Durum:** plan (2026-11-23). Kaynak: canlı test, piyasa karşılaştırması ve [PERSON_MEMORY.md](PERSON_MEMORY.md).

**Kural (her madde için):** tek madde → kod + testler → atılabilir DB'de tarayıcı kontrolü → CHANGELOG → commit → onayınla push / deploy → canlıda doğrulama. Bir madde bitmeden sonrakine geçilmez. Kuralları otomatik toplamayı yasaklayan sitelere (LinkedIn, Kariyer.net, Indeed, Glassdoor, kununu) otomatik erişim yok; onlar senin elinle (eklenti, yapıştırma, dışa aktarma) sisteme girer.

**Senden gerekenler** (ilgili madde başlarken sorulur): Adzuna ve Reed ücretsiz API anahtarları; e-posta için uygulama şifresi ya da yönlendirme; eklentiyi Chrome'a yükleme; LinkedIn bağlantılarını kendin dışa aktarma.

---

## Faz 1: Kapsam ve sonuç döngüsü (veri tarafı)

Amaç: daha çok ve daha doğru ilan, maaş ve şirket bilgisi; başvuruların sonucu kendiliğinden geri gelsin. Faz 2'nin öğrenen sıralaması bu veriye dayanıyor.

| # | Madde | Ne yapılacak | Bitti sayılır | Senden |
|---|---|---|---|---|
| 1.1 | **Resmi ilan API'leri** | Yeni kaynaklar: **Adzuna** (GB, DE, NL, PL, AT, ES, CH, FR, IT…), **Almanya Federal İş Ajansı Jobsuche**, **Reed** (UK). Unvan + ülke aramasıyla, mevcut feed altyapısında (kaynak etiketi, "via X" bağlantısı, tekrar ayıklama, günlük kota). Kaynakların kullanım şartları uygulamadan önce okunur. | Hedef ülkelerinde Search ve Opportunities'te bu kaynaklardan ilanlar; kota aşılmıyor; testler | Adzuna, Reed anahtarları |
| 1.2 | **Unvan filtresini genişletme** | Sisteme girişteki unvan listesi rol aileleriyle büyür (ML / AI / data / backend / platform / security / solutions / forward-deployed…, Almanca ve Türkçe karşılıkları); hangi unvanların dışarıda kaldığı bir kez raporlanır. | Kaçan ilgili unvan raporu boşa yakın; gürültü artmıyor (değerlendirme) | — |
| 1.3 | **Herhangi bir ilanı ekleme** | "Add a job": bağlantı yapıştır (izinli sitelerde sayfa okunur) ya da ilan metnini yapıştır (LinkedIn, Kariyer.net için); LLM ilanı okur, puanlanır, Search / Opportunities'e ve kuyruğa girebilir, kit hazırlanabilir. | Yapıştırılan bir LinkedIn ilanı puanlanıp kit alıyor | — |
| 1.4 | **Maaş verisi** | Adzuna'nın maaş dağılımı ve geçmiş verisi ile ülke × rol medyanları; puandaki "maaş referansı" ve Market sayfası ABD ağırlıklı ilanlar yerine buna dayanır. | Berlin / Londra / İstanbul için rol başına medyan; Market'te kaynaklı | Adzuna anahtarı |
| 1.5 | **Şirket verisi** | Şirket kartı: kuruluş yılı ve büyüklük (Wikidata), İngiltere'de Companies House (var mı, yaşı, durumu), Hacker News'ten "çalışanlar ne diyor" özeti (kaynaklı), haberlerde işten çıkarma / yatırım sinyali. Güven puanına girer. | Okuyucuda ve Companies'te şirket kartı; özetler kaynak gösteriyor | (Companies House ücretsiz anahtar) |
| 1.6 | **Tazelik** | Kaynak başına okuma sıklığı: ucuz şirket panoları saatlik, kotalı feed'ler günlük; yeni çıkan iyi eşleşme Telegram'a dakikalar içinde. | Yeni ilanın görünme süresi saatlere iniyor; kotalar korunuyor | — |
| 1.7 | **Sonucu otomatik görme (e-posta)** | E-posta bağlantısı (önce uygulama şifresiyle IMAP ya da yönlendirme adresi; sonra Gmail / Outlook): şirketlerden gelen yanıtlar bulunur, LLM sınıflandırır (red / mülakat daveti / bilgi isteği / teklif), başvuru durumu ve `OutcomeObserved` güncellenir; emin olmadığı durumda sana sorar. Yalnız başvurduğun şirketlerin e-postaları okunur. | Gerçek bir red ve bir davet otomatik işlendi; gizlilik ayarları ve "unut" çalışıyor | Uygulama şifresi ya da yönlendirme |
| 1.8 | **Takip mesajları** | 14 / 21 günde kanıta dayalı kısa takip e-postası taslağı (Applications ve Telegram'da), gönderen sensin; gönderdiğin işaretlenir. | Taslak, sessiz başvuruda çıkıyor; tekrar sormuyor | — |

**Faz 1 sırası:** 1.1 → 1.2 → 1.3 → 1.7 → 1.8 → 1.4 → 1.5 → 1.6 (önce ilan ve sonuç akışı, sonra zenginleştirme).

---

## Faz 2: İş akışını tamamlama (ilan → teklif)

Amaç: başvurudan teklife kadar her adım Aplio'da; sistem senin sonuçlarından öğreniyor.

| # | Madde | Ne yapılacak | Bitti sayılır | Senden |
|---|---|---|---|---|
| 2.1 | **Tarayıcı eklentisi** | Chrome (MV3): Greenhouse / Lever / Ashby / Workable / Workday / SmartRecruiters formlarını kitteki cevaplarla doldurur (yasal ve demografik alanlar, yapay zekâ politikası boş kalır; göndermeye sen basarsın); herhangi bir sitedeki ilanı tek tıkla Aplio'ya kaydeder (1.3'ü kullanır); Settings'te kişisel erişim anahtarıyla bağlanır. | Gerçek bir Greenhouse formu dolduruldu, bir LinkedIn ilanı kaydedildi | Eklentiyi yüklemek |
| 2.2 | **CV: Resume sayfası** | Kanıttan ana CV; rol ailesi başına sürümler (git gibi: commit, dal, fark); ilan başına "şunu öne çıkar / şunu çıkar" önerileri; kanıt kapısı (kanıtsız iddia yok); PDF çıktı; kitte ve başvuruda hangi sürüm gönderildi. | İki rol için iki sürüm, PDF, başvuruda sürüm etiketi | — |
| 2.3 | **Evidence sayfası** | Kanıtını gör, düzelt, sil, ekle (GitHub, portfolyo, sertifika); her becerinin dayandığı kanıt ve gücü. | "Soon" kalktı; düzeltme hafızaya yazılıyor | — |
| 2.4 | **Learning sayfası** | Hedef ilanlarına göre sıradaki beceri (en çok kapı açan ÷ öğrenme maliyeti), hedef, kaynak, kanıtla ilerleme (repo, proje, sertifika); öğrenilen beceri puanlara yansır. | Bir hedef konuldu, kanıt eklendi, ilgili ilanların puanı yükseldi | — |
| 2.5 | **Öğrenen sıralama** | PERSON_MEMORY Faz 2–3: sönümlü beceri inancı ve kısmi kredi; kararlarından tercih öğrenme (Skip nedenleri dahil); "herhangi bir yanıt" üzerinden şans kalibrasyonu; değerlendirme setiyle önce / sonra ölçümü. | 30+ karardan sonra AUC ve ilk 10 iyileşiyor; açıklamada kişisel katkı satırı | Kullanım (kararlar) |
| 2.6 | **Mülakat hazırlığı** | Davet gelince (1.7): şirket özeti, rolün beklentileri, olası sorular, senin kanıtından hazırlanmış cevap taslakları (her iddia kanıta bağlı), sorulacak sorular. | Bir davet için hazırlık sayfası | — |
| 2.7 | **Tanıdıklar ve referans** | LinkedIn bağlantılarını kendin dışa aktarırsın (CSV); şirketlerle eşleşir: "X şirketinde 2 tanıdığın var"; referans isteme mesajı taslağı; kuyrukta ve okuyucuda gösterilir. | CSV yüklendi, eşleşmeler ve taslak çıkıyor | LinkedIn dışa aktarma |
| 2.8 | **Mobil** | PWA (ana ekrana ekle) ve web bildirimleri; Ready to apply ve rapor telefonda rahat. | Telefonda yükleniyor, bildirim geliyor | — |

**Faz 2 sırası:** 2.1 → 2.2 → 2.3 → 2.5 → 2.4 → 2.6 → 2.7 → 2.8 (2.5, Faz 1'in sonuç verisi ve iki haftalık kullanım biriktikçe).

---

## Riskler ve sınırlar
- Otomatik toplama yasak sitelerde kapsam ancak senin elinle büyür (eklenti, yapıştırma).
- E-posta okuma hassas: yalnız başvurulan şirketler, açık izin, görünür ve silinebilir kayıt.
- Gmail / Outlook API'leri çok kullanıcıda doğrulama süreci ister; önce tek kullanıcı için uygulama şifresi.
- Katsayılar ve sınıflandırıcılar senin verinle ayarlanmalı; değerlendirme seti her fazda yeniden ölçülür.
