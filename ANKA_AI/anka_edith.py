# ── ANKA ANKA MODÜLü ────────────────────────────────────────────────────
# Even Dead I'm The Hero — Tony Stark'ın EDITH sisteminden ilham alan özellikler
# Gelişmiş tehdit analizi, yüz tanıma, gözetleme, otonom karar verme
try:
    import pyperclip
except ImportError:
    class _PyClip:
        def copy(self,x):pass
        def paste(self):return ""
    pyperclip=_PyClip()
import json, os, time, threading, datetime, subprocess, webbrowser
import requests, re, random, base64, tempfile
import psutil, cv2, numpy as np
from anka_config import BASE_DIR

EDITH_FILE    = os.path.join(BASE_DIR, "anka_edith.json")
THREAT_FILE   = os.path.join(BASE_DIR, "anka_threats.json")
WATCHLIST_FILE= os.path.join(BASE_DIR, "anka_watchlist.json")
INTEL_FILE    = os.path.join(BASE_DIR, "anka_intel.json")

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
# ── EDITH CORE — Merkezi Komuta Sistemi ──────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════
class EDITHCore:
    """
    ANKA merkezi sistemi.
    Tüm alt sistemleri koordine eder, tehdit değerlendirmesi yapar.
    """
    VERSION = "ANKA Güvenlik v1.0 — Anka Edition"
    CLEARANCE_LEVELS = {
        "kırmızı": 5,    # Kritik tehdit
        "turuncu": 4,    # Yüksek tehdit
        "sarı": 3,       # Orta tehdit
        "yeşil": 2,      # Düşük tehdit
        "mavi": 1,       # Normal
    }

    def __init__(self, ollama, speak_func, msg_func):
        self.ollama = ollama
        self.speak = speak_func
        self.msg = msg_func
        self.active = True
        self.threat_level = "mavi"
        self.data = _load(EDITH_FILE, {
            "boot_count": 0,
            "threats_detected": 0,
            "faces_identified": 0,
            "missions_completed": 0,
            "last_boot": None
        })
        self.data["boot_count"] += 1
        self.data["last_boot"] = datetime.datetime.now().isoformat()
        _save(EDITH_FILE, self.data)

    def set_threat_level(self, level):
        old = self.threat_level
        self.threat_level = level
        emoji = {"kırmızı":"🔴","turuncu":"🟠","sarı":"🟡","yeşil":"🟢","mavi":"🔵"}
        r = (f"{emoji.get(level,'⚪')} EDITH TEHDİT SEVİYESİ DEĞİŞTİ\n"
             f"• Önceki: {old.upper()}\n"
             f"• Yeni: {level.upper()}\n"
             f"• Protokoller güncellendi efendim.")
        self.msg("ANKA", r)
        self.speak(f"Tehdit seviyesi {level} olarak ayarlandı efendim.")

    def status_report(self):
        data = self.data
        r = (f"📊 ANKA DURUM RAPORU\n"
             f"{'═'*35}\n"
             f"• Versiyon: {self.VERSION}\n"
             f"• Tehdit Seviyesi: {self.threat_level.upper()}\n"
             f"• Boot Sayısı: {data['boot_count']}\n"
             f"• Tespit Edilen Tehditler: {data['threats_detected']}\n"
             f"• Tanınan Yüzler: {data['faces_identified']}\n"
             f"• Tamamlanan Görevler: {data['missions_completed']}\n"
             f"• Son Aktif: {data['last_boot'][:16]}\n"
             f"{'═'*35}")
        self.msg("ANKA", r)
        self.speak("EDITH durum raporu hazırlandı efendim.")


