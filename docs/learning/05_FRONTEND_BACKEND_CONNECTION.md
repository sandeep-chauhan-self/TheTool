# Frontend-Backend Connection and Data Processing

## Overview

This document explains how the React frontend communicates with the Flask backend, including the complete request/response cycle, data transformation, and error handling.

---

## Connection Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        FRONTEND-BACKEND CONNECTION                          │
└─────────────────────────────────────────────────────────────────────────────┘

   FRONTEND (React)                           BACKEND (Flask)
   Port: 3000 (dev)                           Port: 5000
   ┌─────────────────┐                        ┌─────────────────┐
   │   User Action   │                        │    Flask App    │
   │   (Click/Input) │                        │    (app.py)     │
   └────────┬────────┘                        └────────┲────────┘
            │                                          │
            ▼                                          │
   ┌─────────────────┐      HTTP/REST           ┌──────┴────────┐
   │   API Layer     │ ─────────────────────→   │   Blueprint   │
   │   (api.js)      │ ←─────────────────────   │    Router     │
   └────────┬────────┘      JSON                └───────────────┘
            │
            ▼
   ┌─────────────────┐
   │ State Update    │
   │ (Context/Hook)  │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │  UI Re-render   │
   └─────────────────┘
```

---

## Environment-Based API URL Selection

The frontend automatically detects which backend to use:

### api.js Detection Logic

```javascript
const getApiBaseUrl = () => {
  // 1. Explicit override (highest priority)
  if (process.env.REACT_APP_API_BASE_URL) {
    return process.env.REACT_APP_API_BASE_URL;
  }

  // 2. Auto-detect based on hostname
  const hostname = window.location.hostname;

  if (hostname === "localhost" || hostname === "127.0.0.1") {
    return "http://localhost:5000"; // Local development
  }

  if (hostname.includes("the-tool-git-development")) {
    return "https://thetool-development.up.railway.app"; // Dev/Staging
  }

  if (hostname.includes("the-tool-theta")) {
    return "https://thetool-production.up.railway.app"; // Production
  }

  return "http://localhost:5000"; // Default fallback
};
```

---

## HTTP Communication

### Axios Instance Setup

```javascript
// frontend/src/api/api.js
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
    "X-API-Key": process.env.REACT_APP_API_KEY,
  },
});
```

### Request Types Used

| HTTP Method | Purpose                 | Example               |
| ----------- | ----------------------- | --------------------- |
| GET         | Retrieve data           | Fetch watchlist       |
| POST        | Create/start operations | Start analysis job    |
| DELETE      | Remove resources        | Remove from watchlist |

---

## CORS (Cross-Origin Resource Sharing)

### The Problem

- Frontend runs on `localhost:3000`
- Backend runs on `localhost:5000`
- Browsers block cross-origin requests by default

### The Solution (Backend)

```python
# backend/app.py
from flask_cors import CORS

def create_app():
    app = Flask(__name__)

    # Enable CORS for all API routes
    CORS(app, resources={
        r"/api/*": {
            "origins": [
                "http://localhost:3000",
                "https://the-tool-theta.vercel.app",
                "https://the-tool-git-development*.vercel.app"
            ],
            "methods": ["GET", "POST", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "X-API-Key"]
        }
    })

    # Also handle preflight requests
    @app.before_request
    def handle_preflight():
        if request.method == 'OPTIONS':
            response = app.make_default_options_response()
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type, X-API-Key')
            return response
```

---

## API Function Patterns

### 1. Simple GET Request

```javascript
// Frontend: api.js
export const getWatchlist = async (collectionId = null) => {
  let url = "/api/watchlist";
  if (collectionId !== null) {
    url += `?collection_id=${collectionId}`;
  }
  const response = await api.get(url);
  return response.data.watchlist || [];
};

// Usage in component
const [watchlist, setWatchlist] = useState([]);

useEffect(() => {
  const fetchData = async () => {
    const data = await getWatchlist();
    setWatchlist(data);
  };
  fetchData();
}, []);
```

**Backend Handler:**

```python
# backend/routes/watchlist.py
@bp.route("/", methods=["GET"])
def get_watchlist():
    collection_id = request.args.get('collection_id')

    results = query_db(
        "SELECT * FROM watchlist WHERE collection_id = ?",
        (collection_id,)
    )

    return jsonify({
        "count": len(results),
        "watchlist": [dict(r) for r in results]
    }), 200
```

---

### 2. POST Request with Body

```javascript
// Frontend: api.js
export const analyzeStocks = async (tickers, config = {}) => {
  const payload = {
    tickers,
    capital: config.capital || 100000,
    strategy_id: config.strategyId || 1,
    risk_percent: config.riskPercent,
    use_demo_data: config.useDemoData,
  };

  const response = await api.post("/api/analysis/analyze", payload);
  return response.data; // { job_id: "...", status: "queued" }
};

