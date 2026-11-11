# ── ANKA v100 — Gelecek Nesil AI Özellikleri ─────────────────────────────────
# Otonom düşünme, gerçek zamanlı öğrenme, çoklu ajan, sesli asistan pro
try:
    import pyperclip
except ImportError:
    class _PyClip:
        def copy(self,x):pass
        def paste(self):return ""
    pyperclip=_PyClip()
import json, os, time, threading, datetime, subprocess, re, math
import requests, psutil, random, hashlib, socket
from anka_config import BASE_DIR, USER_NAME

V100_FILE = os.path.join(BASE_DIR, "anka_v100.json")

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
# 1. ANKA HAFIZA PALASİ — Sonsuz bağlantılı bilgi ağı
# ═══════════════════════════════════════════════════════════════════════════════
class InfiniteMemory:
    """
    Konuları birbirine bağlayan, hiç unutmayan hafıza sistemi.
    Her bilgi diğer bilgilerle ilişkilendirilir.
    """
    def __init__(self, ollama, speak_func, msg_func):
        self.ollama = ollama
        self.speak  = speak_func
        self.msg    = msg_func
        self.mem_file = os.path.join(BASE_DIR, "anka_infinite_mem.json")
        self.data = _load(self.mem_file, {
            "nodes": {},      # Bilgi düğümleri
            "edges": {},      # Bağlantılar
            "timeline": [],   # Zaman çizelgesi
            "insights": []    # AI içgörüleri
        })

    def remember(self, key, value, tags=None, related=None):
        """Bir şeyi kalıcı olarak hatırla"""
        node = {
            "key": key, "value": value,
            "tags": tags or [],
            "related": related or [],
            "created": datetime.datetime.now().isoformat(),
            "access_count": 0, "importance": 5
        }
        self.data["nodes"][key.lower()] = node
        # Bağlantı ağı oluştur
        if related:
            for rel in related:
                edge_key = f"{key}→{rel}"
                self.data["edges"][edge_key] = {
                    "from": key, "to": rel,
                    "strength": 1.0
                }
        self.data["timeline"].append({
            "action": "remember",
            "key": key,
            "time": datetime.datetime.now().isoformat()
        })
        _save(self.mem_file, self.data)
        r = f"🧠 Hafızaya alındı: '{key}'"
        self.msg("ANKA", r); self.speak(r)

    def recall(self, query):
        """Hafızadan geri çağır"""
        q = query.lower()
        results = []
        for key, node in self.data["nodes"].items():
            score = 0
            if q in key: score += 10
            if any(q in tag for tag in node.get("tags", [])): score += 5
            if q in str(node.get("value","")).lower(): score += 3
            if score > 0:
                results.append((score, node))
        results.sort(key=lambda x: -x[0])
        if not results:
            r = f"'{query}' hafızamda yok efendim."
            self.msg("ANKA", r); return None
        best = results[0][1]
        best["access_count"] += 1
        _save(self.mem_file, self.data)
        related = best.get("related", [])
        r = (f"🧠 Hatırladım: '{best['key']}'\n"
             f"📝 {best['value']}\n"
             f"🔗 İlişkili: {', '.join(related) if related else 'yok'}\n"
             f"👁️ {best['access_count']}. erişim")
        self.msg("ANKA", r)
        return best["value"]

    def find_connections(self, key):
        """Bir konunun tüm bağlantılarını bul"""
        related_nodes = []
        for edge_key, edge in self.data["edges"].items():
            if key.lower() in edge["from"].lower() or key.lower() in edge["to"].lower():
                other = edge["to"] if edge["from"].lower() == key.lower() else edge["from"]
                if other in self.data["nodes"]:
                    related_nodes.append(self.data["nodes"][other])
        if not related_nodes:
            self.msg("ANKA", f"'{key}' için bağlantı bulunamadı efendim.")
            return
        r = f"🕸️ '{key}' Bağlantı Ağı:\n"
        for node in related_nodes[:8]:
            r += f"• {node['key']}: {str(node['value'])[:50]}\n"
        self.msg("ANKA", r)

    def memory_map(self):
        """Hafıza haritası — en önemli düğümler"""
        nodes = self.data["nodes"]
        if not nodes:
            self.msg("ANKA", "Hafıza boş efendim."); return
        sorted_nodes = sorted(nodes.values(),
                             key=lambda x: x.get("access_count",0), reverse=True)
        r = f"🗺️ HAFIZA HARİTASI ({len(nodes)} bilgi)\n{'═'*35}\n"
        r += "🔥 En Çok Erişilenler:\n"
        for n in sorted_nodes[:5]:
            r += f"• {n['key']}: {str(n['value'])[:40]} ({n['access_count']}x)\n"
        # Etiket bulutu
        all_tags = []
        for n in nodes.values():
            all_tags.extend(n.get("tags", []))
        if all_tags:
            tag_count = {}
            for t in all_tags:
                tag_count[t] = tag_count.get(t,0) + 1
            top_tags = sorted(tag_count.items(), key=lambda x: -x[1])[:5]
            r += f"\n🏷️ Popüler Etiketler: {', '.join(t for t,_ in top_tags)}"
        self.msg("ANKA", r)

    def ai_insight(self):
        """Hafızadaki verileri analiz et, içgörü üret"""
        def _insight():
            nodes = self.data["nodes"]
            if len(nodes) < 3:
                self.msg("ANKA", "İçgörü için daha fazla veri gerekiyor efendim."); return
            sample = list(nodes.values())[:10]
            context = "\n".join(f"- {n['key']}: {str(n['value'])[:50]}" for n in sample)
            r = self.ollama.chat(
                f"Bu hafıza verilerini analiz et ve ilginç bağlantılar/içgörüler üret:\n{context}",
                system_override="Analitik AI. Verilerdeki gizli kalıpları bul.")
            self.data["insights"].append({
                "insight": r, "date": datetime.date.today().isoformat()
            })
            _save(self.mem_file, self.data)
            self.msg("ANKA", f"💡 Hafıza İçgörüsü:\n{r}")
            self.speak("İçgörü hazırlandı efendim.")
        threading.Thread(target=_insight, daemon=True).start()


