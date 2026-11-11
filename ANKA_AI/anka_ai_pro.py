# ── ANKA AI PRO MODÜLü ───────────────────────────────────────────────────────
# GPT-4 Vision, Kod Asistanı, Web Arama, Veri Analizi, Gerçek Zamanlı Çeviri
try:
    import pyperclip
except ImportError:
    class _PyClip:
        def copy(self,x):pass
        def paste(self):return ""
    pyperclip=_PyClip()
try:
    import pyautogui
except ImportError:
    pyautogui=None
import json, os, time, threading, datetime, subprocess, random, webbrowser
import requests, re, base64, tempfile
from anka_config import BASE_DIR

MEMORY_LONG_FILE = os.path.join(BASE_DIR, "anka_long_memory.json")
RESEARCH_FILE    = os.path.join(BASE_DIR, "anka_research.json")

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


# ── Uzun Süreli Hafıza ───────────────────────────────────────────────────────
class LongTermMemory:
    def __init__(self, ollama):
        self.ollama = ollama
        self.data = _load(MEMORY_LONG_FILE, {
            "facts": [],
            "preferences": {},
            "patterns": {},
            "emotions": [],
            "important_dates": {}
        })

    def learn_from_conversation(self, text):
        """Konuşmadan önemli bilgileri çıkar ve kaydet"""
        # Önemli bilgi içeriyor mu kontrol et
        keywords = ["seviyorum","sevmiyorum","istiyorum","istemiyorum",
                   "her zaman","hiç","doğum günüm","annem","babam","arkadaşım",
                   "okulum","işim","hobim","en sevdiğim"]
        if any(kw in text.lower() for kw in keywords):
            fact = self.ollama.chat(
                f"Bu cümleden kişisel bir bilgi/tercih var mı? Varsa tek cümleyle yaz, yoksa 'YOK' yaz:\n'{text}'",
                system_override="Kişisel bilgi çıkar. Sadece bilgiyi yaz veya YOK de."
            )
            if fact and "YOK" not in fact.upper() and len(fact) > 3:
                self.data["facts"].append({
                    "fact": fact,
                    "date": datetime.datetime.now().isoformat(),
                    "source": text[:100]
                })
                if len(self.data["facts"]) > 200:
                    self.data["facts"] = self.data["facts"][-200:]
                _save(MEMORY_LONG_FILE, self.data)

    def get_context(self):
        """Konuşmaya bağlam için hafızadan bilgi getir"""
        if not self.data["facts"]:
            return ""
        recent = self.data["facts"][-10:]
        return "Kullanıcı hakkında bilinen bilgiler:\n" + \
               "\n".join(f"• {f['fact']}" for f in recent)

    def remember(self, info):
        self.data["facts"].append({
            "fact": info,
            "date": datetime.datetime.now().isoformat(),
            "source": "manuel"
        })
        _save(MEMORY_LONG_FILE, self.data)

    def get_all_facts(self, limit=20):
        return self.data["facts"][-limit:]

    def log_emotion(self, emotion, text):
        self.data["emotions"].append({
            "emotion": emotion,
            "text": text[:100],
            "date": datetime.datetime.now().isoformat()
        })
        _save(MEMORY_LONG_FILE, self.data)


