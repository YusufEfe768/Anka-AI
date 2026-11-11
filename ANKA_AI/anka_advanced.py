# ── ANKA GELİŞMİŞ ÖZELLİKLER MODÜLü ─────────────────────────────────────────
import subprocess, os, time, threading, datetime, json, ctypes
import psutil, requests
from anka_config import BASE_DIR

AUTOMATION_FILE = os.path.join(BASE_DIR, "anka_automation.json")
BACKUP_FILE     = os.path.join(BASE_DIR, "anka_backup.json")

def _load(path, default):
    try:
        if os.path.exists(path):
            with open(path,"r",encoding="utf-8") as f: return json.load(f)
    except: pass
    return default

def _save(path, data):
    try:
        with open(path,"w",encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except: pass


# ── Ekran Parlaklığı ──────────────────────────────────────────────────────────
def set_brightness(level):
    """0-100 arası parlaklık ayarı (WMI ile)"""
    try:
        subprocess.run(
            ["powershell","-Command",
             f"(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,{level})"],
            capture_output=True, timeout=5
        )
        return True
    except: return False

def get_brightness():
    try:
        result = subprocess.run(
            ["powershell","-Command",
             "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness).CurrentBrightness"],
            capture_output=True, text=True, timeout=5
        )
        return int(result.stdout.strip())
    except: return -1


# ── Ekran Kaydı ───────────────────────────────────────────────────────────────
class ScreenRecorder:
    def __init__(self):
        self.recording = False
        self.proc = None
        self.output_path = None

    def start(self):
        if self.recording: return False
        try:
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            self.output_path = os.path.join(os.path.expanduser("~"), "Desktop", f"anka_kayit_{ts}.mp4")
            # FFmpeg ile ekran kaydı
            self.proc = subprocess.Popen([
                "ffmpeg","-y",
                "-f","gdigrab","-framerate","30","-i","desktop",
                "-vcodec","libx264","-preset","ultrafast",
                self.output_path
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.recording = True
            return True
        except Exception as e:
            print(f"Ekran kaydı başlatılamadı: {e}")
            return False

    def stop(self):
        if not self.recording: return None
        try:
            if self.proc:
                self.proc.terminate()
                self.proc.wait(timeout=5)
        except: pass
        self.recording = False
        return self.output_path


# ── Uygulama Ses Kontrolü ─────────────────────────────────────────────────────
def get_audio_sessions():
    """Ses çıkaran uygulamaları listele"""
    try:
        result = subprocess.run(
            ["powershell","-Command",
             "Get-Process | Where-Object {$_.MainWindowTitle -ne ''} | Select-Object Name,Id | ConvertTo-Json"],
            capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip()
    except: return "Ses bilgisi alınamadı."

def mute_app(app_name):
    try:
        subprocess.run(
            ["powershell","-Command",
             f"$p=Get-Process '{app_name}' -ErrorAction SilentlyContinue; if($p){{$p.Kill()}}"],
            capture_output=True, timeout=5
        )
        return True
    except: return False

def set_app_volume(app_name, volume):
    """Uygulama ses seviyesi (pycaw ile, kurulu değilse atlar)"""
    try:
        from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume
        sessions = AudioUtilities.GetAllSessions()
        for session in sessions:
            if session.Process and app_name.lower() in session.Process.name().lower():
                vol = session._ctl.QueryInterface(ISimpleAudioVolume)
                vol.SetMasterVolume(volume/100, None)
                return True
    except: pass
    return False


# ── Mikrofon Aç/Kapat ─────────────────────────────────────────────────────────
_mic_muted = False
def toggle_microphone():
    global _mic_muted
    try:
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        # Windows varsayılan mikrofonu kapat/aç
        subprocess.run(
            ["powershell","-Command",
             f"$obj = New-Object -ComObject WScript.Shell; $obj.SendKeys([char]173)"],
            capture_output=True, timeout=3
        )
        _mic_muted = not _mic_muted
        return _mic_muted
    except:
        _mic_muted = not _mic_muted
        return _mic_muted


# ── Otomatik Görev Zamanlayıcı ────────────────────────────────────────────────
class AutomationScheduler:
    """Belirli saatte uygulama açma, bildirim gönderme gibi otomatik görevler"""
    def __init__(self, speak_func, msg_func):
        self.speak = speak_func
        self.msg = msg_func
        self.tasks = _load(AUTOMATION_FILE, [])
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def add_task(self, hour, minute, action, label="Otomatik Görev", repeat=True):
        self.tasks.append({
            "hour": hour, "minute": minute,
            "action": action, "label": label,
            "repeat": repeat, "active": True,
            "last_run": None
        })
        _save(AUTOMATION_FILE, self.tasks)

    def _loop(self):
        while self.running:
            try:
                now = datetime.datetime.now()
                for task in self.tasks:
                    if not task.get("active"): continue
                    if task["hour"] == now.hour and task["minute"] == now.minute:
                        last = task.get("last_run")
                        if last != now.strftime("%Y-%m-%d %H:%M"):
                            task["last_run"] = now.strftime("%Y-%m-%d %H:%M")
                            _save(AUTOMATION_FILE, self.tasks)
                            threading.Thread(
                                target=self._run_task,
                                args=(task,), daemon=True
                            ).start()
            except: pass
            time.sleep(10)

    def _run_task(self, task):
        action = task.get("action","")
        label = task.get("label","Görev")
        self.msg("SİSTEM", f"⏰ Otomatik görev: {label}")
        a = action.lower()
        if a.startswith("ac:"):
            app = a.replace("ac:","").strip()
            subprocess.Popen(app, shell=True)
        elif a.startswith("kapat"):
            subprocess.run(["shutdown","/s","/t","60"])
        elif a.startswith("mesaj:"):
            msg = a.replace("mesaj:","").strip()
            self.speak(msg)
        elif a.startswith("site:"):
            import webbrowser
            webbrowser.open(a.replace("site:","").strip())

    def list_tasks(self):
        return self.tasks

    def stop(self):
        self.running = False


# ── Otomatik Yedekleme ────────────────────────────────────────────────────────
class AutoBackup:
    def __init__(self, speak_func, msg_func):
        self.speak = speak_func
        self.msg = msg_func
        self.config = _load(BACKUP_FILE, {"folders":[], "dest":"", "last_backup": None})

    def add_folder(self, folder_path, dest_path):
        self.config["folders"].append({"src": folder_path, "dest": dest_path})
        _save(BACKUP_FILE, self.config)

    def backup_now(self):
        if not self.config["folders"]:
            self.msg("ANKA","Yedeklenecek klasör ayarlanmamış efendim.")
            return
        import shutil
        backed = 0
        for item in self.config["folders"]:
            src = item["src"]; dest = item["dest"]
            if os.path.exists(src):
                try:
                    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M")
                    dst = os.path.join(dest, f"backup_{ts}")
                    shutil.copytree(src, dst)
                    backed += 1
                except Exception as e:
                    self.msg("ANKA", f"Yedekleme hatası: {e}")
        self.config["last_backup"] = datetime.datetime.now().isoformat()
        _save(BACKUP_FILE, self.config)
        r = f"✓ {backed} klasör yedeklendi efendim."
        self.msg("ANKA", r); self.speak(r)


# ── Gmail Entegrasyonu (IMAP) ─────────────────────────────────────────────────
def get_latest_emails(gmail_user, gmail_password, count=5):
    try:
        import imaplib, email as emaillib
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(gmail_user, gmail_password)
        mail.select("inbox")
        _, data = mail.search(None, "ALL")
        ids = data[0].split()[-count:]
        emails = []
        for eid in reversed(ids):
            _, data = mail.fetch(eid, "(RFC822)")
            msg = emaillib.message_from_bytes(data[0][1])
            subject = msg["Subject"] or "(Konu yok)"
            sender = msg["From"] or "Bilinmeyen"
            emails.append({"subject": subject, "from": sender})
        mail.logout()
        return emails
    except Exception as e:
        return []


def send_email(gmail_user, gmail_password, to, subject, body):
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        msg = MIMEMultipart()
        msg["From"] = gmail_user
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_user, gmail_password)
            server.send_message(msg)
        return True
    except Exception as e:
        return str(e)


# ── Telefon Bildirimi (ntfy.sh ücretsiz) ─────────────────────────────────────
def send_phone_notification(topic, title, message):
    """
    ntfy.sh ücretsiz push bildirim servisi.
    Telefona ntfy uygulamasını indir, aynı topic adını gir.
    Topic: istediğin benzersiz bir isim (örn: 'yusuf-anka-2026')
    """
    try:
        requests.post(
            f"https://ntfy.sh/{topic}",
            data=message.encode("utf-8"),
            headers={"Title": title, "Priority": "default"},
            timeout=5
        )
        return True
    except Exception as e:
        return str(e)


# ── Webcam Fotoğraf ───────────────────────────────────────────────────────────
def take_webcam_photo():
    try:
        import cv2
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        time.sleep(0.5)
        ret, frame = cap.read()
        cap.release()
        if ret:
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            path = os.path.join(os.path.expanduser("~"), "Desktop", f"anka_foto_{ts}.jpg")
            cv2.imwrite(path, frame)
            return path
        return None
    except Exception as e:
        return None


# ── Bilgisayar Kapatma Zamanlayıcı ───────────────────────────────────────────
def schedule_shutdown(minutes):
    seconds = minutes * 60
    subprocess.run(["shutdown","/s",f"/t",str(seconds)])
    return True

def cancel_shutdown():
    subprocess.run(["shutdown","/a"])
    return True


# ── Komut İşleyici ───────────────────────────────────────────────────────────
class AdvancedCommandProcessor:
    def __init__(self, speak_func, msg_func, ollama,
                 scheduler=None, backup=None,
                 screen_recorder=None, ntfy_topic="anka-yusuf"):
        self.speak = speak_func
        self.msg = msg_func
        self.ollama = ollama
        self.scheduler = scheduler
        self.backup = backup
        self.recorder = screen_recorder
        self.ntfy_topic = ntfy_topic

    def process(self, text):
        t = text.lower().strip()
        import re, webbrowser

        # ── Parlaklık ────────────────────────────────────────────────────────
        if "parlaklık" in t:
            m = re.search(r'(\d+)', t)
            if m:
                level = min(100, max(0, int(m.group(1))))
                ok = set_brightness(level)
                r = f"✓ Parlaklık %{level} olarak ayarlandı efendim." if ok else "Parlaklık ayarlanamadı efendim."
                self.msg("ANKA", r); self.speak(r)
            else:
                current = get_brightness()
                r = f"Şu anki parlaklık: %{current}" if current >= 0 else "Parlaklık bilgisi alınamadı."
                self.msg("ANKA", r); self.speak(r)
            return True

        # ── Ekran Kaydı ──────────────────────────────────────────────────────
        if "ekran kaydı" in t or "kayıt başlat" in t:
            if self.recorder and self.recorder.start():
                r = "🔴 Ekran kaydı başladı efendim. 'Kaydı durdur' diyince durduracağım."
                self.msg("ANKA", r); self.speak(r)
            else:
                self.msg("ANKA","Ekran kaydı zaten aktif veya başlatılamadı.")
            return True

        if "kaydı durdur" in t or "kaydı bitir" in t:
            if self.recorder:
                path = self.recorder.stop()
                if path:
                    r = f"✓ Kayıt durduruldu, masaüstüne kaydedildi efendim."
                else:
                    r = "Aktif kayıt bulunamadı efendim."
                self.msg("ANKA", r); self.speak(r)
            return True

        # ── Fotoğraf Çek ─────────────────────────────────────────────────────
        if "fotoğraf çek" in t or "webcam" in t:
            self.msg("ANKA","📸 Fotoğraf çekiliyor...")
            def _photo():
                path = take_webcam_photo()
                if path:
                    r = f"✓ Fotoğraf masaüstüne kaydedildi efendim."
                    self.msg("ANKA", r); self.speak(r)
                    os.startfile(path)
                else:
                    self.msg("ANKA","Fotoğraf çekilemedi efendim.")
            threading.Thread(target=_photo, daemon=True).start()
            return True

        # ── Mikrofon ─────────────────────────────────────────────────────────
        if "mikrofonu kapat" in t or "mikrofonu aç" in t or "mikrofon" in t and "sessiz" in t:
            muted = toggle_microphone()
            r = f"✓ Mikrofon {'kapatıldı' if muted else 'açıldı'} efendim."
            self.msg("ANKA", r); self.speak(r)
            return True

        # ── Uygulama Ses Kontrolü ────────────────────────────────────────────
        if "spotify" in t and any(x in t for x in ["kıs","azalt","sessiz"]):
            set_app_volume("Spotify", 20)
            r = "✓ Spotify sesi kısıldı efendim."; self.msg("ANKA",r); self.speak(r)
            return True
        if "spotify" in t and any(x in t for x in ["artır","aç","yükselt"]):
            set_app_volume("Spotify", 80)
            r = "✓ Spotify sesi açıldı efendim."; self.msg("ANKA",r); self.speak(r)
            return True

        # ── Bilgisayar Kapatma Zamanlayıcı ───────────────────────────────────
        if "dakika sonra kapat" in t or "saat sonra kapat" in t:
            m = re.search(r'(\d+)', t)
            if m:
                n = int(m.group(1))
                unit = "saat" if "saat" in t else "dakika"
                mins = n * 60 if unit == "saat" else n
                schedule_shutdown(mins)
                r = f"✓ Bilgisayar {n} {unit} sonra kapanacak efendim."
                self.msg("ANKA", r); self.speak(r)
            return True

        if "kapatmayı iptal" in t or "kapatma iptal" in t:
            cancel_shutdown()
            r = "✓ Otomatik kapatma iptal edildi efendim."; self.msg("ANKA",r); self.speak(r)
            return True

        # ── Telefonuna Bildirim ───────────────────────────────────────────────
        if "telefona bildirim" in t or "telefona gönder" in t or "telefonu uyar" in t:
            msg_text = t.replace("telefona bildirim gönder","").replace("telefona gönder","").replace("telefonu uyar","").strip()
            if not msg_text: msg_text = "Anka'dan bildirim!"
            def _notif():
                ok = send_phone_notification(self.ntfy_topic, "ANKA", msg_text)
                r = "✓ Telefonuna bildirim gönderildi efendim!" if ok is True else f"Bildirim gönderilemedi: {ok}"
                self.msg("ANKA", r); self.speak(r)
            threading.Thread(target=_notif, daemon=True).start()
            return True

        # ── Otomatik Görev Ekle ───────────────────────────────────────────────
        if "her sabah" in t or "otomatik aç" in t or "her gün" in t:
            m = re.search(r'(\d{1,2})[:\.](\d{2})', t)
            if m and self.scheduler:
                h, mn = int(m.group(1)), int(m.group(2))
                apps = {"chrome":"chrome","spotify":"spotify:","youtube":"https://youtube.com",
                        "tarayıcı":"chrome","haber":"https://haberler.com"}
                action = "mesaj:Günaydın efendim!"
                for app, cmd in apps.items():
                    if app in t:
                        action = f"ac:{cmd}"
                        break
                label = t.replace(m.group(0),"").replace("her sabah","").replace("her gün","").replace("otomatik aç","").strip()
                self.scheduler.add_task(h, mn, action, label or "Otomatik görev")
                r = f"✓ Saat {h}:{mn:02d}'de otomatik görev ayarlandı efendim."
                self.msg("ANKA", r); self.speak(r)
            return True

        if "otomatik görevlerim" in t:
            if self.scheduler:
                tasks = self.scheduler.list_tasks()
                if not tasks:
                    r = "Hiç otomatik görev yok efendim."
                else:
                    r = "⚙️ Otomatik görevler:\n" + "\n".join(
                        f"• {t['hour']}:{t['minute']:02d} — {t['label']}" for t in tasks if t.get('active'))
                self.msg("ANKA", r); self.speak(r)
            return True

        # ── Yedekleme ────────────────────────────────────────────────────────
        if "yedekle" in t or "yedekleme yap" in t:
            if self.backup:
                threading.Thread(target=self.backup.backup_now, daemon=True).start()
                self.msg("ANKA","⏳ Yedekleme başladı efendim...")
            return True

        # ── Zoom/Teams Aç ────────────────────────────────────────────────────
        if "zoom" in t and "aç" in t:
            subprocess.Popen("zoom", shell=True)
            r = "✓ Zoom açıldı efendim."; self.msg("ANKA",r); self.speak(r)
            return True
        if "teams" in t and "aç" in t:
            subprocess.Popen("ms-teams:", shell=True)
            r = "✓ Teams açıldı efendim."; self.msg("ANKA",r); self.speak(r)
            return True

        # ── Ses Çıkaran Uygulamalar ───────────────────────────────────────────
        if "hangi uygulama ses" in t or "ses çıkaran" in t:
            info = get_audio_sessions()
            self.msg("ANKA", f"🔊 Açık uygulamalar:\n{info[:500]}")
            self.speak("İşte açık uygulamalar efendim.")
            return True

        # ── Gmail ────────────────────────────────────────────────────────────
        if "maillerimi oku" in t or "yeni mail" in t or "gelen kutusu" in t:
            from anka_config import BASE_DIR
            cfg_path = os.path.join(BASE_DIR, "anka_gmail.json")
            cfg = _load(cfg_path, {})
            if not cfg.get("user") or not cfg.get("password"):
                r = ("Gmail için anka_gmail.json dosyasına bilgilerini eklemen lazım efendim.\n"
                     "Şu formatta: {\"user\": \"mail@gmail.com\", \"password\": \"uygulama_sifresi\"}\n"
                     "Gmail'de 'Uygulama Şifresi' oluşturman gerekiyor (2FA aktifken).")
                self.msg("ANKA", r); self.speak("Gmail bilgileri ayarlanmamış efendim.")
                return True
            def _mail():
                emails = get_latest_emails(cfg["user"], cfg["password"], 5)
                if not emails:
                    self.msg("ANKA","Mail alınamadı efendim.")
                    return
                result = "📧 Son 5 mailiniz:\n" + "\n".join(
                    f"• {e['subject'][:40]} ({e['from'][:25]})" for e in emails)
                self.msg("ANKA", result)
                self.speak(f"{len(emails)} yeni mailiniz var efendim.")
            threading.Thread(target=_mail, daemon=True).start()
            return True

        return False
