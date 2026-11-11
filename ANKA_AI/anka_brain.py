# ── ANKA BRAIN v3 — Gelişmiş Zeka Motoru ─────────────────────────────────────
# Bağlam anlama, niyet tespiti, duygusal zeka, öğrenme, tahmin
import json, os, re, time, math, datetime, random, difflib
from anka_config import BASE_DIR, USER_NAME

BRAIN_FILE   = os.path.join(BASE_DIR, "anka_brain.json")
CONTEXT_FILE = os.path.join(BASE_DIR, "anka_brain_context.json")
LEARN_FILE   = os.path.join(BASE_DIR, "anka_brain_learn.json")

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
# ── NİYET TESPİT MOTORU ──────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════
class IntentEngine:
    INTENT_PATTERNS = {
        "hava": {
            "patterns": ["hava","hava nasıl","hava durumu","yağmur","sıcaklık",
                        "derece","kar yağar mı","güneşli mi","bulutlu","soğuk mu"],
            "normalized": "hava nasıl", "category": "hava"
        },
        "saat": {
            "patterns": ["saat","saat kaç","zaman","tarih","gün","ay","yıl","bugün"],
            "normalized": "saat kaç", "category": "saat"
        },
        "sistem": {
            "patterns": ["sistem","cpu","ram","disk","pil","bellek","işlemci"],
            "normalized": "sistem durumu", "category": "sistem"
        },
        "döviz": {
            "patterns": ["dolar","euro","sterlin","döviz","kur","tl","lira"],
            "normalized": "döviz kuru", "category": "döviz"
        },
        "kripto": {
            "patterns": ["bitcoin","btc","ethereum","eth","kripto","coin"],
            "normalized": "bitcoin fiyatı", "category": "kripto"
        },
        "haber": {
            "patterns": ["haber","gündem","son dakika","ne oldu","bugün ne var"],
            "normalized": "haberler neler", "category": "haber"
        },
        "selamlama": {
            "patterns": ["merhaba","selam","hey","hi","hello","günaydın","iyi günler"],
            "normalized": "merhaba", "category": "selamlama"
        },
        "veda": {
            "patterns": ["bye","hoşçakal","görüşürüz","güle güle","çıkıyorum"],
            "normalized": "hoşçakal", "category": "veda"
        },
        "yardım": {
            "patterns": ["yardım","help","ne yaparsın","özellikler","komutlar"],
            "normalized": "ne yapabilirsin", "category": "yardım"
        },
        "teşekkür": {
            "patterns": ["teşekkür","sağ ol","eyvallah","thanks","çok iyi","helal"],
            "normalized": "teşekkürler", "category": "teşekkür"
        },
        "motivasyon": {
            "patterns": ["motive et","moral ver","cesaretlen","ilham ver","güçlendir"],
            "normalized": "motivasyon ver", "category": "motivasyon"
        },
    }

    SHORTCUTS = {
        "h":"hava nasıl","hv":"hava nasıl","s":"saat kaç","ss":"saat kaç",
        "d":"döviz kuru","b":"bitcoin","btc":"bitcoin","n":"haberler",
        "y":"yardım","m":"merhaba","sd":"sistem durumu","kr":"kripto fiyatları",
    }

    TYPOS = {
        "slm":"selam","mrb":"merhaba","nbr":"ne haber","naber":"ne haber",
        "tşk":"teşekkür","tmm":"tamam","hva":"hava","nsl":"nasıl",
        "evt":"evet","hyr":"hayır","gj":"güzel","ok":"tamam",
    }

    def autocorrect(self, text):
        words = text.lower().split()
        return " ".join(self.TYPOS.get(w, w) for w in words)

    def expand_shortcut(self, text):
        t = text.lower().strip()
        if t in self.SHORTCUTS:
            return self.SHORTCUTS[t], True
        return text, False

    def detect(self, text):
        t = text.lower().strip()
        # Kısayol
        if t in self.SHORTCUTS:
            expanded = self.SHORTCUTS[t]
            return expanded, "shortcut", 1.0
        # Matematiksel ifade
        if re.match(r'^[\d\s\+\-\*\/\(\)\.\^%]+$', t) and any(c.isdigit() for c in t):
            return f"hesapla {text}", "hesap", 0.9
        # Pattern eşleştirme
        best_intent, best_score, best_cat = None, 0.0, None
        for intent_name, data in self.INTENT_PATTERNS.items():
            for pattern in data["patterns"]:
                if pattern in t:
                    score = len(pattern) / max(len(t), 1) * 2
                    score = min(score, 1.0)
                    if score > best_score:
                        best_score = score
                        best_intent = data["normalized"]
                        best_cat = data["category"]
        if best_intent and best_score > 0.1:
            return best_intent, best_cat, best_score
        # Bulanık eşleşme
        all_patterns = [(p, d["normalized"], d["category"])
                       for d in self.INTENT_PATTERNS.values()
                       for p in d["patterns"]]
        for word in t.split():
            matches = difflib.get_close_matches(word,
                [p[0] for p in all_patterns], n=1, cutoff=0.78)
            if matches:
                for pattern, normalized, category in all_patterns:
                    if pattern == matches[0]:
                        return normalized, category, 0.65
        return text, "unknown", 0.0


