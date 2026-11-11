# ── ANKA YENİ ARAYÜZ ─────────────────────────────────────────────────────────
# Glassmorphism + Neon efektleri + Animasyonlu hologram
import customtkinter as ctk
import tkinter as tk
from tkinter import font as tkfont
import math, random, time, datetime, threading, os, json, subprocess
import psutil, requests

# ── TEMA SİSTEMİ ─────────────────────────────────────────────────────────────
THEMES = {
    "cyber": {
        "bg": "#030308", "bg2": "#070712", "bg3": "#0a0a1a",
        "surface": "#0d0d20", "surface2": "#111128",
        "border": "#1a1a3a", "border2": "#252550",
        "accent": "#00ffff", "accent2": "#00cccc", "accent3": "#006666",
        "accent_glow": "#00ffff33",
        "purple": "#7700ff", "pink": "#ff00aa",
        "green": "#00ff88", "orange": "#ff6600",
        "yellow": "#ffcc00", "red": "#ff2244",
        "white": "#e0f0ff", "muted": "#2a2a50", "muted2": "#4a4a80",
        "name": "Cyber Teal"
    },
    "neon_purple": {
        "bg": "#05030a", "bg2": "#08050f", "bg3": "#0b0814",
        "surface": "#100a1e", "surface2": "#150d28",
        "border": "#1e1040", "border2": "#2a1555",
        "accent": "#bf00ff", "accent2": "#9900cc", "accent3": "#550077",
        "accent_glow": "#bf00ff33",
        "purple": "#ff00ff", "pink": "#ff0088",
        "green": "#00ffaa", "orange": "#ff8800",
        "yellow": "#ffdd00", "red": "#ff1133",
        "white": "#f0e0ff", "muted": "#2a1050", "muted2": "#4a2080",
        "name": "Neon Purple"
    },
    "iron_man": {
        "bg": "#080400", "bg2": "#0f0800", "bg3": "#150c00",
        "surface": "#1a1000", "surface2": "#221400",
        "border": "#332200", "border2": "#443300",
        "accent": "#ffaa00", "accent2": "#cc8800", "accent3": "#774400",
        "accent_glow": "#ffaa0033",
        "purple": "#ff4400", "pink": "#ff2200",
        "green": "#44ff00", "orange": "#ff6600",
        "yellow": "#ffdd00", "red": "#ff2200",
        "white": "#fff0d0", "muted": "#332200", "muted2": "#665500",
        "name": "Iron Man"
    },
    "matrix": {
        "bg": "#000500", "bg2": "#000800", "bg3": "#000b00",
        "surface": "#000f00", "surface2": "#001200",
        "border": "#001800", "border2": "#002200",
        "accent": "#00ff41", "accent2": "#00cc33", "accent3": "#006618",
        "accent_glow": "#00ff4133",
        "purple": "#00aa33", "pink": "#00ff88",
        "green": "#00ff41", "orange": "#00dd22",
        "yellow": "#88ff00", "red": "#ff4400",
        "white": "#ccffcc", "muted": "#003300", "muted2": "#005500",
        "name": "Matrix"
    }
}

C = THEMES["cyber"]
ctk.set_appearance_mode("dark")

