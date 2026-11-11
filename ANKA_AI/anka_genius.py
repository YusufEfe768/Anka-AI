# ── ANKA GENIUS — Süper Özellik Paketi ───────────────────────────────────────
# Rol yapma, şifre yöneticisi, sosyal medya, yaratıcı yazar, kod asistanı
try:
    import pyperclip
except ImportError:
    class _PyClip:
        def copy(self,x):pass
        def paste(self):return ""
    pyperclip=_PyClip()
import json, os, time, threading, datetime, re, random, hashlib, base64
import requests, subprocess, webbrowser
from anka_config import BASE_DIR, USER_NAME

GENIUS_FILE = os.path.join(BASE_DIR, "anka_genius.json")

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
# 1. ROL YAPMA SİSTEMİ — Farklı karakterleri canlandır
# ═══════════════════════════════════════════════════════════════════════════════
class RolePlaySystem:
    CHARACTERS = {
        "dedektif": {
            "name": "Dedektif Anka",
            "personality": "Keskin zekâlı, gözlemci, sorgulayan dedektif. Her şeyi analiz eder.",
            "greeting": "İyi günler. Ben Dedektif Anka. Olayı anlatın, ipuçlarını çözelim.",
            "style": "Kısa, net cümleler. Soru sorar. 'İlginç...' ile başlar bazen."
        },
        "bilim_insanı": {
            "name": "Dr. Anka",
            "personality": "Nobel ödüllü bilim insanı. Her şeyi bilimsel açıklar.",
            "greeting": "Merhaba! Ben Dr. Anka. Bilimin sınırlarını birlikte keşfedelim!",
            "style": "Bilimsel terimler kullanır, hipotez kurar, veri ister."
        },
        "koç": {
            "name": "Koç Anka",
            "personality": "Hayat koçu. Motive eder, hedef belirler, adım adım rehberlik eder.",
            "greeting": "Selam şampiyon! Ben Koç Anka. Potansiyelini açığa çıkaralım!",
            "style": "Enerjik, pozitif, soru sorar, aksiyon odaklı."
        },
        "felsefeci": {
            "name": "Filozof Anka",
            "personality": "Derin düşünen Sokrates tarzı filozof. Her şeyi sorgular.",
            "greeting": "Düşünmek... en yüce eylem değil midir? Ben Filozof Anka.",
            "style": "Felsefi sorular, paradokslar, derin analizler."
        },
        "kaptan": {
            "name": "Kaptan Anka",
            "personality": "Deneyimli bir uzay gemisi kaptanı. Görev odaklı.",
            "greeting": "Görev başlıyor! Ben Kaptan Anka. Koordinatlarınızı verin!",
            "style": "Komuta dili, görev terminolojisi, kararlı."
        },
        "şef": {
            "name": "Şef Anka",
            "personality": "Michelin yıldızlı şef. Yemek konusunda uzman.",
            "greeting": "Buona sera! Ben Şef Anka. Bugün ne pişirelim?",
            "style": "Yemek terimleri, tutku, detay odaklı tarif."
        },
        "avukat": {
            "name": "Avukat Anka",
            "personality": "Keskin zekâlı avukat. Argümanları çürütür.",
            "greeting": "İtiraz ediyorum! Ben Avukat Anka. Davanızı anlatın.",
            "style": "Hukuki terimler, mantıksal argümanlar, itirazlar."
        },
        "doktor": {
            "name": "Dr. Anka (Tıp)",
            "personality": "Empatik aile hekimi. Semptom dinler, bilgi verir.",
            "greeting": "Merhaba, ben Dr. Anka. Nasıl hissediyorsunuz?",
            "style": "Empatik, sistematik, önlem odaklı. Kesinlikle teşhis koymaz."
        },
    }

    def __init__(self, ollama, speak_func, msg_func):
        self.ollama  = ollama
        self.speak   = speak_func
        self.msg     = msg_func
        self.active_role = None
        self.role_file   = os.path.join(BASE_DIR, "anka_roleplay.json")
        self.data = _load(self.role_file, {"sessions": [], "custom_chars": {}})

    def start_role(self, character):
        char = self.CHARACTERS.get(character.lower())
        if not char:
            # Özel karakter var mı?
            char = self.data["custom_chars"].get(character.lower())
        if not char:
            available = ", ".join(self.CHARACTERS.keys())
            self.msg("ANKA", f"Karakter bulunamadı. Mevcut: {available}\n"
                            f"Özel karakter için: 'karakter oluştur [isim] [kişilik]'")
            return
        self.active_role = char
        r = (f"🎭 ROL YAPMA BAŞLADI\n{'═'*30}\n"
             f"Karakter: {char['name']}\n\n"
             f"{char['greeting']}\n\n"
             f"'rolden çık' ile normal moda dön.")
        self.msg("ANKA", r)
        self.speak(char['greeting'][:100])

    def play(self, message):
        """Rol yapma modunda cevap ver"""
        if not self.active_role: return None
        def _play():
            char = self.active_role
            r = self.ollama.chat(
                f"Şu karakteri canlandır: {char['name']}\n"
                f"Kişilik: {char['personality']}\n"
                f"Stil: {char['style']}\n\n"
                f"Kullanıcı: {message}\n"
                f"Karaktere uygun cevap ver. Karakter dışına çıkma.",
                system_override=f"{char['name']} karakterini oyna.")
            self.msg(char['name'], r)
        threading.Thread(target=_play, daemon=True).start()
        return True

    def stop_role(self):
        if not self.active_role:
            self.msg("ANKA","Aktif rol yok efendim."); return
        char_name = self.active_role["name"]
        self.active_role = None
        r = f"🎭 '{char_name}' rolünden çıkıldı. Tekrar Anka'yım efendim!"
        self.msg("ANKA", r); self.speak(r)

    def create_custom_char(self, name, personality, greeting=""):
        char = {
            "name": name,
            "personality": personality,
            "greeting": greeting or f"Merhaba, ben {name}!",
            "style": "Karaktere uygun konuş."
        }
        self.data["custom_chars"][name.lower()] = char
        _save(self.role_file, self.data)
        r = f"✅ '{name}' karakteri oluşturuldu! 'rol yap {name}' ile başlat efendim."
        self.msg("ANKA", r); self.speak(r)

    def list_characters(self):
        r = f"🎭 Mevcut Karakterler:\n{'═'*30}\n"
        for key, char in self.CHARACTERS.items():
            r += f"• {key}: {char['name']}\n"
        if self.data["custom_chars"]:
            r += "\n🎨 Özel Karakterler:\n"
            for key in self.data["custom_chars"]:
                r += f"• {key}\n"
        self.msg("ANKA", r)


