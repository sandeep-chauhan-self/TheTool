# Complete Lifecycle: Frontend → Backend → Database (Data Write)

## Overview

This document traces the complete journey of a data point from user interaction on the frontend, through processing in the backend, and finally being stored in the PostgreSQL database.

---

## Scenario: User Analyzes a Stock

**Action:** User clicks "Analyze" for stock ticker "RELIANCE.NS" with ₹100,000 capital.

---

## Phase 1: Frontend - User Interaction

### Step 1.1: User Action in Dashboard

```javascript
// frontend/src/pages/Dashboard.js (lines 384-410)

const handleAnalyzeWithConfig = async (config) => {
  // User clicks "Analyze" button after selecting stocks
  const tickersToAnalyze = Array.from(selectedStocks); // ["RELIANCE.NS"]

  setAnalyzing(true);
  setProgress(0);

  try {
    // Call API layer
    const result = await analyzeStocks(tickersToAnalyze, config);

    // Store job ID for polling
    setJobId(result.job_id);

    // Start polling for status
    pollJobStatus(result.job_id);
  } catch (error) {
    setError(error.message);
    setAnalyzing(false);
  }
};
```

### Step 1.2: API Layer Transforms Request

```javascript
// frontend/src/api/api.js (lines 74-96)

export const analyzeStocks = async (tickers, config = {}) => {
  // Transform frontend config to backend format
  const payload = {
    tickers, // ["RELIANCE.NS"]
    capital: config.capital || 100000, // 100000
    strategy_id: config.strategyId || 1, // 1 (Balanced)
    risk_percent: config.riskPercent, // 2.0
    position_size_limit: config.positionSizeLimit, // 20
    risk_reward_ratio: config.riskRewardRatio, // 1.5
    data_period: config.dataPeriod, // "200d"
    use_demo_data: config.useDemoData, // false
    category_weights: config.categoryWeights,
    enabled_indicators: config.enabledIndicators,
  };

  // Send HTTP POST request
  const response = await api.post("/api/analysis/analyze", payload);
  return response.data;
};
```

**HTTP Request Sent:**

```http
POST http://localhost:5000/api/analysis/analyze
Content-Type: application/json
X-API-Key: [API_KEY]

{
  "tickers": ["RELIANCE.NS"],
  "capital": 100000,
  "strategy_id": 1,
  "risk_percent": 2.0,
  "use_demo_data": false
}
```

---

## Phase 2: Backend - Request Handling

### Step 2.1: Flask Route Handler

```python
# backend/routes/analysis.py (lines 75-218)

@bp.route("/analyze", methods=["POST"])
def analyze():
    """
    Analyze one or more tickers with given capital allocation.
    """
    try:
        # Extract JSON from request body
        data = request.get_json() or {}

        # Log incoming request
        logger.info(f"[ANALYZE] Incoming request - raw data: {data}")

        # Validate request using Pydantic
        validated_data, error_response = validate_request(
            data,
            RequestValidator.AnalyzeRequest
        )
        if error_response:
            return error_response  # Returns 400 Bad Request

        # Extract validated fields
        tickers = validated_data["tickers"]    # ["RELIANCE.NS"]
        capital = validated_data["capital"]    # 100000
        strategy_id = data.get("strategy_id", 1)  # 1

        # Build analysis config
        analysis_config = {
            "capital": capital,
            "risk_percent": data.get("risk_percent"),
            "position_size_limit": data.get("position_size_limit"),
            "risk_reward_ratio": data.get("risk_reward_ratio"),
            "data_period": data.get("data_period"),
            "use_demo_data": data.get("use_demo_data", False),
            "category_weights": data.get("category_weights"),
            "enabled_indicators": data.get("enabled_indicators")
        }

        # Generate unique job ID
        job_id = str(uuid.uuid4())  # "a1b2c3d4-e5f6-7890-abcd-ef1234567890"

        # Create job in database (Step 2.2)
        created = JobStateTransactions.create_job_atomic(
            job_id=job_id,
            status="queued",
            total=len(tickers),
            description=f"Analyze {len(tickers)} ticker(s) with capital {capital}",
            tickers=tickers,
            strategy_id=strategy_id
        )

        # Start background thread (Step 2.3)
        start_analysis_job(job_id, tickers, None, capital, False, analysis_config, strategy_id)

        # Return immediate response
        return jsonify({
            "job_id": job_id,
            "status": "queued",
            "tickers": tickers,
            "capital": capital,
            "strategy_id": strategy_id
        }), 201
```

