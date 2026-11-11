# ── ANKA LGS YARDIMCISI MODÜLü ───────────────────────────────────────────────
import json, os, datetime, random, threading
from anka_config import BASE_DIR

LGS_FILE = os.path.join(BASE_DIR, "anka_lgs.json")
LGS_STATS_FILE = os.path.join(BASE_DIR, "anka_lgs_stats.json")

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


# ── LGS Ders ve Konuları ─────────────────────────────────────────────────────
LGS_SUBJECTS = {
    "Türkçe": [
        "Sözcükte Anlam", "Cümlede Anlam", "Paragraf", "Sözcük Türleri",
        "Cümlenin Ögeleri", "Yazım Kuralları", "Noktalama İşaretleri",
        "Ses Bilgisi", "Yapım Ekleri", "Çekim Ekleri", "Fiilimsiler",
        "Anlatım Biçimleri", "Metin Türleri"
    ],
    "Matematik": [
        "Sayılar ve İşlemler", "Faktöriyel ve Permütasyon", "Olasılık",
        "Veri Analizi", "Cebirsel İfadeler", "Denklemler", "Eşitsizlikler",
        "Üçgenler", "Dörtgenler", "Daireler", "Katı Cisimler",
        "Oran Orantı", "Yüzde Kâr Zarar", "Faiz", "Fonksiyonlar"
    ],
    "Fen Bilimleri": [
        "Mevsimler ve İklim", "DNA ve Genetik Kod", "Basınç",
        "Madde ve Özellikleri", "Kimyasal Reaksiyonlar", "Asit Baz",
        "Elektrik", "Manyetizma", "Işık", "Ses", "Kuvvet ve Hareket",
        "Enerji Dönüşümleri", "Ekosistem", "Hücre", "Besin Zinciri"
    ],
    "İnkılap Tarihi": [
        "Osmanlı'nın Yıkılışı", "Kurtuluş Savaşı", "TBMM'nin Açılması",
        "Lozan Antlaşması", "Cumhuriyet'in İlanı", "Halifeliğin Kaldırılması",
        "Atatürk İlkeleri", "Hukuk Devrimi", "Eğitim Devrimi",
        "Ekonomi Politikaları", "Dış Politika", "İkinci Dünya Savaşı"
    ],
    "İngilizce": [
        "Tenses", "Modals", "Passive Voice", "Conditionals",
        "Reported Speech", "Relative Clauses", "Vocabulary",
        "Reading Comprehension", "Phrasal Verbs", "Prepositions"
    ],
    "Din Kültürü": [
        "Kur'an-ı Kerim", "Hz. Muhammed'in Hayatı", "İbadetler",
        "Ahlak", "İslam Düşüncesinde Yorumlar", "Gençlik ve Din",
        "Güncel Dini Meseleler"
    ]
}

LGS_TIPS = {
    "Türkçe": "📖 Bol paragraf çözün. Her soruyu okurken ana fikri bulmaya çalışın.",
    "Matematik": "🔢 Formülleri ezberlemek yerine anlayın. Adım adım çözün.",
    "Fen Bilimleri": "🔬 Formülleri günlük hayatla ilişkilendirin.",
    "İnkılap Tarihi": "🏛 Olayları kronolojik sırayla öğrenin.",
    "İngilizce": "🌍 Gramer kurallarını örneklerle öğrenin.",
    "Din Kültürü": "🌙 Konuları anlayarak okuyun, ezber yapmayın."
}