# ═══════════════════════════════════════════════════════════════════════════════
# 2. ANKA TAHMİN MOTORU — Gelecek tahminleri
# ═══════════════════════════════════════════════════════════════════════════════
class PredictionMaster:
    """Her şeyi tahmin eden gelişmiş motor"""
    def __init__(self, ollama, speak_func, msg_func):
        self.ollama = ollama
        self.speak  = speak_func
        self.msg    = msg_func
        self.pred_file = os.path.join(BASE_DIR, "anka_predictions.json")
        self.data = _load(self.pred_file, {
            "predictions": [],
            "accuracy": {"correct": 0, "total": 0},
            "behavior_model": {}
        })

    def predict_stock(self, symbol):
        def _p():
            try:
                r = requests.get(
                    f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=5d",
                    timeout=5, headers={"User-Agent":"Mozilla/5.0"})
                data = r.json()
                closes = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]
                closes = [c for c in closes if c]
                if len(closes) < 2:
                    raise ValueError("Yetersiz veri")
                trend = closes[-1] - closes[0]
                pct = (trend / closes[0]) * 100
                avg = sum(closes)/len(closes)
                pred = self.ollama.chat(
                    f"Hisse: {symbol}, Son 5 gün kapanış: {[round(c,2) for c in closes]}, "
                    f"Trend: %{pct:.2f}, Ortalama: {avg:.2f}\n"
                    f"Teknik analiz ve kısa vadeli tahmin yap. Yatırım tavsiyesi değil.",
                    system_override="Teknik analist. Veri bazlı analiz yap.")
                r2 = (f"📈 {symbol} Analizi:\n"
                     f"• Son: ${closes[-1]:.2f}\n"
                     f"• 5G Değişim: %{pct:.2f}\n"
                     f"• Trend: {'↑' if trend>0 else '↓'}\n\n"
                     f"🔮 AI Analizi:\n{pred}")
                self.msg("ANKA", r2)
                self.speak(f"{symbol} analizi hazırlandı efendim.")
            except Exception as e:
                self.msg("ANKA", f"Hisse verisi alınamadı: {e}")
        threading.Thread(target=_p, daemon=True).start()

    def predict_weather_impact(self, activity):
        def _pw():
            try:
                r = requests.get("https://wttr.in/Istanbul?format=j1", timeout=5)
                d = r.json()["current_condition"][0]
                weather_ctx = f"Sıcaklık:{d['temp_C']}°C, {d['weatherDesc'][0]['value']}, Nem:%{d['humidity']}"
                pred = self.ollama.chat(
                    f"Hava: {weather_ctx}\nAktivite: {activity}\n"
                    f"Bu hava koşulları aktiviteyi nasıl etkiler? Öneri ver.",
                    system_override="Hava etkisi analisti. Pratik öneri ver.")
                self.msg("ANKA", f"🌤️ Hava × {activity}:\n{pred}")
            except:
                self.msg("ANKA", "Tahmin yapılamadı efendim.")
        threading.Thread(target=_pw, daemon=True).start()

    def personal_prediction(self):
        """Kişisel davranış tahmini"""
        hour = datetime.datetime.now().hour
        day = datetime.datetime.now().strftime("%A")
        model = self.data["behavior_model"]
        key = f"{day}_{hour}"
        if key in model:
            preds = sorted(model[key].items(), key=lambda x: -x[1])[:3]
            r = f"🔮 Bu saatte genellikle:\n"
            r += "\n".join(f"• {cmd} ({cnt}x)" for cmd,cnt in preds)
            self.msg("ANKA", r)
        else:
            self.msg("ANKA", "Yeterli davranış verisi yok efendim.")

    def log_behavior(self, command):
        """Davranışı öğren"""
        hour = datetime.datetime.now().hour
        day = datetime.datetime.now().strftime("%A")
        key = f"{day}_{hour}"
        if key not in self.data["behavior_model"]:
            self.data["behavior_model"][key] = {}
        cmd = command.lower()[:30]
        self.data["behavior_model"][key][cmd] = \
            self.data["behavior_model"][key].get(cmd, 0) + 1
        _save(self.pred_file, self.data)