// Usage in component
const handleAnalyze = async () => {
  setLoading(true);
  try {
    const result = await analyzeStocks(["AAPL", "MSFT"], { capital: 100000 });
    setJobId(result.job_id);
    startPolling(result.job_id);
  } catch (error) {
    setError(error.message);
  } finally {
    setLoading(false);
  }
};
```

**Backend Handler:**

```python
# backend/routes/analysis.py
@bp.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json() or {}

    # Validate request
    tickers = data.get("tickers", [])
    capital = data.get("capital", 100000)
    strategy_id = data.get("strategy_id", 1)

    if not tickers:
        return jsonify({"error": "No tickers provided"}), 400

    # Create job
    job_id = str(uuid.uuid4())

    # Start background processing
    start_analysis_job(job_id, tickers, capital, strategy_id)

    return jsonify({
        "job_id": job_id,
        "status": "queued",
        "tickers": tickers
    }), 201
```

---

### 3. Polling Pattern (Real-time Progress)

```javascript
// Frontend: Dashboard.js
const pollJobStatus = useCallback(async (jobId) => {
  const pollInterval = setInterval(async () => {
    try {
      const status = await getJobStatus(jobId);

      setProgress(status.progress);

      if (status.status === "completed") {
        clearInterval(pollInterval);
        setResults(status.results);
        setLoading(false);
      } else if (status.status === "failed") {
        clearInterval(pollInterval);
        setError(status.error);
        setLoading(false);
      }
    } catch (error) {
      clearInterval(pollInterval);
      setError(error.message);
      setLoading(false);
    }
  }, 2000); // Poll every 2 seconds

  // Cleanup on unmount
  return () => clearInterval(pollInterval);
}, []);
```

**Backend Status Handler:**

```python
@bp.route("/status/<job_id>", methods=["GET"])
def get_job_status(job_id):
    status = query_db(
        """SELECT job_id, status, progress, total, completed, errors
           FROM analysis_jobs WHERE job_id = ?""",
        (job_id,),
        one=True
    )

    if not status:
        return jsonify({"error": "Job not found"}), 404

    response = {
        "job_id": status[0],
        "status": status[1],
        "progress": status[2],
        "total": status[3],
        "completed": status[4]
    }

    # Include results if completed
    if status[1] == "completed":
        results = query_db(
            "SELECT * FROM analysis_results WHERE job_id = ?",
            (job_id,)
        )
        response["results"] = [dict(r) for r in results]

    return jsonify(response), 200
```

---

## Data Transformation

### Frontend to Backend

```javascript
// Frontend sends (camelCase)
{
  tickers: ["AAPL", "MSFT"],
  capital: 100000,
  strategyId: 2,
  riskPercent: 2.0,
  useDemoData: false
}

// API layer transforms
const payload = {
  tickers,
  capital: config.capital,
  strategy_id: config.strategyId,      // camelCase → snake_case
  risk_percent: config.riskPercent,
  use_demo_data: config.useDemoData
};
```

### Backend to Frontend

```python
# Backend returns (snake_case from DB)
{
    "job_id": "abc-123",
    "status": "completed",
    "results": [
        {
            "ticker": "AAPL",
            "score": 72.5,
            "verdict": "Strong Buy",
            "stop_loss": 145.50,
            "risk_reward_ratio": 2.5
        }
    ]
}

# Frontend receives (used as-is, or transformed)
const result = response.data;
console.log(result.job_id);  // Direct access
console.log(result.results[0].stop_loss);  // snake_case preserved
```

---

## Error Handling

### Frontend Error Handling

```javascript
// api.js - Centralized error handling
export const analyzeStocks = async (tickers, config) => {
  try {
    const response = await api.post("/api/analysis/analyze", payload);
    return response.data;
  } catch (error) {
    // Axios wraps errors
    if (error.response) {
      // Server responded with error status
      throw new Error(error.response.data.message || "Analysis failed");
    } else if (error.request) {
      // Request made but no response
      throw new Error("Server unreachable");
    } else {
      // Request setup error
      throw new Error("Request failed");
    }
  }
};

// Component usage
try {
  const result = await analyzeStocks(tickers);
} catch (error) {
  setError(error.message);
  toast.error(error.message);
}
```

### Backend Error Response Format

```python
# backend/utils/api_utils.py
class StandardizedErrorResponse:
    @staticmethod
    def format(error_code, message, status_code, details=None):
        return jsonify({
            "error": error_code,
            "message": message,
            "details": details,
            "timestamp": get_ist_timestamp()
        }), status_code

# Usage in routes
return StandardizedErrorResponse.format(
    "INVALID_TICKER",
    "Ticker cannot be empty",
    400
)

