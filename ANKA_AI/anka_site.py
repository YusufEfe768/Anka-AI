# ── ANKA SİTE — Site oluştur → GitHub Pages'e yayınla → Google'a hazırla ─────
# Modelsiz, API'siz. Yayın için ücretsiz GitHub hesabı + 'gh' (veya depo adresi) gerekir.
# Google: sahiplik doğrulamasını SEN yaparsın (Search Console); Anka gerisini hazırlar.
import os, re, json, html, shutil, subprocess, threading, time, datetime, webbrowser, secrets
import urllib.parse
from anka_config import BASE_DIR
from anka_nlp import fold

try:
    import requests
except ImportError:
    requests = None

SITES_DIR = os.path.join(BASE_DIR, "siteler")
META_DIR = os.path.join(SITES_DIR, "_meta")
LIVE_TIMEOUT = 300

# ── Yardımcılar ──────────────────────────────────────────────────────────────
_TR = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")

def slugify(s):
    s = re.sub(r"[^a-z0-9]+", "-", (s or "").translate(_TR).lower()).strip("-")
    return s[:40].strip("-") or "site"

def esc(s):
    return html.escape(str(s or ""), quote=True)

def safe_url(u):
    u = (u or "").strip()
    if not u:
        return "#"
    if re.match(r"^(https?://|mailto:|tel:)", u, re.I):
        return u
    if re.match(r"^[a-z][a-z0-9+.\-]*:", u, re.I):   # javascript:, data: vb. engellenir
        return "#"
    return "https://" + u

def valid_email(e):
    return bool(re.match(r"^[^@\s<>\"']+@[^@\s<>\"']+\.[^@\s<>\"']+$", (e or "").strip()))

def phone_digits(p):
    d = re.sub(r"\D", "", p or "")
    if d.startswith("00"):
        d = d[2:]
    elif d.startswith("0"):
        d = "90" + d[1:]
    elif len(d) == 10 and d.startswith("5"):
        d = "90" + d
    return d if 10 <= len(d) <= 15 else ""

THEMES = {"mavi": ("#2563eb", "#1d4ed8"), "mor": ("#7c3aed", "#6d28d9"),
          "yeşil": ("#059669", "#047857"), "turuncu": ("#ea580c", "#c2410c"),
          "kırmızı": ("#dc2626", "#b91c1c"), "pembe": ("#db2777", "#be185d")}
_COLOR_ALIASES = {"mavi": "mavi", "mor": "mor", "yesil": "yeşil", "turuncu": "turuncu",
                  "kirmizi": "kırmızı", "pembe": "pembe"}

def parse_color(t):
    return _COLOR_ALIASES.get(fold(t).strip(), "mavi")

def parse_items(text):
    out = []
    for part in re.split(r"[;\n]+", text or ""):
        part = part.strip()
        if not part:
            continue
        if re.match(r"^https?://", part, re.I):
            out.append({"t": urllib.parse.urlparse(part).netloc or part, "d": part})
        elif ":" in part:
            a, b = part.split(":", 1)
            out.append({"t": a.strip(), "d": b.strip()})
        else:
            out.append({"t": part, "d": ""})
    return [i for i in out if i["t"]]

def parse_github_remote(url):
    url = (url or "").strip()
    m = (re.match(r"^https?://(?:www\.)?github\.com/([^/\s]+)/([^/\s]+?)(?:\.git)?/?$", url, re.I)
         or re.match(r"^git@github\.com:([^/\s]+)/([^/\s]+?)(?:\.git)?$", url, re.I))
    return (m.group(1), m.group(2)) if m else None

def pages_url(login, repo):
    host = f"{login.lower()}.github.io"
    return f"https://{host}" if repo.lower() == host else f"https://{host}/{repo}"

KIND_INFO = {
    "portfolyo": {"emoji": "💼", "label": "Portfolyo",
                  "items_q": "Projelerini yaz: 'proje adı: açıklama' (birden çoksa ; ile ayır)"},
    "isletme":   {"emoji": "🏪", "label": "İşletme",
                  "items_q": "Hizmetlerini yaz: 'hizmet: açıklama' (birden çoksa ; ile ayır)"},
    "blog":      {"emoji": "📝", "label": "Blog",
                  "items_q": "İlk yazılarını yaz: 'başlık: yazı metni' (birden çoksa ; ile ayır)"},
    "link":      {"emoji": "🔗", "label": "Link sayfası",
                  "items_q": "Bağlantılarını yaz: 'etiket: https://adres' (birden çoksa ; ile ayır)"},
}
FIELDS = [
    ("title", "Site adı / ismin ne olsun?", False),
    ("tagline", "Kısa bir slogan ya da meslek yaz (örn: Yazılım geliştirici)", False),
    ("about", "Hakkında 1-2 cümle yaz", False),
    ("items", None, False),
    ("email", "E-posta adresin? ('geç' diyebilirsin)", True),
    ("phone", "WhatsApp numaran? ('geç' diyebilirsin)", True),
    ("color", "Renk? mavi / mor / yeşil / turuncu / kırmızı / pembe ('geç' = mavi)", True),
]

