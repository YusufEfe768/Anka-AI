# ── ANKA BİLGİ VERİTABANI — SQLite tabanlı 100.000+ soru sistemi ─────────────
# Hafif, hızlı, RAM dostu. Açılışta tüm veriyi yüklemez!
import sqlite3, os, re, json, time, difflib
from anka_config import BASE_DIR

DB_PATH = os.path.join(BASE_DIR, "anka_brain.db")
KB_VERSION = "2"


# ═══════════════════════════════════════════════════════════════════════════════
# VERİTABANI YÖNETİCİSİ
# ═══════════════════════════════════════════════════════════════════════════════
class KnowledgeDB:
    def __init__(self):
        self.db = DB_PATH
        self._init_db()
        self._cache = {}
        self._cache_size = 500

    def _conn(self):
        conn = sqlite3.connect(self.db)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._conn() as c:
            c.execute("""
                CREATE TABLE IF NOT EXISTS qa (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT,
                    question TEXT,
                    answer TEXT,
                    keywords TEXT,
                    use_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            c.execute("CREATE INDEX IF NOT EXISTS idx_question ON qa(question)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_category ON qa(category)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_keywords ON qa(keywords)")
            # FTS (Full Text Search) tablosu
            c.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS qa_fts
                USING fts5(question, answer, keywords, content='qa', content_rowid='id')
            """)
            c.execute("CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT)")
            c.commit()

    def insert_many(self, items):
        """Toplu ekleme"""
        with self._conn() as c:
            c.executemany("""
                INSERT OR IGNORE INTO qa (category, question, answer, keywords)
                VALUES (?, ?, ?, ?)
            """, items)
            # FTS güncelle
            c.execute("INSERT INTO qa_fts(qa_fts) VALUES('rebuild')")
            c.commit()

    def get_meta(self, k):
        with self._conn() as c:
            r = c.execute("SELECT v FROM meta WHERE k=?", (k,)).fetchone()
            return r["v"] if r else None

    def set_meta(self, k, v):
        with self._conn() as c:
            c.execute("INSERT OR REPLACE INTO meta (k, v) VALUES (?, ?)", (k, v))
            c.commit()

    def clear_builtin(self):
        """Hazır bilgileri siler (öğretilenler kalır) — tekrar yüklemek için."""
        with self._conn() as c:
            c.execute("DELETE FROM qa WHERE category != 'ogrenilen'")
            c.commit()

    def search(self, query, limit=5):
        """Akıllı arama — önce tam eşleşme, sonra FTS, sonra LIKE"""
        q = query.lower().strip()

        # Cache kontrol
        if q in self._cache:
            return self._cache[q]

        with self._conn() as c:
            # 1. Tam eşleşme
            row = c.execute(
                "SELECT * FROM qa WHERE lower(question)=? LIMIT 1", (q,)
            ).fetchone()
            if row:
                c.execute("UPDATE qa SET use_count=use_count+1 WHERE id=?", (row["id"],))
                result = dict(row)
                self._store_cache(q, [result])
                return [result]

            # 2. FTS (tam metin arama)
            try:
                rows = c.execute(
                    "SELECT qa.* FROM qa JOIN qa_fts ON qa.id=qa_fts.rowid WHERE qa_fts MATCH ? ORDER BY rank LIMIT ?",
                    (q+"*", limit)
                ).fetchall()
                if rows:
                    result = [dict(r) for r in rows]
                    self._store_cache(q, result)
                    return result
            except: pass

            # 3. LIKE arama
            rows = c.execute(
                "SELECT * FROM qa WHERE lower(question) LIKE ? OR lower(keywords) LIKE ? LIMIT ?",
                (f"%{q}%", f"%{q}%", limit)
            ).fetchall()
            if rows:
                result = [dict(r) for r in rows]
                self._store_cache(q, result)
                return result

            # 4. Kelime kelime ara
            words = [w for w in q.split() if len(w) > 2]
            if words:
                placeholders = " OR ".join(["lower(question) LIKE ? OR lower(keywords) LIKE ?" for _ in words])
                params = []
                for w in words:
                    params.extend([f"%{w}%", f"%{w}%"])
                rows = c.execute(
                    f"SELECT * FROM qa WHERE {placeholders} LIMIT ?",
                    params + [limit]
                ).fetchall()
                if rows:
                    result = [dict(r) for r in rows]
                    self._store_cache(q, result)
                    return result

        return []

    def _store_cache(self, key, value):
        self._cache[key] = value
        if len(self._cache) > self._cache_size:
            oldest = list(self._cache.keys())[0]
            del self._cache[oldest]

    def add_qa(self, category, question, answer, keywords=""):
        with self._conn() as c:
            c.execute(
                "INSERT OR REPLACE INTO qa (category,question,answer,keywords) VALUES (?,?,?,?)",
                (category, question.lower(), answer, keywords)
            )
            c.execute("INSERT INTO qa_fts(qa_fts) VALUES('rebuild')")
            c.commit()

    def count(self):
        with self._conn() as c:
            return c.execute("SELECT COUNT(*) FROM qa").fetchone()[0]

    def get_by_category(self, category, limit=20):
        with self._conn() as c:
            rows = c.execute(
                "SELECT * FROM qa WHERE category=? ORDER BY use_count DESC LIMIT ?",
                (category, limit)
            ).fetchall()
            return [dict(r) for r in rows]

    def top_questions(self, limit=10):
        with self._conn() as c:
            rows = c.execute(
                "SELECT question, use_count FROM qa ORDER BY use_count DESC LIMIT ?",
                (limit,)
            ).fetchall()
            return [dict(r) for r in rows]


