# ── ANKA OYUN MODÜLü ─────────────────────────────────────────────────────────
import json, os, threading, datetime, webbrowser, subprocess
import requests, re, random, time, psutil
from anka_config import BASE_DIR

GAMING_FILE = os.path.join(BASE_DIR, "anka_gaming.json")

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

class GamingAssistant:
    def __init__(self, ollama, speak_func, msg_func):
        self.ollama = ollama
        self.speak = speak_func
        self.msg = msg_func
        self.data = _load(GAMING_FILE, {"sessions":[], "achievements":[], "wishlist":[]})
        self.session_start = None
        self.current_game = None

    def start_session(self, game):
        self.session_start = time.time()
        self.current_game = game
        r = f"🎮 {game} oyun seansı başladı! Bol şans efendim."
        self.msg("ANKA", r); self.speak(r)

    def end_session(self):
        if not self.session_start:
            return
        duration = int((time.time() - self.session_start) / 60)
        self.data["sessions"].append({
            "game": self.current_game,
            "duration": duration,
            "date": datetime.date.today().isoformat()
        })
        _save(GAMING_FILE, self.data)
        r = f"✓ {self.current_game} seans bitti: {duration} dakika"
        self.msg("ANKA", r); self.speak(r)
        self.session_start = None

    def get_game_tips(self, game):
        def _t():
            r = self.ollama.chat(
                f"'{game}' oyunu için 5 önemli ipucu ve strateji ver.",
                system_override="Oyun uzmanı. Pratik ipuçları ver.")
            self.msg("ANKA", f"🎮 {game} İpuçları:\n{r}")
        threading.Thread(target=_t, daemon=True).start()

    def recommend_game(self, genre="", platform="PC"):
        def _r():
            r = self.ollama.chat(
                f"{platform} için {genre if genre else 'çeşitli'} türde 5 oyun öner. "
                f"Kısa açıklamalarıyla.",
                system_override="Oyun eleştirmeni. Kaliteli oyunlar öner.")
            self.msg("ANKA", f"🎮 Oyun Önerileri ({platform}):\n{r}")
        threading.Thread(target=_r, daemon=True).start()

    def gaming_stats(self):
        sessions = self.data["sessions"]
        if not sessions:
            return "Henüz oyun seansı kaydı yok efendim."
        total_min = sum(s["duration"] for s in sessions)
        games = {}
        for s in sessions:
            games[s["game"]] = games.get(s["game"], 0) + s["duration"]
        r = f"🎮 Oyun İstatistikleri:\n"
        r += f"• Toplam Süre: {total_min//60}sa {total_min%60}dk\n"
        r += f"• Seans Sayısı: {len(sessions)}\n\n"
        for game, mins in sorted(games.items(), key=lambda x: -x[1])[:5]:
            r += f"• {game}: {mins//60}sa {mins%60}dk\n"
        return r

    def gaming_setup_advice(self, budget):
        def _s():
            r = self.ollama.chat(
                f"{budget}₺ bütçeyle ideal gaming kurulum öner. "
                f"Türkiye fiyatlarına göre.",
                system_override="Donanım uzmanı. Bütçeye uygun gaming kurulum öner.")
            self.msg("ANKA", f"🖥️ Gaming Kurulum ({budget}₺):\n{r}")
        threading.Thread(target=_s, daemon=True).start()

    def fps_boost_tips(self):
        tips = [
            "GPU sürücülerini güncelleyin",
            "Güç planını 'Yüksek Performans' yapın",
            "Arka plan uygulamalarını kapatın",
            "Oyun modunu Windows'ta etkinleştirin",
            "Gölgeleri ve anti-aliasing'i düşürün",
            "SSD'ye taşıyın (HDD yavaşlatıyor)",
            "RAM'i çift kanallı kullanın"
        ]
        r = "⚡ FPS Artırma İpuçları:\n" + "\n".join(f"• {t}" for t in tips)
        self.msg("ANKA", r); self.speak("FPS artırma ipuçları hazırlandı efendim.")

    def add_wishlist(self, game):
        self.data["wishlist"].append({
            "game": game, "added": datetime.date.today().isoformat()
        })
        _save(GAMING_FILE, self.data)

    def stream_tips(self, platform="Twitch"):
        def _st():
            r = self.ollama.chat(
                f"{platform}'de başarılı yayın için ipuçları ve strateji.",
                system_override="Yayıncı koçu. Pratik streaming tavsiyeleri ver.")
            self.msg("ANKA", f"📺 {platform} Yayıncılık:\n{r}")
        threading.Thread(target=_st, daemon=True).start()

class GamingCommandProcessor:
    def __init__(self, speak_func, msg_func, ollama):
        self.speak = speak_func
        self.msg = msg_func
        self.ollama = ollama
        self.gaming = GamingAssistant(ollama, speak_func, msg_func)

    def process(self, text):
        t = text.lower().strip()

        if "oyun başlat" in t or "oynuyorum" in t:
            game = t.replace("oyun başlat","").replace("oynuyorum","").strip()
            self.gaming.start_session(game or "bilinmeyen oyun")
            return True

        if "oyun bitti" in t or "oyunu kapattım" in t:
            self.gaming.end_session()
            return True

        if "oyun ipucu" in t or "oyun stratejisi" in t:
            game = t.replace("oyun ipucu","").replace("oyun stratejisi","").strip()
            self.gaming.get_game_tips(game)
            return True

        if "oyun öner" in t:
            genre = ""
            for g in ["aksiyon","rpg","strateji","spor","yarış","korku","macera"]:
                if g in t: genre = g; break
            platform = "PS5" if "ps5" in t else "PC"
            self.gaming.recommend_game(genre, platform)
            return True

        if "oyun istatistik" in t or "ne kadar oynadım" in t:
            r = self.gaming.gaming_stats()
            self.msg("ANKA", r); self.speak(r)
            return True

        if "gaming kurulum" in t or "oyun bilgisayarı" in t:
            nums = re.findall(r'\d+', t)
            budget = nums[0] if nums else "10000"
            self.gaming.gaming_setup_advice(budget)
            return True

        if "fps artır" in t or "fps boost" in t:
            self.gaming.fps_boost_tips()
            return True

        if "oyun listeme ekle" in t or "wishlist" in t:
            game = t.replace("oyun listeme ekle","").replace("wishlist","").strip()
            if game:
                self.gaming.add_wishlist(game)
                r = f"✓ '{game}' oyun listene eklendi efendim."
                self.msg("ANKA", r); self.speak(r)
            return True

        if "yayın ipucu" in t or "stream nasıl" in t:
            platform = "YouTube" if "youtube" in t else "Twitch"
            self.gaming.stream_tips(platform)
            return True

        if "discord aç" in t:
            subprocess.Popen("discord:", shell=True)
            r = "✓ Discord açıldı efendim."
            self.msg("ANKA", r); self.speak(r)
            return True

        if "steam aç" in t:
            subprocess.Popen("steam:", shell=True)
            r = "✓ Steam açıldı efendim."
            self.msg("ANKA", r); self.speak(r)
            return True

        return False
