# ── ANKA MEGA ÖZELLİKLER MODÜLü ──────────────────────────────────────────────
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
import requests, re
from anka_config import BASE_DIR

EXAM_FILE     = os.path.join(BASE_DIR, "anka_exams.json")
TEMPLATE_FILE = os.path.join(BASE_DIR, "anka_templates.json")
WEEKLY_FILE   = os.path.join(BASE_DIR, "anka_weekly.json")

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


# ── Sınav/Ödev Takibi ─────────────────────────────────────────────────────────
class ExamTracker:
    def add(self, name, date_str, subject=""):
        data = _load(EXAM_FILE, [])
        data.append({
            "name": name, "date": date_str,
            "subject": subject,
            "created": datetime.datetime.now().isoformat()
        })
        _save(EXAM_FILE, data)

    def get_upcoming(self):
        data = _load(EXAM_FILE, [])
        today = datetime.date.today()
        upcoming = []
        for item in data:
            try:
                exam_date = datetime.date.fromisoformat(item["date"])
                days_left = (exam_date - today).days
                if days_left >= 0:
                    item["days_left"] = days_left
                    upcoming.append(item)
            except: pass
        return sorted(upcoming, key=lambda x: x["days_left"])

    def get_countdown(self, name):
        data = _load(EXAM_FILE, [])
        today = datetime.date.today()
        for item in data:
            if name.lower() in item["name"].lower():
                try:
                    exam_date = datetime.date.fromisoformat(item["date"])
                    days = (exam_date - today).days
                    return days
                except: pass
        return None


# ── QR Kod Oluşturucu ─────────────────────────────────────────────────────────
def generate_qr(text, output_path=None):
    try:
        import qrcode
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(text)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        if not output_path:
            output_path = os.path.join(os.path.expanduser("~"), "Desktop", "anka_qr.png")
        img.save(output_path)
        return output_path
    except ImportError:
        return None


# ── Kelime Anlamı & Dil ───────────────────────────────────────────────────────
def get_word_meaning(word, ollama):
    return ollama.chat(
        f"'{word}' kelimesinin Türkçe anlamını ve bir örnek cümleyi yaz. Kısa ol.",
        system_override="Sen bir sözlüksün. Kelime anlamı ve örnek cümle ver."
    )

def find_synonyms(word, ollama):
    return ollama.chat(
        f"'{word}' kelimesinin 5 eş anlamlısını yaz. Sadece kelimeleri listele.",
        system_override="Sen bir eş anlamlı sözlüğüsün."
    )

def fix_grammar(text, ollama):
    return ollama.chat(
        f"Şu metindeki dil bilgisi hatalarını düzelt:\n\n{text}",
        system_override="Sen bir dil editörüsün. Hataları düzelt, düzeltilmiş metni ver."
    )


# ── Müzik Zamanlayıcı ─────────────────────────────────────────────────────────
class MusicTimer:
    def __init__(self, speak_func, msg_func):
        self.speak = speak_func
        self.msg = msg_func
        self.active = False

    def start(self, minutes, music_url=None):
        if not music_url:
            music_url = "https://youtube.com/results?search_query=lofi+study+music"
        webbrowser.open(music_url)
        self.active = True
        def _timer():
            time.sleep(minutes * 60)
            if self.active:
                pyautogui.hotkey('ctrl', 'w')  # Sekmeyi kapat
                r = f"✓ {minutes} dakikalık müzik süresi bitti efendim."
                self.msg("ANKA", r); self.speak(r)
                self.active = False
        threading.Thread(target=_timer, daemon=True).start()

    def stop(self):
        self.active = False
        pyautogui.hotkey('ctrl', 'w')