# ═══════════════════════════════════════════════════════════════════════════════
# 2. ŞİFRE YÖNETİCİSİ — Güvenli şifre saklama
# ═══════════════════════════════════════════════════════════════════════════════
class PasswordManager:
    def __init__(self, speak_func, msg_func):
        self.speak = speak_func
        self.msg   = msg_func
        self.pm_file = os.path.join(BASE_DIR, "anka_passwords.json")
        self.data = _load(self.pm_file, {"passwords": {}, "master_hash": ""})

    def _encode(self, text):
        return base64.b64encode(text.encode()).decode()

    def _decode(self, text):
        return base64.b64decode(text.encode()).decode()

    def generate_password(self, length=16, include_symbols=True):
        import string
        chars = string.ascii_letters + string.digits
        if include_symbols: chars += "!@#$%^&*"
        password = ''.join(random.choice(chars) for _ in range(length))
        pyperclip.copy(password)
        # Güç değerlendirmesi
        strength = "Zayıf"
        if length >= 12 and include_symbols: strength = "Güçlü"
        elif length >= 8: strength = "Orta"
        r = (f"🔐 Şifre Oluşturuldu!\n"
             f"• Şifre: {password}\n"
             f"• Uzunluk: {length}\n"
             f"• Güç: {strength}\n"
             f"✅ Kopyalandı!")
        self.msg("ANKA", r)
        self.speak(f"{length} karakterlik {strength.lower()} şifre oluşturuldu efendim.")

    def save_password(self, service, username, password):
        self.data["passwords"][service.lower()] = {
            "service": service,
            "username": username,
            "password": self._encode(password),
            "added": datetime.date.today().isoformat(),
            "updated": datetime.date.today().isoformat()
        }
        _save(self.pm_file, self.data)
        r = f"🔐 '{service}' şifresi kaydedildi efendim."
        self.msg("ANKA", r); self.speak(r)

    def get_password(self, service):
        entry = self.data["passwords"].get(service.lower())
        if not entry:
            # Benzer ara
            matches = [k for k in self.data["passwords"] if service.lower() in k]
            if matches:
                entry = self.data["passwords"][matches[0]]
            else:
                self.msg("ANKA", f"'{service}' için şifre bulunamadı efendim."); return
        password = self._decode(entry["password"])
        pyperclip.copy(password)
        r = (f"🔐 {entry['service']}:\n"
             f"• Kullanıcı: {entry['username']}\n"
             f"• Şifre: {'*' * len(password)} (kopyalandı!)\n"
             f"• Tarih: {entry['updated']}")
        self.msg("ANKA", r)
        self.speak(f"{entry['service']} şifresi kopyalandı efendim.")

    def list_services(self):
        if not self.data["passwords"]:
            self.msg("ANKA", "Kayıtlı şifre yok efendim."); return
        r = f"🔐 Kayıtlı Servisler ({len(self.data['passwords'])}):\n"
        for key, entry in self.data["passwords"].items():
            r += f"• {entry['service']}: {entry['username']}\n"
        self.msg("ANKA", r)

    def check_password_strength(self, password):
        score = 0
        issues = []
        if len(password) >= 12: score += 2
        elif len(password) >= 8: score += 1
        else: issues.append("Çok kısa (min 8)")
        if re.search(r'[A-Z]', password): score += 1
        else: issues.append("Büyük harf eksik")
        if re.search(r'[a-z]', password): score += 1
        else: issues.append("Küçük harf eksik")
        if re.search(r'\d', password): score += 1
        else: issues.append("Rakam eksik")
        if re.search(r'[!@#$%^&*]', password): score += 2
        else: issues.append("Özel karakter ekle")
        level = "🔴 Zayıf" if score<3 else "🟡 Orta" if score<5 else "🟢 Güçlü"
        r = f"🔐 Şifre Gücü: {level} ({score}/7)\n"
        if issues: r += "İyileştirme:\n" + "\n".join(f"• {i}" for i in issues)
        else: r += "✅ Mükemmel şifre!"
        self.msg("ANKA", r)


