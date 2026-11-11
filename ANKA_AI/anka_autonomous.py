# ── ANKA OTONOM YAPAY ZEKA EKOSİSTEMİ ───────────────────────────────────────
# Kendi başına düşünen, planlayan, öğrenen ve çalışan otonom ajan sistemi
# Yusuf'un imzasını taşıyan gelecek nesil AI mimarisi

try:
    import pyperclip
except ImportError:
    class _PyClip:
        def copy(self,x):pass
        def paste(self):return ""
    pyperclip=_PyClip()
import json, os, time, threading, datetime, subprocess, webbrowser
import requests, re, random, psutil
from anka_config import BASE_DIR

AGENT_MEMORY  = os.path.join(BASE_DIR, "anka_agent_memory.json")
AGENT_LOG     = os.path.join(BASE_DIR, "anka_agent_log.json")
AGENT_GOALS   = os.path.join(BASE_DIR, "anka_agent_goals.json")
AGENT_SKILLS  = os.path.join(BASE_DIR, "anka_agent_skills.json")

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
# ── AJAN BEYNİ (Agent Brain) ─────────────────────────────────────────────────
# Anka'nın otonom düşünme merkezi
# ═══════════════════════════════════════════════════════════════════════════════
class AgentBrain:
    """
    Anka'nın merkezi düşünme motoru.
    Görevleri analiz eder, planlar oluşturur, kararlar alır.
    """
    def __init__(self, ollama):
        self.ollama = ollama
        self.working_memory = []  # Kısa süreli hafıza
        self.context = {}         # Anlık bağlam
        self.confidence_threshold = 0.7

    def analyze(self, situation):
        """Durumu analiz et ve ne yapılması gerektiğini belirle"""
        prompt = (
            f"Durum: {situation}\n\n"
            f"Bağlam: {json.dumps(self.context, ensure_ascii=False)[:500]}\n\n"
            f"Şu soruları cevapla:\n"
            f"1. Bu durumda ne yapılmalı?\n"
            f"2. Hangi bilgiye ihtiyaç var?\n"
            f"3. Öncelik sırası nedir?\n"
            f"4. Risk var mı?\n\n"
            f"JSON formatında: {{\"action\": str, \"needs\": list, \"priority\": int, \"risk\": str}}"
        )
        try:
            r = self.ollama.chat(prompt,
                system_override="Sen bir yapay zeka ajanının analiz motorusun. Kısa JSON cevap ver.")
            clean = r.replace("```json","").replace("```","").strip()
            return json.loads(clean)
        except:
            return {"action": "manual", "needs": [], "priority": 5, "risk": "unknown"}

    def plan(self, goal, constraints=None):
        """Hedef için adım adım plan oluştur"""
        prompt = (
            f"Hedef: {goal}\n"
            f"Kısıtlar: {constraints or 'yok'}\n\n"
            f"Bu hedefi gerçekleştirmek için 5 adımlık somut plan yap.\n"
            f"Her adım bilgisayarda yapılabilir olmalı.\n"
            f"Format: JSON liste [{{'step': int, 'action': str, 'tool': str, 'expected': str}}]"
        )
        try:
            r = self.ollama.chat(prompt,
                system_override="Otonom AI ajan planlayıcısısın. Pratik adımlar ver.")
            clean = r.replace("```json","").replace("```","").strip()
            # JSON parse dene, olmazsa satır satır parse et
            try:
                return json.loads(clean)
            except:
                steps = []
                for i, line in enumerate(r.split('\n'), 1):
                    if line.strip() and len(line) > 5:
                        steps.append({"step": i, "action": line.strip(),
                                     "tool": "general", "expected": "tamamlandı"})
                return steps[:5]
        except:
            return []

    def decide(self, options, context=""):
        """Seçenekler arasında en iyi kararı ver"""
        prompt = (
            f"Bağlam: {context}\n"
            f"Seçenekler: {options}\n\n"
            f"En iyi seçeneği ve nedenini seç. Sadece seçenek numarasını ve kısa gerekçe ver."
        )
        return self.ollama.chat(prompt,
            system_override="Karar verici AI. En mantıklı seçeneği seç.")

    def reflect(self, action_taken, result):
        """Yapılan işlemi değerlendir ve öğren"""
        self.working_memory.append({
            "action": action_taken,
            "result": result,
            "timestamp": datetime.datetime.now().isoformat(),
            "success": "hata" not in result.lower() and "başarısız" not in result.lower()
        })
        if len(self.working_memory) > 50:
            self.working_memory = self.working_memory[-50:]

    def update_context(self, key, value):
        self.context[key] = value