# ═══════════════════════════════════════════════════════════════════════════════
# ── BAĞLAM YÖNETİCİSİ ────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════
class ContextManager:
    def __init__(self):
        self.data = _load(CONTEXT_FILE, {
            "conversation": [], "current_topic": None,
            "mentioned_entities": [], "user_preferences": {},
            "session_start": datetime.datetime.now().isoformat(),
            "topic_history": []
        })
        self.short_term = []

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
            self.data["current_topic"] = category
            if category not in self.data["topic_history"]:
                self.data["topic_history"].append(category)
                if len(self.data["topic_history"]) > 20:
                    self.data["topic_history"] = self.data["topic_history"][-20:]
        self.data["conversation"].append(entry)
        if len(self.data["conversation"]) > 100:
            self.data["conversation"] = self.data["conversation"][-100:]
        _save(CONTEXT_FILE, self.data)

    def resolve_reference(self, text):
        t = text.lower().strip()
        # Kısa onay/red
        if t in ["evet","e","yes","tamam","ok","olur","tabi","tabii","aynen"]:
            if self.short_term:
                last = self.short_term[-1]
                return f"evet, {last['text'][:40]}"
        if t in ["hayır","h","no","olmaz","istemiyorum"]:
            return "hayır teşekkürler"
        # Zamir referansları
        if any(t.startswith(p) for p in ["o ","bu ","şu "]) and self.data.get("current_topic"):
            return text
        return text

    def extract_entities(self, text):
        entities = []
        for word in text.split():
            if len(word) > 2 and word[0].isupper() and \
               word not in ["Ben","Sen","O","Biz","Siz","Bu","Şu","Ne","Nasıl"]:
                entities.append(word)
        if entities:
            self.data["mentioned_entities"].extend(entities)
            self.data["mentioned_entities"] = list(dict.fromkeys(
                self.data["mentioned_entities"]))[-15:]
            _save(CONTEXT_FILE, self.data)
        return entities

    def get_topic_context(self):
        if not self.short_term: return ""
        last = self.short_term[-3:]
        return " | ".join(
            f"{'K' if m['role']=='user' else 'A'}: {m['text'][:40]}"
            for m in last)

    def get_preference(self, key): return self.data["user_preferences"].get(key)
    def set_preference(self, key, value):
        self.data["user_preferences"][key] = value
        _save(CONTEXT_FILE, self.data)
    def get_conversation_count(self): return len(self.data["conversation"])
    def get_topic_history(self): return self.data.get("topic_history", [])


