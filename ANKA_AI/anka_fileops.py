# ── ANKA DOSYA İŞLEMLERİ MODÜLü ─────────────────────────────────────────────
# Dosya organizasyonu, dönüştürme, şifreleme, yedekleme
import json, os, threading, datetime, subprocess, shutil, zipfile
import hashlib, base64, re, glob, time
from anka_config import BASE_DIR

class FileOrganizer:
    def __init__(self, speak_func, msg_func):
        self.speak = speak_func
        self.msg = msg_func

    def organize_folder(self, folder_path):
        def _o():
            if not os.path.exists(folder_path):
                self.msg("ANKA", "Klasör bulunamadı efendim.")
                return
            categories = {
                "📸 Resimler": [".jpg",".jpeg",".png",".gif",".bmp",".svg",".webp",".heic"],
                "📄 Belgeler": [".pdf",".doc",".docx",".txt",".xlsx",".pptx",".odt"],
                "🎥 Videolar": [".mp4",".avi",".mkv",".mov",".wmv",".flv"],
                "🎵 Müzik": [".mp3",".wav",".flac",".aac",".ogg"],
                "📦 Arşivler": [".zip",".rar",".7z",".tar",".gz"],
                "💻 Programlar": [".exe",".msi",".dmg",".apk"],
                "📝 Kod": [".py",".js",".html",".css",".java",".cpp",".json"],
                "📊 Veri": [".csv",".xml",".sql",".db"],
            }
            moved = 0
            for fname in os.listdir(folder_path):
                fpath = os.path.join(folder_path, fname)
                if not os.path.isfile(fpath): continue
                ext = os.path.splitext(fname)[1].lower()
                for cat, exts in categories.items():
                    if ext in exts:
                        cat_dir = os.path.join(folder_path, cat)
                        os.makedirs(cat_dir, exist_ok=True)
                        try:
                            shutil.move(fpath, os.path.join(cat_dir, fname))
                            moved += 1
                        except: pass
                        break
            r = f"✓ {moved} dosya kategorilere ayrıldı efendim!"
            self.msg("ANKA", r); self.speak(r)
        threading.Thread(target=_o, daemon=True).start()

    def bulk_rename(self, folder, pattern, replacement):
        def _r():
            if not os.path.exists(folder): return
            renamed = 0
            for fname in os.listdir(folder):
                if pattern.lower() in fname.lower():
                    new_name = fname.replace(pattern, replacement)
                    try:
                        os.rename(
                            os.path.join(folder, fname),
                            os.path.join(folder, new_name)
                        )
                        renamed += 1
                    except: pass
            r = f"✓ {renamed} dosya yeniden adlandırıldı efendim."
            self.msg("ANKA", r); self.speak(r)
        threading.Thread(target=_r, daemon=True).start()

    def find_duplicates(self, folder):
        def _f():
            self.msg("ANKA","🔍 Tekrar eden dosyalar aranıyor...")
            hashes = {}
            duplicates = []
            for root, _, files in os.walk(folder):
                for fname in files:
                    fpath = os.path.join(root, fname)
                    try:
                        with open(fpath, 'rb') as f:
                            fhash = hashlib.md5(f.read(1024*1024)).hexdigest()
                        if fhash in hashes:
                            duplicates.append((fpath, hashes[fhash]))
                        else:
                            hashes[fhash] = fpath
                    except: pass
                if len(duplicates) >= 20: break

            if duplicates:
                r = f"📁 Tekrar Eden Dosyalar ({len(duplicates)}):\n"
                r += "\n".join(f"• {os.path.basename(d[0])}" for d in duplicates[:10])
            else:
                r = "✓ Tekrar eden dosya bulunamadı efendim."
            self.msg("ANKA", r)
        threading.Thread(target=_f, daemon=True).start()

    def zip_folder(self, source, output_name=None):
        def _z():
            if not os.path.exists(source): return
            if not output_name:
                out = source + f"_{datetime.date.today()}.zip"
            else:
                out = output_name
            try:
                with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as zf:
                    if os.path.isfile(source):
                        zf.write(source, os.path.basename(source))
                    else:
                        for root, _, files in os.walk(source):
                            for file in files:
                                fpath = os.path.join(root, file)
                                zf.write(fpath, os.path.relpath(fpath, source))
                size = os.path.getsize(out) // 1024
                r = f"✓ Sıkıştırıldı: {os.path.basename(out)} ({size}KB)"
                self.msg("ANKA", r); self.speak(r)
            except Exception as e:
                self.msg("ANKA", f"Sıkıştırma hatası: {e}")
        threading.Thread(target=_z, daemon=True).start()

    def extract_zip(self, zip_path, dest=None):
        def _e():
            if not os.path.exists(zip_path): return
            dest_path = dest or os.path.dirname(zip_path)
            try:
                with zipfile.ZipFile(zip_path, 'r') as zf:
                    zf.extractall(dest_path)
                r = f"✓ {os.path.basename(zip_path)} çıkartıldı: {dest_path}"
                self.msg("ANKA", r); self.speak(r)
            except Exception as e:
                self.msg("ANKA", f"Çıkartma hatası: {e}")
        threading.Thread(target=_e, daemon=True).start()

    def file_info(self, path):
        try:
            stat = os.stat(path)
            size = stat.st_size
            modified = datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%d.%m.%Y %H:%M")
            created = datetime.datetime.fromtimestamp(stat.st_ctime).strftime("%d.%m.%Y %H:%M")
            if size > 1024**3: size_str = f"{size//1024**3}GB"
            elif size > 1024**2: size_str = f"{size//1024**2}MB"
            elif size > 1024: size_str = f"{size//1024}KB"
            else: size_str = f"{size}B"
            return {
                "name": os.path.basename(path),
                "size": size_str,
                "modified": modified,
                "created": created,
                "ext": os.path.splitext(path)[1]
            }
        except: return None

    def smart_backup(self, source, backup_dir):
        def _b():
            if not os.path.exists(source): return
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(backup_dir, f"backup_{ts}")
            os.makedirs(backup_path, exist_ok=True)
            try:
                if os.path.isfile(source):
                    shutil.copy2(source, backup_path)
                else:
                    shutil.copytree(source, os.path.join(backup_path, os.path.basename(source)))
                r = f"✓ Yedeklendi: {backup_path}"
                self.msg("ANKA", r); self.speak(r)
            except Exception as e:
                self.msg("ANKA", f"Yedekleme hatası: {e}")
        threading.Thread(target=_b, daemon=True).start()

    def search_in_files(self, folder, keyword):
        def _s():
            found = []
            for root, _, files in os.walk(folder):
                for fname in files:
                    if fname.endswith(('.txt','.py','.html','.css','.js','.json','.xml','.csv')):
                        try:
                            fpath = os.path.join(root, fname)
                            with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                                if keyword.lower() in f.read().lower():
                                    found.append(fpath)
                        except: pass
                if len(found) >= 20: break

            if found:
                r = f"🔍 '{keyword}' içeren dosyalar ({len(found)}):\n"
                r += "\n".join(f"• {os.path.basename(f)}" for f in found[:10])
            else:
                r = f"'{keyword}' içeren dosya bulunamadı efendim."
            self.msg("ANKA", r); self.speak(r)
        threading.Thread(target=_s, daemon=True).start()


