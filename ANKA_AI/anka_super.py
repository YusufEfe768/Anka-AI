# ── ANKA SÜPER ÖZELLİKLER MODÜLü ─────────────────────────────────────────────
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
import json, os, time, threading, datetime, subprocess, random, webbrowser
import psutil, requests
from anka_config import BASE_DIR

SLEEP_FILE    = os.path.join(BASE_DIR, "anka_sleep.json")
CALORIE_FILE  = os.path.join(BASE_DIR, "anka_calories.json")
PRICE_FILE    = os.path.join(BASE_DIR, "anka_price_alerts.json")
CHESS_FILE    = os.path.join(BASE_DIR, "anka_chess.json")

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


# ── Uyku Takibi ───────────────────────────────────────────────────────────────
class SleepTracker:
    def sleep(self):
        data = _load(SLEEP_FILE, [])
        data.append({"event":"sleep","time":datetime.datetime.now().isoformat()})
        _save(SLEEP_FILE, data)

    def wake(self):
        data = _load(SLEEP_FILE, [])
        # Son uyku kaydını bul
        sleep_time = None
        for item in reversed(data):
            if item["event"] == "sleep":
                sleep_time = datetime.datetime.fromisoformat(item["time"])
                break
        data.append({"event":"wake","time":datetime.datetime.now().isoformat()})
        _save(SLEEP_FILE, data)
        if sleep_time:
            duration = datetime.datetime.now() - sleep_time
            hours = duration.total_seconds() / 3600
            return round(hours, 1)
        return None

    def get_last_sleep(self):
        data = _load(SLEEP_FILE, [])
        sleeps = [(i,d) for i,d in enumerate(data) if d["event"]=="sleep"]
        wakes  = [(i,d) for i,d in enumerate(data) if d["event"]=="wake"]
        if sleeps and wakes:
            last_sleep = datetime.datetime.fromisoformat(sleeps[-1][1]["time"])
            last_wake  = datetime.datetime.fromisoformat(wakes[-1][1]["time"])
            if last_wake > last_sleep:
                hours = (last_wake - last_sleep).total_seconds() / 3600
                return round(hours, 1)
        return None


# ── Kalori Takibi ─────────────────────────────────────────────────────────────
CALORIE_DB = {
    "elma": 95, "muz": 105, "portakal": 62, "üzüm": 69,
    "ekmek": 79, "pilav": 206, "makarna": 220, "pizza": 285,
    "hamburger": 295, "tavuk": 165, "balık": 140, "yumurta": 78,
    "çorba": 74, "salata": 20, "patates": 93, "börek": 210,
    "çay": 2, "kahve": 5, "kola": 140, "su": 0, "meyve suyu": 110,
    "çikolata": 546, "dondurma": 207, "pasta": 257, "bisküvi": 480,
    "peynir": 402, "yoğurt": 59, "süt": 61,
}

class CalorieTracker:
    def add(self, food, amount=1):
        data = _load(CALORIE_FILE, {})
        today = datetime.date.today().isoformat()
        if today not in data: data[today] = []
        food_l = food.lower()
        cal = CALORIE_DB.get(food_l, 150)  # Bilinmeyenler için varsayılan
        data[today].append({"food": food, "calories": cal * amount, "amount": amount})
        _save(CALORIE_FILE, data)
        return cal * amount

    def get_today(self):
        data = _load(CALORIE_FILE, {})
        today = datetime.date.today().isoformat()
        items = data.get(today, [])
        total = sum(i["calories"] for i in items)
        return items, total

    def get_weekly_avg(self):
        data = _load(CALORIE_FILE, {})
        totals = []
        for i in range(7):
            day = (datetime.date.today() - datetime.timedelta(days=i)).isoformat()
            items = data.get(day, [])
            if items:
                totals.append(sum(i["calories"] for i in items))
        return round(sum(totals)/len(totals)) if totals else 0