# ═══════════════════════════════════════════════════════════════════════════════
# ── UZMAN AJANLAR (Specialist Agents) ────────────────────────────────────────
# Her biri belirli bir alanda uzmanlaşmış alt ajanlar
# ═══════════════════════════════════════════════════════════════════════════════
class ResearchAgent:
    """Web araştırması yapan uzman ajan"""
    def __init__(self, ollama, msg_func):
        self.ollama = ollama
        self.msg = msg_func
        self.name = "Araştırma Ajanı"

    def run(self, topic, depth="derin"):
        self.msg("ANKA", f"🔍 [{self.name}] '{topic}' araştırılıyor...")
        results = []

        # DuckDuckGo
        try:
            r = requests.get(
                f"https://api.duckduckgo.com/?q={topic}&format=json",
                timeout=5)
            data = r.json()
            if data.get("Abstract"):
                results.append(f"[DuckDuckGo]: {data['Abstract'][:300]}")
            for related in data.get("RelatedTopics", [])[:3]:
                if isinstance(related, dict) and related.get("Text"):
                    results.append(related["Text"][:200])
        except: pass

        # Wikipedia
        try:
            r = requests.get(
                f"https://tr.wikipedia.org/api/rest_v1/page/summary/{topic.replace(' ','_')}",
                timeout=5)
            if r.status_code == 200:
                extract = r.json().get("extract","")[:400]
                if extract:
                    results.append(f"[Wikipedia]: {extract}")
        except: pass

        # Haber
        try:
            import xml.etree.ElementTree as ET
            r = requests.get(
                f"https://news.google.com/rss/search?q={topic}&hl=tr&gl=TR",
                timeout=5)
            root = ET.fromstring(r.content)
            items = root.findall(".//item")[:3]
            for item in items:
                title = item.find("title")
                if title is not None:
                    results.append(f"[Haber]: {title.text}")
        except: pass

        if not results:
            return f"'{topic}' hakkında veri bulunamadı."

        context = "\n\n".join(results)
        summary = self.ollama.chat(
            f"Şu araştırma bulgularını sentezle ve özetle:\n\n{context}",
            system_override="Araştırmacı. Kaynakları sentezle, Türkçe özetle.")
        return summary


class WriterAgent:
    """İçerik üreten uzman ajan"""
    def __init__(self, ollama, msg_func):
        self.ollama = ollama
        self.msg = msg_func
        self.name = "Yazar Ajanı"

    def run(self, task, style="profesyonel", length="orta"):
        self.msg("ANKA", f"✍️ [{self.name}] İçerik oluşturuluyor...")
        lengths = {"kısa": "150-200 kelime", "orta": "400-500 kelime", "uzun": "800-1000 kelime"}
        r = self.ollama.chat(
            f"Görev: {task}\nTarzan: {style}\nUzunluk: {lengths.get(length,'400 kelime')}",
            system_override="Uzman yazar. Verilen tarzda, belirtilen uzunlukta yaz.")
        pyperclip.copy(r)
        return r


class CoderAgent:
    """Kod yazan uzman ajan"""
    def __init__(self, ollama, msg_func):
        self.ollama = ollama
        self.msg = msg_func
        self.name = "Kodlama Ajanı"

    def run(self, task, language="python"):
        self.msg("ANKA", f"💻 [{self.name}] Kod yazılıyor...")
        r = self.ollama.chat(
            f"{language} ile şunu yap: {task}\n\nSadece kodu yaz, açıklama minimal.",
            system_override=f"Senior {language} developer. Temiz, çalışan kod yaz.")
        pyperclip.copy(r)
        return r

    def debug(self, code, error=""):
        r = self.ollama.chat(
            f"Kodu düzelt:\n{code}\n\nHata: {error}",
            system_override="Debug uzmanı. Hatayı bul, düzeltilmiş kodu ver.")
        return r

    def execute_safe(self, code):
        """Kodu güvenli şekilde çalıştır"""
        try:
            import io, contextlib
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exec(code, {"__builtins__": {
                    "print": print, "range": range, "len": len,
                    "str": str, "int": int, "float": float,
                    "list": list, "dict": dict, "sum": sum,
                    "max": max, "min": min, "sorted": sorted
                }})
            return output.getvalue() or "Kod çalıştı, çıktı yok."
        except Exception as e:
            return f"Hata: {e}"


class PlannerAgent:
    """Proje planlayan uzman ajan"""
    def __init__(self, ollama, msg_func):
        self.ollama = ollama
        self.msg = msg_func
        self.name = "Planlayıcı Ajan"

    def run(self, project, timeline="1 ay", resources="sınırlı"):
        self.msg("ANKA", f"📅 [{self.name}] Proje planı oluşturuluyor...")
        r = self.ollama.chat(
            f"Proje: {project}\nSüre: {timeline}\nKaynaklar: {resources}\n\n"
            f"Detaylı proje planı: Milestones, görevler, riskler, başarı kriterleri.",
            system_override="Proje yöneticisi. Gerçekçi ve uygulanabilir plan yap.")
        return r


class AnalystAgent:
    """Veri analizi yapan uzman ajan"""
    def __init__(self, ollama, msg_func):
        self.ollama = ollama
        self.msg = msg_func
        self.name = "Analiz Ajanı"

    def run(self, data, question):
        self.msg("ANKA", f"📊 [{self.name}] Analiz yapılıyor...")
        r = self.ollama.chat(
            f"Veri: {data}\nSoru: {question}\n\nDetaylı analiz yap.",
            system_override="Veri analisti. Veriden içgörü çıkar, öner.")
        return r


