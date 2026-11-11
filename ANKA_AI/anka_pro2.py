# ── ANKA PRO 2 — Şaşırtıcı Yeni Özellikler ───────────────────────────────────
try:
    import pyperclip
except ImportError:
    class _PyClip:
        def copy(self,x):pass
        def paste(self):return ""
    pyperclip=_PyClip()
import json, os, time, threading, datetime, subprocess, webbrowser, re
import requests, random, math, psutil, hashlib
from anka_config import BASE_DIR, USER_NAME

PRO2_FILE = os.path.join(BASE_DIR, "anka_pro2.json")

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
# 1. SPOR & FİTNES KOÇU
# ═══════════════════════════════════════════════════════════════════════════════
class SportsCoach:
    def __init__(self, ollama, speak_func, msg_func):
        self.ollama = ollama
        self.speak = speak_func
        self.msg = msg_func
        self.workout_file = os.path.join(BASE_DIR, "anka_workout.json")
        self.data = _load(self.workout_file, {
            "sessions": [], "goals": {}, "streak": 0, "last_workout": None
        })

    def create_workout_plan(self, goal="genel", level="başlangıç", days=3):
        def _w():
            r = self.ollama.chat(
                f"Hedef: {goal}, Seviye: {level}, Haftalık {days} gün antrenman planı yap. "
                f"Her antrenman için: egzersizler, set/tekrar sayısı, dinlenme süresi.",
                system_override="Kişisel fitness antrenörü. Detaylı plan yap.")
            path = os.path.join(os.path.expanduser("~"), "Desktop", "anka_antrenman.txt")
            with open(path, 'w', encoding='utf-8') as f:
                f.write(r)
            self.msg("ANKA", f"💪 Antrenman Planı:\n{r}")
            pyperclip.copy(r)
            self.speak("Antrenman planı hazırlandı efendim.")
        threading.Thread(target=_w, daemon=True).start()

    def log_workout(self, exercise, sets, reps, weight=0):
        session = {
            "exercise": exercise, "sets": sets, "reps": reps,
            "weight": weight, "date": datetime.date.today().isoformat(),
            "time": datetime.datetime.now().strftime("%H:%M")
        }
        self.data["sessions"].append(session)
        # Streak hesapla
        today = datetime.date.today().isoformat()
        last = self.data.get("last_workout")
        if last:
            last_date = datetime.date.fromisoformat(last)
            diff = (datetime.date.today() - last_date).days
            if diff == 1:
                self.data["streak"] = self.data.get("streak", 0) + 1
            elif diff > 1:
                self.data["streak"] = 1
        else:
            self.data["streak"] = 1
        self.data["last_workout"] = today
        _save(self.workout_file, self.data)
        streak = self.data["streak"]
        emoji = "🔥" if streak >= 7 else "💪"
        r = (f"{emoji} Antrenman kaydedildi!\n"
             f"• {exercise}: {sets}x{reps}" + (f" ({weight}kg)" if weight else "") +
             f"\n• Seri: {streak} gün!")
        self.msg("ANKA", r); self.speak(r)

    def workout_stats(self):
        sessions = self.data["sessions"]
        if not sessions:
            self.msg("ANKA", "Henüz antrenman kaydı yok efendim."); return
        today = datetime.date.today().isoformat()
        this_week = [s for s in sessions if s["date"] >= (datetime.date.today() - datetime.timedelta(days=7)).isoformat()]
        exercises = {}
        for s in this_week:
            exercises[s["exercise"]] = exercises.get(s["exercise"], 0) + 1
        r = (f"💪 Antrenman İstatistikleri:\n{'═'*30}\n"
             f"• Toplam Seans: {len(sessions)}\n"
             f"• Bu Hafta: {len(this_week)}\n"
             f"• Seri: {self.data.get('streak',0)} gün\n"
             f"• En Çok: {max(exercises, key=exercises.get) if exercises else 'veri yok'}")
        self.msg("ANKA", r); self.speak(r)

    def suggest_exercise(self, muscle="tüm vücut"):
        def _s():
            r = self.ollama.chat(
                f"{muscle} için 5 etkili egzersiz öner. Her biri için doğru form ve dikkat noktaları.",
                system_override="Fitness uzmanı. Güvenli egzersiz öner.")
            self.msg("ANKA", f"🏋️ {muscle} Egzersizleri:\n{r}")
        threading.Thread(target=_s, daemon=True).start()

    def calorie_calculator(self, food, amount=100):
        def _c():
            r = self.ollama.chat(
                f"{amount}gr {food} için kalori ve besin değerlerini ver. "
                f"Protein, karbonhidrat, yağ miktarlarını belirt.",
                system_override="Diyetisyen. Besin değerleri ver.")
            self.msg("ANKA", f"🍽️ {food} ({amount}gr):\n{r}")
        threading.Thread(target=_c, daemon=True).start()


