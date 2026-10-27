# Windows Task Scheduler Kurulum Kılavuzu

ApplyPilot'u otomatik olarak her 3 günde bir çalıştırmak için.

## Hedef

Sistemi Pazartesi, Perşembe ve Pazar sabahları otomatik çalıştırmak.

## Adım adım kurulum

### 1. Task Scheduler'ı aç

`Windows Tuşu + R` -> `taskschd.msc` -> Enter, veya Start Menu'den
"Task Scheduler" ara.

### 2. Yeni görev oluştur

1. Sağ menüde "Create Basic Task..." tıkla
2. Name: `ApplyPilot Auto Scan`
3. Description: `Otomatik iş tarama sistemi - her 3 günde bir`
4. Next

### 3. Trigger ayarla

1. "Weekly" seç -> Next
2. Start: bugünün tarihi, saat 09:00
3. Recur every: 1 week
4. Seç: Monday, Thursday, Sunday
5. Next

### 4. Action ayarla

1. "Start a program" seç -> Next
2. Program/script:
   ```
   C:\Users\Dimoontri\Desktop\applypilot-jobs\venv\Scripts\python.exe
   ```
3. Add arguments:
   ```
   C:\Users\Dimoontri\Desktop\applypilot-jobs\scripts\scan\run_full_scan.py
   ```
4. Start in:
   ```
   C:\Users\Dimoontri\Desktop\applypilot-jobs
   ```
5. Next

### 5. Son ayarlar

1. Özet ekranını kontrol et
2. "Open the Properties dialog..." seç
3. Finish

### 6. Properties ayarları

**General:**
- "Run whether user is logged on or not"
- "Run with highest privileges"
- "Configure for: Windows 10"

**Conditions:**
- "Start the task only if the computer is on AC power" seçeneğini kaldır
- "Wake the computer to run this task" işaretle

**Settings:**
- "Allow task to be run on demand"
- "Run task as soon as possible after a scheduled start is missed"
- "If the task fails, restart every: 10 minutes"
- "Stop the task if it runs longer than: 2 hours"

OK'e tıkla, gerekirse Windows şifresini gir.

## Test et

### Manuel test

1. Task Scheduler'da "ApplyPilot Auto Scan"ı bul
2. Sağ tık -> "Run"
3. 25-30 dakika bekle
4. `logs/` klasörünü kontrol et

### Log kontrolü

PowerShell:
```powershell
Get-Content C:\Users\Dimoontri\Desktop\applypilot-jobs\logs\$(Get-Date -Format yyyy-MM-dd).log -Tail 50
```

Git Bash:
```bash
tail -50 ~/Desktop/applypilot-jobs/logs/$(date +%Y-%m-%d).log
```

## Çalışma programı

| Gün | Saat | Süre |
|-----|------|------|
| Pazartesi | 09:00 | ~30 dk |
| Perşembe | 09:00 | ~30 dk |
| Pazar | 09:00 | ~30 dk |

## Bildirim sistemi (opsiyonel)

`scripts/scan/run_full_scan.py`'nin sonuna bir email bildirimi eklenebilir:

```python
def send_email_notification(stats):
    import smtplib
    from email.mime.text import MIMEText

    subject = f"ApplyPilot Scan Complete - {stats['total']} jobs"
    body = f"""
    Scan completed.

    Perfect Match (8+): {sum(v for k, v in stats['by_score'].items() if k >= 8)}
    Good Match (7): {stats['by_score'].get(7, 0)}

    Check reports folder for details.
    """

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = 'your_email@gmail.com'
    msg['To'] = 'abdullahabdulkadir0@gmail.com'

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login('your_email@gmail.com', 'your_app_password')
        smtp.send_message(msg)

# Call at the end of run_full_scan()
if stats:
    send_email_notification(stats)
```

Not: bu kod parçası şu an `run_full_scan.py`'de yok — entegre etmek istersen
elle eklemen gerekiyor, ve Gmail uygulama şifresi (app password) gerekir.

## Sorun giderme

**"Task did not run"** — Python yolu yanlış olabilir. Absolute path kullan:
`C:\Users\Dimoontri\Desktop\applypilot-jobs\venv\Scripts\python.exe`

**"Access Denied"** — Task'ı "Run with highest privileges" ile çalıştır.

**"Task runs but nothing happens"** — "Start in" alanını kontrol et:
`C:\Users\Dimoontri\Desktop\applypilot-jobs`

**"Unicode errors in log"** — Script UTF-8 ile çalışacak şekilde ayarlı; sorun
yaşarsan `run_full_scan.py`'nin başına ekle:
```python
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'
```

## Kontrol listesi

- [ ] Task Scheduler'da görünüyor
- [ ] "Run" ile test edildi
- [ ] Log dosyası oluşturuldu
- [ ] Excel raporu oluşturuldu
- [ ] Backup alındı
- [ ] Zamanlanmış çalışma doğrulandı

## İpuçları

1. Task'ın çalışması için bilgisayar açık olmalı (uyku modunda olabilir)
2. Laptop kullanıyorsan "AC power" koşulunu kapat, yoksa pildeyken çalışmaz
3. İlk hafta manuel kontrol et, sonra otomatiğe güven
4. Email/Telegram bildirimi eklersen sonuçları mobilden de görebilirsin
