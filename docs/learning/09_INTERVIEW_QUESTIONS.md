# Interview Questions - TheTool Project

## Overview

This document contains 100+ interview questions covering all aspects of the TheTool project, organized by category. These questions range from basic to advanced, suitable for various skill levels.

---

## Frontend - React Basics (1-15)

### 1. What is React and why is it used in this project?

**Answer:** React is a JavaScript library for building user interfaces using a component-based architecture. It's used in TheTool for:

- Component reusability (StockRow, Modal components)
- Virtual DOM for efficient updates when stock data changes
- Declarative UI patterns

### 2. Explain the difference between functional and class components.

**Answer:** Functional components are JavaScript functions that return JSX. Class components extend React.Component. This project uses functional components because:

- They're simpler and more readable
- Hooks provide all lifecycle functionality
- Better performance due to no `this` binding

### 3. What are React Hooks? Name the hooks used in this project.

**Answer:** Hooks are functions that let you use state and lifecycle features in functional components. Used hooks:

- `useState` - State management
- `useEffect` - Side effects (API calls)
- `useContext` - Access StocksContext
- `useCallback` - Memoized functions
- `useMemo` - Memoized values
- `useNavigate`, `useParams` - React Router hooks

### 4. Explain the useState hook with an example from the project.

**Answer:**

```javascript
const [loading, setLoading] = useState(false);
const [watchlist, setWatchlist] = useState([]);

// Update state
setLoading(true);
setWatchlist([...watchlist, newStock]);
```

### 5. What is the purpose of useEffect? When does it run?

**Answer:** `useEffect` handles side effects like API calls. It runs:

- After every render (no dependency array)
- Once on mount (empty array `[]`)
- When dependencies change (`[ticker]`)

```javascript
useEffect(() => {
  fetchData();
}, [ticker]); // Runs when ticker changes
```

### 6. What is JSX? How does it differ from HTML?

**Answer:** JSX is JavaScript XML - syntax extension that allows HTML-like code in JavaScript. Differences:

- `className` instead of `class`
- `htmlFor` instead of `for`
- camelCase for event handlers (`onClick`)
- Can embed JavaScript expressions with `{}`

### 7. Explain conditional rendering in React.

**Answer:**

```javascript
{
  isLoading && <Spinner />;
}
{
  error ? <ErrorMessage /> : <Results />;
}
{
  items.length > 0 && <ItemList items={items} />;
}
```

### 8. How do you handle lists in React? Why are keys important?

**Answer:**

```javascript
{
  stocks.map((stock) => <StockRow key={stock.ticker} stock={stock} />);
}
```

Keys help React identify which items changed, improving reconciliation performance.

### 9. What is prop drilling and how does this project avoid it?

**Answer:** Prop drilling is passing props through many levels of components. This project uses React Context (StocksContext) to provide global state access without prop drilling.

### 10. Explain the useCallback hook and when to use it.

**Answer:** `useCallback` returns a memoized callback that only changes if dependencies change. Used to prevent unnecessary re-renders:

```javascript
const handleClick = useCallback(() => {
  analyzeStock(ticker);
}, [ticker]);
```

### 11. What is useMemo? How is it different from useCallback?

**Answer:**

- `useMemo` memoizes a computed **value**
- `useCallback` memoizes a **function**

```javascript
const sortedStocks = useMemo(() => stocks.sort(), [stocks]);
const handleClick = useCallback(() => doSomething(), []);
```

### 12. How do you handle forms in React?

**Answer:** Using controlled components where form state is managed by React:

```javascript
const [ticker, setTicker] = useState("");
<input value={ticker} onChange={(e) => setTicker(e.target.value)} />;
```

### 13. What is the Virtual DOM?

**Answer:** A lightweight copy of the real DOM that React uses to:

1. Compare with previous version (diffing)
2. Calculate minimal changes needed
3. Batch updates to real DOM efficiently

### 14. Explain the component lifecycle in functional components.

**Answer:**

- **Mounting:** `useEffect(() => {}, [])` - runs once
- **Updating:** `useEffect(() => {}, [deps])` - runs on dependency change
- **Unmounting:** Cleanup function in useEffect

