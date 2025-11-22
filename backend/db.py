import os
import sqlite3
from pathlib import Path
from flask import g
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv("DB_PATH", BASE_DIR / "data" / "trading_app.db"))

SCHEMA_SQL = """
PRAGMA journal_mode=WAL;
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
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  completed_at TIMESTAMP,
  started_at TIMESTAMP,
  successful INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS analysis_results (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ticker TEXT,
  symbol TEXT,
  name TEXT,
  yahoo_symbol TEXT,
  score REAL,
  verdict TEXT,
  entry REAL,
  stop_loss REAL,
  target REAL,
  raw_data TEXT,
  created_at TIMESTAMP,
  entry_method TEXT,
  data_source TEXT,
  is_demo_data INTEGER DEFAULT 1,
  status TEXT,
  error_message TEXT,
  updated_at TIMESTAMP,
  analysis_source TEXT
);
"""

def _ensure_db_folder():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def init_db_if_needed():
    """
    Safe initialization: idempotent and safe to call on every request.
    """
    _ensure_db_folder()
    need_init = not DB_PATH.exists()
    # create DB file if missing and apply schema
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    # Always run schema to ensure missing tables are created (idempotent)
    cur.executescript(SCHEMA_SQL)
    conn.commit()
    cur.close()
    conn.close()
    return not need_init  # returns False if we created DB now, True otherwise

def get_db():
    if "db" not in g:
        _ensure_db_folder()
        g.db = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        g.db.row_factory = sqlite3.Row
    return g.db

def get_db_connection():
    _ensure_db_folder()
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    if one:
        return rv[0] if rv else None
    return rv

def execute_db(query, args=()):
    db = get_db()
    cur = db.execute(query, args)
    db.commit()
    cur.close()

def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()
