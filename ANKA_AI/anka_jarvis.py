# ── ANKA JARVIS MODÜLü v2 ────────────────────────────────────────────────────
# Şaşırtıcı düzeyde yeni özellikler
try:
    import pyperclip
except ImportError:
    class _PyClip:
        def copy(self,x):pass
        def paste(self):return ""
    pyperclip=_PyClip()
import json, os, time, threading, datetime, subprocess, webbrowser
import requests, re, random, psutil, math
from anka_config import BASE_DIR, USER_NAME

JARVIS_FILE = os.path.join(BASE_DIR, "anka_jarvis.json")

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


# ── 1. ZAMAN MAKİNESİ — Geçmiş konuşmaları geri getir ───────────────────────
class TimeMachine:
    def __init__(self, speak_func, msg_func):
        self.speak = speak_func
        self.msg = msg_func

    def replay_day(self, days_ago=1):
        from anka_local_ai import CONTEXT_FILE
        data = _load(CONTEXT_FILE, {"conversation": []})
        target = (datetime.date.today() - datetime.timedelta(days=days_ago)).isoformat()
        past = [c for c in data["conversation"] if c.get("time","").startswith(target)]
        if not past:
            r = f"⏳ {days_ago} gün öncesine ait konuşma bulunamadı efendim."
        else:
            r = f"⏳ {days_ago} GÜN ÖNCESİ — {target}\n{'═'*35}\n"
            for c in past[:10]:
                role = "SEN" if c["role"] == "user" else "ANKA"
                r += f"[{c.get('time','?')[11:16]}] {role}: {c['text'][:60]}\n"
        self.msg("ANKA", r); self.speak(r[:150])

    def search_history(self, keyword):
        from anka_local_ai import CONTEXT_FILE
        data = _load(CONTEXT_FILE, {"conversation": []})
        found = [c for c in data["conversation"] if keyword.lower() in c.get("text","").lower()]
        if not found:
            r = f"🔍 '{keyword}' geçmiş konuşmalarda bulunamadı efendim."
        else:
            r = f"🔍 '{keyword}' için {len(found)} sonuç:\n"
            for c in found[-5:]:
                role = "SEN" if c["role"] == "user" else "ANKA"
                r += f"• {c.get('time','?')[:10]} {role}: {c['text'][:50]}\n"
        self.msg("ANKA", r); self.speak(r[:150])


# ── 2. ANKA GÜNLÜĞÜ — Otomatik gün özeti ────────────────────────────────────
class AnkaDiary:
    def __init__(self, ollama, speak_func, msg_func):
        self.ollama = ollama
        self.speak = speak_func
        self.msg = msg_func
        self.diary_file = os.path.join(BASE_DIR, "anka_diary.json")

    def write_entry(self, note=""):
        diary = _load(self.diary_file, [])
        now = datetime.datetime.now()
        entry = {
            "date": now.isoformat(),
            "note": note,
            "mood": "",
            "weather": "",
            "system": f"CPU:%{psutil.cpu_percent():.0f} RAM:%{psutil.virtual_memory().percent:.0f}"
        }
        try:
            r = requests.get("https://wttr.in/Istanbul?format=j1", timeout=3)
            d = r.json()["current_condition"][0]
            entry["weather"] = f"{d['temp_C']}°C {d['weatherDesc'][0]['value']}"
        except: pass
        diary.append(entry)
        if len(diary) > 365: diary = diary[-365:]
        _save(self.diary_file, diary)
        r = f"📔 Günlük kaydedildi: {now.strftime('%d %B %Y %H:%M')}"
        self.msg("ANKA", r); self.speak(r)

    def read_entries(self, days=7):
        diary = _load(self.diary_file, [])
        since = (datetime.date.today() - datetime.timedelta(days=days)).isoformat()
        recent = [e for e in diary if e["date"][:10] >= since]
        if not recent:
            r = f"Son {days} günde günlük kaydı yok efendim."
        else:
            r = f"📔 Son {days} Gün Günlüğü:\n{'═'*30}\n"
            for e in recent[-7:]:
                r += f"\n📅 {e['date'][:10]}\n"
                if e.get("weather"): r += f"🌤 {e['weather']}\n"
                if e.get("note"): r += f"📝 {e['note']}\n"
                r += f"💻 {e.get('system','')}\n"
        self.msg("ANKA", r)

    def generate_weekly_summary(self):
        def _gen():
            diary = _load(self.diary_file, [])
            since = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()
            week = [e for e in diary if e["date"][:10] >= since]
            if not week:
                self.msg("ANKA", "Haftalık günlük verisi yok efendim."); return
            notes = [e.get("note","") for e in week if e.get("note")]
            context = "\n".join(notes[:5]) if notes else "Not yok"
            r = self.ollama.chat(
                f"Bu haftalık günlük notlarına göre özet yaz:\n{context}",
                system_override="Kişisel asistan. Haftalık özet yaz.")
            self.msg("ANKA", f"📔 Haftalık Özet:\n{r}")
            self.speak("Haftalık özet hazırlandı efendim.")
        threading.Thread(target=_gen, daemon=True).start()


