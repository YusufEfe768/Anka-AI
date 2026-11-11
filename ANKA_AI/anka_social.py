# ── ANKA SOCIAL & İLETİŞİM MODÜLü ────────────────────────────────────────────
try:
    import pyperclip
except ImportError:
    class _PyClip:
        def copy(self,x):pass
        def paste(self):return ""
    pyperclip=_PyClip()
import json, os, time, threading, datetime, subprocess, webbrowser, re
import requests, random, psutil
from anka_config import BASE_DIR, USER_NAME

SOCIAL_FILE = os.path.join(BASE_DIR, "anka_social.json")

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


# ═══════════════════════════════════════════════════════════════════════════════
# 1. TOPLANTI ASISTANI — Toplantı hazırlık ve özet
# ═══════════════════════════════════════════════════════════════════════════════
class MeetingAssistant:
    def __init__(self, ollama, speak_func, msg_func):
        self.ollama = ollama
        self.speak = speak_func
        self.msg = msg_func
        self.meetings_file = os.path.join(BASE_DIR, "anka_meetings.json")
        self.data = _load(self.meetings_file, {"meetings": [], "notes": {}})

    def prepare(self, topic, participants="", duration=60):
        def _p():
            r = self.ollama.chat(
                f"Toplantı: '{topic}'\nKatılımcılar: {participants}\nSüre: {duration} dakika\n"
                f"Hazırlık listesi, gündem maddeleri, olası sorular ve hedefler.",
                system_override="Toplantı koordinatörü. Kapsamlı hazırlık yap.")
            self.msg("ANKA", f"📋 Toplantı Hazırlığı:\n{r}")
            pyperclip.copy(r)
            self.speak("Toplantı hazırlığı tamamlandı efendim.")
        threading.Thread(target=_p, daemon=True).start()

    def take_notes(self, meeting_id, note):
        if meeting_id not in self.data["notes"]:
            self.data["notes"][meeting_id] = []
        self.data["notes"][meeting_id].append({
            "note": note, "time": datetime.datetime.now().strftime("%H:%M")
        })
        _save(self.meetings_file, self.data)
        self.msg("ANKA", f"📝 Not alındı: {note[:50]}")

    def summarize_notes(self, meeting_id):
        def _s():
            notes = self.data["notes"].get(meeting_id, [])
            if not notes:
                self.msg("ANKA", "Bu toplantı için not yok efendim."); return
            notes_text = "\n".join(f"[{n['time']}] {n['note']}" for n in notes)
            r = self.ollama.chat(
                f"Bu toplantı notlarını özetle:\n{notes_text}\n\n"
                f"Kararlar, aksiyon maddeleri ve sonuçları belirt.",
                system_override="Toplantı sekreteri. Net özet yap.")
            self.msg("ANKA", f"📊 Toplantı Özeti:\n{r}")
            pyperclip.copy(r)
            self.speak("Toplantı özeti hazırlandı efendim.")
        threading.Thread(target=_s, daemon=True).start()

    def action_items(self, meeting_notes):
        def _a():
            r = self.ollama.chat(
                f"Bu toplantı notlarından aksiyon maddelerini çıkar:\n{meeting_notes}\n\n"
                f"Kim, ne yapacak, ne zaman? Madde madde listele.",
                system_override="Proje yöneticisi. Aksiyon maddeleri çıkar.")
            self.msg("ANKA", f"✅ Aksiyon Maddeleri:\n{r}")
            pyperclip.copy(r)
        threading.Thread(target=_a, daemon=True).start()