# ═══════════════════════════════════════════════════════════════════════════════
# 3. ANKA ÇOKLU AJAN ORKESTRATÖRü — Paralel AI ajanlar
# ═══════════════════════════════════════════════════════════════════════════════
class MultiAgentOrchestrator:
    """
    Birden fazla yapay zeka ajanı paralel çalışır.
    Her ajan farklı bir perspektiften analiz yapar.
    """
    AGENTS = {
        "analist":    "Sen bir veri analisti. Sayısal ve istatistiksel açıdan değerlendir.",
        "eleştirmen": "Sen eleştirel bir düşünür. Zayıf noktaları ve riskleri bul.",
        "yaratıcı":   "Sen yaratıcı bir stratejist. Yenilikçi ve alışılmadık çözümler öner.",
        "pratikçi":   "Sen pratik bir uygulayıcı. Hemen hayata geçirilebilecek adımlar ver.",
        "uzman":      "Sen alanın uzmanı. Derin teknik bilgiyle değerlendir.",
    }

    def __init__(self, ollama, speak_func, msg_func):
        self.ollama = ollama
        self.speak  = speak_func
        self.msg    = msg_func

    def council(self, question, agents=None):
        """Birden fazla ajan soruyu farklı perspektiften yanıtlar"""
        selected = agents or list(self.AGENTS.keys())[:3]
        self.msg("ANKA",
            f"🤖 {len(selected)} Ajan Konseyi Başlıyor...\n"
            f"Soru: {question}")

        results = {}
        threads = []

        def run_agent(name, system):
            r = self.ollama.chat(
                f"Soru: {question}\nKısa ve net yanıt ver (max 150 kelime).",
                system_override=system)
            results[name] = r

        for agent_name in selected:
            if agent_name in self.AGENTS:
                t = threading.Thread(
                    target=run_agent,
                    args=(agent_name, self.AGENTS[agent_name]),
                    daemon=True)
                threads.append(t); t.start()

        def finalize():
            for t in threads: t.join(timeout=30)
            r = f"🤖 ÇOKLU AJAN ANALİZİ\n{'═'*40}\n"
            for name, result in results.items():
                emoji = {"analist":"📊","eleştirmen":"🔍","yaratıcı":"💡",
                        "pratikçi":"⚙️","uzman":"🎓"}.get(name,"🤖")
                r += f"\n{emoji} {name.upper()}:\n{result[:200]}\n"
            # Sentez
            if len(results) > 1:
                context = "\n".join(f"[{k}]: {v[:100]}" for k,v in results.items())
                synthesis = self.ollama.chat(
                    f"Bu ajan görüşlerini sentezle, ortak nokta ve en iyi öneriyi çıkar:\n{context}",
                    system_override="Sentezci. Farklı görüşleri birleştir.")
                r += f"\n{'─'*40}\n🏆 SENTEZ:\n{synthesis}"
            self.msg("ANKA", r)
            pyperclip.copy(r)
            self.speak("Çoklu ajan analizi tamamlandı efendim.")
        threading.Thread(target=finalize, daemon=True).start()

    def debate(self, topic):
        """İki ajan arasında tartışma"""
        def _debate():
            self.msg("ANKA", f"⚔️ Tartışma Başlıyor: {topic}")
            pro = self.ollama.chat(
                f"'{topic}' için en güçlü lehte argümanları sun.",
                system_override="Savunucu. Konuya lehte argüman sun.")
            con = self.ollama.chat(
                f"'{topic}' için en güçlü aleyhte argümanları sun.",
                system_override="Muhalif. Konuya aleyhte argüman sun.")
            verdict = self.ollama.chat(
                f"Konu: {topic}\nLehte: {pro[:200]}\nAleyhte: {con[:200]}\n"
                f"Tarafsız karar ver.",
                system_override="Yargıç. Tarafsız karar ver.")
            r = (f"⚔️ TARTIŞMA: {topic}\n{'═'*40}\n"
                 f"\n✅ LEHTE:\n{pro}\n"
                 f"\n❌ ALEYHte:\n{con}\n"
                 f"\n⚖️ KARAR:\n{verdict}")
            self.msg("ANKA", r); pyperclip.copy(r)
            self.speak("Tartışma tamamlandı efendim.")
        threading.Thread(target=_debate, daemon=True).start()


