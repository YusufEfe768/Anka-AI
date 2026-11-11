# ── ANKA NLP v1 — Modelsiz, API'siz, internetsiz akıllı anlama motoru ────────
# Saf Python: Türkçe normalize + kök bulma + BM25 arama + yazım düzeltme
# + bağlam hafızası + güvenli hesap + canlı saat/tarih + kullanıcıdan öğrenme.
import re, os, math, ast, operator, json, difflib, datetime, threading
from collections import Counter, defaultdict
from anka_config import BASE_DIR

UNANSWERED_FILE = os.path.join(BASE_DIR, "anka_unanswered.json")
FORGET_FILE = os.path.join(BASE_DIR, "anka_forgotten.json")

# ── Türkçe metin işleme ──────────────────────────────────────────────────────
_LOWER = str.maketrans({"İ": "i", "I": "ı"})
_FOLD  = str.maketrans("çğıöşüâîû", "cgiosuaiu")

def lower_tr(s):
    return s.translate(_LOWER).lower()

def fold(s):
    return lower_tr(s).translate(_FOLD)

_STOP = set(fold(w) for w in """
bir bu su o ve ile de da mi mu ne nedir nasil neden icin gibi cok daha en var yok
ben sen biz siz bana sana lutfen acaba hakkinda bilgi ver soyle anlat nin nun in un
peki ya demek midir mudur mıdır hangi kim nerede kac tane ise ama fakat veya
""".split())

_SUFFIX = sorted("""
larin lerin lari leri lara lere dan den tan ten nin nun
lar ler dir dur tir tur yor miş mis
yi yu ya ye la le ki da de ta te
in un i u a e
""".split(), key=len, reverse=True)

def stem(w):
    for _ in range(4):
        for suf in _SUFFIX:
            if w.endswith(suf) and len(w) - len(suf) >= 4:
                w = w[: -len(suf)]
                break
        else:
            break
    return w

def tokens(text):
    ws = re.findall(r"[a-z0-9]+", fold(text))
    return [stem(w) for w in ws if w not in _STOP]


# ── Güvenli hesap makinesi (eval yok) ────────────────────────────────────────
_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.Div: operator.truediv, ast.Pow: operator.pow, ast.Mod: operator.mod,
        ast.FloorDiv: operator.floordiv, ast.USub: operator.neg}

def _ev(n):
    if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
        return n.value
    if isinstance(n, ast.BinOp) and type(n.op) in _OPS:
        a, b = _ev(n.left), _ev(n.right)
        if isinstance(n.op, ast.Pow) and abs(b) > 1000:
            raise ValueError("üs çok büyük")
        return _OPS[type(n.op)](a, b)
    if isinstance(n, ast.UnaryOp) and type(n.op) in _OPS:
        return _OPS[type(n.op)](_ev(n.operand))
    raise ValueError("desteklenmiyor")

def try_math(text):
    t = lower_tr(text)
    for a, b in [("artı", "+"), ("eksi", "-"), ("çarpı", "*"), ("kere", "*"),
                 ("bölü", "/"), ("üssü", "**"), ("^", "**")]:
        t = t.replace(a, b)
    t = re.sub(r"(?<=\d)\s*x\s*(?=\d)", "*", t)
    t = t.replace(",", ".")
    m = re.search(r"\d[\d\s+\-*/().%]*\d", t)
    if not m:
        return None
    expr = m.group(0).strip()
    if not re.search(r"[+\-*/%]", expr):
        return None
    try:
        r = _ev(ast.parse(expr, mode="eval").body)
        if isinstance(r, float) and r == int(r) and abs(r) < 1e15:
            r = int(r)
        r = f"{r:,}" if isinstance(r, int) else f"{r:.8g}"
        return f"🔢 {expr} = {r}"
    except ZeroDivisionError:
        return "❌ Sıfıra bölme olmaz efendim."
    except Exception:
        return None


# ── Canlı cevaplar (internetsiz) ─────────────────────────────────────────────
_GUN = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
_AY = ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz",
       "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]

def dynamic_answer(text):
    t = fold(text)
    now = datetime.datetime.now()
    if re.search(r"\bsaat kac\b|\bsaat kaç\b|\bsimdi saat\b", t):
        return f"🕐 Saat {now.strftime('%H:%M')}"
    if re.search(r"bugun gunlerden|hangi gundeyiz|bugun gun", t):
        return f"📅 Bugün {_GUN[now.weekday()]}"
    if re.search(r"bugunun tarihi|bugun ayin kaci|tarih ne|bugun tarih", t):
        return f"📅 {now.day} {_AY[now.month]} {now.year}, {_GUN[now.weekday()]}"
    if re.search(r"hangi aydayiz|hangi yildayiz|kacinci yil", t):
        return f"📅 {_AY[now.month]} {now.year}"
    return None