def detect_kind(f):
    if re.search(r"portfol|portfoy|kisisel|ozgecmis|\bcv\b", f): return "portfolyo"
    if re.search(r"isletme|dukkan|kafe|restoran|firma|sirket|magaza|esnaf|hizmet", f): return "isletme"
    if re.search(r"blog|yazi", f): return "blog"
    if re.search(r"link|bio|baglanti|linktree", f): return "link"
    return None

# ── Render ───────────────────────────────────────────────────────────────────
CSS = """:root{--accent:%ACCENT%;--accent2:%ACCENT2%;--bg:#fff;--fg:#0f172a;--muted:#475569;--card:#f1f5f9;--border:#e2e8f0}
@media (prefers-color-scheme:dark){:root{--bg:#0b1020;--fg:#e5e7eb;--muted:#94a3b8;--card:#131a2e;--border:#1f2a44}}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;background:var(--bg);color:var(--fg);line-height:1.65}
a{color:var(--accent)}
.wrap{max-width:900px;margin:0 auto;padding:0 20px}
.nav{padding:18px 20px}.brand{font-weight:700;text-decoration:none;color:var(--fg)}
.hero{padding:64px 20px 40px;text-align:center}
.hero h1{font-size:clamp(2rem,6vw,3.2rem);line-height:1.15;margin-bottom:12px}
.tag{color:var(--muted);font-size:1.15rem;max-width:620px;margin:0 auto 24px}
.btn{display:inline-block;background:var(--accent);color:#fff;padding:12px 22px;border-radius:999px;text-decoration:none;font-weight:600;margin:4px}
.btn.ghost{background:transparent;color:var(--accent);border:2px solid var(--accent)}
section{padding:32px 20px}h2{margin-bottom:16px;font-size:1.5rem}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px}
.card{background:var(--card);border:1px solid var(--border);border-radius:16px;padding:20px}
.card h3{margin-bottom:6px}.card p,.meta{color:var(--muted)}
.card a{text-decoration:none;color:inherit}.card a:hover h3{color:var(--accent)}
.linkbtn{display:block;text-align:center;background:var(--card);border:2px solid var(--accent);color:var(--fg);padding:14px;border-radius:14px;margin:10px 0;text-decoration:none;font-weight:600}
.linkbtn:hover{background:var(--accent);color:#fff}
.center{text-align:center}.avatar{font-size:64px}
article p{margin-bottom:16px;font-size:1.05rem}
footer{padding:32px 20px;text-align:center;color:var(--muted);font-size:.9rem}
"""

def _url(base, file):
    if not base:
        return None
    return base + "/" if file == "index.html" else f"{base}/{file}"

def _contact(site):
    out = []
    ph = phone_digits(site.get("phone"))
    if ph:
        out.append(f'<a class="btn" href="https://wa.me/{ph}" rel="noopener">WhatsApp</a>')
    if valid_email(site.get("email")):
        out.append(f'<a class="btn ghost" href="mailto:{esc(site["email"].strip())}">E-posta</a>')
    return " ".join(out)

def _jsonld_tag(obj):
    safe = (json.dumps(obj, ensure_ascii=False).replace("<", "\\u003c")
            .replace(">", "\\u003e").replace("&", "\\u0026"))
    return '<script type="application/ld+json">' + safe + "</script>"

def _post_files(site):
    names, used = [], set()
    for it in site.get("items", []):
        base = "yazi-" + slugify(it["t"])
        n, i = base + ".html", 2
        while n in used:
            n = f"{base}-{i}.html"; i += 1
        used.add(n); names.append(n)
    return names

def _page(site, file, title, desc, body, base, og="website", jsonld=None):
    kind = KIND_INFO[site["kind"]]
    full = title if title == site["title"] else f"{title} — {site['title']}"
    url = _url(base, file)
    head = ['<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            f"<title>{esc(full)}</title>",
            f'<meta name="description" content="{esc(desc)}">']
    if site.get("google_meta"):
        head.append(f'<meta name="google-site-verification" content="{esc(site["google_meta"])}">')
    if url:
        head += [f'<link rel="canonical" href="{esc(url)}">', f'<meta property="og:url" content="{esc(url)}">']
    head += [f'<meta property="og:title" content="{esc(full)}">',
             f'<meta property="og:description" content="{esc(desc)}">',
             f'<meta property="og:type" content="{og}">', '<meta property="og:locale" content="tr_TR">',
             '<meta name="twitter:card" content="summary">',
             f'<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 100 100%27%3E%3Ctext y=%27.9em%27 font-size=%2790%27%3E{kind["emoji"]}%3C/text%3E%3C/svg%3E">',
             '<link rel="stylesheet" href="style.css">']
    if jsonld:
        head.append(_jsonld_tag(jsonld))
    year = datetime.date.today().year
    nav = f'<nav class="nav wrap"><a class="brand" href="index.html">{kind["emoji"]} {esc(site["title"])}</a></nav>'
    foot = f'<footer>© {year} {esc(site["title"])}</footer>'
    return ('<!doctype html>\n<html lang="tr">\n<head>\n' + "\n".join(head) +
            f"\n</head>\n<body>\n{nav}\n{body}\n{foot}\n</body>\n</html>\n")

