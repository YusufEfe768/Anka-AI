# ── ANKA POWER MODÜLü ────────────────────────────────────────────────────────
# YouTube indirme, Oyun takibi, Finans, Sistem, Web, Müzik, Güvenlik
import json, os, time, threading, datetime, subprocess, webbrowser
import requests, re, math, random, psutil
from anka_config import BASE_DIR

GAME_FILE    = os.path.join(BASE_DIR, "anka_games.json")
FINANCE_FILE = os.path.join(BASE_DIR, "anka_finance.json")
RSS_FILE     = os.path.join(BASE_DIR, "anka_rss.json")

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


# ── YouTube İndirici ─────────────────────────────────────────────────────────
class YouTubeDownloader:
    def __init__(self, msg_func, speak_func):
        self.msg = msg_func
        self.speak = speak_func
        self.download_path = os.path.join(os.path.expanduser("~"), "Desktop", "Anka Downloads")
        os.makedirs(self.download_path, exist_ok=True)

    def _check_ytdlp(self):
        try:
            subprocess.run(["yt-dlp","--version"], capture_output=True, timeout=5)
            return True
        except:
            return False

    def download_video(self, url, quality="720"):
        if not self._check_ytdlp():
            self.msg("ANKA","⚠️ yt-dlp kurulu değil. Kurmak için:\npip install yt-dlp")
            return
        self.msg("ANKA",f"📥 Video indiriliyor: {url}")
        def _dl():
            try:
                result = subprocess.run([
                    "yt-dlp", "-f", f"bestvideo[height<={quality}]+bestaudio/best",
                    "--merge-output-format", "mp4",
                    "-o", os.path.join(self.download_path, "%(title)s.%(ext)s"),
                    url
                ], capture_output=True, text=True, timeout=300)
                if result.returncode == 0:
                    r = f"✓ Video indirildi! Masaüstündeki 'Anka Downloads' klasörüne bakın."
                    self.msg("ANKA",r); self.speak(r)
                else:
                    self.msg("ANKA",f"İndirme hatası: {result.stderr[:200]}")
            except Exception as e:
                self.msg("ANKA",f"İndirme hatası: {e}")
        threading.Thread(target=_dl, daemon=True).start()

    def download_audio(self, url):
        if not self._check_ytdlp():
            self.msg("ANKA","⚠️ yt-dlp kurulu değil: pip install yt-dlp")
            return
        self.msg("ANKA",f"🎵 Ses indiriliyor: {url}")
        def _dl():
            try:
                result = subprocess.run([
                    "yt-dlp", "-x", "--audio-format", "mp3",
                    "-o", os.path.join(self.download_path, "%(title)s.%(ext)s"),
                    url
                ], capture_output=True, text=True, timeout=300)
                if result.returncode == 0:
                    r = "✓ MP3 indirildi! 'Anka Downloads' klasörüne bakın."
                    self.msg("ANKA",r); self.speak(r)
                else:
                    self.msg("ANKA","İndirme başarısız.")
            except Exception as e:
                self.msg("ANKA",f"Hata: {e}")
        threading.Thread(target=_dl, daemon=True).start()

    def get_video_info(self, url):
        if not self._check_ytdlp():
            return None
        try:
            result = subprocess.run([
                "yt-dlp", "--dump-json", "--no-download", url
            ], capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return {
                    "title": data.get("title",""),
                    "duration": data.get("duration",0),
                    "views": data.get("view_count",0),
                    "channel": data.get("channel","")
                }
        except: pass
        return None


# ── Oyun Takibi ──────────────────────────────────────────────────────────────
class GameTracker:
    GAMES = {
        "roblox": "RobloxPlayerBeta.exe",
        "minecraft": "javaw.exe",
        "steam": "steam.exe",
        "valorant": "VALORANT.exe",
        "fortnite": "FortniteClient-Win64-Shipping.exe",
        "cs2": "cs2.exe",
        "league": "LeagueClient.exe",
        "gta": "GTA5.exe",
    }

    def __init__(self):
        self.session_start = {}
        self.data = _load(GAME_FILE, {"sessions": [], "total": {}})

    def get_running_games(self):
        running = []
        procs = [p.name().lower() for p in psutil.process_iter(['name'])]
        for game, exe in self.GAMES.items():
            if exe.lower() in procs:
                running.append(game)
        return running

    def start_session(self, game):
        self.session_start[game] = time.time()

    def end_session(self, game):
        if game in self.session_start:
            duration = (time.time() - self.session_start[game]) / 60
            self.data["sessions"].append({
                "game": game,
                "duration_min": round(duration),
                "date": datetime.date.today().isoformat()
            })
            if game not in self.data["total"]:
                self.data["total"][game] = 0
            self.data["total"][game] += round(duration)
            del self.session_start[game]
            _save(GAME_FILE, self.data)
            return round(duration)
        return 0

    def get_stats(self):
        return self.data["total"]

    def get_today(self):
        today = datetime.date.today().isoformat()
        return [s for s in self.data["sessions"] if s["date"] == today]


# ── Finans Gelişmiş ──────────────────────────────────────────────────────────
class AdvancedFinance:
    def __init__(self, speak_func, msg_func, ollama):
        self.speak = speak_func
        self.msg = msg_func
        self.ollama = ollama
        self.portfolio = _load(FINANCE_FILE, {"crypto": {}, "stocks": {}, "gold": {}})

    def get_gold_price(self):
        try:
            r = requests.get("https://api.gold-api.com/price/XAU", timeout=5)
            data = r.json()
            usd = data.get("price", 0)
            # TL'ye çevir
            r2 = requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=5)
            try_rate = r2.json()["rates"]["TRY"]
            gram = (usd / 31.1035) * try_rate
            return {"usd_per_oz": usd, "try_per_gram": round(gram, 2)}
        except:
            return None

    def get_crypto_portfolio(self):
        if not self.portfolio["crypto"]:
            return None
        total = 0
        details = []
        for coin, amount in self.portfolio["crypto"].items():
            try:
                r = requests.get(f"https://api.coinbase.com/v2/prices/{coin.upper()}-USD/spot", timeout=5)
                price = float(r.json()["data"]["amount"])
                value = price * amount
                total += value
                details.append({"coin": coin, "amount": amount, "price": price, "value": round(value, 2)})
            except: pass
        return {"details": details, "total_usd": round(total, 2)}

    def mortgage_calculator(self, loan, rate_yearly, years):
        monthly_rate = rate_yearly / 100 / 12
        n = years * 12
        if monthly_rate == 0:
            monthly = loan / n
        else:
            monthly = loan * (monthly_rate * (1+monthly_rate)**n) / ((1+monthly_rate)**n - 1)
        total = monthly * n
        interest = total - loan
        return {
            "monthly": round(monthly, 2),
            "total": round(total, 2),
            "total_interest": round(interest, 2)
        }

    def analyze_expense_pdf(self, file_path):
        try:
            import PyPDF2
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() or ""
            analysis = self.ollama.chat(
                f"Bu banka ekstresini analiz et, harcama kategorilerini bul:\n{text[:2000]}",
                system_override="Finansal analist. Harcama kategorileri ve özet çıkar."
            )
            return analysis
        except Exception as e:
            return f"PDF analizi hatası: {e}"


