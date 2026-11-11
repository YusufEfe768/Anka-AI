# ── ANKA ULTRA SENIOR — Mühendislik Seviyesi Modülü ──────────────────────────
# OKR, enerji takibi, bilimsel hesap, sistem mühendisi, AI pipeline
try:
    import pyperclip
except ImportError:
    class _PyClip:
        def copy(self,x):pass
        def paste(self):return ""
    pyperclip=_PyClip()
import json, os, time, threading, datetime, subprocess, re, math, statistics
import requests, psutil, socket
from anka_config import BASE_DIR, USER_NAME

ULTRA_FILE = os.path.join(BASE_DIR, "anka_ultra.json")

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
# 1. OKR SİSTEMİ — Google/Intel tarzı hedef yönetimi
# ═══════════════════════════════════════════════════════════════════════════════
class OKRSystem:
    def __init__(self, ollama, speak_func, msg_func):
        self.ollama = ollama
        self.speak  = speak_func
        self.msg    = msg_func
        self.okr_file = os.path.join(BASE_DIR, "anka_okr.json")
        self.data = _load(self.okr_file, {"quarters": {}, "current_quarter": None})

    def _current_quarter(self):
        now = datetime.date.today()
        q = (now.month - 1) // 3 + 1
        return f"Q{q} {now.year}"

    def add_objective(self, title, description=""):
        quarter = self._current_quarter()
        if quarter not in self.data["quarters"]:
            self.data["quarters"][quarter] = []
        obj = {
            "id": len(self.data["quarters"][quarter]) + 1,
            "title": title, "description": description,
            "key_results": [],
            "created": datetime.date.today().isoformat(),
            "status": "active"
        }
        self.data["quarters"][quarter].append(obj)
        self.data["current_quarter"] = quarter
        _save(self.okr_file, self.data)
        r = f"🎯 OKR Eklendi [{quarter}]\nHedef: {title}"
        self.msg("ANKA", r); self.speak(r)
        return obj["id"]

    def add_key_result(self, obj_id, title, target, unit="", current=0):
        quarter = self._current_quarter()
        for obj in self.data["quarters"].get(quarter, []):
            if obj["id"] == obj_id:
                obj["key_results"].append({
                    "title": title, "target": target,
                    "current": current, "unit": unit,
                    "progress": 0, "updates": []
                })
                _save(self.okr_file, self.data)
                r = f"✓ KR eklendi: {title} (Hedef: {target}{unit})"
                self.msg("ANKA", r); self.speak(r)
                return True
        return False

    def update_kr(self, obj_id, kr_index, value, note=""):
        quarter = self._current_quarter()
        for obj in self.data["quarters"].get(quarter, []):
            if obj["id"] == obj_id and kr_index < len(obj["key_results"]):
                kr = obj["key_results"][kr_index]
                kr["current"] = value
                kr["progress"] = min(100, int(value / kr["target"] * 100)) if kr["target"] else 0
                kr["updates"].append({
                    "value": value, "note": note,
                    "date": datetime.date.today().isoformat()
                })
                _save(self.okr_file, self.data)
                r = f"✅ KR Güncellendi: {kr['title']}\n• Mevcut: {value}{kr['unit']}\n• İlerleme: %{kr['progress']}"
                self.msg("ANKA", r); self.speak(r)
                return True
        return False

    def quarterly_review(self):
        def _review():
            quarter = self._current_quarter()
            objectives = self.data["quarters"].get(quarter, [])
            if not objectives:
                self.msg("ANKA", f"{quarter} için OKR bulunamadı efendim."); return
            r = f"📊 OKR DEĞERLENDİRME — {quarter}\n{'═'*40}\n"
            total_progress = []
            for obj in objectives:
                obj_progress = []
                r += f"\n🎯 {obj['title']}\n"
                for kr in obj["key_results"]:
                    prog = kr["progress"]
                    obj_progress.append(prog)
                    bar = "█"*(prog//10) + "░"*(10-prog//10)
                    r += f"  [{bar}] %{prog} — {kr['title']}\n"
                    r += f"  {kr['current']}{kr['unit']} / {kr['target']}{kr['unit']}\n"
                if obj_progress:
                    avg = sum(obj_progress)/len(obj_progress)
                    total_progress.append(avg)
                    r += f"  Ortalama: %{avg:.0f}\n"
            if total_progress:
                overall = sum(total_progress)/len(total_progress)
                emoji = "🏆" if overall>=70 else "⚠️" if overall>=40 else "🔴"
                r += f"\n{emoji} Genel: %{overall:.0f}\n"
            coaching = self.ollama.chat(
                f"OKR sonuç: %{sum(total_progress)/len(total_progress) if total_progress else 0:.0f}. "
                f"Kısa değerlendirme ve 3 öneri.",
                system_override="OKR uzmanı. Pratik öneriler ver.")
            r += f"\n💡 Koçluk:\n{coaching}"
            self.msg("ANKA", r)
            self.speak("OKR değerlendirmesi tamamlandı efendim.")
        threading.Thread(target=_review, daemon=True).start()

    def show_okr(self):
        quarter = self._current_quarter()
        objectives = self.data["quarters"].get(quarter, [])
        if not objectives:
            self.msg("ANKA", f"{quarter} için OKR yok efendim."); return
        r = f"🎯 OKR — {quarter}\n{'═'*35}\n"
        for obj in objectives:
            krlist = obj["key_results"]
            avg = sum(kr["progress"] for kr in krlist)/len(krlist) if krlist else 0
            bar = "█"*(int(avg)//10) + "░"*(10-int(avg)//10)
            r += f"\n#{obj['id']} [{bar}] {obj['title']}\n"
            for i, kr in enumerate(krlist):
                r += f"  KR{i+1}: {kr['title']} — %{kr['progress']}\n"
        self.msg("ANKA", r)


# ═══════════════════════════════════════════════════════════════════════════════
# 2. ENERJİ TAKİP SİSTEMİ
# ═══════════════════════════════════════════════════════════════════════════════
class EnergyTracker:
    def __init__(self, ollama, speak_func, msg_func):
        self.ollama = ollama
        self.speak  = speak_func
        self.msg    = msg_func
        self.energy_file = os.path.join(BASE_DIR, "anka_energy.json")
        self.data = _load(self.energy_file, {
            "logs": [], "hourly_avg": {}, "peak_hours": []
        })

    def log_energy(self, level, mood="", activity=""):
        now = datetime.datetime.now()
        entry = {
            "level": max(1, min(10, level)),
            "mood": mood, "activity": activity,
            "hour": now.hour, "day": now.strftime("%A"),
            "timestamp": now.isoformat()
        }
        self.data["logs"].append(entry)
        h = str(now.hour)
        if h not in self.data["hourly_avg"]:
            self.data["hourly_avg"][h] = []
        self.data["hourly_avg"][h].append(level)
        if len(self.data["logs"]) > 500:
            self.data["logs"] = self.data["logs"][-500:]
        _save(self.energy_file, self.data)
        emoji = "⚡" if level>=8 else "😐" if level>=5 else "😴"
        r = f"{emoji} Enerji: {level}/10" + (f" — {mood}" if mood else "")
        self.msg("ANKA", r); self.speak(r)

    def get_peak_hours(self):
        hourly = self.data["hourly_avg"]
        if not hourly: return []
        avgs = {h: sum(vals)/len(vals) for h,vals in hourly.items()}
        return sorted(avgs.items(), key=lambda x: -x[1])[:3]

    def energy_report(self):
        def _report():
            logs = self.data["logs"]
            if not logs:
                self.msg("ANKA","Enerji verisi yok efendim."); return
            recent = logs[-20:]
            levels = [l["level"] for l in recent]
            avg = statistics.mean(levels)
            trend = levels[-1]-levels[0] if len(levels)>=2 else 0
            peak = self.get_peak_hours()
            r = (f"⚡ ENERJİ RAPORU\n{'═'*30}\n"
                 f"• Ortalama: {avg:.1f}/10\n"
                 f"• Trend: {'↑' if trend>0 else '↓' if trend<0 else '→'}\n"
                 f"• Son Kayıt: {logs[-1]['level']}/10\n")
            if peak:
                r += f"\n🔥 En Verimli:\n"
                r += "\n".join(f"  • {h:0>2}:00 — {avg:.1f}/10" for h,avg in peak)
            advice = self.ollama.chat(
                f"Enerji ort:{avg:.1f}/10, trend:{'↑' if trend>0 else '↓'}. "
                f"3 pratik öneri.",
                system_override="Enerji koçu. Kısa öneriler.")
            r += f"\n\n💡 Öneriler:\n{advice}"
            self.msg("ANKA", r)
            self.speak("Enerji raporu hazırlandı efendim.")
        threading.Thread(target=_report, daemon=True).start()

    def optimal_schedule(self):
        def _schedule():
            peak = self.get_peak_hours()
            if not peak:
                self.msg("ANKA","Yeterli veri yok efendim."); return
            peak_str = ", ".join(f"{h:0>2}:00 ({avg:.1f}/10)" for h,avg in peak)
            r = self.ollama.chat(
                f"En verimli saatler: {peak_str}\n"
                f"Bu saatlere göre ideal günlük program öner.",
                system_override="Verimlilik uzmanı. Kişisel program yap.")
            self.msg("ANKA", f"📅 Optimal Program:\n{r}")
            self.speak("Optimal program hazırlandı efendim.")
        threading.Thread(target=_schedule, daemon=True).start()


# ═══════════════════════════════════════════════════════════════════════════════
# 3. BİLİMSEL HESAP MAKİNESİ
# ═══════════════════════════════════════════════════════════════════════════════
class ScientificCalculator:
    CONSTANTS = {
        "pi": math.pi, "e": math.e, "phi": (1+math.sqrt(5))/2,
        "c": 299792458, "g": 9.80665, "h": 6.62607015e-34,
        "k": 1.380649e-23, "na": 6.02214076e23, "r": 8.314462618
    }

    def __init__(self, speak_func, msg_func):
        self.speak = speak_func
        self.msg   = msg_func

    def evaluate(self, expression):
        try:
            expr = expression.lower()
            for tr,en in [("artı","+"),("eksi","-"),("çarpı","*"),("bölü","/"),
                         ("üssü","**"),("karekök","sqrt"),("faktöriyel","factorial"),
                         ("log","log10"),("ln","log"),("pi","pi"),("e","e")]:
                expr = expr.replace(tr, en)
            safe_ns = {
                "__builtins__":{},
                "sqrt":math.sqrt,"log":math.log,"log10":math.log10,
                "log2":math.log2,"sin":math.sin,"cos":math.cos,
                "tan":math.tan,"asin":math.asin,"acos":math.acos,
                "atan":math.atan,"exp":math.exp,"floor":math.floor,
                "ceil":math.ceil,"abs":abs,"round":round,"pow":pow,
                "factorial":math.factorial,"gcd":math.gcd,
                "pi":math.pi,"e":math.e,"inf":math.inf,
                "degrees":math.degrees,"radians":math.radians,
                **self.CONSTANTS
            }
            result = eval(expr, safe_ns)
            if isinstance(result, float):
                if abs(result)>1e6 or (abs(result)<1e-4 and result!=0):
                    formatted = f"{result:.6e}"
                else:
                    formatted = f"{result:.8g}"
            else:
                formatted = f"{result:,}" if isinstance(result,int) else str(result)
            r = (f"🔢 Hesaplama:\n"
                 f"• İfade: {expression}\n"
                 f"• Sonuç: {formatted}\n"
                 f"• Tip: {type(result).__name__}")
            self.msg("ANKA", r)
            self.speak(f"Sonuç: {formatted}")
            return result
        except ZeroDivisionError:
            self.msg("ANKA","❌ Sıfıra bölme hatası efendim.")
        except Exception as e:
            self.msg("ANKA", f"❌ Hesaplama hatası: {e}")
        return None

    def statistics_analysis(self, numbers_str):
        try:
            data = [float(x.strip()) for x in re.split(r'[,\s]+', numbers_str) if x.strip()]
            if not data:
                self.msg("ANKA","Sayı bulunamadı efendim."); return
            n = len(data)
            mean = statistics.mean(data)
            median = statistics.median(data)
            std = statistics.stdev(data) if n>1 else 0
            r = (f"📊 İstatistiksel Analiz ({n} sayı):\n{'═'*35}\n"
                 f"• Ortalama: {mean:.4f}\n"
                 f"• Medyan: {median:.4f}\n"
                 f"• Std Sapma: {std:.4f}\n"
                 f"• Min: {min(data):.4f}\n"
                 f"• Maks: {max(data):.4f}\n"
                 f"• Toplam: {sum(data):.4f}")
            self.msg("ANKA", r)
            self.speak(f"Ortalama {mean:.2f}, std sapma {std:.2f} efendim.")
        except Exception as e:
            self.msg("ANKA", f"İstatistik hatası: {e}")

    def unit_convert(self, value, from_unit, to_unit):
        conversions = {
            ("km","mil"):0.621371,("mil","km"):1.60934,
            ("kg","pound"):2.20462,("pound","kg"):0.453592,
            ("celsius","fahrenheit"):lambda x:x*9/5+32,
            ("fahrenheit","celsius"):lambda x:(x-32)*5/9,
            ("metre","feet"):3.28084,("feet","metre"):0.3048,
            ("litre","galon"):0.264172,("galon","litre"):3.78541,
            ("cm","inch"):0.393701,("inch","cm"):2.54,
        }
        key = (from_unit.lower(), to_unit.lower())
        conv = conversions.get(key)
        if conv:
            result = conv(value) if callable(conv) else value*conv
            r = f"🔄 {value} {from_unit} = {result:.4f} {to_unit}"
            self.msg("ANKA", r); self.speak(r)
        else:
            self.msg("ANKA", f"'{from_unit}' → '{to_unit}' dönüşümü bilinmiyor efendim.")

    def show_constants(self):
        labels = {
            "pi":"π (Pi)","e":"e (Euler)","phi":"φ (Altın Oran)",
            "c":"c (Işık Hızı, m/s)","g":"g (Yerçekimi, m/s²)",
            "h":"h (Planck, J·s)","k":"k (Boltzmann, J/K)",
            "na":"Nₐ (Avogadro)","r":"R (Gaz Sabiti)"
        }
        r = "🔬 Bilimsel Sabitler:\n"
        for key, val in self.CONSTANTS.items():
            label = labels.get(key, key)
            if abs(val)>1e6 or (abs(val)<1e-4 and val!=0):
                r += f"• {label}: {val:.4e}\n"
            else:
                r += f"• {label}: {val:.8g}\n"
        self.msg("ANKA", r)


# ═══════════════════════════════════════════════════════════════════════════════
# 4. SİSTEM MÜHENDİSİ
# ═══════════════════════════════════════════════════════════════════════════════
class SystemEngineer:
    def __init__(self, ollama, speak_func, msg_func):
        self.ollama  = ollama
        self.speak   = speak_func
        self.msg     = msg_func
        self.baseline = None

    def capture_baseline(self):
        self.baseline = {
            "cpu": psutil.cpu_percent(interval=2),
            "ram": psutil.virtual_memory().percent,
            "disk_io": psutil.disk_io_counters(),
            "net_io": psutil.net_io_counters(),
            "timestamp": datetime.datetime.now().isoformat()
        }
        r = f"📐 Baseline: CPU %{self.baseline['cpu']:.0f}, RAM %{self.baseline['ram']:.0f}"
        self.msg("ANKA", r); self.speak(r)

    def compare_to_baseline(self):
        if not self.baseline:
            self.msg("ANKA","'baseline kaydet' komutunu önce kullanın efendim."); return
        cpu = psutil.cpu_percent(interval=2)
        ram = psutil.virtual_memory().percent
        r = (f"📊 BASELINE KARŞILAŞTIRMA\n{'═'*35}\n"
             f"• CPU: %{cpu:.0f} (Δ{cpu-self.baseline['cpu']:+.0f}%)\n"
             f"• RAM: %{ram:.0f} (Δ{ram-self.baseline['ram']:+.0f}%)\n"
             f"• Durum: {'⚠️ Yüklü' if cpu-self.baseline['cpu']>20 else '✅ Normal'}")
        self.msg("ANKA", r)

    def deep_process_analysis(self):
        def _deep():
            self.msg("ANKA","🔬 Derin süreç analizi...")
            procs = []
            for p in psutil.process_iter(['name','pid','cpu_percent','memory_info','num_threads','status']):
                try:
                    mem = p.info['memory_info'].rss//1024//1024
                    cpu = p.info['cpu_percent'] or 0
                    if mem>50 or cpu>1:
                        procs.append({"name":p.info['name'],"pid":p.info['pid'],
                                     "cpu":cpu,"mem":mem,"threads":p.info['num_threads']})
                except: pass
            procs.sort(key=lambda x:-(x["cpu"]+x["mem"]*0.1))
            r = f"🔬 SÜREÇ ANALİZİ\n{'═'*40}\n"
            r += f"{'Süreç':<20}{'CPU%':>6}{'RAM':>8}{'Thread':>7}\n{'─'*45}\n"
            for p in procs[:12]:
                r += f"{p['name'][:20]:<20}{p['cpu']:>5.1f}%{p['mem']:>7}MB{p['threads']:>7}\n"
            self.msg("ANKA", r)
            self.speak(f"{len(procs)} süreç analiz edildi efendim.")
        threading.Thread(target=_deep, daemon=True).start()

    def network_analysis(self):
        def _net():
            conns = []
            try:
                for c in psutil.net_connections(kind='inet'):
                    if c.status=='ESTABLISHED' and c.raddr:
                        conns.append({"lport":c.laddr.port,"rip":c.raddr.ip,"rport":c.raddr.port})
            except: pass
            stats = psutil.net_if_stats()
            io    = psutil.net_io_counters(pernic=True)
            r = f"🌐 AĞ ANALİZİ\n{'═'*35}\n"
            r += f"Aktif Bağlantı: {len(conns)}\n\n📡 Arayüzler:\n"
            for iface, stat in stats.items():
                if stat.isup and iface in io:
                    nic = io[iface]
                    r += (f"• {iface}: ↓{nic.bytes_recv//1024//1024}MB "
                         f"↑{nic.bytes_sent//1024//1024}MB\n")
            if conns[:5]:
                r += "\n🔗 Bağlantılar:\n"
                for c in conns[:5]:
                    r += f"  :{c['lport']} → {c['rip']}:{c['rport']}\n"
            self.msg("ANKA", r)
            self.speak("Ağ analizi tamamlandı efendim.")
        threading.Thread(target=_net, daemon=True).start()

    def performance_bottleneck(self):
        def _bottle():
            self.msg("ANKA","🔍 Darboğaz analizi...")
            issues = []; suggestions = []
            cpu = psutil.cpu_percent(interval=2)
            ram = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            swap = psutil.swap_memory()
            if cpu>80: issues.append(f"🔴 CPU: %{cpu:.0f}"); suggestions.append("Ağır süreçleri kapat")
            if ram.percent>85: issues.append(f"🔴 RAM: %{ram.percent:.0f}"); suggestions.append("Sekmeleri azalt")
            if disk.percent>90: issues.append(f"🟡 Disk: %{disk.percent:.0f}"); suggestions.append("Temp dosyaları sil")
            if swap.percent>50: issues.append(f"🟡 Swap: %{swap.percent:.0f}"); suggestions.append("RAM yetersiz")
            if not issues:
                r = "✅ Sistem optimal! Darboğaz yok efendim."
            else:
                r = f"🔍 DARBOĞAZ ANALİZİ\n{'═'*35}\n"
                r += "\n".join(issues)
                r += f"\n\n💡 Öneriler:\n" + "\n".join(f"• {s}" for s in suggestions)
            self.msg("ANKA", r)
            self.speak(f"{len(issues)} darboğaz efendim." if issues else "Sistem optimal efendim.")
        threading.Thread(target=_bottle, daemon=True).start()

    def auto_diagnose(self):
        def _diag():
            self.msg("ANKA","🔬 Sistem teşhisi yapılıyor...")
            issues = []
            cpu = psutil.cpu_percent(interval=2)
            ram = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            if cpu>85: issues.append(f"CPU aşırı yüklü: %{cpu:.0f}")
            if ram.percent>88: issues.append(f"RAM kritik: %{ram.percent:.0f}")
            if disk.percent>90: issues.append(f"Disk dolu: %{disk.percent:.0f}")
            zombies = [p for p in psutil.process_iter(['status'])
                      if p.info.get('status')==psutil.STATUS_ZOMBIE]
            if zombies: issues.append(f"{len(zombies)} zombie süreç")
            if issues:
                diagnosis = self.ollama.chat(
                    f"Sorunlar: {'; '.join(issues)}\nHer biri için çözüm ver.",
                    system_override="Sistem mühendisi. Adım adım çözüm.")
                r = f"🔬 TEŞHİS\n{'═'*35}\n" + "\n".join(f"⚠️ {i}" for i in issues)
                r += f"\n\n💊 Çözümler:\n{diagnosis}"
            else:
                r = "✅ Sistem sağlıklı! Sorun yok efendim."
            self.msg("ANKA", r)
            self.speak(f"{len(issues)} sorun efendim." if issues else "Sağlıklı efendim.")
        threading.Thread(target=_diag, daemon=True).start()


# ═══════════════════════════════════════════════════════════════════════════════
# 5. AI PIPELINE — Çok adımlı AI işlemleri
# ═══════════════════════════════════════════════════════════════════════════════
class AIPipeline:
    """Birden fazla AI adımını zincirleme çalıştır"""
    def __init__(self, ollama, speak_func, msg_func):
        self.ollama = ollama
        self.speak  = speak_func
        self.msg    = msg_func

    def research_to_report(self, topic):
        """Araştır → Analiz et → Rapor yaz → Kaydet"""
        def _pipeline():
            self.msg("ANKA", f"🔄 AI Pipeline başlatıldı: {topic}")
            steps = ["Araştırma","Analiz","Rapor","Kayıt"]

            # Adım 1: Araştır
            self.msg("ANKA", f"[1/4] {steps[0]}...")
            research = self.ollama.chat(
                f"'{topic}' hakkında kapsamlı bilgi topla. Kaynaklar ve veriler.",
                system_override="Araştırmacı. Kapsamlı bilgi topla.")

            # Adım 2: Analiz
            self.msg("ANKA", f"[2/4] {steps[1]}...")
            analysis = self.ollama.chat(
                f"Bu araştırma verisini analiz et:\n{research[:500]}\n\nGüçlü/zayıf yönler, fırsatlar.",
                system_override="Analist. SWOT benzeri analiz yap.")

            # Adım 3: Rapor
            self.msg("ANKA", f"[3/4] {steps[2]}...")
            report = self.ollama.chat(
                f"Konu: {topic}\nAraştırma: {research[:300]}\nAnaliz: {analysis[:300]}\n"
                f"Profesyonel rapor yaz. Başlık, özet, bulgular, sonuç.",
                system_override="Rapor yazarı. Profesyonel format kullan.")

            # Adım 4: Kaydet
            self.msg("ANKA", f"[4/4] {steps[3]}...")
            path = os.path.join(os.path.expanduser("~"), "Desktop",
                               f"anka_rapor_{topic[:15].replace(' ','_')}.txt")
            with open(path,'w',encoding='utf-8') as f:
                f.write(f"ANKA AI RAPORU\n{'='*50}\nKonu: {topic}\n"
                       f"Tarih: {datetime.datetime.now().isoformat()}\n\n{report}")
            pyperclip.copy(report)
            self.msg("ANKA", f"✅ Pipeline Tamamlandı!\n📄 Rapor:\n{report[:400]}...")
            self.msg("ANKA", f"💾 Kaydedildi: {path}")
            self.speak("AI pipeline tamamlandı efendim.")
        threading.Thread(target=_pipeline, daemon=True).start()

    def idea_to_action(self, idea):
        """Fikir → Plan → Görevler → Takvim"""
        def _pipeline():
            self.msg("ANKA", f"💡 Fikir Pipeline: {idea}")
            # Fikri değerlendir
            eval_result = self.ollama.chat(
                f"Fikir: '{idea}'\nFikri değerlendir: Fırsatlar, riskler, kaynak ihtiyacı.",
                system_override="Girişimci. Fikri değerlendir.")
            # Plan yap
            plan = self.ollama.chat(
                f"Fikir: {idea}\nDeğerlendirme: {eval_result[:200]}\n"
                f"30 günlük eylem planı yap. Her hafta için 3 görev.",
                system_override="Proje planlayıcı. Somut plan yap.")
            # Önceliklendir
            priorities = self.ollama.chat(
                f"Plan: {plan[:300]}\nEn kritik 5 görevi öncelik sırasına koy.",
                system_override="Öncelik uzmanı. Etkili sırala.")
            r = (f"💡 FİKİR → EYLEM PLANI\n{'═'*40}\n"
                 f"Fikir: {idea}\n\n"
                 f"📊 Değerlendirme:\n{eval_result[:200]}\n\n"
                 f"📅 30 Günlük Plan:\n{plan[:300]}\n\n"
                 f"🎯 İlk 5 Öncelik:\n{priorities}")
            self.msg("ANKA", r)
            pyperclip.copy(r)
            self.speak("Eylem planı hazırlandı efendim.")
        threading.Thread(target=_pipeline, daemon=True).start()

    def content_pipeline(self, topic, platforms=None):
        """Konu → Blog + Twitter + LinkedIn + Özet"""
        platforms = platforms or ["blog","twitter","linkedin"]
        def _content():
            self.msg("ANKA", f"📝 İçerik Pipeline: {topic}")
            results = {}
            platform_prompts = {
                "blog":     f"'{topic}' hakkında 500 kelimelik blog yazısı yaz.",
                "twitter":  f"'{topic}' hakkında viral Twitter/X gönderisi (280 karakter).",
                "linkedin": f"'{topic}' hakkında profesyonel LinkedIn paylaşımı.",
                "instagram":f"'{topic}' için ilgi çekici Instagram başlığı ve hashtagler.",
            }
            for platform in platforms:
                prompt = platform_prompts.get(platform)
                if prompt:
                    self.msg("ANKA", f"✍️ {platform.capitalize()} yazılıyor...")
                    results[platform] = self.ollama.chat(
                        prompt, system_override=f"{platform.capitalize()} içerik uzmanı.")
            r = f"📝 İÇERİK PAKETİ: {topic}\n{'═'*40}\n"
            for platform, content in results.items():
                r += f"\n📱 {platform.upper()}:\n{content[:200]}\n{'─'*30}\n"
            self.msg("ANKA", r)
            pyperclip.copy(r)
            self.speak("İçerik paketi hazırlandı efendim.")
        threading.Thread(target=_content, daemon=True).start()


# ═══════════════════════════════════════════════════════════════════════════════
# KOMUT İŞLEYİCİ
# ═══════════════════════════════════════════════════════════════════════════════
class UltraCommandProcessor:
    def __init__(self, speak_func, msg_func, ollama):
        self.speak   = speak_func
        self.msg     = msg_func
        self.ollama  = ollama
        self.okr     = OKRSystem(ollama, speak_func, msg_func)
        self.energy  = EnergyTracker(ollama, speak_func, msg_func)
        self.calc    = ScientificCalculator(speak_func, msg_func)
        self.syseng  = SystemEngineer(ollama, speak_func, msg_func)
        self.pipeline= AIPipeline(ollama, speak_func, msg_func)

    def process(self, text):
        t = text.lower().strip()

        # ── OKR ──────────────────────────────────────────────────────────────
        if "okr hedef ekle" in t or "okr ekle" in t:
            title = t.replace("okr hedef ekle","").replace("okr ekle","").strip()
            if title: self.okr.add_objective(title); return True
        if "okr kr ekle" in t:
            parts = t.replace("okr kr ekle","").strip().split(",")
            if len(parts)>=3:
                try:
                    self.okr.add_key_result(int(parts[0].strip()),
                        parts[1].strip(), float(parts[2].strip()),
                        parts[3].strip() if len(parts)>3 else "")
                except: self.msg("ANKA","Format: 'okr kr ekle [id],[başlık],[hedef],[birim]'")
            return True
        if "okr güncelle" in t:
            nums = re.findall(r'[\d.]+', t)
            if len(nums)>=3:
                self.okr.update_kr(int(nums[0]), int(nums[1])-1, float(nums[2]))
            return True
        if "okr çeyrek" in t or "okr review" in t:
            self.okr.quarterly_review(); return True
        if "okrlerim" in t or "okr göster" in t:
            self.okr.show_okr(); return True

        # ── Enerji ───────────────────────────────────────────────────────────
        if "enerji kaydet" in t or "enerji seviyem" in t:
            m = re.search(r'(\d+)', t)
            level = int(m.group(1)) if m else 5
            mood = "iyi" if "iyi" in t else "kötü" if "kötü" in t else ""
            self.energy.log_energy(level, mood); return True
        if "enerji raporu" in t: self.energy.energy_report(); return True
        if "optimal program" in t or "verimli saatler" in t:
            self.energy.optimal_schedule(); return True

        # ── Bilimsel Hesap ────────────────────────────────────────────────────
        if "bilimsel hesapla" in t:
            expr = t.replace("bilimsel hesapla","").strip()
            if expr: self.calc.evaluate(expr); return True
        if "istatistik analizi" in t:
            nums = t.replace("istatistik analizi","").strip()
            if nums: self.calc.statistics_analysis(nums); return True
        if "birim çevir" in t:
            m = re.search(r'(\d+(?:\.\d+)?)\s*(\w+)\s*(?:→|to|den|dan)\s*(\w+)', t)
            if m: self.calc.unit_convert(float(m.group(1)), m.group(2), m.group(3))
            return True
        if "bilimsel sabitler" in t or "fizik sabitleri" in t:
            self.calc.show_constants(); return True

        # ── Sistem Mühendisi ──────────────────────────────────────────────────
        if "baseline kaydet" in t: self.syseng.capture_baseline(); return True
        if "baseline karşılaştır" in t: self.syseng.compare_to_baseline(); return True
        if "derin süreç analizi" in t: self.syseng.deep_process_analysis(); return True
        if "ağ analizi" in t: self.syseng.network_analysis(); return True
        if "darboğaz analizi" in t or "performans darboğaz" in t:
            self.syseng.performance_bottleneck(); return True
        if "sistem teşhisi" in t or "oto teşhis" in t:
            self.syseng.auto_diagnose(); return True

        # ── AI Pipeline ───────────────────────────────────────────────────────
        if "araştır ve raporla" in t or "pipeline araştır" in t:
            topic = t.replace("araştır ve raporla","").replace("pipeline araştır","").strip()
            if topic: self.pipeline.research_to_report(topic); return True
        if "fikirden plana" in t or "fikir pipeline" in t:
            idea = t.replace("fikirden plana","").replace("fikir pipeline","").strip()
            if idea: self.pipeline.idea_to_action(idea); return True
        if "içerik paketi" in t or "içerik pipeline" in t:
            topic = t.replace("içerik paketi","").replace("içerik pipeline","").strip()
            if topic: self.pipeline.content_pipeline(topic); return True

        # ── Yardım ───────────────────────────────────────────────────────────
        if "ultra yardım" in t or "senior yardım" in t:
            r = (
                "🚀 ANKA ULTRA SENIOR KOMUTLARI\n"
                "══════════════════════════════\n\n"
                "🎯 OKR:\n"
                "• 'okr hedef ekle [başlık]'\n"
                "• 'okr kr ekle [id],[başlık],[hedef],[birim]'\n"
                "• 'okr güncelle [obj_id] [kr_no] [değer]'\n"
                "• 'okr çeyrek' → Değerlendirme\n"
                "• 'okrlerim'\n\n"
                "⚡ ENERJİ:\n"
                "• 'enerji kaydet 8 iyi'\n"
                "• 'enerji raporu'\n"
                "• 'optimal program'\n\n"
                "🔢 BİLİMSEL HESAP:\n"
                "• 'bilimsel hesapla sqrt(144)+pi'\n"
                "• 'istatistik analizi 1,2,3,4,5'\n"
                "• 'birim çevir 100 km → mil'\n"
                "• 'bilimsel sabitler'\n\n"
                "💻 SİSTEM MÜHENDİSİ:\n"
                "• 'baseline kaydet'\n"
                "• 'baseline karşılaştır'\n"
                "• 'derin süreç analizi'\n"
                "• 'ağ analizi'\n"
                "• 'darboğaz analizi'\n"
                "• 'sistem teşhisi'\n\n"
                "🤖 AI PIPELINE:\n"
                "• 'araştır ve raporla [konu]'\n"
                "• 'fikirden plana [fikir]'\n"
                "• 'içerik paketi [konu]'"
            )
            self.msg("ANKA", r)
            self.speak("Ultra senior komut rehberi hazırlandı efendim.")
            return True

        return False