# ═══════════════════════════════════════════════════════════════════════════════
# 2. KİTAP & OKUMA ASISTANI
# ═══════════════════════════════════════════════════════════════════════════════
class BookAssistant:
    def __init__(self, ollama, speak_func, msg_func):
        self.ollama = ollama
        self.speak = speak_func
        self.msg = msg_func
        self.books_file = os.path.join(BASE_DIR, "anka_books.json")
        self.data = _load(self.books_file, {
            "reading": [], "read": [], "wishlist": [], "notes": {}
        })

    def add_book(self, title, author="", status="okuyorum"):
        book = {
            "title": title, "author": author, "status": status,
            "added": datetime.date.today().isoformat(),
            "progress": 0, "rating": 0
        }
        if status == "okuyorum":
            self.data["reading"].append(book)
        elif status == "okudum":
            self.data["read"].append(book)
        else:
            self.data["wishlist"].append(book)
        _save(self.books_file, self.data)
        emoji = "📖" if status=="okuyorum" else "✅" if status=="okudum" else "📚"
        r = f"{emoji} '{title}' kitap listesine eklendi ({status})"
        self.msg("ANKA", r); self.speak(r)

    def book_summary(self, title):
        def _s():
            r = self.ollama.chat(
                f"'{title}' kitabını özetle. Ana temalar, karakterler, önemli mesajlar.",
                system_override="Edebiyat uzmanı. Kapsamlı özet yaz.")
            self.msg("ANKA", f"📖 {title} Özeti:\n{r}")
            pyperclip.copy(r)
            self.speak("Kitap özeti hazırlandı efendim.")
        threading.Thread(target=_s, daemon=True).start()

    def recommend_books(self, genre="", mood=""):
        def _r():
            prompt = f"{'Tür: ' + genre if genre else ''} {'Ruh hali: ' + mood if mood else ''}"
            r = self.ollama.chat(
                f"Bu kriterlere göre 5 kitap öner: {prompt}\n"
                f"Her kitap için: isim, yazar, kısa açıklama, neden okumalı.",
                system_override="Kitap küratörü. Kişiselleştirilmiş öneri yap.")
            self.msg("ANKA", f"📚 Kitap Önerileri:\n{r}")
        threading.Thread(target=_r, daemon=True).start()

    def reading_stats(self):
        r = (f"📚 Okuma İstatistikleri:\n{'═'*30}\n"
             f"• Okuduklarım: {len(self.data['read'])}\n"
             f"• Şu An Okuduklarım: {len(self.data['reading'])}\n"
             f"• İstek Listem: {len(self.data['wishlist'])}\n"
             f"• Toplam: {len(self.data['read'])+len(self.data['reading'])+len(self.data['wishlist'])}")
        if self.data["reading"]:
            r += "\n\n📖 Şu An:\n" + "\n".join(f"• {b['title']}" for b in self.data["reading"][:3])
        self.msg("ANKA", r)

    def add_note(self, book_title, note):
        if book_title not in self.data["notes"]:
            self.data["notes"][book_title] = []
        self.data["notes"][book_title].append({
            "note": note, "date": datetime.date.today().isoformat()
        })
        _save(self.books_file, self.data)
        r = f"📝 '{book_title}' için not kaydedildi efendim."
        self.msg("ANKA", r); self.speak(r)

    def daily_reading_goal(self, pages=20):
        r = (f"📖 Günlük Okuma Hedefi: {pages} sayfa\n"
             f"💡 {pages} sayfa ≈ {pages*2} dakika\n"
             f"• Sabah {pages//2} sayfa\n"
             f"• Akşam {pages//2} sayfa\n"
             f"Başarılar efendim! 📚")
        self.msg("ANKA", r); self.speak(r)


