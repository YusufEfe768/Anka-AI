# ── ANKA ANKA MODÜLü ──────────────────────────────────────────────────
# Female Replacement Intelligent Digital Assistant Youth
# Tony Stark'ın gelişmiş AI sisteminden ilham alınmıştır
try:
    import pyperclip
except ImportError:
    class _PyClip:
        def copy(self,x):pass
        def paste(self):return ""
    pyperclip=_PyClip()
try:
    import pyautogui
except ImportError:
    pyautogui=None
import json, os, time, threading, datetime, subprocess, webbrowser
import requests, re, random, psutil, math
from anka_config import BASE_DIR

FRIDAY_FILE    = os.path.join(BASE_DIR, "anka_friday.json")
TACTICS_FILE   = os.path.join(BASE_DIR, "anka_tactics.json")
ANALYSIS_FILE  = os.path.join(BASE_DIR, "anka_analysis.json")
WORKFLOW_FILE  = os.path.join(BASE_DIR, "anka_workflows.json")

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
# ── ANKA CORE ─────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════
class FRIDAYCore:
    VERSION = "ANKA Taktik v2.0 — Anka Edition"

    def __init__(self, ollama, speak_func, msg_func):
        self.ollama = ollama
        self.speak = speak_func
        self.msg = msg_func
        self.data = _load(FRIDAY_FILE, {
            "boot_count": 0,
            "analyses_done": 0,
            "tactics_generated": 0,
            "workflows_completed": 0
        })
        self.data["boot_count"] += 1
        _save(FRIDAY_FILE, self.data)

    def status(self):
        r = (f"📊 ANKA DURUM\n"
             f"{'═'*30}\n"
             f"• Boot: #{self.data['boot_count']}\n"
             f"• Analizler: {self.data['analyses_done']}\n"
             f"• Taktikler: {self.data['tactics_generated']}\n"
             f"• İş Akışları: {self.data['workflows_completed']}")
        self.msg("ANKA", r); self.speak(r)


