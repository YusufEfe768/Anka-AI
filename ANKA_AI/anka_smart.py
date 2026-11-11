# ── ANKA SMART — Akıllı Yeni Özellikler ──────────────────────────────────────
try:
    import pyperclip
except ImportError:
    class _PyClip:
        def copy(self,x):pass
        def paste(self):return ""
    pyperclip=_PyClip()
import json, os, time, threading, datetime, subprocess, webbrowser, re
import requests, random, math, psutil, socket
from anka_config import BASE_DIR, USER_NAME

SMART_FILE = os.path.join(BASE_DIR, "anka_smart.json")

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


# ═══════════════════════════════════════════════════════════════════════════════
# 1. HAVA DURUMU PRO — Saatlik & Haftalık tahmin + akıllı öneri
# ═══════════════════════════════════════════════════════════════════════════════
class WeatherPro:
    def __init__(self, speak_func, msg_func):
        self.speak = speak_func
        self.msg = msg_func

    def hourly(self, city="Istanbul"):
        def _h():
            try:
                r = requests.get(f"https://wttr.in/{city}?format=j1", timeout=5)
                d = r.json()
                weather = d["current_condition"][0]
                hourly = d["weather"][0]["hourly"][:6]
                result = (f"🌤 {city} Saatlik Hava:\n"
                         f"Şu an: {weather['temp_C']}°C — {weather['weatherDesc'][0]['value']}\n"
                         f"{'─'*25}\n")
                for h in hourly:
                    result += f"• {h['time'].zfill(4)[:2]}:00 — {h['tempC']}°C {h['weatherDesc'][0]['value']}\n"
                self.msg("ANKA", result)
                self.speak(f"Şu an {weather['temp_C']} derece, {weather['weatherDesc'][0]['value']} efendim.")
            except:
                self.msg("ANKA", "Hava verisi alınamadı efendim.")
        threading.Thread(target=_h, daemon=True).start()

    def weekly(self, city="Istanbul"):
        def _w():
            try:
                r = requests.get(f"https://wttr.in/{city}?format=j1", timeout=5)
                d = r.json()
                days_tr = ["Pzt","Sal","Çar","Per","Cum","Cmt","Paz"]
                result = f"📅 {city} Haftalık Tahmin:\n{'─'*25}\n"
                for i, day in enumerate(d["weather"][:7]):
                    avg = (int(day["maxtempC"]) + int(day["mintempC"])) // 2
                    desc = day["hourly"][4]["weatherDesc"][0]["value"]
                    rain = day["hourly"][4].get("chanceofrain","0")
                    result += f"• {days_tr[i]}: {day['mintempC']}°↑{day['maxtempC']}° {desc} 🌧%{rain}\n"
                self.msg("ANKA", result)
                self.speak("Haftalık hava tahmini hazırlandı efendim.")
            except:
                self.msg("ANKA", "Haftalık tahmin alınamadı efendim.")
        threading.Thread(target=_w, daemon=True).start()

    def smart_suggestion(self, city="Istanbul"):
        def _s():
            try:
                r = requests.get(f"https://wttr.in/{city}?format=j1", timeout=5)
                d = r.json()["current_condition"][0]
                temp = int(d["temp_C"])
                rain = int(d.get("chanceofrain","0"))
                feels = int(d["FeelsLikeC"])
                suggestions = []
                if temp < 10: suggestions.append("🧥 Kalın mont giy efendim!")
                elif temp < 18: suggestions.append("🧣 Hafif ceket yeterli efendim.")
                else: suggestions.append("👕 Hafif kıyafet ideal efendim.")
                if rain > 50: suggestions.append("☂️ Şemsiye almayı unutma!")
                if feels < temp - 5: suggestions.append("💨 Rüzgar var, hissedilen soğuk!")
                result = f"💡 Hava Önerileri:\n" + "\n".join(suggestions)
                self.msg("ANKA", result)
                self.speak(suggestions[0] if suggestions else "Hava güzel efendim.")
            except:
                self.msg("ANKA", "Öneri alınamadı efendim.")
        threading.Thread(target=_s, daemon=True).start()


