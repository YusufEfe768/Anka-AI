# ── A.N.K.A — GELİŞMİŞ NÖRAL KONTROL AJANI ─────────────────────────────────
# Yusuf için özel olarak yapıldı
# Versiyon: 3.0 — 150+ Özellik

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
import customtkinter as ctk
import tkinter as tk
import threading, datetime, math, random, time, os, subprocess, json
import psutil, requests

from anka_config  import USER_NAME, BASE_DIR
from anka_memory  import (load_memory, save_memory, add_note, get_notes,
                           add_task, get_pending_tasks, log_event, load_health)
from anka_local_ai import LocalOllamaClient as OllamaClient
from anka_ai_core import AnkaAICore, get_ai_core
try:
    from anka_nlp import get_nlp
except Exception as _e:
    get_nlp = None
    print(f'[ANKA] NLP yüklenemedi: {_e}')
try:
    from anka_teach import get_teach
except Exception as _e:
    get_teach = None
    print(f'[ANKA] Öğretme sistemi yüklenemedi: {_e}')
try:
    from anka_site import get_site
except Exception as _e:
    get_site = None
    print(f'[ANKA] Site modülü yüklenemedi: {_e}')
try:
    from anka_knowledge_db import init_knowledge_base, search_knowledge
except Exception as _e:
    init_knowledge_base = None
    search_knowledge = None
    print(f'[ANKA] knowledge_db yüklenemedi: {_e}')
from anka_performance import PerformanceManager
from anka_wow import WowCommandProcessor
from anka_ultra2 import Ultra2CommandProcessor
from anka_genius import GeniusCommandProcessor as GeniusCmd
from anka_next import NextGenCommandProcessor
from anka_pro2 import Pro2CommandProcessor
from anka_smart import SmartCommandProcessor
from anka_social import SocialCommandProcessor
from anka_gesture import GestureCommandProcessor
from anka_v100 import V100CommandProcessor
from anka_v300 import V300CommandProcessor
from anka_call  import CallCommandProcessor
from anka_valorant import ValorantCommandProcessor
print("[ANKA] Local AI aktif — API key veya Ollama gerektirmez! 🚀")
from anka_voice   import VoiceRecorder, speak
from anka_commands import CommandProcessor
from anka_alarm   import AlarmManager, WaterReminder
from anka_security import recognize_face, verify_pin, is_authorized, register_face
from anka_location import LocationMonitor, handle_location_command, save_place, get_current_location
from anka_wakeword import WakeWordListener
from anka_system_pro import ClipboardMonitor, ActivityTracker, AutoLocker, SystemProCommands
from anka_advanced import (AdvancedCommandProcessor, AutomationScheduler,
                            AutoBackup, ScreenRecorder, send_phone_notification)
from anka_routines import (SmartRoutineManager, ModeManager, HabitTracker,
                            ScreenTimeTracker, RoutineCommandProcessor)
from anka_super import (SuperCommandProcessor, SleepTracker, CalorieTracker,
                         PriceAlertMonitor, EyeCareReminder, WeatherAlertMonitor)
from anka_mega import MegaCommandProcessor
from anka_ultimate import UltimateCommandProcessor
from anka_watch import WatchCommandProcessor, WatchNotificationManager, send_watch
from anka_school import SchoolCommandProcessor
from anka_ai_pro import AiProCommandProcessor, ProactiveAssistant, LongTermMemory
from anka_genius import GeniusCommandProcessor
from anka_ultra import UltraCommandProcessor
from anka_power import PowerCommandProcessor
from anka_lgs import LGSCommandProcessor
from anka_next import NextGenCommandProcessor
from anka_pro2 import Pro2CommandProcessor
from anka_smart import SmartCommandProcessor
from anka_social import SocialCommandProcessor
from anka_creative import CreativeCommandProcessor
from anka_science import ScienceCommandProcessor
from anka_lifestyle import LifestyleCommandProcessor
from anka_finance2 import Finance2CommandProcessor
from anka_assistant import AssistantCommandProcessor
from anka_gaming import GamingCommandProcessor
from anka_health2 import Health2CommandProcessor
from anka_sysctl import SysCtlCommandProcessor
from anka_fileops import FileOpsCommandProcessor
from anka_automation import AutomationCommandProcessor
from anka_devtools import DevToolsCommandProcessor
from anka_autonomous import AutonomousCommandProcessor, GoalTracker, TaskDecomposer
from anka_jarvis import JarvisCommandProcessor
from anka_jarvis_extra import JarvisExtraCommandProcessor
from anka_edith import EDITHAdvancedCommandProcessor
from anka_friday import FRIDAYCommandProcessor

# ── Renkler ──────────────────────────────────────────────────────────────────
THEMES = {
    "cyber": {
        "BG":"#030308","SURFACE":"#07070f","SURFACE2":"#0a0a14","SURFACE3":"#0d0d1a",
        "BORDER":"#1a1a3a","BORDER2":"#252550",
        "ACCENT":"#00ffff","ACCENT2":"#00cccc","ACCENT3":"#006666",
        "GREEN":"#00ff88","GREEN2":"#00cc66","ORANGE":"#ff6600",
        "YELLOW":"#ffcc00","RED":"#ff2244","WHITE":"#e0f0ff",
        "MUTED":"#2a2a50","MUTED2":"#4a4a80","name":"Cyber Teal"
    },
    "neon_purple": {
        "BG":"#05030a","SURFACE":"#08060f","SURFACE2":"#0b0814","SURFACE3":"#0e0b1a",
        "BORDER":"#1e1040","BORDER2":"#2a1555",
        "ACCENT":"#bf00ff","ACCENT2":"#9900cc","ACCENT3":"#550077",
        "GREEN":"#00ffaa","GREEN2":"#00cc88","ORANGE":"#ff8800",
        "YELLOW":"#ffdd00","RED":"#ff1133","WHITE":"#f0e0ff",
        "MUTED":"#2a1050","MUTED2":"#4a2080","name":"Neon Purple"
    },
    "iron_man": {
        "BG":"#080400","SURFACE":"#0f0800","SURFACE2":"#150c00","SURFACE3":"#1a1000",
        "BORDER":"#332200","BORDER2":"#443300",
        "ACCENT":"#ffaa00","ACCENT2":"#cc8800","ACCENT3":"#774400",
        "GREEN":"#44ff00","GREEN2":"#33cc00","ORANGE":"#ff6600",
        "YELLOW":"#ffdd00","RED":"#ff2200","WHITE":"#fff0d0",
        "MUTED":"#332200","MUTED2":"#665500","name":"Iron Man"
    },
    "matrix": {
        "BG":"#000500","SURFACE":"#000800","SURFACE2":"#000b00","SURFACE3":"#000f00",
        "BORDER":"#001800","BORDER2":"#002200",
        "ACCENT":"#00ff41","ACCENT2":"#00cc33","ACCENT3":"#006618",
        "GREEN":"#00ff41","GREEN2":"#00cc33","ORANGE":"#00dd22",
        "YELLOW":"#88ff00","RED":"#ff4400","WHITE":"#ccffcc",
        "MUTED":"#003300","MUTED2":"#005500","name":"Matrix"
    },
    "teal": {
        "BG":"#060810","SURFACE":"#0b0d18","SURFACE2":"#0f1220","SURFACE3":"#141828",
        "BORDER":"#1e2235","BORDER2":"#252d45",
        "ACCENT":"#00e5cc","ACCENT2":"#00b8a0","ACCENT3":"#007a6b",
        "GREEN":"#00e676","GREEN2":"#69f0ae","ORANGE":"#ffb300",
        "YELLOW":"#ffe57f","RED":"#ff5252","WHITE":"#e0f7fa",
        "MUTED":"#2a3550","MUTED2":"#4a5880","name":"Teal"
    },
    "blue": {
        "BG":"#060a10","SURFACE":"#0b1018","SURFACE2":"#0f1520","SURFACE3":"#141c28",
        "BORDER":"#1e2835","BORDER2":"#253245",
        "ACCENT":"#4fc3f7","ACCENT2":"#29b6f6","ACCENT3":"#0277bd",
        "GREEN":"#00e676","GREEN2":"#69f0ae","ORANGE":"#ffb300",
        "YELLOW":"#ffe57f","RED":"#ff5252","WHITE":"#e3f2fd",
        "MUTED":"#1a2840","MUTED2":"#3a5070","name":"Blue"
    },
}

current_theme = "teal"
C = THEMES[current_theme]

ctk.set_appearance_mode("dark")
if pyautogui:
    pyautogui.FAILSAFE = False

# ── Kilit Ekranı ─────────────────────────────────────────────────────────────
class LockScreen(ctk.CTkToplevel):
    def __init__(self, parent, on_unlock):
        super().__init__(parent)
        self.on_unlock = on_unlock
        self.title("A.N.K.A — Kimlik Doğrulama")
        self.geometry("500x400")
        self.configure(fg_color=C["BG"])
        self.resizable(False, False)
        self.grab_set()
        self._build()

    def _build(self):
        tk.Label(self, text="◈  A.N.K.A", font=("Courier New",24,"bold"),
                 bg=C["BG"], fg=C["ACCENT"]).pack(pady=(40,8))
        tk.Label(self, text="Kimlik Doğrulama Gerekli",
                 font=("Segoe UI",12), bg=C["BG"], fg=C["MUTED2"]).pack(pady=(0,30))

        self.status = tk.Label(self, text="", font=("Segoe UI",11),
                                bg=C["BG"], fg=C["YELLOW"])
        self.status.pack(pady=(0,16))

        ctk.CTkButton(self, text="👤  Yüz ile Giriş",
                      font=("Segoe UI",13,"bold"),
                      fg_color=C["ACCENT3"], hover_color=C["ACCENT2"],
                      height=46, corner_radius=10,
                      command=self._face_login).pack(padx=60, pady=6, fill="x")

        tk.Label(self, text="— veya PIN ile —",
                 font=("Segoe UI",9), bg=C["BG"], fg=C["MUTED"]).pack(pady=8)

        self.pin_var = ctk.StringVar()
        ctk.CTkEntry(self, textvariable=self.pin_var, placeholder_text="PIN kodunu gir",
                     font=("Courier New",14), show="●",
                     fg_color=C["SURFACE2"], text_color=C["WHITE"],
                     border_color=C["BORDER2"], height=42).pack(padx=60, pady=4, fill="x")

        ctk.CTkButton(self, text="🔑  PIN ile Giriş",
                      font=("Segoe UI",12),
                      fg_color=C["SURFACE2"], hover_color=C["SURFACE3"],
                      text_color=C["ACCENT"], border_color=C["BORDER2"], border_width=1,
                      height=40, corner_radius=10,
                      command=self._pin_login).pack(padx=60, pady=4, fill="x")

    def _face_login(self):
        self.status.configure(text="Kameraya bakın...", fg=C["YELLOW"])
        def _f():
            ok, name = recognize_face(timeout=10)
            if ok:
                self.after(0, lambda: self.status.configure(text=f"✓ Hoş geldiniz {name}!", fg=C["GREEN"]))
                self.after(500, self._unlock)
            else:
                self.after(0, lambda: self.status.configure(text="✗ Yüz tanınamadı. PIN deneyin.", fg=C["RED"]))
        threading.Thread(target=_f, daemon=True).start()

    def _pin_login(self):
        pin = self.pin_var.get()
        if verify_pin(pin):
            self.status.configure(text="✓ Giriş başarılı!", fg=C["GREEN"])
            self.after(400, self._unlock)
        else:
            self.status.configure(text="✗ Yanlış PIN!", fg=C["RED"])
            self.pin_var.set("")

    def _unlock(self):
        self.destroy()
        self.on_unlock()


