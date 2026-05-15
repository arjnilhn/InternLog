from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, session, url_for, flash # flash 


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
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    search_query = request.args.get('search', '') # Arama terimini al
    conn = get_db_connection()
    
    if search_query:
        # Arama terimi varsa filtrele
        query = "SELECT * FROM logs WHERE user_id = ? AND (title LIKE ? OR content LIKE ?) ORDER BY created_at DESC"
        logs = conn.execute(query, (session['user_id'], f'%{search_query}%', f'%{search_query}%')).fetchall()
    else:
        # Yoksa hepsini getir
        logs = conn.execute('SELECT * FROM logs WHERE user_id = ? ORDER BY created_at DESC', (session['user_id'],)).fetchall()
    
    total_days = len(logs)
    conn.close()
    return render_template('dashboard.html', logs=logs, total_days=total_days, search_query=search_query)

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

# DELETE - Kayıt Silme
@app.route('/delete/<int:log_id>')
def delete_log(log_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    # Güvenlik Kontrolü: Sadece kendi kaydını silebilir
    conn.execute('DELETE FROM logs WHERE id = ? AND user_id = ?', (log_id, session['user_id']))
    conn.commit()
    conn.close()
     # delete
    flash('Log entry deleted successfully!', 'info')
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

if __name__ == "__main__":
    app.run(debug=True)