# ── ANKA WOW — Şaşırtıcı Yeni Özellikler ────────────────────────────────────
# Gerçekten kimsenin beklemediği, akıl almaz düzeyde özellikler
try:
    import pyautogui
except ImportError:
    pyautogui=None
import json, os, time, threading, datetime, subprocess, webbrowser, re
import requests, random, math, psutil
from anka_config import BASE_DIR, USER_NAME

WOW_FILE = os.path.join(BASE_DIR, "anka_wow.json")

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
# 1. ANKA DEDEKTÖR — Bilgisayarda ne değişti otomatik söylesin
# ═══════════════════════════════════════════════════════════════════════════════
class ChangeDetector:
    """Bilgisayardaki değişiklikleri otomatik tespit eder"""
    def __init__(self, speak_func, msg_func):
        self.speak = speak_func
        self.msg = msg_func
        self.state_file = os.path.join(BASE_DIR, "anka_state.json")
        self.prev_state = _load(self.state_file, {})
        self.running = True
        threading.Thread(target=self._loop, daemon=True).start()

    def _get_state(self):
        state = {}
        # USB cihazlar
        try:
            result = subprocess.run(
                ["powershell","-Command","Get-PnpDevice -PresentOnly | Select Name | ConvertTo-Json"],
                capture_output=True, text=True, timeout=5)
            if result.stdout:
                data = json.loads(result.stdout)
                if isinstance(data, list):
                    state["devices"] = [d.get("Name","") for d in data[:20]]
        except: pass
        # Aktif ağ bağlantısı sayısı
        try:
            state["connections"] = len(psutil.net_connections())
        except: pass
        # Çalışan program sayısı
        try:
            state["processes"] = len(list(psutil.process_iter()))
        except: pass
        return state

    def _loop(self):
        time.sleep(20)
        while self.running:
            try:
                current = self._get_state()
                if self.prev_state:
                    # Yeni USB cihaz takıldı mı?
                    prev_devs = set(self.prev_state.get("devices",[]))
                    curr_devs = set(current.get("devices",[]))
                    new_devs = curr_devs - prev_devs
                    removed_devs = prev_devs - curr_devs
                    if new_devs:
                        r = f"🔌 Yeni cihaz bağlandı: {list(new_devs)[0][:40]}"
                        self.msg("ANKA", r)
                    if removed_devs:
                        r = f"🔌 Cihaz çıkarıldı: {list(removed_devs)[0][:40]}"
                        self.msg("ANKA", r)
                    # Bağlantı ani artışı
                    prev_conn = self.prev_state.get("connections", 0)
                    curr_conn = current.get("connections", 0)
                    if curr_conn - prev_conn > 20:
                        self.msg("ANKA", f"⚠️ Ani ağ bağlantısı artışı: {curr_conn} bağlantı!")
                self.prev_state = current
                _save(self.state_file, current)
            except: pass
            time.sleep(60)

    def stop(self): self.running = False


