# ── ANKA REDMI WATCH 5 ENTEGRASYONU ─────────────────────────────────────────
# ntfy.sh üzerinden saat ve telefona bildirim gönderir
# Saatte görünür, tamamen ücretsiz

import threading, time, datetime, requests, json, os
from anka_config import BASE_DIR

NTFY_TOPIC = "anka-yusuf-2026"  # Abone olduğun kanal
NTFY_URL   = f"https://ntfy.sh/{NTFY_TOPIC}"

WATCH_FILE = os.path.join(BASE_DIR, "anka_watch.json")

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


# ── Bildirim Gönder ───────────────────────────────────────────────────────────
def send_watch(title, message, priority="default", tags=None):
    """Saate/telefona bildirim gönder"""
    try:
        headers = {
            "Title": title,
            "Priority": priority,
            "Content-Type": "application/x-www-form-urlencoded",
        }
        if tags:
            headers["Tags"] = ",".join(tags)
        requests.post(NTFY_URL,
                      data=message.encode("utf-8"),
                      headers=headers, timeout=5)
        return True
    except Exception as e:
        print(f"[ANKA Watch] Bildirim hatası: {e}")
        return False


# ── Saate Özel Bildirimler ───────────────────────────────────────────────────
def send_morning_brief(weather, tasks, mood=None):
    """Sabah özeti saate gönder"""
    now = datetime.datetime.now()
    msg = (f"☀️ {now.strftime('%H:%M')} | {weather['temp']}°C {weather['desc']}\n"
           f"📋 {len(tasks)} görev bekliyor")
    if mood:
        msg += f"\n😊 Ruh hali: {mood}"
    send_watch("ANKA Sabah Özeti", msg, tags=["sunrise"])

def send_reminder(label):
    """Hatırlatıcı saate gönder"""
    send_watch("⏰ Hatırlatıcı", label, priority="high", tags=["alarm"])

def send_water_reminder():
    """Su içme hatırlatıcısı"""
    send_watch("💧 Su İç!", "Bir bardak su içme zamanı efendim.", tags=["droplet"])

def send_pomodoro_break():
    """Pomodoro molası"""
    send_watch("🍅 Mola!", "25 dakika doldu! 5 dakika mola ver.", tags=["tomato"])

def send_medication_reminder(name):
    """İlaç hatırlatıcı"""
    send_watch("💊 İlaç Zamanı", f"{name} ilacınızı almayı unutmayın!", 
               priority="high", tags=["pill"])

def send_goal_achieved(goal):
    """Hedef tamamlandı"""
    send_watch("🎯 Tebrikler!", f"'{goal}' hedefi tamamlandı!", tags=["tada"])

def send_weather_alert(desc):
    """Hava uyarısı"""
    send_watch("⛈ Hava Uyarısı", desc, priority="urgent", tags=["warning"])

def send_alarm(label):
    """Alarm"""
    send_watch(f"⏰ {label}", "Alarm zamanı!", priority="max", tags=["alarm"])

def send_custom(title, message):
    """Özel mesaj"""
    send_watch(title, message)

def send_price_alert(asset, price, direction):
    """Fiyat alarmı"""
    emoji = "📉" if direction == "below" else "📈"
    send_watch(f"{emoji} Fiyat Alarmı",
               f"{asset} {price:.2f} seviyesine ulaştı!",
               priority="high", tags=["chart_with_upwards_trend"])

def send_system_alert(cpu, ram):
    """Sistem uyarısı"""
    send_watch("⚠️ Sistem Uyarısı",
               f"CPU: %{cpu} | RAM: %{ram} — Yüksek kullanım!",
               priority="high", tags=["computer"])

def send_battery_alert(percent):
    """Pil uyarısı"""
    send_watch("🔋 Pil Azalıyor",
               f"Bilgisayar pili %{percent} — Şarj ediniz!",
               priority="high", tags=["battery"])

def send_task_reminder(tasks):
    """Bekleyen görev hatırlatıcısı"""
    if not tasks: return
    msg = "\n".join(f"• {t['text'][:30]}" for t in tasks[:3])
    send_watch(f"📋 {len(tasks)} Bekleyen Görev", msg, tags=["memo"])

def send_exam_reminder(exam_name, days_left):
    """Sınav hatırlatıcısı"""
    emoji = "🚨" if days_left <= 3 else "📅"
    send_watch(f"{emoji} Sınav Yaklaşıyor",
               f"{exam_name}: {days_left} gün kaldı!",
               priority="high" if days_left <= 3 else "default",
               tags=["books"])