# ── LGS İstatistik Yöneticisi ────────────────────────────────────────────────
class LGSStats:
    def __init__(self):
        self.data = _load(LGS_STATS_FILE, {
            "total_questions": 0,
            "correct": 0,
            "wrong": 0,
            "by_subject": {},
            "weak_topics": [],
            "study_sessions": [],
            "exam_date": None,
            "target_score": 500
        })

    def log_answer(self, subject, topic, correct):
        self.data["total_questions"] += 1
        if correct:
            self.data["correct"] += 1
        else:
            self.data["wrong"] += 1
            if topic not in self.data["weak_topics"]:
                self.data["weak_topics"].append(topic)

        if subject not in self.data["by_subject"]:
            self.data["by_subject"][subject] = {"correct": 0, "wrong": 0}
        if correct:
            self.data["by_subject"][subject]["correct"] += 1
        else:
            self.data["by_subject"][subject]["wrong"] += 1
        _save(LGS_STATS_FILE, self.data)

    def get_success_rate(self, subject=None):
        if subject and subject in self.data["by_subject"]:
            d = self.data["by_subject"][subject]
            total = d["correct"] + d["wrong"]
            return round(d["correct"]/total*100) if total > 0 else 0
        total = self.data["correct"] + self.data["wrong"]
        return round(self.data["correct"]/total*100) if total > 0 else 0

    def get_weak_subjects(self):
        weak = []
        for subj, data in self.data["by_subject"].items():
            total = data["correct"] + data["wrong"]
            if total > 0:
                rate = data["correct"]/total*100
                if rate < 60:
                    weak.append((subj, round(rate)))
        return sorted(weak, key=lambda x: x[1])

    def set_exam_date(self, date_str):
        self.data["exam_date"] = date_str
        _save(LGS_STATS_FILE, self.data)

    def days_to_exam(self):
        if not self.data.get("exam_date"):
            return None
        try:
            exam = datetime.date.fromisoformat(self.data["exam_date"])
            return (exam - datetime.date.today()).days
        except: return None

    def get_report(self):
        total = self.data["total_questions"]
        correct = self.data["correct"]
        rate = self.get_success_rate()
        days = self.days_to_exam()
        weak = self.get_weak_subjects()

        report = f"📊 LGS Performans Raporu:\n\n"
        report += f"✅ Toplam Soru: {total}\n"
        report += f"✅ Doğru: {correct} | ❌ Yanlış: {total-correct}\n"
        report += f"🎯 Başarı Oranı: %{rate}\n"
        if days is not None:
            report += f"📅 Sınava {days} gün kaldı\n"

        if self.data["by_subject"]:
            report += f"\n📚 Ders Bazlı Başarı:\n"
            for subj, d in self.data["by_subject"].items():
                t = d["correct"] + d["wrong"]
                r = round(d["correct"]/t*100) if t > 0 else 0
                emoji = "✅" if r >= 70 else "⚠️" if r >= 50 else "❌"
                report += f"{emoji} {subj}: %{r} ({t} soru)\n"

        if weak:
            report += f"\n🔴 Zayıf Konular:\n"
            report += "\n".join(f"• {s}: %{r}" for s,r in weak[:5])

        return report


