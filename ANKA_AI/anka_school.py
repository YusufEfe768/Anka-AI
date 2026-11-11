# ── ANKA OKUL & ÖĞRENME MODÜLü ───────────────────────────────────────────────
import json, os, datetime, random, threading
from anka_config import BASE_DIR

SCHEDULE_FILE  = os.path.join(BASE_DIR, "anka_schedule.json")
FLASHCARD_FILE = os.path.join(BASE_DIR, "anka_flashcards.json")
HOMEWORK_FILE  = os.path.join(BASE_DIR, "anka_homework.json")
REVIEW_FILE    = os.path.join(BASE_DIR, "anka_review.json")

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

DAYS = ["Pazartesi","Salı","Çarşamba","Perşembe","Cuma","Cumartesi","Pazar"]

# ── Ders Programı ─────────────────────────────────────────────────────────────
class LessonSchedule:
    def add_lesson(self, day, time_str, subject, teacher=""):
        data = _load(SCHEDULE_FILE, {})
        if day not in data: data[day] = []
        data[day].append({"time": time_str, "subject": subject, "teacher": teacher})
        data[day].sort(key=lambda x: x["time"])
        _save(SCHEDULE_FILE, data)

    def get_today(self):
        data = _load(SCHEDULE_FILE, {})
        today = DAYS[datetime.date.today().weekday()]
        return data.get(today, [])

    def get_tomorrow(self):
        data = _load(SCHEDULE_FILE, {})
        tomorrow = DAYS[(datetime.date.today().weekday() + 1) % 7]
        return data.get(tomorrow, [])

    def get_week(self):
        return _load(SCHEDULE_FILE, {})

    def get_next_lesson(self):
        today_lessons = self.get_today()
        now = datetime.datetime.now().strftime("%H:%M")
        for lesson in today_lessons:
            if lesson["time"] > now:
                return lesson
        return None


# ── Flashcard Sistemi ─────────────────────────────────────────────────────────
class FlashcardSystem:
    def add_card(self, question, answer, subject="Genel"):
        data = _load(FLASHCARD_FILE, [])
        data.append({
            "question": question,
            "answer": answer,
            "subject": subject,
            "correct": 0,
            "wrong": 0,
            "last_reviewed": None,
            "created": datetime.datetime.now().isoformat()
        })
        _save(FLASHCARD_FILE, data)

    def get_due_cards(self, limit=5):
        """Tekrar edilmesi gereken kartları getir (spaced repetition)"""
        data = _load(FLASHCARD_FILE, [])
        today = datetime.date.today().isoformat()
        due = []
        for card in data:
            last = card.get("last_reviewed")
            if not last or last < today:
                due.append(card)
        return random.sample(due, min(limit, len(due))) if due else []

    def review_card(self, index, correct):
        data = _load(FLASHCARD_FILE, [])
        if 0 <= index < len(data):
            if correct:
                data[index]["correct"] += 1
            else:
                data[index]["wrong"] += 1
            data[index]["last_reviewed"] = datetime.date.today().isoformat()
            _save(FLASHCARD_FILE, data)

    def get_stats(self):
        data = _load(FLASHCARD_FILE, [])
        total = len(data)
        total_correct = sum(c["correct"] for c in data)
        total_wrong = sum(c["wrong"] for c in data)
        return total, total_correct, total_wrong


# ── Ödev Takibi ───────────────────────────────────────────────────────────────
class HomeworkTracker:
    def add(self, subject, description, due_date):
        data = _load(HOMEWORK_FILE, [])
        data.append({
            "subject": subject,
            "description": description,
            "due_date": due_date,
            "done": False,
            "created": datetime.datetime.now().isoformat()
        })
        _save(HOMEWORK_FILE, data)

    def get_pending(self):
        data = _load(HOMEWORK_FILE, [])
        today = datetime.date.today().isoformat()
        pending = []
        for hw in data:
            if not hw["done"]:
                days_left = (datetime.date.fromisoformat(hw["due_date"]) -
                            datetime.date.today()).days
                hw["days_left"] = days_left
                pending.append(hw)
        return sorted(pending, key=lambda x: x["days_left"])

    def complete(self, subject):
        data = _load(HOMEWORK_FILE, [])
        for hw in data:
            if subject.lower() in hw["subject"].lower() and not hw["done"]:
                hw["done"] = True
                _save(HOMEWORK_FILE, data)
                return True
        return False