def _index_body(site):
    k, t = site["kind"], esc(site["title"])
    tag, about = esc(site.get("tagline")), esc(site.get("about"))
    items, contact = site.get("items", []), _contact(site)
    hero = lambda cta: f'<header class="hero wrap"><h1>{t}</h1><p class="tag">{tag}</p>{cta}</header>'
    if k == "link":
        links = "".join(f'<a class="linkbtn" href="{esc(safe_url(i["d"]))}" rel="noopener">{esc(i["t"])}</a>' for i in items)
        return (f'<main class="wrap center"><div class="avatar">{KIND_INFO[k]["emoji"]}</div><h1>{t}</h1>'
                f'<p class="tag">{tag}</p>{links}<p>{contact}</p></main>')
    cards = "".join(f'<div class="card"><h3>{esc(i["t"])}</h3><p>{esc(i["d"])}</p></div>' for i in items)
    if k == "blog":
        files = _post_files(site)
        posts = "".join(
            f'<div class="card"><a href="{files[n]}"><h3>{esc(i["t"])}</h3>'
            f'<p class="meta">{esc(i.get("date",""))}</p><p>{esc(_excerpt(i["d"]))}</p></a></div>'
            for n, i in enumerate(items))
        return (hero("") + f'<section class="wrap" id="yazilar"><h2>Yazılar</h2><div class="grid">{posts}</div></section>'
                + (f'<section class="wrap" id="hakkinda"><h2>Hakkında</h2><p>{about}</p></section>' if about else "")
                + (f'<section class="wrap center" id="iletisim"><h2>İletişim</h2><p>{contact}</p></section>' if contact else ""))
    heading = "Projeler" if k == "portfolyo" else "Hizmetler"
    about_h = "Hakkımda" if k == "portfolyo" else "Hakkımızda"
    cta = f'<p><a class="btn" href="#iletisim">İletişime geç</a></p>'
    return (hero(cta)
            + (f'<section class="wrap" id="hakkinda"><h2>{about_h}</h2><p>{about}</p></section>' if about else "")
            + (f'<section class="wrap" id="liste"><h2>{heading}</h2><div class="grid">{cards}</div></section>' if items else "")
            + f'<section class="wrap center" id="iletisim"><h2>İletişim</h2><p>{contact or "Yakında…"}</p></section>')

def _excerpt(text):
    t = re.sub(r"\s+", " ", text or "").strip()
    return t[:140] + ("…" if len(t) > 140 else "")

def _site_ld(site, base):
    d = {"@context": "https://schema.org",
         "@type": {"portfolyo": "Person", "isletme": "Organization", "blog": "Blog"}.get(site["kind"], "WebSite"),
         "name": site["title"], "description": site.get("tagline") or site.get("about") or site["title"]}
    if base:
        d["url"] = base + "/"
    return d

