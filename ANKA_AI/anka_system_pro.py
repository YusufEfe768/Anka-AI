# ── ANKA SİSTEM PRO MODÜLü ───────────────────────────────────────────────────
# Yazıcı, pencere yönetimi, dosya işlemleri, pano geçmişi, takip ve daha fazlası

try:
    import pyperclip
except ImportError:
    class _PyClip:
        def copy(self,x):pass
        def paste(self):return ""
    pyperclip=_PyClip()
try:
    import pyautogui
except ImportError:
    pyautogui=None
import subprocess, os, time, threading, datetime, json, random, zipfile, shutil
import psutil
from anka_config import BASE_DIR

ACTIVITY_FILE = os.path.join(BASE_DIR, "anka_activity.json")
CLIPBOARD_FILE = os.path.join(BASE_DIR, "anka_clipboard_history.json")

# ── Pano Geçmişi ──────────────────────────────────────────────────────────────
class ClipboardMonitor:
    def __init__(self, max_items=20):
        self.max_items = max_items
        self.last_value = ""
        self.running = True
        self.history = self._load()
        threading.Thread(target=self._loop, daemon=True).start()

    def _load(self):
        try:
            if os.path.exists(CLIPBOARD_FILE):
                with open(CLIPBOARD_FILE,"r",encoding="utf-8") as f: return json.load(f)
        except: pass
        return []

    def _save(self):
        try:
            with open(CLIPBOARD_FILE,"w",encoding="utf-8") as f:
                json.dump(self.history[-self.max_items:], f, ensure_ascii=False, indent=2)
        except: pass

    def _loop(self):
        while self.running:
            try:
                current = pyperclip.paste()
                if current and current != self.last_value and len(current) < 2000:
                    self.last_value = current
                    self.history.append({"text": current, "time": datetime.datetime.now().isoformat()})
                    if len(self.history) > self.max_items:
                        self.history = self.history[-self.max_items:]
                    self._save()
            except: pass
            time.sleep(1.5)

    def get_history(self, limit=10):
        return self.history[-limit:][::-1]

    def stop(self):
        self.running = False


