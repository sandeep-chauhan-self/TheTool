from flask import Flask, jsonify, request
from flask_cors import CORS
from db import init_db_if_needed, query_db, execute_db, close_db
from pathlib import Path
import json
import uuid
from infrastructure.thread_tasks import start_analysis_job, cancel_job
from models.job_state import get_job_state_manager

app = Flask(__name__)

# ---------- GLOBAL CORS ----------
CORS(
    app,
    resources={r"/*": {"origins": ["https://the-tool-theta.vercel.app"]}},
    supports_credentials=False,
    allow_headers=["Content-Type", "X-API-Key", "Authorization"],
    expose_headers=["Content-Type", "X-API-Key"],
)

# Ensure DB connection cleanup
app.teardown_appcontext(close_db)

# ---------- DB INIT (Gunicorn-safe) ----------
@app.before_request
def ensure_db():
    init_db_if_needed()


# ---------- AUTH ----------
@app.before_request
def require_api_key():
    if request.path in ["/health", "/"]:
        return
    if request.method == "OPTIONS":
        return
    # Skip authentication for testing
    if app.config.get('TESTING'):
        return

    api_key = request.headers.get("X-API-Key")
    if not api_key:
        return jsonify({
            "error": "Unauthorized",
            "message": "Missing X-API-Key"
        }), 401


# ---------- ROUTES ----------
@app.route("/")
def index():
    return {"status": "ok", "message": "Backend running"}

@app.route("/health")
def health():
    return {"status": "ok"}


@app.route("/watchlist", methods=["GET"])
def get_watchlist():
    rows = query_db("SELECT id, symbol, name FROM watchlist")
    if rows:
        return jsonify([
            {"id": r["id"], "symbol": r["symbol"], "name": r["name"]}
            for r in rows
        ])
    return jsonify([])

@app.route("/watchlist", methods=["POST"])
def add_watchlist():
    data = request.get_json()
    symbol = data.get("symbol")
    name = data.get("name", "")

    if not symbol:
        return {"error": "Symbol required"}, 400

    existing = query_db(
        "SELECT id FROM watchlist WHERE symbol = ?",
        (symbol,), one=True
    )

    if existing:
        return {"error": "Symbol exists", "already_exists": True}, 409

    execute_db("INSERT INTO watchlist (symbol, name) VALUES (?, ?)", (symbol, name))
    return {"message": "Added", "symbol": symbol}, 201


@app.route("/watchlist", methods=["DELETE"])
def delete_watchlist():
    data = request.get_json()
    symbol = data.get("symbol")
    execute_db("DELETE FROM watchlist WHERE symbol = ?", (symbol,))
    return {"message": "Removed"}


@app.route('/nse-stocks', methods=['GET'])
def get_nse_stocks():
    try:
        from pathlib import Path
        import json

        backend_root = Path(__file__).resolve().parent / "data"

        json_file = backend_root / "nse_stocks.json"
        txt_file = backend_root / "nse_stocks.txt"

        if json_file.exists():
            return jsonify(json.loads(json_file.read_text()))

        if txt_file.exists():
            stocks = [
                line.strip() for line in txt_file.read_text().splitlines()
                if line.strip()
            ]
            return jsonify({
                "count": len(stocks),
                "stocks": [
                    {
                        "symbol": s,
                        "yahoo_symbol": s,
                        "name": s.replace(".NS", "")
                    } for s in stocks
                ]
            })

        return jsonify({
            "error": "NSE stocks list not found.",
            "count": 0,
            "stocks": []
        }), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------- ANALYSIS ROUTES ----------
