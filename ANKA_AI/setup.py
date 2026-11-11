try:
    import pyperclip
except ImportError:
    class _PyClip:
        def copy(self,x):pass
        def paste(self):return ""
    pyperclip=_PyClip()
try:
    import pyautogui
except ImportError:
    pyautogui=None
from setuptools import setup, find_packages
import os, platform

def read(fname):
    try:
        with open(os.path.join(os.path.dirname(__file__), fname), encoding="utf-8") as f:
            return f.read()
    except: return ""

# Platform bazlı gereksinimler
IS_MAC = platform.system() == "Darwin"
IS_WIN = platform.system() == "Windows"

common_requires = [
    "customtkinter>=5.2.0",
    "requests>=2.28.0",
    "psutil>=5.9.0",
    "numpy>=1.24.0",
    "sounddevice>=0.4.6",
    "scipy>=1.10.0",
    "openai-whisper>=20231117",
    "edge-tts>=6.1.9",
    "pygame>=2.5.0",
    "pyautogui>=0.9.54",
    "pyperclip>=1.8.2",
    "opencv-python>=4.8.0",
    "pillow>=10.0.0",
    "difflib2>=1.0.0",
]

mac_requires = [
    "pyobjc-core>=9.0",
    "pyobjc-framework-Cocoa>=9.0",
]

win_requires = [
    "pywin32>=306",
]

install_requires = common_requires
if IS_MAC: install_requires += mac_requires
if IS_WIN: install_requires += win_requires

setup(
    name="anka-ai",
    version="9.0.0",
    author="Yusuf",
    description="Anka — Gelişmiş Nöral Kontrol Ajanı. API key gerektirmez! Windows & macOS",
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    url="https://github.com/yusuf/anka",
    py_modules=[
        "anka","anka_local_ai","anka_brain","anka_training_data",
        "anka_config","anka_memory","anka_voice","anka_wakeword",
        "anka_security","anka_commands","anka_alarm","anka_location",
        "anka_system_pro","anka_advanced","anka_autostart","anka_routines",
        "anka_super","anka_mega","anka_ultimate","anka_watch","anka_school",
        "anka_ai_pro","anka_genius","anka_ultra","anka_power","anka_lgs",
        "anka_next","anka_pro2","anka_smart","anka_social","anka_creative",
        "anka_science","anka_lifestyle","anka_finance2","anka_assistant",
        "anka_gaming","anka_health2","anka_sysctl","anka_fileops",
        "anka_automation","anka_devtools","anka_autonomous","anka_jarvis",
        "anka_jarvis_extra","anka_edith","anka_friday","anka_ui_new",
        "anka_mac","anka_extras",
    ],
    install_requires=install_requires,
    extras_require={
        "windows": win_requires,
        "mac": mac_requires,
        "full": ["yt-dlp","feedparser","qrcode","PyPDF2","pycaw"],
    },
    entry_points={
        "console_scripts": [
            "anka=anka:main",
            "anka-ai=anka:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Natural Language :: Turkish",
    ],
    python_requires=">=3.10",
    keywords="yapay-zeka asistan jarvis edith friday local-ai türkçe ai",
)
