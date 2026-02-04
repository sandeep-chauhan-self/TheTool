# Technologies and Concepts Used in Backend

## Overview

This document explains all technologies, libraries, concepts, and patterns used in TheTool's Flask backend application.

---

## Core Technologies

### 1. Python 3.13+

**Why Python:**

- Excellent data science ecosystem (pandas, numpy)
- Large financial analysis library support
- Simple, readable syntax
- Strong async capabilities

**Key Python Features Used:**

#### a) Type Hints

```python
def analyze_ticker(
    ticker: str,
    indicator_list: Optional[List[str]] = None,
    capital: Optional[float] = None
) -> Dict[str, Any]:
    """Annotated function signature"""
    pass
```

#### b) Decorators

```python
@bp.route("/analyze", methods=["POST"])
def analyze():
    pass

@cached_indicator
def calculate_rsi(df: pd.DataFrame) -> float:
    pass
```

#### c) Context Managers

```python
with get_db_session() as (conn, cursor):
    cursor.execute(query, args)
    conn.commit()
```

#### d) Abstract Base Classes (ABC)

```python
from abc import ABC, abstractmethod

class IndicatorBase(ABC):
    @abstractmethod
    def calculate(self, df: pd.DataFrame) -> Any:
        pass
```

#### e) Dataclasses

```python
from dataclasses import dataclass

@dataclass
class AnalysisConfig:
    capital: float = 100000
    risk_percent: float = 2.0
    strategy_id: int = 1
```

---

### 2. Flask 3.0

**What it is:** Lightweight WSGI web framework for building REST APIs.

**Key Concepts:**

#### a) Application Factory

Creating app instance with configuration:

```python
def create_app(config_object=None):
    app = Flask(__name__)
    app.config.from_object(config)

    # Register extensions
    CORS(app)

    # Register blueprints
    app.register_blueprint(analysis_bp)

    return app
```

#### b) Blueprints

Modular route organization:

```python
# routes/analysis.py
bp = Blueprint("analysis", __name__, url_prefix="/api/analysis")

@bp.route("/analyze", methods=["POST"])
def analyze():
    pass

# app.py
app.register_blueprint(bp)
```

#### c) Request Handling

```python
@bp.route("/analyze", methods=["POST"])
def analyze():
    # Get JSON body
    data = request.get_json()

    # Get query parameters
    page = request.args.get('page', 1, type=int)

    # Return JSON response
    return jsonify({"result": data}), 200
```

#### d) Request Context

```python
from flask import g, request

# g object for request-scoped data
def get_db():
    if 'db' not in g:
        g.db = create_connection()
    return g.db
```

#### e) Error Handling

```python
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404
```

---

### 3. Flask-CORS 4.0

**What it is:** Extension for handling Cross-Origin Resource Sharing.

**Why needed:**

- Frontend (React) runs on different port (3000)
- Backend runs on port 5000
- Browsers block cross-origin requests by default

**Configuration:**

```python
from flask_cors import CORS

CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000", "https://the-tool-theta.vercel.app"],
        "methods": ["GET", "POST", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "X-API-Key"]
    }
})
```

---

### 4. psycopg2-binary 2.9.9

**What it is:** PostgreSQL adapter for Python.

**Key Features:**

#### a) Connection Management

```python
import psycopg2

conn = psycopg2.connect(
    "postgresql://user:password@host:5432/database"
)
cursor = conn.cursor()
```

#### b) Parameterized Queries (SQL Injection Prevention)

```python
# SAFE - parameterized
cursor.execute(
    "SELECT * FROM stocks WHERE ticker = %s",
    (ticker,)
)

# UNSAFE - string formatting (never do this!)
# cursor.execute(f"SELECT * FROM stocks WHERE ticker = '{ticker}'")
```

#### c) Transaction Management

```python
try:
    cursor.execute(insert_query, args)
    conn.commit()  # Success - save changes
except Exception:
    conn.rollback()  # Error - undo changes
```

---

### 5. pandas 2.2.3

