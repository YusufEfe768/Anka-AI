# ── ANKA KOMUT İŞLEYİCİ ─────────────────────────────────────────────────────
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
import subprocess, webbrowser, os, datetime, time, threading
import psutil, requests
from anka_memory import (add_note, get_notes, add_task, get_pending_tasks,
                          complete_task, add_alarm, get_active_alarms,
                          log_water, add_expense, get_monthly_total,
                          log_event, get_daily_log, load_health, save_health)
from anka_config import USER_NAME, WEATHER_CITY

def speak_fn(text, speak):
    threading.Thread(target=lambda: speak(text), daemon=True).start()

class CommandProcessor:
    def __init__(self, speak_func, msg_func, ollama):
        self.speak = speak_func
        self.msg   = msg_func
        self.ollama = ollama
        self.timers = {}
        self.pomodoro_active = False

    def process(self, text):
        t = text.lower().strip()

        # ── Uygulama Aç ──────────────────────────────────────────────────────
        app_map = {
            "chrome":"chrome","firefox":"firefox","spotify":"spotify:",
            "youtube":"https://youtube.com","netflix":"https://netflix.com",
            "instagram":"https://instagram.com","twitter":"https://twitter.com",
            "notepad":"notepad","hesap makinesi":"calc","dosya gezgini":"explorer",
            "görev yöneticisi":"taskmgr","paint":"mspaint","word":"winword",
            "excel":"excel","powerpoint":"powerpnt","discord":"discord",
            "steam":"steam://","whatsapp":"whatsapp:","telegram":"telegram",
            "vs code":"code","visual studio code":"code",
        }
        for k,v in app_map.items():
            if k in t and any(x in t for x in ["aç","başlat","çalıştır","getir"]):
                if v.startswith("http"):
                    webbrowser.open(v)
                else:
                    subprocess.Popen(v, shell=True)
                r = f"✓ {k.capitalize()} açıldı efendim."
                self.msg("ANKA",r); self.speak(r); return True

        # ── Web Arama ────────────────────────────────────────────────────────
        if any(x in t for x in ["google'da ara","internette ara","web'de ara","aratır"]):
            q = t.replace("google'da ara","").replace("internette ara","").replace("web'de ara","").replace("aratır","").strip()
            webbrowser.open(f"https://google.com/search?q={q}")
            r=f"✓ '{q}' Google'da arandı."; self.msg("ANKA",r); self.speak(r); return True

        if "youtube'da ara" in t or ("youtube" in t and "ara" in t):
            q=t.replace("youtube'da ara","").replace("youtube","").replace("ara","").strip()
            webbrowser.open(f"https://youtube.com/search?search_query={q}")
            r=f"✓ YouTube'da '{q}' arandı."; self.msg("ANKA",r); self.speak(r); return True

        # ── Ses Kontrolü ─────────────────────────────────────────────────────
        if "ses" in t and any(x in t for x in ["artır","yükselt","aç"]) and "mesaj" not in t:
            pyautogui.press("volumeup", presses=5)
            r="✓ Ses artırıldı."; self.msg("ANKA",r); self.speak(r); return True
        if "ses" in t and any(x in t for x in ["azalt","kıs","düşür"]):
            pyautogui.press("volumedown", presses=5)
            r="✓ Ses azaltıldı."; self.msg("ANKA",r); self.speak(r); return True
        if "sessiz" in t or "mute" in t:
            pyautogui.press("volumemute")
            r="✓ Sessiz moda alındı."; self.msg("ANKA",r); self.speak(r); return True

        # ── Ekran ────────────────────────────────────────────────────────────
        if "ekran görüntüsü" in t:
            path=os.path.join(os.path.expanduser("~"),"Desktop",f"anka_{int(time.time())}.png")
            pyautogui.screenshot(path)
            r=f"✓ Ekran görüntüsü masaüstüne kaydedildi."; self.msg("ANKA",r); self.speak(r); return True

        if "ekranı kilitle" in t:
            subprocess.run(["rundll32.exe","user32.dll,LockWorkStation"])
            return True

        # ── Bilgisayar Kapat ─────────────────────────────────────────────────
        if "bilgisayarı kapat" in t:
            subprocess.run(["shutdown","/s","/t","30"])
            r="✓ Bilgisayar 30 saniye içinde kapanacak efendim."; self.msg("ANKA",r); self.speak(r); return True
        if "yeniden başlat" in t:
            subprocess.run(["shutdown","/r","/t","30"])
            r="✓ Bilgisayar yeniden başlatılacak efendim."; self.msg("ANKA",r); self.speak(r); return True

        # ── Yazıcı ───────────────────────────────────────────────────────────
        if "yazıcı" in t and "aç" in t:
            subprocess.Popen("control printers", shell=True)
            r="✓ Yazıcı ayarları açıldı efendim."; self.msg("ANKA",r); self.speak(r); return True
        if "yazdır" in t:
            r="Hangi dosyayı yazdırmamı istersiniz efendim?"; self.msg("ANKA",r); self.speak(r); return True

        # ── Notlar ───────────────────────────────────────────────────────────
        if "not al" in t or "not ekle" in t:
            note=t.replace("not al","").replace("not ekle","").strip()
            if note:
                n=add_note(note); log_event("note_added",note)
                r=f"✓ Not kaydedildi. Toplam {n} notunuz var efendim."; self.msg("ANKA",r); self.speak(r); return True

        if any(x in t for x in ["notlarım","notları göster","notlarımı"]):
            notes=get_notes(5)
            if not notes: r="Hiç notunuz yok efendim."
            else: r="📝 Son notlarınız:\n"+"\n".join(f"• {n['text']}" for n in notes)
            self.msg("ANKA",r); self.speak(r); return True

        # ── Görevler ─────────────────────────────────────────────────────────
        if "görev ekle" in t or "yapılacak ekle" in t:
            task=t.replace("görev ekle","").replace("yapılacak ekle","").strip()
            if task:
                add_task(task); log_event("task_added",task)
                r=f"✓ Görev eklendi: {task}"; self.msg("ANKA",r); self.speak(r); return True

        if any(x in t for x in ["görevlerim","yapılacaklarım","görevleri göster"]):
            tasks=get_pending_tasks()
            if not tasks: r="Bekleyen göreviniz yok efendim."
            else: r="📋 Görevleriniz:\n"+"\n".join(f"• {tk['text']}" for tk in tasks)
            self.msg("ANKA",r); self.speak(r); return True

        # ── Alarm ────────────────────────────────────────────────────────────
        if "alarm" in t and "kur" in t:
            import re
            m=re.search(r'(\d{1,2})[:\.](\d{2})',t)
            if m:
                h,mn=int(m.group(1)),int(m.group(2))
                label=t.replace(f"{m.group(0)}","").replace("alarm","").replace("kur","").strip() or "Alarm"
                add_alarm(h,mn,label); log_event("alarm_set",f"{h}:{mn:02d}")
                r=f"✓ Saat {h}:{mn:02d} için alarm kuruldu efendim."; self.msg("ANKA",r); self.speak(r); return True

        if "alarmlarım" in t or "alarm listesi" in t:
            alarms=get_active_alarms()
            if not alarms: r="Aktif alarm yok efendim."
            else: r="⏰ Alarmlarınız:\n"+"\n".join(f"• {a['hour']}:{a['minute']:02d} - {a['label']}" for a in alarms)
            self.msg("ANKA",r); self.speak(r); return True

        # ── Zamanlayıcı ───────────────────────────────────────────────────────
        if any(x in t for x in ["dakika sonra hatırlat","saniye sonra","zamanlayıcı"]):
            import re
            m=re.search(r'(\d+)\s*(dakika|saniye)',t)
            if m:
                n,unit=int(m.group(1)),m.group(2)
                secs=n*60 if unit=="dakika" else n
                label=t.replace(m.group(0),"").replace("sonra hatırlat","").replace("zamanlayıcı","").strip() or "Zamanlayıcı"
                def _timer():
                    time.sleep(secs)
                    self.msg("SİSTEM",f"⏰ {label} — {n} {unit} doldu!")
                    self.speak(f"Efendim, {n} {unit} doldu. {label}")
                threading.Thread(target=_timer,daemon=True).start()
                r=f"✓ {n} {unit} sonra hatırlatacağım efendim."; self.msg("ANKA",r); self.speak(r); return True

        # ── Pomodoro ──────────────────────────────────────────────────────────
        if "pomodoro" in t or "çalışma modu" in t:
            def _pomodoro():
                self.msg("ANKA","🍅 Pomodoro başladı! 25 dakika çalışma...")
                self.speak("Pomodoro başladı, 25 dakika çalışma zamanı efendim.")
                time.sleep(25*60)
                self.msg("ANKA","✅ 25 dakika bitti! 5 dakika mola.")
                self.speak("25 dakika bitti efendim. 5 dakika mola zamanı.")
                time.sleep(5*60)
                self.msg("ANKA","🍅 Mola bitti! Tekrar çalışma zamanı.")
                self.speak("Mola bitti efendim. Tekrar çalışma zamanı.")
            threading.Thread(target=_pomodoro,daemon=True).start()
            return True

        # ── Su Takibi ─────────────────────────────────────────────────────────
        if "su iç" in t or "su içtim" in t:
            count,goal=log_water()
            r=f"✓ Kaydedildi! Bugün {count}/{goal} bardak su içtiniz efendim."
            self.msg("ANKA",r); self.speak(r); return True

        # ── Saat & Tarih ─────────────────────────────────────────────────────
        if "saat" in t and any(x in t for x in ["kaç","söyle","ne"]):
            r=f"Saat {datetime.datetime.now().strftime('%H:%M')} efendim."
            self.msg("ANKA",r); self.speak(r); return True

        if any(x in t for x in ["tarih","bugün ne","hangi gün"]):
            now=datetime.datetime.now()
            r=f"Bugün {now.strftime('%d %B %Y, %A')} efendim."
            self.msg("ANKA",r); self.speak(r); return True

        # ── Hava ─────────────────────────────────────────────────────────────
        if "hava" in t:
            threading.Thread(target=self._get_weather, daemon=True).start()
            return True

        # ── Döviz ────────────────────────────────────────────────────────────
        if any(x in t for x in ["dolar","euro","döviz","kur"]):
            threading.Thread(target=self._get_currency, daemon=True).start()
            return True

        # ── Kripto ───────────────────────────────────────────────────────────
        if any(x in t for x in ["bitcoin","ethereum","kripto","btc","eth"]):
            threading.Thread(target=self._get_crypto, daemon=True).start()
            return True

        # ── Borsa ────────────────────────────────────────────────────────────
        if any(x in t for x in ["borsa","bist","hisse"]):
            threading.Thread(target=self._get_stocks, daemon=True).start()
            return True

        # ── Wikipedia ────────────────────────────────────────────────────────
        if "wikipedia" in t or "vikipedi" in t:
            q=t.replace("wikipedia'da ara","").replace("vikipedide ara","").replace("wikipedia","").replace("vikipedi","").strip()
            threading.Thread(target=lambda: self._wikipedia(q), daemon=True).start()
            return True

        # ── Haberler ─────────────────────────────────────────────────────────
        if any(x in t for x in ["haberler","günün haberleri","haber oku"]):
            threading.Thread(target=self._get_news, daemon=True).start()
            return True

        # ── Sistem Bilgisi ───────────────────────────────────────────────────
        if any(x in t for x in ["sistem durumu","bilgisayar durumu","performans"]):
            cpu=psutil.cpu_percent(); ram=psutil.virtual_memory()
            disk=psutil.disk_usage('/')
            r=(f"💻 Sistem Durumu:\n"
               f"• CPU: %{cpu}\n"
               f"• RAM: %{ram.percent} ({ram.used//1024//1024}MB / {ram.total//1024//1024}MB)\n"
               f"• Disk: %{disk.percent} ({disk.used//1024//1024//1024}GB / {disk.total//1024//1024//1024}GB)")
            self.msg("ANKA",r); self.speak(f"CPU yüzde {int(cpu)}, RAM yüzde {int(ram.percent)} kullanımda efendim."); return True

        # ── RAM Temizle ───────────────────────────────────────────────────────
        if "ram temizle" in t or "bellek temizle" in t:
            subprocess.run(["EmptyStandbyList.exe"], shell=True, capture_output=True)
            r="✓ Bellek temizleme komutu verildi efendim."; self.msg("ANKA",r); self.speak(r); return True

        # ── İnternet Hızı ────────────────────────────────────────────────────
        if "internet hızı" in t or "hız testi" in t:
            threading.Thread(target=self._speedtest, daemon=True).start()
            return True

        # ── WiFi Şifresi ─────────────────────────────────────────────────────
        if "wifi şifresi" in t or "kablosuz şifre" in t:
            threading.Thread(target=self._wifi_password, daemon=True).start()
            return True

        # ── Pil Durumu ────────────────────────────────────────────────────────
        if "pil" in t or "batarya" in t or "şarj" in t:
            battery=psutil.sensors_battery()
            if battery:
                plugged="Şarjda" if battery.power_plugged else "Pilde"
                r=f"🔋 Batarya: %{int(battery.percent)} — {plugged}"
            else:
                r="🔋 Batarya bilgisi alınamadı."
            self.msg("ANKA",r); self.speak(r); return True

        # ── Günlük Özet ───────────────────────────────────────────────────────
        if any(x in t for x in ["günlük özet","bugün ne yaptım","günümü özetle"]):
            logs=get_daily_log()
            tasks=get_pending_tasks()
            h=load_health()
            r=(f"📊 Günlük Özetiniz:\n"
               f"• {len(logs)} etkinlik kaydedildi\n"
               f"• {len(tasks)} bekleyen görev\n"
               f"• {h.get('water_count',0)}/{h.get('water_goal',8)} bardak su\n"
               f"• Saat {datetime.datetime.now().strftime('%H:%M')}")
            self.msg("ANKA",r); self.speak(r); return True

        # ── Bütçe ─────────────────────────────────────────────────────────────
        if "harcama ekle" in t:
            import re
            m=re.search(r'(\d+)',t)
            if m:
                amount=int(m.group(1))
                cat=t.replace(m.group(0),"").replace("harcama ekle","").replace("tl","").strip() or "Genel"
                add_expense(amount,cat)
                total,limit=get_monthly_total()
                r=f"✓ {amount}₺ harcama eklendi. Bu ay toplam: {total}₺/{limit}₺"
                self.msg("ANKA",r); self.speak(r); return True

        if "harcamalarım" in t or "bütçem" in t:
            total,limit=get_monthly_total()
            r=f"💰 Bu ay {total}₺ harcadınız. Limit: {limit}₺. Kalan: {limit-total}₺"
            self.msg("ANKA",r); self.speak(r); return True

        # ── Şifre Üret ────────────────────────────────────────────────────────
        if "şifre üret" in t or "güçlü şifre" in t:
            import secrets, string
            chars=string.ascii_letters+string.digits+"!@#$%^&*"
            pwd=''.join(secrets.choice(chars) for _ in range(16))
            pyperclip.copy(pwd)
            r=f"🔐 Güçlü şifre: {pwd}\n(Panoya kopyalandı)"
            self.msg("ANKA",r); self.speak("Güçlü şifre oluşturuldu ve panoya kopyalandı efendim."); return True

        # ── Doğum Günü ────────────────────────────────────────────────────────
        if "doğum günü" in t and "ekle" in t:
            r="Kimin doğum günü ve tarihi nedir efendim? (örn: Annem 15 Mart)"
            self.msg("ANKA",r); self.speak(r); return True

        # ── Çeviri ────────────────────────────────────────────────────────────
        if any(x in t for x in ["çevir","translate","ingilizce söyle","türkçe söyle"]):
            query=t.replace("çevir","").replace("translate","").replace("ingilizce söyle","").replace("türkçe söyle","").strip()
            if query:
                threading.Thread(target=lambda: self._translate(query,t), daemon=True).start()
                return True

        # ── Fıkra ────────────────────────────────────────────────────────────
        if "fıkra anlat" in t or "fıkra söyle" in t:
            threading.Thread(target=self._tell_joke, daemon=True).start()
            return True

        # ── Şiir ─────────────────────────────────────────────────────────────
        if "şiir yaz" in t or "şiir oku" in t:
            topic=t.replace("şiir yaz","").replace("şiir oku","").strip() or "hayat"
            threading.Thread(target=lambda: self._write_poem(topic), daemon=True).start()
            return True

        # ── Film Önerisi ──────────────────────────────────────────────────────
        if any(x in t for x in ["film öner","dizi öner","ne izlesem"]):
            threading.Thread(target=self._recommend_movie, daemon=True).start()
            return True

        # ── Yemek Tarifi ──────────────────────────────────────────────────────
        if any(x in t for x in ["tarif","ne pişirsem","yemek öner"]):
            threading.Thread(target=self._recipe, daemon=True).start()
            return True

        # ── Kalori ───────────────────────────────────────────────────────────
        if "kalori" in t:
            threading.Thread(target=lambda: self._calorie(t), daemon=True).start()
            return True

        # ── Disk Temizleme ────────────────────────────────────────────────────
        if "disk temizle" in t or "geçici dosya" in t:
            subprocess.Popen("cleanmgr", shell=True)
            r="✓ Disk temizleme başlatıldı efendim."; self.msg("ANKA",r); self.speak(r); return True

        # ── Dosya Ara ─────────────────────────────────────────────────────────
        if "dosya ara" in t or "dosyayı bul" in t:
            q=t.replace("dosya ara","").replace("dosyayı bul","").strip()
            if q:
                subprocess.Popen(f'explorer /root,"search-ms:query={q}&crumb=location:C:"', shell=True)
                r=f"✓ '{q}' dosyası aranıyor efendim."; self.msg("ANKA",r); self.speak(r); return True

        return False

    # ── Yardımcı Metodlar ────────────────────────────────────────────────────
    def _get_weather(self):
        try:
            r=requests.get(f"https://wttr.in/{WEATHER_CITY}?format=j1",timeout=5)
            d=r.json()["current_condition"][0]
            temp=d["temp_C"]; desc=d["weatherDesc"][0]["value"]
            feels=d["FeelsLikeC"]; humidity=d["humidity"]
            msg=f"🌤 İstanbul Hava:\n• Sıcaklık: {temp}°C\n• Durum: {desc}\n• Hissedilen: {feels}°C\n• Nem: %{humidity}"
            self.msg("ANKA",msg); self.speak(f"İstanbul'da hava {temp} derece, {desc}. Hissedilen {feels} derece efendim.")
        except: self.msg("ANKA","Hava bilgisi alınamadı.")

    def _get_currency(self):
        try:
            r=requests.get("https://api.exchangerate-api.com/v4/latest/USD",timeout=5)
            d=r.json()["rates"]
            try_rate=d.get("TRY",0); eur_rate=d.get("EUR",0)
            msg=f"💱 Döviz Kurları:\n• 1 USD = {try_rate:.2f} ₺\n• 1 EUR = {try_rate/eur_rate:.2f} ₺"
            self.msg("ANKA",msg); self.speak(f"1 dolar {try_rate:.1f} lira efendim.")
        except: self.msg("ANKA","Döviz bilgisi alınamadı.")

    def _get_crypto(self):
        try:
            r=requests.get("https://api.coinbase.com/v2/prices/BTC-USD/spot",timeout=5)
            btc=float(r.json()["data"]["amount"])
            r2=requests.get("https://api.coinbase.com/v2/prices/ETH-USD/spot",timeout=5)
            eth=float(r2.json()["data"]["amount"])
            msg=f"₿ Kripto:\n• Bitcoin: ${btc:,.0f}\n• Ethereum: ${eth:,.0f}"
            self.msg("ANKA",msg); self.speak(f"Bitcoin {btc:,.0f} dolar, Ethereum {eth:,.0f} dolar efendim.")
        except: self.msg("ANKA","Kripto bilgisi alınamadı.")

    def _get_stocks(self):
        try:
            r=requests.get("https://query1.finance.yahoo.com/v8/finance/chart/XU100.IS",timeout=5)
            d=r.json()
            price=d["chart"]["result"][0]["meta"]["regularMarketPrice"]
            msg=f"📈 BIST 100: {price:,.0f} puan"
            self.msg("ANKA",msg); self.speak(f"BIST 100 şu an {price:,.0f} puan efendim.")
        except: self.msg("ANKA","Borsa bilgisi alınamadı.")

    def _wikipedia(self, query):
        try:
            import wikipedia
            wikipedia.set_lang("tr")
            summary=wikipedia.summary(query, sentences=3)
            self.msg("ANKA",f"📚 {query}:\n{summary}")
            self.speak(summary[:200])
        except: self.msg("ANKA","Wikipedia'da bulunamadı.")

    def _get_news(self):
        try:
            import feedparser
            feed = feedparser.parse("https://www.hurriyet.com.tr/rss/anasayfa")
            articles = feed.entries[:5]
            if articles:
                msg="📰 Günün Haberleri:\n"+"\n".join(f"• {a.title}" for a in articles)
                self.msg("ANKA",msg); self.speak("İşte günün haberleri efendim. "+articles[0].title)
            else:
                self.msg("ANKA","Haber alınamadı.")
        except Exception as e:
            self.msg("ANKA","Haber alınamadı. 'pip install feedparser' kurulu mu kontrol edin.")

    def _speedtest(self):
        try:
            import speedtest
            st=speedtest.Speedtest()
            down=st.download()/1_000_000
            up=st.upload()/1_000_000
            msg=f"📡 İnternet Hızı:\n• İndirme: {down:.1f} Mbps\n• Yükleme: {up:.1f} Mbps"
            self.msg("ANKA",msg); self.speak(f"İndirme hızınız {down:.0f}, yükleme hızınız {up:.0f} megabit efendim.")
        except: self.msg("ANKA","Hız testi için 'pip install speedtest-cli' kurun.")

    def _wifi_password(self):
        try:
            result=subprocess.run(["netsh","wlan","show","profiles"],capture_output=True,text=True,encoding="utf-8")
            profiles=[l.split(":")[1].strip() for l in result.stdout.split("\n") if "Tüm Kullanıcı Profili" in l or "All User Profile" in l]
            passwords=[]
            for p in profiles[:3]:
                r=subprocess.run(["netsh","wlan","show","profile",p,"key=clear"],capture_output=True,text=True,encoding="utf-8")
                for l in r.stdout.split("\n"):
                    if "Anahtar İçeriği" in l or "Key Content" in l:
                        pwd=l.split(":")[1].strip()
                        passwords.append(f"• {p}: {pwd}")
            msg="📶 WiFi Şifreleri:\n"+("\n".join(passwords) if passwords else "Şifre bulunamadı.")
            self.msg("ANKA",msg); self.speak("WiFi şifreleri bulundu efendim.")
        except: self.msg("ANKA","WiFi şifresi alınamadı.")

    def _translate(self, text, original):
        try:
            target="en" if "ingilizce" in original else "tr"
            r=requests.get(f"https://api.mymemory.translated.net/get?q={text}&langpair=tr|{target}",timeout=5)
            translated=r.json()["responseData"]["translatedText"]
            self.msg("ANKA",f"🌍 Çeviri: {translated}")
            self.speak(translated)
        except: self.msg("ANKA","Çeviri yapılamadı.")

    def _tell_joke(self):
        reply=self.ollama.chat("Komik bir Türkçe fıkra anlat. Kısa olsun.")
        self.msg("ANKA",f"😄 {reply}"); self.speak(reply)

    def _write_poem(self, topic):
        reply=self.ollama.chat(f"'{topic}' konusunda kısa güzel bir şiir yaz. 4-6 dize olsun.")
        self.msg("ANKA",f"✍️ {reply}"); self.speak(reply)

    def _recommend_movie(self):
        reply=self.ollama.chat("Bana izlemek için 3 film veya dizi öner. Kısa açıklamayla.")
        self.msg("ANKA",f"🎬 {reply}"); self.speak(reply)

    def _recipe(self):
        reply=self.ollama.chat("Kolay yapılabilen 1 yemek tarifi öner. Malzeme ve yapılışıyla.")
        self.msg("ANKA",f"🍳 {reply}"); self.speak(reply)

    def _calorie(self, text):
        reply=self.ollama.chat(f"Şu yiyeceğin yaklaşık kalori değerini söyle: {text}. Kısa cevap ver.")
        self.msg("ANKA",f"🔥 {reply}"); self.speak(reply)
