# ── ANKA GESTURE v3 — Ultra Gelişmiş Hareket Kontrolü ────────────────────────
# Göz kırpma, el hareketi, baş hareketi, yüz ifadesi, mesafe kontrolü
# Tamamen arka planda — ekranda hiçbir şey görünmez
import json, os, time, threading, datetime, math, re
import cv2, numpy as np
from anka_config import BASE_DIR

GESTURE_FILE  = os.path.join(BASE_DIR, "anka_gestures.json")
GESTURE_LOG   = os.path.join(BASE_DIR, "anka_gesture_log.json")

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

# ── Varsayılan komut haritası ─────────────────────────────────────────────────
DEFAULT_COMMANDS = {
    # Göz kırpma
    "single_blink":    "onay",
    "double_blink":    "iptal",
    "triple_blink":    "yardım",
    "long_blink":      "ses komutunu aktif et",
    "left_wink":       "önceki sekme",
    "right_wink":      "sonraki sekme",
    # Yüz ifadesi
    "smile":           "şans kurabiyesi",
    "eyebrow_raise":   "ne yapabilirsin",
    "mouth_open":      "ses komutunu aktif et",
    "surprised":       "sistem durumu",
    # El hareketleri
    "fist":            "dur",
    "open_palm":       "hava nasıl",
    "thumbs_up":       "harika",
    "thumbs_down":     "iptal",
    "pointing":        "ses komutunu aktif et",
    "peace_sign":      "ekran görüntüsü al",
    "rock_sign":       "müzik çal",
    "call_sign":       "whatsapp aç",
    "three_fingers":   "sistem durumu",
    "four_fingers":    "günlük rapor üret",
    "ok_sign":         "onay",
    "pinch":           "ses seviyesini artır",
    "pinch_open":      "ses seviyesini azalt",
    "spider_man":      "derin araştır",
    "gun_sign":        "fiyat alarmları",
    "crossed_fingers": "şanslı sayı",
    "love_sign":       "motivasyon ver",
    "middle_three":    "hava nasıl",
    # İki el
    "both_open":       "tüm pencereleri küçült",
    "both_fist":       "ekranı kilitle",
    "both_point":      "yeni sekme",
    "hands_apart":     "ses seviyesini artır",
    "hands_together":  "ses seviyesini azalt",
    # Kaydırma
    "swipe_left":      "önceki sekme",
    "swipe_right":     "sonraki sekme",
    "swipe_up":        "sayfayı aşağı kaydır",
    "swipe_down":      "sayfayı yukarı kaydır",
    # Baş hareketi
    "head_nod":        "onay",
    "head_shake":      "iptal",
    "head_tilt_left":  "önceki sekme",
    "head_tilt_right": "sonraki sekme",
    "head_up":         "sayfayı yukarı kaydır",
    "head_down":       "sayfayı aşağı kaydır",
    # Mesafe
    "come_closer":     "ses seviyesini artır",
    "go_farther":      "ses seviyesini azalt",
}