# ── 3. SES PROFİLİ TANIMA — Sesi ile giriş ──────────────────────────────────
class VoiceProfileManager:
    def __init__(self, speak_func, msg_func):
        self.speak = speak_func
        self.msg = msg_func
        self.profile_file = os.path.join(BASE_DIR, "anka_voice_profiles.json")

    def list_profiles(self):
        profiles = _load(self.profile_file, {})
        if not profiles:
            r = "Kayıtlı ses profili yok efendim."
        else:
            r = f"🎤 Ses Profilleri ({len(profiles)}):\n"
            r += "\n".join(f"• {name}" for name in profiles.keys())
        self.msg("ANKA", r); self.speak(r)

    def set_active(self, name):
        profiles = _load(self.profile_file, {})
        if name.lower() in profiles:
            r = f"✓ '{name}' ses profili aktif efendim."
        else:
            r = f"'{name}' profili bulunamadı. Önce ses kaydı yapın efendim."
        self.msg("ANKA", r); self.speak(r)


# ── 4. AKILLI AJANDA — Çakışma tespiti ve optimizasyon ──────────────────────
class SmartAgenda:
    def __init__(self, ollama, speak_func, msg_func):
        self.ollama = ollama
        self.speak = speak_func
        self.msg = msg_func
        self.agenda_file = os.path.join(BASE_DIR, "anka_smart_agenda.json")

    def add_smart(self, title, duration_min, deadline, priority=5):
        agenda = _load(self.agenda_file, [])
        item = {
            "title": title,
            "duration": duration_min,
            "deadline": deadline,
            "priority": priority,
            "added": datetime.datetime.now().isoformat(),
            "done": False
        }
        agenda.append(item)
        agenda.sort(key=lambda x: (-x["priority"], x["deadline"]))
        _save(self.agenda_file, agenda)
        r = f"✓ '{title}' ajandaya eklendi. Öncelik: {priority}/10"
        self.msg("ANKA", r); self.speak(r)

    def optimize_schedule(self):
        def _opt():
            agenda = _load(self.agenda_file, [])
            pending = [a for a in agenda if not a["done"]]
            if not pending:
                self.msg("ANKA", "Ajanda boş efendim."); return
            items_text = "\n".join(f"- {a['title']} ({a['duration']}dk, son: {a['deadline']}, öncelik: {a['priority']})"
                                  for a in pending[:8])
            r = self.ollama.chat(
                f"Bu görevleri en verimli şekilde sırala ve bugünkü program öner:\n{items_text}",
                system_override="Verimlilik uzmanı. Optimal program yap.")
            self.msg("ANKA", f"📅 Optimize Program:\n{r}")
            self.speak("Program optimize edildi efendim.")
        threading.Thread(target=_opt, daemon=True).start()

    def conflict_check(self):
        agenda = _load(self.agenda_file, [])
        today = datetime.date.today().isoformat()
        today_items = [a for a in agenda if a.get("deadline","") == today and not a["done"]]
        total_min = sum(a["duration"] for a in today_items)
        working_min = 8 * 60
        if total_min > working_min:
            r = (f"⚠️ ÇAKIŞMA TESPİT EDİLDİ!\n"
                f"• Bugün {len(today_items)} görev var\n"
                f"• Toplam süre: {total_min} dakika\n"
                f"• Çalışma süresi: {working_min} dakika\n"
                f"• Fazla: {total_min-working_min} dakika\n"
                f"💡 Bazı görevleri erteleyin efendim!")
        else:
            r = (f"✅ Ajanda temiz efendim!\n"
                f"• {len(today_items)} görev, {total_min} dakika\n"
                f"• {working_min-total_min} dakika boş zaman var")
        self.msg("ANKA", r); self.speak(r[:150])