# ── 20 Soru Oyunu ─────────────────────────────────────────────────────────────
class TwentyQuestionsGame:
    def __init__(self, ollama):
        self.ollama = ollama
        self.active = False
        self.subject = None
        self.questions_asked = 0
        self.max_questions = 20

    def start(self, subject):
        self.subject = subject
        self.questions_asked = 0
        self.active = True
        return (f"🎯 Tamam! '{subject}' hakkında bir şey düşündüm. "
                f"Evet/hayır soruları sorarak tahmin etmeye çalışın! "
                f"({self.max_questions} soru hakkınız var)")

    def answer(self, question):
        if not self.active:
            return None
        self.questions_asked += 1
        remaining = self.max_questions - self.questions_asked
        answer = self.ollama.chat(
            f"Ben '{self.subject}' düşünüyorum. Soru: '{question}'. "
            f"Sadece 'Evet', 'Hayır' veya 'Kısmen' ile cevapla.",
            system_override="20 soru oyununda cevap veriyorsun. Sadece Evet/Hayır/Kısmen de."
        )
        if remaining <= 0:
            self.active = False
            return f"{answer} — Sorular bitti! Düşündüğüm şey: {self.subject}"
        return f"{answer} ({remaining} soru kaldı)"

    def guess(self, guess):
        if guess.lower() in self.subject.lower() or self.subject.lower() in guess.lower():
            self.active = False
            return f"🎉 Doğru! {self.questions_asked} soruda buldunuz!"
        return "❌ Yanlış, devam edin!"


# ── Matematik Yarışması ───────────────────────────────────────────────────────
class MathChallenge:
    def __init__(self):
        self.current = None
        self.score = 0
        self.level = 1

    def ask(self):
        ops = ['+', '-', '*']
        op = random.choice(ops)
        if self.level == 1:
            a, b = random.randint(1,20), random.randint(1,20)
        elif self.level == 2:
            a, b = random.randint(10,99), random.randint(1,9)
        else:
            a, b = random.randint(10,99), random.randint(10,99)

        if op == '*' and self.level > 2:
            a, b = random.randint(2,12), random.randint(2,12)

        expr = f"{a} {op} {b}"
        self.current = {"expr": expr, "answer": eval(expr), "start": time.time()}
        return f"⚡ {expr} = ?"

    def answer(self, ans_str):
        if not self.current:
            return "Önce soru sormanız lazım efendim."
        try:
            ans = int(ans_str.strip())
        except:
            return "Geçerli bir sayı girin efendim."
        elapsed = round(time.time() - self.current["start"], 1)
        correct = ans == self.current["answer"]
        if correct:
            self.score += max(1, 5 - int(elapsed))
            if self.score % 5 == 0: self.level = min(3, self.level + 1)
            r = f"✅ Doğru! ({elapsed}s) Puan: {self.score} | Seviye: {self.level}"
        else:
            r = f"❌ Yanlış! Cevap: {self.current['answer']} | Puan: {self.score}"
        self.current = None
        return r


# ── Adam Asmaca ───────────────────────────────────────────────────────────────
class HangmanGame:
    WORDS = ["bilgisayar","klavye","monitör","internet","yazılım","donanım",
             "programlama","algoritma","veritabanı","ağ","güvenlik","yapay",
             "zeka","robot","otomasyon","teknoloji","uygulama","sistem"]

    def __init__(self):
        self.word = None
        self.guessed = []
        self.wrong = []
        self.max_wrong = 6
        self.active = False

    def start(self):
        self.word = random.choice(self.WORDS)
        self.guessed = []
        self.wrong = []
        self.active = True
        return f"🎮 Adam asmaca başladı! {len(self.word)} harfli kelime\n{self._display()}\n{self.max_wrong} hata hakkınız var."

    def guess(self, letter):
        if not self.active:
            return "Oyun aktif değil. 'adam asmaca başlat' deyin."
        letter = letter.lower().strip()
        if len(letter) != 1:
            return "Tek harf girin efendim."
        if letter in self.guessed or letter in self.wrong:
            return "Bu harfi zaten denediniz efendim."
        if letter in self.word:
            self.guessed.append(letter)
            if all(c in self.guessed for c in self.word):
                self.active = False
                return f"🎉 Tebrikler! Kelime: {self.word}"
            return f"✅ Doğru!\n{self._display()}"
        else:
            self.wrong.append(letter)
            remaining = self.max_wrong - len(self.wrong)
            if remaining <= 0:
                self.active = False
                return f"😢 Oyun bitti! Kelime: {self.word}"
            return f"❌ Yanlış! ({remaining} hak kaldı)\n{self._display()}\nYanlışlar: {', '.join(self.wrong)}"

    def _display(self):
        return " ".join(c if c in self.guessed else "_" for c in self.word)


