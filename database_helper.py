import sqlite3
import os

database_folder = "/data/database"
ideas_database = "/data/database/ideas.db"
media_database = "/data/database/media.db"


def init_ideas_db():
    conn = sqlite3.connect(ideas_database)
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


def init_media_db():
    conn = sqlite3.connect(media_database)
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


def initialize_database():
    if not os.path.exists(database_folder):
        os.makedirs(database_folder)
    if not os.path.exists(ideas_database):
        init_ideas_db()
    if not os.path.exists(media_database):
        init_media_db()


def save_idea(idea):
    conn = sqlite3.connect(ideas_database)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO ideas (texto) VALUES (?)", (idea,))
    conn.commit()
    idea_id = cursor.lastrowid
    conn.close()
    return idea_id


def get_ideas():
    conn = sqlite3.connect(ideas_database)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, texto, alredy_posted, final_post, created_at FROM ideas ORDER BY created_at ASC")
    ideas = cursor.fetchall()
    conn.close()
    return ideas


def remove_ideas(idea_id):
    conn = sqlite3.connect(ideas_database)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM ideas WHERE id = ?", (idea_id,))
    conn.commit()
    conn.close()


def show_idea(idea_id):
    conn = sqlite3.connect(ideas_database)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, texto, final_post, created_at FROM ideas WHERE id = ?", (idea_id,))
    idea = cursor.fetchone()
    conn.close()
    return idea


def save_media(idea_id, tipo, path, original_file_id):
    conn = sqlite3.connect(media_database)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO idea_media (idea_id, type, path, original_file_id) VALUES (?, ?, ?, ?)",
                   (idea_id, tipo, path, original_file_id))
    conn.commit()
    media_id = cursor.lastrowid
    conn.close()
    return media_id


def get_first_not_posted_idea():
    conn = sqlite3.connect(ideas_database)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, texto, final_post FROM ideas WHERE alredy_posted = 0 ORDER BY created_at ASC LIMIT 1")
    idea = cursor.fetchone()
    conn.close()
    return idea


def get_media_for_idea(idea_id):
    conn = sqlite3.connect(media_database)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, type, path FROM idea_media WHERE idea_id = ?", (idea_id,))
    media = cursor.fetchall()
    conn.close()
    return media


def update_idea_generate(idea_id, final_post):
    conn = sqlite3.connect(ideas_database)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE ideas SET alredy_posted = 0, final_post = ? WHERE id = ?", (final_post, idea_id))
    conn.commit()
    conn.close()


def update_idea_as_posted(idea_id):
    conn = sqlite3.connect(ideas_database)
    cursor = conn.cursor()
    # Remove media files associated with the idea to free up storage space
    cursor.execute("SELECT path FROM idea_media WHERE idea_id = ?", (idea_id,))
    media_files = cursor.fetchall()
    for media_file in media_files:
        path = media_file[0]
        if os.path.exists(path):
            os.remove(path)
    # Mark the idea as posted and remove media records from the database
    cursor.execute("DELETE FROM idea_media WHERE idea_id = ?", (idea_id,))
    cursor.execute(
        "UPDATE ideas SET alredy_posted = 1 WHERE id = ?", (idea_id,))
    conn.commit()
    conn.close()


def remove_media_for_idea(idea_id):
    conn = sqlite3.connect(media_database)
    # First, delete the media files from storage
    cursor = conn.cursor()
    cursor.execute("SELECT path FROM idea_media WHERE idea_id = ?", (idea_id,))
    media_files = cursor.fetchall()
    for media_file in media_files:
        path = media_file[0]
        if os.path.exists(path):
            os.remove(path)
    # Then, delete the media records from the database
    cursor.execute("DELETE FROM idea_media WHERE idea_id = ?", (idea_id,))
    conn.commit()
    conn.close()
