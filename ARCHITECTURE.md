# TheTool - Complete Architecture Guide

## Table of Contents
1. [System Overview](#system-overview)
2. [Technology Stack](#technology-stack)
3. [Backend Architecture](#backend-architecture)
4. [Frontend Architecture](#frontend-architecture)
5. [Data Flow](#data-flow)
6. [API Endpoints](#api-endpoints)
7. [Database Schema](#database-schema)
8. [Key Features](#key-features)
9. [Development Workflow](#development-workflow)

---

## System Overview

**TheTool** is a comprehensive stock analysis platform that provides real-time technical analysis, multi-indicator evaluation, and automated trading insights. The system uses a Flask backend with React frontend, analyzing stocks using 13+ technical indicators.

### High-Level Architecture

```
???????????????????????????????????????????
?           Frontend                      ?
?  React SPA (Port 3000)                  ?
?  User Interface & Visualization         ?
???????????????????????????????????????????
                  ? HTTP/REST API
                  ? CORS Enabled
???????????????????????????????????????????
?         Backend API                     ?
?  Flask Server (Port 5000)               ?
?  Business Logic                         ?
???????????????????????????????????????????
?  ???????????? ???????????? ??????????? ?
?  ?Auth Layer? ?Validation? ?Rate Limit? ?
?  ???????????? ???????????? ??????????? ?
???????????????????????????????????????????
?  ???????????? ???????????? ??????????? ?
?  ?Indicators? ? Analysis ? ?Pipeline ? ?
?  ?(13 types)? ?  Engine  ? ?Process  ? ?
?  ???????????? ???????????? ??????????? ?
???????????????????????????????????????????
?  ???????????? ???????????? ??????????? ?
?  ?  Cache   ? ?Background? ?State Mgmt? ?
?  ?(In-Memory)? ?  Tasks   ? ?Redis opt? ?
?  ???????????? ???????????? ??????????? ?
???????????????????????????????????????????
                  ?
???????????????????????????????????????????
?          Data Layer                     ?
?  ???????????? ???????????? ??????????? ?
?  ?SQLite DB ? ?Yahoo Fin.? ?NSE Data ? ?
?  ?(Analysis)? ?API (yFin)? ?(Stocks) ? ?
?  ???????????? ???????????? ??????????? ?
???????????????????????????????????????????
```

---

## Technology Stack

### Backend
- **Framework**: Flask 3.0.0 (Python web framework)
- **Language**: Python 3.13.5
- **Database**: SQLite 3 (local storage for analysis results)
- **Data Source**: yFinance 0.2.66 (Yahoo Finance API)
- **Technical Analysis**: TA-Lib 0.11.0 + Custom implementations
- **Validation**: Pydantic 2.0+ (input validation & security)
- **Security**: Flask-CORS 4.0.0, Flask-Limiter 3.5.0
- **Performance**: Numba 0.58.0 (JIT compilation)
- **Testing**: Pytest 7.4.0+ (350+ test cases)

### Frontend
- **Framework**: React 18.2.0
- **UI Library**: Tailwind CSS 3.3.5
- **HTTP Client**: Axios 1.6.2
- **Routing**: React Router 6.20.0
- **Build Tool**: React Scripts 5.0.1

### Development Tools
- **Package Manager (Backend)**: pip
- **Package Manager (Frontend)**: npm
- **Version Control**: Git
- **Code Quality**: Pytest, ESLint

---

## Backend Architecture

### Directory Structure

```
backend/
??? app.py                    # Main Flask application entry point
??? auth.py                   # API authentication & key management
??? cache.py                  # In-memory caching system
??? celery_config.py          # Celery background task configuration
??? config.py                 # Centralized configuration management
??? database.py               # SQLite database connection & operations
??? .env                      # Environment variables (SECRET)
??? .env.example              # Environment template
??? requirements.txt          # Python dependencies
?
??? models/                   # Domain Models & Business Logic
?   ??? __init__.py
?   ??? job_state.py         # Job state machine (8 states, 10 events)
?   ??? analysis_job.py      # Job aggregate root with invariants
?   ??? validation.py        # Pydantic validation schemas (security)
?
??? indicators/               # Technical Indicators (13 types)
?   ??? __init__.py
?   ??? base.py              # Abstract base class
?   ??? registry.py          # Indicator registry pattern
?   ??? momentum/            # RSI, CCI, Stochastic, Williams %R
?   ??? trend/               # MACD, EMA, ADX, PSAR, Supertrend
?   ??? volatility/          # Bollinger Bands, ATR
?   ??? volume/              # OBV, CMF
?
??? infrastructure/           # Cross-Cutting Concerns
?   ??? __init__.py
?   ??? tasks.py             # Celery background tasks
?   ??? thread_tasks.py      # Threading-based async processing
?
??? app_logging/              # Structured Logging System
?   ??? __init__.py
?   ??? structured_logging.py # JSON logs with correlation IDs
?
??? optimization/             # Performance Optimization
?   ??? complexity_analyzer.py   # Big-O analysis
?   ??? performance_metrics.py   # Execution profiling
?
??? performance/              # Runtime Performance
?   ??? cache.py             # LRU cache with TTL
?   ??? parallel.py          # Multi-threaded execution
?
??? pipeline/                 # Data Processing Pipeline
?   ??? data_pipeline.py     # ETL pipeline for stock data
?
??? project_management/       # Project Tools
?   ??? dependency_visualizer.py  # Mermaid/DOT graph generation
?   ??? health_monitor.py         # System health checks
?   ??? metrics_collector.py      # Performance metrics
?   ??? progress_tracker.py       # Job progress tracking
?   ??? roi_calculator.py         # Refactoring ROI calculation
?
??? refactoring/              # Code Refactoring Tools
?   ??? dependency_analyzer.py    # Dependency graph analysis
?   ??? migration_sequencer.py    # Safe migration ordering
?   ??? rollback_manager.py       # Migration rollback system
?
??? scripts/                  # Utility Scripts
?   ??? migrate_db.py             # Database schema migrations
?   ??? migrate_strategy_columns.py
?   ??? fetch_nse_stocks.py       # NSE stock list fetcher
?   ??? part3a_indicator_configs.py
?
??? strategies/               # Trading Strategies
?   ??? breakout_strategy.py      # Breakout detection logic
?
??? tests/                    # Test Suite (350+ tests)
?   ??? test_backend.py
?   ??? test_part3a_*.py          # Indicator tests
?   ??? test_part4_*.py           # Architecture tests
?   ??? test_part5_*.py           # Optimization tests
?   ??? verify_integration.py
?
??? utils/                    # Utilities
    ??? compute_score.py          # Analysis scoring algorithm
    ??? analysis_orchestrator.py  # Orchestrates analysis workflow
    ??? analysis/                 # Analysis submodules
        ??? orchestrator.py
        ??? signal_validator.py
```

### Core Components Explained

#### 1. **Flask Application (app.py)**
- Main entry point for the backend
- Configures CORS, routes, error handlers
- Initializes database and loads indicators
- Serves API endpoints for frontend

**Key Endpoints**:
```python
GET  /api/health              # Health check
POST /api/analyze             # Analyze specific tickers
POST /api/analyze-all-stocks  # Bulk analysis
GET  /api/job-status/<id>     # Get job progress
POST /api/cancel-job/<id>     # Cancel running job
GET  /api/watchlist           # Get watchlist
POST /api/watchlist           # Add to watchlist
GET  /api/indicators          # List all indicators
GET  /api/analysis-history    # Get past analyses
```

#### 2. **Authentication (auth.py)**
- API key-based authentication
- Master API key for admin access
- Per-request key generation for clients
- SHA-256 hashing for security

#### 3. **Validation (models/validation.py)**
- Pydantic models for request validation
- Input sanitization (SQL injection prevention)
- Ticker symbol validation (alphanumeric + dots/hyphens only)
- Indicator whitelist enforcement
- Capital bounds checking ($1K - $100M)

**Security Features**:
- CWE-20: Improper Input Validation ?
- CWE-89: SQL Injection Prevention ?
- Path traversal protection ?
- Dangerous pattern blacklisting ?

#### 4. **Job State Machine (models/job_state.py)**

**States** (8):
```
CREATED ? QUEUED ? RUNNING ? COMPLETED
                      ?
                   PAUSED ? (resume)
                      ?
                   FAILED ? (retry) ? QUEUED
                      ?
                  CANCELLED
                      ?
                   TIMEOUT
```

**Events** (10):
- CREATE, QUEUE, START, PAUSE, RESUME
- COMPLETE, FAIL, CANCEL, TIMEOUT, RETRY

**Features**:
- Valid transition enforcement
- Terminal state protection (COMPLETED, FAILED, CANCELLED, TIMEOUT)
- Transition history tracking
- Hooks for state change callbacks
- Redis-ready (distributed system support)

#### 5. **Indicator System**

**Architecture**:
```
IndicatorBase (Abstract)
??? MomentumIndicator
?   ??? RSI (Relative Strength Index)
?   ??? CCI (Commodity Channel Index)
?   ??? Stochastic Oscillator
?   ??? Williams %R
?
??? TrendIndicator
?   ??? MACD (Moving Average Convergence Divergence)
?   ??? EMA (Exponential Moving Average)
?   ??? ADX (Average Directional Index)
?   ??? PSAR (Parabolic SAR)
?   ??? Supertrend
?
??? VolatilityIndicator
?   ??? Bollinger Bands
?   ??? ATR (Average True Range)
?
??? VolumeIndicator
    ??? OBV (On-Balance Volume)
    ??? CMF (Chaikin Money Flow)
```

**Common Features**:
- Named constants (MLRM-001 compliance)
- Boundary validation (MLRM-002 compliance)
- NaN/Inf handling
- Type checking
- Configurable parameters
- Cached computation

#### 6. **Analysis Pipeline**

**Flow**:
```
1. Request Validation
   ? Ticker sanitization
   ? Indicator whitelist check
   ? Capital bounds validation

2. Job Creation
   ? Generate unique job_id
   ? Initialize state machine (CREATED)
   ? Store in database

3. Background Processing
   ? Queue job (CREATED ? QUEUED)
   ? Start processing (QUEUED ? RUNNING)
   ? Fetch historical data (yFinance)
   ? Calculate indicators (parallel)
   ? Compute scores & signals
   ? Complete (RUNNING ? COMPLETED)

4. Result Storage
   ? Save to SQLite
   ? Update job status
   ? Return results to client
```

#### 7. **Caching Strategy**

**Two-Level Cache**:
```
L1: In-Memory (cache.py)
??? LRU eviction
??? TTL: 5 minutes
??? Thread-safe
??? Hit rate: ~85%

L2: Database (database.py)
??? Historical analysis results
??? Persistent storage
??? Query by ticker + timeframe
```

#### 8. **Background Tasks**

**Threading Mode** (Default):
- `thread_tasks.py` - Python threading
- Thread-local database connections
- Progress callbacks
- Cancellation support

**Celery Mode** (Optional):
- `tasks.py` - Celery distributed tasks
- Redis broker
- Worker pools
- Distributed processing

#### 9. **Project Management Tools**

**Dependency Visualizer**:
- Scans Python modules
- Detects circular dependencies
- Generates Mermaid/DOT graphs
- Export to docs/analysis_tools/

**Refactoring Tools**:
- Dependency analyzer
- Safe migration sequencer (topological sort)
- Dry-run mode
- Rollback manager

---

## Frontend Architecture

### Directory Structure

```
frontend/
??? public/
?   ??? index.html           # HTML entry point
?   ??? favicon.ico
?
??? src/
?   ??? App.js               # Main React component
?   ??? index.js             # React DOM render
?   ??? index.css            # Tailwind CSS imports
?   ?
?   ??? components/          # React Components
?   ?   ??? Dashboard.js         # Main dashboard view
?   ?   ??? StockAnalysis.js     # Analysis form & results
?   ?   ??? Watchlist.js         # Watchlist management
?   ?   ??? IndicatorConfig.js   # Indicator selection
?   ?   ??? JobProgress.js       # Real-time job progress
?   ?
?   ??? services/            # API Services
?   ?   ??? api.js               # Axios API client
?   ?
?   ??? utils/               # Utilities
?       ??? helpers.js           # Helper functions
?
??? package.json             # npm dependencies
??? tailwind.config.js       # Tailwind configuration
```

### Component Hierarchy

```
<App>
  <Router>
    <Header />
    <Routes>
      <Route path="/" element={<Dashboard />} />
      <Route path="/analyze" element={<StockAnalysis />} />
      <Route path="/watchlist" element={<Watchlist />} />
      <Route path="/history" element={<AnalysisHistory />} />
    </Routes>
    <Footer />
  </Router>
</App>
```

### Key Features

1. **Real-Time Updates**: WebSocket/polling for job progress
2. **Responsive Design**: Tailwind CSS grid/flex layouts
3. **Chart Visualization**: Interactive stock charts
4. **Form Validation**: Client-side validation before API calls
5. **Error Handling**: User-friendly error messages

---

## Data Flow

### Analysis Request Flow

```
?????????
?  User ? 1. Selects tickers (e.g., AAPL, MSFT)
?(Browser)? 2. Chooses indicators (e.g., RSI, MACD)
????????? 3. Sets capital ($100,000)
       ?
       ? HTTP POST /api/analyze
????????????????????????????????
?  Frontend (React)            ?
?  - Validates input           ?
?  - Sends POST request        ?
????????????????????????????????
       ?
       ? JSON: {tickers: [], indicators: [], capital: 100000}
????????????????????????????????
?  Backend API (Flask)         ?
?  1. Auth check (API key)     ?
?  2. Rate limiting (100/min)  ?
?  3. Pydantic validation      ?
?  4. Create job (CREATED)     ?
?  5. Return job_id            ?
????????????????????????????????
       ?
       ? Background Task
????????????????????????????????
?  Thread Worker               ?
?  1. QUEUED ? RUNNING         ?
?  2. Fetch data (yFinance)    ?
?  3. Calculate indicators     ?
?     - RSI, MACD, Bollinger   ?
?  4. Compute scores           ?
?  5. Generate signals         ?
?  6. Save to database         ?
?  7. State: COMPLETED         ?
????????????????????????????????
       ?
       ? Poll /api/job-status/{job_id}
????????????????????????????????
?  Frontend (React)            ?
?  - Shows progress bar        ?
?  - Updates every 2 seconds   ?
?  - Displays results          ?
????????????????????????????????
```

---

## API Endpoints

### 1. Health Check
```http
GET /api/health
Response: {"status": "healthy", "timestamp": "2025-11-16T..."}
```

### 2. Analyze Stocks
```http
POST /api/analyze
Headers: {
  "Content-Type": "application/json",
  "X-API-Key": "your-api-key"
}
Body: {
  "tickers": ["AAPL", "MSFT"],
  "indicators": ["rsi", "macd"],
  "capital": 100000,
  "use_demo_data": true
}
Response: {
  "job_id": "abc-123-xyz",
  "status": "queued",
  "message": "Analysis started"
}
```

### 3. Job Status
```http
GET /api/job-status/{job_id}
Response: {
  "status": "running",
  "progress": 45,
  "total": 100,
  "completed": 45,
  "failed": 0,
  "current_ticker": "AAPL"
}
```

### 4. Cancel Job
```http
POST /api/cancel-job/{job_id}
Response: {"success": true, "message": "Job cancelled"}
```

### 5. Get Indicators
```http
GET /api/indicators
Response: {
  "indicators": [
    {"id": "rsi", "name": "RSI", "category": "momentum"},
    {"id": "macd", "name": "MACD", "category": "trend"}
  ]
}
```

---

## Database Schema

### Table: analysis_results (UNIFIED - Post-Migration)

```sql
CREATE TABLE analysis_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,                 -- Stock ticker (e.g., "RELIANCE.NS")
    symbol TEXT,                          -- Stock symbol without suffix (e.g., "RELIANCE")
    name TEXT,                            -- Company name
    yahoo_symbol TEXT,                    -- Yahoo Finance ticker format
    score REAL NOT NULL,                  -- Analysis score (0-100)
    verdict TEXT NOT NULL,                -- "Buy", "Sell", "Neutral"
    entry REAL,                           -- Entry price recommendation
    stop_loss REAL,                       -- Stop loss price
    target REAL,                          -- Target price
    entry_method TEXT,                    -- "Market Order", "Limit Order", etc.
    data_source TEXT,                     -- "real" or "demo"
    is_demo_data BOOLEAN DEFAULT 0,       -- Flag for demo data
    raw_data TEXT,                        -- JSON string of indicator values
    status TEXT DEFAULT 'completed',      -- "pending", "completed", "failed"
    error_message TEXT,                   -- Error details if analysis failed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    analysis_source TEXT                  -- "watchlist" or "bulk" (KEY FIELD)
);

-- Indexes (10 total for optimized queries)
CREATE INDEX idx_ticker ON analysis_results(ticker);
CREATE INDEX idx_created_at ON analysis_results(created_at);
CREATE INDEX idx_ticker_created ON analysis_results(ticker, created_at DESC);
CREATE INDEX idx_symbol ON analysis_results(symbol);
CREATE INDEX idx_yahoo_symbol ON analysis_results(yahoo_symbol);
CREATE INDEX idx_status ON analysis_results(status);
CREATE INDEX idx_analysis_source ON analysis_results(analysis_source);
CREATE INDEX idx_symbol_created ON analysis_results(symbol, created_at DESC);
CREATE INDEX idx_source_symbol ON analysis_results(analysis_source, symbol);
CREATE INDEX idx_updated_at ON analysis_results(updated_at);
```

**Migration Status**: ? Completed November 17, 2025
- Unified table architecture (previously split across 2 tables)
- 2,204 records migrated successfully
- Cross-visibility working (watchlist ? bulk analysis)

### Table: analysis_jobs

```sql
CREATE TABLE analysis_jobs (
    id TEXT PRIMARY KEY,
    tickers TEXT NOT NULL,
    status TEXT DEFAULT 'created',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    progress INTEGER DEFAULT 0,
    total INTEGER DEFAULT 0,
    successful INTEGER DEFAULT 0,
    failed INTEGER DEFAULT 0,
    error_message TEXT,
    results TEXT  -- JSON blob
);
```

### Table: watchlist

```sql
CREATE TABLE watchlist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT UNIQUE NOT NULL,
    name TEXT,
    user_id INTEGER DEFAULT 1,            -- Multi-user support
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Purpose**: Track user's watched stocks for quick access and monitoring.

---

## Database Architecture Notes

**Recent Migration** (November 17, 2025): The application successfully migrated from a dual-table architecture to a unified `analysis_results` table. This resolved data inconsistency issues where stocks analyzed from different entry points (watchlist vs bulk) were not visible across views.

**Key Improvements**:
- ? Single source of truth for all analysis results
- ? `analysis_source` field distinguishes watchlist vs bulk analysis
- ? Cross-visibility: stocks appear in both watchlist and all-stocks views
- ? Simplified queries: no more UNION operations needed
- ? Zero data loss: 2,204 records migrated successfully

For detailed migration documentation, see `DB_ARCHITECTURE.md`.

---

## Key Features

### 1. Multi-Indicator Analysis
- 13 technical indicators
- Configurable parameters
- Parallel computation
- Cached results

### 2. Background Processing
- Non-blocking API
- Real-time progress updates
- Cancellation support
- Error recovery

### 3. Security
- API key authentication
- Input sanitization
- Rate limiting (100 req/min)
- CORS protection

### 4. Performance
- In-memory caching (5min TTL)
- Numba JIT compilation
- Multi-threaded processing
- Database connection pooling

### 5. Scalability
- Redis-ready state management
- Celery task distribution
- Horizontal scaling support
- Load balancing ready

---

## Development Workflow

### Setup

```bash
# Backend
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py

# Frontend
cd frontend
npm install
npm start
```

### Testing

```bash
# Backend tests (350+)
cd backend
pytest tests/ -v

# State machine tests
pytest tests/test_part4_state_machine.py -v

# Indicator tests
pytest tests/test_part3a_all_indicators.py -v
```

### Running in Production

```bash
# Backend (Gunicorn)
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# Frontend (Build)
npm run build
# Serve build/ with nginx or static server
```

---

## Configuration

### Environment Variables (.env)

```bash
# Flask
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your-secret-key-here

# Database
DATA_PATH=./data

# API
MASTER_API_KEY=your-master-key

# Redis (Optional)
REDIS_URL=redis://localhost:6379/0

# Celery (Optional)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

---

## Performance Metrics

- **Analysis Speed**: ~2-3 seconds per ticker
- **Concurrent Jobs**: Up to 20 parallel
- **Cache Hit Rate**: ~85%
- **API Response Time**: <100ms (cached)
- **Database Queries**: <10ms average

---

## Future Enhancements

1. **Real-time Data**: WebSocket streaming
2. **ML Predictions**: LSTM price forecasting
3. **Portfolio Management**: Track multiple portfolios
4. **Backtesting**: Historical strategy testing
5. **Alerts**: Price/indicator threshold notifications

---

**Last Updated**: November 17, 2025
**Version**: 2.1.0
**Tests Passing**: 350+ (including 23/23 state machine tests)
**Database Migration**: ? Unified table architecture (Nov 17, 2025)
**Records**: 2,204 (10 watchlist + 2,194 bulk analysis)
