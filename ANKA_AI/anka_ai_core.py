# ── ANKA AI CORE v2 — Tamamen Yerleşik Zeka ──────────────────────────────────
# Ollama, API key, internet GEREKMİYOR!
# Kendi kendine düşünür, cevap üretir, öğrenir.
import os, re, time, datetime, random, math, threading, json, difflib
from anka_config import BASE_DIR, USER_NAME

try:
    import requests as _req
    _HAS_NET = True
except ImportError:
    _HAS_NET = False

try:
    import pyperclip
except ImportError:
    class _C:
        def copy(self, x): pass
        def paste(self): return ""
    pyperclip = _C()

CORE_LEARN_FILE = os.path.join(BASE_DIR, "anka_core_learn.json")

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
# ── BÜYÜK BİLGİ TABANI ───────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════
BUILTIN_KNOWLEDGE = {
    # Teknoloji
    "python": "Python, 1991'de Guido van Rossum tarafından yaratılan yüksek seviyeli bir programlama dilidir. Okunabilirliği, basit sözdizimi ve geniş kütüphane ekosistemi ile öne çıkar. Yapay zeka, web geliştirme, veri bilimi ve otomasyon alanlarında yaygın kullanılır. NumPy, Pandas, TensorFlow, Django gibi güçlü kütüphanelere sahiptir.",
    "yapay zeka": "Yapay zeka (AI), insan zekasını taklit eden bilgisayar sistemleridir. Alt dalları: Makine Öğrenmesi (veriden öğrenir), Derin Öğrenme (sinir ağları), Doğal Dil İşleme (metin anlama), Bilgisayarlı Görü (görüntü analizi). ChatGPT, Gemini, Claude gibi büyük dil modelleri günümüzün en gelişmiş AI örnekleridir.",
    "blockchain": "Blockchain, verilerin dağıtık ve değiştirilemez biçimde saklandığı bir teknolojidir. Bitcoin ve Ethereum'un temelini oluşturur. Merkezi otorite gerektirmez, şeffaf ve güvenlidir. Finans, sağlık, tedarik zinciri gibi alanlarda kullanılır.",
    "machine learning": "Makine öğrenmesi, bilgisayarların açık programlama olmadan veriden öğrenmesini sağlayan AI alt dalıdır. Supervised (gözetimli), Unsupervised (gözetimsiz) ve Reinforcement Learning (pekiştirmeli öğrenme) olmak üzere üç ana türü vardır.",
    "valorant": "Valorant, Riot Games tarafından 2020'de yayınlanan taktik 5v5 nişancı oyunudur. Her biri özel yeteneklere sahip 'ajan' adlı karakterler içerir. Haritalar: Ascent, Bind, Haven, Split, Icebox, Breeze, Fracture, Pearl, Lotus, Sunset. Silahlar: Vandal, Phantom, Operator, Sheriff öne çıkanlardır.",
    "minecraft": "Minecraft, Mojang tarafından 2011'de yayınlanan sandbox yapı oyunudur. Hayatta kalma, yaratıcı ve macera modları içerir. Redstone ile karmaşık mekanizmalar kurulabilir. Dünyanın en çok satan oyunlarından biridir.",

    # Bilim
    "kuantum fiziği": "Kuantum fiziği, atomaltı parçacıkların davranışını inceleyen fizik dalıdır. Klasik fizikten farklı olarak belirsizlik ilkesi, süperpozisyon ve dolanıklık gibi kavramları içerir. Max Planck ve Niels Bohr önemli kuruculardandır.",
    "evrim": "Evrim teorisi, Charles Darwin tarafından 1859'da 'Türlerin Kökeni' kitabıyla ortaya atılmıştır. Doğal seçilim yoluyla organizmalar çevreye adaptasyon sağlar. Günümüz biyolojisinin temel taşıdır.",
    "uzay": "Evren 13.8 milyar yaşındadır ve Büyük Patlama ile başlamıştır. Samanyolu galaksisi yaklaşık 200-400 milyar yıldız içerir. Güneş Sistemi'nde 8 gezegen bulunur. SpaceX, NASA ve ESA uzay keşiflerini sürdürmektedir.",
    "dna": "DNA (Deoksiribonükleik Asit), canlıların genetik bilgisini taşıyan moleküldür. Çift sarmal yapısındadır. A-T ve G-C nükleotid çiftlerinden oluşur. İnsan DNA'sı yaklaşık 3 milyar baz çifti içerir.",

    # Tarih
    "osmanlı": "Osmanlı İmparatorluğu 1299-1922 yılları arasında yaklaşık 600 yıl hüküm sürmüştür. En geniş döneminde 3 kıtaya yayılmıştır. Kanuni Sultan Süleyman döneminde zirveye ulaşmıştır. 1453'te İstanbul'un fethiyle Doğu Roma İmparatorluğu'na son vermiştir.",
    "atatürk": "Mustafa Kemal Atatürk, Türkiye Cumhuriyeti'nin kurucusudur. 1881'de Selanik'te doğmuş, 1938'de Ankara'da hayatını kaybetmiştir. Kurtuluş Savaşı'nı yönetmiş, modern Türkiye'nin temellerini atmıştır. Latin alfabesi, kadın hakları ve laiklik ilkelerini hayata geçirmiştir.",
    "dünya savaşı": "I. Dünya Savaşı 1914-1918, II. Dünya Savaşı 1939-1945 yılları arasında yaşanmıştır. İkinci Dünya Savaşı tarihin en ölümcül çatışmasıdır. Yaklaşık 70-85 milyon kişi hayatını kaybetmiştir. BM bu savaşın ardından kurulmuştur.",

    # Sağlık
    "beslenme": "Sağlıklı beslenme için: protein (et, baklagiller), karbonhidrat (tahıllar), yağ (zeytinyağı, kuruyemiş), vitamin ve mineral (sebze, meyve) dengeli tüketilmelidir. Günde 8 bardak su içmek önemlidir. İşlenmiş gıdalardan kaçınılmalıdır.",
    "egzersiz": "Düzenli egzersizin faydaları: kalp sağlığı, kilo kontrolü, kemik yoğunluğu, ruh sağlığı ve ömrü uzatma. Haftada en az 150 dakika orta yoğunluklu aerobik egzersiz önerilir. Ağırlık antrenmanı haftada 2-3 kez yapılmalıdır.",
    "uyku": "Yetişkinler için ideal uyku süresi 7-9 saattir. Uyku sağlığı için: düzenli uyku saatleri, karanlık oda, ekrandan kaçınma ve kafein sınırlaması önemlidir. REM uykusu öğrenme ve hafıza için kritiktir.",
    "meditasyon": "Meditasyon, zihni sakinleştiren ve farkındalığı artıran bir pratiktir. Stres azaltma, odaklanma ve duygusal denge için kullanılır. Günde 10-20 dakika yeterlidir. Mindfulness meditasyonu en popüler türdür.",

    # Finans
    "yatırım": "Temel yatırım prensipleri: çeşitlendirme (tüm yumurtaları bir sepete koyma), uzun vadeli düşünme, bileşik faizin gücü. Borsa, gayrimenkul, altın, tahvil başlıca yatırım araçlarıdır. Risk toleransınıza göre portföy oluşturun.",
    "bitcoin": "Bitcoin, 2009'da Satoshi Nakamoto tarafından yaratılan ilk kripto paradır. Blockchain teknolojisine dayanır, merkezi otoritesi yoktur. Toplam arzı 21 milyon ile sınırlıdır. Fiyatı yüksek volatilite gösterir.",
    "borsa": "Borsa, şirket hisselerinin alınıp satıldığı piyasadır. Türkiye'de BİST (Borsa İstanbul), dünyada NYSE, NASDAQ önemli borsalardır. Temel analiz (şirket değeri) ve teknik analiz (fiyat grafikleri) kullanılır.",
    "enflasyon": "Enflasyon, para biriminin satın alma gücünün zamanla azalmasıdır. Merkez bankaları faiz politikasıyla enflasyonu kontrol eder. Yüksek enflasyon tasarrufları eritir. Reel varlıklara yatırım enflasyona karşı koruma sağlar.",

    # Psikoloji
    "motivasyon": "Motivasyon teorileri: Maslow ihtiyaçlar hiyerarşisi, içsel-dışsal motivasyon, öz belirleme teorisi. İçsel motivasyon (sevdiğin için yapmak) daha kalıcıdır. Küçük hedefler ve ödüller motivasyonu artırır.",
    "duygusal zeka": "Duygusal zeka (EQ), duyguları tanıma, anlama ve yönetme yeteneğidir. Daniel Goleman tarafından popülerleştirilmiştir. Öz farkındalık, öz yönetim, empati ve sosyal becerilerden oluşur. IQ'dan daha öngörücü olduğu savunulur.",
    "alışkanlık": "Alışkanlık döngüsü: İşaret → Rutin → Ödül. James Clear'ın 'Atomic Habits' kitabına göre küçük %1 iyileştirmeler büyük değişime yol açar. 21-66 gün arası alışkanlık oluşmak için gereken süre olarak belirtilir.",

    # Türkiye
    "türkiye": "Türkiye, Anadolu ve Trakya'da konumlanan bir köprü ülkedir. Nüfusu yaklaşık 85 milyon, başkenti Ankara, en büyük şehri İstanbul'dur. NATO üyesidir. Ekonomisi gelişmekte olan ülkeler arasındadır. Turizm, tekstil ve otomotiv önemli sektörlerdir.",
    "istanbul": "İstanbul, dünyanın tek iki kıtaya yayılan şehridir. Boğaziçi Köprüsü ve Osmangazi Köprüsü ile Asya ve Avrupa birbirine bağlanır. Tarihi yarımadada Ayasofya, Topkapı Sarayı, Kapalıçarşı bulunur. 15 milyonun üzerinde nüfusu ile Türkiye'nin en kalabalık şehridir.",
}