class MonitorAgent:
    """Sistemi izleyen ve proaktif davranan ajan"""
    def __init__(self, ollama, speak_func, msg_func):
        self.ollama = ollama
        self.speak = speak_func
        self.msg = msg_func
        self.name = "İzleme Ajanı"
        self.running = True
        self.alerts_sent = {}
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        time.sleep(30)
        while self.running:
            try:
                self._check_system()
                self._check_time_based()
            except: pass
            time.sleep(60)

    def _check_system(self):
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory().percent
        now_key = datetime.datetime.now().strftime("%Y-%m-%d %H")

        if cpu > 90 and self.alerts_sent.get(f"cpu_{now_key}") != True:
            self.alerts_sent[f"cpu_{now_key}"] = True
            suggestion = self.ollama.chat(
                f"CPU %{cpu} kullanımda. Hızlı çözüm öner.",
                system_override="Sistem uzmanı. 1 cümlelik çözüm ver.")
            r = f"🔴 CPU Kritik (%{cpu})!\n💡 {suggestion}"
            self.msg("SİSTEM", r)

        if ram > 90 and self.alerts_sent.get(f"ram_{now_key}") != True:
            self.alerts_sent[f"ram_{now_key}"] = True
            r = "🔴 RAM Kritik! Gereksiz uygulamaları kapatın efendim."
            self.msg("SİSTEM", r)
            self.speak(r)

    def _check_time_based(self):
        now = datetime.datetime.now()
        # Öğle hatırlatıcısı
        if now.hour == 12 and now.minute == 0:
            key = f"lunch_{now.date()}"
            if not self.alerts_sent.get(key):
                self.alerts_sent[key] = True
                self.msg("ANKA", "🍽️ Öğle yemeği zamanı efendim!")

        # Göz dinlendirme (her 20 dakika)
        if now.minute % 20 == 0 and now.second < 60:
            key = f"eye_{now.strftime('%H:%M')}"
            if not self.alerts_sent.get(key):
                self.alerts_sent[key] = True
                self.msg("SİSTEM", "👁️ Gözlerinizi dinlendirin! 20 saniye uzağa bakın.")

    def stop(self):
        self.running = False