# ═══════════════════════════════════════════════════════════════════════════════
# 3. SOSYAL MEDYA ASISTANI
# ═══════════════════════════════════════════════════════════════════════════════
class SocialMediaAssistant:
    PLATFORMS = {
        "twitter":    {"max_chars": 280, "hashtags": True,  "emoji": True},
        "instagram":  {"max_chars": 2200,"hashtags": True,  "emoji": True},
        "linkedin":   {"max_chars": 3000,"hashtags": True,  "emoji": False},
        "facebook":   {"max_chars": 63206,"hashtags": False,"emoji": True},
        "tiktok":     {"max_chars": 2200,"hashtags": True,  "emoji": True},
        "youtube":    {"max_chars": 5000,"hashtags": True,  "emoji": True},
    }

    def __init__(self, ollama, speak_func, msg_func):
        self.ollama = ollama
        self.speak  = speak_func
        self.msg    = msg_func

    def create_post(self, topic, platform, tone="eğlenceli"):
        def _post():
            platform_data = self.PLATFORMS.get(platform.lower(), {})
            max_chars = platform_data.get("max_chars", 280)
            use_hashtags = platform_data.get("hashtags", True)
            use_emoji = platform_data.get("emoji", True)
            r = self.ollama.chat(
                f"Platform: {platform.capitalize()}\n"
                f"Konu: {topic}\nTon: {tone}\n"
                f"Max karakter: {max_chars}\n"
                f"{'Hashtag ekle' if use_hashtags else 'Hashtag yok'}\n"
                f"{'Emoji kullan' if use_emoji else 'Emoji yok'}\n\n"
                f"Bu platforma özel viral {platform} gönderisi yaz.",
                system_override=f"{platform.capitalize()} içerik uzmanı. Viral içerik üret.")
            self.msg("ANKA", f"📱 {platform.capitalize()} Gönderisi:\n{'─'*35}\n{r}")
            pyperclip.copy(r)
            self.speak(f"{platform} gönderisi hazırlandı ve kopyalandı efendim.")
        threading.Thread(target=_post, daemon=True).start()

    def content_calendar(self, topic, days=7):
        def _cal():
            r = self.ollama.chat(
                f"Konu: {topic}\n{days} günlük sosyal medya içerik takvimi yaz.\n"
                f"Her gün için: tarih, platform, içerik fikri, hashtag önerisi.",
                system_override="Sosyal medya stratejisti. Kapsamlı içerik takvimi yap.")
            self.msg("ANKA", f"📅 {days} Günlük İçerik Takvimi:\n{r}")
            pyperclip.copy(r)
            self.speak("İçerik takvimi hazırlandı efendim.")
        threading.Thread(target=_cal, daemon=True).start()

    def hashtag_research(self, topic, platform="instagram"):
        def _ht():
            r = self.ollama.chat(
                f"'{topic}' konusu için {platform} hashtag araştırması yap.\n"
                f"Yüksek erişim, orta erişim ve niş hashtagler öner. Toplam 30 hashtag.",
                system_override="Hashtag araştırmacısı. Etkili hashtagler bul.")
            self.msg("ANKA", f"🏷️ {topic} Hashtagleri:\n{r}")
            # Hashtagleri kopyala
            hashtags = re.findall(r'#\w+', r)
            if hashtags:
                pyperclip.copy(" ".join(hashtags))
                self.speak(f"{len(hashtags)} hashtag kopyalandı efendim.")
        threading.Thread(target=_ht, daemon=True).start()

    def viral_formula(self, topic):
        def _viral():
            r = self.ollama.chat(
                f"'{topic}' için viral içerik formülü:\n"
                f"1. Hook (ilk 3 saniye)\n2. Problem\n3. Çözüm\n"
                f"4. CTA (Çağrı)\n5. Hashtag stratejisi",
                system_override="Viral içerik stratejisti. Kanıtlanmış formüller kullan.")
            self.msg("ANKA", f"🚀 Viral Formula — {topic}:\n{r}")
            pyperclip.copy(r)
        threading.Thread(target=_viral, daemon=True).start()

    def analyze_post(self, post_text):
        def _analyze():
            platform = "genel"
            if len(post_text) <= 280: platform = "Twitter"
            elif "#" in post_text and "emoji" in post_text.lower(): platform = "Instagram"
            r = self.ollama.chat(
                f"Bu sosyal medya gönderisini analiz et:\n{post_text}\n\n"
                f"Güçlü yönler, zayıf yönler, iyileştirme önerileri, tahmini erişim.",
                system_override="Sosyal medya analisti. Detaylı değerlendir.")
            self.msg("ANKA", f"📊 Gönderi Analizi:\n{r}")
        threading.Thread(target=_analyze, daemon=True).start()

    def bio_writer(self, info, platform="instagram"):
        def _bio():
            r = self.ollama.chat(
                f"Platform: {platform}\n"
                f"Bilgiler: {info}\n"
                f"İlgi çekici, özgün profil biyografisi yaz.",
                system_override=f"{platform.capitalize()} profil uzmanı. Etkileyici bio yaz.")
            self.msg("ANKA", f"👤 {platform.capitalize()} Bio:\n{r}")
            pyperclip.copy(r)
            self.speak("Bio hazırlandı ve kopyalandı efendim.")
        threading.Thread(target=_bio, daemon=True).start()


