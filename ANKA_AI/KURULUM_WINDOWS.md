# 🪟 ANKA — Windows Kurulum Rehberi

## Hızlı Kurulum
```bash
pip install -r requirements_windows.txt
python anka.py
```

## Adım Adım

### 1. Python Kur
https://python.org/downloads → Python 3.10+ indir

### 2. Dosyaları Aç
ZIP'i aç → Anka klasörüne koy

### 3. Kütüphaneleri Kur
```bash
cd Masaüstü\Anka
pip install -r requirements_windows.txt
```

### 4. Ayarla
`anka_config.py` dosyasını aç:
```python
USER_NAME = "Adın"
USE_LOCAL_AI = True
```

### 5. Çalıştır
```bash
python anka.py
```

## İlk Kullanım
- "Merhaba" → Anka seninle tanışır
- "Yardım" → Tüm komutlar
- "Edith başlat" → EDITH aktif
- "Friday başlat" → F.R.I.D.A.Y aktif
- "Anka öğren: [tetik]=[cevap]" → Öğret!

## Sorunlar
- **Ses çalışmıyor**: `pip install sounddevice pyaudio`
- **Kamera açılmıyor**: OpenCV sürücüsü kur
- **Whisper yavaş**: GPU yoksa normal, bekle
