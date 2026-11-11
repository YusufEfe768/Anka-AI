# ── ANKA ULTRA 2 — Şaşırtıcı Yeni Özellikler v2 ──────────────────────────────
try:
    import pyperclip
except ImportError:
    class _PyClip:
        def copy(self,x):pass
        def paste(self):return ""
    pyperclip=_PyClip()
import json, os, time, threading, datetime, subprocess, webbrowser, re
import requests, random, math, psutil, hashlib
from anka_config import BASE_DIR, USER_NAME

U2_FILE = os.path.join(BASE_DIR, "anka_ultra2.json")

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
# 1. ANKA RÜYA GÜNLÜĞÜ — Rüyaları kaydet ve analiz et
# ═══════════════════════════════════════════════════════════════════════════════
class DreamJournal:
    def __init__(self, ollama, speak_func, msg_func):
        self.ollama = ollama
        self.speak  = speak_func
        self.msg    = msg_func
        self.dream_file = os.path.join(BASE_DIR, "anka_dreams.json")
        self.data = _load(self.dream_file, {"dreams": [], "patterns": {}})

    def log_dream(self, dream_text, mood="nötr"):
        entry = {
            "dream": dream_text,
            "mood": mood,
            "date": datetime.date.today().isoformat(),
            "time": datetime.datetime.now().strftime("%H:%M")
        }
        self.data["dreams"].append(entry)
        _save(self.dream_file, self.data)
        def _analyze():
            r = self.ollama.chat(
                f"Rüya: '{dream_text}'\nRüyayı psikolojik açıdan analiz et. "
                f"Semboller, duygular ve olası anlamları belirt. Kısa tut.",
                system_override="Rüya analisti. Sembolik ve psikolojik analiz yap.")
            self.msg("ANKA", f"🌙 Rüya Analizi:\n{r}")
            self.speak("Rüya analizi hazırlandı efendim.")
        self.msg("ANKA", f"🌙 Rüya kaydedildi: {dream_text[:50]}...")
        threading.Thread(target=_analyze, daemon=True).start()

    def dream_patterns(self):
        dreams = self.data["dreams"]
        if len(dreams) < 3:
            self.msg("ANKA", "Daha fazla rüya kaydı gerekiyor efendim."); return
        def _pattern():
            all_dreams = "\n".join(f"- {d['dream'][:80]}" for d in dreams[-10:])
            r = self.ollama.chat(
                f"Bu rüyalardaki tekrarlayan temalar ve kalıpları bul:\n{all_dreams}",
                system_override="Rüya analisti. Kalıpları ve temaları belirle.")
            self.msg("ANKA", f"🌙 Rüya Kalıpları:\n{r}")
        threading.Thread(target=_pattern, daemon=True).start()