# ── RSS Feed Okuyucu ─────────────────────────────────────────────────────────
class RSSReader:
    DEFAULT_FEEDS = {
        "Hürriyet": "https://www.hurriyet.com.tr/rss/anasayfa",
        "TRT Haber": "https://www.trthaber.com/sondakika.rss",
        "Milliyet": "https://www.milliyet.com.tr/rss/rssNew/gundemRss.xml",
        "Teknoloji": "https://www.webtekno.com/rss.xml",
    }

    def __init__(self):
        self.feeds = _load(RSS_FILE, self.DEFAULT_FEEDS)

    def get_news(self, source=None, limit=5):
        import xml.etree.ElementTree as ET
        results = {}
        feeds = {source: self.feeds[source]} if source and source in self.feeds else self.feeds
        for name, url in list(feeds.items())[:3]:
            try:
                r = requests.get(url, timeout=5, headers={"User-Agent": "AnkaBot/1.0"})
                root = ET.fromstring(r.content)
                items = root.findall(".//item")[:limit]
                news = []
                for item in items:
                    title = item.find("title")
                    if title is not None and title.text:
                        news.append(title.text.strip())
                if news:
                    results[name] = news
            except: pass
        return results

    def add_feed(self, name, url):
        self.feeds[name] = url
        _save(RSS_FILE, self.feeds)

    def get_sources(self):
        return list(self.feeds.keys())


