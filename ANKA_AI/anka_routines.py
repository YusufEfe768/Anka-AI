# ── ANKA RUTİN & AKILLI OTOMASYON MODÜLü ─────────────────────────────────────
try:
    import pyautogui
except ImportError:
    pyautogui=None
import json, os, time, threading, datetime, subprocess, random
import psutil, requests
from anka_config import BASE_DIR

ROUTINE_FILE  = os.path.join(BASE_DIR, "anka_routines.json")
HABIT_FILE    = os.path.join(BASE_DIR, "anka_habits.json")
MOOD_FILE     = os.path.join(BASE_DIR, "anka_mood.json")
SCREEN_FILE   = os.path.join(BASE_DIR, "anka_screen_time.json")

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


# ── Alışkanlık Takibi ─────────────────────────────────────────────────────────
class HabitTracker:
    HABITS = {
        "su": "💧 Su İçme",
        "egzersiz": "🏃 Egzersiz",
        "kitap": "📚 Kitap Okuma",
        "meditasyon": "🧘 Meditasyon",
        "vitamin": "💊 Vitamin",
    }

    def check_in(self, habit):
        data = _load(HABIT_FILE, {})
        today = datetime.date.today().isoformat()
        if today not in data: data[today] = {}
        data[today][habit] = data[today].get(habit, 0) + 1
        _save(HABIT_FILE, data)
        return data[today][habit]

    def get_today(self):
        data = _load(HABIT_FILE, {})
        today = datetime.date.today().isoformat()
        return data.get(today, {})

    def get_streak(self, habit):
        data = _load(HABIT_FILE, {})
        streak = 0
        day = datetime.date.today()
        while True:
            d = day.isoformat()
            if d in data and habit in data[d]:
                streak += 1
                day -= datetime.timedelta(days=1)
            else:
                break
        return streak

    def weekly_report(self):
        data = _load(HABIT_FILE, {})
        report = {}
        for i in range(7):
            day = (datetime.date.today() - datetime.timedelta(days=i)).isoformat()
            report[day] = data.get(day, {})
        return report


# ── Ruh Hali Takibi ───────────────────────────────────────────────────────────
MOOD_MUSIC = {
    "mutlu":   "https://youtube.com/results?search_query=happy+upbeat+music",
    "üzgün":   "https://youtube.com/results?search_query=sad+relaxing+music",
    "enerjik": "https://youtube.com/results?search_query=energetic+workout+music",
    "sakin":   "https://youtube.com/results?search_query=calm+lofi+music",
    "odakli":  "https://youtube.com/results?search_query=focus+study+music+lofi",
    "stresli": "https://youtube.com/results?search_query=stress+relief+music",
}

def log_mood(mood, note=""):
    data = _load(MOOD_FILE, [])
    data.append({
        "mood": mood,
        "note": note,
        "time": datetime.datetime.now().isoformat()
    })
    if len(data) > 100: data = data[-100:]
    _save(MOOD_FILE, data)

def get_mood_music(mood):
    return MOOD_MUSIC.get(mood.lower(), MOOD_MUSIC["sakin"])

def get_mood_history(days=7):
    data = _load(MOOD_FILE, [])
    cutoff = (datetime.date.today() - datetime.timedelta(days=days)).isoformat()
    return [m for m in data if m["time"] >= cutoff]