def render_site(site):
    """Siteyi diske yazar. Döner: yazılan dosya adları."""
    d = site_dir(site)
    os.makedirs(d, exist_ok=True)
    base = (site.get("base_url") or "").rstrip("/") or None
    acc, acc2 = THEMES.get(site.get("color", "mavi"), THEMES["mavi"])
    files = {}
    files["style.css"] = CSS.replace("%ACCENT%", acc).replace("%ACCENT2%", acc2)
    desc = _excerpt(" ".join(x for x in (site.get("tagline"), site.get("about")) if x)) or site["title"]
    files["index.html"] = _page(site, "index.html", site["title"], desc, _index_body(site), base,
                                jsonld=_site_ld(site, base))
    if site["kind"] == "blog":
        for fn, it in zip(_post_files(site), site.get("items", [])):
            paras = "".join(f"<p>{esc(p)}</p>" for p in re.split(r"\n+", it["d"]) if p.strip())
            body = (f'<main class="wrap"><article><h1>{esc(it["t"])}</h1><p class="meta">{esc(it.get("date",""))}</p>'
                    f'{paras}<p><a href="index.html">← Tüm yazılar</a></p></article></main>')
            ld = {"@context": "https://schema.org", "@type": "BlogPosting", "headline": it["t"],
                  "datePublished": it.get("date", ""), "inLanguage": "tr",
                  "author": {"@type": "Person", "name": site["title"]}}
            if _url(base, fn):
                ld["url"] = _url(base, fn)
            files[fn] = _page(site, fn, it["t"], _excerpt(it["d"]) or it["t"], body, base, "article", ld)
    files["404.html"] = _page(site, "404.html", "Sayfa bulunamadı", "Sayfa bulunamadı",
                              '<main class="wrap center"><h1>404</h1><p>Aradığın sayfa yok.</p>'
                              '<p><a class="btn" href="index.html">Ana sayfa</a></p></main>', None)
    files[".nojekyll"] = ""
    if site.get("indexnow_key"):
        files[site["indexnow_key"] + ".txt"] = site["indexnow_key"]
    if site.get("google_file"):
        files[site["google_file"]] = f"google-site-verification: {site['google_file']}"
    today = datetime.date.today().isoformat()
    if base:
        urls = [_url(base, "index.html")] + [_url(base, fn) for fn in files
                                             if fn.startswith("yazi-")]
        files["sitemap.xml"] = ('<?xml version="1.0" encoding="UTF-8"?>\n'
                                '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
                                "".join(f"<url><loc>{html.escape(u)}</loc><lastmod>{today}</lastmod></url>\n" for u in urls) +
                                "</urlset>\n")
        files["robots.txt"] = f"User-agent: *\nAllow: /\n\nSitemap: {base}/sitemap.xml\n"
    else:
        files["robots.txt"] = "User-agent: *\nAllow: /\n"
    for fn in os.listdir(d):                       # silinmiş yazıların sayfalarını temizle
        if fn.startswith("yazi-") and fn.endswith(".html") and fn not in files:
            os.remove(os.path.join(d, fn))
    for fn, content in files.items():
        with open(os.path.join(d, fn), "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
    return sorted(files)

def site_dir(site):
    return os.path.join(SITES_DIR, site["slug"])

def _meta_path(slug):
    return os.path.join(META_DIR, slug + ".json")

def save_site(site):
    os.makedirs(META_DIR, exist_ok=True)
    site["updated"] = datetime.datetime.now().isoformat(timespec="seconds")
    with open(_meta_path(site["slug"]), "w", encoding="utf-8") as f:
        json.dump(site, f, ensure_ascii=False, indent=1)

def load_sites():
    out = []
    if os.path.isdir(META_DIR):
        for fn in os.listdir(META_DIR):
            if fn.endswith(".json"):
                try:
                    with open(os.path.join(META_DIR, fn), "r", encoding="utf-8") as f:
                        out.append(json.load(f))
                except Exception:
                    pass
    return sorted(out, key=lambda s: s.get("updated", ""), reverse=True)

def create_site(kind, data):
    slug, n = slugify(data["title"]), 2
    taken = {s["slug"] for s in load_sites()}
    base_slug = slug
    while slug in taken or os.path.exists(os.path.join(SITES_DIR, slug)):
        slug = f"{base_slug}-{n}"; n += 1
    today = datetime.date.today().isoformat()
    items = parse_items(data.get("items", ""))
    for it in items:
        it["date"] = today
    site = {"kind": kind, "slug": slug, "title": data["title"].strip(),
            "tagline": (data.get("tagline") or "").strip(), "about": (data.get("about") or "").strip(),
            "items": items, "email": (data.get("email") or "").strip(), "phone": (data.get("phone") or "").strip(),
            "color": data.get("color") or "mavi", "indexnow_key": secrets.token_hex(16),
            "created": today, "base_url": None}
    render_site(site)
    save_site(site)
    return site

# ── Komut çalıştırma ─────────────────────────────────────────────────────────
def _run(cmd, cwd=None, timeout=120):
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0")
    kw = {"creationflags": 0x08000000} if os.name == "nt" else {}
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=timeout, env=env, **kw)
        return r.returncode == 0, ((r.stdout or "") + (r.stderr or "")).strip()
    except subprocess.TimeoutExpired:
        return False, "zaman aşımı"
    except Exception as e:
        return False, str(e)

def _git_prepare(d, msg="Anka site güncellemesi"):
    git = shutil.which("git")
    if not os.path.isdir(os.path.join(d, ".git")):
        ok, out = _run([git, "init"], d)
        if not ok:
            return False, out
        _run([git, "symbolic-ref", "HEAD", "refs/heads/main"], d)
    _run([git, "add", "-A"], d)
    ident = []
    if not _run([git, "config", "user.email"], d)[1].strip():
        ident = ["-c", "user.name=Anka", "-c", "user.email=anka@users.noreply.github.com"]
    ok, out = _run([git] + ident + ["commit", "-m", msg], d)
    if not ok and "nothing to commit" in out.lower():
        return True, out
    return ok, out

