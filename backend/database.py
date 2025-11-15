import sqlite3
import os

DB_PATH = os.path.join(os.getenv('DATA_PATH', './data'), 'trading_app.db')

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database schema"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Watchlist table (with user_id for future multi-user support)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT UNIQUE NOT NULL,
            name TEXT,
            user_id INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Analysis results table (stores last 10 per ticker)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analysis_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            score REAL NOT NULL,
            verdict TEXT NOT NULL,
            entry REAL,
            stop_loss REAL,
            target REAL,
            entry_method TEXT,
            data_source TEXT,
            is_demo_data BOOLEAN DEFAULT 0,
            raw_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # All stocks analysis table (centralized, stores last 10 per stock)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS all_stocks_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            name TEXT NOT NULL,
            yahoo_symbol TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            score REAL,
            verdict TEXT,
            entry REAL,
            stop_loss REAL,
            target REAL,
            entry_method TEXT,
            data_source TEXT,
            is_demo_data BOOLEAN DEFAULT 0,
            raw_data TEXT,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(symbol, created_at)
        )
    ''')
    
    # Job tracking table for async tasks
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analysis_jobs (
            job_id TEXT PRIMARY KEY,
            status TEXT NOT NULL,
            progress INTEGER DEFAULT 0,
            total INTEGER DEFAULT 0,
            completed INTEGER DEFAULT 0,
            successful INTEGER DEFAULT 0,
            errors TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            started_at TIMESTAMP,
            completed_at TIMESTAMP
        )
    ''')
    
    # Create indexes for faster queries
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_ticker ON analysis_results(ticker)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_created_at ON analysis_results(created_at)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_ticker_created ON analysis_results(ticker, created_at DESC)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_job_status ON analysis_jobs(status)')
    
    # Indexes for all_stocks_analysis table
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_all_stocks_symbol ON all_stocks_analysis(symbol)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_all_stocks_status ON all_stocks_analysis(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_all_stocks_created ON all_stocks_analysis(symbol, created_at DESC)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_all_stocks_updated ON all_stocks_analysis(updated_at)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_all_stocks_yahoo ON all_stocks_analysis(yahoo_symbol)')

    
    conn.commit()
    conn.close()
    
    # Use print for startup feedback (before logger is initialized)
    print("Database initialized successfully")


def cleanup_old_analyses(ticker=None, keep_last=10):
    """
    Keep only the last N analyses per ticker
    
    Args:
        ticker: Specific ticker to cleanup (None = all tickers)
        keep_last: Number of analyses to keep per ticker (default 10)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if ticker:
        # Cleanup specific ticker
        cursor.execute('''
            DELETE FROM analysis_results
            WHERE ticker = ?
            AND id NOT IN (
                SELECT id FROM analysis_results
                WHERE ticker = ?
                ORDER BY created_at DESC
                LIMIT ?
            )
        ''', (ticker, ticker, keep_last))
    else:
        # Cleanup all tickers
        cursor.execute('SELECT DISTINCT ticker FROM analysis_results')
        tickers = [row[0] for row in cursor.fetchall()]
        
        for t in tickers:
            cursor.execute('''
                DELETE FROM analysis_results
                WHERE ticker = ?
                AND id NOT IN (
                    SELECT id FROM analysis_results
                    WHERE ticker = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                )
            ''', (t, t, keep_last))
    
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    
    return deleted


def cleanup_all_stocks_analysis(symbol=None, keep_last=10):
    """
    Keep only the last N analyses per stock in all_stocks_analysis table
    Auto-deletes oldest records when limit exceeded
    
    Args:
        symbol: Specific symbol to cleanup (None = all symbols)
        keep_last: Number of analyses to keep per stock (default 10)
    
    Returns:
        Number of records deleted
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if symbol:
        # Cleanup specific symbol
        cursor.execute('''
            DELETE FROM all_stocks_analysis
            WHERE symbol = ?
            AND id NOT IN (
                SELECT id FROM all_stocks_analysis
                WHERE symbol = ?
                ORDER BY created_at DESC
                LIMIT ?
            )
        ''', (symbol, symbol, keep_last))
    else:
        # Cleanup all symbols
        cursor.execute('SELECT DISTINCT symbol FROM all_stocks_analysis')
        symbols = [row[0] for row in cursor.fetchall()]
        
        for sym in symbols:
            cursor.execute('''
                DELETE FROM all_stocks_analysis
                WHERE symbol = ?
                AND id NOT IN (
                    SELECT id FROM all_stocks_analysis
                    WHERE symbol = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                )
            ''', (sym, sym, keep_last))
    
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    
    return deleted