# ── Toplantı Modu ─────────────────────────────────────────────────────────────
class MeetingMode:
    def __init__(self, speak_func, msg_func):
        self.speak = speak_func
        self.msg = msg_func
        self.notes = []
        self.active = False
        self.start_time = None

    def start(self):
        self.active = True
        self.notes = []
        self.start_time = datetime.datetime.now()
        # Bildirimleri kapat
        subprocess.run(["powershell","-Command",
            "Set-ItemProperty -Path 'HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\PushNotifications' -Name ToastEnabled -Value 0"],
            capture_output=True)
        r = "📋 Toplantı modu başladı! Bildirimler kapatıldı. 'Not al: ...' ile not ekleyebilirsiniz."
        self.msg("ANKA", r); self.speak(r)

    def add_note(self, note):
        if not self.active:
            return False
        self.notes.append({
            "note": note,
            "time": datetime.datetime.now().strftime("%H:%M")
        })
        return True

    def end(self, ollama):
        self.active = False
        # Bildirimleri aç
        subprocess.run(["powershell","-Command",
            "Set-ItemProperty -Path 'HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\PushNotifications' -Name ToastEnabled -Value 1"],
            capture_output=True)
        duration = datetime.datetime.now() - self.start_time if self.start_time else None
        duration_str = f"{duration.seconds//60} dakika" if duration else "bilinmiyor"

        if self.notes:
            notes_text = "\n".join(f"[{n['time']}] {n['note']}" for n in self.notes)
            summary = ollama.chat(
                f"Bu toplantı notlarını özetle:\n{notes_text}",
                system_override="Toplantı notlarını kısa ve net özetle."
            )
            r = (f"✅ Toplantı bitti! ({duration_str})\n\n"
                 f"📝 Notlar:\n{notes_text}\n\n"
                 f"📊 Özet:\n{summary}")
        else:
            r = f"✅ Toplantı bitti! ({duration_str}) Not alınmadı."

        self.msg("ANKA", r)
        self.speak("Toplantı modu kapatıldı efendim.")
        return r


# ── Enerji Tasarrufu Modu ─────────────────────────────────────────────────────
def energy_save_mode(speak_func, msg_func):
    killed = []
    unnecessary = ["discord.exe","steam.exe","spotify.exe","teams.exe"]
    for proc in unnecessary:
        result = subprocess.run(["taskkill","/IM",proc,"/F"], capture_output=True)
        if result.returncode == 0:
            killed.append(proc.replace(".exe",""))
    # Parlaklık düşür
    try:
        subprocess.run(["powershell","-Command",
            "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,40)"],
            capture_output=True, timeout=5)
    except: pass
    r = f"⚡ Enerji tasarrufu modu aktif!\n"
    if killed:
        r += f"Kapatılan: {', '.join(killed)}\n"
    r += "Parlaklık %40'a düşürüldü."
    msg_func("ANKA", r); speak_func(r)


# ── Otomatik Görev Çıkarma ────────────────────────────────────────────────────
def extract_task_from_text(text, ollama, add_task_func, add_alarm_func):
    """Konuşmadan otomatik görev/alarm çıkar"""
    # Tarih/zaman içeren ifadeler
    time_keywords = ["yarın","bugün","saat","dakika","sonra","haftaya",
                     "pazartesi","salı","çarşamba","perşembe","cuma","cumartesi","pazar"]
    task_keywords = ["toplantı","sınav","ödev","randevu","işim var","gitmeliyim","unutma","hatırlat"]

    has_time = any(kw in text.lower() for kw in time_keywords)
    has_task = any(kw in text.lower() for kw in task_keywords)

    if has_task and has_time:
        # AI ile görev ve zamanı çıkar
        result = ollama.chat(
            f"Bu cümleden görev/hatırlatıcı bilgisini çıkar: '{text}'\n"
            f"JSON formatında ver: {{\"task\": \"görev\", \"time\": \"zaman\"}}",
            system_override="Cümleden görev ve zaman bilgisini çıkar. Sadece JSON yaz."
        )
        try:
            # JSON parse
            clean = result.replace("```json","").replace("```","").strip()
            data = json.loads(clean)
            task = data.get("task","")
            if task:
                add_task_func(task)
                return task
        except: pass
    return None