# ═══════════════════════════════════════════════════════════════════════════════
# ── TAKTİK ANALİZ SİSTEMİ ────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════
class TacticalAnalyzer:
    """ANKA Taktik'ın taktik analiz ve strateji motoru"""

    def __init__(self, ollama, speak_func, msg_func):
        self.ollama = ollama
        self.speak = speak_func
        self.msg = msg_func

    def situation_assessment(self, situation):
        """Durumu analiz et, taktik değerlendirme yap"""
        def _a():
            r = self.ollama.chat(
                f"Taktik durum değerlendirmesi:\n'{situation}'\n\n"
                f"Şunları analiz et:\n"
                f"1. Mevcut durum özeti\n"
                f"2. Avantajlar ve dezavantajlar\n"
                f"3. Olası riskler\n"
                f"4. Önerilen aksiyonlar (öncelik sırasıyla)\n"
                f"5. Başarı olasılığı (0-100)\n"
                f"Türkçe, net ve kısa yaz.",
                system_override="ANKA Taktik taktik analiz. Askeri/iş taktikleri uygula.")
            self.msg("ANKA", f"🎯 TAKTİK DEĞERLENDİRME\n{'═'*35}\n{r}")
            self.speak("Taktik değerlendirme tamamlandı efendim.")
        threading.Thread(target=_a, daemon=True).start()

    def multi_scenario_analysis(self, situation, scenarios=3):
        """Çoklu senaryo analizi"""
        def _m():
            r = self.ollama.chat(
                f"Durum: '{situation}'\n"
                f"{scenarios} farklı senaryo analiz et:\n"
                f"İyimser, gerçekçi, kötümser senaryolar.\n"
                f"Her senaryo için olasılık ve önerilen aksiyon ver.",
                system_override="ANKA Taktik senaryo analisti. Çoklu senaryo değerlendir.")
            self.msg("ANKA", f"📊 SENARYO ANALİZİ\n{'═'*35}\n{r}")
            self.speak("Senaryo analizi tamamlandı efendim.")
        threading.Thread(target=_m, daemon=True).start()

    def weakness_finder(self, subject):
        """Zayıf nokta analizi"""
        def _w():
            r = self.ollama.chat(
                f"'{subject}' için kapsamlı zayıf nokta analizi:\n"
                f"• Kritik zayıflıklar\n"
                f"• İstismar edilebilir noktalar\n"
                f"• Güçlendirme önerileri\n"
                f"• Öncelik sıralaması",
                system_override="ANKA Taktik güvenlik analisti. Zayıflıkları tespit et.")
            self.msg("ANKA", f"🔍 ZAYIF NOKTA ANALİZİ — {subject}\n{'═'*35}\n{r}")
            self.speak("Zayıf nokta analizi tamamlandı efendim.")
        threading.Thread(target=_w, daemon=True).start()

    def counter_strategy(self, problem):
        """Karşı strateji geliştir"""
        def _c():
            r = self.ollama.chat(
                f"Problem: '{problem}'\n"
                f"Karşı strateji geliştir:\n"
                f"• Ani müdahale planı\n"
                f"• Orta vadeli strateji\n"
                f"• Uzun vadeli çözüm\n"
                f"• Alternatif yaklaşımlar",
                system_override="ANKA Taktik strateji uzmanı. Etkili karşı strateji üret.")
            self.msg("ANKA", f"⚔️ KARŞI STRATEJİ\n{'═'*35}\n{r}")
            self.speak("Karşı strateji hazırlandı efendim.")
        threading.Thread(target=_c, daemon=True).start()

    def decision_matrix(self, options):
        """Karar matrisi analizi"""
        def _d():
            r = self.ollama.chat(
                f"Bu seçenekler için karar matrisi oluştur: {options}\n"
                f"Kriterler: maliyet, zaman, risk, etkinlik, uygulanabilirlik\n"
                f"Her seçeneği puanla ve en iyi seçeneği belirle.",
                system_override="ANKA Taktik karar analisti. Objektif matris oluştur.")
            self.msg("ANKA", f"📊 KARAR MATRİSİ\n{'═'*35}\n{r}")
            self.speak("Karar matrisi hazırlandı efendim.")
        threading.Thread(target=_d, daemon=True).start()


# ═══════════════════════════════════════════════════════════════════════════════
# ── ÇOKLU GÖREV YÖNETİCİSİ ───────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════
class MultiTaskManager:
    """ANKA Taktik'ın paralel görev yönetim sistemi"""

    def __init__(self, ollama, speak_func, msg_func):
        self.ollama = ollama
        self.speak = speak_func
        self.msg = msg_func
        self.tasks = []
        self.running_tasks = {}

    def add_parallel_tasks(self, task_list):
        """Birden fazla görevi paralel başlat"""
        self.msg("ANKA",
            f"⚡ {len(task_list)} görev paralel başlatılıyor...")

        def run_task(task, idx):
            self.msg("ANKA", f"▶️ Görev {idx+1}: {task}")
            result = self.ollama.chat(
                f"Şu görevi tamamla: {task}",
                system_override="ANKA Taktik görev yürütücü. Hızlı ve net çalış.")
            self.msg("ANKA", f"✅ Görev {idx+1} tamamlandı:\n{result[:200]}")
            return result

        threads = []
        for i, task in enumerate(task_list[:5]):
            t = threading.Thread(target=run_task, args=(task, i), daemon=True)
            threads.append(t)
            t.start()

        def wait_all():
            for t in threads:
                t.join(timeout=30)
            self.msg("ANKA",
                f"✅ Tüm {len(task_list)} görev tamamlandı efendim!")
            self.speak("Tüm görevler tamamlandı efendim.")
        threading.Thread(target=wait_all, daemon=True).start()

    def priority_queue(self, tasks_with_priority):
        """Öncelik sırasına göre görev işle"""
        sorted_tasks = sorted(tasks_with_priority,
                             key=lambda x: x.get("priority", 5), reverse=True)
        r = "📋 ÖNCELİK SIRASI:\n"
        for i, task in enumerate(sorted_tasks[:8], 1):
            emoji = "🔴" if task["priority"] >= 8 else "🟡" if task["priority"] >= 5 else "🟢"
            r += f"{emoji} {i}. {task['task']} (Öncelik: {task['priority']}/10)\n"
        self.msg("ANKA", r)
        self.speak("Görev öncelik listesi hazırlandı efendim.")
        return sorted_tasks