# ═══════════════════════════════════════════════════════════════════════════════
# 4. ANKA GERÇEK ZAMANLI ÖĞRENİCİ — Sürekli gelişen AI
# ═══════════════════════════════════════════════════════════════════════════════
class ContinuousLearner:
    """Anka her konuşmadan, her hatadan öğrenir"""
    def __init__(self, ollama, speak_func, msg_func):
        self.ollama = ollama
        self.speak  = speak_func
        self.msg    = msg_func
        self.learn_file = os.path.join(BASE_DIR, "anka_continuous.json")
        self.data = _load(self.learn_file, {
            "knowledge_graph": {},
            "corrections": [],
            "user_preferences": {},
            "skill_levels": {},
            "conversation_patterns": {}
        })

    def update_knowledge(self, topic, fact, confidence=0.8):
        """Bilgi grafiğini güncelle"""
        if topic not in self.data["knowledge_graph"]:
            self.data["knowledge_graph"][topic] = []
        self.data["knowledge_graph"][topic].append({
            "fact": fact, "confidence": confidence,
            "learned": datetime.datetime.now().isoformat()
        })
        if len(self.data["knowledge_graph"][topic]) > 20:
            self.data["knowledge_graph"][topic] = \
                self.data["knowledge_graph"][topic][-20:]
        _save(self.learn_file, self.data)

    def learn_preference(self, category, preference, value):
        """Kullanıcı tercihini öğren"""
        if category not in self.data["user_preferences"]:
            self.data["user_preferences"][category] = {}
        self.data["user_preferences"][category][preference] = {
            "value": value,
            "updated": datetime.datetime.now().isoformat()
        }
        _save(self.learn_file, self.data)
        r = f"✅ Öğrendim: {category}/{preference} = {value}"
        self.msg("ANKA", r); self.speak(r)

    def add_correction(self, wrong, correct, context=""):
        """Yanlışı düzelt ve öğren"""
        self.data["corrections"].append({
            "wrong": wrong, "correct": correct,
            "context": context,
            "date": datetime.date.today().isoformat()
        })
        _save(self.learn_file, self.data)
        r = f"📝 Düzeltme kaydedildi. Bir daha yapmayacağım efendim."
        self.msg("ANKA", r); self.speak(r)

    def skill_assessment(self, topic):
        """Bir konudaki bilgi seviyesini değerlendir"""
        def _assess():
            knowledge = self.data["knowledge_graph"].get(topic, [])
            level = min(10, len(knowledge) * 2)
            r = self.ollama.chat(
                f"Anka'nın '{topic}' konusundaki bilgisini değerlendir. "
                f"Bilgi sayısı: {len(knowledge)}, Seviye: {level}/10.\n"
                f"Gelişim için ne öğrenmeli?",
                system_override="Eğitim değerlendirici. Beceri analizi yap.")
            self.data["skill_levels"][topic] = level
            _save(self.learn_file, self.data)
            self.msg("ANKA", f"📊 {topic} Beceri Analizi:\n{r}")
        threading.Thread(target=_assess, daemon=True).start()

    def learning_report(self):
        """Öğrenme raporu"""
        kg = self.data["knowledge_graph"]
        prefs = self.data["user_preferences"]
        corrections = self.data["corrections"]
        skills = self.data["skill_levels"]
        r = (f"📚 ÖĞRENME RAPORU\n{'═'*35}\n"
             f"• Bilgi Konuları: {len(kg)}\n"
             f"• Toplam Bilgi: {sum(len(v) for v in kg.values())}\n"
             f"• Tercihler: {sum(len(v) for v in prefs.values())}\n"
             f"• Düzeltmeler: {len(corrections)}\n"
             f"• Değerlendirilen Beceri: {len(skills)}\n")
        if skills:
            top = sorted(skills.items(), key=lambda x: -x[1])[:3]
            r += f"\n🏆 En Güçlü Alanlar:\n"
            r += "\n".join(f"• {k}: {v}/10" for k,v in top)
        self.msg("ANKA", r)