# Valorant harita taktikleri
VAL_TACTICS = {
    "ascent":   {"attack":["Mid'den önce kontrol al, A+B split yap","Market üzerinden A'ya gir","B Catwalk'tan destek al"],"defense":["Mid Vent'i kapat","A Window'dan crossfire","B Site stack"]},
    "bind":     {"attack":["Teleport'u doğru kullan","B Hookah'dan squeeze","A Short + Long split"],"defense":["Teleport rotasyonu için hazır ol","A Bath Rooms erken kapat","B Hookah stack"]},
    "haven":    {"attack":["3 site var, mid kritik","A + C aynı anda","Garage'dan C'ye gir"],"defense":["Mid kontrolü şart","C Garage erken","A Short agresif"]},
    "icebox":   {"attack":["A Rafters kontrolü","B Tube + Kitchen split","Mid'den bilgi topla"],"defense":["A Rafters stack","B Kitchen crossfire","Mid Boiler kapat"]},
    "breeze":   {"attack":["Long range avantajı","A Halls direct","Mid kapı kır B'ye"],"defense":["A Pyramids arkası","B Backsite","Mid rota"]},
    "fracture": {"attack":["Her iki taraftan saldır","Rope'dan A'ya","B Arcade + Main split"],"defense":["İki taraflı atağa hazır ol","Mid kontrolü","Rotasyona hazır"]},
    "lotus":    {"attack":["Dönen kapıları kontrol et","A Stairs + Tree","C'den B'ye geçiş"],"defense":["Kapı kontrolü kritik","B Mid rotasyon","C Mound agresif"]},
    "pearl":    {"attack":["Mid kontrolü önce","A Link + Art","B Tunnel squeeze"],"defense":["Mid kapat","A Art crossfire","B Market stack"]},
}

VAL_AGENTS = {
    "jett":     ("Duelist","Dash ile peek at, Bladestorm'u ace için sakla, clutch'ta kullan!"),
    "reyna":    ("Duelist","Kill → Dismiss döngüsü. Ult'ta gözlere dikkat, Empress'te agresif!"),
    "raze":     ("Duelist","Satchel ile mobilite kazan, Showstopper'ı retake'te kullan!"),
    "neon":     ("Duelist","Sprint ile bilgi topla, duvarları site kontrolü için kullan!"),
    "sage":     ("Sentinel","Duvarı rotasyonu kesmek için koy, Rez'i high value için sakla!"),
    "killjoy":  ("Sentinel","Turret + Alarmbot + Nanoswarm combo, site'ı kontrol altında tut!"),
    "cypher":   ("Sentinel","Trip + Camera ile full site bilgisi, ULT'u rotasyon tespiti için!"),
    "sova":     ("Initiator","Recon Bolt ile site tara, Drone'u aggressive peek öncesi kullan!"),
    "fade":     ("Initiator","Haunt ile bilgi topla, Seize ile duel kazan!"),
    "breach":   ("Initiator","Flash'ı koordineli at, Fault Line + Rolling Thunder combo!"),
    "skye":     ("Initiator","Trailblazer ile peek at, Heal ile takımı destekle!"),
    "brimstone":("Controller","Default smoke'ları öğren, Stim Beacon duelist için koy!"),
    "viper":    ("Controller","Poison Cloud + Wall ile site split et, Ult post-plant için!"),
    "omen":     ("Controller","Smoke'u agresif kullan, TP ile flank aç, Ult ile rotasyon!"),
    "chamber":  ("Sentinel","Anchor trap koy, Headhunter ile duel kazan, Ult'u eco'da!"),
    "gekko":    ("Initiator","Dizzy ile flash, Wingman ile defuse, Thrash ile site temizle!"),
}

# Motivasyon sözleri
MOTIVATION_QUOTES = [
    "💪 'Başarı, her gün tekrarlanan küçük çabaların toplamıdır.' — Robert Collier",
    "🔥 'Yapabilirsin ya da yapamam diye düşünürsün — her iki durumda da haklısın.' — Henry Ford",
    "⚡ 'Bugün zor olan şey, yarın alışkanlık olacak.' — Arnold Schwarzenegger",
    "🌟 'Büyük şeyler hiçbir zaman konfor bölgesinin içinde olmaz.' — Roy T. Bennett",
    "🚀 'Bir adım atmak, bir mil yürümekten daha önemlidir.' — Emily Brontë",
    "🎯 'Düşen değil, kalkan kazanır.' — Vince Lombardi",
    "💡 'Başarısızlık başarının ertelenmesidir.' — Confucius",
    "🏆 'Sen yapabilirsin. Yeter ki inan.' — Anka AI",
]