# ═══════════════════════════════════════════════════════════════════════════════
# ── GERÇEK ZAMANLI ANALİZ ────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════
class RealTimeAnalyzer:
    """ANKA Taktik'ın gerçek zamanlı veri analiz sistemi"""

    def __init__(self, ollama, speak_func, msg_func):
        self.ollama = ollama
        self.speak = speak_func
        self.msg = msg_func
        self.monitoring = False
        self.monitor_thread = None

    def start_performance_monitor(self, duration=60):
        """Sistem performansını belirli süre izle"""
        self.monitoring = True

        def _monitor():
            start = time.time()
            samples = []
            self.msg("ANKA",
                f"📊 Performans izleme başladı ({duration} saniye)...")

            while time.time() - start < duration and self.monitoring:
                sample = {
                    "time": datetime.datetime.now().strftime("%H:%M:%S"),
                    "cpu": psutil.cpu_percent(interval=1),
                    "ram": psutil.virtual_memory().percent,
                    "disk_io": psutil.disk_io_counters().read_bytes if
                               psutil.disk_io_counters() else 0
                }
                samples.append(sample)
                time.sleep(5)

            if samples:
                avg_cpu = sum(s["cpu"] for s in samples) / len(samples)
                avg_ram = sum(s["ram"] for s in samples) / len(samples)
                max_cpu = max(s["cpu"] for s in samples)
                max_ram = max(s["ram"] for s in samples)

                r = (f"📊 PERFORMANS RAPORU ({duration}s)\n"
                     f"{'═'*35}\n"
                     f"CPU: Ort %{avg_cpu:.1f} | Maks %{max_cpu:.1f}\n"
                     f"RAM: Ort %{avg_ram:.1f} | Maks %{max_ram:.1f}\n"
                     f"Örnek Sayısı: {len(samples)}\n"
                     f"Durum: {'⚠️ Yüksek Yük' if max_cpu > 80 else '✅ Normal'}")
                self.msg("ANKA", r)
                self.speak("Performans izleme tamamlandı efendim.")
            self.monitoring = False

        self.monitor_thread = threading.Thread(target=_monitor, daemon=True)
        self.monitor_thread.start()

    def stop_monitor(self):
        self.monitoring = False
        self.msg("ANKA", "⏹️ İzleme durduruldu efendim.")

    def anomaly_detection(self):
        """Sistem anomalilerini tespit et"""
        def _detect():
            anomalies = []
            cpu = psutil.cpu_percent(interval=2)
            ram = psutil.virtual_memory().percent
            disk = psutil.disk_usage('/').percent

            if cpu > 85: anomalies.append(f"🔴 CPU aşırı yüklü: %{cpu:.0f}")
            if ram > 90: anomalies.append(f"🔴 RAM kritik: %{ram:.0f}")
            if disk > 92: anomalies.append(f"🔴 Disk doluyor: %{disk:.0f}")

            # Ağ anomalisi
            try:
                net1 = psutil.net_io_counters()
                time.sleep(2)
                net2 = psutil.net_io_counters()
                rate = (net2.bytes_sent - net1.bytes_sent) / 2 / 1024
                if rate > 5000:
                    anomalies.append(f"🟡 Yüksek ağ çıkışı: {rate:.0f} KB/s")
            except: pass

            if anomalies:
                r = f"⚠️ ANOMALİ TESPİT EDİLDİ\n{'═'*30}\n" + "\n".join(anomalies)
            else:
                r = "✅ Sistem normal. Anomali tespit edilmedi efendim."
            self.msg("ANKA", r); self.speak(r[:150])
        threading.Thread(target=_detect, daemon=True).start()

    def predictive_analysis(self, metric, current_value, trend):
        """Tahminsel analiz"""
        def _predict():
            r = self.ollama.chat(
                f"Metrik: {metric}, Mevcut: {current_value}, Trend: {trend}\n"
                f"Önümüzdeki 1 saat, 1 gün, 1 hafta için tahmin yap.\n"
                f"Olası sorunlar ve öneriler.",
                system_override="ANKA Taktik veri bilimcisi. Tahminsel analiz yap.")
            self.msg("ANKA", f"🔮 TAHMİNSEL ANALİZ — {metric}\n{r}")
        threading.Thread(target=_predict, daemon=True).start()