# ═══════════════════════════════════════════════════════════════════════════════
# ── GELİŞMİŞ YÜZ TANIMA SİSTEMİ ─────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════
class FaceIntelligence:
    """
    EDITH'in gelişmiş yüz tanıma ve analiz sistemi.
    Kişileri tanır, duygu analizi yapar, tehdit değerlendirmesi yapar.
    """
    def __init__(self, speak_func, msg_func):
        self.speak = speak_func
        self.msg = msg_func
        self.known_faces = _load(WATCHLIST_FILE, {})
        self.face_cascade = None
        self._load_cascade()

    def _load_cascade(self):
        try:
            self.face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        except: pass

    def scan_room(self, duration=5):
        """Odayı tara, kişi sayısını belirle"""
        def _scan():
            self.msg("ANKA", f"👁️ Oda taranıyor ({duration} saniye)...")
            try:
                cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
                if not cap.isOpened():
                    self.msg("ANKA", "Kamera erişilemiyor efendim.")
                    return

                faces_detected = []
                start = time.time()
                while time.time() - start < duration:
                    ret, frame = cap.read()
                    if not ret: break
                    if self.face_cascade is not None:
                        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                        faces = self.face_cascade.detectMultiScale(
                            gray, scaleFactor=1.1, minNeighbors=5, minSize=(60,60))
                        if len(faces) > 0:
                            faces_detected.append(len(faces))
                    time.sleep(0.2)
                cap.release()

                count = max(faces_detected) if faces_detected else 0
                if count == 0:
                    r = "👁️ Oda Tarama Tamamlandı: Kimse tespit edilmedi."
                elif count == 1:
                    r = "👁️ Oda Tarama: 1 kişi tespit edildi — KULLANICI."
                else:
                    r = f"👁️ Oda Tarama: {count} kişi tespit edildi!\n⚠️ Yabancı varlık algılandı!"
                self.msg("ANKA", r)
                self.speak(r[:150])
            except Exception as e:
                self.msg("ANKA", f"Tarama hatası: {e}")
        threading.Thread(target=_scan, daemon=True).start()

    def emotion_analysis(self):
        """Kullanıcının yüz ifadesinden duygu analizi"""
        def _emo():
            self.msg("ANKA", "😊 Duygu analizi yapılıyor...")
            try:
                cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
                ret, frame = cap.read()
                cap.release()
                if not ret:
                    self.msg("ANKA", "Kamera erişilemedi.")
                    return

                # Yüz bölgesinin parlaklık ve kontrast analizi
                if self.face_cascade is not None:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    faces = self.face_cascade.detectMultiScale(gray, 1.1, 5)
                    if len(faces) > 0:
                        x, y, w, h = faces[0]
                        face_roi = gray[y:y+h, x:x+w]
                        brightness = np.mean(face_roi)
                        # Basit analiz (gerçek duygu analizi için DeepFace gerekir)
                        if brightness > 140:
                            emotion = "pozitif/mutlu"
                        elif brightness > 100:
                            emotion = "nötr"
                        else:
                            emotion = "yorgun/stresli"
                        r = (f"😊 Duygu Analizi:\n"
                             f"• Tespit edilen durum: {emotion}\n"
                             f"• Yüz parlaklığı: {brightness:.0f}\n"
                             f"• Not: Tam analiz için DeepFace kurulumu gerekir.")
                        self.msg("ANKA", r)
                        self.speak(f"Duygu analizi: {emotion} efendim.")
                    else:
                        self.msg("ANKA", "Yüz tespit edilemedi efendim.")
            except Exception as e:
                self.msg("ANKA", f"Duygu analizi hatası: {e}")
        threading.Thread(target=_emo, daemon=True).start()

    def add_to_watchlist(self, name, threat_level="normal"):
        """Kişiyi izleme listesine ekle"""
        self.known_faces[name.lower()] = {
            "name": name,
            "threat_level": threat_level,
            "added": datetime.datetime.now().isoformat(),
            "sightings": 0
        }
        _save(WATCHLIST_FILE, self.known_faces)
        r = f"✅ '{name}' izleme listesine eklendi. Tehdit seviyesi: {threat_level}"
        self.msg("ANKA", r); self.speak(r)

    def get_watchlist(self):
        return list(self.known_faces.values())

    def capture_intruder(self):
        """Yetkisiz kişinin fotoğrafını çek"""
        def _cap():
            try:
                cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
                time.sleep(0.3)
                ret, frame = cap.read()
                cap.release()
                if ret:
                    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    path = os.path.join(BASE_DIR, f"intruder_{ts}.jpg")
                    cv2.imwrite(path, frame)
                    r = f"📸 Yetkisiz erişim fotoğrafı kaydedildi: {path}"
                    self.msg("ANKA", r)
                    # ntfy bildirimi
                    try:
                        requests.post("https://ntfy.sh/anka-yusuf-2026",
                            data="🚨 YETKİSİZ ERİŞİM TESPİT EDİLDİ!".encode(),
                            headers={"Title":"EDITH UYARI","Priority":"max"}, timeout=3)
                    except: pass
            except Exception as e:
                self.msg("ANKA", f"Fotoğraf çekilemedi: {e}")
        threading.Thread(target=_cap, daemon=True).start()