**What it is:** Data manipulation and analysis library.

**Used for:**

- OHLCV (Open, High, Low, Close, Volume) data handling
- Time series operations
- Data cleaning and transformation

**Key Operations:**

#### a) DataFrame Creation

```python
import pandas as pd

# From dictionary
df = pd.DataFrame({
    'Date': dates,
    'Open': opens,
    'High': highs,
    'Low': lows,
    'Close': closes,
    'Volume': volumes
})

# From yfinance
df = yf.download(ticker, period='200d')
```

#### b) Column Operations

```python
# Access column
prices = df['Close']

# Calculate new column
df['SMA_50'] = df['Close'].rolling(window=50).mean()

# Multiple columns
df[['Open', 'Close', 'Volume']]
```

#### c) Rolling Calculations

```python
# 50-day Simple Moving Average
df['SMA_50'] = df['Close'].rolling(window=50).mean()

# 14-day Standard Deviation
df['STD_14'] = df['Close'].rolling(window=14).std()
```

#### d) Indexing and Slicing

```python
# Last row
latest = df.iloc[-1]

# Last 100 rows
recent = df.tail(100)

# Specific date range
filtered = df.loc['2024-01-01':'2024-12-31']
```

---

### 6. numpy 1.26.2

**What it is:** Fundamental package for numerical computing.

**Used for:**

- Mathematical operations on arrays
- Statistical calculations
- Integration with pandas and ta library

**Key Operations:**

```python
import numpy as np

# Array creation
arr = np.array([1, 2, 3, 4, 5])

# Statistical functions
mean = np.mean(prices)
std = np.std(prices)
max_val = np.max(prices)
min_val = np.min(prices)

# NaN handling
clean_data = np.nan_to_num(data, nan=0.0)
has_nan = np.isnan(value)

# Type conversion (for database insertion)
if isinstance(value, np.float64):
    value = float(value)
if isinstance(value, np.int64):
    value = int(value)
```

---

### 7. yfinance 0.2.66

**What it is:** Yahoo Finance API wrapper for fetching stock data.

**Used for:**

- Fetching OHLCV historical data
- Getting stock information
- Real-time price data

**Key Operations:**

```python
import yfinance as yf

# Download historical data
df = yf.download(
    ticker,           # "RELIANCE.NS"
    period='200d',    # Last 200 days
    interval='1d',    # Daily data
    progress=False    # Suppress output
)

# Get stock info
stock = yf.Ticker("AAPL")
info = stock.info
print(info['longName'])  # "Apple Inc."

# Multiple tickers
data = yf.download(
    ["AAPL", "MSFT", "GOOGL"],
    period='1mo'
)
```

---

### 8. ta (Technical Analysis) 0.11.0

**What it is:** Technical Analysis library with 130+ indicators.

**Used for:**

- RSI, MACD, Bollinger Bands calculations
- Trend, momentum, volatility indicators
- Volume-based indicators

**Key Functions:**

```python
import ta

# Momentum indicators
rsi = ta.momentum.RSIIndicator(df['Close'], window=14)
rsi_value = rsi.rsi().iloc[-1]

# Trend indicators
macd = ta.trend.MACD(df['Close'])
macd_line = macd.macd()
signal_line = macd.macd_signal()

# Volatility indicators
bollinger = ta.volatility.BollingerBands(df['Close'], window=20)
upper_band = bollinger.bollinger_hband()
lower_band = bollinger.bollinger_lband()

# Volume indicators
obv = ta.volume.OnBalanceVolumeIndicator(df['Close'], df['Volume'])
obv_value = obv.on_balance_volume()
```

---

### 9. Pydantic 2.0

**What it is:** Data validation library using Python type annotations.

**Used for:**

- Request body validation
- Response schema validation
- Configuration validation

**Example:**

```python
from pydantic import BaseModel, Field, validator

class AnalyzeRequest(BaseModel):
    tickers: List[str]
    capital: float = Field(default=100000, gt=0)
    strategy_id: int = Field(default=1, ge=1, le=5)

    @validator('tickers')
    def validate_tickers(cls, v):
        if not v:
            raise ValueError('At least one ticker required')
        return [t.upper().strip() for t in v]
```

