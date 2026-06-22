# 🕐 Windows Task Scheduler Kurulum Kılavuzu

ApplyPilot'u **otomatik** olarak her 3 günde bir çalıştırmak için.

---

## 🎯 Hedef

Sistemi **Pazartesi, Perşembe, Pazar** sabahları otomatik çalıştırmak.

---

## 📝 Adım Adım Kurulum

### **1. Task Scheduler'ı Aç**

```
Windows Tuşu + R → "taskschd.msc" → Enter
```

veya

```
Start Menu → "Task Scheduler" ara
```

---

### **2. Yeni Görev Oluştur**

1. Sağ menüde **"Create Basic Task..."** tıkla
2. **Name:** `ApplyPilot Auto Scan`
3. **Description:** `Otomatik iş tarama sistemi - her 3 günde bir`
4. **Next** tıkla

---

### **3. Trigger (Tetikleyici) Ayarla**

1. **"Weekly"** seç → **Next**
2. **Start:** Bugünün tarihi, **Saat: 09:00**
3. **Recur every:** `1` week
4. **Seç:** ✅ Monday, ✅ Thursday, ✅ Sunday
5. **Next** tıkla

---

### **4. Action (Eylem) Ayarla**

1. **"Start a program"** seç → **Next**

2. **Program/script:** 
   ```
   C:\Users\Dimoontri\Desktop\applypilot-jobs\venv\Scripts\python.exe
   ```

3. **Add arguments:**
   ```
   C:\Users\Dimoontri\Desktop\applypilot-jobs\scripts\run_full_scan.py
   ```

4. **Start in:**
   ```
   C:\Users\Dimoontri\Desktop\applypilot-jobs
   ```

5. **Next** tıkla

---

### **5. Son Ayarlar**

1. Özet ekranını kontrol et
2. **✅ "Open the Properties dialog..."** seç
3. **Finish** tıkla

---

### **6. Properties Ayarları**

#### **General Sekmesi:**
- ✅ **"Run whether user is logged on or not"**
- ✅ **"Run with highest privileges"**
- ✅ **"Configure for: Windows 10"**

#### **Conditions Sekmesi:**
- ❌ **"Start the task only if the computer is on AC power"** (kaldır!)
- ✅ **"Wake the computer to run this task"**

#### **Settings Sekmesi:**
- ✅ **"Allow task to be run on demand"**
- ✅ **"Run task as soon as possible after a scheduled start is missed"**
- ✅ **"If the task fails, restart every: 10 minutes"**
- **"Stop the task if it runs longer than:** `2 hours`

7. **OK** tıkla
8. Windows şifresini gir (gerekirse)

---

## ✅ Test Et

### **Manuel Test:**

1. Task Scheduler'da **"ApplyPilot Auto Scan"** bulun
2. Sağ tıkla → **"Run"**
3. 25-30 dakika bekle
4. `C:\Users\Dimoontri\Desktop\applypilot-jobs\logs\` kontrol et

### **Log Kontrol:**

```bash
# PowerShell'de:
Get-Content C:\Users\Dimoontri\Desktop\applypilot-jobs\logs\$(Get-Date -Format yyyy-MM-dd).log -Tail 50
```

veya

```bash
# Git Bash'de:
tail -50 ~/Desktop/applypilot-jobs/logs/$(date +%Y-%m-%d).log
```

---

## 📊 Çalışma Programı

| Gün | Saat | Süre | Durum |
|-----|------|------|-------|
| **Pazartesi** | 09:00 | ~30 dk | ✅ Otomatik |
| **Perşembe** | 09:00 | ~30 dk | ✅ Otomatik |
| **Pazar** | 09:00 | ~30 dk | ✅ Otomatik |

---

## 🔔 Bildirim Sistemi (Opsiyonel)

### **Email Bildirimi Ekle:**

1. `scripts/run_full_scan.py` dosyasının sonuna ekle:

```python
# Email notification function
def send_email_notification(stats):
    import smtplib
    from email.mime.text import MIMEText

    subject = f"ApplyPilot Scan Complete - {stats['total']} jobs"
    body = f"""
    Scan completed!
    
    Perfect Match (8+): {sum(v for k,v in stats['by_score'].items() if k >= 8)}
    Good Match (7): {stats['by_score'].get(7, 0)}
    
    Check reports folder for details.
    """

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = 'your_email@gmail.com'
    msg['To'] = 'abdullahabdulkadir0@gmail.com'

    # Send via Gmail
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login('your_email@gmail.com', 'your_app_password')
        smtp.send_message(msg)

# Call it at the end of run_full_scan()
if stats:
    send_email_notification(stats)
```

---

## 🛠️ Sorun Giderme

### ❌ "Task did not run"

**Sebep:** Python path yanlış

**Çözüm:** Absolute path kullan
```
C:\Users\Dimoontri\Desktop\applypilot-jobs\venv\Scripts\python.exe
```

### ❌ "Access Denied"

**Sebep:** Yetki eksik

**Çözüm:** Task'ı "Run with highest privileges" ile çalıştır

### ❌ "Task runs but nothing happens"

**Sebep:** Working directory yanlış

**Çözüm:** "Start in" kısmını kontrol et:
```
C:\Users\Dimoontri\Desktop\applypilot-jobs
```

### ❌ "Unicode errors in log"

**Sebep:** Encoding sorunu

**Çözüm:** Script'te UTF-8 set edilmiş, sorun olmamalı. Eğer varsa:
```python
# run_full_scan.py başına ekle
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'
```

---

## 📋 Checklist

Kurulum tamamlandıktan sonra:

- [ ] Task Scheduler'da görünüyor
- [ ] "Run" ile test edildi
- [ ] Log dosyası oluşturuldu
- [ ] Excel raporu oluşturuldu
- [ ] Backup alındı
- [ ] Zamanlanmış çalışma doğrulandı

---

## 💡 Pro Tips

1. **Bilgisayarı açık tutun:** Task çalışması için bilgisayar açık olmalı (uyku modunda olabilir)

2. **Battery saver mode:** Laptop'taysa, AC power kontrolünü KAPATIN

3. **Test run:** İlk hafta manuel kontrol et, sonra otomatik bırak

4. **Notification:** Email/Telegram bildirimi ekle, sonuçları mobilde gör

---

**Kurulum tamamlandı! Artık sistem her 3 günde bir otomatik çalışacak! 🎉**