# Response:
# {
#   "error": "INVALID_TICKER",
#   "message": "Ticker cannot be empty",
#   "details": null,
#   "timestamp": "2024-01-15T10:30:00+05:30"
# }
```

---

## Request Validation

### Backend Validation (Pydantic)

```python
# backend/utils/api_utils.py
class RequestValidator:
    class AnalyzeRequest:
        tickers: List[str]  # Required
        capital: float = 100000
        strategy_id: int = 1

        @validator('tickers')
        def validate_tickers(cls, v):
            if not v:
                raise ValueError('At least one ticker required')
            return [t.upper().strip() for t in v]

# Usage
@bp.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    validated, error = validate_request(data, RequestValidator.AnalyzeRequest)

    if error:
        return error  # Returns standardized error response

    # Proceed with validated data
    tickers = validated["tickers"]
```

---

## File Downloads

### Excel Report Download

```javascript
// Frontend: api.js
export const downloadReport = async (ticker) => {
  const response = await api.get(`/api/analysis/report/${ticker}/download`, {
    responseType: "blob", // Important: receive as binary
  });

  // Create download link
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement("a");
  link.href = url;
  link.setAttribute("download", `${ticker}_analysis.xlsx`);
  document.body.appendChild(link);
  link.click();
  link.remove();

  // Cleanup
  window.URL.revokeObjectURL(url);
};
```

**Backend Handler:**

```python
from flask import send_file

@bp.route("/report/<ticker>/download", methods=["GET"])
def download_report(ticker):
    # Generate Excel file
    excel_file = export_to_excel(analysis_data)

    return send_file(
        excel_file,
        as_attachment=True,
        download_name=f"{ticker}_analysis.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
```

---

## Complete Request/Response Flow Example

### Analyzing Stocks (Full Flow)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         COMPLETE ANALYSIS FLOW                              │
└─────────────────────────────────────────────────────────────────────────────┘

1. USER CLICKS "ANALYZE"
   Dashboard.js
   │
   └──→ handleAnalyze(['AAPL', 'MSFT'])

2. FRONTEND API CALL
   api.js
   │
   └──→ analyzeStocks(['AAPL', 'MSFT'], { capital: 100000 })
        │
        └──→ POST http://localhost:5000/api/analysis/analyze
             Body: { "tickers": ["AAPL", "MSFT"], "capital": 100000 }

3. BACKEND RECEIVES REQUEST
   routes/analysis.py
   │
   ├──→ Validate request (Pydantic)
   ├──→ Create job_id = "abc-123"
   ├──→ Insert into analysis_jobs table
   └──→ Start background thread
        │
        └──→ Response: { "job_id": "abc-123", "status": "queued" }

4. FRONTEND STARTS POLLING
   Dashboard.js
   │
   └──→ pollJobStatus("abc-123")
        │
        └──→ setInterval every 2000ms
             │
             └──→ GET /api/analysis/status/abc-123

5. BACKGROUND PROCESSING (Backend Thread)
   thread_tasks.py
   │
   ├──→ analyze_stocks_batch(job_id, tickers)
   │    │
   │    ├──→ For each ticker:
   │    │    ├──→ Fetch OHLCV from Yahoo Finance
   │    │    ├──→ Calculate 12 indicators
   │    │    ├──→ Aggregate score
   │    │    ├──→ Calculate entry/stop/target
   │    │    └──→ Save to analysis_results table
   │    │
   │    └──→ Update analysis_jobs (progress += 1)
   │
   └──→ Mark job as "completed"

6. POLLING DETECTS COMPLETION
   Dashboard.js
   │
   └──→ Status response: { "status": "completed", "results": [...] }
        │
        ├──→ clearInterval(polling)
        ├──→ setResults(results)
        └──→ setLoading(false)

7. UI RE-RENDERS WITH RESULTS
   Dashboard.js → StockRow components
   │
   └──→ Display score, verdict, entry, stop, target for each stock
```

---

## Network Debugging

### Browser DevTools

```
1. Open DevTools (F12)
2. Go to "Network" tab
3. Filter by "XHR" or "Fetch"
4. Click on a request to see:
   - Headers
   - Request payload
   - Response data
   - Timing
```

### Common Issues

| Issue              | Cause                       | Solution                 |
| ------------------ | --------------------------- | ------------------------ |
| CORS error         | Backend not allowing origin | Check CORS configuration |
| 401 Unauthorized   | Missing/invalid API key     | Check X-API-Key header   |
| 404 Not Found      | Wrong endpoint URL          | Verify API route         |
| 500 Internal Error | Backend exception           | Check backend logs       |
| Network Error      | Backend not running         | Start Flask server       |

### Console Logging

```javascript
// api.js logs environment detection
console.log(
  `[API] Frontend hostname: localhost, Using backend: http://localhost:5000`,
);

// Component logging
console.log("[Dashboard] Fetching watchlist...");
console.log("[Dashboard] Analysis started, job_id:", jobId);
```