### 15. How do you handle errors in React components?

**Answer:** Using try-catch in async functions and error state:

```javascript
try {
  const data = await fetchData();
  setData(data);
} catch (error) {
  setError(error.message);
}
```

---

## Frontend - React Router (16-25)

### 16. What is React Router and why is it needed?

**Answer:** React Router enables client-side routing - navigating between pages without full page reloads. Needed for single-page applications like TheTool.

### 17. Explain BrowserRouter vs HashRouter.

**Answer:**

- `BrowserRouter` - Uses HTML5 history API (`/results/AAPL`)
- `HashRouter` - Uses URL hash (`/#/results/AAPL`)
  TheTool uses BrowserRouter.

### 18. How do you define routes in React Router v6?

**Answer:**

```javascript
<Routes>
  <Route path="/" element={<Dashboard />} />
  <Route path="/results/:ticker" element={<Results />} />
</Routes>
```

### 19. What are dynamic route parameters? How do you access them?

**Answer:** Dynamic segments prefixed with `:`. Access with `useParams`:

```javascript
// Route: /results/:ticker
const { ticker } = useParams(); // "AAPL"
```

### 20. Explain the difference between Link and useNavigate.

**Answer:**

- `Link` - Declarative navigation via component
- `useNavigate` - Programmatic navigation via hook

```javascript
<Link to="/dashboard">Dashboard</Link>;
navigate("/dashboard");
```

### 21. How do you handle 404 pages?

**Answer:** Using a catch-all route:

```javascript
<Route path="*" element={<NotFound />} />
```

### 22. What is nested routing?

**Answer:** Routes within routes:

```javascript
<Route path="/strategies" element={<StrategiesLayout />}>
  <Route index element={<StrategiesList />} />
  <Route path=":id" element={<StrategyDetail />} />
</Route>
```

### 23. How do you pass state during navigation?

**Answer:**

```javascript
navigate("/results", { state: { fromDashboard: true } });

// Access in target component
const location = useLocation();
const { fromDashboard } = location.state;
```

### 24. What is the purpose of the Outlet component?

**Answer:** Renders child route elements in nested routing:

```javascript
function StrategiesLayout() {
  return (
    <div>
      <StrategiesNav />
      <Outlet /> {/* Child routes render here */}
    </div>
  );
}
```

### 25. How do you implement protected routes?

**Answer:**

```javascript
function ProtectedRoute({ children }) {
  const isAuthenticated = useAuth();
  return isAuthenticated ? children : <Navigate to="/login" />;
}

<Route
  path="/admin"
  element={
    <ProtectedRoute>
      <Admin />
    </ProtectedRoute>
  }
/>;
```

---

## Frontend - State Management & Context (26-35)

### 26. Explain React Context API.

**Answer:** Context provides a way to pass data through the component tree without prop drilling. Components:

- `createContext` - Creates context
- `Provider` - Provides value
- `useContext` - Consumes value

### 27. How is StocksContext structured in this project?

**Answer:**

```javascript
const StocksContext = createContext(null);

function StocksProvider({ children }) {
  const [allStocks, setAllStocks] = useState([]);
  const [watchlist, setWatchlist] = useState([]);

  return (
    <StocksContext.Provider value={{ allStocks, watchlist, ... }}>
      {children}
    </StocksContext.Provider>
  );
}
```

### 28. What data is stored in StocksContext?

**Answer:**

- `allStocks` - List of all NSE stocks
- `watchlist` - User's watchlist
- `analysisResults` - Cached analysis results
- Cache timestamps for TTL validation
- Fetch functions for each data type

### 29. How is caching implemented in the context?

**Answer:**

```javascript
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes

const isCacheValid = (lastFetch) => {
  if (!lastFetch) return false;
  return Date.now() - lastFetch < CACHE_TTL;
};
```

### 30. When would you use Context vs Redux?

**Answer:**
Use Context for:

- Simple state sharing
- Medium-sized apps
- Low update frequency

