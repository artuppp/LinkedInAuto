import sqlite3

def init_db():
    conn = sqlite3.connect("ideas.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ideas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            texto TEXT NOT NULL,
            alredy_posted BOOLEAN DEFAULT 0,
            final_post TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()
    conn.close()

    conn = sqlite3.connect("media.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE idea_media (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            idea_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            path TEXT NOT NULL,
            original_file_id TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (idea_id) REFERENCES ideas(id) ON DELETE CASCADE
    );
    """)
    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()