### Step 2.2: Create Job Record in Database

```python
# backend/utils/db_utils.py - JobStateTransactions.create_job_atomic()

def create_job_atomic(job_id, status, total, description, tickers, strategy_id):
    """Create a new analysis job atomically"""

    with get_db_session() as (conn, cursor):
        # Normalize tickers for storage
        tickers_json = json.dumps(sorted([t.upper().strip() for t in tickers]))

        # INSERT into analysis_jobs table
        query = """
            INSERT INTO analysis_jobs
            (job_id, status, progress, total, completed, tickers_json, strategy_id, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            job_id,         # "a1b2c3d4-..."
            status,         # "queued"
            0,              # progress = 0
            total,          # 1 (number of tickers)
            0,              # completed = 0
            tickers_json,   # '["RELIANCE.NS"]'
            strategy_id,    # 1
            get_ist_timestamp()
        ))

        conn.commit()
    return True
```

**Database INSERT #1:**

```sql
INSERT INTO analysis_jobs
(job_id, status, progress, total, completed, tickers_json, strategy_id, created_at)
VALUES (
    'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
    'queued',
    0,
    1,
    0,
    '["RELIANCE.NS"]',
    1,
    '2024-01-15 10:30:00+05:30'
);
```

---

## Phase 3: Backend - Background Analysis

### Step 3.1: Start Background Thread

```python
# backend/infrastructure/thread_tasks.py (lines 247-269)

def start_analysis_job(job_id, tickers, indicators, capital, use_demo, analysis_config, strategy_id):
    """Start a new analysis job in background thread"""

    # Create thread (non-daemon for cloud deployments)
    thread = threading.Thread(
        target=analyze_stocks_batch,
        args=(job_id, tickers, capital, indicators, use_demo),
        daemon=False
    )

    # Track thread
    job_threads[job_id] = thread
    active_jobs[job_id] = {
        "started": datetime.now(),
        "tickers": tickers
    }

    # Start thread
    thread.start()

    logger.info(f"Started analysis thread for job {job_id}")
    return True
```

### Step 3.2: Batch Analysis Function

```python
# backend/infrastructure/thread_tasks.py (lines 79-244)

def analyze_stocks_batch(job_id, tickers, capital, indicators, use_demo_data):
    """Background task to analyze multiple stocks"""

    try:
        # Update job status to "processing"
        with get_db_session() as (conn, cursor):
            cursor.execute(
                "UPDATE analysis_jobs SET status = %s, started_at = %s WHERE job_id = %s",
                ("processing", datetime.now(), job_id)
            )
            conn.commit()

        # Process each ticker
        for i, ticker in enumerate(tickers):
            try:
                # === ANALYSIS HAPPENS HERE (Step 3.3) ===
                result = analyze_ticker(
                    ticker,
                    indicator_list=indicators,
                    capital=capital,
                    use_demo_data=use_demo_data
                )

                # === SAVE TO DATABASE (Step 3.4) ===
                save_analysis_result(job_id, ticker, result)

                # Update progress
                update_job_progress(job_id, i + 1, len(tickers))

            except Exception as e:
                logger.exception(f"Error analyzing {ticker}")
                save_error_result(job_id, ticker, str(e))

        # Mark job complete
        with get_db_session() as (conn, cursor):
            cursor.execute(
                "UPDATE analysis_jobs SET status = %s, completed_at = %s WHERE job_id = %s",
                ("completed", datetime.now(), job_id)
            )
            conn.commit()

    except Exception as e:
        logger.exception(f"Job {job_id} failed")
        mark_job_failed(job_id, str(e))
```

