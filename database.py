import sqlite3
import os
import threading

class Database:
    def __init__(self, db_file="songs.db"):
        # Ensure the database directory exists
        os.makedirs(os.path.dirname(db_file) if os.path.dirname(db_file) else '.', exist_ok=True)

        # Use threading.local() to handle per-thread connection
        self.local_storage = threading.local()
        self.db_file = db_file

    def get_connection(self):
        if not hasattr(self.local_storage, 'conn'):
            # Create a new SQLite connection for the current thread
            self.local_storage.conn = sqlite3.connect(self.db_file, check_same_thread=False)
            self.create_tables(self.local_storage.conn)
        return self.local_storage.conn

    def create_tables(self, conn):
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS songs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            file_path TEXT UNIQUE NOT NULL,
            thumbnail TEXT,
            duration INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        conn.commit()

    def add_song(self, title, file_path, thumbnail, duration):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO songs (title, file_path, thumbnail, duration)
        VALUES (?, ?, ?, ?)
        ''', (title, file_path, thumbnail, duration))
        conn.commit()
        return cursor.lastrowid

    def get_song_by_path(self, file_path):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM songs WHERE file_path = ?', (file_path,))
        return cursor.fetchone()

    def get_all_songs(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM songs ORDER BY created_at DESC')
        return cursor.fetchall()

    def delete_song(self, song_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        # First get the file path to delete the actual file
        cursor.execute('SELECT file_path FROM songs WHERE id = ?', (song_id,))
        result = cursor.fetchone()
        if result:
            file_path = result[0]
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError:
                    pass  # Handle file deletion error gracefully
                    
        cursor.execute('DELETE FROM songs WHERE id = ?', (song_id,))
        conn.commit()

    def __del__(self):
        if hasattr(self.local_storage, 'conn'):
            self.local_storage.conn.close()