# ═══════════════════════════════════════════════════════════════════════════════
# 3. SEYAHAT ASISTANI
# ═══════════════════════════════════════════════════════════════════════════════
class TravelAssistant:
    def __init__(self, ollama, speak_func, msg_func):
        self.ollama = ollama
        self.speak = speak_func
        self.msg = msg_func
        self.travel_file = os.path.join(BASE_DIR, "anka_travel.json")
        self.data = _load(self.travel_file, {"trips": [], "visited": [], "wishlist": []})

    def plan_trip(self, destination, days, budget="orta"):
        def _p():
            r = self.ollama.chat(
                f"Destinasyon: {destination}, Süre: {days} gün, Bütçe: {budget}\n"
                f"Gün gün seyahat planı yap. Gezilecek yerler, yeme-içme, konaklama önerileri.",
                system_override="Seyahat uzmanı. Detaylı gezi planı yap.")
            path = os.path.join(os.path.expanduser("~"), "Desktop",
                               f"anka_gezi_{destination.replace(' ','_')}.txt")
            with open(path, 'w', encoding='utf-8') as f:
                f.write(f"{destination} Gezi Planı\n{'='*40}\n{r}")
            self.msg("ANKA", f"✈️ {destination} Planı:\n{r}")
            pyperclip.copy(r)
            self.speak(f"{destination} seyahat planı hazırlandı efendim.")
        threading.Thread(target=_p, daemon=True).start()

    def packing_list(self, destination, duration, season="yaz"):
        def _pl():
            r = self.ollama.chat(
                f"{destination} için {duration} günlük {season} seyahati bavul listesi. "
                f"Kategorilere göre düzenle.",
                system_override="Seyahat uzmanı. Kapsamlı bavul listesi yap.")
            self.msg("ANKA", f"🧳 Bavul Listesi:\n{r}")
            pyperclip.copy(r)
        threading.Thread(target=_pl, daemon=True).start()

    def destination_info(self, destination):
        def _d():
            try:
                r = requests.get(
                    f"https://tr.wikipedia.org/api/rest_v1/page/summary/{destination.replace(' ','_')}",
                    timeout=5)
                if r.status_code == 200:
                    extract = r.json().get("extract","")[:500]
                    self.msg("ANKA", f"🌍 {destination}:\n{extract}")
                    self.speak(f"{destination} hakkında bilgi hazırlandı efendim.")
                else:
                    raise Exception()
            except:
                info = self.ollama.chat(
                    f"{destination} hakkında temel bilgi ver. İklim, para birimi, dil, kültür.",
                    system_override="Seyahat rehberi. Temel bilgi ver.")
                self.msg("ANKA", f"🌍 {destination}:\n{info}")
        threading.Thread(target=_d, daemon=True).start()

    def currency_info(self, country):
        def _c():
            try:
                r = requests.get("https://api.exchangerate-api.com/v4/latest/TRY", timeout=5)
                rates = r.json()["rates"]
                common = {"USD":"🇺🇸 Dolar","EUR":"🇪🇺 Euro","GBP":"🇬🇧 Sterlin",
                         "JPY":"🇯🇵 Yen","AED":"🇦🇪 Dirhem"}
                result = "💱 Para Birimleri (TRY bazlı):\n"
                for code, name in common.items():
                    rate = rates.get(code)
                    if rate:
                        result += f"• {name}: {1/rate:.2f} TL\n"
                self.msg("ANKA", result)
                self.speak("Döviz bilgisi hazırlandı efendim.")
            except:
                self.msg("ANKA", "Döviz bilgisi alınamadı efendim.")
        threading.Thread(target=_c, daemon=True).start()

    def add_visited(self, city, rating=5, note=""):
        self.data["visited"].append({
            "city": city, "rating": rating,
            "note": note, "date": datetime.date.today().isoformat()
        })
        _save(self.travel_file, self.data)
        r = f"✅ '{city}' ziyaret listesine eklendi! ({rating}/5 ⭐)"
        self.msg("ANKA", r); self.speak(r)

    def travel_wishlist(self):
        if not self.data["wishlist"]:
            r = "Seyahat istek listeniz boş efendim. 'gitmek istiyorum [şehir]' ile ekleyin."
        else:
            r = f"🗺️ Seyahat İstek Listesi:\n"
            r += "\n".join(f"• {w}" for w in self.data["wishlist"][:10])
        self.msg("ANKA", r)