Use Redux for:

- Complex state logic
- Time-travel debugging
- Large applications

This project uses Context - appropriate for its size.

### 31. How do you avoid unnecessary re-renders with Context?

**Answer:**

- Split context into smaller contexts
- Use `useMemo` for context value
- Use selectors with `useContextSelector` (library)

### 32. Explain the custom hook pattern for context.

**Answer:**

```javascript
export function useStocks() {
  const context = useContext(StocksContext);
  if (!context) {
    throw new Error("useStocks must be used within StocksProvider");
  }
  return context;
}
```

### 33. How do you update context state?

**Answer:** Include update functions in the provider value:

```javascript
const value = {
  watchlist,
  addToWatchlist: (stock) => setWatchlist([...watchlist, stock]),
  removeFromWatchlist: (ticker) =>
    setWatchlist(watchlist.filter((s) => s.ticker !== ticker)),
};
```

### 34. What is the difference between local state and context state?

**Answer:**

- **Local state** (`useState`): Component-specific, like form inputs, loading states
- **Context state**: Shared across components, like user data, watchlist

### 35. How do you handle loading and error states with context?

**Answer:**

```javascript
const [loading, setLoading] = useState(false);
const [error, setError] = useState(null);

const fetchData = async () => {
  setLoading(true);
  setError(null);
  try {
    const data = await api.getData();
    setData(data);
  } catch (err) {
    setError(err.message);
  } finally {
    setLoading(false);
  }
};
```

---

## Frontend - API & HTTP (36-45)

### 36. What is Axios? Why use it over fetch?

**Answer:** Axios is an HTTP client. Benefits over fetch:

- Automatic JSON transformation
- Request/response interceptors
- Built-in timeout support
- Better error handling

### 37. How is the API layer organized in this project?

**Answer:** Centralized in `api/api.js`:

- Single axios instance with base URL
- Grouped functions by domain (analysis, watchlist, stocks)
- Error handling abstraction

### 38. How does the frontend determine which backend URL to use?

**Answer:** Based on hostname:

```javascript
const hostname = window.location.hostname;
if (hostname === "localhost") return "http://localhost:5000";
if (hostname.includes("vercel")) return "https://railway.app/...";
```

### 39. Explain the polling pattern for job status.

**Answer:**

```javascript
const pollStatus = (jobId) => {
  const interval = setInterval(async () => {
    const status = await getJobStatus(jobId);
    if (status.status === "completed") {
      clearInterval(interval);
      handleResults(status.results);
    }
  }, 2000);
};
```

### 40. How do you handle file downloads from the API?

**Answer:**

```javascript
const response = await api.get("/download", { responseType: "blob" });
const url = URL.createObjectURL(new Blob([response.data]));
const link = document.createElement("a");
link.href = url;
link.download = "report.xlsx";
link.click();
```

### 41. What HTTP methods are used and for what purposes?

**Answer:**

- `GET` - Fetch data (watchlist, status)
- `POST` - Create/start operations (analyze, add to watchlist)
- `DELETE` - Remove resources (remove from watchlist)

### 42. How do you handle API errors in components?

**Answer:**

```javascript
try {
  const result = await analyzeStocks(tickers);
  setResults(result);
} catch (error) {
  if (error.response?.status === 404) {
    setError("Stock not found");
  } else {
    setError("Analysis failed");
  }
}
```

### 43. What is CORS and why is it needed?

**Answer:** Cross-Origin Resource Sharing - browser security that blocks requests to different origins. Needed because frontend (port 3000) and backend (port 5000) are different origins.

### 44. How do you add headers to API requests?

**Answer:**

```javascript
const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
    "X-API-Key": process.env.API_KEY,
  },
});
```

### 45. Explain request/response interceptors.

**Answer:**

```javascript
// Request interceptor - add auth token
api.interceptors.request.use((config) => {
  config.headers.Authorization = getToken();
  return config;
});

// Response interceptor - handle errors globally
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) logout();
    return Promise.reject(error);
  },
);
```

---

## Backend - Flask Basics (46-55)

