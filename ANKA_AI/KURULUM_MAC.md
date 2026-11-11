# 🍎 ANKA — macOS Kurulum Rehberi

## Hızlı Kurulum
```bash
pip3 install -r requirements_mac.txt
python3 anka.py
```

## Adım Adım

### 1. Homebrew Kur (yoksa)
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 2. Python Kur
```bash
brew install python@3.11
```

### 3. Dosyaları Aç
ZIP'i aç → Anka klasörüne koy

### 4. Kütüphaneleri Kur
```bash
cd ~/Desktop/Anka
pip3 install -r requirements_mac.txt
```

### 5. Mikrofon İzni Ver
Sistem Ayarları → Gizlilik → Mikrofon → Terminal ✓

### 6. Kamera İzni Ver
Sistem Ayarları → Gizlilik → Kamera → Terminal ✓

### 7. Ayarla
`anka_config.py` dosyasını aç:
```python
USER_NAME = "Adın"
USE_LOCAL_AI = True
```

### 8. Çalıştır
```bash
python3 anka.py
```

## macOS Özel Komutlar
- "karanlık mod" → Dark mode aç/kapat
- "safari aç" → Safari açılır
- "ekranı kilitle" → Ekran kilitlenir
- "bildirim gönder [mesaj]" → macOS bildirimi

## Sorunlar
- **tkinter yok**: `brew install python-tk@3.11`
- **Ses yok**: `pip3 install sounddevice`
- **İzin hatası**: Gizlilik ayarlarını kontrol et
