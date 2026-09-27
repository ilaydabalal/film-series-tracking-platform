from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from collections import Counter
from datetime import datetime
from flask import jsonify
from itsdangerous import URLSafeTimedSerializer as Serializer

app = Flask(__name__)
app.config['SECRET_KEY'] = 'cokx-gizlix-birx-anahtarx'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///film_serisi.db'
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = None  

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=True) 
    password = db.Column(db.String(150), nullable=False)
    partner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    avatar = db.Column(db.String(100), nullable=True)

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tmdb_id = db.Column(db.Integer)
    title = db.Column(db.String(200), nullable=False)
    original_title = db.Column(db.String(200))
    original_language = db.Column(db.String(50)) 
    poster_url = db.Column(db.String(500))
    backdrop_url = db.Column(db.String(500))
    overview = db.Column(db.Text)
    director = db.Column(db.String(200))
    writer = db.Column(db.String(200))
    cast_list = db.Column(db.Text)
    cast_images = db.Column(db.Text)
    genres = db.Column(db.String(200))
    release_date = db.Column(db.String(50))
    runtime = db.Column(db.Integer)
    budget = db.Column(db.BigInteger)
    revenue = db.Column(db.BigInteger)
    awards = db.Column(db.String(100))
    posters_gallery = db.Column(db.Text)
    backdrops_gallery = db.Column(db.Text)
    recommendations = db.Column(db.Text)

class Person(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False)
    profile_url = db.Column(db.String(500))
    birthday = db.Column(db.String(50))
    birth_place = db.Column(db.String(200))
    biography = db.Column(db.Text)
    