### 46. What is Flask? Why was it chosen for this project?

**Answer:** Flask is a lightweight WSGI web framework. Chosen for:

- Simple and flexible
- Great for APIs
- Excellent Python ecosystem integration (pandas, yfinance)
- Easy to extend

### 47. Explain the Application Factory pattern.

**Answer:** Function that creates and configures the app:

```python
def create_app(config=None):
    app = Flask(__name__)
    app.config.from_object(config)
    CORS(app)
    app.register_blueprint(api_bp)
    return app
```

Benefits: Testing, multiple configs, delayed initialization.

### 48. What are Flask Blueprints? How are they used?

**Answer:** Blueprints are modular route collections:

```python
bp = Blueprint('analysis', __name__, url_prefix='/api/analysis')

@bp.route('/analyze', methods=['POST'])
def analyze():
    pass

# Register in app
app.register_blueprint(bp)
```

### 49. How do you access request data in Flask?

**Answer:**

```python
# JSON body
data = request.get_json()

# Query parameters
page = request.args.get('page', 1, type=int)

# Headers
api_key = request.headers.get('X-API-Key')

# Form data
name = request.form.get('name')
```

### 50. How do you return JSON responses?

**Answer:**

```python
from flask import jsonify

return jsonify({"status": "ok", "data": result}), 200
return jsonify({"error": "Not found"}), 404
```

### 51. What is the Flask request context?

**Answer:** Request-scoped context that holds request data. Accessed via `g` object:

```python
from flask import g

def get_db():
    if 'db' not in g:
        g.db = create_connection()
    return g.db
```

### 52. How is CORS configured in this project?

**Answer:**

```python
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000", "https://vercel.app"],
        "methods": ["GET", "POST", "DELETE"],
        "allow_headers": ["Content-Type", "X-API-Key"]
    }
})
```

### 53. How do you handle errors in Flask?

**Answer:**

```python
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404

# Or in route
try:
    result = process()
except ValueError as e:
    return jsonify({"error": str(e)}), 400
```

### 54. What is WSGI?

**Answer:** Web Server Gateway Interface - standard interface between web servers and Python applications. Flask is a WSGI application. Gunicorn is a WSGI server.

### 55. How is the server run in development vs production?

**Answer:**

```bash
# Development
flask run --debug

# Production
gunicorn --config gunicorn.conf.py wsgi:app
```

---

## Backend - Database (56-70)

### 56. What database is used and why?

**Answer:** PostgreSQL - chosen for:

- Robust and reliable
- Full-text search capabilities
- JSON column support (for raw_data)
- Production-ready for cloud deployment

### 57. What is psycopg2?

**Answer:** PostgreSQL adapter for Python. Used for database connections and query execution.

### 58. Explain the database schema.

**Answer:** Main tables:

- `analysis_jobs` - Background job tracking
- `analysis_results` - Stock analysis results
- `watchlist` - User watchlist
- `watchlist_collections` - Watchlist grouping
- `strategies` - Trading strategy definitions

### 59. How are database connections managed?

**Answer:** Three patterns:

1. **Flask context** - `g.db` for request-scoped
2. **Context manager** - `with get_db_session()` for threads
3. **Direct** - For standalone scripts

### 60. What is SQL injection? How is it prevented?

**Answer:** Malicious SQL in user input. Prevented with parameterized queries:

```python
# SAFE
cursor.execute("SELECT * FROM stocks WHERE ticker = %s", (ticker,))

# UNSAFE (never do this)
cursor.execute(f"SELECT * FROM stocks WHERE ticker = '{ticker}'")
```

### 61. How do you handle database transactions?

**Answer:**

```python
try:
    cursor.execute(insert_query)
    cursor.execute(update_query)
    conn.commit()  # Both succeed
except Exception:
    conn.rollback()  # Undo all
```

### 62. What indexes are used in this project?

**Answer:**

```sql
CREATE INDEX idx_analysis_ticker ON analysis_results(ticker);
CREATE INDEX idx_analysis_created ON analysis_results(created_at DESC);
CREATE INDEX idx_jobs_status ON analysis_jobs(status);
```

