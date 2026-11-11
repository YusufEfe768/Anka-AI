# ── ANKA JARVIS EKSTRALARı ───────────────────────────────────────────────────
# Jarvis zip'inden alınan özellikler: WhatsApp, Takvim, Ekran Analizi,
# YouTube, Medya Oynatma, Tarayıcı Kontrolü, Bellek Yönetimi
try:
    import pyautogui
except ImportError:
    pyautogui=None
import json, os, time, threading, datetime, subprocess, webbrowser
import requests, re, urllib.parse
from anka_config import BASE_DIR

MEMORY_FILE   = os.path.join(BASE_DIR, "jarvis_memory.json")
PHONEBOOK_FILE= os.path.join(BASE_DIR, "jarvis_phonebook.json")

def _load(p, d):
    try:
        if os.path.exists(p):
            with open(p,"r",encoding="utf-8") as f: return json.load(f)
    except: pass
    return d

def _save(p, d):
    try:
        with open(p,"w",encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
    except: pass


# ── Bellek Yönetimi (Jarvis'ten) ─────────────────────────────────────────────
class JarvisMemoryManager:
    def __init__(self, msg_func, speak_func):
        self.msg   = msg_func
        self.speak = speak_func

    def save_memory(self, category, key, value):
        mem = _load(MEMORY_FILE, {})
        if category not in mem:
            mem[category] = {}
        mem[category][key] = {"value": value, "updated": datetime.datetime.now().isoformat()}
        _save(MEMORY_FILE, mem)

    def load_memory(self, category=None, key=None):
        mem = _load(MEMORY_FILE, {})
        if category and key:
            return mem.get(category, {}).get(key, {}).get("value")
        elif category:
            return mem.get(category, {})
        return mem

    def delete_memory(self, category, key):
        mem = _load(MEMORY_FILE, {})
        if category in mem and key in mem[category]:
            del mem[category][key]
            _save(MEMORY_FILE, mem)
            return True
        return False

    def format_for_prompt(self):
        mem = _load(MEMORY_FILE, {})
        if not mem: return ""
        lines = ["[KULLANICI HAFIZASI]"]
        for cat, items in mem.items():
            if isinstance(items, dict):
                for k, v in items.items():
                    val = v.get("value", v) if isinstance(v, dict) else v
                    lines.append(f"  {cat}/{k}: {val}")
        return "\n".join(lines)

    def show_all(self):
        mem = _load(MEMORY_FILE, {})
        if not mem:
            return "Hafıza boş efendim."
        r = "🧠 JARVIS HAFIZASI\n" + "═"*30 + "\n"
        for cat, items in mem.items():
            r += f"\n[{cat.upper()}]\n"
            if isinstance(items, dict):
                for k, v in items.items():
                    val = v.get("value", v) if isinstance(v, dict) else v
                    r += f"  • {k}: {val}\n"
        return r


# ── WhatsApp Entegrasyonu (Jarvis'ten) ───────────────────────────────────────
class WhatsAppIntegration:
    def __init__(self, msg_func, speak_func):
        self.msg   = msg_func
        self.speak = speak_func

    def _normalize_phone(self, phone):
        digits = re.sub(r"\D+", "", phone or "")
        if len(digits) == 11 and digits.startswith("0"):
            digits = "90" + digits[1:]
        elif len(digits) == 10:
            digits = "90" + digits
        return digits

    def save_contact(self, name, phone, alias=""):
        book = _load(PHONEBOOK_FILE, {})
        book[name.lower()] = {
            "name": name, "phone": self._normalize_phone(phone),
            "alias": alias, "added": datetime.datetime.now().isoformat()
        }
        _save(PHONEBOOK_FILE, book)
        return f"✓ {name} rehbere kaydedildi: +{self._normalize_phone(phone)}"

    def find_contact(self, name):
        book = _load(PHONEBOOK_FILE, {})
        name_l = name.lower()
        for key, contact in book.items():
            if (name_l in key or name_l in contact.get("name","").lower() or
                name_l in contact.get("alias","").lower()):
                return contact
        return None

    def send_message(self, recipient, message, send_now=False):
        phone = None
        contact = self.find_contact(recipient)
        if contact:
            phone = contact["phone"]
        elif re.search(r'\d{10,}', recipient):
            phone = self._normalize_phone(re.sub(r'\D+','',recipient))

        if not phone:
            return f"'{recipient}' rehberde bulunamadı. Önce 'whatsapp kaydet {recipient} [numara]' kullanın."

        encoded = urllib.parse.quote(message)
        # Desktop URI
        try:
            subprocess.Popen(f'start "" "whatsapp://send?phone={phone}&text={encoded}"', shell=True)
        except:
            webbrowser.open(f"https://web.whatsapp.com/send?phone={phone}&text={encoded}")

        if send_now:
            time.sleep(3)
            try: pyautogui.press("enter")
            except: pass
            return f"✓ '{recipient}' kişisine mesaj gönderildi efendim."
        return f"✓ WhatsApp '{recipient}' için açıldı. Enter ile gönder efendim."

    def list_contacts(self):
        book = _load(PHONEBOOK_FILE, {})
        if not book:
            return "Kayıtlı WhatsApp kişisi yok efendim."
        r = "📱 WhatsApp Rehberi:\n"
        for key, c in book.items():
            r += f"• {c['name']}: +{c['phone']}\n"
        return r


# ── Google Takvim Entegrasyonu (Jarvis'ten) ──────────────────────────────────
class GoogleCalendarIntegration:
    def __init__(self, msg_func, speak_func):
        self.msg   = msg_func
        self.speak = speak_func

    def open_calendar(self):
        webbrowser.open("https://calendar.google.com")

    def add_event(self, title, start_iso, end_iso="", location="", notes=""):
        params = {"text": title, "action": "TEMPLATE"}
        if start_iso:
            date_part = start_iso.replace(":","").replace("-","").split("T")[0]
            time_part = start_iso.split("T")[1].replace(":","")[:4] if "T" in start_iso else ""
            if time_part:
                params["dates"] = f"{date_part}T{time_part}00/{date_part}T{time_part}00"
            else:
                params["dates"] = f"{date_part}/{date_part}"
        if location: params["location"] = location
        if notes: params["details"] = notes
        url = "https://calendar.google.com/calendar/render?" + urllib.parse.urlencode(params)
        webbrowser.open(url)
        return f"✓ Google Calendar'da '{title}' etkinliği açıldı efendim."

    def view_events(self, query="today"):
        queries = {
            "bugün": "https://calendar.google.com/calendar/r/day",
            "today": "https://calendar.google.com/calendar/r/day",
            "hafta": "https://calendar.google.com/calendar/r/week",
            "week":  "https://calendar.google.com/calendar/r/week",
            "ay":    "https://calendar.google.com/calendar/r/month",
            "month": "https://calendar.google.com/calendar/r/month",
        }
        url = queries.get(query.lower(), "https://calendar.google.com")
        webbrowser.open(url)
        return f"✓ Google Calendar ({query}) tarayıcıda açıldı efendim."


# ── Microsoft To-Do Hatırlatıcı (Jarvis'ten) ─────────────────────────────────
class MicrosoftReminders:
    def __init__(self, msg_func, speak_func):
        self.msg   = msg_func
        self.speak = speak_func

    def add_reminder(self, title, due_iso="", notes="", priority="normal"):
        # Windows 10/11 To-Do entegrasyonu
        try:
            ps_cmd = (
                f'$app = New-Object -ComObject "outlook.application"; '
                f'$task = $app.CreateItem(3); '
                f'$task.Subject = "{title}"; '
                f'$task.Body = "{notes}"; '
                f'$task.Save()'
            )
            subprocess.run(["powershell","-Command", ps_cmd],
                          capture_output=True, timeout=10)
        except: pass
        # ntfy ile saate de gönder
        try:
            requests.post("https://ntfy.sh/anka-yusuf-2026",
                data=f"📋 Hatırlatıcı: {title}".encode(),
                headers={"Title":"Anka Hatırlatıcı"}, timeout=3)
        except: pass
        return f"✓ '{title}' hatırlatıcısı eklendi efendim."

    def open_todo(self):
        try:
            subprocess.Popen("ms-to-do://", shell=True)
        except:
            webbrowser.open("https://to-do.microsoft.com")
        return "✓ Microsoft To-Do açıldı efendim."


# ── Ekran Analizi (Jarvis'ten — Gemini Vision yerine OpenRouter) ─────────────
class ScreenAnalyzer:
    def __init__(self, ollama, msg_func, speak_func):
        self.ollama = ollama
        self.msg    = msg_func
        self.speak  = speak_func

    def analyze_active_window(self, question="Ekranda ne var?"):
        def _a():
            try:
                import tempfile, base64
                path = os.path.join(tempfile.gettempdir(), "anka_screen_analysis.png")
                pyautogui.screenshot(path)

                # Aktif pencere başlığı
                try:
                    import ctypes
                    hwnd = ctypes.windll.user32.GetForegroundWindow()
                    length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
                    buf = ctypes.create_unicode_buffer(length+1)
                    ctypes.windll.user32.GetWindowTextW(hwnd, buf, length+1)
                    window_title = buf.value
                except:
                    window_title = "Bilinmeyen pencere"

                # OpenRouter Vision API
                # Local AI modunda sadece pencere başlığını kullan
                result = self.ollama.chat(
                    f"Aktif pencere '{window_title}'. "
                    f"Bu uygulama hakkında {question}",
                    system_override="Ekran asistanı. Yardımcı ol.")

                self.msg("ANKA", f"👁️ Ekran Analizi:\n{result}")
                self.speak(result[:200])
            except Exception as e:
                self.msg("ANKA", f"Ekran analizi hatası: {e}")
        threading.Thread(target=_a, daemon=True).start()


# ── YouTube Kanal Raporu (Jarvis'ten) ────────────────────────────────────────
class YouTubeChannelReport:
    def __init__(self, msg_func, speak_func):
        self.msg   = msg_func
        self.speak = speak_func

    def get_report(self, handle_or_url, query="genel"):
        def _r():
            try:
                # YouTube Data API (ücretsiz tier)
                # Handle'dan channel ID bul
                search_url = f"https://www.youtube.com/@{handle_or_url.replace('@','')}"
                webbrowser.open(search_url)
                self.msg("ANKA",
                    f"📊 YouTube Kanal Raporu\n"
                    f"• Kanal: {handle_or_url}\n"
                    f"• Tarayıcıda açıldı efendim.\n"
                    f"• YouTube Studio için: https://studio.youtube.com")
                self.speak("YouTube kanalı açıldı efendim.")
            except Exception as e:
                self.msg("ANKA", f"YouTube raporu hatası: {e}")
        threading.Thread(target=_r, daemon=True).start()


# ── Medya Oynatma (Jarvis'ten) ───────────────────────────────────────────────
class MediaPlayer:
    def __init__(self, msg_func, speak_func):
        self.msg   = msg_func
        self.speak = speak_func

    def play(self, query, provider="auto", autoplay=True):
        if provider == "spotify" or (provider == "auto" and "spotify" in query.lower()):
            self._play_spotify(query)
        elif provider == "youtube" or provider == "auto":
            self._play_youtube(query, autoplay)

    def _play_youtube(self, query, autoplay=True):
        if autoplay:
            # YouTube'da direkt ara ve aç
            encoded = urllib.parse.quote(query)
            webbrowser.open(f"https://www.youtube.com/results?search_query={encoded}")
        else:
            webbrowser.open(f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}")
        r = f"▶️ YouTube'da '{query}' açıldı efendim."
        self.msg("ANKA", r); self.speak(r)

    def _play_spotify(self, query):
        try:
            encoded = urllib.parse.quote(query)
            subprocess.Popen(f'start "" "spotify:search:{encoded}"', shell=True)
        except:
            webbrowser.open(f"https://open.spotify.com/search/{urllib.parse.quote(query)}")
        r = f"🎵 Spotify'da '{query}' açıldı efendim."
        self.msg("ANKA", r); self.speak(r)


# ── Tarayıcı Kontrolü (Jarvis'ten) ───────────────────────────────────────────
class BrowserController:
    def __init__(self, msg_func, speak_func):
        self.msg   = msg_func
        self.speak = speak_func

    def open_url(self, url):
        if not url.startswith("http"):
            url = "https://" + url
        webbrowser.open(url)
        r = f"✓ {url} açıldı efendim."
        self.msg("ANKA", r); self.speak(r)

    def search(self, query, engine="google"):
        engines = {
            "google": f"https://www.google.com/search?q={urllib.parse.quote(query)}",
            "bing":   f"https://www.bing.com/search?q={urllib.parse.quote(query)}",
            "youtube":f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}",
            "wikipedia":f"https://tr.wikipedia.org/wiki/Special:Search/{urllib.parse.quote(query)}",
        }
        url = engines.get(engine, engines["google"])
        webbrowser.open(url)
        r = f"✓ {engine.capitalize()}'da '{query}' arandı efendim."
        self.msg("ANKA", r); self.speak(r)

    def open_incognito(self, url=""):
        try:
            if url:
                subprocess.Popen(f'start chrome --incognito "{url}"', shell=True)
            else:
                subprocess.Popen("start chrome --incognito", shell=True)
            r = "✓ Gizli sekme açıldı efendim."
            self.msg("ANKA", r); self.speak(r)
        except:
            self.msg("ANKA", "Chrome bulunamadı efendim.")