# ── Fiyat Alarmları ───────────────────────────────────────────────────────────
class PriceAlertMonitor:
    def __init__(self, speak_func, msg_func):
        self.speak = speak_func
        self.msg = msg_func
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def add_alert(self, asset, target_price, direction="below"):
        data = _load(PRICE_FILE, [])
        data.append({
            "asset": asset, "target": target_price,
            "direction": direction, "active": True,
            "created": datetime.datetime.now().isoformat()
        })
        _save(PRICE_FILE, data)

    def _loop(self):
        while self.running:
            try:
                data = _load(PRICE_FILE, [])
                changed = False
                for alert in data:
                    if not alert.get("active"): continue
                    price = self._get_price(alert["asset"])
                    if price is None: continue
                    triggered = (alert["direction"]=="below" and price <= alert["target"]) or \
                                (alert["direction"]=="above" and price >= alert["target"])
                    if triggered:
                        r = (f"🔔 Fiyat Alarmı! {alert['asset']} "
                             f"{'düştü' if alert['direction']=='below' else 'yükseldi'}: "
                             f"${price:.2f} (Hedef: ${alert['target']:.2f})")
                        self.msg("SİSTEM", r)
                        self.speak(r)
                        alert["active"] = False
                        changed = True
                if changed:
                    _save(PRICE_FILE, data)
            except: pass
            time.sleep(300)  # 5 dakikada bir kontrol

    def _get_price(self, asset):
        try:
            asset_l = asset.lower()
            if asset_l in ["btc","bitcoin"]:
                r = requests.get("https://api.coinbase.com/v2/prices/BTC-USD/spot", timeout=5)
                return float(r.json()["data"]["amount"])
            elif asset_l in ["eth","ethereum"]:
                r = requests.get("https://api.coinbase.com/v2/prices/ETH-USD/spot", timeout=5)
                return float(r.json()["data"]["amount"])
            elif asset_l in ["dolar","usd"]:
                r = requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=5)
                return float(r.json()["rates"]["TRY"])
        except: pass
        return None

    def stop(self): self.running = False


# ── Göz Dinlendirme (20-20-20 Kuralı) ────────────────────────────────────────
class EyeCareReminder:
    def __init__(self, speak_func, msg_func, enabled=True):
        self.speak = speak_func
        self.msg = msg_func
        self.enabled = enabled
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def _loop(self):
        while self.running:
            time.sleep(20 * 60)  # 20 dakika
            if self.enabled:
                r = "👁 Göz dinlendirme zamanı! 20 saniye boyunca 6 metre uzağa bakın efendim."
                self.msg("SİSTEM", r)
                self.speak(r)

    def stop(self): self.running = False


# ── Hava Alarmı ───────────────────────────────────────────────────────────────
class WeatherAlertMonitor:
    def __init__(self, speak_func, msg_func):
        self.speak = speak_func
        self.msg = msg_func
        self.running = True
        self.last_alert = None
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def _loop(self):
        time.sleep(60)
        while self.running:
            try:
                r = requests.get("https://wttr.in/Istanbul?format=j1", timeout=5)
                d = r.json()
                cur = d["current_condition"][0]
                code = int(cur.get("weatherCode", 0))
                desc = cur["weatherDesc"][0]["value"]
                temp = int(cur["temp_C"])

                alert = None
                if code in [389, 386, 200, 201, 202]:
                    alert = f"⛈ Dikkat! İstanbul'da fırtına/yıldırım bekleniyor: {desc}"
                elif code in [371, 338, 335, 332, 329]:
                    alert = f"❄️ Dikkat! İstanbul'da kar yağışı bekleniyor: {desc}"
                elif temp > 38:
                    alert = f"🌡 Dikkat! Hava çok sıcak: {temp}°C"
                elif temp < 0:
                    alert = f"🥶 Dikkat! Hava donuyor: {temp}°C"

                if alert and alert != self.last_alert:
                    self.last_alert = alert
                    self.msg("SİSTEM", alert)
                    self.speak(alert)
            except: pass
            time.sleep(3600)  # Saatte bir kontrol

    def stop(self): self.running = False


# ── Kelime Tahmin Oyunu ───────────────────────────────────────────────────────
class WordleGame:
    WORDS = ["elma","masa","kedi","köpek","araba","okul","kitap","deniz",
             "dağ","çiçek","güneş","yıldız","bulut","rüzgar","ateş","su",
             "toprak","hava","ışık","gece","gündüz","sabah","akşam","öğle"]

    def __init__(self):
        self.current_word = None
        self.attempts = 0
        self.max_attempts = 6
        self.active = False

    def start(self):
        self.current_word = random.choice(self.WORDS)
        self.attempts = 0
        self.active = True
        return f"🎯 Kelime oyunu başladı! {len(self.current_word)} harfli bir kelime düşündüm. Tahmin et! ({self.max_attempts} hakkın var)"

    def guess(self, word):
        if not self.active:
            return "Önce 'kelime oyunu başlat' diyerek oyunu başlatın efendim."
        word = word.lower().strip()
        self.attempts += 1
        if word == self.current_word:
            self.active = False
            return f"🎉 Doğru! '{self.current_word}' kelimesini {self.attempts}. denemede buldunuz!"
        elif self.attempts >= self.max_attempts:
            self.active = False
            return f"😢 Hakkınız bitti. Kelime '{self.current_word}' idi."
        else:
            # İpucu ver
            hints = []
            for i, ch in enumerate(word):
                if i < len(self.current_word):
                    if ch == self.current_word[i]:
                        hints.append(f"✅{ch}")
                    elif ch in self.current_word:
                        hints.append(f"🟡{ch}")
                    else:
                        hints.append(f"❌{ch}")
            remaining = self.max_attempts - self.attempts
            return f"{''.join(hints)} — {remaining} hakkınız kaldı."