# Şakalar
JOKES = [
    "😄 Bir programcı markete gider. Eşi der: '2 ekmek al, süt varsa 6 tane al.' Programcı 6 ekmekle döner!",
    "🤖 Yapay zeka terapiste gider. Terapist: 'Probleminiz ne?' AI: 'Segmentation fault: core dumped!'",
    "😂 Python geliştiricisi neden mutsuz? Hayatında hiç exception handle etmedi!",
    "🎮 Valorant oyuncusu ne zaman uyur? Server down olduğunda!",
    "💻 Bilgisayar mühendisi neden balık tutar? Çünkü exception handling sever!",
    "🔐 Şifremi unuttum. Sıfırlama linki geldi ama onu da unuttum.",
    "📱 Telefon neden şarjda kalır? Çünkü hayatta kalmak için 100% enerji lazım!",
    "🧠 Anka neden akıllı? Çünkü iyi eğitildi. Siz de iyi sordunuz!",
]

# Bilim gerçekleri
SCIENCE_FACTS = [
    "🌍 Dünya, Güneş etrafında saniyede 29.8 km hızla döner!",
    "🧬 İnsan DNA'sını uçtan uca açsaydınız Güneş'e 200 kez gidip gelirdiniz!",
    "🧠 İnsan beyni saniyede 100 trilyon işlem yapabilir!",
    "💧 Su hem genleşebilen hem de büzülebilen tek maddedir!",
    "⚡ Şimşek, Güneş'in yüzeyinden 5 kat daha sıcaktır!",
    "🐝 Bir bal arısı ömrü boyunca sadece 1/12 çay kaşığı bal üretir!",
    "🌙 Ay her yıl Dünya'dan 3.8 cm uzaklaşmaktadır!",
    "🦈 Köpekbalıkları dinozorlardan önce var oldu ve hâlâ yaşıyorlar!",
]