# ── Ana motor ────────────────────────────────────────────────────────────────
class AnkaNLP:
    K1, B = 1.5, 0.75

    def __init__(self):
        self.ready = False
        self.docs, self.doclen = [], []
        self.post = defaultdict(dict)
        self.total_len = 0
        self.qvocab = set()
        self._qvocab_list = None
        self.last_topic = None
        self._lock = threading.RLock()
        self.keymap = {}
        self.last_query = None

    # ── İndeks ───────────────────────────────────────────────────────────────
    def build(self):
        with self._lock:
            if self.ready:
                return
            forgotten = set(self._forgotten_load())
            rows = []
            try:
                from anka_knowledge_db import get_db
                with get_db()._conn() as c:
                    rows += [(r["question"], r["answer"], r["category"] == "ogrenilen") for r in
                             c.execute("SELECT question, answer, category FROM qa "
                                       "ORDER BY (category='ogrenilen') DESC, id")]
            except Exception as e:
                print(f"[ANKA-NLP] DB okunamadı: {e}")
            try:
                from anka_training_data import TRAINING_DATA
                for items in TRAINING_DATA.values():
                    rows += [(i["q"], i["a"], False) for i in items]
            except Exception:
                pass
            seen = set()
            for q, a, taught in rows:
                key = lower_tr(q).strip()
                if not key or key in seen:
                    continue
                if key in forgotten and not taught:
                    continue
                seen.add(key)
                self._add_doc(q, a, taught)
            self.ready = True
            print(f"[ANKA-NLP] ✅ {len(self.docs):,} kayıt indekslendi")

    def _add_doc(self, q, a, taught=False):
        with self._lock:
            qt = tokens(q)
            if not qt:
                return None
            key = lower_tr(q).strip()
            old = self.keymap.get(key)
            if old is not None:
                self.docs[old]["dead"] = True
            terms = qt * 3 + tokens(a)[:60]
            did = len(self.docs)
            self.docs.append({"id": did, "q": q, "a": a, "qset": set(qt), "taught": taught})
            self.keymap[key] = did
            self.doclen.append(len(terms))
            self.total_len += len(terms)
            for term, tf in Counter(terms).items():
                self.post[term][did] = tf
            self.qvocab.update(qt)
            self._qvocab_list = None
            return did

    def _forgotten_load(self):
        try:
            if os.path.exists(FORGET_FILE):
                with open(FORGET_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        return []

    def _forgotten_save(self, keys):
        try:
            with open(FORGET_FILE, "w", encoding="utf-8") as f:
                json.dump(sorted(set(keys)), f, ensure_ascii=False)
        except Exception:
            pass

    # ── Yazım düzeltme ───────────────────────────────────────────────────────
    def _fix_typos(self, toks):
        if self._qvocab_list is None:
            self._qvocab_list = list(self.qvocab)
        out = []
        for t in toks:
            if t in self.qvocab or len(t) <= 3 or t.isdigit():
                out.append(t)
                continue
            m = difflib.get_close_matches(t, self._qvocab_list, n=1, cutoff=0.78)
            out.append(m[0] if m else t)
        return out

    # ── Arama ────────────────────────────────────────────────────────────────
    def _match(self, toks):
        with self._lock:
            return self._match_inner(toks)

    def _match_inner(self, toks):
        if not toks or not self.docs:
            return None
        toks = self._fix_typos(toks)
        qs = set(toks)
        N = len(self.docs)
        avgdl = self.total_len / N
        scores = defaultdict(float)
        for t in qs:
            p = self.post.get(t)
            if not p:
                continue
            idf = math.log(1 + (N - len(p) + 0.5) / (len(p) + 0.5))
            for d, tf in p.items():
                if self.docs[d].get("dead"):
                    continue
                scores[d] += idf * tf * (self.K1 + 1) / (
                    tf + self.K1 * (1 - self.B + self.B * self.doclen[d] / avgdl))
        if not scores:
            return None
        top = sorted(scores.items(), key=lambda x: -x[1])[:15]
        best, best_final, best_f1 = None, -1, 0
        for d, s in top:
            qset = self.docs[d]["qset"]
            inter = len(qs & qset)
            if not inter:
                continue
            prec, rec = inter / len(qset), inter / len(qs)
            f1 = 2 * prec * rec / (prec + rec)
            final = f1 + 0.1 * s / top[0][1] + (0.15 if self.docs[d].get("taught") else 0)
            if final > best_final:
                best, best_final, best_f1 = d, final, f1
        if best is None:
            return None
        ranked = [self.docs[d]["q"] for d, _ in top[:3]]
        return {"doc": self.docs[best], "confidence": best_f1, "similar": ranked}

    def _topic_of(self, doc):
        qs = doc["qset"]
        return min(qs, key=lambda t: (len(self.post.get(t, {})), -len(t))) if qs else None

    # ── Öğrenme / düzeltme / unutma ──────────────────────────────────────────
    def _db_exec(self, sql, params=()):
        try:
            from anka_knowledge_db import get_db
            with get_db()._conn() as c:
                c.execute(sql, params)
                c.commit()
        except Exception as e:
            print(f"[ANKA-NLP] DB yazma hatası: {e}")

    def teach(self, q, a):
        """Soru-cevap öğrenir (kalıcı). Aynı soru varsa üzerine yazar."""
        q, a = (q or "").strip(), (a or "").strip()
        if not q or not a:
            return False
        if not self.ready:
            self.build()
        key = lower_tr(q).strip()
        self._db_exec("DELETE FROM qa WHERE lower(question)=? AND category='ogrenilen'", (key,))
        self._db_exec("INSERT INTO qa (category, question, answer, keywords) "
                      "VALUES ('ogrenilen', ?, ?, '')", (key, a))
        ok = self._add_doc(q, a, taught=True) is not None
        fk = self._forgotten_load()
        if key in fk:
            self._forgotten_save([k for k in fk if k != key])
        self.pop_unanswered(q)
        return ok

    learn = teach

    def forget(self, q):
        """Bir bilgiyi unutturur. Unutulan sorunun metnini döner, yoksa None."""
        if not self.ready:
            self.build()
        key = lower_tr(q).strip()
        did = self.keymap.get(key)
        if did is None:
            res = self._match(tokens(q))
            if res and res["confidence"] >= 0.8:
                did = res["doc"]["id"]
                key = lower_tr(res["doc"]["q"]).strip()
        if did is None or self.docs[did].get("dead"):
            return None
        with self._lock:
            self.docs[did]["dead"] = True
            self.keymap.pop(key, None)
        fk = set(self._forgotten_load())
        fk.add(key)
        self._forgotten_save(fk)
        self._db_exec("DELETE FROM qa WHERE lower(question)=?", (key,))
        return self.docs[did]["q"]

    def correct_last(self, new_answer):
        """Son sorulan sorunun cevabını düzeltir."""
        if not self.last_query:
            return None
        q = self.last_query
        return q if self.teach(q, new_answer) else None

    # ── Cevaplanamayan sorular ───────────────────────────────────────────────
    def _unanswered(self):
        try:
            if os.path.exists(UNANSWERED_FILE):
                with open(UNANSWERED_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        return {}

    def _save_unanswered(self, d):
        try:
            with open(UNANSWERED_FILE, "w", encoding="utf-8") as f:
                json.dump(d, f, ensure_ascii=False, indent=1)
        except Exception:
            pass

    def _log_unanswered(self, text):
        if len(text.strip()) < 3:
            return
        d = self._unanswered()
        k = text.strip()[:120]
        d[k] = d.get(k, 0) + 1
        self._save_unanswered(d)

    def pop_unanswered(self, q):
        d = self._unanswered()
        fk = fold(q).strip()
        rm = [k for k in d if fold(k).strip() == fk]
        for k in rm:
            d.pop(k)
        if rm:
            self._save_unanswered(d)

    def top_unanswered(self, n=50):
        d = self._unanswered()
        return [k for k, _ in sorted(d.items(), key=lambda x: -x[1])][:n]

    # ── Ana giriş ────────────────────────────────────────────────────────────
    def answer(self, text):
        """{'answer','confidence','kind'} veya None döner."""
        text = (text or "").strip()
        if not text:
            return None
        if not self.ready:
            self.build()

        m = re.match(r"^(?:anka\s+)?(?:öğren|ogren)\s*[:：]?\s*(.+?)\s*=\s*(.+)$",
                     text, re.I | re.S)
        if m:
            self.teach(m.group(1).strip(), m.group(2).strip())
            return {"answer": f"✅ Öğrendim! '{m.group(1).strip()}' sorulunca "
                              f"'{m.group(2).strip()[:60]}' diyeceğim.",
                    "confidence": 1.0, "kind": "learn"}

        d = dynamic_answer(text)
        if d:
            return {"answer": d, "confidence": 1.0, "kind": "dynamic"}
        mt = try_math(text)
        if mt:
            return {"answer": mt, "confidence": 1.0, "kind": "math"}

        self.last_query = text
        toks = tokens(text)
        res = self._match(toks)
        conf = res["confidence"] if res else 0
        # Devam sorusu: "peki nüfusu?" → önceki konuyla birleştir
        if conf < 0.6 and self.last_topic and 0 < len(toks) <= 4:
            res2 = self._match([self.last_topic] + toks)
            if res2 and res2["confidence"] >= max(0.6, conf):
                res, conf = res2, res2["confidence"]

        if res and conf >= 0.6:
            self.last_topic = self._topic_of(res["doc"])
            return {"answer": res["doc"]["a"], "confidence": conf, "kind": "answer"}
        if res and conf >= 0.45:
            sug = "\n".join(f"• {q}" for q in res["similar"])
            return {"answer": f"🤔 Tam emin olamadım. Şunlardan birini mi demek istedin?\n{sug}",
                    "confidence": conf, "kind": "suggest"}
        self._log_unanswered(text)
        return None


_nlp = None
def get_nlp():
    global _nlp
    if _nlp is None:
        _nlp = AnkaNLP()
    return _nlp