# ── Komut İşleyici ────────────────────────────────────────────────────────────
class JarvisExtraCommandProcessor:
    def __init__(self, speak_func, msg_func, ollama):
        self.speak   = speak_func
        self.msg     = msg_func
        self.ollama  = ollama
        self.memory  = JarvisMemoryManager(msg_func, speak_func)
        self.whatsapp= WhatsAppIntegration(msg_func, speak_func)
        self.calendar= GoogleCalendarIntegration(msg_func, speak_func)
        self.reminder= MicrosoftReminders(msg_func, speak_func)
        self.screen  = ScreenAnalyzer(ollama, msg_func, speak_func)
        self.yt      = YouTubeChannelReport(msg_func, speak_func)
        self.media   = MediaPlayer(msg_func, speak_func)
        self.browser = BrowserController(msg_func, speak_func)

    def process(self, text):
        t = text.lower().strip()

        # ── WhatsApp ──────────────────────────────────────────────────────────
        if "whatsapp gönder" in t or "whatsapp yaz" in t:
            m = re.search(r'(?:whatsapp gönder|whatsapp yaz)\s+(\w+)\s+(.+)', t)
            if m:
                recipient, message = m.group(1), m.group(2)
                send_now = "hemen" in t or "gönder" in t
                r = self.whatsapp.send_message(recipient, message, send_now)
                self.msg("ANKA", r); self.speak(r)
            return True

        if "whatsapp kaydet" in t:
            parts = t.replace("whatsapp kaydet","").strip().split()
            if len(parts) >= 2:
                name, phone = parts[0], parts[1]
                r = self.whatsapp.save_contact(name, phone)
                self.msg("ANKA", r); self.speak(r)
            return True

        if "whatsapp rehber" in t or "whatsapp kişiler" in t:
            r = self.whatsapp.list_contacts()
            self.msg("ANKA", r); self.speak(r)
            return True

        # ── Takvim ────────────────────────────────────────────────────────────
        if "takvim aç" in t or "google takvim" in t:
            query = "today"
            for q in ["hafta","week","ay","month","bugün","today"]:
                if q in t: query = q; break
            r = self.calendar.view_events(query)
            self.msg("ANKA", r); self.speak(r)
            return True

        if "takvime ekle" in t or "etkinlik ekle" in t:
            content = t.replace("takvime ekle","").replace("etkinlik ekle","").strip()
            time_m = re.search(r'(\d{1,2})[:\.](\d{2})', text)
            months = {"ocak":"01","şubat":"02","mart":"03","nisan":"04",
                     "mayıs":"05","haziran":"06","temmuz":"07","ağustos":"08",
                     "eylül":"09","ekim":"10","kasım":"11","aralık":"12"}
            month_found = next((m for m in months if m in t), None)
            day_m = re.search(r'(\d{1,2})', content)
            if month_found and day_m:
                year = datetime.date.today().year
                start_iso = (f"{year}-{months[month_found]}-{day_m.group(1).zfill(2)}"
                           + (f"T{time_m.group(1).zfill(2)}:{time_m.group(2)}" if time_m else ""))
                title = re.sub(r'\d+', '', content).replace(month_found,'').strip()
                r = self.calendar.add_event(title or content, start_iso)
            else:
                r = self.calendar.add_event(content,
                    datetime.datetime.now().strftime("%Y-%m-%dT%H:%M"))
            self.msg("ANKA", r); self.speak(r)
            return True

        # ── To-Do Hatırlatıcı ─────────────────────────────────────────────────
        if "todo ekle" in t or "to-do ekle" in t or "yapılacak ekle" in t:
            title = t.replace("todo ekle","").replace("to-do ekle","").replace("yapılacak ekle","").strip()
            if title:
                r = self.reminder.add_reminder(title)
                self.msg("ANKA", r); self.speak(r)
            return True

        if "todo aç" in t or "to-do aç" in t:
            r = self.reminder.open_todo()
            self.msg("ANKA", r); self.speak(r)
            return True

        # ── Ekran Analizi ─────────────────────────────────────────────────────
        if "ekranı analiz et" in t or "ekranda ne var" in t or "ekranı oku" in t:
            question = t.replace("ekranı analiz et","").replace("ekranda ne var","").replace("ekranı oku","").strip()
            self.screen.analyze_active_window(question or "Ekranda ne görüyorsun?")
            return True

        # ── YouTube Kanal Raporu ──────────────────────────────────────────────
        if "youtube kanal raporu" in t or "yt kanal" in t:
            handle = t.replace("youtube kanal raporu","").replace("yt kanal","").strip()
            if handle:
                self.yt.get_report(handle)
            return True

        # ── Medya Oynatma ─────────────────────────────────────────────────────
        if "youtube'da çal" in t or "youtube çal" in t or "videosunu aç" in t:
            query = t.replace("youtube'da çal","").replace("youtube çal","").replace("videosunu aç","").strip()
            if query: self.media.play(query, "youtube")
            return True

        if "spotify'da çal" in t or "spotify aç" in t:
            query = t.replace("spotify'da çal","").replace("spotify aç","").strip()
            if query: self.media.play(query, "spotify")
            return True

        if "müzik çal" in t or "şarkı çal" in t:
            query = t.replace("müzik çal","").replace("şarkı çal","").strip()
            if query: self.media.play(query, "auto")
            return True

        # ── Tarayıcı Kontrolü ─────────────────────────────────────────────────
        if t.startswith("aç ") and ("http" in t or ".com" in t or ".org" in t or ".net" in t):
            url = t.replace("aç ","").strip()
            self.browser.open_url(url)
            return True

        if "google'da ara" in t or "internette ara" in t:
            query = t.replace("google'da ara","").replace("internette ara","").strip()
            if query: self.browser.search(query, "google")
            return True

        if "youtube'da ara" in t:
            query = t.replace("youtube'da ara","").strip()
            if query: self.browser.search(query, "youtube")
            return True

        if "gizli sekme" in t or "incognito" in t:
            url = t.replace("gizli sekme","").replace("incognito","").strip()
            self.browser.open_incognito(url)
            return True

        # ── Hafıza Yönetimi ───────────────────────────────────────────────────
        if "hafızaya kaydet" in t or "bunu kaydet" in t:
            content = t.replace("hafızaya kaydet","").replace("bunu kaydet","").strip()
            if content:
                self.memory.save_memory("notes", f"not_{int(time.time())}", content)
                r = f"✓ Hafızaya kaydedildi: {content[:50]}"
                self.msg("ANKA", r); self.speak(r)
            return True

        if "hafızamı göster" in t or "hafıza raporu" in t:
            r = self.memory.show_all()
            self.msg("ANKA", r); self.speak(r)
            return True

        if "hafızadan sil" in t:
            content = t.replace("hafızadan sil","").strip()
            mem = _load(MEMORY_FILE, {})
            # Basit arama ile sil
            for cat, items in mem.items():
                if isinstance(items, dict):
                    for k, v in list(items.items()):
                        val = v.get("value","") if isinstance(v,dict) else str(v)
                        if content.lower() in val.lower() or content.lower() in k.lower():
                            del mem[cat][k]
                            _save(MEMORY_FILE, mem)
                            r = f"✓ '{k}' hafızadan silindi efendim."
                            self.msg("ANKA", r); self.speak(r)
                            return True
            self.msg("ANKA", f"'{content}' hafızada bulunamadı efendim.")
            return True

        return False