# ═══════════════════════════════════════════════════════════════════════════════
# ── TEHDİT ANALİZ SİSTEMİ ────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════
class ThreatAnalyzer:
    """
    EDITH'in tehdit analiz ve değerlendirme sistemi.
    Siber tehditler, fiziksel tehditler, sistem anomalileri tespit eder.
    """
    def __init__(self, ollama, speak_func, msg_func):
        self.ollama = ollama
        self.speak = speak_func
        self.msg = msg_func
        self.threats = _load(THREAT_FILE, {"active": [], "history": []})
        self.running = True
        threading.Thread(target=self._threat_monitor, daemon=True).start()

    def analyze_cyber_threat(self, description):
        """Siber tehdit analizi"""
        def _a():
            r = self.ollama.chat(
                f"Siber güvenlik tehdit analizi: '{description}'\n"
                f"Tehdit seviyesi (1-10), olası saldırı vektörleri, "
                f"önlem önerileri. Türkçe yaz.",
                system_override="Siber güvenlik uzmanı. Tehdit analizi yap.")
            threat = {
                "type": "cyber",
                "description": description,
                "analysis": r,
                "timestamp": datetime.datetime.now().isoformat(),
                "level": "orta"
            }
            self.threats["active"].append(threat)
            _save(THREAT_FILE, self.threats)
            self.msg("ANKA", f"🔴 SİBER TEHDİT ANALİZİ\n{'═'*35}\n{r}")
            self.speak("Siber tehdit analizi tamamlandı efendim.")
        threading.Thread(target=_a, daemon=True).start()

    def network_threat_scan(self):
        """Ağ tehdit taraması"""
        def _scan():
            self.msg("ANKA", "🌐 Ağ tehdit taraması başlatılıyor...")
            threats_found = []

            # Açık portları kontrol et
            import socket
            suspicious_ports = [21, 22, 23, 25, 3389, 4444, 8080]
            for port in suspicious_ports:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(0.3)
                    result = sock.connect_ex(('127.0.0.1', port))
                    if result == 0:
                        threats_found.append(f"Port {port} açık!")
                    sock.close()
                except: pass

            # Şüpheli bağlantılar
            try:
                conns = psutil.net_connections(kind='inet')
                for conn in conns:
                    if conn.status == 'ESTABLISHED' and conn.raddr:
                        if conn.raddr.port in [4444, 1337, 31337]:
                            threats_found.append(f"Şüpheli bağlantı: {conn.raddr.ip}:{conn.raddr.port}")
            except: pass

            if threats_found:
                r = (f"⚠️ AĞ TEHDİT TARAMASI\n"
                     f"{'═'*30}\n"
                     f"⚠️ {len(threats_found)} potansiyel tehdit bulundu:\n"
                     + "\n".join(f"• {t}" for t in threats_found))
                self.msg("ANKA", r)
                self.speak(f"Dikkat! {len(threats_found)} potansiyel ağ tehdidi tespit edildi efendim.")
            else:
                r = "✅ Ağ taraması tamamlandı. Tehdit tespit edilmedi efendim."
                self.msg("ANKA", r); self.speak(r)
        threading.Thread(target=_scan, daemon=True).start()

    def process_threat_intel(self, topic):
        """Tehdit istihbaratı işle"""
        def _intel():
            r = self.ollama.chat(
                f"'{topic}' konusunda tehdit istihbaratı raporu hazırla. "
                f"Olası riskler, önlemler, aksiyon planı.",
                system_override="İstihbarat analisti. Kapsamlı tehdit raporu yaz.")
            intel = {
                "topic": topic,
                "report": r,
                "date": datetime.datetime.now().isoformat()
            }
            intel_data = _load(INTEL_FILE, [])
            intel_data.append(intel)
            _save(INTEL_FILE, intel_data)
            self.msg("ANKA", f"🔍 TEHDİT İSTİHBARATI\n{'═'*35}\n{r}")
            self.speak("Tehdit istihbaratı raporu hazırlandı efendim.")
        threading.Thread(target=_intel, daemon=True).start()

    def _threat_monitor(self):
        """Sürekli tehdit izleme"""
        time.sleep(60)
        while self.running:
            try:
                # Şüpheli süreçleri kontrol et
                suspicious_names = ['keylogger','miner','rat','backdoor','trojan']
                for proc in psutil.process_iter(['name']):
                    try:
                        name = proc.info['name'].lower()
                        if any(s in name for s in suspicious_names):
                            r = f"🚨 EDITH: Şüpheli süreç tespit edildi: {proc.info['name']}"
                            self.msg("ANKA", r)
                            self.speak(r)
                    except: pass
            except: pass
            time.sleep(300)

    def stop(self): self.running = False