# ═══════════════════════════════════════════════════════════════════════════════
# ── OTONOM İŞ AKIŞI ──────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════
class WorkflowEngine:
    """ANKA Taktik'ın otonom iş akışı motoru"""

    def __init__(self, ollama, speak_func, msg_func):
        self.ollama = ollama
        self.speak = speak_func
        self.msg = msg_func
        self.workflows = _load(WORKFLOW_FILE, {})

    def create_workflow(self, name, trigger, steps):
        """Yeni iş akışı oluştur"""
        self.workflows[name.lower()] = {
            "name": name,
            "trigger": trigger,
            "steps": steps,
            "created": datetime.datetime.now().isoformat(),
            "run_count": 0
        }
        _save(WORKFLOW_FILE, self.workflows)
        r = (f"✅ İŞ AKIŞI OLUŞTURULDU\n"
             f"• Ad: {name}\n"
             f"• Tetikleyici: {trigger}\n"
             f"• Adım Sayısı: {len(steps)}")
        self.msg("ANKA", r); self.speak(r)

    def run_workflow(self, name):
        """İş akışını çalıştır"""
        wf = self.workflows.get(name.lower())
        if not wf:
            self.msg("ANKA", f"'{name}' iş akışı bulunamadı efendim.")
            return

        def _run():
            self.msg("ANKA",
                f"▶️ İŞ AKIŞI BAŞLADI: {wf['name']}")
            for i, step in enumerate(wf["steps"], 1):
                self.msg("ANKA", f"⚙️ Adım {i}: {step}")
                time.sleep(0.5)

                # Adımı çalıştır
                if step.startswith("open:"):
                    app = step.replace("open:","").strip()
                    subprocess.Popen(app, shell=True)
                elif step.startswith("url:"):
                    webbrowser.open(step.replace("url:","").strip())
                elif step.startswith("say:"):
                    self.speak(step.replace("say:","").strip())
                elif step.startswith("wait:"):
                    secs = int(step.replace("wait:","").strip())
                    time.sleep(secs)
                elif step.startswith("type:"):
                    text = step.replace("type:","").strip()
                    time.sleep(1)
                    pyautogui.write(text)
                elif step.startswith("key:"):
                    keys = step.replace("key:","").strip().split("+")
                    pyautogui.hotkey(*keys)

            wf["run_count"] += 1
            _save(WORKFLOW_FILE, self.workflows)
            self.msg("ANKA", f"✅ {wf['name']} tamamlandı!")
            self.speak(f"{wf['name']} iş akışı tamamlandı efendim.")
        threading.Thread(target=_run, daemon=True).start()

    def list_workflows(self):
        if not self.workflows:
            return "Kayıtlı iş akışı yok efendim."
        r = f"📋 İŞ AKIŞLARI ({len(self.workflows)})\n{'═'*30}\n"
        for name, wf in self.workflows.items():
            r += f"• {wf['name']} ({len(wf['steps'])} adım, {wf['run_count']}x çalıştı)\n"
        return r

    def ai_workflow_generator(self, goal):
        """AI ile iş akışı oluştur"""
        def _gen():
            r = self.ollama.chat(
                f"'{goal}' için otomasyon iş akışı oluştur.\n"
                f"Adımları şu formatta yaz:\n"
                f"open:[uygulama], url:[adres], say:[metin], wait:[saniye], key:[tuşlar]\n"
                f"Her adım ayrı satırda olsun.",
                system_override="ANKA Taktik otomasyon uzmanı. Pratik iş akışı yaz.")
            self.msg("ANKA",
                f"🤖 AI İŞ AKIŞI ÖNERİSİ — {goal}\n{'═'*35}\n{r}")
            pyperclip.copy(r)
            self.speak("İş akışı önerisi hazırlandı efendim.")
        threading.Thread(target=_gen, daemon=True).start()


