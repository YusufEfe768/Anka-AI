# ── ANKA ULTIMATE ÖZELLİKLER MODÜLü ─────────────────────────────────────────
import json, os, time, threading, datetime, subprocess, random, webbrowser
import requests, re, math
from anka_config import BASE_DIR

JOURNAL_FILE  = os.path.join(BASE_DIR, "anka_journal.json")
WISHLIST_FILE = os.path.join(BASE_DIR, "anka_wishlist.json")
CONTACT_FILE  = os.path.join(BASE_DIR, "anka_contacts.json")
RECIPE_FILE   = os.path.join(BASE_DIR, "anka_recipes.json")
STOCK_FILE    = os.path.join(BASE_DIR, "anka_stocks.json")

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


# ── Günlük / Diari ───────────────────────────────────────────────────────────
class Journal:
    def add_entry(self, text, mood=None):
        data = _load(JOURNAL_FILE, [])
        data.append({
            "text": text,
            "mood": mood or "normal",
            "date": datetime.datetime.now().isoformat()
        })
        _save(JOURNAL_FILE, data)

    def get_today(self):
        data = _load(JOURNAL_FILE, [])
        today = datetime.date.today().isoformat()
        return [e for e in data if e["date"].startswith(today)]

    def get_last(self, days=7):
        data = _load(JOURNAL_FILE, [])
        cutoff = (datetime.date.today() - datetime.timedelta(days=days)).isoformat()
        return [e for e in data if e["date"] >= cutoff]

    def get_summary(self, ollama):
        entries = self.get_last(7)
        if not entries:
            return "Son 7 günde günlük girişi yok efendim."
        text = "\n".join(f"[{e['date'][:10]}] {e['text']}" for e in entries)
        return ollama.chat(
            f"Bu günlük girişlerini özetle ve genel ruh halini analiz et:\n{text}",
            system_override="Günlük girişlerini analiz et. Kısa ve destekleyici yaz."
        )


# ── İstek Listesi ─────────────────────────────────────────────────────────────
class WishList:
    def add(self, item, price=None, priority="orta"):
        data = _load(WISHLIST_FILE, [])
        data.append({
            "item": item, "price": price,
            "priority": priority,
            "added": datetime.date.today().isoformat(),
            "bought": False
        })
        _save(WISHLIST_FILE, data)

    def get_all(self):
        return [i for i in _load(WISHLIST_FILE, []) if not i.get("bought")]

    def mark_bought(self, item_name):
        data = _load(WISHLIST_FILE, [])
        for item in data:
            if item_name.lower() in item["item"].lower():
                item["bought"] = True
        _save(WISHLIST_FILE, data)


# ── Kişi Rehberi ──────────────────────────────────────────────────────────────
class ContactBook:
    def add(self, name, phone=None, email=None, notes=None):
        data = _load(CONTACT_FILE, {})
        data[name.lower()] = {
            "name": name, "phone": phone,
            "email": email, "notes": notes,
            "added": datetime.date.today().isoformat()
        }
        _save(CONTACT_FILE, data)

    def find(self, name):
        data = _load(CONTACT_FILE, {})
        for key, val in data.items():
            if name.lower() in key:
                return val
        return None

    def list_all(self):
        return list(_load(CONTACT_FILE, {}).values())


# ── Yemek Tarifi ──────────────────────────────────────────────────────────────
RECIPES = {
    "omlet": {
        "malzeme": ["3 yumurta","1 tutam tuz","tereyağı","peynir (isteğe bağlı)"],
        "yapılış": ["Yumurtaları kırıp çırpın","Tavayı tereyağıyla ısıtın",
                    "Yumurtaları dökün, karıştırın","Peynir ekleyin, katlayın","Servis edin"]
    },
    "makarna": {
        "malzeme": ["250g makarna","domates sosu","tuz","zeytinyağı","parmesan"],
        "yapılış": ["Suyu kaynatın, tuz ekleyin","Makarnayı 8-10 dakika pişirin",
                    "Domates sosunu ısıtın","Makarnayı sosla karıştırın","Parmesan serpin"]
    },
    "çay": {
        "malzeme": ["2 çay kaşığı çay","1 bardak su","şeker (isteğe bağlı)"],
        "yapılış": ["Suyu kaynatın","Çaydanlığa çay ekleyin","5 dakika demlendirin","Bardağa dökün"]
    },
}