# ── GPT-4 Vision (OpenRouter) ────────────────────────────────────────────────
def analyze_image_openrouter(image_path, question, api_key):
    """OpenRouter Vision API ile görsel analiz"""
    try:
        with open(image_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()

        # Dosya uzantısına göre media type
        ext = os.path.splitext(image_path)[1].lower()
        media_types = {".jpg":"image/jpeg",".jpeg":"image/jpeg",
                       ".png":"image/png",".gif":"image/gif",".webp":"image/webp"}
        media_type = media_types.get(ext, "image/jpeg")

        data = json.dumps({
            "model": "google/gemini-2.0-flash-exp:free",
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "image_url",
                     "image_url": {"url": f"data:{media_type};base64,{img_b64}"}},
                    {"type": "text", "text": question + " Türkçe cevap ver."}
                ]
            }],
            "max_tokens": 1000
        }).encode("utf-8")

        req_obj = __import__("urllib.request", fromlist=["Request","urlopen"])
        req = req_obj.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "https://anka-ai.local",
                "X-Title": "Anka AI"
            }
        )
        import urllib.request
        with urllib.request.urlopen(req, timeout=30) as r:
            resp = json.loads(r.read())
            return resp["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Görsel analiz hatası: {e}"


# ── Gerçek Zamanlı Web Arama ─────────────────────────────────────────────────
def web_search_and_summarize(query, ollama):
    """DuckDuckGo ile arama yap, sonuçları özetle"""
    try:
        # DuckDuckGo Instant Answer API (ücretsiz, key gerektirmez)
        r = requests.get(
            f"https://api.duckduckgo.com/?q={query}&format=json&t=anka",
            timeout=5
        )
        data = r.json()
        results = []

        # Abstract (özet)
        if data.get("Abstract"):
            results.append(data["Abstract"])

        # Related topics
        for topic in data.get("RelatedTopics", [])[:3]:
            if isinstance(topic, dict) and topic.get("Text"):
                results.append(topic["Text"])

        if results:
            context = "\n".join(results[:5])
            summary = ollama.chat(
                f"Şu arama sonuçlarını Türkçe özetle (kaynak: {query}):\n{context}",
                system_override="Web arama sonuçlarını kısa ve net özetle."
            )
            return summary, results
        else:
            # Haber arama fallback
            r2 = requests.get(
                f"https://news.google.com/rss/search?q={query}&hl=tr&gl=TR&ceid=TR:tr",
                timeout=5
            )
            import xml.etree.ElementTree as ET
            root = ET.fromstring(r2.text)
            items = root.findall(".//item")[:3]
            news = [i.find("title").text for i in items if i.find("title") is not None]
            if news:
                context = "\n".join(news)
                summary = ollama.chat(
                    f"Bu haberleri özetle:\n{context}",
                    system_override="Haberleri Türkçe özetle."
                )
                return summary, news
            return "Sonuç bulunamadı.", []
    except Exception as e:
        return f"Arama hatası: {e}", []


# ── Kod Asistanı ─────────────────────────────────────────────────────────────
class CodeAssistant:
    def __init__(self, ollama):
        self.ollama = ollama

    def review(self, code):
        return self.ollama.chat(
            f"Bu kodu incele, hataları ve iyileştirme önerilerini yaz:\n\n```\n{code}\n```",
            system_override="Sen bir senior yazılım mühendisisin. Kodu detaylı incele."
        )

    def fix_bug(self, code, error=""):
        prompt = f"Bu kodda hata var:\n```\n{code}\n```"
        if error:
            prompt += f"\n\nHata mesajı:\n{error}"
        prompt += "\n\nHatayı bul ve düzelt. Düzeltilmiş kodu ver."
        return self.ollama.chat(
            prompt,
            system_override="Sen bir debug uzmanısın. Hatayı bul ve düzelt."
        )

    def complete(self, partial_code):
        return self.ollama.chat(
            f"Bu kodu tamamla:\n```\n{partial_code}\n```",
            system_override="Sen bir kod tamamlama asistanısın. Kodu mantıklı tamamla."
        )

    def write_tests(self, code):
        return self.ollama.chat(
            f"Bu kod için birim testleri yaz:\n```\n{code}\n```",
            system_override="Sen bir QA mühendisisin. Kapsamlı testler yaz."
        )

    def write_docs(self, code):
        return self.ollama.chat(
            f"Bu kod için dokümantasyon yaz:\n```\n{code}\n```",
            system_override="Kod dokümantasyonu yaz. Türkçe açıkla."
        )

    def optimize(self, code):
        return self.ollama.chat(
            f"Bu kodu optimize et, daha hızlı ve temiz hale getir:\n```\n{code}\n```",
            system_override="Sen bir performans optimizasyon uzmanısın."
        )

    def explain(self, code):
        return self.ollama.chat(
            f"Bu kodu satır satır açıkla:\n```\n{code}\n```",
            system_override="Kodu basit ve anlaşılır Türkçe ile açıkla."
        )


# ── Veri Analizi ─────────────────────────────────────────────────────────────
class DataAnalyst:
    def __init__(self, ollama):
        self.ollama = ollama

    def analyze_csv(self, file_path):
        """CSV dosyasını analiz et"""
        try:
            import csv
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                rows = list(reader)

            if not rows:
                return "Dosya boş."

            headers = rows[0]
            data_rows = rows[1:min(50, len(rows))]
            total_rows = len(rows) - 1

            preview = f"Sütunlar: {', '.join(headers)}\n"
            preview += f"Toplam: {total_rows} satır\n\n"
            preview += "İlk 5 satır:\n"
            for row in data_rows[:5]:
                preview += " | ".join(row[:6]) + "\n"

            analysis = self.ollama.chat(
                f"Bu CSV verisini analiz et:\n{preview}\nÖnemli bulgular ve öneriler?",
                system_override="Sen bir veri analisti sin. Türkçe analiz et."
            )
            return f"📊 {os.path.basename(file_path)} Analizi:\n\n{analysis}"
        except Exception as e:
            return f"CSV analiz hatası: {e}"

    def analyze_text_file(self, file_path):
        """Metin dosyasını analiz et"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()[:3000]
            return self.ollama.chat(
                f"Bu dosyayı analiz et ve özetle:\n\n{content}",
                system_override="Dosya içeriğini analiz et. Türkçe yaz."
            )
        except Exception as e:
            return f"Dosya analiz hatası: {e}"

    def query_data(self, question, data_context):
        """Doğal dille veri sorgula"""
        return self.ollama.chat(
            f"Veri:\n{data_context}\n\nSoru: {question}",
            system_override="Veriden soruyu cevapla. Net ve kısa ol."
        )


# ── Gerçek Zamanlı Çeviri ────────────────────────────────────────────────────
class RealtimeTranslator:
    LANGUAGES = {
        "ingilizce": "English", "almanca": "German",
        "fransızca": "French", "ispanyolca": "Spanish",
        "italyanca": "Italian", "japonca": "Japanese",
        "çince": "Chinese", "arapça": "Arabic",
        "rusça": "Russian", "türkçe": "Turkish",
        "korece": "Korean", "portekizce": "Portuguese"
    }

    def __init__(self, ollama):
        self.ollama = ollama
        self.active_lang = "ingilizce"
        self.realtime_mode = False

    def translate(self, text, target_lang="ingilizce", source_lang="türkçe"):
        target = self.LANGUAGES.get(target_lang, "English")
        source = self.LANGUAGES.get(source_lang, "Turkish")
        return self.ollama.chat(
            f"'{text}' metnini {source}'den {target}'ye çevir. Sadece çeviriyi yaz.",
            system_override=f"Çevirmen. {source} → {target}. Sadece çeviriyi yaz."
        )

    def detect_and_translate(self, text):
        return self.ollama.chat(
            f"Bu metnin dilini tespit et ve Türkçe'ye çevir:\n'{text}'\n\nFormat: [Dil]: [Çeviri]",
            system_override="Dil tespit et ve Türkçe çevir."
        )

    def pronounce(self, text, lang="ingilizce"):
        return self.ollama.chat(
            f"'{text}' {lang} kelimesinin Türkçe telaffuzunu yaz. Örn: 'hello' → 'helo'",
            system_override="Kelime telaffuzunu fonetik olarak yaz."
        )


# ── Web Scraper ───────────────────────────────────────────────────────────────
def scrape_url(url, ollama):
    """URL'den içerik çek ve özetle"""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        r = requests.get(url, headers=headers, timeout=8)
        r.encoding = 'utf-8'

        # HTML'den metin çıkar
        text = r.text
        # Basit HTML tag temizleme
        import re
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        text = text[:3000]

        summary = ollama.chat(
            f"Bu web sayfası içeriğini özetle:\nURL: {url}\n\n{text}",
            system_override="Web sayfasını özetle. Ana konuyu ve önemli bilgileri ver."
        )
        return summary
    except Exception as e:
        return f"Web sayfası alınamadı: {e}"


# ── Proaktif Asistan ─────────────────────────────────────────────────────────
class ProactiveAssistant:
    """Kullanıcı sormadan önce öneri yapan sistem"""
    def __init__(self, speak_func, msg_func, ollama):
        self.speak = speak_func
        self.msg = msg_func
        self.ollama = ollama
        self.running = True
        self.last_suggestions = {}
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        time.sleep(60)
        while self.running:
            try:
                now = datetime.datetime.now()
                today = now.date().isoformat()

                # Sabah önerisi
                if now.hour == 8 and now.minute == 30:
                    key = f"morning_{today}"
                    if key not in self.last_suggestions:
                        self.last_suggestions[key] = True
                        self._morning_suggestion()

                # Öğle önerisi
                if now.hour == 12 and now.minute == 0:
                    key = f"lunch_{today}"
                    if key not in self.last_suggestions:
                        self.last_suggestions[key] = True
                        self._lunch_suggestion()

                # Akşam önerisi
                if now.hour == 18 and now.minute == 0:
                    key = f"evening_{today}"
                    if key not in self.last_suggestions:
                        self.last_suggestions[key] = True
                        self._evening_suggestion()

                # Hava değişikliği kontrolü
                if now.minute == 0:
                    self._check_weather_change()

            except: pass
            time.sleep(60)

    def _morning_suggestion(self):
        try:
            from anka_memory import get_pending_tasks
            tasks = get_pending_tasks()
            r = requests.get("https://wttr.in/Istanbul?format=j1", timeout=3)
            d = r.json()["current_condition"][0]
            temp = d["temp_C"]
            msg = f"🌅 Günaydın efendim! Bugün {temp}°C."
            if tasks:
                msg += f" {len(tasks)} bekleyen göreviniz var."
            msg += " İyi günler!"
            self.msg("ANKA", msg)
            self.speak(msg)
        except: pass

    def _lunch_suggestion(self):
        suggestions = [
            "🍽 Öğle yemeği zamanı efendim! Sağlıklı bir şeyler yiyin.",
            "🥗 Öğle oldu efendim! Bir mola vermeyi unutmayın.",
            "☕ Öğlen molası vakti efendim!"
        ]
        msg = random.choice(suggestions)
        self.msg("ANKA", msg)
        self.speak(msg)

    def _evening_suggestion(self):
        try:
            from anka_memory import get_pending_tasks
            tasks = get_pending_tasks()
            msg = "🌆 Akşam oldu efendim!"
            if tasks:
                msg += f" Bugün {len(tasks)} göreviniz tamamlanmayı bekliyor."
            self.msg("ANKA", msg)
            self.speak(msg)
        except: pass

    def _check_weather_change(self):
        try:
            r = requests.get("https://wttr.in/Istanbul?format=j1", timeout=3)
            d = r.json()
            code = int(d["current_condition"][0].get("weatherCode", 0))
            if code in [389, 386, 200, 201, 371, 338]:
                msg = "⛈ Dikkat efendim! Hava kötüleşiyor."
                self.msg("SİSTEM", msg)
                self.speak(msg)
        except: pass

    def stop(self): self.running = False


# ── Ana Komut İşleyici ────────────────────────────────────────────────────────
class AiProCommandProcessor:
    def __init__(self, speak_func, msg_func, ollama, api_key=""):
        self.speak = speak_func
        self.msg = msg_func
        self.ollama = ollama
        self.api_key = api_key
        self.code_assistant = CodeAssistant(ollama)
        self.data_analyst = DataAnalyst(ollama)
        self.translator = RealtimeTranslator(ollama)
        self.long_memory = LongTermMemory(ollama)
        self._pending_code = None

    def process(self, text):
        t = text.lower().strip()

        # ── Hafıza ───────────────────────────────────────────────────────────
        if "bunu hatırla" in t or "kaydet hafızana" in t:
            info = t.replace("bunu hatırla","").replace("kaydet hafızana","").strip()
            if info:
                self.long_memory.remember(info)
                r = f"✓ Kaydedildi efendim: {info}"
                self.msg("ANKA",r); self.speak(r)
            return True

        if "ne biliyorsun benim hakkımda" in t or "hakkımda ne biliyorsun" in t:
            facts = self.long_memory.get_all_facts(10)
            if not facts:
                r = "Henüz hakkınızda özel bir bilgi kaydetmedim efendim."
            else:
                r = "🧠 Hakkınızda bildiklerim:\n" + \
                    "\n".join(f"• {f['fact']}" for f in facts)
            self.msg("ANKA",r); self.speak(r)
            return True

        # ── Görsel Analiz ────────────────────────────────────────────────────
        if "fotoğrafı analiz et" in t or "resmi analiz et" in t or "ekranı analiz et" in t:
            if "ekran" in t:
                path = os.path.join(tempfile.gettempdir(), "anka_screen.png")
                pyautogui.screenshot(path)
                question = t.replace("ekranı analiz et","").strip() or "Ekranda ne görüyorsun?"
            else:
                path = None
                question = t

            if path:
                self.msg("ANKA","🔍 Analiz yapılıyor...")
                def _analyze():
                    if self.api_key:
                        result = analyze_image_openrouter(path, question, self.api_key)
                    else:
                        result = "Görsel analiz için OpenRouter API key gerekli efendim."
                    self.msg("ANKA", f"👁 {result}")
                    self.speak(result[:200])
                threading.Thread(target=_analyze, daemon=True).start()
            return True

        # ── Web Arama ────────────────────────────────────────────────────────
        if "araştır" in t or "web'de ara" in t or "internette araştır" in t:
            query = t.replace("araştır","").replace("web'de ara","").replace("internette araştır","").strip()
            if query:
                self.msg("ANKA","🔍 Araştırılıyor...")
                def _search():
                    result, sources = web_search_and_summarize(query, self.ollama)
                    self.msg("ANKA", f"🌐 {query}:\n\n{result}")
                    self.speak(result[:200])
                threading.Thread(target=_search, daemon=True).start()
            return True

        # ── URL Özetle ───────────────────────────────────────────────────────
        if "siteyi özetle" in t or "url özetle" in t or t.startswith("http"):
            url = re.search(r'https?://\S+', text)
            if url:
                self.msg("ANKA","📄 Site okunuyor...")
                def _scrape():
                    result = scrape_url(url.group(0), self.ollama)
                    self.msg("ANKA", f"🌐 Site Özeti:\n{result}")
                    self.speak(result[:200])
                threading.Thread(target=_scrape, daemon=True).start()
            return True

        # ── Kod Review ───────────────────────────────────────────────────────
        if "kodu incele" in t or "kod review" in t or "kodu analiz et" in t:
            self.msg("ANKA","Kodu buraya yapıştırın efendim.")
            self._pending_code = "review"
            return True

        if "bug bul" in t or "hatayı bul" in t:
            self.msg("ANKA","Kodu ve hata mesajını yapıştırın efendim.")
            self._pending_code = "bug"
            return True

        if "kodu tamamla" in t:
            self.msg("ANKA","Yarım kodu yapıştırın efendim.")
            self._pending_code = "complete"
            return True

        if "test yaz" in t or "unit test" in t:
            self.msg("ANKA","Kodu yapıştırın, test yazayım efendim.")
            self._pending_code = "test"
            return True

        if "dokümantasyon yaz" in t or "docstring yaz" in t:
            self.msg("ANKA","Kodu yapıştırın efendim.")
            self._pending_code = "docs"
            return True

        if "kodu optimize et" in t or "kodu hızlandır" in t:
            self.msg("ANKA","Kodu yapıştırın efendim.")
            self._pending_code = "optimize"
            return True

        if "kodu açıkla" in t or "kod nedir" in t:
            self.msg("ANKA","Kodu yapıştırın efendim.")
            self._pending_code = "explain"
            return True

        # Bekleyen kod işlemi
        if self._pending_code and ("def " in text or "import " in text or
            "{" in text or "function" in text or text.startswith("    ")):
            action = self._pending_code
            self._pending_code = None
            self.msg("ANKA","💻 Analiz yapılıyor...")
            def _code_action():
                if action == "review":   result = self.code_assistant.review(text)
                elif action == "bug":    result = self.code_assistant.fix_bug(text)
                elif action == "complete": result = self.code_assistant.complete(text)
                elif action == "test":   result = self.code_assistant.write_tests(text)
                elif action == "docs":   result = self.code_assistant.write_docs(text)
                elif action == "optimize": result = self.code_assistant.optimize(text)
                elif action == "explain": result = self.code_assistant.explain(text)
                else: result = "Bilinmeyen işlem."
                self.msg("ANKA", f"💻 {result}")
                pyperclip.copy(result)
                self.speak("Analiz tamamlandı, panoya kopyalandı efendim.")
            threading.Thread(target=_code_action, daemon=True).start()
            return True

        # ── CSV/Dosya Analizi ────────────────────────────────────────────────
        if "csv analiz et" in t or "dosya analiz et" in t or "excel analiz et" in t:
            self.msg("ANKA","Dosya yolunu söyleyin efendim. Örn: 'C:\\Users\\yusuf\\Desktop\\data.csv'")
            return True

        # ── Çeviri ───────────────────────────────────────────────────────────
        if "gerçek zamanlı çeviri" in t or "anlık çeviri" in t:
            lang = next((l for l in self.translator.LANGUAGES if l in t), "ingilizce")
            self.translator.active_lang = lang
            self.translator.realtime_mode = True
            r = f"✓ Gerçek zamanlı çeviri aktif: Türkçe → {lang.capitalize()}. 'Çeviriyi kapat' ile durdur."
            self.msg("ANKA",r); self.speak(r)
            return True

        if "çeviriyi kapat" in t:
            self.translator.realtime_mode = False
            r = "✓ Çeviri modu kapatıldı efendim."
            self.msg("ANKA",r); self.speak(r)
            return True

        if self.translator.realtime_mode:
            def _tr():
                result = self.translator.translate(text, self.translator.active_lang)
                self.msg("ANKA", f"🌍 {self.translator.active_lang.capitalize()}: {result}")
                self.speak(result[:200])
            threading.Thread(target=_tr, daemon=True).start()
            return True

        # Tek seferlik çeviri
        if "çevir" in t:
            langs = list(self.translator.LANGUAGES.keys())
            target = next((l for l in langs if l in t and l != "türkçe"), "ingilizce")
            content = re.sub(r'\b(çevir|için|türkçe|e|ye|ya|a)\b', '', t).strip()
            if content and len(content) > 2:
                def _single_tr():
                    result = self.translator.translate(content, target)
                    self.msg("ANKA", f"🌍 {target.capitalize()}: {result}")
                    self.speak(result[:200])
                threading.Thread(target=_single_tr, daemon=True).start()
                return True

        # ── Telaffuz ─────────────────────────────────────────────────────────
        if "nasıl telaffuz" in t or "nasıl okunur" in t:
            word = t.replace("nasıl telaffuz edilir","").replace("nasıl okunur","").strip()
            if word:
                def _pron():
                    result = self.translator.pronounce(word)
                    self.msg("ANKA", f"🗣 {word}: {result}")
                    self.speak(result[:100])
                threading.Thread(target=_pron, daemon=True).start()
            return True

        # ── Akademik Araştırma ────────────────────────────────────────────────
        if "akademik" in t or "makale bul" in t or "araştırma makalesi" in t:
            query = t.replace("akademik","").replace("makale bul","").replace("araştırma makalesi","").strip()
            if query:
                webbrowser.open(f"https://scholar.google.com/scholar?q={query}")
                self.msg("ANKA", f"📚 Google Scholar'da '{query}' aranıyor efendim.")
                self.speak(f"Google Scholar'da arama yapıldı efendim.")
            return True

        # ── Duygu Tespiti ─────────────────────────────────────────────────────
        if "nasıl hissediyorum" in t or "duygumu söyle" in t:
            mood = self.ollama.chat(
                f"Bu kişinin duygu durumunu tek kelimeyle söyle: '{text}'",
                system_override="Duygu tespiti yap. Sadece tek kelime."
            )
            r = f"🎭 Duygu analizim: {mood.strip()}"
            self.msg("ANKA",r); self.speak(r)
            return True

        # ── Karşılaştırmalı Analiz ────────────────────────────────────────────
        if " mi " in t and (" iyi" in t or " yoksa" in t):
            def _compare():
                result = self.ollama.chat(
                    f"Şu soruyu analiz et ve karşılaştırmalı cevap ver: {text}",
                    system_override="Nesnel karşılaştırma yap. Artı ve eksileri listele."
                )
                self.msg("ANKA", f"⚖️ Karşılaştırma:\n{result}")
                self.speak(result[:200])
            threading.Thread(target=_compare, daemon=True).start()
            return True

        return False