class FileOpsCommandProcessor:
    def __init__(self, speak_func, msg_func, ollama):
        self.speak = speak_func
        self.msg = msg_func
        self.ollama = ollama
        self.organizer = FileOrganizer(speak_func, msg_func)

    def process(self, text):
        t = text.lower().strip()

        if "klasörü organize et" in t or "klasörü düzenle" in t:
            path = t.replace("klasörü organize et","").replace("klasörü düzenle","").strip()
            if not path:
                path = os.path.join(os.path.expanduser("~"), "Downloads")
            self.organizer.organize_folder(path)
            return True

        if "toplu yeniden adlandır" in t:
            r = "Format: 'toplu yeniden adlandır [klasör] | [eski] | [yeni]'"
            self.msg("ANKA", r); self.speak(r)
            return True

        if "toplu adlandır:" in t:
            parts = t.replace("toplu adlandır:","").split("|")
            if len(parts) >= 3:
                self.organizer.bulk_rename(parts[0].strip(), parts[1].strip(), parts[2].strip())
            return True

        if "tekrar eden dosya" in t or "duplicate" in t:
            path = t.replace("tekrar eden dosyaları bul","").replace("duplicate bul","").strip()
            if not path:
                path = os.path.join(os.path.expanduser("~"), "Downloads")
            self.organizer.find_duplicates(path)
            return True

        if "sıkıştır" in t or "zip yap" in t:
            path = t.replace("sıkıştır","").replace("zip yap","").strip()
            if path and os.path.exists(path):
                self.organizer.zip_folder(path)
            else:
                self.msg("ANKA","Dosya/klasör yolu geçerli değil efendim.")
            return True

        if "zip aç" in t or "arşivi çıkar" in t:
            path = t.replace("zip aç","").replace("arşivi çıkar","").strip()
            if path and os.path.exists(path):
                self.organizer.extract_zip(path)
            else:
                self.msg("ANKA","Zip dosyası bulunamadı efendim.")
            return True

        if "dosya bilgisi" in t:
            path = t.replace("dosya bilgisi","").strip()
            if path and os.path.exists(path):
                info = self.organizer.file_info(path)
                if info:
                    r = (f"📄 {info['name']}:\n"
                         f"• Boyut: {info['size']}\n"
                         f"• Tür: {info['ext']}\n"
                         f"• Değiştirildi: {info['modified']}\n"
                         f"• Oluşturuldu: {info['created']}")
                    self.msg("ANKA", r)
            return True

        if "yedekle" in t:
            parts = t.replace("yedekle","").strip().split("→")
            if len(parts) >= 2:
                self.organizer.smart_backup(parts[0].strip(), parts[1].strip())
            else:
                self.msg("ANKA","Format: 'yedekle [kaynak] → [hedef]' efendim.")
            return True

        if "dosyalarda ara" in t:
            parts = t.replace("dosyalarda ara","").strip().split("|")
            if len(parts) >= 2:
                self.organizer.search_in_files(parts[0].strip(), parts[1].strip())
            else:
                keyword = parts[0].strip() if parts else ""
                if keyword:
                    self.organizer.search_in_files(
                        os.path.expanduser("~"), keyword)
            return True

        if "masaüstü temizle" in t:
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            self.organizer.organize_folder(desktop)
            return True

        if "indirilenler temizle" in t:
            downloads = os.path.join(os.path.expanduser("~"), "Downloads")
            self.organizer.organize_folder(downloads)
            return True

        return False