# ═══════════════════════════════════════════════════════════════════════════════
# 2. SİSTEM İZLEYİCİ ULTRA — Gerçek zamanlı dashboard
# ═══════════════════════════════════════════════════════════════════════════════
class SystemMonitorUltra:
    def __init__(self, speak_func, msg_func):
        self.speak = speak_func
        self.msg = msg_func
        self.alerts = {}
        self.running = True
        threading.Thread(target=self._monitor_loop, daemon=True).start()

    def full_report(self):
        def _f():
            cpu = psutil.cpu_percent(interval=1)
            ram = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            net = psutil.net_io_counters()
            battery = psutil.sensors_battery()
            boot = datetime.datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.datetime.now() - boot
            hours, mins = divmod(uptime.seconds, 3600)
            mins //= 60
            top_procs = sorted(
                [(p.info['name'], p.info['cpu_percent'])
                 for p in psutil.process_iter(['name','cpu_percent'])
                 if p.info.get('cpu_percent',0) > 1],
                key=lambda x: -x[1])[:3]
            r = (f"💻 SİSTEM DASHBOARD\n{'═'*35}\n"
                 f"⏱️  Çalışma: {hours}sa {mins}dk\n"
                 f"{'─'*35}\n"
                 f"🖥️  CPU: %{cpu:.0f}\n"
                 f"🧠 RAM: {ram.used//1024//1024:,}MB / {ram.total//1024//1024:,}MB (%{ram.percent:.0f})\n"
                 f"💾 Disk: {disk.free//1024**3:.0f}GB boş / {disk.total//1024**3:.0f}GB\n"
                 f"🌐 Ağ: ↓{net.bytes_recv//1024//1024}MB ↑{net.bytes_sent//1024//1024}MB\n")
            if battery:
                r += f"🔋 Pil: %{battery.percent:.0f} ({'Şarjda' if battery.power_plugged else 'Pilde'})\n"
            if top_procs:
                r += f"{'─'*35}\n🔥 CPU Yoğun:\n"
                r += "\n".join(f"  • {n[:20]}: %{c:.0f}" for n,c in top_procs)
            self.msg("ANKA", r)
            self.speak(f"CPU yüzde {cpu:.0f}, RAM yüzde {ram.percent:.0f} efendim.")
        threading.Thread(target=_f, daemon=True).start()

    def kill_heavy(self, threshold=80):
        killed = []
        for p in psutil.process_iter(['name','cpu_percent','pid']):
            try:
                if p.info['cpu_percent'] > threshold and \
                   p.info['name'].lower() not in ['system','svchost.exe','python.exe']:
                    p.kill()
                    killed.append(p.info['name'])
            except: pass
        r = f"✅ {len(killed)} ağır süreç kapatıldı!" if killed else "Ağır süreç yok efendim."
        self.msg("ANKA", r); self.speak(r)

    def network_speed(self):
        def _ns():
            net1 = psutil.net_io_counters()
            time.sleep(2)
            net2 = psutil.net_io_counters()
            dl = (net2.bytes_recv - net1.bytes_recv) / 2 / 1024
            ul = (net2.bytes_sent - net1.bytes_sent) / 2 / 1024
            r = (f"🌐 Anlık Ağ Hızı:\n"
                 f"• İndirme: {dl:.1f} KB/s ({dl/1024:.2f} MB/s)\n"
                 f"• Yükleme: {ul:.1f} KB/s ({ul/1024:.2f} MB/s)")
            self.msg("ANKA", r); self.speak(r[:150])
        threading.Thread(target=_ns, daemon=True).start()

    def _monitor_loop(self):
        time.sleep(60)
        while self.running:
            try:
                cpu = psutil.cpu_percent(interval=2)
                ram = psutil.virtual_memory().percent
                hour_key = datetime.datetime.now().strftime("%Y-%m-%d-%H")
                if cpu > 90 and not self.alerts.get(f"cpu_{hour_key}"):
                    self.alerts[f"cpu_{hour_key}"] = True
                    self.msg("ANKA", f"🔴 CPU Kritik: %{cpu:.0f}! Ağır uygulamaları kapatın efendim.")
                if ram > 90 and not self.alerts.get(f"ram_{hour_key}"):
                    self.alerts[f"ram_{hour_key}"] = True
                    self.msg("ANKA", f"🔴 RAM Kritik: %{ram:.0f}! Bellek temizleniyor...")
                    import gc; gc.collect()
            except: pass
            time.sleep(120)

    def stop(self): self.running = False


