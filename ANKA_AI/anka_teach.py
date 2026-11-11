# ── ANKA ÖĞRETME SİSTEMİ — Anka'yı sen eğit ─────────────────────────────────
# • öğretme modu   : Anka cevaplayamadığı soruları sırayla sorar
# • öğren: s = c   : tek soru-cevap öğret
# • toplu satırlar : birden çok "soru = cevap" satırı yapıştır
# • dosyadan öğren : .txt / .csv / .json dosyasından yükle
# • ogretim/ klasörü: dosyayı klasöre at, Anka açılışta kendisi okur
# • yanlış, doğrusu: ... / unut: ... / eş anlamlı: a = b
import os, re, io, csv, json
from anka_config import BASE_DIR
from anka_nlp import get_nlp, fold, tokens

TEACH_DIR = os.path.join(BASE_DIR, "ogretim")
STATE_FILE = os.path.join(BASE_DIR, "anka_teach_state.json")

EXAMPLE = """# Anka öğretim dosyası — her satır:  soru = cevap
# '#' ile başlayan satırlar yok sayılır. Adı '_' ile başlayan dosyalar okunmaz.
# Aşağıdaki örnekleri kullanmak için satırın başındaki # işaretini kaldır:
# en sevdiğim yemek ne = Senin en sevdiğin yemek mantı!
# kaç yaşındasın = Ben yaşsızım ama her gün biraz daha akıllanıyorum!
"""

_SEP1 = re.compile(r"^(.+?)\s+(?:=>|->|→|\||=)\s+(.+)$", re.S)
_SEP2 = re.compile(r"^(.+?)\s*(?:=>|->|→|\||=)\s*(.+)$", re.S)


def parse_line(line):
    l = line.strip()
    if not l or l.startswith("#") or l.startswith("//"):
        return None
    m = _SEP1.match(l) or _SEP2.match(l)
    if not m:
        return None
    q, a = m.group(1).strip(), m.group(2).strip()
    return (q, a) if q and a else None


def _read_text(path):
    for enc in ("utf-8-sig", "cp1254", "latin-1"):
        try:
            with open(path, "r", encoding=enc) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    return ""


def _pairs_from_text(text, ext):
    pairs = []
    if ext == ".json":
        data = json.loads(text)
        if isinstance(data, dict):
            pairs = [(str(k), str(v)) for k, v in data.items()]
        elif isinstance(data, list):
            for it in data:
                if isinstance(it, dict):
                    q = it.get("q") or it.get("soru") or it.get("question")
                    a = it.get("a") or it.get("cevap") or it.get("answer")
                    if q and a:
                        pairs.append((str(q), str(a)))
                elif isinstance(it, (list, tuple)) and len(it) >= 2:
                    pairs.append((str(it[0]), str(it[1])))
    elif ext == ".csv":
        for row in csv.reader(io.StringIO(text)):
            if len(row) >= 2 and row[0].strip() and row[1].strip():
                q, a = row[0].strip(), row[1].strip()
                if q.startswith("#") or q.lower() in ("soru", "question", "q"):
                    continue
                pairs.append((q, a))
    else:
        for line in text.splitlines():
            p = parse_line(line)
            if p:
                pairs.append(p)
    return pairs


