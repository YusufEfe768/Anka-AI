# ── ANKA OTOMASYon MODÜLü ────────────────────────────────────────────────────
# Windows otomasyonu, kısayollar, scheduled tasks, ekran kontrolü
try:
    import pyperclip
except ImportError:
    class _PyClip:
        def copy(self,x):pass
        def paste(self):return ""
    pyperclip=_PyClip()
import json, os, threading, datetime, subprocess, time, re
import pyperclip, ctypes, winreg
try:
    import pyautogui
except ImportError:
    pyautogui=None
from anka_config import BASE_DIR

AUTO_FILE = os.path.join(BASE_DIR, "anka_automation2.json")

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

class WindowsAutomation:
    def __init__(self, speak_func, msg_func):
        self.speak = speak_func
        self.msg = msg_func

    # ── Ekran & Görüntü ───────────────────────────────────────────────────────
    def screenshot_region(self, x, y, w, h, save_path=None):
        try:
            import PIL.ImageGrab as ig
            img = ig.grab(bbox=(x, y, x+w, y+h))
            path = save_path or os.path.join(
                os.path.expanduser("~"), "Desktop",
                f"anka_bolge_{datetime.datetime.now().strftime('%H%M%S')}.png")
            img.save(path)
            return path
        except Exception as e:
            return None

    def set_wallpaper(self, image_path):
        try:
            ctypes.windll.user32.SystemParametersInfoW(20, 0, image_path, 3)
            return True
        except: return False

    def toggle_dark_mode(self):
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize",
                0, winreg.KEY_ALL_ACCESS)
            val, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            winreg.SetValueEx(key, "AppsUseLightTheme", 0, winreg.REG_DWORD, 1-val)
            winreg.SetValueEx(key, "SystemUsesLightTheme", 0, winreg.REG_DWORD, 1-val)
            winreg.CloseKey(key)
            return val == 1  # True = dark mode'a geçildi
        except: return None

    def set_volume(self, level):
        try:
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            from comtypes import CLSCTX_ALL
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = interface.QueryInterface(IAudioEndpointVolume)
            volume.SetMasterVolumeLevelScalar(level/100, None)
            return True
        except:
            # Fallback: nircmd varsa
            try:
                subprocess.run(["nircmd","setsysvolume",str(int(level*655.35))], timeout=3)
                return True
            except: return False

    def type_text(self, text, delay=0.05):
        try:
            pyautogui.write(text, interval=delay)
            return True
        except: return False

    def click_at(self, x, y):
        try:
            pyautogui.click(x, y)
            return True
        except: return False

    def scroll(self, direction="down", amount=3):
        try:
            pyautogui.scroll(-amount if direction=="down" else amount)
            return True
        except: return False

    def hotkey(self, *keys):
        try:
            pyautogui.hotkey(*keys)
            return True
        except: return False

    # ── Windows Görev Zamanlayıcı ─────────────────────────────────────────────
    def create_scheduled_task(self, name, command, trigger_time):
        try:
            ps_cmd = (
                f'$action = New-ScheduledTaskAction -Execute "{command}"; '
                f'$trigger = New-ScheduledTaskTrigger -Daily -At "{trigger_time}"; '
                f'Register-ScheduledTask -TaskName "{name}" -Action $action '
                f'-Trigger $trigger -Force'
            )
            result = subprocess.run(
                ["powershell","-Command", ps_cmd],
                capture_output=True, text=True, timeout=15)
            return result.returncode == 0
        except: return False

    def delete_scheduled_task(self, name):
        try:
            subprocess.run(
                ["powershell","-Command",f'Unregister-ScheduledTask -TaskName "{name}" -Confirm:$false'],
                capture_output=True, timeout=10)
            return True
        except: return False

    def list_scheduled_tasks(self):
        try:
            result = subprocess.run(
                ["powershell","-Command",
                 "Get-ScheduledTask | Where-Object {$_.TaskPath -eq '\\'} | "
                 "Select-Object TaskName,State | ConvertTo-Json"],
                capture_output=True, text=True, timeout=10)
            data = json.loads(result.stdout)
            if isinstance(data, dict): data = [data]
            return [(d.get("TaskName","?"), d.get("State","?")) for d in data[:10]]
        except: return []

    # ── Uygulama Otomasyonu ───────────────────────────────────────────────────
    def open_with(self, file_path, app=None):
        try:
            if app:
                subprocess.Popen([app, file_path])
            else:
                os.startfile(file_path)
            return True
        except: return False

    def close_window(self, title_keyword):
        try:
            result = subprocess.run(
                ["powershell","-Command",
                 f"Get-Process | Where-Object {{$_.MainWindowTitle -like '*{title_keyword}*'}} | Stop-Process"],
                capture_output=True, timeout=10)
            return True
        except: return False

    def minimize_all(self):
        pyautogui.hotkey('win', 'd')

    def maximize_window(self):
        pyautogui.hotkey('win', 'up')

    def snap_left(self):
        pyautogui.hotkey('win', 'left')

    def snap_right(self):
        pyautogui.hotkey('win', 'right')

    # ── Klavye Kısayolları ────────────────────────────────────────────────────
    def undo(self): pyautogui.hotkey('ctrl','z')
    def redo(self): pyautogui.hotkey('ctrl','y')
    def save_all(self): pyautogui.hotkey('ctrl','shift','s')
    def select_all(self): pyautogui.hotkey('ctrl','a')
    def copy(self): pyautogui.hotkey('ctrl','c')
    def paste(self): pyautogui.hotkey('ctrl','v')
    def find(self): pyautogui.hotkey('ctrl','f')
    def new_tab(self): pyautogui.hotkey('ctrl','t')
    def close_tab(self): pyautogui.hotkey('ctrl','w')
    def refresh(self): pyautogui.hotkey('f5')
    def task_manager(self): pyautogui.hotkey('ctrl','shift','esc')
    def lock_screen(self): pyautogui.hotkey('win','l')

    # ── Güç Yönetimi ──────────────────────────────────────────────────────────
    def shutdown(self, minutes=0):
        seconds = minutes * 60
        subprocess.run(["shutdown","/s",f"/t",str(seconds)])

    def restart(self, minutes=0):
        seconds = minutes * 60
        subprocess.run(["shutdown","/r",f"/t",str(seconds)])

    def sleep(self):
        subprocess.run(["rundll32.exe","powrprof.dll,SetSuspendState","0","1","0"])

    def hibernate(self):
        subprocess.run(["shutdown","/h"])

    def cancel_shutdown(self):
        subprocess.run(["shutdown","/a"])

    # ── Ekran Parlaklık & Gece Modu ───────────────────────────────────────────
    def night_light_on(self):
        try:
            subprocess.run(["powershell","-Command",
                "$path = 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\CloudStore\\Store\\DefaultAccount\\Current\\default$windows.data.bluelightreduction.bluelightreductionstate\\windows.data.bluelightreduction.bluelightreductionstate'; "
                "Set-ItemProperty -Path $path -Name 'Data' -Value ([byte[]](0x43,0x42,0x01,0x00,0x0A,0x02,0x01,0x00,0x2E,0x1C))"],
                capture_output=True, timeout=5)
        except: pass

    def set_brightness(self, level):
        try:
            subprocess.run(
                ["powershell","-Command",
                 f"(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,{level})"],
                capture_output=True, timeout=5)
            return True
        except: return False