# ═══════════════════════════════════════════════════════════════════════════════
# 5. ANKA SİSTEM ZEKASI — Bilgisayarı anlayan AI
# ═══════════════════════════════════════════════════════════════════════════════
class SystemIntelligence:
    """Sistemi anlayan ve otomatik optimize eden AI"""
    def __init__(self, ollama, speak_func, msg_func):
        self.ollama = ollama
        self.speak  = speak_func
        self.msg    = msg_func
        self.history = []
        self.running = True
        self.alerts  = {}
        threading.Thread(target=self._smart_monitor, daemon=True).start()

    def auto_diagnose(self):
        """Sistemi otomatik teşhis et ve çözüm üret"""
        def _diag():
            self.msg("ANKA","🔬 Sistem teşhisi yapılıyor...")
            issues = []
            cpu = psutil.cpu_percent(interval=2)
            ram = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            swap = psutil.swap_memory()
            temps = {}
            try: temps = psutil.sensors_temperatures()
            except: pass

            if cpu > 85: issues.append(f"CPU aşırı yüklü: %{cpu:.0f}")
            if ram.percent > 88: issues.append(f"RAM kritik: %{ram.percent:.0f}")
            if disk.percent > 90: issues.append(f"Disk dolu: %{disk.percent:.0f}")
            if swap.percent > 60: issues.append(f"Swap yüksek: %{swap.percent:.0f}")

            # CPU sıcaklık
            for name, entries in temps.items():
                for e in entries:
                    if e.current > 85:
                        issues.append(f"Yüksek sıcaklık ({name}): {e.current}°C")

            # Zombie süreçler
            zombies = [p for p in psutil.process_iter(['status'])
                      if p.info.get('status') == psutil.STATUS_ZOMBIE]
            if zombies:
                issues.append(f"{len(zombies)} zombie süreç var")

            if issues:
                diagnosis = self.ollama.chat(
                    f"Sistem sorunları: {'; '.join(issues)}\n"
                    f"Her sorun için adım adım çözüm ver.",
                    system_override="Sistem mühendisi. Pratik çözümler ver.")
                r = f"🔬 SİSTEM TEŞHİSİ\n{'═'*35}\n"
                r += "\n".join(f"⚠️ {i}" for i in issues)
                r += f"\n\n💊 Çözümler:\n{diagnosis}"
            else:
                r = "✅ Sistem sağlıklı! Sorun tespit edilmedi efendim."
            self.msg("ANKA", r)
            self.speak(f"{len(issues)} sorun tespit edildi efendim." if issues else "Sistem sağlıklı efendim.")
        threading.Thread(target=_diag, daemon=True).start()

    def predictive_maintenance(self):
        """Gelecekteki sorunları tahmin et"""
        def _pred():
            cpu_samples = []
            ram_samples = []
            for _ in range(5):
                cpu_samples.append(psutil.cpu_percent(interval=1))
                ram_samples.append(psutil.virtual_memory().percent)
                time.sleep(1)
            cpu_trend = cpu_samples[-1] - cpu_samples[0]
            ram_trend = ram_samples[-1] - ram_samples[0]
            disk = psutil.disk_usage('/')
            days_to_full = 0
            if disk.percent > 50:
                days_to_full = int((100 - disk.percent) / max(0.1, disk.percent / 30))

            pred = self.ollama.chat(
                f"Sistem metrikleri:\n"
                f"CPU trend: {cpu_trend:+.1f}% (5 örnekte)\n"
                f"RAM trend: {ram_trend:+.1f}% (5 örnekte)\n"
                f"Disk: %{disk.percent:.0f} dolu ({days_to_full} günde dolabilir)\n"
                f"Önümüzdeki 24 saat için sorun tahmini ve önleyici önlemler.",
                system_override="Sistem öngörü analisti. Proaktif öneriler ver.")
            r = (f"🔮 PREDİKTİF BAKIM ANALİZİ\n{'═'*35}\n"
                 f"• CPU Trendi: {cpu_trend:+.1f}%\n"
                 f"• RAM Trendi: {ram_trend:+.1f}%\n"
                 f"• Disk Doluluğu: %{disk.percent:.0f}\n\n"
                 f"🔮 Tahmin:\n{pred}")
            self.msg("ANKA", r)
            self.speak("Prediktif bakım analizi hazırlandı efendim.")
        threading.Thread(target=_pred, daemon=True).start()

    def smart_cleaner(self):
        """Akıllı sistem temizleyici"""
        def _clean():
            import gc, tempfile, glob as glob_mod
            self.msg("ANKA","🧹 Akıllı temizlik başlıyor...")
            cleaned = []
            # Python çöp toplama
            collected = gc.collect()
            cleaned.append(f"Python belleği: {collected} nesne")
            # Temp dosyaları
            temp_dir = tempfile.gettempdir()
            temp_files = glob_mod.glob(os.path.join(temp_dir,"anka_*.png"))
            for f in temp_files:
                try: os.remove(f); cleaned.append(f"Temp: {os.path.basename(f)}")
                except: pass
            r = f"🧹 Temizlik Tamamlandı:\n" + "\n".join(f"• {c}" for c in cleaned)
            self.msg("ANKA", r); self.speak("Temizlik tamamlandı efendim.")
        threading.Thread(target=_clean, daemon=True).start()

    def _smart_monitor(self):
        """Akıllı izleme — sadece gerçek sorunlarda uyar"""
        time.sleep(60)
        while self.running:
            try:
                now_key = datetime.datetime.now().strftime("%Y-%m-%d-%H")
                cpu = psutil.cpu_percent(interval=3)
                ram = psutil.virtual_memory().percent
                if cpu > 92 and not self.alerts.get(f"cpu_{now_key}"):
                    self.alerts[f"cpu_{now_key}"] = True
                    suggestion = "En ağır uygulamayı kapatmayı deneyin efendim."
                    self.msg("ANKA", f"🔴 CPU Kritik: %{cpu:.0f}! {suggestion}")
                if ram > 92 and not self.alerts.get(f"ram_{now_key}"):
                    self.alerts[f"ram_{now_key}"] = True
                    self.msg("ANKA", f"🔴 RAM Kritik: %{ram:.0f}! Bellek temizleniyor...")
                    import gc; gc.collect()
            except: pass
            time.sleep(180)

    def stop(self): self.running = False


