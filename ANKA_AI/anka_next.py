# ── ANKA NEXT — Yeni Nesil Özellikler ────────────────────────────────────────
try:
    import pyperclip
except ImportError:
    class _PyClip:
        def copy(self,x):pass
        def paste(self):return ""
    pyperclip=_PyClip()
import json, os, time, threading, datetime, subprocess, webbrowser, re
import requests, random, math, psutil
from anka_config import BASE_DIR, USER_NAME

NEXT_FILE = os.path.join(BASE_DIR, "anka_next.json")

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
# 1. OTONOM AJAN — Kendi başına görev yapar
# ═══════════════════════════════════════════════════════════════════════════════
class AutonomousAgent:
    def __init__(self, ollama, speak_func, msg_func):
        self.ollama = ollama
        self.speak = speak_func
        self.msg = msg_func
        self.tasks = []
        self.running = True
        self.agent_file = os.path.join(BASE_DIR, "anka_agent.json")
        self.data = _load(self.agent_file, {"tasks": [], "completed": []})
        threading.Thread(target=self._agent_loop, daemon=True).start()

    def add_task(self, task, schedule_time=None, repeat=False):
        item = {
            "id": len(self.data["tasks"]) + 1,
            "task": task,
            "schedule": schedule_time,
            "repeat": repeat,
            "created": datetime.datetime.now().isoformat(),
            "done": False
        }
        self.data["tasks"].append(item)
        _save(self.agent_file, self.data)
        r = f"🤖 Otonom görev eklendi: '{task}'" + (f" (Saat: {schedule_time})" if schedule_time else "")
        self.msg("ANKA", r); self.speak(r)

    def execute_task(self, task):
        def _e():
            self.msg("ANKA", f"⚙️ Otonom görev çalışıyor: {task}")
            # Görev türünü tespit et
            t = task.lower()
            if "haber" in t:
                try:
                    import xml.etree.ElementTree as ET
                    r = requests.get("https://www.hurriyet.com.tr/rss/anasayfa", timeout=5)
                    root = ET.fromstring(r.content)
                    items = root.findall(".//item")[:3]
                    news = [i.find("title").text for i in items if i.find("title") is not None]
                    self.msg("ANKA", "📰 Otomatik Haberler:\n" + "\n".join(f"• {n[:60]}" for n in news))
                except: pass
            elif "hava" in t:
                try:
                    r = requests.get("https://wttr.in/Istanbul?format=j1", timeout=5)
                    d = r.json()["current_condition"][0]
                    self.msg("ANKA", f"🌤 Otomatik Hava: {d['temp_C']}°C — {d['weatherDesc'][0]['value']}")
                except: pass
            elif "sistem" in t:
                cpu = psutil.cpu_percent(interval=1)
                ram = psutil.virtual_memory().percent
                self.msg("ANKA", f"💻 Otomatik Sistem: CPU %{cpu:.0f} | RAM %{ram:.0f}")
            else:
                result = self.ollama.chat(f"Bu görevi tamamla: {task}",
                    system_override="Otonom ajan. Görevi tamamla.")
                self.msg("ANKA", f"✅ Görev tamamlandı:\n{result}")
        threading.Thread(target=_e, daemon=True).start()

    def _agent_loop(self):
        time.sleep(30)
        while self.running:
            try:
                now = datetime.datetime.now().strftime("%H:%M")
                for task in self.data["tasks"]:
                    if not task["done"] and task.get("schedule") == now:
                        self.execute_task(task["task"])
                        if not task["repeat"]:
                            task["done"] = True
                        _save(self.agent_file, self.data)
            except: pass
            time.sleep(60)

    def list_tasks(self):
        tasks = [t for t in self.data["tasks"] if not t["done"]]
        if not tasks:
            r = "Bekleyen otonom görev yok efendim."
        else:
            r = f"🤖 Otonom Görevler ({len(tasks)}):\n"
            r += "\n".join(f"• {t['task']}" + (f" ({t['schedule']})" if t.get('schedule') else "") for t in tasks[:8])
        self.msg("ANKA", r)

    def stop(self): self.running = False


