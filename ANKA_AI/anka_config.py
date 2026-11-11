# ── ANKA KONFİGÜRASYON DOSYASI ──────────────────────────────────────────────
# API anahtarlarını buraya girin

# ══════════════════════════════════════════════════════
# 🤖 YAPAY ZEKA MODU
# True  → API key veya Ollama GEREKMİYOR! Tamamen yerel.
# False → OpenRouter API key veya Ollama gerekir.
USE_LOCAL_AI = True   # ← Değiştir
# ══════════════════════════════════════════════════════

# Haber API (newsapi.org'dan ücretsiz alın)
NEWS_API_KEY = "YOUR_NEWS_API_KEY"

# Spotify (developer.spotify.com'dan alın)
SPOTIFY_CLIENT_ID     = "YOUR_SPOTIFY_CLIENT_ID"
SPOTIFY_CLIENT_SECRET = "YOUR_SPOTIFY_CLIENT_SECRET"
SPOTIFY_REDIRECT_URI  = "http://localhost:8888/callback"

# Telegram (BotFather'dan alın)
TELEGRAM_TOKEN   = "YOUR_TELEGRAM_TOKEN"
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID"

# Gmail
GMAIL_USER     = "your@gmail.com"
GMAIL_PASSWORD = "your_app_password"

# OpenWeatherMap (openweathermap.org'dan ücretsiz)
WEATHER_API_KEY = "YOUR_WEATHER_API_KEY"
WEATHER_CITY    = "Istanbul"

# Kullanıcı bilgileri
USER_NAME  = "Yusuf"
USER_CITY  = "Istanbul"
USER_LANG  = "tr"

# Ollama
OLLAMA_MODEL = "llama3.2"
OLLAMA_URL   = "http://localhost:11434"

# Dosya yolları
import os
BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
MEMORY_FILE   = os.path.join(BASE_DIR, "anka_memory.json")
FACE_DIR      = os.path.join(BASE_DIR, "faces")
ALARM_FILE    = os.path.join(BASE_DIR, "anka_alarms.json")
NOTES_FILE    = os.path.join(BASE_DIR, "anka_notes.json")
TASKS_FILE    = os.path.join(BASE_DIR, "anka_tasks.json")
BUDGET_FILE   = os.path.join(BASE_DIR, "anka_budget.json")
HEALTH_FILE   = os.path.join(BASE_DIR, "anka_health.json")
LOG_FILE      = os.path.join(BASE_DIR, "anka_log.json")

os.makedirs(FACE_DIR, exist_ok=True)