### Step 3.3: Analyze Single Ticker

```python
# backend/utils/analysis_orchestrator.py (AnalysisOrchestrator.analyze)

class AnalysisOrchestrator:
    def analyze(self, ticker, indicator_list, capital, use_demo_data, analysis_config, strategy_id):
        """Main analysis pipeline"""

        # Step 1: Fetch OHLCV data from Yahoo Finance
        data_fetcher = DataFetcher()
        df, source, is_valid, message, warnings = data_fetcher.fetch_and_validate(
            ticker,                    # "RELIANCE.NS"
            use_demo_data=use_demo_data,  # False
            period='200d'              # Last 200 trading days
        )

        if not is_valid:
            return {"error": message}

        # Step 2: Calculate all 12 indicators
        indicator_engine = IndicatorEngine()
        indicator_results = indicator_engine.calculate_indicators(
            df,                        # DataFrame with OHLCV
            ticker,
            indicator_list             # None = all indicators
        )
        # indicator_results = [
        #   {"name": "RSI", "value": 55.2, "vote": 0, "confidence": 0.6, "category": "momentum"},
        #   {"name": "MACD", "value": {"macd": 12.5, "signal": 10.3}, "vote": 1, "confidence": 0.8, ...},
        #   ... (12 total)
        # ]

        # Step 3: Aggregate votes with strategy weighting
        signal_aggregator = SignalAggregator()
        score, verdict, category_breakdown = signal_aggregator.aggregate_votes(
            indicator_results,
            category_weights=None,     # Use strategy defaults
            indicator_weights=None     # Use strategy defaults
        )
        # score = 0.72 (72% bullish)
        # verdict = "Strong Buy"

        # Step 4: Calculate trade parameters
        trade_calculator = TradeCalculator()
        trade_params = trade_calculator.calculate_trade_parameters(
            df,
            score,
            verdict,
            capital                    # 100000
        )
        # trade_params = {
        #   "entry": 2450.50,
        #   "stop_loss": 2400.25,
        #   "target": 2550.75,
        #   "position_size": 20,       # Number of shares
        #   "risk_amount": 1005.00,    # Risk in rupees
        #   "reward_amount": 2005.00,
        #   "risk_reward_ratio": 2.0
        # }

        # Step 5: Format result
        result_formatter = ResultFormatter()
        result = result_formatter.format(
            ticker=ticker,
            score=score,
            verdict=verdict,
            indicators=indicator_results,
            trade_params=trade_params,
            data_source=source,
            strategy_id=strategy_id
        )

        return result
```

**Result Object Structure:**

```python
{
    "ticker": "RELIANCE.NS",
    "symbol": "RELIANCE",
    "score": 72.5,
    "verdict": "Strong Buy",
    "entry": 2450.50,
    "stop_loss": 2400.25,
    "target": 2550.75,
    "position_size": 20,
    "risk_reward_ratio": 2.0,
    "indicators": [
        {"name": "RSI", "value": 55.2, "vote": 0, "confidence": 0.6, "category": "momentum"},
        {"name": "MACD", "value": 12.5, "vote": 1, "confidence": 0.8, "category": "trend"},
        # ... 10 more indicators
    ],
    "data_source": "yahoo_finance",
    "is_demo_data": False,
    "strategy_id": 1,
    "analysis_config": {...}
}
```

---

## Phase 4: Database - Storing Results

### Step 4.1: Save Analysis Result