# ═══════════════════════════════════════════════════════════════════════════════
# ── OTONOM GÖREV YÖNETİCİSİ ──────────────────────────────────────────────────
# Karmaşık görevleri otomatik olarak doğru ajana yönlendiren orkestratör
# ═══════════════════════════════════════════════════════════════════════════════
class AgentOrchestrator:
    """
    Tüm ajanları koordine eden merkezi sistem.
    Görevi analiz eder, hangi ajanın kullanılacağına karar verir,
    ajanları sırayla veya paralel çalıştırır.
    """
    def __init__(self, ollama, speak_func, msg_func):
        self.ollama = ollama
        self.speak = speak_func
        self.msg = msg_func
        self.brain = AgentBrain(ollama)

        # Uzman ajanlar
        self.agents = {
            "araştırma": ResearchAgent(ollama, msg_func),
            "yazar": WriterAgent(ollama, msg_func),
            "kodlama": CoderAgent(ollama, msg_func),
            "planlayıcı": PlannerAgent(ollama, msg_func),
            "analiz": AnalystAgent(ollama, msg_func),
        }

        self.active_goals = []
        self.completed_goals = []
        self.log = _load(AGENT_LOG, [])

    def classify_task(self, task):
        """Görevi analiz et, hangi ajan(lar) gerekli belirle"""
        keywords = {
            "araştırma": ["araştır","bul","hakkında bilgi","nedir","öğren","araştırma"],
            "yazar": ["yaz","oluştur","makale","rapor","içerik","metin","taslak"],
            "kodlama": ["kod","python","javascript","program","script","yazılım","geliştir"],
            "planlayıcı": ["plan","proje","organize","strateji","roadmap","yol haritası"],
            "analiz": ["analiz","değerlendir","karşılaştır","veri","istatistik","rapor"],
        }
        task_lower = task.lower()
        scores = {}
        for agent, kws in keywords.items():
            score = sum(1 for kw in kws if kw in task_lower)
            if score > 0:
                scores[agent] = score

        if scores:
            return sorted(scores.items(), key=lambda x: -x[1])
        return [("araştırma", 1)]  # Default

    def execute(self, goal, auto_mode=False):
        """Hedefi çalıştır"""
        goal_entry = {
            "goal": goal,
            "started": datetime.datetime.now().isoformat(),
            "status": "running",
            "steps": []
        }
        self.active_goals.append(goal_entry)

        def _run():
            self.msg("ANKA",
                f"🤖 OTONOM AJAN BAŞLADI\n"
                f"{'═'*40}\n"
                f"🎯 Hedef: {goal}\n"
                f"🧠 Beyin analiz yapıyor...")

            # 1. Analiz
            analysis = self.brain.analyze(goal)
            self.msg("ANKA",
                f"📊 Analiz Sonucu:\n"
                f"• Eylem: {analysis.get('action','belirsiz')}\n"
                f"• Öncelik: {analysis.get('priority',5)}/10\n"
                f"• Risk: {analysis.get('risk','düşük')}")

            # 2. Hangi ajanlar gerekli?
            agent_list = self.classify_task(goal)
            self.msg("ANKA",
                f"🔧 Kullanılacak Ajanlar: "
                f"{', '.join(a[0] for a in agent_list[:3])}")

            # 3. Plan oluştur
            steps = self.brain.plan(goal)
            if steps:
                plan_text = "\n".join(
                    f"  {s.get('step','?')}. {s.get('action','?')}"
                    for s in steps[:5])
                self.msg("ANKA", f"📋 Yürütme Planı:\n{plan_text}")

            time.sleep(1)

            # 4. Ajanları çalıştır
            results = []
            for agent_name, _ in agent_list[:2]:
                agent = self.agents.get(agent_name)
                if not agent: continue

                self.msg("ANKA", f"\n⚙️ {agent.name} çalışıyor...")

                if agent_name == "araştırma":
                    result = agent.run(goal)
                elif agent_name == "yazar":
                    result = agent.run(f"'{goal}' hakkında içerik oluştur")
                elif agent_name == "kodlama":
                    result = agent.run(goal)
                elif agent_name == "planlayıcı":
                    result = agent.run(goal)
                elif agent_name == "analiz":
                    result = agent.run(goal, "Genel değerlendirme yap")
                else:
                    continue

                results.append((agent_name, result))
                self.brain.reflect(agent_name, result)

                # Sonucu göster
                self.msg("ANKA",
                    f"✅ {agent.name} tamamladı:\n"
                    f"{result[:400]}...")

                goal_entry["steps"].append({
                    "agent": agent_name,
                    "result_length": len(result)
                })

            # 5. Sentez
            if len(results) > 1:
                self.msg("ANKA", "🔄 Sonuçlar sentezleniyor...")
                combined = "\n\n".join(f"[{name}]: {result[:300]}" for name, result in results)
                final = self.ollama.chat(
                    f"Bu ajan çıktılarını birleştir ve '{goal}' için final rapor hazırla:\n\n{combined}",
                    system_override="Orkestratör. Ajan çıktılarını sentezle.")
                self.msg("ANKA",
                    f"\n🏆 FİNAL RAPOR\n{'═'*40}\n{final}")
                pyperclip.copy(final)
                self.speak("Otonom görev tamamlandı efendim. Rapor panoya kopyalandı.")
            elif results:
                pyperclip.copy(results[0][1])
                self.speak("Otonom görev tamamlandı efendim.")

            # 6. Log
            goal_entry["status"] = "completed"
            goal_entry["completed"] = datetime.datetime.now().isoformat()
            self.completed_goals.append(goal_entry)
            self.active_goals.remove(goal_entry)

            self.log.append({
                "goal": goal,
                "date": datetime.datetime.now().isoformat(),
                "agents_used": [a[0] for a in agent_list[:2]],
                "success": True
            })
            if len(self.log) > 200:
                self.log = self.log[-200:]
            _save(AGENT_LOG, self.log)

            self.msg("ANKA",
                f"\n✨ Görev Tamamlandı!\n"
                f"📊 İstatistik: {len(results)} ajan, "
                f"{sum(len(r[1]) for r in results)} karakter çıktı")

        threading.Thread(target=_run, daemon=True).start()

    def get_status(self):
        return {
            "active": len(self.active_goals),
            "completed": len(self.completed_goals),
            "agents": list(self.agents.keys())
        }

    def get_history(self, limit=10):
        return self.log[-limit:]


