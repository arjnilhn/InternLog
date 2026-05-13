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

if __name__ == "__main__":
    app.run(debug=True)