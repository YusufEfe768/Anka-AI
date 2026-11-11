# ── ANKA OTOMATİK BAŞLANGIÇ KURULUMU ─────────────────────────────────────────
# python anka_autostart.py --> çalıştır, Windows başlangıcına ekler
# python anka_autostart.py --remove --> başlangıçtan kaldırır

import os, sys, winreg

ANKA_KEY = "Anka_AI_Yusuf"

def add_autostart():
    script = os.path.abspath(os.path.join(os.path.dirname(__file__), "anka.py"))
    python = sys.executable.replace("python.exe","pythonw.exe")  # Terminalsiz çalıştır
    if not os.path.exists(python):
        python = sys.executable
    value = f'"{python}" "{script}"'
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                              r"Software\Microsoft\Windows\CurrentVersion\Run",
                              0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, ANKA_KEY, 0, winreg.REG_SZ, value)
        winreg.CloseKey(key)
        print(f"✓ Anka Windows başlangıcına eklendi!")
        print(f"  Komut: {value}")
        return True
    except Exception as e:
        print(f"✗ Başlangıca eklenemedi: {e}")
        return False

def remove_autostart():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                              r"Software\Microsoft\Windows\CurrentVersion\Run",
                              0, winreg.KEY_SET_VALUE)
        winreg.DeleteValue(key, ANKA_KEY)
        winreg.CloseKey(key)
        print("✓ Anka başlangıçtan kaldırıldı.")
        return True
    except Exception as e:
        print(f"Kaldırılamadı: {e}")
        return False

def check_autostart():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                              r"Software\Microsoft\Windows\CurrentVersion\Run",
                              0, winreg.KEY_READ)
        val, _ = winreg.QueryValueEx(key, ANKA_KEY)
        winreg.CloseKey(key)
        return val
    except:
        return None

if __name__ == "__main__":
    if "--remove" in sys.argv:
        remove_autostart()
    elif "--check" in sys.argv:
        val = check_autostart()
        if val:
            print(f"✓ Anka başlangıçta aktif: {val}")
        else:
            print("✗ Anka başlangıçta değil")
    else:
        add_autostart()
        input("\nEnter'a bas, pencereyi kapat.")