# ═══════════════════════════════════════════════════════════════════════════════
# 2. ANKA HAFIZA PALASİ — Sonsuz bağlantılı hafıza
# ═══════════════════════════════════════════════════════════════════════════════
class MemoryPalace:
    """
    Konuları birbirine bağlayan hafıza sistemi.
    'matematik' → 'türev' → 'fizik' → 'kuvvet' gibi
    """
    def __init__(self, speak_func, msg_func):
        self.speak = speak_func
        self.msg = msg_func
        self.palace_file = os.path.join(BASE_DIR, "anka_palace.json")
        self.nodes = _load(self.palace_file, {})

    def add_node(self, topic, content, related=[]):
        self.nodes[topic.lower()] = {
            "topic": topic,
            "content": content,
            "related": [r.lower() for r in related],
            "added": datetime.datetime.now().isoformat(),
            "access_count": 0
        }
        # İlişkili node'lara da bağla
        for rel in related:
            rel_l = rel.lower()
            if rel_l in self.nodes:
                if topic.lower() not in self.nodes[rel_l]["related"]:
                    self.nodes[rel_l]["related"].append(topic.lower())
        _save(self.palace_file, self.nodes)
        r = f"🏛️ '{topic}' hafıza sarayına eklendi. Bağlantılar: {', '.join(related) if related else 'yok'}"
        self.msg("ANKA", r); self.speak(r)

    def recall(self, topic):
        node = self.nodes.get(topic.lower())
        if not node:
            # Benzer konuları ara
            similar = [k for k in self.nodes.keys() if topic.lower() in k or k in topic.lower()]
            if similar:
                node = self.nodes[similar[0]]
            else:
                self.msg("ANKA", f"'{topic}' hafıza sarayında bulunamadı efendim.")
                return
        node["access_count"] += 1
        _save(self.palace_file, self.nodes)
        r = f"🏛️ {node['topic']}:\n{node['content']}\n\n🔗 Bağlantılar: {', '.join(node['related']) or 'yok'}"
        self.msg("ANKA", r)

    def explore(self, start_topic, depth=2):
        """Konudan konuya giderek bilgiyi keşfet"""
        visited = []
        current = start_topic.lower()
        r = f"🗺️ Hafıza Yolculuğu: {start_topic}\n{'═'*30}\n"
        for _ in range(depth + 1):
            if current in self.nodes and current not in visited:
                node = self.nodes[current]
                visited.append(current)
                r += f"\n📍 {node['topic']}:\n{node['content'][:100]}...\n"
                if node["related"] and node["related"][0] not in visited:
                    current = node["related"][0]
                else:
                    break
        self.msg("ANKA", r); self.speak("Hafıza yolculuğu tamamlandı efendim.")

    def get_all_topics(self):
        return list(self.nodes.keys())


# ═══════════════════════════════════════════════════════════════════════════════
# 3. ANKA TAHMİN USTASI — Seni öğrenip tahmin eder
# ═══════════════════════════════════════════════════════════════════════════════
class BehaviorPredictor:
    """
    Kullanıcının alışkanlıklarını öğrenir.
    Her sabah 8'de hava soruyor → otomatik gönder!
    """
    def __init__(self, speak_func, msg_func):
        self.speak = speak_func
        self.msg = msg_func
        self.predict_file = os.path.join(BASE_DIR, "anka_predict.json")
        self.data = _load(self.predict_file, {
            "hourly_commands": {},
            "daily_commands": {},
            "sequences": {},
            "auto_triggers": {}
        })
        self.running = True
        threading.Thread(target=self._auto_loop, daemon=True).start()

    def log(self, command):
        hour = str(datetime.datetime.now().hour)
        day = datetime.datetime.now().strftime("%A")
        cmd = command.lower()[:30]
        # Saatlik kayıt
        if hour not in self.data["hourly_commands"]:
            self.data["hourly_commands"][hour] = {}
        self.data["hourly_commands"][hour][cmd] = \
            self.data["hourly_commands"][hour].get(cmd, 0) + 1
        # Günlük kayıt
        if day not in self.data["daily_commands"]:
            self.data["daily_commands"][day] = {}
        self.data["daily_commands"][day][cmd] = \
            self.data["daily_commands"][day].get(cmd, 0) + 1
        _save(self.predict_file, self.data)

    def get_predictions(self):
        hour = str(datetime.datetime.now().hour)
        hourly = self.data["hourly_commands"].get(hour, {})
        if not hourly: return []
        sorted_cmds = sorted(hourly.items(), key=lambda x: -x[1])
        return [cmd for cmd, count in sorted_cmds[:3] if count >= 3]

    def set_auto_trigger(self, hour, command, days="all"):
        self.data["auto_triggers"][str(hour)] = {
            "command": command, "days": days,
            "last_triggered": None
        }
        _save(self.predict_file, self.data)
        r = f"⚡ Otomatik tetikleyici kuruldu: Saat {hour}:00 → '{command}'"
        self.msg("ANKA", r); self.speak(r)

    def _auto_loop(self):
        time.sleep(30)
        while self.running:
            try:
                now = datetime.datetime.now()
                hour = str(now.hour)
                today = now.date().isoformat()
                for h, trigger in self.data["auto_triggers"].items():
                    if h == hour and trigger.get("last_triggered") != today:
                        if now.minute == 0:
                            trigger["last_triggered"] = today
                            _save(self.predict_file, self.data)
                            self.msg("ANKA",
                                f"⚡ Otomatik: {trigger['command']}")
            except: pass
            time.sleep(60)

    def show_predictions(self):
        preds = self.get_predictions()
        if preds:
            r = f"🔮 Bu saatte genellikle şunları soruyorsunuz:\n"
            r += "\n".join(f"• {p}" for p in preds)
        else:
            r = "Henüz yeterli davranış verisi yok efendim."
        self.msg("ANKA", r); self.speak(r)

    def stop(self): self.running = False