class AutomationCommandProcessor:
    def __init__(self, speak_func, msg_func, ollama):
        self.speak = speak_func
        self.msg = msg_func
        self.ollama = ollama
        self.win = WindowsAutomation(speak_func, msg_func)

    def process(self, text):
        t = text.lower().strip()

        # ── Pencere Yönetimi ─────────────────────────────────────────────────
        if "pencereyi sola" in t or "sol yarıya al" in t:
            self.win.snap_left()
            r = "✓ Pencere sola yapıştırıldı efendim."; self.msg("ANKA",r); self.speak(r)
            return True

        if "pencereyi sağa" in t or "sağ yarıya al" in t:
            self.win.snap_right()
            r = "✓ Pencere sağa yapıştırıldı efendim."; self.msg("ANKA",r); self.speak(r)
            return True

        if "pencereyi büyüt" in t or "tam ekran yap" in t:
            self.win.maximize_window()
            r = "✓ Pencere büyütüldü efendim."; self.msg("ANKA",r); self.speak(r)
            return True

        if "tüm pencereleri küçült" in t:
            self.win.minimize_all()
            r = "✓ Tüm pencereler küçültüldü efendim."; self.msg("ANKA",r); self.speak(r)
            return True

        if "pencereyi kapat" in t:
            title = t.replace("pencereyi kapat","").strip()
            self.win.close_window(title)
            r = f"✓ '{title}' penceresi kapatıldı efendim."; self.msg("ANKA",r); self.speak(r)
            return True

        # ── Kısayollar ────────────────────────────────────────────────────────
        if "geri al" in t and "son" in t:
            self.win.undo()
            r = "✓ Geri alındı efendim."; self.msg("ANKA",r); self.speak(r)
            return True

        if "yeni sekme" in t:
            self.win.new_tab()
            r = "✓ Yeni sekme açıldı efendim."; self.msg("ANKA",r); self.speak(r)
            return True

        if "sekmeyi kapat" in t:
            self.win.close_tab()
            r = "✓ Sekme kapatıldı efendim."; self.msg("ANKA",r); self.speak(r)
            return True

        if "görev yöneticisi" in t:
            self.win.task_manager()
            r = "✓ Görev yöneticisi açıldı efendim."; self.msg("ANKA",r); self.speak(r)
            return True

        if "ekranı kilitle" in t:
            self.win.lock_screen()
            r = "✓ Ekran kilitlendi efendim."; self.msg("ANKA",r); self.speak(r)
            return True

        # ── Güç Yönetimi ──────────────────────────────────────────────────────
        if "bilgisayarı uyut" in t:
            self.win.sleep()
            r = "✓ Uyku moduna geçiliyor efendim."; self.msg("ANKA",r); self.speak(r)
            return True

        if "bilgisayarı hazırda beklet" in t:
            self.win.hibernate()
            r = "✓ Hazırda bekleme efendim."; self.msg("ANKA",r); self.speak(r)
            return True

        if re.search(r'(\d+)\s*dakika sonra (kapat|yeniden başlat)', t):
            m = re.search(r'(\d+)', t)
            mins = int(m.group(1))
            if "yeniden başlat" in t:
                self.win.restart(mins)
                r = f"✓ {mins} dakika sonra yeniden başlatılacak efendim."
            else:
                self.win.shutdown(mins)
                r = f"✓ {mins} dakika sonra kapatılacak efendim."
            self.msg("ANKA",r); self.speak(r)
            return True

        if "kapatmayı iptal" in t:
            self.win.cancel_shutdown()
            r = "✓ Otomatik kapatma iptal edildi efendim."; self.msg("ANKA",r); self.speak(r)
            return True

        # ── Görünüm ───────────────────────────────────────────────────────────
        if "karanlık mod" in t or "dark mode" in t:
            result = self.win.toggle_dark_mode()
            if result is not None:
                r = f"✓ {'Karanlık' if result else 'Aydınlık'} mod aktif efendim."
            else:
                r = "Mod değiştirilemedi efendim."
            self.msg("ANKA",r); self.speak(r)
            return True

        if "parlaklık" in t:
            m = re.search(r'(\d+)', t)
            if m:
                level = min(100, max(0, int(m.group(1))))
                self.win.set_brightness(level)
                r = f"✓ Parlaklık %{level} olarak ayarlandı efendim."
                self.msg("ANKA",r); self.speak(r)
            return True

        if "ses seviyesi" in t:
            m = re.search(r'(\d+)', t)
            if m:
                level = min(100, max(0, int(m.group(1))))
                self.win.set_volume(level)
                r = f"✓ Ses %{level} olarak ayarlandı efendim."
                self.msg("ANKA",r); self.speak(r)
            return True

        # ── Windows Zamanlayıcı ───────────────────────────────────────────────
        if "windows görevi oluştur" in t:
            parts = t.replace("windows görevi oluştur","").strip().split("|")
            if len(parts) >= 3:
                name, cmd, trigger = parts[0].strip(), parts[1].strip(), parts[2].strip()
                ok = self.win.create_scheduled_task(name, cmd, trigger)
                r = f"✓ '{name}' görevi oluşturuldu efendim." if ok else "Görev oluşturulamadı."
                self.msg("ANKA",r); self.speak(r)
            return True

        if "zamanlanmış görevler" in t:
            def _t():
                tasks = self.win.list_scheduled_tasks()
                if tasks:
                    r = "⏰ Zamanlanmış Görevler:\n" + "\n".join(f"• {n} ({s})" for n,s in tasks)
                else:
                    r = "Zamanlanmış görev bulunamadı efendim."
                self.msg("ANKA",r)
            threading.Thread(target=_t, daemon=True).start()
            return True

        # ── Metin Yazma Otomasyonu ────────────────────────────────────────────
        if "otomatik yaz:" in t:
            text_to_type = text.replace("otomatik yaz:","").strip()
            if text_to_type:
                def _type():
                    time.sleep(2)
                    self.win.type_text(text_to_type)
                    r = f"✓ Metin yazıldı efendim."
                    self.msg("ANKA",r)
                threading.Thread(target=_type, daemon=True).start()
            return True

        # ── Sayfa Yenile ─────────────────────────────────────────────────────
        if "sayfayı yenile" in t or "f5 bas" in t:
            self.win.refresh()
            r = "✓ Sayfa yenilendi efendim."; self.msg("ANKA",r); self.speak(r)
            return True

        return False