# ── Bilgi Yarışması ───────────────────────────────────────────────────────────
TRIVIA = [
    ("Türkiye'nin başkenti neresidir?", "Ankara"),
    ("En büyük gezegen hangisidir?", "Jüpiter"),
    ("Su'nun kimyasal formülü nedir?", "H2O"),
    ("Türkiye kaç yılında kuruldu?", "1923"),
    ("Dünyanın en yüksek dağı hangisidir?", "Everest"),
    ("Bir yılda kaç ay vardır?", "12"),
    ("Işık hızı yaklaşık kaç km/s'dir?", "300000"),
    ("İnsan vücudunda kaç kemik vardır?", "206"),
    ("Türkiye'nin en büyük şehri hangisidir?", "İstanbul"),
    ("Güneş sistemimizdeki gezegen sayısı kaçtır?", "8"),
]

class TriviaGame:
    def __init__(self):
        self.current = None
        self.score = 0

    def ask(self):
        self.current = random.choice(TRIVIA)
        return f"❓ {self.current[0]}"

    def answer(self, ans):
        if not self.current:
            return "Önce soru sormanız gerekiyor efendim."
        correct = self.current[1].lower() in ans.lower() or ans.lower() in self.current[1].lower()
        if correct:
            self.score += 1
            r = f"✅ Doğru! Toplam puan: {self.score}"
        else:
            r = f"❌ Yanlış. Doğru cevap: {self.current[1]}. Toplam puan: {self.score}"
        self.current = None
        return r


# ── Nefes Egzersizi ───────────────────────────────────────────────────────────
def breathing_exercise(speak_func, msg_func, cycles=3):
    def _run():
        msg_func("ANKA", f"🧘 {cycles} döngülük nefes egzersizi başlıyor efendim. Hazır olun...")
        speak_func(f"{cycles} döngülük nefes egzersizi başlıyor.")
        time.sleep(2)
        for i in range(cycles):
            speak_func("Derin nefes alın... 4 saniye")
            msg_func("ANKA", f"🫁 Döngü {i+1}/{cycles} — Derin nefes alın (4 sn)")
            time.sleep(4)
            speak_func("Tutun... 4 saniye")
            msg_func("ANKA", "⏸ Nefesi tutun (4 sn)")
            time.sleep(4)
            speak_func("Yavaşça verin... 6 saniye")
            msg_func("ANKA", "💨 Yavaşça verin (6 sn)")
            time.sleep(6)
        msg_func("ANKA", "✅ Nefes egzersizi tamamlandı. Kendinizi daha iyi hissedeceksiniz efendim!")
        speak_func("Nefes egzersizi tamamlandı. Kendinizi daha iyi hissedeceksiniz efendim.")
    threading.Thread(target=_run, daemon=True).start()


# ── Şans Topu ─────────────────────────────────────────────────────────────────
ACTIVITIES = [
    "Bir bardak su için 💧",
    "5 dakika yürüyüş yapın 🚶",
    "Bir arkadaşınızı arayın 📞",
    "10 dakika kitap okuyun 📚",
    "Güzel bir müzik açın 🎵",
    "Dışarı çıkıp hava alın 🌿",
    "Sevdiğiniz birine mesaj atın 💬",
    "5 dakika meditasyon yapın 🧘",
    "Yeni bir şey öğrenin 🧠",
    "Sevdiğiniz bir şey pişirin 🍳",
]

def random_activity():
    return random.choice(ACTIVITIES)