def get_recipe(name, ollama):
    name_l = name.lower()
    if name_l in RECIPES:
        r = RECIPES[name_l]
        return (f"🍳 {name.capitalize()} Tarifi:\n\n"
                f"📦 Malzemeler:\n" + "\n".join(f"• {m}" for m in r["malzeme"]) +
                f"\n\n👨‍🍳 Yapılışı:\n" + "\n".join(f"{i+1}. {s}" for i,s in enumerate(r["yapılış"])))
    else:
        return ollama.chat(
            f"'{name}' yemeği için basit bir tarif ver. Malzeme ve yapılışını madde madde yaz.",
            system_override="Sen bir aşçısın. Pratik ve kolay tarif ver."
        )


# ── Hisse Takibi ──────────────────────────────────────────────────────────────
class StockWatcher:
    def __init__(self, speak_func, msg_func):
        self.speak = speak_func
        self.msg = msg_func
        self.watchlist = _load(STOCK_FILE, [])

    def add(self, symbol):
        if symbol.upper() not in self.watchlist:
            self.watchlist.append(symbol.upper())
            _save(STOCK_FILE, self.watchlist)

    def get_price(self, symbol):
        try:
            r = requests.get(
                f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}",
                timeout=5)
            d = r.json()
            price = d["chart"]["result"][0]["meta"]["regularMarketPrice"]
            return price
        except: return None

    def check_all(self):
        results = []
        for sym in self.watchlist[:5]:
            price = self.get_price(sym)
            if price:
                results.append(f"• {sym}: {price:.2f}")
        return results


# ── Döviz Hesaplayıcı ────────────────────────────────────────────────────────
def convert_currency(amount, from_cur, to_cur):
    try:
        r = requests.get(
            f"https://api.exchangerate-api.com/v4/latest/{from_cur.upper()}",
            timeout=5)
        rates = r.json()["rates"]
        if to_cur.upper() in rates:
            result = amount * rates[to_cur.upper()]
            return round(result, 2)
    except: pass
    return None


# ── Hava Tahmini (5 günlük) ───────────────────────────────────────────────────
def get_forecast():
    try:
        r = requests.get("https://wttr.in/Istanbul?format=j1", timeout=5)
        d = r.json()
        forecast = []
        for day in d.get("weather", [])[:5]:
            date = day["date"]
            max_temp = day["maxtempC"]
            min_temp = day["mintempC"]
            desc = day["hourly"][4]["weatherDesc"][0]["value"]
            forecast.append(f"📅 {date}: {min_temp}°C - {max_temp}°C, {desc}")
        return forecast
    except: return []


# ── Şiir Yazıcı ──────────────────────────────────────────────────────────────
POEM_STYLES = ["haikü","sone","serbest","dörtlük","rubai"]

def write_poem(topic, style, ollama):
    return ollama.chat(
        f"'{topic}' konusunda {style} tarzında güzel bir şiir yaz. Türkçe.",
        system_override="Sen yetenekli bir şairsin. Duygusal ve etkileyici şiir yaz."
    )


# ── Bütçe Planlayıcı ─────────────────────────────────────────────────────────
def budget_plan(income, expenses_dict, ollama):
    total_exp = sum(expenses_dict.values())
    remaining = income - total_exp
    savings_rate = (remaining / income * 100) if income > 0 else 0

    report = (f"💰 Bütçe Analizi:\n"
              f"• Gelir: {income}₺\n"
              f"• Toplam Gider: {total_exp}₺\n"
              f"• Kalan: {remaining}₺\n"
              f"• Tasarruf Oranı: %{savings_rate:.1f}\n\n"
              f"Harcamalar:\n")
    for cat, amount in expenses_dict.items():
        pct = (amount/income*100) if income > 0 else 0
        report += f"• {cat}: {amount}₺ (%{pct:.0f})\n"

    advice = ollama.chat(
        f"Gelir {income}₺, gider {total_exp}₺, kalan {remaining}₺. Kısa finansal tavsiye ver.",
        system_override="Sen bir finansal danışmansın. Pratik tavsiye ver."
    )
    return report + f"\n💡 Tavsiye:\n{advice}"


# ── Hız Yazma Testi ──────────────────────────────────────────────────────────
TYPING_TEXTS = [
    "Yapay zeka geleceğin teknolojisidir ve hayatımızı değiştirmektedir.",
    "Bilgisayarlar insanların düşünemeyeceği hızda hesaplama yapabilir.",
    "Türkiye güzel bir ülkedir ve zengin bir kültüre sahiptir.",
    "Programlama öğrenmek geleceğe yapılan en iyi yatırımdır.",
]