# ── Komut İşleyici ────────────────────────────────────────────────────────────
class MegaCommandProcessor:
    def __init__(self, speak_func, msg_func, ollama):
        self.speak = speak_func
        self.msg = msg_func
        self.ollama = ollama
        self.exam_tracker = ExamTracker()
        self.music_timer = MusicTimer(speak_func, msg_func)
        self.twenty_q = TwentyQuestionsGame(ollama)
        self.math_ch = MathChallenge()
        self.hangman = HangmanGame()
        self.meeting = MeetingMode(speak_func, msg_func)

    def process(self, text):
        t = text.lower().strip()

        # ── Sınav/Ödev Takibi ────────────────────────────────────────────────
        if ("sınav" in t or "ödev" in t) and any(m in t for m in
            ["ocak","şubat","mart","nisan","mayıs","haziran",
             "temmuz","ağustos","eylül","ekim","kasım","aralık"]):
            name = t.split("sınav")[0].split("ödev")[0].strip() if "sınav" in t or "ödev" in t else t
            months = {"ocak":"01","şubat":"02","mart":"03","nisan":"04","mayıs":"05","haziran":"06",
                      "temmuz":"07","ağustos":"08","eylül":"09","ekim":"10","kasım":"11","aralık":"12"}
            day_m = re.search(r'(\d{1,2})', t)
            month_found = next((m for m in months if m in t), None)
            if day_m and month_found:
                year = datetime.date.today().year
                date_str = f"{year}-{months[month_found]}-{day_m.group(1).zfill(2)}"
                exam_name = t.replace(month_found,"").replace(day_m.group(1),"").replace("sınav","").replace("ödev","").strip()
                self.exam_tracker.add(exam_name or "Sınav", date_str)
                days = (datetime.date.fromisoformat(date_str) - datetime.date.today()).days
                r = f"✓ '{exam_name or 'Sınav'}' {day_m.group(1)} {month_found.capitalize()} tarihine eklendi. {days} gün kaldı efendim."
                self.msg("ANKA",r); self.speak(r)
                return True

        if "sınavlarım" in t or "ödevlerim" in t or "yaklaşan sınav" in t:
            upcoming = self.exam_tracker.get_upcoming()
            if not upcoming:
                r = "Yaklaşan sınav veya ödev yok efendim."
            else:
                items = "\n".join(f"• {e['name']}: {e['days_left']} gün kaldı" for e in upcoming[:5])
                r = f"📅 Yaklaşan sınavlarınız:\n{items}"
            self.msg("ANKA",r); self.speak(r)
            return True

        if "gün kaldı" in t or "ne zaman" in t and "sınav" in t:
            upcoming = self.exam_tracker.get_upcoming()
            if upcoming:
                e = upcoming[0]
                r = f"⏳ {e['name']} için {e['days_left']} gün kaldı efendim."
            else:
                r = "Kayıtlı sınav bulunamadı efendim."
            self.msg("ANKA",r); self.speak(r)
            return True

        # ── QR Kod ───────────────────────────────────────────────────────────
        if "qr kod" in t:
            content = t.replace("qr kod","").replace("oluştur","").replace("yap","").strip()
            if not content:
                r = "Ne için QR kod oluşturayım efendim? Örn: 'google.com için qr kod yap'"
                self.msg("ANKA",r); self.speak(r)
                return True
            path = generate_qr(content)
            if path:
                r = f"✓ QR kod oluşturuldu, masaüstüne kaydedildi efendim."
                self.msg("ANKA",r); self.speak(r)
                import os; os.startfile(path)
            else:
                r = "QR kod için 'pip install qrcode pillow' kurun efendim."
                self.msg("ANKA",r); self.speak(r)
            return True

        # ── Kelime Anlamı ─────────────────────────────────────────────────────
        if "anlamı ne" in t or "ne demek" in t:
            word = t.replace("anlamı ne","").replace("ne demek","").replace("'nin","").replace("'nın","").strip()
            if word:
                threading.Thread(target=lambda: self._word_meaning(word), daemon=True).start()
            return True

        if "eş anlamlı" in t or "eş anlam" in t:
            word = t.replace("eş anlamlı","").replace("eş anlam","").strip()
            if word:
                threading.Thread(target=lambda: self._synonyms(word), daemon=True).start()
            return True

        if "dil bilgisi düzelt" in t or "yazımı düzelt" in t:
            text_to_fix = t.replace("dil bilgisi düzelt","").replace("yazımı düzelt","").strip()
            if text_to_fix:
                threading.Thread(target=lambda: self._fix_grammar(text_to_fix), daemon=True).start()
            return True

        # ── Müzik Zamanlayıcı ─────────────────────────────────────────────────
        if "dakika müzik" in t or "müzik zamanlayıcı" in t:
            m = re.search(r'(\d+)', t)
            if m:
                mins = int(m.group(1))
                url = None
                if "lofi" in t: url = "https://youtube.com/results?search_query=lofi+study+music"
                elif "uyku" in t: url = "https://youtube.com/results?search_query=sleep+music+relaxing"
                elif "egzersiz" in t: url = "https://youtube.com/results?search_query=workout+music"
                self.music_timer.start(mins, url)
                r = f"🎵 {mins} dakika müzik başlatıldı efendim."
                self.msg("ANKA",r); self.speak(r)
            return True

        # ── 20 Soru ───────────────────────────────────────────────────────────
        if "20 soru" in t and "başlat" in t:
            subject = t.replace("20 soru","").replace("başlat","").strip() or "hayvan"
            r = self.twenty_q.start(subject)
            self.msg("ANKA",r); self.speak(r)
            return True

        if self.twenty_q.active and "?" in text:
            r = self.twenty_q.answer(text.replace("?","").strip())
            self.msg("ANKA",r); self.speak(r)
            return True

        if self.twenty_q.active and "tahminim" in t:
            guess = t.replace("tahminim","").strip()
            r = self.twenty_q.guess(guess)
            self.msg("ANKA",r); self.speak(r)
            return True

        # ── Matematik Yarışması ───────────────────────────────────────────────
        if "matematik yarışması" in t or "matematik sorusu" in t:
            r = self.math_ch.ask()
            self.msg("ANKA",r); self.speak(r)
            return True

        if self.math_ch.current and t.replace(" ","").isdigit():
            r = self.math_ch.answer(t)
            self.msg("ANKA",r); self.speak(r)
            # Otomatik sonraki soru
            time.sleep(1)
            next_q = self.math_ch.ask()
            self.msg("ANKA",next_q); self.speak(next_q)
            return True

        # ── Adam Asmaca ───────────────────────────────────────────────────────
        if "adam asmaca" in t and "başlat" in t:
            r = self.hangman.start()
            self.msg("ANKA",r); self.speak(r)
            return True

        if self.hangman.active and "harf" in t:
            letter = t.replace("harf","").replace(":","").strip()[-1:]
            if letter:
                r = self.hangman.guess(letter)
                self.msg("ANKA",r); self.speak(r)
            return True

        # ── Toplantı Modu ─────────────────────────────────────────────────────
        if "toplantı başlat" in t or "toplantı modu" in t and "başlat" in t:
            self.meeting.start()
            return True

        if "toplantı notu" in t or ("not al" in t and self.meeting.active):
            note = t.replace("toplantı notu","").replace("not al","").replace(":","").strip()
            if note and self.meeting.add_note(note):
                r = f"✓ Not alındı: {note}"
                self.msg("ANKA",r)
            return True

        if "toplantıyı bitir" in t or "toplantı bitti" in t:
            self.meeting.end(self.ollama)
            return True

        # ── Enerji Tasarrufu ─────────────────────────────────────────────────
        if "enerji tasarrufu" in t or "pil tasarrufu" in t:
            energy_save_mode(self.speak, self.msg)
            return True

        # ── Konu Öğret ───────────────────────────────────────────────────────
        if "öğret" in t and any(x in t for x in ["bana","hakkında","nedir"]):
            topic = t.replace("bana öğret","").replace("öğret","").replace("hakkında","").replace("nedir","").strip()
            if topic:
                threading.Thread(target=lambda: self._teach(topic), daemon=True).start()
            return True

        # ── Mail Şablonu ──────────────────────────────────────────────────────
        if "mail yaz" in t or "e-posta yaz" in t:
            mail_type = t.replace("mail yaz","").replace("e-posta yaz","").strip()
            threading.Thread(target=lambda: self._write_email(mail_type), daemon=True).start()
            return True

        # ── YouTube Arama ─────────────────────────────────────────────────────
        if "youtube'da" in t and "aç" in t:
            query = t.replace("youtube'da","").replace("aç","").strip()
            webbrowser.open(f"https://youtube.com/results?search_query={query}")
            r = f"✓ YouTube'da '{query}' açıldı efendim."
            self.msg("ANKA",r); self.speak(r)
            return True

        # ── Anlık Çeviri ──────────────────────────────────────────────────────
        if "çevir" in t and ("ingilizce" in t or "türkçe" in t or "almanca" in t or "fransızca" in t):
            threading.Thread(target=lambda: self._translate(t), daemon=True).start()
            return True

        # ── Haftalık Program ─────────────────────────────────────────────────
        if "haftalık program" in t or "bu haftaki planım" in t:
            threading.Thread(target=self._weekly_schedule, daemon=True).start()
            return True

        # ── Verimli Çalışma İpuçları ─────────────────────────────────────────
        if "çalışma ipucu" in t or "verimli çalış" in t:
            tips = [
                "🎯 Pomodoro tekniği: 25 dakika çalış, 5 dakika mola ver.",
                "📵 Telefonu başka odaya bırak, dikkat dağılmasın.",
                "🎵 Enstrümantal müzik odaklanmayı artırır.",
                "💡 Zor konuları sabah çalış, en zinde olduğun saatte.",
                "📝 Not alarak çalış, akılda kalıcılığı 3 kat artırır.",
                "🌊 Her saat başı 5 dakika dinlen, verimlilik artar.",
                "🏃 Egzersiz beyin performansını %20 artırır.",
            ]
            r = f"💡 Çalışma İpucu:\n{random.choice(tips)}"
            self.msg("ANKA",r); self.speak(r)
            return True

        return False

    def _word_meaning(self, word):
        reply = get_word_meaning(word, self.ollama)
        self.msg("ANKA", f"📖 '{word}':\n{reply}")
        self.speak(reply[:200])

    def _synonyms(self, word):
        reply = find_synonyms(word, self.ollama)
        self.msg("ANKA", f"🔤 '{word}' eş anlamlıları:\n{reply}")
        self.speak(reply[:200])

    def _fix_grammar(self, text):
        reply = fix_grammar(text, self.ollama)
        self.msg("ANKA", f"✏️ Düzeltilmiş metin:\n{reply}")
        pyperclip.copy(reply)
        self.speak("Düzeltilmiş metin hazırlandı ve panoya kopyalandı efendim.")

    def _teach(self, topic):
        reply = self.ollama.chat(
            f"'{topic}' konusunu bana öğret. Adım adım, anlaşılır Türkçe ile anlat.",
            system_override="Sen bir öğretmensin. Konuyu basit ve anlaşılır şekilde anlat."
        )
        self.msg("ANKA", f"📚 {topic.capitalize()}:\n\n{reply}")
        self.speak(reply[:300])

    def _write_email(self, mail_type):
        prompt = f"'{mail_type}' için profesyonel Türkçe bir e-posta şablonu yaz."
        reply = self.ollama.chat(
            prompt,
            system_override="Sen bir iş yazışmaları uzmanısın. Profesyonel mail yaz."
        )
        self.msg("ANKA", f"📧 Mail Şablonu:\n\n{reply}")
        pyperclip.copy(reply)
        self.speak("Mail şablonu hazırlandı ve panoya kopyalandı efendim.")

    def _translate(self, text):
        langs = {"ingilizce": "English", "almanca": "German",
                 "fransızca": "French", "türkçe": "Turkish"}
        target = "English"
        for tr, en in langs.items():
            if tr in text.lower():
                target = en
                break
        content = re.sub(r'(çevir|ingilizce|türkçe|almanca|fransızca|ye|ya|e|a)', '', text).strip()
        reply = self.ollama.chat(
            f"Şunu {target} diline çevir: '{content}'",
            system_override=f"Sadece çeviriyi yaz, başka bir şey yazma."
        )
        self.msg("ANKA", f"🌍 Çeviri:\n{reply}")
        self.speak(reply[:200])

    def _weekly_schedule(self):
        from anka_memory import get_pending_tasks, load_alarms
        tasks = get_pending_tasks()
        exams = self.exam_tracker.get_upcoming()
        schedule = "📅 Bu Haftanın Planı:\n\n"
        if tasks:
            schedule += "📋 Görevler:\n" + "\n".join(f"• {t['text']}" for t in tasks[:5]) + "\n\n"
        if exams:
            schedule += "🎯 Yaklaşan Sınavlar:\n" + "\n".join(
                f"• {e['name']}: {e['days_left']} gün" for e in exams[:3])
        if not tasks and not exams:
            schedule += "Bu hafta için kayıtlı plan yok efendim."
        self.msg("ANKA", schedule)
        self.speak("İşte bu haftanın planı efendim.")