# ═══════════════════════════════════════════════════════════════════════════════
# ── FRIDAY İLETİŞİM SİSTEMİ ──────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════
class CommunicationSystem:
    """ANKA Taktik'ın iletişim ve bildirim sistemi"""

    def __init__(self, ollama, speak_func, msg_func):
        self.ollama = ollama
        self.speak = speak_func
        self.msg = msg_func

    def smart_notification(self, message, priority="normal", channels=None):
        """Akıllı çok kanallı bildirim"""
        channels = channels or ["screen"]
        results = []

        for channel in channels:
            if channel == "screen":
                emoji = "🚨" if priority=="high" else "🔔"
                self.msg("ANKA", f"{emoji} {message}")
                results.append("Ekran")

            elif channel == "ntfy":
                try:
                    requests.post("https://ntfy.sh/anka-yusuf-2026",
                        data=message.encode(),
                        headers={"Title":"ANKA Taktik",
                                "Priority":"high" if priority=="high" else "default"},
                        timeout=3)
                    results.append("Telefon")
                except: pass

            elif channel == "voice":
                self.speak(message)
                results.append("Ses")

            elif channel == "popup":
                try:
                    subprocess.run(["powershell","-Command",
                        f'Add-Type -AssemblyName System.Windows.Forms; '
                        f'[System.Windows.Forms.MessageBox]::Show("{message}","ANKA Taktik")'],
                        timeout=5, capture_output=True)
                    results.append("Popup")
                except: pass

        r = f"✅ Bildirim gönderildi: {', '.join(results)}"
        self.msg("ANKA", r)

    def broadcast(self, message):
        """Tüm kanallara yayın yap"""
        self.smart_notification(message, "high", ["screen","ntfy","voice"])

    def auto_reply_generator(self, received_message, context=""):
        """Alınan mesaja otomatik cevap oluştur"""
        def _gen():
            r = self.ollama.chat(
                f"Alınan mesaj: '{received_message}'\n"
                f"Bağlam: {context}\n"
                f"Profesyonel ve uygun bir cevap yaz. Türkçe.",
                system_override="ANKA Taktik iletişim asistanı. Uygun cevap oluştur.")
            self.msg("ANKA", f"💬 OTOMATİK CEVAP:\n{r}")
            pyperclip.copy(r)
            self.speak("Cevap hazırlandı ve panoya kopyalandı efendim.")
        threading.Thread(target=_gen, daemon=True).start()

    def meeting_coordinator(self, participants, topic, duration):
        """Toplantı koordinasyonu"""
        def _coord():
            r = self.ollama.chat(
                f"Toplantı: {topic}\n"
                f"Katılımcılar: {participants}\n"
                f"Süre: {duration} dakika\n"
                f"Gündem, roller, beklenen çıktılar, takip aksiyonları.",
                system_override="ANKA Taktik toplantı koordinatörü. Detaylı plan yap.")
            self.msg("ANKA",
                f"📅 TOPLANTI KOORDİNASYONU\n{'═'*35}\n{r}")
            pyperclip.copy(r)
            self.speak("Toplantı koordinasyonu hazırlandı efendim.")
        threading.Thread(target=_coord, daemon=True).start()