# ═══════════════════════════════════════════════════════════════════════════════
# 4. ANKA DEDEKTÖR PLUS — Sahte haber, doğruluk analizi
# ═══════════════════════════════════════════════════════════════════════════════
class TruthAnalyzer:
    """Metnin güvenilirliğini analiz eder"""
    def __init__(self, ollama, speak_func, msg_func):
        self.ollama = ollama
        self.speak = speak_func
        self.msg = msg_func

    def analyze_credibility(self, text):
        def _a():
            # Şüpheli kelimeler
            clickbait = ["şok","inanamayacaksınız","herkes bunu","gizlenen gerçek",
                        "inanılmaz","bir gecede","anında","kesin","garantili"]
            score = 100
            found = []
            for word in clickbait:
                if word in text.lower():
                    score -= 15
                    found.append(word)
            # Kaynak kontrolü
            has_source = any(w in text.lower() for w in ["kaynak","araştırma","bilim","üniversite"])
            if has_source: score += 10
            score = max(0, min(100, score))
            emoji = "✅" if score > 70 else "⚠️" if score > 40 else "🚨"
            r = (f"{emoji} GÜVENİLİRLİK ANALİZİ\n"
                 f"{'═'*30}\n"
                 f"• Skor: {score}/100\n"
                 f"• Seviye: {'Güvenilir' if score>70 else 'Şüpheli' if score>40 else 'Güvenilmez'}\n")
            if found:
                r += f"• Dikkat: {', '.join(found[:3])}\n"
            r += f"\n💡 {'Güvenilir görünüyor.' if score>70 else 'Dikkatli olun, kaynağı doğrulayın!'}"
            self.msg("ANKA", r); self.speak(f"Güvenilirlik skoru {score} efendim.")
        threading.Thread(target=_a, daemon=True).start()

    def fact_check_quick(self, claim):
        def _f():
            # DuckDuckGo'da ara
            try:
                r = requests.get(
                    f"https://api.duckduckgo.com/?q={claim}&format=json", timeout=5)
                data = r.json()
                abstract = data.get("Abstract","")
                if abstract:
                    result = self.ollama.chat(
                        f"İddia: '{claim}'\nBulunan bilgi: {abstract}\n"
                        f"Bu iddia doğru mu? Kısa değerlendir.",
                        system_override="Gerçek kontrolcü. Nesnel değerlendir.")
                    self.msg("ANKA", f"🔍 Hızlı Doğrulama:\n{result}")
                else:
                    self.msg("ANKA", f"'{claim}' için yeterli bilgi bulunamadı efendim.")
            except:
                self.msg("ANKA", "Doğrulama yapılamadı efendim.")
        threading.Thread(target=_f, daemon=True).start()