# ── Ekran Süresi Takibi ───────────────────────────────────────────────────────
class ScreenTimeTracker:
    def __init__(self, game_limit_hours=2):
        self.game_limit = game_limit_hours * 3600
        self.game_processes = ["steam.exe","epicgames.exe","roblox.exe",
                                "minecraft.exe","leagueclient.exe","valorant.exe",
                                "fortnite.exe","cs2.exe","dota2.exe"]
        self.running = True
        self.game_time_today = 0
        self.warned = False
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def _loop(self):
        data = _load(SCREEN_FILE, {})
        today = datetime.date.today().isoformat()
        if today not in data:
            data[today] = {"game": 0, "total": 0}
            self.game_time_today = 0
            self.warned = False
        else:
            self.game_time_today = data[today].get("game", 0)

        while self.running:
            try:
                running_procs = [p.name().lower() for p in psutil.process_iter(['name'])]
                is_gaming = any(g in running_procs for g in self.game_processes)
                if is_gaming:
                    self.game_time_today += 10
                    data[today]["game"] = self.game_time_today
                    _save(SCREEN_FILE, data)
                    if self.game_time_today >= self.game_limit and not self.warned:
                        self.warned = True
                        self._game_limit_warning()
            except: pass
            time.sleep(10)

    def _game_limit_warning(self):
        hours = self.game_limit // 3600
        self._speak_callback(f"Efendim, bugün {hours} saattir oyun oynuyorsunuz. Bir mola vermenizi öneririm.")

    def set_speak(self, fn):
        self._speak_callback = fn

    def get_today_game_time(self):
        return self.game_time_today // 60

    def stop(self): self.running = False


# ── Akıllı Rutinler ───────────────────────────────────────────────────────────
class SmartRoutineManager:
    def __init__(self, speak_func, msg_func, ollama):
        self.speak = speak_func
        self.msg = msg_func
        self.ollama = ollama
        self.running = True
        self.routines = _load(ROUTINE_FILE, self._default_routines())
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def _default_routines(self):
        return {
            "morning": {"hour": 8, "minute": 0, "enabled": True, "last_run": None},
            "evening": {"hour": 21, "minute": 0, "enabled": True, "last_run": None},
            "focus_reminder": {"interval_minutes": 90, "enabled": True},
        }

    def _loop(self):
        while self.running:
            try:
                now = datetime.datetime.now()
                today = now.strftime("%Y-%m-%d")

                # Sabah rutini
                morning = self.routines.get("morning", {})
                if (morning.get("enabled") and
                    now.hour == morning.get("hour", 8) and
                    now.minute == morning.get("minute", 0) and
                    morning.get("last_run") != today):
                    morning["last_run"] = today
                    _save(ROUTINE_FILE, self.routines)
                    threading.Thread(target=self._morning_routine, daemon=True).start()

                # Akşam rutini
                evening = self.routines.get("evening", {})
                if (evening.get("enabled") and
                    now.hour == evening.get("hour", 21) and
                    now.minute == evening.get("minute", 0) and
                    evening.get("last_run") != today):
                    evening["last_run"] = today
                    _save(ROUTINE_FILE, self.routines)
                    threading.Thread(target=self._evening_routine, daemon=True).start()

            except: pass
            time.sleep(15)

    def _morning_routine(self):
        time.sleep(1)
        try:
            r = requests.get("https://wttr.in/Istanbul?format=j1", timeout=5)
            d = r.json()["current_condition"][0]
            temp = d["temp_C"]; desc = d["weatherDesc"][0]["value"]
        except: temp="--"; desc="bilinmiyor"

        now = datetime.datetime.now()
        from anka_memory import get_pending_tasks, load_health
        tasks = get_pending_tasks()
        h = load_health()

        msg = (f"🌅 Günaydın efendim! Saat {now.strftime('%H:%M')}. "
               f"İstanbul'da hava {temp}°C, {desc}. "
               f"{len(tasks)} bekleyen göreviniz var. "
               f"Bugün {h.get('water_count',0)} bardak su içtiniz. "
               f"Harika bir gün olsun!")

        motivations = [
            "Bugün harika şeyler başaracaksınız!",
            "Her yeni gün yeni bir fırsat efendim.",
            "Bugün dün yapamadıklarınızı yapma günü!",
            "Kendinize inanın, her şey mümkün efendim.",
        ]
        msg += f"\n💪 {random.choice(motivations)}"
        self.msg("ANKA", msg)
        self.speak(msg[:300])

    def _evening_routine(self):
        time.sleep(1)
        from anka_memory import get_pending_tasks, load_health, get_daily_log
        tasks = get_pending_tasks()
        h = load_health()
        logs = get_daily_log()

        msg = (f"🌙 İyi akşamlar efendim! Günün özeti:\n"
               f"• {len(logs)} aktivite tamamlandı\n"
               f"• {h.get('water_count',0)}/{h.get('water_goal',8)} bardak su\n"
               f"• {len(tasks)} bekleyen görev\n"
               f"İyi geceler, dinlendirici bir uyku dilerim efendim!")

        self.msg("ANKA", msg)
        self.speak(msg[:300])

        # Gece sesi kıs
        import pyautogui
        pyautogui.press("volumedown", presses=8)

    def trigger_morning(self):
        threading.Thread(target=self._morning_routine, daemon=True).start()

    def trigger_evening(self):
        threading.Thread(target=self._evening_routine, daemon=True).start()

    def set_morning_time(self, hour, minute):
        self.routines["morning"]["hour"] = hour
        self.routines["morning"]["minute"] = minute
        _save(ROUTINE_FILE, self.routines)

    def set_evening_time(self, hour, minute):
        self.routines["evening"]["hour"] = hour
        self.routines["evening"]["minute"] = minute
        _save(ROUTINE_FILE, self.routines)

    def stop(self): self.running = False


