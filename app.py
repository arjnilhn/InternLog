from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key_here' # Session güvenliği için şart [cite: 20]

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
        
        # Şifreyi hash'liyoruz (Güvenlik için çok kritik!) [cite: 1426, 1427]
        hashed_password = generate_password_hash(password)
        
        try:
            conn = get_db_connection()
            # Raw SQL kullanıyoruz, ORM yasak! [cite: 26]
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
        # Raw SQL ile kullanıcıyı buluyoruz [cite: 26]
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        # Şifre kontrolü (werkzeug ile hash kontrolü yapıyoruz)
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id'] # Session'a kullanıcı id'sini kaydediyoruz [cite: 20, 21]
            session['username'] = user['username']
            return redirect(url_for('dashboard'))
        else:
            return "Invalid username or password"
            
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    # Sadece giriş yapan kullanıcının günlüklerini getiriyoruz [cite: 21, 29]
    logs = conn.execute('SELECT * FROM logs WHERE user_id = ? ORDER BY created_at DESC', 
                        (session['user_id'],)).fetchall()
    
    # İş mantığı: Toplam staj gün sayısını hesapla (US3 için)
    total_days = len(logs) 
    
    conn.close()
    return render_template('dashboard.html', logs=logs, total_days=total_days)

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
        return redirect(url_for('dashboard'))
        
    return render_template('create_log.html')

# DELETE - Kayıt Silme
@app.route('/delete/<int:log_id>')
def delete_log(log_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    # Güvenlik Kontrolü: Sadece kendi kaydını silebilirsin!
    conn.execute('DELETE FROM logs WHERE id = ? AND user_id = ?', (log_id, session['user_id']))
    conn.commit()
    conn.close()
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
    session.clear()
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True)