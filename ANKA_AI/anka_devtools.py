# ── ANKA GELİŞTİRİCİ ARAÇLAR MODÜLü ─────────────────────────────────────────
# Git, terminal, IDE entegrasyonu, kod analizi, API testi
import json, os, threading, datetime, subprocess, time, re
import requests, webbrowser
try:
    import pyperclip
except ImportError:
    class _PyClip:
        def copy(self,x):pass
        def paste(self):return ""
    pyperclip=_PyClip()
from anka_config import BASE_DIR

DEVTOOLS_FILE = os.path.join(BASE_DIR, "anka_devtools.json")

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

class GitHelper:
    def __init__(self, speak_func, msg_func):
        self.speak = speak_func
        self.msg = msg_func

    def run_git(self, cmd, cwd=None):
        try:
            result = subprocess.run(
                ["git"] + cmd.split(),
                capture_output=True, text=True,
                cwd=cwd or os.getcwd(),
                encoding='utf-8', errors='ignore', timeout=30)
            return result.stdout + result.stderr
        except Exception as e:
            return f"Git hatası: {e}"

    def status(self, path=None):
        return self.run_git("status --short", path)

    def log(self, path=None, count=5):
        return self.run_git(f"log --oneline -{count}", path)

    def diff(self, path=None):
        return self.run_git("diff --stat", path)

    def add_commit_push(self, message, path=None):
        def _p():
            self.msg("ANKA","⏳ Git işlemi yapılıyor...")
            r1 = self.run_git("add .", path)
            r2 = self.run_git(f'commit -m "{message}"', path)
            r3 = self.run_git("push", path)
            result = f"📤 Git Push:\n{r2}\n{r3}"
            self.msg("ANKA", result)
            self.speak("Değişiklikler push edildi efendim.")
        threading.Thread(target=_p, daemon=True).start()

    def create_branch(self, branch_name, path=None):
        r = self.run_git(f"checkout -b {branch_name}", path)
        return r

    def switch_branch(self, branch_name, path=None):
        r = self.run_git(f"checkout {branch_name}", path)
        return r

    def pull(self, path=None):
        def _p():
            r = self.run_git("pull", path)
            self.msg("ANKA", f"📥 Git Pull:\n{r}")
        threading.Thread(target=_p, daemon=True).start()

    def stash(self, path=None):
        r = self.run_git("stash", path)
        return r

    def stash_pop(self, path=None):
        r = self.run_git("stash pop", path)
        return r


class TerminalHelper:
    def __init__(self, speak_func, msg_func):
        self.speak = speak_func
        self.msg = msg_func

    def run_command(self, command, timeout=30):
        def _r():
            try:
                result = subprocess.run(
                    command, shell=True,
                    capture_output=True, text=True,
                    encoding='utf-8', errors='ignore',
                    timeout=timeout)
                output = (result.stdout + result.stderr)[:1000]
                self.msg("ANKA", f"💻 Terminal:\n```\n{output}\n```")
            except subprocess.TimeoutExpired:
                self.msg("ANKA", "Komut zaman aşımına uğradı efendim.")
            except Exception as e:
                self.msg("ANKA", f"Komut hatası: {e}")
        threading.Thread(target=_r, daemon=True).start()

    def pip_install(self, package):
        def _p():
            self.msg("ANKA", f"📦 {package} kuruluyor...")
            result = subprocess.run(
                ["pip","install",package,"--quiet"],
                capture_output=True, text=True,
                encoding='utf-8', errors='ignore', timeout=120)
            if result.returncode == 0:
                r = f"✓ {package} başarıyla kuruldu efendim!"
            else:
                r = f"Kurulum hatası:\n{result.stderr[:300]}"
            self.msg("ANKA", r); self.speak(r)
        threading.Thread(target=_p, daemon=True).start()

    def pip_list(self):
        result = subprocess.run(
            ["pip","list","--format=columns"],
            capture_output=True, text=True,
            encoding='utf-8', errors='ignore')
        return result.stdout[:800]

    def python_version(self):
        result = subprocess.run(
            ["python","--version"],
            capture_output=True, text=True)
        return result.stdout.strip()

    def open_terminal(self):
        subprocess.Popen("cmd.exe")

    def open_powershell(self):
        subprocess.Popen("powershell.exe")

    def open_vscode(self, path="."):
        subprocess.Popen(["code", path], shell=True)


