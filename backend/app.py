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



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
