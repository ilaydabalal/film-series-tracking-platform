# 🎬 Film & Dizi Takip ve Planlama Platformu

Bu proje; kullanıcıların izledikleri veya izlemek istedikleri filmleri ve dizileri takip edebildiği, arkadaşlarıyla/partnerleriyle ortak planlamalar yapabildiği, TMDb API entegrasyonuyla zengin bir filmografiye ve detaylı verilere ulaşabildiği modern bir Flask web uygulamasıdır.

---

## Öne Çıkan Özellikler

* **TMDb API Entegrasyonu:** Filmler ve diziler için Türkçe özetler, yüksek çözünürlüklü posterler, arka plan sahne galerileri ve benzer içerik önerileri.
* **Akıllı Takvim ve Planlama:** Haftalık/aylık takvim yapısı ile film veya dizi izleme seansları planlama ve izlenen içerikleri işaretleme.
* **Partner & Arkadaş Sistemi:** Kullanıcıların birbirleriyle arkadaşlık isteği gönderip kabul edebilmesi, ortak film havuzları oluşturabilmesi.
* **Kişiselleştirilmiş Profil:** En sevilen 4 film/dizi gösterimi, izleme geçmişi günlüğü (journal) ve değerlendirmeler.

---

## Kullanılan Teknolojiler

* **Backend:** Python, Flask, Flask-SQLAlchemy (ORM), Flask-Login
* **Veritabanı:** SQLite
* **Frontend:** HTML5, CSS3, JavaScript, Tailwind CSS (uyarlanabilir arayüz temaları)
* **Harici Servisler:** The Movie Database (TMDb) API

---

Proje Yapısı

film/
│
├── instance/
│   └── film_serisi.db       # SQLite Veritabanı
├── static/                  # Statik dosyalar (CSS, JS, Görseller)
├── templates/               # HTML Arayüz Şablonları
├── app.py                   # Flask ana uygulama ve rotalar
├── init_db.py               # Veritabanı tablo oluşturma betiği
├── populate_actors.py       # TMDb API veri çekme otomasyonu
└── requirements.txt         # Proje bağımlılıkları

Geliştirme Aşaması
Proje şu an aktif olarak geliştirilme ve lokal test aşamasındadır. Yeni özellikler eklendikçe güncellenmeye devam edecektir.