class APITester:
    def __init__(self, speak_func, msg_func):
        self.speak = speak_func
        self.msg = msg_func
        self.history = []

    def get_request(self, url, headers=None):
        def _g():
            try:
                r = requests.get(url, headers=headers or {}, timeout=10)
                self.history.append({"method":"GET","url":url,"status":r.status_code})
                response_text = r.text[:500]
                try:
                    json_data = r.json()
                    response_text = json.dumps(json_data, indent=2, ensure_ascii=False)[:800]
                except: pass
                result = (f"🌐 GET {url}\n"
                         f"Status: {r.status_code}\n"
                         f"Response:\n{response_text}")
                self.msg("ANKA", result)
            except Exception as e:
                self.msg("ANKA", f"API hatası: {e}")
        threading.Thread(target=_g, daemon=True).start()

    def post_request(self, url, data=None, json_data=None):
        def _p():
            try:
                r = requests.post(url, data=data, json=json_data, timeout=10)
                self.history.append({"method":"POST","url":url,"status":r.status_code})
                response_text = r.text[:500]
                result = (f"🌐 POST {url}\n"
                         f"Status: {r.status_code}\n"
                         f"Response:\n{response_text}")
                self.msg("ANKA", result)
            except Exception as e:
                self.msg("ANKA", f"API hatası: {e}")
        threading.Thread(target=_p, daemon=True).start()


class CodeSnippets:
    def __init__(self, ollama, speak_func, msg_func):
        self.ollama = ollama
        self.speak = speak_func
        self.msg = msg_func
        self.snippets_file = os.path.join(BASE_DIR, "anka_snippets.json")
        self.snippets = _load(self.snippets_file, {})

    def save_snippet(self, name, code, language="python"):
        self.snippets[name] = {"code": code, "language": language,
                               "created": datetime.datetime.now().isoformat()}
        _save(self.snippets_file, self.snippets)

    def get_snippet(self, name):
        return self.snippets.get(name)

    def list_snippets(self):
        return list(self.snippets.keys())

    def generate_snippet(self, task, language="python"):
        def _g():
            r = self.ollama.chat(
                f"{language} ile '{task}' yapan kod yaz. Sadece kodu ver.",
                system_override=f"{language} uzmanı. Temiz, çalışan kod yaz.")
            self.msg("ANKA", f"💻 {language} Kodu:\n{r}")
            pyperclip.copy(r)
            self.speak("Kod hazırlandı ve kopyalandı efendim.")
        threading.Thread(target=_g, daemon=True).start()

    def regex_helper(self, pattern_desc):
        def _r():
            r = self.ollama.chat(
                f"'{pattern_desc}' için regex pattern yaz. Python formatında.",
                system_override="Regex uzmanı. Pattern ve açıklama ver.")
            self.msg("ANKA", f"🔍 Regex:\n{r}")
            pyperclip.copy(r)
        threading.Thread(target=_r, daemon=True).start()

    def convert_code(self, code, from_lang, to_lang):
        def _c():
            r = self.ollama.chat(
                f"Bu {from_lang} kodunu {to_lang}'e çevir:\n\n{code}",
                system_override=f"Kod çevirici. {from_lang}'den {to_lang}'e çevir.")
            self.msg("ANKA", f"🔄 {to_lang} Kodu:\n{r}")
            pyperclip.copy(r)
            self.speak("Kod çevrildi efendim.")
        threading.Thread(target=_c, daemon=True).start()


