# Libraries and Processes Explained

## Overview

This document provides detailed explanations of all major libraries and processes used in TheTool, beyond basic constructs. Each library is explained with its purpose, key features, and practical usage in this project.

---

## Frontend Libraries

### 1. Axios (HTTP Client)

**Purpose:** Make HTTP requests from browser to backend server.

**Why Axios over Fetch API:**
| Feature | Axios | Fetch |
|---------|-------|-------|
| Automatic JSON parsing | ✅ | ❌ Manual |
| Request interceptors | ✅ | ❌ |
| Timeout support | ✅ | ❌ Native |
| Progress tracking | ✅ | ❌ |
| Request cancellation | ✅ Easy | ⚠️ AbortController |
| Browser compatibility | ✅ | IE11 needs polyfill |

**Key Concepts:**

#### Instance Configuration

```javascript
const api = axios.create({
  baseURL: "http://localhost:5000",
  timeout: 30000, // 30 seconds
  headers: {
    "Content-Type": "application/json",
  },
});
```

#### Request/Response Interceptors

```javascript
// Add auth token to every request
api.interceptors.request.use((config) => {
  config.headers["X-API-Key"] = process.env.API_KEY;
  return config;
});

// Handle errors globally
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized
    }
    return Promise.reject(error);
  },
);
```

#### Response Types

```javascript
// JSON (default)
const response = await api.get("/data");
const data = response.data;

// Binary (for file downloads)
const response = await api.get("/download", { responseType: "blob" });
```

---

### 2. React Router DOM (Navigation)

**Purpose:** Enable client-side routing in React applications without full page reloads.

**Key Concepts:**

#### Route Matching

```javascript
<Routes>
  {/* Exact match */}
  <Route path="/" element={<Home />} />

  {/* Dynamic segment */}
  <Route path="/results/:ticker" element={<Results />} />

  {/* Nested routes */}
  <Route path="/strategies" element={<StrategiesLayout />}>
    <Route index element={<StrategiesList />} />
    <Route path=":id" element={<StrategyDetail />} />
  </Route>

  {/* Catch-all (404) */}
  <Route path="*" element={<NotFound />} />
</Routes>
```

#### Navigation Methods

```javascript
// Declarative (Link component)
<Link to="/results/AAPL">View AAPL</Link>;

// Programmatic (useNavigate hook)
const navigate = useNavigate();
navigate("/results/AAPL"); // Push
navigate("/results/AAPL", { replace: true }); // Replace
navigate(-1); // Go back
```

#### URL Parameters

```javascript
// Route: /results/:ticker
const { ticker } = useParams(); // ticker = "AAPL"
```

#### Query Parameters

```javascript
// URL: /search?q=apple&page=2
const [searchParams] = useSearchParams();
const query = searchParams.get("q"); // "apple"
const page = searchParams.get("page"); // "2"
```

---

### 3. Tailwind CSS (Styling)

**Purpose:** Utility-first CSS framework for rapid UI development.

**Core Philosophy:**
Instead of writing CSS:

```css
.button {
  padding: 8px 16px;
  background-color: blue;
  color: white;
  border-radius: 4px;
}
```

Write utility classes directly:

```jsx
<button className="py-2 px-4 bg-blue-500 text-white rounded">Click</button>
```

**Key Utility Categories:**

#### Layout

```
flex           → display: flex
grid           → display: grid
items-center   → align-items: center
justify-between → justify-content: space-between
gap-4          → gap: 1rem
```

#### Spacing

```
p-4   → padding: 1rem
px-4  → padding-left/right: 1rem
py-2  → padding-top/bottom: 0.5rem
m-4   → margin: 1rem
mt-8  → margin-top: 2rem
```

#### Sizing

```
w-full    → width: 100%
w-1/2     → width: 50%
h-screen  → height: 100vh
max-w-md  → max-width: 28rem
```

#### Colors