# ═══════════════════════════════════════════════════════════════════════════════
# ── AKILLI ÖĞRENME ───────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════
class SmartLearning:
    def __init__(self):
        self.data = _load(LEARN_FILE, {
            "word_frequency": {},
            "topic_frequency": {},
            "time_patterns": {},
            "user_facts": {},
            "custom_qa": {},
            "corrections": [],
            "feedback": [],
            "conversation_insights": []
        })

    def observe(self, text, category):
        # Kelime sıklığı
        for word in text.lower().split():
            if len(word) > 2:
                self.data["word_frequency"][word] = \
                    self.data["word_frequency"].get(word, 0) + 1
        # Konu sıklığı
        if category:
            self.data["topic_frequency"][category] = \
                self.data["topic_frequency"].get(category, 0) + 1
        # Zaman kalıbı
        hour = str(datetime.datetime.now().hour)
        if hour not in self.data["time_patterns"]:
            self.data["time_patterns"][hour] = {}
        self.data["time_patterns"][hour][category or "general"] = \
            self.data["time_patterns"][hour].get(category or "general", 0) + 1
        self._extract_facts(text)
        _save(LEARN_FILE, self.data)

    def _extract_facts(self, text):
        patterns = [
            (r"adım\s+([A-ZÇĞİÖŞÜa-zçğışöşü]+)", "isim"),
            (r"(\d+)\s+yaşındayım", "yaş"),
            (r"([A-ZÇĞİÖŞÜ][a-zçğışöşü]+)'(?:da|de|ta|te)\s+(?:yaşıyorum|oturuyorum)", "şehir"),
            (r"([A-ZÇĞİÖŞÜ][a-zçğışöşü]+)\s+(?:okuyorum|öğrencisiyim)", "okul"),
            (r"([a-zçğışöşü]+)\s+seviyorum", "sevdiği"),
            (r"hobim\s+([a-zçğışöşü\s]+?)(?:\.|,|$)", "hobi"),
            (r"işim\s+([a-zçğışöşü\s]+?)(?:\.|,|$)", "meslek"),
        ]
        for pattern, label in patterns:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                self.data["user_facts"][label] = m.group(1).strip()

    def add_custom_qa(self, trigger, response):
        self.data["custom_qa"][trigger.lower()] = {
            "response": response,
            "added": datetime.datetime.now().isoformat(),
            "use_count": 0
        }
        _save(LEARN_FILE, self.data)

    def find_custom(self, text):
        t = text.lower()
        # Tam eşleşme
        if t in self.data["custom_qa"]:
            self.data["custom_qa"][t]["use_count"] += 1
            _save(LEARN_FILE, self.data)
            return self.data["custom_qa"][t]["response"]
        # Kısmi eşleşme
        for trigger, data in self.data["custom_qa"].items():
            if trigger in t:
                data["use_count"] += 1
                _save(LEARN_FILE, self.data)
                return data["response"]
        # Bulanık
        triggers = list(self.data["custom_qa"].keys())
        matches = difflib.get_close_matches(t, triggers, n=1, cutoff=0.82)
        if matches:
            self.data["custom_qa"][matches[0]]["use_count"] += 1
            _save(LEARN_FILE, self.data)
            return self.data["custom_qa"][matches[0]]["response"]
        return None

    def get_user_profile(self):
        facts = self.data["user_facts"]
        profile = f"{USER_NAME}"
        if "isim" in facts: profile = facts["isim"]
        extras = []
        if "yaş" in facts: extras.append(f"{facts['yaş']} yaş")
        if "şehir" in facts: extras.append(facts["şehir"])
        if "meslek" in facts: extras.append(facts["meslek"])
        if extras: profile += f" ({', '.join(extras)})"
        return profile

    def get_top_topics(self, n=5):
        return sorted(self.data["topic_frequency"].items(),
                     key=lambda x: -x[1])[:n]

    def predict_next(self, category):
        transitions = {
            "hava": ["giysi önerisi","hava etkisi","haftalık hava"],
            "saat": ["alarm","hatırlatıcı","program"],
            "sistem": ["ram temizlik","darboğaz analizi","süreç"],
            "selamlama": ["yardım","hava","haber","nasılsın"],
            "kripto": ["döviz","hisse analizi","portföy"],
            "döviz": ["kripto","altın","ekonomi"],
            "haber": ["detay","kaynak","dünya nabzı"],
        }
        return transitions.get(category, [])

    def get_stats(self):
        return {
            "words": len(self.data["word_frequency"]),
            "topics": len(self.data["topic_frequency"]),
            "facts": len(self.data["user_facts"]),
            "custom_qa": len(self.data["custom_qa"]),
            "corrections": len(self.data["corrections"]),
            "top_topics": self.get_top_topics(5)
        }

    def add_feedback(self, text, positive):
        self.data["feedback"].append({
            "text": text[:100], "positive": positive,
            "date": datetime.date.today().isoformat()
        })
        _save(LEARN_FILE, self.data)

    def add_correction(self, wrong, correct):
        self.data["corrections"].append({
            "wrong": wrong[:100], "correct": correct[:100],
            "date": datetime.date.today().isoformat()
        })
        _save(LEARN_FILE, self.data)