# ═══════════════════════════════════════════════════════════════════════════════
# 2. ANKA MÜZİK YAPIMCISI — Şarkı sözü + melodi fikri üret
# ═══════════════════════════════════════════════════════════════════════════════
class MusicProducer:
    def __init__(self, ollama, speak_func, msg_func):
        self.ollama = ollama
        self.speak  = speak_func
        self.msg    = msg_func

    def generate_song(self, theme, genre="pop", mood="mutlu"):
        def _gen():
            r = self.ollama.chat(
                f"Tema: {theme}\nTür: {genre}\nRuh hali: {mood}\n\n"
                f"Türkçe şarkı yaz:\n"
                f"- Başlık\n- 1. Kıta (4 satır)\n- Nakarat (4 satır)\n"
                f"- 2. Kıta (4 satır)\n- Köprü (2 satır)\n"
                f"- Melodi notları (örn: La Sol Mi...)\n"
                f"- Chord progression (örn: Am-F-C-G)",
                system_override="Profesyonel söz yazarı ve besteci. Özgün şarkı yaz.")
            path = os.path.join(os.path.expanduser("~"), "Desktop",
                               f"anka_sarki_{theme[:10]}.txt")
            with open(path,'w',encoding='utf-8') as f:
                f.write(f"ANKA MÜZİK STÜDYOSU\n{'='*40}\n{r}")
            pyperclip.copy(r)
            self.msg("ANKA", f"🎵 Şarkı:\n{r}")
            self.speak("Şarkı yazıldı ve masaüstüne kaydedildi efendim.")
        threading.Thread(target=_gen, daemon=True).start()

    def beat_generator(self, bpm=120, genre="hip-hop"):
        def _beat():
            r = self.ollama.chat(
                f"BPM: {bpm}, Tür: {genre}\n"
                f"Beat pattern yaz:\n"
                f"- Kick drum pattern (16 step)\n"
                f"- Snare pattern\n"
                f"- Hi-hat pattern\n"
                f"- Bass line\n"
                f"- Önerilen sample'lar\n"
                f"X=vuruş, .=sessizlik formatında",
                system_override="Beat maker. Ritmik pattern yaz.")
            self.msg("ANKA", f"🥁 Beat Pattern ({bpm} BPM, {genre}):\n{r}")
            pyperclip.copy(r)
        threading.Thread(target=_beat, daemon=True).start()

    def music_theory(self, topic):
        def _theory():
            r = self.ollama.chat(
                f"Müzik teorisi: {topic}\nAnlaşılır şekilde açıkla, örnekler ver.",
                system_override="Müzik teorisi öğretmeni. Anlaşılır açıkla.")
            self.msg("ANKA", f"🎼 Müzik Teorisi — {topic}:\n{r}")
        threading.Thread(target=_theory, daemon=True).start()