# ═══════════════════════════════════════════════════════════════════════════════
# 3. KELİME İŞLEMCİ — Metin analiz ve dönüştürme
# ═══════════════════════════════════════════════════════════════════════════════
class WordProcessor:
    def __init__(self, ollama, speak_func, msg_func):
        self.ollama = ollama
        self.speak = speak_func
        self.msg = msg_func

    def analyze_text(self, text):
        words = text.split()
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        chars = len(text)
        unique_words = len(set(w.lower() for w in words))
        avg_word_len = sum(len(w) for w in words) / len(words) if words else 0
        read_time = len(words) / 200  # 200 kelime/dakika
        r = (f"📊 Metin Analizi:\n{'═'*30}\n"
             f"• Kelime Sayısı: {len(words)}\n"
             f"• Cümle Sayısı: {len(sentences)}\n"
             f"• Karakter: {chars}\n"
             f"• Benzersiz Kelime: {unique_words}\n"
             f"• Ort. Kelime Uzunluğu: {avg_word_len:.1f}\n"
             f"• Okuma Süresi: ~{read_time:.0f} dakika")
        self.msg("ANKA", r); self.speak(r[:200])

    def improve_text(self, text):
        def _i():
            r = self.ollama.chat(
                f"Bu metni düzelt ve geliştir. Dilbilgisi, akıcılık ve netlik açısından:\n{text}",
                system_override="Editör. Metni düzelt, panoya kopyala.")
            self.msg("ANKA", f"✏️ Geliştirilmiş Metin:\n{r}")
            pyperclip.copy(r)
            self.speak("Metin geliştirildi ve kopyalandı efendim.")
        threading.Thread(target=_i, daemon=True).start()

    def formal_to_informal(self, text):
        def _f():
            r = self.ollama.chat(
                f"Bu resmi metni günlük konuşma diline çevir:\n{text}",
                system_override="Dil uzmanı. Doğal konuşma diline çevir.")
            self.msg("ANKA", f"💬 Günlük Dil:\n{r}")
            pyperclip.copy(r)
        threading.Thread(target=_f, daemon=True).start()

    def informal_to_formal(self, text):
        def _f():
            r = self.ollama.chat(
                f"Bu günlük dili resmi/profesyonel dile çevir:\n{text}",
                system_override="Dil uzmanı. Profesyonel dile çevir.")
            self.msg("ANKA", f"📝 Resmi Dil:\n{r}")
            pyperclip.copy(r)
        threading.Thread(target=_f, daemon=True).start()

    def bullet_to_paragraph(self, text):
        def _b():
            r = self.ollama.chat(
                f"Bu madde listesini akıcı bir paragraf haline getir:\n{text}",
                system_override="Yazar. Maddeleri akıcı metne dönüştür.")
            self.msg("ANKA", f"📄 Paragraf:\n{r}")
            pyperclip.copy(r)
        threading.Thread(target=_b, daemon=True).start()

    def count_clipboard(self):
        try:
            text = pyperclip.paste()
            self.analyze_text(text)
        except:
            self.msg("ANKA", "Pano içeriği alınamadı efendim.")

    def random_word(self):
        words = [
            ("serendipity","beklenmedik güzel şeyler bulma yeteneği"),
            ("ephemeral","kısa süren, geçici"),
            ("melancholy","derin bir hüzün"),
            ("sonder","herkesin karmaşık bir hayatı olduğunu fark etme"),
            ("hiraeth","var olmayan bir yere duyulan özlem"),
            ("petrichor","yağmur sonrası toprağın kokusu"),
            ("susurrus","fısıltı veya hışırtı sesi"),
            ("luminous","ışıldayan, parlayan"),
        ]
        word, meaning = random.choice(words)
        r = f"📖 Günün Kelimesi:\n• {word}\n• Anlam: {meaning}"
        self.msg("ANKA", r); self.speak(r)