### 63. How is the raw indicator data stored?

**Answer:** As JSON text in the `raw_data` column:

```python
raw_data = json.dumps(indicators)
cursor.execute("INSERT INTO analysis_results (raw_data) VALUES (%s)", (raw_data,))

# Retrieval
indicators = json.loads(row['raw_data'])
```

### 64. How is database initialization handled?

**Answer:** Using `init_db()` with retry logic:

```python
def init_db():
    for attempt in range(MAX_RETRIES):
        try:
            _init_postgres_db()
            return True
        except Exception:
            time.sleep(2 ** attempt)  # Exponential backoff
    raise Exception("Failed to initialize")
```

### 65. How are timestamps handled?

**Answer:** Using IST (Indian Standard Time):

```python
from datetime import datetime
import pytz

def get_ist_timestamp():
    ist = pytz.timezone('Asia/Kolkata')
    return datetime.now(ist).isoformat()
```

### 66. What is the difference between query_db and execute_db?

**Answer:**

- `query_db` - SELECT queries, returns results
- `execute_db` - INSERT/UPDATE/DELETE, returns affected rows

### 67. How do you handle NULL values from database?

**Answer:**

```python
score = result[0] if result[0] is not None else 0
# Or with Python 3.8+ walrus operator
if (score := result[0]) is None:
    score = 0
```

### 68. How are PostgreSQL and SQLite compatibility maintained?

**Answer:** Parameter conversion:

```python
def _convert_query_params(query, args):
    # SQLite uses ?, PostgreSQL uses %s
    converted = query.replace('?', '%s')
    return converted, args
```

### 69. What is connection pooling and is it used?

**Answer:** Reusing connections instead of creating new ones. Currently not using connection pooling - each request creates a new connection. Could improve with `psycopg2.pool` or SQLAlchemy.

### 70. How would you migrate the database schema?

**Answer:** Using ALTER TABLE statements in `init_db`:

```python
# Add column if not exists
cursor.execute("""
    DO $$ BEGIN
        ALTER TABLE analysis_results ADD COLUMN IF NOT EXISTS strategy_id INTEGER;
    EXCEPTION
        WHEN duplicate_column THEN NULL;
    END $$;
""")
```

---

## Backend - Data Processing (71-85)

### 71. What is pandas and how is it used?

**Answer:** Data manipulation library. Used for:

- OHLCV data handling
- Indicator calculations
- Time series operations

### 72. What is a DataFrame?

**Answer:** 2D labeled data structure (like a spreadsheet):

```python
df = pd.DataFrame({
    'Date': dates,
    'Close': prices,
    'Volume': volumes
})
```

### 73. How is stock data fetched?

**Answer:** Using yfinance:

```python
import yfinance as yf
df = yf.download('AAPL', period='200d', interval='1d')
```

### 74. What technical indicators are calculated?

**Answer:** 12 indicators across 4 categories:

- **Trend:** MACD, ADX, EMA Crossover, Parabolic SAR
- **Momentum:** RSI, Stochastic, CCI, Williams %R
- **Volatility:** ATR, Bollinger Bands
- **Volume:** OBV, CMF

### 75. How are indicator votes determined?

**Answer:** Each indicator returns -1, 0, or +1:

```python
def _get_vote(self, value):
    if value > 70:  # Overbought
        return -1   # Sell
    if value < 30:  # Oversold
        return 1    # Buy
    return 0        # Neutral
```

### 76. How is the final score calculated?

**Answer:**

```python
def aggregate_votes(indicators, weights):
    total_weighted = 0
    total_weight = 0

    for ind in indicators:
        weight = weights.get(ind['name'], 1.0)
        total_weighted += ind['vote'] * ind['confidence'] * weight
        total_weight += weight

    score = (total_weighted / total_weight + 1) * 50  # Normalize to 0-100
    return score
```

### 77. How are entry/stop/target calculated?

**Answer:**

