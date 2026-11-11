<div align="center">

# 🦅 A.N.K.A
### Gelişmiş Nöral Kontrol Ajanı
#### *Yusuf Edition v8.0 — Local AI*

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python)
![Platform](https://img.shields.io/badge/Platform-Windows-0078d4?style=for-the-badge&logo=windows)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![AI](https://img.shields.io/badge/AI-Local%20%28No%20API%20Key%29-ff6b35?style=for-the-badge)
![Stars](https://img.shields.io/github/stars/yusuf/anka?style=for-the-badge)

**API key gerektirmez • Ollama gerektirmez • Tamamen yerel çalışır**

</div>

---

## 🤖 Anka Nedir?

Anka, Tony Stark'ın **Jarvis**, **EDITH** ve **F.R.I.D.A.Y**'ından ilham alınarak geliştirilmiş, tamamen yerel çalışan gelişmiş bir yapay zeka asistanıdır.

- 🚀 **API key gerektirmez** — Tamamen ücretsiz
- 🔒 **Gizlilik** — Verileriniz bilgisayarınızdan çıkmaz
- 🧠 **Öğrenen AI** — Sizi tanır ve gelişir
- ⚡ **Hızlı** — İnternet bağlantısı olmadan da çalışır
- 🎯 **300+ özellik** — Her şey dahil

---

## ⚡ Hızlı Kurulum

```bash
pip install anka-ai
anka
```

### Manuel Kurulum
```bash
git clone https://github.com/yusuf/anka.git
cd anka
pip install -r requirements.txt
python anka.py
```

---

## 🎯 Özellikler

### 🤖 Yapay Zeka
| Özellik | Komut |
|---------|-------|
| Sohbet | `merhaba`, `nasılsın` |
| Öğret | `anka öğren: [tetik]=[cevap]` |
| Kişilik | `profesyonel mod`, `eğlenceli mod` |

### ⚡ E.D.I.T.H Sistemi
| Özellik | Komut |
|---------|-------|
| Aktivasyon | `edith başlat` |
| Oda Tarama | `odayı tara` |
| Tehdit Analizi | `siber tehdit [açıklama]` |
| OSINT | `osint [hedef]` |
| Gözetleme | `gözetleme başlat` |
| Güvenli Kasa | `kasaya ekle [etiket]=[veri]` |
| Küresel Durum | `küresel durum` |
| ISS Takibi | `iss nerede` |

### 🎯 F.R.I.D.A.Y Sistemi
| Özellik | Komut |
|---------|-------|
| Aktivasyon | `friday başlat` |
| Taktik Analiz | `taktik değerlendir [durum]` |
| Senaryo | `senaryo analizi [durum]` |
| Paralel Görev | `paralel görev görev1, görev2` |
| İş Akışı | `iş akışı oluştur [isim]` |
| Yayın | `yayın yap [mesaj]` |

### 🏠 Sistem & Otomasyon
| Özellik | Komut |
|---------|-------|
| Sistem Durumu | `sistem durumu` |
| Disk | `disk bilgisi` |
| RAM | `ram kullanan` |
| Ağ Tara | `ağı tara` |
| WiFi Şifre | `wifi şifre` |
| Hız Testi | `hız testi` |

### 📚 LGS Yardımcısı
| Özellik | Komut |
|---------|-------|
| Konu Anlatım | `lgs matematik anlat` |
| Soru Çöz | `lgs soru` |
| İstatistik | `lgs istatistik` |
| Çalışma Planı | `lgs program` |

### 🎵 Medya & Eğlence
| Özellik | Komut |
|---------|-------|
| YouTube | `youtube'da çal [şarkı]` |
| Spotify | `spotify'da çal [şarkı]` |
| Video İndir | `youtube indir [link]` |
| MP3 İndir | `mp3 indir [link]` |

### 💰 Finans
| Özellik | Komut |
|---------|-------|
| Döviz | `döviz kuru` |
| Altın | `altın fiyatı` |
| Bitcoin | `bitcoin` |
| Harcama | `harcama ekle [tutar] [kategori]` |

### 📱 İletişim
| Özellik | Komut |
|---------|-------|
| WhatsApp | `whatsapp gönder [kişi] [mesaj]` |
| Saat Bildirimi | `saate hava gönder` |
| Takvim | `takvim aç` |

---

## 🛠️ Gereksinimler

```
Python 3.10+
Windows 10/11
```

```bash
pip install customtkinter requests psutil numpy sounddevice scipy
pip install openai-whisper edge-tts pygame pyautogui pyperclip
pip install opencv-python pillow
```

---

## 📁 Proje Yapısı

```
anka/
├── anka.py              # Ana uygulama
├── anka_local_ai.py     # Yerel AI motoru (API key gerektirmez!)
├── anka_config.py       # Ayarlar
├── anka_edith.py        # E.D.I.T.H sistemi
├── anka_friday.py       # F.R.I.D.A.Y sistemi
├── anka_jarvis.py       # Jarvis protokolleri
├── anka_autonomous.py   # Otonom AI ajanları
├── anka_lgs.py          # LGS yardımcısı
├── anka_voice.py        # Ses tanıma (Whisper)
└── ... (46 modül)
```

---

## ⚙️ Ayarlar

`anka_config.py` dosyasını düzenleyin:

```python
USER_NAME  = "Yusuf"      # Adınız
USER_CITY  = "Istanbul"   # Şehriniz
USE_LOCAL_AI = True       # API key gerektirmez!
```

---

## 🤝 Katkıda Bulun

1. Fork edin
2. Branch oluşturun (`git checkout -b feature/YeniOzellik`)
3. Commit edin (`git commit -m 'Yeni özellik eklendi'`)
4. Push edin (`git push origin feature/YeniOzellik`)
5. Pull Request açın

---

## 📜 Lisans

MIT License — Özgürce kullanın, geliştirin, paylaşın!

---

<div align="center">

**Yusuf tarafından ❤️ ile geliştirildi**

*"Jarvis olmak istiyorsan, önce Anka ol."*

</div>