# ═══════════════════════════════════════════════════════════════════════════════
# 6. ANKA YARATICI ZEKA — Orijinal içerik üretimi
# ═══════════════════════════════════════════════════════════════════════════════
class CreativeIntelligence:
    """Benzersiz ve yaratıcı içerik üreten sistem"""
    def __init__(self, ollama, speak_func, msg_func):
        self.ollama = ollama
        self.speak  = speak_func
        self.msg    = msg_func

    def brainstorm(self, topic, count=10):
        def _b():
            r = self.ollama.chat(
                f"'{topic}' için {count} yaratıcı ve orijinal fikir üret. "
                f"Her biri farklı bir perspektiften olsun. Madde madde.",
                system_override="Yaratıcı deha. Alışılmadık, orijinal fikirler üret.")
            self.msg("ANKA", f"💡 {topic} — Fikirleri:\n{r}")
            pyperclip.copy(r)
            self.speak(f"{count} fikir hazırlandı efendim.")
        threading.Thread(target=_b, daemon=True).start()

    def analogies(self, concept):
        def _a():
            r = self.ollama.chat(
                f"'{concept}' kavramını 5 farklı alanla analoji kurarak açıkla. "
                f"Spor, müzik, yemek, doğa, teknoloji gibi.",
                system_override="Analoji ustası. Yaratıcı benzetmeler kur.")
            self.msg("ANKA", f"🔄 {concept} Analojileri:\n{r}")
        threading.Thread(target=_a, daemon=True).start()

    def reframe(self, problem):
        def _r():
            r = self.ollama.chat(
                f"Bu problemi 5 farklı çerçeveden yeniden tanımla:\n'{problem}'\n\n"
                f"Her çerçeve farklı bir çözüm yolu açsın.",
                system_override="Problem yeniden çerçeveci. Farklı bakış açıları sun.")
            self.msg("ANKA", f"🖼️ Yeniden Çerçeveleme:\n{r}")
            pyperclip.copy(r)
        threading.Thread(target=_r, daemon=True).start()

    def first_principles(self, topic):
        def _fp():
            r = self.ollama.chat(
                f"'{topic}' konusunu birinci prensiplerden çözümle. "
                f"Elon Musk'ın yaklaşımı gibi: Temel varsayımları sorgula, "
                f"en basit gerçeklerden başla, yeniden inşa et.",
                system_override="Birinci prensipler düşünürü. Temel varsayımları sor.")
            self.msg("ANKA", f"⚗️ Birinci Prensipler:\n{r}")
            pyperclip.copy(r)
        threading.Thread(target=_fp, daemon=True).start()

    def six_hats(self, topic):
        """Edward de Bono'nun 6 Şapka tekniği"""
        def _six():
            hats = [
                ("⬜ Beyaz Şapka", "Sadece gerçekler ve veriler"),
                ("❤️ Kırmızı Şapka", "Duygular ve sezgiler"),
                ("🖤 Siyah Şapka", "Riskler ve olumsuzluklar"),
                ("💛 Sarı Şapka", "İyimserlik ve faydalar"),
                ("💚 Yeşil Şapka", "Yaratıcılık ve alternatifler"),
                ("💙 Mavi Şapka", "Süreç yönetimi ve özet"),
            ]
            r = f"🎩 6 ŞAPKA ANALİZİ: {topic}\n{'═'*40}\n"
            results = {}

            def analyze_hat(hat_name, perspective):
                result = self.ollama.chat(
                    f"Konu: {topic}\nPerspektif ({hat_name}): {perspective}\n"
                    f"Bu perspektiften 2-3 cümle değerlendir.",
                    system_override=f"{hat_name} perspektifi. Sadece bu açıdan değerlendir.")
                results[hat_name] = result

            threads = [threading.Thread(target=analyze_hat, args=(h,p), daemon=True)
                      for h,p in hats]
            for t in threads: t.start()
            for t in threads: t.join(timeout=20)

            for hat_name, _ in hats:
                if hat_name in results:
                    r += f"\n{hat_name}:\n{results[hat_name]}\n"

            self.msg("ANKA", r)
            pyperclip.copy(r)
            self.speak("6 Şapka analizi tamamlandı efendim.")
        threading.Thread(target=_six, daemon=True).start()