---

### 10. openpyxl 3.1.2

**What it is:** Library for reading/writing Excel files.

**Used for:**

- Generating downloadable analysis reports
- Creating formatted spreadsheets

**Example:**

```python
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment

wb = Workbook()
ws = wb.active
ws.title = "Analysis Report"

# Headers
ws['A1'] = 'Ticker'
ws['A1'].font = Font(bold=True)

# Data
ws['A2'] = ticker
ws['B2'] = score

# Save
wb.save(f"{ticker}_analysis.xlsx")
```

---

### 11. Flask-Limiter 3.5

**What it is:** Rate limiting extension for Flask.

**Used for:**

- Preventing API abuse
- Protecting expensive operations (analysis)

**Example:**

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["100 per hour"]
)

@bp.route("/analyze", methods=["POST"])
@limiter.limit("10 per minute")  # More restrictive for expensive operations
def analyze():
    pass
```

---

### 12. numba 0.58

**What it is:** JIT (Just-In-Time) compiler for Python.

**Used for:**

- Accelerating numerical computations
- Performance-critical indicator calculations

**Example:**

```python
from numba import jit

@jit(nopython=True)
def fast_moving_average(data, window):
    result = np.empty(len(data))
    for i in range(len(data)):
        if i < window:
            result[i] = np.nan
        else:
            result[i] = np.mean(data[i-window:i])
    return result
```

---

## Python Concepts Used

### 1. Threading

Background job processing without external dependencies:

```python
import threading

def start_analysis_job(job_id, tickers, capital):
    thread = threading.Thread(
        target=analyze_stocks_batch,
        args=(job_id, tickers, capital),
        daemon=False  # Keep alive for cloud deployments
    )
    thread.start()
    return thread
```

### 2. Context Managers

Resource management pattern:

```python
from contextlib import contextmanager

@contextmanager
def get_db_session():
    conn = get_db_connection()
    try:
        yield conn, conn.cursor()
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise
    finally:
        conn.close()

# Usage
with get_db_session() as (conn, cursor):
    cursor.execute(query)
```

### 3. Decorators

Function wrappers for cross-cutting concerns:

```python
def cached_indicator(func):
    """Caching decorator for indicator calculations"""
    cache = {}

    def wrapper(df, **kwargs):
        key = hash(str(df.index[-1]) + str(kwargs))
        if key not in cache:
            cache[key] = func(df, **kwargs)
        return cache[key]

    return wrapper

@cached_indicator
def calculate_rsi(df, period=14):
    pass
```

### 4. Generator Functions

Lazy evaluation for large datasets:

```python
def process_tickers(tickers):
    for ticker in tickers:
        yield analyze_ticker(ticker)

# Usage
for result in process_tickers(big_list):
    save_result(result)
```

### 5. Exception Handling

Structured error handling:

```python
try:
    result = analyze_ticker(ticker)
except ValueError as e:
    logger.error(f"Invalid input: {e}")
    return error_response("INVALID_INPUT", str(e))
except ConnectionError as e:
    logger.error(f"Network error: {e}")
    return error_response("NETWORK_ERROR", "Could not fetch data")
except Exception as e:
    logger.exception(f"Unexpected error analyzing {ticker}")
    return error_response("ANALYSIS_ERROR", str(e))
```

---

## Design Patterns Implemented

### 1. Factory Pattern

Creating objects without specifying exact class:

```python
def get_strategy_class(strategy_id: int):
    """Factory for strategy classes"""
    strategies = {
        1: Strategy1,
        2: Strategy2,
        3: Strategy3,
        4: Strategy4,
        5: Strategy5
    }
    return strategies.get(strategy_id, Strategy1)()