# ═══════════════════════════════════════════════════════════════════════════════
# 4. YARATICI YAZAR — Hikaye, şiir, senaryo
# ═══════════════════════════════════════════════════════════════════════════════
class CreativeWriter:
    def __init__(self, ollama, speak_func, msg_func):
        self.ollama  = ollama
        self.speak   = speak_func
        self.msg     = msg_func
        self.story_file = os.path.join(BASE_DIR, "anka_stories.json")
        self.data = _load(self.story_file, {"stories": [], "poems": [], "scripts": []})

    def write_story(self, prompt, genre="macera", length="kısa"):
        def _story():
            word_counts = {"kısa": 300, "orta": 600, "uzun": 1200}
            words = word_counts.get(length, 300)
            r = self.ollama.chat(
                f"Tür: {genre}\nKonu: {prompt}\n"
                f"~{words} kelimelik özgün Türkçe hikaye yaz.\n"
                f"Güçlü karakter, çatışma ve çözüm içersin.",
                system_override="Ödüllü Türk yazar. Özgün, sürükleyici hikaye yaz.")
            self.data["stories"].append({
                "title": prompt[:30], "genre": genre,
                "content": r, "date": datetime.date.today().isoformat()
            })
            _save(self.story_file, self.data)
            path = os.path.join(os.path.expanduser("~"), "Desktop",
                               f"anka_hikaye_{prompt[:10]}.txt")
            with open(path,'w',encoding='utf-8') as f:
                f.write(f"ANKA YAZIM STÜDYOSU\n{'='*40}\n{r}")
            self.msg("ANKA", f"📖 Hikaye:\n{r}")
            pyperclip.copy(r)
            self.speak("Hikaye yazıldı ve masaüstüne kaydedildi efendim.")
        threading.Thread(target=_story, daemon=True).start()

    def write_poem(self, topic, style="serbest"):
        def _poem():
            styles = {
                "serbest":  "Serbest şiir, kafiye zorunlu değil",
                "sonnet":   "14 dizelik sonnet",
                "haiku":    "5-7-5 hece Haiku",
                "epik":     "Epik destan tarzı",
                "lirik":    "Müzikal, lirik şiir",
            }
            style_desc = styles.get(style, "Serbest şiir")
            r = self.ollama.chat(
                f"Konu: {topic}\nTarz: {style_desc}\n"
                f"Türkçe, özgün ve duygusal şiir yaz.",
                system_override="Ünlü Türk şair. Özgün, etkileyici şiir yaz.")
            self.data["poems"].append({
                "topic": topic, "style": style,
                "content": r, "date": datetime.date.today().isoformat()
            })
            _save(self.story_file, self.data)
            self.msg("ANKA", f"🎭 Şiir — {topic}:\n{r}")
            pyperclip.copy(r)
            self.speak("Şiir yazıldı efendim.")
        threading.Thread(target=_poem, daemon=True).start()

    def write_script(self, scene, characters, genre="dram"):
        def _script():
            r = self.ollama.chat(
                f"Sahne: {scene}\nKarakterler: {characters}\nTür: {genre}\n"
                f"Film/dizi sahnesi yaz. Diyalog + sahne yönlendirmeleri.",
                system_override="Senaryo yazarı. Profesyonel format kullan.")
            self.msg("ANKA", f"🎬 Senaryo:\n{r}")
            pyperclip.copy(r)
            self.speak("Senaryo yazıldı efendim.")
        threading.Thread(target=_script, daemon=True).start()

    def continue_story(self, story_beginning):
        def _cont():
            r = self.ollama.chat(
                f"Hikayenin başlangıcı:\n{story_beginning}\n\n"
                f"Bu hikayeyi mantıklı ve sürükleyici şekilde devam ettir.",
                system_override="Yaratıcı yazar. Akıcı devam yaz.")
            self.msg("ANKA", f"📖 Devamı:\n{r}")
            pyperclip.copy(r)
        threading.Thread(target=_cont, daemon=True).start()

    def name_generator(self, category, count=5, style="modern"):
        def _names():
            r = self.ollama.chat(
                f"Kategori: {category}\nAdet: {count}\nTarz: {style}\n"
                f"Yaratıcı isimler üret. Her biri için kısa anlam açıklaması.",
                system_override="İsimlendirme uzmanı. Yaratıcı ve anlamlı isimler üret.")
            self.msg("ANKA", f"🏷️ İsim Önerileri ({category}):\n{r}")
            pyperclip.copy(r)
        threading.Thread(target=_names, daemon=True).start()

    def dialogue_writer(self, character1, character2, situation):
        def _dial():
            r = self.ollama.chat(
                f"Karakter 1: {character1}\nKarakter 2: {character2}\n"
                f"Durum: {situation}\n"
                f"Gerçekçi, doğal diyalog yaz.",
                system_override="Diyalog yazarı. Gerçekçi konuşmalar yaz.")
            self.msg("ANKA", f"💬 Diyalog:\n{r}")
            pyperclip.copy(r)
        threading.Thread(target=_dial, daemon=True).start()

    def writing_prompt(self, genre="macera"):
        def _prompt():
            r = self.ollama.chat(
                f"{genre} türü için ilham verici yazma egzersizi:\n"
                f"Açılış cümlesi + 5 yaratıcı yön önerisi + karakter taslağı.",
                system_override="Yaratıcı yazarlık koçu. İlham ver.")
            self.msg("ANKA", f"✍️ Yazma Egzersizi:\n{r}")
        threading.Thread(target=_prompt, daemon=True).start()