# ── Ana Uygulama ──────────────────────────────────────────────────────────────
class AnkaApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("A.N.K.A — Yusuf Edition v3.0")
        self.geometry("1440x860")
        self.minsize(1200,700)
        self.configure(fg_color=C["BG"])

        # Ana AI motoru — Ollama, API key GEREKMİYOR!
        self.ollama = get_ai_core()  # AnkaAICore — tüm modüller bunu kullanır
        try:
            if init_knowledge_base: init_knowledge_base()
        except Exception as _e:
            print(f'[ANKA] bilgi tabanı başlatılamadı: {_e}')
        try:
            if get_teach:
                threading.Thread(target=lambda: get_teach().scan_folder(), daemon=True).start()
            if get_site:
                get_site().set_notifier(lambda m: self.after(0, lambda m=m: self._show("ANKA", m)))
        except Exception as _e:
            print(f'[ANKA] öğretim/site başlatılamadı: {_e}')
        self.voice    = VoiceRecorder()
        self.cmd_proc = None  # after build
        self.is_recording = False
        self.is_thinking  = False
        self.hw_mode      = False
        self.sleep_mode   = False
        self.last_reply   = ""
        self.angle  = 0
        self.pulse  = 0.0
        self.particles = [(random.uniform(0,360), random.uniform(10,105)) for _ in range(75)]
        self.wave   = [0]*32
        self.current_panel = "chat"

        self._build()
        self.cmd_proc = CommandProcessor(speak, self._msg, self.ollama)
        self.alarm_mgr = AlarmManager(speak, self._msg)
        self.water_rem = WaterReminder(speak, self._msg, interval_minutes=60)
        self.location_mon = LocationMonitor(speak, self._msg, check_interval=300)
        self.wake_listener = WakeWordListener(
            on_wake_callback=self._on_voice_detected,
            on_status_callback=lambda s: self.after(0, lambda: self.footer_msg.configure(text=s, fg=C["ACCENT"]))
        )
        self.clipboard_mon = ClipboardMonitor()
        self.activity_tracker = ActivityTracker()
        self.auto_locker = AutoLocker(timeout_minutes=15, enabled=False)
        self.sys_pro = SystemProCommands(speak, self._msg, self.ollama,
                                          self.clipboard_mon, self.activity_tracker, self.auto_locker)
        self.scheduler = AutomationScheduler(speak, self._msg)
        self.backup = AutoBackup(speak, self._msg)
        self.screen_recorder = ScreenRecorder()
        self.adv_cmd = AdvancedCommandProcessor(
            speak, self._msg, self.ollama,
            scheduler=self.scheduler,
            backup=self.backup,
            screen_recorder=self.screen_recorder,
            ntfy_topic="anka-yusuf-2026"
        )
        # Rutin & mod sistemi
        self.routine_mgr  = SmartRoutineManager(speak, self._msg, self.ollama)
        self.mode_mgr     = ModeManager(speak, self._msg)
        self.habit_tracker= HabitTracker()
        self.screen_time  = ScreenTimeTracker()
        self.screen_time.set_speak(speak)
        self.routine_cmd  = RoutineCommandProcessor(
            speak, self._msg, self.ollama,
            routine_mgr=self.routine_mgr, mode_mgr=self.mode_mgr,
            habit_tracker=self.habit_tracker, screen_tracker=self.screen_time
        )
        # Süper özellikler
        self.sleep_tracker  = SleepTracker()
        self.calorie_tracker= CalorieTracker()
        self.price_monitor  = PriceAlertMonitor(speak, self._msg)
        self.eye_care       = EyeCareReminder(speak, self._msg)
        self.weather_alert  = WeatherAlertMonitor(speak, self._msg)
        self.super_cmd      = SuperCommandProcessor(
            speak, self._msg, self.ollama,
            sleep_tracker=self.sleep_tracker,
            calorie_tracker=self.calorie_tracker,
            price_monitor=self.price_monitor
        )
        self.genius_cmd   = GeniusCommandProcessor(speak, self._msg, self.ollama)
        self.ultra_cmd2   = UltraCommandProcessor(speak, self._msg, self.ollama)
        self.power_cmd    = PowerCommandProcessor(speak, self._msg, self.ollama)
        self.lgs_cmd      = LGSCommandProcessor(speak, self._msg, self.ollama)
        self.next_cmd     = NextGenCommandProcessor(speak, self._msg, self.ollama)
        self.pro2_cmd     = Pro2CommandProcessor(speak, self._msg, self.ollama)
        self.smart_cmd    = SmartCommandProcessor(speak, self._msg, self.ollama)
        self.social_cmd   = SocialCommandProcessor(speak, self._msg, self.ollama)
        self.creative_cmd = CreativeCommandProcessor(speak, self._msg, self.ollama)
        self.science_cmd  = ScienceCommandProcessor(speak, self._msg, self.ollama)
        self.lifestyle_cmd= LifestyleCommandProcessor(speak, self._msg, self.ollama)
        self.finance2_cmd = Finance2CommandProcessor(speak, self._msg, self.ollama)
        self.assistant_cmd= AssistantCommandProcessor(speak, self._msg, self.ollama)
        self.gaming_cmd   = GamingCommandProcessor(speak, self._msg, self.ollama)
        self.health2_cmd  = Health2CommandProcessor(speak, self._msg, self.ollama)
        self.sysctl_cmd   = SysCtlCommandProcessor(speak, self._msg, self.ollama)
        self.fileops_cmd  = FileOpsCommandProcessor(speak, self._msg, self.ollama)
        self.auto_cmd     = AutomationCommandProcessor(speak, self._msg, self.ollama)
        self.devtools_cmd = DevToolsCommandProcessor(speak, self._msg, self.ollama)
        def _safe_init(name, fn):
            try: return fn()
            except Exception as e:
                print(f"[ANKA] {name} yüklenemedi: {e}"); return None

        self.wow_cmd     = _safe_init("wow",      lambda: WowCommandProcessor(speak, self._msg, self.ollama))
        self.ultra2_cmd  = _safe_init("ultra2",   lambda: Ultra2CommandProcessor(speak, self._msg, self.ollama))
        self.genius_cmd2 = _safe_init("genius",   lambda: GeniusCmd(speak, self._msg, self.ollama))
        self.next_cmd    = _safe_init("next",      lambda: NextGenCommandProcessor(speak, self._msg, self.ollama))
        self.pro2_cmd    = _safe_init("pro2",     lambda: Pro2CommandProcessor(speak, self._msg, self.ollama))
        self.smart_cmd   = _safe_init("smart",    lambda: SmartCommandProcessor(speak, self._msg, self.ollama))
        self.social_cmd  = _safe_init("social",   lambda: SocialCommandProcessor(speak, self._msg, self.ollama))
        self.gesture_cmd = _safe_init("gesture",  lambda: GestureCommandProcessor(speak, self._msg, self._send, self.ollama))
        self.v100_cmd    = _safe_init("v100",     lambda: V100CommandProcessor(speak, self._msg, self.ollama))
        self.v300_cmd    = _safe_init("v300",     lambda: V300CommandProcessor(speak, self._msg, self.ollama))
        self.call_cmd    = _safe_init("call",     lambda: CallCommandProcessor(speak, self._msg, self.ollama))
        self.val_cmd     = _safe_init("valorant", lambda: ValorantCommandProcessor(speak, self._msg, self.ollama))
        self.mega_cmd    = _safe_init("mega",     lambda: MegaCommandProcessor(speak, self._msg, self.ollama))
        self.perf_mgr         = _safe_init("perf",     lambda: PerformanceManager())
        self.goal_tracker     = _safe_init("goal",     lambda: GoalTracker(speak, self._msg))
        self.task_decomposer  = _safe_init("taskdec",  lambda: TaskDecomposer(self.ollama))
        self.jarvis_cmd       = _safe_init("jarvis",   lambda: JarvisCommandProcessor(speak, self._msg, self.ollama))
        self.jarvis_extra_cmd = _safe_init("jarvis+",  lambda: JarvisExtraCommandProcessor(speak, self._msg, self.ollama))
        self.edith_cmd        = _safe_init("edith",    lambda: EDITHAdvancedCommandProcessor(speak, self._msg, self.ollama))
        self.friday_cmd       = _safe_init("friday",   lambda: FRIDAYCommandProcessor(speak, self._msg, self.ollama))
        self.ultimate_cmd     = _safe_init("ultimate", lambda: UltimateCommandProcessor(speak, self._msg, self.ollama))
        self.autonomous_cmd   = _safe_init("autonomous", lambda: AutonomousCommandProcessor(speak, self._msg, self.ollama))
        threading.Thread(target=self._auto_start_gesture, daemon=True).start()
        self.watch_cmd      = WatchCommandProcessor(speak, self._msg, self.ollama)
        self.watch_mgr      = WatchNotificationManager(speak, self._msg)
        self.school_cmd     = SchoolCommandProcessor(speak, self._msg, self.ollama)
        # AI Pro - Vision, Web Arama, Kod Asistanı
        self.ai_pro_cmd = AiProCommandProcessor(
            speak, self._msg, self.ollama, api_key=""
        )
        self.proactive = ProactiveAssistant(speak, self._msg, self.ollama)
        self.long_memory = LongTermMemory(self.ollama)
        # Ses parmak izi kilitleme
        from anka_security import VoiceAuth, VoiceLockSystem
        self._voice_auth = VoiceAuth()
        self._voice_lock = VoiceLockSystem(
            self._voice_auth,
            lock_callback=lambda: self.after(0, self._lock)
        )
        self._loops()

        # Kilit ekranı
        self.after(200, self._show_lock)

    def _on_voice_detected(self, audio_data):
        if self.sleep_mode or self.is_recording: return
        if not self.voice.whisper_model: return
        # Ses parmak izi kontrolü
        if hasattr(self,'_voice_lock') and not self._voice_lock.check(audio_data.tolist()):
            return
        try:
            import tempfile, os as _os
            import scipy.io.wavfile as wavfile
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f: tmp=f.name
            wavfile.write(tmp, self.voice.sample_rate, audio_data)
            result = self.voice.whisper_model.transcribe(
                tmp, language="tr", condition_on_previous_text=False,
                no_speech_threshold=0.6, logprob_threshold=-1.0, temperature=0.0)
            _os.unlink(tmp)
            text = result["text"].strip()
            if text and len(text) > 3 and any(c.isalpha() for c in text):
                self.after(0, lambda: self._auto_send(text))
        except Exception as e:
            print(f"[ANKA] Voice detected hatası: {e}")

    def _auto_send(self, text):
        if self.sleep_mode or self.is_recording:
            return
        self.input_box.delete("1.0","end")
        self.input_box.configure(fg=C["WHITE"])
        self.input_box.insert("1.0", text)
        self._send()

    def _show_lock(self):
        LockScreen(self, self._on_unlock)

    def _on_unlock(self):
        self._morning_brief()

    def _morning_brief(self):
        try:
            r = requests.get("https://wttr.in/Istanbul?format=j1", timeout=4)
            d = r.json()["current_condition"][0]
            temp = d["temp_C"]; desc = d["weatherDesc"][0]["value"]
        except:
            temp="--"; desc="bilinmiyor"
        now = datetime.datetime.now()
        tasks = get_pending_tasks()
        h = load_health()
        msg = (f"Hoş geldiniz efendim. Saat {now.strftime('%H:%M')}, "
               f"{now.strftime('%d %B %Y')}. "
               f"İstanbul'da hava {temp}°C, {desc}. "
               f"{len(tasks)} bekleyen göreviniz var. "
               f"Anka sistemleri aktif, emrinizdeyim.")
        self._msg("ANKA", msg)
        speak(msg)
        log_event("startup", {"time": now.isoformat()})

    # ─────────────────────────────────────────────────────────────────────────
    def _build(self):
        self.grid_columnconfigure(0, weight=0, minsize=215)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0, minsize=290)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)

        # ══ HEADER ═══════════════════════════════════════════════════════════
        hdr = tk.Frame(self, bg=C["SURFACE"], height=50)
        hdr.grid(row=0, column=0, columnspan=3, sticky="ew")
        hdr.grid_propagate(False)
        hdr.columnconfigure(1, weight=1)

        lf = tk.Frame(hdr, bg=C["SURFACE"])
        lf.grid(row=0, column=0, padx=16, pady=10)
        tk.Label(lf, text="◈", font=("Segoe UI",20,"bold"), bg=C["SURFACE"], fg=C["ACCENT"]).pack(side="left", padx=(0,8))
        tk.Label(lf, text="A.N.K.A", font=("Courier New",15,"bold"), bg=C["SURFACE"], fg=C["WHITE"]).pack(side="left")

        tk.Label(hdr, text="GELİŞMİŞ NÖRAL KONTROL AJANI  ·  YUSUF EDİTİON  ·  v3.0",
                 font=("Segoe UI",8), bg=C["SURFACE"], fg=C["MUTED2"]).grid(row=0, column=1)

        rf = tk.Frame(hdr, bg=C["SURFACE"])
        rf.grid(row=0, column=2, padx=16)
        self.status_dot = tk.Label(rf, text="●", font=("Segoe UI",12), bg=C["SURFACE"], fg=C["GREEN"])
        self.status_dot.pack(side="left", padx=(0,5))
        self.status_lbl = tk.Label(rf, text="AKTİF", font=("Courier New",10,"bold"), bg=C["SURFACE"], fg=C["GREEN"])
        self.status_lbl.pack(side="left")

        # Tema butonu
        ctk.CTkButton(hdr, text="🎨", width=32, height=28, font=("Segoe UI",12),
                      fg_color=C["SURFACE2"], hover_color=C["BORDER2"],
                      command=self._cycle_theme).place(relx=1.0, x=-110, y=11)

        # Uyku modu
        ctk.CTkButton(hdr, text="🌙", width=32, height=28, font=("Segoe UI",12),
                      fg_color=C["SURFACE2"], hover_color=C["BORDER2"],
                      command=self._toggle_sleep).place(relx=1.0, x=-70, y=11)

        # Kilit
        ctk.CTkButton(hdr, text="🔒", width=32, height=28, font=("Segoe UI",12),
                      fg_color=C["SURFACE2"], hover_color=C["BORDER2"],
                      command=self._lock).place(relx=1.0, x=-30, y=11)

        # ══ SOL PANEL ════════════════════════════════════════════════════════
        left = tk.Frame(self, bg=C["SURFACE"], width=215)
        left.grid(row=1, column=0, sticky="nsew", padx=(6,3), pady=(4,6))
        left.grid_propagate(False)
        left.columnconfigure(0, weight=1)

        self._sec(left,"ZAMAN",0)
        self.time_lbl = tk.Label(left, text="00:00", font=("Courier New",32,"bold"), bg=C["SURFACE"], fg=C["ACCENT"])
        self.time_lbl.grid(row=1,column=0)
        self.sec_lbl = tk.Label(left, text=":00", font=("Courier New",13), bg=C["SURFACE"], fg=C["ACCENT2"])
        self.sec_lbl.grid(row=2,column=0)
        self.date_lbl = tk.Label(left, text="", font=("Segoe UI",9,"bold"), bg=C["SURFACE"], fg=C["ORANGE"])
        self.date_lbl.grid(row=3,column=0,pady=(2,0))
        self.day_lbl = tk.Label(left, text="", font=("Segoe UI",8), bg=C["SURFACE"], fg=C["MUTED2"])
        self.day_lbl.grid(row=4,column=0,pady=(0,4))

        self._div(left,5)
        self._sec(left,"HAVA — İSTANBUL",6)
        self.temp_lbl = tk.Label(left, text="--°C", font=("Courier New",26,"bold"), bg=C["SURFACE"], fg=C["ORANGE"])
        self.temp_lbl.grid(row=7,column=0,pady=(2,1))
        self.wdesc_lbl = tk.Label(left, text="...", font=("Segoe UI",9), bg=C["SURFACE"], fg=C["WHITE"])
        self.wdesc_lbl.grid(row=8,column=0)
        self.feels_lbl = tk.Label(left, text="", font=("Segoe UI",8), bg=C["SURFACE"], fg=C["MUTED2"])
        self.feels_lbl.grid(row=9,column=0)
        self.humid_lbl = tk.Label(left, text="", font=("Segoe UI",8), bg=C["SURFACE"], fg=C["MUTED2"])
        self.humid_lbl.grid(row=10,column=0,pady=(0,4))

        self._div(left,11)
        self._sec(left,"SİSTEM",12)
        self.cpu_bar  = self._pbar(left,"CPU", C["GREEN"], 13)
        self.ram_bar  = self._pbar(left,"RAM", C["ORANGE"],14)
        self.disk_bar = self._pbar(left,"DSK", C["ACCENT"],15)

        self._div(left,16)
        self._sec(left,"KİŞİLİK MODU",17)
        self.personality_var = ctk.StringVar(value="Profesyonel")
        ctk.CTkOptionMenu(left, values=["Profesyonel","Samimi","Komik"],
                          variable=self.personality_var,
                          fg_color=C["SURFACE2"], button_color=C["SURFACE3"],
                          button_hover_color=C["ACCENT3"], text_color=C["ACCENT"],
                          dropdown_fg_color=C["SURFACE2"], font=("Segoe UI",10),
                          command=self._chpersonality).grid(row=18,column=0,padx=10,pady=3,sticky="ew")

        self._sec(left,"MODEL",19)
        self.model_var = ctk.StringVar(value="llama3.2")
        ctk.CTkOptionMenu(left, values=["llama3.2","llama3","phi3"],
                          variable=self.model_var,
                          fg_color=C["SURFACE2"], button_color=C["SURFACE3"],
                          button_hover_color=C["ACCENT3"], text_color=C["ACCENT"],
                          dropdown_fg_color=C["SURFACE2"], font=("Courier New",10),
                          command=self._chmodel).grid(row=20,column=0,padx=10,pady=3,sticky="ew")

        ctk.CTkButton(left, text="🗑  Temizle", font=("Segoe UI",9), height=26,
                      fg_color=C["SURFACE2"], hover_color=C["SURFACE3"],
                      text_color=C["MUTED2"], border_color=C["BORDER"], border_width=1,
                      command=self._clearchat).grid(row=21,column=0,padx=10,pady=2,sticky="ew")

        self.whisper_lbl = tk.Label(left, text="⟳ Whisper...", font=("Segoe UI",7),
                                     bg=C["SURFACE"], fg=C["MUTED"])
        self.whisper_lbl.grid(row=22,column=0,padx=10,pady=(3,6),sticky="w")

        # ══ ORTA PANEL ═══════════════════════════════════════════════════════
        mid = tk.Frame(self, bg=C["BG"])
        mid.grid(row=1,column=1,sticky="nsew",padx=3,pady=(4,6))
        mid.rowconfigure(0,weight=0)
        mid.rowconfigure(1,weight=1)
        mid.columnconfigure(0,weight=1)

        # Canvas
        cv_wrap = tk.Frame(mid, bg=C["SURFACE"], height=215)
        cv_wrap.grid(row=0,column=0,sticky="ew")
        cv_wrap.grid_propagate(False)
        cv_wrap.columnconfigure(0,weight=1)
        cv_wrap.rowconfigure(0,weight=1)
        self.cv = tk.Canvas(cv_wrap, bg=C["BG"], highlightthickness=0)
        self.cv.grid(row=0,column=0,sticky="nsew",padx=1,pady=1)

        # Chat
        chat_wrap = tk.Frame(mid, bg=C["SURFACE"], padx=1, pady=1)
        chat_wrap.grid(row=1,column=0,sticky="nsew",pady=(4,0))
        chat_wrap.rowconfigure(0,weight=1)
        chat_wrap.columnconfigure(0,weight=1)
        chat_in = tk.Frame(chat_wrap, bg=C["SURFACE2"])
        chat_in.grid(row=0,column=0,sticky="nsew")
        chat_in.rowconfigure(0,weight=1)
        chat_in.columnconfigure(0,weight=1)

        self.chat_disp = tk.Text(chat_in, font=("Segoe UI",12), bg=C["SURFACE2"], fg=C["WHITE"],
                                  insertbackground=C["ACCENT"], relief="flat",
                                  padx=16, pady=12, wrap="word", state="disabled",
                                  selectbackground=C["ACCENT3"], spacing1=3, spacing3=3)
        self.chat_disp.grid(row=0,column=0,sticky="nsew")
        sb = tk.Scrollbar(chat_in, command=self.chat_disp.yview,
                          bg=C["SURFACE3"], troughcolor=C["SURFACE2"], width=6, bd=0)
        sb.grid(row=0,column=1,sticky="ns")
        self.chat_disp.configure(yscrollcommand=sb.set)

        self.chat_disp.tag_config("anka",  foreground=C["ACCENT"],  font=("Segoe UI",10,"bold"))
        self.chat_disp.tag_config("user",  foreground=C["YELLOW"],  font=("Segoe UI",10,"bold"))
        self.chat_disp.tag_config("hw",    foreground=C["GREEN"],   font=("Segoe UI",10,"bold"))
        self.chat_disp.tag_config("wa",    foreground="#25d366",    font=("Segoe UI",10,"bold"))
        self.chat_disp.tag_config("sys",   foreground=C["ORANGE"],  font=("Segoe UI",10,"bold"))
        self.chat_disp.tag_config("time",  foreground=C["MUTED2"],  font=("Segoe UI",8))
        self.chat_disp.tag_config("body",  foreground=C["WHITE"],   font=("Segoe UI",12),
                                   lmargin1=14, lmargin2=14, spacing1=2)

        # ══ SAĞ PANEL ════════════════════════════════════════════════════════
        right = tk.Frame(self, bg=C["SURFACE"], width=290)
        right.grid(row=1,column=2,sticky="nsew",padx=(3,6),pady=(4,6))
        right.grid_propagate(False)
        right.rowconfigure(3,weight=1)
        right.columnconfigure(0,weight=1)

        # Panel butonları
        pf = tk.Frame(right, bg=C["SURFACE"])
        pf.grid(row=0,column=0,sticky="ew",padx=8,pady=(10,6))
        pf.columnconfigure((0,1,2,3),weight=1)
        self.pb_chat = self._pbtn(pf,"💬",0,lambda:self._panel("chat"),"Sohbet")
        self.pb_hw   = self._pbtn(pf,"📚",1,lambda:self._panel("hw"),"Ödev")
        self.pb_wa   = self._pbtn(pf,"📱",2,lambda:self._panel("wa"),"WA")
        self.pb_sys  = self._pbtn(pf,"⚙️",3,lambda:self._panel("sys"),"Sistem")

        # Input
        inp_f = tk.Frame(right, bg=C["SURFACE"])
        inp_f.grid(row=1,column=0,sticky="ew",padx=8,pady=(0,6))
        inp_f.columnconfigure(0,weight=1)
        inp_b = tk.Frame(inp_f, bg=C["BORDER2"], padx=1, pady=1)
        inp_b.grid(row=0,column=0,sticky="ew")
        inp_b.columnconfigure(0,weight=1)
        self.input_box = tk.Text(inp_b, font=("Segoe UI",11), bg=C["SURFACE2"], fg=C["WHITE"],
                                  insertbackground=C["ACCENT"], relief="flat",
                                  padx=12, pady=10, wrap="word", height=4,
                                  selectbackground=C["ACCENT3"])
        self.input_box.grid(row=0,column=0,sticky="ew")
        self.input_box.insert("1.0","Bir şey yaz veya komut ver...")
        self.input_box.configure(fg=C["MUTED2"])
        self.input_box.bind("<FocusIn>",  lambda e: self._ph(True))
        self.input_box.bind("<FocusOut>", lambda e: self._ph(False))
        self.input_box.bind("<Return>", self._on_enter)

        # Butonlar
        bf = tk.Frame(right, bg=C["SURFACE"])
        bf.grid(row=2,column=0,sticky="ew",padx=8,pady=(0,6))
        bf.columnconfigure(0,weight=1)

        self.send_btn = ctk.CTkButton(bf, text="↗  Gönder",
                                       font=("Segoe UI",12,"bold"),
                                       fg_color=C["ACCENT3"], hover_color=C["ACCENT2"],
                                       text_color=C["WHITE"], height=40, corner_radius=8,
                                       command=self._send)
        self.send_btn.grid(row=0,column=0,columnspan=2,sticky="ew",pady=(0,5))

        self.voice_btn = ctk.CTkButton(bf, text="🎤  Ses Komutu",
                                        font=("Segoe UI",10),
                                        fg_color=C["SURFACE2"], hover_color=C["SURFACE3"],
                                        text_color=C["ACCENT"], height=34,
                                        border_color=C["BORDER2"], border_width=1, corner_radius=8,
                                        command=self._toggle_voice)
        self.voice_btn.grid(row=1,column=0,sticky="ew",padx=(0,4))
        ctk.CTkButton(bf, text="🔊", font=("Segoe UI",11), width=38, height=34,
                      fg_color=C["SURFACE2"], hover_color=C["SURFACE3"],
                      text_color=C["MUTED2"], border_color=C["BORDER2"], border_width=1,
                      corner_radius=8, command=self._repeat).grid(row=1,column=1,padx=(4,0))

        # Dinamik panel
        self.panel_frame = tk.Frame(right, bg=C["SURFACE"])
        self.panel_frame.grid(row=3,column=0,sticky="nsew",padx=8,pady=(0,6))
        self.panel_frame.columnconfigure(0,weight=1)
        self._build_panels()
        self._panel("chat")

        self.footer_msg = tk.Label(right, text="", font=("Segoe UI",8),
                                    bg=C["SURFACE"], fg=C["MUTED2"], wraplength=270, justify="left")
        self.footer_msg.grid(row=4,column=0,padx=10,pady=(0,8),sticky="w")

        # ══ ALT BAR ══════════════════════════════════════════════════════════
        foot = tk.Frame(self, bg=C["SURFACE"], height=26)
        foot.grid(row=2,column=0,columnspan=3,sticky="ew")
        foot.grid_propagate(False)
        foot.columnconfigure(1,weight=1)
        tk.Label(foot, text="A.N.K.A v3.0 © 2026", font=("Segoe UI",7),
                 bg=C["SURFACE"], fg=C["MUTED"]).grid(row=0,column=0,padx=14,pady=5)
        tk.Label(foot, text="Enter→gönder · Shift+Enter→yeni satır · Komutlar: 'chrome aç' 'alarm kur 08:00' 'haber oku' 'not al' 'dolar'",
                 font=("Segoe UI",7), bg=C["SURFACE"], fg=C["MUTED"]).grid(row=0,column=1)
        tk.Label(foot, text=f"Yusuf için ♥", font=("Segoe UI",7),
                 bg=C["SURFACE"], fg=C["MUTED"]).grid(row=0,column=2,padx=14,pady=5)

    def _build_panels(self):
        # Sohbet paneli
        self.chat_panel = tk.Frame(self.panel_frame, bg=C["SURFACE"])
        self.chat_panel.columnconfigure(0,weight=1)
        self._sec2(self.chat_panel,"HIZLI KOMUTLAR",0)
        quick = [
            ("🌐 Chrome","chrome aç"),("📺 YouTube","youtube aç"),
            ("📸 Ekran","ekran görüntüsü al"),("💱 Döviz","döviz kuru"),
            ("₿ Kripto","bitcoin fiyatı"),("📰 Haberler","haber oku"),
            ("💧 Su İçtim","su içtim"),("⏰ Pomodoro","pomodoro başlat"),
            ("🌤 Hava","hava durumu"),("🔐 Şifre Üret","şifre üret"),
            ("📝 Notlarım","notlarımı göster"),("📋 Görevler","görevlerim"),
            ("📍 Neredeyim","neredeyim"),
        ]
        for i,(lbl,cmd) in enumerate(quick):
            r,c = divmod(i,2)
            if c==0:
                fr=tk.Frame(self.chat_panel,bg=C["SURFACE"])
                fr.grid(row=r+1,column=0,sticky="ew",pady=1)
                fr.columnconfigure((0,1),weight=1)
            ctk.CTkButton(fr, text=lbl, font=("Segoe UI",9),
                          fg_color=C["SURFACE2"], hover_color=C["SURFACE3"],
                          text_color=C["ACCENT"], height=26, corner_radius=6,
                          border_color=C["BORDER"], border_width=1,
                          command=lambda c=cmd:self._quick(c)).grid(row=0,column=c,sticky="ew",padx=(0 if c else 0,2 if c==0 else 0))

        # Ödev paneli
        self.hw_panel = tk.Frame(self.panel_frame, bg=C["SURFACE"])
        self.hw_panel.columnconfigure(0,weight=1)
        self._sec2(self.hw_panel,"ÖDEV MODU",0)
        tk.Label(self.hw_panel, text="Soruyu yaz, Anka çözsün.\nFotoğraf da atabilirsin.",
                 font=("Segoe UI",9), bg=C["SURFACE"], fg=C["MUTED2"], justify="left").grid(row=1,column=0,sticky="w",pady=(0,6))
        self._sec2(self.hw_panel,"DERS",2)
        self.hw_sub = ctk.CTkOptionMenu(self.hw_panel,
                                         values=["Matematik","Fizik","Kimya","Biyoloji",
                                                 "Tarih","İngilizce","Türkçe","Geometri","Diğer"],
                                         fg_color=C["SURFACE2"], button_color=C["SURFACE3"],
                                         button_hover_color=C["ACCENT3"], text_color=C["WHITE"],
                                         font=("Segoe UI",10))
        self.hw_sub.grid(row=3,column=0,sticky="ew",pady=4)
        ctk.CTkButton(self.hw_panel, text="📚 Ödevi Çöz",
                      font=("Segoe UI",11,"bold"),
                      fg_color=C["ACCENT3"], hover_color=C["ACCENT2"],
                      height=36, command=self._solve_hw).grid(row=4,column=0,sticky="ew",pady=4)

        # WhatsApp paneli
        self.wa_panel = tk.Frame(self.panel_frame, bg=C["SURFACE"])
        self.wa_panel.columnconfigure(0,weight=1)
        self._sec2(self.wa_panel,"WHATSAPP",0)
        tk.Label(self.wa_panel, text="Kişi", font=("Segoe UI",8), bg=C["SURFACE"], fg=C["MUTED2"]).grid(row=1,column=0,sticky="w",pady=(4,1))
        self.wa_contact = ctk.CTkEntry(self.wa_panel, font=("Segoe UI",11),
                                        fg_color=C["SURFACE2"], text_color=C["GREEN"],
                                        border_color=C["BORDER2"], placeholder_text="İsim...", height=32)
        self.wa_contact.grid(row=2,column=0,sticky="ew",pady=(0,4))
        tk.Label(self.wa_panel, text="Mesaj", font=("Segoe UI",8), bg=C["SURFACE"], fg=C["MUTED2"]).grid(row=3,column=0,sticky="w",pady=(4,1))
        self.wa_msg = ctk.CTkEntry(self.wa_panel, font=("Segoe UI",11),
                                    fg_color=C["SURFACE2"], text_color=C["WHITE"],
                                    border_color=C["BORDER2"], placeholder_text="Mesaj...", height=32)
        self.wa_msg.grid(row=4,column=0,sticky="ew",pady=(0,8))
        wab = tk.Frame(self.wa_panel, bg=C["SURFACE"])
        wab.grid(row=5,column=0,sticky="ew")
        wab.columnconfigure((0,1),weight=1)
        ctk.CTkButton(wab, text="📤 Gönder", font=("Segoe UI",10,"bold"),
                      fg_color="#075e54", hover_color="#128c7e", height=34,
                      command=self._send_wa).grid(row=0,column=0,sticky="ew",padx=(0,3))
        ctk.CTkButton(wab, text="🤖 Anka Yazsın", font=("Segoe UI",9),
                      fg_color=C["SURFACE2"], hover_color=C["SURFACE3"],
                      text_color=C["ACCENT"], border_color=C["BORDER2"], border_width=1, height=34,
                      command=self._anka_wa).grid(row=0,column=1,padx=(3,0),sticky="ew")

        # Sistem paneli
        self.sys_panel = tk.Frame(self.panel_frame, bg=C["SURFACE"])
        self.sys_panel.columnconfigure(0,weight=1)
        self._sec2(self.sys_panel,"SİSTEM ARAÇLARI",0)
        sys_cmds=[
            ("💾 RAM Temizle","ram temizle"),("🧹 Disk Temizle","disk temizle"),
            ("📡 İnternet Hızı","internet hızı"),("📶 WiFi Şifresi","wifi şifresi"),
            ("🔋 Pil Durumu","pil durumu"),("💻 Sistem Durumu","sistem durumu"),
            ("🔒 Ekranı Kilitle","ekranı kilitle"),("🔄 Yeniden Başlat","yeniden başlat"),
        ]
        for i,(lbl,cmd) in enumerate(sys_cmds):
            ctk.CTkButton(self.sys_panel, text=lbl, font=("Segoe UI",9),
                          fg_color=C["SURFACE2"], hover_color=C["SURFACE3"],
                          text_color=C["ACCENT"], height=28, corner_radius=6,
                          border_color=C["BORDER"], border_width=1,
                          command=lambda c=cmd:self._quick(c)).grid(row=i+1,column=0,sticky="ew",pady=1)

        # Yüz kayıt butonu
        self._sec2(self.sys_panel,"GÜVENLİK",10)
        ctk.CTkButton(self.sys_panel, text="👤 Yüzümü Kaydet",
                      font=("Segoe UI",10),
                      fg_color=C["SURFACE2"], hover_color=C["SURFACE3"],
                      text_color=C["GREEN"], border_color=C["BORDER"], border_width=1, height=32,
                      command=self._register_face).grid(row=11,column=0,sticky="ew",pady=2)
        ctk.CTkButton(self.sys_panel, text="🎤 Sesimi Kaydet",
                      font=("Segoe UI",10),
                      fg_color=C["SURFACE2"], hover_color=C["SURFACE3"],
                      text_color=C["CYAN"] if "CYAN" in dir() else "#00e5cc",
                      border_color=C["BORDER"], border_width=1, height=32,
                      command=self._register_voice).grid(row=12,column=0,sticky="ew",pady=2)

        # Konum butonları
        self._sec2(self.sys_panel,"KONUM",12)
        ctk.CTkButton(self.sys_panel, text="📍 Neredeyim?",
                      font=("Segoe UI",9),
                      fg_color=C["SURFACE2"], hover_color=C["SURFACE3"],
                      text_color=C["ACCENT"], border_color=C["BORDER"], border_width=1, height=28,
                      command=lambda:self._quick("neredeyim")).grid(row=13,column=0,sticky="ew",pady=1)
        ctk.CTkButton(self.sys_panel, text="🏠 Burayı Ev Olarak Kaydet",
                      font=("Segoe UI",9),
                      fg_color=C["SURFACE2"], hover_color=C["SURFACE3"],
                      text_color=C["ACCENT"], border_color=C["BORDER"], border_width=1, height=28,
                      command=lambda:self._quick("burayı ev olarak kaydet")).grid(row=14,column=0,sticky="ew",pady=1)
        ctk.CTkButton(self.sys_panel, text="🏢 Burayı İş Olarak Kaydet",
                      font=("Segoe UI",9),
                      fg_color=C["SURFACE2"], hover_color=C["SURFACE3"],
                      text_color=C["ACCENT"], border_color=C["BORDER"], border_width=1, height=28,
                      command=lambda:self._quick("burayı iş olarak kaydet")).grid(row=15,column=0,sticky="ew",pady=1)

        # Cihaz kontrolü
        self._sec2(self.sys_panel,"CİHAZ KONTROLÜ",9)
        cihaz_cmds = [
            ("🎬 Karargahı Hazırla", "karargahı hazırla"),
            ("📺 Salon TV Aç/Kapat", "salon tv aç"),
            ("📺 Oda TV Aç/Kapat",   "oda tv aç"),
            ("🎮 PS5 Uyandir",        "ps5 aç"),
            ("📱 Tablet 2. Ekran",    "tablet ikinci ekran"),
            ("⌚ Watch Bildir",       "saate bildir"),
        ]
        for i,(lbl,cmd) in enumerate(cihaz_cmds):
            ctk.CTkButton(self.sys_panel, text=lbl, font=("Segoe UI",9),
                          fg_color=C["SURFACE2"], hover_color=C["SURFACE3"],
                          text_color=C["ORANGE"], height=26, corner_radius=6,
                          border_color=C["BORDER"], border_width=1,
                          command=lambda c=cmd:self._quick(c)).grid(
                row=9+i, column=0, sticky="ew", pady=1)

        # Pro araçlar
        self._sec2(self.sys_panel,"PRO ARAÇLAR",16)
        pro_cmds=[
            ("📋 Pano Geçmişi","panodaki son şeyler"),("📝 Hızlı Not","hızlı not"),
            ("📂 İndirilenleri Düzenle","indirilenleri düzenle"),("📊 Aktivite Raporu","en çok kullandığım uygulamalar"),
            ("🎨 Renk Paleti","renk paleti üret"),("🖨 Yazıcı Durumu","yazıcı durumu"),
            ("🪟 Pencereleri Küçült","pencereleri küçült"),
        ]
        for i,(lbl,cmd) in enumerate(pro_cmds):
            ctk.CTkButton(self.sys_panel, text=lbl, font=("Segoe UI",9),
                          fg_color=C["SURFACE2"], hover_color=C["SURFACE3"],
                          text_color=C["ACCENT"], height=28, corner_radius=6,
                          border_color=C["BORDER"], border_width=1,
                          command=lambda c=cmd:self._quick(c)).grid(row=17+i,column=0,sticky="ew",pady=1)

    # ── Yardımcılar ───────────────────────────────────────────────────────────
    def _sec(self, p, t, r):
        f=tk.Frame(p,bg=C["SURFACE"])
        f.grid(row=r,column=0,sticky="ew",padx=10,pady=(8,2))
        f.columnconfigure(1,weight=1)
        tk.Label(f,text=t,font=("Segoe UI",7,"bold"),bg=C["SURFACE"],fg=C["MUTED2"]).pack(side="left")
        tk.Frame(f,bg=C["BORDER"],height=1).pack(side="left",fill="x",expand=True,padx=(6,0))

    def _sec2(self, p, t, r):
        f=tk.Frame(p,bg=C["SURFACE"])
        f.grid(row=r,column=0,sticky="ew",pady=(0,4))
        f.columnconfigure(1,weight=1)
        tk.Label(f,text=t,font=("Segoe UI",7,"bold"),bg=C["SURFACE"],fg=C["MUTED2"]).pack(side="left")
        tk.Frame(f,bg=C["BORDER"],height=1).pack(side="left",fill="x",expand=True,padx=(6,0))

    def _div(self, p, r):
        tk.Frame(p,bg=C["BORDER"],height=1).grid(row=r,column=0,sticky="ew",padx=10,pady=3)

    def _pbar(self, p, lbl, color, r):
        f=tk.Frame(p,bg=C["SURFACE"])
        f.grid(row=r,column=0,padx=10,pady=1,sticky="ew")
        f.columnconfigure(1,weight=1)
        tk.Label(f,text=lbl,font=("Segoe UI",7),bg=C["SURFACE"],fg=C["MUTED2"],width=5,anchor="w").grid(row=0,column=0)
        bar=ctk.CTkProgressBar(f,height=4,progress_color=color,fg_color=C["BORDER"],corner_radius=2)
        bar.grid(row=0,column=1,padx=(3,3),sticky="ew"); bar.set(0)
        pct=tk.Label(f,text="0%",font=("Courier New",7),bg=C["SURFACE"],fg=color,width=5)
        pct.grid(row=0,column=2)
        return (bar,pct)

    def _pbtn(self, p, t, col, cmd, tip):
        btn=ctk.CTkButton(p,text=t,font=("Segoe UI",11),
                           fg_color=C["ACCENT3"] if col==0 else C["SURFACE3"],
                           hover_color=C["ACCENT3"],height=30,corner_radius=6,
                           command=cmd)
        btn.grid(row=0,column=col,padx=2,sticky="ew")
        return btn

    def _ph(self, focus):
        txt=self.input_box.get("1.0","end").strip()
        if focus and txt=="Bir şey yaz veya komut ver...":
            self.input_box.delete("1.0","end"); self.input_box.configure(fg=C["WHITE"])
        elif not focus and not txt:
            self.input_box.insert("1.0","Bir şey yaz veya komut ver...")
            self.input_box.configure(fg=C["MUTED2"])

    # ── Canvas ────────────────────────────────────────────────────────────────
    def _draw(self):
        c=self.cv
        c.delete("all")
        w=c.winfo_width() or 700; h=c.winfo_height() or 213
        cx,cy=w//2,h//2-4
        r=min(h//2-8,90)
        self.pulse=(self.pulse+0.04)%(2*math.pi)
        pr=r+4*math.sin(self.pulse)

        # ── Yıldız arka planı ────────────────────────────────────────────────
        if not hasattr(self,'_stars'):
            self._stars=[(random.randint(0,800),random.randint(0,220),random.random()) for _ in range(60)]
        for sx,sy,br in self._stars:
            if sx<w and sy<h:
                alpha=int(br*120)
                col=f"#{alpha:02x}{alpha:02x}{min(255,alpha+40):02x}"
                c.create_oval(sx-1,sy-1,sx+1,sy+1,fill=col,outline="")

        # ── Dış glow halkaları ───────────────────────────────────────────────
        for i in range(5,0,-1):
            rg=pr+14+i*10
            c.create_oval(cx-rg,cy-rg,cx+rg,cy+rg,
                          outline=C["ACCENT3"] if i>2 else C["MUTED"],width=1)

        c.create_oval(cx-pr,cy-pr,cx+pr,cy+pr,outline=C["ACCENT"],width=2)

        # ── Dönen dış noktalar ───────────────────────────────────────────────
        for i in range(48):
            a=math.radians(i*7.5+self.angle)
            x=cx+pr*math.cos(a); y=cy+pr*math.sin(a)
            if i%8==0:
                sz=5; col=C["ACCENT"]
                x2=cx+(pr-18)*math.cos(a); y2=cy+(pr-18)*math.sin(a)
                c.create_line(x,y,x2,y2,fill=C["ACCENT2"],width=1)
            elif i%4==0: sz=3; col=C["ACCENT2"]
            else: sz=1.5; col=C["MUTED"]
            c.create_oval(x-sz,y-sz,x+sz,y+sz,fill=col,outline="")

        # ── İç halka (ters dönen) ────────────────────────────────────────────
        r2=int(pr*0.65)
        c.create_oval(cx-r2,cy-r2,cx+r2,cy+r2,outline=C["BORDER2"],width=1)
        for i in range(24):
            a=math.radians(i*15-self.angle*0.8)
            x=cx+r2*math.cos(a); y=cy+r2*math.sin(a)
            sz=3 if i%6==0 else 1; col=C["ORANGE"] if i%6==0 else C["MUTED"]
            c.create_oval(x-sz,y-sz,x+sz,y+sz,fill=col,outline="")

        # ── Partiküller ──────────────────────────────────────────────────────
        r3=int(pr*0.44)
        for pa,prf in self.particles:
            a=math.radians(pa+self.angle*0.12)
            pr2=prf*r3/105
            x=cx+pr2*math.cos(a); y=cy+pr2*math.sin(a)
            col=C["GREEN"] if self.is_recording else (C["ACCENT"] if random.random()>0.5 else C["ACCENT3"])
            c.create_oval(x-1.5,y-1.5,x+1.5,y+1.5,fill=col,outline="")

        # ── Merkez yazı (glow efekti) ────────────────────────────────────────
        sc=C["RED"] if self.is_recording else (C["YELLOW"] if self.is_thinking else C["ACCENT"])
        st="● DİNLİYOR" if self.is_recording else ("◆ DÜŞÜNÜYOR" if self.is_thinking else "◇ BEKLİYOR")
        # Glow için arkaya büyük soluk yazı
        c.create_text(cx,cy-14,text="A.N.K.A",font=("Courier New",17,"bold"),fill=C["ACCENT3"],anchor="center")
        c.create_text(cx,cy-14,text="A.N.K.A",font=("Courier New",15,"bold"),fill=C["WHITE"],anchor="center")
        c.create_text(cx,cy+7,text=st,font=("Segoe UI",8,"bold"),fill=sc,anchor="center")
        if self.hw_mode:
            c.create_text(cx,cy+22,text="[ ÖDEV MODU ]",font=("Segoe UI",7),fill=C["YELLOW"],anchor="center")
        if self.sleep_mode:
            c.create_text(cx,cy+22,text="[ UYKU MODU ]",font=("Segoe UI",7),fill=C["MUTED2"],anchor="center")

        # ── Ses dalgası (kayıt sırasında) ────────────────────────────────────
        if self.is_recording:
            for i in range(32):
                self.wave[i]=max(2,self.wave[i]*0.6+random.randint(0,22)*0.4)
                x=cx-75+i*5; hh=self.wave[i]
                c.create_rectangle(x,cy+30,x+3,cy+30+hh,fill=C["GREEN"],outline="")

        # ── HUD köşe işaretleri ──────────────────────────────────────────────
        for ox,oy,dx,dy in [(-1,-1,1,1),(-1,1,1,-1),(1,-1,-1,1),(1,1,-1,-1)]:
            bx=cx+ox*(pr+22); by=cy+oy*(pr+22)
            c.create_line(bx,by,bx+dx*16,by,fill=C["ACCENT2"],width=1)
            c.create_line(bx,by,bx,by+dy*16,fill=C["ACCENT2"],width=1)

        # ── Saat ─────────────────────────────────────────────────────────────
        now=datetime.datetime.now()
        c.create_text(w-10,8,text=now.strftime("%H:%M:%S"),font=("Courier New",9),fill=C["ACCENT3"],anchor="ne")

        # ── Scan line efekti ─────────────────────────────────────────────────
        scan_y=int((time.time()*60)%h)
        c.create_line(0,scan_y,w,scan_y,fill=C["ACCENT3"],width=1)

        self.angle=(self.angle+1)%360
        self.particles=[((pa+random.uniform(-0.12,0.12))%360,pr2) for pa,pr2 in self.particles]

    # ── Döngüler ──────────────────────────────────────────────────────────────
    def _loops(self):
        self._ttick(); self._stick(); self._wtick(); self._anim(); self._wsp()

    def _anim(self): self._draw(); self.after(50,self._anim)

    def _auto_start_gesture(self):
        """Anka açılınca 5 saniye sonra gesture kontrolünü arka planda başlat"""
        import time as _time
        _time.sleep(5)
        try:
            if hasattr(self, 'gesture_cmd') and self.gesture_cmd:
                self.gesture_cmd.blink.start()
                _time.sleep(0.5)
                self.gesture_cmd.hand.start()
                self._msg("ANKA",
                    "👁️ Gesture kontrolü arka planda başladı!\n"
                    "• Göz kırpma + El hareketleri aktif\n"
                    "• Kamera ekranda görünmüyor")
        except Exception as e:
            pass  # Sessizce geç — kamera yoksa sorun değil

    def _ttick(self):
        n=datetime.datetime.now()
        self.time_lbl.configure(text=n.strftime("%H:%M"))
        self.sec_lbl.configure(text=n.strftime(":%S"))
        self.date_lbl.configure(text=n.strftime("%d %B %Y").upper())
        days=["PAZARTESİ","SALI","ÇARŞAMBA","PERŞEMBE","CUMA","CUMARTESİ","PAZAR"]
        self.day_lbl.configure(text=days[n.weekday()])
        self.after(1000,self._ttick)

    def _stick(self):
        cpu=psutil.cpu_percent(); ram=psutil.virtual_memory().percent; disk=psutil.disk_usage('/').percent
        self.cpu_bar[0].set(cpu/100); self.cpu_bar[1].configure(text=f"{int(cpu)}%")
        self.ram_bar[0].set(ram/100); self.ram_bar[1].configure(text=f"{int(ram)}%")
        self.disk_bar[0].set(disk/100); self.disk_bar[1].configure(text=f"{int(disk)}%")
        if ram > 88 and not getattr(self, '_ram_warned', False):
            self._msg("SİSTEM","⚠️ RAM kullanımı çok yüksek! %"+str(int(ram)))
            self._ram_warned = True
        elif ram < 80:
            self._ram_warned = False
        self.after(5000,self._stick)

    def _wtick(self):
        def f():
            try:
                r=requests.get("https://wttr.in/Istanbul?format=j1",timeout=5)
                d=r.json()["current_condition"][0]
                self.temp_lbl.configure(text=f"{d['temp_C']}°C")
                self.wdesc_lbl.configure(text=d["weatherDesc"][0]["value"])
                self.feels_lbl.configure(text=f"Hissedilen {d['FeelsLikeC']}°C")
                self.humid_lbl.configure(text=f"Nem %{d['humidity']}")
            except: pass
        threading.Thread(target=f,daemon=True).start()
        self.after(300000,self._wtick)

    def _wsp(self):
        if self.voice.ready:
            self.whisper_lbl.configure(text="✓ Whisper hazır",fg=C["GREEN"])
        else: self.after(2000,self._wsp)

    # ── Mesaj ─────────────────────────────────────────────────────────────────
    def _msg(self, sender, text):
        self.chat_disp.configure(state="normal")
        now=datetime.datetime.now().strftime("%H:%M")
        tags={"ANKA":"anka","SEN":"user","ÖDEV":"hw","WA":"wa","SİSTEM":"sys"}
        tag=tags.get(sender,"anka")
        self.chat_disp.insert("end",f"\n  {sender}  ","  "+tag+"  ")
        self.chat_disp.insert("end",f"  {now}\n","time")
        self.chat_disp.insert("end",f"{text}\n\n","body")
        self.chat_disp.tag_config(tag)
        self.chat_disp.configure(state="disabled")
        self.chat_disp.see("end")

    def _on_enter(self,e):
        if not(e.state&0x1): self._send(); return "break"

    def _send(self, text=None):
        if self.sleep_mode: return
        if text:
            # Gesture'dan gelen komut — direkt işle
            self.after(0, lambda: self._process_gesture_command(text))
            return
        text=self.input_box.get("1.0","end").strip()
        if not text or text=="Bir şey yaz veya komut ver...": return
        self.input_box.delete("1.0","end"); self.input_box.configure(fg=C["WHITE"])
        self._msg("SEN",text)
        # Uzun süreli hafızaya öğren
        if hasattr(self,'long_memory'):
            threading.Thread(target=lambda: self.long_memory.learn_from_conversation(text), daemon=True).start()
        self._process_text(text)

    def _process_gesture_command(self, text):
        """Gesture komutunu işle"""
        self._msg("SEN", f"[👁️ Jest] {text}")
        self._process_text(text)

    def _process_text(self, text):
        """Komut zinciri — klavyeden yazılan ve jestle gelen komutlar"""
        # Öğretme + Site sistemi (zincirden önce; oturum açıksa her şeyi onlar yakalar)
        for _getter in (get_teach, get_site):
            try:
                if _getter:
                    _r = _getter().handle(text)
                    if _r:
                        self.last_reply = _r
                        self._show("ANKA", _r)
                        return
            except Exception as _e:
                print(f"[ANKA] Ön işleyici hata: {_e}")
        # Komut zinciri
        if handle_location_command(text, speak, self._msg): return
        if self._cihaz_komut(text): return
        if self.smart_cmd      and self.smart_cmd.process(text):      return
        if self.lgs_cmd        and self.lgs_cmd.process(text):        return
        if self.next_cmd       and self.next_cmd.process(text):       return
        if self.pro2_cmd       and self.pro2_cmd.process(text):       return
        if self.genius_cmd     and self.genius_cmd.process(text):     return
        if self.ultra_cmd2     and self.ultra_cmd2.process(text):     return
        if self.power_cmd      and self.power_cmd.process(text):      return
        if self.social_cmd     and self.social_cmd.process(text):     return
        if self.creative_cmd   and self.creative_cmd.process(text):   return
        if self.science_cmd    and self.science_cmd.process(text):    return
        if self.lifestyle_cmd  and self.lifestyle_cmd.process(text):  return
        if self.finance2_cmd   and self.finance2_cmd.process(text):   return
        if self.assistant_cmd  and self.assistant_cmd.process(text):  return
        if self.gaming_cmd     and self.gaming_cmd.process(text):     return
        if self.health2_cmd    and self.health2_cmd.process(text):    return
        if self.sysctl_cmd     and self.sysctl_cmd.process(text):     return
        if self.fileops_cmd    and self.fileops_cmd.process(text):    return
        if self.auto_cmd       and self.auto_cmd.process(text):       return
        if self.devtools_cmd   and self.devtools_cmd.process(text):   return
        if self.jarvis_cmd       and self.jarvis_cmd.process(text):       return
        if self.jarvis_extra_cmd and self.jarvis_extra_cmd.process(text): return
        if self.edith_cmd        and self.edith_cmd.process(text):        return
        if self.friday_cmd       and self.friday_cmd.process(text):       return
        if self.smart_cmd      and self.smart_cmd.process(text):      return
        if self.social_cmd     and self.social_cmd.process(text):     return
        if self.wow_cmd        and self.wow_cmd.process(text):        return
        if self.ultra2_cmd     and self.ultra2_cmd.process(text):     return
        if self.genius_cmd2    and self.genius_cmd2.process(text):    return
        if self.next_cmd       and self.next_cmd.process(text):       return
        if self.pro2_cmd       and self.pro2_cmd.process(text):       return
        if self.v100_cmd       and self.v100_cmd.process(text):       return
        if self.v300_cmd       and self.v300_cmd.process(text):       return
        if self.call_cmd       and self.call_cmd.process(text):       return
        if self.val_cmd        and self.val_cmd.process(text):        return
        if self.gesture_cmd    and self.gesture_cmd.process(text):    return
        if self.autonomous_cmd and self.autonomous_cmd.process(text): return
        if self.ai_pro_cmd and self.ai_pro_cmd.process(text): return
        if self.watch_cmd and self.watch_cmd.process(text): return
        if self.school_cmd and self.school_cmd.process(text): return
        if self.routine_cmd and self.routine_cmd.process(text): return
        if self.super_cmd and self.super_cmd.process(text): return
        if self.mega_cmd and self.mega_cmd.process(text): return
        if self.ultimate_cmd and self.ultimate_cmd.process(text): return
        if self.adv_cmd and self.adv_cmd.process(text): return
        if self.sys_pro and self.sys_pro.process(text): return
        if self.cmd_proc and self.cmd_proc.process(text): return
        self._busy(True)
        threading.Thread(target=self._reply,args=(text,),daemon=True).start()

    def _reply(self,text):
        # 1) Modelsiz NLP motoru (BM25 + kök bulma + bağlam + hesap + öğrenme)
        try:
            if get_nlp:
                res = get_nlp().answer(text)
                if res:
                    r = res["answer"]
                    self.last_reply = r
                    self.after(0, lambda r=r: self._show("ANKA", r))
                    return
        except Exception as _e:
            print(f"[ANKA] NLP hata: {_e}")
        # Önce training data'dan bak
        t = text.lower().strip()
        # Tam eşleşme
        try:
            from anka_training_data import TRAINING_DATA
            for category, items in TRAINING_DATA.items():
                for item in items:
                    if item["q"].lower().strip() == t:
                        r = item["a"]
                        self.last_reply = r
                        self.after(0, lambda r=r: self._show("ANKA", r))
                        return
            # Kısmi eşleşme
            for category, items in TRAINING_DATA.items():
                for item in items:
                    if item["q"].lower().strip() in t or t in item["q"].lower().strip():
                        r = item["a"]
                        self.last_reply = r
                        self.after(0, lambda r=r: self._show("ANKA", r))
                        return
        except: pass
        # SQLite bilgi tabanı
        try:
            if search_knowledge:
                hits = search_knowledge(text, 1)
                if hits:
                    r = hits[0]["answer"]
                    self.last_reply = r
                    self.after(0, lambda r=r: self._show("ANKA", r))
                    return
        except Exception:
            pass
        # AI Core'a gönder
        r = self.ollama.chat(text)
        self.last_reply = r
        self.after(0, lambda r=r: self._show("ANKA", r))

    def _show(self,s,r):
        self._msg(s,r); self._busy(False); speak(r[:400])

    def _busy(self,b):
        self.is_thinking=b
        if b:
            self.send_btn.configure(state="disabled",text="⟳  Düşünüyor...")
            self.status_dot.configure(fg=C["YELLOW"]); self.status_lbl.configure(text="DÜŞÜNÜYOR",fg=C["YELLOW"])
        else:
            self.send_btn.configure(state="normal",text="↗  Gönder")
            self.status_dot.configure(fg=C["GREEN"]); self.status_lbl.configure(text="AKTİF",fg=C["GREEN"])

    def _quick(self,cmd):
        self.input_box.delete("1.0","end"); self.input_box.configure(fg=C["WHITE"])
        self.input_box.insert("1.0",cmd); self._send()

    def _solve_hw(self):
        text=self.input_box.get("1.0","end").strip()
        if not text or text=="Bir şey yaz veya komut ver...":
            self._msg("ANKA","Lütfen soruyu giriş kutusuna yazın efendim."); return
        self.input_box.delete("1.0","end"); self.input_box.configure(fg=C["WHITE"])
        self._msg("SEN",f"[{self.hw_sub.get()}] {text}")
        self._busy(True)
        def _r():
            r=self.ollama.chat(f"{self.hw_sub.get()} sorusu: {text}\n\nAdım adım çöz.",hw_mode=True)
            self.last_reply=r
            self.after(0,lambda:self._show("ÖDEV",r))
        threading.Thread(target=_r,daemon=True).start()

    def _panel(self,m):
        self.hw_mode=(m=="hw")
        for btn,key in [(self.pb_chat,"chat"),(self.pb_hw,"hw"),(self.pb_wa,"wa"),(self.pb_sys,"sys")]:
            btn.configure(fg_color=C["ACCENT3"] if m==key else C["SURFACE3"])
        for w in self.panel_frame.winfo_children(): w.grid_remove()
        panels={"chat":self.chat_panel,"hw":self.hw_panel,"wa":self.wa_panel,"sys":self.sys_panel}
        if m in panels:
            panels[m].grid(row=0,column=0,sticky="nsew")

    def _send_wa(self):
        from anka_commands import CommandProcessor
        contact=self.wa_contact.get().strip(); msg=self.wa_msg.get().strip()
        if not contact or not msg:
            self.footer_msg.configure(text="Kişi ve mesaj boş olamaz!",fg=C["RED"]); return
        self.footer_msg.configure(text=f"Gönderiliyor: {contact}...",fg=C["YELLOW"])
        self._msg("WA",f"{contact} → {msg}")
        from anka_security import WhatsAppController
        wa=WhatsAppController() if False else None
        import pyautogui,pyperclip,subprocess,time as _t
        def _s():
            try:
                subprocess.Popen(["cmd","/c","start","whatsapp:"],shell=True); _t.sleep(3)
                import ctypes; hwnd=None
                def cb(h,_):
                    nonlocal hwnd; buf=ctypes.create_unicode_buffer(256)
                    ctypes.windll.user32.GetWindowTextW(h,buf,256)
                    if "whatsapp" in buf.value.lower(): hwnd=h
                ctypes.windll.user32.EnumWindows(ctypes.WINFUNCTYPE(ctypes.c_bool,ctypes.POINTER(ctypes.c_int),ctypes.POINTER(ctypes.c_int))(cb),None)
                if hwnd: ctypes.windll.user32.ShowWindow(hwnd,9); ctypes.windll.user32.SetForegroundWindow(hwnd); _t.sleep(1)
                pyautogui.hotkey('ctrl','f'); _t.sleep(1); pyautogui.hotkey('ctrl','a')
                pyautogui.typewrite(contact,interval=0.05); _t.sleep(1.5)
                pyautogui.press('enter'); _t.sleep(1); pyautogui.hotkey('ctrl','l'); _t.sleep(0.5)
                pyperclip.copy(msg); pyautogui.hotkey('ctrl','v'); _t.sleep(0.5); pyautogui.press('enter')
                self.after(0,lambda:self.footer_msg.configure(text=f"✓ {contact}'e gönderildi!",fg=C["GREEN"]))
                self.after(0,lambda:self._msg("ANKA",f"{contact} kişisine mesaj gönderildi efendim."))
                self.after(0,lambda:speak(f"{contact} kişisine mesaj gönderildi efendim."))
            except Exception as e:
                self.after(0,lambda:self.footer_msg.configure(text=f"Hata: {e}",fg=C["RED"]))
            self.after(0,lambda:self.wa_msg.delete(0,"end"))
        threading.Thread(target=_s,daemon=True).start()

    def _anka_wa(self):
        contact=self.wa_contact.get().strip() or "birine"
        self.footer_msg.configure(text="Mesaj yazılıyor...",fg=C["YELLOW"])
        def _c():
            r=self.ollama.chat(f"{contact} adlı kişiye kısa samimi Türkçe WhatsApp mesajı yaz. Sadece mesajı yaz.")
            self.after(0,lambda:self.wa_msg.delete(0,"end"))
            self.after(0,lambda:self.wa_msg.insert(0,r.strip()))
            self.after(0,lambda:self.footer_msg.configure(text="✓ Mesaj hazır!",fg=C["GREEN"]))
        threading.Thread(target=_c,daemon=True).start()

    def _toggle_voice(self):
        if self.sleep_mode: return
        if not self.is_recording:
            self.is_recording=True
            if hasattr(self,'wake_listener'): self.wake_listener.pause()
            self.voice_btn.configure(text="⏹  Durdur",fg_color=C["RED"],text_color=C["WHITE"])
            self.status_dot.configure(fg=C["RED"]); self.status_lbl.configure(text="DİNLİYOR",fg=C["RED"])
            self.footer_msg.configure(text="Konuşun... Durdur'a basın.",fg=C["ACCENT"])
            self.voice.start()
        else:
            self.is_recording=False
            self.voice_btn.configure(text="⟳  Çevriliyor...",fg_color=C["ORANGE"],text_color=C["WHITE"],state="disabled")
            self.footer_msg.configure(text="Ses çevriliyor...",fg=C["YELLOW"])
            threading.Thread(target=self._pvoi,daemon=True).start()

    def _pvoi(self):
        text,audio=self.voice.stop_and_transcribe()
        self.after(0,lambda:self._vdone(text))

    def _vdone(self,text):
        if hasattr(self,'wake_listener'): self.wake_listener.resume()
        self.voice_btn.configure(text="🎤  Ses Komutu",fg_color=C["SURFACE2"],text_color=C["ACCENT"],state="normal")
        self.status_dot.configure(fg=C["GREEN"]); self.status_lbl.configure(text="AKTİF",fg=C["GREEN"])
        self.footer_msg.configure(text="")
        if text:
            self.input_box.delete("1.0","end"); self.input_box.configure(fg=C["WHITE"])
            self.input_box.insert("1.0",text); self._send()

    def _repeat(self):
        if self.last_reply: speak(self.last_reply[:400])

    def _chmodel(self,m):
        self.ollama.model=m; self.ollama.clear()
        self._msg("ANKA",f"Model değiştirildi: {m} efendim.")

    def _chpersonality(self,p):
        map_={"Profesyonel":"professional","Samimi":"friendly","Komik":"funny"}
        self.ollama.set_personality(map_.get(p,"professional"))
        self._msg("ANKA",f"Kişilik modu değiştirildi: {p}")

    def _clearchat(self):
        self.ollama.clear()
        self.chat_disp.configure(state="normal"); self.chat_disp.delete("1.0","end")
        self.chat_disp.configure(state="disabled")
        self._msg("ANKA","Sohbet temizlendi efendim.")

    def _toggle_sleep(self):
        self.sleep_mode=not self.sleep_mode
        if self.sleep_mode:
            if hasattr(self,'wake_listener'): self.wake_listener.pause()
            self._msg("ANKA","🌙 Uyku moduna geçildi. 'Anka uyan' yazınca aktif olacağım.")
            speak("Uyku moduna geçiyorum efendim. İyi geceler.")
        else:
            if hasattr(self,'wake_listener'): self.wake_listener.resume()
            self._msg("ANKA","☀️ Uyku modundan çıkıldı. Hoş geldiniz efendim!")
            speak("Tekrar merhaba efendim.")

    def _lock(self):
        from anka_security import logout
        logout()
        self._show_lock()

    def _cycle_theme(self):
        global C, current_theme
        themes=list(THEMES.keys())
        idx=(themes.index(current_theme)+1)%len(themes)
        current_theme=themes[idx]
        C=THEMES[current_theme]
        self._msg("ANKA",f"🎨 Tema değiştirildi: {current_theme.capitalize()}")

    def _register_voice(self):
        """Kullanıcının sesini kaydet — sadece bu sese cevap verilecek"""
        self._msg("ANKA","🎤 Ses kaydı başlıyor! 10 saniye boyunca normal sesle konuşun efendim...")
        speak("Ses kaydı başlıyor. 10 saniye boyunca normal sesle konuşun efendim.")
        def _rec():
            import sounddevice as sd
            import numpy as np
            try:
                audio = sd.rec(int(10 * 16000), samplerate=16000,
                               channels=1, dtype='float32')
                sd.wait()
                from anka_security import VoiceAuth
                if not hasattr(self, '_voice_auth'):
                    self._voice_auth = VoiceAuth()
                ok = self._voice_auth.register_voice(audio[:,0].tolist())
                if ok:
                    msg = "✓ Sesiniz kaydedildi! Artık sadece sizin sesinize cevap vereceğim efendim."
                else:
                    msg = "✗ Ses kaydedilemedi efendim."
                self.after(0, lambda: self._msg("ANKA", msg))
                self.after(0, lambda: speak(msg))
            except Exception as e:
                self.after(0, lambda: self._msg("ANKA", f"Ses kaydı hatası: {e}"))
        threading.Thread(target=_rec, daemon=True).start()

    def _register_face(self):
        self._msg("ANKA","Kameraya bakın, yüzünüz kaydediliyor...")
        def _r():
            ok=register_face()
            msg="✓ Yüzünüz başarıyla kaydedildi efendim!" if ok else "✗ Yüz kaydedilemedi."
            self.after(0,lambda:self._msg("ANKA",msg))
            self.after(0,lambda:speak(msg))
        threading.Thread(target=_r,daemon=True).start()

    # ── SİBER EV VE MOBİL EKOSİSTEM KONTROL MERKEZİ ─────────────────────────
    def _cihaz_yonetici(self, cihaz, komut, alt_cihaz=None):
        """
        Yusuf Reis, bu fonksiyon tüm ekosistemi tek noktadan yönetir.
        Redmi Watch 5 ve Mi 10T entegrasyonu dahil edilmiştir.
        """
        import socket
        # --- TELEVİZYONLAR (Toshiba / Vestel Altyapısı) ---
        if cihaz == "tv":
            tv_ip_haritasi = {
                "salon": "192.168.1.50",
                "oda": "192.168.1.51"
            }
            if alt_cihaz not in tv_ip_haritasi: return False
            ip = tv_ip_haritasi[alt_cihaz]
            url = f"http://{ip}:56789/apps/vr/remote"
            komut_haritasi = {
                "ac_kapat": "POWER", "ses_arti": "VOLUMEUP", "ses_eksi": "VOLUMEDOWN",
                "youtube": "YOUTUBE", "netflix": "NETFLIX", "tamam": "OK", "geri": "BACK"
            }
            if komut in komut_haritasi:
                payload = f"<remote><key code='{komut_haritasi[komut]}'/></remote>"
                try:
                    requests.post(url, data=payload, timeout=2)
                    return True
                except: return False

        # --- PLAYSTATION 5 ---
        elif cihaz == "ps5":
            ps5_ip = "192.168.1.60"
            ps5_mac = "AA:BB:CC:DD:EE:FF"  # PS5 MAC adresini buraya gir
            if komut == "uyandir":
                try:
                    mac_bytes = bytes.fromhex(ps5_mac.replace(":", ""))
                    packet = b'\xff' * 6 + mac_bytes * 16
                    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                    sock.sendto(packet, (ps5_ip, 9))
                    sock.sendto(packet, ('255.255.255.255', 9))
                    return True
                except: return False

        # --- SAMSUNG TABLET (Galaxy Tab S10 FE) ---
        elif cihaz == "tablet":
            if komut == "ikinci_ekran":
                try:
                    pyautogui.hotkey('win', 'k')
                    return True
                except: return False

        # --- XIAOMI MI 10T & REDMI WATCH 5 EKOSİSTEMİ ---
        elif cihaz == "mobil":
            mi10t_ip = "192.168.1.70"
            if komut == "saat_bildirim":
                url = f"http://{mi10t_ip}:8585/anka_komut?mesaj=ANKA_SAAT_AKTIF"
                try:
                    threading.Thread(
                        target=lambda: requests.get(url, timeout=1),
                        daemon=True
                    ).start()
                    return True
                except: return False

        return False

    def _karargah_tam_senaryo(self):
        """Bütün cihazları tek seferde ateşleyen senaryo (Büyük Şov Modu)"""
        self._msg("SİSTEM", "🎬 'Karargahı Hazırla' tam ekosistem modu aktif!")
        speak("Anlaşıldı Yusuf Reis. Tüm cihazlar için siber protokoller tetikleniyor.")

        # 1. Televizyonlar ve PS5 tetikleniyor
        self._cihaz_yonetici("tv", "ac_kapat", "salon")
        self._cihaz_yonetici("tv", "ac_kapat", "oda")
        self._cihaz_yonetici("ps5", "uyandir")

        # 2. Tablet için yansıtma arayüzü tetikleniyor
        self._cihaz_yonetici("tablet", "ikinci_ekran")

        # 3. Mi 10T üzerinden Redmi Watch 5'e siber sinyal gönderiliyor
        self._cihaz_yonetici("mobil", "saat_bildirim")

        time.sleep(1)
        pyautogui.hotkey('win', 'd')

        msg = "Tüm karargah hazırlandı Yusuf Reis. İki TV, PS5, tablet ve Redmi Watch 5 senkronize edildi!"
        self._msg("ANKA", msg)
        speak(msg)

    def _cihaz_komut(self, text):
        """Sesli/yazılı cihaz komutlarını işle"""
        t = text.lower()

        if "karargahı hazırla" in t or "büyük şov" in t:
            threading.Thread(target=self._karargah_tam_senaryo, daemon=True).start()
            return True

        # TV Komutları
        tv_oda = "salon" if "salon" in t else "oda" if "oda" in t else None
        if tv_oda:
            if "tv" in t or "televizyon" in t:
                if "aç" in t or "kapat" in t:
                    ok = self._cihaz_yonetici("tv", "ac_kapat", tv_oda)
                    r = f"✓ {tv_oda.capitalize()} TV {'açıldı/kapatıldı' if ok else 'yanıt vermedi'} efendim."
                    self._msg("ANKA",r); speak(r); return True
                if "ses" in t and "artır" in t:
                    self._cihaz_yonetici("tv", "ses_arti", tv_oda); return True
                if "ses" in t and "azalt" in t:
                    self._cihaz_yonetici("tv", "ses_eksi", tv_oda); return True
                if "youtube" in t:
                    self._cihaz_yonetici("tv", "youtube", tv_oda); return True
                if "netflix" in t:
                    self._cihaz_yonetici("tv", "netflix", tv_oda); return True

        # PS5
        if "ps5" in t or "playstation" in t:
            if "aç" in t or "uyandir" in t or "başlat" in t:
                ok = self._cihaz_yonetici("ps5", "uyandir")
                r = "✓ PS5 uyandırma sinyali gönderildi efendim." if ok else "PS5'e ulaşılamadı efendim."
                self._msg("ANKA",r); speak(r); return True

        # Tablet
        if "tablet" in t and ("yansıt" in t or "ikinci ekran" in t):
            self._cihaz_yonetici("tablet", "ikinci_ekran")
            r = "✓ Tablet ikinci ekran modu açıldı efendim."
            self._msg("ANKA",r); speak(r); return True

        # Saat/Watch bildirimi
        if ("saat" in t or "watch" in t) and "bildir" in t:
            ok = self._cihaz_yonetici("mobil", "saat_bildirim")
            r = "✓ Redmi Watch 5'e sinyal gönderildi efendim." if ok else "Saate ulaşılamadı efendim."
            self._msg("ANKA",r); speak(r); return True

        return False


# ── Başlangıçta Otomatik Çalıştır ────────────────────────────────────────────
def setup_autostart():
    import winreg
    script=os.path.abspath(__file__)
    key=winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                        r"Software\Microsoft\Windows\CurrentVersion\Run",0,winreg.KEY_SET_VALUE)
    winreg.SetValueEx(key,"Anka",0,winreg.REG_SZ,f'pythonw "{script}"')
    winreg.CloseKey(key)


if __name__=="__main__":
    import sys
    if "--setup-autostart" in sys.argv:
        setup_autostart()
        print("✓ Anka Windows başlangıcına eklendi!")
    else:
        app=AnkaApp()
        app.mainloop()