# ── 5. KOD HAFIZA — Kod parçalarını kaydet ve bul ───────────────────────────
class CodeVault:
    def __init__(self, speak_func, msg_func):
        self.speak = speak_func
        self.msg = msg_func
        self.vault_file = os.path.join(BASE_DIR, "anka_code_vault.json")

    def save_code(self, name, code, language="python", description=""):
        vault = _load(self.vault_file, {})
        vault[name.lower()] = {
            "name": name, "code": code,
            "language": language, "description": description,
            "saved": datetime.datetime.now().isoformat(),
            "use_count": 0
        }
        _save(self.vault_file, vault)
        r = f"💾 '{name}' kodu kasaya kaydedildi efendim."
        self.msg("ANKA", r); self.speak(r)

    def get_code(self, name):
        vault = _load(self.vault_file, {})
        # Tam eşleşme
        if name.lower() in vault:
            entry = vault[name.lower()]
            entry["use_count"] += 1
            _save(self.vault_file, vault)
            pyperclip.copy(entry["code"])
            r = f"💻 '{entry['name']}' ({entry['language']}):\n{entry['code'][:500]}\n\n✓ Panoya kopyalandı!"
            self.msg("ANKA", r)
            return entry["code"]
        # Kısmi eşleşme
        for key, entry in vault.items():
            if name.lower() in key or name.lower() in entry.get("description","").lower():
                pyperclip.copy(entry["code"])
                self.msg("ANKA", f"💻 '{entry['name']}' bulundu ve kopyalandı efendim.")
                return entry["code"]
        self.msg("ANKA", f"'{name}' kodu kasada bulunamadı efendim.")
        return None

    def list_codes(self):
        vault = _load(self.vault_file, {})
        if not vault:
            r = "Kod kasası boş efendim."
        else:
            r = f"💻 KOD KASASI ({len(vault)} kod):\n"
            for name, entry in vault.items():
                r += f"• {entry['name']} [{entry['language']}] — {entry.get('description','')[:30]}\n"
        self.msg("ANKA", r)

    def search_code(self, keyword):
        vault = _load(self.vault_file, {})
        found = [(name, e) for name, e in vault.items()
                if keyword.lower() in e.get("code","").lower() or
                   keyword.lower() in e.get("description","").lower()]
        if found:
            r = f"🔍 '{keyword}' için {len(found)} kod bulundu:\n"
            r += "\n".join(f"• {e['name']}" for _, e in found[:5])
        else:
            r = f"'{keyword}' içeren kod bulunamadı efendim."
        self.msg("ANKA", r)


