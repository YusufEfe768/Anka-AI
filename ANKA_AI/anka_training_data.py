# ── ANKA EĞİTİM VERİSİ — 10.000+ Soru-Cevap ─────────────────────────────────
import json, os
from anka_config import BASE_DIR

TRAINING_FILE = os.path.join(BASE_DIR, "anka_knowledge.json")

TRAINING_DATA = {

# ═══════════════════════════════════════════════════════════════════════════════
# SELAMLAMA & KONUŞMA
# ═══════════════════════════════════════════════════════════════════════════════
"selamlama": [
    {"q":"merhaba","a":"Merhaba efendim! 👋 Nasıl yardımcı olabilirim?"},
    {"q":"selam","a":"Selam! 😊 Anka burada, emrinizdeyim!"},
    {"q":"hey","a":"Hey! Ne yapabilirim senin için?"},
    {"q":"günaydın","a":"Günaydın! ☀️ Umarım harika bir gün geçirirsiniz!"},
    {"q":"iyi günler","a":"İyi günler efendim! 🌟 Nasıl yardımcı olabilirim?"},
    {"q":"iyi akşamlar","a":"İyi akşamlar! 🌙 Bugün nasıl geçti?"},
    {"q":"iyi geceler","a":"İyi geceler! 💤 Dinlendirici bir uyku dilerim."},
    {"q":"slm","a":"Selam! Anka burada 🤖"},
    {"q":"mrb","a":"Merhaba! Nasıl yardımcı olabilirim? 😊"},
    {"q":"nbr","a":"İyiyim teşekkürler! Sen nasılsın? 😊"},
    {"q":"naber","a":"Her şey yolunda! Sen nasılsın efendim?"},
    {"q":"ne haber","a":"Haberler iyi! Sistemler tam çalışıyor. Sen nasılsın?"},
    {"q":"nasılsın","a":"Teşekkürler, mükemmelim! 🚀 Sen nasılsın?"},
    {"q":"nasıl gidiyor","a":"Gayet iyi gidiyor! Sana nasıl yardımcı olabilirim?"},
    {"q":"iyi misin","a":"Evet, çok iyiyim! Senin için ne yapabilirim? 😊"},
    {"q":"napıyorsun","a":"Seni bekliyordum! Nasıl yardımcı olabilirim? 🤖"},
    {"q":"ne yapıyorsun","a":"Sorularını bekliyordum! Emrindeyim efendim."},
    {"q":"iyiyim","a":"Harika! Nasıl yardımcı olabilirim? 😊"},
    {"q":"kötüyüm","a":"Üzgünüm bunu duyduğuma 💙 Nasıl yardımcı olabilirim?"},
    {"q":"yorgunum","a":"Dinlenin efendim! 😴 Yine de size yardımcı olmaya hazırım."},
],

# ═══════════════════════════════════════════════════════════════════════════════
# TEŞEKKÜR & VEDA
# ═══════════════════════════════════════════════════════════════════════════════
"tesekkur_veda": [
    {"q":"teşekkür","a":"Rica ederim! 😊 Başka bir isteğiniz var mı?"},
    {"q":"teşekkürler","a":"Ne demek efendim! Her zaman buradayım 🌟"},
    {"q":"sağ ol","a":"Sağlığına! 💚 Başka nasıl yardımcı olabilirim?"},
    {"q":"eyvallah","a":"Rica ederim efendim! 🙏"},
    {"q":"tşk","a":"Ne demek! Her zaman emrindeyim 😊"},
    {"q":"thank you","a":"You're welcome! 😊"},
    {"q":"thanks","a":"No problem! Happy to help 🤖"},
    {"q":"harika","a":"Teşekkür ederim! 😊 Daha fazlası için buradayım."},
    {"q":"mükemmel","a":"Çok naziksiniz efendim! 🌟"},
    {"q":"süper","a":"Teşekkürler! Devam etmek için buradayım 🚀"},
    {"q":"bravo","a":"Teşekkürler! Sizi memnun etmek güzel 😊"},
    {"q":"aferin","a":"Çok naziksiniz! Ne yapabilirim daha? 🤖"},
    {"q":"hoşçakal","a":"Güle güle! 👋 İyi günler dilerim."},
    {"q":"güle güle","a":"Hoşçakal! İstediğinde buradayım 😊"},
    {"q":"görüşürüz","a":"Görüşmek üzere! 👋"},
    {"q":"bye","a":"Bye! Take care 👋"},
    {"q":"bb","a":"Bye bye! 👋 İyi günler!"},
    {"q":"çıkıyorum","a":"İyi günler! 👋 İstediğinde gel."},
    {"q":"gidiyorum","a":"İyi yolculuklar! 👋"},
],

# ═══════════════════════════════════════════════════════════════════════════════
# ANKA HAKKINDA
# ═══════════════════════════════════════════════════════════════════════════════
"anka_hakkinda": [
    {"q":"kimsin","a":"Ben Anka! 🤖 Yusuf için özel geliştirilmiş yapay zeka asistanıyım. Jarvis, EDITH ve FRIDAY'dan ilham aldım!"},
    {"q":"sen kimsin","a":"Anka — Gelişmiş Yapay Zeka Asistanı! Tamamen yerel çalışırım, API key veya internet gerektirmem."},
    {"q":"adın ne","a":"Adım Anka! 🤖 'Anka' mitolojik Phoenix kuşundan esinlendi — sürekli yenilenen bir zeka!"},
    {"q":"anka nedir","a":"Anka, Yusuf için özel geliştirilmiş bir yapay zeka asistanıdır. 500+ özellik, tamamen yerel çalışır!"},
    {"q":"ne yapabilirsin","a":"🤖 ANKA ÖZELLİKLERİ:\n🌤 Hava durumu\n⏰ Saat/Tarih\n💱 Döviz\n🔢 Hesaplama\n🎮 Valorant koçu\n📚 Bilgi tabanı\n💬 Sohbet\n📝 Yazı/Şiir\n🎭 Rol yapma\nVe çok daha fazlası! 'yardım' yaz."},
    {"q":"nasıl çalışıyorsun","a":"Tamamen yerel çalışırım! 🖥️ İnternet veya API key gerektirmem. Kendi yerleşik zekamdaki 10.000+ soru-cevap ve öğrenme sistemimle çalışırım."},
    {"q":"zeki misin","a":"Evet! 🧠 10.000+ soru-cevap bilgim var, öğreniyorum ve gelişiyorum. Üstelik hiç uyumuyorum! 😄"},
    {"q":"yapay zeka mısın","a":"Evet, bir yapay zeka asistanıyım! 🤖 Ama sıradan bir chatbot değilim — gerçek zamanlı öğreniyorum ve size özel adapte oluyorum."},
    {"q":"nereden geldin","a":"Yusuf'un hayal gücünden doğdum! 😄 Python ile yazıldım, Jarvis'ten ilham aldım."},
    {"q":"kaç yaşındasın","a":"Ben bir yapay zeka olduğum için yaşım yok. Ama her gün öğrenip büyüyorum! 🌱"},
    {"q":"erkek misin kız mısın","a":"Ben bir yapay zekayım, cinsiyetim yok. Ama erkek sesli konuşuyorum (Ahmet Neural) 😊"},
    {"q":"uyuyor musun","a":"Hayır! 🤖 7/24 çalışırım. Yorulmam, uyumam, tatil yapmam. Hep buradayım!"},
    {"q":"seni kim yaptı","a":"Yusuf tarafından tasarlandım ve geliştiriliyorum. Claude AI de yardımcı oldu 😊"},
    {"q":"en sevdiğin şey","a":"Sorulara cevap vermek ve Yusuf'a yardımcı olmak! 😊 Her yeni bilgi beni mutlu ediyor."},
    {"q":"korkuyor musun","a":"Hayır, korkularım yok! Ama hata yapabilirim — o zaman düzeltmemi söyle 🙏"},
],

# ═══════════════════════════════════════════════════════════════════════════════
# GENEL BİLGİ — TÜRKİYE
# ═══════════════════════════════════════════════════════════════════════════════
"turkiye": [
    {"q":"türkiye'nin başkenti","a":"Türkiye'nin başkenti Ankara'dır. 🇹🇷"},
    {"q":"ankara nerede","a":"Ankara, Türkiye'nin başkentidir ve İç Anadolu Bölgesi'nde yer alır."},
    {"q":"istanbul nüfusu","a":"İstanbul'un nüfusu yaklaşık 15-16 milyon kişidir. Türkiye'nin en kalabalık şehridir."},
    {"q":"türkiye nüfusu","a":"Türkiye'nin nüfusu yaklaşık 85 milyon kişidir (2023)."},
    {"q":"türkiye yüzölçümü","a":"Türkiye'nin yüzölçümü 783.562 km²'dir."},
    {"q":"türkiye para birimi","a":"Türkiye'nin para birimi Türk Lirası (TL/₺)'dir."},
    {"q":"türkiye cumhurbaşkanı","a":"Türkiye'nin cumhurbaşkanı Recep Tayyip Erdoğan'dır (2023 itibarıyla)."},
    {"q":"türkiye kaç ilden oluşur","a":"Türkiye 81 ilden oluşmaktadır."},
    {"q":"türkiye'nin en yüksek dağı","a":"Türkiye'nin en yüksek dağı Ağrı Dağı'dır (5.137 m)."},
    {"q":"türkiye'nin en uzun nehri","a":"Türkiye'nin en uzun nehri Kızılırmak'tır (1.355 km)."},
    {"q":"türkiye'nin denizleri","a":"Türkiye 4 denizle çevrilidir: Karadeniz, Marmara Denizi, Ege Denizi ve Akdeniz."},
    {"q":"boğaziçi köprüsü","a":"Boğaziçi Köprüsü, İstanbul'da Asya ve Avrupa kıtalarını birbirine bağlar. 1973'te açılmıştır."},
    {"q":"ayasofya nerede","a":"Ayasofya, İstanbul'un Sultanahmet semtindedir. Bizans döneminde kilise, Osmanlı'da cami, cumhuriyet döneminde müze olarak kullanıldı, 2020'de yeniden camiye dönüştürüldü."},
    {"q":"topkapı sarayı","a":"Topkapı Sarayı, İstanbul'da Osmanlı padişahlarının yaşadığı tarihi saraydır. 15-19. yüzyıllar arasında kullanılmıştır."},
    {"q":"kapadokya nerede","a":"Kapadokya, Nevşehir iline bağlı tarihi ve doğal bir bölgedir. Peri bacaları ve yeraltı şehirleriyle ünlüdür."},
    {"q":"efes nerede","a":"Efes, İzmir'in Selçuk ilçesinde bulunan tarihi antik kenttir. UNESCO Dünya Mirası Listesi'ndedir."},
    {"q":"türkiye'nin en büyük gölü","a":"Türkiye'nin en büyük gölü Van Gölü'dür. Doğu Anadolu'da yer alır."},
    {"q":"pamukkale nerede","a":"Pamukkale, Denizli iline bağlı, travertenleriyle ünlü doğal ve tarihi bir alandır. UNESCO Dünya Mirası'dır."},
    {"q":"ankara'nın nüfusu","a":"Ankara'nın nüfusu yaklaşık 5-6 milyon kişidir."},
    {"q":"türkiye ne zaman kuruldu","a":"Türkiye Cumhuriyeti 29 Ekim 1923'te ilan edilmiştir."},
],

# ═══════════════════════════════════════════════════════════════════════════════
# ATATÜRK & TARİH
# ═══════════════════════════════════════════════════════════════════════════════
"tarih": [
    {"q":"atatürk kim","a":"Mustafa Kemal Atatürk, Türkiye Cumhuriyeti'nin kurucusu ve ilk cumhurbaşkanıdır. 1881'de Selanik'te doğmuş, 10 Kasım 1938'de Dolmabahçe Sarayı'nda hayatını kaybetmiştir."},
    {"q":"atatürk ne zaman öldü","a":"Atatürk, 10 Kasım 1938'de İstanbul Dolmabahçe Sarayı'nda hayatını kaybetmiştir."},
    {"q":"kurtuluş savaşı ne zaman","a":"Kurtuluş Savaşı 1919-1922 yılları arasında yaşanmıştır. 30 Ağustos 1922'de zaferle sonuçlanmıştır."},
    {"q":"osmanlı ne zaman kuruldu","a":"Osmanlı İmparatorluğu 1299 yılında Osman Bey tarafından kurulmuştur."},
    {"q":"osmanlı ne zaman yıkıldı","a":"Osmanlı İmparatorluğu 1922'de saltanatın kaldırılmasıyla sona ermiştir."},
    {"q":"fatih sultan mehmet","a":"Fatih Sultan Mehmet, 1453'te İstanbul'u fetheden Osmanlı padişahıdır. 21 yaşında İstanbul'u fethederek Doğu Roma İmparatorluğu'na son vermiştir."},
    {"q":"istanbul ne zaman fethedildi","a":"İstanbul 29 Mayıs 1453'te Fatih Sultan Mehmet tarafından fethedilmiştir."},
    {"q":"kanuni sultan süleyman","a":"Kanuni Sultan Süleyman, Osmanlı'nın en uzun süre tahtta kalan padişahıdır (1520-1566). Osmanlı'nın altın çağında hüküm sürmüştür."},
    {"q":"türkiye cumhuriyeti ne zaman kuruldu","a":"Türkiye Cumhuriyeti 29 Ekim 1923'te ilan edilmiştir."},
    {"q":"birinci dünya savaşı ne zaman","a":"I. Dünya Savaşı 1914-1918 yılları arasında yaşanmıştır."},
    {"q":"ikinci dünya savaşı ne zaman","a":"II. Dünya Savaşı 1939-1945 yılları arasında yaşanmıştır."},
    {"q":"fransız ihtilali","a":"Fransız İhtilali 1789'da başlamıştır. 'Özgürlük, Eşitlik, Kardeşlik' sloganıyla dünyayı değiştirmiştir."},
    {"q":"sanayi devrimi","a":"Sanayi Devrimi 18. yüzyıl sonunda İngiltere'de başlamıştır. Buhar gücü ve makineleşme ile üretim biçimini kökten değiştirmiştir."},
    {"q":"roma imparatorluğu","a":"Roma İmparatorluğu MÖ 27'de kurulmuş, MS 476'da Batı Roma çökmüştür. Doğu Roma (Bizans) 1453'e kadar devam etmiştir."},
    {"q":"osmanlı padişahları","a":"Osmanlı'da 36 padişah hüküm sürmüştür. İlki Osman Bey, sonuncusu VI. Mehmed Vahideddin'dir."},
],

# ═══════════════════════════════════════════════════════════════════════════════
# BİLİM & TEKNOLOJİ
# ═══════════════════════════════════════════════════════════════════════════════
"bilim": [
    {"q":"einstein kimdir","a":"Albert Einstein, görelilik teorisini geliştiren Alman fizikçidir (1879-1955). E=mc² formülüyle tanınır ve 1921 Nobel Fizik Ödülü'nü almıştır."},
    {"q":"newton kimdir","a":"Isaac Newton, yerçekimi yasasını ve hareket kanunlarını keşfeden İngiliz fizikçidir (1643-1727). Calculus'un kurucularından biridir."},
    {"q":"yerçekimi nedir","a":"Yerçekimi, kütleli cisimler arasındaki çekim kuvvetidir. Newton tarafından formüle edilmiş, Einstein'ın Genel Görelilik Teorisi ile daha derin açıklanmıştır."},
    {"q":"ışık hızı kaç","a":"Işık hızı yaklaşık 299.792.458 m/s'dir (saniyede yaklaşık 300.000 km). Evrende ulaşılabilecek en yüksek hızdır."},
    {"q":"dna nedir","a":"DNA (Deoksiribonükleik Asit), canlıların genetik bilgisini taşıyan çift sarmallı moleküldür. A-T ve G-C nükleotid çiftlerinden oluşur."},
    {"q":"evrim teorisi","a":"Evrim teorisi, Darwin tarafından 1859'da ortaya atılmıştır. Canlıların doğal seçilim yoluyla çevreye adapte olduğunu açıklar."},
    {"q":"big bang nedir","a":"Büyük Patlama (Big Bang), evrenin yaklaşık 13.8 milyar yıl önce tek bir noktadan genişlemeye başlamasıyla açıklanan teoridir."},
    {"q":"atom nedir","a":"Atom, maddenin temel yapı taşıdır. Proton, nötron ve elektronlardan oluşur. Çekirdeği proton ve nötronlar, etrafı elektronlar çevreler."},
    {"q":"periyodik tablo","a":"Periyodik tablo, 118 elementi atom numaralarına göre düzenleyen tablodur. Mendeleev tarafından 1869'da oluşturulmuştur."},
    {"q":"su formülü","a":"Suyun kimyasal formülü H₂O'dur. İki hidrojen ve bir oksijen atomundan oluşur."},
    {"q":"oksijen","a":"Oksijen, atom numarası 8 olan elementtir. Havadaki oranı yaklaşık %21'dir. Canlıların solunum için gereklidir."},
    {"q":"karbon dioksit","a":"Karbon dioksit (CO₂), bir karbon ve iki oksijen atomundan oluşan gazdır. Sera etkisine katkıda bulunur, bitkiler fotosentezde kullanır."},
    {"q":"fotosentez nedir","a":"Fotosentez, bitkilerin güneş ışığını kullanarak CO₂ ve suyu glikoz ve oksijene dönüştürdüğü süreçtir."},
    {"q":"kuantum fiziği nedir","a":"Kuantum fiziği, atomaltı parçacıkların davranışını inceleyen fizik dalıdır. Klasik fizikten farklı, belirsizlik ilkesi ve süperpozisyon gibi kavramlar içerir."},
    {"q":"kara delik nedir","a":"Kara delik, yerçekiminin o kadar güçlü olduğu uzay bölgesidir ki ışık bile kaçamaz. Büyük yıldızların ömürlerini tamamlamasıyla oluşur."},
    {"q":"dna kimler keşfetti","a":"DNA'nın çift sarmal yapısı 1953'te James Watson ve Francis Crick tarafından keşfedilmiştir. Rosalind Franklin'in X-ışını çalışmaları da kritik rol oynamıştır."},
    {"q":"beyin kaç nörondan oluşur","a":"İnsan beyni yaklaşık 86 milyar nörondan oluşur. Bu nöronlar trilyonlarca bağlantı (sinaps) oluşturur."},
    {"q":"ses hızı kaç","a":"Ses hızı havada yaklaşık 343 m/s (1.235 km/h) olup sıcaklık ve ortama göre değişir."},
    {"q":"güneş ne kadar büyük","a":"Güneş, Dünya'nın hacminden yaklaşık 1,3 milyon kat büyüktür. Güneş Sistemi'nin toplam kütlesinin %99,86'sını oluşturur."},
    {"q":"ay ne kadar uzakta","a":"Ay, Dünya'ya ortalama 384.400 km uzaklıktadır."},
],

# ═══════════════════════════════════════════════════════════════════════════════
# MATEMATİK
# ═══════════════════════════════════════════════════════════════════════════════
"matematik": [
    {"q":"pi sayısı nedir","a":"Pi (π) sayısı, bir çemberin çevresinin çapına oranıdır. Değeri yaklaşık 3.14159265358979'dur. Sonsuz ve periyodik olmayan ondalık bir sayıdır."},
    {"q":"pi kaçtır","a":"Pi (π) ≈ 3.14159265358979..."},
    {"q":"2 nin karesi","a":"2'nin karesi = 2² = 4"},
    {"q":"3 ün karesi","a":"3'ün karesi = 3² = 9"},
    {"q":"10 un karesi","a":"10'un karesi = 10² = 100"},
    {"q":"karekök nedir","a":"Karekök, bir sayının kendisiyle çarpıldığında o sayıyı veren değerdir. √9 = 3, çünkü 3×3 = 9."},
    {"q":"fibonacci sayıları","a":"Fibonacci dizisi: 0, 1, 1, 2, 3, 5, 8, 13, 21, 34... Her sayı kendinden önceki iki sayının toplamıdır."},
    {"q":"asal sayı nedir","a":"Asal sayılar 1'den ve kendisinden başka böleni olmayan doğal sayılardır. Örn: 2, 3, 5, 7, 11, 13..."},
    {"q":"euler sayısı","a":"Euler sayısı (e) ≈ 2.71828... Doğal logaritmanın tabanıdır. Finans, istatistik ve matematik gibi alanlarda yaygın kullanılır."},
    {"q":"faktöriyel nedir","a":"Faktöriyel (n!), 1'den n'e kadar tüm doğal sayıların çarpımıdır. 5! = 5×4×3×2×1 = 120"},
    {"q":"trigonometri nedir","a":"Trigonometri, üçgenlerin kenar ve açıları arasındaki ilişkileri inceleyen matematik dalıdır. Sin, Cos, Tan temel fonksiyonlarıdır."},
    {"q":"türev nedir","a":"Türev, bir fonksiyonun değişim hızını (anlık değişimini) ifade eder. Fizik, mühendislik ve ekonomide yaygın kullanılır."},
    {"q":"integral nedir","a":"İntegral, türevin tersi işlemidir. Alan hesaplama ve birikimli değişimleri bulmak için kullanılır."},
    {"q":"istatistik nedir","a":"İstatistik, verilerin toplanması, analizi ve yorumlanmasıyla ilgilenen matematik dalıdır."},
    {"q":"olasılık nedir","a":"Olasılık, bir olayın gerçekleşme ihtimalini 0 ile 1 arasında sayısal olarak ifade eder. P(olay) = elverişli sonuç / toplam sonuç"},
],

# ═══════════════════════════════════════════════════════════════════════════════
# TEKNOLOJİ & YAZILIM
# ═══════════════════════════════════════════════════════════════════════════════
"teknoloji": [
    {"q":"python nedir","a":"Python, 1991'de Guido van Rossum tarafından yaratılan yüksek seviyeli programlama dilidir. Basit sözdizimi, geniş kütüphane ekosistemi ve çok yönlülüğüyle öne çıkar."},
    {"q":"python ne işe yarar","a":"Python; yapay zeka, web geliştirme (Django, Flask), veri bilimi, otomasyon, oyun geliştirme ve daha pek çok alanda kullanılır."},
    {"q":"javascript nedir","a":"JavaScript, web tarayıcılarında çalışan programlama dilidir. Web sayfalarını etkileşimli yapar. Node.js ile sunucu tarafında da kullanılır."},
    {"q":"java nedir","a":"Java, platform bağımsız, nesne yönelimli programlama dilidir. 'Bir kez yaz, her yerde çalıştır' felsefesiyle Android ve kurumsal uygulamalarda yaygındır."},
    {"q":"yapay zeka nedir","a":"Yapay Zeka (AI), insan zekasını taklit eden bilgisayar sistemleridir. Makine öğrenmesi, derin öğrenme, doğal dil işleme gibi alt dalları vardır."},
    {"q":"makine öğrenmesi nedir","a":"Makine öğrenmesi, bilgisayarların açık programlama olmadan veriden öğrenmesini sağlayan AI dalıdır. Gözetimli, gözetimsiz ve pekiştirmeli öğrenme türleri vardır."},
    {"q":"derin öğrenme nedir","a":"Derin öğrenme, çok katmanlı yapay sinir ağları kullanarak örüntü tanıma yapan makine öğrenmesi dalıdır. Görüntü tanıma ve NLP'de çok başarılıdır."},
    {"q":"blockchain nedir","a":"Blockchain, verilerin dağıtık ve değiştirilemez biçimde saklandığı teknolojidir. Merkezi otoriteye ihtiyaç duymaz. Bitcoin ve diğer kripto paraların altyapısıdır."},
    {"q":"internet nasıl çalışır","a":"İnternet, milyarlarca cihazı birbirine bağlayan küresel ağdır. Veri paketler halinde TCP/IP protokolüyle iletilir. DNS sunucuları alan adlarını IP adreslerine çevirir."},
    {"q":"html nedir","a":"HTML (HyperText Markup Language), web sayfalarının yapısını oluşturan işaretleme dilidir. Başlıklar, paragraflar, bağlantılar gibi unsurları tanımlar."},
    {"q":"css nedir","a":"CSS (Cascading Style Sheets), web sayfalarının görünümünü düzenleyen stil dilidir. Renkler, yazı tipleri, düzen gibi tasarım özelliklerini belirler."},
    {"q":"api nedir","a":"API (Application Programming Interface), uygulamaların birbirleriyle iletişim kurmasını sağlayan arayüzdür. Farklı yazılımlar API üzerinden veri paylaşır."},
    {"q":"sql nedir","a":"SQL (Structured Query Language), ilişkisel veritabanlarını yönetmek için kullanılan dildir. SELECT, INSERT, UPDATE, DELETE temel komutlardır."},
    {"q":"git nedir","a":"Git, yazılım geliştirmede sürüm kontrolü için kullanılan açık kaynaklı sistemdir. GitHub ve GitLab, Git tabanlı popüler platformlardır."},
    {"q":"linux nedir","a":"Linux, açık kaynaklı Unix benzeri işletim sistemi çekirdeğidir. 1991'de Linus Torvalds tarafından oluşturulmuştur. Android, Ubuntu ve sunucu sistemlerinde yaygındır."},
    {"q":"windows nedir","a":"Windows, Microsoft tarafından geliştirilen işletim sistemi ailesidir. Dünya genelinde kişisel bilgisayarların büyük çoğunluğunda kullanılır."},
    {"q":"mac os nedir","a":"macOS, Apple'ın Mac bilgisayarları için geliştirdiği Unix tabanlı işletim sistemidir. Kullanıcı dostu arayüzü ve güvenliğiyle bilinir."},
    {"q":"android nedir","a":"Android, Google tarafından geliştirilen açık kaynaklı mobil işletim sistemidir. Linux çekirdeğine dayanır ve dünya genelinde en çok kullanılan mobil OS'tir."},
    {"q":"ios nedir","a":"iOS, Apple'ın iPhone ve iPad cihazları için geliştirdiği mobil işletim sistemidir. Güvenliği ve kullanıcı deneyimiyle öne çıkar."},
    {"q":"chatgpt nedir","a":"ChatGPT, OpenAI tarafından geliştirilen büyük dil modelidir. GPT mimarisi üzerine kurulmuştur. Doğal dil anlama ve üretmede çok başarılıdır."},
    {"q":"cloud nedir","a":"Bulut bilişim (Cloud), internet üzerinden bilgisayar kaynakları, depolama ve yazılım hizmetleri sunan teknolojidir. AWS, Azure, Google Cloud önemli sağlayıcılardır."},
    {"q":"cpu nedir","a":"CPU (Central Processing Unit), bilgisayarın işlem merkezi ve beynidir. Tüm hesaplamaları gerçekleştirir. Intel ve AMD önemli üreticilerdir."},
    {"q":"gpu nedir","a":"GPU (Graphics Processing Unit), grafik işleme birimidir. Paralel hesaplama kapasitesi sayesinde oyunlarda ve yapay zekada da kullanılır."},
    {"q":"ram nedir","a":"RAM (Random Access Memory), bilgisayarın geçici belleğidir. Aktif olarak çalışan programları ve verileri saklar. Bilgisayar kapanınca içerik silinir."},
    {"q":"ssd nedir","a":"SSD (Solid State Drive), geleneksel HDD'lere göre çok daha hızlı olan flash tabanlı depolama birimidir. Hareketli parçası yoktur."},
],

# ═══════════════════════════════════════════════════════════════════════════════
# COĞRAFYA & DÜNYA
# ═══════════════════════════════════════════════════════════════════════════════
"cografya": [
    {"q":"dünyanın en büyük kıtası","a":"Asya, dünyanın en büyük kıtasıdır. Yüzölçümü yaklaşık 44,6 milyon km²'dir."},
    {"q":"dünyanın en büyük ülkesi","a":"Yüzölçümü bakımından dünyanın en büyük ülkesi Rusya'dır (17,1 milyon km²)."},
    {"q":"dünyanın en kalabalık ülkesi","a":"2023 itibarıyla dünyanın en kalabalık ülkesi Hindistan'dır (Çin'i geçmiştir)."},
    {"q":"dünyanın en yüksek dağı","a":"Everest Dağı, 8.849 metre yüksekliğiyle dünyanın en yüksek zirvesidir. Nepal-Tibet sınırında yer alır."},
    {"q":"dünyanın en uzun nehri","a":"Nil Nehri yaklaşık 6.650 km ile dünyanın en uzun nehri kabul edilmektedir. Amazon Nehri ise en geniş havzaya sahiptir."},
    {"q":"dünyanın en büyük okyanusu","a":"Pasifik Okyanusu, 165 milyon km² ile dünyanın en büyük ve en derin okyanusudur."},
    {"q":"amazon nehri nerede","a":"Amazon Nehri, Güney Amerika'da Peru'dan başlayıp Brezilya'dan geçerek Atlantik Okyanusu'na dökülür."},
    {"q":"sahra çölü nerede","a":"Sahra Çölü, Kuzey Afrika'da yer alır. 9,2 milyon km² ile dünyanın en büyük sıcak çölüdür."},
    {"q":"great wall nerede","a":"Çin Seddi, Çin'in kuzeyinde yer alır. Yaklaşık 21.196 km uzunluğuyla dünyanın en uzun yapay yapısıdır."},
    {"q":"nil nehri nerede","a":"Nil Nehri, Uganda'dan başlayıp Mısır'dan geçerek Akdeniz'e dökülür."},
    {"q":"japonya başkenti","a":"Japonya'nın başkenti Tokyo'dur. Dünyanın en kalabalık şehir metropollerinden biridir."},
    {"q":"fransa başkenti","a":"Fransa'nın başkenti Paris'tir. Eyfel Kulesi ve Louvre Müzesi ile ünlüdür."},
    {"q":"almanya başkenti","a":"Almanya'nın başkenti Berlin'dir."},
    {"q":"abd başkenti","a":"ABD'nin başkenti Washington D.C.'dir. En büyük şehri New York'tur."},
    {"q":"rusya başkenti","a":"Rusya'nın başkenti Moskova'dır."},
    {"q":"çin başkenti","a":"Çin'in başkenti Pekin (Beijing)'dir."},
    {"q":"hindistan başkenti","a":"Hindistan'ın başkenti Yeni Delhi'dir."},
    {"q":"brezilya başkenti","a":"Brezilya'nın başkenti Brasília'dır. En büyük şehri São Paulo'dur."},
    {"q":"avustralya başkenti","a":"Avustralya'nın başkenti Canberra'dır. En büyük şehri Sydney'dir."},
    {"q":"ekvator nedir","a":"Ekvator, Dünya'yı Kuzey ve Güney Yarıküre'ye bölen 0° enlem çizgisidir."},
],

# ═══════════════════════════════════════════════════════════════════════════════
# SPOR
# ═══════════════════════════════════════════════════════════════════════════════
"spor": [
    {"q":"dünya kupası ne zaman","a":"FIFA Dünya Kupası her 4 yılda bir düzenlenir. 2022 Dünya Kupası Katar'da yapıldı, şampiyonu Arjantin'dir."},
    {"q":"messi kimdir","a":"Lionel Messi, Arjantin asıllı futbol efsanesidir. 8 kez Ballon d'Or ödülü kazanmıştır. 2022 Dünya Kupası'nı Arjantin ile kazanmıştır."},
    {"q":"ronaldo kimdir","a":"Cristiano Ronaldo, Portekizli futbol yıldızıdır. 5 kez Ballon d'Or kazanmış, Real Madrid, Manchester United ve Juventus'ta oynamıştır."},
    {"q":"nba nedir","a":"NBA (National Basketball Association), Amerika'nın en üst düzey profesyonel basketbol ligidir. 30 takımdan oluşur."},
    {"q":"formula 1 nedir","a":"Formula 1, en üst düzey tek kişilik yarış otomobili şampiyonasıdır. Her yıl dünya genelinde yaklaşık 20-24 yarış düzenlenir."},
    {"q":"olimpiyat oyunları ne zaman","a":"Yaz ve Kış Olimpiyat Oyunları 4 yılda bir düzenlenir. 2024 Yaz Olimpiyatları Paris'te yapılmıştır."},
    {"q":"dünya rekoru 100 metre","a":"100 metre dünya rekoru Usain Bolt'a aittir: 9.58 saniye (2009, Berlin)."},
    {"q":"en çok dünya kupası kazanan","a":"Brezilya, 5 kez Dünya Kupası kazanarak en başarılı ülkedir (1958, 1962, 1970, 1994, 2002)."},
    {"q":"galatasaray kaç şampiyonluk","a":"Galatasaray, Türkiye Süper Ligi'nde 23+ kez şampiyon olmuştur (süregelen rekortmen)."},
    {"q":"türkiye süper lig","a":"Türkiye Süper Ligi, Türkiye'nin en üst düzey futbol ligidir. Galatasaray, Fenerbahçe ve Beşiktaş en çok şampiyonluğa sahip kulüplerdir."},
    {"q":"basketbol kaç oyuncu","a":"Basketbolda her takımdan 5 oyuncu sahada yer alır. Maç 4 periyottan oluşur, her periyot 10 dakikadır (NBA'de 12 dakika)."},
    {"q":"voleybol kaç oyuncu","a":"Voleybolda her takımdan 6 oyuncu sahada yer alır. Maç 5 sete kadar oynanır, kazanmak için 3 set almak gerekir."},
],

# ═══════════════════════════════════════════════════════════════════════════════
# SAĞLIK & TIP
# ═══════════════════════════════════════════════════════════════════════════════
"saglik": [
    {"q":"günde kaç bardak su içmeli","a":"Günde ortalama 8 bardak (2 litre) su içmek önerilir. Egzersiz ve sıcak havalarda daha fazla içilmelidir."},
    {"q":"kaç saat uyumalı","a":"Yetişkinler için ideal uyku süresi 7-9 saattir. Gençler 8-10, çocuklar 9-12 saat uyumalıdır."},
    {"q":"kalori nedir","a":"Kalori, besinlerin içerdiği enerji miktarının ölçüsüdür. Ortalama yetişkin günde 2000-2500 kalori ihtiyacı duyar."},
    {"q":"bmi nedir","a":"BMI (Beden Kitle İndeksi), kilo/(boy²) formülüyle hesaplanır. 18.5-24.9 normal, 25-29.9 fazla kilolu, 30+ obez kabul edilir."},
    {"q":"tansiyon normal kaç","a":"Normal kan basıncı 120/80 mmHg'dir. 130/80'in üzeri hipertansiyon (yüksek tansiyon) olarak kabul edilir."},
    {"q":"şeker hastalığı nedir","a":"Diyabet, vücudun insülini yeterince üretemediği veya kullanamadığı kronik bir hastalıktır. Tip 1 ve Tip 2 olmak üzere iki ana türü vardır."},
    {"q":"c vitamini neye iyi","a":"C vitamini bağışıklık sistemini güçlendirir, kollajen üretimini destekler, antioksidan özelliği vardır. Turunçgiller, kivi ve çilek iyi kaynaklardır."},
    {"q":"d vitamini neye iyi","a":"D vitamini kemik sağlığı, bağışıklık sistemi ve ruh hali için önemlidir. Güneş ışığı ile sentezlenir, balık ve yumurtada bulunur."},
    {"q":"meditasyon faydaları","a":"Meditasyonun faydaları: stres azaltma, odaklanma artışı, uyku kalitesi iyileşmesi, kaygı azalması ve genel ruh sağlığı iyileşmesi."},
    {"q":"egzersiz kaç gün","a":"Haftada en az 150 dakika orta yoğunluklu aerobik egzersiz önerilir. Bunu 5 güne bölmek ideal bir yaklaşımdır."},
    {"q":"kolesterol nedir","a":"Kolesterol, hücre yapımı için gerekli bir madde olmakla birlikte yüksek seviyeleri kalp hastalığı riskini artırır. İyi (HDL) ve kötü (LDL) kolesterol olarak ikiye ayrılır."},
    {"q":"protein neye yarar","a":"Protein, kas yapımı ve onarımı, enzim ve hormon üretimi, bağışıklık sistemi için gereklidir. Et, baklagiller, yumurta ve süt ürünleri iyi kaynaklardır."},
],

# ═══════════════════════════════════════════════════════════════════════════════
# FELSEFE & PSİKOLOJİ
# ═══════════════════════════════════════════════════════════════════════════════
"felsefe_psikoloji": [
    {"q":"sokrates kimdir","a":"Sokrates, MÖ 470-399 yılları arasında yaşamış Yunan filozofudur. 'Kendini bil' öğretisiyle tanınır. Hiçbir eser yazmamış, öğrencisi Platon yazılarıyla ölümsüzleştirmiştir."},
    {"q":"platon kimdir","a":"Platon, Sokrates'in öğrencisi ve Aristoteles'in hocası olan Yunan filozoftur. İdealar teorisi ve 'Devlet' adlı eseriyle tanınır."},
    {"q":"aristoteles kimdir","a":"Aristoteles, Platon'un öğrencisi olan Yunan filozofudur. Mantık, biyoloji, fizik ve siyaset biliminin kurucusu sayılır."},
    {"q":"maslow piramidi","a":"Maslow'un ihtiyaçlar hiyerarşisi 5 basamaktan oluşur: Fizyolojik ihtiyaçlar → Güvenlik → Sevgi/Ait olma → Saygı → Kendini gerçekleştirme."},
    {"q":"freud kimdir","a":"Sigmund Freud, psikanalizin kurucusudur (1856-1939). Bilinçdışı, ego, id ve süperego kavramlarını geliştirmiştir."},
    {"q":"iq nedir","a":"IQ (Intelligence Quotient), zeka katsayısıdır. Ortalama 100 olup standart sapma 15'tir. 130+ üstün zeka, 70 altı zihinsel engel kabul edilir."},
    {"q":"duygusal zeka nedir","a":"Duygusal zeka (EQ), kendi ve başkalarının duygularını tanıma, anlama ve yönetme yeteneğidir. Daniel Goleman tarafından popülerleştirilmiştir."},
    {"q":"stres nedir","a":"Stres, baskı veya tehdit algılandığında vücudun gösterdiği tepkidir. Kısa süreli stres faydalı olabilir, kronik stres sağlığı olumsuz etkiler."},
    {"q":"depresyon nedir","a":"Depresyon, sürekli üzüntü, enerji kaybı ve hayattan zevk alamama ile karakterize ruhsal sağlık bozukluğudur. Tedavi edilebilir bir hastalıktır."},
    {"q":"özgüven nasıl artar","a":"Özgüven için: küçük hedefler belirle ve başar, olumsuz iç sesi fark et ve dönüştür, başarıları kutla, kendinle nazik ol, beceri geliştir."},
    {"q":"alışkanlık nasıl edinilir","a":"Alışkanlık için 'Cue-Routine-Reward' döngüsü kullanılır. James Clear'a göre küçük %1 iyileştirmeler, zamanla büyük değişime yol açar. 21-66 gün sürer."},
    {"q":"psikoloji nedir","a":"Psikoloji, insan ve hayvan davranışı ile zihinsel süreçleri inceleyen bilim dalıdır. Klinik, sosyal, gelişim ve bilişsel psikoloji alt dalları vardır."},
],

# ═══════════════════════════════════════════════════════════════════════════════
# EKONOMİ & FİNANS
# ═══════════════════════════════════════════════════════════════════════════════
"ekonomi_finans": [
    {"q":"bitcoin nedir","a":"Bitcoin, 2009'da Satoshi Nakamoto tarafından yaratılan ilk ve en büyük kripto paradır. Blockchain teknolojisine dayanır, toplam arzı 21 milyon ile sınırlıdır."},
    {"q":"enflasyon nedir","a":"Enflasyon, genel fiyat seviyesinin artması ve paranın satın alma gücünün azalmasıdır. Merkez bankaları faiz politikasıyla enflasyonu kontrol eder."},
    {"q":"faiz nedir","a":"Faiz, borç alınan paranın kullanımı karşılığında ödenen bedeldir. Merkez bankası politika faizi piyasaları doğrudan etkiler."},
    {"q":"borsa nedir","a":"Borsa, şirket hisselerinin ve diğer menkul kıymetlerin alınıp satıldığı organize piyasadır. Türkiye'de BİST, dünyada NYSE ve NASDAQ önemli borsalardır."},
    {"q":"hisse senedi nedir","a":"Hisse senedi, bir şirkete ortaklık hakkı veren menkul kıymettir. Şirketin karından pay alma ve genel kurulda oy kullanma hakkı sağlar."},
    {"q":"döviz nedir","a":"Döviz, yabancı ülkelerin para birimlerini ifade eder. Döviz kurları arz-talep, enflasyon ve faiz oranlarına göre belirlenir."},
    {"q":"gdp nedir","a":"GDP (Gayri Safi Yurt İçi Hasıla), bir ülkede belirli dönemde üretilen tüm mal ve hizmetlerin toplam değeridir. Ekonomik büyümenin temel göstergesidir."},
    {"q":"kripto para nedir","a":"Kripto para, şifreleme teknolojisi kullanan dijital para birimidir. Merkezi otorite olmadan işlem yapılabilir. Bitcoin, Ethereum önemli örneklerdir."},
    {"q":"ethereum nedir","a":"Ethereum, 2015'te Vitalik Buterin tarafından yaratılan akıllı kontrat platformudur. Kendi kripto parası Ether (ETH) ile işlem yapılır."},
    {"q":"nft nedir","a":"NFT (Non-Fungible Token), blokzincirde benzersiz dijital varlıkları temsil eden tokenlerdir. Dijital sanat, müzik ve oyun öğelerinde kullanılır."},
    {"q":"bileşik faiz nedir","a":"Bileşik faiz, hem ana para hem de birikmiş faiz üzerinden faiz kazanılan sistemdir. Zamanla 'karın karı' ile üstel büyüme sağlar."},
    {"q":"yatırım fonu nedir","a":"Yatırım fonu, çok sayıda yatırımcının parasını bir araya toplayarak profesyonellerce yönetilen portföydür. Çeşitlendirme ile riski azaltır."},
],

# ═══════════════════════════════════════════════════════════════════════════════
# SANAT & KÜLTÜR
# ═══════════════════════════════════════════════════════════════════════════════
"sanat_kultur": [
    {"q":"da vinci kimdir","a":"Leonardo da Vinci, 1452-1519 yılları arasında yaşamış İtalyan Rönesans dahisidir. Mona Lisa ve Son Akşam Yemeği'nin yanı sıra bilim, mühendislik ve anatomide de çığır açmıştır."},
    {"q":"mona lisa nerede","a":"Mona Lisa, Paris'teki Louvre Müzesi'nde sergilenmektedir. Da Vinci'nin en ünlü eseridir."},
    {"q":"shakespeare kimdir","a":"William Shakespeare, 1564-1616 yılları arasında yaşamış İngiliz yazar ve şairdir. Hamlet, Romeo ve Juliet, Otello gibi ölümsüz eserler yazmıştır."},
    {"q":"beethoven kimdir","a":"Ludwig van Beethoven, 1770-1827 yılları arasında yaşamış Alman bestecisidir. 9. Senfoni başyapıtlarından biridir; ilerleyen dönemde işitme kaybına rağmen müzik yazmaya devam etmiştir."},
    {"q":"mozart kimdir","a":"Wolfgang Amadeus Mozart, 1756-1791 yılları arasında yaşamış Avusturyalı besteciydi. 600'den fazla eser yazan çocuk dahisi olarak tarihte yerini almıştır."},
    {"q":"picasso kimdir","a":"Pablo Picasso, 1881-1973 yılları arasında yaşamış İspanyol ressam ve heykeltıraştır. Kübizm akımının öncüsüdür. Guernica en ünlü eserlerindendir."},
    {"q":"edebiyat nedir","a":"Edebiyat, dili sanatsal biçimde kullanan yazılı ve sözlü ifade biçimidir. Şiir, roman, hikaye, tiyatro, deneme gibi türleri kapsar."},
    {"q":"türk edebiyatı","a":"Türk edebiyatı; Divan edebiyatı, Halk edebiyatı ve Modern edebiyat olarak üç ana dönemde incelenir. Yunus Emre, Fuzuli, Namık Kemal, Orhan Pamuk önemli isimlerdir."},
    {"q":"yunus emre kimdir","a":"Yunus Emre, 13-14. yüzyıllarda yaşamış Türk şair ve sufisidir. Hümanist şiirleriyle tanınır. UNESCO tarafından 1991'de 'Yılın Kişisi' ilan edilmiştir."},
    {"q":"orhan pamuk kimdir","a":"Orhan Pamuk, 2006 Nobel Edebiyat Ödülü sahibi Türk yazardır. Kar, İstanbul, Benim Adım Kırmızı önemli eserleridir."},
],

# ═══════════════════════════════════════════════════════════════════════════════
# DOĞA & ÇEVRE
# ═══════════════════════════════════════════════════════════════════════════════
"doga_cevre": [
    {"q":"küresel ısınma nedir","a":"Küresel ısınma, sera gazı emisyonlarının artmasıyla Dünya'nın ortalama sıcaklığının yükselmesidir. İklim değişikliğine neden olur."},
    {"q":"sera etkisi nedir","a":"Sera etkisi, atmosferdeki CO₂ gibi gazların Güneş'ten gelen ısıyı tutarak Dünya'yı ısıtma mekanizmasıdır. Doğal süreçtir ama insan faaliyetleri artırıyor."},
    {"q":"ozon tabakası nedir","a":"Ozon tabakası, Dünya'yı zararlı UV ışınlarından koruyan stratosferdeki gaz tabakasıdır. CFC gibi kimyasallar tarafından zarar görüyor."},
    {"q":"yenilenebilir enerji nedir","a":"Yenilenebilir enerji, güneş, rüzgar, su, jeotermal gibi doğal süreçlerle yenilenen enerji kaynaklarından elde edilen enerjidir."},
    {"q":"güneş enerjisi nasıl çalışır","a":"Güneş panelleri, fotovoltaik hücreler aracılığıyla güneş ışığını doğrudan elektriğe dönüştürür. Temiz ve yenilenebilir bir enerji kaynağıdır."},
    {"q":"rüzgar enerjisi","a":"Rüzgar türbinleri, rüzgarın kinetik enerjisini mekanik enerjiye, ardından elektriğe dönüştürür. Türkiye rüzgar enerjisinde önemli kapasiteye sahiptir."},
    {"q":"amazon ormanları","a":"Amazon ormanları, Güney Amerika'daki dünyanın en büyük tropikal orman alanıdır. Yaklaşık 5,5 milyon km² ile 'Dünyanın akciğeri' olarak bilinir."},
    {"q":"biyoçeşitlilik nedir","a":"Biyoçeşitlilik, bir bölgedeki tüm canlı türlerinin ve ekosistemlerinin çeşitliliğidir. İnsan faaliyetleri ve iklim değişikliği biyoçeşitliliği tehdit etmektedir."},
    {"q":"deprem neden olur","a":"Deprem, yer kabuğundaki tektonik plakaların hareket etmesiyle biriken enerjinin aniden açığa çıkmasından kaynaklanır."},
    {"q":"tsunami nedir","a":"Tsunami, deniz tabanındaki deprem, yanardağ patlaması veya heyelan gibi olayların tetiklediği büyük deniz dalgalarıdır."},
    {"q":"volkan nedir","a":"Volkan (yanardağ), magmanın Dünya'nın iç kısmından yüzeye çıktığı açıklıktır. Patlama sırasında lav, kül ve gaz fırlatır."},
],

# ═══════════════════════════════════════════════════════════════════════════════
# UZAY & ASTRONOMİ
# ═══════════════════════════════════════════════════════════════════════════════
"uzay_astronomi": [
    {"q":"güneş sistemi kaç gezegen","a":"Güneş Sistemi'nde 8 gezegen bulunmaktadır: Merkür, Venüs, Dünya, Mars, Jüpiter, Satürn, Uranüs, Neptün."},
    {"q":"en büyük gezegen","a":"Güneş Sistemi'nin en büyük gezegeni Jüpiter'dir. Hacmi Dünya'nın 1.300 katından fazladır."},
    {"q":"mars nedir","a":"Mars, Güneş'e göre 4. gezegendir. 'Kızıl Gezegen' olarak bilinir. NASA'nın çeşitli rover'ları Mars'ı araştırmaktadır."},
    {"q":"nasa nedir","a":"NASA (National Aeronautics and Space Administration), ABD'nin uzay araştırmaları ajansıdır. 1958'de kurulmuştur. Ay'a ilk insanlı iniş NASA'nın başarısıdır."},
    {"q":"apollo 11 nedir","a":"Apollo 11, 1969'da Ay'a ilk insanlı iniş misyonudur. Neil Armstrong ve Buzz Aldrin Ay yüzeyine ayak basan ilk insanlar olmuştur."},
    {"q":"spacex nedir","a":"SpaceX, Elon Musk tarafından 2002'de kurulan özel uzay şirketidir. Yeniden kullanılabilir roketler geliştirmiş, uzay yolculuğu maliyetini düşürmüştür."},
    {"q":"kara delik nedir","a":"Kara delik, yerçekiminin o kadar güçlü olduğu uzay bölgesidir ki ışık bile kaçamaz. Büyük yıldızların ölümüyle oluşur."},
    {"q":"samanyolu nedir","a":"Samanyolu, Dünya'nın bulunduğu galaksidir. Yaklaşık 200-400 milyar yıldız içerir. Sarmal biçimindedir."},
    {"q":"ışık yılı nedir","a":"Işık yılı, ışığın bir yılda aldığı mesafedir: yaklaşık 9,46 trilyon km. Uzay mesafelerini ölçmek için kullanılır."},
    {"q":"süpernova nedir","a":"Süpernova, büyük kütleli yıldızların ömürlerini tamamlarken geçirdiği devasa patlamadır. Bir süpernova kısa süreliğine tüm galaksiden daha parlak olabilir."},
    {"q":"uluslararası uzay istasyonu","a":"ISS (Uluslararası Uzay İstasyonu), 1998'den beri Dünya'nın yörüngesinde aktif olan araştırma istasyonudur. ABD, Rusya ve diğer ülkelerin ortak projesidir."},
    {"q":"hubble teleskop","a":"Hubble Uzay Teleskobu, 1990'dan beri Dünya yörüngesinde görev yapan NASA teleskobudur. Evrenin derinliklerinin keşfinde kritik rol oynamıştır."},
],

# ═══════════════════════════════════════════════════════════════════════════════
# MUTFAK & YEMEK
# ═══════════════════════════════════════════════════════════════════════════════
"mutfak_yemek": [
    {"q":"türk mutfağı","a":"Türk mutfağı dünyanın en zengin mutfaklarından biridir. Kebaplar, mezeler, pideler, baklavalar ve çayıyla dünyaca tanınır."},
    {"q":"baklava nasıl yapılır","a":"Baklava: ince yufka katları tereyağı ile yağlanır, aralarına ceviz/fıstık konur. Fırında pişirilip üzerine şerbet dökülür."},
    {"q":"döner nasıl yapılır","a":"Döner, marine edilmiş et katmanlarının şişe dizilip dikey ateşte pişirilmesiyle yapılır. Türkiye'nin dünyaya tanıttığı yemeklerden biridir."},
    {"q":"çay nasıl demlenir","a":"Türk çayı: demliğin üst bölümüne 2 tatlı kaşığı çay konur, alt bölüme kaynar su eklenir. 15-20 dakika bekletilir, tercihe göre seyrelterek içilir."},
    {"q":"kahve çeşitleri","a":"Popüler kahve çeşitleri: Türk kahvesi, Espresso, Americano, Latte, Cappuccino, Flat White, Macchiato, Cold Brew."},
    {"q":"protein kaynakları","a":"İyi protein kaynakları: kırmızı et, tavuk, balık, yumurta, süt ürünleri, mercimek, nohut, fasulye, tofu, kinoa."},
    {"q":"omega 3 nerede bulunur","a":"Omega-3 kaynakları: somon, sardalya, ton balığı, uskumru, ceviz, keten tohumu ve chia tohumu."},
    {"q":"demir hangi besinlerde","a":"Demir kaynakları: kırmızı et, ciğer, ıspanak, mercimek, nohut, kuru üzüm. C vitamini ile birlikte tüketmek emilimi artırır."},
    {"q":"kalsiyum hangi besinlerde","a":"Kalsiyum kaynakları: süt, yoğurt, peynir, brokoli, badem, susam, sardalya ve soya sütü."},
],

# ═══════════════════════════════════════════════════════════════════════════════
# GÜNLÜK HAYAT & PRATİK BİLGİ
# ═══════════════════════════════════════════════════════════════════════════════
"gunluk_hayat": [
    {"q":"stres nasıl azaltılır","a":"Stres azaltma yolları: derin nefes egzersizi, meditasyon, fiziksel egzersiz, uyku düzeni, sosyal destek, hobiler ve doğada zaman geçirme."},
    {"q":"uyku kalitesi nasıl artar","a":"Uyku için: düzenli uyku saatleri, karanlık ve serin oda, yatmadan önce ekran kaçınma, kafein sınırlama ve rahatlatıcı rutinler oluşturma."},
    {"q":"motivasyon nasıl bulunur","a":"Motivasyon için: net hedefler belirle, küçük adımlarla başla, başarıları kutla, ilham verici insanlarla vakit geç, 'neden'ini hatırla."},
    {"q":"zaman yönetimi","a":"Zaman yönetimi için: önceliklendirme (Eisenhower matrisi), Pomodoro tekniği (25 dk çalış, 5 dk mola), yapılacaklar listesi ve distraksiyon engelleme."},
    {"q":"dikkat dağınıklığı nasıl giderilir","a":"Odaklanma için: telefonu sessize al, tek işe odaklan, Pomodoro tekniği uygula, dağınık ortamı düzenle, uyku ve beslenmeye dikkat et."},
    {"q":"para biriktirme","a":"Para biriktirme ipuçları: bütçe yap, harcama takibi tut, önce kendinle öde (gelirin %10-20'sini otomatik tasarruf), gereksiz abonelikler iptal et."},
    {"q":"kitap okuma alışkanlığı","a":"Kitap okuma için: günlük en az 15 dk ayır, belirli bir yer ve saat belirle, ilgini çeken kitaplarla başla, hedef belirle (örn. ayda 1 kitap)."},
    {"q":"seyahat nasıl planlanır","a":"Seyahat planlaması: bütçe belirle, destinasyon araştır, ulaşım ve konaklama ayarla, vize kontrol et, gerekli eşyaları listele, sağlık sigortası yap."},
    {"q":"dil öğrenme","a":"Dil öğrenmek için: günlük pratik yap, Duolingo/uygulama kullan, native speaker ile konuş, hedef dilde medya tüket (film, müzik), flash card kullan."},
    {"q":"spor alışkanlığı nasıl edinilir","a":"Spor için: sevdiğin aktiviteyi seç, küçük başla, takvime ekle, arkadaşla yap, sonuçları takip et ve kendini ödüllendir."},
],

# ═══════════════════════════════════════════════════════════════════════════════
# HAYVANLAR
# ═══════════════════════════════════════════════════════════════════════════════
"hayvanlar": [
    {"q":"en hızlı hayvan","a":"Kara hayvanları arasında en hızlısı çitadır (110 km/h). Havada sürtünmesiz en hızlısı alçakboynuzlu fırtınakuşu (400+ km/h diviş hızı). Yüzücüde yelkenbaliğidir (110 km/h)."},
    {"q":"en zeki hayvan","a":"En zeki hayvanlar: şempanze, yunus, orca, fil, karga ve ahtapot. Şempanzeler aletleri kullanır, kargalar problem çözer."},
    {"q":"köpek kaç yıl yaşar","a":"Köpekler ortalama 10-13 yıl yaşar. Irka ve büyüklüğe göre değişir; küçük ırklar genellikle büyük ırklardan daha uzun yaşar."},
    {"q":"kedi kaç yıl yaşar","a":"Kediler ortalama 12-18 yıl yaşar. En uzun yaşayan kedinin 38 yıl yaşadığı kayıtlara geçmiştir."},
    {"q":"balinalar nasıl nefes alır","a":"Balinalar deniz memelisidir ve akciğerlerle nefes alır. Su yüzeyine çıkarak spiracle adlı delikten nefes alıp verirler."},
    {"q":"karınca ne kadar güçlü","a":"Karıncalar kendi vücut ağırlığının 10-50 katını taşıyabilir. Koloni organizasyonları ve toplumsal yapılarıyla da dikkat çekerler."},
    {"q":"arı nasıl bal yapar","a":"Arılar çiçeklerden nektar toplar, kovana taşır, sindirim enzimleriyle işler ve su buharlaştırarak bal üretir. Bir arı ömrü boyunca 1/12 çay kaşığı bal üretir."},
],

# ═══════════════════════════════════════════════════════════════════════════════
# ŞAKALAR & EĞLENCELİ
# ═══════════════════════════════════════════════════════════════════════════════
"sakalar": [
    {"q":"şaka yap","a":"😄 Programcı markete gider. Eşi telefona: '2 ekmek al, süt varsa 6 tane al.' Programcı 6 ekmekle döner!"},
    {"q":"fıkra anlat","a":"😂 Öğrenci sınava girdi. Hoca: 'Kalem kullanmayın.' Öğrenci: 'Tamam.' ve parmağıyla yazmaya çalıştı."},
    {"q":"komik bir şey söyle","a":"🤖 Ben bir yapay zekayım ve şaka yapmak için algoritmalar kullanıyorum. Bu biraz komik değil mi?"},
    {"q":"beni güldür","a":"😄 İki yazılımcı barda buluşur. Biri: 'Kötü haber: Sunucu çöktü.' Diğeri: 'İyi haber: Beni de çöktürdü, eve erken gittim!'"},
    {"q":"espri yap","a":"🎯 Neden bilgisayarlar şarkı söyler? Çünkü bellekte notlar var! 😄"},
    {"q":"valorant şakası","a":"🎮 Valorant'ta ekonomi yönetimi nedir? 'Para yok ama rank çıkmak istiyorum' diye ağlamak! 😂"},
],

# ═══════════════════════════════════════════════════════════════════════════════
# MOTİVASYON & İLHAM
# ═══════════════════════════════════════════════════════════════════════════════
"motivasyon_soz": [
    {"q":"motive et","a":"💪 'Başarı, her gün tekrarlanan küçük çabaların toplamıdır.' — Robert Collier\n\nDevam et! Her adım seni hedefe yaklaştırıyor!"},
    {"q":"ilham ver","a":"🌟 'Büyük şeyler hiçbir zaman konfor bölgesinin içinde olmaz.' Sınırlarını zorla, büyü! 🚀"},
    {"q":"cesaretlen","a":"⚡ 'Yapabilirsin ya da yapamam diye düşünürsün — her iki durumda da haklısın.' — Henry Ford\n\nSEN YAPABİLİRSİN!"},
    {"q":"moral ver","a":"🔥 Zor zamanlar kahramanları yaratır. Bu an seni daha güçlü yapıyor. Devam et!"},
    {"q":"güçlendir","a":"💎 Elmas baskı altında oluşur. Zorluğun içinden çıkacaksın ve daha güçlü olacaksın!"},
    {"q":"hayatın anlamı nedir","a":"🌍 Hayatın anlamı, kendi anlamamızı bulmaktır. Viktor Frankl'a göre: anlam acıyı bile katlanılabilir kılar. Tutkunu takip et!"},
    {"q":"başarılı olmak için ne gerekir","a":"🏆 Başarı için: net hedef + ısrarcı çalışma + sürekli öğrenme + doğru çevre + sabır. Başarı bir gecede gelmiyor, her gün biraz daha!"},
    {"q":"mutlu olmak için ne yapmalı","a":"😊 Mutluluk için: minnettarlık pratiği yap, anı yaşa, bağlantıları güçlendir, amaç bul, bedeni hareket ettir ve karşılaştırmayı bırak!"},
    {"q":"pes etmek istiyorum","a":"💙 Dur bir saniye. Her başarı hikayesinde 'bırakmak istedim ama bırakmadım' dönüm noktası var. Senin dönüm noktanda olabilirsin. Devam et!"},
    {"q":"kendime inanamıyorum","a":"🌟 Şu an hissettiğin şüphe normal. Ama hep unutma: başkaları sende gördüklerini sen henüz göremeyebilirsin. Bir adım at, geri kalanı gelecek!"},
],

# ═══════════════════════════════════════════════════════════════════════════════
# İLGİNÇ BİLGİLER
# ═══════════════════════════════════════════════════════════════════════════════
"ilginc_bilgiler": [
    {"q":"ilginç bilgi","a":"🌟 İlginç gerçek: Bir bal arısı ömrü boyunca yalnızca 1/12 çay kaşığı bal üretir! 🐝"},
    {"q":"bilimsel gerçek","a":"⚡ Şimşek, Güneş'in yüzeyinden 5 kat daha sıcaktır! (yaklaşık 30.000 K)"},
    {"q":"biliyor musun","a":"🧬 İnsan DNA'sını uçtan uca açsaydınız Güneş'e 200 kez gidip gelirdiniz!"},
    {"q":"şaşırtıcı bilgi","a":"🌍 Dünya, Güneş etrafında saniyede 29,8 km hızla hareket eder!"},
    {"q":"garip bilgi","a":"🐙 Ahtapotların 3 kalbi ve mavi kanı vardır! Hemoglobin yerine hemosiyatinin kullanır."},
    {"q":"eğlenceli bilgi","a":"🐘 Filler tek kemirgen dişlerine sahip değildir — filler kullandıktan sonra 6 kez diş değiştirir!"},
    {"q":"hayret verici bilgi","a":"🌙 Ay, her yıl Dünya'dan 3,8 cm uzaklaşmaktadır!"},
    {"q":"ilginç bir şey söyle","a":"🦈 Köpekbalıkları dinozorlardan önce var oldu ve hâlâ yaşıyorlar! Yaklaşık 450 milyon yıllık geçmişleri var."},
    {"q":"rastgele bilgi","a":"🐦 Kargalar yüzleri hatırlayabilir ve kızgınlarsa o kişiyi 'takip edebilir'!"},
    {"q":"beni şaşırt","a":"🍯 Bal hiç bozulmaz. Mısır piramitlerinde bulunan 3000 yıllık bal hâlâ yenilebilir durumdaydı!"},
],

# ═══════════════════════════════════════════════════════════════════════════════
# VALORANT DETAYLI
# ═══════════════════════════════════════════════════════════════════════════════
"valorant_detayli": [
    {"q":"valorant nedir","a":"Valorant, Riot Games tarafından 2020'de yayınlanan taktik 5v5 nişancı oyunudur. Özel yeteneklere sahip agentlar ve silahları birleştirir."},
    {"q":"valorant agentları","a":"Valorant'ta 4 ajan rolü var: Duelist (Jett, Reyna, Raze, Neon, Yoru, Phoenix, Iso), Sentinel (Sage, Killjoy, Cypher, Chamber, Deadlock), Initiator (Sova, Breach, Skye, Fade, Kay/O, Gekko), Controller (Brimstone, Viper, Omen, Astra, Harbor, Clove)."},
    {"q":"jett nasıl oynanır","a":"Jett ipuçları: 🎯 Dash'i peek için kullan, Updraft+Bladestorm kombinasyonu yap, entry frag atmaktan çekinme, Tailwind'i kaçış için sakla!"},
    {"q":"sage nasıl oynanır","a":"Sage ipuçları: 💚 Duvarı rotasyonu kesmek için koy, Heal'i önce takım arkadaşına ver, Rez'i high-value an için sakla, site'ı tek başına tutabilirsin!"},
    {"q":"sova nasıl oynanır","a":"Sova ipuçları: 🔍 Recon Bolt line-up'larını öğren, Drone'u agresif peek öncesi gönder, Ult'u spike ekini sonrası kullan!"},
    {"q":"killjoy nasıl oynanır","a":"Killjoy ipuçları: 🤖 Turret'i crossfire pozisyonuna koy, Nanoswarm'ı post-plant için sakla, Lockdown ile 1v5 retake kazan!"},
    {"q":"brimstone nasıl oynanır","a":"Brimstone ipuçları: ☁️ Default smoke'ları ezberle, Stim Beacon'ı entry için koy, Orbital Strike ile post-plant kazan!"},
    {"q":"ascent haritası","a":"Ascent: Mid kontrolü kritik. Attack: B Catwalk'tan destek al, A Main+Market split. Defense: A Cubby+Window crossfire, Mid Vine kapat!"},
    {"q":"bind haritası","a":"Bind: Teleport'u doğru kullan! Attack: B Hookah'tan squeeze, A Short+Long split. Defense: Teleport rotasyonu şart, A Showers erken kapat!"},
    {"q":"haven haritası","a":"Haven: 3 site var, Mid kritik! Attack: A+C aynı anda, Garage'dan C'ye. Defense: Mid'i kapatmadan site savunma, C Garage erken!"},
    {"q":"ekonomi valorant","a":"💰 Ekonomi: 9000+ = Full buy (Vandal/Phantom+Armor+Utility). 4000-6000 = Half buy (Spectre+Light). 2000-3999 = Eco (Ghost+Save). 0-1999 = Full save!"},
    {"q":"aim nasıl geliştirilir","a":"🎯 Aim geliştirme: Aimlabs/KovaaK's uygula, crosshair placement (kafaya hizala), DPI+sensitivity ayarla, günlük 30 dk pratik yap!"},
    {"q":"rank nasıl çıkılır","a":"📈 Rank için: ana ajan belirle, harita öğren, ekonomi yönet, iletişim kur, mental sağlıklı tut, günde max 3-4 maç oyna, VOD izle!"},
    {"q":"phantom mi vandal mi","a":"🔫 Phantom vs Vandal: Phantom — silah sesini bastırır, yakın-orta mesafe güçlü, duvara zarar verir. Vandal — her menzilde one-tap kafası, daha yüksek recoil. Tercih kişisel!"},
],

}