class TeachManager:
    def __init__(self, nlp):
        self.nlp = nlp
        self.active = False
        self.queue = []
        self.current = None
        self.taught_now = 0

    # ── Toplu öğretme ────────────────────────────────────────────────────────
    def _fts_rebuild(self):
        try:
            from anka_knowledge_db import get_db
            with get_db()._conn() as c:
                c.execute("INSERT INTO qa_fts(qa_fts) VALUES('rebuild')")
                c.commit()
        except Exception:
            pass

    def teach_pairs(self, pairs):
        n = sum(1 for q, a in pairs if self.nlp.teach(q, a))
        self._fts_rebuild()
        return n

    def import_file(self, path):
        path = path.strip().strip('"').strip("'")
        if not os.path.isfile(path):
            raise FileNotFoundError(path)
        ext = os.path.splitext(path)[1].lower()
        return self.teach_pairs(_pairs_from_text(_read_text(path), ext))

    def scan_folder(self, force=False):
        """ogretim/ klasöründeki yeni/değişen dosyaları okur."""
        try:
            os.makedirs(TEACH_DIR, exist_ok=True)
            ex = os.path.join(TEACH_DIR, "_ornek.txt")
            if not os.path.exists(ex):
                with open(ex, "w", encoding="utf-8") as f:
                    f.write(EXAMPLE)
            state = {}
            if os.path.exists(STATE_FILE):
                try:
                    with open(STATE_FILE, "r", encoding="utf-8") as f:
                        state = json.load(f)
                except Exception:
                    state = {}
            total = 0
            for name in sorted(os.listdir(TEACH_DIR)):
                if name.startswith("_") or os.path.splitext(name)[1].lower() not in (".txt", ".csv", ".json"):
                    continue
                path = os.path.join(TEACH_DIR, name)
                mt = os.path.getmtime(path)
                if not force and state.get(name) == mt:
                    continue
                try:
                    total += self.import_file(path)
                    state[name] = mt
                except Exception as e:
                    print(f"[ANKA-ÖĞRETİM] {name} okunamadı: {e}")
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(state, f)
            if total:
                print(f"[ANKA-ÖĞRETİM] ✅ {total} bilgi öğrenildi ({TEACH_DIR})")
            return total
        except Exception as e:
            print(f"[ANKA-ÖĞRETİM] klasör hatası: {e}")
            return 0

    # ── Öğretme oturumu ──────────────────────────────────────────────────────
    def _start(self):
        self.queue = self.nlp.top_unanswered(50)
        if not self.queue:
            return ("🎉 Şu an cevaplayamadığım soru yok!\nİstersen kendin öğret:\n"
                    "• öğren: soru = cevap\n• dosyadan öğren C:\\yol\\dosya.txt\n"
                    "• 'öğretme yardım' yaz")
        self.active, self.taught_now = True, 0
        return (f"🎓 Öğretme modu açık! {len(self.queue)} soruyu cevaplayamadım.\n"
                f"('geç' atla, 'bitir' çık)\n\n" + self._next_prompt())

    def _next_prompt(self):
        if not self.queue:
            return self._end()
        self.current = self.queue.pop(0)
        return (f"❓ \"{self.current}\"\nBunu nasıl cevaplamalıyım? "
                f"({len(self.queue)} soru daha var)")

    def _end(self):
        self.active, self.current, self.queue = False, None, []
        return (f"🎓 Öğretme bitti! Bu oturumda {self.taught_now} şey öğrendim. "
                f"Teşekkürler efendim! 🙏")

    def _stats(self):
        n, last = 0, []
        try:
            from anka_knowledge_db import get_db
            with get_db()._conn() as c:
                n = c.execute("SELECT COUNT(*) FROM qa WHERE category='ogrenilen'").fetchone()[0]
                last = [r["question"] for r in c.execute(
                    "SELECT question FROM qa WHERE category='ogrenilen' ORDER BY id DESC LIMIT 5")]
        except Exception:
            pass
        un = len(self.nlp.top_unanswered(100000))
        r = (f"📊 ÖĞRETİM DURUMU\n• Senin öğrettiklerin: {n}\n"
             f"• Cevaplayamadığım soru: {un}\n• Toplam bilgi: {len(self.nlp.docs):,}")
        if last:
            r += "\n\n🆕 Son öğrettiklerin:\n" + "\n".join(f"• {q}" for q in last)
        if un:
            r += "\n\n💡 'öğretme modu' yaz, cevaplayamadıklarımı birlikte çözelim."
        return r

    HELP = ("🎓 ANKA'YI EĞİTMEK\n════════════════\n"
            "1️⃣ Öğretme modu:\n   'öğretme modu' → bilmediğim soruları sorarım\n\n"
            "2️⃣ Tek bilgi:\n   öğren: soru = cevap\n\n"
            "3️⃣ Toplu (çok satır yapıştır):\n   soru1 = cevap1\n   soru2 = cevap2\n\n"
            "4️⃣ Dosyadan:\n   dosyadan öğren C:\\yol\\dosya.txt\n   (.txt / .csv / .json)\n\n"
            "5️⃣ Klasör:\n   ogretim klasörüne dosya at, açılışta okurum\n   'öğretim klasörünü tara' → hemen oku\n\n"
            "✏️ Düzeltme: yanlış, doğrusu: doğru cevap\n"
            "🗑️ Unutturma: unut: soru\n"
            "🔗 Eş anlam: eş anlamlı: yeni soru = bilinen soru\n"
            "📊 Durum: 'ne kadar öğrendim'")

    # ── Ana giriş ────────────────────────────────────────────────────────────
    def handle(self, text):
        """Öğretme komutuysa cevap metni döner, değilse None."""
        t = (text or "").strip()
        if not t:
            return None
        f = fold(t)
        self.nlp.build()

        if self.active:
            if f in ("bitir", "cik", "dur", "yeter", "bitti", "oturumu bitir", "ogretmeyi bitir"):
                return self._end()
            if f in ("gec", "atla", "sonraki", "bilmiyorum"):
                return self._next_prompt()
            self.nlp.teach(self.current, t)
            self.taught_now += 1
            self._fts_rebuild()
            return "✅ Öğrendim!\n\n" + self._next_prompt()

        if re.search(r"\bogretme yardim|\bogretim yardim|\bnasil ogretirim|\banka'?yi nasil egitirim", f):
            return self.HELP
        if re.search(r"\bogretme modu|\bbeni egit|\begitim modu|\bogretmen modu", f):
            return self._start()

        m = re.match(r"^dosyadan\s+(?:öğren|öğret|ogren|ogret)\s+(.+)$", t, re.I | re.S)
        if m:
            path = m.group(1).strip().strip('"').strip("'")
            try:
                return f"✅ Dosyadan {self.import_file(path)} soru-cevap öğrendim!"
            except FileNotFoundError:
                return f"❌ Dosya bulunamadı: {path}"
            except Exception as e:
                return f"❌ Dosya okunamadı: {e}"

        if re.search(r"ogretim klasor|ogretimi tara|klasoru tara", f):
            n = self.scan_folder(force=True)
            return f"📁 {TEACH_DIR}\n✅ {n} bilgi öğrendim."

        m = re.match(r"^(?:anka\s+)?(?:öğren|ogren)\s*[:：]\s*(.+?)\s*=\s*(.+)$", t, re.I | re.S)
        if m:
            q, a = m.group(1).strip(), m.group(2).strip()
            self.nlp.teach(q, a)
            self._fts_rebuild()
            return f"✅ Öğrendim! '{q}' sorulunca '{a[:60]}' diyeceğim."

        m = (re.match(r"^(?:hayır|hayir|yanlış|yanlis|bu yanlış|bu yanlis|yanlış cevap|yanlis cevap)"
                      r"[\s,.!]*(?:doğrusu|dogrusu)\s*(?:şu|su)?\s*[:：]?\s*(.+)$", t, re.I | re.S)
             or re.match(r"^(?:doğrusu|dogrusu)\s*[:：]\s*(.+)$", t, re.I | re.S))
        if m:
            new = m.group(1).strip()
            q = self.nlp.correct_last(new)
            if q:
                self._fts_rebuild()
                return f"✅ Düzelttim! \"{q}\" sorusuna artık şunu diyeceğim:\n{new[:120]}"
            return "🤔 Düzeltecek bir önceki sorum yok. Önce bir soru sor."

        m = re.match(r"^unut\s*[:：]\s*(.+)$", t, re.I | re.S)
        if m:
            q = self.nlp.forget(m.group(1).strip())
            return f"🗑️ Unuttum: \"{q}\"" if q else "🤔 Bu soruyu zaten bilmiyorum."

        m = re.match(r"^(?:eş anlamlı|es anlamli|aynısı|aynisi)\s*[:：]\s*(.+?)\s*=\s*(.+)$", t, re.I | re.S)
        if m:
            yeni, bilinen = m.group(1).strip(), m.group(2).strip()
            res = self.nlp._match(tokens(bilinen))
            if res and res["confidence"] >= 0.6:
                self.nlp.teach(yeni, res["doc"]["a"])
                return f"✅ Tamam! '{yeni}' sorusuna da '{bilinen}' ile aynı cevabı vereceğim."
            return f"🤔 '{bilinen}' sorusunun cevabını bilmiyorum. Önce ona cevap öğret."

        if re.search(r"ne kadar ogrendim|ogrendiklerim|ogretim istatistik|ogrendigin sey", f):
            return self._stats()

        lines = [l for l in t.splitlines() if l.strip() and not l.strip().startswith("#")]
        if len(lines) >= 2:
            pairs = [p for p in (parse_line(l) for l in lines) if p]
            if len(pairs) >= 2 and len(pairs) >= 0.8 * len(lines):
                return f"✅ {self.teach_pairs(pairs)} soru-cevap öğrendim!"
        return None


_tm = None
def get_teach():
    global _tm
    if _tm is None:
        _tm = TeachManager(get_nlp())
    return _tm