# ── Sistem Gelişmiş ──────────────────────────────────────────────────────────
class SystemAdvanced:
    def disk_health(self):
        try:
            result = subprocess.run(
                ["powershell","-Command",
                 "Get-WmiObject -Class Win32_DiskDrive | Select Model,Status,Size | ConvertTo-Json"],
                capture_output=True, text=True, timeout=10)
            data = json.loads(result.stdout)
            if isinstance(data, dict): data = [data]
            report = "💾 Disk Sağlığı:\n"
            for disk in data:
                size_gb = int(disk.get("Size",0)) // (1024**3)
                report += f"• {disk.get('Model','?')}: {disk.get('Status','?')} ({size_gb}GB)\n"
            return report
        except: return "Disk bilgisi alınamadı."

    def ram_usage_by_app(self, top=10):
        procs = []
        for proc in psutil.process_iter(['name','memory_info']):
            try:
                mem = proc.info['memory_info'].rss / 1024 / 1024
                procs.append((proc.info['name'], round(mem, 1)))
            except: pass
        procs.sort(key=lambda x: -x[1])
        return procs[:top]

    def startup_apps(self):
        try:
            result = subprocess.run(
                ["powershell","-Command",
                 "Get-CimInstance Win32_StartupCommand | Select Name,Command | ConvertTo-Json"],
                capture_output=True, text=True, timeout=10)
            data = json.loads(result.stdout)
            if isinstance(data, dict): data = [data]
            return [(d.get("Name","?"), d.get("Command","?")) for d in data[:10]]
        except: return []

    def windows_update_check(self):
        try:
            result = subprocess.run(
                ["powershell","-Command",
                 "(New-Object -ComObject Microsoft.Update.Session).CreateUpdateSearcher().Search('IsInstalled=0').Updates.Count"],
                capture_output=True, text=True, timeout=30)
            count = result.stdout.strip()
            return int(count) if count.isdigit() else 0
        except: return -1

    def optimize_startup(self):
        subprocess.Popen(["msconfig"], shell=True)
        return "✓ Başlangıç Yapılandırması açıldı efendim."

    def clear_temp(self):
        import shutil
        temp = os.environ.get("TEMP", "C:\\Windows\\Temp")
        deleted = 0
        for item in os.listdir(temp):
            try:
                path = os.path.join(temp, item)
                if os.path.isfile(path):
                    os.unlink(path); deleted += 1
                elif os.path.isdir(path):
                    shutil.rmtree(path); deleted += 1
            except: pass
        return f"✓ {deleted} geçici dosya temizlendi."