```python
def calculate_trade_params(df, risk_percent, risk_reward_ratio):
    current_price = df['Close'].iloc[-1]
    atr = calculate_atr(df)

    stop_loss = current_price - (atr * 1.5)  # 1.5 ATR stop
    risk_amount = current_price - stop_loss
    target = current_price + (risk_amount * risk_reward_ratio)

    return {
        'entry': current_price,
        'stop_loss': stop_loss,
        'target': target
    }
```

### 78. What is the AnalysisOrchestrator?

**Answer:** Main pipeline that coordinates analysis:

1. `DataFetcher` - Get OHLCV data
2. `IndicatorEngine` - Calculate indicators
3. `SignalAggregator` - Aggregate votes
4. `TradeCalculator` - Calculate entry/stop/target
5. `ResultFormatter` - Format output

### 79. How do indicators handle missing data?

**Answer:**

```python
# Check for NaN
if np.isnan(value):
    return {"error": "Insufficient data"}

# Forward fill
df.fillna(method='ffill', inplace=True)

# Drop NaN rows
df.dropna(inplace=True)
```

### 80. What is the ta library?

**Answer:** Technical Analysis library with 130+ indicators:

```python
import ta
rsi = ta.momentum.RSIIndicator(df['Close']).rsi()
macd = ta.trend.MACD(df['Close']).macd()
```

### 81. How do rolling calculations work?

**Answer:**

```python
# 20-day moving average
df['SMA_20'] = df['Close'].rolling(window=20).mean()

# 14-day RSI (using EMA internally)
df['RSI'] = ta.momentum.RSIIndicator(df['Close'], window=14).rsi()
```

### 82. What is numpy used for?

**Answer:** Numerical operations:

```python
import numpy as np
mean = np.mean(prices)
std = np.std(prices)
max_val = np.max(prices)
```

### 83. How are numpy types converted for database storage?

**Answer:**

```python
def convert_numpy_types(value):
    if isinstance(value, np.float64):
        return float(value)
    if isinstance(value, np.int64):
        return int(value)
    return value
```

### 84. What is the backtesting engine?

**Answer:** Simulates historical trades:

```python
def backtest(ticker, strategy, start_date, end_date):
    df = fetch_historical_data(ticker, start_date, end_date)

    trades = []
    for date in df.index:
        signal = generate_signal(df.loc[:date], strategy)
        if signal == 'buy':
            trades.append(execute_trade(df, date))

    return calculate_performance(trades)
```

### 85. How is data validation performed?

**Answer:**

```python
def validate_data(df):
    if df is None or df.empty:
        return False, "No data returned"

    if len(df) < 50:
        return False, "Insufficient history"

    if df['Close'].isnull().all():
        return False, "No valid prices"

    return True, "Valid"
```

---

## Backend - Threading & Jobs (86-95)

### 86. Why use threading instead of Celery?

**Answer:** Simpler setup, no Redis dependency:

- Celery + Redis adds infrastructure complexity
- Python threading sufficient for this load
- Easier deployment to cloud platforms

### 87. How are background jobs started?

**Answer:**

```python
thread = threading.Thread(
    target=analyze_stocks_batch,
    args=(job_id, tickers, capital),
    daemon=False  # Survives main thread
)
thread.start()
```

### 88. How is job status tracked?

**Answer:** In `analysis_jobs` table:

```python
# Update progress
execute_db(
    "UPDATE analysis_jobs SET progress = ?, status = ? WHERE job_id = ?",
    (progress, 'processing', job_id)
)
```

### 89. What is a daemon thread?

**Answer:** Thread that exits when main program exits. We use `daemon=False` so analysis continues even if request ends.

### 90. How do you handle thread-safe database connections?

**Answer:** Context manager with new connection per thread:

```python
@contextmanager
def get_db_session():
    conn = psycopg2.connect(DATABASE_URL)
    try:
        yield conn, conn.cursor()
        conn.commit()
    finally:
        conn.close()
```

### 91. How is job cancellation implemented?

**Answer:**