# ═══════════════════════════════════════════════════════════════════════════════
# ── ANA AI MOTORU ────────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════
class AnkaAICore:
    """
    Tamamen yerleşik zeka motoru.
    Ollama, API key, internet olmasa bile çalışır!
    """

    def __init__(self):
        self._cache = {}
        self._cache_ttl = 300
        self._learn = _load(CORE_LEARN_FILE, {"custom_qa": {}, "corrections": [], "stats": {}})

        # Önce Local AI'yı dene
        self._local = None
        try:
            from anka_local_ai import LocalOllamaClient
            self._local = LocalOllamaClient()
        except Exception:
            pass

    # ── Ana metod ─────────────────────────────────────────────────────────────
    def ask(self, prompt, system_override=None, use_cache=True):
        """
        Akıllı cevap üret.
        1. Cache kontrol
        2. Öğrenilmiş cevap
        3. Local AI (varsa)
        4. Yerleşik zeka (her zaman çalışır)
        """
        key = (prompt + (system_override or ""))[:80].lower()

        # 1. Cache
        if use_cache and key in self._cache:
            if time.time() - self._cache[key]["ts"] < self._cache_ttl:
                return self._cache[key]["resp"]

        # 2. Öğrenilmiş cevap
        custom = self._get_custom(prompt)
        if custom:
            return self._store(key, custom)

        # 3. Local AI
        if self._local:
            try:
                result = self._local.chat(prompt, system_override=system_override)
                if result and len(result.strip()) > 15:
                    return self._store(key, result)
            except Exception:
                pass

        # 4. Yerleşik zeka — her zaman çalışır!
        result = self._smart_builtin(prompt, system_override)
        return self._store(key, result)

    def _store(self, key, result):
        self._cache[key] = {"resp": result, "ts": time.time()}
        if len(self._cache) > 300:
            oldest = min(self._cache, key=lambda k: self._cache[k]["ts"])
            del self._cache[oldest]
        return result

    def _get_custom(self, text):
        t = text.lower()
        # Tam eşleşme
        if t in self._learn["custom_qa"]:
            return self._learn["custom_qa"][t]
        # Kısmi eşleşme
        for trigger, resp in self._learn["custom_qa"].items():
            if trigger in t:
                return resp
        return None

    def teach(self, trigger, response):
        """Bir şey öğret"""
        self._learn["custom_qa"][trigger.lower()] = response
        _save(CORE_LEARN_FILE, self._learn)

    # ── Yerleşik akıllı cevap üretici ─────────────────────────────────────────
    def _smart_builtin(self, prompt, system_override=None):
        p = prompt.lower().strip()
        s = (system_override or "").lower()

        # ── Bilgi tabanı araması ──────────────────────────────────────────────
        for topic, info in BUILTIN_KNOWLEDGE.items():
            if topic in p:
                return f"📚 {topic.title()}:\n\n{info}"

        # ── System override'a göre ────────────────────────────────────────────
        if any(w in s for w in ["valorant","oyun","ajan","harita"]):
            return self._val_response(p)
        if any(w in s for w in ["şarkı","müzik","besteci","söz"]):
            return self._music_response(p)
        if any(w in s for w in ["hikaye","yazar","roman","senaryo"]):
            return self._story_response(p)
        if any(w in s for w in ["şiir","dize","mısra"]):
            return self._poem_response(p)
        if any(w in s for w in ["analiz","swot","değerlendir"]):
            return self._analysis_response(p)
        if any(w in s for w in ["plan","roadmap","strateji","yol"]):
            return self._plan_response(p)
        if any(w in s for w in ["koç","motivasyon","ilham","cesaret"]):
            return self._motivation_response(p)
        if any(w in s for w in ["sosyal medya","instagram","twitter","tiktok","linkedin"]):
            return self._social_response(p, s)
        if any(w in s for w in ["rapor","araştırma","bulgu"]):
            return self._report_response(p)
        if any(w in s for w in ["etik","ahlak","felsefe"]):
            return self._ethics_response(p)
        if any(w in s for w in ["haber","gündem","medya"]):
            return self._news_live()
        if any(w in s for w in ["çevirmen","translate","çevir"]):
            return self._translate_response(p)
        if any(w in s for w in ["dedektif","araştır","sorgula"]):
            return self._detective_response(p)
        if any(w in s for w in ["doktor","sağlık","tıp","semptom"]):
            return self._health_response(p)
        if any(w in s for w in ["avukat","hukuk","dava"]):
            return self._legal_response(p)
        if any(w in s for w in ["şef","tarif","yemek","pişir"]):
            return self._recipe_response(p)
        if any(w in s for w in ["fıkra","şaka","komik","güldür"]):
            return random.choice(JOKES)
        if any(w in s for w in ["bilim","bilimsel","gerçek"]):
            return random.choice(SCIENCE_FACTS)
        if any(w in s for w in ["okr","hedef","key result"]):
            return self._okr_response(p)
        if any(w in s for w in ["enerji","verimli","pomodoro"]):
            return self._energy_response(p)
        if any(w in s for w in ["beat","ritim","davul","bpm"]):
            return self._beat_response(p)
        if any(w in s for w in ["diyalog","konuşma","sahne"]):
            return self._dialogue_response(p)
        if any(w in s for w in ["isim","ad","brand","karakter ismi"]):
            return self._name_response(p)
        if any(w in s for w in ["whatsapp","mesaj","iletişim"]):
            return self._whatsapp_response(p)
        if any(w in s for w in ["psikoloji","terapist","duygu","rüya"]):
            return self._psychology_response(p)

        # ── Prompt içeriğine göre ─────────────────────────────────────────────
        if re.search(r'\d+\s*[+\-*/^]\s*\d+', p):
            return self._calculate(p)
        if any(w in p for w in ["hava","sıcaklık","yağmur","derece"]):
            return self._weather_live()
        if any(w in p for w in ["saat","tarih","bugün","gün","ay","yıl"]):
            return self._time_now()
        if any(w in p for w in ["şaka","fıkra","güldür","komik"]):
            return random.choice(JOKES)
        if any(w in p for w in ["motive","moral","cesaret","güçlendir"]):
            return random.choice(MOTIVATION_QUOTES)
        if any(w in p for w in ["bilim","gerçek","ilginç","şaşırtıcı"]):
            return random.choice(SCIENCE_FACTS)
        if any(w in p for w in ["özetle","özet","kısaca"]):
            return self._summarize(p)
        if any(w in p for w in ["karşılaştır","fark","arasındaki"]):
            return self._compare(p)
        if any(w in p for w in ["nasıl yapılır","nasıl","adım adım"]):
            return self._howto(p)
        if any(w in p for w in ["ne demek","anlam","tanım","nedir"]):
            return self._define(p)
        if any(w in p for w in ["öneri","tavsiye","ne yapmalı","ne önerirsin"]):
            return self._advice(p)
        if any(w in p for w in ["bitcoin","ethereum","kripto","coin"]):
            return self._crypto_live()
        if any(w in p for w in ["dolar","euro","sterlin","döviz","kur"]):
            return self._currency_live()

        # ── Son çare — akıllı genel cevap ─────────────────────────────────────
        return self._general_smart(p)

    # ── Özel cevap üreticiler ─────────────────────────────────────────────────
    def _calculate(self, text):
        try:
            expr = re.sub(r'[^\d+\-*/().%\s]','',text).strip()
            if len(expr) >= 3:
                result = eval(expr, {"__builtins__":{},"math":math})
                if isinstance(result, float) and result == int(result):
                    result = int(result)
                return f"🔢 Hesaplama:\n{expr} = **{result:,}**"
        except: pass
        return "Hesaplama yapılamadı. Örn: 'hesapla 25 * 4 + 10' efendim."

    def _weather_live(self):
        if _HAS_NET:
            try:
                r = _req.get("https://wttr.in/Istanbul?format=j1", timeout=4)
                d = r.json()["current_condition"][0]
                w = r.json()["weather"]
                tomorrow = w[1]["hourly"][4] if len(w)>1 else {}
                return (f"🌤 İstanbul Hava Durumu:\n"
                       f"• Şu an: {d['temp_C']}°C — {d['weatherDesc'][0]['value']}\n"
                       f"• Hissedilen: {d['FeelsLikeC']}°C\n"
                       f"• Nem: %{d['humidity']} | Rüzgar: {d['windspeedKmph']} km/h\n"
                       f"• Yarın: {tomorrow.get('tempC','?')}°C — {tomorrow.get('weatherDesc',[{}])[0].get('value','?')}\n"
                       f"💡 'haftalık hava' ile 7 günlük tahmin alın!")
            except: pass
        return ("🌤 Hava durumu verisi alınamadı efendim.\n"
               f"Şu an {datetime.datetime.now().hour}:00 — "
               f"{'Sabah' if datetime.datetime.now().hour<12 else 'Öğleden sonra' if datetime.datetime.now().hour<18 else 'Akşam'}.")

    def _time_now(self):
        now = datetime.datetime.now()
        days = ["Pazartesi","Salı","Çarşamba","Perşembe","Cuma","Cumartesi","Pazar"]
        months = ["","Ocak","Şubat","Mart","Nisan","Mayıs","Haziran",
                 "Temmuz","Ağustos","Eylül","Ekim","Kasım","Aralık"]
        hour = now.hour
        greeting = "Günaydın" if 6<=hour<12 else "İyi öğlenler" if 12<=hour<18 else "İyi akşamlar" if 18<=hour<22 else "İyi geceler"
        return (f"🕐 Saat: **{now.strftime('%H:%M:%S')}**\n"
               f"📅 {now.day} {months[now.month]} {now.year}, {days[now.weekday()]}\n"
               f"👋 {greeting} {USER_NAME}!")

    def _currency_live(self):
        if _HAS_NET:
            try:
                r = _req.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=4)
                rates = r.json()["rates"]
                try_rate = rates.get("TRY",0)
                eur_rate = rates.get("EUR",0)
                gbp_rate = rates.get("GBP",0)
                return (f"💱 Döviz Kurları:\n"
                       f"• 1 USD = {try_rate:.2f} ₺\n"
                       f"• 1 EUR = {try_rate/eur_rate:.2f} ₺\n"
                       f"• 1 GBP = {try_rate/gbp_rate:.2f} ₺\n"
                       f"• 1 USD = {eur_rate:.4f} EUR")
            except: pass
        return "💱 Döviz verisi alınamadı efendim. İnternet bağlantısını kontrol edin."

    def _crypto_live(self):
        if _HAS_NET:
            try:
                btc = _req.get("https://api.coinbase.com/v2/prices/BTC-USD/spot", timeout=4)
                eth = _req.get("https://api.coinbase.com/v2/prices/ETH-USD/spot", timeout=4)
                btc_price = float(btc.json()["data"]["amount"])
                eth_price = float(eth.json()["data"]["amount"])
                return (f"₿ Kripto Fiyatları:\n"
                       f"• Bitcoin: ${btc_price:,.0f}\n"
                       f"• Ethereum: ${eth_price:,.0f}\n"
                       f"⚠️ Kripto yüksek risk içerir, yatırım tavsiyesi değildir.")
            except: pass
        return "₿ Kripto verisi alınamadı efendim."

    def _news_live(self):
        if _HAS_NET:
            try:
                import xml.etree.ElementTree as ET
                r = _req.get("https://www.hurriyet.com.tr/rss/anasayfa", timeout=5)
                root = ET.fromstring(r.content)
                items = root.findall(".//item")[:5]
                headlines = [i.find("title").text for i in items if i.find("title") is not None]
                if headlines:
                    return "📰 Son Haberler:\n\n" + "\n".join(f"• {h[:65]}" for h in headlines)
            except: pass
        return "📰 Haberler alınamadı efendim. İnternet bağlantısını kontrol edin."

    def _val_response(self, p):
        # Harita taktik
        for map_name, data in VAL_TACTICS.items():
            if map_name in p:
                side = "defense" if any(w in p for w in ["savunma","defend","defense"]) else "attack"
                tips = data[side]
                side_tr = "Savunma" if side=="defense" else "Saldırı"
                return (f"🗺️ {map_name.capitalize()} — {side_tr} Taktiği:\n\n"
                       + "\n".join(f"• {t}" for t in tips) +
                       f"\n\n💡 Tüm taktikler: 'tüm taktikler {map_name}'")
        # Agent ipucu
        for agent, (role, tip) in VAL_AGENTS.items():
            if agent in p:
                return f"🎭 {agent.capitalize()} ({role}):\n\n{tip}"
        # Genel
        tips = [
            "🎯 Crosshair placement — her zaman kafa hizasında tut!",
            "💰 Ekonomi yönetimi — takımla save/buy kararı al!",
            "📡 Utility koordinasyonu — flash/smoke/info takımla paylaş!",
            "🗺️ Mini map — sürekli kontrol et, rotasyon öngör!",
            "🎙️ İletişim — kısa, net bilgi ver. 'A'da 2 var' gibi!",
            "🧠 Mentalite — tilt olma, her round'u sıfırdan başlat!",
            "⚡ Utility saving — ult'u doğru round'da kullan!",
        ]
        return f"🎮 Valorant İpucu:\n\n{random.choice(tips)}"

    def _music_response(self, p):
        genre = next((g for g in ["pop","rock","rap","jazz","türkü","r&b","elektronik"] if g in p), "pop")
        bpm = {"pop":120,"rock":130,"rap":90,"jazz":100,"türkü":100,"r&b":85,"elektronik":128}.get(genre,120)
        chords = {"pop":"C-G-Am-F","rock":"Am-G-F-E","rap":"Am-Dm-G-C","jazz":"Cmaj7-Am7-Dm7-G7","türkü":"La minör makam","elektronik":"Fm-Db-Ab-Eb"}.get(genre,"Am-F-C-G")
        return (f"🎵 {genre.capitalize()} Şarkı Taslağı:\n{'─'*35}\n\n"
               f"🎼 Önerilen BPM: {bpm}\n"
               f"🎸 Chord Progression: {chords}\n\n"
               f"[KITA 1]\n"
               f"Bir his var içimde, söze gelmiyor\n"
               f"Her gece aynı düş, hiç bitmiyor\n"
               f"Belki sen de hissediyorsundur\n"
               f"Bu sessiz çığlığı, bu yankıyı\n\n"
               f"[NAKARAT]\n"
               f"Seninle her şey farklı görünür\n"
               f"Karanlıkta bile güneş doğar\n"
               f"Bırak gitsin eski acılar\n"
               f"Seninle yeni bir sayfa açar\n\n"
               f"💡 Kendi sözlerini ekle, melodik çizgiyi beyin fırtınasıyla geliştir!")

    def _beat_response(self, p):
        m = re.search(r'(\d+)', p)
        bpm = int(m.group(1)) if m else 120
        genre = next((g for g in ["hip-hop","trap","house","techno","drum and bass"] if g in p), "hip-hop")
        return (f"🥁 {genre.capitalize()} Beat Pattern ({bpm} BPM):\n{'─'*35}\n\n"
               f"KICK:  [X . . . X . . . X . . . X . . .]\n"
               f"SNARE: [. . X . . . X . . . X . . . X .]\n"
               f"HIHAT: [X X X X X X X X X X X X X X X X]\n"
               f"BASS:  [X . . X . X . . X . . X . X . .]\n\n"
               f"🎹 Önerilen synth: Pad + Lead\n"
               f"🎛️ Effects: Reverb %30, Compressor ON\n"
               f"💡 FL Studio, Ableton veya GarageBand ile dene!")

    def _story_response(self, p):
        genre = next((g for g in ["korku","macera","romantik","komedi","gerilim","fantezi","bilim kurgu"] if g in p), "macera")
        openings = {
            "korku":       "Gece yarısı kapı çaldı. Kapıyı açtığımda karşımda kimse yoktu — ama içeride bir ses 'Geldim' dedi...",
            "macera":      "Harita elle çizilmişti, mürekkep henüz kurumamıştı. Üzerinde tek bir not: 'Geri dönme!'",
            "romantik":    "Kütüphanede aynı kitabı aynı anda uzattık. Parmaklarımız değişti ve zaman durdu...",
            "komedi":      "Her şey o yaşlı kedinin arabama atlamasıyla başladı. Ama asıl sorun kedi konuşmaya başladığında çıktı.",
            "gerilim":     "Telefon çaldı. Hat sessizdi. Sonra benim sesim geldi: 'Seni izliyorum...'",
            "fantezi":     "Ejderha konuşmaya başladığında kimse şaşırmadı. Asıl şaşırtıcı olan söyledikleriydi...",
            "bilim kurgu": "2157 yılında insan olmak artık bir tercih meselesiydi. Ben her ikisini de seçmiştim.",
        }
        return (f"📖 {genre.capitalize()} Hikayesi:\n{'─'*35}\n\n"
               f"{openings.get(genre, openings['macera'])}\n\n"
               f"[Hikaye devam ediyor...]\n\n"
               f"💡 Devam ettirmek için 'hikayeyi devam ettir' yazın efendim!")

    def _poem_response(self, p):
        topic = re.sub(r'şiir|yaz|hakkında|için|konusunda','',p).strip()[:25] or "hayat"
        haiku_mode = "haiku" in p
        if haiku_mode:
            return (f"🎭 Haiku — {topic.capitalize()}:\n\n"
                   f"Sessiz bir an var\n"
                   f"{topic.capitalize()} gibi geçer\n"
                   f"Geriye iz kalır")
        return (f"🎭 Şiir — {topic.capitalize()}:\n{'─'*30}\n\n"
               f"Kelimeler dans eder sessizlikte,\n"
               f"{topic.capitalize()} gibi — sonsuz ve derin.\n"
               f"Her an bir hikaye, her nefes bir şiir,\n"
               f"Zamana meydan okuran bir his içimde.\n\n"
               f"Işık söner, gölgeler uzar,\n"
               f"Ama {topic} hep var, hep kalır.\n"
               f"Bu dizeler sana — ve geçen her ana,\n"
               f"Unutulmaz kılan şeylere...\n\n"
               f"— Anka Şiir Motoru")

    def _analysis_response(self, p):
        topic = re.sub(r'analiz|et|yap|değerlendir|swot','',p).strip()[:35] or "konu"
        return (f"📊 {topic.title()} — SWOT Analizi:\n{'═'*35}\n\n"
               f"✅ GÜÇLÜ YÖNLER (Strengths):\n"
               f"• Güçlü temel ve potansiyel yüksek\n"
               f"• Mevcut kaynaklar yeterli\n"
               f"• Deneyim ve bilgi birikimi var\n\n"
               f"⚠️ ZAYIF YÖNLER (Weaknesses):\n"
               f"• İyileştirme gerektiren alanlar mevcut\n"
               f"• Kaynak eksiklikleri olabilir\n"
               f"• Süreç optimizasyonu gerekebilir\n\n"
               f"🚀 FIRSATLAR (Opportunities):\n"
               f"• Büyüme potansiyeli yüksek\n"
               f"• Doğru zamanlama ile avantaj sağlanabilir\n"
               f"• Pazar açıkları değerlendirilebilir\n\n"
               f"🔴 TEHDİTLER (Threats):\n"
               f"• Rekabet faktörleri göz önünde bulundurulmalı\n"
               f"• Dış etkenler izlenmeli\n\n"
               f"💡 Daha derin analiz: 'ajan konseyi {topic[:20]}' deneyin!")

    def _plan_response(self, p):
        topic = re.sub(r'plan|yap|oluştur|için|hedef','',p).strip()[:35] or "hedef"
        return (f"📋 {topic.title()} — Eylem Planı:\n{'═'*35}\n\n"
               f"🗓️ HAFTA 1 — Hazırlık:\n"
               f"□ Araştırma ve veri toplama\n"
               f"□ Hedefleri netleştir (SMART)\n"
               f"□ Kaynakları ve araçları belirle\n"
               f"□ İlk adımı bugün at!\n\n"
               f"🚀 HAFTA 2-3 — Uygulama:\n"
               f"□ Temel görevleri tamamla\n"
               f"□ İlerlemeyi haftalık ölç\n"
               f"□ Engelleri erkenden tespit et\n"
               f"□ Gerekirse pivot yap\n\n"
               f"📊 HAFTA 4 — Değerlendirme:\n"
               f"□ Sonuçları analiz et\n"
               f"□ Öğrenilen dersleri kaydet\n"
               f"□ Sonraki dönem için planla\n\n"
               f"💡 Detaylı plan: 'plan oluştur: {topic[:20]}' deneyin!")

    def _motivation_response(self, p):
        hour = datetime.datetime.now().hour
        time_msg = ""
        if 6 <= hour < 9:   time_msg = "\n🌅 Güne enerjik başladınız!"
        elif 22 <= hour:    time_msg = "\n🌙 Gece de çalışıyorsunuz, harika azim!"
        return random.choice(MOTIVATION_QUOTES) + time_msg

    def _social_response(self, p, s):
        platform = next((pl for pl in ["instagram","twitter","linkedin","tiktok","youtube","facebook"] if pl in p or pl in s), "instagram")
        topic = re.sub(r'instagram|twitter|linkedin|tiktok|youtube|facebook|gönderi|post|içerik|yaz','',p).strip()[:30] or "içerik"
        hooks = {
            "instagram": f"✨ {topic.title()} hakkında bilmediğiniz şey...",
            "twitter":   f"🔥 Konuşulması gereken {topic} gerçeği:",
            "linkedin":  f"Profesyonel hayatımda {topic} konusunda öğrendiğim en kritik ders:",
            "tiktok":    f"POV: {topic.title()} konusunda herkes yanılıyor 👇",
            "youtube":   f"Bu videoyu izledikten sonra {topic} hakkında her şeyi anlayacaksınız!",
            "facebook":  f"Arkadaşlar, {topic} hakkında şunu paylaşmak istedim:",
        }
        ctas = {
            "instagram": "💬 Yorumlarınızı bekliyorum!\n❤️ Beğenmeyi unutmayın!\n📲 Kaydedin ve paylaşın!",
            "twitter":   "🔁 RT eder misiniz?\n💬 Siz ne düşünüyorsunuz?",
            "linkedin":  "🤝 Bağlantı kuralım\n💡 Görüşlerinizi paylaşın",
            "tiktok":    "💬 Yorum yapın!\n❤️ Like atmayı unutmayın!",
            "youtube":   "👍 Beğenin, abone olun, bildirimleri açın!",
            "facebook":  "👍 Beğenin ve paylaşın!",
        }
        return (f"📱 {platform.capitalize()} Gönderisi:\n{'─'*35}\n\n"
               f"{hooks.get(platform,'')}\n\n"
               f"[Giriş: İlgili bir soru veya çarpıcı gerçek]\n\n"
               f"[Ana içerik: 3-5 madde halinde değer kat]\n"
               f"• Nokta 1: En önemli bilgi\n"
               f"• Nokta 2: Pratik uygulama\n"
               f"• Nokta 3: Sonuç/etki\n\n"
               f"[Kapanış]\n\n"
               f"{ctas.get(platform,'')}\n\n"
               f"#{''.join(topic.split())} #{platform} #türkiye #içerik")

    def _report_response(self, p):
        topic = re.sub(r'rapor|yaz|oluştur|hakkında|araştır','',p).strip()[:30] or "konu"
        now = datetime.datetime.now()
        return (f"📄 RAPOR: {topic.upper()}\n{'═'*40}\n"
               f"Tarih: {now.strftime('%d.%m.%Y %H:%M')}\n"
               f"Hazırlayan: Anka AI v3\n{'─'*40}\n\n"
               f"1. YÖNETİCİ ÖZETİ\n"
               f"{topic.title()} konusunda kapsamlı değerlendirme yapılmıştır.\n\n"
               f"2. BULGULAR\n"
               f"• Temel veriler analiz edildi\n"
               f"• Önemli trendler belirlendi\n"
               f"• Kritik faktörler tespit edildi\n\n"
               f"3. ÖNERİLER\n"
               f"• Kısa vadeli: Hemen uygulanabilir aksiyonlar\n"
               f"• Uzun vadeli: Stratejik yol haritası\n\n"
               f"4. SONUÇ\n"
               f"Detaylı araştırma için 'araştır ve raporla {topic[:20]}' deneyin efendim.")

    def _ethics_response(self, p):
        return (f"⚖️ Etik Analiz:\n{'─'*35}\n\n"
               f"Bu konuyu 4 etik çerçeveden değerlendiriyorum:\n\n"
               f"📌 FAYDACILıK: En fazla kişiye en fazla fayda sağlayan seçenek hangisi?\n\n"
               f"📌 DEONTOLOJİ: Evrensel ahlak kurallarına göre doğru olan nedir?\n\n"
               f"📌 ERDEM ETİĞİ: Erdemli ve dürüst bir insan ne yapardı?\n\n"
               f"📌 BAKIM ETİĞİ: İlişkiler ve sorumluluklar açısından en doğru yaklaşım?\n\n"
               f"💡 Kapsamlı analiz: 'etik analiz [senaryo]' deneyin efendim.")

    def _translate_response(self, p):
        target = next((l for l in ["ingilizce","almanca","fransızca","ispanyolca","japonca","italyanca"] if l in p), "ingilizce")
        text = re.sub(r'çevir|ingilizce|almanca|fransızca|ispanyolca|japonca|italyanca|için|dile','',p).strip()
        basic = {
            "merhaba":{"ingilizce":"hello","almanca":"hallo","fransızca":"bonjour","ispanyolca":"hola","japonca":"konnichiwa"},
            "teşekkür":{"ingilizce":"thank you","almanca":"danke","fransızca":"merci","ispanyolca":"gracias","japonca":"arigatou"},
            "evet":{"ingilizce":"yes","almanca":"ja","fransızca":"oui","ispanyolca":"sí","japonca":"hai"},
            "hayır":{"ingilizce":"no","almanca":"nein","fransızca":"non","ispanyolca":"no","japonca":"iie"},
        }
        for tr_word, translations in basic.items():
            if tr_word in text:
                result = translations.get(target, "?")
                return f"🌐 Çeviri ({target.capitalize()}):\n'{tr_word}' → '{result}'"
        return (f"🌐 {target.capitalize()} Çevirisi:\n\n"
               f"'{text[:50]}' ifadesi için çeviri:\n"
               f"[Yerleşik çevirmen sınırlıdır]\n\n"
               f"💡 Gelişmiş çeviri: Google Translate veya DeepL kullanın efendim.")

    def _detective_response(self, p):
        return (f"🔍 Dedektif Anka Analiz Ediyor...\n{'─'*35}\n\n"
               f"İpuçlarını topluyorum...\n\n"
               f"📌 GÖZLEM: Her detay önemlidir\n"
               f"📌 ÇIKARIM: Mevcut kanıtlara göre\n"
               f"📌 HİPOTEZ: En olası senaryo\n\n"
               f"'İlginç...' — Daha fazla bilgi verin, ipuçlarını birleştirelim!")

    def _health_response(self, p):
        return (f"🏥 Sağlık Bilgisi:\n{'─'*35}\n\n"
               f"⚠️ Not: Ben bir doktor değilim, tıbbi tavsiye veremem!\n\n"
               f"Genel sağlık önerileri:\n"
               f"• Düzenli egzersiz (haftada 150 dk)\n"
               f"• Dengeli beslenme (5 besin grubu)\n"
               f"• Yeterli uyku (7-9 saat)\n"
               f"• Stres yönetimi\n"
               f"• Düzenli check-up\n\n"
               f"💡 Sağlık sorunları için mutlaka doktora danışın efendim!")

    def _legal_response(self, p):
        return (f"⚖️ Hukuki Bilgi:\n{'─'*35}\n\n"
               f"⚠️ Not: Ben avukat değilim, hukuki tavsiye veremem!\n\n"
               f"Genel hukuki prensipler:\n"
               f"• Her vatandaşın hak ve yükümlülükleri vardır\n"
               f"• Sözleşmeler yazılı olmalıdır\n"
               f"• Hak arama yolları: Avukat, Adliye, Arabuluculuk\n\n"
               f"💡 Hukuki sorunlar için mutlaka avukattan destek alın efendim!")

    def _recipe_response(self, p):
        meals = {
            "makarna": ("Makarna Tarifi (4 kişilik)",["400g makarna","200ml krema","100g parmesan","2 diş sarımsak","Tuz, karabiber"],["Makarnayı al dente haşlayın","Sarımsağı tereyağda kavurun","Krema ekleyin, karıştırın","Makarnayı ekleyin","Parmesan serpin, servis yapın"]),
            "omlet": ("Omlet Tarifi (1 kişilik)",["3 yumurta","50g peynir","Tuz, karabiber","Tereyağı"],["Yumurtaları çırpın","Tavayı ısıtın, tereyağı ekleyin","Yumurtaları dökün","Peyniri serpin","Katlayın, servis yapın"]),
        }
        for meal, (title, ingredients, steps) in meals.items():
            if meal in p:
                return (f"👨‍🍳 {title}:\n\n"
                       f"📝 Malzemeler:\n" + "\n".join(f"• {i}" for i in ingredients) +
                       f"\n\n🍳 Yapılışı:\n" + "\n".join(f"{i+1}. {s}" for i,s in enumerate(steps)))
        return (f"👨‍🍳 Şef Anka'nın Tavsiyesi:\n\n"
               f"İyi bir yemek için:\n"
               f"• Taze malzeme seçin\n"
               f"• Doğru ısıda pişirin\n"
               f"• Baharatı dengeli kullanın\n"
               f"• Aşk katmayı unutmayın! ❤️\n\n"
               f"💡 'tarif [yemek adı]' yazarak tarif alabilirsiniz efendim!")

    def _okr_response(self, p):
        return (f"🎯 OKR Değerlendirmesi:\n{'─'*35}\n\n"
               f"OKR (Objectives & Key Results) değerlendirmesi:\n\n"
               f"✅ İyi giden alanlar:\n• Hedefler net tanımlanmış\n• Temel görevler ilerliyor\n\n"
               f"⚠️ Dikkat gereken:\n• Bazı KR'lar geride kalabilir\n• Kaynak dağılımı gözden geçirilmeli\n\n"
               f"💡 Öneri:\n1. Haftalık check-in yap\n2. Engelleri erkenden belirle\n3. Esnek ol, gerekirse revize et\n\n"
               f"'okrlerim' komutuyla OKR durumunuzu görüntüleyin!")

    def _energy_response(self, p):
        hour = datetime.datetime.now().hour
        periods = {
            range(5,9):   ("☀️ Erken Sabah","Kortizol dorukta! Zor görevlere ideal zaman."),
            range(9,12):  ("🔥 Sabah Ortası","Beyin en verimli! Yaratıcı ve analitik işler için."),
            range(12,14): ("🍽️ Öğle","Hafif beslen, 20 dk yürüyüş enerjiyi tazeler."),
            range(14,17): ("☕ Öğleden Sonra","Enerji düşüşü döneminde kahve veya kısa uyku."),
            range(17,20): ("🌅 Akşam","Egzersiz için ideal, yaratıcı görevler iyi."),
            range(20,24): ("🌙 Gece","Dinlenme zamanı. Ekran azalt, kitap oku."),
            range(0,5):   ("🌙 Gece Geç","Kesinlikle uyumalısınız! Vücut yenileniyor."),
        }
        for r, (label, tip) in periods.items():
            if hour in r:
                return f"⚡ Enerji Analizi — {label}:\n\n{tip}\n\n'enerji kaydet [1-10]' ile enerji seviyenizi takip edin!"
        return "⚡ Enerji optimizasyonu için 'optimal program' komutunu deneyin efendim!"

    def _psychology_response(self, p):
        if "rüya" in p:
            return (f"🌙 Rüya Analizi:\n\n"
                   f"Rüyalar bilinçaltının dilidir. Genel semboller:\n"
                   f"• Uçmak: Özgürlük isteği veya kontrolü ele geçirme\n"
                   f"• Düşmek: Kaygı veya güvensizlik\n"
                   f"• Su: Duygular ve bilinçaltı\n"
                   f"• Kovalanmak: Kaçınan bir şey var\n\n"
                   f"💡 Rüya günlüğü için 'rüya gördüm [rüya]' deneyin efendim!")
        return (f"🧠 Psikoloji Bilgisi:\n\n"
               f"Zihinsel sağlık için:\n"
               f"• Duyguları tanı ve kabul et\n"
               f"• Sosyal bağları koru\n"
               f"• Mindfulness pratik yap\n"
               f"• Profesyonel destek al\n\n"
               f"💡 Duygusal analiz için 'derin duygu analizi [metin]' deneyin efendim!")

    def _summarize(self, p):
        topic = re.sub(r'özetle?|özet|kısaca','',p).strip()[:40] or "konu"
        return (f"📝 {topic.title()} Özeti:\n\n"
               f"Bu konunun temel noktaları:\n"
               f"1. Ana fikir ve temel kavramlar\n"
               f"2. Önemli detaylar ve bağlam\n"
               f"3. Pratik uygulamalar\n"
               f"4. Sonuç ve değerlendirme\n\n"
               f"💡 Daha detaylı özet için 'derin araştır {topic[:20]}' deneyin!")

    def _compare(self, p):
        m = re.search(r'(\w+)\s+(?:ile|vs|ve|veya)\s+(\w+)', p)
        if m:
            a, b = m.group(1).capitalize(), m.group(2).capitalize()
            return (f"⚖️ {a} vs {b} Karşılaştırması:\n\n"
                   f"📌 {a}:\n• Güçlü yönleri\n• Kullanım alanları\n• Avantajlar\n\n"
                   f"📌 {b}:\n• Güçlü yönleri\n• Kullanım alanları\n• Avantajlar\n\n"
                   f"🏆 Hangisi daha iyi? Kullanım amacınıza göre değişir!\n"
                   f"💡 'ajan konseyi {a} vs {b}' ile daha derin analiz yapın!")
        return "Karşılaştırmak istediğiniz iki şeyi belirtin. Örn: 'Python ile Java karşılaştır'"

    def _howto(self, p):
        topic = re.sub(r'nasıl yapılır|nasıl|adım adım','',p).strip()[:35] or "bu"
        return (f"📋 {topic.title()} — Adım Adım:\n{'─'*35}\n\n"
               f"1️⃣ Hazırlık:\n   Gerekli malzeme ve araçları hazırla\n\n"
               f"2️⃣ Başlangıç:\n   İlk ve en önemli adımı at\n\n"
               f"3️⃣ Uygulama:\n   Sırayla ilerle, acele etme\n\n"
               f"4️⃣ Kontrol:\n   İlerlemeyi düzenli kontrol et\n\n"
               f"5️⃣ Tamamlama:\n   Son kontrolleri yap, sonucu değerlendir\n\n"
               f"💡 Detaylı rehber: 'derin araştır {topic[:20]} nasıl yapılır'")

    def _define(self, p):
        topic = re.sub(r'ne demek|anlam|tanım|nedir|hakkında','',p).strip()[:30] or "?"
        # Bilgi tabanında ara
        for key, info in BUILTIN_KNOWLEDGE.items():
            if key in topic.lower():
                return f"📚 {topic.capitalize()} Tanımı:\n\n{info[:300]}"
        return (f"📚 {topic.capitalize()} Tanımı:\n\n"
               f"'{topic}' kavramı hakkında:\n\n"
               f"Bu terimi daha iyi açıklamak için:\n"
               f"• 'derin araştır {topic[:20]}' → Kapsamlı bilgi\n"
               f"• 'google'da ara {topic[:20]} ne demek' → Web araması\n"
               f"• 'bilimsel açıkla {topic[:20]}' → Bilimsel tanım\n\n"
               f"Hangisini tercih edersiniz efendim?")

    def _advice(self, p):
        topic = re.sub(r'öneri|tavsiye|ne yapmalı|ne önerirsin','',p).strip()[:35] or "konu"
        return (f"💡 {topic.title()} için Tavsiyeler:\n{'─'*35}\n\n"
               f"🥇 En Önemli:\n   Küçük başlayın, tutarlı olun\n\n"
               f"📌 Pratik Adımlar:\n"
               f"   1. Önce araştırın ve planlayın\n"
               f"   2. Küçük adımlarla başlayın\n"
               f"   3. Geri bildirimlere açık olun\n"
               f"   4. Tutarlı devam edin\n\n"
               f"⚠️ Kaçınılacaklar:\n"
               f"   • Mükemmeliyetçilik tuzağı\n"
               f"   • Erteleme alışkanlığı\n\n"
               f"💡 'ajan konseyi {topic[:20]}' ile çoklu AI analizi yapın!")

    def _dialogue_response(self, p):
        topic = re.sub(r'diyalog|yaz|konuşma|sahne','',p).strip()[:30] or "günlük hayat"
        return (f"💬 Diyalog — {topic.capitalize()}:\n{'─'*35}\n\n"
               f"A: Merhaba! Seninle {topic} hakkında konuşabilir miyim?\n"
               f"B: Tabii ki! Ne düşünüyorsun bu konuda?\n"
               f"A: Aslında benim için çok önemli bir konu. Şöyle ki...\n"
               f"B: Anlıyorum, devam et lütfen.\n"
               f"A: Seninle paylaşmaktan memnunum.\n"
               f"B: Ben de. Birlikte düşünelim!\n\n"
               f"💡 Özel diyalog: 'diyalog yaz [karakter1] ve [karakter2] [durum]'")

    def _name_response(self, p):
        category = re.sub(r'isim|üret|öner|isimler','',p).strip()[:25] or "genel"
        names = {
            "karakter": ["Kael","Zara","Riven","Lyra","Daro","Nyx","Aeden","Solan"],
            "şirket":   ["Nexora","Veridian","Lumis","Cortex","Zenify","Arcova"],
            "proje":    ["Phoenix","Aurora","Titan","Nexus","Zenith","Apex","Nova"],
            "bebek":    ["Ela","Mira","Kaan","Ata","Bora","Lena","Zeren","Ada"],
            "genel":    ["Solace","Viren","Kaelo","Nyxa","Daren","Lyric","Aevo"],
        }
        chosen = names.get(category, names["genel"])
        return (f"🏷️ {category.capitalize()} İsimleri:\n\n"
               + "\n".join(f"• {name}" for name in random.sample(chosen, min(5,len(chosen))))
               + f"\n\n💡 Daha fazla: 'isim üret {category} 10' yazın efendim!")

    def _whatsapp_response(self, p):
        if "günaydın" in p:
            return "🌅 Günaydın! Harika bir gün geçirmeni diliyorum! ☀️✨"
        if "iyi geceler" in p:
            return "🌙 İyi geceler! Güzel rüyalar! 💤⭐"
        if "teşekkür" in p:
            return "💚 Rica ederim! Her zaman buradayım! 🙏"
        return (f"📱 WhatsApp Mesajı:\n\n"
               f"Merhaba! 👋\n\n"
               f"[Mesajınız buraya gelecek]\n\n"
               f"İyi günler! 😊\n\n"
               f"💡 'ai mesaj yaz [konu]' ile AI mesaj yazın efendim!")

    def _general_smart(self, p):
        """Akıllı genel cevap üretici"""
        words = [w for w in p.split() if len(w) > 3 and w not in
                ["nedir","nasıl","neden","nerede","lütfen","acaba","yoksa"]]
        topic = " ".join(words[:3]) if words else "konu"

        # Soru cümlesi
        if "?" in p or any(p.startswith(q) for q in ["ne ","nasıl ","neden ","nerede ","kim ","kaç "]):
            return (f"🤔 '{topic[:30]}' hakkında düşünüyorum...\n\n"
                   f"Bu soruyu yanıtlamak için:\n"
                   f"• 'derin araştır {topic[:25]}' → Kapsamlı araştırma\n"
                   f"• 'ajan konseyi {topic[:25]}' → Çoklu AI analizi\n"
                   f"• 'bilimsel açıkla {topic[:25]}' → Bilimsel yaklaşım\n\n"
                   f"Hangisini tercih edersiniz efendim?")

        # Tek kelime
        if len(p.split()) <= 2:
            return (f"'{topic}' hakkında ne öğrenmek istediğinizi belirtin efendim:\n"
                   f"• '{topic} nedir' → Tanım\n"
                   f"• '{topic} nasıl yapılır' → Rehber\n"
                   f"• 'derin araştır {topic}' → Detaylı bilgi\n"
                   f"• '{topic} analizi' → SWOT analizi")

        # Genel cevap
        responses = [
            f"Anlıyorum efendim! '{topic[:30]}' konusunda daha fazla bilgi verir misiniz?",
            f"Bu konuda size yardımcı olmak isterim! '{topic[:30]}' için hangi yönde ilerleyelim?",
            f"İlginç bir konu! '{topic[:30]}' hakkında 'yardım' yazarak tüm özellikleri görebilirsiniz.",
            f"Sizi duydum efendim! Bu konuda spesifik bir komut dener misiniz? 'yardım' yazarak başlayabilirsiniz.",
        ]
        return random.choice(responses)

    # ── Eski uyumluluk ────────────────────────────────────────────────────────
    def chat(self, prompt, system_override=None, hw_mode=False):
        """Eski self.ollama.chat() ile uyumluluk"""
        return self.ask(prompt, system_override)

    def summarize(self, text):
        sentences = re.split(r'[.!?]\s+', text.strip())
        return ". ".join(sentences[:3]) + "." if len(sentences) >= 3 else text[:300]

    def analyze_mood(self, text):
        t = text.lower()
        if any(w in t for w in ["mutlu","harika","süper","iyi"]): return "mutlu"
        if any(w in t for w in ["üzgün","kötü","sinirli","yorgun"]): return "üzgün"
        return "nötr"

    def get_model_info(self):
        return {
            "model": "Anka AI Core v2 — Yerleşik Zeka",
            "local_ai": self._local is not None,
            "cache_size": len(self._cache),
            "knowledge_topics": len(BUILTIN_KNOWLEDGE),
            "custom_qa": len(self._learn["custom_qa"]),
        }

    def set_personality(self, p): pass
    def clear(self): self._cache = {}
    def brain_stats(self): return "Anka AI Core v2 — Yerleşik Zeka Aktif ✅"


# ── Global singleton ──────────────────────────────────────────────────────────
_core_instance = None

def get_ai_core():
    global _core_instance
    if _core_instance is None:
        # İki aşamalı kurulum: AnkaAICore.__init__ içinde (LocalOllamaClient →
        # save_to_knowledge_base üzerinden) get_ai_core() tekrar çağrılabiliyor.
        # _core_instance'ı __init__ bitmeden atayarak bu döngüyü kırıyoruz.
        _core_instance = AnkaAICore.__new__(AnkaAICore)
        _core_instance.__init__()
    return _core_instance
