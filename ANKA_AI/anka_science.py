# ── ANKA BİLİM & ARAŞTIRMA MODÜLü ───────────────────────────────────────────
import json, os, threading, datetime, math, random, webbrowser
import requests, re
from anka_config import BASE_DIR

class ScienceAssistant:
    def __init__(self, ollama, speak_func, msg_func):
        self.ollama = ollama
        self.speak = speak_func
        self.msg = msg_func

    def explain_concept(self, concept, level="lise"):
        def _e():
            r = self.ollama.chat(
                f"'{concept}' kavramını {level} seviyesinde açıkla. Örnekler ver.",
                system_override="Bilim insanı. Anlaşılır açıkla.")
            self.msg("ANKA", f"🔬 {concept}:\n{r}")
            self.speak(r[:300])
        threading.Thread(target=_e, daemon=True).start()

    def scientific_facts(self, topic, count=5):
        def _f():
            r = self.ollama.chat(
                f"'{topic}' hakkında {count} ilginç bilimsel gerçek.",
                system_override="Bilim insanı. Doğrulanmış gerçekler ver.")
            self.msg("ANKA", f"🧬 {topic} Gerçekleri:\n{r}")
        threading.Thread(target=_f, daemon=True).start()

    def research_summary(self, topic):
        def _r():
            r = self.ollama.chat(
                f"'{topic}' hakkında güncel araştırmaları özetle. Önemli bulgular.",
                system_override="Araştırmacı. Bilimsel özet yap.")
            self.msg("ANKA", f"📊 Araştırma Özeti - {topic}:\n{r}")
            webbrowser.open(f"https://scholar.google.com/scholar?q={topic}")
        threading.Thread(target=_r, daemon=True).start()

    def hypothesis(self, observation):
        def _h():
            r = self.ollama.chat(
                f"Bu gözlem için bilimsel hipotez oluştur: '{observation}'",
                system_override="Bilim insanı. Hipotez ve test yöntemi öner.")
            self.msg("ANKA", f"🔭 Hipotez:\n{r}")
        threading.Thread(target=_h, daemon=True).start()

    def math_formula(self, topic):
        def _m():
            r = self.ollama.chat(
                f"'{topic}' için matematiksel formüller ve açıklamaları.",
                system_override="Matematik profesörü. Formüller ve kullanımları.")
            self.msg("ANKA", f"📐 Formüller - {topic}:\n{r}")
        threading.Thread(target=_m, daemon=True).start()

    def space_fact(self):
        def _s():
            r = self.ollama.chat(
                "Uzay hakkında ilginç ve az bilinen bir gerçek söyle.",
                system_override="Astrofizikçi. Etkileyici uzay gerçeği ver.")
            self.msg("ANKA", f"🌌 Uzay Gerçeği:\n{r}")
            self.speak(r[:200])
        threading.Thread(target=_s, daemon=True).start()

    def periodic_table(self, element):
        def _p():
            r = self.ollama.chat(
                f"'{element}' elementi hakkında: sembol, atom numarası, özellikler, kullanım.",
                system_override="Kimyacı. Element bilgisi ver.")
            self.msg("ANKA", f"⚗️ {element}:\n{r}")
        threading.Thread(target=_p, daemon=True).start()

    def biology_fact(self, topic):
        def _b():
            r = self.ollama.chat(
                f"'{topic}' hakkında biyolojik gerçekler ve mekanizmalar.",
                system_override="Biyolog. Bilimsel açıklama yap.")
            self.msg("ANKA", f"🧬 {topic}:\n{r}")
        threading.Thread(target=_b, daemon=True).start()

    def climate_info(self):
        def _c():
            r = self.ollama.chat(
                "İklim değişikliği hakkında güncel durum ve çözüm önerileri.",
                system_override="İklim bilimcisi. Güncel bilgi ver.")
            self.msg("ANKA", f"🌍 İklim Değişikliği:\n{r}")
        threading.Thread(target=_c, daemon=True).start()

    def future_tech(self, years=10):
        def _f():
            r = self.ollama.chat(
                f"Önümüzdeki {years} yılda beklenen teknolojik gelişmeler neler?",
                system_override="Fütürist. Bilimsel temelli tahmin yap.")
            self.msg("ANKA", f"🚀 {years} Yıl Sonra:\n{r}")
        threading.Thread(target=_f, daemon=True).start()

class ScienceCommandProcessor:
    def __init__(self, speak_func, msg_func, ollama):
        self.speak = speak_func
        self.msg = msg_func
        self.ollama = ollama
        self.science = ScienceAssistant(ollama, speak_func, msg_func)

    def process(self, text):
        t = text.lower().strip()

        if "kavramı açıkla" in t or "ne demek" in t and "bilim" in t:
            concept = t.replace("kavramı açıkla","").replace("ne demek","").strip()
            level = "lise" if "lise" in t else "üniversite" if "üniversite" in t else "lise"
            self.science.explain_concept(concept, level)
            return True

        if "bilimsel gerçek" in t:
            topic = t.replace("bilimsel gerçek","").strip()
            self.science.scientific_facts(topic or "evren")
            return True

        if "araştırma özeti" in t:
            topic = t.replace("araştırma özeti","").strip()
            self.science.research_summary(topic)
            return True

        if "hipotez" in t:
            obs = t.replace("hipotez kur","").replace("hipotez","").strip()
            self.science.hypothesis(obs)
            return True

        if "formüller" in t and "göster" in t:
            topic = t.replace("formüller göster","").strip()
            self.science.math_formula(topic)
            return True

        if "uzay gerçeği" in t or "uzay bilgisi" in t:
            self.science.space_fact()
            return True

        if "element bilgisi" in t or "periyodik" in t:
            element = t.replace("element bilgisi","").replace("periyodik tablo","").strip()
            self.science.periodic_table(element or "karbon")
            return True

        if "biyoloji" in t and "anlat" in t:
            topic = t.replace("biyoloji anlat","").strip()
            self.science.biology_fact(topic)
            return True

        if "iklim" in t and ("değişikliği" in t or "bilgi" in t):
            self.science.climate_info()
            return True

        if "gelecek teknoloji" in t or "teknoloji geleceği" in t:
            m = re.search(r'(\d+)', t)
            years = int(m.group(1)) if m else 10
            self.science.future_tech(years)
            return True

        if "bilim tarihi" in t:
            topic = t.replace("bilim tarihi","").strip()
            def _hist():
                r = self.ollama.chat(
                    f"'{topic}' bilim tarihindeki önemi ve gelişimi.",
                    system_override="Bilim tarihçisi. Kronolojik anlat.")
                self.msg("ANKA", f"📚 Bilim Tarihi - {topic}:\n{r}")
            threading.Thread(target=_hist, daemon=True).start()
            return True

        return False