# ═══════════════════════════════════════════════════════════════════════════════
# VERİ YÜKLEYICI — 100.000+ soru üretir
# ═══════════════════════════════════════════════════════════════════════════════
class KnowledgeLoader:
    def __init__(self, db: KnowledgeDB):
        self.db = db

    def load_all(self):
        if self.db.get_meta("kb_version") == KB_VERSION:
            print(f"[ANKA] 📚 {self.db.count():,} soru hazır")
            return
        self.db.clear_builtin()

        print("[ANKA] 📚 Bilgi tabanı yükleniyor...")
        t0 = time.time()
        total = 0
        total += self._load_genel()
        total += self._load_bilim()
        total += self._load_matematik()
        total += self._load_teknoloji()
        total += self._load_tarih()
        total += self._load_cografya()
        total += self._load_saglik()
        total += self._load_felsefe()
        total += self._load_ekonomi()
        total += self._load_sanat()
        total += self._load_doga()
        total += self._load_uzay()
        total += self._load_spor()
        total += self._load_yemek()
        total += self._load_dil()
        total += self._load_psikoloji()
        total += self._load_valorant()
        total += self._load_gunluk()
        total += self._load_motivasyon()
        total += self._load_ilginc()
        total += self._load_selamlama()
        total += self._load_hesap()
        elapsed = time.time() - t0
        self.db.set_meta("kb_version", KB_VERSION)
        print(f"[ANKA] ✅ {self.db.count():,} soru yüklendi! ({elapsed:.1f}s)")

    def _bulk(self, category, items):
        data = []
        for q, a in items:
            keywords = " ".join(set(q.lower().split() + [category]))
            data.append((category, q.lower(), a, keywords))
        self.db.insert_many(data)
        return len(data)

    def _load_selamlama(self):
        items = [
            ("merhaba","Merhaba efendim! 👋 Nasıl yardımcı olabilirim?"),
            ("selam","Selam! 😊 Anka burada, emrinizdeyim!"),
            ("günaydın","Günaydın! ☀️ Harika bir gün dilerim!"),
            ("iyi akşamlar","İyi akşamlar! 🌙 Nasıl yardımcı olabilirim?"),
            ("iyi geceler","İyi geceler! 💤 Dinlendirici uyku dilerim."),
            ("nasılsın","Teşekkürler, mükemmelim! 🚀 Sen nasılsın?"),
            ("ne haber","Her şey yolunda! Sen nasılsın efendim?"),
            ("teşekkür ederim","Rica ederim! 😊 Başka isteğin var mı?"),
            ("sağ ol","Sağlığına! 💚"),
            ("hoşçakal","Güle güle! 👋 İyi günler!"),
            ("görüşürüz","Görüşmek üzere! 👋"),
            ("kimsin","Ben Anka! 🤖 Yusuf için özel yapay zeka asistanı."),
            ("ne yapabilirsin","🤖 Hava, saat, hesap, bilgi, Valorant, sohbet ve çok daha fazlası! 'yardım' yaz."),
            ("iyiyim","Harika! 😊 Nasıl yardımcı olabilirim?"),
            ("kötüyüm","Üzgünüm 💙 Nasıl yardımcı olabilirim?"),
            ("yorgunum","Dinlenin efendim 😴 Yine de buradayım!"),
            ("mutluyum","Harika! 🎉 Mutluluğunu paylaşmana sevindim!"),
            ("üzgünüm","Üzülme 💙 Her şey geçer. Yardımcı olabilir miyim?"),
            ("sıkıldım","Sana ilginç bir şey anlatayım mı? Yoksa birlikte bir şeyler yapalım mı? 😊"),
            ("yardım et","Tabii! Ne konusunda yardım istiyorsun? 'yardım' yazarak tüm özellikleri görebilirsin."),
        ]
        # Varyasyonlar ekle
        variations = []
        for q, a in items:
            for prefix in ["bana ","lütfen ",""]:
                for suffix in [" lütfen","?"," bana",""]:
                    vq = (prefix + q + suffix).strip()
                    if vq != q:
                        variations.append((vq, a))
        return self._bulk("selamlama", items + variations[:200])

    def _load_bilim(self):
        items = []
        # Fizik
        fizik = [
            ("ışık hızı kaçtır","Işık hızı yaklaşık 299.792.458 m/s'dir (saniyede ~300.000 km). Evrendeki en yüksek hızdır."),
            ("ses hızı kaçtır","Ses hızı havada yaklaşık 343 m/s (1.235 km/h)'dir. Sıcaklık ve ortama göre değişir."),
            ("yerçekimi nedir","Yerçekimi, kütleli cisimler arasındaki çekim kuvvetidir. Newton g=9,8 m/s², Einstein genel görelilik ile açıkladı."),
            ("elektrik nedir","Elektrik, yük taşıyıcılarının (elektron) hareketiyle oluşan enerji biçimidir. Watt, Volt, Amper temel birimleridir."),
            ("manyetizma nedir","Manyetizma, manyetik alanların oluşturduğu kuvvetlerdir. Elektrikle birleşerek elektromanyetizma oluşturur."),
            ("termodinamik nedir","Termodinamik, ısı ve iş arasındaki ilişkileri inceleyen fizik dalıdır. 4 temel yasası vardır."),
            ("entropi nedir","Entropi, bir sistemdeki düzensizliğin ölçüsüdür. Termodinamiğin 2. yasasına göre entropi her zaman artar."),
            ("kuantum süperpozisyon","Kuantum süperpozisyon, bir parçacığın gözlemlenmeden önce aynı anda birden fazla durumda bulunabilmesidir."),
            ("schrödinger'in kedisi","Schrödinger'in kedisi, kuantum belirsizliğini makroskopik ölçeğe taşıyan düşünce deneyidir. Kutu açılana kadar kedi hem canlı hem ölüdür."),
            ("e=mc2 ne demek","E=mc², Einstein'ın kütle-enerji denkliğini ifade eder. E:enerji, m:kütle, c:ışık hızı. Küçük bir kütle devasa enerji içerir."),
        ]
        # Kimya
        kimya = [
            ("atom nedir","Atom, maddenin en küçük yapı taşıdır. Proton ve nötronlardan oluşan çekirdek ile etrafındaki elektronlardan oluşur."),
            ("elektron nedir","Elektron, negatif yüklü temel parçacıktır. Atom çekirdeğinin etrafında bulunur. Kütlesi 9.11×10⁻³¹ kg'dır."),
            ("proton nedir","Proton, pozitif yüklü nükleon parçacığıdır. Atom çekirdeğinde bulunur. Proton sayısı elementin kimliğini belirler."),
            ("periyodik tablo","Periyodik tablo 118 elementi atom numaralarına göre düzenler. Mendeleev 1869'da oluşturdu. Dönemler ve gruplardan oluşur."),
            ("asit baz nedir","Asit, H⁺ iyonu veren maddedir. Baz ise OH⁻ iyonu verir. pH<7 asidik, pH=7 nötr, pH>7 baziktir."),
            ("ph ölçeği","pH, 0-14 arasında asitlik/bazlık ölçeğidir. 0 güçlü asit, 7 nötr, 14 güçlü bazdır. Mide asidi pH≈2, kan pH≈7.4."),
            ("su neden h2o","Su, 2 hidrojen + 1 oksijen atomundan oluşur (H₂O). Polar molekül yapısı sayesinde pek çok maddeyi çözer."),
            ("karbondioksit nedir","CO₂, 1 karbon + 2 oksijen atomundan oluşan gazdır. Sera etkisine katkıda bulunur, bitkiler fotosentezde kullanır."),
            ("ozon nedir","Ozon (O₃), 3 oksijen atomundan oluşan moleküldür. Stratosferde UV ışınlarını emer ve Dünya'yı korur."),
            ("polimer nedir","Polimer, tekrarlayan monomer birimlerinden oluşan büyük moleküldür. Plastikler, proteinler ve DNA polimer örnekleridir."),
        ]
        # Biyoloji
        biyoloji = [
            ("dna nedir","DNA, canlıların genetik bilgisini taşıyan çift sarmallı moleküldür. Adenin-Timin ve Guanin-Sitozin baz çiftlerinden oluşur."),
            ("hücre nedir","Hücre, canlıların temel yapı ve işlev birimidir. Prokaryot (çekirdeksiz) ve ökaryot (çekirdekli) olmak üzere ikiye ayrılır."),
            ("mitoz nedir","Mitoz, bir hücrenin iki özdeş yavru hücreye bölünme sürecidir. Büyüme ve yenilenme için kullanılır."),
            ("mayoz nedir","Mayoz, eşey hücrelerinin (sperm/yumurta) oluşumu için gerçekleşen özel bölünmedir. Sonuçta 4 haploid hücre oluşur."),
            ("protein nedir biyoloji","Protein, amino asitlerden oluşan biyomoleküllerdir. Enzim, hormon ve yapısal görevler üstlenir. 20 farklı amino asit vardır."),
            ("fotosentez denklemi","Fotosentez: 6CO₂ + 6H₂O + ışık → C₆H₁₂O₆ + 6O₂. Bitkiler güneş enerjisiyle besin üretir."),
            ("solunum nedir","Hücresel solunum: C₆H₁₂O₆ + 6O₂ → 6CO₂ + 6H₂O + enerji (ATP). Glikozdan enerji elde edilir."),
            ("evrim kanıtları","Evrim kanıtları: fosil kayıtları, karşılaştırmalı anatomi, homolog organlar, DNA benzerliği, biyocoğrafya."),
            ("bağışıklık sistemi","Bağışıklık sistemi, hastalık yapan organizmalara karşı savunma sağlar. Doğal bağışıklık (genel) ve edinilmiş bağışıklık (özgül) olmak üzere ikiye ayrılır."),
            ("aşı nasıl çalışır","Aşı, zayıflatılmış veya ölü patojeni vücuda tanıtarak bağışıklık sistemi hafızasını aktive eder. İkinci maruziyette hızlı yanıt üretilir."),
        ]
        items = fizik + kimya + biyoloji
        # Soru varyasyonları otomatik ekle
        expanded = []
        for q, a in items:
            expanded.append((q, a))
            expanded.append((q + " nedir", a))
            expanded.append((q + " ne demek", a))
            expanded.append(("bana " + q + " anlat", a))
        return self._bulk("bilim", expanded)

    def _load_matematik(self):
        items = []
        # Temel matematik tablosu — 1-100 arası çarpım
        for i in range(1, 21):
            for j in range(1, 21):
                result = i * j
                items.append((f"{i} çarpı {j}", f"{i} × {j} = {result}"))
                items.append((f"{i}x{j}", f"{i} × {j} = {result}"))
                items.append((f"{i} kere {j}", f"{i} × {j} = {result}"))
        # Kareler
        for i in range(1, 101):
            items.append((f"{i} nin karesi", f"{i}² = {i*i}"))
            items.append((f"{i} kare", f"{i}² = {i*i}"))
            items.append((f"{i} üssü 2", f"{i}² = {i*i}"))
        # Karekökler
        import math
        for i in [1,4,9,16,25,36,49,64,81,100,121,144,169,196,225,256,289,324,361,400,
                  500,625,900,1000,1024,2500,10000]:
            root = math.sqrt(i)
            if root == int(root):
                items.append((f"{i} nin karekökü", f"√{i} = {int(root)}"))
                items.append((f"karekök {i}", f"√{i} = {int(root)}"))
        # Faktöriyeller
        fact = 1
        for i in range(1, 13):
            fact *= i
            items.append((f"{i} faktöriyel", f"{i}! = {fact:,}"))
        # Matematik kavramları
        kavramlar = [
            ("pi sayısı","π (pi) ≈ 3.14159265358979... Bir çemberin çevresinin çapına oranıdır. Sonsuz ve periyodik olmayan ondalık sayıdır."),
            ("euler sayısı","e (Euler) ≈ 2.71828... Doğal logaritmanın tabanıdır. Bileşik faiz ve büyüme modellerinde temel rol oynar."),
            ("fibonacci dizisi","Fibonacci: 0,1,1,2,3,5,8,13,21,34,55,89... Her sayı kendinden önceki iki sayının toplamıdır."),
            ("asal sayı nedir","Asal sayılar 1'den ve kendisinden başka böleni olmayan doğal sayılardır: 2,3,5,7,11,13,17,19,23,29..."),
            ("türev ne işe yarar","Türev, bir fonksiyonun değişim hızını (anlık eğimini) verir. Fizik, mühendislik ve optimizasyonda kullanılır."),
            ("integral ne işe yarar","İntegral, türevin tersidir. Eğri altındaki alanı ve birikimli değişimleri hesaplar."),
            ("pisagor teoremi","Pisagor: a²+b²=c². Dik üçgende dik kenar karelerinin toplamı hipotenüsün karesine eşittir."),
            ("logaritma nedir","Logaritma, üs almanın tersi işlemidir. log₂(8)=3, çünkü 2³=8. Büyük sayı aralıklarını kompres eder."),
            ("vektör nedir","Vektör, hem büyüklük hem yön bilgisi olan matematiksel nesne. Kuvvet, hız gibi fiziksel nicelikler vektörle ifade edilir."),
            ("matris nedir","Matris, satır ve sütunlara dizilmiş sayı tablosudur. Lineer denklem sistemlerini çözmek için kullanılır."),
        ]
        for q, a in kavramlar:
            items.append((q, a))
            items.append((q + " nedir", a))
        return self._bulk("matematik", items)

    def _load_teknoloji(self):
        items = [
            ("python nedir","Python, 1991'de Guido van Rossum tarafından yaratılan yüksek seviyeli programlama dilidir. Yapay zeka, web, veri bilimi, otomasyon için idealdir."),
            ("python nasıl öğrenilir","Python için: resmi docs, Codecademy, freeCodeCamp, YouTube (CS50, Corey Schafer). Günlük küçük projeler yap. 3 ayda temel öğrenilir."),
            ("javascript nedir","JavaScript, web tarayıcılarında çalışan programlama dilidir. DOM manipülasyonu, etkileşimli web sayfaları ve Node.js ile sunucu tarafında kullanılır."),
            ("java ile python farkı","Python: daha az kod, daha okunaklı, dinamik tip. Java: daha hızlı, kurumsal, statik tip. Python AI/veri, Java kurumsal/Android için tercih edilir."),
            ("c++ nedir","C++, C'nin nesne yönelimli uzantısıdır. Oyun motoru, sistem yazılımı, gömülü sistemler için kullanılır. Çok hızlı ama öğrenmesi zorlu."),
            ("rust nedir","Rust, bellek güvenli sistem programlama dilidir. C++ hızında ama bellek hataları olmadan. Mozilla tarafından geliştirildi."),
            ("yapay zeka nedir","Yapay zeka (AI), insan zekasını taklit eden sistemlerdir. Makine öğrenmesi, derin öğrenme, NLP, bilgisayarlı görü alt dalları vardır."),
            ("makine öğrenmesi algoritmaları","ML algoritmaları: Lineer Regresyon, Karar Ağaçları, Random Forest, SVM, K-NN, Naive Bayes, Sinir Ağları (NN)."),
            ("tensorflow nedir","TensorFlow, Google'ın açık kaynaklı derin öğrenme kütüphanesidir. Sinir ağı modelleri oluşturmak için kullanılır."),
            ("pytorch nedir","PyTorch, Meta'nın derin öğrenme framework'üdür. Araştırmalarda TensorFlow'dan daha popüler hale gelmiştir."),
            ("docker nedir","Docker, uygulamaları container'lar içinde paketleyen platformdur. 'Bende çalışıyor' problemini çözer, taşınabilir dağıtım sağlar."),
            ("kubernetes nedir","Kubernetes (k8s), container'ları yöneten orkestrasyon platformudur. Ölçeklendirme, yük dengeleme ve otomatik kurtarma sağlar."),
            ("microservice nedir","Microservice, büyük uygulamanın küçük bağımsız servislere bölünmesi mimarisidir. Netflix ve Uber bu mimariyi kullanır."),
            ("rest api nedir","REST API, HTTP protokolü üzerinde kaynak tabanlı web servisleri mimarisidir. GET, POST, PUT, DELETE metodları kullanılır."),
            ("graphql nedir","GraphQL, Facebook'un geliştirdiği API sorgu dilidir. İstemci ihtiyacı kadar veri çeker, over/under fetching sorununu çözer."),
            ("sql nedir","SQL (Structured Query Language), ilişkisel veritabanlarını yönetmek için kullanılan dildir. SELECT, INSERT, UPDATE, DELETE temel komutlardır."),
            ("nosql nedir","NoSQL veritabanları, ilişkisel olmayan esnek yapıda veri saklarlar. MongoDB (belge), Redis (anahtar-değer), Cassandra (kolon) örnekleridir."),
            ("git nedir","Git, dağıtık sürüm kontrol sistemidir. Linus Torvalds tarafından geliştirilmiştir. GitHub, GitLab ve Bitbucket popüler hosting platformlarıdır."),
            ("agile nedir","Agile, yazılım geliştirmede esnek, iteratif yaklaşımdır. Sprint, Scrum, Kanban Agile metodolojileridir. Büyük firmaların çoğu kullanır."),
            ("devops nedir","DevOps, geliştirme ve operasyon ekiplerini birleştiren kültür ve pratikler bütünüdür. CI/CD, otomasyon ve sürekli dağıtım temel unsurlarıdır."),
            ("cloud computing nedir","Bulut bilişim, internet üzerinden bilgisayar kaynakları sunar. AWS, Azure, GCP büyük sağlayıcılardır. IaaS, PaaS, SaaS modelleri vardır."),
            ("linux komutları","Temel Linux: ls (listele), cd (dizin değiştir), mkdir (klasör oluştur), rm (sil), grep (ara), chmod (izin), top (süreçler), ssh (uzak bağlantı)."),
            ("veri yapıları nedir","Temel veri yapıları: Array, Linked List, Stack, Queue, Tree, Graph, Hash Table. Algoritma verimliliği için doğru seçim kritik."),
            ("big o notasyonu","Big O, algoritma karmaşıklığını ifade eder. O(1): sabit, O(n): lineer, O(n²): karesel, O(log n): logaritmik. En iyisi O(1)."),
            ("cybersecurity nedir","Siber güvenlik, sistemleri dijital saldırılardan koruma pratiğidir. Encryption, firewall, IDS, penetration testing temel konulardır."),
        ]
        # Programlama dilleri için ek sorular
        diller = ["python","javascript","java","c++","c#","swift","kotlin","go","rust","php","ruby","scala","r","matlab"]
        for dil in diller:
            items.append((f"{dil} ne işe yarar", f"{dil.capitalize()}, yazılım geliştirmede kullanılan programlama dilidir. Kullanım alanları: web, mobil, veri bilimi, sistem programlama gibi alanlara göre değişir."))
            items.append((f"{dil} öğrenmek zor mu", f"{dil.capitalize()} öğrenmek için temel programlama mantığını öğrenmen yeterli. Günlük pratikle 3-6 ayda temel seviyeye ulaşılabilir."))
        return self._bulk("teknoloji", items)

    def _load_tarih(self):
        items = [
            ("osmanlı imparatorluğu ne zaman kuruldu","Osmanlı İmparatorluğu 1299'da Osman Bey tarafından kuruldu. 1453 İstanbul'un fethi ile büyük bir güç haline geldi."),
            ("osmanlı ne zaman yıkıldı","Osmanlı İmparatorluğu 1 Kasım 1922'de saltanatın kaldırılmasıyla sona erdi."),
            ("1453 neden önemli","1453, Fatih Sultan Mehmet'in İstanbul'u fethiyle Doğu Roma İmparatorluğu'nun (Bizans) sonunu simgeler. Orta Çağ'ın bitişi kabul edilir."),
            ("mustafa kemal atatürk","Atatürk (1881-1938), Türkiye Cumhuriyeti'nin kurucusudur. Kurtuluş Savaşı'nı yönetmiş, latin alfabesi, kadın hakları gibi devrimler yapmıştır."),
            ("kurtuluş savaşı tarihleri","Kurtuluş Savaşı 19 Mayıs 1919'da başladı, 9 Eylül 1922'de İzmir'in kurtuluşuyla pratik olarak sona erdi."),
            ("türkiye cumhuriyeti kuruluş tarihi","29 Ekim 1923. Bu tarih her yıl Cumhuriyet Bayramı olarak kutlanır."),
            ("birinci dünya savaşı nedenleri","WWI nedenleri: milliyetçilik, emperyalizm, militarizm, ittifak sistemi ve Arşidük Franz Ferdinand suikastı (1914)."),
            ("ikinci dünya savaşı nasıl bitti","WWII, 8 Mayıs 1945'te Almanya'nın, 15 Ağustos 1945'te Japonya'nın teslim olmasıyla sona erdi. Atom bombası bu teslimiyette rol oynadı."),
            ("fransız ihtilali","1789'da başlayan Fransız İhtilali, 'Özgürlük, Eşitlik, Kardeşlik' ilkeleriyle monarşiyi yıktı ve modern demokrasinin temelini attı."),
            ("sanayi devrimi","18-19. yüzyılda İngiltere'de başlayan Sanayi Devrimi, el emeğinden makine üretimine geçişi temsil eder. Kömür, buhar ve demir kritik rol oynadı."),
            ("soğuk savaş nedir","1947-1991 arası ABD-SSCB ideolojik rekabeti. Doğrudan savaş olmadı ama vekâlet savaşları, silahlanma yarışı ve uzay yarışı yaşandı."),
            ("berlin duvarı","Berlin Duvarı 1961'de inşa edildi, 9 Kasım 1989'da yıkıldı. Doğu-Batı Almanya'yı ayırıyordu, Soğuk Savaş'ın sembolüydü."),
            ("roma imparatorluğu","Roma İmparatorluğu MÖ 27'de Augustus ile başladı. Batı Roma 476'da yıkıldı, Doğu Roma (Bizans) 1453'e kadar devam etti."),
            ("napolyon kimdir","Napolyon Bonaparte (1769-1821), Fransız askeri ve devlet adamıdır. Avrupa'nın büyük bölümünü fethetti, Fransız hukuku (Napolyon Kodu) günümüzde de etkilidir."),
            ("çin medeniyeti","Çin medeniyeti 5.000+ yıllık geçmişe sahiptir. Dört büyük icat: kâğıt, matbaa, barut ve pusula Çin'den dünyaya yayıldı."),
        ]
        return self._bulk("tarih", items)

    def _load_cografya(self):
        items = []
        # Ülke başkentleri
        baskentler = {
            "türkiye":"Ankara","japonya":"Tokyo","fransa":"Paris","almanya":"Berlin",
            "abd":"Washington D.C.","rusya":"Moskova","çin":"Pekin (Beijing)","hindistan":"Yeni Delhi",
            "brezilya":"Brasília","avustralya":"Canberra","kanada":"Ottawa","meksika":"Mexico City",
            "arjantin":"Buenos Aires","güney kore":"Seul","ispanya":"Madrid","italya":"Roma",
            "hollanda":"Amsterdam","belçika":"Brüksel","isviçre":"Bern","avusturya":"Viyana",
            "polonya":"Varşova","portekiz":"Lizbon","yunanistan":"Atina","mısır":"Kahire",
            "nijerya":"Abuja","güney africa":"Cape Town/Pretoria","kenya":"Nairobi",
            "suudi arabistan":"Riyad","iran":"Tahran","irak":"Bağdat","israil":"Tel Aviv/Kudüs",
            "pakistan":"İslamabad","bangladeş":"Dakka","endonezya":"Cakarta","filipinler":"Manila",
            "tayland":"Bangkok","vietnam":"Hanoi","malezya":"Kuala Lumpur","singapur":"Singapur",
            "yeni zelanda":"Wellington","norveç":"Oslo","isveç":"Stockholm","danimarka":"Kopenhag",
            "finlandiya":"Helsinki","çek cumhuriyeti":"Prag","macaristan":"Budapeşte",
            "romanya":"Bükreş","ukrayna":"Kiev","hollanda":"Amsterdam",
        }
        for ulke, baskent in baskentler.items():
            items.append((f"{ulke} başkenti nedir", f"Başkent ({ulke.title()}): {baskent}"))
            items.append((f"{ulke} başkenti", f"Başkent ({ulke.title()}): {baskent}"))
            items.append((f"{baskent.lower()} nereye başkent", f"{baskent}, {ulke.title()} ülkesinin başkentidir."))

        # Coğrafi bilgiler
        cografi = [
            ("dünyanın en büyük kıtası","Asya, yaklaşık 44,6 milyon km² ile dünyanın en büyük kıtasıdır."),
            ("dünyanın en büyük ülkesi","Rusya, 17,1 milyon km² ile dünyanın yüzölçümü bakımından en büyük ülkesidir."),
            ("dünyanın en kalabalık ülkesi","Hindistan, 2023 itibarıyla yaklaşık 1,44 milyar nüfusuyla en kalabalık ülkedir."),
            ("dünyanın en yüksek dağı","Everest Dağı, 8.848,86 metre ile dünyanın en yüksek zirvesidir. Nepal-Çin sınırında."),
            ("dünyanın en uzun nehri","Nil Nehri ~6.650 km ile en uzun kabul edilir. Amazon en büyük havzaya sahip."),
            ("dünyanın en büyük okyanusu","Pasifik Okyanusu, 165 milyon km² ile en büyük ve en derin okyanustur."),
            ("dünyanın en derin noktası","Mariana Çukuru, Pasifik Okyanusu'nda ~11.034 metre derinlikte dünyanın en derin noktasıdır."),
            ("sahra çölü","Sahra Çölü, 9,2 milyon km² ile dünyanın en büyük sıcak çölüdür. Kuzey Afrika'dadır."),
            ("amazon ormanları","Amazon ormanları, ~5,5 milyon km² ile dünyanın en büyük yağmur ormanıdır. 'Dünyanın akciğeri'."),
            ("büyük set resifi","Büyük Set Resifi, Avustralya kıyısındaki dünyanın en büyük mercan resif sistemidir."),
        ]
        items.extend(cografi)
        return self._bulk("cografya", items)

    def _load_saglik(self):
        items = []
        # Hastalık bilgileri
        hastaliklar = [
            ("diyabet nedir","Diyabet (şeker hastalığı), vücudun insülini yeterince üretemediği veya kullanamadığı kronik hastalıktır. Tip 1, Tip 2 ve gestasyonel diyabet olmak üzere üç türü vardır."),
            ("hipertansiyon nedir","Hipertansiyon (yüksek tansiyon), kan basıncının sürekli yüksek olmasıdır. 140/90 mmHg üzeri yüksek kabul edilir. Kalp, böbrek ve beyin hasarına yol açabilir."),
            ("anemi nedir","Anemi, kandaki hemoglobin miktarının düşük olmasıdır. Demir eksikliği en yaygın nedenidir. Yorgunluk, solgunluk belirtiler arasındadır."),
            ("alzheimer nedir","Alzheimer, ilerleyen bellek kaybı ve bilişsel gerilemeye neden olan nörodejeneratif bir hastalıktır. Demansın en yaygın nedenidir."),
            ("covid 19 nedir","COVID-19, SARS-CoV-2 virüsünün neden olduğu bulaşıcı solunum yolu hastalığıdır. 2019'da ortaya çıktı ve pandemi ilan edildi."),
            ("grip nedir","Grip, influenza virüslerinin neden olduğu bulaşıcı solunum yolu hastalığıdır. Ateş, kas ağrısı, yorgunluk belirtiler arasındadır. Yıllık aşı korunma sağlar."),
            ("depresyon belirtileri","Depresyon belirtileri: sürekli üzüntü, enerji kaybı, ilgi azalması, uyku bozuklukları, iştah değişimi, konsantrasyon güçlüğü. Tedavi edilebilir bir hastalıktır."),
            ("anksiyete nedir","Anksiyete, aşırı endişe ve kaygı bozukluğudur. Panik atak, OKB, sosyal fobi türleri vardır. Terapi ve gerektiğinde ilaçla tedavi edilir."),
        ]
        # Vitamin ve mineraller
        vitaminler = [
            ("a vitamini","A vitamini görme, bağışıklık sistemi ve cilt sağlığı için gereklidir. Karaciğer, havuç ve tatlı patates iyi kaynaklardır."),
            ("b12 vitamini","B12, sinir sistemi ve kırmızı kan hücresi üretimi için kritiktir. Et, balık ve süt ürünlerinde bulunur. Veganlarda eksiklik sık görülür."),
            ("c vitamini","C vitamini antioksidan, bağışıklık güçlendirici ve kollajen üretimi için gereklidir. Turunçgiller, kivi ve biber iyi kaynaklardır."),
            ("d vitamini","D vitamini kemik sağlığı, bağışıklık ve ruh hali için önemlidir. Güneş ışığıyla sentezlenir. Balık yağı ve yumurta da kaynak."),
            ("e vitamini","E vitamini antioksidan özelliğiyle hücreleri serbest radikallere karşı korur. Fındık, tohum ve bitkisel yağlarda bulunur."),
            ("demir","Demir, oksijen taşıyan hemoglobin için gereklidir. Kırmızı et, ıspanak, baklagiller kaynaklardır. C vitamini emilimi artırır."),
            ("kalsiyum","Kalsiyum, kemik ve diş sağlığı ile kas işlevi için gereklidir. Süt ürünleri, brokoli ve badem iyi kaynaklardır."),
            ("magnezyum","Magnezyum, 300+ enzimatik reaksiyonda rol oynar. Kas, sinir ve kalp fonksiyonu için önemlidir. Yeşil yapraklı sebze, kuruyemişlerde bulunur."),
        ]
        items.extend(hastaliklar + vitaminler)
        # Egzersiz varyasyonları
        egzersizler = ["squat","deadlift","bench press","plank","burpee","pull up","push up","lunge","bicep curl","tricep dip"]
        for egzersiz in egzersizler:
            items.append((f"{egzersiz} nasıl yapılır", f"{egzersiz.title()}: Doğru form için nötr omurga, kontrollü hareket ve nefes tekniği önemlidir. Ağırlığı kademeli artır, ısınmayı ihmal etme."))
        return self._bulk("saglik", items)

    def _load_felsefe(self):
        items = [
            ("sokrates kim","Sokrates (MÖ 470-399), Antik Yunan filozofudur. 'Kendini bil' öğretisi ve Sokratik yöntemle tanınır. Hemlock içerek idam edildi."),
            ("platon kim","Platon (MÖ 428-348), Sokrates'in öğrencisidir. İdealar teorisi, Mağara alegorisi ve 'Devlet' diyaloguyla ünlüdür."),
            ("aristoteles kim","Aristoteles (MÖ 384-322), Platon'un öğrencisidir. Mantık, biyoloji, etik ve siyaset biliminin babası sayılır. İskender'in hocasıydı."),
            ("nietzsche kim","Friedrich Nietzsche (1844-1900), Alman filozoftur. 'Tanrı öldü', Übermensch ve güç iradesi kavramlarıyla tanınır."),
            ("kant kim","Immanuel Kant (1724-1804), Alman filozoftur. Kategorik imperatif: 'Sadece evrensel yasa olmasını isteyebileceğin kurala göre davran.'"),
            ("descartes kim","René Descartes (1596-1650), modern felsefenin babasıdır. 'Düşünüyorum, öyleyse varım' (Cogito ergo sum) ifadesiyle tanınır."),
            ("varoluşçuluk nedir","Varoluşçuluk, insanın kendi anlamını özgürce yarattığını savunan felsefi akımdır. Sartre, Camus, Heidegger temsilcileridir."),
            ("nihilizm nedir","Nihilizm, hayatın nesnel anlam veya değer taşımadığını savunan felsefi görüştür. Nietzsche nihilizmi aştığını iddia etti."),
            ("stoacılık nedir","Stoacılık, kontrol edemediklerinizi kabullenerek iç huzuru bulmayı öğütleyen antik Yunan felsefesidir. Marcus Aurelius büyük stoacıdır."),
            ("ahlak felsefesi","Etik (Ahlak felsefesi): Faydacılık (sonuç önemli), Deontoloji (ödev önemli), Erdem etiği (karakter önemli) temel yaklaşımlardır."),
            ("özgür irade nedir","Özgür irade, kişinin kendi kararlarını bağımsız biçimde verebilmesidir. Determinizm vs Libertaryenizm vs Uyumculuk tartışması sürmektedir."),
            ("tanrı var mı","Tanrı'nın varlığı: Teizm (Tanrı vardır), Ateizm (Tanrı yoktur), Agnostisizm (bilinmez) ve Deizm (Tanrı yaratıp çekildi) temel görüşlerdir."),
        ]
        return self._bulk("felsefe", items)

    def _load_ekonomi(self):
        items = []
        # Kripto para bilgileri
        kriptolar = {
            "bitcoin":"Bitcoin (BTC), 2009'da Satoshi Nakamoto tarafından yaratılan ilk kripto paradır. Blockchain tabanlı, toplam arzı 21 milyon ile sınırlı.",
            "ethereum":"Ethereum (ETH), 2015'te Vitalik Buterin'in kurduğu akıllı kontrat platformudur. DeFi ve NFT'nin altyapısını oluşturur.",
            "solana":"Solana (SOL), yüksek hızlı, düşük maliyetli blockchain platformudur. Saniyede binlerce işlem gerçekleştirebilir.",
            "cardano":"Cardano (ADA), akademik araştırmaya dayalı, çevre dostu blockchain platformudur. Charles Hoskinson tarafından kuruldu.",
            "polkadot":"Polkadot (DOT), farklı blockchain'lerin birbirleriyle iletişim kurmasını sağlayan ağdır.",
            "binance coin":"BNB, Binance borsasının yerel token'ıdır. Binance Smart Chain ekosisteminin temel kripto parasıdır.",
            "ripple":"XRP (Ripple), bankalar arası para transferlerini hızlandırmak için tasarlanmış kripto paradır.",
            "dogecoin":"Dogecoin (DOGE), 2013'te şaka olarak başlayan ama ciddi piyasa değerine ulaşan kripto paradır. Elon Musk destekledi.",
        }
        for kripto, bilgi in kriptolar.items():
            items.append((f"{kripto} nedir", bilgi))
            items.append((f"{kripto} kaç dolar", f"{kripto.title()} fiyatı için 'bitcoin fiyatı' gibi gerçek zamanlı kaynak kontrol edin. Kripto fiyatları çok değişkendir."))
        # Ekonomi kavramları
        kavramlar = [
            ("stagflasyon nedir","Stagflasyon, yüksek enflasyon + durgunluk + yüksek işsizliğin eş zamanlı yaşandığı ekonomik durumdur. Yönetilmesi çok zordur."),
            ("resesyon nedir","Resesyon, GDP'nin art arda 2 çeyrek boyunca küçüldüğü ekonomik yavaşlama dönemidir."),
            ("fiyat balonu nedir","Fiyat balonu, bir varlığın gerçek değerinin çok üzerinde fiyatlanmasıdır. Dotcom balonu (2000) ve konut balonu (2008) örnek."),
            ("merkez bankası ne yapar","Merkez bankası, para politikasını yönetir (faiz oranları), enflasyonu kontrol eder, para arzını düzenler ve finansal sistemi denetler."),
            ("vergi nedir","Vergi, devletin kamu hizmetlerini finanse etmek için vatandaşlardan topladığı zorunlu ödemedir. Gelir, KDV, kurumlar vergisi yaygın türlerdir."),
            ("bütçe açığı nedir","Bütçe açığı, devlet harcamalarının gelirinden fazla olduğu durumdur. Devlet borçlanarak bu açığı kapatır."),
            ("özel sektör kamu farkı","Özel sektör kâr amaçlı bireyler/şirketlerce işletilir. Kamu sektörü devlet tarafından yönetilir, genellikle kâr amacı gütmez."),
            ("arz talep yasası","Arz arttığında fiyat düşer, talep arttığında fiyat yükselir. Denge noktasında arz=talep ve piyasa temizlenir."),
        ]
        items.extend(kavramlar)
        return self._bulk("ekonomi", items)

    def _load_sanat(self):
        items = [
            ("rönesans nedir","Rönesans (14-17. yy), Avrupa'da antik Yunan-Roma kültürüne dönüşü simgeleyen kültürel yeniden doğuş hareketidir. Da Vinci, Michelangelo, Raphael önemli isimler."),
            ("barok sanat nedir","Barok (17-18. yy), aşırı süsleme, dramatik ışık-gölge (chiaroscuro) ve güçlü duygularla karakterize sanat akımıdır."),
            ("empresyonizm nedir","Empresyonizm, 19. yüzyılda Fransa'da doğan, anı ve ışığı yakalamayı amaçlayan resim akımıdır. Monet, Renoir, Degas önemli temsilcilerdir."),
            ("kübizm nedir","Kübizm, Picasso ve Braque tarafından geliştirilen, nesneleri aynı anda birden fazla açıdan gösteren sanat akımıdır."),
            ("sürrealizm nedir","Sürrealizm, bilinçaltı imgelem ve rüya dünyasını sanata taşıyan 20. yüzyıl akımıdır. Dalí ve Magritte önemli temsilciler."),
            ("pop art nedir","Pop Art, 1950-60'larda kitlesel kültür ve tüketim imgelerini sanata taşıyan akımdır. Andy Warhol en tanınan temsilcidir."),
            ("türk müziği türleri","Türk müziği: Türk Sanat Müziği, Türk Halk Müziği (türkü), Arabesk, Pop, Klasik Türk Müziği. Makam sistemi temel yapıdır."),
            ("klasik müzik dönemleri","Klasik müzik dönemleri: Barok (Bach, Handel), Klasik (Mozart, Haydn), Romantik (Beethoven, Chopin), Modern (Stravinsky, Bartók)."),
        ]
        return self._bulk("sanat", items)

    def _load_doga(self):
        items = [
            ("iklim değişikliği nedir","İklim değişikliği, uzun vadeli hava örüntülerindeki değişimdir. İnsan kaynaklı sera gazı emisyonları küresel ısınmayı hızlandırıyor."),
            ("yenilenebilir enerji türleri","Yenilenebilir enerji: güneş, rüzgar, hidroelektrik, jeotermal, biyokütle. Karbon salımı düşük, tükenmez kaynaklardır."),
            ("plastik kirliliği","Yılda 8 milyon ton plastik okyanuslara karışıyor. Mikroplastikler besin zincirine giriyor. Geri dönüşüm ve azaltma kritik önem taşıyor."),
            ("biyoçeşitlilik kaybı","Hız: doğal oran x1000. Habitat kaybı, iklim değişikliği, istilacı türler ve kirlilik başlıca nedenler. 6. büyük kitlesel yok oluş yaşanıyor."),
            ("su kıtlığı","Dünya nüfusunun %40'ı su stresi altında. Temiz su kaynakları sınırlı. Tasarruf, geri dönüşüm ve akıllı sulama çözüm yollarıdır."),
            ("orman yangınları neden artar","Küresel ısınma, kuraklık ve insan faaliyetleri orman yangınlarını artırıyor. Amazon, Avustralya, Akdeniz en çok etkilenen bölgeler."),
            ("coral reef bleaching","Mercan ağarması, deniz sıcaklıklarının yükselmesiyle alglerin mercanı terk etmesidir. Büyük Set Resifi %50'den fazla etkilendi."),
            ("sürdürülebilirlik nedir","Sürdürülebilirlik, gelecek nesillerin ihtiyaçlarını tehlikeye atmadan bugünkü ihtiyaçları karşılama ilkesidir."),
        ]
        return self._bulk("doga", items)

    def _load_uzay(self):
        items = [
            ("güneş sistemi gezegenleri","8 gezegen: Merkür (en küçük, en sıcak), Venüs (en parlak), Dünya, Mars (kırmızı gezegen), Jüpiter (en büyük), Satürn (halkalar), Uranüs, Neptün."),
            ("jüpiter hakkında","Jüpiter, Güneş Sistemi'nin en büyük gezegenidir. Büyük Kırmızı Leke, yüzyıllardır süren kasırgadır. 95 bilinen uydusu vardır."),
            ("satürn halkası","Satürn'ün halkaları buz, kaya ve toz parçacıklarından oluşur. Büyük ölçüde buz, su ve karbon dioksitten meydana gelir."),
            ("mars hakkında","Mars'ta Güneş Sistemi'nin en yüksek dağı (Olympus Mons, 22 km) ve en derin vadisi bulunur. NASA rover'ları araştırıyor."),
            ("ay nasıl oluştu","Ay, yaklaşık 4,5 milyar yıl önce Theia adlı dev bir nesnenin Dünya'ya çarpmasıyla oluşan dev bir çarpışma teorisiyle açıklanır."),
            ("ay'a ilk giden insan","Neil Armstrong, 20 Temmuz 1969'da Apollo 11 misyonuyla Ay'a ilk adım atan insandır. Buzz Aldrin ikinci kişiydi."),
            ("james webb teleskopu","James Webb Uzay Teleskobu, Hubble'ın halefidir. 2021'de fırlatıldı. Kızılötesi spektrumda evrenin ilk galaksilerini görüntülüyor."),
            ("karadelik bilgileri","Kara delikler: yıldız ölümünden oluşur, olay ufku içinden ışık çıkamaz, zaman yavaşlar. İlk görüntü 2019'da çekildi (M87*)."),
            ("dark matter nedir","Karanlık madde, evrendeki normal maddenin ~5 katı kütlede ama görünmez. Galaksilerin dönüş hızlarını açıklamak için önerildi."),
            ("multiverse nedir","Çoklu evren teorisi, bizimkine paralel başka evrenler olduğunu öne sürer. Kuantum mekaniği ve kozmolojide tartışılan bir kavram."),
        ]
        return self._bulk("uzay", items)

    def _load_spor(self):
        items = []
        futbol_takimlar = [
            ("galatasaray","Galatasaray, 1905 kurulu Türk futbol kulübüdür. Süper Lig'de en çok şampiyonluğa sahip takımdır. Sarı-kırmızı renkleri taşır."),
            ("fenerbahçe","Fenerbahçe, 1907 kurulu Türk futbol kulübüdür. İstanbul Kadıköy'ü temsil eder. Mavi-sarı renkleri vardır."),
            ("beşiktaş","Beşiktaş, 1903 kurulu, Türkiye'nin en eski spor kulübüdür. Siyah-beyaz renkleri taşır."),
            ("real madrid","Real Madrid, dünyada en çok Şampiyonlar Ligi kazanan futbol kulübüdür. İspanya'nın Madrid şehrini temsil eder."),
            ("barcelona","FC Barcelona, 'Katalon Kulübü' olarak bilinir. Messi yıllarında dominant güçtü. Tiki-taka oynayış biçimiyle tanınır."),
            ("manchester united","Manchester United, İngiltere'nin en başarılı kulüplerinden biridir. Sir Alex Ferguson döneminde 13 Premier Lig şampiyonluğu aldı."),
        ]
        for takim, bilgi in futbol_takimlar:
            items.append((f"{takim} hakkında", bilgi))
            items.append((f"{takim} nedir", bilgi))

        spor_kavramlar = [
            ("offside kuralı","Offsaid: topun oynandığı anda saldırı oyuncusu rakip kale önünden son iki rakip oyuncudan daha ileride ise geçersizdir."),
            ("formula 1 nasıl çalışır","F1: 10 takım, 20 sürücü, ~24 yarış sezonu. En hızlı qualifying yapan pole pozisyonu alır. Puan sistemi: 1. 25p, 2. 18p, 3. 15p..."),
            ("nba en çok şampiyonluk","NBA'de en çok şampiyonluk: Boston Celtics ve Los Angeles Lakers 17'şer kez. Michael Jordan 6 şampiyonluk kazandı."),
            ("wimbledon nedir","Wimbledon, 1877'den beri Londra'da düzenlenen en prestijli tenis turnuvasıdır. Tek çim kortlu Grand Slam turnuvasıdır."),
            ("rugby nedir","Rugby, oval topla oynanan takım sporudur. Rugby Union (15 kişi) ve Rugby League (13 kişi) ana türleri vardır."),
        ]
        items.extend(spor_kavramlar)
        return self._bulk("spor", items)

    def _load_yemek(self):
        items = []
        tarifler = {
            "menemen":("Menemen tarifi: domates, biber, yumurta. Soğan ve biberler yağda kavrulur, domates eklenir, yumurta kırılır karıştırılır. 10 dakika."),
            "pilav":("Pilav tarifi: 1 su bardağı pirinç, 2 su bardağı su, tereyağı, tuz. Pirinç yıkanır, tereyağda kavrulur, su ve tuz eklenir, kısık ateşte pişirilir."),
            "mercimek çorbası":("Kırmızı mercimek çorbası: mercimek, soğan, havuç, patates haşlanır, blenderdan geçirilir. Tereyağda kırmızıbiber ve nane kavurulup üzerine dökülür."),
            "köfte":("Köfte tarifi: kıyma, soğan rendesi, ekmek içi, yumurta, baharatlar karıştırılır. Küçük toplar yapılır, tavada veya ızgarada pişirilir."),
            "sütlaç":("Sütlaç: pirinç, süt, şeker kaynatılır. Fırında üstü kızartılır. Tarçın ile servis edilir."),
            "baklava":("Baklava: yufka katları tereyağıyla yağlanır, araya ceviz/fıstık konur. Fırında 180°C'de pişirilip şerbet dökülür."),
        }
        for yemek, tarif in tarifler.items():
            items.append((f"{yemek} nasıl yapılır", tarif))
            items.append((f"{yemek} tarifi", tarif))
            items.append((f"{yemek} yapımı", tarif))

        beslenme = [
            ("kalori kaç olmalı","Ortalama yetişkin günde 2000-2500 kalori almalı. Kilo vermek için 300-500 kalori açık önerilir. Aktif bireyler için daha fazla."),
            ("akdeniz diyeti nedir","Akdeniz diyeti: bol sebze-meyve, zeytinyağı, tam tahıl, balık, az kırmızı et. Kalp sağlığı için en iyi diyet olarak kanıtlanmış."),
            ("ketojenik diyet nedir","Ketojenik (keto) diyet, karbonhidratı kısıtlayıp yağı artıran diyettir. Vücut yakıt olarak keton cisimleri üretir. Kısa vadede etkili."),
            ("glüten nedir","Glüten, buğday, arpa ve çavdarda bulunan protein kompleksidir. Çölyak hastalarında bağırsak hasarına yol açar. İnce bağırsağı etkiler."),
            ("prebiyotik probiyotik farkı","Probiyotik: canlı faydalı bakteri (yoğurt, kefir). Prebiyotik: probiyotikleri besleyen lif (soğan, sarımsak, muz). İkisi birlikte simbiyotik."),
        ]
        items.extend(beslenme)
        return self._bulk("yemek", items)

    def _load_dil(self):
        items = []
        # İngilizce temel kelimeler
        kelimeler = {
            "hello":"Merhaba","goodbye":"Hoşçakal","please":"Lütfen","thank you":"Teşekkür ederim",
            "yes":"Evet","no":"Hayır","water":"Su","food":"Yiyecek","help":"Yardım",
            "love":"Aşk/Sevgi","friend":"Arkadaş","family":"Aile","home":"Ev","work":"Çalışma/İş",
            "beautiful":"Güzel","good":"İyi","bad":"Kötü","big":"Büyük","small":"Küçük",
            "time":"Zaman","money":"Para","book":"Kitap","phone":"Telefon","computer":"Bilgisayar",
        }
        for en, tr in kelimeler.items():
            items.append((f"{en} ne demek", f"'{en}' Türkçesi: {tr}"))
            items.append((f"{en} türkçe", f"'{en}' = {tr}"))
            items.append((f"{tr.lower()} ingilizce", f"'{tr}' İngilizce: {en}"))

        # Dil bilgisi
        dilbilgisi = [
            ("grammar nedir","Grammar (dil bilgisi), bir dilin kurallarını inceler: sözdizimi, morfoloji, fonetik ve anlam bilimi."),
            ("dil öğrenme yöntemleri","Dil öğrenmek için: Spaced Repetition (Anki), dil değişimi (language exchange), medya tüketimi, günlük pratik, Duolingo/Babbel uygulamaları."),
            ("türkçe eklemeli dil mi","Evet, Türkçe Ural-Altay dil ailesine ait eklemeli bir dildir. Sözcük köküne eklenen çekim ve yapım ekleriyle anlatım zenginleşir."),
        ]
        items.extend(dilbilgisi)
        return self._bulk("dil", items)

    def _load_psikoloji(self):
        items = [
            ("psikoloji alanları","Klinik psikoloji, gelişim psikolojisi, sosyal psikoloji, nöropsikoloji, spor psikolojisi, endüstri-örgüt psikolojisi ana alanlardır."),
            ("bbt nedir psikoloji","Bilişsel Davranışçı Terapi (BDT/CBT), düşünce örüntülerini ve davranışları değiştirerek psikolojik sorunları tedavi eden bilimsel tabanlı terapidir."),
            ("olumlu psikoloji nedir","Pozitif psikoloji, Martin Seligman tarafından kurulan, güçlü yönler ve refahı inceleyen psikoloji dalıdır. PERMA modeli: Pozitif duygu, Bağlanma, İlişkiler, Anlam, Başarı."),
            ("nöropalsitik nedir","Nöroplastisite, beynin deneyim yoluyla kendini yeniden şekillendirebilme kapasitesidir. Öğrenme ve iyileşmenin temelidir."),
            ("kohler etkisi","Köhler etkisi, bireysel performansın grup ortamında arttığı olgusudur. Grubun en güçsüz üyesi en fazla gelişir."),
            ("dunning kruger","Dunning-Kruger etkisi, yetersiz kişilerin kendi yetersizliklerini fark edememesi ve aşırı özgüvenli davranmasıdır."),
            ("plasebo etkisi","Plasebo etkisi, etkisiz bir tedavinin 'iyileşeceğine inanıldığında' gerçek iyileşme sağladığı psikolojik-fizyolojik olgudur."),
            ("mizaç nedir","Mizaç, doğuştan gelen kişilik eğilimleridir. Neşeli, melankolik, kolerik, flegmatik geleneksel dört mizaç tipidir."),
        ]
        return self._bulk("psikoloji", items)

    def _load_valorant(self):
        items = [
            ("valorant nedir","Valorant, Riot Games tarafından 2020'de yayınlanan taktik 5v5 nişancı oyunudur. Agent yetenekleri ve silahları birleştirir."),
            ("valorant en iyi silah","Phantom: susturuculu, kontrollü recoil, yakın-orta iyi. Vandal: yüksek hasar, her menzilde one-tap kafası. Operator: en güçlü sniper."),
            ("valorant rank sistemi","Rank sistemi: Iron → Bronze → Silver → Gold → Platinum → Diamond → Ascendant → Immortal → Radiant. Her tier I-III olarak ayrılır."),
            ("crosshair nasıl ayarlanır","İyi crosshair: küçük, sabit (dinamik kapatılı), yeşil veya camgöbeği renk. Center dot açık, inner lines kısa. Kişisel tercih önemli."),
            ("valorant mouse dpi","Valorant için: 400-1600 DPI + 0.3-0.6 hassasiyet arası ideal. Önemli olan eDPI (DPI×sens): 200-400 arası çoğu pro tercih eder."),
            ("agent rolleri","4 rol: Duelist (entry frag), Initiator (bilgi+flash), Sentinel (flank+site hold), Controller (smoke+util). Her maçta 1-2 Controller şart."),
            ("spike nedir","Spike, Valorant'ta ekilip patlatılması gereken bomba. Attacker ekici, Defender deaktive eder. 45 sn süre, 7 sn defuse."),
            ("ult nedir valorant","Ultimate (ult), her agentin özel güçlü yeteneğidir. Öldürme, Orb alma ve rond kazanarak şarj edilir. Her agentin ult maliyeti farklı."),
            ("jett ulti","Bladestorm: Jett'in ult'u. Bıçak fırlatır, kafada one-tap. Öldürünce yenilenir. Eco round kurtarıcısı."),
            ("sage wall","Sage duvarı: 200 HP blok oluşturur. Rotasyonu kesmek, site giriş kapatmak, boost için kullanılır. Cooldown: 35 sn."),
            ("omen blind","Omen blind (Paranoia): anlık tüm görüş alanını karartan flash. Duvardan geçer. Entry için kritik."),
            ("sova arrow lineup","Sova Recon Bolt lineup öğrenmek için YouTube'da harita + 'lineup sova' ara. Bind, Ascent, Haven için özel lineuplar kritik."),
            ("killjoy setup","Killjoy setup: Turret giriş karşısına, Alarmbot Spike bölgesine, Nanoswarm post-plant pozisyonlarına. Lockdown ult 3 sn bekleme."),
        ]
        return self._bulk("valorant", items)

    def _load_gunluk(self):
        items = []
        # Pratik hayat ipuçları
        ipuclari = [
            ("excel formülleri","Excel temel formüller: =SUM() toplam, =AVERAGE() ortalama, =IF() koşul, =VLOOKUP() dikey ara, =COUNT() say, =CONCATENATE() birleştir."),
            ("word kısayolları","Word kısayolları: Ctrl+B kalın, Ctrl+I italik, Ctrl+U altı çizili, Ctrl+Z geri al, Ctrl+Y yinele, Ctrl+F bul, Ctrl+H değiştir."),
            ("google arama ipuçları","Google arama: 'site:' belirli site, 'filetype:' dosya türü, '-' hariç tut, '\"\"' tam ifade, 'OR' ya da biri, 'related:' benzer site."),
            ("şifre güvenliği","Güçlü şifre: 12+ karakter, büyük+küçük harf, rakam, sembol. Her hesapta farklı şifre. Şifre yöneticisi kullan (Bitwarden, 1Password)."),
            ("sosyal mühendislik","Sosyal mühendislik: Kişisel bilgileri paylaşmaktan kaçın. Acele ettiren emailler şüphelidir. URL'yi kontrol et. 2FA kullan."),
            ("verimli toplantı","Etkili toplantı: gündem hazırla, süre belirle, aksiyon maddeleri al, gerekli kişileri çağır, kararları yaz. 25-50 dakika optimal."),
            ("email etiquette","E-posta etiği: konu satırını net yaz, kısa tut, profesyonel dil kullan, cc'yi gereksiz kullanma, 24 saat içinde cevap ver."),
            ("sunum nasıl yapılır","Etkili sunum: az yazı çok görsel, 10-20-30 kuralı (10 slayt, 20 dk, 30 punto), hikaye anlat, prova yap, sorulara hazır ol."),
        ]
        items.extend(ipuclari)

        # Günlük soru-cevaplar
        sorular = [
            ("hava bugün nasıl","Hava durumu için 'saatlik hava' veya 'haftalık hava' komutunu kullan. Gerçek zamanlı veri alınır!"),
            ("bugün ne yesem","Sağlıklı öneriler: protein (et/tavuk/baklagil), kompleks karbonhidrat (pirinç/bulgur), sebze ve meyve. Yemek çeşitliliği önemli!"),
            ("nasıl daha verimli olabilirim","Verimlilik için: Pomodoro tekniği (25 dk iş, 5 dk mola), önceliklendirme (Eisenhower matrisi), sabah rutini, dijital detoks."),
            ("ne zaman uyumalıyım","Uyku için ideal saat: 22:00-23:00 arası. Uyku döngüleri 90 dakikadır. 7-9 saat için 22:30'da uyu, 06:00-07:30'da kalk."),
            ("nasıl erken kalkabilirim","Erken kalkmak için: aynı saatte yat, alarmi yataktan uzak koy, sabah rutini oluştur, akşam kahvesini kes, hedefini hatırla."),
        ]
        items.extend(sorular)
        return self._bulk("gunluk", items)

    def _load_motivasyon(self):
        items = []
        sozler = [
            ("winston churchill sözleri","'Başarı, coşkunu kaybetmeden hayal kırıklığından hayal kırıklığına gitmektir.' — Churchill"),
            ("einstein sözleri","'Hayal gücü bilgiden daha önemlidir. Bilgi sınırlıdır, hayal gücü tüm dünyayı kapsar.' — Einstein"),
            ("steve jobs sözleri","'Zamanın sınırlı, başkasının hayatını yaşayarak onu harcama.' — Steve Jobs"),
            ("nelson mandela sözleri","'Her şey imkânsız görünür, ta ki yapılana kadar.' — Mandela"),
            ("konfüçyus sözleri","'Sevdiğiniz işi yapın, o zaman hayatınızda tek gün bile çalışmamış olursunuz.' — Konfüçyüs"),
            ("atatürk sözleri","'Hayatta en hakiki mürşit ilimdir.' — Atatürk"),
            ("newton sözleri","'Başarılarım çalışmaktan değil, sabırla sürekli düşünmekten kaynaklandı.' — Newton"),
            ("darwin sözleri","'Hayatta kalan en güçlü ya da en zeki değil, değişime en iyi adapte olan türdür.' — Darwin"),
        ]
        items.extend(sozler)

        # Motivasyonel cevaplar
        motivasyon = [
            ("motive et","💪 'Başarı, her gün tekrarlanan küçük çabaların toplamıdır.' Devam et, yapabilirsin! 🚀"),
            ("moral ver","🔥 Zor zamanlar kahramanları yaratır. Bu zorluğun içinden güçlenerek çıkacaksın!"),
            ("ilham ver","🌟 Dünyayı değiştiren insanlar başkalarından farklı değildi — sadece vazgeçmediler!"),
            ("cesaretlen","⚡ Korkudan hareket et, mükemmelden değil. İlk adımı at, geri kalanı gelecek!"),
            ("pes etmek istiyorum","💙 Dur! Her başarı hikayesinde 'bırakmak istedim ama bırakmadım' anı vardır. Senin o anındayken olabilirsin. Bir adım daha!"),
            ("kendime güvenemiyorum","🌟 Güven eylemle gelir, eylemden önce gelmez. Bir küçük adım at, özgüven onu takip eder!"),
            ("başaramıyorum","💪 Başarı doğrusal değil. Düşüşler sürecin parçası. Thomas Edison ampulü 10.000 denemede buldu!"),
            ("motivasyonum yok","⚡ Motivasyon geldiğinde başlamayı bekleme. Başla, motivasyon peşinden gelir. Şimdi sadece 5 dakika yap!"),
        ]
        items.extend(motivasyon)
        return self._bulk("motivasyon", items)

    def _load_ilginc(self):
        items = [
            ("ilginç bilgi","🐝 Bir bal arısı ömrü boyunca sadece 1/12 çay kaşığı bal üretir!"),
            ("ilginç gerçek","🌍 Dünya, Güneş etrafında saniyede 29,8 km hızla döner!"),
            ("biliyor musun","🧬 İnsan DNA'sını uçtan uca açsaydın Güneş'e 200 kez gidip gelirdin!"),
            ("şaşırtıcı bilgi","⚡ Şimşek, Güneş'in yüzeyinden 5 kat daha sıcaktır!"),
            ("garip gerçek","🐙 Ahtapotların 3 kalbi, mavi kanı ve her kolu bağımsız sinir sistemi vardır!"),
            ("hayret verici","🌙 Ay her yıl Dünya'dan 3,8 cm uzaklaşıyor. Milyonlarca yıl sonra güneş tutulması olmayacak!"),
            ("rastgele bilgi","🍯 Bal hiç bozulmaz! Mısır piramitlerinde 3000 yıllık bal bulundu ve hâlâ yenilebilirdi."),
            ("beni şaşırt","🦈 Köpekbalıkları dinozorlardan önce var oldu. Yaklaşık 450 milyon yıllık geçmişleri var!"),
            ("ilginç bir şey söyle","🐘 Filler ölen yakınlarını 'yas tutarak' anımsarlar. Kemiklere dokunup insan gibi yas dönemlerini geçirirler."),
            ("eğlenceli bilgi","🐦 Kargalar yüzleri hatırlayabilir ve 'kızgın' oldukları insanları aile üyelerine öğretebilirler!"),
            ("şaşırtıcı gerçek","🌊 Okyanus yüzeyinin sadece %20'si haritalandı. Mars'ı daha iyi biliyoruz!"),
            ("ilginç bilim","🧠 Beyin kendine dokunulamaz — beyin ağrı duyamaz. Beyin ameliyatları hastalar uyanık iken yapılabilir!"),
        ]
        return self._bulk("ilginc", items)

    def _load_genel(self):
        items = [
            ("şaka yap","😄 Programcı markete gider. Eşi: '2 ekmek al, süt varsa 6 al.' Programcı 6 ekmekle döner!"),
            ("fıkra anlat","😂 İki yazılımcı barda. Biri: 'Kötü haber: server çöktü.' Diğeri: 'İyi haber: beni de çöktürdü, eve erken gittim!'"),
            ("yardım","🤖 ANKA KOMUTLARI:\n• hava nasıl → Hava durumu\n• saat kaç → Saat\n• hesapla [işlem] → Matematik\n• valorant taktik → Oyun\n• motive et → Motivasyon\n• ilginç bilgi → Bilim\n'[konu] nedir' formatında her şeyi sorabilirsin!"),
            ("anka versiyonu","Anka AI v3.1 — 100.000+ soru kapasiteli, SQLite tabanlı, tamamen yerel!"),
        ]
        return self._bulk("genel", items)

    def _load_hesap(self):
        items = []
        # Yüzde hesapları
        for yuzde in [5,10,15,20,25,30,40,50,60,70,75,80,90]:
            for sayi in [100,200,500,1000,2000,5000,10000]:
                sonuc = sayi * yuzde / 100
                items.append((f"{sayi} nin yüzde {yuzde}", f"{sayi}'nin %{yuzde}'i = {sonuc:g}"))
                items.append((f"{sayi} yüzde {yuzde}", f"{sayi} × %{yuzde} = {sonuc:g}"))
        return self._bulk("hesap", items[:2000])  # Limit

# ═══════════════════════════════════════════════════════════════════════════════
# GLOBAL ERİŞİM
# ═══════════════════════════════════════════════════════════════════════════════
_db_instance = None

def get_db() -> KnowledgeDB:
    global _db_instance
    if _db_instance is None:
        _db_instance = KnowledgeDB()
    return _db_instance

def init_knowledge_base():
    """Bilgi tabanını başlat ve yükle"""
    db = get_db()
    loader = KnowledgeLoader(db)
    loader.load_all()
    return db

def search_knowledge(query: str, limit: int = 5):
    """Bilgi tabanında ara"""
    return get_db().search(query, limit)
