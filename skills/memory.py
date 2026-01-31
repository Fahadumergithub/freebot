import sqlite3
import datetime

DB_PATH = 'freebot_memory.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS memories (user_id TEXT, fact TEXT, timestamp DATETIME)')
    conn.commit()
    conn.close()

def save_fact(user_id, fact):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO memories VALUES (?, ?, ?)', (str(user_id), fact, datetime.datetime.now()))
    conn.commit()
    conn.close()

def get_memories(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT fact FROM memories WHERE user_id = ? ORDER BY timestamp DESC LIMIT 15', (str(user_id),))
    facts = [row[0] for row in c.fetchall()]
    conn.close()
    return facts