# ═══════════════════════════════════════════════════════════════════════════════
# ── DUYGUSAL ZEKA ─────────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════
class EmotionalIntelligence:
    EMOTIONS = {
        "mutlu": {
            "words": ["mutluyum","harika","süper","mükemmel","neşeliyim","sevindim",
                     "güzel","memnun","iyi hissediyorum","müthiş","harikayım"],
            "responses": [
                "Bu haberi duymak güzel efendim! 😊 Bu enerjiyi koruyun!",
                "Harika efendim! Mutluluğunuz beni de mutlu etti! 🌟",
                "Ne güzel efendim! Bugün harika şeyler başarabilirsiniz! ⚡",
            ],
            "follow_up": "Bu güzel ruh halini verimli kullanmak ister misiniz?"
        },
        "üzgün": {
            "words": ["üzgünüm","kötüyüm","moralim bozuk","ağlıyorum","depresyon",
                     "mutsuzum","üzülüyorum","kötü hissediyorum","içim sıkışık"],
            "responses": [
                "Üzgünüm bunu duyduğuma efendim 💙 Her şey geçer. Yanınızdayım.",
                "Zor zamanlar herkesin başına gelir efendim. Güçlüsünüz! 💪",
                "Bu his de geçer efendim. Size yardımcı olmak için buradayım 🌟",
            ],
            "follow_up": "Size yardımcı olabileceğim bir şey var mı?"
        },
        "sinirli": {
            "words": ["sinirliyim","kızgınım","öfkeliyim","bıktım","usandım",
                     "dayanamıyorum","saçma","berbat","sinir oldum"],
            "responses": [
                "Anlıyorum efendim, bu can sıkıcı olmalı. Derin nefes alın 🌬️",
                "Haklısınız efendim. Birlikte çözelim bunu.",
                "Sinirlenebilirsiniz efendim. Nasıl yardımcı olabilirim?",
            ],
            "follow_up": "Problemi çözmek için ne yapabiliriz?"
        },
        "yorgun": {
            "words": ["yorgunum","bitkinim","uyku bastı","enerjim yok","halsizim",
                     "tükendim","çok yoruldum","ayakta duramıyorum"],
            "responses": [
                "Dinlenin efendim! 😴 20 dakikalık kısa uyku harika gelir.",
                "Yorgunluk önemli bir sinyal efendim. Su için, biraz yürüyün 💧",
                "Mola verin efendim! Vücudunuz hak ediyor bunu ☕",
            ],
            "follow_up": "Ne kadar süredir çalışıyorsunuz?"
        },
        "stresli": {
            "words": ["stres","stresli","bunaldım","panikledim","endişeleniyorum",
                     "kaygılanıyorum","kafam karıştı","baskı altındayım"],
            "responses": [
                "Derin nefes alın efendim 🌬️ 4 sayı nefes, 4 tut, 4 verin.",
                "Stres yönetilebilir efendim. Önce en önemlisine odaklanın 🎯",
                "Her şeyi bir anda çözmenize gerek yok efendim. Adım adım 👣",
            ],
            "follow_up": "Ne sizi en çok stres ediyor?"
        },
        "heyecanlı": {
            "words": ["heyecanlıyım","çok heyecanlı","sabırsızlanıyorum","bekleyemiyorum",
                     "harika haber","çok iyi haber","inanamıyorum"],
            "responses": [
                "Bu heyecanı hissedebiliyorum efendim! 🚀 Paylaşın, ne var?",
                "Mükemmel efendim! Bu enerjiyle neler başarabilirsiniz! ⚡",
                "Harika efendim! 🎉",
            ],
            "follow_up": "Daha fazla anlatır mısınız?"
        },
        "kararsız": {
            "words": ["bilmiyorum","emin değilim","karar veremedim","kafam karışık",
                     "ne yapacağımı bilmiyorum","ikileme düştüm","zor karar"],
            "responses": [
                "Anlaşılabilir efendim. Seçenekleri birlikte değerlendirelim mi?",
                "Kararsızlık normaldir efendim. Artıları ve eksileri yazalım mı?",
                "Size yardımcı olabilirim efendim. Hangi konuda kararsızsınız?",
            ],
            "follow_up": "Her iki seçeneği de analiz edelim mi?"
        },
    }

    def detect(self, text):
        t = text.lower()
        scores = {}
        for emotion, data in self.EMOTIONS.items():
            score = sum(1 for word in data["words"] if word in t)
            if score > 0: scores[emotion] = score
        return max(scores, key=scores.get) if scores else None

    def respond(self, text):
        emotion = self.detect(text)
        if emotion:
            resp = random.choice(self.EMOTIONS[emotion]["responses"])
            follow = self.EMOTIONS[emotion].get("follow_up","")
            if follow and random.random() > 0.5:
                resp += f"\n💭 {follow}"
            return resp, emotion
        return None, None


