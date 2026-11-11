# ── ANKA v300 — Yapay Genel Zeka Seviyesi ────────────────────────────────────
# Otonom planlama, meta-öğrenme, çoklu modal analiz, gerçek zamanlı adaptasyon
try:
    import pyperclip
except ImportError:
    class _PyClip:
        def copy(self,x):pass
        def paste(self):return ""
    pyperclip=_PyClip()
import json, os, time, threading, datetime, re, math, random, hashlib
import requests, psutil, subprocess, webbrowser, socket
from anka_config import BASE_DIR, USER_NAME

V300_FILE = os.path.join(BASE_DIR, "anka_v300.json")

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
# 1. OTONOM HEDEF PLANLAYICI — Kendisi plan yapar ve uygular
# ═══════════════════════════════════════════════════════════════════════════════
class AutonomousPlanner:
    """
    Verilen hedefi analiz eder, alt görevlere böler,
    önceliklendirir ve otomatik çalıştırır.
    """
    def __init__(self, ollama, speak_func, msg_func):
        self.ollama  = ollama
        self.speak   = speak_func
        self.msg     = msg_func
        self.plan_file = os.path.join(BASE_DIR, "anka_plans.json")
        self.data = _load(self.plan_file, {"active": [], "completed": [], "failed": []})

    def create_plan(self, goal, deadline=None, constraints=None):
        def _plan():
            self.msg("ANKA", f"🧠 Hedef analiz ediliyor: {goal}")
            # 1. Hedefi parçala
            decompose = self.ollama.chat(
                f"Hedef: '{goal}'\nKısıtlar: {constraints or 'yok'}\n"
                f"Bu hedefi 5-7 somut, ölçülebilir alt göreve böl.\n"
                f"Her görev için: süre tahmini, öncelik (1-10), bağımlılık.\n"
                f"JSON: [{{'task':str,'duration_min':int,'priority':int,'depends_on':int,'category':str}}]",
                system_override="Otonom planlayıcı. Sadece JSON döndür.")
            try:
                clean = decompose.replace("```json","").replace("```","").strip()
                tasks = json.loads(clean)
            except:
                tasks = [{"task": goal, "duration_min": 30, "priority": 5,
                         "depends_on": 0, "category": "genel"}]

            # 2. Risk analizi
            risks = self.ollama.chat(
                f"Hedef: {goal}, Görevler: {len(tasks)}\n"
                f"3 ana risk ve her biri için risk azaltma stratejisi.",
                system_override="Risk analisti. Kısa ve pratik.")

            plan = {
                "id": len(self.data["active"]) + len(self.data["completed"]) + 1,
                "goal": goal, "tasks": tasks,
                "risks": risks, "deadline": deadline,
                "created": datetime.datetime.now().isoformat(),
                "status": "active", "progress": 0,
                "completed_tasks": []
            }
            self.data["active"].append(plan)
            _save(self.plan_file, self.data)

            # 3. Görsel plan
            r = (f"📋 OTONOM PLAN #{plan['id']}\n{'═'*40}\n"
                 f"🎯 Hedef: {goal}\n"
                 f"{'📅 Son Tarih: ' + deadline if deadline else ''}\n"
                 f"{'─'*40}\n📌 Görevler:\n")
            for i, t in enumerate(tasks, 1):
                priority_bar = "🔴" if t['priority']>=8 else "🟡" if t['priority']>=5 else "🟢"
                r += f"{priority_bar} {i}. {t['task']} ({t['duration_min']}dk)\n"
            total_min = sum(t.get('duration_min',0) for t in tasks)
            r += (f"\n{'─'*40}\n"
                  f"⏱️ Tahmini Süre: {total_min} dakika\n"
                  f"⚠️ Riskler:\n{risks[:200]}\n")
            self.msg("ANKA", r)
            pyperclip.copy(r)
            self.speak(f"Plan hazır! {len(tasks)} görev, {total_min} dakika efendim.")
        threading.Thread(target=_plan, daemon=True).start()

    def execute_next_task(self, plan_id):
        plan = next((p for p in self.data["active"] if p["id"] == plan_id), None)
        if not plan:
            self.msg("ANKA", f"Plan #{plan_id} bulunamadı efendim."); return
        completed = len(plan["completed_tasks"])
        if completed >= len(plan["tasks"]):
            plan["status"] = "completed"
            self.data["completed"].append(plan)
            self.data["active"].remove(plan)
            _save(self.plan_file, self.data)
            self.msg("ANKA", f"🎉 Plan #{plan_id} tamamlandı efendim!"); return
        next_task = plan["tasks"][completed]
        plan["completed_tasks"].append(next_task)
        plan["progress"] = int(len(plan["completed_tasks"]) / len(plan["tasks"]) * 100)
        _save(self.plan_file, self.data)
        if plan["progress"] == 100:
            next_info = "🎉 Plan Tamamlandı!"
        elif completed < len(plan["tasks"]) - 1:
            next_info = f"Sıradaki: {plan['tasks'][completed].get('task','?')}"
        else:
            next_info = ""
        r = (f"✅ Görev Tamamlandı: {next_task['task']}\n"
             f"📊 İlerleme: %{plan['progress']}\n"
             f"{next_info}")
        self.msg("ANKA", r); self.speak(r[:150])

    def list_plans(self):
        if not self.data["active"]:
            r = "Aktif plan yok efendim."
        else:
            r = f"📋 Aktif Planlar ({len(self.data['active'])}):\n"
            for p in self.data["active"]:
                bar = "█"*(p["progress"]//10) + "░"*(10-p["progress"]//10)
                r += f"#{p['id']} [{bar}] %{p['progress']} — {p['goal'][:40]}\n"
        self.msg("ANKA", r)


# ═══════════════════════════════════════════════════════════════════════════════
# 2. META-ÖĞRENME — Anka kendi öğrenme stratejisini öğrenir
# ═══════════════════════════════════════════════════════════════════════════════
class MetaLearner:
    """Nasıl öğrenileceğini öğrenen sistem"""
    def __init__(self, ollama, speak_func, msg_func):
        self.ollama  = ollama
        self.speak   = speak_func
        self.msg     = msg_func
        self.meta_file = os.path.join(BASE_DIR, "anka_meta.json")
        self.data = _load(self.meta_file, {
            "learning_styles": {},
            "effective_strategies": [],
            "topic_difficulty": {},
            "spaced_repetition": {},
            "performance_log": []
        })

    def analyze_learning_style(self, topic, method, success):
        """Hangi öğrenme yöntemi daha etkili?"""
        key = f"{topic}_{method}"
        if key not in self.data["learning_styles"]:
            self.data["learning_styles"][key] = {"success": 0, "total": 0}
        self.data["learning_styles"][key]["total"] += 1
        if success:
            self.data["learning_styles"][key]["success"] += 1
        _save(self.meta_file, self.data)

    def spaced_repetition_schedule(self, topic, last_studied=None):
        """Aralıklı tekrar programı"""
        intervals = [1, 3, 7, 14, 30, 90]  # Günler
        sr_data = self.data["spaced_repetition"].get(topic, {"level": 0, "last": None})
        level = sr_data.get("level", 0)
        next_review = intervals[min(level, len(intervals)-1)]
        if last_studied:
            sr_data["last"] = last_studied
            sr_data["level"] = min(level + 1, len(intervals)-1)
            self.data["spaced_repetition"][topic] = sr_data
            _save(self.meta_file, self.data)
        today = datetime.date.today()
        next_date = today + datetime.timedelta(days=next_review)
        r = (f"📅 Aralıklı Tekrar — {topic}:\n"
             f"• Seviye: {level}/{len(intervals)-1}\n"
             f"• Sonraki Tekrar: {next_date.isoformat()} ({next_review} gün sonra)\n"
             f"• Öneri: {['Hemen tekrar et','Yarın tekrar et','Bu hafta tekrar et',
                        '2 haftaya tekrar et','Ay sonuna tekrar et','3 aya tekrar et'][min(level,5)]}")
        self.msg("ANKA", r)
        return next_date

    def generate_study_plan(self, topics, hours_per_day=2, days=7):
        def _gen():
            topics_str = ", ".join(topics)
            r = self.ollama.chat(
                f"Konular: {topics_str}\n"
                f"Günlük: {hours_per_day} saat, {days} gün\n"
                f"Meta-öğrenme prensiplerine göre optimal çalışma planı yap.\n"
                f"Aralıklı tekrar, aktif hatırlama, interleaving tekniklerini kullan.",
                system_override="Meta-öğrenme uzmanı. Bilimsel tabanlı plan yap.")
            self.msg("ANKA", f"📚 Meta-Öğrenme Planı:\n{r}")
            pyperclip.copy(r)
            self.speak("Meta-öğrenme planı hazırlandı efendim.")
        threading.Thread(target=_gen, daemon=True).start()

    def feynman_technique(self, topic):
        """Feynman tekniği ile öğrenme"""
        def _feynman():
            r = self.ollama.chat(
                f"'{topic}' konusunu Feynman tekniğiyle öğret:\n"
                f"1. Konuyu 5 yaşında bir çocuğa açıkla\n"
                f"2. Anlaşılmayan yerleri tespit et\n"
                f"3. Basit analojilerle açıkla\n"
                f"4. En basit haliyle özetle",
                system_override="Feynman tekniği uzmanı. Basitten karmaşığa öğret.")
            self.msg("ANKA", f"🧪 Feynman Tekniği — {topic}:\n{r}")
            self.speak(f"{topic} Feynman tekniğiyle açıklandı efendim.")
        threading.Thread(target=_feynman, daemon=True).start()

    def pomodoro_ai(self, task, sessions=4):
        """AI destekli Pomodoro"""
        def _pom():
            r = self.ollama.chat(
                f"Görev: {task}, {sessions} Pomodoro (25dk çalış, 5dk mola)\n"
                f"Her Pomodoro için:\n"
                f"- Net alt hedef\n- Dikkat dağıtıcı riskler\n- Motivasyon ipucu",
                system_override="Pomodoro koçu. Her seans için özel rehberlik.")
            self.msg("ANKA", f"⏱️ AI Pomodoro Planı:\n{r}")
            self.speak(f"{sessions} Pomodoro planı hazır efendim.")
        threading.Thread(target=_pom, daemon=True).start()