# ═══════════════════════════════════════════════════════════════════════════════
# 5. ANKA SIHIRBAZ — Klavye kısayol makro sistemi
# ═══════════════════════════════════════════════════════════════════════════════
class KeyboardWizard:
    """Ses komutuyla klavye makroları çalıştır"""
    def __init__(self, speak_func, msg_func):
        self.speak = speak_func
        self.msg = msg_func
        self.macros_file = os.path.join(BASE_DIR, "anka_keyboard.json")
        self.macros = _load(self.macros_file, {
            "kopyala": "ctrl+c",
            "yapıştır": "ctrl+v",
            "geri al": "ctrl+z",
            "kaydet": "ctrl+s",
            "yeni sekme": "ctrl+t",
            "sekmeyi kapat": "ctrl+w",
            "tam ekran": "f11",
            "ekran görüntüsü": "win+shift+s",
            "görev yöneticisi": "ctrl+shift+esc",
            "masaüstü": "win+d",
        })

    def execute(self, name):
        macro = self.macros.get(name.lower())
        if macro:
            try:
                keys = macro.split("+")
                pyautogui.hotkey(*keys)
                r = f"⌨️ '{name}' çalıştırıldı: {macro}"
                self.msg("ANKA", r)
                return True
            except Exception as e:
                self.msg("ANKA", f"Hata: {e}")
        return False

    def add_macro(self, name, keys):
        self.macros[name.lower()] = keys
        _save(self.macros_file, self.macros)
        r = f"✓ '{name}' makrosu eklendi: {keys}"
        self.msg("ANKA", r); self.speak(r)

    def list_macros(self):
        r = f"⌨️ Klavye Makroları ({len(self.macros)}):\n"
        r += "\n".join(f"• {name}: {keys}" for name,keys in list(self.macros.items())[:10])
        self.msg("ANKA", r)

    def type_template(self, template_name):
        templates = {
            "mail imza": f"\n\nSaygılarımla,\n{USER_NAME}",
            "tarih": datetime.datetime.now().strftime("%d/%m/%Y"),
            "saat": datetime.datetime.now().strftime("%H:%M"),
            "teşekkür": "Teşekkür ederim, iyi çalışmalar.",
            "merhaba": f"Merhaba,\n\nUmarım iyisinizdir.",
        }
        text = templates.get(template_name.lower())
        if text:
            time.sleep(0.5)
            pyautogui.write(text, interval=0.02)
            self.msg("ANKA", f"✓ '{template_name}' yazıldı efendim.")
        else:
            self.msg("ANKA", f"'{template_name}' şablonu bulunamadı efendim.")


# ═══════════════════════════════════════════════════════════════════════════════
# 6. ANKA ZİHİN HARİTASI — Görsel düşünce sistemi
# ═══════════════════════════════════════════════════════════════════════════════
class MindMapGenerator:
    """Metin tabanlı zihin haritası oluşturur ve HTML olarak kaydeder"""
    def __init__(self, ollama, speak_func, msg_func):
        self.ollama = ollama
        self.speak = speak_func
        self.msg = msg_func

    def generate(self, topic):
        def _gen():
            r = self.ollama.chat(
                f"'{topic}' için JSON formatında zihin haritası oluştur.\n"
                f"Format: {{\"merkez\": \"{topic}\", \"dallar\": [{{\"baslik\": \"...\", \"alt_dallar\": [\"...\"]}}]}}",
                system_override="Zihin haritası uzmanı. Sadece JSON döndür.")
            try:
                clean = r.replace("```json","").replace("```","").strip()
                data = json.loads(clean)
                html = self._to_html(data)
                path = os.path.join(os.path.expanduser("~"), "Desktop", f"anka_mindmap_{topic[:10]}.html")
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(html)
                webbrowser.open(path)
                self.msg("ANKA", f"🗺️ '{topic}' zihin haritası açıldı efendim!")
                self.speak("Zihin haritası hazırlandı efendim.")
            except:
                # Fallback — metin olarak göster
                self.msg("ANKA", f"🗺️ {topic}:\n{r}")
        threading.Thread(target=_gen, daemon=True).start()

    def _to_html(self, data):
        branches = data.get("dallar", [])
        center = data.get("merkez", "Konu")
        html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<title>Anka Zihin Haritası — {center}</title>
