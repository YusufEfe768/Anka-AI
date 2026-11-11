# ── ANKA SAĞLIK 2 MODÜLü ─────────────────────────────────────────────────────
import json, os, threading, datetime, random, time
import requests, re
from anka_config import BASE_DIR

HEALTH2_FILE = os.path.join(BASE_DIR, "anka_health2.json")

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

class HealthAssistant2:
    def __init__(self, ollama, speak_func, msg_func):
        self.ollama = ollama
        self.speak = speak_func
        self.msg = msg_func
        self.data = _load(HEALTH2_FILE, {
            "medications": [], "symptoms_log": [],
            "vitals": [], "water": 0, "water_date": ""
        })
        self._check_water_date()

    def _check_water_date(self):
        today = datetime.date.today().isoformat()
        if self.data.get("water_date") != today:
            self.data["water"] = 0
            self.data["water_date"] = today
            _save(HEALTH2_FILE, self.data)

    def add_medication(self, name, dose, times):
        self.data["medications"].append({
            "name": name, "dose": dose, "times": times,
            "added": datetime.date.today().isoformat()
        })
        _save(HEALTH2_FILE, self.data)

    def log_symptom(self, symptom, severity=5):
        self.data["symptoms_log"].append({
            "symptom": symptom, "severity": severity,
            "date": datetime.datetime.now().isoformat()
        })
        _save(HEALTH2_FILE, self.data)

    def log_vitals(self, systolic, diastolic, pulse):
        self.data["vitals"].append({
            "bp": f"{systolic}/{diastolic}",
            "pulse": pulse,
            "date": datetime.datetime.now().isoformat()
        })
        _save(HEALTH2_FILE, self.data)
        # Kontrol
        warnings = []
        if systolic > 140 or diastolic > 90:
            warnings.append("⚠️ Tansiyon yüksek!")
        if pulse > 100:
            warnings.append("⚠️ Nabız yüksek!")
        if pulse < 50:
            warnings.append("⚠️ Nabız düşük!")
        return warnings

    def drink_water(self, glasses=1):
        self._check_water_date()
        self.data["water"] += glasses
        _save(HEALTH2_FILE, self.data)
        remaining = max(0, 8 - self.data["water"])
        return self.data["water"], remaining

    def first_aid(self, situation):
        def _f():
            r = self.ollama.chat(
                f"'{situation}' için acil ilk yardım adımları.",
                system_override="İlk yardım uzmanı. Hızlı ve net adımlar ver. "
                               "Not: Acil durumlarda 112'yi arayın.")
            self.msg("ANKA", f"🚑 İlk Yardım - {situation}:\n{r}\n\n⚠️ Acil durumlarda 112'yi arayın!")
            self.speak(r[:300])
        threading.Thread(target=_f, daemon=True).start()

    def nutrition_analysis(self, food_list):
        def _n():
            r = self.ollama.chat(
                f"Şu besinlerin besin değerlerini analiz et: {food_list}",
                system_override="Diyetisyen. Besin değerleri ve sağlık etkileri.")
            self.msg("ANKA", f"🥗 Besin Analizi:\n{r}")
        threading.Thread(target=_n, daemon=True).start()

    def workout_recovery(self, workout_type):
        def _r():
            r = self.ollama.chat(
                f"'{workout_type}' sonrası iyileşme protokolü. "
                f"Beslenme, dinlenme, esneme.",
                system_override="Spor fizyolojisti. İyileşme protokolü ver.")
            self.msg("ANKA", f"💪 {workout_type} Sonrası İyileşme:\n{r}")
        threading.Thread(target=_r, daemon=True).start()

    def mental_health_check(self):
        questions = [
            "Son 2 haftadır kendinizi nasıl hissettiniz?",
            "Uyku düzeniniz nasıl?",
            "Sosyal aktivitelerinizde değişiklik var mı?",
            "Stres seviyeniz nedir? (1-10)"
        ]
        r = "🧠 Zihinsel Sağlık Kontrolü:\n"
        r += "\n".join(f"• {q}" for q in questions)
        r += "\n\nCevaplarınızı paylaşabilirsiniz."
        self.msg("ANKA", r)
        self.speak("Zihinsel sağlık kontrolü için birkaç sorum var efendim.")

    def pain_assessment(self, pain_area, intensity):
        def _p():
            r = self.ollama.chat(
                f"'{pain_area}' bölgesinde {intensity}/10 şiddetinde ağrı. "
                f"Olası nedenler ve ne zaman doktora gidilmeli?",
                system_override="Sağlık danışmanı. Genel bilgi ver, tanı koymadan.")
            self.msg("ANKA", f"🩺 Ağrı Değerlendirme:\n{r}\n\n⚠️ Şiddetli ağrıda doktora gidin!")
        threading.Thread(target=_p, daemon=True).start()