# ── 6. CANLI FİYAT TAKİBİ — Alarm sistemi ───────────────────────────────────
class LivePriceTracker:
    def __init__(self, speak_func, msg_func):
        self.speak = speak_func
        self.msg = msg_func
        self.alerts_file = os.path.join(BASE_DIR, "anka_price_alerts.json")
        self.running = True
        self.alerts = _load(self.alerts_file, [])
        threading.Thread(target=self._loop, daemon=True).start()

    def add_alert(self, asset, target_price, direction="above"):
        self.alerts.append({
            "asset": asset.upper(), "target": target_price,
            "direction": direction, "triggered": False,
            "added": datetime.datetime.now().isoformat()
        })
        _save(self.alerts_file, self.alerts)
        emoji = "📈" if direction == "above" else "📉"
        r = f"{emoji} Alarm kuruldu: {asset.upper()} {'>' if direction=='above' else '<'} {target_price}"
        self.msg("ANKA", r); self.speak(r)

    def _get_price(self, asset):
        try:
            asset = asset.upper()
            if asset in ["BTC","ETH","BNB","SOL","DOGE","XRP"]:
                r = requests.get(
                    f"https://api.coinbase.com/v2/prices/{asset}-USD/spot", timeout=5)
                return float(r.json()["data"]["amount"]), "USD"
            elif asset in ["USD","EUR","GBP"]:
                r = requests.get(
                    "https://api.exchangerate-api.com/v4/latest/USD", timeout=5)
                rate = r.json()["rates"].get("TRY", 0)
                if asset == "USD": return rate, "TRY"
        except: pass
        return None, None

    def check_prices(self):
        changed = False
        for alert in self.alerts:
            if alert["triggered"]: continue
            price, currency = self._get_price(alert["asset"])
            if price is None: continue
            triggered = (alert["direction"] == "above" and price >= alert["target"]) or \
                       (alert["direction"] == "below" and price <= alert["target"])
            if triggered:
                alert["triggered"] = True
                changed = True
                emoji = "📈" if alert["direction"] == "above" else "📉"
                r = (f"{emoji} FİYAT ALARMI!\n"
                     f"• {alert['asset']}: {price:,.2f} {currency}\n"
                     f"• Hedef: {alert['target']:,.2f}")
                self.msg("ANKA", r)
                self.speak(f"{alert['asset']} fiyat alarmı tetiklendi efendim!")
                try:
                    requests.post("https://ntfy.sh/anka-yusuf-2026",
                        data=r.encode(),
                        headers={"Title":f"{emoji} FİYAT ALARMI","Priority":"high"},
                        timeout=3)
                except: pass
        if changed: _save(self.alerts_file, self.alerts)

    def list_alerts(self):
        active = [a for a in self.alerts if not a["triggered"]]
        if not active:
            r = "Aktif fiyat alarmı yok efendim."
        else:
            r = f"🔔 Aktif Fiyat Alarmları ({len(active)}):\n"
            for a in active:
                emoji = "📈" if a["direction"] == "above" else "📉"
                r += f"{emoji} {a['asset']} {'>' if a['direction']=='above' else '<'} {a['target']:,.2f}\n"
        self.msg("ANKA", r); self.speak(r)

    def _loop(self):
        time.sleep(30)
        while self.running:
            try: self.check_prices()
            except: pass
            time.sleep(60)

    def stop(self): self.running = False