def _git_sync(d, remote=None):
    git = shutil.which("git")
    ok, out = _git_prepare(d)
    if not ok:
        return False, out
    if remote:
        if _run([git, "remote", "get-url", "origin"], d)[0]:
            _run([git, "remote", "set-url", "origin", remote], d)
        else:
            _run([git, "remote", "add", "origin", remote], d)
    return _run([git, "push", "-u", "origin", "main"], d, 180)

HELP_PUBLISH = ("🌐 Yayınlamak için bir kerelik kurulum gerekiyor (ücretsiz):\n"
                "1️⃣ github.com'da hesap aç\n2️⃣ GitHub CLI kur:  winget install GitHub.cli\n"
                "3️⃣ Terminalde bir kez:  gh auth login\nSonra 'siteyi yayınla' yazman yeterli.\n\n"
                "Ya da github.com'da boş bir depo (repo) aç ve:\nsiteyi yayınla https://github.com/KULLANICI/DEPO")

HELP = ("🌐 SİTE KOMUTLARI\n════════════════\n"
        "• site oluştur → sorularla site kurar\n"
        "• site oluştur portfolyo | Ad | Slogan | Hakkında | proje: açıklama; ... | mail | tel | renk\n"
        "  (türler: portfolyo, işletme, blog, link)\n"
        "• sitelerim · site önizle [ad] · site yenile [ad]\n"
        "• siteyi yayınla [ad] [github-depo-adresi]\n"
        "• yazı ekle [ad] | başlık | metin   (blog)\n"
        "• google'a ekle [ad]   → adımları gösterir\n"
        "• google doğrulama [ad] google123abc.html   (veya etiket kodu)\n"
        "• google sitemap [ad] → sitemap sayfasını açar\n"
        "• indexnow [ad] → Bing/Yandex'e bildirir\n"
        "• google'da ara [ad] → indekslendi mi bak (site:)")