# ═══════════════════════════════════════════════════════════════════════════════
# 2. AKILLI MAKRO — Komut zinciri kaydet
# ═══════════════════════════════════════════════════════════════════════════════
class SmartMacro:
    def __init__(self, speak_func, msg_func):
        self.speak = speak_func
        self.msg = msg_func
        self.macro_file = os.path.join(BASE_DIR, "anka_macros.json")
        self.macros = _load(self.macro_file, {})
        self.recording = False
        self.recording_name = None
        self.recording_steps = []

    def start_record(self, name):
        self.recording = True
        self.recording_name = name
        self.recording_steps = []
        r = f"🔴 Kayıt başladı: '{name}'\nKomutlarınızı girin, 'kaydı durdur' ile bitirin."
        self.msg("ANKA", r); self.speak(r)

    def add_step(self, command):
        if self.recording:
            self.recording_steps.append(command)
            self.msg("ANKA", f"✓ Adım {len(self.recording_steps)} kaydedildi: {command}")
            return True
        return False

    def stop_record(self):
        if not self.recording: return
        self.macros[self.recording_name] = {
            "steps": self.recording_steps,
            "created": datetime.datetime.now().isoformat()
        }
        _save(self.macro_file, self.macros)
        self.recording = False
        r = f"⏹️ '{self.recording_name}' kaydedildi! {len(self.recording_steps)} adım."
        self.msg("ANKA", r); self.speak(r)
        self.recording_name = None

    def run_macro(self, name):
        macro = self.macros.get(name.lower())
        if not macro:
            self.msg("ANKA", f"'{name}' makrosu bulunamadı efendim."); return
        r = f"▶️ '{name}' makrosu çalışıyor ({len(macro['steps'])} adım)..."
        self.msg("ANKA", r)
        return macro["steps"]

    def list_macros(self):
        if not self.macros:
            r = "Kayıtlı makro yok efendim."
        else:
            r = f"📋 Makrolar ({len(self.macros)}):\n"
            r += "\n".join(f"• {name}: {len(m['steps'])} adım" for name, m in self.macros.items())
        self.msg("ANKA", r)


# ═══════════════════════════════════════════════════════════════════════════════
# 3. AKILLI HATIRLATICI — Bağlamsal hatırlatıcı
# ═══════════════════════════════════════════════════════════════════════════════
class SmartReminder:
    def __init__(self, speak_func, msg_func):
        self.speak = speak_func
        self.msg = msg_func
        self.reminders_file = os.path.join(BASE_DIR, "anka_reminders.json")
        self.reminders = _load(self.reminders_file, [])
        self.running = True
        threading.Thread(target=self._check_loop, daemon=True).start()

    def add(self, text, when, repeat=None, priority="normal"):
        reminder = {
            "text": text,
            "when": when,
            "repeat": repeat,
            "priority": priority,
            "created": datetime.datetime.now().isoformat(),
            "triggered": False,
            "trigger_count": 0
        }
        self.reminders.append(reminder)
        _save(self.reminders_file, self.reminders)
        emoji = "🔴" if priority == "yüksek" else "🟡" if priority == "orta" else "🟢"
        r = f"{emoji} Hatırlatıcı eklendi: '{text}' — {when}"
        self.msg("ANKA", r); self.speak(r)

    def _check_loop(self):
        while self.running:
            try:
                now = datetime.datetime.now()
                now_str = now.strftime("%H:%M")
                today = now.date().isoformat()
                changed = False
                for rem in self.reminders:
                    if rem["triggered"] and not rem.get("repeat"): continue
                    when = rem["when"]
                    # Saat kontrolü
                    if ":" in when and when == now_str:
                        key = f"{rem['text']}_{today}_{when}"
                        if not rem.get(f"done_{today}"):
                            rem[f"done_{today}"] = True
                            rem["trigger_count"] = rem.get("trigger_count", 0) + 1
                            changed = True
                            emoji = "🔴" if rem["priority"] == "yüksek" else "⏰"
                            r = f"{emoji} HATIRLATICI: {rem['text']}"
                            self.msg("ANKA", r)
                            self.speak(r)
                            try:
                                requests.post("https://ntfy.sh/anka-yusuf-2026",
                                    data=r.encode(),
                                    headers={"Title":"⏰ Anka Hatırlatıcı"}, timeout=3)
                            except: pass
                if changed: _save(self.reminders_file, self.reminders)
            except: pass
            time.sleep(30)

    def list_reminders(self):
        active = [r for r in self.reminders if not r.get("triggered", False) or r.get("repeat")]
        if not active:
            r = "Aktif hatırlatıcı yok efendim."
        else:
            r = f"⏰ Hatırlatıcılar ({len(active)}):\n"
            r += "\n".join(f"• {rem['text']} — {rem['when']}" for rem in active[:8])
        self.msg("ANKA", r)

    def stop(self): self.running = False