```
text-blue-500   → color: #3b82f6
bg-gray-100     → background: #f3f4f6
border-red-500  → border-color: #ef4444
```

#### Responsive Design

```
md:flex  → @media (min-width: 768px) { display: flex }
lg:w-1/3 → @media (min-width: 1024px) { width: 33.33% }
```

---

### 4. React Context API (State Management)

**Purpose:** Share state across components without prop drilling.

**The Problem (Prop Drilling):**

```jsx
// Without Context - props passed through every level
<App>
  <Layout user={user}>
    <Sidebar user={user}>
      <UserInfo user={user} /> // Finally uses it
    </Sidebar>
  </Layout>
</App>
```

**The Solution (Context):**

```jsx
// With Context - direct access from any level
<UserProvider value={user}>
  <App>
    <Layout>
      <Sidebar>
        <UserInfo /> // Uses useContext(UserContext)
      </Sidebar>
    </Layout>
  </App>
</UserProvider>
```

**Implementation Pattern:**

```javascript
// 1. Create Context
const StocksContext = createContext(null);

// 2. Provider Component
export function StocksProvider({ children }) {
  const [stocks, setStocks] = useState([]);

  const addStock = (stock) => setStocks([...stocks, stock]);

  return (
    <StocksContext.Provider value={{ stocks, addStock }}>
      {children}
    </StocksContext.Provider>
  );
}

// 3. Custom Hook for access
export function useStocks() {
  const context = useContext(StocksContext);
  if (!context) throw new Error("Must be used within StocksProvider");
  return context;
}

// 4. Usage anywhere in tree
function SomeComponent() {
  const { stocks, addStock } = useStocks();
}
```

---

## Backend Libraries

### 5. Flask (Web Framework)

**Purpose:** Lightweight WSGI web framework for building REST APIs.

**Core Concepts:**

#### Application Factory Pattern

```python
def create_app(config=None):
    app = Flask(__name__)

    # Configuration
    app.config.from_object(config or 'config.DevelopmentConfig')

    # Extensions
    CORS(app)

    # Blueprints
    app.register_blueprint(api_bp, url_prefix='/api')

    # Initialize database
    with app.app_context():
        init_db()

    return app
```

#### Blueprints (Modular Routes)

```python
# routes/analysis.py
bp = Blueprint('analysis', __name__, url_prefix='/api/analysis')

@bp.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    return jsonify(result), 201
```

#### Request Handling

```python
@bp.route('/analyze', methods=['POST'])
def analyze():
    # JSON body
    data = request.get_json()
    tickers = data.get('tickers')

    # Query parameters
    page = request.args.get('page', 1, type=int)

    # Headers
    api_key = request.headers.get('X-API-Key')

    # Return JSON
    return jsonify({"status": "ok"}), 200
```

#### Request Context

```python
from flask import g

def get_db():
    if 'db' not in g:
        g.db = create_connection()
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()
```

---

### 6. pandas (Data Analysis)

**Purpose:** Data manipulation and analysis, especially for tabular data.

**Core Concepts:**

#### DataFrame Creation

```python
import pandas as pd

# From dictionary
df = pd.DataFrame({
    'Date': ['2024-01-01', '2024-01-02'],
    'Close': [100.5, 102.3],
    'Volume': [1000000, 1200000]
})

# From CSV
df = pd.read_csv('data.csv')

# From API (yfinance)
df = yf.download('AAPL', period='1mo')
```

#### Column Operations

```python
# Select column (returns Series)
prices = df['Close']

# Select multiple columns
df[['Open', 'Close', 'Volume']]

# Create new column
df['SMA_20'] = df['Close'].rolling(20).mean()

# Conditional column
df['Signal'] = np.where(df['Close'] > df['SMA_20'], 'Buy', 'Sell')
```

#### Row Operations