# ── Komut İşleyici ────────────────────────────────────────────────────────────
class SuperCommandProcessor:
    def __init__(self, speak_func, msg_func, ollama,
                 sleep_tracker=None, calorie_tracker=None,
                 price_monitor=None, wordle=None, trivia=None):
        self.speak = speak_func
        self.msg = msg_func
        self.ollama = ollama
        self.sleep = sleep_tracker or SleepTracker()
        self.calories = calorie_tracker or CalorieTracker()
        self.prices = price_monitor
        self.wordle = wordle or WordleGame()
        self.trivia = trivia or TriviaGame()

    def process(self, text):
        t = text.lower().strip()
        import re

        # ── Uyku Takibi ──────────────────────────────────────────────────────
        if any(x in t for x in ["uyuyorum","uyku moduna","yatıyorum","iyi geceler"]):
            self.sleep.sleep()
            r = "🌙 Uyku zamanınız kaydedildi. İyi geceler efendim, güzel rüyalar!"
            self.msg("ANKA", r); self.speak(r)
            return True

        if any(x in t for x in ["uyandım","günaydın","kalktım"]):
            hours = self.sleep.wake()
            if hours:
                quality = "harika" if hours >= 7 else ("yeterli" if hours >= 6 else "az")
                r = f"☀️ Günaydın efendim! {hours} saat uyudunuz — {quality} bir uyku."
                if hours < 6:
                    r += " Bugün biraz dinlenmeye özen gösterin."
            else:
                r = "☀️ Günaydın efendim! Uyanış zamanınız kaydedildi."
            self.msg("ANKA", r); self.speak(r)
            return True

        if "uyku süresi" in t or "kaç saat uyudum" in t:
            hours = self.sleep.get_last_sleep()
            if hours:
                r = f"😴 Son uykunuz: {hours} saat."
            else:
                r = "Uyku kaydı bulunamadı efendim. 'Uyuyorum' ve 'uyandım' diyerek takip başlatabilirsiniz."
            self.msg("ANKA", r); self.speak(r)
            return True

        # ── Kalori ───────────────────────────────────────────────────────────
        if "yedim" in t or "içtim" in t and "su" not in t:
            # "elma yedim", "pizza yedim 2 dilim"
            food_match = re.search(r'(\w+)\s*yedim|içtim', t)
            if food_match:
                food = food_match.group(1)
                amount_m = re.search(r'(\d+)', t)
                amount = int(amount_m.group(1)) if amount_m else 1
                cal = self.calories.add(food, amount)
                _, total = self.calories.get_today()
                r = f"🍽 {food.capitalize()} kaydedildi (+{cal} kal). Bugün toplam: {total} kalori."
                self.msg("ANKA", r); self.speak(r)
                return True

        if "kalori" in t and any(x in t for x in ["bugün","toplam","ne kadar"]):
            items, total = self.calories.get_today()
            if not items:
                r = "Bugün henüz kalori kaydı yok efendim."
            else:
                r = f"🔥 Bugünkü toplam: {total} kalori\n"
                r += "\n".join(f"• {i['food']}: {i['calories']} kal" for i in items[-5:])
            self.msg("ANKA", r); self.speak(f"Bugün toplam {total} kalori aldınız efendim.")
            return True

        # ── Fiyat Alarmı ─────────────────────────────────────────────────────
        if "fiyat alarmı" in t or "olunca söyle" in t or "ulaşınca söyle" in t:
            m = re.search(r'(\d+(?:\.\d+)?)', t)
            if m and self.prices:
                target = float(m.group(1))
                asset = "btc" if "bitcoin" in t or "btc" in t else \
                        "eth" if "ethereum" in t or "eth" in t else "dolar"
                direction = "below" if any(x in t for x in ["düşünce","altına","inince"]) else "above"
                if self.prices:
                    self.prices.add_alert(asset, target, direction)
                r = f"✓ {asset.upper()} {'$' if asset!='dolar' else ''}{target} {'altına düşünce' if direction=='below' else 'üstüne çıkınca'} sizi uyaracağım efendim."
                self.msg("ANKA", r); self.speak(r)
            return True

        # ── Göz Dinlendirme ───────────────────────────────────────────────────
        if "göz dinlendir" in t or "20 20" in t:
            r = "👁 Şimdi 20 saniye boyunca 6 metre uzağa bakın efendim. Gözleriniz dinlenecek."
            self.msg("ANKA", r); self.speak(r)
            return True

        # ── Nefes Egzersizi ───────────────────────────────────────────────────
        if "nefes egzersizi" in t or "nefes al" in t:
            m = re.search(r'(\d+)', t)
            cycles = int(m.group(1)) if m else 3
            breathing_exercise(self.speak, self.msg, cycles)
            return True

        # ── Kelime Oyunu ──────────────────────────────────────────────────────
        if "kelime oyunu" in t and "başlat" in t:
            r = self.wordle.start()
            self.msg("ANKA", r); self.speak(r)
            return True

        if "tahminim" in t or ("tahmin" in t and self.wordle.active):
            guess = t.replace("tahminim","").replace("tahmin","").replace(":","").strip()
            if guess:
                r = self.wordle.guess(guess)
                self.msg("ANKA", r); self.speak(r)
            return True

        # ── Bilgi Yarışması ───────────────────────────────────────────────────
        if "bilgi yarışması" in t or "soru sor" in t:
            r = self.trivia.ask()
            self.msg("ANKA", r); self.speak(r)
            return True

        if "cevabım" in t and self.trivia.current:
            ans = t.replace("cevabım","").replace(":","").strip()
            r = self.trivia.answer(ans)
            self.msg("ANKA", r); self.speak(r)
            return True

        if "puan" in t and "yarışma" in t:
            r = f"🏆 Bilgi yarışması puanınız: {self.trivia.score}"
            self.msg("ANKA", r); self.speak(r)
            return True

        # ── Şans Topu / Aktivite Öneri ────────────────────────────────────────
        if any(x in t for x in ["ne yapayım","aktivite öner","şans topu","sıkıldım"]):
            act = random_activity()
            r = f"🎲 Öneri: {act}"
            self.msg("ANKA", r); self.speak(act)
            return True

        # ── Ekranı AI ile Analiz Et ───────────────────────────────────────────
        if "ekranımda ne var" in t or "ekranı analiz et" in t:
            threading.Thread(target=self._analyze_screen, daemon=True).start()
            return True

        # ── Makale/Rapor Yaz ─────────────────────────────────────────────────
        if "makale yaz" in t or "rapor yaz" in t:
            topic = t.replace("makale yaz","").replace("rapor yaz","").replace("hakkında","").strip()
            if topic:
                self.msg("ANKA","📝 Yazılıyor...")
                threading.Thread(target=self._write_article, args=(topic,), daemon=True).start()
            return True

        # ── Kod Yaz ve Çalıştır ───────────────────────────────────────────────
        if "kod yaz" in t:
            task = t.replace("kod yaz","").strip()
            if task:
                threading.Thread(target=self._write_code, args=(task,), daemon=True).start()
            return True

        # ── Proje Planı ───────────────────────────────────────────────────────
        if "proje planı" in t:
            project = t.replace("proje planı","").replace("oluştur","").strip()
            if project:
                threading.Thread(target=self._project_plan, args=(project,), daemon=True).start()
            return True

        # ── Verimlilik Skoru ──────────────────────────────────────────────────
        if "verimlilik" in t or "ne kadar verimli" in t:
            threading.Thread(target=self._productivity_score, daemon=True).start()
            return True

        # ── Duruş Hatırlatıcı ────────────────────────────────────────────────
        if "duruş" in t or "dik otur" in t:
            r = "🪑 Duruşunuzu kontrol edin efendim! Dik oturun, omuzlarınızı gerin, ekrana 50-60cm uzaklıkta olun."
            self.msg("ANKA", r); self.speak(r)
            return True

        # ── Egzersiz Önerisi ─────────────────────────────────────────────────
        if "egzersiz öner" in t or "antrenman öner" in t:
            threading.Thread(target=self._workout_plan, daemon=True).start()
            return True

        # ── Reddit Haberleri ──────────────────────────────────────────────────
        if "reddit" in t:
            threading.Thread(target=self._reddit_news, daemon=True).start()
            return True

        # ── Trend Konular ─────────────────────────────────────────────────────
        if "trend" in t or "gündem" in t:
            threading.Thread(target=self._trending, daemon=True).start()
            return True

        return False

    def _analyze_screen(self):
        try:
            import tempfile
            path = os.path.join(tempfile.gettempdir(), "anka_screen_analysis.png")
            pyautogui.screenshot(path)
            # OpenRouter Vision API ile analiz
            import base64
            with open(path, "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode()
            reply = self.ollama.chat(
                "Bu ekran görüntüsünde ne görüyorsun? Kısaca açıkla.",
                system_override="Ekran görüntüsünü analiz et ve Türkçe açıkla."
            )
            self.msg("ANKA", f"🖥 Ekran analizi:\n{reply}")
            self.speak(reply[:200])
        except Exception as e:
            self.msg("ANKA", f"Ekran analizi yapılamadı: {e}")

    def _write_article(self, topic):
        reply = self.ollama.chat(
            f"'{topic}' hakkında 3-4 paragraflık bilgilendirici bir makale yaz. Türkçe.",
            system_override="Sen bir içerik yazarısın. Bilgilendirici ve akıcı yaz."
        )
        self.msg("ANKA", f"📄 {topic.capitalize()} Makalesi:\n\n{reply}")
        pyperclip.copy(reply)
        self.speak("Makale hazırlandı ve panoya kopyalandı efendim.")

    def _write_code(self, task):
        reply = self.ollama.chat(
            f"Şu görevi yapan Python kodu yaz: {task}. Sadece kodu yaz, açıklama az tut.",
            system_override="Sen bir Python programcısısın. Temiz, çalışan kod yaz."
        )
        self.msg("ANKA", f"💻 Kod:\n\n{reply}")
        pyperclip.copy(reply)
        self.speak("Kod hazırlandı ve panoya kopyalandı efendim.")

    def _project_plan(self, project):
        reply = self.ollama.chat(
            f"'{project}' projesi için adım adım proje planı oluştur. Türkçe, madde madde.",
            system_override="Sen bir proje yöneticisisin. Pratik ve uygulanabilir plan yap."
        )
        self.msg("ANKA", f"📋 {project} Proje Planı:\n\n{reply}")
        self.speak("Proje planı hazırlandı efendim.")

    def _productivity_score(self):
        from anka_memory import get_pending_tasks, get_daily_log, load_health
        tasks = get_pending_tasks()
        logs = get_daily_log()
        h = load_health()
        water = h.get("water_count", 0)
        water_goal = h.get("water_goal", 8)
        score = 0
        if len(logs) > 5: score += 25
        if water >= water_goal: score += 25
        if len(tasks) < 3: score += 25
        score += min(25, len(logs) * 2)
        emoji = "🏆" if score >= 80 else "👍" if score >= 60 else "💪" if score >= 40 else "📈"
        r = f"{emoji} Bugünkü verimlilik skorunuz: {score}/100\n"
        r += f"• {len(logs)} aktivite\n• Su: {water}/{water_goal}\n• {len(tasks)} bekleyen görev"
        self.msg("ANKA", r)
        self.speak(f"Verimlilik skorunuz {score} üzerinden 100 efendim.")

    def _workout_plan(self):
        reply = self.ollama.chat(
            "Evde yapılabilecek 15 dakikalık egzersiz planı ver. Madde madde, Türkçe.",
            system_override="Sen bir fitness koçusun. Pratik egzersizler öner."
        )
        self.msg("ANKA", f"💪 Egzersiz Planı:\n\n{reply}")
        self.speak("Egzersiz planı hazırlandı efendim.")

    def _reddit_news(self):
        try:
            r = requests.get(
                "https://www.reddit.com/r/turkey/top.json?limit=5&t=day",
                headers={"User-Agent": "AnkaBot/1.0"}, timeout=5
            )
            posts = r.json()["data"]["children"]
            if posts:
                result = "📱 Reddit r/turkey günün en çok konuşulanları:\n"
                result += "\n".join(f"• {p['data']['title'][:60]}" for p in posts)
                self.msg("ANKA", result)
                self.speak(f"Reddit'te bugün {len(posts)} popüler konu var efendim.")
            else:
                self.msg("ANKA", "Reddit haberleri alınamadı.")
        except Exception as e:
            self.msg("ANKA", f"Reddit bağlantı hatası: {e}")

    def _trending(self):
        try:
            r = requests.get("https://trends.google.com/trends/trendingsearches/daily/rss?geo=TR",
                            timeout=5)
            import xml.etree.ElementTree as ET
            root = ET.fromstring(r.text)
            trends = []
            for item in root.findall(".//item")[:5]:
                title = item.find("title")
                if title is not None:
                    trends.append(title.text)
            if trends:
                result = "🔥 Türkiye'de gündem:\n" + "\n".join(f"• {t}" for t in trends)
                self.msg("ANKA", result)
                self.speak(f"Bugün Türkiye gündeminde {len(trends)} konu var efendim.")
            else:
                self.msg("ANKA", "Trend konular alınamadı.")
        except:
            self.msg("ANKA", "Trend konular şu an alınamıyor efendim.")
