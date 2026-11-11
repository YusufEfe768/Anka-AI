# ── ANKA FİNANS 2 MODÜLü ─────────────────────────────────────────────────────
import json, os, threading, datetime, webbrowser
import requests, re, random
from anka_config import BASE_DIR

FINANCE2_FILE = os.path.join(BASE_DIR, "anka_finance2.json")

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

class AdvancedFinance2:
    def __init__(self, ollama, speak_func, msg_func):
        self.ollama = ollama
        self.speak = speak_func
        self.msg = msg_func
        self.data = _load(FINANCE2_FILE, {"expenses":[], "income":[], "budgets":{}})

    def add_expense(self, amount, category, note=""):
        self.data["expenses"].append({
            "amount": amount, "category": category,
            "note": note, "date": datetime.date.today().isoformat()
        })
        _save(FINANCE2_FILE, self.data)

    def monthly_summary(self):
        today = datetime.date.today()
        month = today.strftime("%Y-%m")
        expenses = [e for e in self.data["expenses"] if e["date"].startswith(month)]
        total = sum(e["amount"] for e in expenses)
        by_cat = {}
        for e in expenses:
            by_cat[e["category"]] = by_cat.get(e["category"], 0) + e["amount"]
        r = f"💰 {today.strftime('%B %Y')} Harcama Özeti:\n"
        r += f"• Toplam: {total:,.0f}₺\n\n"
        for cat, amt in sorted(by_cat.items(), key=lambda x: -x[1]):
            pct = amt/total*100 if total > 0 else 0
            r += f"• {cat}: {amt:,.0f}₺ (%{pct:.0f})\n"
        return r

    def tax_calculator(self, annual_income):
        brackets = [(32000,0.15),(70000,0.20),(250000,0.27),(880000,0.35),(float('inf'),0.40)]
        tax = 0; prev = 0
        for limit, rate in brackets:
            if annual_income <= prev: break
            taxable = min(annual_income, limit) - prev
            tax += taxable * rate
            prev = limit
        net = annual_income - tax
        r = (f"📊 Vergi Hesaplama ({annual_income:,.0f}₺):\n"
             f"• Vergi: {tax:,.0f}₺\n"
             f"• Net Gelir: {net:,.0f}₺\n"
             f"• Efektif Oran: %{tax/annual_income*100:.1f}")
        return r

    def compound_interest(self, principal, rate, years, monthly=False):
        if monthly:
            n = 12; amount = principal * (1 + rate/100/n)**(n*years)
        else:
            amount = principal * (1 + rate/100)**years
        interest = amount - principal
        r = (f"📈 Bileşik Faiz:\n"
             f"• Anapara: {principal:,.0f}₺\n"
             f"• Süre: {years} yıl @ %{rate}\n"
             f"• Toplam: {amount:,.0f}₺\n"
             f"• Kazanç: {interest:,.0f}₺")
        return r

    def emergency_fund(self, monthly_expenses):
        fund_3 = monthly_expenses * 3
        fund_6 = monthly_expenses * 6
        r = (f"🛡️ Acil Fon Hesabı:\n"
             f"• Aylık Gider: {monthly_expenses:,.0f}₺\n"
             f"• 3 Aylık Fon: {fund_3:,.0f}₺\n"
             f"• 6 Aylık Fon (Önerilen): {fund_6:,.0f}₺")
        return r

    def debt_payoff(self, debt, rate, monthly_payment):
        months = 0; balance = debt
        total_interest = 0
        while balance > 0 and months < 600:
            interest = balance * rate/100/12
            total_interest += interest
            balance = balance + interest - monthly_payment
            months += 1
            if balance < 0: balance = 0
        r = (f"💳 Borç Ödeme Planı:\n"
             f"• Borç: {debt:,.0f}₺ @ %{rate}\n"
             f"• Aylık Ödeme: {monthly_payment:,.0f}₺\n"
             f"• Süre: {months} ay ({months//12} yıl {months%12} ay)\n"
             f"• Toplam Faiz: {total_interest:,.0f}₺")
        return r

    def financial_advice(self, situation):
        def _a():
            r = self.ollama.chat(
                f"Finansal durum: {situation}. Türk ekonomisi bağlamında tavsiye ver.",
                system_override="Finansal danışman. Pratik Türkiye'ye uygun tavsiye ver.")
            self.msg("ANKA", f"💡 Finansal Tavsiye:\n{r}")
        threading.Thread(target=_a, daemon=True).start()

    def get_gold_silver(self):
        try:
            r = requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=5)
            rates = r.json()["rates"]
            usd_try = rates.get("TRY", 32)
            gold_usd = 2300
            silver_usd = 27
            gold_try = (gold_usd/31.1035) * usd_try
            silver_try = (silver_usd/31.1035) * usd_try
            return {
                "gold_gram": round(gold_try, 2),
                "silver_gram": round(silver_try, 2),
                "usd_try": round(usd_try, 2)
            }
        except:
            return None

