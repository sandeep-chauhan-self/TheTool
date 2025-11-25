# AI Agent Instructions for TheTool Codebase

> **Critical guidance for AI agents to work productively in the TheTool stock analysis system**

## 1. Architecture Overview

**TheTool** is a Python/React stock analysis platform with:
- **Backend**: Flask API with modular indicator engine (12 technical indicators)
- **Frontend**: React UI with real-time progress tracking for bulk analysis
- **Database**: Unified PostgreSQL/SQLite support with automatic query parameter conversion
- **Async Processing**: Thread-based background jobs (no Redis required) with optional Redis support
- **Key Pattern**: Modular indicator organization by category (`momentum/`, `trend/`, `volatility/`, `volume/`)

## 2. Critical Architectural Decisions

### Database Abstraction Layer (PostgreSQL/SQLite Compatibility)

**Location**: `backend/database.py` - `_convert_query_params()` function

**Pattern**: All SQL queries use SQLite placeholder style (`?`), then convert automatically:
```python
# Write queries with SQLite-style placeholders
query = 'INSERT INTO analysis_results (ticker, score) VALUES (?, ?)'
query, args = _convert_query_params(query, ('AAPL', 95.5))
# Automatically converted to PostgreSQL (%s) if DATABASE_TYPE=='postgres'
cursor.execute(query, args)
```

**Why**: Enables same code to work with both SQLite (local dev) and PostgreSQL (Railway production).

**When Adding Queries**: Always use `?` placeholders. Never hardcode `%s` or mix placeholder styles.

### Unified Analysis Results Table

**Location**: `backend/database.py` - `_init_sqlite_db()` / `_init_postgres_db()`

**Migration Complete**: Single `analysis_results` table replaced dual-table architecture (old: `analysis_results` + `all_stocks_analysis`).

**Key Fields**:
- `ticker`: Watchlist identifier (e.g., "RELIANCE.NS")
- `symbol`: Bulk analysis identifier (e.g., "RELIANCE")
- `raw_data`: JSON string containing all indicator calculations and signals
- `analysis_source`: "watchlist" or "bulk" (tracks origin)

**When Querying**: Check `analysis_source` or use both `ticker` and `symbol` fields for backward compatibility.

### Thread-Safe Database Access

**Location**: `backend/database.py` - `get_db_session()` context manager

**Pattern**: Always use context managers for background threads:
```python
# Inside thread_tasks.py or other background code
with get_db_session() as (conn, cursor):
    cursor.execute(query, args)
    conn.commit()
    # Connection auto-closes
```

**Why**: SQLite requires thread-local connections. Context manager handles connection cleanup.

**Flask Requests**: Use `get_db()` (Flask g-based) inside request handlers.

### Indicator Engine Architecture

**Location**: `backend/utils/analysis_orchestrator.py`

**Classes**:
- `DataFetcher`: Acquires & validates OHLCV data
- `IndicatorEngine`: Calculates 12 technical indicators
- `SignalAggregator`: Votes on buy/sell/hold (weighted by category)
- `TradeCalculator`: Computes entry/stop/target levels
- `ResultFormatter`: Serializes to JSON

**Adding New Indicator**:
1. Create class in appropriate category directory: `backend/indicators/{category}/{name}.py`
2. Inherit from base indicator class with `calculate()` method
3. Register in `backend/indicators/__init__.py`
4. Add to `ALL_INDICATORS` dict in `analysis_orchestrator.py`

### Configuration Management

**Location**: `backend/config.py` - `Config` class

**Pattern**: All settings are environment variables with sensible defaults:
```python
DATABASE_URL = os.getenv('DATABASE_URL', None)  # PostgreSQL (production)
DATA_PATH = os.getenv('DATA_PATH', './data')     # SQLite directory (dev)
MAX_THREADS = int(os.getenv('MAX_THREADS', '10'))
```

**Critical**: Call `config.validate()` during startup to catch configuration errors early.

## 3. Common Developer Workflows

### Adding a Technical Indicator

1. **Create indicator file**: `backend/indicators/trend/new_indicator.py`
2. **Implement `calculate()` method** returning dict with signal (1/-1/0) and scores
3. **Register in `__init__.py`**: `from .new_indicator import NewIndicator`
4. **Add to `analysis_orchestrator.py`**: Add to `ALL_INDICATORS` dict
5. **Test**: Run `backend/test_comprehensive_scenarios.py`

### Running Analysis for Single Stock