# ── CANVAS ANİMASYON SINIFI ───────────────────────────────────────────────────
class HologramCanvas(tk.Canvas):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.angle = 0
        self.pulse = 0.0
        self.wave_vals = [0] * 40
        self.particles = [(random.uniform(0,360), random.uniform(5,120)) for _ in range(80)]
        self.stars = [(random.randint(0,800), random.randint(0,300), random.random()) for _ in range(60)]
        self.is_recording = False
        self.is_thinking = False
        self.hw_mode = False
        self.state_text = "BEKLIYOR"

    def draw(self):
        self.delete("all")
        w = self.winfo_width() or 800
        h = self.winfo_height() or 260
        cx, cy = w//2, h//2

        # Yıldız arka planı
        for sx, sy, brightness in self.stars:
            if sx < w and sy < h:
                alpha = int(brightness * 150)
                color = f"#{alpha:02x}{alpha:02x}{min(255,alpha+30):02x}"
                self.create_oval(sx-1, sy-1, sx+1, sy+1, fill=color, outline="")

        self.pulse = (self.pulse + 0.03) % (2 * math.pi)
        pulse_r = 90 + 5 * math.sin(self.pulse)

        # Dış glow halkaları
        for i in range(5, 0, -1):
            r_glow = pulse_r + 15 + i * 12
            alpha = 25 - i * 4
            self.create_oval(cx-r_glow, cy-r_glow, cx+r_glow, cy+r_glow,
                           outline=C["accent"], width=1 if i == 1 else 0)

        # Ana dış halka
        self.create_oval(cx-pulse_r, cy-pulse_r, cx+pulse_r, cy+pulse_r,
                        outline=C["accent"], width=2)

        # Dönen dış noktalar
        for i in range(60):
            a = math.radians(i * 6 + self.angle)
            x = cx + pulse_r * math.cos(a)
            y = cy + pulse_r * math.sin(a)
            if i % 10 == 0:
                sz = 5
                col = C["accent"]
                x2 = cx + (pulse_r-20) * math.cos(a)
                y2 = cy + (pulse_r-20) * math.sin(a)
                self.create_line(x, y, x2, y2, fill=C["accent2"], width=1)
            elif i % 5 == 0:
                sz = 3
                col = C["accent2"]
            else:
                sz = 1.5
                col = C["muted"]
            self.create_oval(x-sz, y-sz, x+sz, y+sz, fill=col, outline="")

        # İç halka (ters dönen)
        r2 = int(pulse_r * 0.68)
        self.create_oval(cx-r2, cy-r2, cx+r2, cy+r2, outline=C["border2"], width=1)
        for i in range(30):
            a = math.radians(i * 12 - self.angle * 0.8)
            x = cx + r2 * math.cos(a)
            y = cy + r2 * math.sin(a)
            sz = 3 if i % 5 == 0 else 1
            col = C["orange"] if i % 5 == 0 else C["muted"]
            self.create_oval(x-sz, y-sz, x+sz, y+sz, fill=col, outline="")

        # En iç halka
        r3 = int(pulse_r * 0.42)
        self.create_oval(cx-r3, cy-r3, cx+r3, cy+r3, outline=C["accent3"], width=1)

        # Partiküller
        for pa, prf in self.particles:
            a = math.radians(pa + self.angle * 0.15)
            pr = prf * r3 / 120
            x = cx + pr * math.cos(a)
            y = cy + pr * math.sin(a)
            col = C["green"] if self.is_recording else (
                  C["accent"] if random.random() > 0.4 else C["accent3"])
            self.create_oval(x-1.5, y-1.5, x+1.5, y+1.5, fill=col, outline="")

        # Merkez yazı
        sc = C["red"] if self.is_recording else (C["yellow"] if self.is_thinking else C["accent"])
        # Glow efekti için arkaya daha büyük yazı
        self.create_text(cx, cy-20, text="A.N.K.A",
                        font=("Courier New", 22, "bold"), fill=C["accent3"], anchor="center")
        self.create_text(cx, cy-20, text="A.N.K.A",
                        font=("Courier New", 20, "bold"), fill=C["white"], anchor="center")

        # Durum
        st = "● DİNLİYOR" if self.is_recording else ("◆ DÜŞÜNÜYOR" if self.is_thinking else "◇ BEKLİYOR")
        self.create_text(cx, cy+5, text=st,
                        font=("Segoe UI", 9, "bold"), fill=sc, anchor="center")

        if self.hw_mode:
            self.create_text(cx, cy+22, text="[ ÖDEV MODU ]",
                           font=("Segoe UI", 8), fill=C["yellow"], anchor="center")

        # Ses dalgası
        if self.is_recording:
            for i in range(40):
                self.wave_vals[i] = max(2, self.wave_vals[i]*0.6 + random.randint(0,28)*0.4)
                x = cx - 95 + i * 5
                hh = self.wave_vals[i]
                self.create_rectangle(x, cy+38, x+3, cy+38+hh, fill=C["green"], outline="")

        # Köşe L işaretleri (HUD stili)
        for ox, oy, dx, dy in [(-1,-1,1,1),(-1,1,1,-1),(1,-1,-1,1),(1,1,-1,-1)]:
            bx = cx + ox*(pulse_r+25)
            by = cy + oy*(pulse_r+25)
            self.create_line(bx, by, bx+dx*18, by, fill=C["accent2"], width=1)
            self.create_line(bx, by, bx, by+dy*18, fill=C["accent2"], width=1)

        # Saat (sağ üst)
        now = datetime.datetime.now()
        self.create_text(w-12, 10, text=now.strftime("%H:%M:%S"),
                        font=("Courier New", 10), fill=C["accent3"], anchor="ne")

        # Scan line efekti
        scan_y = int((time.time() * 80) % h)
        self.create_line(0, scan_y, w, scan_y, fill=C["accent_glow"], width=1)

        self.angle = (self.angle + 1) % 360
        self.particles = [((pa + random.uniform(-0.1, 0.1)) % 360, pr)
                         for pa, pr in self.particles]


