# ── ANKA SES MODÜLü ──────────────────────────────────────────────────────────
import asyncio, os, subprocess, tempfile, threading
import sounddevice as sd, numpy as np, scipy.io.wavfile as wavfile

async def _tts_async(text, out):
    try:
        import edge_tts
        # tr-TR-AhmetNeural — Türkçe erkek sesi
        c = edge_tts.Communicate(text, voice="tr-TR-AhmetNeural", rate="+5%", pitch="-5Hz")
        await c.save(out)
        _play_audio(out)
    except Exception as e:
        print(f"[ANKA TTS] Oluşturma hatası: {e}")

def _play_audio(path):
    try:
        import pygame
        pygame.mixer.init()
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()
        import time
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
        pygame.mixer.music.unload()
        try: os.unlink(path)
        except: pass
        return
    except Exception as e:
        print(f"[ANKA TTS] pygame hatası: {e}")
    try:
        ps = (f'Add-Type -AssemblyName presentationCore; '
              f'$mp=New-Object System.Windows.Media.MediaPlayer; '
              f'$mp.Open([uri]"{path}"); $mp.Play(); '
              f'Start-Sleep -Milliseconds 500; '
              f'$timeout=0; while(-not $mp.NaturalDuration.HasTimeSpan -and $timeout -lt 30)'
              f'{{Start-Sleep -Milliseconds 200; $timeout++}}; '
              f'$len = if($mp.NaturalDuration.HasTimeSpan){{$mp.NaturalDuration.TimeSpan.TotalSeconds}}else{{5}}; '
              f'Start-Sleep -Seconds $len; $mp.Stop(); $mp.Close()')
        subprocess.run(["powershell","-NoProfile","-Command",ps], timeout=30,
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"[ANKA TTS] PowerShell hatası: {e}")

def speak(text):
    if not text: return
    def _s():
        try:
            clean = text.replace('"','').replace("'",'')[:500]
            tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
            tmp.close()
            asyncio.run(_tts_async(clean, tmp.name))
        except Exception as e:
            try:
                clean2 = text.replace('"','').replace("'",'')[:400]
                ps = (f'Add-Type -AssemblyName System.Speech; '
                      f'$s=New-Object System.Speech.Synthesis.SpeechSynthesizer; '
                      f'$s.Rate=0; '
                      f'foreach($v in $s.GetInstalledVoices()){{if($v.VoiceInfo.Culture.Name -like "*tr*")'
                      f'{{$s.SelectVoice($v.VoiceInfo.Name); break}}}}; '
                      f'$s.Speak("{clean2}")')
                subprocess.run(["powershell","-Command",ps], timeout=20,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except: pass
    threading.Thread(target=_s, daemon=True).start()


class VoiceRecorder:
    def __init__(self):
        self.recording = False
        self.audio_data = []
        self.sample_rate = 16000
        self.whisper_model = None
        self.ready = False
        # Lazy load — başlangıçta yükleme, ilk kullanımda yükle
        threading.Thread(target=self._load, daemon=True).start()

    def _load(self):
        try:
            import whisper
            # tiny model — çok daha az RAM, hız kazanımı
            self.whisper_model = whisper.load_model("tiny")
            self.ready = True
            print("[ANKA] Whisper tiny modeli yüklendi! (Düşük RAM modu)")
        except Exception as e:
            print(f"Whisper yüklenemedi: {e}")

    def start(self):
        self.recording = True
        self.audio_data = []
        self.stream = sd.InputStream(
            samplerate=self.sample_rate, channels=1,
            dtype='float32', callback=self._cb)
        self.stream.start()

    def _cb(self, indata, frames, t, s):
        if self.recording:
            self.audio_data.extend(indata[:, 0].tolist())

    def stop_and_transcribe(self):
        self.recording = False
        if hasattr(self, 'stream'):
            self.stream.stop()
            self.stream.close()
        audio = np.array(self.audio_data, dtype=np.float32)
        return self._transcribe(audio), audio

    def transcribe_audio(self, audio_data):
        """Dışarıdan ses verisi gönderilerek çeviri yapılır"""
        return self._transcribe(audio_data)

    def _transcribe(self, audio):
        if audio is None or len(audio) == 0 or not self.whisper_model:
            return ""
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                tmp = f.name
            wavfile.write(tmp, self.sample_rate, audio)
            result = self.whisper_model.transcribe(
                tmp, language="tr",
                condition_on_previous_text=False,
                no_speech_threshold=0.5,
                logprob_threshold=-1.0,
                temperature=0.0,  # Daha deterministik sonuç
            )
            os.unlink(tmp)
            return result["text"].strip()
        except Exception as e:
            print(f"[ANKA] Transcribe hatası: {e}")
            return ""
