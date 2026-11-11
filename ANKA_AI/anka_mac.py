# ── ANKA macOS ADAPTÖR MODÜLü ─────────────────────────────────────────────────
# Windows'a özel kodları macOS'a uyarlar
# import anka_mac → otomatik platform tespiti yapılır

import sys, os, platform

IS_MAC     = platform.system() == "Darwin"
IS_WINDOWS = platform.system() == "Windows"
IS_LINUX   = platform.system() == "Linux"

print(f"[ANKA] Platform: {platform.system()} {platform.machine()}")


# ── macOS Ses Sistemi ─────────────────────────────────────────────────────────
class MacSpeaker:
    """macOS'ta TTS — edge-tts veya sistem sesi"""
    def speak(self, text):
        import subprocess, tempfile, os
        try:
            import asyncio, edge_tts
            async def _say():
                c = edge_tts.Communicate(text, voice="tr-TR-EmelNeural", rate="+8%")
                tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
                tmp.close()
                await c.save(tmp.name)
                subprocess.run(["afplay", tmp.name])
                os.unlink(tmp.name)
            asyncio.run(_say())
        except:
            # Fallback: macOS say komutu
            clean = text.replace('"',"").replace("'",'')[:300]
            subprocess.run(["say", "-v", "Yelda", clean])


# ── macOS Ekran Kontrolü ──────────────────────────────────────────────────────
class MacScreenController:
    def screenshot(self, path):
        import subprocess
        subprocess.run(["screencapture", "-x", path])
        return os.path.exists(path)

    def get_active_window(self):
        try:
            import subprocess
            result = subprocess.run(
                ["osascript", "-e",
                 'tell application "System Events" to get name of first application process whose frontmost is true'],
                capture_output=True, text=True)
            return result.stdout.strip()
        except: return "Bilinmeyen"

    def set_volume(self, level):
        import subprocess
        subprocess.run(["osascript", "-e", f"set volume output volume {level}"])

    def set_brightness(self, level):
        try:
            import subprocess
            # brightness komutu (brew install brightness ile kurulur)
            subprocess.run(["brightness", str(level/100)])
        except: pass

    def open_app(self, app_name):
        import subprocess
        subprocess.run(["open", "-a", app_name])

    def dark_mode_toggle(self):
        import subprocess
        subprocess.run([
            "osascript", "-e",
            'tell app "System Events" to tell appearance preferences to set dark mode to not dark mode'
        ])

    def lock_screen(self):
        import subprocess
        subprocess.run([
            "osascript", "-e",
            'tell application "System Events" to keystroke "q" using {command down, control down}'
        ])

    def minimize_all(self):
        import subprocess
        subprocess.run([
            "osascript", "-e",
            'tell application "System Events" to keystroke "m" using {command down, option down}'
        ])

    def new_tab_browser(self):
        import subprocess
        subprocess.run([
            "osascript", "-e",
            'tell application "Safari" to activate\ntell application "System Events" to keystroke "t" using command down'
        ])


# ── macOS Bildirim Sistemi ────────────────────────────────────────────────────
class MacNotifier:
    def notify(self, title, message, subtitle=""):
        import subprocess
        script = f'display notification "{message}" with title "{title}"'
        if subtitle:
            script += f' subtitle "{subtitle}"'
        subprocess.run(["osascript", "-e", script])

    def reminder(self, title, date_str, notes=""):
        """macOS Reminders'a ekle"""
        import subprocess
        script = f'''
        tell application "Reminders"
            make new reminder with properties {{name:"{title}", body:"{notes}"}}
        end tell
        '''
        subprocess.run(["osascript", "-e", script])

    def calendar_event(self, title, start, end="", location=""):
        """macOS Calendar'a etkinlik ekle"""
        import subprocess
        script = f'''
        tell application "Calendar"
            tell calendar "Takvim"
                make new event with properties {{summary:"{title}", start date:date "{start}"}}
            end tell
        end tell
        '''
        subprocess.run(["osascript", "-e", script])


