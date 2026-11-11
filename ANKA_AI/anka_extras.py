# ── ANKA EKSTRA ÖZELLİKLER MODÜLü ────────────────────────────────────────────
# Eğlence, kişi profilleri, hedefler, günlük öğrenme, geçmiş arama

import json, os, random, datetime, threading
from anka_config import BASE_DIR

PEOPLE_FILE   = os.path.join(BASE_DIR, "anka_people.json")
GOALS_FILE    = os.path.join(BASE_DIR, "anka_goals.json")
LEARN_FILE    = os.path.join(BASE_DIR, "anka_learning.json")
CHARACTER_FILE= os.path.join(BASE_DIR, "anka_character.json")

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


# ── Kişi Profilleri ───────────────────────────────────────────────────────────
def add_person(name, info_key, info_value):
    people = _load(PEOPLE_FILE, {})
    name_l = name.lower()
    if name_l not in people:
        people[name_l] = {"name": name}
    people[name_l][info_key] = info_value
    _save(PEOPLE_FILE, people)

def get_person_info(name, info_key=None):
    people = _load(PEOPLE_FILE, {})
    person = people.get(name.lower())
    if not person: return None
    if info_key:
        return person.get(info_key)
    return person

def list_people():
    return _load(PEOPLE_FILE, {})


# ── Hedefler ─────────────────────────────────────────────────────────────────
def set_daily_goal(text):
    goals = _load(GOALS_FILE, {})
    today = datetime.date.today().isoformat()
    if today not in goals:
        goals[today] = []
    goals[today].append({"text": text, "done": False})
    _save(GOALS_FILE, goals)

def get_today_goals():
    goals = _load(GOALS_FILE, {})
    today = datetime.date.today().isoformat()
    return goals.get(today, [])

def complete_goal(index):
    goals = _load(GOALS_FILE, {})
    today = datetime.date.today().isoformat()
    if today in goals and 0 <= index < len(goals[today]):
        goals[today][index]["done"] = True
        _save(GOALS_FILE, goals)
        return True
    return False


# ── Günlük Öğrenme (İngilizce kelime) ────────────────────────────────────────
WORD_BANK = [
    ("Achieve", "Başarmak"), ("Ambitious", "Hırslı"), ("Brilliant", "Parlak/Zeki"),
    ("Curious", "Meraklı"), ("Determined", "Kararlı"), ("Efficient", "Verimli"),
    ("Flexible", "Esnek"), ("Genuine", "Gerçek/Samimi"), ("Honest", "Dürüst"),
    ("Inspire", "İlham vermek"), ("Journey", "Yolculuk"), ("Knowledge", "Bilgi"),
    ("Loyal", "Sadık"), ("Mindful", "Dikkatli/Farkında"), ("Notice", "Fark etmek"),
    ("Opportunity", "Fırsat"), ("Patience", "Sabır"), ("Quality", "Kalite"),
    ("Resilient", "Dayanıklı"), ("Sincere", "Samimi"), ("Thoughtful", "Düşünceli"),
    ("Unique", "Eşsiz"), ("Valuable", "Değerli"), ("Wisdom", "Bilgelik"),
    ("Productive", "Üretken"), ("Grateful", "Minnettar"), ("Confident", "Kendine güvenen"),
    ("Persistent", "Azimli"), ("Authentic", "Özgün"), ("Diligent", "Çalışkan"),
]

def get_word_of_day():
    today = datetime.date.today().toordinal()
    word, meaning = WORD_BANK[today % len(WORD_BANK)]
    return word, meaning

def get_learned_count():
    data = _load(LEARN_FILE, {"learned": []})
    today = datetime.date.today().isoformat()
    if today not in data["learned"]:
        data["learned"].append(today)
        _save(LEARN_FILE, data)
    return len(data["learned"])