# ═══════════════════════════════════════════════════════════════════════════════
# 3. ANKA OYUN MOTORU v2 — Yapay Zeka ile Oyunlar
# ═══════════════════════════════════════════════════════════════════════════════
class GameEngineV2:
    def __init__(self, ollama, speak_func, msg_func):
        self.ollama = ollama
        self.speak  = speak_func
        self.msg    = msg_func
        self.game_state = {}
        self.active_game = None
        self.score = 0

    def twenty_questions(self, thing=None):
        """20 soru oyunu"""
        if not thing:
            things = ["elma","araba","telefon","ağaç","deniz","güneş","kitap","kedi"]
            thing = random.choice(things)
        self.active_game = "20q"
        self.game_state = {"thing": thing, "questions": 0, "max": 20}
        r = ("🎮 20 SORU OYUNU\n"
             "Aklımdaki şeyi bulmaya çalış!\n"
             "Sadece Evet/Hayır soruları sor.\n"
             "20 hakkın var. Başla!")
        self.msg("ANKA", r); self.speak(r)

    def answer_20q(self, question):
        if self.active_game != "20q": return False
        state = self.game_state
        state["questions"] += 1
        thing = state["thing"]

        # Basit kural bazlı yanıt
        q = question.lower()
        answer = "Bilmiyorum"
        if any(w in q for w in ["canlı","diri","yaşıyor"]): answer = "Evet" if thing in ["kedi","ağaç"] else "Hayır"
        elif any(w in q for w in ["yenebilir","yenir","yer"]): answer = "Evet" if thing in ["elma"] else "Hayır"
        elif any(w in q for w in ["araç","taşıt","gider"]): answer = "Evet" if thing == "araba" else "Hayır"
        elif any(w in q for w in ["teknoloji","elektronik"]): answer = "Evet" if thing == "telefon" else "Hayır"
        elif any(w in q for w in ["doğa","bitki"]): answer = "Evet" if thing in ["ağaç","elma"] else "Hayır"
        else:
            answer = random.choice(["Evet","Hayır","Bazen"])

        remaining = state["max"] - state["questions"]
        r = f"{'✅' if answer=='Evet' else '❌'} {answer}! ({remaining} hak kaldı)"
        if remaining == 0:
            r += f"\n⏰ Bitti! Cevap: {thing}"
            self.active_game = None
        self.msg("ANKA", r); self.speak(r)
        return True

    def story_game(self, genre="macera"):
        """Etkileşimli hikaye oyunu"""
        def _start():
            r = self.ollama.chat(
                f"Türü: {genre}\n"
                f"Kısa, etkileşimli hikaye başlat. Son satırda 3 seçenek sun:\n"
                f"A) ... B) ... C) ...",
                system_override="Etkileşimli hikaye anlatıcısı. Sürükleyici başlangıç yaz.")
            self.active_game = "story"
            self.game_state = {"history": [r], "genre": genre}
            self.msg("ANKA", f"📖 HİKAYE OYUNU\n{'═'*30}\n{r}")
            self.speak("Hikaye başladı! A, B veya C seçin efendim.")
        threading.Thread(target=_start, daemon=True).start()

    def story_choice(self, choice):
        if self.active_game != "story": return False
        def _continue():
            history = "\n".join(self.game_state["history"][-3:])
            r = self.ollama.chat(
                f"Hikaye geçmişi:\n{history}\n\n"
                f"Kullanıcı '{choice}' seçti.\n"
                f"Hikayeyi devam ettir. Son satırda 3 yeni seçenek sun.",
                system_override="Etkileşimli hikaye anlatıcısı. Devam ettir.")
            self.game_state["history"].append(r)
            self.msg("ANKA", r)
            self.speak("Seçiminiz işlendi efendim.")
        threading.Thread(target=_continue, daemon=True).start()
        return True

    def riddle_game(self):
        """Bilmece oyunu"""
        def _riddle():
            r = self.ollama.chat(
                "Türkçe, zekice bir bilmece sor. Cevabı gizle.",
                system_override="Bilmece ustası. Yaratıcı bilmece sor.")
            self.active_game = "riddle"
            self.game_state = {"riddle": r}
            self.msg("ANKA", f"🤔 BİLMECE:\n{r}")
            self.speak("Bilmece hazır! Cevabınızı yazın efendim.")
        threading.Thread(target=_riddle, daemon=True).start()

    def check_riddle(self, answer):
        if self.active_game != "riddle": return False
        def _check():
            r = self.ollama.chat(
                f"Bilmece: {self.game_state['riddle']}\n"
                f"Verilen cevap: {answer}\n"
                f"Doğru mu? Açıkla.",
                system_override="Bilmece hakemi. Değerlendir.")
            self.msg("ANKA", r)
            self.active_game = None
        threading.Thread(target=_check, daemon=True).start()
        return True

    def speed_math(self, level="kolay"):
        """Hız matematik oyunu"""
        ops = {
            "kolay": [("+",1,20),("-",1,20),("*",1,10)],
            "orta":  [("+",10,100),("-",10,100),("*",2,20)],
            "zor":   [("+",100,999),("-",100,999),("*",10,99)]
        }
        op_list = ops.get(level, ops["kolay"])
        op_sym, min_v, max_v = random.choice(op_list)
        a = random.randint(min_v, max_v)
        b = random.randint(min_v, max_v)
        if op_sym == "-" and b > a: a, b = b, a
        answer = eval(f"{a}{op_sym}{b}")
        self.active_game = "math"
        self.game_state = {
            "question": f"{a} {op_sym} {b}",
            "answer": answer,
            "start": time.time(),
            "level": level
        }
        r = f"⚡ HIZ MATEMATİK!\n{a} {op_sym} {b} = ?"
        self.msg("ANKA", r); self.speak(r)

    def check_math(self, user_answer):
        if self.active_game != "math": return False
        elapsed = time.time() - self.game_state["start"]
        correct = int(user_answer.strip()) == self.game_state["answer"]
        if correct:
            self.score += max(10, int(30 - elapsed))
            r = f"✅ DOĞRU! {elapsed:.1f}sn — Puan: {self.score}"
        else:
            r = f"❌ YANLIŞ! Cevap: {self.game_state['answer']} — Puan: {self.score}"
        self.msg("ANKA", r); self.speak(r)
        self.active_game = None
        return True


