# ── ANKA GÜVENLİK MODÜLü ────────────────────────────────────────────────────
import cv2, os, json, numpy as np, threading, time
from anka_config import FACE_DIR, USER_NAME

AUTHORIZED = False
PIN_CODE = "1234"  # Değiştir

# ── Yüz Kayıt ────────────────────────────────────────────────────────────────
def register_face(name=USER_NAME, timeout_seconds=30):
    """Hızlı yüz kaydı — 20 örnek, 30 saniye limit, ESC/Q/X ile kapanır"""
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ANKA] Kamera açılamadı!")
        return False

    # Kamera ısınması için bekle
    time.sleep(0.5)

    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    samples = []
    count = 0
    start_time = time.time()
    window_name = "Anka Yuz Kaydı - ESC/Q ile kapat"
    TARGET = 20  # 30'dan 20'ye düşürdük - daha hızlı

    try:
        while count < TARGET and (time.time() - start_time) < timeout_seconds:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.05)
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # Parametre optimizasyonu - daha hızlı algılama
            faces = face_cascade.detectMultiScale(
                gray, scaleFactor=1.2, minNeighbors=4,
                minSize=(80, 80))

            for (x, y, w, h) in faces:
                samples.append(gray[y:y+h, x:x+w])
                count += 1
                cv2.rectangle(frame, (x,y), (x+w,y+h), (0,255,0), 2)

            # UI
            progress = int((count / TARGET) * 100)
            cv2.rectangle(frame, (10,40), (10 + progress*2, 55), (0,255,0), -1)
            cv2.putText(frame, f"Kayıt: {count}/{TARGET} (%{progress})",
                        (10,35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)
            cv2.putText(frame, "ESC veya Q: Kapat",
                        (10, frame.shape[0]-15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,200,255), 1)
            remaining = int(timeout_seconds - (time.time() - start_time))
            cv2.putText(frame, f"Sure: {remaining}s",
                        (frame.shape[1]-100, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,200,0), 2)

            cv2.imshow(window_name, frame)
            key = cv2.waitKey(30) & 0xFF
            if key in [ord('q'), ord('Q'), 27]:  # 27=ESC
                break

            # Pencere X'le kapatıldı mı?
            try:
                if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                    break
            except: break

    finally:
        cap.release()
        cv2.destroyAllWindows()
        for _ in range(5):
            cv2.waitKey(1)

    print(f"[ANKA] Yüz kaydı: {count} örnek toplandı")

    if len(samples) >= 5:  # En az 5 örnek yeterli
        try:
            recognizer = cv2.face.LBPHFaceRecognizer_create()
            labels = [0] * len(samples)
            recognizer.train(samples, np.array(labels))
            model_path = os.path.join(FACE_DIR, f"{name}_model.yml")
            recognizer.save(model_path)
            with open(os.path.join(FACE_DIR, "users.json"), "w") as f:
                json.dump({"0": name}, f)
            print(f"[ANKA] Yüz modeli kaydedildi: {model_path}")
            return True
        except Exception as e:
            print(f"[ANKA] Model kayıt hatası: {e}")
            return False
    else:
        print(f"[ANKA] Yetersiz örnek: {len(samples)}")
        return False


# ── Yüz Tanıma ───────────────────────────────────────────────────────────────
def recognize_face(timeout=12):
    global AUTHORIZED
    model_path = os.path.join(FACE_DIR, f"{USER_NAME}_model.yml")
    if not os.path.exists(model_path):
        AUTHORIZED = True
        return True, "Model yok, giriş açık"

    try:
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        recognizer.read(model_path)
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap = cv2.VideoCapture(0)

        start = time.time()
        result = False
        name_found = "Bilinmeyen"
        attempts = 0

        while time.time() - start < timeout:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.1)
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(
                gray, scaleFactor=1.2, minNeighbors=4, minSize=(80,80))

            for (x,y,w,h) in faces:
                face = gray[y:y+h, x:x+w]
                try:
                    label, confidence = recognizer.predict(face)
                    attempts += 1
                    print(f"[ANKA] Yüz güven: {confidence:.1f}")
                    if confidence < 85:  # Eşiği biraz gevşettik
                        result = True
                        name_found = USER_NAME
                        AUTHORIZED = True
                        break
                except: pass

            if result:
                break
            time.sleep(0.05)

        cap.release()

        if not result:
            _save_intruder_photo()

        return result, name_found

    except Exception as e:
        AUTHORIZED = True
        return True, f"Hata: {e}"