# ═══════════════════════════════════════════════════════════════════════════════
# 4. DİL ÖĞRENMESİ ASISTANI
# ═══════════════════════════════════════════════════════════════════════════════
class LanguageLearner:
    def __init__(self, ollama, speak_func, msg_func):
        self.ollama = ollama
        self.speak = speak_func
        self.msg = msg_func
        self.learn_file = os.path.join(BASE_DIR, "anka_language.json")
        self.data = _load(self.learn_file, {
            "words": {},
            "sessions": [],
            "current_language": "İngilizce"
        })

    def daily_words(self, language="İngilizce", count=5):
        def _d():
            r = self.ollama.chat(
                f"Bugün için {count} tane {language} kelime öğret. "
                f"Her biri için: kelime, Türkçe anlamı, örnek cümle ve telaffuz ipucu.",
                system_override=f"{language} öğretmeni. Günlük kelimeler öğret.")
            self.msg("ANKA", f"📚 Günlük {language} Kelimeleri:\n{r}")
            self.speak(f"{count} {language} kelimesi hazırlandı efendim.")
        threading.Thread(target=_d, daemon=True).start()

    def translate(self, text, to_lang="İngilizce"):
        def _t():
            r = self.ollama.chat(
                f"'{text}' ifadesini {to_lang}'ceye çevir. "
                f"Çeviri, alternatifler ve kullanım notunu ver.",
                system_override="Çevirmen. Doğal çeviri yap.")
            self.msg("ANKA", f"🌐 {to_lang}:\n{r}")
            # Sadece çeviriyi kopyala
            first_line = r.split('\n')[0]
            pyperclip.copy(first_line)
            self.speak("Çeviri hazırlandı efendim.")
        threading.Thread(target=_t, daemon=True).start()

    def pronunciation_guide(self, word, language="İngilizce"):
        def _p():
            r = self.ollama.chat(
                f"'{word}' kelimesinin {language}ce telaffuzunu öğret. "
                f"IPA, Türkçe benzetme ve ipuçları ver.",
                system_override="Telaffuz uzmanı. Detaylı rehber ver.")
            self.msg("ANKA", f"🗣️ Telaffuz:\n{r}")
        threading.Thread(target=_p, daemon=True).start()

    def mini_quiz(self, language="İngilizce"):
        def _q():
            r = self.ollama.chat(
                f"{language} mini quiz: 3 soru sor. "
                f"Çoktan seçmeli, cevapları A/B/C/D şeklinde.",
                system_override=f"{language} quiz hazırlayıcı. Eğlenceli sorular sor.")
            self.msg("ANKA", f"📝 {language} Mini Quiz:\n{r}")
            self.speak("Quiz hazırlandı efendim!")
        threading.Thread(target=_q, daemon=True).start()

    def conversation_practice(self, topic, language="İngilizce"):
        def _c():
            r = self.ollama.chat(
                f"'{topic}' hakkında {language} konuşma pratiği için diyalog yaz. "
                f"A (sen) ve B (konuşma partneri) olarak. Türkçe çevirisiyle.",
                system_override=f"{language} konuşma pratiği uzmanı. Günlük diyalog yaz.")
            self.msg("ANKA", f"💬 Konuşma Pratiği:\n{r}")
        threading.Thread(target=_c, daemon=True).start()