class Finance2CommandProcessor:
    def __init__(self, speak_func, msg_func, ollama):
        self.speak = speak_func
        self.msg = msg_func
        self.ollama = ollama
        self.finance = AdvancedFinance2(ollama, speak_func, msg_func)

    def process(self, text):
        t = text.lower().strip()

        if "harcama ekle" in t:
            nums = re.findall(r'\d+(?:\.\d+)?', t)
            if nums:
                amount = float(nums[0])
                cats = ["market","yemek","ulaşım","eğlence","fatura","sağlık","kıyafet","eğitim"]
                cat = next((c for c in cats if c in t), "diğer")
                self.finance.add_expense(amount, cat)
                r = f"✓ {amount:,.0f}₺ {cat} harcaması eklendi efendim."
                self.msg("ANKA", r); self.speak(r)
            return True

        if "aylık harcama" in t or "harcama özeti" in t:
            r = self.finance.monthly_summary()
            self.msg("ANKA", r); self.speak("Aylık harcama özeti hazır efendim.")
            return True

        if "vergi hesapla" in t:
            nums = re.findall(r'\d+(?:\.\d+)?', t)
            if nums:
                r = self.finance.tax_calculator(float(nums[0]))
                self.msg("ANKA", r); self.speak(r)
            return True

        if "bileşik faiz" in t:
            nums = re.findall(r'\d+(?:\.\d+)?', t)
            if len(nums) >= 3:
                r = self.finance.compound_interest(float(nums[0]), float(nums[1]), int(nums[2]))
                self.msg("ANKA", r); self.speak(r)
            return True

        if "acil fon" in t:
            nums = re.findall(r'\d+(?:\.\d+)?', t)
            if nums:
                r = self.finance.emergency_fund(float(nums[0]))
                self.msg("ANKA", r); self.speak(r)
            return True

        if "borç ödeme" in t:
            nums = re.findall(r'\d+(?:\.\d+)?', t)
            if len(nums) >= 3:
                r = self.finance.debt_payoff(float(nums[0]), float(nums[1]), float(nums[2]))
                self.msg("ANKA", r); self.speak(r)
            return True

        if "finansal tavsiye" in t:
            situation = t.replace("finansal tavsiye","").strip()
            self.finance.financial_advice(situation or "genel")
            return True

        if "altın gümüş" in t or "altın fiyat" in t:
            def _g():
                data = self.finance.get_gold_silver()
                if data:
                    r = (f"💰 Değerli Metaller:\n"
                         f"• Gram Altın: {data['gold_gram']:,.2f}₺\n"
                         f"• Gram Gümüş: {data['silver_gram']:,.2f}₺\n"
                         f"• Dolar: {data['usd_try']:.2f}₺")
                    self.msg("ANKA", r); self.speak(r)
                else:
                    self.msg("ANKA", "Fiyat alınamadı efendim.")
            threading.Thread(target=_g, daemon=True).start()
            return True

        if "enflasyon etkisi" in t:
            nums = re.findall(r'\d+(?:\.\d+)?', t)
            if len(nums) >= 2:
                amount, years = float(nums[0]), int(nums[1])
                rate = float(nums[2]) if len(nums) > 2 else 60
                future = amount * (1 + rate/100)**years
                lost = future - amount
                r = (f"📉 Enflasyon Etkisi:\n"
                     f"• Bugünkü {amount:,.0f}₺\n"
                     f"• {years} yıl sonra (@ %{rate}): {future:,.0f}₺ değerinde olması lazım\n"
                     f"• Satın alma gücü kaybı: {lost:,.0f}₺")
                self.msg("ANKA", r); self.speak(r)
            return True

        return False