# ── LGS Yardımcısı Ana Sınıf ─────────────────────────────────────────────────
class LGSAssistant:
    def __init__(self, ollama, speak_func, msg_func):
        self.ollama = ollama
        self.speak = speak_func
        self.msg = msg_func
        self.stats = LGSStats()
        self.current_question = None
        self.current_answer = None
        self.current_subject = None
        self.current_topic = None
        self.study_mode = False
        self.quiz_mode = False

    def teach_topic(self, subject, topic):
        """Konuyu anlat"""
        self.msg("ANKA", f"📚 {subject} - {topic} anlatılıyor...")
        def _teach():
            prompt = (f"LGS sınavına hazırlanan 8. sınıf öğrencisine "
                     f"'{subject}' dersinden '{topic}' konusunu anlat.\n\n"
                     f"Şu formatta anlat:\n"
                     f"1. Konunun özeti (3-4 cümle)\n"
                     f"2. Temel kavramlar (madde madde)\n"
                     f"3. Önemli formül/kural varsa yaz\n"
                     f"4. Günlük hayattan 1 örnek\n"
                     f"5. LGS'de nasıl çıkar (1-2 cümle ipucu)\n\n"
                     f"Basit ve anlaşılır Türkçe kullan.")

            reply = self.ollama.chat(prompt,
                system_override="Sen LGS uzmanı bir öğretmensin. Konuları sade, net ve öğrenci dostu anlat.")

            self.msg("ANKA", f"📖 {subject} - {topic}\n\n{reply}")
            self.speak(f"{topic} konusu hazırlandı efendim.")

            # Ders sonrası soru öner
            import time
            time.sleep(1)
            self.msg("ANKA",
                f"💡 İpucu: {LGS_TIPS.get(subject,'Bol pratik yapın.')}\n\n"
                f"📝 Şimdi soru çözmek ister misin? 'LGS soru' yaz!")
        threading.Thread(target=_teach, daemon=True).start()

    def generate_question(self, subject=None, topic=None, difficulty="orta"):
        """Soru oluştur"""
        if not subject:
            subject = random.choice(list(LGS_SUBJECTS.keys()))
        if not topic:
            topic = random.choice(LGS_SUBJECTS.get(subject, ["Genel"]))

        self.current_subject = subject
        self.current_topic = topic
        self.msg("ANKA", f"🎯 {subject} - {topic} sorusu hazırlanıyor...")

        def _gen():
            difficulty_map = {
                "kolay": "kolay, temel düzey",
                "orta": "orta zorlukta, LGS seviyesinde",
                "zor": "zor, net ayırt edici"
            }
            diff_text = difficulty_map.get(difficulty, "orta zorlukta")

            prompt = (f"LGS sınavı için '{subject}' dersinden '{topic}' konusunda "
                     f"{diff_text} 4 seçenekli (A,B,C,D) bir soru oluştur.\n\n"
                     f"Format:\n"
                     f"SORU: [soru metni]\n"
                     f"A) [seçenek]\n"
                     f"B) [seçenek]\n"
                     f"C) [seçenek]\n"
                     f"D) [seçenek]\n"
                     f"CEVAP: [doğru şık harfi]\n"
                     f"AÇIKLAMA: [kısa açıklama]\n\n"
                     f"Sadece bu formatı kullan, başka şey yazma.")

            reply = self.ollama.chat(prompt,
                system_override="LGS sınav sorusu üret. Gerçekçi ve öğretici olsun.")

            # Cevabı parse et
            lines = reply.split('\n')
            self.current_question = reply
            answer_line = next((l for l in lines if l.startswith('CEVAP:')), None)
            if answer_line:
                self.current_answer = answer_line.replace('CEVAP:','').strip().upper()

            self.msg("ANKA",
                f"❓ {subject} Sorusu ({topic}):\n\n{reply.split('CEVAP:')[0].strip()}\n\n"
                f"Cevabını yaz: A, B, C veya D")
            self.quiz_mode = True
        threading.Thread(target=_gen, daemon=True).start()

    def check_answer(self, user_answer):
        """Cevabı kontrol et"""
        if not self.quiz_mode or not self.current_answer:
            return False

        user_ans = user_answer.upper().strip()
        correct = user_ans == self.current_answer

        self.stats.log_answer(
            self.current_subject or "Genel",
            self.current_topic or "Genel",
            correct
        )

        if correct:
            r = (f"✅ DOĞRU! Tebrikler efendim!\n"
                 f"Başarı oranın: %{self.stats.get_success_rate()}")
            self.msg("ANKA", r)
            self.speak("Doğru! Tebrikler efendim.")
        else:
            # Açıklamayı bul
            explanation = ""
            if self.current_question and "AÇIKLAMA:" in self.current_question:
                explanation = self.current_question.split("AÇIKLAMA:")[-1].strip()

            r = (f"❌ YANLIŞ! Doğru cevap: {self.current_answer}\n\n"
                 f"📖 Açıklama: {explanation}\n\n"
                 f"💪 Üzülme, bir dahaki soruda daha dikkatli ol!")
            self.msg("ANKA", r)
            self.speak(f"Yanlış. Doğru cevap {self.current_answer} efendim.")

        self.quiz_mode = False
        self.current_question = None
        self.current_answer = None

        # Sonraki soru öner
        import time
        time.sleep(0.5)
        self.msg("ANKA", "➡️ Devam etmek için 'LGS soru' yaz, başka konu için 'LGS [ders]' yaz!")
        return True

    def lgs_exam_simulation(self, subject, question_count=5):
        """Mini sınav simülasyonu"""
        self.msg("ANKA",
            f"📝 {subject} Mini Sınavı Başlıyor!\n"
            f"{question_count} soru olacak. Hazır mısın?\n"
            f"İlk soru geliyor...")
        threading.Thread(
            target=lambda: self.generate_question(subject),
            daemon=True
        ).start()

    def get_study_plan(self, days_left, weak_subjects=None):
        """Çalışma programı oluştur"""
        weak = weak_subjects or [s for s,_ in self.stats.get_weak_subjects()[:3]]
        subjects = list(LGS_SUBJECTS.keys())

        prompt = (f"LGS sınavına {days_left} gün kalan bir öğrenci için "
                 f"günlük çalışma programı oluştur.\n"
                 f"Zayıf olduğu konular: {', '.join(weak) if weak else 'belirtilmedi'}\n"
                 f"Dersler: {', '.join(subjects)}\n\n"
                 f"Haftalık program yap. Her gün hangi ders, kaç saat, hangi konu.")

        def _plan():
            reply = self.ollama.chat(prompt,
                system_override="LGS uzman koçu. Gerçekçi ve uygulanabilir program yap.")
            self.msg("ANKA", f"📅 LGS Çalışma Programı ({days_left} gün):\n\n{reply}")
            self.speak("Çalışma programı hazırlandı efendim.")
        threading.Thread(target=_plan, daemon=True).start()

    def explain_wrong(self, topic):
        """Yanlış yapılan konuyu tekrar anlat"""
        self.msg("ANKA", f"🔄 {topic} konusu tekrar anlatılıyor...")
        def _explain():
            prompt = (f"LGS öğrencisi '{topic}' konusunda sürekli hata yapıyor. "
                     f"Bu konuyu özellikle hata yapılan noktalara odaklanarak anlat. "
                     f"Sık yapılan hatalar ve tuzaklar neler? Nasıl önlenir?")
            reply = self.ollama.chat(prompt,
                system_override="LGS öğretmeni. Hataları önlemeye odaklan.")
            self.msg("ANKA", f"⚠️ {topic} - Dikkat Edilecek Noktalar:\n\n{reply}")
            self.speak("Açıklama hazırlandı efendim.")
        threading.Thread(target=_explain, daemon=True).start()