# ═══════════════════════════════════════════════════════════════════════════════
# ── ÖĞRENEN HAFIZA SİSTEMİ ───────────────────────────────────────────────────
# Anka zamanla öğrenen ve gelişen hafıza
# ═══════════════════════════════════════════════════════════════════════════════
class LearningMemory:
    """
    Anka'nın öğrenen hafızası.
    Kullanıcı davranışlarından, hatalardan ve başarılardan öğrenir.
    """
    def __init__(self, ollama):
        self.ollama = ollama
        self.memory = _load(AGENT_MEMORY, {
            "facts": [],
            "patterns": {},
            "preferences": {},
            "corrections": [],
            "skills": [],
            "last_updated": None
        })

    def observe(self, event_type, data):
        """Olayı gözlemle ve öğren"""
        if event_type == "command":
            cmd = data.lower()[:30]
            self.memory["patterns"][cmd] = self.memory["patterns"].get(cmd, 0) + 1

        elif event_type == "correction":
            self.memory["corrections"].append({
                "correction": data,
                "date": datetime.date.today().isoformat()
            })

        elif event_type == "preference":
            key, value = data
            self.memory["preferences"][key] = value

        self.memory["last_updated"] = datetime.datetime.now().isoformat()
        _save(AGENT_MEMORY, self.memory)

    def get_context_for_prompt(self):
        """Sistem promptuna eklenecek kişiselleştirilmiş bağlam"""
        context_parts = []

        # Sık kullanılan komutlar
        if self.memory["patterns"]:
            top = sorted(self.memory["patterns"].items(), key=lambda x: -x[1])[:3]
            context_parts.append(f"Sık kullanılan: {', '.join(c[0] for c in top)}")

        # Tercihler
        if self.memory["preferences"]:
            prefs = list(self.memory["preferences"].items())[:3]
            context_parts.append(f"Tercihler: {', '.join(f'{k}={v}' for k,v in prefs)}")

        # Son düzeltmeler
        if self.memory["corrections"]:
            last = self.memory["corrections"][-2:]
            context_parts.append(f"Düzeltmeler: {'; '.join(c['correction'] for c in last)}")

        return "\n".join(context_parts) if context_parts else ""

    def extract_fact(self, text):
        """Metinden öğrenilebilecek gerçeği çıkar"""
        keywords = ["seviyorum","istemiyorum","her zaman","hiç","doğum günüm",
                   "annem","babam","arkadaşım","okulum","hobim"]
        if any(kw in text.lower() for kw in keywords):
            self.memory["facts"].append({
                "fact": text[:100],
                "date": datetime.date.today().isoformat()
            })
            if len(self.memory["facts"]) > 300:
                self.memory["facts"] = self.memory["facts"][-300:]
            _save(AGENT_MEMORY, self.memory)

    def get_stats(self):
        return {
            "facts": len(self.memory["facts"]),
            "patterns": len(self.memory["patterns"]),
            "corrections": len(self.memory["corrections"]),
            "last_updated": self.memory.get("last_updated","hiç")
        }


# ═══════════════════════════════════════════════════════════════════════════════
# ── PROAKTIF ANKA ─────────────────────────────────────────────────────────────
# Sen söylemeden önce davranan Anka
# ═══════════════════════════════════════════════════════════════════════════════
class ProactiveAnka:
    """
    Kullanıcı sormadan önce harekete geçen sistem.
    Alışkanlıkları öğrenir, tahmin eder, önerir.
    """
    def __init__(self, ollama, speak_func, msg_func, learning_memory):
        self.ollama = ollama
        self.speak = speak_func
        self.msg = msg_func
        self.memory = learning_memory
        self.running = True
        self.last_suggestions = {}
        threading.Thread(target=self._proactive_loop, daemon=True).start()

    def _proactive_loop(self):
        time.sleep(120)  # 2 dakika bekle, sistem kurulsun
        while self.running:
            try:
                now = datetime.datetime.now()
                today = now.date().isoformat()

                # Sabah rutini (08:00)
                if now.hour == 8 and now.minute == 0:
                    self._morning_brief(now, today)

                # Öğle önerisi (12:30)
                elif now.hour == 12 and now.minute == 30:
                    self._lunch_suggestion(today)

                # Akşam özeti (18:00)
                elif now.hour == 18 and now.minute == 0:
                    self._evening_summary(today)

                # Çalışma hatırlatıcı (saatte bir)
                elif now.minute == 0 and 9 <= now.hour <= 17:
                    self._work_reminder(now, today)

                # Gece uyarısı (23:00)
                elif now.hour == 23 and now.minute == 0:
                    self._sleep_reminder(today)

            except: pass
            time.sleep(60)

    def _morning_brief(self, now, today):
        key = f"morning_{today}"
        if self.last_suggestions.get(key): return
        self.last_suggestions[key] = True
        def _m():
            try:
                r = requests.get("https://wttr.in/Istanbul?format=j1", timeout=5)
                d = r.json()["current_condition"][0]
                temp = d["temp_C"]; desc = d["weatherDesc"][0]["value"]
                weather_text = f"{temp}°C, {desc}"
            except:
                weather_text = "bilinmiyor"

            msg = (f"🌅 Günaydın efendim!\n"
                   f"━━━━━━━━━━━━━━━━━\n"
                   f"🌤 Hava: {weather_text}\n"
                   f"📅 {now.strftime('%d %B %Y, %A')}\n"
                   f"━━━━━━━━━━━━━━━━━\n"
                   f"💪 {random.choice(['Bugün harika şeyler başaracaksınız!','Her gün yeni bir fırsat!','Kendinize inanın!'])}")
            self.msg("ANKA", msg)
            self.speak(f"Günaydın efendim! Bugün {weather_text}.")
        threading.Thread(target=_m, daemon=True).start()

    def _lunch_suggestion(self, today):
        key = f"lunch_{today}"
        if self.last_suggestions.get(key): return
        self.last_suggestions[key] = True
        r = "🍽️ Öğle molası zamanı efendim! Ekrandan uzaklaşın, yiyin, dinlenin."
        self.msg("ANKA", r)

    def _evening_summary(self, today):
        key = f"evening_{today}"
        if self.last_suggestions.get(key): return
        self.last_suggestions[key] = True
        self.msg("ANKA",
            "🌆 Akşam oldu efendim! Günü nasıl geçirdiniz?\n"
            "'Günü değerlendir' yazarsanız özet çıkartabilirim.")

    def _work_reminder(self, now, today):
        key = f"work_{now.strftime('%H')}_{today}"
        if self.last_suggestions.get(key): return
        self.last_suggestions[key] = True
        tips = [
            "⏰ Bir saat geçti, biraz hareket edin efendim!",
            "💧 Su içmeyi unutmayın efendim!",
            "👁️ Gözlerinizi dinlendirin, 20 saniye uzağa bakın efendim!"
        ]
        self.msg("ANKA", random.choice(tips))

    def _sleep_reminder(self, today):
        key = f"sleep_{today}"
        if self.last_suggestions.get(key): return
        self.last_suggestions[key] = True
        self.msg("ANKA",
            "🌙 Gece geç oldu efendim! İyi bir uyku sağlık için önemli.\n"
            "Bilgisayarı kapatmamı ister misiniz?")

    def stop(self):
        self.running = False


