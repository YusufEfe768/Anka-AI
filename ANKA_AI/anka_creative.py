# ── ANKA YARATICI İÇERİK MODÜLü ─────────────────────────────────────────────
try:
    import pyperclip
except ImportError:
    class _PyClip:
        def copy(self,x):pass
        def paste(self):return ""
    pyperclip=_PyClip()
import json, os, threading, datetime, random, webbrowser
import requests, re
from anka_config import BASE_DIR

class CreativeWriter:
    def __init__(self, ollama, speak_func, msg_func):
        self.ollama = ollama
        self.speak = speak_func
        self.msg = msg_func

    def story(self, genre, characters, setting):
        def _s():
            r = self.ollama.chat(
                f"Tür: {genre}, Karakterler: {characters}, Ortam: {setting}. "
                f"Kısa ve etkileyici bir hikaye yaz. Türkçe.",
                system_override="Yaratıcı yazar. Özgün ve sürükleyici hikaye yaz.")
            self.msg("ANKA", f"📖 Hikaye:\n{r}")
            pyperclip.copy(r)
        threading.Thread(target=_s, daemon=True).start()

    def poem(self, topic, style="serbest"):
        def _p():
            r = self.ollama.chat(
                f"'{topic}' hakkında {style} tarzda şiir yaz.",
                system_override="Şair. Duygusal ve etkileyici şiir yaz.")
            self.msg("ANKA", f"📝 Şiir:\n{r}")
            pyperclip.copy(r)
        threading.Thread(target=_p, daemon=True).start()

    def script(self, scene, characters):
        def _sc():
            r = self.ollama.chat(
                f"Sahne: {scene}, Karakterler: {characters}. Kısa senaryo yaz.",
                system_override="Senarist. Diyalog ağırlıklı senaryo yaz.")
            self.msg("ANKA", f"🎬 Senaryo:\n{r}")
            pyperclip.copy(r)
        threading.Thread(target=_sc, daemon=True).start()

    def song_lyrics(self, topic, genre="pop"):
        def _l():
            r = self.ollama.chat(
                f"'{topic}' hakkında {genre} tarzında şarkı sözü yaz. "
                f"Nakarat ve kıtalar olsun.",
                system_override="Söz yazarı. Orijinal şarkı sözü yaz.")
            self.msg("ANKA", f"🎵 Şarkı Sözü:\n{r}")
            pyperclip.copy(r)
        threading.Thread(target=_l, daemon=True).start()

    def joke(self, topic="genel", style="fıkra"):
        def _j():
            r = self.ollama.chat(
                f"'{topic}' hakkında {style} formatında komik bir şey yaz.",
                system_override="Komedyen. Komik ve esprili yaz.")
            self.msg("ANKA", f"😄 {style.capitalize()}:\n{r}")
            self.speak(r[:200])
        threading.Thread(target=_j, daemon=True).start()

    def riddle(self):
        def _r():
            r = self.ollama.chat(
                "Özgün ve zekice bir Türkçe bilmece yaz. Cevabını da ver.",
                system_override="Bilmece yazarı. Zekice bilmece yaz.")
            self.msg("ANKA", f"🧩 Bilmece:\n{r}")
        threading.Thread(target=_r, daemon=True).start()

    def motivational_speech(self, topic):
        def _m():
            r = self.ollama.chat(
                f"'{topic}' hakkında güçlü motivasyon konuşması yaz. 3-4 paragraf.",
                system_override="Motivasyon konuşmacısı. İlham ver.")
            self.msg("ANKA", f"💪 Motivasyon:\n{r}")
            pyperclip.copy(r)
            self.speak(r[:300])
        threading.Thread(target=_m, daemon=True).start()

    def creative_title(self, topic, count=10):
        def _ct():
            r = self.ollama.chat(
                f"'{topic}' için {count} yaratıcı ve dikkat çekici başlık üret.",
                system_override="Yaratıcı direktör. İlgi çekici başlıklar yaz.")
            self.msg("ANKA", f"✨ Başlıklar:\n{r}")
            pyperclip.copy(r)
        threading.Thread(target=_ct, daemon=True).start()

    def metaphor(self, concept):
        def _met():
            r = self.ollama.chat(
                f"'{concept}' kavramı için 5 yaratıcı metafor yaz.",
                system_override="Dil ustası. Özgün metaforlar yaz.")
            self.msg("ANKA", f"🌟 Metaforlar:\n{r}")
        threading.Thread(target=_met, daemon=True).start()

    def name_generator(self, category, style=""):
        def _n():
            r = self.ollama.chat(
                f"{category} için {style} tarzda 10 isim öner. Açıklamalarıyla.",
                system_override="İsimlendirme uzmanı. Özgün isimler öner.")
            self.msg("ANKA", f"✨ İsim Önerileri:\n{r}")
            pyperclip.copy(r)
        threading.Thread(target=_n, daemon=True).start()

class CreativeCommandProcessor:
    def __init__(self, speak_func, msg_func, ollama):
        self.speak = speak_func
        self.msg = msg_func
        self.ollama = ollama
        self.writer = CreativeWriter(ollama, speak_func, msg_func)

    def process(self, text):
        t = text.lower().strip()

        if "hikaye yaz" in t:
            genre = "macera"
            for g in ["macera","romantik","korku","bilim kurgu","komedi","dram"]:
                if g in t: genre = g; break
            topic = t.replace("hikaye yaz","").replace(genre,"").strip()
            self.writer.story(genre, "Ana karakter", topic or "şehir")
            return True

        if "şiir yaz" in t:
            topic = t.replace("şiir yaz","").strip()
            style = "haiku" if "haiku" in t else "sone" if "sone" in t else "serbest"
            self.writer.poem(topic or "hayat", style)
            return True

        if "şarkı sözü" in t and "yaz" in t:
            topic = t.replace("şarkı sözü yaz","").strip()
            genre = "pop" if "pop" in t else "rap" if "rap" in t else "pop"
            self.writer.song_lyrics(topic or "aşk", genre)
            return True

        if "fıkra anlat" in t or "espri yap" in t:
            topic = t.replace("fıkra anlat","").replace("espri yap","").strip()
            self.writer.joke(topic or "genel")
            return True

        if "bilmece sor" in t or "yeni bilmece" in t:
            self.writer.riddle()
            return True

        if "motivasyon konuşması" in t:
            topic = t.replace("motivasyon konuşması","").strip()
            self.writer.motivational_speech(topic or "başarı")
            return True

        if "başlık üret" in t or "başlık öner" in t:
            topic = t.replace("başlık üret","").replace("başlık öner","").strip()
            self.writer.creative_title(topic)
            return True

        if "metafor" in t:
            concept = t.replace("metafor yaz","").replace("metafor","").strip()
            self.writer.metaphor(concept)
            return True

        if "isim öner" in t or "isim üret" in t:
            category = t.replace("isim öner","").replace("isim üret","").strip()
            self.writer.name_generator(category or "proje")
            return True

        if "senaryo yaz" in t:
            scene = t.replace("senaryo yaz","").strip()
            self.writer.script(scene or "ofis", "İki karakter")
            return True

        if "yaratıcı içerik" in t:
            topic = t.replace("yaratıcı içerik","").strip()
            def _c():
                r = self.ollama.chat(
                    f"'{topic}' için yaratıcı içerik fikirleri: hikaye, şiir, gönderi öner.",
                    system_override="Yaratıcı direktör. Çeşitli içerik fikirleri ver.")
                self.msg("ANKA", f"🎨 İçerik Fikirleri:\n{r}")
            threading.Thread(target=_c, daemon=True).start()
            return True

        return False
