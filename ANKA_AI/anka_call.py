# ── ANKA WHATSAPP ARAMA SİSTEMİ v2 ───────────────────────────────────────────
# Gelişmiş WhatsApp entegrasyonu — Sesli arama, mesaj, planlama, AI asistan
import json, os, time, threading, datetime, subprocess, re, webbrowser
import requests, psutil, urllib.parse, random
from anka_config import BASE_DIR, USER_NAME

CALL_FILE = os.path.join(BASE_DIR, "anka_calls.json")

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


class AnkaCallSystem:
    def __init__(self, speak_func, msg_func, ollama):
        self.speak  = speak_func
        self.msg    = msg_func
        self.ollama = ollama
        self.data   = _load(CALL_FILE, {
            "my_phone":        "",
            "contacts":        {},
            "scheduled_calls": [],
            "call_log":        [],
            "ntfy_topic":      "anka-yusuf-2026",
            "auto_messages":   {},
            "do_not_disturb":  {"enabled": False, "start": "23:00", "end": "07:00"},
            "call_stats":      {"total": 0, "today": 0, "last_date": ""}
        })
        self.running = True
        threading.Thread(target=self._scheduler_loop, daemon=True).start()
        threading.Thread(target=self._smart_monitor,  daemon=True).start()

    # ── Numara Yönetimi ───────────────────────────────────────────────────────
    def set_my_number(self, number):
        clean = re.sub(r'\D','', number)
        if clean.startswith("0"):   clean = "90" + clean[1:]
        if clean.startswith("5"):   clean = "90" + clean
        if not clean.startswith("90"): clean = "90" + clean
        self.data["my_phone"] = clean
        _save(CALL_FILE, self.data)
        r = (f"✅ Numaran kaydedildi: +{clean}\n"
             f"📱 Artık seni WhatsApp'tan arayabilirim efendim!\n"
             f"🔔 ntfy.sh uygulamasını kur ve '{self.data['ntfy_topic']}' kanalına abone ol.")
        self.msg("ANKA", r); self.speak(r[:100])

    def add_contact(self, name, number, relation=""):
        clean = re.sub(r'\D','', number)
        if clean.startswith("0"):  clean = "90" + clean[1:]
        if clean.startswith("5"):  clean = "90" + clean
        self.data["contacts"][name.lower()] = {
            "name": name, "number": clean,
            "relation": relation,
            "added": datetime.date.today().isoformat(),
            "call_count": 0
        }
        _save(CALL_FILE, self.data)
        r = f"✅ Kişi eklendi: {name} (+{clean})"
        self.msg("ANKA", r); self.speak(r)

    def get_contact(self, name):
        # Tam eşleşme
        contact = self.data["contacts"].get(name.lower())
        if contact: return contact
        # Kısmi eşleşme
        for key, contact in self.data["contacts"].items():
            if name.lower() in key or name.lower() in contact["name"].lower():
                return contact
        return None

    def list_contacts(self):
        if not self.data["contacts"]:
            r = "Kayıtlı kişi yok efendim. 'kişi ekle [isim] [numara]' ile ekle."
        else:
            r = f"📱 Kayıtlı Kişiler ({len(self.data['contacts'])}):\n"
            for c in self.data["contacts"].values():
                r += f"• {c['name']}: +{c['number']}"
                if c.get("relation"): r += f" ({c['relation']})"
                r += f" — {c['call_count']}x arandı\n"
        self.msg("ANKA", r)

    # ── Ana Arama Fonksiyonu ──────────────────────────────────────────────────
    def call_you(self, reason="Anka sizi arıyor!", urgent=False, contact=None):
        # DND kontrolü
        if self._is_dnd() and not urgent:
            r = f"🔕 Rahatsız etme modu aktif. Acil aramalar için 'acil beni ara' kullanın efendim."
            self.msg("ANKA", r); return

        phone = contact["number"] if contact else self.data.get("my_phone","")
        name  = contact["name"]   if contact else USER_NAME
        if not phone:
            self.msg("ANKA",
                "📱 Numara kayıtlı değil!\n"
                "'numaramı kaydet 5XXXXXXXXX' komutuyla kaydet efendim.")
            return

        now = datetime.datetime.now().strftime("%H:%M")
        emoji = "🚨" if urgent else "📞"

        # 1. WhatsApp aç + sesli arama linki
        wa_call_url  = f"https://wa.me/{phone}"
        wa_msg_url   = f"https://wa.me/{phone}?text={urllib.parse.quote(f'{emoji} {reason} [{now}]')}"
        # Önce mesaj sayfasını aç, kullanıcı oradan sesli aramaya geçer
        webbrowser.open(wa_msg_url)

        # 2. Zil sesi
        threading.Thread(target=self._ring, args=(urgent,), daemon=True).start()

        # 3. Windows toast
        self._toast(f"{emoji} ANKA {name}'i ARIYOR!", reason, urgent)

        # 4. ntfy bildirimi
        self._ntfy(
            title=f"{emoji} ANKA ARIYOR — {now}",
            message=f"{reason}\n📲 WhatsApp'ı aç ve sesli aramayı başlat!",
            priority="urgent" if urgent else "high",
            tags=["rotating_light","telephone"] if urgent else ["telephone"]
        )

        # 5. Sesli uyarı
        self.speak(f"{'Acil! ' if urgent else ''}{name}'i arıyorum! {reason}")

        # 6. İstatistik güncelle
        self._update_stats()
        if contact:
            contact["call_count"] += 1
            _save(CALL_FILE, self.data)

        # 7. Log
        self.data["call_log"].append({
            "time": datetime.datetime.now().isoformat(),
            "reason": reason, "urgent": urgent,
            "phone": f"+{phone}", "name": name,
            "type": "anka→sen"
        })
        if len(self.data["call_log"]) > 300:
            self.data["call_log"] = self.data["call_log"][-300:]
        _save(CALL_FILE, self.data)

        r = (f"{emoji} WHATSAPP ARAMASI\n{'═'*35}\n"
             f"• Kişi: {name} (+{phone})\n"
             f"• Sebep: {reason}\n"
             f"• Saat: {now}\n"
             f"{'🚨 ACİL ARAMA!' if urgent else ''}\n"
             f"✅ WhatsApp açıldı — sesli aramayı başlat!")
        self.msg("ANKA", r)

    def call_contact(self, name, reason=""):
        """Rehberdeki kişiyi ara"""
        contact = self.get_contact(name)
        if not contact:
            self.msg("ANKA",
                f"'{name}' rehberde bulunamadı efendim.\n"
                f"'kişi ekle {name} 5XXXXXXXXX' ile ekle.")
            return
        self.call_you(
            reason or f"Anka {contact['name']}'i arıyor!",
            contact=contact
        )

    def call_anka(self, message=""):
        """Sen → Anka'yı ara (kendi numarana WhatsApp açar)"""
        phone = self.data.get("my_phone","")
        if not phone:
            self.msg("ANKA","Numara kayıtlı değil efendim."); return
        msg_text = message or f"📞 Merhaba Anka! Seninle konuşmak istiyorum. [{datetime.datetime.now().strftime('%H:%M')}]"
        wa_url = f"https://wa.me/{phone}?text={urllib.parse.quote(msg_text)}"
        webbrowser.open(wa_url)
        r = (f"📞 WhatsApp Açıldı!\n"
             f"Sesli arama butonuna basarak Anka'yı arayabilirsiniz efendim!")
        self.msg("ANKA", r)
        self.speak("WhatsApp açıldı, sesli aramayı başlatabilirsiniz efendim!")

    # ── Mesaj Gönderme ────────────────────────────────────────────────────────
    def send_whatsapp_message(self, message, contact_name=None):
        """WhatsApp mesajı gönder"""
        if contact_name:
            contact = self.get_contact(contact_name)
            phone = contact["number"] if contact else None
        else:
            phone = self.data.get("my_phone","")
        if not phone:
            self.msg("ANKA","Numara bulunamadı efendim."); return
        wa_url = f"https://wa.me/{phone}?text={urllib.parse.quote(message)}"
        webbrowser.open(wa_url)
        r = f"📨 WhatsApp mesajı hazırlandı efendim:\n'{message[:80]}'"
        self.msg("ANKA", r); self.speak("Mesaj hazırlandı efendim.")

    def ai_message(self, topic, contact_name=None):
        """AI ile mesaj yaz ve gönder"""
        def _gen():
            r = self.ollama.chat(
                f"'{topic}' hakkında kısa, samimi bir WhatsApp mesajı yaz. Emoji kullan.",
                system_override="WhatsApp mesaj yazarı. Kısa ve doğal yaz.")
            self.msg("ANKA", f"📨 AI Mesajı:\n{r}")
            if contact_name:
                self.send_whatsapp_message(r, contact_name)
            else:
                self.send_whatsapp_message(r)
        threading.Thread(target=_gen, daemon=True).start()

    # ── Planlı Arama ─────────────────────────────────────────────────────────
    def schedule_call(self, time_str, reason, repeat=False, contact_name=None, days=None):
        call = {
            "time": time_str, "reason": reason,
            "repeat": repeat, "active": True,
            "contact": contact_name,
            "days": days or ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"],
            "created": datetime.datetime.now().isoformat(),
            "call_count": 0
        }
        self.data["scheduled_calls"].append(call)
        _save(CALL_FILE, self.data)
        day_str = "her gün" if not days else ", ".join(days)
        r = (f"📅 Arama Planlandı!\n"
             f"• Saat: {time_str}\n"
             f"• Sebep: {reason}\n"
             f"• Kişi: {contact_name or USER_NAME}\n"
             f"• Tekrar: {'✅ ' + day_str if repeat else 'Bir kez'}")
        self.msg("ANKA", r)
        self.speak(f"Saat {time_str}'de arayacağım efendim.")

    def _scheduler_loop(self):
        time.sleep(30)
        while self.running:
            try:
                now = datetime.datetime.now()
                now_str  = now.strftime("%H:%M")
                today    = now.date().isoformat()
                day_abbr = now.strftime("%a")
                for call in self.data["scheduled_calls"]:
                    if not call.get("active"): continue
                    if day_abbr not in call.get("days",["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]):
                        continue
                    if call["time"] == now_str:
                        done_key = f"done_{today}_{call['time']}"
                        if not call.get(done_key):
                            call[done_key] = True
                            call["call_count"] = call.get("call_count",0) + 1
                            if not call.get("repeat"):
                                call["active"] = False
                            _save(CALL_FILE, self.data)
                            contact = self.get_contact(call["contact"]) if call.get("contact") else None
                            self.call_you(call["reason"], contact=contact)
            except: pass
            time.sleep(30)

    # ── Akıllı İzleme ────────────────────────────────────────────────────────
    def _smart_monitor(self):
        """CPU/RAM kritik olduğunda otomatik ara"""
        time.sleep(120)
        alerted = {}
        while self.running:
            try:
                today = datetime.date.today().isoformat()
                cpu = psutil.cpu_percent(interval=3)
                ram = psutil.virtual_memory().percent
                battery = psutil.sensors_battery()
                if cpu > 95 and not alerted.get(f"cpu_{today}"):
                    alerted[f"cpu_{today}"] = True
                    self.call_you("⚠️ CPU %95+ kritik! Bilgisayarınızı kontrol edin.", urgent=True)
                if ram > 95 and not alerted.get(f"ram_{today}"):
                    alerted[f"ram_{today}"] = True
                    self.call_you("⚠️ RAM %95+ kritik! Uygulama kapatın.", urgent=True)
                if battery and battery.percent < 10 and not battery.power_plugged:
                    if not alerted.get(f"batt_{today}"):
                        alerted[f"batt_{today}"] = True
                        self.call_you("🔋 Pil %10'un altında! Şarj edin.", urgent=True)
            except: pass
            time.sleep(120)

    # ── Rahatsız Etme Modu ────────────────────────────────────────────────────
    def set_dnd(self, enabled, start="23:00", end="07:00"):
        self.data["do_not_disturb"] = {
            "enabled": enabled, "start": start, "end": end
        }
        _save(CALL_FILE, self.data)
        if enabled:
            r = f"🔕 Rahatsız etme modu: {start} — {end} arası aktif efendim."
        else:
            r = "🔔 Rahatsız etme modu kapatıldı efendim."
        self.msg("ANKA", r); self.speak(r)

    def _is_dnd(self):
        dnd = self.data.get("do_not_disturb", {})
        if not dnd.get("enabled"): return False
        now = datetime.datetime.now().strftime("%H:%M")
        start, end = dnd.get("start","23:00"), dnd.get("end","07:00")
        if start <= end:
            return start <= now <= end
        return now >= start or now <= end

    # ── İstatistikler ─────────────────────────────────────────────────────────
    def _update_stats(self):
        today = datetime.date.today().isoformat()
        stats = self.data["call_stats"]
        stats["total"] += 1
        if stats.get("last_date") != today:
            stats["today"] = 0
            stats["last_date"] = today
        stats["today"] += 1
        _save(CALL_FILE, self.data)

    def call_stats(self):
        stats = self.data["call_stats"]
        log   = self.data["call_log"]
        today_calls = [c for c in log if c["time"][:10] == datetime.date.today().isoformat()]
        r = (f"📊 ARAMA İSTATİSTİKLERİ\n{'═'*30}\n"
             f"• Toplam Arama: {stats.get('total',0)}\n"
             f"• Bugün: {stats.get('today',0)}\n"
             f"• Kayıtlı Kişi: {len(self.data['contacts'])}\n"
             f"• Planlı Arama: {sum(1 for c in self.data['scheduled_calls'] if c.get('active'))}\n"
             f"• DND: {'Aktif' if self.data['do_not_disturb'].get('enabled') else 'Kapalı'}\n")
        if today_calls:
            r += f"\n📋 Bugünkü Aramalar:\n"
            for c in today_calls[-5:]:
                r += f"• {c['time'][11:16]} — {c['reason'][:40]}\n"
        self.msg("ANKA", r)

    def call_log(self, last=10):
        log = self.data["call_log"][-last:]
        if not log:
            r = "Arama geçmişi yok efendim."
        else:
            r = f"📞 Son {len(log)} Arama:\n{'═'*30}\n"
            for c in reversed(log):
                t    = c["time"][:16].replace("T"," ")
                name = c.get("name", USER_NAME)
                r += f"• {t} — {name}: {c['reason'][:40]}\n"
        self.msg("ANKA", r)

    def list_scheduled(self):
        active = [c for c in self.data["scheduled_calls"] if c.get("active")]
        if not active:
            r = "Planlanmış arama yok efendim."
        else:
            r = f"📅 Planlanmış Aramalar ({len(active)}):\n{'═'*30}\n"
            for c in active:
                r += (f"• {c['time']} — {c['reason'][:40]}\n"
                     f"  {'🔄 ' + ', '.join(c.get('days',[])) if c.get('repeat') else '1 kez'}\n")
        self.msg("ANKA", r)

    def cancel_call(self, time_str):
        cancelled = 0
        for c in self.data["scheduled_calls"]:
            if c["time"] == time_str and c.get("active"):
                c["active"] = False; cancelled += 1
        _save(CALL_FILE, self.data)
        r = f"✅ {time_str} araması iptal edildi efendim." if cancelled else f"'{time_str}' araması bulunamadı."
        self.msg("ANKA", r); self.speak(r)

    # ── Yardımcı Metodlar ─────────────────────────────────────────────────────
    def _ring(self, urgent=False):
        try:
            import winsound
            pattern = [(1200,400),(900,250),(1200,400)] if not urgent else \
                      [(1500,200),(1000,100),(1500,200),(1000,100),(1500,400)]
            for freq, dur in pattern:
                winsound.Beep(freq, dur); time.sleep(0.1)
        except:
            try:
                count = 5 if urgent else 3
                for _ in range(count):
                    subprocess.run([
                        "powershell","-Command",
                        "[console]::beep(1200,300);[console]::beep(900,200)"
                    ], capture_output=True, timeout=2)
                    time.sleep(0.3)
            except: pass

    def _toast(self, title, message, urgent=False):
        try:
            icon = "Warning" if urgent else "Information"
            script = (
                f'Add-Type -AssemblyName System.Windows.Forms;'
                f'$n=New-Object System.Windows.Forms.NotifyIcon;'
                f'$n.Icon=[System.Drawing.SystemIcons]::{icon};'
                f'$n.Visible=$true;'
                f'$n.ShowBalloonTip(8000,"{title}","{message}",'
                f'[System.Windows.Forms.ToolTipIcon]::{icon});'
                f'Start-Sleep 8;$n.Dispose()'
            )
            subprocess.Popen(
                ["powershell","-Command", script],
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        except: pass

    def _ntfy(self, title, message, priority="high", tags=None):
        try:
            requests.post(
                f"https://ntfy.sh/{self.data['ntfy_topic']}",
                data=message.encode("utf-8"),
                headers={
                    "Title": title, "Priority": priority,
                    "Tags": ",".join(tags or ["telephone"]),
                    "Content-Type": "text/plain; charset=utf-8"
                },
                timeout=5
            )
        except: pass

    def test_connection(self):
        success = False
        try:
            r = requests.post(
                f"https://ntfy.sh/{self.data['ntfy_topic']}",
                data="🧪 Anka bağlantı testi!".encode("utf-8"),
                headers={"Title":"Anka Test","Priority":"low","Tags":"white_check_mark"},
                timeout=5
            )
            success = r.status_code == 200
        except: pass
        r = ("✅ ntfy bağlantısı çalışıyor! Telefona bildirim gönderildi efendim."
             if success else
             "❌ ntfy bağlantısı yok efendim.\n"
             "1. Telefona 'ntfy' uygulaması kur\n"
             f"2. '{self.data['ntfy_topic']}' kanalına abone ol")
        self.msg("ANKA", r); self.speak(r[:100])

    def stop(self): self.running = False


# ═══════════════════════════════════════════════════════════════════════════════
# ── KOMUT İŞLEYİCİ ───────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════
class CallCommandProcessor:
    def __init__(self, speak_func, msg_func, ollama):
        self.speak = speak_func
        self.msg   = msg_func
        self.call  = AnkaCallSystem(speak_func, msg_func, ollama)
        self.wa    = WhatsAppAdvanced(self.call, ollama, speak_func, msg_func)
        self.ultra = WhatsAppUltra(self.call, ollama, speak_func, msg_func)

    def process(self, text):
        t = text.lower().strip()

        # ── Numara & Kişi ─────────────────────────────────────────────────────
        if "numaramı kaydet" in t or "numara kaydet" in t:
            m = re.search(r'[\d\s\+]{10,15}', text)
            if m: self.call.set_my_number(m.group(0).replace(" ",""))
            else: self.msg("ANKA","Format: 'numaramı kaydet 5XXXXXXXXX' efendim.")
            return True

        if "kişi ekle" in t or "rehbere ekle" in t:
            parts = t.replace("kişi ekle","").replace("rehbere ekle","").strip().split()
            if len(parts) >= 2:
                name   = parts[0].capitalize()
                number = re.sub(r'\D','',parts[1])
                rel    = " ".join(parts[2:]) if len(parts) > 2 else ""
                self.call.add_contact(name, number, rel)
            return True

        if "kişilerim" in t or "rehber" in t:
            self.call.list_contacts(); return True

        # ── Arama ────────────────────────────────────────────────────────────
        if "acil beni ara" in t or "acil ara" in t:
            reason = re.sub(r'acil beni ara|acil ara','',t).strip()
            self.call.call_you(reason or "🚨 ACİL!", urgent=True)
            return True

        if "beni ara" in t or "anka ara" in t or "hemen ara" in t:
            reason = re.sub(r'beni ara|anka ara|hemen ara','',t).strip()
            self.call.call_you(reason or f"📞 {USER_NAME}, Anka sizi arıyor!")
            return True

        if re.search(r'(\w+)(?:\'?[iıuü]yi?|yı?|yu?|yü?)?\s+ara$', t):
            m = re.search(r'(\w+)(?:\'?[iıuü]yi?|yı?|yu?|yü?)?\s+ara', t)
            if m:
                name = m.group(1)
                if name not in ["beni","hemen","acil","bana","onu","anka"]:
                    self.call.call_contact(name); return True

        if "anka'yı ara" in t or "ankayı ara" in t or "seni arıyorum" in t:
            msg = re.sub(r"anka'?yı ara|seni arıyorum",'',t).strip()
            self.call.call_anka(msg); return True

        # ── Mesaj ────────────────────────────────────────────────────────────
        if "whatsapp mesaj" in t or "mesaj gönder" in t:
            content = t.replace("whatsapp mesaj","").replace("mesaj gönder","").strip()
            m = re.search(r'(\w+)\'?[ae]\s+(.+)', content)
            if m: self.call.send_whatsapp_message(m.group(2), m.group(1))
            else:  self.call.send_whatsapp_message(content)
            return True

        if "ai mesaj yaz" in t or "ai mesajı" in t:
            topic = t.replace("ai mesaj yaz","").replace("ai mesajı","").strip()
            if topic: self.wa.ai_message(topic); return True

        # ── WhatsApp Advanced ─────────────────────────────────────────────────
        if "şablon gönder" in t or "hazır mesaj" in t:
            parts = t.replace("şablon gönder","").replace("hazır mesaj","").strip().split()
            template = parts[0] if parts else ""
            contact  = parts[1] if len(parts) > 1 else None
            if template: self.wa.send_template(template, contact)
            return True

        if "şablonlar" in t or "şablon listesi" in t:
            self.wa.list_templates(); return True

        if "şablon ekle" in t:
            parts = t.replace("şablon ekle","").strip().split("=")
            if len(parts) == 2:
                self.wa.add_template(parts[0].strip(), parts[1].strip())
            return True

        if "doğum günü mesajı" in t:
            name = t.replace("doğum günü mesajı","").strip()
            if name:
                contact = self.call.get_contact(name)
                rel = contact["relation"] if contact else "arkadaş"
                self.wa.smart_birthday_message(name, rel)
            return True

        if "hatırlatıcı mesaj" in t:
            parts = t.replace("hatırlatıcı mesaj","").strip().split("|")
            if len(parts) >= 2:
                time_m = re.search(r'(\d{1,2}:\d{2})', parts[2] if len(parts)>2 else "")
                self.wa.reminder_message(
                    parts[0].strip(), parts[1].strip(),
                    time_m.group(1) if time_m else None)
            return True

        if "konum paylaş" in t:
            loc = t.replace("konum paylaş","").strip()
            if loc: self.wa.location_share(loc); return True

        if "whatsapp raporu" in t or "arama raporu" in t:
            self.wa.call_report(); return True

        if "acil yayın" in t:
            msg = t.replace("acil yayın","").strip()
            if msg and self.call.data["contacts"]:
                contacts = list(self.call.data["contacts"].keys())
                self.wa.urgent_broadcast(msg, contacts)
            return True

        if "otomatik yanıt" in t:
            away = t.replace("otomatik yanıt","").strip()
            if away: self.wa.auto_reply_setup(away)
            return True

        # ── WhatsApp Ultra ────────────────────────────────────────────────────
        if "grup oluştur" in t:
            parts = t.replace("grup oluştur","").strip().split()
            if len(parts) >= 2:
                name    = parts[0]
                members = [m.strip() for m in " ".join(parts[1:]).split(",")]
                self.ultra.create_group(name, members)
            return True

        if "gruba mesaj" in t:
            parts = t.replace("gruba mesaj","").strip().split(maxsplit=1)
            if len(parts) == 2:
                self.ultra.send_group_message(parts[0], parts[1])
            return True

        if "gruplarım" in t or "grup listesi" in t:
            self.ultra.list_groups(); return True

        if "duygu mesajı" in t or "duygusal mesaj" in t:
            parts = t.replace("duygu mesajı","").replace("duygusal mesaj","").strip().split()
            if len(parts) >= 2:
                contact = parts[0]
                emotion = parts[1]
                extra   = " ".join(parts[2:]) if len(parts) > 2 else ""
                self.ultra.emotion_message(contact, emotion, extra)
            return True

        if "çevir ve gönder" in t:
            parts = t.replace("çevir ve gönder","").strip().split("|")
            if len(parts) >= 2:
                self.ultra.translate_and_send(parts[0].strip(), parts[1].strip(),
                    parts[2].strip() if len(parts) > 2 else None)
            return True

        if "takip planla" in t:
            parts = t.replace("takip planla","").strip().split("|")
            if len(parts) >= 2:
                days_m = re.search(r'(\d+)', parts[2] if len(parts)>2 else "1")
                days   = int(days_m.group(1)) if days_m else 1
                self.ultra.schedule_follow_up(parts[0].strip(), parts[1].strip(), days)
            return True

        if "takip kontrol" in t or "takip mesajları" in t:
            self.ultra.check_follow_ups(); return True

        if "taslak kaydet" in t:
            parts = t.replace("taslak kaydet","").strip().split(maxsplit=1)
            if len(parts) == 2:
                self.ultra.save_draft(parts[0], parts[1])
            return True

        if "taslak gönder" in t:
            parts = t.replace("taslak gönder","").strip().split()
            draft   = parts[0] if parts else ""
            contact = parts[1] if len(parts) > 1 else None
            if draft: self.ultra.send_draft(draft, contact)
            return True

        if "taslaklar" in t or "taslak listesi" in t:
            self.ultra.list_drafts(); return True

        if "iş mesajı" in t:
            parts = t.replace("iş mesajı","").strip().split("|")
            if len(parts) >= 2:
                self.ultra.business_message(parts[0].strip(), parts[1].strip(),
                    parts[2].strip() if len(parts) > 2 else None)
            return True

        if "mesajı analiz et" in t or "mesaj analizi" in t:
            content = t.replace("mesajı analiz et","").replace("mesaj analizi","").strip()
            if not content:
                try:
                    content = pyperclip.paste()
                except: pass
            if content: self.ultra.analyze_message(content)
            return True

        if "akıllı yanıt" in t or "yanıt öner" in t:
            content = t.replace("akıllı yanıt","").replace("yanıt öner","").strip()
            if not content:
                try:
                    content = pyperclip.paste()
                except: pass
            if content:
                tone = "resmi" if "resmi" in t else "samimi"
                self.ultra.smart_reply(content, tone)
            return True

        if "iş saati ayarla" in t:
            times = re.findall(r'(\d{1,2}:\d{2})', t)
            if len(times) >= 2:
                self.ultra.set_business_hours(times[0], times[1])
            return True

        if "hızlı yanıt" in t:
            parts = t.replace("hızlı yanıt","").strip().split()
            shortcut = parts[0] if parts else ""
            contact  = parts[1] if len(parts) > 1 else None
            if shortcut: self.ultra.quick_reply(shortcut, contact)
            return True

        if "kısayollar" in t or "hızlı yanıtlar" in t:
            self.ultra.list_shortcuts(); return True

        # ── Planlı Arama ──────────────────────────────────────────────────────
        if "aramayı planla" in t or "saat ara" in t or "zamanla ara" in t:
            time_m = re.search(r'(\d{1,2}:\d{2})', text)
            if time_m:
                time_str = time_m.group(1)
                reason   = re.sub(r'\d{1,2}:\d{2}|aramayı planla|saat ara|zamanla ara','',t).strip()
                repeat   = "her gün" in t or "tekrar" in t or "günlük" in t
                day_map  = {"pazartesi":"Mon","salı":"Tue","çarşamba":"Wed",
                           "perşembe":"Thu","cuma":"Fri","cumartesi":"Sat","pazar":"Sun"}
                days = [v for k,v in day_map.items() if k in t] or None
                self.call.schedule_call(time_str, reason or "Hatırlatıcı", repeat, None, days)
            return True

        if "pomodoro ara" in t:
            call_time = (datetime.datetime.now() + datetime.timedelta(minutes=25)).strftime("%H:%M")
            self.call.schedule_call(call_time, "⏰ 25 dakika doldu! Mola zamanı ☕", False)
            return True

        if re.search(r'(\d+)\s*(?:dk|dakika)\s*sonra\s*ara', t):
            m = re.search(r'(\d+)', t)
            if m:
                mins = int(m.group(1))
                call_time = (datetime.datetime.now() + datetime.timedelta(minutes=mins)).strftime("%H:%M")
                reason = re.sub(r'\d+\s*(?:dk|dakika)\s*sonra\s*ara','',t).strip()
                self.call.schedule_call(call_time, reason or f"⏰ {mins} dakika doldu!", False)
            return True

        # ── DND ───────────────────────────────────────────────────────────────
        if "rahatsız etme aç" in t or "dnd aç" in t:
            times = re.findall(r'(\d{1,2}:\d{2})', t)
            start = times[0] if times else "23:00"
            end   = times[1] if len(times) > 1 else "07:00"
            self.call.set_dnd(True, start, end); return True

        if "rahatsız etme kapat" in t or "dnd kapat" in t:
            self.call.set_dnd(False); return True

        # ── Listeler & Geçmiş ─────────────────────────────────────────────────
        if "arama geçmişi" in t: self.call.call_log(); return True
        if "planlı aramalar" in t or "aramalarım" in t:
            self.call.list_scheduled(); return True
        if "arama istatistik" in t: self.call.call_stats(); return True
        if "aramayı iptal et" in t:
            m = re.search(r'(\d{1,2}:\d{2})', t)
            if m: self.call.cancel_call(m.group(1))
            return True

        # ── Test & Ayar ───────────────────────────────────────────────────────
        if "arama testi" in t or "ntfy test" in t:
            self.call.test_connection(); return True

        if "ntfy konusu" in t or "telefon konusu" in t:
            topic = re.sub(r'ntfy konusu|telefon konusu','',t).strip()
            if topic:
                self.call.data["ntfy_topic"] = topic
                _save(CALL_FILE, self.call.data)
                r = f"✅ Bildirim konusu: {topic}"
                self.msg("ANKA", r); self.speak(r)
            return True

        # ── Yardım ────────────────────────────────────────────────────────────
        if "arama yardım" in t or "whatsapp yardım" in t:
            r = (
                "📞 ANKA WHATSAPP SİSTEMİ v4\n"
                "════════════════════════════\n\n"
                "1️⃣ KURULUM:\n"
                "• 'numaramı kaydet 5XXXXXXXXX'\n"
                "• 'kişi ekle Anne 5XXXXXXXXX aile'\n"
                "• 'ntfy' uyg. kur → anka-yusuf-2026\n\n"
                "📞 ARAMA:\n"
                "• 'beni ara [sebep]'\n"
                "• 'acil beni ara'\n"
                "• 'anneyi ara'\n"
                "• 'ankayı ara'\n\n"
                "📨 MESAJ:\n"
                "• 'whatsapp mesaj [metin]'\n"
                "• 'ai mesaj yaz [konu]'\n"
                "• 'şablon gönder günaydın [kişi]'\n"
                "• 'doğum günü mesajı [isim]'\n"
                "• 'duygu mesajı [kişi] [duygu]'\n"
                "• 'akıllı yanıt [mesaj]'\n"
                "• 'çevir ve gönder [metin]|[dil]|[kişi]'\n"
                "• 'iş mesajı toplantı|konu|kişi'\n"
                "• 'hızlı yanıt tmo [kişi]'\n\n"
                "👥 GRUP:\n"
                "• 'grup oluştur aile Anne,Baba'\n"
                "• 'gruba mesaj aile İyi geceler!'\n"
                "• 'gruplarım'\n\n"
                "📋 TASLAK:\n"
                "• 'taslak kaydet isim mesaj'\n"
                "• 'taslak gönder isim [kişi]'\n"
                "• 'taslaklar'\n\n"
                "📅 TAKİP:\n"
                "• 'takip planla kişi|konu|3'\n"
                "• 'takip kontrol'\n\n"
                "📅 PLANLI:\n"
                "• 'aramayı planla 08:30 günaydın'\n"
                "• 'pomodoro ara'\n"
                "• '45 dakika sonra ara'\n\n"
                "🔕 DND:\n"
                "• 'rahatsız etme aç 23:00 07:00'\n"
                "• 'iş saati ayarla 09:00 18:00'\n\n"
                "📊:\n"
                "• 'whatsapp raporu'\n"
                "• 'arama istatistik'\n"
                "• 'şablonlar' | 'kısayollar'\n"
                "• 'arama testi'"
            )
            self.msg("ANKA", r)
            self.speak("WhatsApp rehberi hazırlandı efendim.")
            return True

        return False

    def process(self, text):
        t = text.lower().strip()

        # ── Numara & Kişi Yönetimi ────────────────────────────────────────────
        if "numaramı kaydet" in t or "numara kaydet" in t:
            m = re.search(r'[\d\s\+]{10,15}', text)
            if m: self.call.set_my_number(m.group(0).replace(" ",""))
            else: self.msg("ANKA","Format: 'numaramı kaydet 5XXXXXXXXX' efendim.")
            return True

        if "kişi ekle" in t or "rehbere ekle" in t:
            parts = t.replace("kişi ekle","").replace("rehbere ekle","").strip().split()
            if len(parts) >= 2:
                name   = parts[0].capitalize()
                number = re.sub(r'\D','',parts[1])
                rel    = " ".join(parts[2:]) if len(parts) > 2 else ""
                self.call.add_contact(name, number, rel)
            else:
                self.msg("ANKA","Format: 'kişi ekle [isim] [numara] [ilişki]' efendim.")
            return True

        if "kişilerim" in t or "rehber" in t:
            self.call.list_contacts(); return True

        # ── Arama ────────────────────────────────────────────────────────────
        if "acil beni ara" in t or "acil ara" in t:
            reason = re.sub(r'acil beni ara|acil ara','',t).strip()
            self.call.call_you(reason or "🚨 ACİL! Lütfen hemen bakın!", urgent=True)
            return True

        if "beni ara" in t or "anka ara" in t or "hemen ara" in t:
            reason = re.sub(r'beni ara|anka ara|hemen ara','',t).strip()
            self.call.call_you(reason or f"📞 {USER_NAME}, Anka sizi arıyor!", urgent=False)
            return True

        # Kişiyi ara
        if re.search(r'(arayı|arasın|ara)\s+\w+', t) or "kişiyi ara" in t:
            # "anneyi ara", "ahmet'i ara"
            m = re.search(r'(\w+)(?:\'?[iıuü]|yi|yı|yu|yü)?\s+ara', t)
            if m:
                name = m.group(1)
                if name not in ["beni","hemen","acil","bana","onu"]:
                    reason_part = re.sub(r'\w+(?:\'?[iıuü]|yi|yı|yu|yü)?\s+ara','',t).strip()
                    self.call.call_contact(name, reason_part)
                    return True

        if "anka'yı ara" in t or "ankayı ara" in t or "seni arıyorum" in t:
            msg = re.sub(r"anka'?yı ara|seni arıyorum",'',t).strip()
            self.call.call_anka(msg); return True

        # ── Mesaj ────────────────────────────────────────────────────────────
        if "whatsapp mesaj" in t or "mesaj gönder" in t:
            content = t.replace("whatsapp mesaj","").replace("mesaj gönder","").strip()
            # Kişi adı var mı?
            contact_m = re.search(r'(\w+)\'?[ae]\s+(.+)', content)
            if contact_m:
                self.call.send_whatsapp_message(contact_m.group(2), contact_m.group(1))
            else:
                self.call.send_whatsapp_message(content)
            return True

        if "ai mesaj yaz" in t or "ai mesajı" in t:
            topic = t.replace("ai mesaj yaz","").replace("ai mesajı","").strip()
            if topic: self.call.ai_message(topic); return True

        # ── Planlı Arama ──────────────────────────────────────────────────────
        if "aramayı planla" in t or "saat ara" in t or "zamanla ara" in t:
            time_m = re.search(r'(\d{1,2}:\d{2})', text)
            if time_m:
                time_str = time_m.group(1)
                reason   = re.sub(r'\d{1,2}:\d{2}|aramayı planla|saat ara|zamanla ara','',t).strip()
                repeat   = "her gün" in t or "tekrar" in t or "günlük" in t
                # Haftalık gün tespiti
                day_map  = {"pazartesi":"Mon","salı":"Tue","çarşamba":"Wed",
                           "perşembe":"Thu","cuma":"Fri","cumartesi":"Sat","pazar":"Sun"}
                days = [v for k,v in day_map.items() if k in t]
                if not days: days = None
                self.call.schedule_call(time_str, reason or "Hatırlatıcı", repeat, None, days)
            else:
                self.msg("ANKA","Format: 'aramayı planla 08:30 [sebep]' efendim.")
            return True

        if "pomodoro ara" in t or "25 dk sonra ara" in t:
            m = re.search(r'(\d+)', t)
            mins = int(m.group(1)) if m and "pomodoro" not in t else 25
            call_time = (datetime.datetime.now() + datetime.timedelta(minutes=mins)).strftime("%H:%M")
            self.call.schedule_call(call_time, f"⏰ {mins} dakika doldu! Mola zamanı ☕", False)
            return True

        if re.search(r'(\d+)\s*(?:dk|dakika)\s*sonra\s*ara', t):
            m = re.search(r'(\d+)', t)
            if m:
                mins = int(m.group(1))
                call_time = (datetime.datetime.now() + datetime.timedelta(minutes=mins)).strftime("%H:%M")
                reason = re.sub(r'\d+\s*(?:dk|dakika)\s*sonra\s*ara','',t).strip()
                self.call.schedule_call(call_time, reason or f"⏰ {mins} dakika doldu!", False)
            return True

        # ── DND ───────────────────────────────────────────────────────────────
        if "rahatsız etme aç" in t or "dnd aç" in t:
            time_m = re.findall(r'(\d{1,2}:\d{2})', t)
            start = time_m[0] if time_m else "23:00"
            end   = time_m[1] if len(time_m) > 1 else "07:00"
            self.call.set_dnd(True, start, end); return True

        if "rahatsız etme kapat" in t or "dnd kapat" in t:
            self.call.set_dnd(False); return True

        # ── Listeler & Geçmiş ─────────────────────────────────────────────────
        if "arama geçmişi" in t: self.call.call_log(); return True
        if "planlı aramalar" in t or "aramalarım" in t:
            self.call.list_scheduled(); return True
        if "arama istatistik" in t or "kaç kez arandım" in t:
            self.call.call_stats(); return True
        if "aramayı iptal et" in t:
            m = re.search(r'(\d{1,2}:\d{2})', t)
            if m: self.call.cancel_call(m.group(1))
            return True

        # ── Test & Ayar ───────────────────────────────────────────────────────
        if "arama testi" in t or "ntfy test" in t:
            self.call.test_connection(); return True

        if "ntfy konusu" in t or "telefon konusu" in t:
            topic = re.sub(r'ntfy konusu|telefon konusu','',t).strip()
            if topic:
                self.call.data["ntfy_topic"] = topic
                _save(CALL_FILE, self.call.data)
                r = f"✅ Bildirim konusu: {topic}"
                self.msg("ANKA", r); self.speak(r)
            return True

        # ── WhatsApp Gelişmiş ─────────────────────────────────────────────────
        if "şablon gönder" in t or "hazır mesaj" in t:
            parts = t.replace("şablon gönder","").replace("hazır mesaj","").strip().split()
            template = parts[0] if parts else ""
            contact  = parts[1] if len(parts) > 1 else None
            if template: self.wa.send_template(template, contact)
            return True

        if "şablonlar" in t or "şablon listesi" in t:
            self.wa.list_templates(); return True

        if "şablon ekle" in t:
            parts = t.replace("şablon ekle","").strip().split("=")
            if len(parts) == 2:
                self.wa.add_template(parts[0].strip(), parts[1].strip())
            return True

        if "doğum günü mesajı" in t:
            name = t.replace("doğum günü mesajı","").strip()
            if name:
                contact = self.call.get_contact(name)
                rel = contact["relation"] if contact else "arkadaş"
                self.wa.smart_birthday_message(name, rel)
            return True

        if "hatırlatıcı mesaj" in t:
            parts = t.replace("hatırlatıcı mesaj","").strip().split("|")
            if len(parts) >= 2:
                contact_name = parts[0].strip()
                reminder     = parts[1].strip()
                time_m = re.search(r'(\d{1,2}:\d{2})', parts[2] if len(parts) > 2 else "")
                send_time = time_m.group(1) if time_m else None
                self.wa.reminder_message(contact_name, reminder, send_time)
            return True

        if "konum paylaş" in t:
            location = t.replace("konum paylaş","").strip()
            if location: self.wa.location_share(location)
            return True

        if "whatsapp raporu" in t or "arama raporu" in t:
            self.wa.call_report(); return True

        if "acil yayın" in t:
            msg = t.replace("acil yayın","").strip()
            if msg and self.call.data["contacts"]:
                contacts = list(self.call.data["contacts"].keys())
                self.wa.urgent_broadcast(msg, contacts)
            return True

        if "otomatik yanıt" in t:
            away = t.replace("otomatik yanıt","").strip()
            if away: self.wa.auto_reply_setup(away)
            return True

        # ── Yardım ────────────────────────────────────────────────────────────
        if "arama yardım" in t or "whatsapp yardım" in t:
            r = (
                "📞 ANKA WHATSAPP SİSTEMİ v3\n"
                "════════════════════════════\n\n"
                "1️⃣ KURULUM:\n"
                "• 'numaramı kaydet 5XXXXXXXXX'\n"
                "• 'kişi ekle Anne 5XXXXXXXXX aile'\n"
                "• Telefona 'ntfy' uyg. kur → kanal: anka-yusuf-2026\n\n"
                "📞 ARAMA:\n"
                "• 'beni ara [sebep]'\n"
                "• 'acil beni ara'\n"
                "• 'anneyi ara'\n"
                "• 'ankayı ara'\n\n"
                "📨 MESAJ:\n"
                "• 'whatsapp mesaj [metin]'\n"
                "• 'ai mesaj yaz [konu]'\n"
                "• 'şablon gönder günaydın'\n"
                "• 'şablon gönder tebrikler Anne'\n"
                "• 'doğum günü mesajı [isim]'\n"
                "• 'hatırlatıcı mesaj Anne|ilaç vakti|20:00'\n"
                "• 'konum paylaş Taksim'\n"
                "• 'acil yayın [mesaj]'\n\n"
                "📅 PLANLI:\n"
                "• 'aramayı planla 08:30 günaydın'\n"
                "• 'aramayı planla 22:00 ilaç her gün'\n"
                "• 'pomodoro ara'\n"
                "• '45 dakika sonra ara'\n\n"
                "🔕 RAHATSIZ ETME:\n"
                "• 'rahatsız etme aç 23:00 07:00'\n"
                "• 'rahatsız etme kapat'\n\n"
                "📊 RAPORLAR:\n"
                "• 'whatsapp raporu'\n"
                "• 'arama istatistik'\n"
                "• 'arama geçmişi'\n"
                "• 'planlı aramalar'\n"
                "• 'kişilerim'\n"
                "• 'şablonlar'\n"
                "• 'arama testi'"
            )
            self.msg("ANKA", r)
            self.speak("Arama sistemi rehberi hazırlandı efendim.")
            return True

        return False


# ═══════════════════════════════════════════════════════════════════════════════
# ── GELİŞMİŞ WHATSAPP ÖZELLİKLERİ ───────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

class WhatsAppAdvanced:
    """
    Gelişmiş WhatsApp özellikleri:
    - Durum mesajı gönder
    - Grup mesajı
    - Sesli not simülasyonu
    - Otomatik yanıt
    - Mesaj şablonları
    - Doğum günü mesajı
    - Hatırlatıcı mesajlar
    """
    def __init__(self, call_system, ollama, speak_func, msg_func):
        self.call   = call_system
        self.ollama = ollama
        self.speak  = speak_func
        self.msg    = msg_func
        self.templates = {
            "günaydın":       "🌅 Günaydın! Harika bir gün geçirmeni diliyorum! ☀️",
            "iyi geceler":    "🌙 İyi geceler! Güzel rüyalar! 💤",
            "geçmiş olsun":   "💙 Geçmiş olsun! Umarım çok geçmez, iyi hissedersin yakında! 🌷",
            "tebrikler":      "🎉 Tebrikler! Çok hak ettin, gurur duyuyorum! 🏆",
            "özür":           "🙏 Özür dilerim, çok üzüldüm. Umarım anlayışla karşılarsın.",
            "teşekkür":       "💚 Çok teşekkürler! Yardımın için minnettarım! 🌟",
            "neredesin":      "📍 Neredesin? Her şey yolunda mı? 🤔",
            "görüşelim":      "☕ Bu hafta buluşalım mı? Özledim! 😊",
            "başarılar":      "💪 Başarılar! Biliyorum yapabilirsin! 🚀",
            "doğum günü":     "🎂 Doğum günün kutlu olsun! Nice mutlu yıllara! 🎉🎈",
        }

    def send_template(self, template_name, contact_name=None):
        """Hazır şablondan mesaj gönder"""
        template = self.templates.get(template_name.lower())
        if not template:
            available = ", ".join(self.templates.keys())
            self.msg("ANKA", f"Şablon bulunamadı. Mevcut: {available}")
            return
        if contact_name:
            self.call.send_whatsapp_message(template, contact_name)
        else:
            self.call.send_whatsapp_message(template)
        self.msg("ANKA", f"📨 '{template_name}' şablonu gönderildi efendim!")
        self.speak(f"{template_name} şablonu gönderildi efendim.")

    def smart_birthday_message(self, name, relation="arkadaş", age=None):
        """AI ile kişiselleştirilmiş doğum günü mesajı"""
        def _gen():
            age_str = f"{age} yaşına" if age else ""
            r = self.ollama.chat(
                f"{name} ({relation}) {age_str} doğum günü için:\n"
                f"- Samimi ve sıcak\n- Emoji kullan\n- 2-3 cümle\n- Türkçe",
                system_override="WhatsApp doğum günü mesajı yazarı. Kişisel ve samimi.")
            self.msg("ANKA", f"🎂 {name} için Mesaj:\n{r}")
            self.call.send_whatsapp_message(r, name)
            self.speak(f"{name} için doğum günü mesajı gönderildi efendim.")
        import threading
        threading.Thread(target=_gen, daemon=True).start()

    def reminder_message(self, contact_name, reminder, send_time=None):
        """Birine hatırlatıcı mesaj gönder"""
        msg = f"⏰ Hatırlatma: {reminder}"
        if send_time:
            # Zamanla gönder
            def _delayed():
                import time as _time
                now_str = datetime.datetime.now().strftime("%H:%M")
                while now_str != send_time:
                    _time.sleep(30)
                    now_str = datetime.datetime.now().strftime("%H:%M")
                self.call.send_whatsapp_message(msg, contact_name)
                self.msg("ANKA", f"📨 Hatırlatıcı mesaj {contact_name}'e gönderildi efendim.")
            import threading
            threading.Thread(target=_delayed, daemon=True).start()
            self.msg("ANKA", f"✅ Saat {send_time}'de '{contact_name}'e hatırlatıcı gönderilecek efendim.")
        else:
            self.call.send_whatsapp_message(msg, contact_name)

    def bulk_message(self, contacts, message):
        """Birden fazla kişiye mesaj gönder"""
        import time as _time
        sent = 0
        for name in contacts:
            contact = self.call.get_contact(name)
            if contact:
                self.call.send_whatsapp_message(message, name)
                sent += 1
                _time.sleep(2)  # WhatsApp spam koruması için bekle
        r = f"✅ {sent}/{len(contacts)} kişiye mesaj gönderildi efendim."
        self.msg("ANKA", r); self.speak(r)

    def call_report(self):
        """Günlük arama raporu"""
        log   = self.call.data["call_log"]
        today = datetime.date.today().isoformat()
        today_calls = [c for c in log if c["time"][:10] == today]
        # Kişi bazlı istatistik
        contact_stats = {}
        for c in log:
            name = c.get("name", "Ben")
            contact_stats[name] = contact_stats.get(name, 0) + 1
        r = (f"📊 WHATSAPP RAPORU\n{'═'*35}\n"
             f"📅 Bugün: {len(today_calls)} arama\n"
             f"📈 Toplam: {len(log)} arama\n\n")
        if contact_stats:
            r += "👥 Kişi Bazlı:\n"
            for name, count in sorted(contact_stats.items(), key=lambda x: -x[1])[:5]:
                r += f"  • {name}: {count}x\n"
        if today_calls:
            r += f"\n📋 Bugünkü Aramalar:\n"
            for c in today_calls[-5:]:
                r += f"  • {c['time'][11:16]} — {c.get('name','?')}: {c['reason'][:30]}\n"
        self.msg("ANKA", r)

    def add_template(self, name, message):
        """Özel şablon ekle"""
        self.templates[name.lower()] = message
        r = f"✅ '{name}' şablonu eklendi efendim!"
        self.msg("ANKA", r); self.speak(r)

    def list_templates(self):
        r = f"📋 WhatsApp Şablonları ({len(self.templates)}):\n"
        r += "\n".join(f"• {k}" for k in self.templates.keys())
        self.msg("ANKA", r)

    def auto_reply_setup(self, away_message):
        """Otomatik yanıt mesajı ayarla"""
        self.call.data["auto_reply"] = {
            "enabled": True,
            "message": away_message,
            "set_at": datetime.datetime.now().isoformat()
        }
        _save(CALL_FILE, self.call.data)
        r = f"✅ Otomatik yanıt ayarlandı: '{away_message[:50]}' efendim."
        self.msg("ANKA", r); self.speak(r)

    def location_share(self, location_name):
        """Konum paylaş (Google Maps linki)"""
        import urllib.parse
        maps_url = f"https://www.google.com/maps/search/{urllib.parse.quote(location_name)}"
        phone = self.call.data.get("my_phone","")
        if not phone:
            self.msg("ANKA","Numara kayıtlı değil efendim."); return
        msg = f"📍 Konum: {location_name}\n{maps_url}"
        wa_url = f"https://wa.me/{phone}?text={urllib.parse.quote(msg)}"
        import webbrowser
        webbrowser.open(wa_url)
        self.msg("ANKA", f"📍 '{location_name}' konumu WhatsApp'ta paylaşıldı efendim!")

    def urgent_broadcast(self, message, contacts):
        """Acil durum — tüm kişilere bildirim"""
        import time as _time
        self.msg("ANKA", f"🚨 Acil yayın başlatılıyor ({len(contacts)} kişi)...")
        for name in contacts:
            self.call.send_whatsapp_message(f"🚨 ACİL: {message}", name)
            _time.sleep(1.5)
        # ntfy ile de gönder
        self.call._ntfy(
            title="🚨 ANKA ACİL YAYIN",
            message=message,
            priority="urgent",
            tags=["rotating_light","loudspeaker"]
        )
        r = f"✅ Acil yayın {len(contacts)} kişiye gönderildi efendim!"
        self.msg("ANKA", r); self.speak(r)


# ═══════════════════════════════════════════════════════════════════════════════
# ── WHATSAPP ULTRA — En Gelişmiş Özellikler ───────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

class WhatsAppUltra:
    """
    Ultra gelişmiş WhatsApp özellikleri:
    - Akıllı mesaj zamanlayıcı
    - Duygu bazlı mesaj
    - Çoklu dil desteği
    - Sesli not metni
    - Mesaj analizi
    - Otomatik takip
    - Grup yönetimi
    - İş mesajları
    - Kişisel günlük
    """
    def __init__(self, call_system, ollama, speak_func, msg_func):
        self.call   = call_system
        self.ollama = ollama
        self.speak  = speak_func
        self.msg    = msg_func
        self.ultra_file = os.path.join(BASE_DIR, "anka_wa_ultra.json")
        self.data = _load(self.ultra_file, {
            "groups":         {},
            "follow_ups":     [],
            "message_drafts": {},
            "business_hours": {"start": "09:00", "end": "18:00", "enabled": False},
            "language_prefs": {},
            "sent_log":       []
        })

    # ── Grup Yönetimi ─────────────────────────────────────────────────────────
    def create_group(self, group_name, members):
        """Sanal grup oluştur"""
        self.data["groups"][group_name.lower()] = {
            "name": group_name,
            "members": members,
            "created": datetime.date.today().isoformat(),
            "message_count": 0
        }
        _save(self.ultra_file, self.data)
        r = (f"✅ Grup oluşturuldu: {group_name}\n"
             f"👥 Üyeler: {', '.join(members)}\n"
             f"'gruba mesaj [grup adı] [mesaj]' ile mesaj gönder!")
        self.msg("ANKA", r); self.speak(r[:100])

    def send_group_message(self, group_name, message):
        """Gruba mesaj gönder"""
        group = self.data["groups"].get(group_name.lower())
        if not group:
            self.msg("ANKA", f"'{group_name}' grubu bulunamadı efendim.")
            return
        members = group["members"]
        import time as _time
        sent = 0
        self.msg("ANKA", f"📨 {group_name} grubuna ({len(members)} kişi) mesaj gönderiliyor...")
        for member in members:
            self.call.send_whatsapp_message(message, member)
            sent += 1
            _time.sleep(1.5)
        group["message_count"] += 1
        _save(self.ultra_file, self.data)
        r = f"✅ {sent} kişiye mesaj gönderildi efendim!"
        self.msg("ANKA", r); self.speak(r)

    def list_groups(self):
        if not self.data["groups"]:
            self.msg("ANKA", "Grup yok. 'grup oluştur [isim] [üye1,üye2]' ile oluştur efendim.")
            return
        r = f"👥 WhatsApp Grupları ({len(self.data['groups'])}):\n"
        for g in self.data["groups"].values():
            r += f"• {g['name']}: {', '.join(g['members'])} ({g['message_count']} mesaj)\n"
        self.msg("ANKA", r)

    # ── Duygu Bazlı Mesaj ─────────────────────────────────────────────────────
    def emotion_message(self, contact_name, emotion, extra_context=""):
        """Duyguya göre mesaj yaz ve gönder"""
        def _gen():
            emotion_prompts = {
                "üzgün":      "Üzgün birine moral veren, empatik mesaj yaz.",
                "mutlu":      "Mutlu birini tebrik eden, neşeli mesaj yaz.",
                "stresli":    "Stresli birine sakinleştirici, destek mesajı yaz.",
                "yorgun":     "Yorgun birine dinlendirici, anlayışlı mesaj yaz.",
                "başarılı":   "Başarı kazanan birine tebrik mesajı yaz.",
                "hasta":      "Hasta birine geçmiş olsun mesajı yaz.",
                "özleyen":    "Özlem duyduğun birine samimi mesaj yaz.",
                "endişeli":   "Endişeli birine rahatlatıcı mesaj yaz.",
            }
            prompt = emotion_prompts.get(emotion.lower(),
                f"{emotion} hisseden birine uygun mesaj yaz.")
            r = self.ollama.chat(
                f"Kişi: {contact_name}\nDurum: {emotion}\n"
                f"Ek bilgi: {extra_context}\n{prompt}\n"
                f"Kısa (2-3 cümle), emoji kullan, Türkçe.",
                system_override="Duygusal zeka mesaj yazarı. Empatiyle yaz.")
            self.msg("ANKA", f"💌 {contact_name} için ({emotion}):\n{r}")
            self.call.send_whatsapp_message(r, contact_name)
            self.speak(f"{contact_name} için {emotion} mesajı gönderildi efendim.")
        import threading
        threading.Thread(target=_gen, daemon=True).start()

    # ── Çok Dilli Mesaj ───────────────────────────────────────────────────────
    def translate_and_send(self, message, target_language, contact_name=None):
        """Mesajı çevir ve gönder"""
        def _translate():
            r = self.ollama.chat(
                f"Bu mesajı {target_language} diline çevir:\n{message}\n\nSadece çeviriyi ver.",
                system_override="Çevirmen. Doğal çeviri yap.")
            self.msg("ANKA", f"🌐 {target_language}:\n{r}")
            if contact_name:
                self.call.send_whatsapp_message(r, contact_name)
            else:
                self.call.send_whatsapp_message(r)
            self.speak(f"Mesaj {target_language}'e çevrildi ve gönderildi efendim.")
        import threading
        threading.Thread(target=_translate, daemon=True).start()

    # ── Takip Mesajı ──────────────────────────────────────────────────────────
    def schedule_follow_up(self, contact_name, topic, days=1):
        """Belirli gün sonra takip mesajı gönder"""
        follow_date = (datetime.date.today() + datetime.timedelta(days=days)).isoformat()
        self.data["follow_ups"].append({
            "contact": contact_name,
            "topic": topic,
            "date": follow_date,
            "done": False
        })
        _save(self.ultra_file, self.data)
        r = (f"✅ Takip planlandı!\n"
             f"• Kişi: {contact_name}\n"
             f"• Konu: {topic}\n"
             f"• Tarih: {follow_date} ({days} gün sonra)")
        self.msg("ANKA", r); self.speak(r[:100])

    def check_follow_ups(self):
        """Takip mesajlarını kontrol et"""
        today = datetime.date.today().isoformat()
        due = [f for f in self.data["follow_ups"]
               if f["date"] <= today and not f["done"]]
        if not due:
            self.msg("ANKA", "Bugün için takip mesajı yok efendim."); return
        r = f"📋 Takip Edilecekler ({len(due)}):\n"
        for f in due:
            r += f"• {f['contact']}: {f['topic']}\n"
        self.msg("ANKA", r)
        self.speak(f"{len(due)} takip mesajı var efendim!")

    # ── Taslak Mesaj ──────────────────────────────────────────────────────────
    def save_draft(self, name, message):
        """Mesaj taslağı kaydet"""
        self.data["message_drafts"][name.lower()] = {
            "name": name, "message": message,
            "saved": datetime.datetime.now().isoformat()
        }
        _save(self.ultra_file, self.data)
        r = f"✅ '{name}' taslağı kaydedildi efendim."
        self.msg("ANKA", r); self.speak(r)

    def send_draft(self, draft_name, contact_name=None):
        """Taslak mesajı gönder"""
        draft = self.data["message_drafts"].get(draft_name.lower())
        if not draft:
            self.msg("ANKA", f"'{draft_name}' taslağı bulunamadı efendim.")
            return
        self.call.send_whatsapp_message(draft["message"], contact_name)
        r = f"✅ '{draft_name}' taslağı gönderildi efendim!"
        self.msg("ANKA", r); self.speak(r)

    def list_drafts(self):
        if not self.data["message_drafts"]:
            self.msg("ANKA","Taslak yok. 'taslak kaydet [isim] [mesaj]' ile ekle efendim.")
            return
        r = f"📝 Taslaklar ({len(self.data['message_drafts'])}):\n"
        for d in self.data["message_drafts"].values():
            r += f"• {d['name']}: {d['message'][:40]}...\n"
        self.msg("ANKA", r)

    # ── İş Mesajları ──────────────────────────────────────────────────────────
    def business_message(self, msg_type, details, contact_name=None):
        """Profesyonel iş mesajı"""
        def _biz():
            templates = {
                "toplantı":    f"Merhaba, {details} hakkında bir toplantı ayarlamak istiyorum. Uygun zamanınız var mı?",
                "teklif":      f"Sayın Yetkili, {details} konusunda bir teklifimiz var. Detayları paylaşabilir miyim?",
                "takip":       f"Merhaba, önceki görüşmemizde {details} konusunu konuşmuştuk. Gelişme var mı?",
                "teşekkür":    f"Merhaba, {details} konusundaki yardımlarınız için çok teşekkür ederim.",
                "özür":        f"Merhaba, {details} konusunda yaşanan aksaklık için içtenlikle özür dilerim.",
                "bilgilendirme": f"Bilginize: {details}",
            }
            if msg_type.lower() in templates:
                message = templates[msg_type.lower()]
            else:
                message = self.ollama.chat(
                    f"Profesyonel WhatsApp mesajı yaz:\nTür: {msg_type}\nDetay: {details}",
                    system_override="İş iletişimi uzmanı. Profesyonel Türkçe yaz.")
            self.msg("ANKA", f"💼 İş Mesajı ({msg_type}):\n{message}")
            if contact_name:
                self.call.send_whatsapp_message(message, contact_name)
            self.speak("İş mesajı hazırlandı efendim.")
        import threading
        threading.Thread(target=_biz, daemon=True).start()

    # ── Mesaj Analizi ─────────────────────────────────────────────────────────
    def analyze_message(self, message):
        """Gelen mesajı analiz et"""
        def _analyze():
            r = self.ollama.chat(
                f"Bu WhatsApp mesajını analiz et:\n'{message}'\n\n"
                f"1. Ton (resmi/samimi/acil/sinirli)\n"
                f"2. Ana istek/amaç\n"
                f"3. Önerilen yanıt yaklaşımı\n"
                f"4. Aciliyet seviyesi (1-10)",
                system_override="Mesaj analisti. Kısa ve net analiz yap.")
            self.msg("ANKA", f"📊 Mesaj Analizi:\n{r}")
            self.speak("Mesaj analizi tamamlandı efendim.")
        import threading
        threading.Thread(target=_analyze, daemon=True).start()

    def smart_reply(self, received_message, tone="samimi"):
        """Gelen mesaja akıllı yanıt üret"""
        def _reply():
            r = self.ollama.chat(
                f"Gelen mesaj: '{received_message}'\n"
                f"Ton: {tone}\n"
                f"Bu mesaja uygun kısa yanıt yaz. Emoji kullan.",
                system_override="WhatsApp yanıt uzmanı. Doğal ve uygun yanıt yaz.")
            self.msg("ANKA", f"💬 Önerilen Yanıt:\n{r}")
            try:
                pyperclip.copy(r)
            except: pass
            self.speak("Yanıt hazırlandı ve kopyalandı efendim.")
        import threading
        threading.Thread(target=_reply, daemon=True).start()

    # ── İş Saati Kontrolü ─────────────────────────────────────────────────────
    def set_business_hours(self, start, end, enabled=True):
        """İş saatlerini ayarla"""
        self.data["business_hours"] = {
            "start": start, "end": end, "enabled": enabled
        }
        _save(self.ultra_file, self.data)
        r = (f"✅ İş saatleri: {start} — {end}\n"
             f"Bu saatler dışında DND otomatik aktif efendim.")
        self.msg("ANKA", r); self.speak(r[:100])

    def is_business_hours(self):
        bh = self.data["business_hours"]
        if not bh.get("enabled"): return True
        now = datetime.datetime.now().strftime("%H:%M")
        return bh["start"] <= now <= bh["end"]

    # ── Hızlı Cevap Kısayolları ───────────────────────────────────────────────
    def quick_reply(self, shortcut, contact_name=None):
        """Hızlı yanıt kısayolları"""
        shortcuts = {
            "yv":  "Yoldayım, birazdan geliyorum! 🚗",
            "gly": "Geliyorum! ⚡",
            "tmo": "Tamam, olur! ✅",
            "hyr": "Hayır, uygun değilim 🙅",
            "nrd": "Neredesin? 📍",
            "bkr": "Birazdan yazarım, şu an meşgulüm 🙏",
            "sry": "Özür dilerim! 🙏",
            "tşk": "Teşekkürler! 🙏💚",
            "gün": "Günaydın! ☀️🌟",
            "gec": "İyi geceler! 🌙💤",
            "hbr": "Ne haber? 😊",
            "ok":  "Tamam 👍",
        }
        message = shortcuts.get(shortcut.lower())
        if message:
            if contact_name:
                self.call.send_whatsapp_message(message, contact_name)
            else:
                self.call.send_whatsapp_message(message)
            self.msg("ANKA", f"✅ Hızlı yanıt: '{message}' gönderildi efendim.")
        else:
            available = ", ".join(shortcuts.keys())
            self.msg("ANKA", f"Kısayol bulunamadı. Mevcut: {available}")

    def list_shortcuts(self):
        shortcuts = {
            "yv":"Yoldayım","gly":"Geliyorum","tmo":"Tamam olur",
            "hyr":"Hayır","nrd":"Neredesin","bkr":"Meşgulüm",
            "sry":"Özür","tşk":"Teşekkür","gün":"Günaydın",
            "gec":"İyi geceler","hbr":"Ne haber","ok":"Tamam"
        }
        r = "⚡ Hızlı Yanıt Kısayolları:\n"
        r += "\n".join(f"• '{k}' → {v}" for k,v in shortcuts.items())
        self.msg("ANKA", r)