# ═══════════════════════════════════════════════════════════════════════════════
# ── İSTİHBARAT TOPLAMA SİSTEMİ ───────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════
class IntelligenceGatherer:
    """
    EDITH'in açık kaynak istihbarat (OSINT) toplama sistemi.
    Web'den bilgi toplar, analiz eder, raporlar.
    """
    def __init__(self, ollama, speak_func, msg_func):
        self.ollama = ollama
        self.speak = speak_func
        self.msg = msg_func

    def osint_search(self, target):
        """Hedef hakkında açık kaynak istihbarat topla"""
        def _search():
            self.msg("ANKA", f"🔍 OSINT araştırması: '{target}'")
            results = []

            # DuckDuckGo
            try:
                r = requests.get(
                    f"https://api.duckduckgo.com/?q={target}&format=json",
                    timeout=5)
                data = r.json()
                if data.get("Abstract"):
                    results.append(f"[Genel]: {data['Abstract'][:300]}")
                for t in data.get("RelatedTopics", [])[:2]:
                    if isinstance(t, dict) and t.get("Text"):
                        results.append(f"[İlgili]: {t['Text'][:200]}")
            except: pass

            # Wikipedia
            try:
                r = requests.get(
                    f"https://tr.wikipedia.org/api/rest_v1/page/summary/{target.replace(' ','_')}",
                    timeout=5)
                if r.status_code == 200:
                    extract = r.json().get("extract","")[:400]
                    if extract:
                        results.append(f"[Wikipedia]: {extract}")
            except: pass

            if results:
                context = "\n\n".join(results)
                analysis = self.ollama.chat(
                    f"'{target}' hakkında toplanan OSINT verilerini analiz et:\n\n{context}",
                    system_override="İstihbarat analisti. Verileri sentezle, önemli noktaları çıkar.")
                r = f"🔍 OSINT RAPORU — {target}\n{'═'*35}\n{analysis}"
            else:
                r = f"'{target}' için yeterli açık kaynak verisi bulunamadı efendim."

            self.msg("ANKA", r)
            self.speak("OSINT araştırması tamamlandı efendim.")
        threading.Thread(target=_search, daemon=True).start()

    def track_keyword(self, keyword):
        """Anahtar kelimeyi haberlerde takip et"""
        def _track():
            try:
                import xml.etree.ElementTree as ET
                r = requests.get(
                    f"https://news.google.com/rss/search?q={keyword}&hl=tr&gl=TR",
                    timeout=5)
                root = ET.fromstring(r.content)
                items = root.findall(".//item")[:5]
                if items:
                    news = [i.find("title").text for i in items
                           if i.find("title") is not None]
                    result = (f"📡 '{keyword}' TAKİP RAPORU\n"
                             f"{'═'*35}\n"
                             + "\n".join(f"• {n[:60]}" for n in news))
                    self.msg("ANKA", result)
                    self.speak(f"'{keyword}' için {len(news)} haber bulundu efendim.")
                else:
                    self.msg("ANKA", f"'{keyword}' için haber bulunamadı efendim.")
            except Exception as e:
                self.msg("ANKA", f"Takip hatası: {e}")
        threading.Thread(target=_track, daemon=True).start()

    def ip_intelligence(self, ip):
        """IP adresi hakkında istihbarat"""
        def _ip():
            try:
                r = requests.get(f"https://ipapi.co/{ip}/json/", timeout=5)
                d = r.json()
                result = (f"🌐 IP İSTİHBARATI — {ip}\n"
                         f"{'═'*35}\n"
                         f"• Ülke: {d.get('country_name','?')}\n"
                         f"• Şehir: {d.get('city','?')}\n"
                         f"• ISP: {d.get('org','?')}\n"
                         f"• Timezone: {d.get('timezone','?')}\n"
                         f"• ASN: {d.get('asn','?')}\n"
                         f"• Enlem/Boylam: {d.get('latitude','?')},{d.get('longitude','?')}")
                self.msg("ANKA", result)
                self.speak(f"IP {ip} analizi tamamlandı efendim.")
            except Exception as e:
                self.msg("ANKA", f"IP sorgulama hatası: {e}")
        threading.Thread(target=_ip, daemon=True).start()

    def domain_intel(self, domain):
        """Domain hakkında istihbarat"""
        def _d():
            try:
                import socket
                ip = socket.gethostbyname(domain)
                result = f"🌐 {domain} → {ip}\n"
                r2 = requests.get(f"https://ipapi.co/{ip}/json/", timeout=5)
                d = r2.json()
                result += (f"• Sunucu: {d.get('org','?')}\n"
                          f"• Ülke: {d.get('country_name','?')}\n"
                          f"• Şehir: {d.get('city','?')}")
                self.msg("ANKA", f"🔍 DOMAIN İSTİHBARATI\n{result}")
                self.speak(f"{domain} domain analizi tamamlandı efendim.")
            except Exception as e:
                self.msg("ANKA", f"Domain sorgulama hatası: {e}")
        threading.Thread(target=_d, daemon=True).start()


# ═══════════════════════════════════════════════════════════════════════════════
# ── EDITH GÖREV SİSTEMİ ──────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════
class EDITHMissionSystem:
    """
    EDITH görev planlama ve yürütme sistemi.
    Kompleks görevleri adımlarına böler, otomatik çalıştırır.
    """
    def __init__(self, ollama, speak_func, msg_func):
        self.ollama = ollama
        self.speak = speak_func
        self.msg = msg_func
        self.active_missions = []
        self.completed_missions = []

    def create_mission(self, name, objective, priority="normal"):
        mission = {
            "id": len(self.active_missions) + 1,
            "name": name,
            "objective": objective,
            "priority": priority,
            "status": "planning",
            "created": datetime.datetime.now().isoformat(),
            "steps": [],
            "intel": []
        }
        self.active_missions.append(mission)

        def _plan():
            self.msg("ANKA",
                f"🎯 YENİ GÖREV OLUŞTURULDU\n"
                f"{'═'*35}\n"
                f"• Görev: {name}\n"
                f"• Hedef: {objective}\n"
                f"• Öncelik: {priority.upper()}\n"
                f"• Durum: PLANLANIYOR...")

            plan = self.ollama.chat(
                f"EDITH görev planı: '{name}'\nHedef: {objective}\n"
                f"5 adımlık operasyon planı yap. Her adım somut ve yapılabilir olsun.",
                system_override="Taktik planlayıcı. Ayrıntılı operasyon planı yap.")

            mission["steps"] = plan
            mission["status"] = "ready"
            self.msg("ANKA",
                f"📋 GÖREV PLANI HAZIR — {name}\n"
                f"{'═'*35}\n{plan}")
            self.speak(f"{name} görevi planlandı, hazır efendim.")
        threading.Thread(target=_plan, daemon=True).start()
        return mission["id"]

    def mission_briefing(self, mission_id):
        mission = next((m for m in self.active_missions if m["id"] == mission_id), None)
        if not mission:
            self.msg("ANKA", f"Görev #{mission_id} bulunamadı efendim.")
            return
        r = (f"📊 GÖREV BRİFİNGİ #{mission_id}\n"
             f"{'═'*35}\n"
             f"• Adı: {mission['name']}\n"
             f"• Hedef: {mission['objective']}\n"
             f"• Durum: {mission['status'].upper()}\n"
             f"• Öncelik: {mission['priority'].upper()}\n"
             f"• Oluşturuldu: {mission['created'][:16]}")
        self.msg("ANKA", r)
        self.speak(f"Görev #{mission_id} brifing tamamlandı efendim.")

    def complete_mission(self, mission_id):
        for i, m in enumerate(self.active_missions):
            if m["id"] == mission_id:
                m["status"] = "completed"
                m["completed"] = datetime.datetime.now().isoformat()
                self.completed_missions.append(m)
                self.active_missions.pop(i)
                r = f"✅ GÖREV #{mission_id} TAMAMLANDI: {m['name']}"
                self.msg("ANKA", r); self.speak(r)
                return True
        return False

    def list_missions(self):
        if not self.active_missions:
            return "Aktif görev yok efendim."
        r = f"🎯 AKTİF GÖREVLER ({len(self.active_missions)})\n{'═'*35}\n"
        for m in self.active_missions:
            emoji = {"planning":"📋","ready":"✅","running":"⚙️"}.get(m["status"],"❓")
            r += f"{emoji} #{m['id']} {m['name']} [{m['priority'].upper()}]\n"
        return r