# ═══════════════════════════════════════════════════════════════════════════════
# ── KOMUT İŞLEYİCİ ───────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════
class AutonomousCommandProcessor:
    def __init__(self, speak_func, msg_func, ollama):
        self.speak = speak_func
        self.msg = msg_func
        self.ollama = ollama
        self.orchestrator = AgentOrchestrator(ollama, speak_func, msg_func)
        self.monitor = MonitorAgent(ollama, speak_func, msg_func)
        self.learning = LearningMemory(ollama)
        self.proactive = ProactiveAnka(ollama, speak_func, msg_func, self.learning)

    def process(self, text):
        t = text.lower().strip()

        # Öğren
        self.learning.observe("command", t)
        self.learning.extract_fact(text)

        # ── Otonom Görev ──────────────────────────────────────────────────────
        if t.startswith("otonom:") or t.startswith("ajan:") or "kendiliğinden yap:" in t:
            goal = text.replace("otonom:","").replace("ajan:","").replace("kendiliğinden yap:","").strip()
            if goal:
                self.orchestrator.execute(goal)
            return True

        # ── Araştırma Ajanı ───────────────────────────────────────────────────
        if "araştırma ajanı:" in t or "derinlemesine araştır:" in t:
            topic = text.replace("araştırma ajanı:","").replace("derinlemesine araştır:","").strip()
            if topic:
                def _r():
                    result = self.orchestrator.agents["araştırma"].run(topic, "derin")
                    self.msg("ANKA", f"🔍 Araştırma Sonucu:\n{result}")
                    pyperclip.copy(result)
                    self.speak("Araştırma tamamlandı efendim.")
                threading.Thread(target=_r, daemon=True).start()
            return True

        # ── Yazar Ajanı ───────────────────────────────────────────────────────
        if "yazar ajanı:" in t or "içerik ajanı:" in t:
            task = text.replace("yazar ajanı:","").replace("içerik ajanı:","").strip()
            if task:
                def _w():
                    result = self.orchestrator.agents["yazar"].run(task)
                    self.msg("ANKA", f"✍️ İçerik:\n{result}")
                    self.speak("İçerik hazırlandı efendim.")
                threading.Thread(target=_w, daemon=True).start()
            return True

        # ── Kodlama Ajanı ─────────────────────────────────────────────────────
        if "kodlama ajanı:" in t or "kod ajanı:" in t:
            task = text.replace("kodlama ajanı:","").replace("kod ajanı:","").strip()
            lang = "python"
            for l in ["python","javascript","java","c++"]:
                if l in t: lang = l; break
            if task:
                def _c():
                    result = self.orchestrator.agents["kodlama"].run(task, lang)
                    self.msg("ANKA", f"💻 Kod:\n{result}")
                    self.speak("Kod hazırlandı efendim.")
                threading.Thread(target=_c, daemon=True).start()
            return True

        # ── Kodu Çalıştır ─────────────────────────────────────────────────────
        if "kodu çalıştır:" in t:
            code = text.replace("kodu çalıştır:","").strip()
            if code:
                result = self.orchestrator.agents["kodlama"].execute_safe(code)
                self.msg("ANKA", f"💻 Çıktı:\n{result}")
            return True

        # ── Planlayıcı Ajanı ──────────────────────────────────────────────────
        if "planlayıcı ajanı:" in t or "proje ajanı:" in t:
            project = text.replace("planlayıcı ajanı:","").replace("proje ajanı:","").strip()
            if project:
                def _p():
                    result = self.orchestrator.agents["planlayıcı"].run(project)
                    self.msg("ANKA", f"📅 Plan:\n{result}")
                    pyperclip.copy(result)
                    self.speak("Plan hazırlandı efendim.")
                threading.Thread(target=_p, daemon=True).start()
            return True

        # ── Analiz Ajanı ──────────────────────────────────────────────────────
        if "analiz ajanı:" in t:
            parts = text.replace("analiz ajanı:","").strip().split("|")
            data = parts[0].strip()
            question = parts[1].strip() if len(parts) > 1 else "Genel analiz yap"
            def _a():
                result = self.orchestrator.agents["analiz"].run(data, question)
                self.msg("ANKA", f"📊 Analiz:\n{result}")
            threading.Thread(target=_a, daemon=True).start()
            return True

        # ── Ajan Durumu ───────────────────────────────────────────────────────
        if "ajan durumu" in t or "ajanlar" in t:
            status = self.orchestrator.get_status()
            r = (f"🤖 Otonom Ajan Sistemi:\n"
                 f"• Aktif Görevler: {status['active']}\n"
                 f"• Tamamlanan: {status['completed']}\n"
                 f"• Uzman Ajanlar: {', '.join(status['agents'])}")
            self.msg("ANKA", r); self.speak(r)
            return True

        # ── Ajan Geçmişi ──────────────────────────────────────────────────────
        if "ajan geçmişi" in t or "tamamlanan görevler" in t:
            history = self.orchestrator.get_history(5)
            if history:
                r = "📋 Son Görevler:\n"
                r += "\n".join(f"• {h['goal'][:40]} ({h['date'][:10]})" for h in history)
            else:
                r = "Henüz tamamlanan görev yok efendim."
            self.msg("ANKA", r); self.speak(r)
            return True

        # ── Hafıza İstatistikleri ─────────────────────────────────────────────
        if "hafıza istatistik" in t or "anka ne öğrendi" in t:
            stats = self.learning.get_stats()
            r = (f"🧠 Anka Öğrenme İstatistikleri:\n"
                 f"• Öğrenilen Gerçekler: {stats['facts']}\n"
                 f"• Komut Kalıpları: {stats['patterns']}\n"
                 f"• Düzeltmeler: {stats['corrections']}\n"
                 f"• Son Güncelleme: {stats['last_updated'][:16] if stats['last_updated'] != 'hiç' else 'henüz yok'}")
            self.msg("ANKA", r); self.speak(r)
            return True

        # ── Düzeltme Bildirimi ────────────────────────────────────────────────
        if "bunu öğren:" in t or "düzelt:" in t:
            correction = text.replace("bunu öğren:","").replace("düzelt:","").strip()
            if correction:
                self.learning.observe("correction", correction)
                r = f"✓ Öğrendim: {correction}"
                self.msg("ANKA", r); self.speak(r)
            return True

        # ── Tercih Kaydet ─────────────────────────────────────────────────────
        if "tercihim:" in t:
            parts = text.replace("tercihim:","").strip().split("=")
            if len(parts) == 2:
                self.learning.observe("preference", (parts[0].strip(), parts[1].strip()))
                r = f"✓ Tercih kaydedildi: {parts[0]} = {parts[1]}"
                self.msg("ANKA", r); self.speak(r)
            return True

        # ── Yardım ───────────────────────────────────────────────────────────
        if "otonom yardım" in t or "ajan yardım" in t:
            r = (
                "🤖 OTONOM AJAN SİSTEMİ\n"
                "═══════════════════════\n\n"
                "🎯 OTONOM GÖREVLER:\n"
                "• 'otonom: [hedef]' → Ajan otomatik çalışır\n"
                "• 'araştırma ajanı: [konu]' → Derin araştırma\n"
                "• 'yazar ajanı: [görev]' → İçerik üret\n"
                "• 'kodlama ajanı: [görev]' → Kod yaz\n"
                "• 'planlayıcı ajanı: [proje]' → Plan oluştur\n"
                "• 'analiz ajanı: [veri]|[soru]' → Analiz\n"
                "• 'kodu çalıştır: [kod]' → Güvenli çalıştır\n\n"
                "🧠 ÖĞRENME:\n"
                "• 'bunu öğren: [bilgi]' → Anka öğrenir\n"
                "• 'düzelt: [düzeltme]' → Hata düzelt\n"
                "• 'tercihim: [key]=[value]' → Tercih kaydet\n"
                "• 'hafıza istatistik' → Ne öğrendiğini gör\n\n"
                "📊 DURUM:\n"
                "• 'ajan durumu' → Sistem durumu\n"
                "• 'ajan geçmişi' → Tamamlanan görevler"
            )
            self.msg("ANKA", r)
            self.speak("Otonom ajan rehberi hazırlandı efendim.")
            return True

        return False