@app.route('/analyze', methods=['POST'])
def analyze_stocks():
    """Start analysis of selected stocks from watchlist"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body required"}), 400

        tickers = data.get("tickers", [])
        indicators = data.get("indicators")
        capital = data.get("capital", 100000)  # Default capital

        if not tickers:
            return jsonify({"error": "tickers list required"}), 400

        if not isinstance(tickers, list) or len(tickers) > 100:
            return jsonify({"error": "tickers must be list of 1-100 symbols"}), 400

        # Generate unique job ID
        job_id = str(uuid.uuid4())

        # Create analysis job record in database
        execute_db('''
            INSERT INTO analysis_jobs (job_id, status, total, created_at)
            VALUES (?, ?, ?, datetime('now'))
        ''', (job_id, 'queued', len(tickers)))

        # Start background analysis
        success = start_analysis_job(job_id, tickers, indicators, capital, use_demo=False)

        if not success:
            # Update job status to failed if couldn't start
            execute_db('''
                UPDATE analysis_jobs SET status = 'failed' WHERE job_id = ?
            ''', (job_id,))
            return jsonify({"error": "Failed to start analysis job"}), 500

        return jsonify({
            "job_id": job_id,
            "status": "started",
            "total": len(tickers)
        }), 202

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/status/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """Get status of analysis job"""
    try:
        # Try to get from job state manager first
        job_state = get_job_state_manager()
        job = job_state.get_job(job_id)

        if job:
            return jsonify(job)

        # Fallback to database query
        row = query_db('''
            SELECT job_id, status, progress, total, completed, successful,
                   errors, created_at, started_at, completed_at
            FROM analysis_jobs WHERE job_id = ?
        ''', (job_id,), one=True)

        if not row:
            return jsonify({"error": "Job not found"}), 404

        # Parse errors if any
        errors = []
        if row['errors']:
            try:
                errors = json.loads(row['errors'])
            except:
                errors = [row['errors']]

        return jsonify({
            "job_id": row['job_id'],
            "status": row['status'],
            "progress": row['progress'],
            "total": row['total'],
            "completed": row['completed'],
            "successful": row.get('successful', 0),
            "errors": errors,
            "created_at": row['created_at'],
            "started_at": row['started_at'],
            "completed_at": row['completed_at']
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/report/<ticker>', methods=['GET'])
def get_analysis_report(ticker):
    """Get latest analysis result for a stock"""
    try:
        # Query latest analysis result from unified table
        row = query_db('''
            SELECT ticker, symbol, name, yahoo_symbol, score, verdict,
                   entry, stop_loss, target, entry_method, data_source,
                   is_demo_data, raw_data, status, error_message,
                   created_at, updated_at, analysis_source
            FROM analysis_results
            WHERE ticker = ? OR symbol = ?
            ORDER BY created_at DESC
            LIMIT 1
        ''', (ticker, ticker), one=True)

        if not row:
            return jsonify({"error": "No analysis found for this stock"}), 404

        # Parse raw_data if exists
        raw_data = None
        if row['raw_data']:
            try:
                raw_data = json.loads(row['raw_data'])
            except:
                raw_data = row['raw_data']

        return jsonify({
            "ticker": row['ticker'],
            "symbol": row['symbol'],
            "name": row['name'],
            "yahoo_symbol": row['yahoo_symbol'],
            "score": row['score'],
            "verdict": row['verdict'],
            "entry": row['entry'],
            "stop_loss": row['stop_loss'],
            "target": row['target'],
            "entry_method": row['entry_method'],
            "data_source": row['data_source'],
            "is_demo_data": bool(row['is_demo_data']),
            "raw_data": raw_data,
            "status": row['status'],
            "error_message": row['error_message'],
            "analyzed_at": row['created_at'],
            "updated_at": row['updated_at'],
            "analysis_source": row['analysis_source']
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/cancel-job/<job_id>', methods=['POST'])
def cancel_analysis_job(job_id):
    """Cancel a running analysis job"""
    try:
        success = cancel_job(job_id)

        # Also update database if job exists
        execute_db('''
            UPDATE analysis_jobs
            SET status = 'cancelled', completed_at = datetime('now')
            WHERE job_id = ? AND status IN ('queued', 'processing')
        ''', (job_id,))

        if success:
            return jsonify({"message": "Job cancelled successfully"})
        else:
            return jsonify({"error": "Job not found or already completed"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------- BULK ANALYSIS ROUTES ----------
@app.route('/all-stocks', methods=['GET'])
def get_all_stocks():
    """Get all bulk-analyzed stocks with latest analysis"""
    try:
        # Get latest analysis for each unique symbol from bulk analysis
        rows = query_db('''
            SELECT
                symbol,
                name,
                yahoo_symbol,
                score,
                verdict,
                entry,
                stop_loss,
                target,
                created_at as analyzed_at,
                updated_at
            FROM analysis_results
            WHERE analysis_source = 'bulk'
            AND (symbol, created_at) IN (
                SELECT symbol, MAX(created_at)
                FROM analysis_results
                WHERE analysis_source = 'bulk'
                GROUP BY symbol
            )
            ORDER BY symbol
        ''')

        stocks = []
        if rows:
            stocks = [{
                "symbol": r["symbol"],
                "name": r["name"],
                "yahoo_symbol": r["yahoo_symbol"],
                "score": r["score"],
                "verdict": r["verdict"],
                "entry": r["entry"],
                "stop_loss": r["stop_loss"],
                "target": r["target"],
                "analyzed_at": r["analyzed_at"],
                "updated_at": r["updated_at"]
            } for r in rows]

        return jsonify({
            "stocks": stocks,
            "count": len(stocks)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/all-stocks/<symbol>/history', methods=['GET'])
def get_stock_history(symbol):
    """Get analysis history for a specific stock"""
    try:
        # Get all analyses for this symbol (both bulk and watchlist)
        rows = query_db('''
            SELECT
                ticker,
                symbol,
                name,
                yahoo_symbol,
                score,
                verdict,
                entry,
                stop_loss,
                target,
                entry_method,
                data_source,
                is_demo_data,
                raw_data,
                status,
                error_message,
                created_at as analyzed_at,
                updated_at,
                analysis_source
            FROM analysis_results
            WHERE symbol = ? OR ticker = ?
            ORDER BY created_at DESC
        ''', (symbol, symbol))

        history = []
        if rows:
            history = [{
                "ticker": r["ticker"],
                "symbol": r["symbol"],
                "name": r["name"],
                "yahoo_symbol": r["yahoo_symbol"],
                "score": r["score"],
                "verdict": r["verdict"],
                "entry": r["entry"],
                "stop_loss": r["stop_loss"],
                "target": r["target"],
                "entry_method": r["entry_method"],
                "data_source": r["data_source"],
                "is_demo_data": bool(r["is_demo_data"]),
                "raw_data": r["raw_data"],
                "status": r["status"],
                "error_message": r["error_message"],
                "analyzed_at": r["analyzed_at"],
                "updated_at": r["updated_at"],
                "analysis_source": r["analysis_source"]
            } for r in rows]

        return jsonify({"history": history})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/analyze-all-stocks', methods=['POST'])
def analyze_all_stocks():
    """Start bulk analysis of all stocks"""
    try:
        from infrastructure import start_bulk_analysis, analyze_single_stock_bulk

        data = request.get_json()
        symbols = data.get("symbols", []) if data else []

        # If no symbols provided or empty, get all NSE stocks
        if not symbols:
            # Try to get from NSE stocks file
            try:
                from pathlib import Path
                import json

                backend_root = Path(__file__).resolve().parent / "data"
                json_file = backend_root / "nse_stocks.json"

                if json_file.exists():
                    with open(json_file, 'r') as f:
                        nse_data = json.load(f)
                        symbols = [stock.get('symbol', stock.get('yahoo_symbol', '')) for stock in nse_data.get('stocks', [])]
                        symbols = [s for s in symbols if s]  # Filter out empty strings

                if not symbols:
                    return jsonify({"error": "No symbols provided and could not load NSE stocks"}), 400

            except Exception as load_error:
                return jsonify({"error": f"Could not load NSE stocks: {str(load_error)}"}), 500

        # Limit to reasonable number for bulk analysis
        if len(symbols) > 500:
            symbols = symbols[:500]

        # Convert symbols to stock objects for bulk analysis
        stocks = [
            {
                "symbol": symbol.replace('.NS', ''),  # Remove exchange suffix for symbol
                "yahoo_symbol": symbol if '.NS' in symbol else f"{symbol}.NS",
                "name": ""
            }
            for symbol in symbols
        ]

        # Start bulk analysis (this returns immediately, analysis runs in background)
        start_bulk_analysis(stocks, use_demo=True)  # Use demo=True for bulk analysis

        return jsonify({
            "message": f"Started bulk analysis of {len(stocks)} stocks",
            "total": len(stocks)
        }), 202

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/all-stocks/progress', methods=['GET'])
def get_all_stocks_progress():
    """Get progress of bulk analysis"""
    # For now, return a simple status since bulk analysis is fire-and-forget
    # In a more complete implementation, you'd track progress in a database
    return jsonify({
        "status": "completed",  # Placeholder
        "progress": 100,
        "message": "Bulk analysis completed"
    })


@app.route('/initialize-all-stocks', methods=['POST'])
def initialize_all_stocks():
    """Initialize bulk analysis infrastructure"""
    return jsonify({
        "message": "Bulk analysis infrastructure initialized",
        "status": "ready"
    }), 200



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