```python
cancelled_jobs = set()

def cancel_job(job_id):
    cancelled_jobs.add(job_id)
    execute_db("UPDATE analysis_jobs SET status = 'cancelled' WHERE job_id = ?", (job_id,))

# In worker
def analyze_batch(job_id, tickers):
    for ticker in tickers:
        if job_id in cancelled_jobs:
            return  # Stop processing
        analyze(ticker)
```

### 92. What happens if a job fails mid-way?

**Answer:** Partial results are kept:

```python
try:
    result = analyze_ticker(ticker)
    save_result(job_id, ticker, result)
except Exception as e:
    save_error(job_id, ticker, str(e))

# Job continues to next ticker
```

### 93. How do you prevent duplicate jobs?

**Answer:**

```python
def check_duplicate_job(tickers):
    existing = query_db(
        "SELECT job_id FROM analysis_jobs WHERE tickers_json = ? AND status = 'processing'",
        (json.dumps(sorted(tickers)),)
    )
    return existing is not None
```

### 94. How is progress percentage calculated?

**Answer:**

```python
def update_progress(job_id, completed, total):
    progress = int((completed / total) * 100)
    execute_db(
        "UPDATE analysis_jobs SET progress = ?, completed = ? WHERE job_id = ?",
        (progress, completed, job_id)
    )
```

### 95. What is the GIL and does it affect this project?

**Answer:** Global Interpreter Lock - only one thread executes Python at a time. Impact:

- CPU-bound tasks: Limited parallelism
- I/O-bound tasks (API calls): Works well

This project's analysis is I/O-bound (yfinance calls), so threading works well.

---

## Architecture & Design Patterns (96-110)

### 96. Explain the overall architecture.

**Answer:**

- **Frontend:** React SPA → REST API → Flask Backend
- **Backend:** Flask + Blueprints → PostgreSQL
- **Processing:** Background threads for analysis

### 97. What is the Template Method pattern? Where is it used?

**Answer:** Define algorithm skeleton, subclasses implement steps:

```python
class IndicatorBase:
    def vote_and_confidence(self, df):
        value = self.calculate(df)        # Abstract
        vote = self._get_vote(value)      # Abstract
        conf = self._get_confidence(value) # Abstract
        return {"value": value, "vote": vote, "confidence": conf}
```

Used in indicators.

### 98. What is the Strategy pattern? Where is it used?

**Answer:** Interchangeable algorithms:

```python
class BalancedStrategy(BaseStrategy):
    def get_weights(self):
        return {"RSI": 1.0, "MACD": 1.0, ...}

class TrendStrategy(BaseStrategy):
    def get_weights(self):
        return {"RSI": 0.5, "MACD": 1.5, ...}
```

User selects strategy, system uses its weights.

### 99. What is the Factory pattern? Where is it used?

**Answer:** Create objects without specifying class:

```python
def get_strategy(strategy_id):
    strategies = {1: Strategy1, 2: Strategy2, ...}
    return strategies.get(strategy_id, Strategy1)()
```

### 100. What is the Repository pattern?

**Answer:** Abstract data access:

```python
# database.py acts as repository
def query_db(query, args=()): ...
def execute_db(query, args=()): ...
```

Routes don't know about PostgreSQL specifics.

### 101. How is separation of concerns achieved?

**Answer:** Clear layer separation:

- **Routes:** Request handling, validation
- **Utils:** Business logic (orchestrator)
- **Database:** Data access
- **Indicators:** Technical calculations
- **Strategies:** Configuration

### 102. What is dependency injection? Is it used?

**Answer:** Providing dependencies instead of creating them. Partially used:

```python
def analyze(fetcher=None, engine=None):
    fetcher = fetcher or DataFetcher()
    engine = engine or IndicatorEngine()
```

### 103. How would you scale this application?

**Answer:**

1. **Horizontal:** Multiple backend instances
2. **Caching:** Redis for API caching
3. **Queue:** Celery for job processing
4. **Database:** Connection pooling, read replicas

### 104. What is the single responsibility principle? Examples?

**Answer:** Each class has one job:

- `DataFetcher` - Only fetches data
- `IndicatorEngine` - Only calculates
- `SignalAggregator` - Only aggregates