class DevToolsCommandProcessor:
    def __init__(self, speak_func, msg_func, ollama):
        self.speak = speak_func
        self.msg = msg_func
        self.ollama = ollama
        self.git = GitHelper(speak_func, msg_func)
        self.terminal = TerminalHelper(speak_func, msg_func)
        self.api = APITester(speak_func, msg_func)
        self.snippets = CodeSnippets(ollama, speak_func, msg_func)
        self.git_path = None

    def process(self, text):
        t = text.lower().strip()

        # ── Git ───────────────────────────────────────────────────────────────
        if "git durumu" in t or "git status" in t:
            def _s():
                r = self.git.status(self.git_path)
                self.msg("ANKA", f"📂 Git Status:\n{r or 'Temiz, değişiklik yok.'}")
            threading.Thread(target=_s, daemon=True).start()
            return True

        if "git log" in t or "commit geçmişi" in t:
            def _l():
                r = self.git.log(self.git_path)
                self.msg("ANKA", f"📋 Git Log:\n{r}")
            threading.Thread(target=_l, daemon=True).start()
            return True

        if "git push" in t or "değişiklikleri gönder" in t:
            msg_match = re.search(r'mesaj[:\s]+(.+)', t)
            commit_msg = msg_match.group(1).strip() if msg_match else "Anka ile güncellendi"
            self.git.add_commit_push(commit_msg, self.git_path)
            return True

        if "git pull" in t or "değişiklikleri çek" in t:
            self.git.pull(self.git_path)
            return True

        if "git branch oluştur" in t:
            branch = t.replace("git branch oluştur","").strip()
            if branch:
                def _b():
                    r = self.git.create_branch(branch, self.git_path)
                    self.msg("ANKA", f"✓ Branch '{branch}' oluşturuldu:\n{r}")
                threading.Thread(target=_b, daemon=True).start()
            return True

        if "git stash" in t:
            def _st():
                if "uygula" in t or "pop" in t:
                    r = self.git.stash_pop(self.git_path)
                else:
                    r = self.git.stash(self.git_path)
                self.msg("ANKA", f"📦 Git Stash:\n{r}")
            threading.Thread(target=_st, daemon=True).start()
            return True

        if "git klasörü ayarla" in t:
            path = t.replace("git klasörü ayarla","").strip()
            if os.path.exists(path):
                self.git_path = path
                r = f"✓ Git klasörü: {path}"
                self.msg("ANKA",r); self.speak(r)
            return True

        # ── Terminal ─────────────────────────────────────────────────────────
        if t.startswith("terminal:") or t.startswith("cmd:"):
            command = text.replace("terminal:","").replace("cmd:","").strip()
            if command:
                self.terminal.run_command(command)
            return True

        if "pip kur" in t or "pip install" in t:
            package = t.replace("pip kur","").replace("pip install","").strip()
            if package:
                self.terminal.pip_install(package)
            return True

        if "pip listesi" in t or "kurulu paketler" in t:
            def _pl():
                r = self.terminal.pip_list()
                self.msg("ANKA", f"📦 Kurulu Paketler:\n{r}")
            threading.Thread(target=_pl, daemon=True).start()
            return True

        if "python versiyonu" in t or "python sürümü" in t:
            v = self.terminal.python_version()
            r = f"🐍 {v}"
            self.msg("ANKA",r); self.speak(r)
            return True

        if "terminali aç" in t or "cmd aç" in t:
            self.terminal.open_terminal()
            r = "✓ Terminal açıldı efendim."; self.msg("ANKA",r); self.speak(r)
            return True

        if "powershell aç" in t:
            self.terminal.open_powershell()
            r = "✓ PowerShell açıldı efendim."; self.msg("ANKA",r); self.speak(r)
            return True

        if "vscode aç" in t or "vs code aç" in t:
            path = t.replace("vscode aç","").replace("vs code aç","").strip() or "."
            self.terminal.open_vscode(path)
            r = "✓ VS Code açıldı efendim."; self.msg("ANKA",r); self.speak(r)
            return True

        # ── API Test ──────────────────────────────────────────────────────────
        if t.startswith("get ") and "http" in t:
            url = re.search(r'https?://\S+', text)
            if url:
                self.api.get_request(url.group(0))
            return True

        if t.startswith("post ") and "http" in t:
            url = re.search(r'https?://\S+', text)
            if url:
                self.api.post_request(url.group(0))
            return True

        # ── Kod Snippet ───────────────────────────────────────────────────────
        if "kod üret" in t or "snippet üret" in t:
            task = t.replace("kod üret","").replace("snippet üret","").strip()
            lang = "python"
            for l in ["python","javascript","java","c++","c#","php","go","rust"]:
                if l in t: lang = l; break
            if task:
                self.snippets.generate_snippet(task, lang)
            return True

        if "regex yaz" in t or "regex pattern" in t:
            desc = t.replace("regex yaz","").replace("regex pattern","").strip()
            if desc:
                self.snippets.regex_helper(desc)
            return True

        if "kodu çevir" in t:
            m = re.search(r'(\w+)\'den\s+(\w+)\'e', t)
            if m:
                from_lang, to_lang = m.group(1), m.group(2)
                code = t.replace(m.group(0),"").replace("kodu çevir","").strip()
                if code:
                    self.snippets.convert_code(code, from_lang, to_lang)
            return True

        if "snippet kaydet" in t:
            parts = t.replace("snippet kaydet","").strip().split(":")
            if len(parts) >= 2:
                name = parts[0].strip()
                code = parts[1].strip()
                self.snippets.save_snippet(name, code)
                r = f"✓ '{name}' snippet'i kaydedildi efendim."
                self.msg("ANKA",r); self.speak(r)
            return True

        if "snippet listesi" in t or "snippetlerim" in t:
            snippets = self.snippets.list_snippets()
            if snippets:
                r = "💻 Kayıtlı Snippetler:\n" + "\n".join(f"• {s}" for s in snippets)
            else:
                r = "Kayıtlı snippet yok efendim."
            self.msg("ANKA",r); self.speak(r)
            return True

        if "snippet göster" in t:
            name = t.replace("snippet göster","").strip()
            snippet = self.snippets.get_snippet(name)
            if snippet:
                self.msg("ANKA", f"💻 {name}:\n{snippet['code']}")
                pyperclip.copy(snippet['code'])
                self.speak("Snippet kopyalandı efendim.")
            else:
                self.msg("ANKA", f"'{name}' bulunamadı efendim.")
            return True

        # ── Hata Ayıklama ─────────────────────────────────────────────────────
        if "hata açıkla" in t or "error açıkla" in t:
            error_text = t.replace("hata açıkla","").replace("error açıkla","").strip()
            if error_text:
                def _e():
                    r = self.ollama.chat(
                        f"Bu hatayı açıkla ve çözüm öner:\n{error_text}",
                        system_override="Senior developer. Hatayı açıkla, çözüm ver.")
                    self.msg("ANKA", f"🐛 Hata Analizi:\n{r}")
                threading.Thread(target=_e, daemon=True).start()
            return True

        # ── Dokümantasyon ─────────────────────────────────────────────────────
        if "dokümantasyon yaz" in t:
            code = t.replace("dokümantasyon yaz","").strip()
            if code:
                def _d():
                    r = self.ollama.chat(
                        f"Bu kod için docstring ve açıklama yaz:\n{code}",
                        system_override="Teknik yazar. Kapsamlı dokümantasyon yaz.")
                    self.msg("ANKA", f"📚 Dokümantasyon:\n{r}")
                    pyperclip.copy(r)
                threading.Thread(target=_d, daemon=True).start()
            return True

        # ── Güvenlik Testi ────────────────────────────────────────────────────
        if "port tara" in t:
            host = t.replace("port tara","").strip() or "localhost"
            def _pt():
                import socket
                open_ports = []
                common_ports = [21,22,23,25,53,80,110,143,443,3306,5432,6379,8080,8443,27017]
                for port in common_ports:
                    try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(0.5)
                        result = sock.connect_ex((host, port))
                        if result == 0:
                            open_ports.append(port)
                        sock.close()
                    except: pass
                if open_ports:
                    r = f"🔍 {host} Açık Portlar:\n" + "\n".join(f"• Port {p}" for p in open_ports)
                else:
                    r = f"{host} üzerinde yaygın açık port bulunamadı efendim."
                self.msg("ANKA", r)
            threading.Thread(target=_pt, daemon=True).start()
            return True

        return False