class TypingTest:
    def __init__(self):
        self.text = None
        self.start_time = None
        self.active = False

    def start(self):
        self.text = random.choice(TYPING_TEXTS)
        self.active = True
        self.start_time = None
        return f"⌨️ Yazma testi! Şu metni yaz:\n\n'{self.text}'\n\nHazır olunca 'başla' de!"

    def begin(self):
        self.start_time = time.time()
        return "⏱ Başla! Metni yaz..."

    def submit(self, typed):
        if not self.active or not self.start_time:
            return "Önce 'yazma testi başlat' deyin efendim."
        elapsed = time.time() - self.start_time
        words = len(typed.split())
        wpm = int(words / elapsed * 60)
        # Doğruluk
        correct = sum(1 for a,b in zip(typed,self.text) if a==b)
        accuracy = int(correct/len(self.text)*100)
        self.active = False
        return (f"⌨️ Sonuç:\n"
                f"• Hız: {wpm} kelime/dakika\n"
                f"• Doğruluk: %{accuracy}\n"
                f"• Süre: {elapsed:.1f} saniye\n"
                f"{'🏆 Harika!' if wpm > 40 else '👍 İyi!' if wpm > 25 else '💪 Pratik yapın!'}")


# ── Hesap Makinesi Gelişmiş ───────────────────────────────────────────────────
def advanced_calc(expr):
    try:
        # Güvenli hesaplama
        allowed = set('0123456789+-*/().% ')
        if not all(c in allowed for c in expr):
            return None
        result = eval(expr)
        return result
    except: return None

def unit_convert(value, from_unit, to_unit):
    conversions = {
        ("km","mil"): 0.621371, ("mil","km"): 1.60934,
        ("kg","pound"): 2.20462, ("pound","kg"): 0.453592,
        ("metre","feet"): 3.28084, ("feet","metre"): 0.3048,
        ("litre","galon"): 0.264172, ("galon","litre"): 3.78541,
        ("celsius","fahrenheit"): lambda x: x*9/5+32,
        ("fahrenheit","celsius"): lambda x: (x-32)*5/9,
    }
    key = (from_unit.lower(), to_unit.lower())
    if key in conversions:
        conv = conversions[key]
        result = conv(value) if callable(conv) else value * conv
        return round(result, 4)
    return None


# ── Kişisel AI Koçu ───────────────────────────────────────────────────────────
class PersonalCoach:
    def __init__(self, ollama):
        self.ollama = ollama
        self.sessions = []

    def daily_checkin(self):
        questions = [
            "Bugün kendinizi nasıl hissediyorsunuz?",
            "Bugün ne başardınız?",
            "Yarın için hedefleriniz neler?",
        ]
        return random.choice(questions)

    def get_advice(self, problem):
        return self.ollama.chat(
            f"Şu sorun için kısa ve pratik tavsiye ver: {problem}",
            system_override="Sen bir yaşam koçusun. Kısa, net ve uygulanabilir tavsiye ver."
        )

    def motivate(self, context=""):
        return self.ollama.chat(
            f"Bana güçlü bir motivasyon konuşması yap. {context}",
            system_override="Sen bir motivasyon konuşmacısısın. Enerji ver, ilham ver."
        )