# ═══════════════════════════════════════════════════════════════════════════════
# ── TAHMİN MOTORU ─────────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════
class PredictionEngine:
    def __init__(self, learning):
        self.learning = learning

    def suggest_next(self, current_text, category, context):
        suggestions = []
        hour = datetime.datetime.now().hour
        # Saate göre
        if 6 <= hour < 9:
            suggestions.extend(["hava nasıl","günlük program","günaydın"])
        elif 12 <= hour < 13:
            suggestions.append("öğle planı")
        elif 17 <= hour < 19:
            suggestions.extend(["haberler","günü değerlendir"])
        elif 22 <= hour:
            suggestions.extend(["yarın için plan","iyi geceler"])
        # Konuya göre
        topic_preds = self.learning.predict_next(category)
        suggestions.extend(topic_preds)
        # En çok kullanılanlar
        top = [t[0] for t in self.learning.get_top_topics(2)]
        suggestions.extend(top)
        return list(dict.fromkeys(suggestions))[:3]


# ═══════════════════════════════════════════════════════════════════════════════
# ── ANA BRAIN SINIFI ─────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════
class AnkaBrain:
    def __init__(self):
        self.intent    = IntentEngine()
        self.context   = ContextManager()
        self.learning  = SmartLearning()
        self.emotion   = EmotionalIntelligence()
        self.predictor = PredictionEngine(self.learning)
        self.personality = "professional"

    def process(self, text, base_response_fn):
        # 1. Yazım düzeltme
        corrected = self.intent.autocorrect(text)
        # 2. Kısayol genişletme
        expanded, was_shortcut = self.intent.expand_shortcut(corrected)
        # 3. Referans çözümleme
        resolved = self.context.resolve_reference(expanded)
        # 4. Özel cevap
        custom = self.learning.find_custom(text)
        if custom:
            self.context.add("user", text, "custom")
            self.context.add("assistant", custom, "custom")
            self.learning.observe(text, "custom")
            return custom, None
        # 5. Duygu tespiti (kısa mesajlarda)
        if len(text.split()) <= 8:
            emo_resp, emotion = self.emotion.respond(text)
            if emo_resp:
                hour = datetime.datetime.now().hour
                if emotion == "üzgün" and hour < 8:
                    emo_resp += "\n🌅 Sabah zor başlayabilir. İyi bir gün olacak!"
                elif emotion == "yorgun" and hour > 22:
                    emo_resp += "\n🌙 Gece geç oldu, dinlenmenizi öneririm."
                self.context.add("user", text, "emotion")
                self.context.add("assistant", emo_resp, "emotion")
                self.learning.observe(text, "emotion")
                return emo_resp, None
        # 6. Niyet tespiti
        _, category, confidence = self.intent.detect(resolved)
        # 7. Öğren
        self.learning.observe(text, category)
        self.context.extract_entities(text)
        self.context.add("user", text, category)
        # 8. Temel cevap
        response = base_response_fn(resolved)
        # 9. Kişiselleştir
        response = self._personalize(response, text, category)
        # 10. Kaydet
        self.context.add("assistant", response, category)
        # 11. Tahmin
        suggestions = self.predictor.suggest_next(text, category, self.context)
        return response, suggestions

    def _personalize(self, response, text, category):
        facts = self.learning.data.get("user_facts", {})
        name  = facts.get("isim", USER_NAME)
        hour  = datetime.datetime.now().hour
        conv  = self.context.get_conversation_count()
        # İlk karşılaşma
        if conv <= 2 and "merhaba" not in response.lower():
            response = f"Merhaba {name}! " + response
        # Sabah selamı
        elif conv <= 5 and 5 <= hour < 10 and category == "selamlama":
            response = f"Günaydın {name}! " + response
        # Gece geç
        elif hour >= 23 and category == "selamlama":
            response = f"Gece geç oldu {name}! " + response
        # Kısa cevaplara ipucu
        if len(response) < 60 and category not in ["selamlama","teşekkür","veda","emotion"]:
            tips = {
                "hesap":  "\n💡 'gelişmiş hesapla' ile daha fazlası",
                "hava":   "\n💡 'saatlik hava' veya 'haftalık hava' deneyin",
                "sistem": "\n💡 'sistem dashboard' ile tam rapor",
                "kripto": "\n💡 'korku endeksi' veya 'kripto fiyatları' deneyin",
            }
            tip = tips.get(category,"")
            if tip: response += tip
        return response

    def teach(self, trigger, response):
        self.learning.add_custom_qa(trigger, response)
        return f"✓ Öğrendim! '{trigger}' → '{response[:50]}' efendim."

    def correct(self, wrong, correct):
        self.learning.add_correction(wrong, correct)
        return "✓ Düzeltme kaydedildi efendim! Teşekkürler."

    def feedback(self, positive, text=""):
        self.learning.add_feedback(text, positive)
        if positive:
            return "Teşekkürler efendim! Bu geri bildirim çok yardımcı! 😊"
        return "Anlıyorum efendim. Nasıl daha iyi yapabilirim?"

    def show_stats(self):
        stats = self.learning.get_stats()
        conv  = self.context.get_conversation_count()
        top_topics = stats.get("top_topics", [])
        r = (f"🧠 ANKA BEYİN v3 — İSTATİSTİKLER\n{'═'*38}\n"
             f"💬 Konuşma: {conv}\n"
             f"📚 Kelime: {stats['words']:,}\n"
             f"🎯 Konu: {stats['topics']}\n"
             f"👤 Kullanıcı Bilgisi: {stats['facts']}\n"
             f"✏️ Özel Q&A: {stats['custom_qa']}\n"
             f"🔧 Düzeltme: {stats['corrections']}\n"
             f"👤 Profil: {self.learning.get_user_profile()}\n")
        if top_topics:
            r += "\n📊 En Çok Sorulanlar:\n"
            r += "\n".join(f"  • {t}: {c}x" for t,c in top_topics[:5])
        topic_hist = self.context.get_topic_history()
        if topic_hist:
            r += f"\n\n🕐 Konu Geçmişi: {' → '.join(topic_hist[-5:])}"
        return r