# ═══════════════════════════════════════════════════════════════════════════════
# 4. ANKA ARAŞTIRMACI v2 — Derin web araştırması + kaynak doğrulama
# ═══════════════════════════════════════════════════════════════════════════════
class DeepResearcherV2:
    def __init__(self, ollama, speak_func, msg_func):
        self.ollama = ollama
        self.speak  = speak_func
        self.msg    = msg_func
        self.research_file = os.path.join(BASE_DIR, "anka_research.json")
        self.data = _load(self.research_file, {"saved": [], "bookmarks": []})

    def research(self, topic):
        def _r():
            self.msg("ANKA", f"🔬 '{topic}' araştırılıyor...")
            results = {}
            # Wikipedia
            try:
                r = requests.get(
                    f"https://tr.wikipedia.org/api/rest_v1/page/summary/{topic.replace(' ','_')}",
                    timeout=5)
                if r.status_code == 200:
                    d = r.json()
                    results["wikipedia"] = d.get("extract","")[:500]
                    results["wiki_url"]  = d.get("content_urls",{}).get("desktop",{}).get("page","")
            except: pass
            # DuckDuckGo
            try:
                r = requests.get(
                    f"https://api.duckduckgo.com/?q={topic}&format=json", timeout=5)
                d = r.json()
                if d.get("Abstract"):
                    results["duckduckgo"] = d["Abstract"][:400]
                related = [t["Text"][:100] for t in d.get("RelatedTopics",[])[:3]
                          if isinstance(t,dict) and t.get("Text")]
                if related: results["related"] = related
            except: pass

            if not results:
                self.msg("ANKA", f"'{topic}' için veri bulunamadı efendim."); return

            context = "\n\n".join(f"[{k}]: {v}" for k,v in results.items()
                                  if isinstance(v, str))
            summary = self.ollama.chat(
                f"'{topic}' hakkında toplanan bilgileri sentezle:\n\n{context}",
                system_override="Araştırmacı. Kapsamlı ve güvenilir özet yaz.")

            report = (f"🔬 ARAŞTIRMA RAPORU: {topic}\n{'═'*40}\n"
                     f"{summary}\n\n")
            if results.get("wiki_url"):
                report += f"📚 Kaynak: {results['wiki_url']}\n"
            if results.get("related"):
                report += f"\n🔗 İlgili: {', '.join(results['related'][:2])}"

            # Kaydet
            self.data["saved"].append({
                "topic": topic, "report": report,
                "date": datetime.date.today().isoformat()
            })
            if len(self.data["saved"]) > 50:
                self.data["saved"] = self.data["saved"][-50:]
            _save(self.research_file, self.data)

            self.msg("ANKA", report)
            pyperclip.copy(report)
            self.speak(f"'{topic}' araştırması tamamlandı efendim.")
        threading.Thread(target=_r, daemon=True).start()

    def save_bookmark(self, url, title=""):
        self.data["bookmarks"].append({
            "url": url, "title": title or url[:50],
            "saved": datetime.datetime.now().isoformat()
        })
        _save(self.research_file, self.data)
        r = f"🔖 Yer imi kaydedildi: {title or url[:40]}"
        self.msg("ANKA", r); self.speak(r)

    def list_bookmarks(self):
        bm = self.data["bookmarks"]
        if not bm:
            self.msg("ANKA","Yer imi yok efendim."); return
        r = f"🔖 Yer İmleri ({len(bm)}):\n"
        r += "\n".join(f"• {b['title'][:40]}: {b['url'][:40]}" for b in bm[-10:])
        self.msg("ANKA", r)


