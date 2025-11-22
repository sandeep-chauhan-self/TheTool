import os
import sqlite3
from flask import g

# Database paths - Railway-safe for production, local for development
import os
DB_PATH = os.environ.get("DB_PATH", os.path.join(os.getcwd(), "trading_app.db"))


def init_db_if_needed():
    """Initialize database and tables if the DB does not exist."""
    if not os.path.exists(DB_PATH):
        print("Initializing SQLite database in /tmp ...")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.executescript("""
        CREATE TABLE IF NOT EXISTS watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT UNIQUE NOT NULL,
            name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS analysis_jobs (
            job_id TEXT PRIMARY KEY,
            status TEXT NOT NULL,
            progress INTEGER DEFAULT 0,
            total INTEGER DEFAULT 0,
            completed INTEGER DEFAULT 0,
            errors TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            started_at TIMESTAMP,
            successful INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS analysis_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            score REAL NOT NULL,
            verdict TEXT NOT NULL,
            entry REAL,
            stop_loss REAL,
            target REAL,
            raw_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            entry_method TEXT DEFAULT 'unknown',
            data_source TEXT DEFAULT 'demo',
            is_demo_data INTEGER DEFAULT 1,
            symbol TEXT,
            name TEXT,
            yahoo_symbol TEXT,
            status TEXT DEFAULT 'completed',
            error_message TEXT,
            updated_at TIMESTAMP,
            analysis_source TEXT
        );
        """)

        conn.commit()
        conn.close()


def get_db():
    """Return a per-request SQLite connection."""
    if 'db' not in g:
        init_db_if_needed()
        g.db = sqlite3.connect(DB_PATH, check_same_thread=False)
        g.db.row_factory = sqlite3.Row
    return g.db


def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


def execute_db(query, args=()):
    db = get_db()
    cur = db.execute(query, args)
    db.commit()
    cur.close()


def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()