# ── macOS Uygulama Yönetimi ───────────────────────────────────────────────────
class MacAppManager:
    MAC_APPS = {
        "chrome": "Google Chrome",
        "safari": "Safari",
        "firefox": "Firefox",
        "vscode": "Visual Studio Code",
        "terminal": "Terminal",
        "finder": "Finder",
        "spotify": "Spotify",
        "whatsapp": "WhatsApp",
        "discord": "Discord",
        "zoom": "zoom.us",
        "notion": "Notion",
        "xcode": "Xcode",
        "iterm": "iTerm",
    }

    def open(self, name):
        import subprocess
        app = self.MAC_APPS.get(name.lower(), name)
        subprocess.run(["open", "-a", app])
        return f"✓ {app} açıldı efendim."

    def quit(self, name):
        import subprocess
        app = self.MAC_APPS.get(name.lower(), name)
        subprocess.run(["osascript", "-e", f'tell application "{app}" to quit'])
        return f"✓ {app} kapatıldı efendim."

    def list_running(self):
        import subprocess
        result = subprocess.run(
            ["osascript", "-e",
             'tell application "System Events" to get name of every application process'],
            capture_output=True, text=True)
        apps = result.stdout.strip().split(", ")
        return apps[:20]


# ── macOS Sistem Bilgisi ──────────────────────────────────────────────────────
class MacSystemInfo:
    def battery(self):
        import subprocess
        result = subprocess.run(
            ["pmset", "-g", "batt"],
            capture_output=True, text=True)
        output = result.stdout
        import re
        percent_m = re.search(r'(\d+)%', output)
        charging = "charging" in output.lower() or "AC" in output
        if percent_m:
            return {
                "percent": int(percent_m.group(1)),
                "charging": charging
            }
        return None

    def disk_usage(self):
        import subprocess
        result = subprocess.run(
            ["df", "-h", "/"],
            capture_output=True, text=True)
        lines = result.stdout.strip().split('\n')
        if len(lines) > 1:
            parts = lines[1].split()
            return {
                "total": parts[1] if len(parts)>1 else "?",
                "used": parts[2] if len(parts)>2 else "?",
                "free": parts[3] if len(parts)>3 else "?",
                "percent": parts[4] if len(parts)>4 else "?"
            }
        return None

    def wifi_info(self):
        import subprocess
        result = subprocess.run(
            ["/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport", "-I"],
            capture_output=True, text=True)
        output = result.stdout
        import re
        ssid_m = re.search(r'SSID: (.+)', output)
        rssi_m = re.search(r'agrCtlRSSI: (-\d+)', output)
        return {
            "ssid": ssid_m.group(1).strip() if ssid_m else "?",
            "signal": rssi_m.group(1) if rssi_m else "?"
        }