# ═══════════════════════════════════════════════════════════════════════════════
# 5. ANKA SAĞLIK PRO v2 — Gelişmiş sağlık takibi
# ═══════════════════════════════════════════════════════════════════════════════
class HealthProV2:
    def __init__(self, ollama, speak_func, msg_func):
        self.ollama = ollama
        self.speak  = speak_func
        self.msg    = msg_func
        self.health_file = os.path.join(BASE_DIR, "anka_health_pro2.json")
        self.data = _load(self.health_file, {
            "weight_log": [], "bp_log": [], "glucose_log": [],
            "medication": [], "symptoms": [], "vitals": {}
        })

    def log_weight(self, kg, body_fat=None):
        entry = {"kg": kg, "date": datetime.date.today().isoformat()}
        if body_fat: entry["body_fat"] = body_fat
        self.data["weight_log"].append(entry)
        _save(self.health_file, self.data)
        # Trend analizi
        log = self.data["weight_log"]
        if len(log) >= 2:
            diff = kg - log[-2]["kg"]
            trend = f"↑ {abs(diff):.1f}kg artış" if diff > 0 else f"↓ {abs(diff):.1f}kg düşüş"
        else:
            trend = "İlk kayıt"
        r = f"⚖️ Kilo: {kg}kg ({trend})"
        if body_fat: r += f" | Yağ: %{body_fat}"
        self.msg("ANKA", r); self.speak(r)

    def log_blood_pressure(self, systolic, diastolic, pulse=None):
        entry = {
            "systolic": systolic, "diastolic": diastolic,
            "pulse": pulse, "date": datetime.datetime.now().isoformat()
        }
        self.data["bp_log"].append(entry)
        _save(self.health_file, self.data)
        # Değerlendirme
        if systolic < 120 and diastolic < 80: status = "✅ Normal"
        elif systolic < 130 and diastolic < 80: status = "⚠️ Yüksek Normal"
        elif systolic < 140 or diastolic < 90: status = "🟡 Evre 1 Hipertansiyon"
        else: status = "🔴 Evre 2 Hipertansiyon — Doktor görün!"
        r = f"💉 Tansiyon: {systolic}/{diastolic} mmHg — {status}"
        if pulse: r += f" | Nabız: {pulse}/dk"
        self.msg("ANKA", r); self.speak(r[:150])

    def add_medication(self, name, dose, frequency, reminder_times):
        med = {
            "name": name, "dose": dose,
            "frequency": frequency,
            "times": reminder_times,
            "added": datetime.date.today().isoformat()
        }
        self.data["medication"].append(med)
        _save(self.health_file, self.data)
        r = (f"💊 İlaç eklendi: {name}\n"
             f"• Doz: {dose}\n"
             f"• Sıklık: {frequency}\n"
             f"• Hatırlatma: {', '.join(reminder_times)}")
        self.msg("ANKA", r); self.speak(r[:150])

    def health_summary(self):
        def _summary():
            log = self.data["weight_log"]
            bp  = self.data["bp_log"]
            meds = self.data["medication"]
            r = f"🏥 SAĞLIK ÖZETİ\n{'═'*35}\n"
            if log:
                latest = log[-1]
                r += f"⚖️ Son Kilo: {latest['kg']}kg ({latest['date']})\n"
                if len(log) >= 2:
                    diff = log[-1]["kg"] - log[0]["kg"]
                    r += f"📊 Toplam Değişim: {diff:+.1f}kg\n"
            if bp:
                latest_bp = bp[-1]
                r += f"💉 Son Tansiyon: {latest_bp['systolic']}/{latest_bp['diastolic']}\n"
            if meds:
                r += f"\n💊 İlaçlar ({len(meds)}):\n"
                r += "\n".join(f"• {m['name']} {m['dose']}" for m in meds[:5])

            context = r
            advice = self.ollama.chat(
                f"Sağlık verileri:\n{context}\nGenel değerlendirme ve öneriler.",
                system_override="Sağlık asistanı. Genel bilgi ver, teşhis koyma.")
            r += f"\n\n💡 Genel Değerlendirme:\n{advice}"
            self.msg("ANKA", r)
            self.speak("Sağlık özeti hazırlandı efendim.")
        threading.Thread(target=_summary, daemon=True).start()