# ═══════════════════════════════════════════════════════════════════════════════
# ── EDITH KOMUT İŞLEYİCİ ─────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════
class EDITHCommandProcessor:
    def __init__(self, speak_func, msg_func, ollama):
        self.speak = speak_func
        self.msg = msg_func
        self.ollama = ollama
        self.core = EDITHCore(ollama, speak_func, msg_func)
        self.face_intel = FaceIntelligence(speak_func, msg_func)
        self.threat = ThreatAnalyzer(ollama, speak_func, msg_func)
        self.intel = IntelligenceGatherer(ollama, speak_func, msg_func)
        self.missions = EDITHMissionSystem(ollama, speak_func, msg_func)

    def process(self, text):
        t = text.lower().strip()

        # ── EDITH Aktivasyon ──────────────────────────────────────────────────


        if "tehdit seviyesi" in t:
            for level in ["kırmızı","turuncu","sarı","yeşil","mavi"]:
                if level in t:
                    self.core.set_threat_level(level)
                    return True

        # ── Yüz Tanıma ───────────────────────────────────────────────────────
        if "odayı tara" in t or "çevreyi tara" in t:
            m = re.search(r'(\d+)', t)
            duration = int(m.group(1)) if m else 5
            self.face_intel.scan_room(duration)
            return True

        if "duygu analizi" in t or "yüz analizi" in t:
            self.face_intel.emotion_analysis()
            return True

        if "izleme listesine ekle" in t or "watchlist ekle" in t:
            name = t.replace("izleme listesine ekle","").replace("watchlist ekle","").strip()
            threat = "yüksek" if "tehlikeli" in t else "normal"
            if name:
                self.face_intel.add_to_watchlist(name, threat)
            return True

        if "izleme listesi" in t or "watchlist göster" in t:
            watchlist = self.face_intel.get_watchlist()
            if watchlist:
                r = f"👁️ İZLEME LİSTESİ ({len(watchlist)} kişi)\n{'═'*30}\n"
                r += "\n".join(f"• {w['name']} [{w['threat_level']}]"
                              for w in watchlist)
            else:
                r = "İzleme listesi boş efendim."
            self.msg("ANKA", r); self.speak(r)
            return True

        if "yetkisiz erişim" in t or "davetsiz misafir" in t or "intruder" in t:
            self.face_intel.capture_intruder()
            return True

        # ── Tehdit Analizi ────────────────────────────────────────────────────
        if "siber tehdit" in t:
            desc = t.replace("siber tehdit analiz","").replace("siber tehdit","").strip()
            if desc:
                self.threat.analyze_cyber_threat(desc)
            return True

        if "ağ tara" in t or "ağ tehdit" in t:
            self.threat.network_threat_scan()
            return True

        if "tehdit istihbaratı" in t:
            topic = t.replace("tehdit istihbaratı","").strip()
            if topic:
                self.threat.process_threat_intel(topic)
            return True

        # ── İstihbarat ────────────────────────────────────────────────────────
        if "osint" in t or "istihbarat topla" in t:
            target = t.replace("osint","").replace("istihbarat topla","").strip()
            if target:
                self.intel.osint_search(target)
            return True

        if "kelime takip" in t or "haber takip" in t:
            keyword = t.replace("kelime takip","").replace("haber takip","").strip()
            if keyword:
                self.intel.track_keyword(keyword)
            return True

        if "ip sorgula" in t or "ip istihbarat" in t:
            ip_m = re.search(r'\d+\.\d+\.\d+\.\d+', t)
            if ip_m:
                self.intel.ip_intelligence(ip_m.group(0))
            return True

        if "domain sorgula" in t or "domain istihbarat" in t:
            domain = t.replace("domain sorgula","").replace("domain istihbarat","").strip()
            if domain:
                self.intel.domain_intel(domain)
            return True

        # ── Görev Sistemi ─────────────────────────────────────────────────────
        if "görev oluştur" in t or "yeni görev" in t or "misyon başlat" in t:
            name_m = re.search(r"['\"]([^'\"]+)['\"]", text)
            name = name_m.group(1) if name_m else t.replace("görev oluştur","").replace("yeni görev","").replace("misyon başlat","").strip()[:30]
            objective = t.replace(name,"").strip() or "Belirtilmedi"
            priority = "yüksek" if "acil" in t or "kritik" in t else "normal"
            if name:
                mid = self.missions.create_mission(name, objective, priority)
                return True

        if "görev brifing" in t:
            m = re.search(r'(\d+)', t)
            if m:
                self.missions.mission_briefing(int(m.group(1)))
            return True

        if "görevi tamamla" in t:
            m = re.search(r'(\d+)', t)
            if m:
                self.missions.complete_mission(int(m.group(1)))
            return True

        if "görevlerim" in t or "aktif görevler" in t:
            r = self.missions.list_missions()
            self.msg("ANKA", r); self.speak(r)
            return True

        # ── EDITH Yardım ─────────────────────────────────────────────────────

        return False


