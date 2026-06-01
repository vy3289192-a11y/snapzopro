import sqlite3

conn = sqlite3.connect('news.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        image_path TEXT,
        seo_tags TEXT,
        status TEXT DEFAULT 'published',
        category TEXT DEFAULT 'General',
        views INTEGER DEFAULT 0,
        react_fire INTEGER DEFAULT 0,
        react_shock INTEGER DEFAULT 0,
        react_sad INTEGER DEFAULT 0,
        react_angry INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

conn.commit()
conn.close()
print("Database Created with Reactions & Infinite Scroll Support!")