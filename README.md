# 🎬 Film & Dizi Takip ve Planlama Platformu

Bu proje; kullanıcıların izledikleri veya izlemek istedikleri filmleri ve dizileri takip edebildiği, arkadaşlarıyla/partnerleriyle ortak planlamalar yapabildiği, TMDb API entegrasyonuyla zengin bir filmografiye ve detaylı verilere ulaşabildiği modern bir Flask web uygulamasıdır.

---

## 🚀 Öne Çıkan Özellikler

* **TMDb API Entegrasyonu:** Filmler ve diziler için Türkçe özetler, yüksek çözünürlüklü posterler, arka plan sahne galerileri ve benzer içerik önerileri.
* **Kapsamlı Sanatçı Arşivi:** Türkan Şoray, Gülşen Bubikoğlu, Hülya Koçyiğit, Tarık Akan, Kemal Sunal ve Giray Altınok gibi usta isimlerin tüm filmografisini otomatik içe aktarma desteği.
* **Akıllı Takvim ve Planlama:** Haftalık/aylık takvim yapısı ile film veya dizi izleme seansları planlama ve izlenen içerikleri işaretleme.
* **Partner & Arkadaş Sistemi:** Kullanıcıların birbirleriyle arkadaşlık isteği gönderip kabul edebilmesi, ortak film havuzları oluşturabilmesi.
* **Kişiselleştirilmiş Profil:** En sevilen 4 film/dizi gösterimi, izleme geçmişi günlüğü (journal) ve değerlendirmeler.

---

## 🛠️ Kullanılan Teknolojiler

* **Backend:** Python, Flask, Flask-SQLAlchemy (ORM), Flask-Login
* **Veritabanı:** SQLite
* **Frontend:** HTML5, CSS3, JavaScript, Tailwind CSS (uyarlanabilir arayüz temaları)
* **Harici Servisler:** The Movie Database (TMDb) API

---

## 📦 Kurulum ve Çalıştırma

Projeyi yerel ortamınızda (local) çalıştırmak için aşağıdaki adımları takip edebilirsiniz:

1. **Depoyu Klonlayın:**
   ```bash
   git clone [https://github.com/kullanici-adin/proje-adi.git](https://github.com/kullanici-adin/proje-adi.git)
   cd proje-adi
Sanal Ortam (Virtual Environment) Oluşturun ve Aktifleştirin:

Bash
python -m venv venv
# Windows için:
venv\Scripts\activate
# macOS / Linux için:
source venv/bin/activate
Gerekli Kütüphaneleri Yükleyin:

Bash
pip install -r requirements.txt
Veritabanını Başlatın ve Verileri Çekin:

Bash
python init_db.py
python populate_actors.py
Uygulamayı Çalıştırın:

Bash
python app.py
Tarayıcınızda http://127.0.0.1:5000 adresine giderek projeyi inceleyebilirsiniz.

📂 Proje Yapısı
Plaintext
film/
│
├── instance/
│   └── film_serisi.db       # SQLite Veritabanı
├── static/                  # Statik dosyalar (CSS, JS, Görseller)
├── templates/               # HTML Arayüz Şablonları (Jinja2)
├── app.py                   # Flask ana uygulama ve rotalar
├── init_db.py               # Veritabanı tablo oluşturma betiği
├── populate_actors.py       # TMDb API veri çekme otomasyonu
└── requirements.txt         # Proje bağımlılıkları
💡 Geliştirme Aşaması
Proje şu an aktif olarak geliştirilme ve lokal test aşamasındadır. Yeni özellikler eklendikçe güncellenmeye devam edecektir.