```python
# Last row
latest = df.iloc[-1]

# Last N rows
recent = df.tail(20)

# Filter rows
bullish = df[df['Signal'] == 'Buy']

# Multiple conditions
strong = df[(df['Score'] > 70) & (df['Volume'] > 1000000)]
```

#### Rolling Calculations

```python
# Simple Moving Average
df['SMA_50'] = df['Close'].rolling(window=50).mean()

# Exponential Moving Average
df['EMA_20'] = df['Close'].ewm(span=20).mean()

# Rolling Standard Deviation
df['STD_20'] = df['Close'].rolling(window=20).std()
```

#### Time Series

```python
# Set datetime index
df['Date'] = pd.to_datetime(df['Date'])
df.set_index('Date', inplace=True)

# Resample
weekly = df.resample('W').mean()
monthly = df.resample('M').last()
```

---

### 7. yfinance (Market Data)

**Purpose:** Download market data from Yahoo Finance.

**Key Functions:**

#### Download Historical Data

```python
import yfinance as yf

# Single ticker
df = yf.download('AAPL', period='1y', interval='1d')

# Multiple tickers
df = yf.download(['AAPL', 'MSFT', 'GOOGL'], period='1mo')

# With dates
df = yf.download('AAPL', start='2024-01-01', end='2024-12-31')
```

**Parameters:**
| Parameter | Values | Description |
|-----------|--------|-------------|
| period | 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max | Time period |
| interval | 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo | Data granularity |

#### Ticker Object

```python
ticker = yf.Ticker('AAPL')

# Company info
info = ticker.info
print(info['longName'])      # "Apple Inc."
print(info['marketCap'])     # 3000000000000
print(info['sector'])        # "Technology"

# Historical data
hist = ticker.history(period='1mo')

# Actions (dividends, splits)
actions = ticker.actions
```

---

### 8. ta (Technical Analysis)

**Purpose:** Calculate 130+ technical analysis indicators.

**Indicator Categories:**

#### Momentum Indicators

```python
import ta

# RSI (Relative Strength Index)
rsi = ta.momentum.RSIIndicator(df['Close'], window=14)
df['RSI'] = rsi.rsi()

# Stochastic Oscillator
stoch = ta.momentum.StochasticOscillator(df['High'], df['Low'], df['Close'])
df['Stoch_K'] = stoch.stoch()
df['Stoch_D'] = stoch.stoch_signal()

# Williams %R
williams = ta.momentum.WilliamsRIndicator(df['High'], df['Low'], df['Close'])
df['Williams_R'] = williams.williams_r()
```

#### Trend Indicators

```python
# MACD
macd = ta.trend.MACD(df['Close'])
df['MACD'] = macd.macd()
df['MACD_Signal'] = macd.macd_signal()
df['MACD_Diff'] = macd.macd_diff()

# ADX (Average Directional Index)
adx = ta.trend.ADXIndicator(df['High'], df['Low'], df['Close'])
df['ADX'] = adx.adx()
df['DI+'] = adx.adx_pos()
df['DI-'] = adx.adx_neg()

# EMA
df['EMA_50'] = ta.trend.EMAIndicator(df['Close'], window=50).ema_indicator()
df['EMA_200'] = ta.trend.EMAIndicator(df['Close'], window=200).ema_indicator()
```

#### Volatility Indicators

```python
# Bollinger Bands
bollinger = ta.volatility.BollingerBands(df['Close'], window=20)
df['BB_Upper'] = bollinger.bollinger_hband()
df['BB_Middle'] = bollinger.bollinger_mavg()
df['BB_Lower'] = bollinger.bollinger_lband()

# ATR (Average True Range)
atr = ta.volatility.AverageTrueRange(df['High'], df['Low'], df['Close'])
df['ATR'] = atr.average_true_range()
```

#### Volume Indicators