# ── Aktivite Takibi ───────────────────────────────────────────────────────────
class ActivityTracker:
    """Hangi uygulamada ne kadar süre geçirildiğini takip eder"""
    def __init__(self):
        self.running = True
        self.data = self._load()
        threading.Thread(target=self._loop, daemon=True).start()

    def _load(self):
        try:
            if os.path.exists(ACTIVITY_FILE):
                with open(ACTIVITY_FILE,"r",encoding="utf-8") as f: return json.load(f)
        except: pass
        return {}

    def _save(self):
        try:
            with open(ACTIVITY_FILE,"w",encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except: pass

    def _get_active_window(self):
        try:
            import ctypes
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
            buf = ctypes.create_unicode_buffer(length + 1)
            ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
            return buf.value or "Bilinmeyen"
        except:
            return "Bilinmeyen"

    def _loop(self):
        while self.running:
            try:
                today = datetime.date.today().isoformat()
                window = self._get_active_window()
                # Pencere başlığından uygulama adını basitleştir
                app = window.split(" - ")[-1].split(" — ")[-1][:40] if window else "Bilinmeyen"
                if today not in self.data:
                    self.data[today] = {}
                self.data[today][app] = self.data[today].get(app, 0) + 5
                # 30 günden eski kayıtları temizle
                if len(self.data) > 30:
                    oldest = sorted(self.data.keys())[0]
                    del self.data[oldest]
                self._save()
            except: pass
            time.sleep(5)

    def get_today_summary(self, top=5):
        today = datetime.date.today().isoformat()
        day_data = self.data.get(today, {})
        sorted_apps = sorted(day_data.items(), key=lambda x: -x[1])[:top]
        return [(app, seconds//60) for app, seconds in sorted_apps]

    def stop(self):
        self.running = False


# ── Auto-Lock (Hareketsizlik Kilidi) ─────────────────────────────────────────
class AutoLocker:
    def __init__(self, timeout_minutes=15, enabled=False):
        self.timeout = timeout_minutes * 60
        self.enabled = enabled
        self.running = True
        try:
            self.last_pos = pyautogui.position() if pyautogui else (0, 0)
        except Exception:
            self.last_pos = (0, 0)
        self.last_active = time.time()
        threading.Thread(target=self._loop, daemon=True).start()

    def set_enabled(self, val):
        self.enabled = val
        self.last_active = time.time()

    def set_timeout(self, minutes):
        self.timeout = minutes * 60

    def _loop(self):
        while self.running:
            try:
                if self.enabled:
                    pos = pyautogui.position()
                    if pos != self.last_pos:
                        self.last_pos = pos
                        self.last_active = time.time()
                    elif time.time() - self.last_active > self.timeout:
                        subprocess.run(["rundll32.exe","user32.dll,LockWorkStation"])
                        self.last_active = time.time()
            except: pass
            time.sleep(10)

    def stop(self):
        self.running = False


# ── Komut İşleyici Genişletme ─────────────────────────────────────────────────
class SystemProCommands:
    def __init__(self, speak_func, msg_func, ollama, clipboard_mon=None, activity_tracker=None, auto_locker=None):
        self.speak = speak_func
        self.msg = msg_func
        self.ollama = ollama
        self.clipboard = clipboard_mon
        self.activity = activity_tracker
        self.locker = auto_locker

    def process(self, text):
        t = text.lower().strip()

        # ── Yazıcı: Dosya Yazdır ─────────────────────────────────────────────
        if "yazdır" in t and "dosya" in t:
            r = "Hangi dosyayı yazdırmak istersiniz? Dosya gezgininden dosyaya sağ tıklayıp 'Yazdır' seçeneğini de kullanabilirsiniz efendim."
            self.msg("ANKA", r); self.speak(r); return True

        if "yazıcı durumu" in t or "mürekkep" in t:
            subprocess.Popen("control printers", shell=True)
            r = "✓ Yazıcı ve aygıtlar penceresi açıldı, durumu oradan görebilirsiniz efendim."
            self.msg("ANKA", r); self.speak(r); return True

        # ── Pencere Yönetimi ─────────────────────────────────────────────────
        if "pencereleri küçült" in t or "tümünü küçült" in t:
            pyautogui.hotkey('win','d')
            r = "✓ Tüm pencereler küçültüldü efendim."; self.msg("ANKA",r); self.speak(r); return True

        if "pencereleri yan yana" in t or "yan yana diz" in t:
            pyautogui.hotkey('win','left')
            r = "✓ Pencere düzenlendi efendim."; self.msg("ANKA",r); self.speak(r); return True

        if "kapat" in t and any(app in t for app in ["chrome","firefox","spotify","discord","whatsapp"]):
            for app in ["chrome","firefox","spotify","discord","whatsapp"]:
                if app in t:
                    proc_name = {"chrome":"chrome.exe","firefox":"firefox.exe",
                                 "spotify":"Spotify.exe","discord":"Discord.exe",
                                 "whatsapp":"WhatsApp.exe"}.get(app)
                    if proc_name:
                        subprocess.run(["taskkill","/IM",proc_name,"/F"], capture_output=True)
                        r = f"✓ {app.capitalize()} kapatıldı efendim."
                        self.msg("ANKA",r); self.speak(r); return True

        if "masaüstüne geç" in t or "sanal masaüstü" in t:
            import re
            m = re.search(r'(\d+)', t)
            if m:
                num = int(m.group(1))
                key = 'left' if num == 1 else 'right'
                pyautogui.hotkey('ctrl','win',key)
                r = f"✓ Masaüstü {num}'e geçildi efendim."
                self.msg("ANKA",r); self.speak(r); return True

        # ── Dosya & Klasör ───────────────────────────────────────────────────
        if "klasör oluştur" in t or "yeni klasör" in t:
            name = t.replace("klasör oluştur","").replace("yeni klasör","").replace("oluştur","").strip()
            if not name: name = f"Yeni Klasör {int(time.time())}"
            path = os.path.join(os.path.expanduser("~"), "Desktop", name)
            try:
                os.makedirs(path, exist_ok=True)
                r = f"✓ '{name}' klasörü masaüstünde oluşturuldu efendim."
            except Exception as e:
                r = f"Klasör oluşturulamadı: {e}"
            self.msg("ANKA",r); self.speak(r); return True

        if "indirilenler" in t and ("düzenle" in t or "organize" in t):
            threading.Thread(target=self._organize_downloads, daemon=True).start()
            return True

        if "sıkıştır" in t and "klasör" in t:
            r = "Hangi klasörü sıkıştırmak istediğinizi tam yol ile söyleyin efendim."
            self.msg("ANKA",r); self.speak(r); return True

        # ── Pano Geçmişi ─────────────────────────────────────────────────────
        if "panodaki" in t or "pano geçmişi" in t:
            if self.clipboard:
                history = self.clipboard.get_history(5)
                if not history:
                    r = "Pano geçmişiniz boş efendim."
                else:
                    items = "\n".join(f"• {h['text'][:50]}{'...' if len(h['text'])>50 else ''}" for h in history)
                    r = f"📋 Son kopyalananlar:\n{items}"
                self.msg("ANKA",r); self.speak("İşte pano geçmişiniz efendim.")
            return True

        # ── Mini Not Penceresi ───────────────────────────────────────────────
        if "hızlı not" in t or "mini not" in t:
            self._quick_note_window()
            return True

        # ── Wallpaper Değiştir ───────────────────────────────────────────────
        if "duvar kağıdı" in t or "wallpaper" in t:
            r = "Duvar kağıdı değiştirme için Windows Ayarlar > Kişiselleştirme > Arka Plan'ı kullanabilirsiniz efendim."
            self.msg("ANKA",r); self.speak(r); return True

        # ── ASCII Art ────────────────────────────────────────────────────────
        if "ascii" in t:
            word = t.replace("ascii art yap","").replace("ascii","").strip() or "ANKA"
            reply = self.ollama.chat(f"'{word}' kelimesi için basit bir ASCII art oluştur, sadece ASCII art'ı yaz.")
            self.msg("ANKA", reply); return True

        # ── Aktivite Raporu ──────────────────────────────────────────────────
        if any(x in t for x in ["en çok kullandığım","aktivite raporu","ekran kullanım","hangi uygulamada"]):
            if self.activity:
                summary = self.activity.get_today_summary(5)
                if not summary:
                    r = "Henüz yeterli aktivite verisi toplanmadı efendim."
                else:
                    items = "\n".join(f"• {app}: {minutes} dakika" for app, minutes in summary)
                    r = f"📊 Bugünkü en çok kullandığınız uygulamalar:\n{items}"
                self.msg("ANKA", r); self.speak("İşte günlük kullanım raporunuz efendim.")
            return True

        # ── Otomatik Kilit Ayarı ─────────────────────────────────────────────
        if "otomatik kilit" in t and "aç" in t:
            if self.locker:
                self.locker.set_enabled(True)
                r = "✓ Otomatik ekran kilidi açıldı. 15 dakika hareketsizlikte ekran kilitlenecek efendim."
                self.msg("ANKA",r); self.speak(r)
            return True

        if "otomatik kilit" in t and "kapat" in t:
            if self.locker:
                self.locker.set_enabled(False)
                r = "✓ Otomatik ekran kilidi kapatıldı efendim."
                self.msg("ANKA",r); self.speak(r)
            return True

        # ── Sekme Sayısı ─────────────────────────────────────────────────────
        if "kaç sekmem" in t or "sekme sayısı" in t:
            r = "Sekme sayısını doğrudan göremiyorum efendim, ama Chrome'da Ctrl+Shift+A ile tüm sekmeleri görebilirsiniz."
            self.msg("ANKA",r); self.speak(r); return True

        # ── Renk Paleti ──────────────────────────────────────────────────────
        if "renk paleti" in t:
            colors = [f"#{random.randint(0,0xFFFFFF):06x}" for _ in range(5)]
            r = "🎨 Renk Paleti:\n" + "\n".join(f"• {c}" for c in colors)
            pyperclip.copy(", ".join(colors))
            self.msg("ANKA", r + "\n(Panoya kopyalandı)")
            self.speak("Renk paleti oluşturuldu ve panoya kopyalandı efendim.")
            return True

        return False

    def _organize_downloads(self):
        downloads = os.path.join(os.path.expanduser("~"), "Downloads")
        if not os.path.exists(downloads):
            self.msg("ANKA","İndirilenler klasörü bulunamadı."); return

        categories = {
            "Resimler": [".jpg",".jpeg",".png",".gif",".bmp",".svg",".webp"],
            "Belgeler": [".pdf",".doc",".docx",".txt",".xlsx",".pptx"],
            "Videolar": [".mp4",".avi",".mkv",".mov"],
            "Müzik": [".mp3",".wav",".flac"],
            "Sıkıştırılmış": [".zip",".rar",".7z"],
            "Programlar": [".exe",".msi"],
        }

        moved = 0
        try:
            for fname in os.listdir(downloads):
                fpath = os.path.join(downloads, fname)
                if os.path.isfile(fpath):
                    ext = os.path.splitext(fname)[1].lower()
                    for cat, exts in categories.items():
                        if ext in exts:
                            cat_dir = os.path.join(downloads, cat)
                            os.makedirs(cat_dir, exist_ok=True)
                            try:
                                shutil.move(fpath, os.path.join(cat_dir, fname))
                                moved += 1
                            except: pass
                            break
            r = f"✓ İndirilenler klasörü düzenlendi. {moved} dosya kategorilere ayrıldı efendim."
        except Exception as e:
            r = f"Düzenleme sırasında hata: {e}"
        self.msg("ANKA", r); self.speak(r)

    def _quick_note_window(self):
        """Basit bir sticky-note penceresi açar"""
        try:
            import tkinter as tk
            win = tk.Toplevel()
            win.title("Anka Hızlı Not")
            win.geometry("300x200+100+100")
            win.configure(bg="#1c1c2e")
            win.attributes("-topmost", True)
            text = tk.Text(win, bg="#252540", fg="#e0e0f0", font=("Segoe UI",11),
                           insertbackground="#00e5cc", relief="flat", padx=10, pady=10)
            text.pack(fill="both", expand=True, padx=8, pady=8)
            text.focus()
        except Exception as e:
            print(f"Hızlı not penceresi açılamadı: {e}")