# ═══════════════════════════════════════════════════════════════════════════════
# 4. AJANDA ULTRA — Gelişmiş takvim ve planlama
# ═══════════════════════════════════════════════════════════════════════════════
class AgendaUltra:
    def __init__(self, ollama, speak_func, msg_func):
        self.ollama = ollama
        self.speak = speak_func
        self.msg = msg_func
        self.agenda_file = os.path.join(BASE_DIR, "anka_agenda_ultra.json")
        self.data = _load(self.agenda_file, {"events": [], "recurring": []})

    def add_event(self, title, date, time_str="", location="", notes=""):
        event = {
            "title": title, "date": date, "time": time_str,
            "location": location, "notes": notes,
            "created": datetime.datetime.now().isoformat()
        }
        self.data["events"].append(event)
        self.data["events"].sort(key=lambda x: (x["date"], x.get("time","")))
        _save(self.agenda_file, self.data)
        r = f"📅 '{title}' eklendi: {date}" + (f" {time_str}" if time_str else "")
        self.msg("ANKA", r); self.speak(r)

    def today(self):
        today = datetime.date.today().isoformat()
        events = [e for e in self.data["events"] if e["date"] == today]
        now = datetime.datetime.now().strftime("%H:%M")
        if not events:
            r = "📅 Bugün için etkinlik yok efendim."
        else:
            r = f"📅 Bugünün Programı ({today}):\n{'═'*30}\n"
            for e in events:
                past = e.get("time","") < now if e.get("time") else False
                emoji = "✅" if past else "⏰"
                r += f"{emoji} {e.get('time','?')} — {e['title']}\n"
                if e.get("location"): r += f"   📍 {e['location']}\n"
        self.msg("ANKA", r); self.speak(r[:200])

    def week_view(self):
        today = datetime.date.today()
        r = f"📅 Bu Haftanın Programı:\n{'═'*30}\n"
        days_tr = ["Pzt","Sal","Çar","Per","Cum","Cmt","Paz"]
        for i in range(7):
            day = today + datetime.timedelta(days=i)
            day_str = day.isoformat()
            events = [e for e in self.data["events"] if e["date"] == day_str]
            day_name = days_tr[day.weekday()]
            if events:
                r += f"\n{day_name} {day.strftime('%d/%m')}:\n"
                for e in events:
                    r += f"  • {e.get('time','')} {e['title']}\n"
            else:
                r += f"{day_name} {day.strftime('%d/%m')}: Boş\n"
        self.msg("ANKA", r)

    def upcoming(self, days=7):
        today = datetime.date.today().isoformat()
        until = (datetime.date.today() + datetime.timedelta(days=days)).isoformat()
        upcoming = [e for e in self.data["events"] if today <= e["date"] <= until]
        if not upcoming:
            r = f"Önümüzdeki {days} günde etkinlik yok efendim."
        else:
            r = f"📅 Yaklaşan Etkinlikler ({len(upcoming)}):\n"
            for e in upcoming:
                days_left = (datetime.date.fromisoformat(e["date"]) - datetime.date.today()).days
                r += f"• {e['title']} — {e['date']}" + (f" ({days_left} gün sonra)\n" if days_left > 0 else " (bugün!)\n")
        self.msg("ANKA", r); self.speak(r[:200])

    def ai_daily_plan(self):
        def _plan():
            today = datetime.date.today().isoformat()
            today_events = [e for e in self.data["events"] if e["date"] == today]
            event_text = "\n".join(f"• {e.get('time','?')} {e['title']}" for e in today_events) or "Etkinlik yok"
            now_hour = datetime.datetime.now().hour
            r = self.ollama.chat(
                f"Bugünkü etkinlikler:\n{event_text}\nSaat: {now_hour}:00\n"
                f"Günü nasıl verimli geçiririm? Kısa öneriler ver.",
                system_override="Verimlilik koçu. Kısa ve uygulanabilir öneriler ver.")
            self.msg("ANKA", f"💡 Günlük Plan Önerisi:\n{r}")
            self.speak(r[:200])
        threading.Thread(target=_plan, daemon=True).start()