# ── Güvenlik Gelişmiş ────────────────────────────────────────────────────────
class AdvancedSecurity:
    def check_vpn(self):
        try:
            r = requests.get("https://api.ipify.org?format=json", timeout=5)
            ip = r.json()["ip"]
            r2 = requests.get(f"https://ipapi.co/{ip}/json/", timeout=5)
            data = r2.json()
            return {
                "ip": ip,
                "country": data.get("country_name","?"),
                "city": data.get("city","?"),
                "org": data.get("org","?")
            }
        except: return None

    def check_email_breach(self, email):
        try:
            r = requests.get(
                f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}",
                headers={"User-Agent":"AnkaBot"},
                timeout=5)
            if r.status_code == 200:
                breaches = r.json()
                return [b["Name"] for b in breaches[:5]]
            elif r.status_code == 404:
                return []
        except: pass
        return None

    def check_permissions(self):
        try:
            result = subprocess.run(
                ["powershell","-Command",
                 "Get-AppxPackage | Select Name | ConvertTo-Json"],
                capture_output=True, text=True, timeout=15)
            data = json.loads(result.stdout)
            if isinstance(data, dict): data = [data]
            apps = [d.get("Name","") for d in data[:20] if d.get("Name")]
            return apps
        except: return []

    def firewall_status(self):
        try:
            result = subprocess.run(
                ["powershell","-Command",
                 "Get-NetFirewallProfile | Select Name,Enabled | ConvertTo-Json"],
                capture_output=True, text=True, timeout=10)
            data = json.loads(result.stdout)
            if isinstance(data, dict): data = [data]
            return [(d.get("Name","?"), d.get("Enabled",False)) for d in data]
        except: return []


# ── Podcast / Şarkı Sözü ────────────────────────────────────────────────────
class MediaInfo:
    def __init__(self, ollama):
        self.ollama = ollama

    def get_lyrics(self, song, artist=""):
        try:
            query = f"{artist} {song}".strip()
            webbrowser.open(f"https://www.google.com/search?q={query}+lyrics+sözleri")
            return f"✓ '{query}' şarkı sözleri için tarayıcı açıldı efendim."
        except: return "Açılamadı efendim."

    def recommend_music(self, mood, genre=""):
        return self.ollama.chat(
            f"Ruh hali: {mood}, Tür: {genre if genre else 'herhangi'}. "
            f"5 şarkı öner. Sanatçı - Şarkı adı formatında.",
            system_override="Müzik önerisi yap. Çeşitli ve kaliteli öneriler sun."
        )

    def podcast_recommend(self, topic):
        return self.ollama.chat(
            f"'{topic}' konusunda Türkçe podcast önerisi yap. 3-5 öneri.",
            system_override="Podcast uzmanısın. Kaliteli Türkçe podcastler öner."
        )