class Health2CommandProcessor:
    def __init__(self, speak_func, msg_func, ollama):
        self.speak = speak_func
        self.msg = msg_func
        self.ollama = ollama
        self.health = HealthAssistant2(ollama, speak_func, msg_func)

    def process(self, text):
        t = text.lower().strip()

        if "su içtim" in t:
            m = re.search(r'(\d+)', t)
            glasses = int(m.group(1)) if m else 1
            current, remaining = self.health.drink_water(glasses)
            emoji = "💧" if remaining > 0 else "✅"
            r = f"{emoji} Su: {current}/8 bardak. {f'{remaining} bardak kaldı.' if remaining > 0 else 'Günlük hedef tamamlandı!'}"
            self.msg("ANKA", r); self.speak(r)
            return True

        if "ilaç ekle" in t:
            parts = t.replace("ilaç ekle","").strip().split(",")
            if parts:
                name = parts[0].strip()
                dose = parts[1].strip() if len(parts) > 1 else "belirtilmedi"
                times = parts[2].strip() if len(parts) > 2 else "günde 1"
                self.health.add_medication(name, dose, times)
                r = f"✓ {name} ilacı eklendi: {dose}, {times}"
                self.msg("ANKA", r); self.speak(r)
            return True

        if "belirti kaydet" in t or "semptom" in t:
            symptom = t.replace("belirti kaydet","").replace("semptom kaydet","").strip()
            m = re.search(r'(\d+)', t)
            severity = int(m.group(1)) if m else 5
            self.health.log_symptom(symptom, severity)
            r = f"✓ Belirti kaydedildi: {symptom} (şiddet: {severity}/10)"
            self.msg("ANKA", r); self.speak(r)
            return True

        if "tansiyon" in t and re.search(r'\d+/\d+', t):
            m = re.search(r'(\d+)/(\d+)', t)
            pulse_m = re.search(r'nabız\s*(\d+)|(\d+)\s*nabız', t)
            systolic, diastolic = int(m.group(1)), int(m.group(2))
            pulse = int(pulse_m.group(1) or pulse_m.group(2)) if pulse_m else 75
            warnings = self.health.log_vitals(systolic, diastolic, pulse)
            r = f"✓ Tansiyon kaydedildi: {systolic}/{diastolic}, Nabız: {pulse}"
            if warnings:
                r += "\n" + "\n".join(warnings)
            self.msg("ANKA", r); self.speak(r)
            return True

        if "ilk yardım" in t:
            situation = t.replace("ilk yardım","").strip()
            self.health.first_aid(situation or "genel")
            return True

        if "besin analizi" in t or "ne yesem" in t:
            food = t.replace("besin analizi","").replace("ne yesem","").strip()
            self.health.nutrition_analysis(food or "dengeli beslenme")
            return True

        if "antrenman sonrası" in t or "spor sonrası" in t:
            workout = t.replace("antrenman sonrası","").replace("spor sonrası","").strip()
            self.health.workout_recovery(workout or "genel antrenman")
            return True

        if "zihinsel sağlık" in t or "ruh sağlığı kontrolü" in t:
            self.health.mental_health_check()
            return True

        if "ağrım var" in t or "ağrı değerlendir" in t:
            content = t.replace("ağrım var","").replace("ağrı değerlendir","").strip()
            intensity_m = re.search(r'(\d+)', content)
            intensity = int(intensity_m.group(1)) if intensity_m else 5
            area = re.sub(r'\d+', '', content).strip() or "genel"
            self.health.pain_assessment(area, intensity)
            return True

        if "sağlık raporu" in t:
            vitals = self.health.data.get("vitals", [])
            meds = self.health.data.get("medications", [])
            symptoms = self.health.data.get("symptoms_log", [])[-5:]
            water = self.health.data.get("water", 0)
            r = (f"🏥 Sağlık Raporu:\n"
                 f"• Su: {water}/8 bardak\n"
                 f"• İlaçlar: {len(meds)} kayıtlı\n"
                 f"• Son vitaller: {vitals[-1]['bp'] if vitals else 'yok'}\n"
                 f"• Son belirtiler: {len(symptoms)}")
            self.msg("ANKA", r); self.speak(r)
            return True

        return False
