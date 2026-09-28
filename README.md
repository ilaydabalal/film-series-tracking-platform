
### https://berilay.pythonanywhere.com/

# 🎬 Film & Series Tracking and Planning Platform

This project is a modern Flask web application that allows users to track movies and series they have watched or want to watch, make joint plans with friends/partners, and access a rich filmography and detailed data via TMDb API integration.

---

## Key Features

* **TMDb API Integration:** Turkish overviews, high-resolution posters, backdrop scene galleries, and similar content recommendations for movies and series.
* **Smart Calendar & Planning:** Plan movie or series viewing sessions and mark watched content using a weekly/monthly calendar structure.
* **Partner & Friend System:** Users can send and accept friend requests and create joint watch pools.
* **Personalized Profile:** Top 4 favorite movie/series showcase, viewing history journal, and ratings.

---

## Technologies Used

* **Backend:** Python, Flask, Flask-SQLAlchemy (ORM), Flask-Login
* **Database:** SQLite
* **Frontend:** HTML5, CSS3, JavaScript, Tailwind CSS (adaptable UI themes)
* **External Services:** The Movie Database (TMDb) API

---

## 📂 Project Structure

```text
film/
│
├── instance/
│   └── film_serisi.db       # SQLite Database
├── static/                  # Static files (CSS, JS, Images)
├── templates/               # HTML UI Templates (Jinja2)
├── app.py                   # Flask main application and routes
├── init_db.py               # Database table creation script
├── populate_actors.py       # TMDb API data fetching automation
└── requirements.txt         # Project dependencies
```

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
## 📂 Proje Yapısı

```text
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