# ═══════════════════════════════════════════════════════════════════════════════
# ── GELİŞMİŞ OTONOM AJAN EKLENTİLERİ ────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

class MultiStepAgent:
    """
    Çok adımlı görevleri zincir halinde çalıştıran ajan.
    Her adımın çıktısı bir sonraki adımın girdisi olur.
    """
    def __init__(self, ollama, speak_func, msg_func):
        self.ollama = ollama
        self.speak = speak_func
        self.msg = msg_func
        self.pipeline = []

    def add_step(self, agent_type, task_template):
        self.pipeline.append({"type": agent_type, "task": task_template})

    def run(self, initial_input):
        result = initial_input
        results_chain = []
        for i, step in enumerate(self.pipeline, 1):
            self.msg("ANKA", f"🔗 Zincir Adım {i}/{len(self.pipeline)}: {step['type']}")
            task = step["task"].replace("{input}", result[:500])
            result = self.ollama.chat(task,
                system_override=f"Sen bir {step['type']} uzmanısın. Verilen görevi yap.")
            results_chain.append(result)
            time.sleep(0.5)
        return results_chain


class AdaptiveAgent:
    """
    Kullanıcının geri bildirimlerine göre kendini adapte eden ajan.
    Başarısız yaklaşımları öğrenip farklı yöntemler dener.
    """
    def __init__(self, ollama, speak_func, msg_func):
        self.ollama = ollama
        self.speak = speak_func
        self.msg = msg_func
        self.attempts = {}
        self.success_rate = {}

    def try_approaches(self, goal, max_attempts=3):
        approaches = [
            f"'{goal}' için doğrudan ve pratik çözüm ver.",
            f"'{goal}' için adım adım yaklaşım ile çöz.",
            f"'{goal}' için alternatif yöntem ile çöz.",
        ]
        results = []
        for i, approach in enumerate(approaches[:max_attempts], 1):
            self.msg("ANKA", f"🔄 Yaklaşım {i}/{max_attempts} deneniyor...")
            result = self.ollama.chat(approach,
                system_override="Yaratıcı problem çözücü. Farklı açıdan bak.")
            results.append(result)
            if len(result) > 100:
                break
        return results[-1] if results else "Çözüm bulunamadı."