def _save_intruder_photo():
    try:
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        ret, frame = cap.read()
        if ret:
            path = os.path.join(FACE_DIR, f"intruder_{int(time.time())}.jpg")
            cv2.imwrite(path, frame)
            print(f"[ANKA] Yetkisiz giriş fotoğrafı: {path}")
        cap.release()
    except: pass


# ── PIN ───────────────────────────────────────────────────────────────────────
def verify_pin(pin):
    global AUTHORIZED
    if pin == PIN_CODE:
        AUTHORIZED = True
        return True
    return False

def is_authorized(): return AUTHORIZED
def logout():
    global AUTHORIZED
    AUTHORIZED = False


# ── Ses Parmak İzi ───────────────────────────────────────────────────────────
class VoiceAuth:
    def __init__(self):
        self.voice_profile = None
        self.profile_path = os.path.join(FACE_DIR, "voice_profile.npy")
        if os.path.exists(self.profile_path):
            try:
                self.voice_profile = np.load(self.profile_path)
                print("[ANKA] Ses profili yüklendi")
            except: pass

    def register_voice(self, audio_data, sample_rate=16000):
        features = self._extract(audio_data, sample_rate)
        self.voice_profile = features
        try:
            np.save(self.profile_path, features)
            return True
        except:
            return False

    def verify_voice(self, audio_data, sample_rate=16000, threshold=0.70):
        if self.voice_profile is None:
            return True  # Profil yoksa herkese izin ver
        features = self._extract(audio_data, sample_rate)
        if np.linalg.norm(features) == 0 or np.linalg.norm(self.voice_profile) == 0:
            return True
        similarity = np.dot(self.voice_profile, features) / (
            np.linalg.norm(self.voice_profile) * np.linalg.norm(features) + 1e-10)
        print(f"[ANKA] Ses benzerliği: {similarity:.3f} (eşik: {threshold})")
        return float(similarity) > threshold

    def _extract(self, audio, sr=16000):
        audio = np.array(audio, dtype=np.float32)
        if len(audio) == 0:
            return np.zeros(30)
        frame_size = sr // 10
        hop = frame_size // 2
        features = []
        for i in range(0, max(1, len(audio)-frame_size), hop):
            frame = audio[i:i+frame_size]
            if len(frame) > 0:
                energy = float(np.sqrt(np.mean(frame**2)))
                zcr = float(np.mean(np.abs(np.diff(np.sign(frame)))) / 2)
                features.extend([energy, zcr])
        features = features[:30] if len(features) >= 30 else features + [0]*(30-len(features))
        feat = np.array(features[:30], dtype=np.float32)
        norm = np.linalg.norm(feat)
        return feat / norm if norm > 0 else feat


# ── Yabancı Ses Kilitleme ─────────────────────────────────────────────────────
class VoiceLockSystem:
    """Yabancı ses gelince ekranı kilitler"""
    def __init__(self, voice_auth, lock_callback, enabled=False):
        self.auth = voice_auth
        self.lock_callback = lock_callback
        self.enabled = enabled
        self.fail_count = 0
        self.FAIL_LIMIT = 3  # 3 yabancı ses → kilitle

    def check(self, audio_data):
        if not self.enabled or self.auth.voice_profile is None:
            return True
        if self.auth.verify_voice(audio_data):
            self.fail_count = 0
            return True
        else:
            self.fail_count += 1
            print(f"[ANKA] Yabancı ses #{self.fail_count}")
            if self.fail_count >= self.FAIL_LIMIT:
                self.fail_count = 0
                if self.lock_callback:
                    self.lock_callback()
            return False