# ── Ana Komut İşleyici ────────────────────────────────────────────────────────
class PowerCommandProcessor:
    def __init__(self, speak_func, msg_func, ollama):
        self.speak = speak_func
        self.msg = msg_func
        self.ollama = ollama
        self.yt = YouTubeDownloader(msg_func, speak_func)
        self.games = GameTracker()
        self.finance = AdvancedFinance(speak_func, msg_func, ollama)
        self.rss = RSSReader()
        self.sys_adv = SystemAdvanced()
        self.security = AdvancedSecurity()
        self.media = MediaInfo(ollama)

    def process(self, text):
        t = text.lower().strip()

        # ── YouTube İndirme ───────────────────────────────────────────────────
        if "youtube indir" in t or "video indir" in t:
            url = re.search(r'https?://\S+', text)
            if url:
                quality = "480"
                for q in ["1080","720","480","360"]:
                    if q in t: quality = q; break
                self.yt.download_video(url.group(0), quality)
            else:
                self.msg("ANKA","YouTube linkini söyleyin efendim. Örn: 'youtube indir https://...'")
            return True

        if "mp3 indir" in t or "ses indir" in t or "müzik indir" in t:
            url = re.search(r'https?://\S+', text)
            if url:
                self.yt.download_audio(url.group(0))
            else:
                self.msg("ANKA","YouTube linkini söyleyin efendim.")
            return True

        if "video bilgisi" in t or "youtube bilgisi" in t:
            url = re.search(r'https?://\S+', text)
            if url:
                def _info():
                    info = self.yt.get_video_info(url.group(0))
                    if info:
                        mins = info["duration"] // 60
                        r = (f"📺 Video Bilgisi:\n"
                             f"• Başlık: {info['title']}\n"
                             f"• Süre: {mins} dakika\n"
                             f"• İzlenme: {info['views']:,}\n"
                             f"• Kanal: {info['channel']}")
                        self.msg("ANKA",r)
                    else:
                        self.msg("ANKA","Video bilgisi alınamadı efendim.")
                threading.Thread(target=_info, daemon=True).start()
            return True

        # ── Oyun Takibi ───────────────────────────────────────────────────────
        if "hangi oyunlar çalışıyor" in t or "oyun durumu" in t:
            games = self.games.get_running_games()
            if games:
                r = "🎮 Çalışan Oyunlar:\n" + "\n".join(f"• {g.capitalize()}" for g in games)
            else:
                r = "Şu an aktif oyun yok efendim."
            self.msg("ANKA",r); self.speak(r)
            return True

        if "oyun istatistik" in t or "ne kadar oynadım" in t:
            stats = self.games.get_stats()
            if not stats:
                r = "Henüz oyun istatistiği yok efendim."
            else:
                r = "🎮 Toplam Oyun Süreleri:\n"
                for game, mins in sorted(stats.items(), key=lambda x: -x[1]):
                    hours = mins // 60
                    r += f"• {game.capitalize()}: {hours}sa {mins%60}dk\n"
            self.msg("ANKA",r); self.speak(r)
            return True

        # ── Altın Fiyatı ──────────────────────────────────────────────────────
        if "altın fiyatı" in t or "gram altın" in t:
            def _gold():
                data = self.finance.get_gold_price()
                if data:
                    r = f"🥇 Altın Fiyatı:\n• Gram: {data['try_per_gram']:,.2f} ₺\n• Ons: ${data['usd_per_oz']:,.2f}"
                    self.msg("ANKA",r); self.speak(f"Gram altın {data['try_per_gram']:,.0f} lira efendim.")
                else:
                    self.msg("ANKA","Altın fiyatı alınamadı efendim.")
            threading.Thread(target=_gold, daemon=True).start()
            return True

        # ── Kripto Portföy ────────────────────────────────────────────────────
        if "kripto ekle" in t or "portföye ekle" in t:
            m = re.search(r'(\w+)\s+(\d+(?:\.\d+)?)', t)
            if m:
                coin, amount = m.group(1), float(m.group(2))
                self.finance.portfolio["crypto"][coin.upper()] = amount
                _save(FINANCE_FILE, self.finance.portfolio)
                r = f"✓ {coin.upper()} portföye eklendi: {amount} adet"
                self.msg("ANKA",r); self.speak(r)
            return True

        if "portföyüm" in t or "kripto portföy" in t:
            def _port():
                data = self.finance.get_crypto_portfolio()
                if data and data["details"]:
                    r = "₿ Kripto Portföyünüz:\n"
                    for d in data["details"]:
                        r += f"• {d['coin']}: {d['amount']} adet × ${d['price']:,.0f} = ${d['value']:,.2f}\n"
                    r += f"💰 Toplam: ${data['total_usd']:,.2f}"
                    self.msg("ANKA",r); self.speak(f"Portföy değeri {data['total_usd']:,.0f} dolar efendim.")
                else:
                    self.msg("ANKA","Portföy boş. 'bitcoin 0.5 portföye ekle' ile ekleyin efendim.")
            threading.Thread(target=_port, daemon=True).start()
            return True

        # ── Kredi/Mortgage ────────────────────────────────────────────────────
        if "kredi hesapla" in t or "mortgage" in t or "taksit hesapla" in t:
            nums = re.findall(r'\d+(?:\.\d+)?', t)
            if len(nums) >= 3:
                loan, rate, years = float(nums[0]), float(nums[1]), int(nums[2])
                result = self.finance.mortgage_calculator(loan, rate, years)
                r = (f"🏦 Kredi Hesaplama:\n"
                     f"• Kredi: {loan:,.0f}₺\n"
                     f"• Faiz: %{rate}/yıl\n"
                     f"• Vade: {years} yıl\n"
                     f"• Aylık Taksit: {result['monthly']:,.2f}₺\n"
                     f"• Toplam Ödeme: {result['total']:,.2f}₺\n"
                     f"• Toplam Faiz: {result['total_interest']:,.2f}₺")
                self.msg("ANKA",r); self.speak(f"Aylık taksit {result['monthly']:,.0f} lira efendim.")
            return True

        # ── RSS Haberler ──────────────────────────────────────────────────────
        if "rss haber" in t or "kaynak haber" in t:
            source = None
            for src in self.rss.get_sources():
                if src.lower() in t: source = src; break
            def _rss():
                news = self.rss.get_news(source)
                if news:
                    r = "📰 Haberler:\n"
                    for src, articles in news.items():
                        r += f"\n【{src}】\n"
                        r += "\n".join(f"• {a[:60]}" for a in articles)
                    self.msg("ANKA",r); self.speak("Haberler hazır efendim.")
                else:
                    self.msg("ANKA","Haber alınamadı efendim.")
            threading.Thread(target=_rss, daemon=True).start()
            return True

        if "rss kaynağı ekle" in t:
            parts = t.replace("rss kaynağı ekle","").strip().split(":")
            if len(parts) >= 2:
                name, url = parts[0].strip(), parts[1].strip()
                self.rss.add_feed(name, url)
                r = f"✓ {name} RSS kaynağı eklendi efendim."
                self.msg("ANKA",r); self.speak(r)
            return True

        # ── Disk Sağlığı ──────────────────────────────────────────────────────
        if "disk sağlığı" in t or "disk durumu" in t:
            def _disk():
                result = self.sys_adv.disk_health()
                self.msg("ANKA",result); self.speak("Disk sağlık raporu hazır efendim.")
            threading.Thread(target=_disk, daemon=True).start()
            return True

        # ── RAM Kullanımı ─────────────────────────────────────────────────────
        if "ram kullanan" in t or "bellek kullanan" in t:
            apps = self.sys_adv.ram_usage_by_app()
            r = "💾 En Çok RAM Kullanan:\n"
            r += "\n".join(f"• {name}: {mem} MB" for name,mem in apps[:8])
            self.msg("ANKA",r); self.speak(r)
            return True

        # ── Geçici Dosya ──────────────────────────────────────────────────────
        if "geçici dosya" in t and "temizle" in t:
            def _temp():
                result = self.sys_adv.clear_temp()
                self.msg("ANKA",result); self.speak(result)
            threading.Thread(target=_temp, daemon=True).start()
            return True

        # ── Windows Update ────────────────────────────────────────────────────
        if "windows güncelleme" in t or "update var mı" in t:
            def _upd():
                count = self.sys_adv.windows_update_check()
                if count > 0:
                    r = f"⚠️ {count} Windows güncellemesi bekliyor efendim."
                elif count == 0:
                    r = "✓ Windows güncel efendim."
                else:
                    r = "Güncelleme kontrolü yapılamadı efendim."
                self.msg("ANKA",r); self.speak(r)
            threading.Thread(target=_upd, daemon=True).start()
            return True

        # ── VPN Kontrolü ──────────────────────────────────────────────────────
        if "vpn durumu" in t or "ip adresim" in t or "konumum" in t:
            def _vpn():
                data = self.security.check_vpn()
                if data:
                    r = (f"🌐 Bağlantı Bilgisi:\n"
                         f"• IP: {data['ip']}\n"
                         f"• Ülke: {data['country']}\n"
                         f"• Şehir: {data['city']}\n"
                         f"• Sağlayıcı: {data['org']}")
                    self.msg("ANKA",r); self.speak(f"IP adresiniz {data['ip']} efendim.")
                else:
                    self.msg("ANKA","Bağlantı bilgisi alınamadı efendim.")
            threading.Thread(target=_vpn, daemon=True).start()
            return True

        # ── E-posta Güvenlik ──────────────────────────────────────────────────
        if "mail sızıntı" in t or "email güvenlik" in t:
            email_m = re.search(r'[\w.+-]+@[\w-]+\.\w+', t)
            if email_m:
                def _breach():
                    breaches = self.security.check_email_breach(email_m.group(0))
                    if breaches is None:
                        self.msg("ANKA","Kontrol yapılamadı efendim.")
                    elif not breaches:
                        self.msg("ANKA","✓ Bu e-posta herhangi bir veri ihlalinde bulunmuyor efendim.")
                    else:
                        r = f"⚠️ Dikkat! Bu e-posta şu ihlallerde görüldü:\n" + \
                            "\n".join(f"• {b}" for b in breaches)
                        self.msg("ANKA",r); self.speak("E-posta veri ihlali bulundu efendim!")
                threading.Thread(target=_breach, daemon=True).start()
            return True

        # ── Güvenlik Duvarı ───────────────────────────────────────────────────
        if "güvenlik duvarı" in t or "firewall" in t:
            def _fw():
                profiles = self.security.firewall_status()
                if profiles:
                    r = "🔒 Güvenlik Duvarı:\n"
                    r += "\n".join(f"• {name}: {'✓ Açık' if enabled else '✗ Kapalı'}"
                                   for name,enabled in profiles)
                    self.msg("ANKA",r); self.speak(r)
                else:
                    self.msg("ANKA","Güvenlik duvarı bilgisi alınamadı efendim.")
            threading.Thread(target=_fw, daemon=True).start()
            return True

        # ── Şarkı Sözü ────────────────────────────────────────────────────────
        if "şarkı sözü" in t or "lyrics" in t:
            song = t.replace("şarkı sözü","").replace("lyrics","").strip()
            if song:
                result = self.media.get_lyrics(song)
                self.msg("ANKA",result); self.speak(result)
            return True

        # ── Müzik Öneri ───────────────────────────────────────────────────────
        if "müzik öner" in t or "şarkı öner" in t:
            mood = t.replace("müzik öner","").replace("şarkı öner","").strip() or "genel"
            def _music():
                result = self.media.recommend_music(mood)
                self.msg("ANKA",f"🎵 Öneri ({mood}):\n{result}")
                self.speak("Müzik önerileri hazır efendim.")
            threading.Thread(target=_music, daemon=True).start()
            return True

        # ── Podcast Öneri ─────────────────────────────────────────────────────
        if "podcast öner" in t:
            topic = t.replace("podcast öner","").strip() or "teknoloji"
            def _pod():
                result = self.media.podcast_recommend(topic)
                self.msg("ANKA",f"🎙 Podcast Önerisi ({topic}):\n{result}")
                self.speak("Podcast önerileri hazır efendim.")
            threading.Thread(target=_pod, daemon=True).start()
            return True

        # ── Başlangıç Optimize ────────────────────────────────────────────────
        if "başlangıç optimize" in t or "startup optimize" in t:
            result = self.sys_adv.optimize_startup()
            self.msg("ANKA",result); self.speak(result)
            return True

        # ── Startup Uygulamaları ──────────────────────────────────────────────
        if "başlangıç uygulamaları" in t or "startup uygulamaları" in t:
            def _startup():
                apps = self.sys_adv.startup_apps()
                if apps:
                    r = "🚀 Başlangıç Uygulamaları:\n"
                    r += "\n".join(f"• {name}" for name,_ in apps[:10])
                    self.msg("ANKA",r)
                else:
                    self.msg("ANKA","Başlangıç uygulamaları alınamadı efendim.")
            threading.Thread(target=_startup, daemon=True).start()
            return True

        return False