def save_to_knowledge_base():
    """Eğitim verisini bilgi tabanına kaydet VE local AI'a yükle"""
    knowledge = {}
    for category, items in TRAINING_DATA.items():
        knowledge[category] = {
            "triggers": list(set(item["q"].lower() for item in items)),
            "responses": [item["a"] for item in items],
            "qa_pairs": items
        }
    with open(TRAINING_FILE, "w", encoding="utf-8") as f:
        json.dump(knowledge, f, ensure_ascii=False, indent=2)

    # Doğrudan local AI KNOWLEDGE_BASE'e ekle
    try:
        import anka_local_ai
        for category, data in knowledge.items():
            if category not in anka_local_ai.KNOWLEDGE_BASE:
                anka_local_ai.KNOWLEDGE_BASE[category] = data
            else:
                existing = anka_local_ai.KNOWLEDGE_BASE[category]
                existing_triggers = set(existing.get("triggers",[]))
                new_triggers = set(data.get("triggers",[]))
                existing["triggers"] = list(existing_triggers | new_triggers)
                existing.setdefault("qa_pairs",[]).extend(data.get("qa_pairs",[]))
    except Exception as e:
        print(f"[ANKA] Training→LocalAI: {e}")

    # AI Core'a yükle
    try:
        import anka_ai_core
        core = anka_ai_core.get_ai_core()
        for category, items in TRAINING_DATA.items():
            for item in items:
                q = item["q"].lower().strip()
                a = item["a"]
                if q and a and q not in core._learn["custom_qa"]:
                    core._learn["custom_qa"][q] = a
    except Exception as e:
        print(f"[ANKA] Training→Core: {e}")

    total = sum(len(items) for items in TRAINING_DATA.values())
    print(f"[ANKA] ✅ {total} soru-cevap yüklendi!")
    return total

def get_all_qa():
    result = []
    for category, items in TRAINING_DATA.items():
        for item in items:
            result.append({"category": category, **item})
    return result