# ── Yönetici ─────────────────────────────────────────────────────────────────
class SiteManager:
    def __init__(self):
        self.wiz = None
        self.last = None
        self.notify = lambda m: print(f"[ANKA-SİTE] {m}")
        self._thread = None

    def set_notifier(self, fn):
        self.notify = fn

    # ── site seçme
    def _find(self, words):
        sites = load_sites()
        for w in words:
            sl = slugify(w)
            for s in sites:
                if s["slug"] == sl:
                    return s
        if self.last:
            for s in sites:
                if s["slug"] == self.last:
                    return s
        return sites[0] if len(sites) == 1 else None

    def _need_site(self, words):
        s = self._find(words)
        if s:
            self.last = s["slug"]
            return s, None
        sites = load_sites()
        if not sites:
            return None, "📭 Henüz site yok. 'site oluştur' yaz."
        return None, "🤔 Hangi site? " + ", ".join(x["slug"] for x in sites)

    # ── sihirbaz
    def _start_wizard(self, kind=None):
        self.wiz = {"kind": kind, "i": 0, "data": {}}
        if kind is None:
            return ("🌐 Hangi tür site yapalım?\n💼 portfolyo (kişisel/CV)\n🏪 işletme (dükkan, kafe, firma)\n"
                    "📝 blog\n🔗 link sayfası (tek sayfada tüm linkler)\n\n(Vazgeçmek için 'iptal')")
        return self._wiz_prompt()

    def _wiz_prompt(self):
        w = self.wiz
        key, q, opt = FIELDS[w["i"]]
        q = q or KIND_INFO[w["kind"]]["items_q"]
        return f"({w['i']+1}/{len(FIELDS)}) {q}"

    def _set_field(self, data, key, t):
        if key == "email" and not valid_email(t):
            return "🤔 E-posta geçerli görünmüyor. Tekrar yaz ya da 'geç'."
        if key == "phone" and not phone_digits(t):
            return "🤔 Numara geçerli görünmüyor (örn 0532 123 45 67). Tekrar yaz ya da 'geç'."
        if key == "items" and not parse_items(t):
            return "🤔 En az bir madde yaz (örn: 'Anka: Yapay zeka asistanı')."
        data[key] = parse_color(t) if key == "color" else t.strip()
        return None

    def _wiz_answer(self, t):
        w = self.wiz
        if w["kind"] is None:
            k = detect_kind(fold(t))
            if not k:
                return "🤔 Hangisi? portfolyo / işletme / blog / link"
            w["kind"] = k
            return self._wiz_prompt()
        key, q, opt = FIELDS[w["i"]]
        if fold(t) in ("gec", "atla"):
            if not opt:
                return "Bu alan zorunlu, kısaca yazar mısın?"
        else:
            err = self._set_field(w["data"], key, t)
            if err:
                return err
        w["i"] += 1
        if w["i"] >= len(FIELDS):
            kind, data = w["kind"], w["data"]
            self.wiz = None
            return self._finish(kind, data)
        return self._wiz_prompt()

    def _finish(self, kind, data):
        site = create_site(kind, data)
        self.last = site["slug"]
        try:
            webbrowser.open("file:///" + os.path.join(site_dir(site), "index.html").replace("\\", "/"))
        except Exception:
            pass
        return (f"✅ Site hazır: {site['title']}\n📁 {site_dir(site)}\n👀 Önizlemeyi tarayıcıda açtım.\n\n"
                f"Sıradaki:\n• 'siteyi yayınla' → GitHub Pages (ücretsiz)\n• sonra 'google'a ekle'")

    def _oneshot(self, parts):
        kind = detect_kind(fold(parts[0]))
        if not kind:
            return "🤔 Tür anlaşılmadı. portfolyo / işletme / blog / link"
        data = {}
        for (key, _, opt), val in zip(FIELDS, parts[1:]):
            val = val.strip()
            if val in ("", "-"):
                continue
            err = self._set_field(data, key, val)
            if err:
                return err
        if not data.get("title"):
            return "🤔 Site adı lazım: site oluştur portfolyo | Ad Soyad | Slogan | ..."
        return self._finish(kind, data)

    # ── yayınlama
    def publish(self, site, remote=None):
        self._thread = threading.Thread(target=self._publish_job, args=(site, remote), daemon=True)
        self._thread.start()
        return "🚀 Yayınlama başladı… (1-2 dk sürebilir, bitince haber veririm)"

    def _publish_job(self, site, remote):
        say = self.notify
        d = site_dir(site)
        git, gh = shutil.which("git"), shutil.which("gh")
        if not git:
            say("❌ Git bulunamadı. https://git-scm.com/download/win adresinden kur, sonra tekrar dene.")
            return
        try:
            has_origin, origin = False, ""
            if os.path.isdir(os.path.join(d, ".git")):
                has_origin, origin = _run([git, "remote", "get-url", "origin"], d)
            if has_origin:
                lr = parse_github_remote(origin)
                if lr:
                    site["repo"], site["base_url"] = f"{lr[0]}/{lr[1]}", pages_url(*lr)
                render_site(site)
                ok, msg = _git_sync(d)
                if not ok:
                    say(f"❌ Gönderilemedi:\n{msg[:300]}"); return
            elif remote:
                lr = parse_github_remote(remote)
                if not lr:
                    say("❌ Bu bir GitHub depo adresi gibi görünmüyor.\nÖrnek: https://github.com/kullanici/depo"); return
                site["repo"], site["base_url"] = f"{lr[0]}/{lr[1]}", pages_url(*lr)
                render_site(site)
                ok, msg = _git_sync(d, remote)
                if not ok:
                    say(f"❌ Gönderilemedi (GitHub girişi gerekebilir):\n{msg[:300]}"); return
                if gh:
                    _run([gh, "api", f"repos/{lr[0]}/{lr[1]}/pages", "-X", "POST", "-f", "build_type=legacy",
                          "-f", "source[branch]=main", "-f", "source[path]=/"], d)
                else:
                    webbrowser.open(f"https://github.com/{lr[0]}/{lr[1]}/settings/pages")
                    say("⚙️ Son adım (bir kerelik): açılan sayfada Branch: main / Folder: / (root) seçip Save'e bas.")
            elif gh:
                if not _run([gh, "auth", "status"], d)[0]:
                    say("🔑 GitHub'a giriş yapılmamış. Terminalde bir kez şunu çalıştır:  gh auth login\nSonra tekrar 'siteyi yayınla'."); return
                ok, login = _run([gh, "api", "user", "--jq", ".login"], d)
                login = login.strip()
                if not ok or not login:
                    say(f"❌ GitHub kullanıcı adı alınamadı:\n{login[:200]}"); return
                repo = site["slug"]
                site["repo"], site["base_url"] = f"{login}/{repo}", pages_url(login, repo)
                render_site(site)
                ok, msg = _git_prepare(d)
                if not ok:
                    say(f"❌ Git hatası:\n{msg[:300]}"); return
                ok, msg = _run([gh, "repo", "create", repo, "--public", "--source=.", "--remote=origin", "--push"], d, 180)
                if not ok:
                    site.pop("repo", None); site["base_url"] = None
                    say(f"❌ Depo oluşturulamadı:\n{msg[:300]}\n(Aynı adlı depo varsa site adını değiştir.)"); return
                ok, msg = _run([gh, "api", f"repos/{login}/{repo}/pages", "-X", "POST", "-f", "build_type=legacy",
                                "-f", "source[branch]=main", "-f", "source[path]=/"], d)
                if not ok and "already" not in msg.lower() and "409" not in msg:
                    say(f"⚠️ Pages otomatik açılamadı. Elle aç: https://github.com/{login}/{repo}/settings/pages (main / root)")
            else:
                say(HELP_PUBLISH); return
            site["published_at"] = datetime.datetime.now().isoformat(timespec="seconds")
            save_site(site)
            url = site["base_url"]
            say(f"✅ GitHub'a gönderildi!\n🌐 {url}\n⏳ Yayına girmesi 1-2 dk sürer, hazır olunca haber vereceğim.")
            if self._wait_live(url):
                say(f"🟢 Site yayında!\n{url}")
                say(self.indexnow(site))
            else:
                say(f"🟡 Henüz açılmadı (GitHub biraz geç kalabilir). Birkaç dk sonra dene:\n{url}")
            say("🔎 Google için: 'google'a ekle' yaz, adımları göstereyim.")
        except Exception as e:
            say(f"❌ Yayınlama hatası: {e}")

    def _wait_live(self, url):
        if not requests:
            return False
        end = time.time() + LIVE_TIMEOUT
        while True:
            try:
                r = requests.get(url + "/", timeout=8)
                if r.status_code == 200 and "<title" in r.text:
                    return True
            except Exception:
                pass
            if time.time() >= end:
                return False
            time.sleep(10)

    # ── Arama motorları
    def indexnow(self, site):
        base = (site.get("base_url") or "").rstrip("/")
        if not base:
            return "❌ Önce siteyi yayınla."
        if not requests:
            return "❌ 'requests' kütüphanesi yok."
        urls = [base + "/"] + [f"{base}/{fn}" for fn in _post_files(site)]
        payload = {"host": urllib.parse.urlparse(base).netloc, "key": site["indexnow_key"],
                   "keyLocation": f"{base}/{site['indexnow_key']}.txt", "urlList": urls}
        try:
            r = requests.post("https://api.indexnow.org/indexnow", json=payload, timeout=15,
                              headers={"Content-Type": "application/json; charset=utf-8"})
            if r.status_code in (200, 202):
                return "📣 Bing/Yandex gibi IndexNow destekli motorlara bildirildi. (Google IndexNow'u desteklemiyor.)"
            return f"⚠️ IndexNow cevabı: {r.status_code} (site henüz yayında olmayabilir, sonra tekrar dene)"
        except Exception as e:
            return f"⚠️ IndexNow gönderilemedi: {e}"

    def google_assist(self, site):
        base = (site.get("base_url") or "").rstrip("/")
        if not base:
            return "❌ Önce siteyi yayınla: 'siteyi yayınla'. Google, yayında olmayan siteyi göremez."
        try:
            webbrowser.open("https://search.google.com/search-console/welcome")
        except Exception:
            pass
        if not (site.get("google_file") or site.get("google_meta")):
            return (f"🔎 GOOGLE'A EKLEME\nSearch Console'u açtım. Sahipliği Google hesabınla SEN doğrulamalısın:\n\n"
                    f"1️⃣ 'URL öneki'ni seç ve şunu yapıştır:\n{base}/\n"
                    f"2️⃣ Doğrulama yöntemi: 'HTML dosyası' → dosya adını (google….html) bana yaz:\n"
                    f"   google doğrulama google1234abcd.html\n   (ya da 'HTML etiketi' → kodu yaz: google doğrulama KOD)\n"
                    f"3️⃣ Ben siteye koyup yayınlarım, sen 'Doğrula'ya bas\n"
                    f"4️⃣ Sonra 'google sitemap' yaz, site haritası sayfasını açayım")
        return (f"🔎 Doğrulama dosyası/etiketi sitede hazır ✅\nSearch Console'da 'Doğrula'ya bastın mı?\n"
                f"Basıldıysa: 'google sitemap' yaz.\nİndekslenmesi günler sürebilir.")

    def google_sitemap(self, site):
        base = (site.get("base_url") or "").rstrip("/")
        if not base:
            return "❌ Önce siteyi yayınla."
        try:
            webbrowser.open("https://search.google.com/search-console/sitemaps?resource_id=" +
                            urllib.parse.quote(base + "/", safe=""))
        except Exception:
            pass
        return (f"🗺️ Site haritası sayfasını açtım.\n'Yeni site haritası ekle' kutusuna  sitemap.xml  yaz → Gönder.\n"
                f"(Sayfa açılmazsa: Search Console → mülkü seç → Dizin Oluşturma → Site Haritaları.)\n"
                f"Harita adresi: {base}/sitemap.xml")

    def google_verify(self, site, arg):
        arg = (arg or "").strip()
        m = re.search(r"content\s*=\s*[\"']([A-Za-z0-9_\-]{10,100})[\"']", arg)
        fm = re.search(r"\b(google[a-z0-9]{6,40}\.html)\b", arg, re.I)
        if fm:
            site["google_file"] = fm.group(1).lower()
            kind = f"doğrulama dosyası ({site['google_file']})"
        elif m or re.fullmatch(r"[A-Za-z0-9_\-]{20,100}", arg):
            site["google_meta"] = m.group(1) if m else arg
            kind = "doğrulama etiketi"
        else:
            return ("🤔 Anlayamadım. Search Console'daki dosya adını (google1234abcd.html) "
                    "ya da etiketteki kodu yaz.")
        render_site(site)
        save_site(site)
        if site.get("base_url"):
            return f"✅ {kind} siteye eklendi.\n" + self.publish(site) + "\nYayına girince Search Console'da 'Doğrula'ya bas."
        return f"✅ {kind} siteye eklendi. Siteyi yayınlayınca geçerli olur ('siteyi yayınla')."

    # ── Ana giriş
    def handle(self, text):
        t = (text or "").strip()
        if not t:
            return None
        f = fold(t)
        if self.wiz:
            if f in ("iptal", "vazgec", "dur", "iptal et"):
                self.wiz = None
                return "❌ Site oluşturma iptal edildi."
            return self._wiz_answer(t)
        words = re.findall(r"[\w\-]+", t)

        if re.search(r"\bsite yardim|\bsite rehber|\bsite komut", f):
            return HELP
        if re.search(r"^sitelerim\b|\bsite listesi|\bsiteleri listele", f):
            sites = load_sites()
            if not sites:
                return "📭 Henüz site yok. 'site oluştur' yaz."
            return "🌐 SİTELERİM\n" + "\n".join(
                f"• {s['slug']} ({KIND_INFO[s['kind']]['label']})" + (f" → {s['base_url']}" if s.get("base_url") else " — yayınlanmadı")
                for s in sites)

        if re.search(r"\b(?:web\s*)?site(?:si|yi)?\s+(?:olustur|yap|kur|hazirla)\b", f):
            if "|" in t:
                return self._oneshot(t.split("|"))
            return self._start_wizard(detect_kind(f))

        if re.search(r"\byazi ekle\b", f) and "|" in t:
            parts = t.split("|")
            site, err = self._need_site(re.findall(r"[\w\-]+", parts[0]))
            if err:
                return err
            if site["kind"] != "blog":
                return "🤔 Yazı sadece blog türü sitelere eklenir."
            if len(parts) < 3 or not parts[1].strip() or not parts[2].strip():
                return "Format: yazı ekle [site] | başlık | metin"
            site["items"].insert(0, {"t": parts[1].strip(), "d": "|".join(parts[2:]).strip(),
                                     "date": datetime.date.today().isoformat()})
            render_site(site); save_site(site)
            return f"✅ Yazı eklendi: {parts[1].strip()}\nYayınlamak için: 'siteyi yayınla'"

        if re.search(r"\bgoogle\w*\s+dogrulama\b", f):
            arg = re.split(r"dogrulama", fold(t), 1)[1] if "dogrulama" in fold(t) else ""
            raw = t[len(t) - len(arg):] if arg else ""
            site, err = self._need_site(raw.split()[:1])
            if err:
                return err
            return self.google_verify(site, raw)
        if re.search(r"\bgoogle\w*\W*\s*sitemap|\bsitemap\s+gonder", f):
            site, err = self._need_site(words)
            return err or self.google_sitemap(site)
        if re.search(r"\bgoogle\W*(?:a|e)?\s+(?:ekle|kaydet)\b|\bgoogle\W*da\s+yayinla\b", f):
            site, err = self._need_site(words)
            return err or self.google_assist(site)
        if re.search(r"\bgoogle\W*da\s+(?:ara|kontrol)", f):
            site, err = self._need_site(words)
            if err:
                return err
            if not site.get("base_url"):
                return "❌ Önce siteyi yayınla."
            host = site["base_url"].replace("https://", "")
            webbrowser.open("https://www.google.com/search?q=" + urllib.parse.quote("site:" + host))
            return f"🔍 'site:{host}' aramasını açtım. Sonuç yoksa henüz indekslenmemiş demektir (günler sürebilir)."
        if re.search(r"\bindexnow\b|\bbing\w*\s+(?:ekle|bildir)", f):
            site, err = self._need_site(words)
            return err or self.indexnow(site)

        if re.search(r"\bsite\w*\s+yayinla\b", f):
            remote = next((w for w in t.split() if parse_github_remote(w)), None)
            site, err = self._need_site(words)
            return err or self.publish(site, remote)
        if re.search(r"\bsite\w*\s+(?:onizle|ac)\b", f):
            site, err = self._need_site(words)
            if err:
                return err
            webbrowser.open("file:///" + os.path.join(site_dir(site), "index.html").replace("\\", "/"))
            return "👀 Önizlemeyi açtım."
        if re.search(r"\bsite\w*\s+yenile\b", f):
            site, err = self._need_site(words)
            if err:
                return err
            render_site(site)
            return f"🔄 '{site['slug']}' yeniden oluşturuldu. Yayınlamak için: 'siteyi yayınla'"
        return None


_sm = None
def get_site():
    global _sm
    if _sm is None:
        _sm = SiteManager()
    return _sm
