# ── ANKA SİSTEM KONTROL MODÜLü ───────────────────────────────────────────────
# Gelişmiş bilgisayar yönetimi, süreç kontrolü, ağ yönetimi
import json, os, threading, datetime, subprocess, time, re
import psutil, requests
from anka_config import BASE_DIR

class ProcessManager:
    def __init__(self, speak_func, msg_func):
        self.speak = speak_func
        self.msg = msg_func

    def list_heavy(self, top=10):
        procs = []
        for p in psutil.process_iter(['name','cpu_percent','memory_info','pid']):
            try:
                cpu = p.info['cpu_percent'] or 0
                mem = p.info['memory_info'].rss // 1024 // 1024
                procs.append((p.info['name'], cpu, mem, p.info['pid']))
            except: pass
        procs.sort(key=lambda x: -x[2])
        r = "💾 En Çok RAM Kullananlar:\n"
        for name, cpu, mem, pid in procs[:top]:
            r += f"• {name[:25]}: {mem}MB RAM, %{cpu:.1f} CPU (PID:{pid})\n"
        return r

    def kill_process(self, name):
        killed = []
        for p in psutil.process_iter(['name','pid']):
            try:
                if name.lower() in p.info['name'].lower():
                    p.kill()
                    killed.append(p.info['name'])
            except: pass
        return killed

    def suspend_process(self, name):
        for p in psutil.process_iter(['name']):
            try:
                if name.lower() in p.info['name'].lower():
                    p.suspend()
                    return True
            except: pass
        return False

    def resume_process(self, name):
        for p in psutil.process_iter(['name']):
            try:
                if name.lower() in p.info['name'].lower():
                    p.resume()
                    return True
            except: pass
        return False

    def get_process_info(self, name):
        for p in psutil.process_iter(['name','pid','cpu_percent','memory_info','create_time','status']):
            try:
                if name.lower() in p.info['name'].lower():
                    mem = p.info['memory_info'].rss // 1024 // 1024
                    created = datetime.datetime.fromtimestamp(p.info['create_time']).strftime("%H:%M:%S")
                    return {
                        "name": p.info['name'],
                        "pid": p.info['pid'],
                        "cpu": p.info['cpu_percent'],
                        "mem": mem,
                        "status": p.info['status'],
                        "started": created
                    }
            except: pass
        return None


class NetworkManager:
    def __init__(self, speak_func, msg_func):
        self.speak = speak_func
        self.msg = msg_func

    def get_connections(self):
        try:
            conns = psutil.net_connections(kind='inet')
            active = [(c.laddr.port, c.raddr.ip if c.raddr else "—",
                      c.status) for c in conns if c.status == 'ESTABLISHED']
            return active[:15]
        except: return []

    def speed_test(self):
        def _s():
            self.msg("ANKA","🌐 Hız testi yapılıyor...")
            try:
                # Download hızı
                start = time.time()
                r = requests.get("https://speed.cloudflare.com/__down?bytes=10000000",
                                timeout=15, stream=True)
                data = b""
                for chunk in r.iter_content(chunk_size=8192):
                    data += chunk
                elapsed = time.time() - start
                down_mbps = round((len(data)*8/1_000_000)/elapsed, 2)
                result = f"🌐 İnternet Hızı:\n• İndirme: {down_mbps} Mbps"
                self.msg("ANKA", result)
                self.speak(f"İndirme hızınız {down_mbps} megabit efendim.")
            except Exception as e:
                self.msg("ANKA", f"Hız testi başarısız: {e}")
        threading.Thread(target=_s, daemon=True).start()

    def get_wifi_password(self):
        try:
            result = subprocess.run(
                ["netsh","wlan","show","profiles"],
                capture_output=True, text=True, encoding='utf-8', errors='ignore')
            profiles = re.findall(r"All User Profile\s*:\s*(.+)", result.stdout)
            passwords = {}
            for profile in profiles[:5]:
                profile = profile.strip()
                r2 = subprocess.run(
                    ["netsh","wlan","show","profile", profile, "key=clear"],
                    capture_output=True, text=True, encoding='utf-8', errors='ignore')
                pw = re.findall(r"Key Content\s*:\s*(.+)", r2.stdout)
                passwords[profile] = pw[0].strip() if pw else "Şifresiz"
            return passwords
        except: return {}

    def flush_dns(self):
        try:
            subprocess.run(["ipconfig","/flushdns"], capture_output=True)
            return True
        except: return False

    def get_ip_info(self):
        try:
            r = requests.get("https://ipapi.co/json/", timeout=5)
            d = r.json()
            return {
                "ip": d.get("ip","?"),
                "city": d.get("city","?"),
                "country": d.get("country_name","?"),
                "isp": d.get("org","?"),
                "timezone": d.get("timezone","?")
            }
        except: return None

    def ping(self, host):
        try:
            result = subprocess.run(
                ["ping","-n","4",host],
                capture_output=True, text=True,
                encoding='utf-8', errors='ignore', timeout=15)
            lines = result.stdout.split('\n')
            stats = [l for l in lines if 'ortalama' in l.lower() or 'average' in l.lower() or 'ms' in l.lower()]
            return '\n'.join(stats[-3:]) if stats else result.stdout[-200:]
        except Exception as e:
            return f"Ping hatası: {e}"