```python
# backend/infrastructure/thread_tasks.py - save_analysis_result()

def save_analysis_result(job_id, ticker, result):
    """Save analysis result to database"""

    with get_db_session() as (conn, cursor):
        # Convert numpy types to Python native types
        score = convert_numpy_types(result.get("score"))
        entry = convert_numpy_types(result.get("entry"))
        stop_loss = convert_numpy_types(result.get("stop_loss"))
        target = convert_numpy_types(result.get("target"))
        position_size = convert_numpy_types(result.get("position_size", 0))
        risk_reward = convert_numpy_types(result.get("risk_reward_ratio", 0))

        # Serialize indicators to JSON
        indicators_json = json.dumps(result.get("indicators", []), cls=NumpyEncoder)
        config_json = json.dumps(result.get("analysis_config", {}), cls=NumpyEncoder)

        # INSERT into analysis_results
        query = """
            INSERT INTO analysis_results (
                ticker, symbol, score, verdict, entry, stop_loss, target,
                position_size, risk_reward_ratio, raw_data, analysis_config,
                data_source, is_demo_data, status, strategy_id, job_id,
                created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s
            )
        """

        cursor.execute(query, (
            ticker,                           # "RELIANCE.NS"
            result.get("symbol", "RELIANCE"), # "RELIANCE"
            score,                            # 72.5
            result.get("verdict"),            # "Strong Buy"
            entry,                            # 2450.50
            stop_loss,                        # 2400.25
            target,                           # 2550.75
            position_size,                    # 20
            risk_reward,                      # 2.0
            indicators_json,                  # '[{"name":"RSI",...},...]'
            config_json,                      # '{"capital":100000,...}'
            result.get("data_source"),        # "yahoo_finance"
            result.get("is_demo_data", False), # False
            "completed",                      # status
            result.get("strategy_id", 1),     # 1
            job_id,                           # "a1b2c3d4-..."
            get_ist_timestamp(),              # "2024-01-15T10:30:05+05:30"
            get_ist_timestamp()               # same as created_at
        ))

        conn.commit()

        logger.info(f"Saved analysis for {ticker}: score={score}, verdict={result.get('verdict')}")
```

**Database INSERT #2:**

```sql
INSERT INTO analysis_results (
    ticker, symbol, score, verdict, entry, stop_loss, target,
    position_size, risk_reward_ratio, raw_data, analysis_config,
    data_source, is_demo_data, status, strategy_id, job_id,
    created_at, updated_at
) VALUES (
    'RELIANCE.NS',
    'RELIANCE',
    72.5,
    'Strong Buy',
    2450.50,
    2400.25,
    2550.75,
    20,
    2.0,
    '[{"name":"RSI","value":55.2,"vote":0,"confidence":0.6,"category":"momentum"},...]',
    '{"capital":100000,"risk_percent":2.0}',
    'yahoo_finance',
    false,
    'completed',
    1,
    'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
    '2024-01-15 10:30:05+05:30',
    '2024-01-15 10:30:05+05:30'
);
```

### Step 4.2: Update Job Progress

```python
# backend/infrastructure/thread_tasks.py

def update_job_progress(job_id, completed, total):
    """Update job progress in database"""

    progress = int((completed / total) * 100)

    with get_db_session() as (conn, cursor):
        query = """
            UPDATE analysis_jobs
            SET completed = %s, progress = %s, updated_at = %s
            WHERE job_id = %s
        """
        cursor.execute(query, (completed, progress, datetime.now(), job_id))
        conn.commit()
```

**Database UPDATE:**

```sql
UPDATE analysis_jobs
SET completed = 1, progress = 100, updated_at = '2024-01-15 10:30:05+05:30'
WHERE job_id = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890';
```

---

## Phase 5: Backend - Response to Frontend

### Step 5.1: Status Polling Response