# ═══════════════════════════════════════════════════════════════════════════════
# 2. E-POSTA ASISTANI — Akıllı mail yazma
# ═══════════════════════════════════════════════════════════════════════════════
class EmailAssistant:
    def __init__(self, ollama, speak_func, msg_func):
        self.ollama = ollama
        self.speak = speak_func
        self.msg = msg_func

    def compose(self, subject, context, tone="profesyonel", recipient=""):
        def _c():
            r = self.ollama.chat(
                f"Konu: {subject}\nBağlam: {context}\nTon: {tone}\n"
                f"{'Alıcı: ' + recipient if recipient else ''}\n\n"
                f"Profesyonel Türkçe e-posta yaz. Konu satırı dahil.",
                system_override="E-posta uzmanı. Etkili mail yaz.")
            self.msg("ANKA", f"📧 E-posta:\n{r}")
            pyperclip.copy(r)
            self.speak("E-posta hazırlandı ve kopyalandı efendim.")
        threading.Thread(target=_c, daemon=True).start()

    def reply(self, original_email, instruction):
        def _r():
            r = self.ollama.chat(
                f"Orijinal mail:\n{original_email}\n\n"
                f"Bu maile şu talimatla cevap yaz: {instruction}",
                system_override="E-posta uzmanı. Uygun cevap yaz.")
            self.msg("ANKA", f"📧 Cevap:\n{r}")
            pyperclip.copy(r)
            self.speak("Mail cevabı hazırlandı efendim.")
        threading.Thread(target=_r, daemon=True).start()

    def templates(self, template_type):
        templates = {
            "özür": "Konu: Özür Diliyorum\n\nSayın [İsim],\n\n[Durum] nedeniyle yaşanan aksaklık için içtenlikle özür dilerim...",
            "teşekkür": "Konu: Teşekkürler\n\nSayın [İsim],\n\n[Konu] için çok teşekkür ederim. Desteğiniz gerçekten değerliydi...",
            "talep": "Konu: [Konu] Hakkında Talep\n\nSayın [İsim],\n\n[Talep] konusunda yardımınızı rica ediyorum...",
            "bilgilendirme": "Konu: Bilgilendirme: [Konu]\n\nSayın [İsim],\n\nBu mail [konu] hakkında sizi bilgilendirmek amacıyla gönderilmektedir...",
            "davet": "Konu: Davet - [Etkinlik]\n\nSayın [İsim],\n\nSizi [etkinlik]'e davet etmekten büyük mutluluk duyarım...",
        }
        template = templates.get(template_type.lower())
        if template:
            pyperclip.copy(template)
            self.msg("ANKA", f"📧 {template_type.capitalize()} Şablonu:\n{template}\n\n✓ Kopyalandı!")
            self.speak("Şablon kopyalandı efendim.")
        else:
            available = ", ".join(templates.keys())
            self.msg("ANKA", f"Mevcut şablonlar: {available}")

    def analyze_email(self, email_text):
        def _a():
            r = self.ollama.chat(
                f"Bu maili analiz et:\n{email_text}\n\n"
                f"Ton, ana mesaj, beklentiler ve önerilen cevap yönü.",
                system_override="İletişim uzmanı. Mail analizi yap.")
            self.msg("ANKA", f"📊 Mail Analizi:\n{r}")
        threading.Thread(target=_a, daemon=True).start()