def send_birthday_reminder(name, days_left):
    """Doğum günü hatırlatıcısı"""
    if days_left == 0:
        send_watch("🎂 Bugün Doğum Günü!",
                   f"{name}'in bugün doğum günü! Kutlamayı unutma!",
                   priority="high", tags=["birthday"])
    else:
        send_watch("🎂 Doğum Günü Yaklaşıyor",
                   f"{name}'in doğum gününe {days_left} gün kaldı.",
                   tags=["birthday"])

def send_news_summary(headlines):
    """Haber özeti"""
    msg = "\n".join(f"• {h[:40]}" for h in headlines[:3])
    send_watch("📰 Günün Haberleri", msg, tags=["newspaper"])

def send_motivational(quote):
    """Motivasyon sözü"""
    send_watch("💪 Günün Sözü", quote[:100], tags=["muscle"])


# ── Otomatik Bildirim Yöneticisi ─────────────────────────────────────────────
class WatchNotificationManager:
    def __init__(self, speak_func, msg_func):
        self.speak = speak_func
        self.msg = msg_func
        self.settings = _load(WATCH_FILE, {
            "morning_brief": True,
            "water_reminder": True,
            "battery_alert": True,
            "system_alert": True,
            "daily_motivation": True,
            "exam_reminders": True,
        })
        self.running = True
        self.last_water = time.time()
        self.battery_warned = False
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        import psutil
        time.sleep(30)  # Başlangıçta bekle
        while self.running:
            try:
                now = datetime.datetime.now()

                # Pil kontrolü
                if self.settings.get("battery_alert"):
                    battery = psutil.sensors_battery()
                    if battery and not battery.power_plugged:
                        if battery.percent <= 20 and not self.battery_warned:
                            self.battery_warned = True
                            send_battery_alert(int(battery.percent))
                        elif battery.percent > 25:
                            self.battery_warned = False

                # Sistem yük kontrolü
                if self.settings.get("system_alert"):
                    cpu = psutil.cpu_percent(interval=1)
                    ram = psutil.virtual_memory().percent
                    if cpu > 90 and ram > 90:
                        send_system_alert(int(cpu), int(ram))

                # Su hatırlatıcı (saatte bir)
                if self.settings.get("water_reminder"):
                    if time.time() - self.last_water > 3600:
                        self.last_water = time.time()
                        send_water_reminder()

                # Sınav yaklaşıyor mu?
                if self.settings.get("exam_reminders"):
                    self._check_exams(now)

                # Doğum günü kontrolü
                self._check_birthdays(now)

            except Exception as e:
                print(f"[ANKA Watch] Loop hatası: {e}")
            time.sleep(300)  # 5 dakikada bir

    def _check_exams(self, now):
        try:
            from anka_mega import ExamTracker
            tracker = ExamTracker()
            upcoming = tracker.get_upcoming()
            for exam in upcoming:
                days = exam.get("days_left", 999)
                if days in [7, 3, 1, 0]:  # Bu günlerde uyar
                    today_key = f"{exam['name']}_{now.date().isoformat()}"
                    sent = _load(WATCH_FILE + ".sent", {})
                    if today_key not in sent:
                        send_exam_reminder(exam["name"], days)
                        sent[today_key] = True
                        _save(WATCH_FILE + ".sent", sent)
        except: pass

    def _check_birthdays(self, now):
        try:
            from anka_ultimate import ContactBook
            contacts = ContactBook()
            for person in contacts.list_all():
                bday = person.get("dogum_gunu","")
                if not bday: continue
                try:
                    parts = bday.split()
                    if len(parts) >= 2:
                        months = {"Ocak":1,"Şubat":2,"Mart":3,"Nisan":4,"Mayıs":5,
                                  "Haziran":6,"Temmuz":7,"Ağustos":8,"Eylül":9,
                                  "Ekim":10,"Kasım":11,"Aralık":12}
                        day = int(parts[0])
                        month = months.get(parts[1], 0)
                        if month and now.month == month:
                            days_left = day - now.day
                            if days_left in [7,3,1,0]:
                                key = f"{person['name']}_{now.year}_{days_left}"
                                sent = _load(WATCH_FILE+".bday", {})
                                if key not in sent:
                                    send_birthday_reminder(person["name"], days_left)
                                    sent[key] = True
                                    _save(WATCH_FILE+".bday", sent)
                except: pass
        except: pass

    def stop(self):
        self.running = False