# ═══════════════════════════════════════════════════════════════════════════════
# 4. FİNANS KOÇU PRO
# ═══════════════════════════════════════════════════════════════════════════════
class FinanceCoachPro:
    def __init__(self, ollama, speak_func, msg_func):
        self.ollama = ollama
        self.speak = speak_func
        self.msg = msg_func
        self.finance_file = os.path.join(BASE_DIR, "anka_finance_pro.json")
        self.data = _load(self.finance_file, {
            "income": 0, "expenses": [], "savings_goal": 0,
            "budget": {}, "investments": []
        })

    def set_budget(self, category, amount):
        self.data["budget"][category] = {"limit": amount, "spent": 0}
        _save(self.finance_file, self.data)
        r = f"💰 Bütçe ayarlandı: {category} = {amount}₺"
        self.msg("ANKA", r); self.speak(r)

    def log_expense(self, amount, category, description=""):
        expense = {
            "amount": amount, "category": category,
            "description": description, "date": datetime.date.today().isoformat()
        }
        self.data["expenses"].append(expense)
        # Bütçe kontrol
        if category in self.data["budget"]:
            self.data["budget"][category]["spent"] = \
                self.data["budget"][category].get("spent", 0) + amount
            limit = self.data["budget"][category]["limit"]
            spent = self.data["budget"][category]["spent"]
            if spent > limit:
                self.msg("ANKA", f"⚠️ {category} bütçesi aşıldı! ({spent}₺/{limit}₺)")
        _save(self.finance_file, self.data)
        r = f"💸 Harcama kaydedildi: {amount}₺ — {category}"
        self.msg("ANKA", r); self.speak(r)

    def monthly_report(self):
        today = datetime.date.today()
        month_start = today.replace(day=1).isoformat()
        month_expenses = [e for e in self.data["expenses"] if e["date"] >= month_start]
        total = sum(e["amount"] for e in month_expenses)
        by_cat = {}
        for e in month_expenses:
            by_cat[e["category"]] = by_cat.get(e["category"], 0) + e["amount"]
        r = (f"💰 AYLIK FİNANS RAPORU\n{'═'*30}\n"
             f"• Toplam Harcama: {total:,.0f}₺\n"
             f"• İşlem Sayısı: {len(month_expenses)}\n\n"
             f"📊 Kategoriler:\n")
        for cat, amt in sorted(by_cat.items(), key=lambda x: -x[1])[:8]:
            pct = int(amt/total*100) if total else 0
            r += f"• {cat}: {amt:,.0f}₺ (%{pct})\n"
        self.msg("ANKA", r); self.speak("Aylık finans raporu hazırlandı efendim.")

    def compound_interest(self, principal, rate, years, monthly=0):
        results = []
        total = principal
        for year in range(1, years+1):
            total = total * (1 + rate/100) + monthly * 12
            results.append((year, round(total, 2)))
        r = (f"📈 Bileşik Faiz Hesabı:\n"
             f"• Ana Para: {principal:,.0f}₺\n"
             f"• Yıllık Oran: %{rate}\n"
             f"• Süre: {years} yıl\n"
             + ("• Aylık Katkı: {monthly:,.0f}₺\n" if monthly else "") +
             f"\n{'─'*20}\n")
        for year, total in results[::max(1,years//5)][:5]:
            r += f"• {year}. yıl: {total:,.2f}₺\n"
        r += f"\n💰 {years}. yıl sonu: {results[-1][1]:,.2f}₺"
        self.msg("ANKA", r); self.speak(f"{years} yıl sonunda {results[-1][1]:,.0f} lira efendim.")

    def investment_advice(self, amount, risk="orta", horizon="uzun"):
        def _i():
            r = self.ollama.chat(
                f"Yatırım: {amount}₺, Risk toleransı: {risk}, Vade: {horizon}\n"
                f"Portföy önerisi yap. Dağılım yüzdelerini belirt.",
                system_override="Finansal danışman. Kişiselleştirilmiş portföy öner.")
            self.msg("ANKA", f"📈 Yatırım Önerisi:\n{r}")
            self.speak("Yatırım tavsiyesi hazırlandı efendim.")
        threading.Thread(target=_i, daemon=True).start()

    def savings_plan(self, goal_amount, months):
        monthly = goal_amount / months
        r = (f"💰 Tasarruf Planı:\n"
             f"• Hedef: {goal_amount:,.0f}₺\n"
             f"• Süre: {months} ay\n"
             f"• Aylık Tasarruf: {monthly:,.0f}₺\n"
             f"• Günlük Tasarruf: {monthly/30:,.0f}₺\n"
             f"💡 İpucu: Maaş gelir gelmez {monthly:,.0f}₺ ayır efendim!")
        self.msg("ANKA", r); self.speak(r[:200])


# ═══════════════════════════════════════════════════════════════════════════════
# KOMUT İŞLEYİCİ
# ═══════════════════════════════════════════════════════════════════════════════
class Pro2CommandProcessor:
    def __init__(self, speak_func, msg_func, ollama):
        self.speak = speak_func
        self.msg = msg_func
        self.ollama = ollama
        self.sports = SportsCoach(ollama, speak_func, msg_func)
        self.books = BookAssistant(ollama, speak_func, msg_func)
        self.travel = TravelAssistant(ollama, speak_func, msg_func)
        self.finance = FinanceCoachPro(ollama, speak_func, msg_func)

    def process(self, text):
        t = text.lower().strip()

        # ── Spor & Fitness ────────────────────────────────────────────────────
        if "antrenman planı" in t:
            goal = "genel"
            for g in ["kilo ver","kas kazan","dayanıklılık","güç"]:
                if g in t: goal = g; break
            level = "orta" if "orta" in t else "ileri" if "ileri" in t else "başlangıç"
            m = re.search(r'(\d+)\s*gün', t)
            days = int(m.group(1)) if m else 3
            self.sports.create_workout_plan(goal, level, days); return True

        if "antrenman kaydet" in t or "egzersiz yaptım" in t:
            parts = t.replace("antrenman kaydet","").replace("egzersiz yaptım","").strip().split(",")
            if parts:
                exercise = parts[0].strip()
                nums = re.findall(r'\d+', t)
                sets = int(nums[0]) if len(nums) > 0 else 3
                reps = int(nums[1]) if len(nums) > 1 else 10
                weight = int(nums[2]) if len(nums) > 2 else 0
                self.sports.log_workout(exercise, sets, reps, weight); return True

        if "antrenman istatistik" in t or "spor özeti" in t:
            self.sports.workout_stats(); return True

        if "egzersiz öner" in t:
            muscle = t.replace("egzersiz öner","").strip() or "tüm vücut"
            self.sports.suggest_exercise(muscle); return True

        if "kalori hesapla" in t:
            parts = t.replace("kalori hesapla","").strip().split(",")
            food = parts[0].strip() if parts else "elma"
            m = re.search(r'(\d+)', parts[1] if len(parts) > 1 else "100")
            amount = int(m.group(1)) if m else 100
            self.sports.calorie_calculator(food, amount); return True

        # ── Kitap Asistanı ────────────────────────────────────────────────────
        if "kitap ekle" in t or "okuyorum" in t:
            book = t.replace("kitap ekle","").replace("okuyorum","").strip()
            status = "okudum" if "okudum" in t else "okuyorum"
            if book: self.books.add_book(book, status=status); return True

        if "kitap özeti" in t:
            book = t.replace("kitap özeti","").strip()
            if book: self.books.book_summary(book); return True

        if "kitap öner" in t:
            genre = ""
            for g in ["roman","bilim kurgu","kişisel gelişim","tarih","felsefe","polisiye"]:
                if g in t: genre = g; break
            self.books.recommend_books(genre=genre); return True

        if "okuma istatistik" in t or "kitaplığım" in t:
            self.books.reading_stats(); return True

        if "kitap notu" in t:
            parts = t.replace("kitap notu","").strip().split("|")
            if len(parts) >= 2:
                self.books.add_note(parts[0].strip(), parts[1].strip()); return True

        if "günlük okuma hedefi" in t:
            m = re.search(r'(\d+)', t)
            pages = int(m.group(1)) if m else 20
            self.books.daily_reading_goal(pages); return True

        # ── Seyahat Asistanı ──────────────────────────────────────────────────
        if "gezi planı" in t or "seyahat planla" in t:
            dest = t.replace("gezi planı","").replace("seyahat planla","").strip()
            m = re.search(r'(\d+)\s*gün', t)
            days = int(m.group(1)) if m else 5
            budget = "lüks" if "lüks" in t else "ekonomik" if "ekonomik" in t else "orta"
            dest = re.sub(r'\d+\s*gün','', dest).strip()
            if dest: self.travel.plan_trip(dest, days, budget); return True

        if "bavul listesi" in t:
            dest = t.replace("bavul listesi","").strip()
            m = re.search(r'(\d+)', t)
            days = int(m.group(1)) if m else 7
            season = "kış" if "kış" in t else "ilkbahar" if "ilkbahar" in t else "yaz"
            if dest: self.travel.packing_list(dest, days, season); return True

        if "şehir hakkında" in t or "ülke hakkında" in t:
            dest = t.replace("şehir hakkında","").replace("ülke hakkında","").strip()
            if dest: self.travel.destination_info(dest); return True

        if "gitmek istiyorum" in t:
            dest = t.replace("gitmek istiyorum","").strip()
            if dest:
                self.travel.data["wishlist"].append(dest)
                _save(self.travel.travel_file, self.travel.data)
                r = f"🗺️ '{dest}' seyahat listenize eklendi efendim!"
                self.msg("ANKA", r); self.speak(r); return True

        if "seyahat listem" in t:
            self.travel.travel_wishlist(); return True

        if "ziyaret ettim" in t:
            city = t.replace("ziyaret ettim","").strip()
            m = re.search(r'(\d+)/5', t)
            rating = int(m.group(1)) if m else 5
            if city: self.travel.add_visited(city, rating); return True

        if "döviz bilgisi" in t and "seyahat" in t:
            self.travel.currency_info("genel"); return True

        # ── Finans Koçu Pro ───────────────────────────────────────────────────
        if "bütçe ayarla" in t:
            parts = t.replace("bütçe ayarla","").strip().split(",")
            if len(parts) >= 2:
                cat = parts[0].strip()
                m = re.search(r'(\d+)', parts[1])
                if m: self.finance.set_budget(cat, int(m.group(1))); return True

        if "harcama kaydet" in t or "para harcadım" in t:
            m = re.search(r'(\d+(?:\.\d+)?)', t)
            if m:
                amount = float(m.group(1))
                cat_words = ["yemek","ulaşım","eğlence","alışveriş","fatura","sağlık","eğitim"]
                cat = next((c for c in cat_words if c in t), "diğer")
                self.finance.log_expense(amount, cat); return True

        if "aylık rapor" in t or "finans raporu" in t:
            self.finance.monthly_report(); return True

        if "bileşik faiz" in t:
            nums = re.findall(r'(\d+(?:\.\d+)?)', t)
            if len(nums) >= 3:
                self.finance.compound_interest(
                    float(nums[0]), float(nums[1]), int(nums[2]),
                    float(nums[3]) if len(nums) > 3 else 0); return True

        if "yatırım tavsiyesi" in t:
            m = re.search(r'(\d+)', t)
            amount = int(m.group(1)) if m else 10000
            risk = "yüksek" if "yüksek" in t else "düşük" if "düşük" in t else "orta"
            self.finance.investment_advice(amount, risk); return True

        if "tasarruf planı" in t:
            nums = re.findall(r'(\d+)', t)
            if len(nums) >= 2:
                self.finance.savings_plan(int(nums[0]), int(nums[1])); return True

        return False