# ── ÖZEL WIDGET'LAR ────────────────────────────────────────────────────────────
class GlowButton(ctk.CTkButton):
    """Neon glow efektli buton"""
    pass

class NeonLabel(tk.Label):
    """Neon efektli etiket"""
    def __init__(self, parent, text="", color=None, size=12, bold=False, **kwargs):
        c = color or C["accent"]
        f = ("Courier New" if bold else "Segoe UI", size, "bold" if bold else "normal")
        super().__init__(parent, text=text, fg=c, bg=C["surface"],
                        font=f, **kwargs)

class StatBar:
    """Animasyonlu istatistik çubuğu"""
    def __init__(self, parent, label, color, row):
        self.frame = tk.Frame(parent, bg=C["surface"])
        self.frame.grid(row=row, column=0, padx=10, pady=2, sticky="ew")
        self.frame.columnconfigure(1, weight=1)

        tk.Label(self.frame, text=label, font=("Segoe UI", 8), 
                bg=C["surface"], fg=C["muted2"], width=5, anchor="w").grid(row=0, column=0)
        
        self.bar = ctk.CTkProgressBar(self.frame, height=5,
                                       progress_color=color, fg_color=C["border"],
                                       corner_radius=3)
        self.bar.grid(row=0, column=1, padx=(4,4), sticky="ew")
        self.bar.set(0)
        
        self.pct = tk.Label(self.frame, text="0%", font=("Courier New", 8),
                           bg=C["surface"], fg=color, width=5)
        self.pct.grid(row=0, column=2)

    def update(self, value):
        self.bar.set(value/100)
        self.pct.configure(text=f"{int(value)}%")


class ChatMessage(tk.Frame):
    """Güzel mesaj baloncuğu"""
    def __init__(self, parent, sender, text, time_str, **kwargs):
        colors = {
            "ANKA": C["accent"], "SEN": C["yellow"],
            "ÖDEV": C["green"], "WA": "#25d366",
            "SİSTEM": C["orange"], "WATCH": "#4fc3f7"
        }
        sender_color = colors.get(sender, C["accent"])

        super().__init__(parent, bg=C["surface2"], **kwargs)
        self.columnconfigure(0, weight=1)

        # Üst kısım (gönderen + zaman)
        top = tk.Frame(self, bg=C["surface2"])
        top.grid(row=0, column=0, sticky="ew", padx=8, pady=(6,2))

        tk.Label(top, text=sender, font=("Segoe UI", 9, "bold"),
                bg=C["surface2"], fg=sender_color).pack(side="left")
        tk.Label(top, text=time_str, font=("Segoe UI", 8),
                bg=C["surface2"], fg=C["muted2"]).pack(side="right")

        # İnce çizgi (gönderen renginde)
        tk.Frame(self, bg=sender_color, height=1).grid(row=1, column=0, sticky="ew", padx=8)

        # Mesaj içeriği
        msg_label = tk.Label(self, text=text, font=("Segoe UI", 11),
                            bg=C["surface2"], fg=C["white"],
                            wraplength=700, justify="left", anchor="w")
        msg_label.grid(row=2, column=0, sticky="ew", padx=12, pady=(4,8))

        # Alt separator
        tk.Frame(self, bg=C["border"], height=1).grid(row=3, column=0, sticky="ew")