# ═══════════════════════════════════════════════════════════════════════════════
# 3. DOĞUM GÜNÜ & ÖZEL GÜN TAKİBİ
# ═══════════════════════════════════════════════════════════════════════════════
class SpecialDayTracker:
    def __init__(self, ollama, speak_func, msg_func):
        self.ollama = ollama
        self.speak = speak_func
        self.msg = msg_func
        self.days_file = os.path.join(BASE_DIR, "anka_special_days.json")
        self.data = _load(self.days_file, {"birthdays": [], "anniversaries": [], "events": []})
        self.running = True
        threading.Thread(target=self._check_loop, daemon=True).start()

    def add_birthday(self, name, date, relation="arkadaş"):
        self.data["birthdays"].append({
            "name": name, "date": date, "relation": relation,
            "added": datetime.date.today().isoformat()
        })
        _save(self.days_file, self.data)
        r = f"🎂 {name}'in doğum günü kaydedildi: {date}"
        self.msg("ANKA", r); self.speak(r)

    def upcoming_birthdays(self, days=30):
        today = datetime.date.today()
        upcoming = []
        for b in self.data["birthdays"]:
            try:
                parts = b["date"].split("-")
                month, day = int(parts[0]), int(parts[1])
                birthday_this_year = datetime.date(today.year, month, day)
                if birthday_this_year < today:
                    birthday_this_year = datetime.date(today.year + 1, month, day)
                diff = (birthday_this_year - today).days
                if diff <= days:
                    upcoming.append((b["name"], diff, b["relation"], birthday_this_year))
            except: pass
        upcoming.sort(key=lambda x: x[1])
        if not upcoming:
            r = f"Önümüzdeki {days} günde doğum günü yok efendim."
        else:
            r = f"🎂 Yaklaşan Doğum Günleri:\n{'═'*30}\n"
            for name, diff, relation, date in upcoming[:10]:
                if diff == 0:
                    r += f"🎉 BUGÜN: {name} ({relation})\n"
                elif diff == 1:
                    r += f"⚡ YARIN: {name} ({relation})\n"
                else:
                    r += f"• {diff} gün: {name} ({relation}) — {date.strftime('%d %B')}\n"
        self.msg("ANKA", r)
        if upcoming and upcoming[0][1] <= 3:
            self.speak(f"Dikkat! {upcoming[0][0]}'in doğum günü {upcoming[0][1]} gün sonra efendim!")

    def birthday_message(self, name, relation="arkadaş"):
        def _m():
            r = self.ollama.chat(
                f"{name} ({relation}) için sıcak ve samimi doğum günü mesajı yaz. Türkçe.",
                system_override="Duygusal yazar. Kişiselleştirilmiş mesaj yaz.")
            self.msg("ANKA", f"🎂 {name} için Mesaj:\n{r}")
            pyperclip.copy(r)
            self.speak("Doğum günü mesajı hazırlandı efendim.")
        threading.Thread(target=_m, daemon=True).start()

    def _check_loop(self):
        time.sleep(30)
        while self.running:
            try:
                today = datetime.date.today()
                for b in self.data["birthdays"]:
                    parts = b["date"].split("-")
                    if len(parts) >= 2:
                        month, day = int(parts[0]), int(parts[1])
                        if today.month == month and today.day == day:
                            key = f"bday_{b['name']}_{today.isoformat()}"
                            if not _load(os.path.join(BASE_DIR, "anka_notified.json"), {}).get(key):
                                notified = _load(os.path.join(BASE_DIR, "anka_notified.json"), {})
                                notified[key] = True
                                _save(os.path.join(BASE_DIR, "anka_notified.json"), notified)
                                r = f"🎂 BUGÜN {b['name']}'in doğum günü!"
                                self.msg("ANKA", r)
                                self.speak(f"{b['name']}'in bugün doğum günü efendim!")
            except: pass
            time.sleep(3600)

    def stop(self): self.running = False


# ═══════════════════════════════════════════════════════════════════════════════
# 4. ALIŞVERIŞ ASISTANI
# ═══════════════════════════════════════════════════════════════════════════════
class ShoppingAssistant:
    def __init__(self, ollama, speak_func, msg_func):
        self.ollama = ollama
        self.speak = speak_func
        self.msg = msg_func
        self.shopping_file = os.path.join(BASE_DIR, "anka_shopping.json")
        self.data = _load(self.shopping_file, {"lists": {}, "history": []})

    def add_item(self, item, list_name="genel", quantity=1, priority="normal"):
        if list_name not in self.data["lists"]:
            self.data["lists"][list_name] = []
        self.data["lists"][list_name].append({
            "item": item, "quantity": quantity,
            "priority": priority, "done": False,
            "added": datetime.date.today().isoformat()
        })
        _save(self.shopping_file, self.data)
        r = f"🛒 '{item}' listeye eklendi ({list_name})"
        self.msg("ANKA", r); self.speak(r)

    def show_list(self, list_name="genel"):
        items = self.data["lists"].get(list_name, [])
        pending = [i for i in items if not i["done"]]
        if not pending:
            r = f"'{list_name}' listesi boş efendim."
        else:
            r = f"🛒 {list_name.capitalize()} Listesi ({len(pending)} ürün):\n"
            high = [i for i in pending if i["priority"] == "yüksek"]
            normal = [i for i in pending if i["priority"] != "yüksek"]
            if high:
                r += "🔴 Öncelikli:\n" + "".join(f"  • {i['item']} (x{i['quantity']})\n" for i in high)
            r += "".join(f"• {i['item']} (x{i['quantity']})\n" for i in normal[:15])
        self.msg("ANKA", r)

    def complete_item(self, item, list_name="genel"):
        for i in self.data["lists"].get(list_name, []):
            if item.lower() in i["item"].lower():
                i["done"] = True
                _save(self.shopping_file, self.data)
                r = f"✅ '{i['item']}' sepetten çıkarıldı efendim."
                self.msg("ANKA", r); self.speak(r)
                return True
        return False

    def smart_list(self, occasion):
        def _s():
            r = self.ollama.chat(
                f"'{occasion}' için alışveriş listesi oluştur. "
                f"Kategorilere göre düzenle, tahmini fiyatları belirt.",
                system_override="Alışveriş uzmanı. Kapsamlı liste yap.")
            self.msg("ANKA", f"🛒 {occasion} Listesi:\n{r}")
            pyperclip.copy(r)
            self.speak("Alışveriş listesi hazırlandı efendim.")
        threading.Thread(target=_s, daemon=True).start()

    def price_compare(self, product):
        def _p():
            r = self.ollama.chat(
                f"'{product}' için fiyat karşılaştırma ipuçları ver. "
                f"Hangi platformlarda aranmalı, nelere dikkat edilmeli.",
                system_override="Akıllı alışveriş danışmanı. Fiyat karşılaştırma yap.")
            self.msg("ANKA", f"💰 {product} Fiyat Analizi:\n{r}")
        threading.Thread(target=_p, daemon=True).start()


