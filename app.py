from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, session, url_for, flash # flash 


app = Flask(__name__)
app.secret_key = 'your_secret_key_here' # Session güvenliği için şart [cite: 20]
from functools import wraps

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Veritabanı bağlantı yardımcısı
def get_db_connection():
    conn = sqlite3.connect('internship.db')
    conn.row_factory = sqlite3.Row # Verilere sözlük gibi erişmemizi sağlar
    return conn

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

# REGISTER (KAYIT) İŞLEMLERİ
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Şifreyi hash'liyoruz (Güvenlik için) [cite: 1426, 1427]
        hashed_password = generate_password_hash(password)
        
        try:
            conn = get_db_connection()
            
            conn.execute('INSERT INTO users (username, password) VALUES (?, ?)',
                         (username, hashed_password))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return "Username already exists!"
            
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('Successfully logged in!', 'success')
            return redirect(url_for('dashboard'))
        else:
            # KRİTİK NOKTA: Dashboard'a gitmiyoruz, tekrar login sayfasına yönlendiriyoruz
            flash('Invalid username or password', 'danger')
            return redirect(url_for('login')) # Seni login sayfasına geri atar ve mesajı gösterir
            
    return render_template('login.html')


@app.route('/create', methods=['GET', 'POST'])
def create_log():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        
        # Boş veri kontrolü (US1 Acceptance Criteria)
        if not title or not content:
            return "Title and Content are required!"
            
        conn = get_db_connection()
        conn.execute('INSERT INTO logs (user_id, title, content) VALUES (?, ?, ?)',
                     (session['user_id'], title, content))
        conn.commit()
        conn.close()
            # create
        flash('New internship log added!', 'success')
       
        return redirect(url_for('dashboard')) 
    
        
    return render_template('create_log.html')

@app.route('/delete/<int:log_id>', methods=['POST'])
@login_required
def delete_log(log_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM logs WHERE id = ? AND user_id = ?', (log_id, session['user_id']))
    conn.commit()
    conn.close()
    
    # Kullanıcıya gidecek mesaj burada:
    flash('Log entry successfully deleted!', 'success') 
    
    return redirect(url_for('dashboard'))

# EDIT - Kayıt Düzenleme
@app.route('/edit/<int:log_id>', methods=['GET', 'POST'])
def edit_log(log_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    # Önce düzenlenecek kaydı bulalım
    log = conn.execute('SELECT * FROM logs WHERE id = ? AND user_id = ?', (log_id, session['user_id'])).fetchone()
    
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        
        conn.execute('UPDATE logs SET title = ?, content = ? WHERE id = ? AND user_id = ?',
                     (title, content, log_id, session['user_id']))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))
        
    conn.close()
    return render_template('edit_log.html', log=log)

# Logout - Oturumu sonlandırma 
@app.route('/logout')
def logout():
    session.clear() # Tüm oturum bilgilerini temizler
    flash('You have been logged out.', 'info') # Mesajı sıraya ekler
    return redirect(url_for('login')) # Mesajın görüneceği sayfaya gönderir

@app.route('/export')
def export_logs():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    logs = conn.execute('SELECT * FROM logs WHERE user_id = ? ORDER BY created_at ASC', (session['user_id'],)).fetchall()
    conn.close()
    
    output = f"INTERNSHIP LOG REPORT - User: {session['username']}\n"
    output += "="*40 + "\n\n"
    
    for log in logs:
        output += f"Date: {log['created_at']}\nTitle: {log['title']}\nContent: {log['content']}\n"
        output += "-"*20 + "\n"
        
    # Dosya olarak indirmeyi sağlayan Response ayarı
    from flask import Response
    return Response(output, mimetype="text/plain", headers={"Content-disposition": "attachment; filename=internship_report.txt"})
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        conn = get_db_connection()
        user = conn.execute('SELECT password FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        
        # 1. Mevcut şifre kontrolü
        if not check_password_hash(user['password'], old_password):
            flash('Current password is incorrect!', 'danger')
            conn.close()
        # 2. Yeni şifrelerin eşleşme kontrolü
        elif new_password != confirm_password:
            flash('New passwords do not match!', 'danger')
            conn.close()
        # 3. Boş şifre kontrolü
        elif not new_password:
            flash('New password cannot be empty!', 'danger')
            conn.close()
        else:
            # Her şey yolunda, şifreyi güncelle
            hashed_password = generate_password_hash(new_password)
            conn.execute('UPDATE users SET password = ? WHERE id = ?', (hashed_password, session['user_id']))
            conn.commit()
            conn.close()
            flash('Your password has been updated successfully!', 'success')
            return redirect(url_for('profile'))
            
    return render_template('profile.html')
 
@app.route('/dashboard')
@login_required
def dashboard():
    # 1. Arama terimini URL'den alıyoruz (Giriş: ?search=...)
    search_query = request.args.get('search', '') 
    
    conn = get_db_connection()
    
    # 2. Kullanıcı bilgilerini çekiyoruz (Staj adı ve toplam gün için)
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    
    # 3. Logları Çekme (Eğer arama varsa filtrele, yoksa hepsini getir)
    if search_query:
        query = "SELECT * FROM logs WHERE user_id = ? AND (title LIKE ? OR content LIKE ?) ORDER BY created_at DESC"
        logs = conn.execute(query, (session['user_id'], f'%{search_query}%', f'%{search_query}%')).fetchall()
    else:
        logs = conn.execute('SELECT * FROM logs WHERE user_id = ? ORDER BY created_at DESC', (session['user_id'],)).fetchall()
    
    # 4. İstatistik Hesaplamaları
    total = user['total_days'] if user['total_days'] else 20
    title = user['internship_name'] if user['internship_name'] else "My Internship"
    completed = len(logs)
    remaining = total - completed if (total - completed) > 0 else 0
    
    conn.close()
    
    # 5. Her şeyi Template'e gönderiyoruz (Arama kutusunun içi boş kalmasın diye search_query'yi de yolluyoruz)
    return render_template('dashboard.html', 
                           logs=logs, 
                           remaining=remaining, 
                           total=total, 
                           title=title, 
                           completed=completed,
                           search_query=search_query)

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    conn = get_db_connection()
    if request.method == 'POST':
        name = request.form['internship_name']
        days = request.form['total_days']
        
        # Veritabanındaki internship_name ve total_days sütunlarını günceller
        conn.execute('UPDATE users SET internship_name = ?, total_days = ? WHERE id = ?', 
                     (name, days, session['user_id']))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))
    
    # Sayfa ilk açıldığında mevcut bilgileri kutucuklara doldurur
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    conn.close()
    return render_template('settings.html', user=user)

if __name__ == "__main__":
    app.run(debug=True)