# ═══════════════════════════════════════════════════════════════════════════════
# ── TEMEL KAMERA YÖNETİCİSİ — Tek kamera, çok algılayıcı
# ═══════════════════════════════════════════════════════════════════════════════
class CameraManager:
    """
    Tek bir kamera açar, tüm algılayıcılar bu kamerayı paylaşır.
    RAM ve CPU tasarrufu sağlar.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._init()
        return cls._instance

    def _init(self):
        self.cap = None
        self.frame = None
        self.running = False
        self.subscribers = []
        self._thread = None

    def subscribe(self, callback):
        """Kare gelince çağrılacak fonksiyon ekle"""
        if callback not in self.subscribers:
            self.subscribers.append(callback)
        if not self.running:
            self._start()

    def unsubscribe(self, callback):
        if callback in self.subscribers:
            self.subscribers.remove(callback)
        if not self.subscribers:
            self._stop()

    def _start(self):
        self.running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def _loop(self):
        try:
            self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH,  320)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
            self.cap.set(cv2.CAP_PROP_FPS, 15)
            if not self.cap.isOpened():
                print("[ANKA Gesture] Kamera açılamadı.")
                self.running = False
                return
            while self.running:
                ret, frame = self.cap.read()
                if not ret: break
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                for cb in list(self.subscribers):
                    try: cb(rgb, frame.shape[1], frame.shape[0])
                    except: pass
                time.sleep(0.066)
        except Exception as e:
            print(f"[ANKA Gesture] Kamera hatası: {e}")
        finally:
            if self.cap: self.cap.release()

    def _stop(self):
        self.running = False


# ═══════════════════════════════════════════════════════════════════════════════
# ── KOMUT ÇALIŞTIRICISI — Cooldown ve log yönetimi
# ═══════════════════════════════════════════════════════════════════════════════
class GestureExecutor:
    def __init__(self, send_func, msg_func):
        self.send = send_func
        self.msg  = msg_func
        self.last_exec  = {}
        self.cooldowns  = {
            "single_blink": 1.2, "double_blink": 1.5, "triple_blink": 2.0,
            "long_blink": 2.0, "left_wink": 1.5, "right_wink": 1.5,
            "smile": 4.0, "eyebrow_raise": 4.0, "mouth_open": 3.0,
            "head_nod": 2.0, "head_shake": 2.0,
            "swipe_left": 1.0, "swipe_right": 1.0,
            "swipe_up": 1.0, "swipe_down": 1.0,
            "come_closer": 3.0, "go_farther": 3.0,
        }
        self.default_cooldown = 2.0
        self.log = _load(GESTURE_LOG, {"executions": [], "stats": {}})
        self.commands = _load(GESTURE_FILE, {}).get("commands", DEFAULT_COMMANDS)

    def execute(self, gesture):
        """Hareketi cooldown kontrolüyle çalıştır"""
        now = time.time()
        cooldown = self.cooldowns.get(gesture, self.default_cooldown)
        if now - self.last_exec.get(gesture, 0) < cooldown:
            return False
        self.last_exec[gesture] = now
        cmd = self.commands.get(gesture)
        if not cmd: return False

        # Emoji ve etiket
        EMOJI = {
            "single_blink":"👁️","double_blink":"👁️👁️","triple_blink":"✨",
            "long_blink":"⏳","left_wink":"😉L","right_wink":"😉R",
            "smile":"😊","eyebrow_raise":"🤨","mouth_open":"😮","surprised":"😲",
            "fist":"✊","open_palm":"🖐️","thumbs_up":"👍","thumbs_down":"👎",
            "pointing":"☝️","peace_sign":"✌️","rock_sign":"🤘","call_sign":"🤙",
            "three_fingers":"3️⃣","four_fingers":"4️⃣","ok_sign":"👌",
            "pinch":"🤌","pinch_open":"🤌↑","spider_man":"🕷️","gun_sign":"🔫",
            "crossed_fingers":"🤞","love_sign":"🤟","middle_three":"🖖",
            "both_open":"🙌","both_fist":"✊✊","both_point":"☝️☝️",
            "hands_apart":"↔️","hands_together":"🤲",
            "swipe_left":"👈","swipe_right":"👉","swipe_up":"👆","swipe_down":"👇",
            "head_nod":"🙂↕","head_shake":"🙅","head_tilt_left":"↙","head_tilt_right":"↘",
            "head_up":"⬆️","head_down":"⬇️",
            "come_closer":"🔊","go_farther":"🔉",
        }
        emoji = EMOJI.get(gesture, "🖐️")
        self.msg("ANKA", f"{emoji} → '{cmd}'")
        self.send(cmd)

        # Log
        self.log["stats"][gesture] = self.log["stats"].get(gesture, 0) + 1
        self.log["executions"].append({
            "gesture": gesture, "command": cmd,
            "time": datetime.datetime.now().isoformat()
        })
        if len(self.log["executions"]) > 200:
            self.log["executions"] = self.log["executions"][-200:]
        _save(GESTURE_LOG, self.log)
        return True

    def get_stats(self):
        stats = self.log["stats"]
        if not stats: return "Henüz gesture kullanımı yok efendim."
        sorted_s = sorted(stats.items(), key=lambda x: -x[1])
        r = "📊 Gesture İstatistikleri:\n"
        r += "\n".join(f"• {g}: {c} kez" for g,c in sorted_s[:8])
        return r

    def reload_commands(self):
        self.commands = _load(GESTURE_FILE, {}).get("commands", DEFAULT_COMMANDS)


# ═══════════════════════════════════════════════════════════════════════════════
# ── GÖZ & YÜZ ALGILAYICISI
# ═══════════════════════════════════════════════════════════════════════════════
class FaceDetector:
    LEFT_EYE  = [362,385,387,263,373,380]
    RIGHT_EYE = [33, 160,158,133,153,144]

    def __init__(self, executor):
        self.executor = executor
        self.running  = False
        self.face_mesh = None
        # Göz durumu
        self.eye_closed_start  = 0
        self.blink_count       = 0
        self.last_blink        = 0
        self.blink_reset       = 1.5
        self.ear_threshold     = 0.22
        self.long_blink_time   = 0.8
        self.left_closed_start  = 0
        self.right_closed_start = 0
        # Yüz ifadesi
        self._smile_sent   = 0
        self._brow_sent    = 0
        self._mouth_sent   = 0
        self._surprise_sent= 0
        # Mesafe (yüz büyüklüğüne göre)
        self.prev_face_size = None
        self._dist_sent    = 0

    def _ear(self, pts, lms, w, h):
        p = [(int(lms[i].x*w), int(lms[i].y*h)) for i in pts]
        d1 = math.dist(p[1],p[5]); d2 = math.dist(p[2],p[4])
        d3 = math.dist(p[0],p[3])
        return (d1+d2)/(2*d3) if d3>0 else 0

    def _face_size(self, lms, w, h):
        """Yüzün ekrandaki büyüklüğü — mesafe tahmini"""
        x_coords = [lms[i].x * w for i in [234,454,10,152]]
        y_coords = [lms[i].y * h for i in [234,454,10,152]]
        return (max(x_coords)-min(x_coords)) * (max(y_coords)-min(y_coords))

    def process(self, rgb, w, h):
        if not self.face_mesh: return
        res = self.face_mesh.process(rgb)
        if not res.multi_face_landmarks: return
        lms = res.multi_face_landmarks[0].landmark
        now = time.time()

        # ── EAR ───────────────────────────────────────────────────────────────
        le  = self._ear(self.LEFT_EYE,  lms, w, h)
        re_ = self._ear(self.RIGHT_EYE, lms, w, h)
        avg_ear = (le + re_) / 2

        # Wink tespiti
        if le < self.ear_threshold and re_ >= self.ear_threshold:
            if self.left_closed_start == 0: self.left_closed_start = now
        elif self.left_closed_start > 0:
            if now - self.left_closed_start < 0.4:
                self.executor.execute("left_wink")
            self.left_closed_start = 0

        if re_ < self.ear_threshold and le >= self.ear_threshold:
            if self.right_closed_start == 0: self.right_closed_start = now
        elif self.right_closed_start > 0:
            if now - self.right_closed_start < 0.4:
                self.executor.execute("right_wink")
            self.right_closed_start = 0

        # Her iki göz kırpma
        if avg_ear < self.ear_threshold:
            if self.eye_closed_start == 0: self.eye_closed_start = now
        else:
            if self.eye_closed_start > 0:
                dur = now - self.eye_closed_start
                self.eye_closed_start = 0
                if dur >= self.long_blink_time:
                    self.executor.execute("long_blink")
                    self.blink_count = 0
                else:
                    if now - self.last_blink > self.blink_reset:
                        self.blink_count = 0
                    self.blink_count += 1
                    self.last_blink = now

        if self.blink_count > 0 and now - self.last_blink > self.blink_reset:
            blink_map = {1:"single_blink",2:"double_blink",3:"triple_blink"}
            self.executor.execute(blink_map.get(min(self.blink_count,3),"triple_blink"))
            self.blink_count = 0

        # ── Yüz İfadesi ───────────────────────────────────────────────────────
        try:
            # Gülümseme
            mouth_left  = (int(lms[61].x*w), int(lms[61].y*h))
            mouth_right = (int(lms[291].x*w),int(lms[291].y*h))
            mouth_top   = (int(lms[13].x*w), int(lms[13].y*h))
            mouth_bot   = (int(lms[14].x*w), int(lms[14].y*h))
            mouth_w = math.dist(mouth_left, mouth_right)
            mouth_h = math.dist(mouth_top, mouth_bot)
            mar = mouth_h / mouth_w if mouth_w > 0 else 0

            if mar < 0.12 and now - self._smile_sent > 4:
                self._smile_sent = now
                self.executor.execute("smile")
            elif mar > 0.45 and now - self._mouth_sent > 3:
                self._mouth_sent = now
                self.executor.execute("mouth_open")
            elif mar > 0.65 and now - self._surprise_sent > 3:
                self._surprise_sent = now
                self.executor.execute("surprised")

            # Kaş kaldırma
            lb = int(lms[223].y * h)
            le_y = int(lms[159].y * h)
            rb = int(lms[443].y * h)
            re_y = int(lms[386].y * h)
            brow_dist = ((le_y - lb) + (re_y - rb)) / 2
            if brow_dist > 44 and now - self._brow_sent > 4:
                self._brow_sent = now
                self.executor.execute("eyebrow_raise")

            # Mesafe tahmini
            face_size = self._face_size(lms, w, h)
            if self.prev_face_size is not None and now - self._dist_sent > 3:
                change = face_size - self.prev_face_size
                if change > 2000:
                    self._dist_sent = now
                    self.executor.execute("come_closer")
                elif change < -2000:
                    self._dist_sent = now
                    self.executor.execute("go_farther")
            self.prev_face_size = face_size * 0.8 + (self.prev_face_size or face_size) * 0.2
        except: pass

    def start(self):
        try:
            import mediapipe as mp
            self.face_mesh = mp.solutions.face_mesh.FaceMesh(
                max_num_faces=1, refine_landmarks=True,
                min_detection_confidence=0.7, min_tracking_confidence=0.7)
            self.running = True
            CameraManager().subscribe(self.process)
        except ImportError:
            pass

    def stop(self):
        self.running = False
        CameraManager().unsubscribe(self.process)
        if self.face_mesh:
            self.face_mesh.close()
            self.face_mesh = None


# ═══════════════════════════════════════════════════════════════════════════════
# ── EL ALGILAYICISI
# ═══════════════════════════════════════════════════════════════════════════════
class HandDetector:
    def __init__(self, executor):
        self.executor = executor
        self.hands_model = None
        self.running = False
        self.prev_x = None
        self.prev_y = None
        self.swipe_threshold = 0.15
        # İki el mesafe takibi
        self.prev_hand_dist = None
        self._dist_sent = 0

    def _fingers(self, lms):
        tips = [4,8,12,16,20]
        f = [1 if lms[tips[0]].x < lms[tips[0]-1].x else 0]
        for tip in tips[1:]:
            f.append(1 if lms[tip].y < lms[tip-2].y else 0)
        return f

    def _dist(self, lms, a, b):
        dx = lms[a].x - lms[b].x
        dy = lms[a].y - lms[b].y
        return math.sqrt(dx*dx + dy*dy)

    def _identify(self, fingers, lms):
        count = sum(fingers)
        if count == 0: return "fist"
        if count == 5: return "open_palm"
        if fingers == [1,0,0,0,0]:
            return "thumbs_up" if lms[4].y < lms[3].y else "thumbs_down"
        if fingers == [0,1,0,0,0]: return "pointing"
        if fingers == [0,1,1,0,0]: return "peace_sign"
        if fingers == [0,1,0,0,1]: return "rock_sign"
        if fingers == [1,0,0,0,1]: return "call_sign"
        if fingers == [1,1,0,0,1]: return "spider_man"
        if fingers == [1,1,0,0,0]: return "gun_sign"
        if fingers == [1,0,0,0,0] and count == 1:
            if lms[4].y > lms[3].y: return "thumbs_down"
        if count == 3 and fingers[1] and fingers[2] and fingers[3]:
            return "three_fingers"
        if count == 3 and fingers[2] and fingers[3] and fingers[4]:
            return "middle_three"
        if count == 4 and not fingers[0]: return "four_fingers"
        if fingers == [1,0,0,0,1] and self._dist(lms,4,20) < 0.12:
            return "love_sign"
        # OK işareti
        if self._dist(lms,4,8) < 0.05 and fingers[2] and fingers[3] and fingers[4]:
            return "ok_sign"
        # Pinch
        if self._dist(lms,4,8) < 0.04 and count <= 2:
            return "pinch"
        if self._dist(lms,4,8) < 0.08 and count == 5:
            return "pinch_open"
        # Çapraz parmak
        if fingers == [0,1,1,0,0] and lms[8].x > lms[12].x:
            return "crossed_fingers"
        return f"unknown_{count}"

    def _detect_swipe(self, lms):
        cx, cy = lms[0].x, lms[0].y
        if self.prev_x is None:
            self.prev_x, self.prev_y = cx, cy
            return None
        dx = cx - self.prev_x
        dy = cy - self.prev_y
        self.prev_x, self.prev_y = cx, cy
        if abs(dx) > self.swipe_threshold and abs(dx) > abs(dy)*1.5:
            return "swipe_left" if dx < 0 else "swipe_right"
        if abs(dy) > self.swipe_threshold and abs(dy) > abs(dx)*1.5:
            return "swipe_up" if dy < 0 else "swipe_down"
        return None

    def process(self, rgb, w, h):
        if not self.hands_model: return
        res = self.hands_model.process(rgb)
        now = time.time()

        if res.multi_hand_landmarks:
            if len(res.multi_hand_landmarks) == 2:
                l1 = res.multi_hand_landmarks[0].landmark
                l2 = res.multi_hand_landmarks[1].landmark
                f1 = self._fingers(l1); f2 = self._fingers(l2)
                s1 = sum(f1); s2 = sum(f2)
                # İki el tespitleri
                if s1==5 and s2==5:
                    # El mesafesi
                    dist = abs(l1[0].x - l2[0].x)
                    if self.prev_hand_dist is not None and now - self._dist_sent > 2:
                        if dist - self.prev_hand_dist > 0.15:
                            self._dist_sent = now
                            self.executor.execute("hands_apart")
                        elif self.prev_hand_dist - dist > 0.15:
                            self._dist_sent = now
                            self.executor.execute("hands_together")
                    self.prev_hand_dist = dist
                    self.executor.execute("both_open")
                elif s1==0 and s2==0:
                    self.executor.execute("both_fist")
                elif f1==[0,1,0,0,0] and f2==[0,1,0,0,0]:
                    self.executor.execute("both_point")
            else:
                lms = res.multi_hand_landmarks[0].landmark
                fingers = self._fingers(lms)
                gesture = self._identify(fingers, lms)
                if not gesture.startswith("unknown"):
                    self.executor.execute(gesture)
                swipe = self._detect_swipe(lms)
                if swipe:
                    self.executor.execute(swipe)
        else:
            self.prev_x = None
            self.prev_y = None
            self.prev_hand_dist = None

    def start(self):
        try:
            import mediapipe as mp
            self.hands_model = mp.solutions.hands.Hands(
                max_num_hands=2,
                min_detection_confidence=0.8,
                min_tracking_confidence=0.7)
            self.running = True
            CameraManager().subscribe(self.process)
        except ImportError:
            pass

    def stop(self):
        self.running = False
        CameraManager().unsubscribe(self.process)
        if self.hands_model:
            self.hands_model.close()
            self.hands_model = None


# ═══════════════════════════════════════════════════════════════════════════════
# ── BAŞ HAREKET ALGILAYICISI
# ═══════════════════════════════════════════════════════════════════════════════
class HeadDetector:
    def __init__(self, executor):
        self.executor = executor
        self.face_mesh = None
        self.running = False
        self.positions = []
        self.last_exec = {}

    def _nose(self, lms):
        return (lms[1].x, lms[1].y)

    def _detect(self, positions):
        if len(positions) < 8: return None
        xs = [p[0] for p in positions]
        ys = [p[1] for p in positions]
        x_range = max(xs) - min(xs)
        y_range = max(ys) - min(ys)
        avg_x = sum(xs)/len(xs)
        avg_y = sum(ys)/len(ys)
        # Dikey hareket — baş sallama
        if y_range > 0.04 and y_range > x_range * 2:
            return "head_nod"
        # Yatay hareket — baş salma
        if x_range > 0.06 and x_range > y_range * 2:
            return "head_shake"
        # Pozisyon — eğme
        if avg_x < 0.40: return "head_tilt_left"
        if avg_x > 0.60: return "head_tilt_right"
        if avg_y < 0.35: return "head_up"
        if avg_y > 0.65: return "head_down"
        return None

    def process(self, rgb, w, h):
        if not self.face_mesh: return
        res = self.face_mesh.process(rgb)
        if not res.multi_face_landmarks: return
        lms = res.multi_face_landmarks[0].landmark
        pos = self._nose(lms)
        self.positions.append(pos)
        if len(self.positions) > 15:
            self.positions = self.positions[-15:]
        gesture = self._detect(self.positions)
        if gesture:
            now = time.time()
            if now - self.last_exec.get(gesture, 0) > 2.0:
                self.last_exec[gesture] = now
                self.executor.execute(gesture)

    def start(self):
        try:
            import mediapipe as mp
            self.face_mesh = mp.solutions.face_mesh.FaceMesh(
                max_num_faces=1, refine_landmarks=True,
                min_detection_confidence=0.7, min_tracking_confidence=0.7)
            self.running = True
            CameraManager().subscribe(self.process)
        except ImportError:
            pass

    def stop(self):
        self.running = False
        CameraManager().unsubscribe(self.process)
        if self.face_mesh:
            self.face_mesh.close()
            self.face_mesh = None


# ═══════════════════════════════════════════════════════════════════════════════
# ── GESTURE AYAR YÖNETİCİSİ
# ═══════════════════════════════════════════════════════════════════════════════
class GestureSettings:
    def __init__(self, executor):
        self.executor = executor
        self.data = _load(GESTURE_FILE, {"commands": DEFAULT_COMMANDS, "enabled": True})

    def set_command(self, gesture, command):
        self.data["commands"][gesture] = command
        _save(GESTURE_FILE, self.data)
        self.executor.reload_commands()
        return f"✅ '{gesture}' → '{command}' efendim."

    def reset_defaults(self):
        self.data["commands"] = DEFAULT_COMMANDS.copy()
        _save(GESTURE_FILE, self.data)
        self.executor.reload_commands()
        return "✅ Varsayılan komutlar yüklendi efendim."

    def show_all(self):
        cmds = self.data["commands"]
        categories = {
            "👁️ Göz Kırpma": ["single_blink","double_blink","triple_blink","long_blink","left_wink","right_wink"],
            "😊 Yüz İfadesi": ["smile","eyebrow_raise","mouth_open","surprised"],
            "🖐️ El Hareketi": ["fist","open_palm","thumbs_up","thumbs_down","pointing","peace_sign",
                              "rock_sign","call_sign","three_fingers","four_fingers","ok_sign",
                              "pinch","pinch_open","spider_man","gun_sign","crossed_fingers",
                              "love_sign","middle_three"],
            "🤲 İki El": ["both_open","both_fist","both_point","hands_apart","hands_together"],
            "👈 Kaydırma": ["swipe_left","swipe_right","swipe_up","swipe_down"],
            "🙂 Baş": ["head_nod","head_shake","head_tilt_left","head_tilt_right","head_up","head_down"],
            "📏 Mesafe": ["come_closer","go_farther"],
        }
        r = "🎮 TÜM GESTURE KOMUTLARI\n" + "═"*40 + "\n"
        for cat, gestures in categories.items():
            active = [(g, cmds[g]) for g in gestures if g in cmds]
            if active:
                r += f"\n{cat}:\n"
                r += "\n".join(f"  • {g}: '{c}'" for g,c in active)
                r += "\n"
        return r


# ═══════════════════════════════════════════════════════════════════════════════
# ── ANA KOMUT İŞLEYİCİSİ
# ═══════════════════════════════════════════════════════════════════════════════
class GestureCommandProcessor:
    def __init__(self, speak_func, msg_func, send_func, ollama=None):
        self.speak    = speak_func
        self.msg      = msg_func
        self.send     = send_func
        self.executor = GestureExecutor(send_func, msg_func)
        self.face     = FaceDetector(self.executor)
        self.hand     = HandDetector(self.executor)
        self.head     = HeadDetector(self.executor)
        self.settings = GestureSettings(self.executor)
        self._all_active = False

    def start_all(self, silent=False):
        """Tümünü arka planda sessizce başlat"""
        self.face.start()
        time.sleep(0.2)
        self.hand.start()
        time.sleep(0.2)
        self.head.start()
        self._all_active = True
        if not silent:
            self.msg("ANKA",
                "🎮 GESTURE KONTROLÜ AKTİF (Arka Plan)\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "👁️  Göz: Kırpma, Wink, Gülümseme, Kaş\n"
                "🖐️  El: 20+ hareket + İki el + Kaydırma\n"
                "🙂  Baş: Sallama, Salma, Eğme\n"
                "📏  Yüz: Mesafe kontrolü\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "📷 Kamera ekranda görünmüyor!\n"
                "'gesture komutları' ile tam listeyi gör.")
            self.speak("Gesture kontrolü aktif efendim.")

    def stop_all(self):
        self.face.stop()
        self.hand.stop()
        self.head.stop()
        self._all_active = False
        self.msg("ANKA","⏹️ Tüm gesture kontrolleri durduruldu efendim.")

    def process(self, text):
        t = text.lower().strip()

        # ── Başlatma ──────────────────────────────────────────────────────────
        if any(x in t for x in ["jest kontrolü başlat","tam kontrol başlat",
                                  "gesture başlat","hareket kontrolü başlat"]):
            self.start_all(); return True

        if "göz kontrolü başlat" in t:
            self.face.start()
            self.msg("ANKA","👁️ Göz & Yüz kontrolü başladı efendim."); return True

        if "el kontrolü başlat" in t:
            self.hand.start()
            self.msg("ANKA","🖐️ El hareketi kontrolü başladı efendim."); return True

        if "baş kontrolü başlat" in t:
            self.head.start()
            self.msg("ANKA","🙂 Baş hareketi kontrolü başladı efendim."); return True

        # ── Durdurma ──────────────────────────────────────────────────────────
        if any(x in t for x in ["jest kontrolünü durdur","tam kontrolü durdur",
                                  "gesture durdur","hareketi durdur"]):
            self.stop_all(); return True

        if "göz kontrolünü durdur" in t:
            self.face.stop()
            self.msg("ANKA","👁️ Göz kontrolü durduruldu efendim."); return True

        if "el kontrolünü durdur" in t:
            self.hand.stop()
            self.msg("ANKA","🖐️ El kontrolü durduruldu efendim."); return True

        if "baş kontrolünü durdur" in t:
            self.head.stop()
            self.msg("ANKA","🙂 Baş kontrolü durduruldu efendim."); return True

        # ── Ayarlar ───────────────────────────────────────────────────────────
        if "jest ayarla" in t:
            m = re.search(r'jest ayarla\s+(\S+)\s*=\s*(.+)', t)
            if m:
                r = self.settings.set_command(m.group(1), m.group(2).strip())
                self.msg("ANKA", r); self.speak(r)
            return True

        if "gesture varsayılan" in t or "jest sıfırla" in t:
            r = self.settings.reset_defaults()
            self.msg("ANKA", r); self.speak(r); return True

        if "gesture komutları" in t or "jest listesi" in t:
            r = self.settings.show_all()
            self.msg("ANKA", r); return True

        if "gesture istatistik" in t or "jest istatistik" in t:
            r = self.executor.get_stats()
            self.msg("ANKA", r); return True

        # ── Yardım ────────────────────────────────────────────────────────────
        if "gesture yardım" in t or "jest yardım" in t:
            r = (
                "🎮 GESTURE KONTROL REHBERİ v3\n"
                "═══════════════════════════════\n\n"
                "🚀 BAŞLATMA:\n"
                "• 'jest kontrolü başlat' → Hepsi\n"
                "• 'göz kontrolü başlat'\n"
                "• 'el kontrolü başlat'\n"
                "• 'baş kontrolü başlat'\n\n"
                "👁️ GÖZ (6):\n"
                "1,2,3 kırpma | Uzun | Sol wink | Sağ wink\n\n"
                "😊 YÜZ (4):\n"
                "Gülümse | Kaş kaldır | Ağız aç | Şaşır\n\n"
                "🖐️ EL (20+):\n"
                "Yumruk,Açık,Beğeni,Barış,Rock,Ara,OK\n"
                "Pinch,Spider-Man,Silah,Çapraz,Aşk,3,4 parmak\n"
                "Kaydırma: Sol,Sağ,Yukarı,Aşağı\n\n"
                "🤲 İKİ EL (5):\n"
                "İki Açık | İki Yumruk | İki İşaret\n"
                "Ayır | Birleştir\n\n"
                "🙂 BAŞ (6):\n"
                "Salla,Sal,Sol,Sağ,Yukarı,Aşağı\n\n"
                "📏 MESAFE (2):\n"
                "Yaklaş | Uzaklaş\n\n"
                "⚙️ AYAR:\n"
                "• 'jest ayarla [hareket] = [komut]'\n"
                "• 'gesture komutları'\n"
                "• 'gesture istatistik'\n"
                "• 'jest sıfırla'\n\n"
                "⏹️ DURDUR:\n"
                "• 'jest kontrolünü durdur'"
            )
            self.msg("ANKA", r)
            self.speak("Gesture rehberi hazırlandı efendim.")
            return True

        return False


# ═══════════════════════════════════════════════════════════════════════════════
# ── GESTURE v3 EK — Gelişmiş Özellikler ──────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

# ── PARMAK SAYACI — Kaç parmak açık ─────────────────────────────────────────
class FingerCounter:
    """Parmak sayısına göre direkt komut"""
    def __init__(self, executor):
        self.executor = executor
        self.running  = False
        self.hands_model = None
        self.last_count  = -1
        self.last_time   = 0
        self.cooldown    = 2.5

        # Parmak sayısı → komut haritası
        self.count_commands = {
            0: "dur",
            1: "ses komutunu aktif et",
            2: "ekran görüntüsü al",
            3: "sistem durumu",
            4: "günlük rapor üret",
            5: "hava nasıl",
        }

    def process(self, rgb, w, h):
        if not self.hands_model: return
        res = self.hands_model.process(rgb)
        if not res.multi_hand_landmarks: return
        lms = res.multi_hand_landmarks[0].landmark
        # Parmak say
        tips  = [4,8,12,16,20]
        count = 0
        # Başparmak
        if lms[4].x < lms[3].x: count += 1
        # Diğerleri
        for tip in tips[1:]:
            if lms[tip].y < lms[tip-2].y: count += 1
        now = time.time()
        if count != self.last_count and now - self.last_time > self.cooldown:
            self.last_count = count
            self.last_time  = now
            cmd = self.count_commands.get(count)
            if cmd:
                self.executor.msg("ANKA", f"🖐️ {count} parmak → '{cmd}'")
                self.executor.send(cmd)

    def set_command(self, count, command):
        self.count_commands[count] = command
        self.executor.msg("ANKA", f"✅ {count} parmak → '{command}' efendim.")

    def start(self):
        try:
            import mediapipe as mp
            self.hands_model = mp.solutions.hands.Hands(
                max_num_hands=1,
                min_detection_confidence=0.85,
                min_tracking_confidence=0.8)
            self.running = True
            CameraManager().subscribe(self.process)
            self.executor.msg("ANKA",
                "🔢 PARMAK SAYACI AKTİF\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "0 parmak (yumruk) → Dur\n"
                "1 parmak → Ses komutu\n"
                "2 parmak → Ekran görüntüsü\n"
                "3 parmak → Sistem durumu\n"
                "4 parmak → Günlük rapor\n"
                "5 parmak (açık el) → Hava")
        except ImportError:
            self.executor.msg("ANKA","MediaPipe yok. pip install mediapipe")

    def stop(self):
        self.running = False
        CameraManager().unsubscribe(self.process)
        if self.hands_model:
            self.hands_model.close()
            self.hands_model = None


# ── YÜZÜN EKRANDAKI KONUMU — Ekran kaydırma ─────────────────────────────────
class FacePositionController:
    """
    Yüzün ekrandaki pozisyonuna göre kontrol.
    Sola bak → önceki sekme
    Sağa bak → sonraki sekme
    Yukarı bak → sayfayı yukarı kaydır
    Aşağı bak → sayfayı aşağı kaydır
    """
    def __init__(self, executor):
        self.executor   = executor
        self.running    = False
        self.face_mesh  = None
        self.last_exec  = {}
        self.cooldown   = 1.5
        self.zone_threshold = 0.15  # Merkez zonunun dışı

    def process(self, rgb, w, h):
        if not self.face_mesh: return
        res = self.face_mesh.process(rgb)
        if not res.multi_face_landmarks: return
        lms = res.multi_face_landmarks[0].landmark
        # Burun ucu koordinatları
        nose_x = lms[1].x  # 0=sol, 1=sağ
        nose_y = lms[1].y  # 0=üst, 1=alt
        now = time.time()

        # Yatay bakış
        if nose_x < 0.35:  # Sola bakıyor
            if now - self.last_exec.get("look_left",0) > self.cooldown:
                self.last_exec["look_left"] = now
                cmd = self.executor.commands.get("head_tilt_left","önceki sekme")
                self.executor.msg("ANKA", f"👈 Sola bakış → '{cmd}'")
                self.executor.send(cmd)
        elif nose_x > 0.65:  # Sağa bakıyor
            if now - self.last_exec.get("look_right",0) > self.cooldown:
                self.last_exec["look_right"] = now
                cmd = self.executor.commands.get("head_tilt_right","sonraki sekme")
                self.executor.msg("ANKA", f"👉 Sağa bakış → '{cmd}'")
                self.executor.send(cmd)

        # Dikey bakış
        if nose_y < 0.30:  # Yukarı bakıyor
            if now - self.last_exec.get("look_up",0) > self.cooldown:
                self.last_exec["look_up"] = now
                cmd = self.executor.commands.get("head_up","sayfayı yukarı kaydır")
                self.executor.msg("ANKA", f"⬆️ Yukarı bakış → '{cmd}'")
                self.executor.send(cmd)
        elif nose_y > 0.70:  # Aşağı bakıyor
            if now - self.last_exec.get("look_down",0) > self.cooldown:
                self.last_exec["look_down"] = now
                cmd = self.executor.commands.get("head_down","sayfayı aşağı kaydır")
                self.executor.msg("ANKA", f"⬇️ Aşağı bakış → '{cmd}'")
                self.executor.send(cmd)

    def start(self):
        try:
            import mediapipe as mp
            self.face_mesh = mp.solutions.face_mesh.FaceMesh(
                max_num_faces=1, refine_landmarks=True,
                min_detection_confidence=0.7, min_tracking_confidence=0.7)
            self.running = True
            CameraManager().subscribe(self.process)
            self.executor.msg("ANKA",
                "👀 YÜZ KONUM KONTROLÜ AKTİF\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "👈 Sola bak → Önceki sekme\n"
                "👉 Sağa bak → Sonraki sekme\n"
                "⬆️ Yukarı bak → Sayfayı yukarı\n"
                "⬇️ Aşağı bak → Sayfayı aşağı")
        except ImportError:
            self.executor.msg("ANKA","MediaPipe yok. pip install mediapipe")

    def stop(self):
        self.running = False
        CameraManager().unsubscribe(self.process)
        if self.face_mesh:
            self.face_mesh.close()
            self.face_mesh = None


# ── EL HIZ ALGILAYICISI — El sallama hızına göre komut ─────────────────────
class HandSpeedDetector:
    """
    El sallama hızını ölçer:
    - Yavaş sallama → normal komut
    - Hızlı sallama → acil/öncelikli komut
    - Çok hızlı sallama → iptal/durdur
    """
    def __init__(self, executor):
        self.executor = executor
        self.running  = False
        self.hands_model = None
        self.positions = []  # (x, y, time)
        self.last_speed_cmd = 0

    def _calc_speed(self):
        if len(self.positions) < 3: return 0
        total_dist = 0
        for i in range(1, len(self.positions)):
            dx = self.positions[i][0] - self.positions[i-1][0]
            dy = self.positions[i][1] - self.positions[i-1][1]
            total_dist += math.sqrt(dx*dx + dy*dy)
        time_span = self.positions[-1][2] - self.positions[0][2]
        return total_dist / max(time_span, 0.001)

    def process(self, rgb, w, h):
        if not self.hands_model: return
        res = self.hands_model.process(rgb)
        if not res.multi_hand_landmarks:
            self.positions = []
            return
        lms = res.multi_hand_landmarks[0].landmark
        now = time.time()
        self.positions.append((lms[0].x, lms[0].y, now))
        if len(self.positions) > 10:
            self.positions = self.positions[-10:]
        speed = self._calc_speed()
        if now - self.last_speed_cmd < 2.0: return
        if speed > 3.0:    # Çok hızlı
            self.last_speed_cmd = now
            self.executor.msg("ANKA","⚡⚡ Çok hızlı el → 'dur'")
            self.executor.send("dur")
        elif speed > 1.5:  # Hızlı
            self.last_speed_cmd = now
            self.executor.msg("ANKA","⚡ Hızlı el → 'ses komutunu aktif et'")
            self.executor.send("ses komutunu aktif et")

    def start(self):
        try:
            import mediapipe as mp
            self.hands_model = mp.solutions.hands.Hands(
                max_num_hands=1,
                min_detection_confidence=0.8,
                min_tracking_confidence=0.7)
            self.running = True
            CameraManager().subscribe(self.process)
            self.executor.msg("ANKA","⚡ El hız algılayıcı aktif efendim!")
        except ImportError:
            self.executor.msg("ANKA","MediaPipe yok.")

    def stop(self):
        self.running = False
        CameraManager().unsubscribe(self.process)
        if self.hands_model:
            self.hands_model.close()
            self.hands_model = None


# ── GESTURE MACROLARı — Zincirleme hareketler ───────────────────────────────
class GestureMacro:
    """
    Birden fazla hareketi arka arkaya yapınca makro çalıştır.
    Örn: thumbs_up → peace_sign → "müzik çal"
    """
    def __init__(self, executor):
        self.executor = executor
        self.macros   = {}
        self.sequence = []
        self.last_gesture_time = 0
        self.sequence_timeout  = 3.0  # 3 sn içinde yapılmalı
        self.macro_file = os.path.join(BASE_DIR, "anka_gesture_macros.json")
        self.macros = _load(self.macro_file, {
            "thumbs_up+peace_sign":   "müzik çal",
            "fist+open_palm":         "ekranı kilitle",
            "peace_sign+rock_sign":   "ses seviyesini artır",
            "pointing+ok_sign":       "onay",
            "thumbs_down+fist":       "iptal",
        })

    def add_gesture(self, gesture):
        """Yeni hareket ekle, makro kontrol et"""
        now = time.time()
        if now - self.last_gesture_time > self.sequence_timeout:
            self.sequence = []
        self.sequence.append(gesture)
        self.last_gesture_time = now
        # Makro var mı kontrol et
        if len(self.sequence) >= 2:
            key = "+".join(self.sequence[-2:])
            if key in self.macros:
                cmd = self.macros[key]
                self.executor.msg("ANKA",
                    f"🔗 Makro: {self.sequence[-2]} + {self.sequence[-1]} → '{cmd}'")
                self.executor.send(cmd)
                self.sequence = []

    def add_macro(self, gesture1, gesture2, command):
        key = f"{gesture1}+{gesture2}"
        self.macros[key] = command
        _save(self.macro_file, self.macros)
        r = f"✅ Makro eklendi: {gesture1} + {gesture2} → '{command}' efendim."
        self.executor.msg("ANKA", r)

    def list_macros(self):
        if not self.macros:
            self.executor.msg("ANKA","Makro yok efendim.")
            return
        r = "🔗 Gesture Makroları:\n"
        r += "\n".join(f"• {k}: '{v}'" for k,v in self.macros.items())
        self.executor.msg("ANKA", r)


# ── GESTURE İSTATİSTİK DASHBOARD ────────────────────────────────────────────
class GestureDashboard:
    """Gesture kullanım istatistikleri ve öneriler"""
    def __init__(self, executor, msg_func):
        self.executor = executor
        self.msg      = msg_func

    def show_dashboard(self):
        log = _load(GESTURE_LOG, {"executions": [], "stats": {}})
        stats = log.get("stats", {})
        execs = log.get("executions", [])

        if not stats:
            self.msg("ANKA","Henüz gesture kullanımı yok efendim.")
            return

        # En çok kullanılanlar
        sorted_stats = sorted(stats.items(), key=lambda x: -x[1])
        total = sum(stats.values())

        # Son 24 saat
        yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).isoformat()
        recent = [e for e in execs if e.get("time","") > yesterday]

        r = (f"📊 GESTURE DASHBOARD\n{'═'*35}\n"
             f"• Toplam Kullanım: {total}\n"
             f"• Son 24 Saat: {len(recent)}\n"
             f"• Benzersiz Hareket: {len(stats)}\n\n"
             f"🏆 En Çok Kullanılanlar:\n")
        for gesture, count in sorted_stats[:5]:
            pct = int(count/total*100)
            bar = "█" * (pct//10) + "░" * (10-pct//10)
            r += f"  {gesture[:20]:<20} {bar} {count}x\n"

        # Öneri
        if sorted_stats:
            top = sorted_stats[0][0]
            r += f"\n💡 '{top}' en çok kullanılan hareketiniz.\n"
            r += "Bunu daha önemli bir komuta atayabilirsiniz!"

        self.msg("ANKA", r)

    def suggest_optimizations(self):
        """Kullanım kalıplarına göre optimizasyon öner"""
        log = _load(GESTURE_LOG, {"executions": [], "stats": {}})
        stats = log.get("stats", {})
        if not stats:
            self.msg("ANKA","Yeterli veri yok efendim."); return

        top3 = sorted(stats.items(), key=lambda x: -x[1])[:3]
        easy = ["single_blink","thumbs_up","open_palm"]
        suggestions = []

        for i, (gesture, count) in enumerate(top3):
            if gesture not in easy and i < len(easy):
                suggestions.append(
                    f"• '{gesture}' → '{easy[i]}' olarak taşıyın (daha kolay)")

        if suggestions:
            r = "💡 Optimizasyon Önerileri:\n" + "\n".join(suggestions)
        else:
            r = "✅ Gesture ayarlarınız zaten optimal efendim!"
        self.msg("ANKA", r)


# ── GELİŞTİRİLMİŞ GESTURE COMMAND PROCESSOR ─────────────────────────────────
# Mevcut GestureCommandProcessor'a yeni özellikler ekle
_original_process = GestureCommandProcessor.process

def _new_process(self, text):
    t = text.lower().strip()

    # ── Parmak Sayacı ─────────────────────────────────────────────────────────
    if "parmak sayacı başlat" in t or "parmak kontrolü" in t:
        if not hasattr(self, 'finger_counter'):
            self.finger_counter = FingerCounter(self.executor)
        self.finger_counter.start(); return True
    if "parmak sayacı durdur" in t:
        if hasattr(self, 'finger_counter'):
            self.finger_counter.stop(); return True
    if "parmak komutu ayarla" in t:
        m = re.search(r'(\d)\s*=\s*(.+)', t.replace("parmak komutu ayarla",""))
        if m and hasattr(self, 'finger_counter'):
            self.finger_counter.set_command(int(m.group(1)), m.group(2).strip())
        return True

    # ── Yüz Konum Kontrolü ────────────────────────────────────────────────────
    if "yüz konum kontrolü" in t or "göz yönü kontrolü" in t:
        if not hasattr(self, 'face_pos'):
            self.face_pos = FacePositionController(self.executor)
        self.face_pos.start(); return True
    if "yüz konum durdur" in t:
        if hasattr(self, 'face_pos'):
            self.face_pos.stop(); return True

    # ── El Hız Algılayıcı ─────────────────────────────────────────────────────
    if "el hız algılayıcı" in t or "hız kontrolü başlat" in t:
        if not hasattr(self, 'hand_speed'):
            self.hand_speed = HandSpeedDetector(self.executor)
        self.hand_speed.start(); return True
    if "el hız durdur" in t:
        if hasattr(self, 'hand_speed'):
            self.hand_speed.stop(); return True

    # ── Gesture Makro ─────────────────────────────────────────────────────────
    if not hasattr(self, 'gesture_macro'):
        self.gesture_macro = GestureMacro(self.executor)

    if "gesture makro ekle" in t:
        parts = t.replace("gesture makro ekle","").strip().split("+")
        if len(parts) == 2:
            cmd_parts = parts[1].split("=")
            if len(cmd_parts) == 2:
                self.gesture_macro.add_macro(
                    parts[0].strip(), cmd_parts[0].strip(), cmd_parts[1].strip())
        return True
    if "gesture makrolar" in t:
        self.gesture_macro.list_macros(); return True

    # ── Dashboard ─────────────────────────────────────────────────────────────
    if not hasattr(self, 'gesture_dashboard'):
        self.gesture_dashboard = GestureDashboard(self.executor, self.msg)

    if "gesture dashboard" in t or "gesture istatistik" in t:
        self.gesture_dashboard.show_dashboard(); return True
    if "gesture optimizasyon" in t or "jest optimizasyon" in t:
        self.gesture_dashboard.suggest_optimizations(); return True

    # ── Tam Kontrol (güncellenmiş) ────────────────────────────────────────────
    if "ultra gesture başlat" in t or "tüm gesture başlat" in t:
        self.start_all()
        if not hasattr(self, 'finger_counter'):
            self.finger_counter = FingerCounter(self.executor)
        self.finger_counter.start()
        if not hasattr(self, 'face_pos'):
            self.face_pos = FacePositionController(self.executor)
        self.face_pos.start()
        self.msg("ANKA",
            "🚀 ULTRA GESTURE MODU AKTİF!\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "✅ Göz kırpma (8 çeşit)\n"
            "✅ El hareketleri (20+ çeşit)\n"
            "✅ Baş hareketleri (6 çeşit)\n"
            "✅ Parmak sayacı (0-5)\n"
            "✅ Yüz konum kontrolü\n"
            "✅ Gesture makroları\n"
            "📷 Kamera ekranda görünmüyor!")
        self.speak("Ultra gesture modu aktif efendim!")
        return True

    # ── Yardım (güncellenmiş) ─────────────────────────────────────────────────
    if "gesture yardım" in t or "jest yardım" in t:
        r = (
            "🎮 GESTURE v3 — TAM REHBER\n"
            "════════════════════════════\n\n"
            "🚀 BAŞLATMA:\n"
            "• 'ultra gesture başlat' → Hepsi\n"
            "• 'jest kontrolü başlat' → Temel\n"
            "• 'parmak sayacı başlat'\n"
            "• 'yüz konum kontrolü'\n"
            "• 'el hız algılayıcı'\n\n"
            "👁️ GÖZ (8):\n"
            "1,2,3 kırpma | Uzun | L/R wink\n"
            "Gülümse | Kaş kaldır\n\n"
            "🖐️ EL (20+):\n"
            "Yumruk,Açık,👍,👎,☝️,✌️,🤘\n"
            "🤙,👌,🤌,3,4 parmak\n"
            "Spider-Man,Silah,Çapraz\n"
            "Sola/Sağa/Yukarı/Aşağı kaydır\n"
            "İki el: Açık,Yumruk,İşaret\n\n"
            "🔢 PARMAK SAYACI:\n"
            "0→Dur | 1→Ses | 2→Ekran\n"
            "3→Sistem | 4→Rapor | 5→Hava\n\n"
            "👀 YÜZ KONUM:\n"
            "Sol/Sağ/Yukarı/Aşağı bak\n\n"
            "🔗 MAKROLAR:\n"
            "• 'gesture makro ekle g1+g2=komut'\n"
            "• 'gesture makrolar'\n\n"
            "📊 İSTATİSTİK:\n"
            "• 'gesture dashboard'\n"
            "• 'gesture optimizasyon'\n\n"
            "⚙️ AYAR:\n"
            "• 'jest ayarla [hareket] = [komut]'\n"
            "• 'parmak komutu ayarla 3 = haber'\n\n"
            "⏹️ DURDUR:\n"
            "• 'jest kontrolünü durdur'"
        )
        self.msg("ANKA", r)
        self.speak("Gesture rehberi hazırlandı efendim.")
        return True

    # Orijinal process'e devret
    return _original_process(self, text)

# Monkey-patch
GestureCommandProcessor.process = _new_process