```python
# backend/routes/analysis.py (lines 221-260)

@bp.route("/status/<job_id>", methods=["GET"])
def get_analysis_job_status(job_id):
    """Get status of a specific analysis job"""

    status = query_db("""
        SELECT job_id, status, progress, total, completed
        FROM analysis_jobs
        WHERE job_id = ?
    """, (job_id,), one=True)

    if not status:
        return jsonify({"error": "Job not found"}), 404

    response = {
        "job_id": status[0],
        "status": status[1],      # "completed"
        "progress": status[2],    # 100
        "total": status[3],       # 1
        "completed": status[4]    # 1
    }

    # If completed, include results
    if status[1] == "completed":
        results = query_db("""
            SELECT ticker, symbol, verdict, score, entry, stop_loss, target
            FROM analysis_results
            WHERE job_id = ?
        """, (job_id,))

        response["results"] = [
            {
                "ticker": r[0],
                "symbol": r[1],
                "verdict": r[2],
                "score": r[3],
                "entry": r[4],
                "stop_loss": r[5],
                "target": r[6]
            }
            for r in results
        ]

    return jsonify(response), 200
```

**HTTP Response:**

```json
{
  "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "completed",
  "progress": 100,
  "total": 1,
  "completed": 1,
  "results": [
    {
      "ticker": "RELIANCE.NS",
      "symbol": "RELIANCE",
      "verdict": "Strong Buy",
      "score": 72.5,
      "entry": 2450.5,
      "stop_loss": 2400.25,
      "target": 2550.75
    }
  ]
}
```

---

## Complete Data Flow Diagram

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                         DATA WRITE LIFECYCLE                                   │
└────────────────────────────────────────────────────────────────────────────────┘

FRONTEND                    BACKEND                         DATABASE
────────                    ───────                         ────────

1. User clicks
   "Analyze"
      │
      ▼
2. analyzeStocks()
   POST /api/analysis/analyze
   ─────────────────────────→
                            3. analyze() route
                               │
                               ├─→ Validate request
                               ├─→ Generate job_id
                               │
                               └─→ INSERT analysis_jobs ────→ analysis_jobs
                                   (status: "queued")          ┌──────────────┐
                                   │                           │ job_id       │
                                   │                           │ status: queued│
                                   │                           │ progress: 0  │
                                   │                           └──────────────┘
                               │
                               ├─→ Start thread
                               │   (analyze_stocks_batch)
                               │
   4. Response ←───────────────┘
   { job_id, status: "queued" }

5. Start polling ────────────────→
   GET /status/{job_id}
                            6. Background thread running
                               │
                               ├─→ UPDATE status: "processing"
                               │
                               ├─→ fetch_and_validate(ticker)
                               │   (Yahoo Finance API)
                               │
                               ├─→ calculate_indicators()
                               │   (12 technical indicators)
                               │
                               ├─→ aggregate_votes()
                               │   (score: 72.5, verdict: "Strong Buy")
                               │
                               ├─→ calculate_trade_parameters()
                               │   (entry, stop, target, position)
                               │
                               └─→ INSERT analysis_results ──→ analysis_results
                                                               ┌──────────────┐
                                                               │ ticker       │
                                                               │ score: 72.5  │
                                                               │ verdict      │
                                                               │ entry: 2450  │
                                                               │ raw_data:JSON│
                                                               └──────────────┘
                               │
                               └─→ UPDATE analysis_jobs ─────→ analysis_jobs
                                   (status: "completed",       ┌──────────────┐
                                    progress: 100)             │ status:      │
                                                               │  completed   │
                                                               │ progress:100 │
                                                               └──────────────┘

7. Poll response ←───────────────
   { status: "completed",
     results: [...] }

8. UI updates
   - Show results
   - Clear loading
```

---

## Key Code Files Reference

| File                                     | Purpose                   |
| ---------------------------------------- | ------------------------- |
| `frontend/src/pages/Dashboard.js`        | User interaction handlers |
| `frontend/src/api/api.js`                | HTTP request functions    |
| `backend/routes/analysis.py`             | API endpoint handlers     |
| `backend/infrastructure/thread_tasks.py` | Background job processing |
| `backend/utils/analysis_orchestrator.py` | Analysis pipeline         |
| `backend/database.py`                    | Database operations       |