# ── Konu Tekrar Sistemi ───────────────────────────────────────────────────────
class ReviewScheduler:
    def add_topic(self, subject, topic, difficulty=3):
        """difficulty: 1-5 (1=kolay, 5=zor)"""
        data = _load(REVIEW_FILE, [])
        today = datetime.date.today()
        # Spaced repetition aralıkları
        intervals = {1:[7,14,30], 2:[3,7,14], 3:[1,3,7], 4:[1,2,3], 5:[0,1,2]}
        days = intervals.get(difficulty, [1,3,7])
        review_dates = [
            (today + datetime.timedelta(days=d)).isoformat()
            for d in days
        ]
        data.append({
            "subject": subject,
            "topic": topic,
            "difficulty": difficulty,
            "review_dates": review_dates,
            "completed_reviews": [],
            "created": today.isoformat()
        })
        _save(REVIEW_FILE, data)

    def get_due_today(self):
        data = _load(REVIEW_FILE, [])
        today = datetime.date.today().isoformat()
        due = []
        for item in data:
            if today in item.get("review_dates", []) and \
               today not in item.get("completed_reviews", []):
                due.append(item)
        return due

    def mark_reviewed(self, topic):
        data = _load(REVIEW_FILE, [])
        today = datetime.date.today().isoformat()
        for item in data:
            if topic.lower() in item["topic"].lower():
                if "completed_reviews" not in item:
                    item["completed_reviews"] = []
                item["completed_reviews"].append(today)
        _save(REVIEW_FILE, data)