# ── Karakter Modu ─────────────────────────────────────────────────────────────
CHARACTERS = {
    "normal": "",
    "robot": "Cevaplarını robotik bir tarzda ver, 'BİP BİP', 'İŞLEM TAMAMLANDI' gibi ekler kullan.",
    "korsan": "Cevaplarını korsan tarzında ver, 'Ahoy!', 'Denizci!' gibi ifadeler kullan, eğlenceli ol.",
    "sair": "Cevaplarını şiirsel ve duygusal bir dille ver, kafiyeli konuş.",
}

def get_character():
    data = _load(CHARACTER_FILE, {"current": "normal"})
    return data.get("current", "normal")

def set_character(char):
    if char in CHARACTERS:
        _save(CHARACTER_FILE, {"current": char})
        return True
    return False


# ── Burç Yorumu (eğlence amaçlı, rastgele) ───────────────────────────────────
ZODIAC_SIGNS = ["koç","boğa","ikizler","yengeç","aslan","başak",
                "terazi","akrep","yay","oğlak","kova","balık"]

HOROSCOPE_TEMPLATES = [
    "Bugün enerjiniz yüksek, yeni fırsatlar kapınızı çalabilir.",
    "Sakin bir gün sizi bekliyor, dinlenmeye zaman ayırın.",
    "İlişkilerinizde güzel gelişmeler olabilir, açık iletişim kurun.",
    "Kariyerinizde önemli bir adım atma şansınız var.",
    "Finansal konularda dikkatli olmanız faydalı olacak.",
    "Yaratıcılığınız bugün zirvede, yeni fikirler üretebilirsiniz.",
    "Sosyal çevrenizle vakit geçirmek size iyi gelecek.",
    "Sağlığınıza biraz daha özen göstermeniz önerilir.",
]

def get_horoscope(sign):
    sign_l = sign.lower()
    today = datetime.date.today().toordinal()
    idx = (today + hash(sign_l)) % len(HOROSCOPE_TEMPLATES)
    return HOROSCOPE_TEMPLATES[idx]


# ── Motivasyon Sözleri ────────────────────────────────────────────────────────
MOTIVATION_QUOTES = [
    "Başarı, küçük çabaların her gün tekrarlanmasıdır.",
    "Bugün attığın her adım, yarının temelidir.",
    "Zorluklar seni güçlendirir, vazgeçme.",
    "En karanlık gece bile sona erer, güneş doğar.",
    "Hayallerinin peşinden git, onlar seni bekliyor.",
    "Her uzman bir zamanlar acemiydi.",
    "Bugün yapamadığın şey, yarın yapabileceğin şey değildir.",
    "Kendine inan, gerisi gelir.",
    "Küçük adımlar, büyük yolculukların başlangıcıdır.",
    "Disiplin, hedefler ile başarı arasındaki köprüdür.",
]

def get_motivation():
    return random.choice(MOTIVATION_QUOTES)


# ── Bilmeceler ────────────────────────────────────────────────────────────────
RIDDLES = [
    ("Başı tarak, sonu yatak, ortası nedir?", "Başak"),
    ("Yedi kardeş bir yorganın altında.", "Hafta günleri"),
    ("Suyu var, denizi yok; dalı var, ormanı yok; nedir bu?", "Harita"),
    ("İnce ince undan, gel beni bul.", "İp"),
    ("Akşamdan kuruludur, sabaha kurulmaz.", "Yatak"),
]

def get_riddle():
    return random.choice(RIDDLES)