# ═══════════════════════════════════════════════════════════════════════════════
# KOMUT İŞLEYİCİ
# ═══════════════════════════════════════════════════════════════════════════════
class SmartCommandProcessor:
    def __init__(self, speak_func, msg_func, ollama):
        self.speak = speak_func
        self.msg = msg_func
        self.ollama = ollama
        self.weather = WeatherPro(speak_func, msg_func)
        self.monitor = SystemMonitorUltra(speak_func, msg_func)
        self.word_proc = WordProcessor(ollama, speak_func, msg_func)
        self.agenda = AgendaUltra(ollama, speak_func, msg_func)

    def process(self, text):
        t = text.lower().strip()

        # ── Hava Durumu Pro ───────────────────────────────────────────────────
        if "saatlik hava" in t:
            city = t.replace("saatlik hava","").strip() or "Istanbul"
            self.weather.hourly(city); return True
        if "haftalık hava" in t:
            city = t.replace("haftalık hava","").strip() or "Istanbul"
            self.weather.weekly(city); return True
        if "hava önerisi" in t or "ne giyeyim" in t:
            self.weather.smart_suggestion(); return True
        if "hava nasıl" in t or "hava durumu" in t:
            self.weather.hourly(); return True

        # ── Sistem Monitor Ultra ──────────────────────────────────────────────
        if "sistem dashboard" in t or "tam sistem raporu" in t:
            self.monitor.full_report(); return True
        if "ağır süreçleri kapat" in t:
            self.monitor.kill_heavy(); return True
        if "anlık ağ hızı" in t or "internet hızı" in t:
            self.monitor.network_speed(); return True

        # ── Kelime İşlemci ────────────────────────────────────────────────────
        if "metni analiz et" in t:
            content = t.replace("metni analiz et","").strip()
            if not content:
                try: content = pyperclip.paste()
                except: pass
            if content: self.word_proc.analyze_text(content); return True

        if "metni geliştir" in t or "metni düzelt" in t:
            content = t.replace("metni geliştir","").replace("metni düzelt","").strip()
            if not content:
                try: content = pyperclip.paste()
                except: pass
            if content: self.word_proc.improve_text(content); return True

        if "resmi dile çevir" in t:
            content = t.replace("resmi dile çevir","").strip()
            if not content:
                try: content = pyperclip.paste()
                except: pass
            if content: self.word_proc.informal_to_formal(content); return True

        if "günlük dile çevir" in t:
            content = t.replace("günlük dile çevir","").strip()
            if not content:
                try: content = pyperclip.paste()
                except: pass
            if content: self.word_proc.formal_to_informal(content); return True

        if "maddeleri paragrafa çevir" in t:
            content = t.replace("maddeleri paragrafa çevir","").strip()
            if not content:
                try: content = pyperclip.paste()
                except: pass
            if content: self.word_proc.bullet_to_paragraph(content); return True

        if "panodaki kelime sayısı" in t or "pano analizi" in t:
            self.word_proc.count_clipboard(); return True

        if "günün kelimesi" in t or "yeni kelime öğret" in t:
            self.word_proc.random_word(); return True

        # ── Ajanda Ultra ──────────────────────────────────────────────────────
        if "etkinlik ekle" in t or "ajandaya ekle" in t:
            content = t.replace("etkinlik ekle","").replace("ajandaya ekle","").strip()
            date_m = re.search(r'(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4})', text)
            time_m = re.search(r'(\d{1,2}:\d{2})', text)
            if date_m:
                date_str = date_m.group(1).replace("/","-")
                if len(date_str.split("-")[0]) == 2:
                    parts = date_str.split("-")
                    date_str = f"{parts[2]}-{parts[1]}-{parts[0]}"
            else:
                date_str = datetime.date.today().isoformat()
            time_str = time_m.group(1) if time_m else ""
            title = re.sub(r'\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|\d{1,2}:\d{2}', '', content).strip()
            if title: self.agenda.add_event(title, date_str, time_str)
            return True

        if "bugünkü program" in t or "bugün ne var" in t:
            self.agenda.today(); return True

        if "haftalık program" in t or "bu hafta ne var" in t:
            self.agenda.week_view(); return True

        if "yaklaşan etkinlikler" in t:
            m = re.search(r'(\d+)', t)
            days = int(m.group(1)) if m else 7
            self.agenda.upcoming(days); return True

        if "günü planla" in t or "ai günlük plan" in t:
            self.agenda.ai_daily_plan(); return True

        return False