class StorageManager:
    def __init__(self, speak_func, msg_func):
        self.speak = speak_func
        self.msg = msg_func

    def get_disk_info(self):
        try:
            partitions = psutil.disk_partitions()
            result = "💾 Disk Bilgisi:\n"
            for p in partitions:
                try:
                    usage = psutil.disk_usage(p.mountpoint)
                    total = usage.total // 1024**3
                    used = usage.used // 1024**3
                    free = usage.free // 1024**3
                    result += f"• {p.device} ({p.mountpoint}): {used}GB/{total}GB (Boş: {free}GB)\n"
                except: pass
            return result
        except: return "Disk bilgisi alınamadı."

    def find_large_files(self, path="C:\\", min_gb=1):
        def _f():
            self.msg("ANKA", f"🔍 {min_gb}GB üzeri dosyalar aranıyor...")
            found = []
            try:
                for root, dirs, files in os.walk(path):
                    # Sistem klasörlerini atla
                    dirs[:] = [d for d in dirs if d not in
                               ['Windows','$Recycle.Bin','System Volume Information']]
                    for file in files:
                        try:
                            fp = os.path.join(root, file)
                            size = os.path.getsize(fp) // 1024**3
                            if size >= min_gb:
                                found.append((fp, size))
                        except: pass
                    if len(found) >= 10: break
            except: pass

            if found:
                r = f"📁 Büyük Dosyalar (>{min_gb}GB):\n"
                r += "\n".join(f"• {f}: {s}GB" for f,s in sorted(found, key=lambda x: -x[1])[:10])
            else:
                r = f"{min_gb}GB üzeri dosya bulunamadı efendim."
            self.msg("ANKA", r)
        threading.Thread(target=_f, daemon=True).start()

    def get_folder_size(self, path):
        total = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                for f in filenames:
                    try:
                        total += os.path.getsize(os.path.join(dirpath, f))
                    except: pass
        except: pass
        return total // 1024**2  # MB