# ═══════════════════════════════════════════════════════════════════════════════
# 7. ANKA KİŞİSEL BÜYÜME — Gelişim takibi
# ═══════════════════════════════════════════════════════════════════════════════
class PersonalGrowth:
    def __init__(self, ollama, speak_func, msg_func):
        self.ollama = ollama
        self.speak  = speak_func
        self.msg    = msg_func
        self.growth_file = os.path.join(BASE_DIR, "anka_growth.json")
        self.data = _load(self.growth_file, {
            "journal": [],
            "gratitude": [],
            "wins": [],
            "lessons": [],
            "values": [],
            "vision": ""
        })

    def daily_journal(self, entry):
        self.data["journal"].append({
            "entry": entry,
            "date": datetime.datetime.now().isoformat(),
            "mood": ""
        })
        _save(self.growth_file, self.data)
        # AI ile analiz
        def _analyze():
            r = self.ollama.chat(
                f"Günlük giriş: '{entry}'\n"
                f"Duygu tonu, öne çıkan tema ve 1 içgörü. Kısa.",
                system_override="Kişisel gelişim koçu. Empatik analiz yap.")
            self.msg("ANKA", f"📔 Günlük Analizi:\n{r}")
        threading.Thread(target=_analyze, daemon=True).start()
        r = "📔 Günlük kaydedildi efendim."
        self.msg("ANKA", r); self.speak(r)

    def gratitude(self, items):
        today = datetime.date.today().isoformat()
        self.data["gratitude"].append({"items": items, "date": today})
        _save(self.growth_file, self.data)
        streak = len(set(g["date"] for g in self.data["gratitude"]))
        r = f"🙏 Şükran kaydedildi! (Toplam: {streak} gün)"
        self.msg("ANKA", r); self.speak(r)

    def log_win(self, win, category="genel"):
        self.data["wins"].append({
            "win": win, "category": category,
            "date": datetime.date.today().isoformat()
        })
        _save(self.growth_file, self.data)
        r = f"🏆 Kazanım kaydedildi: {win}"
        self.msg("ANKA", r); self.speak(r)

    def weekly_reflection(self):
        def _reflect():
            recent_journal = self.data["journal"][-7:]
            recent_wins = self.data["wins"][-5:]
            context = (
                f"Bu haftalık journal girişleri: {len(recent_journal)}\n"
                f"Kazanımlar: {[w['win'] for w in recent_wins]}\n"
            )
            r = self.ollama.chat(
                f"{context}\nHaftalık büyüme özeti ve önümüzdeki hafta için 3 odak noktası.",
                system_override="Kişisel gelişim koçu. İlham verici haftalık özet yaz.")
            self.msg("ANKA", f"🌱 Haftalık Büyüme Özeti:\n{r}")
            pyperclip.copy(r)
            self.speak("Haftalık refleksiyon hazırlandı efendim.")
        threading.Thread(target=_reflect, daemon=True).start()

    def set_vision(self, vision):
        self.data["vision"] = vision
        _save(self.growth_file, self.data)
        r = f"🌟 Vizyon belirlendi: {vision}"
        self.msg("ANKA", r); self.speak(r)

    def growth_stats(self):
        r = (f"🌱 KİŞİSEL BÜYÜME İSTATİSTİKLERİ\n{'═'*35}\n"
             f"📔 Journal: {len(self.data['journal'])} giriş\n"
             f"🙏 Şükran: {len(self.data['gratitude'])} gün\n"
             f"🏆 Kazanım: {len(self.data['wins'])}\n"
             f"💡 Ders: {len(self.data['lessons'])}\n"
             f"🌟 Vizyon: {self.data['vision'][:50] if self.data['vision'] else 'Belirlenmedi'}")
        self.msg("ANKA", r)


