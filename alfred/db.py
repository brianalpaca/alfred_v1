import sqlite3
from pathlib import Path

from config.settings import ALFRED_DB_PATH


def get_connection() -> sqlite3.Connection:
    Path(ALFRED_DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(ALFRED_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at TEXT NOT NULL,
                ended_at TEXT,
                summary TEXT,
                qmd_path TEXT,
                token_count INTEGER DEFAULT 0,
                topics TEXT
            );

            CREATE TABLE IF NOT EXISTS ideas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                session_id INTEGER,
                created_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            );

            CREATE VIRTUAL TABLE IF NOT EXISTS archives_fts
            USING fts5(
                session_id UNINDEXED,
                qmd_path UNINDEXED,
                content,
                topics,
                summary
            );
        """)
        conn.commit()
    finally:
        conn.close()