# ── Komut İşleyici ─────────────────────────────────────────────────────────────
class ExtrasCommandProcessor:
    def __init__(self, speak_func, msg_func, ollama):
        self.speak = speak_func
        self.msg = msg_func
        self.ollama = ollama
        self.rps_score = {"user": 0, "anka": 0}

    def process(self, text):
        t = text.lower().strip()

        # ── Taş Kağıt Makas ──────────────────────────────────────────────────
        if any(x in t for x in ["taş kağıt makas","taş-kağıt-makas"]):
            choices = ["taş","kağıt","makas"]
            user_choice = None
            for c in choices:
                if c in t:
                    user_choice = c
            if not user_choice:
                r = "Taş, kağıt veya makas seçin efendim! Örnek: 'taş kağıt makas taş'"
                self.msg("ANKA", r); self.speak(r); return True
            anka_choice = random.choice(choices)
            result = self._rps_winner(user_choice, anka_choice)
            r = f"🎮 Siz: {user_choice} | Anka: {anka_choice}\n{result}"
            self.msg("ANKA", r); self.speak(result)
            return True

        # ── Zar At ───────────────────────────────────────────────────────────
        if "zar at" in t:
            num = random.randint(1,6)
            r = f"🎲 Zar: {num}"
            self.msg("ANKA", r); self.speak(f"Zar {num} geldi efendim.")
            return True

        # ── Yazı Tura ────────────────────────────────────────────────────────
        if "yazı tura" in t:
            result = random.choice(["Yazı","Tura"])
            r = f"🪙 {result}!"
            self.msg("ANKA", r); self.speak(f"{result} geldi efendim.")
            return True

        # ── Bilmece ──────────────────────────────────────────────────────────
        if "bilmece" in t and "cevap" not in t:
            riddle, answer = get_riddle()
            self._last_riddle_answer = answer
            r = f"🧩 Bilmece: {riddle}"
            self.msg("ANKA", r); self.speak(riddle)
            return True

        if "cevap" in t and hasattr(self, '_last_riddle_answer'):
            given = t.replace("cevap","").replace(":","").strip()
            correct = self._last_riddle_answer.lower() in given.lower() or given.lower() in self._last_riddle_answer.lower()
            r = f"✓ Doğru! Cevap: {self._last_riddle_answer}" if correct else f"✗ Yanlış. Doğru cevap: {self._last_riddle_answer}"
            self.msg("ANKA", r); self.speak(r)
            del self._last_riddle_answer
            return True

        # ── Burç Yorumu ──────────────────────────────────────────────────────
        if "burç" in t and "yorum" in t:
            sign = None
            for s in ZODIAC_SIGNS:
                if s in t:
                    sign = s
            if not sign:
                r = "Hangi burcunuzu yorumlamamı istersiniz efendim? (örn: 'koç burç yorumu')"
                self.msg("ANKA", r); self.speak(r)
                return True
            horoscope = get_horoscope(sign)
            r = f"🔮 {sign.capitalize()} Burç Yorumu:\n{horoscope}\n\n(Sadece eğlence amaçlıdır)"
            self.msg("ANKA", r); self.speak(horoscope)
            return True

        # ── Karakter Modu ────────────────────────────────────────────────────
        if "karakter modu" in t or "robot gibi konuş" in t or "korsan gibi konuş" in t:
            for char in CHARACTERS.keys():
                if char in t:
                    set_character(char)
                    r = f"✓ Karakter modu '{char}' olarak ayarlandı efendim."
                    self.msg("ANKA", r); self.speak(r)
                    return True
            if "robot" in t: set_character("robot")
            elif "korsan" in t: set_character("korsan")
            elif "şair" in t: set_character("sair")
            elif "normal" in t: set_character("normal")
            r = "✓ Karakter modu ayarlandı efendim."
            self.msg("ANKA", r); self.speak(r)
            return True

        # ── Kişi Profili Ekle ────────────────────────────────────────────────
        if "doğum günü ekle" in t or ("doğum günü" in t and " olarak kaydet" not in t and "tarihi" in t):
            import re
            # "annem doğum günü 15 mart" gibi formatları yakala
            r = "Kim için ve hangi tarih efendim? Şu formatta söyleyin: '[isim] doğum günü [gün] [ay]'"
            self.msg("ANKA", r); self.speak(r)
            return True

        if "doğum günü" in t and any(month in t for month in ["ocak","şubat","mart","nisan","mayıs","haziran","temmuz","ağustos","eylül","ekim","kasım","aralık"]):
            import re
            words = t.split()
            name = words[0].capitalize() if words else "Birisi"
            months = ["ocak","şubat","mart","nisan","mayıs","haziran","temmuz","ağustos","eylül","ekim","kasım","aralık"]
            month_found = next((m for m in months if m in t), None)
            day_match = re.search(r'\b(\d{1,2})\b', t)
            if month_found and day_match:
                date_str = f"{day_match.group(1)} {month_found.capitalize()}"
                add_person(name, "dogum_gunu", date_str)
                r = f"✓ {name}'in doğum günü {date_str} olarak kaydedildi efendim."
                self.msg("ANKA", r); self.speak(r)
                return True

        if "kimin doğum günü" in t or "ne zamandı" in t:
            people = list_people()
            for name, info in people.items():
                if name in t and "dogum_gunu" in info:
                    r = f"📅 {info['name']}'in doğum günü: {info['dogum_gunu']}"
                    self.msg("ANKA", r); self.speak(r)
                    return True
            r = "Bu kişi için kayıtlı bir doğum günü bulamadım efendim."
            self.msg("ANKA", r); self.speak(r)
            return True

        # ── Hedef Belirleme ──────────────────────────────────────────────────
        if "hedefim" in t and ("koy" in t or "belirle" in t or "ekle" in t):
            goal = t.replace("hedefim","").replace("koy","").replace("belirle","").replace("ekle","").strip()
            if goal:
                set_daily_goal(goal)
                r = f"✓ Günlük hedefiniz kaydedildi: {goal}"
                self.msg("ANKA", r); self.speak(r)
                return True

        if "bugünkü hedef" in t or "hedeflerim" in t:
            goals = get_today_goals()
            if not goals:
                r = "Bugün için henüz hedef belirlemediniz efendim."
            else:
                items = "\n".join(f"{'✓' if g['done'] else '○'} {g['text']}" for g in goals)
                r = f"🎯 Bugünkü hedefleriniz:\n{items}"
            self.msg("ANKA", r); self.speak("İşte bugünkü hedefleriniz efendim.")
            return True

        # ── Günlük Kelime ────────────────────────────────────────────────────
        if "günün kelimesi" in t or "ingilizce kelime" in t or "kelime öğret" in t:
            word, meaning = get_word_of_day()
            count = get_learned_count()
            r = f"📚 Günün Kelimesi:\n**{word}** = {meaning}\n\n(Toplam {count} gündür kelime öğreniyorsunuz!)"
            self.msg("ANKA", r); self.speak(f"Günün kelimesi: {word}, anlamı {meaning} efendim.")
            return True

        # ── Motivasyon ───────────────────────────────────────────────────────
        if "motivasyon" in t or "moralim bozuk" in t or "motive et" in t:
            quote = get_motivation()
            r = f"💪 {quote}"
            self.msg("ANKA", r); self.speak(quote)
            return True

        # ── Yarının Planı ────────────────────────────────────────────────────
        if "yarın ne" in t or "yarının planı" in t:
            from anka_memory import get_pending_tasks
            tasks = get_pending_tasks()
            if not tasks:
                r = "Yarın için planlanmış göreviniz yok efendim. Yeni gün, yeni fırsatlar!"
            else:
                items = "\n".join(f"• {tk['text']}" for tk in tasks[:5])
                r = f"📅 Bekleyen görevleriniz:\n{items}"
            self.msg("ANKA", r); self.speak(r[:200])
            return True

        return False

    def _rps_winner(self, user, anka):
        if user == anka:
            return "Berabere! 🤝"
        wins = {"taş":"makas", "kağıt":"taş", "makas":"kağıt"}
        if wins[user] == anka:
            self.rps_score["user"] += 1
            return f"Siz kazandınız! 🎉 (Skor: Siz {self.rps_score['user']} - Anka {self.rps_score['anka']})"
        else:
            self.rps_score["anka"] += 1
            return f"Anka kazandı! 🤖 (Skor: Siz {self.rps_score['user']} - Anka {self.rps_score['anka']})"

    def apply_character_prefix(self, base_system):
        """Sistem promptuna aktif karakter modunu ekler"""
        char = get_character()
        if char != "normal" and char in CHARACTERS:
            return base_system + " " + CHARACTERS[char]
        return base_system
