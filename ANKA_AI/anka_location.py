# ── ANKA KONUM MODÜLü ────────────────────────────────────────────────────────
import json, os, threading, time, requests
from anka_config import BASE_DIR

LOCATION_FILE = os.path.join(BASE_DIR, "anka_locations.json")

def _load():
    try:
        if os.path.exists(LOCATION_FILE):
            with open(LOCATION_FILE,"r",encoding="utf-8") as f: return json.load(f)
    except: pass
    return {"saved_places":{}, "reminders":[]}

def _save(data):
    try:
        with open(LOCATION_FILE,"w",encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except: pass

def get_current_location():
    """IP tabanlı yaklaşık konum (GPS yoksa fallback)"""
    try:
        r = requests.get("http://ip-api.com/json/", timeout=5)
        d = r.json()
        return {"lat": d.get("lat"), "lon": d.get("lon"),
                "city": d.get("city"), "address": f"{d.get('city','')}, {d.get('regionName','')}"}
    except:
        return None

def save_place(name, lat=None, lon=None):
    """Ev, iş gibi önemli yerleri kaydet"""
    data = _load()
    if lat is None or lon is None:
        loc = get_current_location()
        if loc:
            lat, lon = loc["lat"], loc["lon"]
    if lat is not None:
        data["saved_places"][name.lower()] = {"lat": lat, "lon": lon}
        _save(data)
        return True
    return False

def get_saved_places():
    return _load()["saved_places"]

def add_location_reminder(place_name, message):
    """Belirli bir yere varınca hatırlat"""
    data = _load()
    data["reminders"].append({
        "place": place_name.lower(),
        "message": message,
        "active": True,
        "triggered": False
    })
    _save(data)

def _distance_km(lat1, lon1, lat2, lon2):
    from math import radians, sin, cos, sqrt, atan2
    R = 6371
    dlat = radians(lat2-lat1); dlon = radians(lon2-lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1))*cos(radians(lat2))*sin(dlon/2)**2
    return R * 2*atan2(sqrt(a), sqrt(1-a))


class LocationMonitor:
    """Arka planda periyodik konum kontrolü yapar, kayıtlı yerlere yaklaşınca hatırlatır"""
    def __init__(self, speak_func, msg_func, check_interval=300):
        self.speak = speak_func
        self.msg = msg_func
        self.check_interval = check_interval  # saniye, varsayılan 5 dakika
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def _loop(self):
        # İlk kontrolden önce biraz bekle (uygulama açılışı)
        time.sleep(10)
        while self.running:
            try:
                self._check()
            except Exception as e:
                print(f"Konum kontrol hatası: {e}")
            time.sleep(self.check_interval)

    def _check(self):
        current = get_current_location()
        if not current or current["lat"] is None:
            return

        data = _load()
        places = data["saved_places"]
        reminders = data["reminders"]

        for reminder in reminders:
            if not reminder.get("active", True) or reminder.get("triggered", False):
                continue
            place_name = reminder["place"]
            if place_name not in places:
                continue
            place = places[place_name]
            dist = _distance_km(current["lat"], current["lon"], place["lat"], place["lon"])
            if dist < 0.5:  # 500 metre yakınlık eşiği
                msg = reminder["message"]
                self.msg("SİSTEM", f"📍 {place_name.capitalize()}'e vardınız: {msg}")
                self.speak(f"Efendim, {place_name} konumuna vardınız. {msg}")
                reminder["triggered"] = True

        _save(data)

    def stop(self):
        self.running = False


def handle_location_command(text, speak, msg):
    """Konum komutlarını işle, anka_commands.py'den çağrılabilir"""
    t = text.lower().strip()

    # Konumu kaydet — "burayı ev olarak kaydet"
    if "burayı" in t and "kaydet" in t:
        for keyword in ["ev","iş","işyeri","okul","spor salonu"]:
            if keyword in t:
                ok = save_place(keyword)
                if ok:
                    r = f"✓ Bu konum '{keyword}' olarak kaydedildi efendim."
                else:
                    r = "Konum alınamadı. GPS/internet bağlantınızı kontrol edin."
                msg("ANKA", r); speak(r)
                return True
        # Genel isimle kaydet
        name = t.replace("burayı","").replace("olarak kaydet","").replace("kaydet","").strip()
        if name:
            ok = save_place(name)
            r = f"✓ Bu konum '{name}' olarak kaydedildi efendim." if ok else "Konum alınamadı."
            msg("ANKA", r); speak(r)
            return True

    # Mevcut konum — "neredeyim"
    if "neredeyim" in t or "konumum" in t:
        loc = get_current_location()
        if loc:
            r = f"📍 Şu anki konumunuz: {loc['address']}"
        else:
            r = "Konum bilgisi alınamadı efendim."
        msg("ANKA", r); speak(r)
        return True

    # Kayıtlı yerler — "kayıtlı yerlerim"
    if "kayıtlı yer" in t or "kayıtlı konum" in t:
        places = get_saved_places()
        if not places:
            r = "Henüz kayıtlı yeriniz yok efendim."
        else:
            r = "📍 Kayıtlı yerleriniz:\n" + "\n".join(f"• {p.capitalize()}" for p in places.keys())
        msg("ANKA", r); speak(r)
        return True

    # Konum hatırlatıcı — "eve gelince çöpü çıkar diye hatırlat"
    if "gelince" in t and "hatırlat" in t:
        for place in get_saved_places().keys():
            if place in t:
                message = t.split("hatırlat")[0].split("gelince")[-1].strip()
                if not message:
                    message = t.split(place)[-1].replace("gelince","").replace("hatırlat","").strip()
                add_location_reminder(place, message or "Hatırlatma")
                r = f"✓ {place.capitalize()}'e gelince hatırlatacağım efendim."
                msg("ANKA", r); speak(r)
                return True

    return False