```python
# OBV (On-Balance Volume)
obv = ta.volume.OnBalanceVolumeIndicator(df['Close'], df['Volume'])
df['OBV'] = obv.on_balance_volume()

# CMF (Chaikin Money Flow)
cmf = ta.volume.ChaikinMoneyFlowIndicator(df['High'], df['Low'], df['Close'], df['Volume'])
df['CMF'] = cmf.chaikin_money_flow()
```

---

### 9. psycopg2 (PostgreSQL Driver)

**Purpose:** PostgreSQL database adapter for Python.

**Connection Management:**

```python
import psycopg2

# Connect
conn = psycopg2.connect(
    host="localhost",
    database="trading_db",
    user="postgres",
    password="password"
)

# Or with connection string
conn = psycopg2.connect("postgresql://user:pass@localhost:5432/db")

# Cursor for queries
cursor = conn.cursor()
```

**Query Execution:**

```python
# Select
cursor.execute("SELECT * FROM stocks WHERE ticker = %s", ('AAPL',))
rows = cursor.fetchall()  # List of tuples

# Insert
cursor.execute(
    "INSERT INTO stocks (ticker, name) VALUES (%s, %s)",
    ('AAPL', 'Apple Inc.')
)
conn.commit()

# Update
cursor.execute(
    "UPDATE stocks SET score = %s WHERE ticker = %s",
    (75.5, 'AAPL')
)
conn.commit()
```

**Parameterized Queries (SQL Injection Prevention):**

```python
# SAFE - parameterized
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))

# UNSAFE - string formatting (NEVER DO THIS)
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
```

**Transaction Management:**

```python
try:
    cursor.execute(insert_query, args)
    cursor.execute(update_query, args)
    conn.commit()  # Both succeed
except Exception:
    conn.rollback()  # Undo all
finally:
    cursor.close()
    conn.close()
```

---

### 10. threading (Concurrent Execution)

**Purpose:** Run code in parallel without external task queue (Redis/Celery).

**Basic Thread Creation:**

```python
import threading

def background_task(arg1, arg2):
    # Long-running work
    result = expensive_computation(arg1, arg2)
    save_result(result)

# Create thread
thread = threading.Thread(
    target=background_task,
    args=(value1, value2),
    daemon=False  # Non-daemon survives main thread exit
)

# Start execution
thread.start()

# Continue immediately (non-blocking)
return {"status": "started"}
```

**Thread Pool:**

```python
from concurrent.futures import ThreadPoolExecutor

def analyze_ticker(ticker):
    return fetch_and_analyze(ticker)

with ThreadPoolExecutor(max_workers=4) as executor:
    # Submit all tasks
    futures = [executor.submit(analyze_ticker, t) for t in tickers]

    # Collect results
    results = [f.result() for f in futures]
```

**Thread Safety:**

```python
import threading

# Lock for shared resources
db_lock = threading.Lock()

def save_to_db(data):
    with db_lock:  # Only one thread at a time
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(insert_query, data)
        connection.commit()
```

---

## Processes Explained

### 1. Polling Pattern

**Problem:** User starts a long-running job (analysis). Page needs to show progress.

**Solution:** Frontend polls backend for status updates.

```javascript
const pollJobStatus = async (jobId) => {
  const interval = setInterval(async () => {
    const status = await getJobStatus(jobId);

    setProgress(status.progress);

    if (status.status === "completed" || status.status === "failed") {
      clearInterval(interval);
      handleCompletion(status);
    }
  }, 2000); // Every 2 seconds
};
```

**Alternative Patterns:**
| Pattern | Pros | Cons |
|---------|------|------|
| Polling | Simple, works everywhere | Network overhead |
| WebSockets | Real-time, efficient | Complex setup |
| Server-Sent Events | One-way streaming | Less browser support |

---

### 2. Template Method Pattern (Indicators)

**Problem:** 12 indicators with same structure but different calculations.

**Solution:** Abstract base class defines algorithm skeleton.

