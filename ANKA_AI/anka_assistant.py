# ── ANKA KİŞİSEL ASİSTAN MODÜLü ─────────────────────────────────────────────
try:
    import pyperclip
except ImportError:
    class _PyClip:
        def copy(self,x):pass
        def paste(self):return ""
    pyperclip=_PyClip()
import json, os, threading, datetime, webbrowser, subprocess
import requests, re, random, time
from anka_config import BASE_DIR

ASSISTANT_FILE = os.path.join(BASE_DIR, "anka_assistant.json")

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

class PersonalAssistant:
    def __init__(self, ollama, speak_func, msg_func):
        self.ollama = ollama
        self.speak = speak_func
        self.msg = msg_func
        self.data = _load(ASSISTANT_FILE, {"preferences": {}, "history": []})

    def set_preference(self, key, value):
        self.data["preferences"][key] = value
        _save(ASSISTANT_FILE, self.data)

    def get_preference(self, key, default=None):
        return self.data["preferences"].get(key, default)

    def smart_search(self, query):
        def _s():
            # Önce AI cevabı al
            ai_reply = self.ollama.chat(
                f"'{query}' hakkında kısa bilgi ver.",
                system_override="Asistan. Kısa ve net cevap ver.")
            self.msg("ANKA", f"💡 {ai_reply}")
            # Sonra web'de de aç
            webbrowser.open(f"https://www.google.com/search?q={query}")
            self.speak(ai_reply[:200])
        threading.Thread(target=_s, daemon=True).start()

    def remind_birthday(self, name, date_str):
        data = _load(ASSISTANT_FILE, {"birthdays": {}})
        if "birthdays" not in data:
            data["birthdays"] = {}
        data["birthdays"][name] = date_str
        _save(ASSISTANT_FILE, data)

    def check_birthdays(self):
        data = _load(ASSISTANT_FILE, {"birthdays": {}})
        birthdays = data.get("birthdays", {})
        today = datetime.date.today()
        upcoming = []
        for name, date_str in birthdays.items():
            try:
                parts = date_str.split("-")
                bday = datetime.date(today.year, int(parts[1]), int(parts[2]))
                if bday < today:
                    bday = datetime.date(today.year + 1, int(parts[1]), int(parts[2]))
                days_left = (bday - today).days
                upcoming.append((name, days_left, date_str))
            except: pass
        return sorted(upcoming, key=lambda x: x[1])

    def meeting_prep(self, topic, participants, duration):
        def _p():
            r = self.ollama.chat(
                f"Toplantı: {topic}, Katılımcılar: {participants}, Süre: {duration} dk. "
                f"Gündem, hazırlık checklist, sorular listele.",
                system_override="Toplantı koordinatörü. Eksiksiz hazırlık listesi yap.")
            self.msg("ANKA", f"📋 Toplantı Hazırlık - {topic}:\n{r}")
            pyperclip.copy(r)
            self.speak("Toplantı hazırlığı tamam efendim.")
        threading.Thread(target=_p, daemon=True).start()

    def draft_email(self, recipient, subject, key_points, tone="resmi"):
        def _e():
            r = self.ollama.chat(
                f"Kime: {recipient}, Konu: {subject}, Noktalar: {key_points}, Ton: {tone}. "
                f"Profesyonel Türkçe mail yaz.",
                system_override="İş yazışmaları uzmanı. Eksiksiz mail yaz.")
            self.msg("ANKA", f"📧 Mail Taslağı:\n{r}")
            pyperclip.copy(r)
            self.speak("Mail taslağı hazırlandı efendim.")
        threading.Thread(target=_e, daemon=True).start()

    def delegation_plan(self, task, team_members):
        def _d():
            r = self.ollama.chat(
                f"Görev: {task}, Ekip: {team_members}. "
                f"Görevi nasıl delege edelim? Kime ne, ne zaman?",
                system_override="Proje yöneticisi. Delege planı yap.")
            self.msg("ANKA", f"📊 Delege Planı:\n{r}")
        threading.Thread(target=_d, daemon=True).start()

    def create_checklist(self, task):
        def _c():
            r = self.ollama.chat(
                f"'{task}' için eksiksiz yapılacaklar listesi.",
                system_override="Proje asistanı. Adım adım checklist yap.")
            self.msg("ANKA", f"✅ Checklist - {task}:\n{r}")
            pyperclip.copy(r)
        threading.Thread(target=_c, daemon=True).start()

    def daily_briefing(self):
        def _b():
            now = datetime.datetime.now()
            try:
                r = requests.get("https://wttr.in/Istanbul?format=j1", timeout=5)
                d = r.json()["current_condition"][0]
                weather = f"{d['temp_C']}°C {d['weatherDesc'][0]['value']}"
            except:
                weather = "bilinmiyor"
            try:
                r2 = requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=5)
                usd = r2.json()["rates"]["TRY"]
                currency = f"1 USD = {usd:.2f}₺"
            except:
                currency = "bilinmiyor"

            birthdays = self.check_birthdays()
            bday_text = ""
            for name, days, _ in birthdays[:2]:
                if days == 0:
                    bday_text += f"\n🎂 BUGÜN {name}'in doğum günü!"
                elif days <= 7:
                    bday_text += f"\n🎂 {name}: {days} gün sonra doğum günü"

            briefing = (
                f"🌅 GÜNLÜK BRİFİNG — {now.strftime('%d %B %Y, %H:%M')}\n"
                f"{'━'*35}\n"
                f"🌤 Hava: {weather}\n"
                f"💱 Döviz: {currency}\n"
                f"{bday_text}\n"
                f"{'━'*35}\n"
                f"💪 Günün Sözü: {random.choice(['Başarı hazırlıkla buluştuğunda gelir.','Her gün yeni bir fırsat.','Küçük adımlar büyük yolculuklar yapar.'])}"
            )
            self.msg("ANKA", briefing)
            self.speak(f"Günaydın efendim! Bugün {now.strftime('%d %B')}, hava {weather}.")
        threading.Thread(target=_b, daemon=True).start()

    def gift_ideas(self, person, budget, occasion):
        def _g():
            r = self.ollama.chat(
                f"Kişi: {person}, Bütçe: {budget}₺, Durum: {occasion}. "
                f"10 hediye fikri öner. Neden uygun olduğunu açıkla.",
                system_override="Hediye uzmanı. Yaratıcı ve pratik öneriler ver.")
            self.msg("ANKA", f"🎁 Hediye Önerileri:\n{r}")
        threading.Thread(target=_g, daemon=True).start()