class SysCtlCommandProcessor:
    def __init__(self, speak_func, msg_func, ollama):
        self.speak = speak_func
        self.msg = msg_func
        self.ollama = ollama
        self.proc_mgr = ProcessManager(speak_func, msg_func)
        self.net_mgr = NetworkManager(speak_func, msg_func)
        self.storage = StorageManager(speak_func, msg_func)

    def process(self, text):
        t = text.lower().strip()

        # ── Süreç Yönetimi ────────────────────────────────────────────────────
        if "ağır uygulamalar" in t or "ram yiyen" in t or "süreçleri listele" in t:
            def _h():
                r = self.proc_mgr.list_heavy()
                self.msg("ANKA", r)
                self.speak("En çok kaynak kullananlar listelendi efendim.")
            threading.Thread(target=_h, daemon=True).start()
            return True

        if "süreci öldür" in t or "uygulamayı zorla kapat" in t:
            name = t.replace("süreci öldür","").replace("uygulamayı zorla kapat","").strip()
            if name:
                killed = self.proc_mgr.kill_process(name)
                r = f"✓ Kapatıldı: {', '.join(killed)}" if killed else f"'{name}' bulunamadı."
                self.msg("ANKA", r); self.speak(r)
            return True

        if "süreci dondur" in t:
            name = t.replace("süreci dondur","").strip()
            ok = self.proc_mgr.suspend_process(name)
            r = f"✓ {name} donduruldu." if ok else "Süreç bulunamadı."
            self.msg("ANKA", r); self.speak(r)
            return True

        if "süreci devam ettir" in t:
            name = t.replace("süreci devam ettir","").strip()
            ok = self.proc_mgr.resume_process(name)
            r = f"✓ {name} devam ediyor." if ok else "Süreç bulunamadı."
            self.msg("ANKA", r); self.speak(r)
            return True

        if "süreç bilgisi" in t:
            name = t.replace("süreç bilgisi","").strip()
            info = self.proc_mgr.get_process_info(name)
            if info:
                r = (f"ℹ️ {info['name']}:\n"
                     f"• PID: {info['pid']}\n"
                     f"• CPU: %{info['cpu']}\n"
                     f"• RAM: {info['mem']}MB\n"
                     f"• Durum: {info['status']}\n"
                     f"• Başladı: {info['started']}")
            else:
                r = "Süreç bulunamadı efendim."
            self.msg("ANKA", r); self.speak(r)
            return True

        # ── Ağ Yönetimi ───────────────────────────────────────────────────────
        if "aktif bağlantılar" in t or "ağ bağlantıları" in t:
            conns = self.net_mgr.get_connections()
            if conns:
                r = f"🌐 Aktif Bağlantılar ({len(conns)}):\n"
                r += "\n".join(f"• Port {port} → {ip}" for port,ip,_ in conns[:10])
            else:
                r = "Aktif bağlantı yok efendim."
            self.msg("ANKA", r)
            return True

        if "hız testi" in t or "internet hızı" in t:
            self.net_mgr.speed_test()
            return True

        if "wifi şifre" in t or "wifi şifresi" in t:
            def _w():
                passwords = self.net_mgr.get_wifi_password()
                if passwords:
                    r = "📶 WiFi Şifreleri:\n"
                    r += "\n".join(f"• {name}: {pw}" for name,pw in passwords.items())
                    self.msg("ANKA", r)
                else:
                    self.msg("ANKA", "WiFi şifresi alınamadı efendim.")
            threading.Thread(target=_w, daemon=True).start()
            return True

        if "dns temizle" in t or "dns flush" in t:
            def _d():
                ok = self.net_mgr.flush_dns()
                r = "✓ DNS önbelleği temizlendi efendim." if ok else "DNS temizlenemedi."
                self.msg("ANKA", r); self.speak(r)
            threading.Thread(target=_d, daemon=True).start()
            return True

        if "ip bilgim" in t or "ip adresim" in t:
            def _ip():
                info = self.net_mgr.get_ip_info()
                if info:
                    r = (f"🌐 IP Bilgisi:\n"
                         f"• IP: {info['ip']}\n"
                         f"• Şehir: {info['city']}, {info['country']}\n"
                         f"• ISP: {info['isp']}\n"
                         f"• Saat Dilimi: {info['timezone']}")
                    self.msg("ANKA", r); self.speak(f"IP adresiniz {info['ip']} efendim.")
                else:
                    self.msg("ANKA", "IP bilgisi alınamadı efendim.")
            threading.Thread(target=_ip, daemon=True).start()
            return True

        if "ping" in t:
            host = t.replace("ping","").strip() or "google.com"
            def _p():
                result = self.net_mgr.ping(host)
                self.msg("ANKA", f"📡 Ping - {host}:\n{result}")
                self.speak(f"{host} ping testi tamamlandı efendim.")
            threading.Thread(target=_p, daemon=True).start()
            return True

        # ── Depolama ──────────────────────────────────────────────────────────
        if "disk bilgisi" in t or "disk durumu" in t:
            r = self.storage.get_disk_info()
            self.msg("ANKA", r); self.speak(r)
            return True

        if "büyük dosyalar" in t or "yer kaplayan" in t:
            m = re.search(r'(\d+)\s*gb', t)
            min_gb = int(m.group(1)) if m else 1
            self.storage.find_large_files(min_gb=min_gb)
            return True

        if "klasör boyutu" in t:
            path = t.replace("klasör boyutu","").strip()
            if path and os.path.exists(path):
                def _cs():
                    size = self.storage.get_folder_size(path)
                    r = f"📁 {path}: {size}MB"
                    self.msg("ANKA", r); self.speak(r)
                threading.Thread(target=_cs, daemon=True).start()
            return True

        return False