# ── 7. AKILLI DOSYA ASISTANI — Dosyaları AI ile organize et ─────────────────
class SmartFileAssistant:
    def __init__(self, ollama, speak_func, msg_func):
        self.ollama = ollama
        self.speak = speak_func
        self.msg = msg_func

    def analyze_folder(self, path):
        def _analyze():
            if not os.path.exists(path):
                self.msg("ANKA", "Klasör bulunamadı efendim."); return
            files = os.listdir(path)
            ext_count = {}
            for f in files:
                ext = os.path.splitext(f)[1].lower() or "no_ext"
                ext_count[ext] = ext_count.get(ext, 0) + 1
            summary = f"Klasör: {path}\nDosya sayısı: {len(files)}\n"
            for ext, count in sorted(ext_count.items(), key=lambda x: -x[1])[:8]:
                summary += f"  {ext}: {count} dosya\n"
            r = self.ollama.chat(
                f"Bu klasör analizine göre düzenleme öner:\n{summary}",
                system_override="Dosya organizasyon uzmanı. Pratik öneriler ver.")
            self.msg("ANKA", f"📁 Klasör Analizi:\n{summary}\n💡 Öneriler:\n{r}")
            self.speak("Klasör analizi tamamlandı efendim.")
        threading.Thread(target=_analyze, daemon=True).start()

    def rename_smart(self, folder, pattern, ollama):
        def _rename():
            if not os.path.exists(folder): return
            files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
            if not files:
                self.msg("ANKA", "Klasörde dosya yok efendim."); return
            sample = "\n".join(files[:10])
            suggestion = ollama.chat(
                f"Bu dosyalar için '{pattern}' kuralına göre yeniden adlandırma öner:\n{sample}",
                system_override="Dosya adlandırma uzmanı. Eski→Yeni formatında listele.")
            self.msg("ANKA", f"✏️ Yeniden Adlandırma Önerileri:\n{suggestion}")
            self.speak("Adlandırma önerileri hazırlandı efendim.")
        threading.Thread(target=_rename, daemon=True).start()


# ── 8. KİŞİSEL KOÇ — Günlük hedef takibi ───────────────────────────────────
class PersonalCoach:
    def __init__(self, ollama, speak_func, msg_func):
        self.ollama = ollama
        self.speak = speak_func
        self.msg = msg_func
        self.coach_file = os.path.join(BASE_DIR, "anka_coach.json")
        self.data = _load(self.coach_file, {
            "daily_goals": [],
            "streaks": {},
            "completed_today": [],
            "last_date": None
        })
        self._check_new_day()

    def _check_new_day(self):
        today = datetime.date.today().isoformat()
        if self.data.get("last_date") != today:
            self.data["completed_today"] = []
            self.data["last_date"] = today
            _save(self.coach_file, self.data)

    def set_daily_goal(self, goal, category="genel"):
        self.data["daily_goals"].append({
            "goal": goal, "category": category,
            "set_date": datetime.date.today().isoformat(),
            "completed_dates": []
        })
        _save(self.coach_file, self.data)
        r = f"🎯 Günlük hedef eklendi: {goal}"
        self.msg("ANKA", r); self.speak(r)

    def complete_goal(self, goal_name):
        today = datetime.date.today().isoformat()
        for goal in self.data["daily_goals"]:
            if goal_name.lower() in goal["goal"].lower():
                if today not in goal["completed_dates"]:
                    goal["completed_dates"].append(today)
                    # Streak hesapla
                    streak = self._calc_streak(goal["completed_dates"])
                    self.data["streaks"][goal["goal"]] = streak
                    _save(self.coach_file, self.data)
                    emoji = "🔥" if streak >= 7 else "✅"
                    r = f"{emoji} '{goal['goal']}' tamamlandı! Seri: {streak} gün!"
                    self.msg("ANKA", r); self.speak(r)
                    return True
        return False

    def _calc_streak(self, dates):
        if not dates: return 0
        sorted_dates = sorted(dates, reverse=True)
        streak = 1
        for i in range(1, len(sorted_dates)):
            d1 = datetime.date.fromisoformat(sorted_dates[i-1])
            d2 = datetime.date.fromisoformat(sorted_dates[i])
            if (d1 - d2).days == 1:
                streak += 1
            else:
                break
        return streak

    def daily_checkin(self):
        def _check():
            goals = self.data["daily_goals"]
            today = datetime.date.today().isoformat()
            completed = [g for g in goals if today in g.get("completed_dates", [])]
            pending = [g for g in goals if today not in g.get("completed_dates", [])]
            r = (f"📊 GÜNLÜK KONTROL\n{'═'*30}\n"
                f"✅ Tamamlanan: {len(completed)}/{len(goals)}\n")
            if pending:
                r += "\n⏳ Bekleyen:\n"
                r += "\n".join(f"• {g['goal']}" for g in pending[:5])
            streaks = self.data.get("streaks", {})
            if streaks:
                best = max(streaks.items(), key=lambda x: x[1])
                r += f"\n\n🔥 En İyi Seri: {best[0]} — {best[1]} gün!"
            coach_msg = self.ollama.chat(
                f"Günlük kontrol: {len(completed)}/{len(goals)} hedef tamamlandı. "
                f"Motive edici kısa mesaj ver.",
                system_override="Kişisel koç. 1-2 cümle motivasyon.")
            r += f"\n\n💪 {coach_msg}"
            self.msg("ANKA", r)
            self.speak(f"{len(completed)} hedef tamamlandı efendim!")
        threading.Thread(target=_check, daemon=True).start()

    def get_coaching_advice(self, problem):
        def _advice():
            r = self.ollama.chat(
                f"Problem: {problem}\nKişisel koçluk tavsiyesi ver. Somut adımlar.",
                system_override="Deneyimli kişisel koç. Pratik tavsiyeler ver.")
            self.msg("ANKA", f"💪 Koçluk Tavsiyesi:\n{r}")
            self.speak(r[:200])
        threading.Thread(target=_advice, daemon=True).start()