```

### 2. Template Method Pattern

Defining algorithm skeleton in base class:

```python
class IndicatorBase(ABC):
    """Template Method pattern implementation"""

    def vote_and_confidence(self, df):
        # Fixed algorithm structure
        value = self.calculate(df)          # Step 1: Calculate
        vote = self._get_vote(value, df)    # Step 2: Get vote
        conf = self._get_confidence(value)   # Step 3: Get confidence
        return {"value": value, "vote": vote, "confidence": conf}

    @abstractmethod
    def calculate(self, df): pass

    @abstractmethod
    def _get_vote(self, value, df): pass
```

### 3. Strategy Pattern

Interchangeable algorithms:

```python
class BaseStrategy(ABC):
    @abstractmethod
    def get_indicator_weights(self): pass

    @abstractmethod
    def get_category_weights(self): pass

class Strategy1(BaseStrategy):
    """Equal weights to all indicators"""
    def get_indicator_weights(self):
        return {ind: 1.0 for ind in ALL_INDICATORS}

class Strategy2(BaseStrategy):
    """Trend-focused weights"""
    def get_indicator_weights(self):
        return {"MACD": 1.5, "ADX": 1.5, "RSI": 0.8, ...}
```

### 4. Repository Pattern

Data access abstraction:

```python
# database.py acts as repository
def query_db(query, args=(), one=False):
    """Abstract database operations"""
    pass

def execute_db(query, args=()):
    """Abstract database modifications"""
    pass

# Usage in routes
results = query_db(
    "SELECT * FROM analysis_results WHERE ticker = ?",
    (ticker,)
)
```

### 5. Singleton Pattern

Single instance for shared resources:

```python
# Job state manager singleton
_job_state_manager = None

def get_job_state_manager():
    global _job_state_manager
    if _job_state_manager is None:
        _job_state_manager = JobStateManager()
    return _job_state_manager
```

---

## Configuration Management

### Environment Variables

```python
import os
from dotenv import load_dotenv

load_dotenv()  # Load .env file

class Config:
    DATABASE_URL = os.getenv('DATABASE_URL')
    DATA_PATH = os.getenv('DATA_PATH', './data')
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
```

### Configuration Objects

```python
# config.py
class DevelopmentConfig:
    DEBUG = True
    LOG_LEVEL = "DEBUG"

class ProductionConfig:
    DEBUG = False
    LOG_LEVEL = "WARNING"

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig
}
```

---

## Logging

### Logger Setup

```python
import logging

def setup_logger():
    logger = logging.getLogger('trading_analyzer')
    logger.setLevel(logging.DEBUG)

    # Console handler
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(handler)

    return logger
```

### Usage

```python
logger = setup_logger()

logger.debug("Detailed debugging info")
logger.info("General information")
logger.warning("Warning messages")
logger.error("Error messages")
logger.exception("Error with stack trace")  # In except block
```

---

## Testing

### pytest

```python
import pytest
from app import create_app

@pytest.fixture
def client():
    app = create_app({'TESTING': True})
    with app.test_client() as client:
        yield client

def test_analyze_endpoint(client):
    response = client.post('/api/analysis/analyze', json={
        'tickers': ['AAPL'],
        'capital': 100000
    })
    assert response.status_code == 201
    assert 'job_id' in response.json
```

---

## Key Libraries Summary

| Library         | Version | Purpose               |
| --------------- | ------- | --------------------- |
| Flask           | 3.0.0   | Web framework         |
| Flask-CORS      | 4.0.0   | CORS handling         |
| psycopg2-binary | 2.9.9   | PostgreSQL driver     |
| pandas          | 2.2.3+  | Data manipulation     |
| numpy           | 1.26.2+ | Numerical computing   |
| yfinance        | 0.2.66  | Stock data fetching   |
| ta              | 0.11.0  | Technical analysis    |
| openpyxl        | 3.1.2   | Excel reports         |
| Pydantic        | 2.0+    | Data validation       |
| Flask-Limiter   | 3.5+    | Rate limiting         |
| numba           | 0.58+   | JIT compilation       |
| python-dotenv   | 1.0.0   | Environment variables |
| pytest          | 7.4+    | Testing framework     |