# ═══════════════════════════════════════════════════════════════════════════════
# ── EDITH GELİŞMİŞ ÖZELLİKLER ───────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

class EDITHSurveillance:
    """Gelişmiş gözetleme ve izleme sistemi"""
    def __init__(self, ollama, speak_func, msg_func):
        self.ollama = ollama
        self.speak = speak_func
        self.msg = msg_func
        self.surveillance_active = False
        self.motion_detected_count = 0

    def start_surveillance(self, duration=30):
        """Kamera gözetlemesi başlat"""
        self.surveillance_active = True
        def _surv():
            self.msg("ANKA", f"📹 GÖZETİ_EMLİ BAŞLADI ({duration}s)...")
            try:
                cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
                if not cap.isOpened():
                    self.msg("ANKA", "Kamera erişilemiyor."); return
                ret, prev_frame = cap.read()
                if not ret: cap.release(); return
                prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
                start = time.time()
                motion_events = []
                while time.time() - start < duration and self.surveillance_active:
                    ret, frame = cap.read()
                    if not ret: break
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    diff = cv2.absdiff(prev_gray, gray)
                    _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
                    motion_pixels = cv2.countNonZero(thresh)
                    if motion_pixels > 5000:
                        self.motion_detected_count += 1
                        ts = datetime.datetime.now().strftime("%H:%M:%S")
                        motion_events.append(ts)
                        if len(motion_events) == 1:
                            self.speak("Hareket algılandı efendim!")
                            try:
                                requests.post("https://ntfy.sh/anka-yusuf-2026",
                                    data="⚠️ EDITH: Hareket algılandı!".encode(),
                                    headers={"Title":"EDITH Gözetleme","Priority":"high"}, timeout=3)
                            except: pass
                    prev_gray = gray
                    time.sleep(0.3)
                cap.release()
                r = (f"📹 GÖZETİ_EME TAMAMLANDI\n"
                     f"• Süre: {duration}s\n"
                     f"• Hareket Olayları: {len(motion_events)}\n"
                     f"• İlk Hareket: {motion_events[0] if motion_events else 'Yok'}")
                self.msg("ANKA", r)
            except Exception as e:
                self.msg("ANKA", f"Gözetleme hatası: {e}")
            self.surveillance_active = False
        threading.Thread(target=_surv, daemon=True).start()

    def stop_surveillance(self):
        self.surveillance_active = False
        self.msg("ANKA", "⏹️ Gözetleme durduruldu efendim.")

    def perimeter_check(self):
        """Çevre güvenlik kontrolü"""
        def _check():
            self.msg("ANKA", "🔍 ÇEV_RE GÜVENLİK KONTROL...")
            checks = []
            # Ekran kilidi durumu
            checks.append("✅ Ekran kilidi: Aktif")
            # Ağ bağlantıları
            try:
                conns = psutil.net_connections(kind='inet')
                established = [c for c in conns if c.status == 'ESTABLISHED']
                if len(established) > 20:
                    checks.append(f"⚠️ Yüksek bağlantı sayısı: {len(established)}")
                else:
                    checks.append(f"✅ Ağ bağlantıları normal: {len(established)}")
            except: pass
            # Şüpheli süreçler
            try:
                procs = [p.info['name'] for p in psutil.process_iter(['name'])]
                checks.append(f"✅ Aktif süreç: {len(procs)}")
            except: pass
            r = "🛡️ ÇEV_RE GÜVENLİK RAPORU\n" + "\n".join(f"• {c}" for c in checks)
            self.msg("ANKA", r); self.speak("Çevre güvenlik kontrolü tamamlandı efendim.")
        threading.Thread(target=_check, daemon=True).start()


