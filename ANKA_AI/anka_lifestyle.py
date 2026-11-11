# ── ANKA YAŞAM TARZI MODÜLü ──────────────────────────────────────────────────
try:
    import pyperclip
except ImportError:
    class _PyClip:
        def copy(self,x):pass
        def paste(self):return ""
    pyperclip=_PyClip()
import json, os, threading, datetime, random, webbrowser
import requests, re, time
from anka_config import BASE_DIR

LIFESTYLE_FILE = os.path.join(BASE_DIR, "anka_lifestyle.json")
MOOD_LOG_FILE  = os.path.join(BASE_DIR, "anka_mood_log.json")

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

class LifestyleCoach:
    def __init__(self, ollama, speak_func, msg_func):
        self.ollama = ollama
        self.speak = speak_func
        self.msg = msg_func
        self.mood_log = _load(MOOD_LOG_FILE, [])

    def log_mood(self, mood, note=""):
        self.mood_log.append({
            "mood": mood, "note": note,
            "date": datetime.date.today().isoformat(),
            "time": datetime.datetime.now().strftime("%H:%M")
        })
        if len(self.mood_log) > 365:
            self.mood_log = self.mood_log[-365:]
        _save(MOOD_LOG_FILE, self.mood_log)

    def mood_analysis(self):
        if len(self.mood_log) < 3:
            return "Yeterli veri yok. 'Ruh halim [duygu]' diyerek kayıt yapın."
        last_7 = self.mood_log[-7:]
        moods = [m["mood"] for m in last_7]
        most_common = max(set(moods), key=moods.count)
        return f"📊 Son 7 gün ruh hali analizi:\nEn sık: {most_common}\nKayıtlar: {', '.join(moods)}"

    def morning_routine(self, wake_time, goals):
        def _r():
            r = self.ollama.chat(
                f"Saat {wake_time}'de kalkan biri için sabah rutini. Hedefler: {goals}",
                system_override="Yaşam koçu. Verimli sabah rutini tasarla.")
            self.msg("ANKA", f"☀️ Sabah Rutini ({wake_time}):\n{r}")
        threading.Thread(target=_r, daemon=True).start()

    def evening_routine(self):
        def _e():
            r = self.ollama.chat(
                "Akşam verimliliği ve dinlenme için ideal rutin.",
                system_override="Yaşam koçu. Rahatlatıcı akşam rutini.")
            self.msg("ANKA", f"🌙 Akşam Rutini:\n{r}")
        threading.Thread(target=_e, daemon=True).start()

    def habit_formation(self, habit, duration_days=21):
        def _h():
            r = self.ollama.chat(
                f"'{habit}' alışkanlığını {duration_days} günde kazanma planı. "
                f"Günlük adımlar ve motivasyon stratejisi.",
                system_override="Alışkanlık uzmanı. Adım adım plan yap.")
            self.msg("ANKA", f"🔄 Alışkanlık Planı - {habit}:\n{r}")
            pyperclip.copy(r)
        threading.Thread(target=_h, daemon=True).start()

    def stress_relief(self, stress_level="orta"):
        techniques = {
            "düşük": ["5 dakika nefes egzersizi", "Kısa yürüyüş", "Müzik dinle"],
            "orta": ["Meditasyon", "Egzersiz", "Arkadaşla konuş", "Günlük yaz"],
            "yüksek": ["Profesyonel destek alın", "Düzenli uyku", "Sosyal medyadan uzak dur"]
        }
        level_techs = techniques.get(stress_level, techniques["orta"])
        r = f"😌 Stres Azaltma Teknikleri ({stress_level} seviye):\n"
        r += "\n".join(f"• {t}" for t in level_techs)
        self.msg("ANKA", r)
        self.speak(r[:200])

    def life_goals(self, timeframe="1 yıl"):
        def _g():
            r = self.ollama.chat(
                f"{timeframe} için hayat hedefleri belirleme rehberi. "
                f"Sağlık, kariyer, ilişkiler, kişisel gelişim alanlarında.",
                system_override="Yaşam koçu. Somut hedefler belirlemeye yardım et.")
            self.msg("ANKA", f"🎯 {timeframe} Hedefleri:\n{r}")
        threading.Thread(target=_g, daemon=True).start()

    def digital_detox(self, hours=2):
        def _d():
            r = self.ollama.chat(
                f"{hours} saatlik dijital detoks planı. Ne yapılabilir?",
                system_override="Dijital sağlık uzmanı. Offline aktiviteler öner.")
            self.msg("ANKA", f"📵 {hours} Saatlik Detoks:\n{r}")
        threading.Thread(target=_d, daemon=True).start()

    def gratitude_journal(self):
        prompts = [
            "Bugün için minnettar olduğunuz 3 şey nedir?",
            "Bugün sizi güldüren bir şey oldu mu?",
            "Bugün kendinizi övebileceğiniz bir şey?",
            "Hayatınızda kimi veya neyi takdir ediyorsunuz?"
        ]
        r = f"📔 Şükran Günlüğü:\n{random.choice(prompts)}"
        self.msg("ANKA", r)
        self.speak(r)

    def sleep_optimization(self, sleep_issues=""):
        def _s():
            r = self.ollama.chat(
                f"Uyku optimizasyonu rehberi. Sorunlar: {sleep_issues or 'genel'}",
                system_override="Uyku uzmanı. Bilimsel uyku iyileştirme öner.")
            self.msg("ANKA", f"😴 Uyku Optimizasyonu:\n{r}")
        threading.Thread(target=_s, daemon=True).start()

    def mindfulness_exercise(self, duration_min=5):
        def _m():
            r = self.ollama.chat(
                f"{duration_min} dakikalık farkındalık egzersizi rehberi.",
                system_override="Meditasyon uzmanı. Adım adım egzersiz yaz.")
            self.msg("ANKA", f"🧘 {duration_min} Dakika Farkındalık:\n{r}")
            self.speak(r[:300])
        threading.Thread(target=_m, daemon=True).start()

