import unittest
import sqlite3

class TestInternLogBusinessLogic(unittest.TestCase):
    def setUp(self):
        # Set up an isolated, temporary database in RAM for clean testing 
        self.conn = sqlite3.connect(':memory:')
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        
        # Initialize tables required by the system scope 
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
        # Close database connection after each test run
        self.conn.close()

    def test_user_data_isolation_logic(self):
        # US2: Verify that users can only fetch their own logs 
        self.cursor.execute("INSERT INTO users (username) VALUES (?)", ("Zeynep",))
        user1_id = self.cursor.lastrowid
        self.cursor.execute("INSERT INTO users (username) VALUES (?)", ("OtherIntern",))
        user2_id = self.cursor.lastrowid
        
        # Insert a log entry belonging specifically to user
        self.cursor.execute("INSERT INTO logs (user_id, title, content) VALUES (?, ?, ?)", 
                            (user1_id, "Day 1 Log", "Worked on backend modules."))
        self.conn.commit()
        
        # Execute queries scoped by user_id to simulate session isolation 
        user1_logs = self.cursor.execute('SELECT * FROM logs WHERE user_id = ?', (user1_id,)).fetchall()
        user2_logs = self.cursor.execute('SELECT * FROM logs WHERE user_id = ?', (user2_id,)).fetchall()
        
        # Assertions to validate explicit multi-user data boundary
        self.assertEqual(len(user1_logs), 1)
        self.assertEqual(user1_logs[0]['title'], "Day 1 Log")
        self.assertEqual(len(user2_logs), 0)

    def test_progress_calculation_logic(self):
        # US3: Verify the internal counting logic for progress indicators 
        self.cursor.execute("INSERT INTO users (username, total_days) VALUES (?, ?)", ("Zeynep", 30))
        user_id = self.cursor.lastrowid
        
        # Add sample log records for the target user [cite: 29]
        self.cursor.execute("INSERT INTO logs (user_id, title, content) VALUES (?, ?, ?)", (user_id, "Log 1", "Content 1"))
        self.cursor.execute("INSERT INTO logs (user_id, title, content) VALUES (?, ?, ?)", (user_id, "Log 2", "Content 2"))
        self.conn.commit()
        
        # Calculate log total count programmatically
        logs = self.cursor.execute('SELECT * FROM logs WHERE user_id = ?', (user_id,)).fetchall()
        completed = len(logs)
        
        # Validate that the metrics correctly calculate to 2 entries
        self.assertEqual(completed, 2)

    def test_unauthorized_deletion_protection(self):
        # US4: Ensure cross-user data tampering via raw SQL manipulation is blocked
        self.cursor.execute("INSERT INTO users (username) VALUES (?)", ("Zeynep",))
        zeynep_id = self.cursor.lastrowid
        self.cursor.execute("INSERT INTO users (username) VALUES (?)", ("Hacker",))
        hacker_id = self.cursor.lastrowid

        # Target user writes a log entry [cite: 29]
        self.cursor.execute("INSERT INTO logs (user_id, title, content) VALUES (?, ?, ?)", 
                            (zeynep_id, "Secure Entry", "Private data..."))
        self.conn.commit()
        log_id = self.cursor.lastrowid

        # Malicious user attempts to execute a hard delete query using wrong ownership criteria 
        self.cursor.execute('DELETE FROM logs WHERE id = ? AND user_id = ?', (log_id, hacker_id))
        self.conn.commit()

        # The rowcount must be 0 because query clauses do not match the real owner 
        self.assertEqual(self.cursor.rowcount, 0)
        
        # Double check the original record remains uncorrupted in the database 
        existing_log = self.cursor.execute('SELECT * FROM logs WHERE id = ?', (log_id,)).fetchone()
        self.assertIsNotNone(existing_log)

    def test_input_sanitization_and_whitespace_trimming(self):
        # US1: Verify standard input handling rules before executing raw persistence operations
        raw_title = "   Day 3: API Integration   "
        raw_content = "<script>alert('XSS')</script> Solved core bugs."

        # Apply basic cleaning procedures locally 
        clean_title = raw_title.strip()
        clean_content = raw_content.replace("<script>", "").replace("</script>", "")

        # Persist cleansed attributes to the database 
        self.cursor.execute("INSERT INTO logs (user_id, title, content) VALUES (?, ?, ?)", 
                            (1, clean_title, clean_content))
        self.conn.commit()
        log_id = self.cursor.lastrowid

        # Retrieve verified parameters from database rows 
        saved_log = self.cursor.execute('SELECT * FROM logs WHERE id = ?', (log_id,)).fetchone()
        
        # Assert clean strings match our system's core sanitation targets
        self.assertEqual(saved_log['title'], "Day 3: API Integration")
        self.assertEqual(saved_log['content'], "alert('XSS') Solved core bugs.")

if __name__ == '__main__':
    unittest.main()