# ── Komut İşleyici ────────────────────────────────────────────────────────────
class LGSCommandProcessor:
    def __init__(self, speak_func, msg_func, ollama):
        self.speak = speak_func
        self.msg = msg_func
        self.ollama = ollama
        self.lgs = LGSAssistant(ollama, speak_func, msg_func)

    def process(self, text):
        t = text.lower().strip()

        # ── Konu Anlat ────────────────────────────────────────────────────────
        if "lgs" in t and "anlat" in t:
            subject_found = None
            topic_found = None
            for subj, topics in LGS_SUBJECTS.items():
                if subj.lower() in t:
                    subject_found = subj
                    for topic in topics:
                        if topic.lower() in t:
                            topic_found = topic
                            break
                    break
            if not subject_found:
                # Hangi ders?
                r = ("📚 Hangi dersi anlatayım efendim?\n"
                     "Örnek: 'LGS matematik anlat' veya 'LGS türkçe paragraf anlat'\n\n"
                     "Dersler: " + ", ".join(LGS_SUBJECTS.keys()))
                self.msg("ANKA", r); self.speak(r)
                return True
            if not topic_found:
                topics = LGS_SUBJECTS[subject_found]
                r = (f"📚 {subject_found} konuları:\n" +
                     "\n".join(f"• {t}" for t in topics) +
                     f"\n\nHangi konuyu anlatalım? Örn: 'LGS {subject_found.lower()} {topics[0]} anlat'")
                self.msg("ANKA", r); self.speak(r)
                return True
            self.lgs.teach_topic(subject_found, topic_found)
            return True

        # ── Soru Oluştur ─────────────────────────────────────────────────────
        if "lgs soru" in t or ("lgs" in t and "soru" in t):
            subject_found = None
            difficulty = "orta"
            for subj in LGS_SUBJECTS:
                if subj.lower() in t:
                    subject_found = subj
                    break
            for diff in ["kolay","zor","orta"]:
                if diff in t:
                    difficulty = diff
                    break
            self.lgs.generate_question(subject_found, difficulty=difficulty)
            return True

        # ── Cevap Kontrol ─────────────────────────────────────────────────────
        if self.lgs.quiz_mode and t.strip() in ["a","b","c","d"]:
            self.lgs.check_answer(t.strip())
            return True

        if "cevabım" in t and self.lgs.quiz_mode:
            for opt in ["a","b","c","d"]:
                if opt in t:
                    self.lgs.check_answer(opt)
                    return True

        # ── Sınav Simülasyonu ─────────────────────────────────────────────────
        if "lgs sınav" in t or "lgs simülasyon" in t or "lgs deneme" in t:
            subject_found = None
            for subj in LGS_SUBJECTS:
                if subj.lower() in t:
                    subject_found = subj
                    break
            if subject_found:
                self.lgs.lgs_exam_simulation(subject_found)
            else:
                self.lgs.lgs_exam_simulation(random.choice(list(LGS_SUBJECTS.keys())))
            return True

        # ── Çalışma Programı ──────────────────────────────────────────────────
        if "lgs program" in t or "çalışma planı" in t or "lgs plan" in t:
            days = self.lgs.stats.days_to_exam()
            if not days:
                # Varsayılan
                days = 90
            self.lgs.get_study_plan(days)
            return True

        # ── Sınav Tarihi ──────────────────────────────────────────────────────
        if "lgs tarihi" in t or "sınav tarihi" in t or "lgs ne zaman" in t:
            import re
            date_m = re.search(r'(\d{4}-\d{2}-\d{2}|\d{1,2}[./]\d{1,2}[./]\d{4})', t)
            if date_m:
                date_str = date_m.group(1).replace('/','-').replace('.','-')
                self.lgs.stats.set_exam_date(date_str)
                days = self.lgs.stats.days_to_exam()
                r = f"✓ LGS tarihi kaydedildi! Sınava {days} gün kaldı efendim."
                self.msg("ANKA", r); self.speak(r)
            else:
                days = self.lgs.stats.days_to_exam()
                if days:
                    r = f"📅 LGS'ye {days} gün kaldı efendim!"
                else:
                    r = "LGS tarihini söyleyin efendim. Örn: 'LGS tarihi 2025-06-15'"
                self.msg("ANKA", r); self.speak(r)
            return True

        # ── İstatistik ────────────────────────────────────────────────────────
        if "lgs istatistik" in t or "lgs rapor" in t or "lgs başarı" in t:
            report = self.lgs.stats.get_report()
            self.msg("ANKA", report)
            self.speak("LGS raporun hazır efendim.")
            return True

        # ── Zayıf Konular ─────────────────────────────────────────────────────
        if "zayıf konu" in t or "hangi konular zayıf" in t:
            weak = self.lgs.stats.get_weak_subjects()
            if weak:
                r = "⚠️ Zayıf Olduğun Konular:\n"
                r += "\n".join(f"• {s}: %{rate} başarı" for s,rate in weak)
                r += "\n\nBu konuları çalışmak ister misin? 'LGS [ders] anlat' yaz!"
            else:
                r = "Henüz yeterli veri yok. Soru çöz ve istatistiğini oluştur!"
            self.msg("ANKA", r); self.speak(r)
            return True

        # ── Konu Listesi ──────────────────────────────────────────────────────
        if "lgs konular" in t or "lgs müfredat" in t:
            r = "📚 LGS Konuları:\n\n"
            for subj, topics in LGS_SUBJECTS.items():
                r += f"【{subj}】\n"
                r += "\n".join(f"• {t}" for t in topics[:5])
                r += "\n...\n\n"
            self.msg("ANKA", r)
            self.speak("LGS konu listesi hazırlandı efendim.")
            return True

        # ── Hata Analizi ──────────────────────────────────────────────────────
        if "lgs hata analiz" in t or "neden yanlış" in t:
            topic = t.replace("lgs hata analiz","").replace("neden yanlış","").strip()
            if topic:
                self.lgs.explain_wrong(topic)
            return True

        # ── Motivasyon ────────────────────────────────────────────────────────
        if "lgs motivasyon" in t or "lgs için motive et" in t:
            days = self.lgs.stats.days_to_exam()
            rate = self.lgs.stats.get_success_rate()
            def _mot():
                reply = self.ollama.chat(
                    f"LGS'ye hazırlanan bir öğrenciye motivasyon ver. "
                    f"Sınava {days or 'birkaç'} gün kaldı. Başarı oranı %{rate}. "
                    f"Güçlü ve içten konuş.",
                    system_override="Öğrenci koçu. Samimi ve güçlü motivasyon ver."
                )
                self.msg("ANKA", f"💪 {reply}")
                self.speak(reply[:300])
            threading.Thread(target=_mot, daemon=True).start()
            return True

        # ── Hızlı Başlat ──────────────────────────────────────────────────────
        if t == "lgs" or "lgs yardım" in t or "lgs ne yapabiliriz" in t:
            r = ("📚 LGS Yardımcısı Aktif!\n\n"
                 "🔹 'LGS matematik anlat' → Konu anlatımı\n"
                 "🔹 'LGS soru' → Soru çöz\n"
                 "🔹 'LGS fen soru kolay' → Kolay soru\n"
                 "🔹 'LGS sınav türkçe' → Mini sınav\n"
                 "🔹 'LGS program' → Çalışma planı\n"
                 "🔹 'LGS istatistik' → Performans raporu\n"
                 "🔹 'LGS tarihi 2025-06-15' → Sınav tarihi kaydet\n"
                 "🔹 'LGS motivasyon' → Motivasyon\n"
                 "🔹 'LGS konular' → Tüm konular\n\n"
                 "Hadi başlayalım! 🚀")
            self.msg("ANKA", r)
            self.speak("LGS yardımcısı aktif efendim. Ne yapmak istiyorsunuz?")
            return True

        return False
