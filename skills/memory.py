import sqlite3
import os

DB_PATH = 'freebot_memory.db'

def init_db():
    """Initializes the SQLite database and creates the table if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS memories (
            user_id TEXT,
            fact TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_fact(user_id, fact):
    """Saves a fact to the database and COMMITS the change."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO memories (user_id, fact) VALUES (?, ?)', (str(user_id), fact))
    conn.commit()  # <--- THIS IS THE FIX
    conn.close()
    print(f"DEBUG: Saved to DB for {user_id}: {fact}")

def get_memories(user_id):
    """Retrieves all facts for a specific user."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT fact FROM memories WHERE user_id = ?', (str(user_id),))
    results = [row[0] for row in cursor.fetchall()]
    conn.close()
    return results
