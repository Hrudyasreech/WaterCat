import sqlite3
import os
from datetime import datetime
import src.config as config

DB_PATH = os.path.join(config.BASE_DIR, "watercat.db")

def init_db():
    """Initialize the database and create tables if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS drinks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def record_drink():
    """Record that the user drank water."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO drinks DEFAULT VALUES")
    conn.commit()
    conn.close()

def get_drinks_today():
    """Return the number of drinks recorded today (local time)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # SQLite CURRENT_TIMESTAMP is UTC. We can just use DATE('now', 'localtime')
    cursor.execute("""
        SELECT COUNT(*) FROM drinks 
        WHERE date(timestamp, 'localtime') = date('now', 'localtime')
    """)
    count = cursor.fetchone()[0]
    conn.close()
    return count