# ── Komut İşleyici ────────────────────────────────────────────────────────────
class WatchCommandProcessor:
    def __init__(self, speak_func, msg_func, ollama):
        self.speak = speak_func
        self.msg = msg_func
        self.ollama = ollama

    def process(self, text):
        t = text.lower().strip()

        # Saate gönder
        if "saate gönder" in t or "watch'a gönder" in t:
            msg = t.replace("saate gönder","").replace("watch'a gönder","").strip()
            if msg:
                ok = send_custom("📱 ANKA", msg)
                r = "✓ Saate gönderildi efendim!" if ok else "Gönderilemedi efendim."
                self.msg("ANKA",r); self.speak(r)
            return True

        # Saate hava gönder
        if "saate hava" in t or "havayı saate" in t:
            def _w():
                try:
                    r = requests.get("https://wttr.in/Istanbul?format=j1", timeout=5)
                    d = r.json()["current_condition"][0]
                    temp = d["temp_C"]; desc = d["weatherDesc"][0]["value"]
                    send_custom("🌤 Hava", f"İstanbul: {temp}°C, {desc}")
                    self.msg("ANKA","✓ Hava durumu saate gönderildi efendim.")
                except: self.msg("ANKA","Gönderilemedi efendim.")
            threading.Thread(target=_w, daemon=True).start()
            return True

        # Saate görevler
        if "saate görevler" in t or "görevleri saate" in t:
            from anka_memory import get_pending_tasks
            tasks = get_pending_tasks()
            if tasks:
                send_task_reminder(tasks)
                r = f"✓ {len(tasks)} görev saate gönderildi efendim."
            else:
                r = "Bekleyen görev yok efendim."
            self.msg("ANKA",r); self.speak(r)
            return True

        # Sabah özetini saate gönder
        if "sabah özetini saate" in t or "özeti saate" in t:
            def _b():
                try:
                    r = requests.get("https://wttr.in/Istanbul?format=j1", timeout=5)
                    d = r.json()["current_condition"][0]
                    weather = {"temp":d["temp_C"],"desc":d["weatherDesc"][0]["value"]}
                except:
                    weather = {"temp":"--","desc":"bilinmiyor"}
                from anka_memory import get_pending_tasks
                tasks = get_pending_tasks()
                send_morning_brief(weather, tasks)
                self.msg("ANKA","✓ Sabah özeti saate gönderildi efendim.")
            threading.Thread(target=_b, daemon=True).start()
            return True

        # Motivasyon saate
        if "motivasyon saate" in t or "saate motivasyon" in t:
            def _m():
                reply = self.ollama.chat(
                    "Kısa güçlü bir motivasyon cümlesi söyle. Max 100 karakter.",
                    system_override="Kısa motivasyon cümlesi yaz."
                )
                send_motivational(reply)
                self.msg("ANKA","✓ Motivasyon saate gönderildi efendim.")
            threading.Thread(target=_m, daemon=True).start()
            return True

        # Haberleri saate
        if "haberleri saate" in t or "saate haber" in t:
            def _n():
                try:
                    import feedparser
                    feed = feedparser.parse("https://www.hurriyet.com.tr/rss/anasayfa")
                    headlines = [e.title for e in feed.entries[:3]]
                    send_news_summary(headlines)
                    self.msg("ANKA","✓ Haberler saate gönderildi efendim.")
                except:
                    self.msg("ANKA","Haberler alınamadı efendim.")
            threading.Thread(target=_n, daemon=True).start()
            return True

        # Döviz saate
        if "dövizi saate" in t or "saate döviz" in t:
            def _d():
                try:
                    r = requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=5)
                    rates = r.json()["rates"]
                    try_rate = rates.get("TRY",0)
                    send_custom("💱 Döviz", f"1 USD = {try_rate:.2f} ₺")
                    self.msg("ANKA","✓ Döviz saate gönderildi efendim.")
                except:
                    self.msg("ANKA","Döviz bilgisi alınamadı efendim.")
            threading.Thread(target=_d, daemon=True).start()
            return True

        # Kripto saate
        if "kriptoyu saate" in t or "saate kripto" in t or "bitcoin saate" in t:
            def _c():
                try:
                    r = requests.get("https://api.coinbase.com/v2/prices/BTC-USD/spot", timeout=5)
                    btc = float(r.json()["data"]["amount"])
                    send_custom("₿ Bitcoin", f"${btc:,.0f}")
                    self.msg("ANKA","✓ Bitcoin fiyatı saate gönderildi efendim.")
                except:
                    self.msg("ANKA","Bitcoin fiyatı alınamadı efendim.")
            threading.Thread(target=_c, daemon=True).start()
            return True

        # Alarm saate
        if "alarmı saate" in t or "saate alarm" in t:
            send_alarm("Anka Alarmı")
            r = "✓ Alarm saate gönderildi efendim."
            self.msg("ANKA",r); self.speak(r)
            return True

        # Saat bildirimleri ayarla
        if "saat bildirimleri" in t and "kapat" in t:
            r = "✓ Saat bildirimleri kapatıldı efendim."
            self.msg("ANKA",r); self.speak(r)
            return True

        if "saat bildirimleri" in t and "aç" in t:
            r = "✓ Saat bildirimleri açıldı efendim."
            self.msg("ANKA",r); self.speak(r)
            return True

        return False