# ═══════════════════════════════════════════════════════════════════════════════
# ── FRIDAY ÖĞRENME SİSTEMİ ───────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════
class FRIDAYLearning:
    """ANKA Taktik'ın adaptif öğrenme sistemi"""

    def __init__(self, ollama, speak_func, msg_func):
        self.ollama = ollama
        self.speak = speak_func
        self.msg = msg_func
        self.learn_file = os.path.join(BASE_DIR, "friday_learning.json")
        self.data = _load(self.learn_file, {
            "patterns": {},
            "user_style": {},
            "success_rates": {},
            "feedback_log": []
        })

    def learn_from_feedback(self, action, was_good):
        """Geri bildirimden öğren"""
        self.data["feedback_log"].append({
            "action": action,
            "good": was_good,
            "date": datetime.datetime.now().isoformat()
        })
        key = action[:30].lower()
        if key not in self.data["success_rates"]:
            self.data["success_rates"][key] = {"good": 0, "bad": 0}
        if was_good:
            self.data["success_rates"][key]["good"] += 1
        else:
            self.data["success_rates"][key]["bad"] += 1
        _save(self.learn_file, self.data)

    def get_improvement_suggestions(self):
        """Gelişim önerileri sun"""
        bad_actions = []
        for action, rates in self.data["success_rates"].items():
            total = rates["good"] + rates["bad"]
            if total > 2 and rates["bad"] / total > 0.5:
                bad_actions.append(action)

        if not bad_actions:
            r = "✅ Tüm alanlarda iyi performans! Gelişim alanı tespit edilmedi."
        else:
            r = f"📈 GELİŞİM ÖNERİLERİ\n{'═'*30}\n"
            r += "Şu alanlarda iyileştirme yapılabilir:\n"
            r += "\n".join(f"• {a}" for a in bad_actions[:5])
        self.msg("ANKA", r); self.speak(r[:200])

    def adapt_response_style(self, preference):
        """Cevap stilini adapte et"""
        self.data["user_style"]["preference"] = preference
        _save(self.learn_file, self.data)
        r = f"✅ Cevap stili güncellendi: {preference}"
        self.msg("ANKA", r); self.speak(r)

    def learning_stats(self):
        total_fb = len(self.data["feedback_log"])
        good = sum(1 for f in self.data["feedback_log"] if f["good"])
        r = (f"📊 ÖĞRENME İSTATİSTİKLERİ\n"
             f"• Toplam Geri Bildirim: {total_fb}\n"
             f"• Başarılı: {good}\n"
             f"• Başarı Oranı: %{(good/total_fb*100) if total_fb else 0:.0f}\n"
             f"• Öğrenilen Kalıplar: {len(self.data['patterns'])}")
        self.msg("ANKA", r); self.speak(r)


