# ── ANKA LOCAL AI v4.0 — Gelişmiş Zeka Motoru ────────────────────────────────
# API key veya Ollama GEREKMİYOR! Tamamen yerel ve ücretsiz.
# Bağlam anlama, duygu zekası, öğrenme, tahmin, kişiselleştirme

import json, os, datetime, random, re, math, time, difflib, statistics
import requests, psutil, subprocess, webbrowser
from anka_config import BASE_DIR, USER_NAME

KNOWLEDGE_FILE   = os.path.join(BASE_DIR, "anka_knowledge.json")
CONTEXT_FILE     = os.path.join(BASE_DIR, "anka_local_context.json")
LEARN_FILE       = os.path.join(BASE_DIR, "anka_local_learn.json")
PERSONALITY_FILE = os.path.join(BASE_DIR, "anka_local_personality.json")
CACHE_FILE       = os.path.join(BASE_DIR, "anka_response_cache.json")

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
# ── GENİŞ BİLGİ TABANI ───────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════
KNOWLEDGE_BASE = {
    "selamlama": {
        "triggers": ["merhaba","selam","hey","günaydın","iyi akşamlar","iyi geceler","hello","hi","selamlar","nbr","slm","mrb"],
        "responses": [
            f"Merhaba efendim! Bugün size nasıl yardımcı olabilirim?",
            f"Hoş geldiniz efendim! Sistemler hazır, emrinizdeyim.",
            f"Selam efendim! Ne yapabilirim sizin için?",
        ]
    },
    "nasılsın": {
        "triggers": ["nasılsın","nasıl gidiyor","iyi misin","ne haber","ne var ne yok","napıyorsun","naber"],
        "responses": [
            "Teşekkürler efendim! Sistemler %100 çalışıyor, size yardıma hazırım!",
            "Gayet iyiyim efendim! Siz nasılsınız?",
            "Harika efendim! Her şey yolunda. Bugün ne planlıyorsunuz?",
        ]
    },
    "teşekkür": {
        "triggers": ["teşekkür","sağ ol","eyvallah","makbule geçsin","thanks","thank you","çok iyi","helal","tşk"],
        "responses": [
            "Rica ederim efendim! Başka bir isteğiniz var mı?",
            "Ne demek efendim, her zaman emrinizdeyim.",
            "Memnun oldum efendim! Başka nasıl yardımcı olabilirim?",
        ]
    },
    "kim_sin": {
        "triggers": ["kimsin","sen kimsin","adın ne","anka nedir","kendini tanıt","hakkında bilgi"],
        "responses": [
            f"Ben Anka — {USER_NAME} için özel geliştirilmiş yapay zeka asistanıyım! Jarvis, EDITH ve FRIDAY'dan ilham aldım. Tamamen yerel çalışırım efendim!",
            f"Anka! {USER_NAME}'in kişisel yapay zeka asistanı. API key veya internet gerektirmeden çalışan, öğrenen ve gelişen bir sistemim efendim.",
        ]
    },
    "neler_yapabilirsin": {
        "triggers": ["ne yapabilirsin","özellikler","neler yaparsın","yeteneklerin","komutlar","yardım","ne yaparsın"],
        "responses": [
            """🤖 ANKA v300 ÖZELLİKLERİ:
🌤 Hava durumu & Tahmin
⏰ Alarm, hatırlatıcı, zamanlayıcı
📝 Görev, not, proje yönetimi
🔢 Bilimsel hesap makinesi
💻 Sistem analizi & optimizasyon
🌐 Web araştırma & URL analizi
🎵 Müzik & medya kontrolü
📱 WhatsApp araması
👁️ Gesture kontrolü (göz+el+baş)
🧠 Sonsuz hafıza sistemi
🤖 Çoklu ajan konseyi
💡 Yaratıcı zeka (6 şapka, analoji)
🌍 Dünya nabzı (haber+döviz+kripto)
📚 Meta öğrenme (Feynman, Pomodoro)
Ve çok daha fazlası! 'v100 yardım' veya 'v300 yardım' yazın efendim."""
        ]
    },
    "veda": {
        "triggers": ["güle güle","hoşçakal","bye","görüşürüz","kendin iyi bak","kapan","kapat","çıkıyorum"],
        "responses": [
            "Güle güle efendim! İyi günler dilerim.",
            "Hoşçakalın efendim! İstediğinizde buradayım.",
            "Görüşmek üzere efendim! Sistemler bekleme modunda olacak.",
        ]
    },
    "motivasyon": {
        "triggers": ["motive et","motivasyon ver","cesaret ver","güçlendir","moral ver","ilham ver","moralim bozuk"],
        "responses": [
            "💪 Siz yapabilirsiniz efendim! Her büyük başarı küçük adımlarla başlar. Devam edin!",
            "🔥 İnanın kendinize efendim! Zorluklar sizi daha güçlü yapar. Başaracaksınız!",
            "⚡ Bugün harika şeyler başaracaksınız efendim! Odaklanın ve ilerlemeye devam edin!",
            "🎯 Hedefinize odaklanın efendim! Her adım sizi oraya yaklaştırır. Durmayin!",
            "🌟 Siz güçlüsünüz efendim! Şimdiye kadar her engeli aştınız, bunu da aşacaksınız!",
        ]
    },
    "şaka": {
        "triggers": ["şaka yap","fıkra anlat","güldür","komik bir şey","şakalar","espri yap"],
        "responses": [
            "😄 Bir yazılımcı markete gider. Eşi telefon açar: '2 ekmek al, süt varsa 6 tane al.' Yazılımcı 6 ekmekle döner!",
            "🤖 Neden programcılar karanlıktan korkar? Çünkü dark mode'da çalışırlar!",
            "😂 Bir yapay zeka psikoloğa gider. Psikolog sorar: 'Probleminiz ne?' Yapay zeka: 'Segmentation fault: core dumped!'",
            "🎯 Python geliştiricisi neden mutsuz? Çünkü hayatında hiç exception handle etmedi!",
        ]
    },
    "hava": {
        "triggers": ["hava nasıl","hava durumu","bugün hava","yağmur var mı","sıcaklık kaç","kaç derece","hava tahmin","hava"],
        "responses": ["__WEATHER__"]
    },
    "saat": {
        "triggers": ["saat kaç","şu an saat","zaman nedir","tarih nedir","bugün ne günü","hangi gün","ay nedir","saat","tarih"],
        "responses": ["__TIME__"]
    },
    "sistem": {
        "triggers": ["sistem durumu","cpu ne kadar","ram ne kadar","bellek durumu","disk durumu","bilgisayar nasıl","pil durumu","sistem"],
        "responses": ["__SYSTEM__"]
    },
    "hesap": {
        "triggers": ["hesapla","kaç eder","kaç yapar","topla","çarp","böl","çıkar","karekök","yüzde","hesap"],
        "responses": ["__CALC__"]
    },
    "haber": {
        "triggers": ["haberler","gündem","son dakika","ne oldu","haberler neler","haber"],
        "responses": ["__NEWS__"]
    },
    "döviz": {
        "triggers": ["döviz","dolar kaç","euro kaç","sterlin","kur nedir","döviz kuru","dolar","euro"],
        "responses": ["__CURRENCY__"]
    },
    "kripto": {
        "triggers": ["bitcoin","btc","ethereum","kripto","coin fiyatı","btc kaç","eth kaç"],
        "responses": ["__CRYPTO__"]
    },
    "övgü": {
        "triggers": ["harika","mükemmel","süper","bravo","aferin","çok iyi","perfect","muhteşem","fevkalade"],
        "responses": [
            "Teşekkür ederim efendim! Motive olduk! 😊",
            "Çok naziksiniz efendim! Daha iyisini yapmaya çalışacağım.",
            "Sağ olun efendim! Takdiriniz beni mutlu etti. Çalışmaya devam!",
        ]
    },
    "üzgün": {
        "triggers": ["üzgünüm","kötüyüm","moralim bozuk","yoruldum","sıkıldım","stres","bunaldım","zor","depresyon"],
        "responses": [
            "Üzgünüm bunu duyduğuma efendim. Biraz mola vermek ister misiniz? 💙",
            "Her şey geçer efendim. Kendinize iyi bakın, dinlenin. 🌟",
            "Zor zamanlar olur efendim ama siz güçlüsünüz. Yardımcı olabileceğim bir şey var mı? 💪",
        ]
    },
    "yapay_zeka": {
        "triggers": ["yapay zeka nedir","ai nedir","machine learning","derin öğrenme","nöral ağ","chatgpt","gemini"],
        "responses": [
            "Yapay zeka, insan zekasını taklit eden sistemlerdir. Ben API key olmadan yerel çalışan bir yapay zekayım! Kural tabanlı + öğrenme sistemi kombinasyonunu kullanıyorum efendim.",
        ]
    },
    "enerji": {
        "triggers": ["yorgunum","enerji yok","uyku bastı","uykusuz","dinlenmek istiyorum","halsizim"],
        "responses": [
            "Kısa bir mola verin efendim! ☕ Kahve veya 20 dakikalık uyku çok yardımcı olur.",
            "Su için efendim! Dehidrasyon enerji düşürür. Biraz hareket de iyi gelir! 💧",
        ]
    },
    "zaman_yönetimi": {
        "triggers": ["zaman yönetimi","pomodoro","verimli olmak","procrastination","erteleme","odaklanma"],
        "responses": [
            "Pomodoro tekniği: 25 dakika çalış, 5 dakika mola ver. 4 pomodoro sonra uzun mola! 'ai pomodoro [görev]' komutuyla başlayabilirsiniz efendim.",
            "Eisenhower matrisi kullanın efendim: Önemli+Acil → Hemen yap, Önemli+Acil değil → Planla!",
        ]
    },
    "sağlık": {
        "triggers": ["sağlıklı olmak","diyet","egzersiz","spor yap","uyku","su iç","beslenme","sağlık"],
        "responses": [
            "Sağlıklı olmak için: 💧 Bol su için, 🏃 düzenli egzersiz yapın, 😴 7-8 saat uyuyun, 🥗 dengeli beslenin efendim!",
            "Günde en az 8 bardak su içmeyi unutmayın efendim! Vücudunuzun %60'ı sudur.",
        ]
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# ── VERİ TOPLAYICI ───────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════
class DataFetcher:
    CACHE = {}
    CACHE_EXPIRE = 300

    @classmethod
    def _cached(cls, key, fetch_fn):
        now = time.time()
        if key in cls.CACHE:
            data, ts = cls.CACHE[key]
            if now - ts < cls.CACHE_EXPIRE:
                return data
        data = fetch_fn()
        cls.CACHE[key] = (data, now)
        return data

    @classmethod
    def weather(cls, city="Istanbul"):
        def fetch():
            try:
                r = requests.get(f"https://wttr.in/{city}?format=j1", timeout=5)
                d = r.json()["current_condition"][0]
                return {
                    "temp": d["temp_C"], "feels": d["FeelsLikeC"],
                    "desc": d["weatherDesc"][0]["value"],
                    "humidity": d["humidity"],
                    "rain": d.get("chanceofrain","0"),
                    "wind": d.get("windspeedKmph","0")
                }
            except: return None
        return cls._cached(f"weather_{city}", fetch)

    @classmethod
    def currency(cls):
        def fetch():
            try:
                r = requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=5)
                rates = r.json()["rates"]
                return {"TRY": rates.get("TRY",0), "EUR": rates.get("EUR",0),
                        "GBP": rates.get("GBP",0), "JPY": rates.get("JPY",0)}
            except: return None
        return cls._cached("currency", fetch)

    @classmethod
    def crypto(cls):
        def fetch():
            try:
                btc = requests.get("https://api.coinbase.com/v2/prices/BTC-USD/spot", timeout=5)
                eth = requests.get("https://api.coinbase.com/v2/prices/ETH-USD/spot", timeout=5)
                return {
                    "BTC": float(btc.json()["data"]["amount"]),
                    "ETH": float(eth.json()["data"]["amount"])
                }
            except: return None
        return cls._cached("crypto", fetch)

    @classmethod
    def news(cls):
        def fetch():
            try:
                import xml.etree.ElementTree as ET
                r = requests.get("https://www.hurriyet.com.tr/rss/anasayfa", timeout=5)
                root = ET.fromstring(r.content)
                items = root.findall(".//item")[:5]
                return [i.find("title").text for i in items if i.find("title") is not None]
            except: return []
        return cls._cached("news", fetch)


# ═══════════════════════════════════════════════════════════════════════════════
# ── GELİŞMİŞ ÖĞRENME SİSTEMİ ────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════
class LearningSystem:
    def __init__(self):
        self.data = _load(LEARN_FILE, {
            "user_facts": [],
            "custom_responses": {},
            "corrections": [],
            "favorite_topics": {},
            "conversation_count": 0,
            "user_vocabulary": {},
            "interaction_patterns": {}
        })

    def learn_from_user(self, text):
        patterns = [
            (r"adım\s+([A-ZÇĞİÖŞÜa-zçğışöşü]+)", "isim"),
            (r"(\d+)\s+yaşındayım", "yaş"),
            (r"([A-ZÇĞİÖŞÜ][a-zçğışöşü]+)'(?:da|de|ta|te)\s+(?:yaşıyorum|oturuyorum)", "şehir"),
            (r"([A-ZÇĞİÖŞÜ][a-zçğışöşü]+)\s+(?:okuyorum|öğrencisiyim)", "okul"),
            (r"([a-zçğışöşü]+)\s+seviyorum", "sevilen"),
            (r"([a-zçğışöşü]+)\s+sevmiyorum", "sevilmeyen"),
            (r"hobim\s+([a-zçğışöşü\s]+)", "hobi"),
            (r"işim\s+([a-zçğışöşü\s]+)", "iş"),
        ]
        for pattern, label in patterns:
            m = re.search(pattern, text.lower())
            if m:
                fact = {"label": label, "value": m.group(1),
                       "text": text[:100], "date": datetime.date.today().isoformat()}
                self.data["user_facts"] = [f for f in self.data["user_facts"] if f["label"] != label]
                self.data["user_facts"].append(fact)
                _save(LEARN_FILE, self.data)

        # Kelime hazinesi öğren
        words = text.lower().split()
        for word in words:
            if len(word) > 3:
                self.data["user_vocabulary"][word] = \
                    self.data["user_vocabulary"].get(word, 0) + 1

    def add_custom_response(self, trigger, response):
        self.data["custom_responses"][trigger.lower()] = {
            "response": response,
            "added": datetime.datetime.now().isoformat(),
            "use_count": 0
        }
        _save(LEARN_FILE, self.data)

    def get_custom_response(self, text):
        t = text.lower()
        # Tam eşleşme
        for trigger, data in self.data["custom_responses"].items():
            if trigger in t:
                data["use_count"] += 1
                _save(LEARN_FILE, self.data)
                return data["response"]
        # Bulanık eşleşme
        triggers = list(self.data["custom_responses"].keys())
        matches = difflib.get_close_matches(t, triggers, n=1, cutoff=0.8)
        if matches:
            data = self.data["custom_responses"][matches[0]]
            data["use_count"] += 1
            _save(LEARN_FILE, self.data)
            return data["response"]
        return None

    def log_topic(self, topic):
        self.data["favorite_topics"][topic] = \
            self.data["favorite_topics"].get(topic, 0) + 1
        self.data["conversation_count"] += 1
        _save(LEARN_FILE, self.data)

    def get_user_context(self):
        facts = self.data["user_facts"]
        if not facts: return f"Kullanıcı: {USER_NAME}"
        return "Kullanıcı: " + ", ".join(
            f"{f['label']}={f['value']}" for f in facts[-5:])

    def get_user_name(self):
        for fact in self.data["user_facts"]:
            if fact["label"] == "isim":
                return fact["value"]
        return USER_NAME

    def get_top_topics(self, n=5):
        return sorted(self.data["favorite_topics"].items(),
                     key=lambda x: -x[1])[:n]

    def add_correction(self, wrong, correct):
        self.data["corrections"].append({
            "wrong": wrong[:100], "correct": correct[:100],
            "date": datetime.date.today().isoformat()
        })
        _save(LEARN_FILE, self.data)


# ═══════════════════════════════════════════════════════════════════════════════
# ── KİŞİLİK SİSTEMİ ──────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════
class PersonalitySystem:
    def __init__(self):
        self.current = "professional"

    def set(self, personality):
        valid = ["professional","friendly","serious","funny","motivator"]
        if personality in valid:
            self.current = personality
            return True
        return False

    def format(self, response):
        text = response.strip()
        if self.current == "professional":
            if not any(text.endswith(x) for x in ["efendim.","efendim!","?"]):
                if not text.endswith(".") and not text.endswith("!") and len(text) < 200:
                    text += " efendim."
        elif self.current == "friendly":
            if "!" not in text: text += " 😊"
        elif self.current == "motivator":
            text += " 💪"
        return text


# ═══════════════════════════════════════════════════════════════════════════════
# ── DUYGUSAL ZEKA ─────────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════
class EmotionalIntelligence:
    EMOTIONS = {
        "mutlu": {
            "words": ["mutluyum","harika","süper","mükemmel","harikayım","neşeliyim",
                     "sevindim","güzel","memnun","iyi hissediyorum","çok iyi"],
            "responses": [
                "Bu haberi duymak güzel efendim! Bu enerjiyi koruyun! 😊",
                "Harika efendim! Mutluluğunuz beni de mutlu etti! 🌟",
            ]
        },
        "üzgün": {
            "words": ["üzgünüm","kötüyüm","moralim bozuk","ağlıyorum","mutsuzum","üzülüyorum"],
            "responses": [
                "Üzgünüm bunu duyduğuma efendim 💙 Her şey geçer. Yanınızdayım.",
                "Zor zamanlar herkesin başına gelir efendim. Güçlüsünüz! 💪",
            ]
        },
        "sinirli": {
            "words": ["sinirliyim","kızgınım","öfkeliyim","bıktım","usandım","berbat","saçma"],
            "responses": [
                "Anlıyorum efendim, bu can sıkıcı olmalı. Derin bir nefes alın. 🌬️",
                "Haklısınız efendim. Nasıl yardımcı olabilirim?",
            ]
        },
        "yorgun": {
            "words": ["yorgunum","bitkinim","uyku bastı","enerjim yok","halsizim","tükendim"],
            "responses": [
                "Dinlenin efendim! 😴 20 dakikalık uyku harika gelir.",
                "Yorgunluk önemli bir sinyal efendim. Su için, biraz yürüyün. 💧",
            ]
        },
        "stresli": {
            "words": ["stres","stresli","bunaldım","panikledim","endişeleniyorum","kaygılanıyorum"],
            "responses": [
                "Derin nefes alın efendim 🌬️ 4 sayı nefes, 4 tut, 4 ver.",
                "Stres yönetilebilir efendim. Önce en önemli şeye odaklanın. 🎯",
            ]
        },
        "heyecanlı": {
            "words": ["heyecanlıyım","çok heyecanlı","sabırsızlanıyorum","harika haber"],
            "responses": [
                "Bu heyecanı hissedebiliyorum efendim! 🚀",
                "Mükemmel efendim! Bu enerjiyle neler başarabileceğinizi düşünün! ⚡",
            ]
        },
    }

    def detect(self, text):
        t = text.lower()
        scores = {}
        for emotion, data in self.EMOTIONS.items():
            score = sum(1 for word in data["words"] if word in t)
            if score > 0: scores[emotion] = score
        if scores:
            return max(scores, key=scores.get)
        return None

    def respond(self, text):
        emotion = self.detect(text)
        if emotion:
            return random.choice(self.EMOTIONS[emotion]["responses"]), emotion
        return None, None


# ═══════════════════════════════════════════════════════════════════════════════
# ── AKILLI NİYET TESPİTİ ─────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════
class SmartIntentDetector:
    """Kullanıcının ne demek istediğini gelişmiş yöntemlerle anlar"""

    # Yazım düzeltme haritası
    TYPOS = {
        "slm":"selam","mrb":"merhaba","nbr":"ne haber","naber":"ne haber",
        "tşk":"teşekkür","tmm":"tamam","hva":"hava","nvr":"nerede",
        "nsl":"nasıl","nnsl":"nasıl","slmlar":"selamlar","gj":"güzel",
        "ok":"tamam","kk":"tamam","np":"ne var ne yok","hyr":"hayır",
        "evt":"evet","yp":"yap","gb":"gibi","bl":"bile","hr":"her",
        "bn":"ben","sn":"sen","bz":"biz","sz":"siz","onlr":"onlar",
    }

    # Kısayol genişletme
    SHORTCUTS = {
        "h":"hava nasıl", "hv":"hava nasıl",
        "s":"saat kaç", "ss":"saat kaç",
        "d":"döviz kuru", "dv":"döviz kuru",
        "b":"bitcoin fiyatı", "btc":"bitcoin fiyatı",
        "n":"haberler", "hbr":"haberler",
        "y":"ne yapabilirsin", "yd":"yardım",
        "m":"merhaba", "sd":"sistem durumu",
    }

    def autocorrect(self, text):
        words = text.lower().split()
        corrected = []
        for word in words:
            corrected.append(self.TYPOS.get(word, word))
        return " ".join(corrected)

    def expand_shortcut(self, text):
        t = text.lower().strip()
        if t in self.SHORTCUTS:
            return self.SHORTCUTS[t], True
        return text, False

    def detect_question_type(self, text):
        t = text.lower()
        if re.match(r'^ne\s+\w+', t): return "what"
        if re.match(r'^nasıl\s+', t): return "how"
        if re.match(r'^neden\s+', t): return "why"
        if re.match(r'^nerede\s+', t): return "where"
        if re.match(r'^kim\s+', t): return "who"
        if re.match(r'^kaç\s+', t): return "how_many"
        if re.match(r'^ne\s+zaman', t): return "when"
        if t.endswith("?") or any(t.startswith(q) for q in
            ["mi ","mı ","mu ","mü "]): return "yes_no"
        return "statement"

    def extract_intent(self, text):
        t = text.lower()
        # Matematiksel ifade
        if re.search(r'\d+\s*[+\-*/^]\s*\d+', t):
            return "calculate"
        # URL
        if re.search(r'https?://', t):
            return "url_analysis"
        # Arama isteği
        if any(w in t for w in ["ara","bul","google","araştır"]):
            return "search"
        return "general"


# ═══════════════════════════════════════════════════════════════════════════════
# ── BAĞLAM YÖNETİCİSİ ────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════
class ContextManager:
    """Konuşma bağlamını takip eder"""
    def __init__(self):
        self.short_term = []   # Son 20 mesaj
        self.current_topic = None
        self.last_question = None
        self.entities = []     # Bahsedilen varlıklar

    def add(self, role, text, category=None):
        entry = {
            "role": role, "text": text,
            "category": category,
            "time": datetime.datetime.now().isoformat()
        }
        self.short_term.append(entry)
        if len(self.short_term) > 20:
            self.short_term = self.short_term[-20:]
        if category and category != "unknown":
            self.current_topic = category
        if "?" in text and role == "user":
            self.last_question = text

    def resolve_reference(self, text):
        """'O', 'Bu', 'Evet', 'Hayır' referanslarını çöz"""
        t = text.lower().strip()
        if t in ["evet","e","yes","tamam","ok","olur","tabi","tabii","aynen"]:
            return "evet"
        if t in ["hayır","h","no","olmaz","istemiyorum"]:
            return "hayır"
        return text

    def get_last_user_msg(self):
        for msg in reversed(self.short_term):
            if msg["role"] == "user":
                return msg["text"]
        return ""

    def extract_entities(self, text):
        """Metinden varlıkları çıkar"""
        words = text.split()
        for word in words:
            if len(word) > 2 and word[0].isupper() and \
               word not in ["Ben","Sen","O","Biz","Siz","Bu","Şu"]:
                if word not in self.entities:
                    self.entities.append(word)
        self.entities = self.entities[-15:]


# ═══════════════════════════════════════════════════════════════════════════════
# ── YANIT ÜRETME MOTORU ──────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════
class SmartResponseEngine:
    def __init__(self):
        self.learning    = LearningSystem()
        self.personality = PersonalitySystem()
        self.emotion     = EmotionalIntelligence()
        self.intent      = SmartIntentDetector()
        self.context     = ContextManager()
        self.custom_kb   = _load(KNOWLEDGE_FILE, {})
        self.last_topic  = None
        self.response_cache = {}

    def _find_category(self, text):
        t = text.lower().strip()
        best_cat, best_score = None, 0
        all_kb = {**KNOWLEDGE_BASE, **self.custom_kb}
        for category, data in all_kb.items():
            score = 0
            for trigger in data.get("triggers", []):
                if trigger == t: score += 20        # Tam eşleşme
                elif trigger in t: score += len(trigger) * 2
                elif any(w in t for w in trigger.split()): score += 1
            if score > best_score:
                best_score = score
                best_cat = category
        return best_cat if best_score > 0 else None

    def _process_special(self, key, text):
        if key == "__WEATHER__":
            d = DataFetcher.weather()
            if d:
                return (f"🌤 İstanbul Hava:\n"
                       f"• Sıcaklık: {d['temp']}°C (Hissedilen: {d['feels']}°C)\n"
                       f"• {d['desc']}\n"
                       f"• Nem: %{d['humidity']} | Rüzgar: {d['wind']} km/h\n"
                       f"• Yağmur ihtimali: %{d['rain']}")
            return "Hava verisi alınamadı efendim."

        elif key == "__TIME__":
            now = datetime.datetime.now()
            days = ["Pazartesi","Salı","Çarşamba","Perşembe","Cuma","Cumartesi","Pazar"]
            months = ["","Ocak","Şubat","Mart","Nisan","Mayıs","Haziran",
                     "Temmuz","Ağustos","Eylül","Ekim","Kasım","Aralık"]
            return (f"🕐 {now.strftime('%H:%M:%S')}\n"
                   f"📅 {now.day} {months[now.month]} {now.year}, {days[now.weekday()]}")

        elif key == "__SYSTEM__":
            cpu = psutil.cpu_percent(interval=1)
            ram = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            battery = psutil.sensors_battery()
            r = (f"💻 Sistem:\n"
                f"• CPU: %{cpu:.0f}\n"
                f"• RAM: {ram.used//1024//1024:,}MB/%{ram.percent:.0f}\n"
                f"• Disk: {disk.free//1024**3:.0f}GB boş")
            if battery:
                r += f"\n• Pil: %{battery.percent:.0f} ({'Şarjda' if battery.power_plugged else 'Pilde'})"
            return r

        elif key == "__CALC__":
            return self._calculate(text)

        elif key == "__NEWS__":
            news = DataFetcher.news()
            if news:
                return "📰 Haberler:\n" + "\n".join(f"• {n[:60]}" for n in news[:5])
            return "Haberler alınamadı efendim."

        elif key == "__CURRENCY__":
            d = DataFetcher.currency()
            if d:
                return (f"💱 Döviz (USD bazlı):\n"
                       f"• 1 USD = {d['TRY']:.2f} ₺\n"
                       f"• 1 USD = {d['EUR']:.4f} €\n"
                       f"• 1 USD = {d['GBP']:.4f} £")
            return "Döviz bilgisi alınamadı efendim."

        elif key == "__CRYPTO__":
            d = DataFetcher.crypto()
            if d:
                return (f"₿ Kripto:\n"
                       f"• Bitcoin: ${d['BTC']:,.0f}\n"
                       f"• Ethereum: ${d['ETH']:,.0f}")
            return "Kripto verisi alınamadı efendim."

        return None

    def _calculate(self, text):
        try:
            t = text.lower()
            for tr, en in [("artı","+"),("eksi","-"),("çarpı","*"),("bölü","/"),
                          ("ve","+"),("mod","%"),("üssü","**"),("karekök","sqrt")]:
                t = t.replace(tr, en)
            for w in ["hesapla","kaç eder","kaç yapar","topla","ne kadar","bilimsel hesapla"]:
                t = t.replace(w, "")
            expr = re.sub(r'[^0-9+\-*/().%\s\^sqrt]', '', t).strip()
            expr = expr.replace('^','**')
            if expr and len(expr) > 0:
                result = eval(expr, {"__builtins__": {}, "math": math,
                                    "sqrt": math.sqrt, "pi": math.pi, "e": math.e})
                original = re.sub(r'hesapla|kaç eder|kaç yapar|bilimsel hesapla', '',
                                 text.lower()).strip()
                return f"🔢 {original} = {result:,}" if isinstance(result, int) else f"🔢 {original} = {result:.6g}"
        except: pass
        return "Hesaplama yapılamadı efendim. Örn: 'hesapla 25 * 4'"

    def _contextual_response(self, text):
        t = text.lower().strip()
        if t in ["evet","tamam","olur","tabi","aynen","e","ok"]:
            last = self.context.get_last_user_msg()
            return "Anlaşıldı efendim! Başka bir isteğiniz var mı?"
        if t in ["hayır","olmaz","istemiyorum","h"]:
            return "Tamam efendim! Başka nasıl yardımcı olabilirim?"
        if any(w in t for w in ["devam et","anlat","daha fazla","detay"]):
            if self.last_topic:
                return (f"'{self.last_topic}' hakkında daha fazla bilgi için "
                       f"'derin araştır {self.last_topic}' komutunu kullanabilirsiniz efendim.")
        if any(w in t for w in ["tekrarla","bir daha","anlamadım"]):
            return "Özür dilerim efendim, biraz farklı sorar mısınız?"
        return None

    def _pattern_response(self, text):
        t = text.lower().strip()
        patterns = [
            (r"^(.+?)\s+nedir\??$",
             lambda m: f"'{m.group(1)}' hakkında bilgi için 'derin araştır {m.group(1)}' deneyin efendim."),
            (r"^(.+?)\s+ne\s+demek\??$",
             lambda m: f"'{m.group(1)}' kelimesini açıklamam için 'bilimsel açıkla {m.group(1)}' deneyin efendim."),
            (r"^(.+?)\s+nasıl\s+yapılır\??$",
             lambda m: f"'{m.group(1)}' yapımı için 'derin araştır {m.group(1)} nasıl yapılır' deneyin efendim."),
            (r"^kaç\s+tane\s+(.+?)\??$",
             lambda m: f"'{m.group(1)}' sayısı için araştırayım efendim."),
            (r"(\d+)\s*[+\-*/]\s*(\d+)",
             lambda m: self._calculate(text)),
        ]
        for pattern, handler in patterns:
            m = re.match(pattern, t)
            if m:
                result = handler(m)
                if result: return result
        return None

    def _smart_fallback(self, text):
        t = text.lower().strip()
        words = t.split()
        if len(words) == 1:
            self.last_topic = words[0]
            return (f"'{words[0]}' hakkında ne öğrenmek istersiniz efendim?\n"
                   f"• 'derin araştır {words[0]}' → Detaylı\n"
                   f"• 'bilimsel açıkla {words[0]}' → Bilimsel\n"
                   f"• 'ajan konseyi {words[0]} hakkında ne düşünüyorsun' → Çoklu analiz")
        if "?" in text:
            topic = " ".join(words[1:3]) if len(words) > 1 else text[:20]
            self.last_topic = topic
            return (f"Bu soruyu yanıtlamak için:\n"
                   f"• 'derin araştır {topic}' → Web araştırması\n"
                   f"• 'ajan konseyi {topic}' → AI analizi\n"
                   f"Hangisini tercih edersiniz efendim?")
        return random.choice([
            "Anlıyorum efendim. Bu konuda daha fazla detay verir misiniz?",
            "Emrinizdeyim efendim! Daha spesifik bir komut dener misiniz?",
            "Sizi duydum efendim. 'yardım' yazarak tüm komutları görebilirsiniz.",
        ])

    def generate_response(self, text):
        t = text.lower().strip()

        # 1. Cache kontrol
        cache_key = t[:60]
        if cache_key in self.response_cache:
            cached = self.response_cache[cache_key]
            if time.time() - cached["ts"] < 120:  # 2 dk cache
                return cached["resp"]

        # 2. Öğretme komutu
        learn_m = re.match(r'anka öğren[:\s]+(.+?)\s*=\s*(.+)', text, re.IGNORECASE)
        if learn_m:
            trigger, response = learn_m.group(1).strip(), learn_m.group(2).strip()
            self.learning.add_custom_response(trigger, response)
            return f"✓ Öğrendim! '{trigger}' → '{response[:50]}' efendim."

        # 3. Düzeltme
        correct_m = re.match(r'düzelt[:\s]+(.+?)\s*→\s*(.+)', text, re.IGNORECASE)
        if correct_m:
            self.learning.add_correction(correct_m.group(1), correct_m.group(2))
            return "✓ Düzeltme kaydedildi efendim!"

        # 4. Özel cevap
        custom = self.learning.get_custom_response(text)
        if custom:
            self.learning.log_topic("custom")
            return self.personality.format(custom)

        # 5. Kullanıcıdan öğren
        self.learning.learn_from_user(text)
        self.context.add("user", text)
        self.context.extract_entities(text)

        # 6. Duygu tespiti (kısa mesajlarda)
        if len(t.split()) <= 7:
            emo_resp, emotion = self.emotion.respond(text)
            if emo_resp:
                self.context.add("assistant", emo_resp, "emotion")
                return emo_resp

        # 7. Anlık veri gerektiren kategoriler
        direct_cats = {
            "hava": "__WEATHER__", "saat": "__TIME__",
            "sistem": "__SYSTEM__", "hesap": "__CALC__",
            "haber": "__NEWS__", "döviz": "__CURRENCY__",
            "kripto": "__CRYPTO__"
        }
        for cat, special_key in direct_cats.items():
            triggers = KNOWLEDGE_BASE.get(cat,{}).get("triggers",[])
            if any(tr in t for tr in triggers):
                result = self._process_special(special_key, text)
                if result:
                    self.learning.log_topic(cat)
                    resp = self.personality.format(result)
                    self.context.add("assistant", resp, cat)
                    self.response_cache[cache_key] = {"resp": resp, "ts": time.time()}
                    return resp

        # 8. Matematik
        if re.search(r'\d+\s*[+\-*/^]\s*\d+', text):
            result = self._calculate(text)
            return self.personality.format(result)

        # 9. Kategori eşleştirme
        category = self._find_category(text)
        if category:
            self.last_topic = category
            self.learning.log_topic(category)
            all_kb = {**KNOWLEDGE_BASE, **self.custom_kb}
            data = all_kb.get(category, {})
            responses = data.get("responses", [])
            if responses:
                response = random.choice(responses)
                if response.startswith("__") and response.endswith("__"):
                    result = self._process_special(response, text)
                    if result:
                        resp = self.personality.format(result)
                        self.context.add("assistant", resp, category)
                        return resp
                resp = self.personality.format(response)
                self.context.add("assistant", resp, category)
                return resp

        # 10. Bağlamsal cevap
        ctx_resp = self._contextual_response(text)
        if ctx_resp:
            return self.personality.format(ctx_resp)

        # 11. Desen eşleştirme
        pattern_resp = self._pattern_response(text)
        if pattern_resp:
            return self.personality.format(pattern_resp)

        # 12. Akıllı fallback
        resp = self.personality.format(self._smart_fallback(text))
        self.context.add("assistant", resp, "unknown")
        return resp

    def chat(self, message, system_override=None, hw_mode=False):
        if hw_mode:
            return self._homework(message)
        return self.generate_response(message)

    def _homework(self, question):
        calc = self._calculate(question)
        if "=" in calc:
            return calc
        return f"Çözüm için adımlar:\n1. Verilenleri yaz\n2. Formülü seç\n3. Uygula\n4. Kontrol et efendim!"


# ═══════════════════════════════════════════════════════════════════════════════
# ── KONUŞMA AKIŞ YÖNETİCİSİ ──────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════
class ConversationFlow:
    """Konuşma akışını ve bağlamı yönetir"""
    FLOW_PATTERNS = {
        ("selamlama","nasılsın"): "Teşekkürler efendim! Sistemler mükemmel. Bugün nasıl bir gün?",
        ("hava","ne_giyeyim"):   "Hava önerisi için 'hava önerisi' komutunu kullanın efendim!",
        ("saat","alarm"):        "Alarm kurmak için 'alarm kur HH:MM' komutunu deneyin efendim.",
        ("teşekkür","rica"):     "Her zaman efendim! Başka bir isteğiniz?",
    }

    def __init__(self):
        self.history = []

    def add(self, category, text):
        self.history.append((category, text.lower()[:50]))
        if len(self.history) > 12: self.history = self.history[-12:]

    def get_flow_response(self, text, category):
        if not self.history: return None
        last_cat = self.history[-1][0]
        return self.FLOW_PATTERNS.get((last_cat, category))


# ═══════════════════════════════════════════════════════════════════════════════
# ── SÜPER ZEKA KATMANI ───────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════
class SuperIntelligence:
    """Tüm alt sistemleri koordine eden ana zeka"""
    def __init__(self, engine, brain=None):
        self.engine = engine
        self.brain  = brain
        self.flow   = ConversationFlow()
        self.intent = SmartIntentDetector()
        self.cache  = {}

    def process(self, text):
        # 1. Otomatik düzelt
        corrected = self.intent.autocorrect(text)
        # 2. Kısayol genişlet
        expanded, was_shortcut = self.intent.expand_shortcut(corrected)
        # 3. Cache
        cache_key = expanded.lower().strip()[:60]
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if time.time() - cached["ts"] < 180:
                return cached["resp"]
        # 4. Konuşma akışı
        _, category, _ = self._detect(expanded)
        flow_resp = self.flow.get_flow_response(expanded, category)
        if flow_resp:
            self.flow.add(category, expanded)
            return flow_resp
        # 5. Brain varsa brain'e gönder
        if self.brain:
            try:
                response, _ = self.brain.process(expanded, self.engine.generate_response)
                self.cache[cache_key] = {"resp": response, "ts": time.time()}
                if len(self.cache) > 150:
                    oldest = min(self.cache, key=lambda k: self.cache[k]["ts"])
                    del self.cache[oldest]
                self.flow.add(category, expanded)
                return response
            except: pass
        # 6. Direkt engine
        response = self.engine.generate_response(expanded)
        self.cache[cache_key] = {"resp": response, "ts": time.time()}
        self.flow.add(category, expanded)
        return response

    def _detect(self, text):
        t = text.lower()
        for cat, data in KNOWLEDGE_BASE.items():
            for trigger in data.get("triggers",[]):
                if trigger in t:
                    return text, cat, 0.8
        return text, "unknown", 0.0


# ═══════════════════════════════════════════════════════════════════════════════
# ── LOCAL OLLAMA CLIENT ───────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════
class LocalOllamaClient:
    """API key veya Ollama GEREKMİYOR. Tamamen yerel."""
    def __init__(self, model="local"):
        self.model       = model
        self.engine      = SmartResponseEngine()
        self.history     = []
        self.system      = f"Sen Anka, {USER_NAME}'in yapay zeka asistanısın."
        self.personality = "professional"
        self.current_model = "Anka Local AI v4.0 — Super Intelligence"

        # AnkaBrain
        try:
            from anka_brain import AnkaBrain
            self.brain = AnkaBrain()
            self._brain_active = True
            print("[ANKA] 🧠 Brain aktif!")
        except:
            self.brain = None
            self._brain_active = False

        # Süper Zeka
        self.super_ai = SuperIntelligence(
            self.engine,
            self.brain if self._brain_active else None
        )
        print("[ANKA] ⚡ SuperIntelligence v4 aktif!")

        # Eğitim verisi
        try:
            from anka_training_data import save_to_knowledge_base
            save_to_knowledge_base()
        except: pass

    def chat(self, message, hw_mode=False, system_override=None):
        if hw_mode:
            result = self.engine.chat(message, system_override, hw_mode)
            return result
        try:
            result = self.super_ai.process(message)
        except Exception as e:
            print(f"[ANKA] SuperAI hata: {e}")
            result = self.engine.generate_response(message)
        self.history.append({"role":"user","content":message})
        self.history.append({"role":"assistant","content":result})
        if len(self.history) > 20:
            self.history = self.history[-20:]
        return result

    def set_personality(self, p):
        self.personality = p
        self.engine.personality.set(p)

    def clear(self):
        self.history = []
        self.super_ai.cache = {}

    def summarize(self, text):
        sentences = re.split(r'[.!?]\s+', text.strip())
        return ". ".join(sentences[:3]) + "." if len(sentences) >= 3 else text[:300]

    def analyze_mood(self, text):
        _, emotion = self.engine.emotion.respond(text)
        if emotion: return emotion
        t = text.lower()
        if any(w in t for w in ["iyi","harika","mutlu","güzel"]): return "mutlu"
        if any(w in t for w in ["kötü","üzgün","sinirli","yorgun"]): return "üzgün"
        return "nötr"

    def get_model_info(self):
        return {
            "current": self.current_model,
            "brain_active": self._brain_active,
            "personality": self.personality,
            "cache_size": len(self.super_ai.cache),
            "conversations": len(self.history) // 2,
        }

    def add_knowledge(self, trigger, response):
        self.engine.learning.add_custom_response(trigger, response)
        return f"✓ Öğrendim: {trigger}"

    def brain_stats(self):
        if self._brain_active and self.brain:
            return self.brain.show_stats()
        return "Brain modu aktif değil efendim."