# ═══════════════════════════════════════════════════════════════════════════════
# 5. KİŞİSEL ASISTAN PRO — Hatırlatma ve organizasyon
# ═══════════════════════════════════════════════════════════════════════════════
class PersonalAssistantPro:
    def __init__(self, ollama, speak_func, msg_func):
        self.ollama = ollama
        self.speak = speak_func
        self.msg = msg_func
        self.pa_file = os.path.join(BASE_DIR, "anka_pa_pro.json")
        self.data = _load(self.pa_file, {
            "contacts": {}, "tasks": [], "notes": [],
            "delegated": [], "waiting_for": []
        })

    def add_contact(self, name, phone="", email="", notes="", relation=""):
        self.data["contacts"][name.lower()] = {
            "name": name, "phone": phone, "email": email,
            "notes": notes, "relation": relation,
            "added": datetime.date.today().isoformat(),
            "last_contact": None
        }
        _save(self.pa_file, self.data)
        r = f"👤 '{name}' kişi rehberine eklendi efendim."
        self.msg("ANKA", r); self.speak(r)

    def find_contact(self, name):
        contact = self.data["contacts"].get(name.lower())
        if not contact:
            similar = [(k,v) for k,v in self.data["contacts"].items()
                      if name.lower() in k or name.lower() in v["name"].lower()]
            if similar: contact = similar[0][1]
        if contact:
            r = (f"👤 {contact['name']}:\n"
                 f"{'• Tel: ' + contact['phone'] + chr(10) if contact.get('phone') else ''}"
                 f"{'• Mail: ' + contact['email'] + chr(10) if contact.get('email') else ''}"
                 f"{'• İlişki: ' + contact['relation'] + chr(10) if contact.get('relation') else ''}"
                 f"{'• Not: ' + contact['notes'] if contact.get('notes') else ''}")
            self.msg("ANKA", r)
            if contact.get("phone"):
                pyperclip.copy(contact["phone"])
                self.speak(f"{contact['name']}'in numarası kopyalandı efendim.")
        else:
            self.msg("ANKA", f"'{name}' rehberde bulunamadı efendim.")

    def add_task(self, task, due=None, priority=5, context=""):
        self.data["tasks"].append({
            "task": task, "due": due, "priority": priority,
            "context": context, "done": False,
            "added": datetime.datetime.now().isoformat()
        })
        self.data["tasks"].sort(key=lambda x: -x["priority"])
        _save(self.pa_file, self.data)
        r = f"✅ Görev eklendi: {task}" + (f" (Öncelik: {priority}/10)" if priority != 5 else "")
        self.msg("ANKA", r); self.speak(r)

    def next_action(self):
        pending = [t for t in self.data["tasks"] if not t["done"]]
        if not pending:
            r = "Yapılacak görev yok efendim! 🎉"
        else:
            top = pending[0]
            r = (f"🎯 Şu An Yapılacak:\n{'═'*30}\n"
                 f"• {top['task']}\n"
                 f"• Öncelik: {top['priority']}/10\n"
                 f"{'• Bağlam: ' + top['context'] if top.get('context') else ''}\n\n"
                 f"📋 Bekleyen: {len(pending)} görev")
        self.msg("ANKA", r); self.speak(r[:200])

    def add_note_quick(self, note):
        self.data["notes"].append({
            "note": note,
            "date": datetime.datetime.now().isoformat()
        })
        _save(self.pa_file, self.data)
        r = f"📝 Not alındı: {note[:50]}"
        self.msg("ANKA", r); self.speak(r)

    def show_notes(self, last=5):
        notes = self.data["notes"][-last:]
        if not notes:
            r = "Not yok efendim."
        else:
            r = f"📝 Son {len(notes)} Not:\n"
            r += "\n".join(f"• [{n['date'][:10]}] {n['note'][:60]}" for n in reversed(notes))
        self.msg("ANKA", r)

    def weekly_review_pa(self):
        def _w():
            pending = [t for t in self.data["tasks"] if not t["done"]]
            done = [t for t in self.data["tasks"] if t["done"]]
            notes_count = len(self.data["notes"])
            contacts_count = len(self.data["contacts"])
            r = (f"📊 HAFTALIK ÖZET\n{'═'*30}\n"
                 f"✅ Tamamlanan: {len(done)}\n"
                 f"⏳ Bekleyen: {len(pending)}\n"
                 f"📝 Notlar: {notes_count}\n"
                 f"👥 Kişiler: {contacts_count}\n")
            if pending:
                r += f"\n🔴 Öncelikli Görevler:\n"
                r += "\n".join(f"• {t['task']}" for t in pending[:3])
            self.msg("ANKA", r)
            self.speak("Haftalık özet hazırlandı efendim.")
        threading.Thread(target=_w, daemon=True).start()


