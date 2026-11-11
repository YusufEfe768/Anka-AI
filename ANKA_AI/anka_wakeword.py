# ── ANKA WAKE WORD + SES DOĞRULAMA MODÜLü ────────────────────────────────────
# "Anka" kelimesini duyunca uyanır, yabancı ses gelince kilitler
# Hiçbir API key gerektirmez, tamamen offline çalışır

import threading, time, numpy as np, sounddevice as sd
import os, tempfile, scipy.io.wavfile as wavfile

WAKE_WORDS = ["anka", "ankara", "anка"]  # Whisper bazen farklı yazabilir

class WakeWordListener:
    def __init__(self, on_wake_callback, on_status_callback=None,
                 sample_rate=16000):
        self.on_wake = on_wake_callback
        self.on_status = on_status_callback or (lambda x: None)
        self.sample_rate = sample_rate
        self.running = False
        self.paused = False
        self.ready = False
        self.whisper_model = None

        # Ses eşikleri
        self.silence_threshold = 0.012  # Sessizlik eşiği
        self.silence_duration   = 1.4   # Sessizlik süresi (saniye)
        self.min_speech_duration= 0.8   # Minimum konuşma süresi
        self.wake_mode = True           # True: sadece "Anka" ile uyan

        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def pause(self): self.paused = True
    def resume(self): self.paused = False

    def _load_whisper(self):
        try:
            import whisper
            self.whisper_model = whisper.load_model("medium")
            self.on_status("✓ Sürekli dinleme aktif — 'Anka' de!")
            self.ready = True
        except Exception as e:
            self.on_status(f"⚠️ Whisper yüklenemedi: {e}")

    def _is_wake_word(self, audio_data):
        """Ses verisinde 'Anka' kelimesi var mı kontrol et"""
        if not self.whisper_model: return False
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                tmp = f.name
            wavfile.write(tmp, self.sample_rate, audio_data)
            result = self.whisper_model.transcribe(
                tmp, language="tr",
                condition_on_previous_text=False,
                no_speech_threshold=0.4,
                temperature=0.0,
            )
            os.unlink(tmp)
            text = result["text"].strip().lower()
            print(f"[ANKA Wake] Duyulan: '{text}'")
            return any(w in text for w in WAKE_WORDS)
        except:
            return False

    def _find_mic(self):
        """En iyi mikrofonu bul"""
        try:
            devices = sd.query_devices()
            # WASAPI Realtek tercih et
            for i, d in enumerate(devices):
                if d['max_input_channels'] > 0:
                    name = d['name'].lower()
                    hostapi = sd.query_hostapis(d['hostapi'])['name'].lower()
                    if 'realtek' in name and 'mic' in name and 'wasapi' in hostapi:
                        print(f"[ANKA] Mikrofon: {d['name']}")
                        return i
            return None
        except:
            return None

    def _run(self):
        # Önce Whisper'ı yükle
        threading.Thread(target=self._load_whisper, daemon=True).start()
        time.sleep(1)

        device = self._find_mic()
        self.running = True

        # İki aşamalı sistem:
        # Aşama 1: Sessizlik/ses algıla (düşük CPU)
        # Aşama 2: "Anka" mı dedi? (Whisper ile kontrol)
        # Aşama 3: Evet ise → gerçek komutu dinle

        speaking = False
        silence_start = None
        speech_start = None
        buffer = []
        state = "wake"  # "wake" veya "command"
        command_buffer = []
        command_speaking = False
        command_silence_start = None
        command_speech_start = None

        def callback(indata, frames, time_info, status):
            nonlocal speaking, silence_start, speech_start, buffer
            nonlocal state, command_buffer, command_speaking
            nonlocal command_silence_start, command_speech_start

            if self.paused or not self.running:
                return

            vol = float(np.sqrt(np.mean(indata[:,0]**2)))

            if state == "wake":
                # Wake word aşaması
                if vol > self.silence_threshold:
                    if not speaking:
                        speaking = True
                        speech_start = time.time()
                        buffer = []
                    silence_start = None
                    buffer.extend(indata[:,0].tolist())
                else:
                    if speaking:
                        buffer.extend(indata[:,0].tolist())
                        if silence_start is None:
                            silence_start = time.time()
                        elif time.time() - silence_start > self.silence_duration:
                            duration = time.time() - speech_start
                            speaking = False
                            silence_start = None
                            if duration >= self.min_speech_duration:
                                audio = np.array(buffer, dtype=np.float32)
                                buffer = []
                                # Wake word kontrolü ayrı thread'de
                                def _check():
                                    nonlocal state
                                    if not self.whisper_model:
                                        # Whisper yüklenene kadar her sesi gönder
                                        self.on_wake(audio)
                                        return
                                    if self._is_wake_word(audio):
                                        print("[ANKA] Wake word algılandı!")
                                        state = "command"
                                        self.on_status("🎤 Dinliyorum...")
                                        # Kısa "buyurun" sesi çal
                                        try:
                                            from anka_voice import speak
                                            speak("Buyurun efendim")
                                        except: pass
                                threading.Thread(target=_check, daemon=True).start()

            elif state == "command":
                # Komut dinleme aşaması — "Anka" dedikten sonra
                if vol > self.silence_threshold * 0.8:
                    if not command_speaking:
                        command_speaking = True
                        command_speech_start = time.time()
                        command_buffer = []
                    command_silence_start = None
                    command_buffer.extend(indata[:,0].tolist())
                else:
                    if command_speaking:
                        command_buffer.extend(indata[:,0].tolist())
                        if command_silence_start is None:
                            command_silence_start = time.time()
                        elif time.time() - command_silence_start > 1.2:
                            duration = time.time() - command_speech_start
                            command_speaking = False
                            command_silence_start = None
                            if duration >= 0.5:
                                audio = np.array(command_buffer, dtype=np.float32)
                                command_buffer = []
                                state = "wake"
                                self.on_status("✓ Sürekli dinleme aktif — 'Anka' de!")
                                self.on_wake(audio)
                    elif time.time() - (command_speech_start or time.time()) > 8:
                        # 8 saniye komut gelmezse wake moduna dön
                        state = "wake"
                        command_speaking = False
                        command_buffer = []

        try:
            try:
                with sd.InputStream(samplerate=self.sample_rate, channels=1,
                                     dtype='float32', callback=callback,
                                     device=device):
                    while self.running:
                        time.sleep(0.1)
            except Exception as e:
                print(f"[ANKA] Seçili cihaz başarısız ({e}), varsayılan deneniyor...")
                self.on_status("⟳ Mikrofon yeniden bağlanıyor...")
                with sd.InputStream(samplerate=self.sample_rate, channels=1,
                                     dtype='float32', callback=callback,
                                     device=None):
                    self.on_status("✓ Sürekli dinleme aktif — 'Anka' de!")
                    while self.running:
                        time.sleep(0.1)
        except Exception as e:
            self.on_status("⚠️ Sürekli dinleme kapalı — 🎤 butonunu kullan")
            print(f"[ANKA] Dinleme başarısız: {e}")

    def stop(self):
        self.running = False