# ── Komut İşleyici ────────────────────────────────────────────────────────────
class SchoolCommandProcessor:
    def __init__(self, speak_func, msg_func, ollama):
        self.speak = speak_func
        self.msg = msg_func
        self.ollama = ollama
        self.schedule = LessonSchedule()
        self.flashcards = FlashcardSystem()
        self.homework = HomeworkTracker()
        self.review = ReviewScheduler()
        self._current_flashcard = None
        self._flashcard_index = None

    def process(self, text):
        t = text.lower().strip()
        import re

        # ── Ders Programı ─────────────────────────────────────────────────────
        if "ders ekle" in t or "derse ekle" in t:
            # "pazartesi 09:00 matematik ekle"
            day_found = next((d for d in DAYS if d.lower() in t), None)
            time_m = re.search(r'(\d{1,2})[:\.](\d{2})', t)
            subjects = ["matematik","fizik","kimya","biyoloji","türkçe",
                       "ingilizce","tarih","coğrafya","felsefe","din","beden"]
            subject_found = next((s for s in subjects if s in t), None)
            if day_found and time_m and subject_found:
                time_str = f"{time_m.group(1).zfill(2)}:{time_m.group(2)}"
                self.schedule.add_lesson(day_found, time_str, subject_found.capitalize())
                r = f"✓ {day_found} {time_str} - {subject_found.capitalize()} eklendi efendim."
                self.msg("ANKA",r); self.speak(r)
                return True

        if "bugünkü dersler" in t or "günün dersleri" in t:
            lessons = self.schedule.get_today()
            if not lessons:
                r = "Bugün ders programında ders yok efendim."
            else:
                today = DAYS[datetime.date.today().weekday()]
                r = f"📚 {today} Ders Programı:\n"
                r += "\n".join(f"• {l['time']} — {l['subject']}" for l in lessons)
            self.msg("ANKA",r); self.speak(r)
            return True

        if "yarınki dersler" in t or "yarın ne var" in t:
            lessons = self.schedule.get_tomorrow()
            tomorrow = DAYS[(datetime.date.today().weekday()+1)%7]
            if not lessons:
                r = f"{tomorrow} günü ders yok efendim."
            else:
                r = f"📚 {tomorrow} Ders Programı:\n"
                r += "\n".join(f"• {l['time']} — {l['subject']}" for l in lessons)
            self.msg("ANKA",r); self.speak(r)
            return True

        if "sıradaki ders" in t or "sonraki ders" in t:
            lesson = self.schedule.get_next_lesson()
            if lesson:
                r = f"📚 Sıradaki ders: {lesson['time']} — {lesson['subject']}"
            else:
                r = "Bugün başka ders yok efendim."
            self.msg("ANKA",r); self.speak(r)
            return True

        # ── Flashcard ─────────────────────────────────────────────────────────
        if "kart ekle" in t or "flashcard ekle" in t:
            # "matematik kart ekle: türev nedir? | türevin tanımı..."
            if ":" in text and "|" in text:
                parts = text.split(":",1)[1].split("|")
                if len(parts) >= 2:
                    q = parts[0].strip(); a = parts[1].strip()
                    subjects = ["matematik","fizik","kimya","biyoloji","ingilizce"]
                    subj = next((s for s in subjects if s in t), "Genel")
                    self.flashcards.add_card(q, a, subj.capitalize())
                    r = f"✓ Flashcard eklendi: '{q[:30]}...'"
                    self.msg("ANKA",r); self.speak(r)
                    return True

        if "flashcard çalış" in t or "kart çalış" in t or "kart tekrar" in t:
            cards = self.flashcards.get_due_cards(1)
            if not cards:
                r = "Tekrar edilecek kart yok efendim. Yeni kartlar ekleyin."
            else:
                card = cards[0]
                self._current_flashcard = card
                self._flashcard_index = 0
                r = f"🃏 Soru ({card['subject']}):\n{card['question']}\n\n'cevap' yazınca göstereyim."
            self.msg("ANKA",r); self.speak(r)
            return True

        if "cevap" in t and self._current_flashcard:
            card = self._current_flashcard
            r = f"✅ Cevap: {card['answer']}\n\nDoğru muydu? (evet/hayır)"
            self.msg("ANKA",r); self.speak(r)
            return True

        if self._current_flashcard and ("evet" in t or "hayır" in t or "hayir" in t):
            correct = "evet" in t
            self.flashcards.review_card(self._flashcard_index or 0, correct)
            r = "✓ Kaydedildi! " + ("Harika efendim! 🎉" if correct else "Bir dahaki sefere daha iyi olacak efendim. 💪")
            self._current_flashcard = None
            self.msg("ANKA",r); self.speak(r)
            # Sonraki kart
            cards = self.flashcards.get_due_cards(1)
            if cards:
                card = cards[0]
                self._current_flashcard = card
                r2 = f"🃏 Sonraki soru:\n{card['question']}"
                self.msg("ANKA",r2); self.speak(r2)
            return True

        if "kart istatistik" in t or "flashcard istatistik" in t:
            total, correct, wrong = self.flashcards.get_stats()
            rate = int(correct/(correct+wrong)*100) if (correct+wrong)>0 else 0
            r = (f"🃏 Flashcard İstatistikleri:\n"
                 f"• Toplam: {total} kart\n"
                 f"• Doğru: {correct}\n"
                 f"• Yanlış: {wrong}\n"
                 f"• Başarı: %{rate}")
            self.msg("ANKA",r); self.speak(r)
            return True

        # ── Ödev ─────────────────────────────────────────────────────────────
        if "ödev ekle" in t:
            months = {"ocak":"01","şubat":"02","mart":"03","nisan":"04",
                     "mayıs":"05","haziran":"06","temmuz":"07","ağustos":"08",
                     "eylül":"09","ekim":"10","kasım":"11","aralık":"12"}
            month_found = next((m for m in months if m in t), None)
            day_m = re.search(r'(\d{1,2})', t)
            subjects = ["matematik","fizik","kimya","biyoloji","türkçe",
                       "ingilizce","tarih","coğrafya"]
            subject_found = next((s for s in subjects if s in t), "Genel")
            if month_found and day_m:
                year = datetime.date.today().year
                due = f"{year}-{months[month_found]}-{day_m.group(1).zfill(2)}"
                desc = t.replace(subject_found,"").replace("ödev ekle","").strip()
                self.homework.add(subject_found.capitalize(), desc, due)
                days_left = (datetime.date.fromisoformat(due)-datetime.date.today()).days
                r = f"✓ {subject_found.capitalize()} ödevi eklendi. {days_left} gün kaldı efendim."
                self.msg("ANKA",r); self.speak(r)
                return True

        if "ödevlerim" in t or "bekleyen ödev" in t:
            pending = self.homework.get_pending()
            if not pending:
                r = "Bekleyen ödev yok efendim."
            else:
                r = "📝 Bekleyen Ödevler:\n"
                for hw in pending[:5]:
                    emoji = "🚨" if hw["days_left"] <= 1 else "⚠️" if hw["days_left"] <= 3 else "📌"
                    r += f"{emoji} {hw['subject']}: {hw['days_left']} gün kaldı\n"
            self.msg("ANKA",r); self.speak(r)
            return True

        if "ödevi tamamla" in t or "ödev bitti" in t:
            subject = t.replace("ödevi tamamla","").replace("ödev bitti","").strip()
            if self.homework.complete(subject):
                r = f"✓ {subject.capitalize()} ödevi tamamlandı efendim! 🎉"
            else:
                r = "Ödev bulunamadı efendim."
            self.msg("ANKA",r); self.speak(r)
            return True

        # ── Konu Tekrar ───────────────────────────────────────────────────────
        if "tekrar hatırlat" in t or "konu ekle tekrar" in t:
            r = "Hangi konuyu tekrar etmemi istersiniz? Format: '[ders] [konu] [zorluk 1-5]'"
            self.msg("ANKA",r); self.speak(r)
            return True

        if "bugün tekrar" in t or "tekrar listesi" in t:
            due = self.review.get_due_today()
            if not due:
                r = "Bugün tekrar edilecek konu yok efendim."
            else:
                r = "📚 Bugün Tekrar Edilecekler:\n"
                r += "\n".join(f"• {i['subject']}: {i['topic']}" for i in due)
            self.msg("ANKA",r); self.speak(r)
            return True

        # ── AI Destekli Öğrenme ───────────────────────────────────────────────
        if "bana anlat" in t or "açıkla" in t:
            topic = t.replace("bana anlat","").replace("açıkla","").strip()
            if topic:
                threading.Thread(target=lambda: self._explain(topic), daemon=True).start()
            return True

        if "soru üret" in t or "test sorusu" in t:
            topic = t.replace("soru üret","").replace("test sorusu","").strip()
            if topic:
                threading.Thread(target=lambda: self._generate_questions(topic), daemon=True).start()
            return True

        if "özet çıkar" in t or "konuyu özetle" in t:
            topic = t.replace("özet çıkar","").replace("konuyu özetle","").strip()
            if topic:
                threading.Thread(target=lambda: self._summarize_topic(topic), daemon=True).start()
            return True

        return False

    def _explain(self, topic):
        reply = self.ollama.chat(
            f"'{topic}' konusunu bana basit ve anlaşılır şekilde açıkla. "
            f"Örnekler ver. Sanki lise öğrencisine anlatıyormuş gibi.",
            system_override="Sen bir öğretmensin. Konuyu adım adım, anlaşılır anlat."
        )
        self.msg("ANKA", f"📚 {topic.capitalize()}:\n\n{reply}")
        self.speak(reply[:300])

    def _generate_questions(self, topic):
        reply = self.ollama.chat(
            f"'{topic}' konusundan 3 test sorusu oluştur. "
            f"Her sorunun 4 şıkkı olsun (A,B,C,D). Cevapları da yaz.",
            system_override="Sen bir sınav hazırlayan öğretmensin."
        )
        self.msg("ANKA", f"📝 Test Soruları - {topic}:\n\n{reply}")
        self.speak("Test soruları hazırlandı efendim.")

    def _summarize_topic(self, topic):
        reply = self.ollama.chat(
            f"'{topic}' konusunu madde madde özetle. "
            f"En önemli 5 noktayı vurgula.",
            system_override="Sen bir ders notu hazırlıyorsun. Kısa ve öz yaz."
        )
        self.msg("ANKA", f"📋 {topic} Özeti:\n\n{reply}")
        self.speak(reply[:300])
