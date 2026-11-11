# ── ANKA ALARM MODÜLü ────────────────────────────────────────────────────────
import threading, time, datetime
from anka_memory import get_active_alarms, load_alarms, _save
from anka_config import ALARM_FILE

class AlarmManager:
    def __init__(self, speak_func, msg_func):
        self.speak = speak_func
        self.msg   = msg_func
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def _loop(self):
        while self.running:
            try:
                now = datetime.datetime.now()
                alarms = get_active_alarms()
                for i, alarm in enumerate(alarms):
                    if alarm["hour"] == now.hour and alarm["minute"] == now.minute and now.second < 5:
                        label = alarm.get("label","Alarm")
                        self.msg("SİSTEM", f"⏰ {label}!")
                        self.speak(f"Efendim, alarm zamanı! {label}")
                        if not alarm.get("repeat", False):
                            all_alarms = load_alarms()
                            for a in all_alarms:
                                if a["hour"]==alarm["hour"] and a["minute"]==alarm["minute"]:
                                    a["active"] = False
                            _save(ALARM_FILE, all_alarms)
            except: pass
            time.sleep(5)

    def stop(self):
        self.running = False


class WaterReminder:
    def __init__(self, speak_func, msg_func, interval_minutes=60):
        self.speak = speak_func
        self.msg   = msg_func
        self.interval = interval_minutes * 60
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def _loop(self):
        time.sleep(self.interval)
        while self.running:
            self.msg("SİSTEM","💧 Su içme zamanı! Bir bardak su için.")
            self.speak("Efendim, su içme zamanı geldi.")
            time.sleep(self.interval)

    def stop(self):
        self.running = False


class MedicationReminder:
    def __init__(self, speak_func, msg_func, medications):
        self.speak = speak_func
        self.msg   = msg_func
        self.medications = medications
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def _loop(self):
        while self.running:
            now = datetime.datetime.now()
            for med in self.medications:
                if med["hour"]==now.hour and med["minute"]==now.minute and now.second < 5:
                    msg=f"💊 İlaç zamanı: {med['name']}"
                    self.msg("SİSTEM",msg)
                    self.speak(f"Efendim, {med['name']} ilacınızı içme zamanı.")
            time.sleep(5)

    def stop(self):
        self.running = False