# ═══════════════════════════════════════════════════════════════════════════════
# KOMUT İŞLEYİCİ
# ═══════════════════════════════════════════════════════════════════════════════
class V100CommandProcessor:
    def __init__(self, speak_func, msg_func, ollama):
        self.speak   = speak_func
        self.msg     = msg_func
        self.ollama  = ollama
        self.memory  = InfiniteMemory(ollama, speak_func, msg_func)
        self.pred    = PredictionMaster(ollama, speak_func, msg_func)
        self.agents  = MultiAgentOrchestrator(ollama, speak_func, msg_func)
        self.learner = ContinuousLearner(ollama, speak_func, msg_func)
        self.sysai   = SystemIntelligence(ollama, speak_func, msg_func)
        self.creative= CreativeIntelligence(ollama, speak_func, msg_func)
        self.growth  = PersonalGrowth(ollama, speak_func, msg_func)

    def process(self, text):
        t = text.lower().strip()

        # ── Sonsuz Hafıza ─────────────────────────────────────────────────────
        if "hatırla:" in t or "hafızaya al:" in t:
            content = t.replace("hatırla:","").replace("hafızaya al:","").strip()
            parts = content.split("=")
            if len(parts) >= 2:
                self.memory.remember(parts[0].strip(), parts[1].strip())
            return True
        if "hatırla" in t and len(t) < 30:
            query = t.replace("hatırla","").strip()
            if query: self.memory.recall(query); return True
        if "hafıza haritası" in t: self.memory.memory_map(); return True
        if "bağlantıları bul" in t:
            key = t.replace("bağlantıları bul","").strip()
            if key: self.memory.find_connections(key); return True
        if "hafıza içgörüsü" in t: self.memory.ai_insight(); return True

        # ── Tahmin Motoru ─────────────────────────────────────────────────────
        if "hisse analizi" in t or "hisse tahmin" in t:
            symbol = t.replace("hisse analizi","").replace("hisse tahmin","").strip().upper()
            if symbol: self.pred.predict_stock(symbol); return True
        if "hava etkisi" in t:
            activity = t.replace("hava etkisi","").strip()
            if activity: self.pred.predict_weather_impact(activity); return True
        if "kişisel tahmin" in t or "ne yapacağımı tahmin et" in t:
            self.pred.personal_prediction(); return True

        # ── Çoklu Ajan ────────────────────────────────────────────────────────
        if "ajan konseyi" in t or "çoklu ajan" in t:
            question = t.replace("ajan konseyi","").replace("çoklu ajan","").strip()
            if question: self.agents.council(question); return True
        if "tartışma başlat" in t:
            topic = t.replace("tartışma başlat","").strip()
            if topic: self.agents.debate(topic); return True

        # ── Sürekli Öğrenme ───────────────────────────────────────────────────
        if "tercih kaydet" in t:
            parts = t.replace("tercih kaydet","").strip().split("=")
            if len(parts) >= 2:
                cat_pref = parts[0].strip().split("/")
                cat = cat_pref[0] if len(cat_pref)>1 else "genel"
                pref = cat_pref[-1]
                self.learner.learn_preference(cat, pref, parts[1].strip())
            return True
        if "düzelt:" in t:
            parts = t.replace("düzelt:","").strip().split("→")
            if len(parts) >= 2:
                self.learner.add_correction(parts[0].strip(), parts[1].strip())
            return True
        if "öğrenme raporu" in t: self.learner.learning_report(); return True
        if "beceri analizi" in t:
            topic = t.replace("beceri analizi","").strip()
            if topic: self.learner.skill_assessment(topic); return True

        # ── Sistem Zekası ─────────────────────────────────────────────────────
        if "sistem teşhisi" in t or "oto teşhis" in t:
            self.sysai.auto_diagnose(); return True
        if "prediktif bakım" in t or "sistem tahmini" in t:
            self.sysai.predictive_maintenance(); return True
        if "akıllı temizlik" in t:
            self.sysai.smart_cleaner(); return True

        # ── Yaratıcı Zeka ─────────────────────────────────────────────────────
        if "beyin fırtınası" in t or "fikir üret" in t:
            topic = t.replace("beyin fırtınası","").replace("fikir üret","").strip()
            m = re.search(r'(\d+)', t)
            count = int(m.group(1)) if m else 10
            if topic: self.creative.brainstorm(topic, count); return True
        if "analoji kur" in t:
            concept = t.replace("analoji kur","").strip()
            if concept: self.creative.analogies(concept); return True
        if "yeniden çerçevele" in t:
            problem = t.replace("yeniden çerçevele","").strip()
            if problem: self.creative.reframe(problem); return True
        if "birinci prensipler" in t:
            topic = t.replace("birinci prensipler","").strip()
            if topic: self.creative.first_principles(topic); return True
        if "6 şapka" in t or "altı şapka" in t:
            topic = t.replace("6 şapka","").replace("altı şapka","").strip()
            if topic: self.creative.six_hats(topic); return True

        # ── Kişisel Büyüme ────────────────────────────────────────────────────
        if "günlük yaz:" in t:
            entry = text.replace("günlük yaz:","").strip()
            if entry: self.growth.daily_journal(entry); return True
        if "şükran:" in t or "şükranım:" in t:
            items = t.replace("şükran:","").replace("şükranım:","").strip()
            if items: self.growth.gratitude(items); return True
        if "kazanım ekle:" in t:
            win = t.replace("kazanım ekle:","").strip()
            if win: self.growth.log_win(win); return True
        if "haftalık refleksiyon" in t: self.growth.weekly_reflection(); return True
        if "vizyon belirle:" in t:
            vision = text.replace("vizyon belirle:","").strip()
            if vision: self.growth.set_vision(vision); return True
        if "büyüme istatistik" in t: self.growth.growth_stats(); return True

        # ── v100 Yardım ───────────────────────────────────────────────────────
        if "v100 yardım" in t or "v100 komutlar" in t:
            r = (
                "🚀 ANKA v100 KOMUTLARI\n"
                "══════════════════════\n\n"
                "🧠 SONSUZ HAFIZA:\n"
                "• 'hatırla: [konu]=[değer]'\n"
                "• 'hatırla [konu]'\n"
                "• 'hafıza haritası'\n"
                "• 'bağlantıları bul [konu]'\n"
                "• 'hafıza içgörüsü'\n\n"
                "🔮 TAHMİN:\n"
                "• 'hisse analizi AAPL'\n"
                "• 'hava etkisi [aktivite]'\n"
                "• 'kişisel tahmin'\n\n"
                "🤖 ÇOKLU AJAN:\n"
                "• 'ajan konseyi [soru]'\n"
                "• 'tartışma başlat [konu]'\n\n"
                "📚 ÖĞRENME:\n"
                "• 'tercih kaydet [cat/pref]=[değer]'\n"
                "• 'düzelt: [yanlış]→[doğru]'\n"
                "• 'beceri analizi [konu]'\n"
                "• 'öğrenme raporu'\n\n"
                "💻 SİSTEM:\n"
                "• 'sistem teşhisi'\n"
                "• 'prediktif bakım'\n"
                "• 'akıllı temizlik'\n\n"
                "💡 YARATICI:\n"
                "• 'beyin fırtınası [konu]'\n"
                "• 'analoji kur [kavram]'\n"
                "• 'yeniden çerçevele [problem]'\n"
                "• 'birinci prensipler [konu]'\n"
                "• '6 şapka [konu]'\n\n"
                "🌱 KİŞİSEL BÜYÜME:\n"
                "• 'günlük yaz: [giriş]'\n"
                "• 'şükran: [maddeler]'\n"
                "• 'kazanım ekle: [başarı]'\n"
                "• 'haftalık refleksiyon'\n"
                "• 'vizyon belirle: [vizyon]'"
            )
            self.msg("ANKA", r)
            self.speak("v100 komut rehberi hazırlandı efendim.")
            return True

        return False