# ── macOS Platform Uyumluluk Katmanı ─────────────────────────────────────────
class MacPlatformAdapter:
    """
    Windows komutlarını macOS'a çevirir.
    anka_automation.py'deki Windows komutlarının Mac versiyonu.
    """
    def __init__(self, speak_func, msg_func):
        self.speak = speak_func
        self.msg = msg_func
        self.screen = MacScreenController()
        self.notifier = MacNotifier()
        self.apps = MacAppManager()
        self.system = MacSystemInfo()

    def process(self, text):
        t = text.lower().strip()

        # Uygulama aç
        if "aç" in t:
            for app in ["chrome","safari","firefox","spotify","discord","whatsapp",
                       "vscode","terminal","finder","zoom","notion"]:
                if app in t:
                    r = self.apps.open(app)
                    self.msg("ANKA", r); self.speak(r)
                    return True

        # Karanlık mod
        if "karanlık mod" in t or "dark mode" in t:
            self.screen.dark_mode_toggle()
            r = "✓ Karanlık mod değiştirildi efendim."
            self.msg("ANKA", r); self.speak(r)
            return True

        # Ses
        if "ses" in t and any(c.isdigit() for c in t):
            import re
            m = re.search(r'(\d+)', t)
            if m:
                self.screen.set_volume(int(m.group(1)))
                r = f"✓ Ses %{m.group(1)} yapıldı efendim."
                self.msg("ANKA", r); self.speak(r)
            return True

        # Ekran kilitle
        if "ekranı kilitle" in t:
            self.screen.lock_screen()
            r = "✓ Ekran kilitlendi efendim."
            self.msg("ANKA", r); self.speak(r)
            return True

        # Ekran görüntüsü
        if "ekran görüntüsü" in t:
            import tempfile
            path = os.path.join(os.path.expanduser("~"), "Desktop",
                               f"anka_{int(__import__('time').time())}.png")
            self.screen.screenshot(path)
            r = f"✓ Ekran görüntüsü alındı: {path}"
            self.msg("ANKA", r); self.speak(r)
            return True

        # Bildirim
        if "bildirim gönder" in t:
            msg = t.replace("bildirim gönder","").strip()
            self.notifier.notify("Anka", msg)
            r = "✓ Bildirim gönderildi efendim."
            self.msg("ANKA", r); self.speak(r)
            return True

        # Pil durumu
        if "pil" in t or "şarj" in t:
            batt = self.system.battery()
            if batt:
                r = f"🔋 Pil: %{batt['percent']} ({'Şarjda' if batt['charging'] else 'Pilde'})"
                self.msg("ANKA", r); self.speak(r)
            return True

        # WiFi
        if "wifi" in t or "ağ bilgisi" in t:
            info = self.system.wifi_info()
            r = f"📶 WiFi: {info['ssid']} (Sinyal: {info['signal']} dBm)"
            self.msg("ANKA", r); self.speak(r)
            return True

        # Disk
        if "disk" in t:
            disk = self.system.disk_usage()
            if disk:
                r = f"💾 Disk: {disk['used']}/{disk['total']} kullanıldı (%{disk['percent']})"
                self.msg("ANKA", r); self.speak(r)
            return True

        # Takvim
        if "takvime ekle" in t:
            event = t.replace("takvime ekle","").strip()
            self.notifier.calendar_event(event, "tomorrow")
            r = f"✓ '{event}' takvime eklendi efendim."
            self.msg("ANKA", r); self.speak(r)
            return True

        # Uygulama kapat
        if "kapat" in t:
            for app in ["chrome","safari","spotify","discord","whatsapp","zoom"]:
                if app in t:
                    r = self.apps.quit(app)
                    self.msg("ANKA", r); self.speak(r)
                    return True

        return False


# ── Platform Tespiti & Otomatik Adaptör ──────────────────────────────────────
def get_platform_adapter(speak_func=None, msg_func=None):
    """Platform'a göre doğru adaptörü döndür"""
    if IS_MAC:
        return MacPlatformAdapter(speak_func, msg_func)
    return None  # Windows için mevcut modüller yeterli


def patch_for_mac():
    """macOS'ta çalışmayan Windows modüllerini yama"""
    if not IS_MAC:
        return

    # winreg yoksa sahte modül oluştur
    import importlib.util
    if not importlib.util.find_spec("winreg"):
        import types
        winreg = types.ModuleType("winreg")
        winreg.HKEY_CURRENT_USER = None
        winreg.HKEY_LOCAL_MACHINE = None
        winreg.OpenKey = lambda *a, **k: None
        winreg.QueryValueEx = lambda *a, **k: (None, None)
        winreg.SetValueEx = lambda *a, **k: None
        winreg.CloseKey = lambda *a, **k: None
        winreg.REG_DWORD = 4
        winreg.REG_SZ = 1
        winreg.KEY_ALL_ACCESS = 0xF003F
        sys.modules["winreg"] = winreg

    # ctypes.windll yoksa patch
    import ctypes
    if not hasattr(ctypes, 'windll'):
        class FakeWinDLL:
            class user32:
                @staticmethod
                def GetForegroundWindow(): return 0
                @staticmethod
                def GetWindowTextLengthW(h): return 0
                @staticmethod
                def GetWindowTextW(h, b, n): pass
                @staticmethod
                def SystemParametersInfoW(*a): pass
        ctypes.windll = FakeWinDLL()

    print("[ANKA] macOS uyumluluk yamaları uygulandı.")


# Otomatik uygula
if IS_MAC:
    patch_for_mac()