class LifestyleCommandProcessor:
    def __init__(self, speak_func, msg_func, ollama):
        self.speak = speak_func
        self.msg = msg_func
        self.ollama = ollama
        self.coach = LifestyleCoach(ollama, speak_func, msg_func)

    def process(self, text):
        t = text.lower().strip()

        if "ruh halim" in t:
            moods = ["mutlu","üzgün","sinirli","stresli","enerjik","sakin","heyecanlı","yorgun","kaygılı"]
            mood = next((m for m in moods if m in t), None)
            if mood:
                self.coach.log_mood(mood, t)
                r = f"✓ Ruh hali kaydedildi: {mood}"
                self.msg("ANKA", r)
            return True

        if "ruh hali analizi" in t or "duygu raporu" in t:
            r = self.coach.mood_analysis()
            self.msg("ANKA", r); self.speak(r)
            return True

        if "sabah rutini" in t:
            time_m = re.search(r'(\d{1,2})[:\.](\d{2})', t)
            wake = f"{time_m.group(1)}:{time_m.group(2)}" if time_m else "07:00"
            self.coach.morning_routine(wake, "verimlilik ve sağlık")
            return True

        if "akşam rutini" in t:
            self.coach.evening_routine()
            return True

        if "alışkanlık kazan" in t or "alışkanlık oluştur" in t:
            habit = t.replace("alışkanlık kazan","").replace("alışkanlık oluştur","").strip()
            self.coach.habit_formation(habit or "egzersiz")
            return True

        if "stres azalt" in t or "stresim var" in t:
            level = "yüksek" if "çok" in t or "yüksek" in t else "orta"
            self.coach.stress_relief(level)
            return True

        if "hayat hedefleri" in t or "hedef belirle" in t:
            timeframe = "1 yıl"
            if "5 yıl" in t: timeframe = "5 yıl"
            elif "3 yıl" in t: timeframe = "3 yıl"
            self.coach.life_goals(timeframe)
            return True

        if "dijital detoks" in t:
            m = re.search(r'(\d+)', t)
            hours = int(m.group(1)) if m else 2
            self.coach.digital_detox(hours)
            return True

        if "şükran günlüğü" in t or "minnettar" in t:
            self.coach.gratitude_journal()
            return True

        if "uyku optimizasyon" in t or "uyku problemi" in t:
            issue = t.replace("uyku optimizasyon","").replace("uyku problemi","").strip()
            self.coach.sleep_optimization(issue)
            return True

        if "farkındalık" in t or "meditasyon egzersizi" in t:
            m = re.search(r'(\d+)', t)
            mins = int(m.group(1)) if m else 5
            self.coach.mindfulness_exercise(mins)
            return True

        return False