# ── Mod Yöneticisi ────────────────────────────────────────────────────────────
class ModeManager:
    def __init__(self, speak_func, msg_func):
        self.speak = speak_func
        self.msg = msg_func
        self.current_mode = "normal"

    def set_mode(self, mode):
        import pyautogui, subprocess, webbrowser
        self.current_mode = mode

        if mode == "calisma":
            # Odaklanma modu
            pyautogui.press("volumedown", presses=3)
            webbrowser.open("https://youtube.com/results?search_query=lofi+study+music")
            r = "🎯 Çalışma modu aktif! Lofi müzik başlatıldı, başarılar efendim."
            self.msg("ANKA", r); self.speak(r)

        elif mode == "film":
            # Film modu
            try:
                subprocess.run(
                    ["powershell","-Command",
                     "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,30)"],
                    capture_output=True, timeout=5)
            except: pass
            pyautogui.press("volumeup", presses=5)
            r = "🎬 Film modu aktif! Parlaklık düşürüldü, ses yükseltildi efendim."
            self.msg("ANKA", r); self.speak(r)

        elif mode == "uyku":
            # Uyku/gece modu
            try:
                subprocess.run(
                    ["powershell","-Command",
                     "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,10)"],
                    capture_output=True, timeout=5)
            except: pass
            pyautogui.press("volumedown", presses=10)
            r = "🌙 Gece modu aktif! Parlaklık ve ses kısıldı. İyi geceler efendim."
            self.msg("ANKA", r); self.speak(r)

        elif mode == "oyun":
            # Oyun modu
            pyautogui.press("volumeup", presses=5)
            try:
                subprocess.run(
                    ["powershell","-Command",
                     "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,100)"],
                    capture_output=True, timeout=5)
            except: pass
            r = "🎮 Oyun modu aktif! Ses ve parlaklık maksimuma alındı efendim."
            self.msg("ANKA", r); self.speak(r)

        elif mode == "normal":
            try:
                subprocess.run(
                    ["powershell","-Command",
                     "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,70)"],
                    capture_output=True, timeout=5)
            except: pass
            r = "✓ Normal moda dönüldü efendim."
            self.msg("ANKA", r); self.speak(r)

        elif mode == "eve_geldim":
            webbrowser.open("https://youtube.com/results?search_query=relaxing+home+music")
            r = "🏠 Hoş geldiniz efendim! Rahatlatıcı müzik başlatıldı."
            self.msg("ANKA", r); self.speak(r)