# ═══════════════════════════════════════════════════════════════════════════════
# 6. ANKA HABER ANALİZÖRÜ v2
# ═══════════════════════════════════════════════════════════════════════════════
class NewsAnalyzerV2:
    def __init__(self, ollama, speak_func, msg_func):
        self.ollama = ollama
        self.speak  = speak_func
        self.msg    = msg_func
        self.feeds  = {
            "teknoloji": "https://www.webtekno.com/rss.xml",
            "gündem":    "https://www.hurriyet.com.tr/rss/anasayfa",
            "spor":      "https://www.hurriyet.com.tr/rss/spor",
            "ekonomi":   "https://www.hurriyet.com.tr/rss/ekonomi",
            "dünya":     "https://feeds.bbci.co.uk/news/world/rss.xml",
            "bilim":     "https://www.sciencedaily.com/rss/top/science.xml",
        }

    def get_by_category(self, category="gündem"):
        def _n():
            import xml.etree.ElementTree as ET
            url = self.feeds.get(category.lower(), self.feeds["gündem"])
            try:
                r = requests.get(url, timeout=6,
                    headers={"User-Agent":"AnkaBot/4.0"})
                root = ET.fromstring(r.content)
                items = root.findall(".//item")[:6]
                headlines = []
                for item in items:
                    title = item.find("title")
                    desc  = item.find("description")
                    if title is not None:
                        headlines.append({
                            "title": title.text[:70],
                            "desc": re.sub(r'<[^>]+>','',desc.text or "")[:100] if desc is not None else ""
                        })
                news_text = "\n".join(f"• {h['title']}" for h in headlines)
                analysis = self.ollama.chat(
                    f"Bu {category} haberlerini analiz et:\n{news_text}\n\n"
                    f"Öne çıkan tema, olası etkiler ve önemli noktalar.",
                    system_override="Haber analisti. Kısa ve nesnel analiz yap.")
                r2 = (f"📰 {category.capitalize()} Haberleri:\n{'─'*35}\n"
                     f"{news_text}\n\n💡 Analiz:\n{analysis}")
                self.msg("ANKA", r2)
                self.speak(f"{category} haberleri hazırlandı efendim.")
            except Exception as e:
                self.msg("ANKA", f"Haber alınamadı: {e}")
        threading.Thread(target=_n, daemon=True).start()

    def personalized_digest(self, interests):
        def _digest():
            all_news = []
            import xml.etree.ElementTree as ET
            for cat in interests[:3]:
                url = self.feeds.get(cat.lower())
                if not url: continue
                try:
                    r = requests.get(url, timeout=5)
                    root = ET.fromstring(r.content)
                    for item in root.findall(".//item")[:2]:
                        title = item.find("title")
                        if title: all_news.append(f"[{cat}] {title.text[:60]}")
                except: pass

            if not all_news:
                self.msg("ANKA","Haber alınamadı efendim."); return

            news_str = "\n".join(all_news)
            digest = self.ollama.chat(
                f"Kişisel haber özeti — İlgi alanları: {', '.join(interests)}\n\n{news_str}",
                system_override="Kişisel haber editörü. İlgi alanlarına göre özetle.")
            self.msg("ANKA", f"📰 Kişisel Haber Özeti:\n{digest}")
            self.speak("Kişisel haber özeti hazırlandı efendim.")
        threading.Thread(target=_digest, daemon=True).start()