```python
# From backend/utils/compute_score.py
from utils.compute_score import analyze_ticker

result = analyze_ticker(
    ticker='RELIANCE.NS',
    capital=100000,
    use_demo_data=False  # Set True for testing
)
# Returns: {
#   'ticker': 'RELIANCE.NS',
#   'score': 75.5,
#   'verdict': 'BUY',
#   'entry': 1234.50,
#   'indicators': [...]  # All 12 indicator results
# }
```

### Running Bulk Analysis (Async)

```python
# Frontend: POST /analyze with stock list
# Backend: routes/analysis.py handles request
# Returns: { 'job_id': 'abc-123' }

# Poll for progress: GET /status/abc-123
# Returns: { 'progress': 67, 'status': 'processing', 'completed': 2 }

# When done, fetch results from routes/stocks.py
```

### Debugging Database Connection Issues

**SQLite Issues** (local development):
- Check `DATA_PATH` environment variable or uses default `./data/`
- Ensure directory exists and is writable
- Look for multiple `trading_app.db` files (root, `backend/data/`, etc.) - keep only one

**PostgreSQL Issues** (production):
- Verify `DATABASE_URL` format: `postgresql://user:pass@host:port/dbname`
- Railway may use `postgres://` - config.py auto-converts to `postgresql://`
- Check credentials in Railway environment variables

**Retry Logic**: Database connections auto-retry with exponential backoff (2, 4, 8 seconds) for transient failures.

## 4. File Structure & Key Patterns

### Backend Organization
```
backend/
├── app.py                          # Flask app factory
├── config.py                       # Centralized configuration
├── database.py                     # DB abstraction + retry logic
├── utils/
│   ├── analysis_orchestrator.py   # Core analysis pipeline
│   └── compute_score.py            # Single-stock analysis entry point
├── indicators/
│   ├── momentum/                   # RSI, MACD, Stochastic, etc.
│   ├── trend/                      # ADX, EMA, SAR, etc.
│   ├── volatility/                 # Bollinger, ATR, etc.
│   └── volume/                     # OBV, CMF, etc.
├── infrastructure/
│   └── thread_tasks.py             # Background job processing
└── routes/
    ├── analysis.py                 # /analyze endpoints
    ├── stocks.py                   # /all-stocks/* endpoints
    └── watchlist.py                # /watchlist/* endpoints
```

### Query Parameter Conversion Reference
```python
# Always query with ? placeholders
"SELECT * FROM analysis_results WHERE ticker = ? AND score > ?"
# Automatically converted to %s for PostgreSQL

# Result handling works with both:
# - PostgreSQL: tuples
# - SQLite: sqlite3.Row objects
# Use routes/stocks.py as reference for handling both
```

## 5. Common Pitfalls & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| "No data appearing in UI" | Data inserted to wrong database (relative path) | Use absolute paths in config |
| INSERT fails silently | Using non-existent column name | Check schema in `database.py` |
| Thread crashes | Using Flask `get_db()` in background thread | Use `get_db_session()` context manager |
| PostgreSQL query fails | Placeholder mismatch (`?` vs `%s`) | Use `_convert_query_params()` always |
| SQLite locks up | Multiple writers on same connection | Each thread gets own connection via `get_db_session()` |

## 6. Testing & Validation

**Run Analysis Tests**:
```bash
cd backend
python test_comprehensive_scenarios.py      # Full integration test
python test_backend_api.py                  # API endpoint tests
```

**Demo Data Generation**:
```python
# Use in any test or development script
from utils.analysis_orchestrator import DataFetcher
df = DataFetcher._generate_demo_data('RELIANCE.NS', days=100)
```

## 7. Deploy-Specific Notes

### Railway Production
- **Must use PostgreSQL** via `DATABASE_URL` environment variable
- SQLite won't persist between deployments (no persistent volume)
- Set `FLASK_ENV=production` and verify `DEBUG=False`
- Redis optional but recommended for distributed job tracking

### Local Development
- SQLite stored in `backend/data/trading_app.db` (default)
- Run `scripts/setup.ps1` once to initialize environment
- Use `USE_DEMO_DATA=True` for testing without internet

## 8. When Making Changes

### Before Committing
1. Verify SQL queries use `?` placeholders (converted automatically)
2. Test with both SQLite (local) and PostgreSQL (if possible)
3. Use thread-safe patterns in background code (`get_db_session()`)
4. Run relevant test suite for your changes

### Documentation
- Update `backend/README.md` if changing API endpoints
- Add comments explaining database abstraction usage
- Reference this file when documenting new patterns

---

**Last Updated**: 2025-01-15 | **Scope**: Project-specific patterns only | **Target Audience**: AI coding agents