```python
class IndicatorBase(ABC):
    """Template: defines the steps"""

    def vote_and_confidence(self, df):
        # Step 1: Calculate (subclass implements)
        value = self.calculate(df)

        # Step 2: Get vote (subclass implements)
        vote = self._get_vote(value, df)

        # Step 3: Get confidence (subclass implements)
        conf = self._get_confidence(value, df)

        return {"value": value, "vote": vote, "confidence": conf}

    @abstractmethod
    def calculate(self, df): pass

    @abstractmethod
    def _get_vote(self, value, df): pass

class RSIIndicator(IndicatorBase):
    """Concrete implementation"""

    def calculate(self, df):
        return ta.momentum.RSIIndicator(df['Close']).rsi().iloc[-1]

    def _get_vote(self, value, df):
        if value < 30: return 1   # Oversold = Buy
        if value > 70: return -1  # Overbought = Sell
        return 0                  # Neutral
```

---

### 3. Strategy Pattern (Trading Strategies)

**Problem:** Different users want different weighting of indicators.

**Solution:** Interchangeable strategy objects.

```python
class BaseStrategy(ABC):
    @abstractmethod
    def get_weights(self) -> Dict[str, float]:
        pass

class BalancedStrategy(BaseStrategy):
    def get_weights(self):
        return {"RSI": 1.0, "MACD": 1.0, "ADX": 1.0, ...}

class TrendStrategy(BaseStrategy):
    def get_weights(self):
        return {"RSI": 0.5, "MACD": 1.5, "ADX": 1.5, ...}

# Usage
def calculate_score(indicators, strategy: BaseStrategy):
    weights = strategy.get_weights()

    total = 0
    for ind in indicators:
        total += ind['vote'] * weights[ind['name']] * ind['confidence']

    return total / len(indicators)
```

---

### 4. Application Factory Pattern

**Problem:** Need different configurations for dev/test/production.

**Solution:** Function that creates configured app instance.

```python
def create_app(config_name='development'):
    app = Flask(__name__)

    # Load config based on environment
    if config_name == 'production':
        app.config.from_object(ProductionConfig)
    elif config_name == 'testing':
        app.config.from_object(TestingConfig)
    else:
        app.config.from_object(DevelopmentConfig)

    # Initialize extensions
    CORS(app)

    # Register blueprints
    app.register_blueprint(analysis_bp)

    return app

# Usage
app = create_app('production')  # In production
app = create_app('testing')     # In tests
```

---

### 5. Context Manager Pattern (Database)

**Problem:** Database connections must be closed even if errors occur.

**Solution:** Context manager guarantees cleanup.

```python
from contextlib import contextmanager

@contextmanager
def get_db_session():
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    try:
        yield conn, cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

# Usage - connection always cleaned up
with get_db_session() as (conn, cursor):
    cursor.execute(query, args)
    # Error here? Still closes connection
```

---

### 6. Caching with TTL

**Problem:** Frequent API calls for same data waste resources.

**Solution:** Cache with Time-To-Live expiration.

```javascript
// Frontend caching
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes

const cache = {
  data: null,
  timestamp: null,
};

const getCachedData = async () => {
  const now = Date.now();

  // Return cached if valid
  if (cache.data && now - cache.timestamp < CACHE_TTL) {
    return cache.data;
  }

  // Fetch fresh data
  const freshData = await fetchFromAPI();

  // Update cache
  cache.data = freshData;
  cache.timestamp = now;

  return freshData;
};
```

```python
# Backend caching (simple in-memory)
from functools import lru_cache
from datetime import datetime, timedelta

@lru_cache(maxsize=100)
def get_cached_indicator(ticker, indicator_name, cache_key):
    """cache_key includes timestamp for TTL"""
    return calculate_indicator(ticker, indicator_name)

def get_indicator(ticker, indicator_name):
    # Create cache key - changes every 5 minutes
    cache_key = datetime.now().strftime("%Y%m%d%H") + str(datetime.now().minute // 5)
    return get_cached_indicator(ticker, indicator_name, cache_key)
```
