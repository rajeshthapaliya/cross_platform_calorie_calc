import os
import sqlite3

# Cross-platform database path
DB_FILE = os.path.join(os.path.dirname(__file__), "..", "calorie_pro.db")

def db_connect():
    """Establishes and returns a connection to the SQLite database."""
    return sqlite3.connect(DB_FILE)

def setup_database():
    """Creates the necessary tables if they don't exist."""
    conn = db_connect()
    cur = conn.cursor()
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            gender TEXT,
            age INTEGER,
            height_cm REAL,
            weight_kg REAL,
            activity TEXT,
            goal TEXT,
            macro_json TEXT
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS foods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            log_date TEXT,
            name TEXT,
            calories REAL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS exercises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            log_date TEXT,
            name TEXT,
            calories_burned REAL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS weights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            log_date TEXT,
            weight_kg REAL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    conn.commit()
    conn.close()