class AssistantCommandProcessor:
    def __init__(self, speak_func, msg_func, ollama):
        self.speak = speak_func
        self.msg = msg_func
        self.ollama = ollama
        self.assistant = PersonalAssistant(ollama, speak_func, msg_func)

    def process(self, text):
        t = text.lower().strip()

        if "akıllı ara" in t or "hızlı bilgi" in t:
            query = t.replace("akıllı ara","").replace("hızlı bilgi","").strip()
            if query:
                self.assistant.smart_search(query)
            return True

        if "doğum günü ekle" in t or "doğum günü kaydet" in t:
            name_m = re.search(r"'([^']+)'|\"([^\"]+)\"|(\w+)(?=\s+doğum)", t)
            date_m = re.search(r'(\d{4}-\d{2}-\d{2}|\d{1,2}[./]\d{1,2}[./]\d{2,4})', t)
            if date_m:
                date_str = date_m.group(1).replace('.','-').replace('/','-')
                name = name_m.group(1) or name_m.group(2) or "Kişi" if name_m else "Kişi"
                self.assistant.remind_birthday(name, date_str)
                r = f"✓ {name}'in doğum günü kaydedildi: {date_str}"
                self.msg("ANKA", r); self.speak(r)
            return True

        if "doğum günleri" in t or "yaklaşan doğum günü" in t:
            birthdays = self.assistant.check_birthdays()
            if not birthdays:
                r = "Kayıtlı doğum günü yok efendim."
            else:
                r = "🎂 Yaklaşan Doğum Günleri:\n"
                for name, days, date in birthdays[:5]:
                    emoji = "🎉" if days == 0 else "⏳"
                    r += f"{emoji} {name}: {'BUGÜN!' if days==0 else f'{days} gün sonra'}\n"
            self.msg("ANKA", r); self.speak(r)
            return True

        if "toplantı hazırlık" in t or "toplantıya hazırlan" in t:
            topic = t.replace("toplantı hazırlık","").replace("toplantıya hazırlan","").strip()
            self.assistant.meeting_prep(topic or "iş toplantısı", "Ekip", 60)
            return True

        if "mail taslağı" in t or "mail yaz" in t:
            content = t.replace("mail taslağı","").replace("mail yaz","").strip()
            self.assistant.draft_email("Alıcı", content or "Genel", "Belirtilmedi")
            return True

        if "checklist oluştur" in t or "yapılacaklar listesi" in t:
            task = t.replace("checklist oluştur","").replace("yapılacaklar listesi","").strip()
            self.assistant.create_checklist(task or "proje")
            return True

        if "günlük brifing" in t or "sabah özeti" in t:
            self.assistant.daily_briefing()
            return True

        if "hediye fikri" in t or "ne hediye alsam" in t:
            content = t.replace("hediye fikri","").replace("ne hediye alsam","").strip()
            self.assistant.gift_ideas("arkadaş", 500, content or "doğum günü")
            return True

        if "delege et" in t or "görevi dağıt" in t:
            task = t.replace("delege et","").replace("görevi dağıt","").strip()
            self.assistant.delegation_plan(task, "ekip üyeleri")
            return True

        if "tercih kaydet" in t:
            parts = t.replace("tercih kaydet","").strip().split("=")
            if len(parts) == 2:
                self.assistant.set_preference(parts[0].strip(), parts[1].strip())
                r = f"✓ Tercih kaydedildi: {parts[0]} = {parts[1]}"
                self.msg("ANKA", r); self.speak(r)
            return True

        return False