# ═══════════════════════════════════════════════════════════════════════════════
# KOMUT İŞLEYİCİ
# ═══════════════════════════════════════════════════════════════════════════════
class Ultra2CommandProcessor:
    def __init__(self, speak_func, msg_func, ollama):
        self.speak      = speak_func
        self.msg        = msg_func
        self.ollama     = ollama
        self.dreams     = DreamJournal(ollama, speak_func, msg_func)
        self.music      = MusicProducer(ollama, speak_func, msg_func)
        self.games      = GameEngineV2(ollama, speak_func, msg_func)
        self.researcher = DeepResearcherV2(ollama, speak_func, msg_func)
        self.health     = HealthProV2(ollama, speak_func, msg_func)
        self.news       = NewsAnalyzerV2(ollama, speak_func, msg_func)

    def process(self, text):
        t = text.lower().strip()

        # ── Rüya Günlüğü ─────────────────────────────────────────────────────
        if "rüya kaydet" in t or "rüya gördüm" in t:
            dream = t.replace("rüya kaydet","").replace("rüya gördüm","").strip()
            if dream: self.dreams.log_dream(dream); return True
        if "rüya kalıpları" in t or "rüya analizi" in t:
            self.dreams.dream_patterns(); return True

        # ── Müzik Yapımcısı ───────────────────────────────────────────────────
        if "şarkı yaz" in t or "şarkı oluştur" in t:
            theme = t.replace("şarkı yaz","").replace("şarkı oluştur","").strip()
            genre = next((g for g in ["pop","rock","rap","türkü","arabesk","jazz"] if g in t), "pop")
            if theme: self.music.generate_song(theme, genre); return True
        if "beat üret" in t or "beat yap" in t:
            m = re.search(r'(\d+)', t)
            bpm = int(m.group(1)) if m else 120
            genre = next((g for g in ["hip-hop","electronic","rock","jazz"] if g in t), "hip-hop")
            self.music.beat_generator(bpm, genre); return True
        if "müzik teorisi" in t:
            topic = t.replace("müzik teorisi","").strip()
            if topic: self.music.music_theory(topic); return True

        # ── Oyunlar ───────────────────────────────────────────────────────────
        if "20 soru" in t or "yirmi soru" in t:
            self.games.twenty_questions(); return True
        if self.games.active_game == "20q":
            self.games.answer_20q(text); return True

        if "hikaye oyunu" in t or "etkileşimli hikaye" in t:
            genre = next((g for g in ["macera","korku","komedi","bilim kurgu"] if g in t), "macera")
            self.games.story_game(genre); return True
        if self.games.active_game == "story" and t.strip() in ["a","b","c","a)","b)","c)"]:
            self.games.story_choice(t.strip().replace(")","").upper()); return True

        if "bilmece sor" in t or "bilmece oyunu" in t:
            self.games.riddle_game(); return True
        if self.games.active_game == "riddle" and len(t) > 2:
            self.games.check_riddle(t); return True

        if "hız matematik" in t or "matematik oyunu" in t:
            level = "zor" if "zor" in t else "kolay" if "kolay" in t else "orta"
            self.games.speed_math(level); return True
        if self.games.active_game == "math" and re.match(r'^-?\d+$', t.strip()):
            self.games.check_math(t.strip()); return True

        # ── Araştırma ─────────────────────────────────────────────────────────
        if "derin araştır" in t or "araştırma raporu" in t:
            topic = t.replace("derin araştır","").replace("araştırma raporu","").strip()
            if topic: self.researcher.research(topic); return True
        if "yer imi ekle" in t or "bookmark ekle" in t:
            url_m = re.search(r'https?://\S+', text)
            if url_m:
                title = t.replace("yer imi ekle","").replace("bookmark ekle","")
                title = re.sub(r'https?://\S+','',title).strip()
                self.researcher.save_bookmark(url_m.group(0), title)
            return True
        if "yer imleri" in t or "bookmarklar" in t:
            self.researcher.list_bookmarks(); return True

        # ── Sağlık Pro ────────────────────────────────────────────────────────
        if "kilo kaydet" in t or "kilom" in t:
            m = re.search(r'(\d+(?:\.\d+)?)', t)
            if m: self.health.log_weight(float(m.group(1))); return True
        if "tansiyon kaydet" in t or "tansiyonum" in t:
            m = re.search(r'(\d{2,3})[/\\](\d{2,3})', t)
            if m:
                pulse_m = re.search(r'nabız\s*(\d+)', t)
                self.health.log_blood_pressure(
                    int(m.group(1)), int(m.group(2)),
                    int(pulse_m.group(1)) if pulse_m else None)
            return True
        if "ilaç ekle" in t:
            parts = t.replace("ilaç ekle","").strip().split(",")
            if len(parts) >= 3:
                times = [p.strip() for p in parts[2].split()]
                self.health.add_medication(parts[0].strip(), parts[1].strip(),
                    "günlük", times)
            return True
        if "sağlık özeti" in t or "sağlık raporum" in t:
            self.health.health_summary(); return True

        # ── Haber ────────────────────────────────────────────────────────────
        if "teknoloji haberleri" in t: self.news.get_by_category("teknoloji"); return True
        if "spor haberleri" in t: self.news.get_by_category("spor"); return True
        if "ekonomi haberleri" in t: self.news.get_by_category("ekonomi"); return True
        if "dünya haberleri" in t: self.news.get_by_category("dünya"); return True
        if "bilim haberleri" in t: self.news.get_by_category("bilim"); return True
        if "kişisel haber özeti" in t:
            interests = t.replace("kişisel haber özeti","").strip().split(",")
            if not interests or interests == [""]:
                interests = ["teknoloji","gündem","spor"]
            self.news.personalized_digest(interests); return True

        return False