# ═══════════════════════════════════════════════════════════════════════════════
# 3. GERÇEK ZAMANLI ADAPTASYON — Kullanıcıya göre kendini ayarlar
# ═══════════════════════════════════════════════════════════════════════════════
class RealTimeAdapter:
    """Kullanıcının anlık durumuna göre Anka'yı adapte eder"""
    def __init__(self, ollama, speak_func, msg_func):
        self.ollama  = ollama
        self.speak   = speak_func
        self.msg     = msg_func
        self.adapt_file = os.path.join(BASE_DIR, "anka_adapt.json")
        self.data = _load(self.adapt_file, {
            "user_state": "normal",
            "response_style": "balanced",
            "energy_level": 5,
            "focus_mode": False,
            "context_stack": []
        })
        self.running = True
        threading.Thread(target=self._adaptive_loop, daemon=True).start()

    def detect_user_state(self, text, response_time=0):
        """Kullanıcının anlık durumunu tespit et"""
        t = text.lower()
        state = "normal"
        # Stres belirtileri
        stress_words = ["acil","hemen","çabuk","bekliyor","teslim","son tarih","bitti","panik"]
        if any(w in t for w in stress_words):
            state = "stressed"
        # Odaksızlık
        elif len(t) < 5 or t in ["e","hm","tamam","ok","neyse"]:
            state = "distracted"
        # Öğrenme modu
        elif any(w in t for w in ["nasıl","neden","açıkla","öğret","anlat"]):
            state = "learning"
        # Verimli mod
        elif any(w in t for w in ["plan","görev","tamamla","bitir","yap"]):
            state = "productive"
        self.data["user_state"] = state
        _save(self.adapt_file, self.data)
        return state

    def adapt_response(self, response, state):
        """Cevabı kullanıcı durumuna göre adapte et"""
        if state == "stressed":
            # Kısa, net, aksiyon odaklı
            lines = response.split('\n')
            short = '\n'.join(lines[:5])
            return f"⚡ {short}\n\n💡 İpucu: Derin nefes alın, adım adım ilerleyin efendim."
        elif state == "learning":
            return response + "\n\n📚 Daha fazlası için: 'feynman tekniği [konu]' yazın efendim."
        elif state == "distracted":
            return response.split('.')[0] + " efendim."  # Sadece ilk cümle
        elif state == "productive":
            return response + "\n\n✅ Tamamladığınızda 'görev bitti' yazın efendim."
        return response

    def set_focus_mode(self, enabled):
        self.data["focus_mode"] = enabled
        _save(self.adapt_file, self.data)
        if enabled:
            r = "🎯 ODAK MODU AKTİF\n• Bildirimler azaltıldı\n• Cevaplar kısa ve net\n• Distraksiyon koruması aktif"
        else:
            r = "✓ Normal moda dönüldü efendim."
        self.msg("ANKA", r); self.speak(r)

    def context_push(self, context):
        """Bağlam yığınına ekle"""
        self.data["context_stack"].append({
            "context": context,
            "time": datetime.datetime.now().isoformat()
        })
        if len(self.data["context_stack"]) > 10:
            self.data["context_stack"] = self.data["context_stack"][-10:]
        _save(self.adapt_file, self.data)

    def _adaptive_loop(self):
        """Sürekli adaptasyon döngüsü"""
        time.sleep(300)
        while self.running:
            try:
                hour = datetime.datetime.now().hour
                # Saate göre otomatik mod
                if 22 <= hour or hour < 6:
                    if self.data.get("response_style") != "quiet":
                        self.data["response_style"] = "quiet"
                        _save(self.adapt_file, self.data)
                elif 9 <= hour <= 17:
                    if self.data.get("response_style") != "productive":
                        self.data["response_style"] = "productive"
                        _save(self.adapt_file, self.data)
            except: pass
            time.sleep(3600)

    def stop(self): self.running = False


