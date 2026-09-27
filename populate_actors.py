import requests
from app import app, db, Movie, Series, Person

API_KEY = "d973f8c77c29694c80e3cf888f853aa3"

print("🚀 Veritabanındaki tüm film/dizi oyuncuları, yönetmenleri ve yaratıcıları TMDb'den önden yükleniyor...", flush=True)

with app.app_context():
    # 1. Veritabanındaki tüm filmlerden ve dizilerden benzersiz isimleri toplayalım
    all_movies = Movie.query.all()
    all_series = Series.query.all()
    people_set = set()
    
    # Filmlerdeki yönetmen ve oyuncular
    for m in all_movies:
        if m.director and m.director != "Unknown":
            people_set.add(m.director.strip())
        if m.cast_list:
            for actor in m.cast_list.split(','):
                clean_name = actor.strip()
                if clean_name:
                    people_set.add(clean_name)
                    
    # Dizilerdeki yaratıcı (creator) ve oyuncular
    for s in all_series:
        if s.creator and s.creator != "Unknown":
            people_set.add(s.creator.strip())
        if hasattr(s, 'cast_list') and s.cast_list:
            for actor in s.cast_list.split(','):
                clean_name = actor.strip()
                if clean_name:
                    people_set.add(clean_name)
    
    total = len(people_set)
    print(f"Toplam {total} benzersiz kişi (oyuncu/yönetmen/yaratıcı) bulundu. Veriler çekiliyor...\n")

    # 2. Her kişi için API'ye sorgu atıp Person tablosuna kaydedelim
    for index, name in enumerate(people_set, start=1):
        existing = Person.query.filter_by(name=name).first()
        if existing:
            print(f"[{index}/{total}] Zaten veritabanında var: {name}")
            continue

        search_url = f"https://api.themoviedb.org/3/search/person?api_key={API_KEY}&query={name}"
        res = requests.get(search_url)
        
        profile_url = ""
        birthday = "Belirtilmemiş"
        birth_place = "Belirtilmemiş"
        bio = "Biyografi bulunamadı."

        if res.status_code == 200:
            results = res.json().get('results', [])
            if results:
                person_data = results[0]
                person_id = person_data.get('id')
                profile_path = person_data.get('profile_path')
                if profile_path:
                    profile_url = f"https://image.tmdb.org/t/p/w500{profile_path}"
                    
                detail_url = f"https://api.themoviedb.org/3/person/{person_id}?api_key={API_KEY}&language=en-US"
                detail_res = requests.get(detail_url)
                if detail_res.status_code == 200:
                    d_data = detail_res.json()
                    bio = d_data.get('biography') or "Biyografi bulunamadı."
                    birthday = d_data.get('birthday') or "Belirtilmemiş"
                    birth_place = d_data.get('place_of_birth') or "Belirtilmemiş"

        new_person = Person(
            name=name,
            profile_url=profile_url,
            birthday=birthday,
            birth_place=birth_place,
            biography=bio
        )
        db.session.add(new_person)
        db.session.commit()
        print(f"[{index}/{total}] ✅ Kaydedildi: {name}")

    print("\n🎉 İşlem Tamamlandı! Tüm film ve dizi kişileri veritabanına yüklendi.")