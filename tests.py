import unittest
import sqlite3

class TestInternLogBusinessLogic(unittest.TestCase):
    def setUp(self):
        """Her testten önce RAM üzerinde geçici bir test veritabanı kurar."""
        self.conn = sqlite3.connect(':memory:')
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        
        # Test tablolarını oluştur (Hocanın istediği en az 2 tablo kuralı)
        self.cursor.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                internship_name TEXT,
                total_days INTEGER
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                title TEXT,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    def tearDown(self):
        """Test bittiğinde geçici bağlantıyı kapatır."""
        self.conn.close()

    def test_user_data_isolation_logic(self):
        """Kılavuz 1.3 & US2: Farklı kullanıcıların birbirinin verisini görmediğini test eder."""
        # İki farklı kullanıcı ekle
        self.cursor.execute("INSERT INTO users (username) VALUES (?)", ("Zeynep",))
        user1_id = self.cursor.lastrowid
        self.cursor.execute("INSERT INTO users (username) VALUES (?)", ("Diğer Stajyer",))
        user2_id = self.cursor.lastrowid
        
        # Sadece Zeynep için bir log ekle
        self.cursor.execute("INSERT INTO logs (user_id, title, content) VALUES (?, ?, ?)", 
                            (user1_id, "Zeynep'in Günlüğü", "Bugün backend yazdım."))
        self.conn.commit()
        
        # Veritabanından sorgula
        zeynep_logs = self.cursor.execute('SELECT * FROM logs WHERE user_id = ?', (user1_id,)).fetchall()
        diger_logs = self.cursor.execute('SELECT * FROM logs WHERE user_id = ?', (user2_id,)).fetchall()
        
        # Doğrulama: Herkes sadece kendi verisine erişebilmeli
        self.assertEqual(len(zeynep_logs), 1)
        self.assertEqual(zeynep_logs[0]['title'], "Zeynep'in Günlüğü")
        self.assertEqual(len(diger_logs), 0)

    def test_progress_calculation_logic(self):
        """Kılavuz US3: Log sayısının otomatik ve doğru hesaplandığını test eder."""
        self.cursor.execute("INSERT INTO users (username, total_days) VALUES (?, ?)", ("Zeynep", 30))
        user_id = self.cursor.lastrowid
        
        # Kullanıcı 2 adet log ekliyor
        self.cursor.execute("INSERT INTO logs (user_id, title, content) VALUES (?, ?, ?)", (user_id, "Day 1", "Content 1"))
        self.cursor.execute("INSERT INTO logs (user_id, title, content) VALUES (?, ?, ?)", (user_id, "Day 2", "Content 2"))
        self.conn.commit()
        
        # İş mantığı hesaplaması
        logs = self.cursor.execute('SELECT * FROM logs WHERE user_id = ?', (user_id,)).fetchall()
        completed = len(logs)
        
        # Doğrulama: Log sayısı tam olarak 2 olmalı
        self.assertEqual(completed, 2)

if __name__ == '__main__':
    unittest.main()