# ═══════════════════════════════════════════════════════════════════════════════
# 4. ÇOKLU MODAL ZEKA — Metin + Ses + Görüntü analizi
# ═══════════════════════════════════════════════════════════════════════════════
class MultiModalIntelligence:
    """Farklı veri tiplerini analiz eden zeka"""
    def __init__(self, ollama, speak_func, msg_func):
        self.ollama  = ollama
        self.speak   = speak_func
        self.msg     = msg_func

    def analyze_clipboard_content(self):
        """Panodaki içeriği analiz et"""
        def _analyze():
            try:
                content = pyperclip.paste()
                if not content or len(content) < 5:
                    self.msg("ANKA","Pano boş efendim."); return
                # İçerik türü tespiti
                if content.startswith("http"):
                    content_type = "URL"
                elif re.search(r'\d{4}-\d{2}-\d{2}', content):
                    content_type = "Tarihli metin"
                elif re.search(r'def |class |import |function', content):
                    content_type = "Kod"
                elif len(content) > 500:
                    content_type = "Uzun metin"
                else:
                    content_type = "Kısa metin"

                analysis = self.ollama.chat(
                    f"İçerik türü: {content_type}\nİçerik:\n{content[:800]}\n\n"
                    f"Bu içeriği analiz et: ana fikir, kalite, öneriler.",
                    system_override="İçerik analisti. Kapsamlı analiz yap.")
                self.msg("ANKA",
                    f"📋 Pano Analizi ({content_type}):\n"
                    f"Uzunluk: {len(content)} karakter\n\n{analysis}")
                self.speak("Pano analizi tamamlandı efendim.")
            except Exception as e:
                self.msg("ANKA", f"Analiz hatası: {e}")
        threading.Thread(target=_analyze, daemon=True).start()

    def analyze_url(self, url):
        """URL içeriğini analiz et"""
        def _url():
            try:
                r = requests.get(url, timeout=8, headers={"User-Agent":"AnkaBot/3.0"})
                # Basit HTML temizleme
                text = re.sub(r'<[^>]+>', ' ', r.text)
                text = re.sub(r'\s+', ' ', text).strip()[:2000]
                analysis = self.ollama.chat(
                    f"URL: {url}\nİçerik:\n{text[:1500]}\n\n"
                    f"Bu sayfayı analiz et: konu, güvenilirlik, ana mesaj, özet.",
                    system_override="Web içerik analisti. Kapsamlı değerlendir.")
                self.msg("ANKA", f"🌐 URL Analizi:\n{analysis}")
                pyperclip.copy(analysis)
                self.speak("URL analizi tamamlandı efendim.")
            except Exception as e:
                self.msg("ANKA", f"URL analizi hatası: {e}")
        threading.Thread(target=_url, daemon=True).start()

    def compare_texts(self, text1, text2):
        """İki metni karşılaştır"""
        def _compare():
            r = self.ollama.chat(
                f"Metin 1:\n{text1[:500]}\n\nMetin 2:\n{text2[:500]}\n\n"
                f"Bu iki metni karşılaştır: benzerlikler, farklar, hangi daha iyi ve neden.",
                system_override="Metin karşılaştırma uzmanı. Detaylı analiz yap.")
            self.msg("ANKA", f"⚖️ Metin Karşılaştırması:\n{r}")
            pyperclip.copy(r)
        threading.Thread(target=_compare, daemon=True).start()

    def sentiment_deep(self, text):
        """Derin duygu analizi"""
        def _sentiment():
            r = self.ollama.chat(
                f"Bu metni derin duygu analizi yap:\n{text}\n\n"
                f"Tespit et: temel duygu, yoğunluk (0-100), gizli duygular, "
                f"beden dili ipuçları, iletişim tarzı, önerilen cevap yaklaşımı.",
                system_override="Duygu analizi uzmanı. Psikolojik derinlikte analiz yap.")
            self.msg("ANKA", f"💭 Derin Duygu Analizi:\n{r}")
        threading.Thread(target=_sentiment, daemon=True).start()

    def generate_mindmap_advanced(self, topic):
        """Gelişmiş zihin haritası"""
        def _mind():
            r = self.ollama.chat(
                f"'{topic}' için 3 seviyeli zihin haritası:\n"
                f"Merkez → 5 ana dal → Her dala 3 alt dal\n"
                f"JSON: {{'center':str,'branches':[{{'title':str,'color':str,'sub':[str]}}]}}",
                system_override="Zihin haritası uzmanı. JSON döndür.")
            try:
                clean = r.replace("```json","").replace("```","").strip()
                data = json.loads(clean)
                # HTML olarak oluştur
                html = self._build_mindmap_html(data, topic)
                path = os.path.join(os.path.expanduser("~"), "Desktop",
                                   f"anka_mindmap_{topic[:10]}.html")
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(html)
                webbrowser.open(path)
                self.msg("ANKA", f"🗺️ '{topic}' zihin haritası açıldı efendim!")
                self.speak("Zihin haritası hazırlandı efendim.")
            except:
                self.msg("ANKA", f"🗺️ Zihin Haritası:\n{r}")
        threading.Thread(target=_mind, daemon=True).start()

    def _build_mindmap_html(self, data, topic):
        branches = data.get("branches", [])
        center = data.get("center", topic)
        html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Anka MindMap — {center}</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#030308;font-family:Arial;min-height:100vh;padding:30px}}