# ═══════════════════════════════════════════════════════════════════════════════
# 5. PROJE YÖNETİCİSİ
# ═══════════════════════════════════════════════════════════════════════════════
class ProjectManager:
    def __init__(self, ollama, speak_func, msg_func):
        self.ollama = ollama
        self.speak = speak_func
        self.msg = msg_func
        self.project_file = os.path.join(BASE_DIR, "anka_projects.json")
        self.data = _load(self.project_file, {"projects": []})

    def create_project(self, name, description, deadline=None):
        project = {
            "id": len(self.data["projects"]) + 1,
            "name": name,
            "description": description,
            "deadline": deadline,
            "created": datetime.date.today().isoformat(),
            "status": "aktif",
            "tasks": [],
            "notes": [],
            "progress": 0
        }
        self.data["projects"].append(project)
        _save(self.project_file, self.data)
        r = f"📁 Proje oluşturuldu: '{name}'"
        self.msg("ANKA", r); self.speak(r)
        return project["id"]

    def add_task(self, project_id, task, priority=5):
        for p in self.data["projects"]:
            if p["id"] == project_id:
                p["tasks"].append({
                    "task": task, "priority": priority,
                    "done": False, "added": datetime.date.today().isoformat()
                })
                _save(self.project_file, self.data)
                r = f"✓ '{task}' projeye eklendi."
                self.msg("ANKA", r); self.speak(r)
                return True
        return False

    def complete_task(self, project_id, task_name):
        for p in self.data["projects"]:
            if p["id"] == project_id:
                for t in p["tasks"]:
                    if task_name.lower() in t["task"].lower():
                        t["done"] = True
                        done = sum(1 for t in p["tasks"] if t["done"])
                        p["progress"] = int(done/len(p["tasks"])*100) if p["tasks"] else 0
                        _save(self.project_file, self.data)
                        r = f"✅ Görev tamamlandı! İlerleme: %{p['progress']}"
                        self.msg("ANKA", r); self.speak(r)
                        return True
        return False

    def project_status(self, project_id=None):
        projects = self.data["projects"]
        if project_id:
            projects = [p for p in projects if p["id"] == project_id]
        if not projects:
            self.msg("ANKA", "Proje bulunamadı efendim."); return
        r = ""
        for p in projects[:3]:
            done = sum(1 for t in p["tasks"] if t["done"])
            total = len(p["tasks"])
            bar = "█" * (p["progress"]//10) + "░" * (10 - p["progress"]//10)
            r += (f"\n📁 {p['name']}\n"
                  f"[{bar}] %{p['progress']}\n"
                  f"• Görevler: {done}/{total}\n"
                  f"• Durum: {p['status']}\n")
            if p.get("deadline"):
                days = (datetime.date.fromisoformat(p["deadline"]) - datetime.date.today()).days
                r += f"• Bitiş: {p['deadline']} ({days} gün kaldı)\n"
        self.msg("ANKA", f"📊 Proje Durumu:{r}")

    def ai_project_plan(self, name, goal):
        def _plan():
            r = self.ollama.chat(
                f"'{name}' projesi için detaylı plan yap. Hedef: {goal}\n"
                f"Görevler, milestones, riskler, kaynaklar ve timeline.",
                system_override="Proje yöneticisi. Detaylı plan oluştur.")
            self.msg("ANKA", f"📋 AI Proje Planı:\n{r}")
            pyperclip.copy(r)
            self.speak("Proje planı hazırlandı efendim.")
        threading.Thread(target=_plan, daemon=True).start()

    def list_projects(self):
        active = [p for p in self.data["projects"] if p["status"] == "aktif"]
        if not active:
            r = "Aktif proje yok efendim."
        else:
            r = f"📁 Aktif Projeler ({len(active)}):\n"
            r += "\n".join(f"• #{p['id']} {p['name']} (%{p['progress']})" for p in active[:6])
        self.msg("ANKA", r)


# ═══════════════════════════════════════════════════════════════════════════════
# 6. MATEMATİK DEHASI
# ═══════════════════════════════════════════════════════════════════════════════
class MathGenius:
    def __init__(self, ollama, speak_func, msg_func):
        self.ollama = ollama
        self.speak = speak_func
        self.msg = msg_func

    def solve(self, problem):
        def _s():
            r = self.ollama.chat(
                f"Matematik problemi:\n{problem}\n\nAdım adım çöz, formülleri göster.",
                system_override="Matematik öğretmeni. Adım adım çöz.")
            self.msg("ANKA", f"📐 Çözüm:\n{r}")
        threading.Thread(target=_s, daemon=True).start()

    def calculate_advanced(self, expression):
        results = {}
        try:
            # Temel hesaplama
            safe_expr = re.sub(r'[^0-9+\-*/().%\s\^]', '', expression)
            safe_expr = safe_expr.replace('^', '**')
            result = eval(safe_expr, {"__builtins__": {}, "math": math})
            results["sonuç"] = result
            # İstatistiksel bilgiler
            if isinstance(result, (int, float)):
                results["kare"] = result ** 2
                results["karekök"] = round(math.sqrt(abs(result)), 4)
                results["log10"] = round(math.log10(abs(result)), 4) if result != 0 else "tanımsız"
                results["yüzde"] = f"%{result}"
        except: pass
        if results:
            r = f"🔢 {expression}:\n"
            r += "\n".join(f"• {k}: {v}" for k, v in results.items())
            self.msg("ANKA", r)
            self.speak(f"Sonuç: {results.get('sonuç', '?')}")
        else:
            self.msg("ANKA", "Hesaplanamadı efendim.")

    def unit_convert(self, value, from_unit, to_unit):
        conversions = {
            ("km","mil"): 0.621371, ("mil","km"): 1.60934,
            ("kg","pound"): 2.20462, ("pound","kg"): 0.453592,
            ("celsius","fahrenheit"): lambda x: x*9/5+32,
            ("fahrenheit","celsius"): lambda x: (x-32)*5/9,
            ("metre","feet"): 3.28084, ("feet","metre"): 0.3048,
            ("litre","galon"): 0.264172, ("galon","litre"): 3.78541,
            ("cm","inch"): 0.393701, ("inch","cm"): 2.54,
        }
        key = (from_unit.lower(), to_unit.lower())
        conv = conversions.get(key)
        if conv:
            result = conv(value) if callable(conv) else value * conv
            r = f"🔄 {value} {from_unit} = {result:.4f} {to_unit}"
            self.msg("ANKA", r); self.speak(r)
        else:
            self.msg("ANKA", f"'{from_unit}' → '{to_unit}' dönüşümü bilinmiyor efendim.")

    def generate_problem(self, level="orta", topic="karma"):
        def _g():
            r = self.ollama.chat(
                f"Seviye: {level}, Konu: {topic} matematik sorusu oluştur. "
                f"Soru ve cevabı ayrı ver.",
                system_override="Matematik sorusu oluşturucu.")
            self.msg("ANKA", f"📐 Matematik Sorusu:\n{r}")
            self.speak("Soru hazırlandı efendim.")
        threading.Thread(target=_g, daemon=True).start()


# ═══════════════════════════════════════════════════════════════════════════════
# KOMUT İŞLEYİCİ
# ═══════════════════════════════════════════════════════════════════════════════
class NextGenCommandProcessor:
    def __init__(self, speak_func, msg_func, ollama):
        self.speak = speak_func
        self.msg = msg_func
        self.ollama = ollama
        self.agent = AutonomousAgent(ollama, speak_func, msg_func)
        self.macro = SmartMacro(speak_func, msg_func)
        self.reminder = SmartReminder(speak_func, msg_func)
        self.language = LanguageLearner(ollama, speak_func, msg_func)
        self.project = ProjectManager(ollama, speak_func, msg_func)
        self.math = MathGenius(ollama, speak_func, msg_func)

    def process(self, text):
        t = text.lower().strip()

        # ── Otonom Ajan ───────────────────────────────────────────────────────
        if "otonom görev ekle" in t:
            parts = t.replace("otonom görev ekle","").strip().split("saat")
            task = parts[0].strip()
            schedule = parts[1].strip() if len(parts) > 1 else None
            if task: self.agent.add_task(task, schedule); return True
        if "otonom görevler" in t:
            self.agent.list_tasks(); return True
        if "görevi şimdi çalıştır" in t:
            task = t.replace("görevi şimdi çalıştır","").strip()
            if task: self.agent.execute_task(task); return True

        # ── Makro ─────────────────────────────────────────────────────────────
        if "makro kaydet" in t or "makro başlat" in t:
            name = t.replace("makro kaydet","").replace("makro başlat","").strip()
            if name: self.macro.start_record(name); return True
        if "kaydı durdur" in t:
            self.macro.stop_record(); return True
        if "makro çalıştır" in t:
            name = t.replace("makro çalıştır","").strip()
            if name:
                steps = self.macro.run_macro(name)
                return steps  # steps döndür, ana app çalıştırsın
            return True
        if "makro listesi" in t:
            self.macro.list_macros(); return True
        if self.macro.recording and t not in ["kaydı durdur"]:
            self.macro.add_step(text); return True

        # ── Hatırlatıcı ───────────────────────────────────────────────────────
        if "hatırlat" in t or "hatırlatıcı ekle" in t:
            m = re.search(r'(\d{1,2}:\d{2})', t)
            if m:
                when = m.group(1)
                reminder_text = re.sub(r'\d{1,2}:\d{2}', '', t)
                reminder_text = reminder_text.replace("hatırlat","").replace("hatırlatıcı ekle","").strip()
                priority = "yüksek" if "önemli" in t else "orta" if "orta" in t else "normal"
                self.reminder.add(reminder_text or "Hatırlatıcı", when, priority=priority)
            return True
        if "hatırlatıcılar" in t:
            self.reminder.list_reminders(); return True

        # ── Dil Öğrenme ───────────────────────────────────────────────────────
        if "günlük kelime" in t:
            lang = "İngilizce"
            for l in ["İngilizce","Almanca","Fransızca","İspanyolca","İtalyanca","Japonca"]:
                if l.lower() in t: lang = l; break
            m = re.search(r'(\d+)', t)
            count = int(m.group(1)) if m else 5
            self.language.daily_words(lang, count); return True
        if "çevir" in t or "tercüme et" in t:
            text_to_translate = t.replace("çevir","").replace("tercüme et","").strip()
            lang = "İngilizce"
            for l in ["almanca","fransızca","ispanyolca","japonca"]:
                if l in t: lang = l.capitalize(); break
            if text_to_translate:
                self.language.translate(text_to_translate, lang); return True
        if "telaffuz" in t:
            word = t.replace("telaffuz","").strip()
            if word: self.language.pronunciation_guide(word); return True
        if "dil quiz" in t or "dil sınavı" in t:
            lang = "İngilizce"
            for l in ["İngilizce","Almanca","Fransızca"]:
                if l.lower() in t: lang = l; break
            self.language.mini_quiz(lang); return True
        if "konuşma pratiği" in t:
            topic = t.replace("konuşma pratiği","").strip() or "günlük hayat"
            self.language.conversation_practice(topic); return True

        # ── Proje Yöneticisi ──────────────────────────────────────────────────
        if "proje oluştur" in t or "yeni proje" in t:
            name_m = re.search(r"['\"]([^'\"]+)['\"]", text)
            name = name_m.group(1) if name_m else t.replace("proje oluştur","").replace("yeni proje","").strip()[:30]
            if name:
                self.project.create_project(name, name)
                return True
        if "projeye görev ekle" in t:
            m = re.search(r'#(\d+)', t)
            if m:
                pid = int(m.group(1))
                task = re.sub(r'projeye görev ekle|#\d+', '', t).strip()
                self.project.add_task(pid, task); return True
        if "proje durumu" in t or "projelerim" in t:
            m = re.search(r'#(\d+)', t)
            pid = int(m.group(1)) if m else None
            self.project.project_status(pid); return True
        if "ai proje planı" in t:
            parts = t.replace("ai proje planı","").strip().split(":")
            if len(parts) >= 2:
                self.project.ai_project_plan(parts[0].strip(), parts[1].strip())
            return True

        # ── Matematik Dehası ──────────────────────────────────────────────────
        if "matematik çöz" in t:
            problem = t.replace("matematik çöz","").strip()
            if problem: self.math.solve(problem); return True
        if "gelişmiş hesapla" in t:
            expr = t.replace("gelişmiş hesapla","").strip()
            if expr: self.math.calculate_advanced(expr); return True
        if "birim çevir" in t:
            m = re.search(r'(\d+(?:\.\d+)?)\s*(\w+)\s*(?:→|to|to|den|dan)\s*(\w+)', t)
            if m:
                self.math.unit_convert(float(m.group(1)), m.group(2), m.group(3)); return True
        if "matematik sorusu üret" in t:
            level = "zor" if "zor" in t else "kolay" if "kolay" in t else "orta"
            self.math.generate_problem(level); return True

        return False