class MonthPool(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'))
    movie = db.relationship('Movie')

class WeeklyCalendar(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'))
    scheduled_date = db.Column(db.String(50), nullable=True)
    time_slot = db.Column(db.String(20), default="20:00")
    partner_name = db.Column(db.String(150), nullable=True)
    is_watched = db.Column(db.Boolean, default=False)
    
    user_rating = db.Column(db.Float, default=0.0)
    user_comment = db.Column(db.Text, nullable=True)
    user_favorite = db.Column(db.Boolean, default=False)
    user_updated_at = db.Column(db.String(50), nullable=True)

    partner_rating = db.Column(db.Float, default=0.0)
    partner_comment = db.Column(db.Text, nullable=True)
    partner_favorite = db.Column(db.Boolean, default=False)
    partner_updated_at = db.Column(db.String(50), nullable=True)
    
    movie = db.relationship('Movie')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
@login_required
def index():
    return redirect(url_for('pool'))
import json
from sqlalchemy import or_

# Türler ve diller her seferinde DB'yi yormasın diye global önbellek
CACHED_GENRES = []
CACHED_LANGUAGES = []
@app.route('/pool')
@login_required
def pool():
    global CACHED_GENRES, CACHED_LANGUAGES
    
    page = request.args.get('page', 1, type=int)
    per_page = 20
    selected_genre = request.args.get('genre', '')
    selected_language = request.args.get('language', '')
    search_query = request.args.get('q', '').strip()

    # Sıralı JSON dosyasını okuyoruz
    try:
        with open("sıralı_film.json", "r", encoding="utf-8") as f:
            ordered_titles = json.load(f)
    except FileNotFoundError:
        ordered_titles = []

    # JSON içindeki her başlığı temizleyip hızlı arama için indeks sözlüğü oluşturuyoruz
    title_to_index = {}
    for idx, title in enumerate(ordered_titles):
        clean_json_title = title.split('(')[0].strip().lower()
        title_to_index[clean_json_title] = idx

    query = Movie.query

    if selected_genre:
        query = query.filter(Movie.genres.ilike(f'%{selected_genre}%'))
    if selected_language:
        query = query.filter(Movie.original_language == selected_language)

    all_movies = query.all()

    # --- TÜRKÇE KARAKTER VE BÜYÜK/KÜÇÜK HARF DUYARSIZ ARAMA YARDIMCISI ---
    def normalize_tr(text):
        if not text:
            return ""
        return text.replace('Ç', 'c').replace('ç', 'c') \
                   .replace('Ş', 's').replace('ş', 's') \
                   .replace('Ğ', 'g').replace('ğ', 'g') \
                   .replace('Ü', 'u').replace('ü', 'u') \
                   .replace('Ö', 'o').replace('ö', 'o') \
                   .replace('İ', 'i').replace('ı', 'i') \
                   .lower()

    # Film Arama Kısmı (Esnek & Türkçe Karakter Duyarsız)
    if search_query:
        q_norm = normalize_tr(search_query)
        filtered_list = []
        for movie in all_movies:
            title_norm = normalize_tr(movie.title)
            director_norm = normalize_tr(movie.director)
            cast_norm = normalize_tr(movie.cast_list)
            
            if q_norm in title_norm or q_norm in director_norm or q_norm in cast_norm:
                filtered_list.append(movie)
        all_movies = filtered_list

    def sorting_key(movie):
        clean_movie_title = movie.title.split('(')[0].strip().lower()
        
        if clean_movie_title in title_to_index:
            return (0, title_to_index[clean_movie_title])
        
        year = 0
        if movie.release_date and len(movie.release_date) >= 4:
            try:
                year = int(movie.release_date[:4])
            except ValueError:
                year = 0
        return (1, -year)

    # Python tarafında hızlı sıralama
    sorted_movies = sorted(all_movies, key=sorting_key)

    total = len(sorted_movies)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_movies = sorted_movies[start:end]

    class Pagination:
        def __init__(self, page, per_page, total):
            self.page = page
            self.per_page = per_page
            self.total = total
            self.pages = (total + per_page - 1) // per_page if total > 0 else 1
            self.has_prev = page > 1
            self.has_next = page < self.pages
            self.prev_num = page - 1
            self.next_num = page + 1

        def iter_pages(self, left_edge=1, right_edge=1, left_current=2, right_current=2):
            return range(1, self.pages + 1)

    pagination = Pagination(page, per_page, total)

    # Tür ve dilleri önbellekten al
    if not CACHED_GENRES or not CACHED_LANGUAGES:
        raw_genres = [g[0] for g in db.session.query(Movie.genres).distinct().all() if g[0]]
        CACHED_GENRES = sorted(list(set([genre.strip() for sublist in raw_genres for genre in sublist.split(',')])))
        CACHED_LANGUAGES = [l[0] for l in db.session.query(Movie.original_language).distinct().all() if l[0]]

    # --- Ay havuzu, takvim planlı ve izlenen film ID'leri ---
    month_pool_records = MonthPool.query.filter_by(user_id=current_user.id).all()
    month_pool_ids = [item.movie_id for item in month_pool_records]

    calendar_records = WeeklyCalendar.query.filter_by(user_id=current_user.id).all()
    scheduled_movie_ids = [item.movie_id for item in calendar_records if item.scheduled_date]
    watched_movie_ids = [item.movie_id for item in calendar_records if item.is_watched]

    return render_template('pool.html', 
                           movies=paginated_movies, 
                           pagination=pagination, 
                           genres=CACHED_GENRES,
                           languages=CACHED_LANGUAGES,
                           selected_genre=selected_genre,
                           selected_language=selected_language,
                           search_query=search_query,
                           month_pool_ids=month_pool_ids,
                           scheduled_movie_ids=scheduled_movie_ids,
                           watched_movie_ids=watched_movie_ids)
@app.route('/remove_journal_item/<int:item_id>', methods=['POST'])
@login_required
def remove_journal_item(item_id):
    # Önce film takviminden aramayı deniyoruz
    item = WeeklyCalendar.query.get(item_id)
    if item and item.user_id == current_user.id:
        db.session.delete(item)
        db.session.commit()
        return redirect(url_for('journal'))
        
    # Eğer film takviminde bulunamazsa dizi takviminden arıyoruz
    series_item = SeriesCalendar.query.get(item_id)
    if series_item and series_item.user_id == current_user.id:
        db.session.delete(series_item)
        db.session.commit()
        
    return redirect(url_for('journal'))
@app.route('/movie/<int:movie_id>')
@login_required
def movie_detail(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    calendar_entry = WeeklyCalendar.query.filter_by(user_id=current_user.id, movie_id=movie_id).first()
    all_calendar_entries = WeeklyCalendar.query.filter_by(user_id=current_user.id, movie_id=movie_id).all()
    
    # Türkçe karakter duyarsızlaştırma fonksiyonu
    def normalize_tr(text):
        if not text:
            return ""
        return text.replace('Ç', 'c').replace('ç', 'c') \
                   .replace('Ş', 's').replace('ş', 's') \
                   .replace('Ğ', 'g').replace('ğ', 'g') \
                   .replace('Ü', 'u').replace('ü', 'u') \
                   .replace('Ö', 'o').replace('ö', 'o') \
                   .replace('İ', 'i').replace('ı', 'i') \
                   .lower()

    recommendations_with_status = []
    if movie.recommendations:
        # Tüm filmleri bir kere belleğe çekip esnek arama yapıyoruz (performans için idealdir)
        all_db_movies = Movie.query.all()
        
        for rec in movie.recommendations.split('||'):
            parts = rec.split('|')
            if len(parts) >= 3 and parts[1] != "":
                rec_title = parts[0]
                rec_poster = parts[1]
                rec_score = parts[2]
                
                found_movie = None
                rec_clean = normalize_tr(rec_title.split('(')[0].strip())
                
                # Arşivdeki filmlerle TMDb öneri başlığını esnekçe kıyasla
                for db_m in all_db_movies:
                    db_clean = normalize_tr(db_m.title.split('(')[0].strip())
                    if rec_clean in db_clean or db_clean in rec_clean:
                        found_movie = db_m
                        break

                recommendations_with_status.append({
                    'title': found_movie.title if found_movie else rec_title,
                    'poster': rec_poster,
                    'score': rec_score,
                    'found_id': found_movie.id if found_movie else None
                })

    return render_template(
        'movie_detail.html', 
        movie=movie, 
        calendar_entry=calendar_entry, 
        all_calendar_entries=all_calendar_entries,
        recommendations_with_status=recommendations_with_status
    )
@app.route('/add_to_month_pool/<int:movie_id>')
@login_required
def add_to_month_pool(movie_id):
    existing = MonthPool.query.filter_by(user_id=current_user.id, movie_id=movie_id).first()
    if not existing:
        mp = MonthPool(user_id=current_user.id, movie_id=movie_id)
        db.session.add(mp)
        db.session.commit()
        flash('Film bu ayın havuzuna eklendi!', 'success')
    else:
        flash('Bu film zaten ay havuzunda var!', 'info')
    return redirect(request.referrer or url_for('pool'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        new_username = request.form.get('username')
        if new_username and new_username != current_user.username:
            existing = User.query.filter_by(username=new_username).first()
            if existing:
                flash('Bu kullanıcı adı zaten kullanımda', 'error')
            else:
                current_user.username = new_username
                db.session.commit()
                flash('Kullanıcı adınız güncellendi', 'success')
                
    partner = User.query.get(current_user.partner_id) if current_user.partner_id else None
    
    pending_requests = db.session.query(PartnerRequest, User).join(User, PartnerRequest.sender_id == User.id).filter(
        PartnerRequest.receiver_id == current_user.id, 
        PartnerRequest.status == 'pending'
    ).all()

    pending_friend_requests = db.session.query(FriendRequest, User).join(User, FriendRequest.sender_id == User.id).filter(
        FriendRequest.receiver_id == current_user.id, 
        FriendRequest.status == 'pending'
    ).all()
    
    watched_items = WeeklyCalendar.query.filter_by(user_id=current_user.id, is_watched=True).all()
    total_watched = len(watched_items)
    
    genre_list = []
    for item in watched_items:
        if item.movie and item.movie.genres:
            for g in item.movie.genres.split(','):
                genre_list.append(g.strip())
    
    fav_genre = Counter(genre_list).most_common(1)[0][0] if genre_list else "Belirtilmemiş"

    return render_template(
        'profile.html', 
        partner=partner, 
        pending_requests=pending_requests, 
        pending_friend_requests=pending_friend_requests,
        total_watched=total_watched, 
        fav_genre=fav_genre
    )
@app.route('/update_avatar', methods=['POST'])
@login_required
def update_avatar():
    selected_avatar = request.form.get('avatar')
    print("SEÇİLEN AVATAR:", selected_avatar) # Konsolda (terminalde) görünüp görünmediğini kontrol etmek için
    if selected_avatar:
        current_user.avatar = selected_avatar
        db.session.commit()
        flash('Profil karakteriniz başarıyla güncellendi.', 'success')
    else:
        flash('Lütfen bir karakter seçin', 'error')
    return redirect(url_for('profile'))

# Üst menüde yeşil bildirim ışığı için her sayfaya sayaç ekleyen yardımcı fonksiyon
@app.context_processor
def inject_pending_requests():
    count = 0
    if current_user.is_authenticated:
        count = PartnerRequest.query.filter_by(receiver_id=current_user.id, status='pending').count()
    return dict(pending_requests_count=count)
@app.route('/remove_partner', methods=['POST'])
@login_required
def remove_partner():
    if current_user.partner_id:
        partner_id = current_user.partner_id
        partner = User.query.get(partner_id)
        
        if partner:
            partner.partner_id = None
        current_user.partner_id = None
        
        # Bu iki kullanıcı arasındaki tüm partnerlik isteklerini tamamen temizle
        old_requests = PartnerRequest.query.filter(
            ((PartnerRequest.sender_id == current_user.id) & (PartnerRequest.receiver_id == partner_id)) |
            ((PartnerRequest.sender_id == partner_id) & (PartnerRequest.receiver_id == current_user.id))
        ).all()
        
        for req in old_requests:
            db.session.delete(req)
            
        db.session.commit()
        flash('Partner bağlantısı kaldırıldı.', 'success')
    return redirect(url_for('profile'))
@app.route('/add_partner', methods=['POST'])
@login_required
def add_partner():
    partner_name = request.form.get('partner_name')
    partner = User.query.filter_by(username=partner_name).first()
    
    if not partner:
        flash('Böyle bir kullanıcı bulunamadı!', 'toast_error')
    elif partner.id == current_user.id:
        flash('Kendinizi partner olarak ekleyemezsiniz!', 'toast_error')
    elif current_user.partner_id:
        flash('Zaten bağlı bir partneriniz var!', 'toast_error')
    elif partner.partner_id:
        flash('Bu kullanıcının zaten bağlı bir partneri var!', 'toast_error')
    else:
        existing_req = PartnerRequest.query.filter_by(sender_id=current_user.id, receiver_id=partner.id, status='pending').first()
        if not existing_req:
            req = PartnerRequest(sender_id=current_user.id, receiver_id=partner.id)
            db.session.add(req)
            db.session.commit()
            flash('Partnerlik isteği gönderildi!', 'toast_success')
        else:
            flash('Bu kullanıcıya zaten bekleyen bir istek gönderdiniz!', 'toast_error')
            
    return redirect(request.referrer or url_for('pool'))

@app.route('/partner_action/<int:req_id>/<action>')
@login_required
def partner_action(req_id, action):
    req = PartnerRequest.query.get_or_404(req_id)
    if req.receiver_id == current_user.id:
        if action == 'accept':
            req.status = 'accepted'
            current_user.partner_id = req.sender_id
            sender = User.query.get(req.sender_id)
            if sender:
                sender.partner_id = current_user.id
            db.session.commit()
            flash('Partnerlik isteği kabul edildi!', 'success')
        elif action == 'reject':
            req.status = 'rejected'
            db.session.commit()
            flash('Partnerlik isteği reddedildi.', 'info')
    return redirect(url_for('profile'))
@app.route('/friends')
@login_required
def friends():
    accepted_requests = FriendRequest.query.filter(
        ((FriendRequest.sender_id == current_user.id) | (FriendRequest.receiver_id == current_user.id)) &
        (FriendRequest.status == 'accepted')
    ).all()
    
    friend_ids = []
    for req in accepted_requests:
        other_id = req.receiver_id if req.sender_id == current_user.id else req.sender_id
        friend_ids.append(other_id)
        
    friend_list = User.query.filter(User.id.in_(friend_ids)).all() if friend_ids else []
    
    # Arkadaşların film ve dizi verilerini hazırlıyoruz
    member_movies_data = {}
    member_series_data = {}
    member_top_four_data = {}
    member_top_four_series_data = {}

    for f in friend_list:
        # Filmler
        watched_items = WeeklyCalendar.query.filter_by(user_id=f.id, is_watched=True).all()
        member_movies_data[f.username] = [
            {
                'title': item.movie.title,
                'poster_url': item.movie.poster_url,
                'movie_id': item.movie_id,
                'director': item.movie.director if hasattr(item.movie, 'director') else '',
                'scheduled_date': item.scheduled_date,
                'user_rating': item.user_rating if item.user_rating else 0.0,
                'partner_rating': item.partner_rating if item.partner_rating else 0.0,
                'user_comment': item.user_comment if item.user_comment else '',
                'user_favorite': item.user_favorite if item.user_favorite else False,
            }
            for item in watched_items if item.movie
        ]

        # Diziler
        series_watched_items = SeriesCalendar.query.filter_by(user_id=f.id, is_watched=True).all()
        member_series_data[f.username] = [
            {
                'title': item.series.title,
                'poster_url': item.series.poster_url,
                'series_id': item.series_id,
                'director': item.series.director if hasattr(item.series, 'director') else '',
                'scheduled_date': item.scheduled_date,
                'user_rating': item.user_rating if item.user_rating else 0.0,
                'partner_rating': item.partner_rating if item.partner_rating else 0.0,
                'user_comment': item.user_comment if item.user_comment else '',
                'user_favorite': item.user_favorite if item.user_favorite else False,
            }
            for item in series_watched_items if item.series
        ]

        # Top 4 Favoriler (Eğer veritabanında modelin varsa buraya ekleyebilirsin, yoksa boş liste bırakır)
        member_top_four_data[f.username] = [None, None, None, None]
        member_top_four_series_data[f.username] = [None, None, None, None]

    return render_template(
        'friends.html', 
        friends=friend_list, 
        member_movies_data=member_movies_data,
        member_series_data=member_series_data,
        member_top_four_data=member_top_four_data,
        member_top_four_series_data=member_top_four_series_data
    )
@app.route('/remove_friend/<int:friend_id>', methods=['POST'])
@login_required
def remove_friend(friend_id):
    req = FriendRequest.query.filter(
        (((FriendRequest.sender_id == current_user.id) & (FriendRequest.receiver_id == friend_id)) |
         ((FriendRequest.sender_id == friend_id) & (FriendRequest.receiver_id == current_user.id))) &
        (FriendRequest.status == 'accepted')
    ).first()
    
    if req:
        db.session.delete(req)
        db.session.commit()
        flash("Arkadaşlıktan çıkarıldı.", "success")
    return redirect(url_for('friends'))

from datetime import datetime
@app.route('/journal')
@login_required
def journal():
    aylar = {
        1: 'Ocak', 2: 'Şubat', 3: 'Mart', 4: 'Nisan', 5: 'Mayıs', 6: 'Haziran',
        7: 'Temmuz', 8: 'Ağustos', 9: 'Eylül', 10: 'Ekim', 11: 'Kasım', 12: 'Aralık'
    }
    bugun = datetime.now()
    bugun_str = f"{bugun.day} {aylar[bugun.month]}"

    calendar_items = WeeklyCalendar.query.filter_by(user_id=current_user.id).all()
    series_calendar_items = SeriesCalendar.query.filter_by(user_id=current_user.id).all()
    
    # Tarihi belirlenmemiş (Ay havuzundaki) film ve diziler
    unassigned_movies = MonthPool.query.filter_by(user_id=current_user.id).all()
    unassigned_series = SeriesMonthPool.query.filter_by(user_id=current_user.id).all()    
    watched_items = WeeklyCalendar.query.filter_by(user_id=current_user.id, is_watched=True).all()
    watched_series_items = SeriesCalendar.query.filter_by(user_id=current_user.id, is_watched=True).all()
    
    all_movies = Movie.query.order_by(Movie.title.asc()).all()
    all_series = Series.query.order_by(Series.title.asc()).all()
    
    # --- BURASI GÜNCELLENDİ: Sadece kabul edilmiş arkadaşlar çekiliyor ---
    accepted_requests = FriendRequest.query.filter(
        ((FriendRequest.sender_id == current_user.id) | (FriendRequest.receiver_id == current_user.id)) &
        (FriendRequest.status == 'accepted')
    ).all()
    
    friend_ids = []
    for req in accepted_requests:
        other_id = req.receiver_id if req.sender_id == current_user.id else req.sender_id
        friend_ids.append(other_id)
        
    friends = User.query.filter(User.id.in_(friend_ids)).all() if friend_ids else []
    # ------------------------------------------------------------------
    
    top_four_items = TopFourMovie.query.filter_by(user_id=current_user.id).all()
    top_four_dict = {item.slot_index: item for item in top_four_items}

    top_four_series = TopFourSeries.query.filter_by(user_id=current_user.id).all()
    top_four_series_dict = {item.slot_index: item for item in top_four_series}

    return render_template(
        'journal.html', 
        bugun_str=bugun_str,
        calendar_items=calendar_items, 
        series_calendar_items=series_calendar_items,
        unassigned_movies=unassigned_movies,
        unassigned_series=unassigned_series,
        watched_items=watched_items, 
        watched_series_items=watched_series_items,
        all_movies=all_movies, 
        all_series=all_series,
        friends=friends,
        top_four_dict=top_four_dict,
        top_four_series_dict=top_four_series_dict
    )

@app.route('/update_series_journal_review/<int:entry_id>', methods=['POST'])
@login_required
def update_series_journal_review(entry_id):
    entry = SeriesCalendar.query.get_or_404(entry_id)
    if entry.user_id != current_user.id:
        return "Yetkisiz işlem", 403

    entry.user_rating = float(request.form.get('user_rating', 0))
    entry.user_comment = request.form.get('user_comment', '')
    entry.user_favorite = True if request.form.get('user_favorite') == 'on' else False
    entry.user_updated_at = datetime.now().strftime('%Y-%m-%d %H:%M')
    entry.is_watched = True  # <--- BURAYI EKLİYORUZ (Artık otomatik izlendi olacak ve yeşile dönecek)
    
    db.session.commit()
    flash('Dizi değerlendirmeniz başarıyla güncellendi!', 'success')
    return redirect(url_for('journal'))
@app.route('/toggle_series_watch/<int:entry_id>')
@login_required
def toggle_series_watch(entry_id):
    entry = SeriesCalendar.query.get_or_404(entry_id)
    if entry.user_id != current_user.id:
        return "Yetkisiz işlem", 403

    entry.is_watched = not entry.is_watched
    db.session.commit()
    return redirect(url_for('journal'))

@app.route('/update-top-four-series/<int:slot_index>', methods=['POST'])
@login_required
def update_top_four_series(slot_index):
    series_id = request.form.get('series_id')
    
    # Mevcut slot kaydını bulalım
    existing = TopFourSeries.query.filter_by(user_id=current_user.id, slot_index=slot_index).first()
    
    if not series_id: # Kaldırıldıysa veya boş seçildiyse
        if existing:
            db.session.delete(existing)
            db.session.commit()
    else:
        if existing:
            existing.series_id = int(series_id)
        else:
            new_tf = TopFourSeries(user_id=current_user.id, slot_index=slot_index, series_id=int(series_id))
            db.session.add(new_tf)
        db.session.commit()
        
    return redirect(url_for('journal'))
# Top 4 slotuna film kaydetme / güncelleme rotası
@app.route('/update_top_four/<int:slot_index>', methods=['POST'])
@login_required
def update_top_four(slot_index):
    movie_id = request.form.get('movie_id')
    
    existing = TopFourMovie.query.filter_by(user_id=current_user.id, slot_index=slot_index).first()
    if existing:
        existing.movie_id = movie_id if movie_id else None
    else:
        new_slot = TopFourMovie(user_id=current_user.id, slot_index=slot_index, movie_id=movie_id if movie_id else None)
        db.session.add(new_slot)
        
    db.session.commit()
    flash('Top 4 favorileriniz güncellendi!', 'success')
    return redirect(url_for('journal'))
@app.route('/journal/assign_from_pool/<int:pool_id>', methods=['POST'])
@login_required
def assign_from_pool(pool_id):
    print(f"👉 Gelen pool_id: {pool_id}")
    
    mp = MonthPool.query.get_or_404(pool_id)
    scheduled_date_str = request.form.get('scheduled_date')
    time_slot = request.form.get('time_slot', '20:00')
    partner_name = request.form.get('partner_name')
    
    print(f"👉 Tarih: {scheduled_date_str}, Film ID: {mp.movie_id}")

    if scheduled_date_str:
        try:
            parsed_date = datetime.strptime(scheduled_date_str, '%Y-%m-%d').date()
        except ValueError:
            parsed_date = scheduled_date_str

        entry = WeeklyCalendar(
            user_id=current_user.id,
            movie_id=mp.movie_id,
            scheduled_date=parsed_date,
            time_slot=time_slot,
            partner_name=partner_name if partner_name else None
        )
        db.session.add(entry)
        
        if partner_name:
            partner_user = User.query.filter_by(username=partner_name).first()
            if partner_user:
                p_entry = WeeklyCalendar(
                    user_id=partner_user.id,
                    movie_id=mp.movie_id,
                    scheduled_date=parsed_date,
                    time_slot=time_slot,
                    partner_name=current_user.username
                )
                db.session.add(p_entry)

        # MonthPool kaydını siliyoruz
        db.session.delete(mp)
        db.session.commit()
        print("✅ MonthPool kaydı başarıyla silindi ve veritabanı güncellendi.")
    else:
        print("❌ Hata: scheduled_date_str boş geldi!")
        
    return redirect(url_for('journal'))
@app.route('/journal/assign', methods=['POST'])
@login_required
def assign_journal():
    movie_id = request.form.get('movie_id')
    series_id = request.form.get('series_id')
    partner_name = request.form.get('partner_name')
    scheduled_date = request.form.get('scheduled_date')
    time_slot = request.form.get('time_slot', '20:00')

    # Eğer film seçildiyse
    if movie_id and movie_id != '':
        # Senin için kayıt
        new_entry = WeeklyCalendar(
            user_id=current_user.id,
            movie_id=int(movie_id),
            partner_name=partner_name if partner_name else None,
            scheduled_date=scheduled_date,
            time_slot=time_slot,
            is_watched=False
        )
        db.session.add(new_entry)
        
        # Eğer bir eşlikçi (partner) seçildiyse, onun takvimine de ekleyelim
        if partner_name:
            partner_user = User.query.filter_by(username=partner_name).first()
            if partner_user:
                partner_entry = WeeklyCalendar(
                    user_id=partner_user.id,
                    movie_id=int(movie_id),
                    partner_name=current_user.username,
                    scheduled_date=scheduled_date,
                    time_slot=time_slot,
                    is_watched=False
                )
                db.session.add(partner_entry)
    
    # Eğer dizi seçildiyse
    if series_id and series_id != '':
        new_series_entry = SeriesCalendar(
            user_id=current_user.id,
            series_id=int(series_id),
            partner_name=partner_name if partner_name else None,
            scheduled_date=scheduled_date,
            time_slot=time_slot,
            is_watched=False
        )
        db.session.add(new_series_entry)
        
        # Eşlikçi için dizi takvimi kaydı
        if partner_name:
            partner_user = User.query.filter_by(username=partner_name).first()
            if partner_user:
                partner_series_entry = SeriesCalendar(
                    user_id=partner_user.id,
                    series_id=int(series_id),
                    partner_name=current_user.username,
                    scheduled_date=scheduled_date,
                    time_slot=time_slot,
                    is_watched=False
                )
                db.session.add(partner_series_entry)

    db.session.commit()
    flash('İçerik başarıyla takvime planlandı!', 'success')
    return redirect(url_for('journal'))

@app.route('/update_journal_review/<int:item_id>', methods=['POST'])
@login_required
def update_journal_review(item_id):
    item = WeeklyCalendar.query.get_or_404(item_id)
    
    new_rating = float(request.form.get('user_rating', 0.0))
    new_comment = request.form.get('user_comment', '')
    new_favorite = True if request.form.get('user_favorite') == 'on' else False
    current_date_str = datetime.now().strftime('%Y-%m-%d')
    
    item.user_rating = new_rating
    item.user_comment = new_comment
    item.user_favorite = new_favorite
    item.user_updated_at = current_date_str
    item.is_watched = True
    
    partner_user = User.query.filter_by(username=item.partner_name).first() if item.partner_name else None
    if partner_user:
        partner_item = WeeklyCalendar.query.filter_by(
            user_id=partner_user.id,
            movie_id=item.movie_id,
            scheduled_date=item.scheduled_date
        ).first()
        
        if partner_item:
            partner_item.partner_rating = new_rating
            partner_item.partner_comment = new_comment
            partner_item.partner_favorite = new_favorite
            partner_item.partner_updated_at = current_date_str
            partner_item.is_watched = True
            
            item.partner_rating = partner_item.user_rating
            item.partner_comment = partner_item.user_comment
            item.partner_updated_at = current_date_str
            partner_item.partner_rating = item.user_rating
            partner_item.partner_comment = item.user_comment
            partner_item.user_updated_at = current_date_str

    db.session.commit()
    flash('Değerlendirmeler başarıyla kaydedildi!', 'success')
    return redirect(request.referrer or url_for('pool'))

@app.route('/toggle_watch/<int:item_id>')
@login_required
def toggle_watch(item_id):
    item = WeeklyCalendar.query.get_or_404(item_id)
    if item.user_id == current_user.id:
        item.is_watched = not item.is_watched
        db.session.commit()
    return redirect(url_for('journal'))

@app.route('/watched')
@login_required
def watched():
    watched_items = WeeklyCalendar.query.filter_by(user_id=current_user.id, is_watched=True).all()
    return render_template('watched.html', watched_items=watched_items)

@app.route('/members')
@login_required
def members():
    users = User.query.all()
    user_stats = {}
    member_movies_data = {}
    member_top_four_data = {}
    member_series_data = {}         # YENİ: Dizi izlenenler verisi
    member_top_four_series_data = {} # YENİ: Top 4 diziler verisi
    friend_statuses = {}
    partner_statuses = {}
    
    for u in users:
        watched_items = WeeklyCalendar.query.filter_by(user_id=u.id, is_watched=True).all()
        total = len(watched_items)
        
        genre_counts = {}
        for item in watched_items:
            if item.movie and item.movie.genres:
                for g in item.movie.genres.split(','):
                    genre = g.strip()
                    genre_counts[genre] = genre_counts.get(genre, 0) + 1
        fav_genre = max(genre_counts, key=genre_counts.get) if genre_counts else "Veri Yok"
        
        user_stats[u.id] = {
            'total': total,
            'fav_genre': fav_genre
        }

        member_movies_data[u.username] = [
            {
                'title': item.movie.title,
                'poster_url': item.movie.poster_url,
                'movie_id': item.movie_id,
                'scheduled_date': item.scheduled_date,
                'user_rating': item.user_rating if item.user_rating else 0.0,
                'partner_rating': item.partner_rating if item.partner_rating else 0.0,
                'user_favorite': item.user_favorite if hasattr(item, 'user_favorite') else False
            }
            for item in watched_items if item.movie
        ]

        # --- Üyenin Top 4 Favori Filmlerini Çekiyoruz ---
        top_four_records = TopFourMovie.query.filter_by(user_id=u.id).all()
        top_four_list = []
        for slot in range(1, 5):
            rec = next((tf for tf in top_four_records if tf.slot_index == slot), None)
            if rec and rec.movie:
                top_four_list.append({
                    'title': rec.movie.title,
                    'poster_url': rec.movie.poster_url,
                    'movie_id': rec.movie_id
                })
            else:
                top_four_list.append(None)
        member_top_four_data[u.username] = top_four_list

        # --- YENİ: Üyenin İzlenen Dizilerini Çekiyoruz ---
        watched_series_items = SeriesCalendar.query.filter_by(user_id=u.id, is_watched=True).all()
        member_series_data[u.username] = [
            {
                'title': item.series.title,
                'poster_url': item.series.poster_url,
                'series_id': item.series_id,
                'scheduled_date': item.scheduled_date,
                'user_rating': item.user_rating if item.user_rating else 0.0,
                'partner_rating': item.partner_rating if item.partner_rating else 0.0,
                'user_favorite': item.user_favorite if hasattr(item, 'user_favorite') else False,
                'director': item.series.creator
            }
            for item in watched_series_items if item.series
        ]

        # --- YENİ: Üyenin Top 4 Favori Dizilerini Çekiyoruz ---
        top_four_series_records = TopFourSeries.query.filter_by(user_id=u.id).all()
        top_four_series_list = []
        for slot in range(1, 5):
            rec = next((tf for tf in top_four_series_records if tf.slot_index == slot), None)
            if rec and rec.series:
                top_four_series_list.append({
                    'title': rec.series.title,
                    'poster_url': rec.series.poster_url,
                    'series_id': rec.series_id
                })
            else:
                top_four_series_list.append(None)
        member_top_four_series_data[u.username] = top_four_series_list

        if u.id != current_user.id:
            f_req = FriendRequest.query.filter(
                db.or_(
                    db.and_(FriendRequest.sender_id == current_user.id, FriendRequest.receiver_id == u.id),
                    db.and_(FriendRequest.sender_id == u.id, FriendRequest.receiver_id == current_user.id)
                )
            ).first()
            friend_statuses[u.id] = f_req.status if f_req else None

            p_req = PartnerRequest.query.filter(
                db.or_(
                    db.and_(PartnerRequest.sender_id == current_user.id, PartnerRequest.receiver_id == u.id),
                    db.and_(PartnerRequest.sender_id == u.id, PartnerRequest.receiver_id == current_user.id)
                )
            ).first()
            partner_statuses[u.id] = p_req.status if p_req else None
        
    return render_template(
        'members.html', 
        users=users, 
        user_stats=user_stats, 
        member_movies_data=member_movies_data,
        member_top_four_data=member_top_four_data,
        friend_statuses=friend_statuses,
        partner_statuses=partner_statuses,
        member_series_data=member_series_data,
        member_top_four_series_data=member_top_four_series_data
    )

@app.route('/cancel_friend_request/<int:user_id>', methods=['POST'])
@login_required
def cancel_friend_request(user_id):
    req = FriendRequest.query.filter_by(sender_id=current_user.id, receiver_id=user_id, status='pending').first()
    if req:
        db.session.delete(req)
        db.session.commit()
        flash("Arkadaşlık isteği geri çekildi.", "info")
    return redirect(url_for('members'))

@app.route('/cancel_partner_request/<int:user_id>', methods=['POST'])
@login_required
def cancel_partner_request(user_id):
    req = PartnerRequest.query.filter_by(sender_id=current_user.id, receiver_id=user_id, status='pending').first()
    if req:
        db.session.delete(req)
        db.session.commit()
        flash("Partnerlik teklifi geri çekildi.", "info")
    return redirect(url_for('members'))

# Veritabanı Modelleri (app.py içerisinde uygun bir yere ekleyin)
class FriendRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending') # pending, accepted, rejected

class PartnerRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')

@app.route('/send_friend_request/<int:user_id>', methods=['POST'])
@login_required
def send_friend_request(user_id):
    if user_id == current_user.id:
        flash("Kendinize arkadaşlık isteği gönderemezsiniz.", "danger")
        return redirect(url_for('members'))
    
    existing = FriendRequest.query.filter_by(sender_id=current_user.id, receiver_id=user_id, status='pending').first()
    if not existing:
        req = FriendRequest(sender_id=current_user.id, receiver_id=user_id)
        db.session.add(req)
        db.session.commit()
        flash("Arkadaşlık isteği gönderildi.", "success")
    else:
        flash("Bu kullanıcıya zaten bekleyen bir isteğiniz var.", "warning")
    return redirect(url_for('members'))

@app.route('/accept_friend/<int:req_id>', methods=['POST'])
@login_required
def accept_friend(req_id):
    req = FriendRequest.query.get_or_404(req_id)
    if req.receiver_id == current_user.id:
        req.status = 'accepted'
        db.session.commit()
        flash("Arkadaşlık isteği kabul edildi!", "success")
    return redirect(url_for('profile'))

@app.route('/reject_friend/<int:req_id>', methods=['POST'])
@login_required
def reject_friend(req_id):
    req = FriendRequest.query.get_or_404(req_id)
    if req.receiver_id == current_user.id:
        req.status = 'rejected'
        db.session.commit()
        flash("Arkadaşlık isteği reddedildi.", "info")
    return redirect(url_for('profile'))

@app.context_processor
def inject_pending_requests():
    partner_count = 0
    friend_count = 0
    if current_user.is_authenticated:
        partner_count = PartnerRequest.query.filter_by(receiver_id=current_user.id, status='pending').count()
        friend_count = FriendRequest.query.filter_by(receiver_id=current_user.id, status='pending').count()
    return dict(pending_requests_count=(partner_count + friend_count))
@app.route('/send_partner_request/<int:user_id>', methods=['POST'])
@login_required
def send_partner_request(user_id):
    if user_id == current_user.id:
        flash("Kendinize partnerlik teklifi gönderemezsiniz.", "danger")
        return redirect(url_for('members'))
    
    existing = PartnerRequest.query.filter_by(sender_id=current_user.id, receiver_id=user_id, status='pending').first()
    if not existing:
        req = PartnerRequest(sender_id=current_user.id, receiver_id=user_id)
        db.session.add(req)
        db.session.commit()
        flash("Partnerlik teklifi başarıyla gönderildi.", "success")
    else:
        flash("Bu kullanıcıya zaten bekleyen bir teklifiniz var.", "warning")
    return redirect(url_for('members'))

@app.route('/accept_partner/<int:req_id>', methods=['POST'])
@login_required
def accept_partner(req_id):
    req = PartnerRequest.query.get_or_404(req_id)
    if req.receiver_id == current_user.id:
        req.status = 'accepted'
        current_user.partner_id = req.sender_id
        sender = User.query.get(req.sender_id)
        if sender:
            sender.partner_id = current_user.id
        db.session.commit()
        flash("Partnerlik teklifi kabul edildi!", "success")
    return redirect(url_for('profile'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False # Çeltik işaretlenmiş mi?
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user, remember=remember) # Beni hatırla aktifleşir
            return redirect(url_for('pool'))
        else:
            flash('Hatalı kullanıcı adı veya şifre')
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # E-posta daha önce kullanılmış mı kontrolü
        if User.query.filter_by(email=email).first():
            flash('Bu e-posta adresi zaten kullanımda.', 'error')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password, method='scrypt')
        
        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Kayıt başarılı! Şimdi giriş yapabilirsiniz.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/journal/remove_pool/<int:pool_id>')
@login_required
def remove_from_month_pool(pool_id):
    mp = MonthPool.query.get_or_404(pool_id)
    if mp.user_id == current_user.id:
        db.session.delete(mp)
        db.session.commit()
        flash('Film ay havuzundan kaldırıldı.', 'info')
    return redirect(url_for('journal'))

@app.route('/member/<int:user_id>')
@login_required
def member_journal(user_id):
    member = User.query.get_or_404(user_id)
    watched_items = WeeklyCalendar.query.filter_by(user_id=member.id, is_watched=True).all()
    return render_template('member_journal.html', member=member, watched_items=watched_items)

from werkzeug.security import generate_password_hash
@app.route('/update_username', methods=['POST'])
@login_required
def update_username():
    new_username = request.form.get('username')
    if new_username:
        existing_user = User.query.filter_by(username=new_username).first()
        if existing_user and existing_user.id != current_user.id:
            flash('Bu kullanıcı adı zaten alınmış.', 'danger')
        else:
            current_user.username = new_username
            db.session.commit()
            flash('Kullanıcı adınız başarıyla güncellendi.', 'success') # Yeşil başarı mesajı
    return redirect(url_for('profile'))

@app.route('/update_password', methods=['POST'])
@login_required
def update_password():
    new_password = request.form.get('new_password')
    if new_password:
        current_user.password = generate_password_hash(new_password)
        db.session.commit()
        flash('Şifreniz başarıyla güncellendi.', 'success') # Yeşil başarı mesajı
    return redirect(url_for('profile'))

import random

@app.route('/api/random-movie')
@login_required
def random_movie_api():
    movies = Movie.query.all()
    if not movies:
        return jsonify({'error': 'Film bulunamadı'}), 404
    
    selected = random.choice(movies)
    return jsonify({
        'id': selected.id,
        'title': selected.title,
        'director': selected.director or 'Belirtilmemiş',
        'genres': selected.genres or 'Belirtilmemiş',
        'poster_url': selected.poster_url
    })

@app.route('/api/random-series')
@login_required
def api_random_series():
    series_list = Series.query.all()
    if not series_list:
        return {'error': 'Havuzda hiç dizi bulunmuyor.'}, 404
    
    random_s = random.choice(series_list)
    return {
        'id': random_s.id,
        'title': random_s.title,
        'creator': random_s.creator,
        'genres': random_s.genres,
        'poster_url': random_s.poster_url
    }

# Şifre sıfırlama tokeni üretmek için secret key kullanıyoruz
def get_reset_token(user_id, expires_sec=1800):
    s = Serializer(app.config['SECRET_KEY'])
    return s.dumps({'user_id': user_id}, salt='password-reset-salt')

def verify_reset_token(token, expires_sec=1800):
    s = Serializer(app.config['SECRET_KEY'])
    try:
        user_id = s.loads(token, salt='password-reset-salt', max_age=expires_sec)['user_id']
    except:
        return None
    return User.query.get(user_id)

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user:
            token = get_reset_token(user.id)
            reset_url = url_for('reset_password', token=token, _external=True)
            
            # --- MAİL GÖNDERME KISMI ---
            # Canlıda veya testte mail göndermek için smtplib kullanıyoruz:
            import smtplib
            from email.message import EmailMessage

            msg = EmailMessage()
            msg['Subject'] = 'Berilay - Şifre Sıfırlama Talebi'
            msg['From'] = 'seninmailin@gmail.com'  # Kendi mail adresin
            msg['To'] = email
            msg.set_content(f'Şifrenizi sıfırlamak için şu bağlantıya tıklayın:\n{reset_url}\n\nEğer bu talebi siz yapmadıysanız dikkate almayın.')

            try:
                # Gmail SMTP ayarları (Google hesabından "Uygulama Şifresi" almalısın)
                with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                    smtp.login('berilayfilm@gmail.com', 'ansn kzvr brwr pjzw')
                    smtp.send_message(msg)
                flash('Şifre sıfırlama talimatları e-posta adresinize gönderildi.', 'success')
            except Exception as e:
                flash(f'Mail gönderilirken bir hata oluştu: {e}', 'error')
        else:
            flash('Bu e-posta adresine kayıtlı bir kullanıcı bulunamadı.', 'error')
            
        return redirect(url_for('login'))
        
    return render_template('forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = verify_reset_token(token)
    if not user:
        flash('Geçersiz veya süresi dolmuş bağlantı.', 'error')
        return redirect(url_for('forgot_password'))
        
    if request.method == 'POST':
        password = request.form.get('password')
        user.password = generate_password_hash(password, method='scrypt')
        db.session.commit()
        flash('Şifreniz başarıyla güncellendi! Giriş yapabilirsiniz.', 'success')
        return redirect(url_for('login'))
        
    return render_template('reset_password.html')
@app.route('/my-comments')
@login_required
def my_comments():
    # Film yorumları
    comments_items = WeeklyCalendar.query.filter_by(user_id=current_user.id).filter(
        WeeklyCalendar.user_comment != None,
        WeeklyCalendar.user_comment != ''
    ).all()
    
    # Dizi yorumları (YENİ)
    series_comments_items = SeriesCalendar.query.filter_by(user_id=current_user.id).filter(
        SeriesCalendar.user_comment != None,
        SeriesCalendar.user_comment != ''
    ).all()
    
    return render_template('my_comments.html', comments_items=comments_items, series_comments_items=series_comments_items)

import requests
@app.route('/person/<name>')
@login_required
def person_detail(name):
    person = Person.query.filter_by(name=name).first_or_404()
    
    movies = Movie.query.filter(
        db.or_(
            Movie.director.ilike(f"%{name}%"),
            Movie.cast_list.ilike(f"%{name}%")
        )
    ).all()

    series_list = Series.query.filter(
        db.or_(
            Series.creator.ilike(f"%{name}%"),
            Series.cast_list.ilike(f"%{name}%")
        )
    ).all()

    return render_template('person_detail.html', person=person, movies=movies, series_list=series_list)

class TopFourMovie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    slot_index = db.Column(db.Integer, nullable=False) # 1, 2, 3 veya 4
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'), nullable=True)
    
    movie = db.relationship('Movie')
@app.route('/actors')
@login_required
def actors_list():
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('q', '').strip()
    per_page = 30  # Her sayfada 30 kişi
    
    # Tüm kişileri ve filmleri/dizileri tek seferde belleğe çekiyoruz
    all_people = Person.query.all()
    person_map = {p.name.strip(): p.profile_url for p in all_people if p.name and p.profile_url}
    
    all_movies = Movie.query.all()
    all_series = Series.query.all()
    
    people_dict = {} # { isim: resim_url }
    
    # Filmleri tarama
    for m in all_movies:
        if m.director and m.director != "Unknown":
            d_name = m.director.strip()
            if d_name and d_name not in people_dict:
                people_dict[d_name] = person_map.get(d_name, "https://via.placeholder.com/185x278?text=No+Image")
                
        if m.cast_list and m.cast_images:
            names = m.cast_list.split(',')
            imgs = m.cast_images.split('|')
            for i in range(len(names)):
                c_name = names[i].strip()
                if c_name and c_name not in people_dict:
                    if c_name in person_map:
                        people_dict[c_name] = person_map[c_name]
                    else:
                        people_dict[c_name] = imgs[i] if i < len(imgs) and imgs[i] else "https://via.placeholder.com/185x278?text=No+Image"

    # Dizileri tarama
    for s in all_series:
        if s.creator and s.creator != "Unknown":
            c_name = s.creator.strip()
            if c_name and c_name not in people_dict:
                people_dict[c_name] = person_map.get(c_name, "https://via.placeholder.com/185x278?text=No+Image")
                
        if s.cast_list and s.cast_images:
            names = s.cast_list.split(',')
            imgs = s.cast_images.split('|')
            for i in range(len(names)):
                c_name = names[i].strip()
                if c_name and c_name not in people_dict:
                    if c_name in person_map:
                        people_dict[c_name] = person_map[c_name]
                    else:
                        people_dict[c_name] = imgs[i] if i < len(imgs) and imgs[i] else "https://via.placeholder.com/185x278?text=No+Image"

    # Arama filtresi varsa isme göre filtreleyelim
    filtered_people = {}
    for name, img in people_dict.items():
        if not search_query or search_query.lower() in name.lower():
            filtered_people[name] = img

    # --- ÖZEL SIRALAMA MANTIĞI ---
    # 1. Öncelik: Profil resmi olanlar (0), olmayanlar/placeholder olanlar en sonda (1)
    # 2. Öncelik: Kendi içlerinde isme göre alfabetik sıralama
    def sort_key(item):
        name, img = item
        no_image = 1 if (not img or "placeholder" in img.lower() or "no+image" in img.lower()) else 0
        return (no_image, name.lower())

    sorted_people = sorted(filtered_people.items(), key=sort_key)
    
    # Sayfalama (Pagination) mantığı
    total_items = len(sorted_people)
    total_pages = (total_items + per_page - 1) // per_page if total_items > 0 else 1
    
    if page < 1:
        page = 1
    elif page > total_pages and total_pages > 0:
        page = total_pages
        
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_people = sorted_people[start_idx:end_idx]
    
    class PaginationDummy:
        def __init__(self, page, per_page, total_items, total_pages):
            self.page = page
            self.per_page = per_page
            self.total = total_items
            self.pages = total_pages
            self.has_prev = page > 1
            self.prev_num = page - 1
            self.has_next = page < total_pages
            self.next_num = page + 1
            
        def iter_pages(self, left_edge=1, right_edge=1, left_current=2, right_current=2):
            last = 0
            for num in range(1, self.pages + 1):
                if num <= left_edge or \
                   (num > self.page - left_current - 1 and num < self.page + right_current) or \
                   num > self.pages - right_edge:
                    if last + 1 != num:
                        yield None
                    yield num
                    last = num

    pagination = PaginationDummy(page, per_page, total_items, total_pages)
    
    return render_template(
        'actors_list.html', 
        actors=paginated_people, 
        pagination=pagination, 
        search_query=search_query
    )
class Series(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tmdb_id = db.Column(db.Integer, unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    original_language = db.Column(db.String(10))
    poster_url = db.Column(db.String(500))
    backdrop_url = db.Column(db.String(500))
    overview = db.Column(db.Text)
    creator = db.Column(db.String(200)) # Dizilerde yönetmen yerine yaratıcı (creator) veya showrunner
    cast_list = db.Column(db.Text)
    cast_images = db.Column(db.Text)
    genres = db.Column(db.String(200))
    first_air_date = db.Column(db.String(50))
    number_of_seasons = db.Column(db.Integer)
    number_of_episodes = db.Column(db.Integer)
    awards = db.Column(db.Text)
    posters_gallery = db.Column(db.Text)
    backdrops_gallery = db.Column(db.Text)
    recommendations = db.Column(db.Text)

class SeriesCalendar(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    series_id = db.Column(db.Integer, db.ForeignKey('series.id'), nullable=False)
    scheduled_date = db.Column(db.String(50), nullable=False)
    time_slot = db.Column(db.String(20), default="20:00")
    partner_name = db.Column(db.String(100))
    is_watched = db.Column(db.Boolean, default=False)
    user_rating = db.Column(db.Float, default=0.0)
    user_comment = db.Column(db.Text)
    user_favorite = db.Column(db.Boolean, default=False)
    partner_rating = db.Column(db.Float, default=0.0)
    partner_comment = db.Column(db.Text)
    partner_favorite = db.Column(db.Boolean, default=False)
    
    series = db.relationship('Series')

class SeriesMonthPool(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    series_id = db.Column(db.Integer, db.ForeignKey('series.id'), nullable=False)
    
    series = db.relationship('Series')

class TopFourSeries(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    slot_index = db.Column(db.Integer, nullable=False) # 1, 2, 3 veya 4
    series_id = db.Column(db.Integer, db.ForeignKey('series.id'), nullable=True)
    
    series = db.relationship('Series')

import json
from sqlalchemy import or_

# Dizi türleri ve dilleri her seferinde DB'yi yormasın diye global önbellek
CACHED_SERIES_GENRES = []
CACHED_SERIES_LANGUAGES = []
@app.route('/series-pool')
@login_required
def series_pool():
    global CACHED_SERIES_GENRES, CACHED_SERIES_LANGUAGES
    
    page = request.args.get('page', 1, type=int)
    per_page = 20
    selected_genre = request.args.get('genre', '')
    selected_language = request.args.get('language', '')
    search_query = request.args.get('q', '').strip()

    try:
        with open("sıralı_dizi.json", "r", encoding="utf-8") as f:
            ordered_titles = json.load(f)
    except FileNotFoundError:
        ordered_titles = []

    title_to_index = {}
    for idx, title in enumerate(ordered_titles):
        clean_json_title = title.split('(')[0].strip().lower()
        title_to_index[clean_json_title] = idx

    query = Series.query

    if selected_genre:
        query = query.filter(Series.genres.ilike(f'%{selected_genre}%'))
    if selected_language:
        query = query.filter(Series.original_language == selected_language)
        
    all_series = query.all()

    # --- TÜRKÇE KARAKTER DUYARSIZ VE KISMI ARAMA YARDIMCISI ---
    def normalize_tr(text):
        if not text:
            return ""
        return text.replace('Ç', 'c').replace('ç', 'c') \
                   .replace('Ş', 's').replace('ş', 's') \
                   .replace('Ğ', 'g').replace('ğ', 'g') \
                   .replace('Ü', 'u').replace('ü', 'u') \
                   .replace('Ö', 'o').replace('ö', 'o') \
                   .replace('İ', 'i').replace('ı', 'i') \
                   .lower()

    if search_query:
        q_norm = normalize_tr(search_query)
        filtered_list = []
        for series in all_series:
            title_norm = normalize_tr(series.title)
            creator_norm = normalize_tr(series.creator)
            cast_norm = normalize_tr(series.cast_list)
            
            if q_norm in title_norm or q_norm in creator_norm or q_norm in cast_norm:
                filtered_list.append(series)
        all_series = filtered_list

    def sorting_key(series):
        clean_series_title = series.title.split('(')[0].strip().lower()
        if clean_series_title in title_to_index:
            return (0, title_to_index[clean_series_title])
        
        year = 0
        if series.first_air_date and len(series.first_air_date) >= 4:
            try:
                year = int(series.first_air_date[:4])
            except ValueError:
                year = 0
        return (1, -year)

    sorted_series = sorted(all_series, key=sorting_key)

    total = len(sorted_series)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_series = sorted_series[start:end]

    class Pagination:
        def __init__(self, page, per_page, total):
            self.page = page
            self.per_page = per_page
            self.total = total
            self.pages = (total + per_page - 1) // per_page if total > 0 else 1
            self.has_prev = page > 1
            self.has_next = page < self.pages
            self.prev_num = page - 1
            self.next_num = page + 1

        def iter_pages(self, left_edge=1, right_edge=1, left_current=2, right_current=2):
            return range(1, self.pages + 1)

    pagination = Pagination(page, per_page, total)

    if not CACHED_SERIES_GENRES or not CACHED_SERIES_LANGUAGES:
        raw_genres = [g[0] for g in db.session.query(Series.genres).distinct().all() if g[0]]
        CACHED_SERIES_GENRES = sorted(list(set([genre.strip() for sublist in raw_genres for genre in sublist.split(',')])))
        CACHED_SERIES_LANGUAGES = [l[0] for l in db.session.query(Series.original_language).distinct().all() if l[0]]

    # --- YENİ EKLENEN KISIM: Dizi ay havuzu ve takvim planlı/izlenmiş dizi ID'leri ---
    series_pool_records = SeriesMonthPool.query.filter_by(user_id=current_user.id).all()
    series_pool_ids = [item.series_id for item in series_pool_records]

    series_calendar_records = SeriesCalendar.query.filter_by(user_id=current_user.id).all()
    scheduled_series_ids = [item.series_id for item in series_calendar_records if item.scheduled_date]
    watched_series_ids = [item.series_id for item in series_calendar_records if item.is_watched]

    return render_template('series_pool.html',
                           movies=paginated_series,
                           pagination=pagination,
                           genres=CACHED_SERIES_GENRES,
                           languages=CACHED_SERIES_LANGUAGES,
                           selected_genre=selected_genre,
                           selected_language=selected_language,
                           search_query=search_query,
                           series_pool_ids=series_pool_ids,
                           scheduled_series_ids=scheduled_series_ids,
                           watched_series_ids=watched_series_ids)
@app.route('/series/<int:series_id>')
@login_required
def series_detail(series_id):
    series = Series.query.get_or_404(series_id)
    calendar_entry = SeriesCalendar.query.filter_by(user_id=current_user.id, series_id=series_id).first()
    all_calendar_entries = SeriesCalendar.query.filter_by(user_id=current_user.id, series_id=series_id).all()
    
    # Türkçe karakter duyarsızlaştırma fonksiyonu
    def normalize_tr(text):
        if not text:
            return ""
        return text.replace('Ç', 'c').replace('ç', 'c') \
                   .replace('Ş', 's').replace('ş', 's') \
                   .replace('Ğ', 'g').replace('ğ', 'g') \
                   .replace('Ü', 'u').replace('ü', 'u') \
                   .replace('Ö', 'o').replace('ö', 'o') \
                   .replace('İ', 'i').replace('ı', 'i') \
                   .lower()

    recommendations_with_status = []
    if series.tmdb_id:
        import requests
        API_KEY = "d973f8c77c29694c80e3cf888f853aa3"
        rec_url = f"https://api.themoviedb.org/3/tv/{series.tmdb_id}/recommendations?api_key={API_KEY}&language=tr-TR&page=1"
        res = requests.get(rec_url)
        
        if res.status_code == 200:
            rec_results = res.json().get('results', [])[:10]
            
            # Veritabanındaki tüm dizileri bir kere belleğe çekip esnek arama yapıyoruz
            all_db_series = Series.query.all()
            
            for r in rec_results:
                t_id = r.get('id')
                title = r.get('name') or r.get('original_name')
                poster_path = r.get('poster_path')
                poster = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else ""
                vote_avg = r.get('vote_average', 0)
                score = f"%{int(vote_avg * 10)}" if vote_avg else "N/A"
                
                # 1. Öncelik: tmdb_id ile birebir eşleşme var mı?
                found_s = Series.query.filter_by(tmdb_id=t_id).first()
                
                # 2. Öncelik: tmdb_id eşleşmediyse başlıkları esnek ve Türkçe karakter duyarsız kıyasla
                if not found_s and title:
                    rec_clean = normalize_tr(title.split('(')[0].strip())
                    for db_s in all_db_series:
                        db_clean = normalize_tr(db_s.title.split('(')[0].strip())
                        if rec_clean in db_clean or db_clean in rec_clean:
                            found_s = db_s
                            break

                recommendations_with_status.append({
                    'title': found_s.title if found_s else title,
                    'poster': poster,
                    'score': score,
                    'found_id': found_s.id if found_s else None
                })

    return render_template(
        'series_detail.html',
        series=series,
        calendar_entry=calendar_entry,
        all_calendar_entries=all_calendar_entries,
        recommendations_with_status=recommendations_with_status
    )

@app.route('/add-to-series-month-pool/<int:series_id>')
@login_required
def add_to_series_month_pool(series_id):
    # Kullanıcının ay havuzunda bu dizi zaten var mı kontrol edelim
    existing = SeriesMonthPool.query.filter_by(user_id=current_user.id, series_id=series_id).first()
    if not existing:
        new_pool_item = SeriesMonthPool(user_id=current_user.id, series_id=series_id)
        db.session.add(new_pool_item)
        db.session.commit()
        flash('Dizi başarıyla ay havuzuna eklendi!', 'success')
    else:
        flash('Bu dizi zaten ay havuzunuzda mevcut.', 'info')
    
    return redirect(url_for('series_pool'))
@app.route('/remove-from-series-month-pool/<int:pool_id>', methods=['POST'])
@login_required
def remove_from_series_month_pool(pool_id):
    item = SeriesMonthPool.query.get_or_404(pool_id)
    if item.user_id == current_user.id:
        db.session.delete(item)
        db.session.commit()
        flash('Dizi ay havuzundan kaldırıldı.', 'success')
    return redirect(url_for('journal'))
@app.route('/assign-series-from-pool/<int:pool_id>', methods=['POST'])
@login_required
def assign_series_from_pool(pool_id):
    pool_item = SeriesMonthPool.query.get_or_404(pool_id)
    if pool_item.user_id == current_user.id:
        scheduled_date = request.form.get('scheduled_date')
        time_slot = request.form.get('time_slot', '20:00')
        partner_name = request.form.get('partner_name', '')

        # Senin için takvim kaydı
        new_calendar_entry = SeriesCalendar(
            user_id=current_user.id,
            series_id=pool_item.series_id,
            scheduled_date=scheduled_date,
            time_slot=time_slot,
            partner_name=partner_name if partner_name else None,
            is_watched=False
        )
        db.session.add(new_calendar_entry)

        # Eğer partner seçildiyse onun takvimine de ekle
        if partner_name:
            partner_user = User.query.filter_by(username=partner_name).first()
            if partner_user:
                partner_entry = SeriesCalendar(
                    user_id=partner_user.id,
                    series_id=pool_item.series_id,
                    scheduled_date=scheduled_date,
                    time_slot=time_slot,
                    partner_name=current_user.username,
                    is_watched=False
                )
                db.session.add(partner_entry)

        db.session.delete(pool_item)
        db.session.commit()
        flash('Dizi başarıyla takvime planlandı!', 'success')
    return redirect(url_for('journal'))
@app.route('/remove_month_pool_item/<int:pool_id>', methods=['POST'])
@login_required
def remove_month_pool_item(pool_id):
    mp = MonthPool.query.filter_by(id=pool_id, user_id=current_user.id).first_or_404()
    db.session.delete(mp)
    db.session.commit()
    return redirect(url_for('journal'))

@app.route('/remove_series_month_pool_item/<int:pool_id>', methods=['POST'])
@login_required
def remove_series_month_pool_item(pool_id):
    msp = SeriesMonthPool.query.filter_by(id=pool_id, user_id=current_user.id).first_or_404()
    db.session.delete(msp)
    db.session.commit()
    return redirect(url_for('journal'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)