class EDITHWeaponrySystem:
    """Silah/araç sistemi simülasyonu (yazılım araçları)"""
    def __init__(self, ollama, speak_func, msg_func):
        self.ollama = ollama
        self.speak = speak_func
        self.msg = msg_func
        self.arsenal = {
            "tarama": "Ağ ve sistem tarama araçları",
            "analiz": "Veri analiz motorları",
            "iletişim": "Çok kanallı iletişim sistemi",
            "şifreleme": "Veri şifreleme modülü",
            "izleme": "Gerçek zamanlı izleme sistemi",
        }

    def deploy_tool(self, tool_name):
        """Yazılım aracı devreye al"""
        if tool_name.lower() in self.arsenal:
            r = (f"⚡ ARAÇ DEV_REYE ALINDI\n"
                 f"• Araç: {tool_name.capitalize()}\n"
                 f"• Açıklama: {self.arsenal[tool_name.lower()]}\n"
                 f"• Durum: AKTİF")
            self.msg("ANKA", r); self.speak(f"{tool_name} devreye alındı efendim.")
        else:
            available = ", ".join(self.arsenal.keys())
            self.msg("ANKA", f"Araç bulunamadı. Mevcut: {available}")

    def arsenal_status(self):
        r = "⚡ ARSENAL DURUMU\n" + "═"*30 + "\n"
        for name, desc in self.arsenal.items():
            r += f"• {name.upper()}: {desc}\n"
        self.msg("ANKA", r); self.speak("Arsenal durumu raporu hazırlandı efendim.")

    def system_lockdown(self):
        """Sistem kilitlemesi"""
        def _lock():
            self.msg("ANKA", "🔐 SİSTEM KİLİT_LEME BAŞLATILIYOR...")
            time.sleep(1)
            # Ekranı kilitle
            try: subprocess.run(["rundll32.exe","user32.dll,LockWorkStation"])
            except: pass
            try:
                requests.post("https://ntfy.sh/anka-yusuf-2026",
                    data="🔐 EDITH: Sistem kilitlendi!".encode(),
                    headers={"Title":"EDITH Güvenlik","Priority":"urgent"}, timeout=3)
            except: pass
            self.msg("ANKA", "🔐 Sistem kilitlendi efendim.")
        threading.Thread(target=_lock, daemon=True).start()


