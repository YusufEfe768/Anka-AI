# ── ANKA VALORANT KOÇU — Ekran İzleyici + Taktik Sistemi ─────────────────────
# Ekranı analiz eder, taktik verir, skor takibi yapar, agent önerir
# Vanguard ile ÇAKIŞMAZ — sadece ekran okur, oyuna dokunmaz!
try:
    import pyautogui
except ImportError:
    pyautogui=None
import json, os, time, threading, datetime, re, random
import requests
from anka_config import BASE_DIR, USER_NAME

try:
    import pyperclip
except ImportError:
    pyperclip = None

VAL_FILE = os.path.join(BASE_DIR, "anka_valorant.json")

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
# 1. EKRAN ANALİZÖRÜ — Ekranı okur, oyun durumunu anlar
# ═══════════════════════════════════════════════════════════════════════════════
class ScreenAnalyzer:
    """
    Ekranı periyodik olarak yakalar ve analiz eder.
    Vanguard'a DOKUNMAZ — sadece ekranı okur (screenshot).
    """
    def __init__(self, msg_func, speak_func, ollama):
        self.msg    = msg_func
        self.speak  = speak_func
        self.ollama = ollama
        self.running   = False
        self.interval  = 10  # Kaç saniyede bir analiz
        self.last_state = {}
        self.game_active = False

    def _capture(self):
        """Ekran görüntüsü al"""
        try:
            import pyautogui
            screenshot = pyautogui.screenshot()
            return screenshot
        except:
            return None

    def _analyze_screen(self, screenshot):
        """Ekran görüntüsünü analiz et"""
        try:
            import pyautogui
            from PIL import Image
            import io, base64

            # Küçült (daha hızlı analiz için)
            screenshot = screenshot.resize((960, 540))
            buf = io.BytesIO()
            screenshot.save(buf, format='PNG')
            img_b64 = base64.b64encode(buf.getvalue()).decode()

            # Pixel renk analizi ile basit durum tespiti
            width, height = screenshot.size
            pixels = screenshot.load()

            # Skor bölgesi (üst merkez) analizi
            top_center_colors = []
            for x in range(width//2-50, width//2+50):
                for y in range(10, 60):
                    try:
                        r, g, b = pixels[x, y][:3]
                        top_center_colors.append((r, g, b))
                    except: pass

            # Mini map analizi (sağ üst köşe)
            minimap_colors = []
            for x in range(width-200, width-10):
                for y in range(10, 200):
                    try:
                        r, g, b = pixels[x, y][:3]
                        minimap_colors.append((r, g, b))
                    except: pass

            # Renk analizi
            avg_r = sum(c[0] for c in top_center_colors) / max(len(top_center_colors), 1)
            avg_g = sum(c[1] for c in top_center_colors) / max(len(top_center_colors), 1)
            avg_b = sum(c[2] for c in top_center_colors) / max(len(top_center_colors), 1)

            state = {
                "timestamp": datetime.datetime.now().isoformat(),
                "screen_brightness": (avg_r + avg_g + avg_b) / 3,
                "top_color": (avg_r, avg_g, avg_b),
            }

            # Basit durum tespiti (renk tabanlı)
            if avg_r > 180 and avg_g < 80:
                state["alert"] = "red_screen"  # Hasar aldın!
            elif avg_g > 150 and avg_r < 100:
                state["alert"] = "green_screen"  # Spike defuse / round win
            else:
                state["alert"] = "normal"

            return state
        except Exception as e:
            return {"error": str(e), "timestamp": datetime.datetime.now().isoformat()}

    def start(self, interval=10):
        """Ekran izlemeyi başlat"""
        self.running  = True
        self.interval = interval
        threading.Thread(target=self._loop, daemon=True).start()
        self.msg("ANKA",
            f"👁️ EKRAN İZLEME BAŞLADI\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• Her {interval} saniyede analiz\n"
            f"• Vanguard'a dokunmaz ✅\n"
            f"• Sadece ekran okur ✅\n"
            f"'ekran izlemeyi durdur' ile kapat")
        self.speak(f"Ekran izleme başladı, her {interval} saniyede analiz yapacağım efendim.")

    def _loop(self):
        while self.running:
            try:
                screenshot = self._capture()
                if screenshot:
                    state = self._analyze_screen(screenshot)
                    self._react_to_state(state)
                    self.last_state = state
            except: pass
            time.sleep(self.interval)

    def _react_to_state(self, state):
        """Duruma göre tepki ver"""
        alert = state.get("alert", "normal")
        if alert == "red_screen":
            tips = [
                "🔴 Hasar aldın! Mevziye çekil efendim!",
                "🔴 Cover al, heal yok edin!",
                "🔴 Takım arkadaşlarını çağır!",
            ]
            tip = random.choice(tips)
            self.msg("ANKA", tip)
            self.speak(tip)

    def stop(self):
        self.running = False
        self.msg("ANKA","👁️ Ekran izleme durduruldu efendim.")


# ═══════════════════════════════════════════════════════════════════════════════
# 2. TAKTİK ANALİZÖRÜ — Duruma göre taktik üretir
# ═══════════════════════════════════════════════════════════════════════════════
class TacticAnalyzer:
    # Harita bilgileri
    MAPS = {
        "ascent": {
            "sides": ["A Site", "B Site", "Mid"],
            "attack_tips": [
                "Mid'den A'ya orta oyna, B için Catwalk kullan",
                "A Main'den uzun yap, Market'ten destek al",
                "B Main'den hızlı rush, A'da 2 kişi beklet",
            ],
            "defense_tips": [
                "A'da Cubby + Window kontrol et",
                "Mid'i erken kapat, B'ye 3 kişi koy",
                "Retake için Market'i kullan",
            ]
        },
        "bind": {
            "sides": ["A Site", "B Site"],
            "attack_tips": [
                "Teleport'u akıllı kullan, split attack yap",
                "Showers'dan B'ye gir, Hookah'dan destek",
                "A Short + A Long split attack",
            ],
            "defense_tips": [
                "Teleport rotasyon için kritik",
                "B Hookah'ı erken kontrol et",
                "Eco round'da stack B",
            ]
        },
        "haven": {
            "sides": ["A Site", "B Site", "C Site"],
            "attack_tips": [
                "3 site'lı map, mid kontrolü kritik",
                "B kısa al, A + C'ye split",
                "Garage'dan C'ye, Mid Box'tan B'ye",
            ],
            "defense_tips": [
                "Mid'i kapatmadan site savunma",
                "C Garage erken kontrol",
                "A Short'tan agresif oyna",
            ]
        },
        "split": {
            "sides": ["A Site", "B Site", "Mid"],
            "attack_tips": [
                "Mid kontrolü olmadan site alma",
                "Ropes'dan A'ya yukarı çık",
                "B Garage'dan hızlı push",
            ],
            "defense_tips": [
                "Mid Vent erken kontrol et",
                "A Heaven'dan crossfire kur",
                "B'de Garage + Main crossfire",
            ]
        },
        "icebox": {
            "sides": ["A Site", "B Site"],
            "attack_tips": [
                "Snowman'dan A'ya, Mid'den B'ye",
                "Kitchen kontrolü önemli",
                "B Orange + Tube split",
            ],
            "defense_tips": [
                "A Rafters kontrolü kritik",
                "B için Tube + Kitchen crossfire",
                "Mid'i erken kapat",
            ]
        },
        "breeze": {
            "sides": ["A Site", "B Site", "Mid"],
            "attack_tips": [
                "Long distance fight avantajın",
                "A Halls'dan doğrudan gir",
                "Mid kapısını kir, B'ye geç",
            ],
            "defense_tips": [
                "A Pyramids arkasından oyna",
                "B Backsite stack etkili",
                "Mid kontrolü ile rotasyon",
            ]
        },
        "fracture": {
            "sides": ["A Site", "B Site"],
            "attack_tips": [
                "Her iki taraftan saldır (A + B aynı anda)",
                "Rope'dan A'ya hızlı gir",
                "B Arcade + Main split",
            ],
            "defense_tips": [
                "İki taraflı attack'a dikkat",
                "Mid kontrolü kritik",
                "Rotasyon için hazır ol",
            ]
        },
        "lotus": {
            "sides": ["A Site", "B Site", "C Site"],
            "attack_tips": [
                "Dönen kapıları kontrol et",
                "A Stairs + Tree split",
                "C'den B'ye geçiş avantajı",
            ],
            "defense_tips": [
                "Kapı kontrolü çok önemli",
                "B Mid'den rotasyon",
                "C Mound'dan agresif oyna",
            ]
        },
    }

    # Agent rolleri ve ipuçları
    AGENTS = {
        "duelist": {
            "agents": ["Jett","Reyna","Phoenix","Raze","Neon","Yoru","Iso"],
            "role": "Fragman — Saldırıyı sen başlat",
            "tips": [
                "Entry frag atmaktan çekinme, takım seni takip eder",
                "Duel kazan, bekletme",
                "Flanklara dikkat, arkadan gelirler",
                "Eco round'da agresif oynama",
                "Smoke olmadan geniş alanları geçme",
            ]
        },
        "controller": {
            "agents": ["Brimstone","Viper","Omen","Astra","Harbor","Clove"],
            "role": "Kontrolcü — Smoke, bombayı kontrol et",
            "tips": [
                "Smoke'ları doğru yere koy, iletişim kur",
                "Default smoke'ları ezberle",
                "Takımın arkasında kalma, onlarla hareket et",
                "Molotov/Poison ile push'u engelle",
                "Post-plant smoke önemli",
            ]
        },
        "sentinel": {
            "agents": ["Sage","Cypher","Killjoy","Chamber","Deadlock"],
            "role": "Sentinel — Flanku kapat, site tut",
            "tips": [
                "Flanku kapat, trap'leri stratejik koy",
                "Lurk'e dikkat, arkadan gelirler",
                "Site savunmada en güçlü ajansın",
                "Ult'unu doğru round'da kullan",
                "Takımdan ayrı gezme",
            ]
        },
        "initiator": {
            "agents": ["Sova","Breach","Skye","Kay/O","Fade","Gekko"],
            "role": "Başlatıcı — Bilgi topla, push aç",
            "tips": [
                "Önce bilgi topla, sonra gir",
                "Flash'ları takım ile koordine et",
                "Drone/Owl ile site'ı tara",
                "Entry'den önce utility at",
                "Duelist ile koordineli çalış",
            ]
        },
    }

    def __init__(self, ollama, msg_func, speak_func):
        self.ollama = ollama
        self.msg    = msg_func
        self.speak  = speak_func

    def get_map_tactic(self, map_name, side="attack"):
        map_data = self.MAPS.get(map_name.lower())
        if not map_data:
            available = ", ".join(self.MAPS.keys())
            self.msg("ANKA", f"Harita bulunamadı. Mevcut: {available}")
            return
        tips = map_data[f"{side}_tips"]
        tip  = random.choice(tips)
        sites = ", ".join(map_data["sides"])
        r = (f"🗺️ {map_name.capitalize()} — {'Saldırı' if side=='attack' else 'Savunma'}\n"
             f"{'═'*40}\n"
             f"📍 Site'lar: {sites}\n\n"
             f"💡 Taktik:\n{tip}\n\n"
             f"🎯 Tüm taktikler için 'tüm taktikler {map_name}' yaz!")
        self.msg("ANKA", r)
        self.speak(tip[:100])

    def all_tactics(self, map_name):
        map_data = self.MAPS.get(map_name.lower())
        if not map_data:
            self.msg("ANKA","Harita bulunamadı efendim."); return
        r = f"🗺️ {map_name.capitalize()} — TÜM TAKTİKLER\n{'═'*40}\n"
        r += "\n⚔️ SALDIRI:\n"
        for i, tip in enumerate(map_data["attack_tips"], 1):
            r += f"{i}. {tip}\n"
        r += "\n🛡️ SAVUNMA:\n"
        for i, tip in enumerate(map_data["defense_tips"], 1):
            r += f"{i}. {tip}\n"
        self.msg("ANKA", r)

    def agent_advice(self, agent_name):
        agent_name_cap = agent_name.capitalize()
        # Agent rolünü bul
        role_data = None
        role_name = None
        for role, data in self.AGENTS.items():
            if agent_name_cap in data["agents"]:
                role_data = data
                role_name = role
                break
        if not role_data:
            all_agents = []
            for d in self.AGENTS.values():
                all_agents.extend(d["agents"])
            self.msg("ANKA",
                f"'{agent_name}' bulunamadı efendim.\n"
                f"Bilinen agentlar: {', '.join(all_agents)}")
            return
        tip = random.choice(role_data["tips"])
        r = (f"🎭 {agent_name_cap} — {role_data['role']}\n"
             f"{'═'*40}\n"
             f"🎯 Rol: {role_name.capitalize()}\n\n"
             f"💡 İpucu:\n{tip}\n\n"
             f"📋 Takımdaki diğer {'iyi' if role_name=='duelist' else 'uyumlu'} agentlar:\n"
             f"{', '.join([a for a in role_data['agents'] if a != agent_name_cap][:4])}")
        self.msg("ANKA", r)
        self.speak(tip[:120])

    def suggest_agent(self, playstyle, map_name=None):
        """Oyun stiline göre agent öner"""
        playstyle = playstyle.lower()
        suggestions = []
        if any(w in playstyle for w in ["agresif","saldırgan","fragman","kill"]):
            suggestions = [("Jett","duelist","Dash + Bladestorm ile öldür"),
                          ("Reyna","duelist","Kill + Dismiss döngüsü"),
                          ("Neon","duelist","Hız + Sprint avantajı")]
        elif any(w in playstyle for w in ["savunma","tut","site","bekle"]):
            suggestions = [("Killjoy","sentinel","Turret + Alarmbot ile site tut"),
                          ("Cypher","sentinel","Trip + Camera ile bilgi topla"),
                          ("Sage","sentinel","Wall + Heal ile destek")]
        elif any(w in playstyle for w in ["destek","yardım","heal","smoke"]):
            suggestions = [("Sage","sentinel","Heal + Resurrect ile destek"),
                          ("Brimstone","controller","Smoke + Ult ile kontrol"),
                          ("Skye","initiator","Flash + Heal ile açılım")]
        elif any(w in playstyle for w in ["bilgi","keşif","intel","drone"]):
            suggestions = [("Sova","initiator","Drone + Owl ile harita tara"),
                          ("Fade","initiator","Haunt + Seize ile bilgi"),
                          ("Cypher","sentinel","Camera + Trip ile kontrol")]
        else:
            suggestions = [("Brimstone","controller","Kolay smoke, iyi başlangıç"),
                          ("Sage","sentinel","Heal + Resurrect, takıma faydalı"),
                          ("Sova","initiator","Drone ile güvenli keşif")]
        r = f"🎭 AGENT ÖNERİSİ\n{'═'*35}\n"
        for agent, role, reason in suggestions:
            r += f"\n⭐ {agent} ({role.capitalize()})\n   {reason}\n"
        self.msg("ANKA", r)
        self.speak(f"{suggestions[0][0]} oynamanı öneririm efendim!")

    def economy_advice(self, money, team_money=None):
        """Para durumuna göre ekonomi tavsiyesi"""
        if money >= 7000:
            rec = "Full Buy"
            items = "Vandal/Phantom + Armor + Utility"
            tip = "Full ekipmanla oyna, utility kullanmaktan çekinme!"
        elif money >= 4000:
            rec = "Half Buy"
            items = "Spectre/Bulldog + Light Armor"
            tip = "Yarı ekipman, agresif oynama — position al!"
        elif money >= 2000:
            rec = "Eco"
            items = "Ghost/Classic + Save"
            tip = "Eco round — bilgi topla, save yap, riski minimize et!"
        else:
            rec = "Full Save"
            items = "Sadece default silah"
            tip = "Full save! Positional play yap, kill almaya çalış ama risk alma!"
        r = (f"💰 EKONOMİ TAVSİYESİ\n{'═'*35}\n"
             f"• Cüzdan: {money:,} ₺\n"
             f"• Öneri: {rec}\n"
             f"• Al: {items}\n\n"
             f"💡 {tip}")
        if team_money:
            avg = team_money // 5
            r += f"\n\n👥 Takım Ortalaması: {avg:,} — "
            r += "Takımla birlikte al!" if avg >= 4000 else "Takım eco yapıyor, sen de yap!"
        self.msg("ANKA", r)
        self.speak(tip[:120])

    def ai_tactic(self, situation):
        """AI ile anlık taktik üret"""
        def _tactic():
            r = self.ollama.chat(
                f"Valorant durumu: {situation}\n\n"
                f"Kısa, uygulanabilir taktik ver. Maksimum 3 adım.",
                system_override="Valorant koçu. Pratik taktikler ver.")
            self.msg("ANKA", f"🎯 AI Taktik:\n{r}")
            self.speak(r[:150])
        threading.Thread(target=_tactic, daemon=True).start()


# ═══════════════════════════════════════════════════════════════════════════════
# 3. SKOR TAKİPÇİSİ — Maç istatistikleri
# ═══════════════════════════════════════════════════════════════════════════════
class ScoreTracker:
    def __init__(self, msg_func, speak_func):
        self.msg   = msg_func
        self.speak = speak_func
        self.data  = _load(VAL_FILE, {
            "matches": [], "current_match": None,
            "stats": {"kills":0,"deaths":0,"assists":0,"wins":0,"losses":0}
        })

    def start_match(self, map_name, agent, side="attack"):
        self.data["current_match"] = {
            "map": map_name, "agent": agent, "side": side,
            "kills": 0, "deaths": 0, "assists": 0,
            "rounds_won": 0, "rounds_lost": 0,
            "start": datetime.datetime.now().isoformat(),
            "rounds": []
        }
        _save(VAL_FILE, self.data)
        r = (f"🎮 MAÇ BAŞLADI!\n{'═'*30}\n"
             f"• Harita: {map_name.capitalize()}\n"
             f"• Agent: {agent.capitalize()}\n"
             f"• Başlangıç: {'⚔️ Saldırı' if side=='attack' else '🛡️ Savunma'}\n\n"
             f"💡 'kill', 'death', 'assist' komutlarıyla takip et!")
        self.msg("ANKA", r)
        self.speak(f"{map_name} haritasında {agent} ile maç başladı efendim!")

    def log_kill(self, count=1, weapon="", headshot=False):
        if not self.data["current_match"]:
            self.msg("ANKA","Önce 'maç başlat [harita] [agent]' komutu kullan efendim."); return
        self.data["current_match"]["kills"] += count
        self.data["stats"]["kills"] += count
        _save(VAL_FILE, self.data)
        kills = self.data["current_match"]["kills"]
        hs_txt = " 🎯 HEADSHOT!" if headshot else ""
        weapon_txt = f" ({weapon})" if weapon else ""
        r = f"💀 Kill!{weapon_txt}{hs_txt} — Bu maç: {kills} kill"
        self.msg("ANKA", r)
        if kills in [5,10,15,20]:
            self.speak(f"İnanılmaz! {kills} kill efendim! Devam et!")
        elif headshot:
            self.speak("Headshot! Mükemmel aim efendim!")

    def log_death(self, count=1):
        if not self.data["current_match"]: return
        self.data["current_match"]["deaths"] += count
        self.data["stats"]["deaths"] += count
        _save(VAL_FILE, self.data)
        deaths = self.data["current_match"]["deaths"]
        kills  = self.data["current_match"]["kills"]
        kd = kills/deaths if deaths > 0 else kills
        tips = [
            "Pozisyonunu değiştir efendim! Aynı yerden oynama.",
            "Utility kullan, açık girme!",
            "Takımla birlikte hareket et!",
            "Peek'lemeden önce bilgi topla!",
        ]
        r = (f"💀 Death. Bu maç: {kills}K/{deaths}D (K/D: {kd:.1f})\n"
             f"💡 {random.choice(tips)}")
        self.msg("ANKA", r)

    def log_assist(self, count=1):
        if not self.data["current_match"]: return
        self.data["current_match"]["assists"] += count
        self.data["stats"]["assists"] += count
        _save(VAL_FILE, self.data)
        r = f"🤝 Assist! Bu maç: {self.data['current_match']['assists']} assist"
        self.msg("ANKA", r)

    def round_won(self):
        if not self.data["current_match"]: return
        self.data["current_match"]["rounds_won"] += 1
        _save(VAL_FILE, self.data)
        w = self.data["current_match"]["rounds_won"]
        l = self.data["current_match"]["rounds_lost"]
        r = f"✅ Round Kazanıldı! {w} - {l}"
        self.msg("ANKA", r)
        if w == 13:
            self.speak("MAÇ KAZANILDI! Harika oyun efendim!")

    def round_lost(self):
        if not self.data["current_match"]: return
        self.data["current_match"]["rounds_lost"] += 1
        _save(VAL_FILE, self.data)
        w = self.data["current_match"]["rounds_won"]
        l = self.data["current_match"]["rounds_lost"]
        tips = [
            "Strateji değiştirin, aynı şeyi tekrarlama!",
            "Utility kullanımını artırın!",
            "Daha fazla iletişim kurun takımla!",
        ]
        r = f"❌ Round Kaybedildi. {w} - {l}\n💡 {random.choice(tips)}"
        self.msg("ANKA", r)

    def end_match(self, result="win"):
        if not self.data["current_match"]:
            self.msg("ANKA","Aktif maç yok efendim."); return
        match = self.data["current_match"]
        match["result"] = result
        match["end"] = datetime.datetime.now().isoformat()
        # İstatistikler
        deaths = match["deaths"]
        kills  = match["kills"]
        kd = kills/deaths if deaths > 0 else kills
        acs_estimate = (kills * 150 + match["assists"] * 50) // max(match["rounds_won"]+match["rounds_lost"],1)
        if result == "win":
            self.data["stats"]["wins"] += 1
            result_emoji = "🏆 ZAFER!"
        else:
            self.data["stats"]["losses"] += 1
            result_emoji = "💔 Mağlubiyet"
        self.data["matches"].append(match)
        if len(self.data["matches"]) > 50:
            self.data["matches"] = self.data["matches"][-50:]
        self.data["current_match"] = None
        _save(VAL_FILE, self.data)
        # Performans değerlendirmesi
        if kd >= 2.0: perf = "🔥 Müthiş performans!"
        elif kd >= 1.5: perf = "✅ İyi performans!"
        elif kd >= 1.0: perf = "👍 Dengeli oyun"
        else: perf = "📚 Geliştirme gereken alanlar var"
        r = (f"{result_emoji}\n{'═'*35}\n"
             f"• Harita: {match['map'].capitalize()}\n"
             f"• Agent: {match['agent'].capitalize()}\n"
             f"• Skor: {match['rounds_won']} - {match['rounds_lost']}\n"
             f"• K/D/A: {kills}/{deaths}/{match['assists']}\n"
             f"• K/D: {kd:.2f}\n"
             f"• ACS (tahmini): {acs_estimate}\n\n"
             f"{perf}")
        self.msg("ANKA", r)
        self.speak(r[:150])

    def career_stats(self):
        stats  = self.data["stats"]
        matches= self.data["matches"]
        total  = stats["wins"] + stats["losses"]
        winrate= (stats["wins"]/total*100) if total > 0 else 0
        kd_all = stats["kills"]/max(stats["deaths"],1)
        r = (f"📊 KARİYER İSTATİSTİKLERİ\n{'═'*35}\n"
             f"• Toplam Maç: {total}\n"
             f"• Galibiyet: {stats['wins']} (%{winrate:.0f})\n"
             f"• Mağlubiyet: {stats['losses']}\n"
             f"• Toplam Kill: {stats['kills']:,}\n"
             f"• Toplam Death: {stats['deaths']:,}\n"
             f"• Toplam Assist: {stats['assists']:,}\n"
             f"• Genel K/D: {kd_all:.2f}\n")
        if matches:
            last5 = matches[-5:]
            r += f"\n📋 Son {len(last5)} Maç:\n"
            for m in reversed(last5):
                res = "✅" if m.get("result")=="win" else "❌"
                r += (f"{res} {m['map'].capitalize()} ({m['agent'].capitalize()}) "
                     f"{m['rounds_won']}-{m['rounds_lost']} "
                     f"{m['kills']}K/{m['deaths']}D\n")
        self.msg("ANKA", r)

    def current_match_status(self):
        match = self.data["current_match"]
        if not match:
            self.msg("ANKA","Aktif maç yok efendim. 'maç başlat' ile başlat."); return
        kills  = match["kills"]
        deaths = match["deaths"]
        assists= match["assists"]
        kd = kills/deaths if deaths > 0 else kills
        r = (f"🎮 MEVCUT MAÇ\n{'═'*30}\n"
             f"• Harita: {match['map'].capitalize()}\n"
             f"• Agent: {match['agent'].capitalize()}\n"
             f"• Skor: {match['rounds_won']} - {match['rounds_lost']}\n"
             f"• K/D/A: {kills}/{deaths}/{assists}\n"
             f"• K/D: {kd:.2f}")
        self.msg("ANKA", r)


# ═══════════════════════════════════════════════════════════════════════════════
# 4. KOMPOZİSYON ANALİZÖRÜ — Takım oluşturma
# ═══════════════════════════════════════════════════════════════════════════════
class CompositionAnalyzer:
    # Harita-agent uyum matrisi
    AGENT_MAP_SYNERGY = {
        "viper": ["Icebox","Breeze","Pearl"],
        "brimstone": ["Ascent","Bind","Haven"],
        "omen": ["Haven","Split","Fracture"],
        "astra": ["Bind","Pearl","Lotus"],
        "sova": ["Icebox","Breeze","Ascent"],
        "fade": ["Haven","Pearl","Lotus"],
        "jett": ["Breeze","Icebox","Ascent"],
        "chamber": ["Breeze","Pearl","Haven"],
        "killjoy": ["Ascent","Bind","Icebox"],
        "cypher": ["Bind","Haven","Pearl"],
    }

    def __init__(self, ollama, msg_func, speak_func):
        self.ollama = ollama
        self.msg    = msg_func
        self.speak  = speak_func

    def analyze_composition(self, agents, map_name=None):
        """Takım kompozisyonunu analiz et"""
        roles = {"duelist":0,"controller":0,"sentinel":0,"initiator":0}
        duelist_agents   = ["Jett","Reyna","Phoenix","Raze","Neon","Yoru","Iso"]
        controller_agents= ["Brimstone","Viper","Omen","Astra","Harbor","Clove"]
        sentinel_agents  = ["Sage","Cypher","Killjoy","Chamber","Deadlock"]
        initiator_agents = ["Sova","Breach","Skye","Kay/O","Fade","Gekko"]

        for agent in agents:
            a = agent.capitalize()
            if a in duelist_agents:    roles["duelist"] += 1
            elif a in controller_agents: roles["controller"] += 1
            elif a in sentinel_agents:   roles["sentinel"] += 1
            elif a in initiator_agents:  roles["initiator"] += 1

        issues = []
        if roles["controller"] == 0: issues.append("❌ Smoke yok! Controller alın")
        if roles["sentinel"] == 0:   issues.append("❌ Flank koruması yok! Sentinel alın")
        if roles["initiator"] == 0:  issues.append("❌ Entry yok! Initiator alın")
        if roles["duelist"] == 0:    issues.append("⚠️ Fragman yok")
        if roles["duelist"] >= 3:    issues.append("⚠️ Çok fazla duelist — support az")

        # Map uyumu
        map_synergy = []
        if map_name:
            for agent in agents:
                synergy_maps = self.AGENT_MAP_SYNERGY.get(agent.lower(), [])
                if map_name.capitalize() in synergy_maps:
                    map_synergy.append(f"✅ {agent.capitalize()} bu haritada güçlü")

        score = 10 - len(issues) * 2 + len(map_synergy)
        score = max(1, min(10, score))

        r = (f"👥 KOMPOZİSYON ANALİZİ\n{'═'*35}\n"
             f"Agentlar: {', '.join(a.capitalize() for a in agents)}\n"
             f"{'Harita: ' + map_name.capitalize() if map_name else ''}\n\n"
             f"📊 Roller:\n"
             f"• Duelist: {roles['duelist']} | Controller: {roles['controller']}\n"
             f"• Sentinel: {roles['sentinel']} | Initiator: {roles['initiator']}\n\n"
             f"Uyum Puanı: {score}/10\n")

        if issues:
            r += f"\n⚠️ Sorunlar:\n" + "\n".join(issues)
        if map_synergy:
            r += f"\n\n🗺️ Harita Sinerjisi:\n" + "\n".join(map_synergy)
        if not issues:
            r += "\n✅ Kompozisyon dengeli!"

        self.msg("ANKA", r)
        self.speak(f"Kompozisyon puanı {score} üzerinden 10 efendim!")

    def suggest_composition(self, map_name, playstyle="balanced"):
        """Harita ve stile göre kompozisyon öner"""
        compositions = {
            "ascent": {
                "aggressive": ["Jett","Brimstone","Sova","Killjoy","Reyna"],
                "balanced":   ["Jett","Brimstone","Sova","Killjoy","Sage"],
                "defensive":  ["Chamber","Brimstone","Fade","Killjoy","Sage"]
            },
            "bind": {
                "aggressive": ["Raze","Brimstone","Skye","Cypher","Reyna"],
                "balanced":   ["Raze","Brimstone","Skye","Cypher","Sage"],
                "defensive":  ["Chamber","Viper","Fade","Cypher","Sage"]
            },
            "haven": {
                "aggressive": ["Jett","Omen","Breach","Cypher","Reyna"],
                "balanced":   ["Jett","Omen","Breach","Cypher","Sage"],
                "defensive":  ["Chamber","Omen","Fade","Killjoy","Sage"]
            },
        }
        comp = compositions.get(map_name.lower(), {}).get(playstyle,
            ["Jett","Brimstone","Sova","Killjoy","Sage"])
        r = (f"🎯 ÖNERİLEN KOMPOZİSYON\n{'═'*35}\n"
             f"• Harita: {map_name.capitalize()}\n"
             f"• Stil: {playstyle.capitalize()}\n\n"
             f"👥 Takım:\n"
             + "\n".join(f"• {a}" for a in comp))
        self.msg("ANKA", r)
        self.speak(f"{map_name} için önerilen kompozisyon hazır efendim!")


# ═══════════════════════════════════════════════════════════════════════════════
# KOMUT İŞLEYİCİ
# ═══════════════════════════════════════════════════════════════════════════════
class ValorantCommandProcessor:
    def __init__(self, speak_func, msg_func, ollama):
        self.speak   = speak_func
        self.msg     = msg_func
        self.ollama  = ollama
        self.screen  = ScreenAnalyzer(msg_func, speak_func, ollama)
        self.tactic  = TacticAnalyzer(ollama, msg_func, speak_func)
        self.tracker = ScoreTracker(msg_func, speak_func)
        self.comp    = CompositionAnalyzer(ollama, msg_func, speak_func)

    def process(self, text):
        t = text.lower().strip()

        # ── Ekran İzleme ──────────────────────────────────────────────────────
        if "ekran izle" in t or "valorant izle" in t:
            m = re.search(r'(\d+)', t)
            interval = int(m.group(1)) if m else 10
            self.screen.start(interval); return True
        if "ekran izlemeyi durdur" in t:
            self.screen.stop(); return True

        # ── Taktik ────────────────────────────────────────────────────────────
        if "taktik" in t and ("saldırı" in t or "attack" in t):
            for map_name in self.tactic.MAPS:
                if map_name in t:
                    self.tactic.get_map_tactic(map_name, "attack"); return True
            self.tactic.get_map_tactic("ascent", "attack"); return True

        if "taktik" in t and ("savunma" in t or "defend" in t or "defense" in t):
            for map_name in self.tactic.MAPS:
                if map_name in t:
                    self.tactic.get_map_tactic(map_name, "defense"); return True
            self.tactic.get_map_tactic("ascent", "defense"); return True

        if "tüm taktikler" in t:
            for map_name in self.tactic.MAPS:
                if map_name in t:
                    self.tactic.all_tactics(map_name); return True
            return True

        if "ai taktik" in t:
            situation = t.replace("ai taktik","").strip()
            if situation: self.tactic.ai_tactic(situation); return True

        # ── Agent ─────────────────────────────────────────────────────────────
        if "agent tavsiyesi" in t or "agent öner" in t:
            playstyle = t.replace("agent tavsiyesi","").replace("agent öner","").strip()
            if playstyle: self.tactic.suggest_agent(playstyle)
            else: self.tactic.suggest_agent("balanced")
            return True

        if "agent ipucu" in t or "agent tüyosu" in t:
            agent = t.replace("agent ipucu","").replace("agent tüyosu","").strip()
            if agent: self.tactic.agent_advice(agent); return True

        # ── Ekonomi ───────────────────────────────────────────────────────────
        if "ekonomi" in t or "para tavsiyesi" in t or "ne alsam" in t:
            m = re.search(r'(\d{3,5})', t)
            if m:
                self.tactic.economy_advice(int(m.group(1))); return True
            self.msg("ANKA","Format: 'ekonomi 3800' efendim.")
            return True

        # ── Skor Takibi ───────────────────────────────────────────────────────
        if "maç başlat" in t or "oyun başlat" in t:
            words = t.replace("maç başlat","").replace("oyun başlat","").strip().split()
            map_name = "ascent"
            agent    = "jett"
            side     = "attack"
            for w in words:
                if w in self.tactic.MAPS: map_name = w
                if w in ["attack","saldırı"]: side = "attack"
                if w in ["defense","defend","savunma"]: side = "defense"
                for role_data in self.tactic.AGENTS.values():
                    if w.capitalize() in role_data["agents"]:
                        agent = w
            self.tracker.start_match(map_name, agent, side); return True

        if t.strip() in ["kill","öldürdüm","kill aldım","k"]:
            headshot = "hs" in t or "headshot" in t
            self.tracker.log_kill(headshot=headshot); return True
        if re.match(r'^(\d+)\s*kill', t):
            m = re.search(r'(\d+)', t)
            self.tracker.log_kill(int(m.group(1))); return True
        if t.strip() in ["öldüm","death","dead","d"]:
            self.tracker.log_death(); return True
        if t.strip() in ["assist","yardım ettim","a"]:
            self.tracker.log_assist(); return True
        if "round kazandık" in t or "round win" in t:
            self.tracker.round_won(); return True
        if "round kaybettik" in t or "round loss" in t:
            self.tracker.round_lost(); return True
        if "maç bitti" in t or "oyun bitti" in t:
            result = "win" if any(w in t for w in ["kazandık","win","zafer"]) else "loss"
            self.tracker.end_match(result); return True
        if "maç durumu" in t or "kaç kill" in t:
            self.tracker.current_match_status(); return True
        if "kariyer istatistik" in t or "genel istatistik" in t:
            self.tracker.career_stats(); return True

        # ── Kompozisyon ───────────────────────────────────────────────────────
        if "kompozisyon analiz" in t or "takım analiz" in t:
            agents = re.findall(r'[A-Z][a-z]+', text)
            map_m  = None
            for map_name in self.tactic.MAPS:
                if map_name in t: map_m = map_name; break
            if agents: self.comp.analyze_composition(agents, map_m); return True

        if "kompozisyon öner" in t or "takım öner" in t:
            map_m = "ascent"
            for map_name in self.tactic.MAPS:
                if map_name in t: map_m = map_name; break
            style = "aggressive" if "agresif" in t else "defensive" if "savunma" in t else "balanced"
            self.comp.suggest_composition(map_m, style); return True

        # ── Yardım ────────────────────────────────────────────────────────────
        if "valorant yardım" in t or "val yardım" in t:
            r = (
                "🎮 ANKA VALORANT KOÇU\n"
                "═══════════════════════\n\n"
                "👁️ EKRAN İZLEME:\n"
                "• 'valorant izle' → Ekranı analiz et\n"
                "• 'valorant izle 5' → 5sn'de bir\n"
                "• 'ekran izlemeyi durdur'\n\n"
                "🗺️ TAKTİK:\n"
                "• 'taktik saldırı ascent'\n"
                "• 'taktik savunma bind'\n"
                "• 'tüm taktikler haven'\n"
                "• 'ai taktik [durum]'\n\n"
                "🎭 AGENT:\n"
                "• 'agent öner agresif'\n"
                "• 'agent ipucu Jett'\n"
                "• 'agent öner savunma'\n\n"
                "💰 EKONOMİ:\n"
                "• 'ekonomi 3800'\n"
                "• 'ne alsam 2400'\n\n"
                "📊 SKOR TAKİBİ:\n"
                "• 'maç başlat ascent Jett saldırı'\n"
                "• 'kill' / 'öldüm' / 'assist'\n"
                "• 'round kazandık' / 'kaybettik'\n"
                "• 'maç bitti kazandık'\n"
                "• 'kariyer istatistik'\n\n"
                "👥 KOMPOZİSYON:\n"
                "• 'kompozisyon analiz Jett Brimstone Sova'\n"
                "• 'kompozisyon öner ascent agresif'\n\n"
                "Haritalar: ascent, bind, haven, split,\n"
                "icebox, breeze, fracture, lotus"
            )
            self.msg("ANKA", r)
            self.speak("Valorant koçu rehberi hazırlandı efendim.")
            return True

        return False