### 105. How is error handling standardized?

**Answer:**

```python
class StandardizedErrorResponse:
    @staticmethod
    def format(code, message, status):
        return jsonify({
            "error": code,
            "message": message,
            "timestamp": get_ist_timestamp()
        }), status
```

### 106. What is the Open/Closed principle? Examples?

**Answer:** Open for extension, closed for modification. Adding new indicator:

1. Create new class extending `IndicatorBase`
2. Register in registry
3. No changes to existing code

### 107. How is logging implemented?

**Answer:**

```python
import logging
logger = logging.getLogger('trading_analyzer')
logger.info(f"Analyzing {ticker}")
logger.error(f"Failed: {error}")
logger.exception(f"Unexpected error")  # Includes stack trace
```

### 108. What is the Observer pattern?

**Answer:** Objects notified of state changes. Not currently used but could implement:

- Job status changes → Notify frontend (WebSocket)
- Price alerts → Notify user

### 109. How would you implement WebSocket for real-time updates?

**Answer:**

```python
# Backend with Flask-SocketIO
from flask_socketio import SocketIO
socketio = SocketIO(app)

def update_job_status(job_id, status):
    socketio.emit('job_update', {'job_id': job_id, 'status': status})

# Frontend
const socket = io();
socket.on('job_update', (data) => setJobStatus(data));
```

### 110. What deployment options are used?

**Answer:**

- **Frontend:** Vercel (static hosting)
- **Backend:** Railway (container hosting)
- **Database:** Railway PostgreSQL

---

## Testing & Quality (111-115)

### 111. How would you test the frontend?

**Answer:**

- **Unit:** Jest + React Testing Library
- **Integration:** Test API interactions
- **E2E:** Cypress or Playwright

### 112. How would you test the backend?

**Answer:**

```python
import pytest

@pytest.fixture
def client():
    app = create_app({'TESTING': True})
    with app.test_client() as client:
        yield client

def test_analyze_endpoint(client):
    response = client.post('/api/analysis/analyze', json={
        'tickers': ['AAPL']
    })
    assert response.status_code == 201
    assert 'job_id' in response.json
```

### 113. What is mocking and when would you use it?

**Answer:** Replace real objects with test doubles:

```python
def test_analysis(mocker):
    # Mock yfinance to avoid real API calls
    mocker.patch('yfinance.download', return_value=mock_df)
    result = analyze_ticker('AAPL')
    assert result['score'] > 0
```

### 114. How would you implement code coverage?

**Answer:**

```bash
# Python
pytest --cov=backend --cov-report=html

# JavaScript
npm test -- --coverage
```

### 115. What is CI/CD and how would you set it up?

**Answer:** Continuous Integration/Deployment. GitHub Actions:

```yaml
name: CI
on: push
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - run: pip install -r requirements.txt
      - run: pytest
  deploy:
    needs: test
    if: github.ref == 'refs/heads/main'
    steps:
      - run: railway up
```

---

## Bonus Questions (116-120)

### 116. How do you handle environment variables?

**Answer:**

- **Frontend:** `.env` files, `process.env.REACT_APP_*`
- **Backend:** `.env` files, `python-dotenv`, `os.getenv()`

### 117. What security measures are implemented?

**Answer:**

- SQL parameterization (no injection)
- CORS configuration
- API key headers (optional)
- Input validation (Pydantic)
- Rate limiting (Flask-Limiter)

### 118. How would you improve performance?

**Answer:**

- Add Redis caching for API responses
- Connection pooling for database
- Lazy load frontend components
- CDN for static assets
- Database query optimization

### 119. What is rate limiting and how is it implemented?

**Answer:** Prevent API abuse:

```python
from flask_limiter import Limiter

limiter = Limiter(app)

@bp.route('/analyze')
@limiter.limit("10 per minute")
def analyze():
    pass
```

### 120. How would you add user authentication?

**Answer:**

1. Add users table with password hashes
2. Implement JWT token generation
3. Add login/register endpoints
4. Protect routes with `@login_required`
5. Associate watchlists with user_id