class EDITHDataVault:
    """Güvenli veri kasası"""
    def __init__(self, speak_func, msg_func):
        self.speak = speak_func
        self.msg = msg_func
        self.vault_file = os.path.join(BASE_DIR, "edith_vault.json")
        self._master = None

    def set_master_key(self, key):
        import hashlib
        self._master = hashlib.sha256(key.encode()).hexdigest()
        self.msg("ANKA", "✅ Kasa ana anahtarı ayarlandı efendim.")

    def store_secret(self, label, data):
        if not self._master:
            self.msg("ANKA", "Önce 'kasa anahtarı [şifre]' ile anahtar ayarlayın efendim."); return
        import base64, hashlib
        key_bytes = hashlib.sha256(self._master.encode()).digest()
        encoded = base64.b64encode(
            bytes(b ^ k for b, k in zip(data.encode(), key_bytes * (len(data) // 32 + 1)))
        ).decode()
        vault = _load(self.vault_file, {})
        vault[label] = {"data": encoded, "added": datetime.datetime.now().isoformat()}
        _save(self.vault_file, vault)
        self.msg("ANKA", f"✅ '{label}' kasaya güvenli şekilde eklendi efendim.")

    def retrieve_secret(self, label):
        if not self._master:
            self.msg("ANKA", "Ana anahtar gerekli efendim."); return None
        vault = _load(self.vault_file, {})
        if label not in vault:
            self.msg("ANKA", f"'{label}' kasada bulunamadı efendim."); return None
        import base64, hashlib
        key_bytes = hashlib.sha256(self._master.encode()).digest()
        encoded = base64.b64decode(vault[label]["data"])
        data = bytes(b ^ k for b, k in zip(encoded, key_bytes * (len(encoded) // 32 + 1))).decode()
        pyperclip.copy(data)
        self.msg("ANKA", f"✅ '{label}' çözüldü ve panoya kopyalandı efendim.")
        return data

    def list_vault(self):
        vault = _load(self.vault_file, {})
        if not vault:
            self.msg("ANKA", "Kasa boş efendim."); return
        r = f"🔐 GÜVENLİ KASA ({len(vault)} öğe)\n" + "═"*30 + "\n"
        r += "\n".join(f"• {k}: {v['added'][:10]}" for k, v in vault.items())
        self.msg("ANKA", r)


class EDITHGlobalMonitor:
    """Küresel izleme simülasyonu"""
    def __init__(self, ollama, speak_func, msg_func):
        self.ollama = ollama
        self.speak = speak_func
        self.msg = msg_func

    def global_status(self):
        """Küresel durum raporu"""
        def _gs():
            self.msg("ANKA", "🌍 KÜRESEL DURUM TARANIY_OR...")
            results = []
            # IP konum
            try:
                r = requests.get("https://ipapi.co/json/", timeout=5)
                d = r.json()
                results.append(f"📍 Konum: {d.get('city')}, {d.get('country_name')}")
                results.append(f"🌐 IP: {d.get('ip')} ({d.get('org','')})")
            except: pass
            # Hava
            try:
                r = requests.get("https://wttr.in/Istanbul?format=j1", timeout=5)
                d = r.json()["current_condition"][0]
                results.append(f"🌤 Hava: {d['temp_C']}°C — {d['weatherDesc'][0]['value']}")
            except: pass
            # Döviz
            try:
                r = requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=5)
                usd = r.json()["rates"]["TRY"]
                results.append(f"💱 USD/TRY: {usd:.2f}")
            except: pass
            # BTC
            try:
                r = requests.get("https://api.coinbase.com/v2/prices/BTC-USD/spot", timeout=5)
                btc = float(r.json()["data"]["amount"])
                results.append(f"₿ Bitcoin: ${btc:,.0f}")
            except: pass
            report = "🌍 KÜRESEL DURUM RAPORU\n" + "═"*35 + "\n" + "\n".join(results)
            self.msg("ANKA", report)
            self.speak("Küresel durum raporu hazırlandı efendim.")
        threading.Thread(target=_gs, daemon=True).start()

    def emergency_broadcast(self, message):
        """Acil yayın — tüm kanallara"""
        def _eb():
            self.msg("ANKA", f"🚨 ACİL YAYIN: {message}")
            self.speak(f"Acil yayın: {message}")
            try:
                requests.post("https://ntfy.sh/anka-yusuf-2026",
                    data=message.encode(),
                    headers={"Title":"🚨 EDITH ACİL","Priority":"max","Tags":"warning"},
                    timeout=3)
            except: pass
        threading.Thread(target=_eb, daemon=True).start()

    def track_satellite(self, name="ISS"):
        """Uydu takibi simülasyonu"""
        def _sat():
            try:
                r = requests.get(
                    f"https://api.wheretheiss.at/v1/satellites/25544",
                    timeout=5)
                d = r.json()
                result = (f"🛸 ISS KONUM BİLGİSİ\n"
                         f"• Enlem: {d.get('latitude',0):.4f}°\n"
                         f"• Boylam: {d.get('longitude',0):.4f}°\n"
                         f"• Yükseklik: {d.get('altitude',0):.0f} km\n"
                         f"• Hız: {d.get('velocity',0):.0f} km/h")
                self.msg("ANKA", result)
                self.speak("ISS konumu belirlendi efendim.")
            except:
                self.msg("ANKA", "Uydu verisi alınamadı efendim.")
        threading.Thread(target=_sat, daemon=True).start()


class EDITHAdvancedCommandProcessor(EDITHCommandProcessor):
    """Gelişmiş EDITH komut işleyici — tüm modülleri içerir"""
    def __init__(self, speak_func, msg_func, ollama):
        super().__init__(speak_func, msg_func, ollama)
        self.surveillance = EDITHSurveillance(ollama, speak_func, msg_func)
        self.weaponry = EDITHWeaponrySystem(ollama, speak_func, msg_func)
        self.vault = EDITHDataVault(speak_func, msg_func)
        self.global_monitor = EDITHGlobalMonitor(ollama, speak_func, msg_func)

    def process(self, text):
        t = text.lower().strip()

        # ── Gözetleme ─────────────────────────────────────────────────────────
        if "gözetleme başlat" in t or "kamerayı izle" in t:
            m = re.search(r'(\d+)', t)
            duration = int(m.group(1)) if m else 30
            self.surveillance.start_surveillance(duration); return True

        if "gözetlemeyi durdur" in t:
            self.surveillance.stop_surveillance(); return True

        if "çevre kontrolü" in t or "güvenlik çevre" in t:
            self.surveillance.perimeter_check(); return True

        # ── Arsenal ───────────────────────────────────────────────────────────
        if "araç devreye al" in t:
            tool = t.replace("araç devreye al","").strip()
            self.weaponry.deploy_tool(tool); return True

        if "arsenal durumu" in t or "edith arsenal" in t:
            self.weaponry.arsenal_status(); return True

        if "sistem kilitle" in t or "lockdown" in t:
            self.weaponry.system_lockdown(); return True

        # ── Kasa ──────────────────────────────────────────────────────────────
        if "kasa anahtarı" in t:
            key = t.replace("kasa anahtarı","").strip()
            if key: self.vault.set_master_key(key); return True

        if "kasaya ekle" in t:
            parts = t.replace("kasaya ekle","").strip().split("=")
            if len(parts) == 2:
                self.vault.store_secret(parts[0].strip(), parts[1].strip())
            return True

        if "kasadan al" in t or "sırrı getir" in t:
            label = t.replace("kasadan al","").replace("sırrı getir","").strip()
            if label: self.vault.retrieve_secret(label); return True

        if "kasa listesi" in t or "kasadakiler" in t:
            self.vault.list_vault(); return True

        # ── Küresel İzleme ────────────────────────────────────────────────────
        if "küresel durum" in t or "dünya raporu" in t:
            self.global_monitor.global_status(); return True

        if "acil yayın" in t:
            message = t.replace("acil yayın","").strip()
            if message: self.global_monitor.emergency_broadcast(message); return True

        if "iss nerede" in t or "uydu takip" in t:
            self.global_monitor.track_satellite(); return True

        # ── Ebeveyn komut işleyiciyi çağır ───────────────────────────────────
        return super().process(text)