h1{{color:#00ffff;text-align:center;margin-bottom:20px;font-size:24px}}
.center{{background:linear-gradient(135deg,#00ffff,#0099cc);color:#030308;
  padding:15px 30px;border-radius:25px;font-size:20px;font-weight:bold;
  text-align:center;margin:0 auto 30px;width:fit-content;display:block;
  box-shadow:0 0 30px #00ffff55}}
.branches{{display:flex;flex-wrap:wrap;gap:20px;justify-content:center}}
.branch{{background:#0d0d20;border-radius:15px;padding:15px;min-width:200px;
  max-width:260px;border-top:4px solid var(--color)}}
.branch h3{{color:var(--color);margin-bottom:10px;font-size:15px}}
.sub{{background:#07070f;border-radius:8px;padding:6px 10px;margin:4px 0;
  font-size:12px;color:#a0d0ff;border-left:3px solid var(--color)}}
</style></head><body>
<h1>🗺️ Anka Zihin Haritası</h1>
<span class="center">🎯 {center}</span>
<div class="branches">"""
        colors = ["#00ffff","#ff6b6b","#ffd93d","#6bcb77","#4d96ff","#ff922b"]
        for i, branch in enumerate(branches):
            color = branch.get("color", colors[i % len(colors)])
            html += f'<div class="branch" style="--color:{color}"><h3>📌 {branch.get("title","")}</h3>'
            for sub in branch.get("sub", []):
                html += f'<div class="sub">• {sub}</div>'
            html += '</div>'
        html += "</div></body></html>"
        return html


# ═══════════════════════════════════════════════════════════════════════════════
# 5. ETİK AI DANIŞMANI — Ahlaki sorular için rehberlik
# ═══════════════════════════════════════════════════════════════════════════════
class EthicsAdvisor:
    """Etik ve ahlaki kararlar için çok boyutlu analiz"""
    def __init__(self, ollama, speak_func, msg_func):
        self.ollama  = ollama
        self.speak   = speak_func
        self.msg     = msg_func

    def ethical_analysis(self, scenario):
        def _eth():
            frameworks = [
                ("Faydacılık", "En fazla kişiye en fazla fayda sağlayan seçenek"),
                ("Deontoloji", "Evrensel ahlak yasalarına göre doğru olan"),
                ("Erdem Etiği", "Erdemli bir insan ne yapardı"),
                ("Bakım Etiği", "İlişkiler ve sorumluluklar açısından")
            ]
            r = f"⚖️ ETİK ANALİZ\n{'═'*40}\nSenaryo: {scenario}\n\n"
            results = {}

            def analyze(name, desc):
                result = self.ollama.chat(
                    f"Senaryo: {scenario}\nÇerçeve: {name} ({desc})\n"
                    f"Bu etik çerçeveden kısa değerlendirme yap.",
                    system_override=f"{name} etik çerçevesi. Kısa değerlendir.")
                results[name] = result

            threads = [threading.Thread(target=analyze, args=(n,d), daemon=True)
                      for n,d in frameworks]
            for t in threads: t.start()
            for t in threads: t.join(timeout=25)

            for name, _ in frameworks:
                if name in results:
                    r += f"📌 {name}:\n{results[name][:150]}\n\n"

            # Sentez
            synthesis = self.ollama.chat(
                f"Senaryo: {scenario}\n4 etik çerçeve değerlendirmesi yapıldı.\n"
                f"Tarafsız sentez ve en dengeli yaklaşım nedir?",
                system_override="Etik felsefeci. Tarafsız sentez yap.")
            r += f"🏛️ SENTEZ:\n{synthesis}"
            self.msg("ANKA", r)
            pyperclip.copy(r)
            self.speak("Etik analiz tamamlandı efendim.")
        threading.Thread(target=_eth, daemon=True).start()

    def moral_dilemma(self, dilemma):
        def _md():
            r = self.ollama.chat(
                f"Ahlaki ikilem: {dilemma}\n\n"
                f"Analiz et:\n"
                f"1. İkilemi netleştir\n"
                f"2. Paydaşları belirle\n"
                f"3. Her seçeneğin sonuçları\n"
                f"4. Değer çatışmaları\n"
                f"5. Tavsiye edilen yaklaşım",
                system_override="Etik danışman. Sistematik ikilem analizi yap.")
            self.msg("ANKA", f"🤔 Ahlaki İkilem Analizi:\n{r}")
            pyperclip.copy(r)
        threading.Thread(target=_md, daemon=True).start()


# ═══════════════════════════════════════════════════════════════════════════════
# 6. ANKA DÜNYA MODELİ — Gerçek zamanlı dünya bilgisi
# ═══════════════════════════════════════════════════════════════════════════════
class WorldModel:
    """Dünyadaki gelişmeleri takip eden ve modelleyen sistem"""
    def __init__(self, ollama, speak_func, msg_func):
        self.ollama  = ollama
        self.speak   = speak_func
        self.msg     = msg_func

    def global_pulse(self):
        """Dünyanın nabzını tut — haber, döviz, kripto, hava"""
        def _pulse():
            self.msg("ANKA","🌍 Dünya nabzı ölçülüyor...")
            results = {}
            threads = []

            def get_news():
                try:
                    import xml.etree.ElementTree as ET
                    r = requests.get("https://feeds.bbci.co.uk/news/world/rss.xml", timeout=5)
                    root = ET.fromstring(r.content)
                    items = root.findall(".//item")[:3]
                    results["news"] = [i.find("title").text for i in items
                                      if i.find("title") is not None]
                except: results["news"] = []

            def get_rates():
                try:
                    r = requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=5)
                    rates = r.json()["rates"]
                    results["rates"] = {"TRY": rates.get("TRY",0), "EUR": rates.get("EUR",0)}
                except: results["rates"] = {}

            def get_crypto():
                try:
                    r = requests.get("https://api.coinbase.com/v2/prices/BTC-USD/spot", timeout=5)
                    results["btc"] = float(r.json()["data"]["amount"])
                except: results["btc"] = 0

            def get_weather():
                try:
                    r = requests.get("https://wttr.in/Istanbul?format=j1", timeout=5)
                    d = r.json()["current_condition"][0]
                    results["weather"] = f"{d['temp_C']}°C {d['weatherDesc'][0]['value']}"
                except: results["weather"] = "?"

            for fn in [get_news, get_rates, get_crypto, get_weather]:
                t = threading.Thread(target=fn, daemon=True)
                threads.append(t); t.start()
            for t in threads: t.join(timeout=8)

            r = f"🌍 DÜNYA NABZI — {datetime.datetime.now().strftime('%H:%M')}\n{'═'*40}\n"
            if results.get("weather"):
                r += f"🌤️ İstanbul: {results['weather']}\n"
            if results.get("rates"):
                r += f"💱 USD: {results['rates'].get('TRY',0):.2f}₺ | EUR: {results['rates'].get('EUR',0):.4f}\n"
            if results.get("btc"):
                r += f"₿ Bitcoin: ${results['btc']:,.0f}\n"
            if results.get("news"):
                r += f"\n📰 Dünya Gündeми:\n"
                r += "\n".join(f"• {n[:60]}" for n in results["news"])

            # AI yorum
            context = f"Haber: {results.get('news',[])[0] if results.get('news') else 'yok'}"
            comment = self.ollama.chat(
                f"{context}\nBu gündem için 1 cümlelik akıllı yorum.",
                system_override="Dünya analisti. 1 cümle.")
            r += f"\n\n💡 Anka Yorumu: {comment}"
            self.msg("ANKA", r)
            self.speak("Dünya nabzı hazırlandı efendim.")
        threading.Thread(target=_pulse, daemon=True).start()

    def geo_political_brief(self, region):
        def _geo():
            r = self.ollama.chat(
                f"'{region}' bölgesi jeopolitik özet:\n"
                f"• Güncel durum\n• Temel aktörler\n• Riskler\n• Fırsatlar\n• 6 aylık tahmin",
                system_override="Jeopolitik analist. Tarafsız ve analitik.")
            self.msg("ANKA", f"🌏 {region} Jeopolitik Brifing:\n{r}")
            pyperclip.copy(r)
        threading.Thread(target=_geo, daemon=True).start()

    def economic_indicator(self, country="Türkiye"):
        def _eco():
            r = self.ollama.chat(
                f"{country} ekonomik göstergeler analizi:\n"
                f"Enflasyon, faiz, büyüme, işsizlik, döviz trendleri.\n"
                f"Mevcut bilgilere göre değerlendir.",
                system_override="Ekonomist. Gerçekçi ekonomik analiz yap.")
            self.msg("ANKA", f"📊 {country} Ekonomi Analizi:\n{r}")
        threading.Thread(target=_eco, daemon=True).start()


# ═══════════════════════════════════════════════════════════════════════════════
# KOMUT İŞLEYİCİ
# ═══════════════════════════════════════════════════════════════════════════════
class V300CommandProcessor:
    def __init__(self, speak_func, msg_func, ollama):
        self.speak   = speak_func
        self.msg     = msg_func
        self.ollama  = ollama
        self.planner = AutonomousPlanner(ollama, speak_func, msg_func)
        self.meta    = MetaLearner(ollama, speak_func, msg_func)
        self.adapter = RealTimeAdapter(ollama, speak_func, msg_func)
        self.modal   = MultiModalIntelligence(ollama, speak_func, msg_func)
        self.ethics  = EthicsAdvisor(ollama, speak_func, msg_func)
        self.world   = WorldModel(ollama, speak_func, msg_func)

    def process(self, text):
        t = text.lower().strip()

        # ── Otonom Planlayıcı ────────────────────────────────────────────────
        if "plan oluştur:" in t:
            goal = text.replace("plan oluştur:","").strip()
            if goal: self.planner.create_plan(goal); return True
        if "sonraki görevi yap" in t:
            m = re.search(r'#(\d+)', t)
            if m: self.planner.execute_next_task(int(m.group(1))); return True
        if "planlarım" in t or "aktif planlar" in t:
            self.planner.list_plans(); return True

        # ── Meta Öğrenme ─────────────────────────────────────────────────────
        if "aralıklı tekrar" in t:
            topic = t.replace("aralıklı tekrar","").strip()
            if topic: self.meta.spaced_repetition_schedule(topic, datetime.date.today().isoformat()); return True
        if "meta öğrenme planı" in t:
            topics_str = t.replace("meta öğrenme planı","").strip()
            topics = [x.strip() for x in topics_str.split(",") if x.strip()]
            if topics: self.meta.generate_study_plan(topics); return True
        if "feynman" in t:
            topic = t.replace("feynman tekniği","").replace("feynman","").strip()
            if topic: self.meta.feynman_technique(topic); return True
        if "ai pomodoro" in t:
            task = t.replace("ai pomodoro","").strip()
            m = re.search(r'(\d+)', t)
            sessions = int(m.group(1)) if m else 4
            task = re.sub(r'\d+','',task).strip()
            if task: self.meta.pomodoro_ai(task, sessions); return True

        # ── Adaptasyon ───────────────────────────────────────────────────────
        if "odak modu aç" in t:
            self.adapter.set_focus_mode(True); return True
        if "odak modu kapat" in t:
            self.adapter.set_focus_mode(False); return True

        # ── Çoklu Modal ──────────────────────────────────────────────────────
        if "panoyu analiz et" in t or "clipboard analiz" in t:
            self.modal.analyze_clipboard_content(); return True
        if "url analiz" in t:
            url_m = re.search(r'https?://\S+', text)
            if url_m: self.modal.analyze_url(url_m.group(0)); return True
        if "metinleri karşılaştır" in t:
            try:
                content = pyperclip.paste()
                if content:
                    self.msg("ANKA","İkinci metni girin efendim.")
                    return True
            except: pass
            return True
        if "derin duygu analizi" in t:
            content = t.replace("derin duygu analizi","").strip()
            if not content:
                try: content = pyperclip.paste()
                except: pass
            if content: self.modal.sentiment_deep(content); return True
        if "gelişmiş zihin haritası" in t:
            topic = t.replace("gelişmiş zihin haritası","").strip()
            if topic: self.modal.generate_mindmap_advanced(topic); return True

        # ── Etik Danışman ────────────────────────────────────────────────────
        if "etik analiz" in t:
            scenario = t.replace("etik analiz","").strip()
            if scenario: self.ethics.ethical_analysis(scenario); return True
        if "ahlaki ikilem" in t:
            dilemma = t.replace("ahlaki ikilem","").strip()
            if dilemma: self.ethics.moral_dilemma(dilemma); return True

        # ── Dünya Modeli ─────────────────────────────────────────────────────
        if "dünya nabzı" in t or "global pulse" in t:
            self.world.global_pulse(); return True
        if "jeopolitik" in t:
            region = t.replace("jeopolitik","").strip() or "Orta Doğu"
            self.world.geo_political_brief(region); return True
        if "ekonomi analizi" in t:
            country = t.replace("ekonomi analizi","").strip() or "Türkiye"
            self.world.economic_indicator(country); return True

        # ── v300 Yardım ──────────────────────────────────────────────────────
        if "v300 yardım" in t or "v300 komutlar" in t:
            r = (
                "🚀 ANKA v300 KOMUTLARI\n"
                "══════════════════════\n\n"
                "📋 OTONOM PLANLAYICI:\n"
                "• 'plan oluştur: [hedef]'\n"
                "• 'sonraki görevi yap #[id]'\n"
                "• 'planlarım'\n\n"
                "📚 META ÖĞRENME:\n"
                "• 'feynman [konu]'\n"
                "• 'aralıklı tekrar [konu]'\n"
                "• 'meta öğrenme planı [konu1,konu2]'\n"
                "• 'ai pomodoro [görev]'\n\n"
                "🎯 ADAPTASYON:\n"
                "• 'odak modu aç/kapat'\n\n"
                "🔍 ÇOKLU MODAL:\n"
                "• 'panoyu analiz et'\n"
                "• 'url analiz [url]'\n"
                "• 'derin duygu analizi [metin]'\n"
                "• 'gelişmiş zihin haritası [konu]'\n\n"
                "⚖️ ETİK DANIŞMAN:\n"
                "• 'etik analiz [senaryo]'\n"
                "• 'ahlaki ikilem [durum]'\n\n"
                "🌍 DÜNYA MODELİ:\n"
                "• 'dünya nabzı'\n"
                "• 'jeopolitik [bölge]'\n"
                "• 'ekonomi analizi [ülke]'"
            )
            self.msg("ANKA", r)
            self.speak("v300 komut rehberi hazırlandı efendim.")
            return True

        return False