class GoalTracker:
    """Uzun vadeli hedefleri takip eden sistem"""
    def __init__(self, speak_func, msg_func):
        self.speak = speak_func
        self.msg = msg_func
        self.goals_file = os.path.join(BASE_DIR, "anka_longterm_goals.json")
        self.goals = _load(self.goals_file, [])
        self.running = True
        threading.Thread(target=self._daily_check, daemon=True).start()

    def add_goal(self, title, description, deadline=None, milestones=None):
        goal = {
            "id": len(self.goals) + 1,
            "title": title,
            "description": description,
            "deadline": deadline,
            "milestones": milestones or [],
            "progress": 0,
            "created": datetime.date.today().isoformat(),
            "status": "active",
            "daily_log": []
        }
        self.goals.append(goal)
        _save(self.goals_file, self.goals)
        return goal["id"]

    def update_progress(self, goal_id, progress, note=""):
        for goal in self.goals:
            if goal["id"] == goal_id:
                goal["progress"] = min(100, max(0, progress))
                goal["daily_log"].append({
                    "date": datetime.date.today().isoformat(),
                    "progress": progress,
                    "note": note
                })
                if progress >= 100:
                    goal["status"] = "completed"
                _save(self.goals_file, self.goals)
                return True
        return False

    def get_active_goals(self):
        return [g for g in self.goals if g["status"] == "active"]

    def get_summary(self):
        active = self.get_active_goals()
        if not active:
            return "Aktif uzun vadeli hedef yok efendim."
        r = f"🎯 Uzun Vadeli Hedefler ({len(active)} aktif):\n"
        for g in active:
            bar = "█" * (g["progress"]//10) + "░" * (10 - g["progress"]//10)
            r += f"\n• {g['title']}\n  [{bar}] %{g['progress']}"
            if g.get("deadline"):
                try:
                    deadline = datetime.date.fromisoformat(g["deadline"])
                    days = (deadline - datetime.date.today()).days
                    r += f" | {days} gün kaldı"
                except: pass
        return r

    def _daily_check(self):
        time.sleep(3600)
        while self.running:
            try:
                active = self.get_active_goals()
                for goal in active:
                    if goal.get("deadline"):
                        try:
                            deadline = datetime.date.fromisoformat(goal["deadline"])
                            days = (deadline - datetime.date.today()).days
                            if days in [7, 3, 1]:
                                self.msg("ANKA",
                                    f"⏰ Hedef Hatırlatıcısı: '{goal['title']}' - {days} gün kaldı!")
                        except: pass
            except: pass
            time.sleep(86400)

    def stop(self): self.running = False


class TaskDecomposer:
    """Karmaşık görevleri otomatik olarak küçük parçalara böler"""
    def __init__(self, ollama):
        self.ollama = ollama

    def decompose(self, complex_task):
        result = self.ollama.chat(
            f"'{complex_task}' görevini en küçük yapılabilir adımlara böl.\n"
            f"Her adım 5-10 dakikada yapılabilmeli.\n"
            f"Format: JSON [{{'step':int,'task':str,'duration_min':int,'depends_on':int}}]",
            system_override="Görev decomposer. Karmaşık görevi mikro görevlere böl.")
        try:
            clean = result.replace("```json","").replace("```","").strip()
            return json.loads(clean)
        except:
            lines = [l.strip() for l in result.split('\n') if l.strip() and len(l) > 5]
            return [{"step": i+1, "task": l, "duration_min": 10, "depends_on": i}
                   for i, l in enumerate(lines[:8])]

    def estimate_time(self, tasks):
        total = sum(t.get("duration_min", 10) for t in tasks)
        return total