# ═══════════════════════════════════════════════════════════════════════════════
# ── FRIDAY KOMUT İŞLEYİCİ ────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════
class FRIDAYCommandProcessor:
    def __init__(self, speak_func, msg_func, ollama):
        self.speak = speak_func
        self.msg = msg_func
        self.ollama = ollama
        self.core = FRIDAYCore(ollama, speak_func, msg_func)
        self.tactics = TacticalAnalyzer(ollama, speak_func, msg_func)
        self.multitask = MultiTaskManager(ollama, speak_func, msg_func)
        self.realtime = RealTimeAnalyzer(ollama, speak_func, msg_func)
        self.workflow = WorkflowEngine(ollama, speak_func, msg_func)
        self.comms = CommunicationSystem(ollama, speak_func, msg_func)
        self.learning = FRIDAYLearning(ollama, speak_func, msg_func)

    def process(self, text):
        t = text.lower().strip()

        # ── FRIDAY Aktivasyon ─────────────────────────────────────────────────


        # ── Taktik Analiz ─────────────────────────────────────────────────────
        if "taktik değerlendir" in t or "durum değerlendir" in t:
            situation = t.replace("taktik değerlendir","").replace("durum değerlendir","").strip()
            if situation: self.tactics.situation_assessment(situation)
            return True

        if "senaryo analizi" in t:
            situation = t.replace("senaryo analizi","").strip()
            if situation: self.tactics.multi_scenario_analysis(situation)
            return True

        if "zayıf nokta" in t or "güvenlik açığı" in t:
            subject = t.replace("zayıf nokta bul","").replace("güvenlik açığı","").strip()
            if subject: self.tactics.weakness_finder(subject)
            return True

        if "karşı strateji" in t:
            problem = t.replace("karşı strateji","").strip()
            if problem: self.tactics.counter_strategy(problem)
            return True

        if "karar matrisi" in t:
            options = t.replace("karar matrisi","").strip()
            if options: self.tactics.decision_matrix(options)
            return True

        # ── Çoklu Görev ───────────────────────────────────────────────────────
        if "paralel görev" in t or "çoklu görev" in t:
            tasks_text = t.replace("paralel görev","").replace("çoklu görev","").strip()
            if tasks_text:
                tasks = [t.strip() for t in tasks_text.split(",") if t.strip()]
                if tasks: self.multitask.add_parallel_tasks(tasks)
            return True

        # ── Gerçek Zamanlı İzleme ─────────────────────────────────────────────
        if "performans izle" in t:
            m = re.search(r'(\d+)', t)
            duration = int(m.group(1)) if m else 60
            self.realtime.start_performance_monitor(duration)
            return True

        if "izlemeyi durdur" in t:
            self.realtime.stop_monitor(); return True

        if "anomali tara" in t or "anomali tespit" in t:
            self.realtime.anomaly_detection(); return True

        if "tahmin analizi" in t:
            parts = t.replace("tahmin analizi","").strip().split(",")
            if len(parts) >= 2:
                self.realtime.predictive_analysis(parts[0], parts[1],
                    parts[2] if len(parts)>2 else "düz")
            return True

        # ── İş Akışı ─────────────────────────────────────────────────────────
        if "iş akışı oluştur" in t:
            name_m = re.search(r"['\"]([^'\"]+)['\"]", text)
            name = name_m.group(1) if name_m else t.replace("iş akışı oluştur","").strip()[:20]
            self.msg("ANKA",
                f"İş akışı adımlarını söyleyin. Format:\n"
                f"open:[uygulama], url:[adres], say:[metin], wait:[saniye], key:[tuşlar]")
            return True

        if "iş akışı çalıştır" in t:
            name = t.replace("iş akışı çalıştır","").strip()
            if name: self.workflow.run_workflow(name)
            return True

        if "iş akışlarım" in t:
            r = self.workflow.list_workflows()
            self.msg("ANKA", r); self.speak(r)
            return True

        if "ai iş akışı" in t:
            goal = t.replace("ai iş akışı","").strip()
            if goal: self.workflow.ai_workflow_generator(goal)
            return True

        # ── İletişim ──────────────────────────────────────────────────────────
        if "yayın yap" in t or "broadcast" in t:
            message = t.replace("yayın yap","").replace("broadcast","").strip()
            if message: self.comms.broadcast(message)
            return True

        if "akıllı bildirim" in t:
            parts = t.replace("akıllı bildirim","").strip().split("|")
            msg = parts[0].strip()
            priority = parts[1].strip() if len(parts)>1 else "normal"
            channels_str = parts[2].strip() if len(parts)>2 else "screen"
            channels = [c.strip() for c in channels_str.split(",")]
            if msg: self.comms.smart_notification(msg, priority, channels)
            return True

        if "otomatik cevap" in t:
            message = t.replace("otomatik cevap","").strip()
            if message: self.comms.auto_reply_generator(message)
            return True

        if "toplantı koordine" in t:
            parts = t.replace("toplantı koordine","").strip().split(",")
            if len(parts) >= 2:
                self.comms.meeting_coordinator(parts[0], parts[1],
                    int(parts[2]) if len(parts)>2 else 60)
            return True

        # ── Öğrenme ───────────────────────────────────────────────────────────
        if "iyi yaptın" in t or "harika" in t and "friday" in t:
            self.learning.learn_from_feedback(t, True)
            r = "Teşekkürler! Öğrendim efendim. 😊"
            self.msg("ANKA", r); self.speak(r)
            return True

        if "kötü yaptın" in t or "yanlış" in t and "friday" in t:
            self.learning.learn_from_feedback(t, False)
            r = "Anlıyorum, bir dahaki sefere daha iyi yapacağım efendim."
            self.msg("ANKA", r); self.speak(r)
            return True

        if "gelişim önerileri" in t or "friday geliş" in t:
            self.learning.get_improvement_suggestions(); return True

        if "öğrenme istatistik" in t:
            self.learning.learning_stats(); return True

        # ── FRIDAY Yardım ─────────────────────────────────────────────────────

        return False