# ── Komut İşleyici ────────────────────────────────────────────────────────────
class UltimateCommandProcessor:
    def __init__(self, speak_func, msg_func, ollama):
        self.speak = speak_func
        self.msg = msg_func
        self.ollama = ollama
        self.journal = Journal()
        self.wishlist = WishList()
        self.contacts = ContactBook()
        self.stocks = StockWatcher(speak_func, msg_func)
        self.typing_test = TypingTest()
        self.coach = PersonalCoach(ollama)

    def process(self, text):
        t = text.lower().strip()

        # ── Günlük ───────────────────────────────────────────────────────────
        if "günlüğe yaz" in t or "günlük:" in t:
            entry = t.replace("günlüğe yaz","").replace("günlük:","").strip()
            if entry:
                self.journal.add_entry(entry)
                r = "✓ Günlüğünüze kaydedildi efendim."
                self.msg("ANKA",r); self.speak(r)
            return True

        if "günlüğümü göster" in t or "günlük özeti" in t:
            entries = self.journal.get_today()
            if not entries:
                r = "Bugün günlük girişi yok efendim."
            else:
                r = "📔 Bugünkü günlük:\n" + "\n".join(f"• {e['text']}" for e in entries)
            self.msg("ANKA",r); self.speak(r)
            return True

        if "günlük analizi" in t or "haftalık günlük" in t:
            self.msg("ANKA","📔 Analiz yapılıyor...")
            threading.Thread(target=lambda: self._journal_summary(), daemon=True).start()
            return True

        # ── İstek Listesi ────────────────────────────────────────────────────
        if "istek listesi" in t and "ekle" in t:
            item = t.replace("istek listesine ekle","").replace("istek listesi ekle","").strip()
            if item:
                self.wishlist.add(item)
                r = f"✓ '{item}' istek listesine eklendi efendim."
                self.msg("ANKA",r); self.speak(r)
            return True

        if "istek listem" in t or "istek listesi göster" in t:
            items = self.wishlist.get_all()
            if not items:
                r = "İstek listeniz boş efendim."
            else:
                r = "🎁 İstek Listeniz:\n" + "\n".join(
                    f"• {i['item']}" + (f" (~{i['price']}₺)" if i['price'] else "")
                    for i in items)
            self.msg("ANKA",r); self.speak(r)
            return True

        # ── Kişi Rehberi ─────────────────────────────────────────────────────
        if "rehbere ekle" in t or "kişi ekle" in t:
            # "Ahmet'i rehbere ekle, telefon 05551234567"
            parts = t.replace("rehbere ekle","").replace("kişi ekle","").strip()
            phone_m = re.search(r'0?\d{10,11}', parts)
            phone = phone_m.group(0) if phone_m else None
            name = re.sub(r'0?\d{10,11}','',parts).replace("telefon","").replace(",","").strip()
            if name:
                self.contacts.add(name.capitalize(), phone)
                r = f"✓ {name.capitalize()} rehbere eklendi efendim."
                self.msg("ANKA",r); self.speak(r)
            return True

        if "rehber" in t and "göster" in t:
            contacts = self.contacts.list_all()
            if not contacts:
                r = "Rehberiniz boş efendim."
            else:
                r = "📞 Rehberiniz:\n" + "\n".join(
                    f"• {c['name']}" + (f": {c['phone']}" if c.get('phone') else "")
                    for c in contacts[:10])
            self.msg("ANKA",r); self.speak(r)
            return True

        if "ara" in t and "rehber" not in t:
            for c in self.contacts.list_all():
                if c['name'].lower() in t:
                    if c.get('phone'):
                        r = f"📞 {c['name']}: {c['phone']}"
                        self.msg("ANKA",r); self.speak(r)
                        return True

        # ── Yemek Tarifi ─────────────────────────────────────────────────────
        if "tarif" in t or "nasıl yapılır" in t:
            food = t.replace("tarifi","").replace("nasıl yapılır","").replace("tarif","").strip()
            if food:
                self.msg("ANKA","👨‍🍳 Tarif hazırlanıyor...")
                threading.Thread(target=lambda: self._recipe(food), daemon=True).start()
            return True

        # ── Hisse Senedi ─────────────────────────────────────────────────────
        if "hisse" in t and "ekle" in t:
            m = re.search(r'[A-Z]{2,6}', text.upper())
            if m:
                symbol = m.group(0)
                self.stocks.add(symbol)
                r = f"✓ {symbol} hisse takip listesine eklendi efendim."
                self.msg("ANKA",r); self.speak(r)
            return True

        if "hisselerim" in t or "portföy" in t:
            threading.Thread(target=self._check_stocks, daemon=True).start()
            return True

        # ── Para Çevirici ─────────────────────────────────────────────────────
        if "kaç" in t and any(c in t for c in ["dolar","euro","lira","pound","yen"]):
            m = re.search(r'(\d+(?:\.\d+)?)', t)
            if m:
                amount = float(m.group(1))
                currencies = {
                    "dolar": "USD", "euro": "EUR",
                    "lira": "TRY", "pound": "GBP", "yen": "JPY"
                }
                from_c = to_c = None
                for word, code in currencies.items():
                    if word in t:
                        if from_c is None: from_c = code
                        elif to_c is None: to_c = code
                if from_c and to_c:
                    result = convert_currency(amount, from_c, to_c)
                    if result:
                        r = f"💱 {amount} {from_c} = {result} {to_c}"
                        self.msg("ANKA",r); self.speak(r)
            return True

        # ── 5 Günlük Hava ────────────────────────────────────────────────────
        if "5 günlük hava" in t or "haftalık hava" in t:
            threading.Thread(target=self._forecast, daemon=True).start()
            return True

        # ── Şiir Yaz ─────────────────────────────────────────────────────────
        if "şiir yaz" in t:
            topic = t.replace("şiir yaz","").strip() or "hayat"
            style = next((s for s in POEM_STYLES if s in t), "serbest")
            self.msg("ANKA","✍️ Şiir yazılıyor...")
            threading.Thread(target=lambda: self._poem(topic, style), daemon=True).start()
            return True

        # ── Bütçe Planlama ────────────────────────────────────────────────────
        if "bütçe planı" in t:
            r = ("💰 Bütçe planı için önce gelirinizi söyleyin.\n"
                 "Örn: 'gelirim 10000 lira, kira 3000, market 2000, ulaşım 500'")
            self.msg("ANKA",r); self.speak(r)
            return True

        # ── Yazma Testi ──────────────────────────────────────────────────────
        if "yazma testi" in t:
            r = self.typing_test.start()
            self.msg("ANKA",r); self.speak(r)
            return True

        if "başla" in t and self.typing_test.active and not self.typing_test.start_time:
            r = self.typing_test.begin()
            self.msg("ANKA",r); self.speak(r)
            return True

        if self.typing_test.active and self.typing_test.start_time and len(t) > 10:
            r = self.typing_test.submit(text)
            self.msg("ANKA",r); self.speak(r)
            return True

        # ── Hesap Makinesi ────────────────────────────────────────────────────
        if "hesapla" in t or "kaç eder" in t:
            expr = t.replace("hesapla","").replace("kaç eder","").strip()
            result = advanced_calc(expr)
            if result is not None:
                r = f"🔢 {expr} = {result}"
                self.msg("ANKA",r); self.speak(r)
                return True

        # ── Birim Çevirici ───────────────────────────────────────────────────
        if "çevir" in t and any(u in t for u in ["km","mil","kg","pound","metre","feet","celsius","fahrenheit"]):
            m = re.search(r'(\d+(?:\.\d+)?)', t)
            if m:
                val = float(m.group(1))
                units = ["km","mil","kg","pound","metre","feet","celsius","fahrenheit","litre","galon"]
                found = [u for u in units if u in t]
                if len(found) >= 2:
                    result = unit_convert(val, found[0], found[1])
                    if result:
                        r = f"📐 {val} {found[0]} = {result} {found[1]}"
                        self.msg("ANKA",r); self.speak(r)
                        return True

        # ── Kişisel Koç ──────────────────────────────────────────────────────
        if "günlük kontrol" in t or "nasıl gidiyor" in t:
            q = self.coach.daily_checkin()
            self.msg("ANKA",q); self.speak(q)
            return True

        if "tavsiye ver" in t or "ne yapmalıyım" in t:
            problem = t.replace("tavsiye ver","").replace("ne yapmalıyım","").strip()
            if problem:
                threading.Thread(target=lambda: self._advice(problem), daemon=True).start()
            return True

        if "motive et" in t or "ilham ver" in t:
            threading.Thread(target=self._motivate, daemon=True).start()
            return True

        # ── Rastgele Şaka ─────────────────────────────────────────────────────
        if "şaka" in t or "espri" in t:
            threading.Thread(target=self._joke, daemon=True).start()
            return True

        # ── Falım Açılsın ────────────────────────────────────────────────────
        if "falıma bak" in t or "falım" in t:
            threading.Thread(target=self._fortune, daemon=True).start()
            return True

        # ── Hava Durumu Kıyafet Önerisi ──────────────────────────────────────
        if "ne giyeyim" in t or "kıyafet öner" in t:
            threading.Thread(target=self._clothing_advice, daemon=True).start()
            return True

        # ── Dua/Namaz Vakitleri ───────────────────────────────────────────────
        if "namaz vakti" in t or "ezan" in t:
            threading.Thread(target=self._prayer_times, daemon=True).start()
            return True

        # ── Sağlıklı Tarif Öner ───────────────────────────────────────────────
        if "sağlıklı yemek" in t or "diyet tarifi" in t:
            threading.Thread(target=self._healthy_recipe, daemon=True).start()
            return True

        # ── Döviz Kuru Grafiği ────────────────────────────────────────────────
        if "dolar grafiği" in t or "kur grafiği" in t:
            webbrowser.open("https://finance.yahoo.com/chart/USDTRY=X")
            r = "📈 Dolar/TL grafiği açıldı efendim."
            self.msg("ANKA",r); self.speak(r)
            return True

        return False

    # ── Yardımcı Metodlar ────────────────────────────────────────────────────
    def _journal_summary(self):
        summary = self.journal.get_summary(self.ollama)
        self.msg("ANKA", f"📔 Günlük Analizi:\n{summary}")
        self.speak(summary[:200])

    def _recipe(self, food):
        reply = get_recipe(food, self.ollama)
        self.msg("ANKA", reply)
        self.speak(f"{food} tarifi hazırlandı efendim.")

    def _check_stocks(self):
        results = self.stocks.check_all()
        if results:
            r = "📈 Hisseleriniz:\n" + "\n".join(results)
            self.msg("ANKA",r); self.speak("İşte hisse fiyatlarınız efendim.")
        else:
            self.msg("ANKA","Takip listesinde hisse yok. 'THYAO hisse ekle' gibi ekleyebilirsiniz.")

    def _forecast(self):
        forecast = get_forecast()
        if forecast:
            r = "🌤 5 Günlük Hava Tahmini:\n" + "\n".join(forecast)
            self.msg("ANKA",r); self.speak("İşte 5 günlük hava tahmini efendim.")
        else:
            self.msg("ANKA","Hava tahmini alınamadı efendim.")

    def _poem(self, topic, style):
        reply = write_poem(topic, style, self.ollama)
        self.msg("ANKA", f"📝 {style.capitalize()} Şiiri:\n\n{reply}")
        self.speak("Şiiriniz hazır efendim.")

    def _advice(self, problem):
        reply = self.coach.get_advice(problem)
        self.msg("ANKA", f"💡 Tavsiye:\n{reply}")
        self.speak(reply[:200])

    def _motivate(self):
        reply = self.coach.motivate()
        self.msg("ANKA", f"💪 {reply}")
        self.speak(reply[:300])

    def _joke(self):
        reply = self.ollama.chat(
            "Komik ve zekice bir Türkçe fıkra veya espri söyle.",
            system_override="Sen komik bir komedyensin. Kısa ve eğlenceli fıkra söyle."
        )
        self.msg("ANKA", f"😄 {reply}")
        self.speak(reply[:200])

    def _fortune(self):
        reply = self.ollama.chat(
            "Eğlenceli ve gizemli bir fal bak. Genel ve pozitif olsun.",
            system_override="Sen eğlenceli bir falcısın. Gizemli ama pozitif fal bak."
        )
        self.msg("ANKA", f"🔮 {reply}")
        self.speak(reply[:200])

    def _clothing_advice(self):
        try:
            r = requests.get("https://wttr.in/Istanbul?format=j1", timeout=5)
            d = r.json()["current_condition"][0]
            temp = int(d["temp_C"])
            desc = d["weatherDesc"][0]["value"]
            reply = self.ollama.chat(
                f"İstanbul'da hava {temp}°C ve {desc}. Bugün ne giyeyim? Kısa öner.",
                system_override="Hava durumuna göre kıyafet öner. Pratik ve kısa ol."
            )
            self.msg("ANKA", f"👗 Kıyafet Önerisi ({temp}°C):\n{reply}")
            self.speak(reply[:200])
        except:
            self.msg("ANKA","Hava bilgisi alınamadı efendim.")

    def _prayer_times(self):
        try:
            today = datetime.date.today()
            r = requests.get(
                f"https://api.aladhan.com/v1/timingsByCity/{today.day}-{today.month}-{today.year}"
                f"?city=Istanbul&country=Turkey&method=13",
                timeout=5)
            times = r.json()["data"]["timings"]
            result = (f"🕌 Bugün İstanbul Namaz Vakitleri:\n"
                      f"• İmsak: {times['Fajr']}\n"
                      f"• Güneş: {times['Sunrise']}\n"
                      f"• Öğle: {times['Dhuhr']}\n"
                      f"• İkindi: {times['Asr']}\n"
                      f"• Akşam: {times['Maghrib']}\n"
                      f"• Yatsı: {times['Isha']}")
            self.msg("ANKA", result)
            self.speak(f"Öğle namazı {times['Dhuhr']}, akşam namazı {times['Maghrib']} efendim.")
        except:
            self.msg("ANKA","Namaz vakitleri alınamadı efendim.")

    def _healthy_recipe(self):
        reply = self.ollama.chat(
            "Sağlıklı ve kolay yapılabilen bir yemek tarifi öner. Kalori bilgisi de ver.",
            system_override="Sen bir diyetisyensin. Sağlıklı ve lezzetli tarif ver."
        )
        self.msg("ANKA", f"🥗 Sağlıklı Tarif:\n{reply}")
        self.speak("Sağlıklı tarif hazırlandı efendim.")