# ═══════════════════════════════════════════════════════════════════════════════
# KOMUT İŞLEYİCİ
# ═══════════════════════════════════════════════════════════════════════════════
class SocialCommandProcessor:
    def __init__(self, speak_func, msg_func, ollama):
        self.speak = speak_func
        self.msg = msg_func
        self.ollama = ollama
        self.meeting = MeetingAssistant(ollama, speak_func, msg_func)
        self.email = EmailAssistant(ollama, speak_func, msg_func)
        self.birthdays = SpecialDayTracker(ollama, speak_func, msg_func)
        self.shopping = ShoppingAssistant(ollama, speak_func, msg_func)
        self.pa = PersonalAssistantPro(ollama, speak_func, msg_func)

    def process(self, text):
        t = text.lower().strip()

        # ── Toplantı ──────────────────────────────────────────────────────────
        if "toplantı hazırla" in t:
            topic = t.replace("toplantı hazırla","").strip()
            m = re.search(r'(\d+)\s*dakika', t)
            dur = int(m.group(1)) if m else 60
            if topic: self.meeting.prepare(topic, duration=dur); return True
        if "toplantı notu" in t:
            parts = t.replace("toplantı notu","").strip().split("|")
            if len(parts) >= 2:
                self.meeting.take_notes(parts[0].strip(), parts[1].strip()); return True
        if "toplantı özeti" in t:
            meeting_id = t.replace("toplantı özeti","").strip() or "son"
            self.meeting.summarize_notes(meeting_id); return True
        if "aksiyon maddeleri" in t:
            notes = t.replace("aksiyon maddeleri","").strip()
            if not notes:
                try: notes = pyperclip.paste()
                except: pass
            if notes: self.meeting.action_items(notes); return True

        # ── E-posta ───────────────────────────────────────────────────────────
        if "mail yaz" in t or "e-posta yaz" in t:
            content = t.replace("mail yaz","").replace("e-posta yaz","").strip()
            tone = "resmi" if "resmi" in t else "samimi" if "samimi" in t else "profesyonel"
            if content: self.email.compose(content, content, tone); return True
        if "mail cevapla" in t:
            self.msg("ANKA","Yanıtlanacak maili yapıştırın ve 'cevap talimatı [talimat]' yazın efendim.")
            return True
        if "cevap talimatı" in t:
            instruction = t.replace("cevap talimatı","").strip()
            try:
                original = pyperclip.paste()
                if original and instruction:
                    self.email.reply(original, instruction); return True
            except: pass
            return True
        if "mail şablonu" in t:
            template = t.replace("mail şablonu","").strip()
            if template: self.email.templates(template); return True
        if "maili analiz et" in t:
            try:
                email_text = pyperclip.paste()
                if email_text: self.email.analyze_email(email_text)
            except: pass
            return True

        # ── Doğum Günleri ─────────────────────────────────────────────────────
        if "doğum günü ekle" in t:
            parts = t.replace("doğum günü ekle","").strip().split(",")
            if len(parts) >= 2:
                name = parts[0].strip()
                date = parts[1].strip()
                relation = parts[2].strip() if len(parts) > 2 else "arkadaş"
                self.birthdays.add_birthday(name, date, relation); return True
        if "yaklaşan doğum günleri" in t or "doğum günleri" in t:
            m = re.search(r'(\d+)', t)
            days = int(m.group(1)) if m else 30
            self.birthdays.upcoming_birthdays(days); return True
        if "doğum günü mesajı" in t:
            name = t.replace("doğum günü mesajı","").strip()
            if name: self.birthdays.birthday_message(name); return True

        # ── Alışveriş ─────────────────────────────────────────────────────────
        if "listeye ekle" in t or "alışverişe ekle" in t:
            item = t.replace("listeye ekle","").replace("alışverişe ekle","").strip()
            priority = "yüksek" if "acil" in t or "önemli" in t else "normal"
            if item: self.shopping.add_item(item, priority=priority); return True
        if "alışveriş listesi" in t or "liste göster" in t:
            list_name = t.replace("alışveriş listesi","").replace("liste göster","").strip() or "genel"
            self.shopping.show_list(list_name); return True
        if "akıllı liste" in t:
            occasion = t.replace("akıllı liste","").strip()
            if occasion: self.shopping.smart_list(occasion); return True
        if "fiyat karşılaştır" in t:
            product = t.replace("fiyat karşılaştır","").strip()
            if product: self.shopping.price_compare(product); return True

        # ── Kişisel Asistan Pro ───────────────────────────────────────────────
        if "kişi ekle" in t or "rehbere ekle" in t:
            parts = t.replace("kişi ekle","").replace("rehbere ekle","").strip().split(",")
            if parts:
                name = parts[0].strip()
                phone = parts[1].strip() if len(parts) > 1 else ""
                email = parts[2].strip() if len(parts) > 2 else ""
                self.pa.add_contact(name, phone, email); return True
        if "kişi bul" in t or "rehberde ara" in t:
            name = t.replace("kişi bul","").replace("rehberde ara","").strip()
            if name: self.pa.find_contact(name); return True
        if "görev ekle" in t:
            task = t.replace("görev ekle","").strip()
            m = re.search(r'öncelik\s*(\d+)', t)
            priority = int(m.group(1)) if m else 5
            task = re.sub(r'öncelik\s*\d+', '', task).strip()
            if task: self.pa.add_task(task, priority=priority); return True
        if "sonraki görev" in t or "ne yapmalıyım" in t:
            self.pa.next_action(); return True
        if "hızlı not" in t or "not al" in t:
            note = t.replace("hızlı not","").replace("not al","").strip()
            if not note:
                try: note = pyperclip.paste()[:200]
                except: pass
            if note: self.pa.add_note_quick(note); return True
        if "notlarım" in t or "notları göster" in t:
            m = re.search(r'(\d+)', t)
            last = int(m.group(1)) if m else 5
            self.pa.show_notes(last); return True
        if "haftalık özet" in t or "haftayı değerlendir" in t:
            self.pa.weekly_review_pa(); return True

        return False
