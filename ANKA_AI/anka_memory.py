# ── ANKA HAFIZA SİSTEMİ ──────────────────────────────────────────────────────
import json, os, datetime
from anka_config import MEMORY_FILE, NOTES_FILE, TASKS_FILE, BUDGET_FILE, HEALTH_FILE, LOG_FILE, ALARM_FILE

def _load(path, default):
    try:
        if os.path.exists(path):
            with open(path,"r",encoding="utf-8") as f: return json.load(f)
    except: pass
    return default

def _save(path, data):
    try:
        with open(path,"w",encoding="utf-8") as f: json.dump(data,f,ensure_ascii=False,indent=2)
    except: pass

# ── Hafıza ───────────────────────────────────────────────────────────────────
def load_memory():
    return _load(MEMORY_FILE, {
        "name":"Yusuf","city":"Istanbul","language":"tr",
        "history":[],"preferences":{},"birthdays":{},
        "last_seen":None,"mood":"normal"
    })

def save_memory(mem):
    mem["last_seen"] = datetime.datetime.now().isoformat()
    _save(MEMORY_FILE, mem)

# ── Notlar ───────────────────────────────────────────────────────────────────
def load_notes():
    return _load(NOTES_FILE, [])

def add_note(text):
    notes = load_notes()
    notes.append({"text":text,"time":datetime.datetime.now().isoformat(),"done":False})
    _save(NOTES_FILE, notes)
    return len(notes)

def get_notes(limit=10):
    return load_notes()[-limit:]

def clear_notes():
    _save(NOTES_FILE, [])

# ── Görevler ─────────────────────────────────────────────────────────────────
def load_tasks():
    return _load(TASKS_FILE, [])

def add_task(text, deadline=None):
    tasks = load_tasks()
    tasks.append({"text":text,"time":datetime.datetime.now().isoformat(),
                  "deadline":deadline,"done":False})
    _save(TASKS_FILE, tasks)

def complete_task(index):
    tasks = load_tasks()
    if 0 <= index < len(tasks):
        tasks[index]["done"] = True
        _save(TASKS_FILE, tasks)
        return True
    return False

def get_pending_tasks():
    return [t for t in load_tasks() if not t["done"]]

# ── Alarmlar ─────────────────────────────────────────────────────────────────
def load_alarms():
    return _load(ALARM_FILE, [])

def add_alarm(hour, minute, label="Alarm", repeat=False):
    alarms = load_alarms()
    alarms.append({"hour":hour,"minute":minute,"label":label,
                   "repeat":repeat,"active":True,
                   "created":datetime.datetime.now().isoformat()})
    _save(ALARM_FILE, alarms)

def get_active_alarms():
    return [a for a in load_alarms() if a["active"]]

def remove_alarm(index):
    alarms = load_alarms()
    if 0 <= index < len(alarms):
        alarms.pop(index)
        _save(ALARM_FILE, alarms)

# ── Sağlık ───────────────────────────────────────────────────────────────────
def load_health():
    return _load(HEALTH_FILE, {
        "water_count":0,"water_goal":8,
        "sleep_start":None,"sleep_end":None,
        "medications":[],"weight_log":[],
        "exercise_log":[],"last_reset":datetime.date.today().isoformat()
    })

def save_health(h):
    _save(HEALTH_FILE, h)

def log_water():
    h = load_health()
    today = datetime.date.today().isoformat()
    if h.get("last_reset") != today:
        h["water_count"] = 0
        h["last_reset"] = today
    h["water_count"] += 1
    save_health(h)
    return h["water_count"], h["water_goal"]

# ── Bütçe ────────────────────────────────────────────────────────────────────
def load_budget():
    return _load(BUDGET_FILE, {"income":0,"expenses":[],"limit":5000})

def add_expense(amount, category, note=""):
    b = load_budget()
    b["expenses"].append({"amount":amount,"category":category,
                          "note":note,"date":datetime.datetime.now().isoformat()})
    _save(BUDGET_FILE, b)

def get_monthly_total():
    b = load_budget()
    now = datetime.datetime.now()
    total = sum(e["amount"] for e in b["expenses"]
                if datetime.datetime.fromisoformat(e["date"]).month == now.month)
    return total, b["limit"]

# ── Log ──────────────────────────────────────────────────────────────────────
def log_event(event, data=None):
    logs = _load(LOG_FILE, [])
    logs.append({"event":event,"data":data,"time":datetime.datetime.now().isoformat()})
    if len(logs) > 1000: logs = logs[-1000:]
    _save(LOG_FILE, logs)

def get_daily_log():
    logs = _load(LOG_FILE, [])
    today = datetime.date.today().isoformat()
    return [l for l in logs if l["time"].startswith(today)]