# ── Komut İşleyici ────────────────────────────────────────────────────────────
class RoutineCommandProcessor:
    def __init__(self, speak_func, msg_func, ollama,
                 routine_mgr=None, mode_mgr=None,
                 habit_tracker=None, screen_tracker=None):
        self.speak = speak_func
        self.msg = msg_func
        self.ollama = ollama
        self.routine_mgr = routine_mgr
        self.mode_mgr = mode_mgr
        self.habits = habit_tracker
        self.screen = screen_tracker

    def process(self, text):
        t = text.lower().strip()
        import re, webbrowser

        # ── Modlar ───────────────────────────────────────────────────────────
        mode_map = {
            "çalışma moduna": "calisma",
            "odaklanma moduna": "calisma",
            "film moduna": "film",
            "dizi moduna": "film",
            "uyku moduna": "uyku",
            "gece moduna": "uyku",
            "oyun moduna": "oyun",
            "normal moda": "normal",
            "eve geldim": "eve_geldim",
            "eve döndüm": "eve_geldim",
        }
        for phrase, mode in mode_map.items():
            if phrase in t and self.mode_mgr:
                self.mode_mgr.set_mode(mode)
                return True

        # ── Sabah Rutini Manuel ───────────────────────────────────────────────
        if "sabah rutini" in t or "günaydın rutini" in t:
            if self.routine_mgr:
                self.routine_mgr.trigger_morning()
            return True

        # ── Akşam Rutini Manuel ───────────────────────────────────────────────
        if "akşam rutini" in t or "gece rutini" in t:
            if self.routine_mgr:
                self.routine_mgr.trigger_evening()
            return True

        # ── Rutin Saati Ayarla ────────────────────────────────────────────────
        if "sabah rutinini" in t and "ayarla" in t:
            m = re.search(r'(\d{1,2})[:\.](\d{2})', t)
            if m and self.routine_mgr:
                h, mn = int(m.group(1)), int(m.group(2))
                self.routine_mgr.set_morning_time(h, mn)
                r = f"✓ Sabah rutini saat {h}:{mn:02d}'e ayarlandı efendim."
                self.msg("ANKA", r); self.speak(r)
            return True

        # ── Ruh Hali ─────────────────────────────────────────────────────────
        mood_keywords = {
            "mutluyum": "mutlu", "çok iyiyim": "mutlu", "harikayım": "mutlu",
            "üzgünüm": "üzgün", "moralim bozuk": "üzgün", "kötü hissediyorum": "üzgün",
            "enerjik": "enerjik", "hareketliyim": "enerjik",
            "sakinim": "sakin", "dinlenmek istiyorum": "sakin",
            "odaklanmak": "odakli", "çalışmak istiyorum": "odakli",
            "stresli": "stresli", "gerginim": "stresli",
        }
        for kw, mood in mood_keywords.items():
            if kw in t:
                log_mood(mood, text)
                music_url = get_mood_music(mood)
                r = f"Ruh halinizi anladım efendim. Size uygun müzik açılıyor..."
                self.msg("ANKA", r)
                webbrowser.open(music_url)
                reply = self.ollama.chat(
                    f"Kullanıcı '{mood}' hissediyor. Kısa, destekleyici bir mesaj yaz.")
                self.msg("ANKA", reply); self.speak(reply)
                return True

        # ── Ruh Hali Müzik ───────────────────────────────────────────────────
        if "ruh halime göre müzik" in t or "mod müziği" in t:
            moods = get_mood_history(1)
            mood = moods[-1]["mood"] if moods else "sakin"
            url = get_mood_music(mood)
            webbrowser.open(url)
            r = f"🎵 {mood.capitalize()} ruh halinize göre müzik açıldı efendim."
            self.msg("ANKA", r); self.speak(r)
            return True

        # ── Alışkanlık Check-in ───────────────────────────────────────────────
        habit_map = {
            "su içtim": "su", "su içtim": "su",
            "egzersiz yaptım": "egzersiz", "spor yaptım": "egzersiz",
            "kitap okudum": "kitap",
            "meditasyon yaptım": "meditasyon",
            "vitamin aldım": "vitamin", "vitamin içtim": "vitamin",
        }
        for kw, habit in habit_map.items():
            if kw in t and self.habits:
                count = self.habits.check_in(habit)
                streak = self.habits.get_streak(habit)
                r = f"✓ {HabitTracker.HABITS.get(habit, habit)} kaydedildi! "
                r += f"Bugün {count}. kez. "
                if streak > 1: r += f"🔥 {streak} günlük seri!"
                self.msg("ANKA", r); self.speak(r)
                return True

        # ── Alışkanlık Raporu ────────────────────────────────────────────────
        if "alışkanlıklar" in t or "alışkanlık raporu" in t:
            if self.habits:
                today = self.habits.get_today()
                if not today:
                    r = "Bugün henüz hiç alışkanlık kaydı yok efendim."
                else:
                    items = "\n".join(
                        f"• {HabitTracker.HABITS.get(h,h)}: {c} kez"
                        for h, c in today.items())
                    r = f"📊 Bugünkü alışkanlıklarınız:\n{items}"
                self.msg("ANKA", r); self.speak(r)
            return True

        # ── Oyun Süresi ──────────────────────────────────────────────────────
        if "oyun süresi" in t or "ne kadar oynadım" in t:
            if self.screen:
                mins = self.screen.get_today_game_time()
                r = f"🎮 Bugün toplam {mins} dakika oyun oynadınız efendim."
                self.msg("ANKA", r); self.speak(r)
            return True

        # ── Haftalık Rapor ───────────────────────────────────────────────────
        if "haftalık rapor" in t or "bu hafta ne yaptım" in t:
            threading.Thread(target=self._weekly_report, daemon=True).start()
            return True

        # ── Odaklanma Modu ───────────────────────────────────────────────────
        if "odaklan" in t and "mod" in t or "focus mod" in t:
            if self.mode_mgr:
                self.mode_mgr.set_mode("calisma")
            return True

        # ── Çalışma Müziği ───────────────────────────────────────────────────
        if "lofi" in t or "çalışma müziği" in t or "odak müziği" in t:
            import webbrowser
            webbrowser.open("https://youtube.com/results?search_query=lofi+hip+hop+study+music")
            r = "🎵 Lofi çalışma müziği başlatıldı efendim."
            self.msg("ANKA", r); self.speak(r)
            return True

        # ── Haftalık Alışkanlık ───────────────────────────────────────────────
        if "haftalık alışkanlık" in t:
            if self.habits:
                report = self.habits.weekly_report()
                lines = []
                for day, habits in sorted(report.items(), reverse=True):
                    if habits:
                        day_str = datetime.date.fromisoformat(day).strftime("%d %B")
                        habit_str = ", ".join(
                            f"{HabitTracker.HABITS.get(h,h)}" for h in habits.keys())
                        lines.append(f"• {day_str}: {habit_str}")
                r = "📅 Haftalık alışkanlık raporunuz:\n" + ("\n".join(lines) if lines else "Kayıt yok")
                self.msg("ANKA", r); self.speak("İşte haftalık raporunuz efendim.")
            return True

        return False

    def _weekly_report(self):
        from anka_memory import get_pending_tasks, load_health
        from anka_system_pro import ActivityTracker
        tasks = get_pending_tasks()
        h = load_health()

        report = (f"📊 Haftalık Özet:\n"
                  f"• Bekleyen görevler: {len(tasks)}\n"
                  f"• Bugün su: {h.get('water_count',0)}/{h.get('water_goal',8)} bardak\n")

        if self.habits:
            today_habits = self.habits.get_today()
            if today_habits:
                report += f"• Bugünkü alışkanlıklar: {len(today_habits)} tamamlandı\n"

        if self.screen:
            mins = self.screen.get_today_game_time()
            if mins > 0:
                report += f"• Bugünkü oyun süresi: {mins} dakika\n"

        # AI ile özet
        ai_summary = self.ollama.chat(
            "Kullanıcının haftasını değerlendir, kısa motivasyon ver. 2-3 cümle.")
        report += f"\n💬 {ai_summary}"

        self.msg("ANKA", report)
        self.speak("İşte haftalık raporunuz efendim.")