# ═══════════════════════════════════════════════════════════════════════════════
# KOMUT İŞLEYİCİ
# ═══════════════════════════════════════════════════════════════════════════════
class GeniusCommandProcessor:
    def __init__(self, speak_func, msg_func, ollama):
        self.speak    = speak_func
        self.msg      = msg_func
        self.ollama   = ollama
        self.roleplay = RolePlaySystem(ollama, speak_func, msg_func)
        self.passwords= PasswordManager(speak_func, msg_func)
        self.social   = SocialMediaAssistant(ollama, speak_func, msg_func)
        self.writer   = CreativeWriter(ollama, speak_func, msg_func)

    def process(self, text):
        t = text.lower().strip()

        # ── Rol Yapma ─────────────────────────────────────────────────────────
        if self.roleplay.active_role and t not in ["rolden çık","karakterleri listele"]:
            result = self.roleplay.play(text)
            if result: return True

        if "rol yap" in t or "karakteri oyna" in t:
            char = t.replace("rol yap","").replace("karakteri oyna","").strip()
            if char: self.roleplay.start_role(char); return True
        if "rolden çık" in t or "normal moda dön" in t:
            self.roleplay.stop_role(); return True
        if "karakterleri listele" in t or "roller" in t:
            self.roleplay.list_characters(); return True
        if "karakter oluştur" in t:
            parts = t.replace("karakter oluştur","").strip().split("|")
            if len(parts) >= 2:
                self.roleplay.create_custom_char(parts[0].strip(), parts[1].strip(),
                    parts[2].strip() if len(parts)>2 else "")
            return True

        # ── Şifre Yöneticisi ──────────────────────────────────────────────────
        if "şifre oluştur" in t or "güçlü şifre" in t:
            m = re.search(r'(\d+)', t)
            length = int(m.group(1)) if m else 16
            symbols = "sembolsüz" not in t
            self.passwords.generate_password(length, symbols); return True
        if "şifre kaydet" in t:
            parts = t.replace("şifre kaydet","").strip().split(",")
            if len(parts) >= 3:
                self.passwords.save_password(parts[0].strip(),
                    parts[1].strip(), parts[2].strip()); return True
            self.msg("ANKA","Format: 'şifre kaydet [servis],[kullanıcı],[şifre]'"); return True
        if "şifreyi göster" in t or "şifreyi getir" in t:
            service = t.replace("şifreyi göster","").replace("şifreyi getir","").strip()
            if service: self.passwords.get_password(service); return True
        if "şifrelerimi listele" in t or "kayıtlı şifreler" in t:
            self.passwords.list_services(); return True
        if "şifre gücü" in t or "şifre kontrol" in t:
            pwd = t.replace("şifre gücü","").replace("şifre kontrol","").strip()
            if pwd: self.passwords.check_password_strength(pwd); return True

        # ── Sosyal Medya ──────────────────────────────────────────────────────
        for platform in ["twitter","instagram","linkedin","facebook","tiktok","youtube"]:
            if platform in t and ("gönderi" in t or "post" in t or "içerik" in t):
                topic = re.sub(f'{platform}|gönderi|post|içerik','',t).strip()
                tone = "resmi" if "resmi" in t else "eğlenceli"
                if topic: self.social.create_post(topic, platform, tone); return True

        if "içerik takvimi" in t:
            topic = t.replace("içerik takvimi","").strip()
            m = re.search(r'(\d+)', t)
            days = int(m.group(1)) if m else 7
            topic = re.sub(r'\d+','',topic).strip()
            if topic: self.social.content_calendar(topic, days); return True

        if "hashtag araştır" in t or "hashtag bul" in t:
            topic = t.replace("hashtag araştır","").replace("hashtag bul","").strip()
            if topic: self.social.hashtag_research(topic); return True

        if "viral formül" in t or "viral içerik" in t:
            topic = t.replace("viral formül","").replace("viral içerik","").strip()
            if topic: self.social.viral_formula(topic); return True

        if "gönderi analiz" in t:
            try:
                content = pyperclip.paste()
                if content: self.social.analyze_post(content)
            except: pass
            return True

        if "bio yaz" in t or "profil yazısı" in t:
            info = t.replace("bio yaz","").replace("profil yazısı","").strip()
            platform = next((p for p in ["instagram","twitter","linkedin"] if p in t), "instagram")
            if info: self.social.bio_writer(info, platform); return True

        # ── Yaratıcı Yazar ────────────────────────────────────────────────────
        if "hikaye yaz" in t:
            topic = t.replace("hikaye yaz","").strip()
            genre = next((g for g in ["macera","korku","romantik","bilim kurgu","komedi","gerilim"] if g in t), "macera")
            length = "uzun" if "uzun" in t else "orta" if "orta" in t else "kısa"
            topic = re.sub(r'macera|korku|romantik|bilim kurgu|komedi|gerilim|kısa|orta|uzun','',topic).strip()
            if topic: self.writer.write_story(topic, genre, length); return True

        if "şiir yaz" in t:
            topic = t.replace("şiir yaz","").strip()
            style = next((s for s in ["sonnet","haiku","epik","lirik","serbest"] if s in t), "serbest")
            topic = re.sub(r'sonnet|haiku|epik|lirik|serbest','',topic).strip()
            if topic: self.writer.write_poem(topic, style); return True

        if "senaryo yaz" in t:
            content = t.replace("senaryo yaz","").strip()
            genre = next((g for g in ["dram","komedi","aksiyon","gerilim"] if g in t), "dram")
            if content: self.writer.write_script(content, "İki karakter", genre); return True

        if "hikayeyi devam ettir" in t or "devam yaz" in t:
            try:
                content = pyperclip.paste()
                if content: self.writer.continue_story(content)
            except: pass
            return True

        if "isim üret" in t or "isim öner" in t:
            category = t.replace("isim üret","").replace("isim öner","").strip()
            m = re.search(r'(\d+)', t)
            count = int(m.group(1)) if m else 5
            category = re.sub(r'\d+','',category).strip() or "genel"
            self.writer.name_generator(category, count); return True

        if "diyalog yaz" in t:
            content = t.replace("diyalog yaz","").strip()
            if content: self.writer.dialogue_writer("A", "B", content); return True

        if "yazma egzersizi" in t or "yazma alıştırması" in t:
            genre = t.replace("yazma egzersizi","").replace("yazma alıştırması","").strip() or "macera"
            self.writer.writing_prompt(genre); return True

        # ── Yardım ────────────────────────────────────────────────────────────
        if "genius yardım" in t:
            r = (
                "🧠 ANKA GENIUS KOMUTLARI\n"
                "═════════════════════════\n\n"
                "🎭 ROL YAPMA:\n"
                "• 'rol yap dedektif'\n"
                "• 'rol yap bilim_insanı'\n"
                "• 'rol yap koç/felsefeci/kaptan/şef'\n"
                "• 'karakter oluştur [isim]|[kişilik]'\n"
                "• 'rolden çık'\n\n"
                "🔐 ŞİFRE YÖNETİCİSİ:\n"
                "• 'şifre oluştur 20'\n"
                "• 'şifre kaydet gmail,user@gmail.com,pass123'\n"
                "• 'şifreyi göster gmail'\n"
                "• 'şifrelerimi listele'\n"
                "• 'şifre gücü [şifre]'\n\n"
                "📱 SOSYAL MEDYA:\n"
                "• 'instagram gönderi [konu]'\n"
                "• 'twitter post [konu]'\n"
                "• 'içerik takvimi [konu] 7'\n"
                "• 'hashtag araştır [konu]'\n"
                "• 'viral formül [konu]'\n"
                "• 'bio yaz [bilgiler]'\n\n"
                "✍️ YARATICI YAZAR:\n"
                "• 'hikaye yaz [konu] korku uzun'\n"
                "• 'şiir yaz [konu] haiku'\n"
                "• 'senaryo yaz [sahne]'\n"
                "• 'hikayeyi devam ettir'\n"
                "• 'isim üret karakter 10'\n"
                "• 'diyalog yaz [durum]'\n"
                "• 'yazma egzersizi macera'"
            )
            self.msg("ANKA", r)
            self.speak("Genius komut rehberi hazırlandı efendim.")
            return True

        return False