<style>
body{{background:#030308;color:#e0f0ff;font-family:Arial;margin:0;padding:20px}}
h1{{color:#00ffff;text-align:center}}
.map{{display:flex;flex-wrap:wrap;gap:20px;justify-content:center;margin-top:30px}}
.branch{{background:#0d0d20;border:1px solid #00ffff;border-radius:12px;padding:15px;min-width:200px;max-width:250px}}
.branch h3{{color:#00ffff;margin:0 0 10px}}
.sub{{background:#07070f;border-radius:8px;padding:6px 10px;margin:4px 0;font-size:13px;color:#a0d0ff}}
.center{{background:#00ffff;color:#030308;padding:15px 30px;border-radius:20px;font-size:20px;font-weight:bold;text-align:center;margin:20px auto;display:block;width:fit-content}}
</style></head><body>
<h1>🗺️ Anka Zihin Haritası</h1>
<span class="center">🎯 {center}</span>
<div class="map">"""
        for branch in branches:
            html += f'<div class="branch"><h3>📌 {branch.get("baslik","")}</h3>'
            for sub in branch.get("alt_dallar", []):
                html += f'<div class="sub">• {sub}</div>'
            html += '</div>'
        html += "</div></body></html>"
        return html


# ═══════════════════════════════════════════════════════════════════════════════
# 7. ANKA ZAMAN KAPSÜLÜ PRO — Gelecekteki sana mesaj
# ═══════════════════════════════════════════════════════════════════════════════
class TimeCapsulePro:
    """Gelecekteki kendinle konuş"""
    def __init__(self, speak_func, msg_func):
        self.speak = speak_func
        self.msg = msg_func
        self.capsule_file = os.path.join(BASE_DIR, "anka_capsules.json")
        self.running = True
        threading.Thread(target=self._check_loop, daemon=True).start()

    def create(self, message, open_date, note=""):
        capsules = _load(self.capsule_file, [])
        capsules.append({
            "message": message,
            "note": note,
            "created": datetime.datetime.now().isoformat(),
            "open_date": open_date,
            "opened": False
        })
        _save(self.capsule_file, capsules)
        r = f"⏳ Zaman kapsülü oluşturuldu!\n📅 Açılacak: {open_date}\n💌 Mesaj kaydedildi."
        self.msg("ANKA", r); self.speak(r)

    def _check_loop(self):
        time.sleep(60)
        while self.running:
            try:
                capsules = _load(self.capsule_file, [])
                today = datetime.date.today().isoformat()
                changed = False
                for cap in capsules:
                    if not cap["opened"] and cap["open_date"] <= today:
                        cap["opened"] = True
                        changed = True
                        r = (f"💌 ZAMAN KAPSÜLÜ AÇILDI!\n"
                             f"{'═'*35}\n"
                             f"📅 Oluşturulma: {cap['created'][:10]}\n"
                             f"💭 Mesaj:\n{cap['message']}\n"
                             f"{'═'*35}")
                        self.msg("ANKA", r)
                        self.speak("Zaman kapsülü açıldı efendim!")
                        try:
                            requests.post("https://ntfy.sh/anka-yusuf-2026",
                                data=f"💌 Zaman kapsülü: {cap['message'][:100]}".encode(),
                                headers={"Title":"⏳ Zaman Kapsülü Açıldı!"}, timeout=3)
                        except: pass
                if changed: _save(self.capsule_file, capsules)
            except: pass
            time.sleep(3600)

    def list_capsules(self):
        capsules = _load(self.capsule_file, [])
        pending = [c for c in capsules if not c["opened"]]
        if not pending:
            r = "Bekleyen zaman kapsülü yok efendim."
        else:
            r = f"⏳ Bekleyen Zaman Kapsülleri ({len(pending)}):\n"
            for c in pending:
                days = (datetime.date.fromisoformat(c["open_date"]) - datetime.date.today()).days
                r += f"• {c['open_date']} ({days} gün sonra): {c['message'][:40]}...\n"
        self.msg("ANKA", r)

    def stop(self): self.running = False


# ═══════════════════════════════════════════════════════════════════════════════
# 8. ANKA HAYAT KOÇu PRO — Yapay zeka destekli koçluk
# ═══════════════════════════════════════════════════════════════════════════════
class LifeCoachPro:
    """Gerçek anlamda kişisel yaşam koçu"""
    def __init__(self, ollama, speak_func, msg_func):
        self.ollama = ollama
        self.speak = speak_func
        self.msg = msg_func
        self.coach_pro_file = os.path.join(BASE_DIR, "anka_coach_pro.json")

    def weekly_review(self):
        def _r():
            r = self.ollama.chat(
                f"Haftalık yaşam değerlendirmesi için sorular sor. "
                f"İş, sağlık, ilişkiler, kişisel gelişim alanlarında 5 soru.",
                system_override="Yaşam koçu. Derin sorular sor.")
            self.msg("ANKA", f"📊 HAFTALIK DEĞERLENDİRME\n{'═'*30}\n{r}")
            self.speak("Haftalık değerlendirme soruları hazır efendim.")
        threading.Thread(target=_r, daemon=True).start()

    def ikigai_analysis(self):
        def _i():
            r = self.ollama.chat(
                "İkigai analizi için 4 alan sorusu sor:\n"
                "1. Ne yapmaktan keyif alıyorsunuz?\n"
                "2. Neyde iyisiniz?\n"
                "3. Dünya neye ihtiyaç duyuyor?\n"
                "4. Ne için ödeme alabilirsiniz?\n"
                "Bu soruların kesişimi ikigainizdir.",
                system_override="İkigai uzmanı. Japonca yaşam amacı metodunu açıkla.")
            self.msg("ANKA", f"🎯 İKIGAI ANALİZİ\n{'═'*30}\n{r}")
            self.speak("İkigai analizi hazırlandı efendim.")
        threading.Thread(target=_i, daemon=True).start()

    def future_self_letter(self):
        def _f():
            r = self.ollama.chat(
                f"5 yıl sonraki {USER_NAME}'e mektup yaz. "
                f"Umut, hedef ve tavsiyeler içersin. Türkçe, samimi.",
                system_override="Yaşam koçu. İlham verici mektup yaz.")
            path = os.path.join(os.path.expanduser("~"), "Desktop", "gelecekteki_ben.txt")
            with open(path, 'w', encoding='utf-8') as f:
                f.write(f"5 YIL SONRA KENDİME MEKTUP\n{'='*40}\n{r}")
            self.msg("ANKA", f"💌 Gelecekteki Kendinize Mektup:\n{r}")
            self.speak("Mektup yazıldı ve masaüstüne kaydedildi efendim.")
        threading.Thread(target=_f, daemon=True).start()

    def energy_map(self, activities):
        def _e():
            r = self.ollama.chat(
                f"Bu aktiviteleri enerji haritasına göre değerlendir: {activities}\n"
                f"Enerji veren / Enerji alan olarak ayır ve öneriler ver.",
                system_override="Enerji yönetimi uzmanı. Enerji haritası çıkar.")
            self.msg("ANKA", f"⚡ ENERJİ HARİTASI\n{'═'*30}\n{r}")
        threading.Thread(target=_e, daemon=True).start()


# ═══════════════════════════════════════════════════════════════════════════════
# 9. ANKA CRYPTO ORACLE — Kripto analiz ve takip
# ═══════════════════════════════════════════════════════════════════════════════
class CryptoOracle:
    def __init__(self, speak_func, msg_func):
        self.speak = speak_func
        self.msg = msg_func

    def multi_price(self, coins=None):
        coins = coins or ["BTC","ETH","BNB","SOL","DOGE"]
        def _p():
            results = []
            for coin in coins[:5]:
                try:
                    r = requests.get(
                        f"https://api.coinbase.com/v2/prices/{coin}-USD/spot", timeout=5)
                    price = float(r.json()["data"]["amount"])
                    results.append(f"• {coin}: ${price:,.2f}")
                except: results.append(f"• {coin}: —")
            r = f"₿ Kripto Fiyatları:\n" + "\n".join(results)
            self.msg("ANKA", r); self.speak("Kripto fiyatları hazır efendim.")
        threading.Thread(target=_p, daemon=True).start()

    def fear_greed_index(self):
        def _fg():
            try:
                r = requests.get("https://api.alternative.me/fng/", timeout=5)
                data = r.json()["data"][0]
                value = int(data["value"])
                classification = data["value_classification"]
                emoji = "😱" if value < 25 else "😰" if value < 45 else "😐" if value < 55 else "😊" if value < 75 else "🤑"
                r2 = (f"📊 Kripto Korku/Açgözlülük Endeksi\n"
                     f"{'═'*30}\n"
                     f"{emoji} Değer: {value}/100\n"
                     f"• Durum: {classification}\n"
                     f"• {'Alım fırsatı olabilir!' if value < 30 else 'Dikkatli olun!' if value > 75 else 'Nötr piyasa.'}")
                self.msg("ANKA", r2); self.speak(f"Korku endeksi {value} efendim.")
            except:
                self.msg("ANKA", "Endeks verisi alınamadı efendim.")
        threading.Thread(target=_fg, daemon=True).start()

    def portfolio_summary(self, holdings):
        """holdings: {'BTC': 0.5, 'ETH': 2.0}"""
        def _ps():
            total = 0
            lines = []
            for coin, amount in holdings.items():
                try:
                    r = requests.get(
                        f"https://api.coinbase.com/v2/prices/{coin}-USD/spot", timeout=5)
                    price = float(r.json()["data"]["amount"])
                    value = price * amount
                    total += value
                    lines.append(f"• {coin}: {amount} × ${price:,.0f} = ${value:,.2f}")
                except: pass
            r = f"💼 Portföy Özeti:\n" + "\n".join(lines) + f"\n\n💰 Toplam: ${total:,.2f}"
            self.msg("ANKA", r); self.speak(f"Toplam portföy {total:,.0f} dolar efendim.")
        threading.Thread(target=_ps, daemon=True).start()


# ═══════════════════════════════════════════════════════════════════════════════
# ANA KOMUT İŞLEYİCİ
# ═══════════════════════════════════════════════════════════════════════════════
class WowCommandProcessor:
    def __init__(self, speak_func, msg_func, ollama):
        self.speak = speak_func
        self.msg = msg_func
        self.ollama = ollama
        self.detector      = ChangeDetector(speak_func, msg_func)
        self.palace        = MemoryPalace(speak_func, msg_func)
        self.predictor     = BehaviorPredictor(speak_func, msg_func)
        self.truth         = TruthAnalyzer(ollama, speak_func, msg_func)
        self.keyboard      = KeyboardWizard(speak_func, msg_func)
        self.mindmap       = MindMapGenerator(ollama, speak_func, msg_func)
        self.capsule       = TimeCapsulePro(speak_func, msg_func)
        self.life_coach    = LifeCoachPro(ollama, speak_func, msg_func)
        self.crypto        = CryptoOracle(speak_func, msg_func)

    def process(self, text):
        t = text.lower().strip()

        # Tahmin logla
        self.predictor.log(t)

        # ── Hafıza Sarayı ────────────────────────────────────────────────────
        if "saray ekle" in t or "hafızaya bağla" in t:
            parts = t.replace("saray ekle","").replace("hafızaya bağla","").strip().split("|")
            if len(parts) >= 2:
                topic = parts[0].strip()
                content = parts[1].strip()
                related = [r.strip() for r in parts[2].split(",")] if len(parts) > 2 else []
                self.palace.add_node(topic, content, related)
            return True

        if "saraydan getir" in t or "sarayı hatırla" in t:
            topic = t.replace("saraydan getir","").replace("sarayı hatırla","").strip()
            if topic: self.palace.recall(topic)
            return True

        if "saray keşfet" in t:
            topic = t.replace("saray keşfet","").strip()
            if topic: self.palace.explore(topic)
            return True

        if "saray konuları" in t:
            topics = self.palace.get_all_topics()
            r = f"🏛️ Hafıza Sarayı ({len(topics)} konu):\n" + "\n".join(f"• {t}" for t in topics[:15])
            self.msg("ANKA", r)
            return True

        # ── Tahmin ───────────────────────────────────────────────────────────
        if "ne soracağımı tahmin et" in t or "tahminlerim" in t:
            self.predictor.show_predictions(); return True

        if "otomatik tetikle" in t:
            parts = t.replace("otomatik tetikle","").strip().split("=")
            if len(parts) == 2:
                hour_m = re.search(r'(\d+)', parts[0])
                if hour_m:
                    self.predictor.set_auto_trigger(int(hour_m.group(1)), parts[1].strip())
            return True

        # ── Gerçek Analizi ────────────────────────────────────────────────────
        if "güvenilirlik analizi" in t or "sahte mi" in t:
            content = t.replace("güvenilirlik analizi","").replace("sahte mi","").strip()
            if content: self.truth.analyze_credibility(content)
            return True

        if "doğru mu" in t and len(t) > 8:
            claim = t.replace("doğru mu","").strip()
            if claim: self.truth.fact_check_quick(claim)
            return True

        # ── Klavye Sihirbazı ──────────────────────────────────────────────────
        if "klavye makro" in t or "tuş kombinasyonu" in t:
            name = t.replace("klavye makro","").replace("tuş kombinasyonu","").strip()
            if name: self.keyboard.execute(name)
            return True

        if "makro ekle" in t:
            parts = t.replace("makro ekle","").strip().split("=")
            if len(parts) == 2:
                self.keyboard.add_macro(parts[0].strip(), parts[1].strip())
            return True

        if "makrolar" in t and "listele" in t:
            self.keyboard.list_macros(); return True

        if "şablon yaz" in t:
            name = t.replace("şablon yaz","").strip()
            if name: self.keyboard.type_template(name)
            return True

        # ── Zihin Haritası ────────────────────────────────────────────────────
        if "zihin haritası" in t:
            topic = t.replace("zihin haritası","").replace("oluştur","").strip()
            if topic: self.mindmap.generate(topic)
            return True

        # ── Zaman Kapsülü ─────────────────────────────────────────────────────
        if "zaman kapsülü oluştur" in t or "kapsül oluştur" in t:
            parts = t.replace("zaman kapsülü oluştur","").replace("kapsül oluştur","").strip().split("|")
            if len(parts) >= 2:
                message = parts[0].strip()
                date_str = parts[1].strip()
                self.capsule.create(message, date_str)
            else:
                self.msg("ANKA","Format: 'kapsül oluştur [mesaj] | [YYYY-MM-DD]' efendim.")
            return True

        if "kapsüllerim" in t or "zaman kapsülleri" in t:
            self.capsule.list_capsules(); return True

        # ── Yaşam Koçu Pro ────────────────────────────────────────────────────
        if "haftalık değerlendirme" in t:
            self.life_coach.weekly_review(); return True

        if "ikigai" in t:
            self.life_coach.ikigai_analysis(); return True

        if "gelecekteki bana mektup" in t or "geleceğe mektup" in t:
            self.life_coach.future_self_letter(); return True

        if "enerji haritası" in t:
            activities = t.replace("enerji haritası","").strip()
            self.life_coach.energy_map(activities or "çalışma, spor, sosyal medya, aile, hobiler")
            return True

        # ── Kripto Oracle ─────────────────────────────────────────────────────
        if "kripto fiyatları" in t or "tüm kripto" in t:
            self.crypto.multi_price(); return True

        if "korku endeksi" in t or "fear greed" in t:
            self.crypto.fear_greed_index(); return True

        # ── Performans ────────────────────────────────────────────────────────
        if "anka optimizasyon" in t or "belleği temizle" in t:
            try:
                from anka_performance import perf
                r = perf.optimize_now()
                self.msg("ANKA", r); self.speak(r)
            except:
                import gc; gc.collect()
                self.msg("ANKA", "✅ Bellek temizlendi efendim.")
            return True

        if "anka performans" in t:
            try:
                from anka_performance import perf
                stats = perf.get_stats()
                r = (f"⚡ Performans:\n"
                     f"• CPU: %{stats['cpu']:.0f}\n"
                     f"• RAM: %{stats['ram_percent']:.0f} ({stats['ram_used_mb']}MB)\n"
                     f"• Boş RAM: {stats['ram_free_mb']}MB")
                self.msg("ANKA", r); self.speak(r)
            except: pass
            return True

        return False