# ── 9. OTOMATİK RAPOR ÜRETICI ────────────────────────────────────────────────
class AutoReportGenerator:
    def __init__(self, ollama, speak_func, msg_func):
        self.ollama = ollama
        self.speak = speak_func
        self.msg = msg_func

    def generate_daily(self):
        def _gen():
            now = datetime.datetime.now()
            cpu = psutil.cpu_percent(interval=1)
            ram = psutil.virtual_memory().percent
            disk = psutil.disk_usage('/').percent
            try:
                r2 = requests.get("https://wttr.in/Istanbul?format=j1", timeout=3)
                d = r2.json()["current_condition"][0]
                weather = f"{d['temp_C']}°C {d['weatherDesc'][0]['value']}"
            except: weather = "bilinmiyor"
            try:
                r3 = requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=3)
                usd = r3.json()["rates"]["TRY"]
                currency = f"1 USD = {usd:.2f}₺"
            except: currency = "bilinmiyor"
            report = (
                f"📊 ANKA GÜNLÜK RAPOR\n"
                f"{'═'*35}\n"
                f"📅 {now.strftime('%d %B %Y, %H:%M')}\n"
                f"{'─'*35}\n"
                f"🌤 Hava: {weather}\n"
                f"💱 Döviz: {currency}\n"
                f"{'─'*35}\n"
                f"💻 Sistem:\n"
                f"  CPU: %{cpu:.0f} | RAM: %{ram:.0f} | Disk: %{disk:.0f}\n"
                f"{'─'*35}\n"
                f"💡 Günün Sözü:\n"
                f"  {random.choice(['Başarı hazırlıkla buluştuğunda gelir.','Her gün yeni bir fırsat.','Küçük adımlar büyük yolculuklar yapar.','Kendinize inanın!'])}\n"
                f"{'═'*35}"
            )
            self.msg("ANKA", report)
            self.speak("Günlük rapor hazırlandı efendim.")
            try:
                requests.post("https://ntfy.sh/anka-yusuf-2026",
                    data=report[:500].encode(),
                    headers={"Title":"📊 ANKA Günlük Rapor"}, timeout=3)
            except: pass
        threading.Thread(target=_gen, daemon=True).start()

    def generate_performance_report(self):
        def _perf():
            procs = sorted(
                [(p.info['name'], p.info['memory_info'].rss//1024//1024)
                 for p in psutil.process_iter(['name','memory_info'])
                 if p.info.get('memory_info')],
                key=lambda x: -x[1])[:5]
            report = f"⚡ PERFORMANS RAPORU\n{'═'*30}\n"
            report += "En Çok RAM Kullananlar:\n"
            for name, mem in procs:
                report += f"  • {name[:20]}: {mem}MB\n"
            net = psutil.net_io_counters()
            report += f"\n🌐 Ağ:\n  ↓{net.bytes_recv//1024//1024}MB ↑{net.bytes_sent//1024//1024}MB"
            self.msg("ANKA", report)
        threading.Thread(target=_perf, daemon=True).start()


# ── 10. ANKA ASISTAN KİŞİLİĞİ — Konuşma tarzı değiştir ─────────────────────
# ── KOMUT İŞLEYİCİ ───────────────────────────────────────────────────────────
class JarvisCommandProcessor:
    def __init__(self, speak_func, msg_func, ollama):
        self.speak = speak_func
        self.msg = msg_func
        self.ollama = ollama
        self.time_machine  = TimeMachine(speak_func, msg_func)
        self.diary         = AnkaDiary(ollama, speak_func, msg_func)
        self.voice_profile = VoiceProfileManager(speak_func, msg_func)
        self.agenda        = SmartAgenda(ollama, speak_func, msg_func)
        self.code_vault    = CodeVault(speak_func, msg_func)
        self.price_tracker = LivePriceTracker(speak_func, msg_func)
        self.file_assistant= SmartFileAssistant(ollama, speak_func, msg_func)
        self.coach         = PersonalCoach(ollama, speak_func, msg_func)
        self.reporter      = AutoReportGenerator(ollama, speak_func, msg_func)

    def process(self, text):
        t = text.lower().strip()

        # ── Zaman Makinesi ────────────────────────────────────────────────────
        if "geçmiş konuşma" in t or "dün ne konuştuk" in t:
            m = re.search(r'(\d+)', t)
            days = int(m.group(1)) if m else 1
            self.time_machine.replay_day(days); return True

        if "geçmişte ara" in t or "konuşmada ara" in t:
            kw = t.replace("geçmişte ara","").replace("konuşmada ara","").strip()
            if kw: self.time_machine.search_history(kw); return True

        # ── Günlük ────────────────────────────────────────────────────────────
        if "günlük yaz" in t or "günlüğe ekle" in t:
            note = t.replace("günlük yaz","").replace("günlüğe ekle","").strip()
            self.diary.write_entry(note); return True

        if "günlüğümü oku" in t or "günlük oku" in t:
            m = re.search(r'(\d+)', t)
            days = int(m.group(1)) if m else 7
            self.diary.read_entries(days); return True

        if "haftalık günlük özeti" in t:
            self.diary.generate_weekly_summary(); return True

        # ── Akıllı Ajanda ─────────────────────────────────────────────────────
        if "akıllı ajanda ekle" in t:
            parts = t.replace("akıllı ajanda ekle","").strip().split(",")
            if len(parts) >= 2:
                title = parts[0].strip()
                dur_m = re.search(r'(\d+)', parts[1] if len(parts)>1 else "30")
                duration = int(dur_m.group(1)) if dur_m else 30
                deadline = parts[2].strip() if len(parts)>2 else datetime.date.today().isoformat()
                self.agenda.add_smart(title, duration, deadline)
            return True

        if "ajandayı optimize et" in t or "programı optimize et" in t:
            self.agenda.optimize_schedule(); return True

        if "ajanda çakışma" in t or "çakışma kontrol" in t:
            self.agenda.conflict_check(); return True

        # ── Kod Kasası ────────────────────────────────────────────────────────
        if "kod kaydet" in t or "kodu kasaya ekle" in t:
            parts = t.replace("kod kaydet","").replace("kodu kasaya ekle","").strip().split(":")
            if len(parts) >= 2:
                self.code_vault.save_code(parts[0].strip(), parts[1].strip())
            return True

        if "kodu getir" in t or "kod kasasından al" in t:
            name = t.replace("kodu getir","").replace("kod kasasından al","").strip()
            if name: self.code_vault.get_code(name); return True

        if "kod kasası" in t or "kayıtlı kodlar" in t:
            self.code_vault.list_codes(); return True

        if "kodda ara" in t:
            kw = t.replace("kodda ara","").strip()
            if kw: self.code_vault.search_code(kw); return True

        # ── Fiyat Takibi ──────────────────────────────────────────────────────
        if "fiyat alarmı kur" in t or "fiyat alarm" in t:
            m_asset = re.search(r'(btc|eth|usd|eur|bitcoin|ethereum)', t)
            m_price = re.search(r'(\d+(?:\.\d+)?)', t)
            if m_asset and m_price:
                asset = m_asset.group(1)
                price = float(m_price.group(1))
                direction = "below" if "altına" in t or "düşünce" in t else "above"
                self.price_tracker.add_alert(asset, price, direction)
            return True

        if "fiyat alarmları" in t or "aktif alarmlar" in t:
            self.price_tracker.list_alerts(); return True

        # ── Dosya Asistanı ────────────────────────────────────────────────────
        if "klasörü analiz et" in t:
            path = t.replace("klasörü analiz et","").strip()
            if not path: path = os.path.join(os.path.expanduser("~"), "Desktop")
            self.file_assistant.analyze_folder(path); return True

        # ── Kişisel Koç ───────────────────────────────────────────────────────
        if "günlük hedef ekle" in t:
            goal = t.replace("günlük hedef ekle","").strip()
            if goal: self.coach.set_daily_goal(goal); return True

        if "hedefi tamamladım" in t or "hedef bitti" in t:
            goal = t.replace("hedefi tamamladım","").replace("hedef bitti","").strip()
            if goal: self.coach.complete_goal(goal); return True

        if "günlük kontrol" in t or "hedeflerim nasıl" in t:
            self.coach.daily_checkin(); return True

        if "koçluk ver" in t or "tavsiye ver" in t:
            problem = t.replace("koçluk ver","").replace("tavsiye ver","").strip()
            if problem: self.coach.get_coaching_advice(problem); return True

        # ── Rapor Üretici ─────────────────────────────────────────────────────
        if "günlük rapor üret" in t or "rapor oluştur" in t:
            self.reporter.generate_daily(); return True

        if "performans raporu" in t:
            self.reporter.generate_performance_report(); return True

            available = ", ".join(self.personality.MODES.keys())
            self.msg("ANKA", f"Mevcut modlar: {available}")
            return True


        # ── Nasılsın sorusuna akıllı cevap ───────────────────────────────────
        if t in ["nasılsın","nasılsın anka","iyi misin","ne haber"]:
            cpu = psutil.cpu_percent(interval=1)
            score = max(0, 100 - cpu)
            emoji = "😊" if score > 70 else "😐" if score > 40 else "😓"
            r = f"{emoji} Sistem skorum {score:.0f}/100 efendim! CPU %{cpu:.0f}. Size nasıl yardımcı olabilirim?"
            self.msg("ANKA", r); self.speak(r)
            return True

        # ── Merhaba ───────────────────────────────────────────────────────────
        if t in ["merhaba","selam","hey","merhaba anka"]:
            hour = datetime.datetime.now().hour
            greeting = "Günaydın" if hour < 12 else "İyi öğleler" if hour < 18 else "İyi akşamlar"
            try:
                r2 = requests.get("https://wttr.in/Istanbul?format=j1", timeout=3)
                temp = r2.json()["current_condition"][0]["temp_C"]
                weather = f" Hava {temp}°C."
            except: weather = ""
            r = f"{greeting} efendim!{weather} Sistemler hazır, emrinizdeyim."
            self.msg("ANKA", r); self.speak(r)
            return True

        return False
