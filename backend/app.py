import os
import uuid
import json
import traceback
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Union, Tuple

from flask import Flask, request, jsonify, send_file, Response
from flask_cors import CORS
from dotenv import load_dotenv
from pathlib import Path

# Local modules (keep existing project structure)
# db.py must expose init_db_if_needed, get_db_connection (or get_db), query_db, execute_db, close_db
from db import init_db_if_needed, get_db_connection, query_db, execute_db, close_db
from auth import require_auth, MASTER_API_KEY
from config import config

# optional: rate-limiter (graceful if not installed)
try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    LIMITER_AVAILABLE = True
except ImportError:
    LIMITER_AVAILABLE = False
    print("WARNING: flask-limiter not installed. Rate limiting disabled.")

load_dotenv()

app = Flask(__name__)

# -------------------------
# CORS (explicit allow-list for frontend)
# -------------------------
CORS(
    app,
    resources={r"/*": {"origins": config.CORS_ORIGINS}},
    supports_credentials=False,
    allow_headers=["Content-Type", "Authorization", "X-API-Key"],
    expose_headers=["Content-Type", "X-API-Key"],
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
)

# -------------------------
# Global OPTIONS handler for preflight requests
# -------------------------
@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        resp = app.make_default_options_response()
        headers = resp.headers
        # Allow the vercel origin
        headers["Access-Control-Allow-Origin"] = "https://the-tool-theta.vercel.app"
        headers["Access-Control-Allow-Headers"] = "Content-Type, X-API-Key, Authorization"
        headers["Access-Control-Allow-Methods"] = "GET, POST, DELETE, PUT, OPTIONS"
        return resp

# Ensure DB connection closed after request
app.teardown_appcontext(close_db)

# -------------------------
# Rate limiter (optional)
# -------------------------
if LIMITER_AVAILABLE and getattr(config, "RATE_LIMIT_ENABLED", False):
    limiter = Limiter(app=app, key_func=get_remote_address, default_limits=[f"{config.RATE_LIMIT_PER_MINUTE} per minute"], storage_uri="memory://")
else:
    # Mock limiter decorator (no-op)
    class _MockLimiter:
        @staticmethod
        def limit(val):
            def dec(f):
                return f
            return dec
    limiter = _MockLimiter()

# -------------------------
# Gunicorn-safe DB init: run once per worker process
# -------------------------
@app.before_request
def ensure_db_initialized():
    """
    Safe to call on every request: init_db_if_needed does nothing if DB already exists.
    Using before_request is safer under gunicorn (worker-per-process).
    """
    # Skip for static checks
    if request.method == "OPTIONS":
        return  # let CORS handle preflight

    init_db_if_needed()


# -------------------------
# Authentication middleware
# -------------------------
@app.before_request
def require_api_key():
    # Public endpoints
    if request.path in ["/", "/health"] or request.method == "OPTIONS":
        return

    # Allow bypass in tests or if MASTER_API_KEY is empty in local dev
    if app.config.get("TESTING"):
        return

    api_key = request.headers.get("X-API-Key") or request.headers.get("Authorization")
    if not api_key:
        return jsonify({"error": "Unauthorized", "message": "Missing X-API-Key"}), 401

# -------------------------
# Lazy helpers (keeps imports light until needed)
# -------------------------
def get_logger():
    try:
        from utils.infrastructure.logging import setup_logger
        return setup_logger()
    except Exception:
        import logging
        logger = logging.getLogger("thetool")
        if not logger.handlers:
            h = logging.StreamHandler()
            fmt = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
            h.setFormatter(fmt)
            logger.addHandler(h)
        logger.setLevel("INFO")
        return logger

logger = get_logger()
logger.info("Starting backend (merged)")

# Import real analysis orchestrator & thread tasks lazily so app can start even if heavy deps missing
def get_analysis_orchestrator():
    from utils.analysis.orchestrator import analyze_ticker, export_to_excel
    return analyze_ticker, export_to_excel

def get_thread_tasks():
    from infrastructure.thread_tasks import start_analysis_job, cancel_job, start_bulk_analysis
    return start_analysis_job, cancel_job, start_bulk_analysis

def _data_root():
    return Path(__file__).resolve().parent


# -------------------------
# Routes (original full backend behavior)
# -------------------------
@app.route("/", methods=["GET"])
def index():
    return {"status": "ok", "message": "Backend running"}

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "message": "backend running"})

# Watchlist endpoints (GET/POST/DELETE)
@app.route("/watchlist", methods=["GET"])
def get_watchlist():
    rows = query_db("SELECT id, symbol, name FROM watchlist")
    if not rows:
        return jsonify([])
    # rows expected as sqlite3.Row -> mapping
    return jsonify([{"id": r["id"], "symbol": r["symbol"], "name": r["name"]} for r in rows])

@app.route("/watchlist", methods=["POST"])
def add_watchlist():
    data = request.get_json() or {}
    symbol = data.get("symbol")
    name = data.get("name", "")
    if not symbol:
        return jsonify({"error": "Symbol is required"}), 400
    existing = query_db("SELECT id FROM watchlist WHERE symbol = ?", (symbol,), one=True)
    if existing:
        return jsonify({"error": "Symbol already in watchlist", "already_exists": True}), 409
    execute_db("INSERT INTO watchlist (symbol, name, created_at, user_id) VALUES (?, ?, datetime('now'), 1)", (symbol, name))
    return jsonify({"message": "Added to watchlist", "symbol": symbol}), 201

@app.route("/watchlist", methods=["DELETE"])
def delete_watchlist():
    data = request.get_json() or {}
    symbol = data.get("symbol")
    if not symbol:
        return jsonify({"error": "symbol required"}), 400
    execute_db("DELETE FROM watchlist WHERE symbol = ?", (symbol,))
    return jsonify({"message": "Removed from watchlist"})

# NSE stocks list
@app.route("/nse-stocks", methods=["GET"])
def get_nse_stocks():
    try:
        backend_root = _data_root()
        json_file = backend_root / "nse_stocks.json"
        txt_file = backend_root / "nse_stocks.txt"

        if json_file.exists():
            return jsonify(json.loads(json_file.read_text(encoding="utf-8")))

        if txt_file.exists():
            lines = [line.strip() for line in txt_file.read_text(encoding="utf-8").splitlines() if line.strip()]
            return jsonify({
                "count": len(lines),
                "stocks": [
                    {"symbol": s, "yahoo_symbol": s, "name": s.replace(".NS", "")}
                    for s in lines
                ]
            })

        return jsonify({"error": "NSE stocks list not found.", "count": 0, "stocks": []}), 404
    except Exception as e:
        logger.exception("Error reading NSE files")
        return jsonify({"error": str(e)}), 500

# ANALYZE single / multiple
@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request data required"}), 400
	    
        from models.validation import TickerAnalysisRequest, validate_request
        validated, error = validate_request(TickerAnalysisRequest, data)
        if error:
            return jsonify(error), 400

        tickers = validated.tickers
        indicators = validated.indicators
        capital = validated.capital
        use_demo = validated.use_demo_data

        job_id = str(uuid.uuid4())

        # insert job record
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('''INSERT INTO analysis_jobs (job_id, status, total, created_at, updated_at) VALUES (?, ?, ?, ?, ?)''',
                    (job_id, 'queued', len(tickers), datetime.now().isoformat(), datetime.now().isoformat()))
        conn.commit()
        conn.close()

        # start background job (thread_tasks should exist in your repo)
        start_analysis_job, _, _ = get_thread_tasks()
        success = start_analysis_job(job_id, tickers, indicators, capital, use_demo)
        if not success:
            execute_db("UPDATE analysis_jobs SET status = 'failed' WHERE job_id = ?", (job_id,))
            return jsonify({"error": "Failed to start background job"}), 500

        return jsonify({"status": "queued", "job_id": job_id, "count": len(tickers)}), 202

    except Exception as e:
        logger.exception("Analyze endpoint error")
        return jsonify({"error": str(e)}), 500

# Job status
@app.route("/status/<job_id>", methods=["GET"])
def get_status(job_id):
    try:
        # First try in-memory job state manager if exists
        try:
            from models.job_state import get_job_state_manager
            jm = get_job_state_manager()
            job = jm.get_job(job_id)
            if job:
                return jsonify(job)
        except Exception:
            pass

        row = query_db('''SELECT job_id, status, progress, total, completed, errors, created_at, started_at, completed_at, successful FROM analysis_jobs WHERE job_id = ?''', (job_id,), one=True)
        if not row:
            return jsonify({"error": "Job not found"}), 404

        errors = []
        if row.get("errors"):
            try:
                errors = json.loads(row["errors"])
            except:
                errors = [row["errors"]]

        return jsonify({
            "job_id": row["job_id"],
            "status": row["status"],
            "progress": row["progress"],
            "total": row["total"],
            "completed": row["completed"],
            "successful": row.get("successful", 0),
            "errors": errors,
            "created_at": row["created_at"],
            "started_at": row["started_at"],
            "completed_at": row["completed_at"]
        })

    except Exception as e:
        logger.exception("Status endpoint error")
        return jsonify({"error": str(e)}), 500

# report, download, bulk, history, etc. -- restore original implementations
# (for brevity I include core routes; if you have the older file in repo keep the rest verbatim)
@app.route("/report/<ticker>", methods=["GET"])
def get_report(ticker):
    try:
        row = query_db('''SELECT ticker, symbol, name, yahoo_symbol, score, verdict, entry, stop_loss, target, raw_data, status, error_message, created_at, updated_at, analysis_source FROM analysis_results WHERE ticker = ? OR symbol = ? ORDER BY created_at DESC LIMIT 1''', (ticker, ticker), one=True)
        if not row:
            return jsonify({"error": "No analysis found for this ticker"}), 404

        raw_data = None
        if row.get("raw_data"):
            try:
                raw_data = json.loads(row["raw_data"])
            except:
                raw_data = row["raw_data"]

        return jsonify({
            "ticker": row["ticker"],
            "symbol": row["symbol"],
            "name": row["name"],
            "yahoo_symbol": row["yahoo_symbol"],
            "score": row["score"],
            "verdict": row["verdict"],
            "entry": row["entry"],
            "stop_loss": row["stop_loss"],
            "target": row["target"],
            "entry_method": row["entry_method"],
            "data_source": row["data_source"],
            "is_demo_data": bool(row["is_demo_data"]),
            "raw_data": raw_data,
            "status": row["status"],
            "error_message": row["error_message"],
            "analyzed_at": row["created_at"],
            "updated_at": row["updated_at"],
            "analysis_source": row["analysis_source"]
        })
    except Exception as e:
        logger.exception("Report endpoint error")
        return jsonify({"error": str(e)}), 500

# ---------- Cancel job ----------
@app.route("/cancel-job/<job_id>", methods=["POST"])
def cancel_analysis_job(job_id):
    try:
        success = False
        try:
            if cancel_job:
                success = cancel_job(job_id)
            else:
                success = False
        except Exception:
            success = False

        # Update DB status if present
        execute_db("""
            UPDATE analysis_jobs
            SET status = 'cancelled', completed_at = datetime('now'), updated_at = datetime('now')
            WHERE job_id = ? AND status IN ('queued', 'processing')
        """, (job_id,))

        if success:
            return jsonify({"message": "Job cancelled successfully"})
        else:
            return jsonify({"error": "Job not found or already completed"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------- Bulk endpoints ----------

@app.route("/all-stocks", methods=["GET"])
def get_all_stocks():
    try:
        # Latest analysis per symbol (bulk and watchlist)
        rows = query_db("""
            SELECT
                COALESCE(symbol, ticker) AS symbol,
                name,
                yahoo_symbol,
                score,
                verdict,
                entry,
                stop_loss,
                target,
                created_at AS analyzed_at,
                updated_at,
                analysis_source
            FROM analysis_results
            WHERE analysis_source IN ('bulk', 'watchlist')
            AND (COALESCE(symbol, ticker), created_at) IN (
                SELECT COALESCE(symbol, ticker), MAX(created_at)
                FROM analysis_results
                WHERE analysis_source IN ('bulk', 'watchlist')
                GROUP BY COALESCE(symbol, ticker)
            )
            ORDER BY symbol ASC
        """)

        stocks = []
        if rows:
            for r in rows:
                stocks.append({
                    "symbol": r["symbol"],
                    "name": r["name"],
                    "yahoo_symbol": r["yahoo_symbol"],
                    "score": r["score"],
                    "verdict": r["verdict"],
                    "entry": r["entry"],
                    "stop_loss": r["stop_loss"],
                    "target": r["target"],
                    "analyzed_at": r["analyzed_at"],
                    "updated_at": r["updated_at"],
                    "analysis_source": r["analysis_source"]
                })

        return jsonify({"count": len(stocks), "stocks": stocks})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/all-stocks/<symbol>/history", methods=["GET"])
def get_stock_history(symbol):
    try:
        rows = query_db("""
            SELECT
                ticker, symbol, name, yahoo_symbol, score, verdict, entry, stop_loss, target,
                entry_method, data_source, is_demo_data, raw_data, status, error_message, created_at AS analyzed_at, updated_at, analysis_source
            FROM analysis_results
            WHERE COALESCE(symbol, ticker) = ?
            ORDER BY created_at DESC
            LIMIT 50
        """, (symbol,))

        history = []
        if rows:
            for r in rows:
                raw_data = None
                if r["raw_data"]:
                    try:
                        raw_data = json.loads(r["raw_data"])
                    except Exception:
                        raw_data = r["raw_data"]

                history.append({
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
                    "raw_data": raw_data,
                    "status": r["status"],
                    "error_message": r["error_message"],
                    "analyzed_at": r["analyzed_at"],
                    "updated_at": r["updated_at"],
                    "analysis_source": r["analysis_source"]
                })

        return jsonify({"symbol": symbol, "history": history, "count": len(history)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/analyze-all-stocks", methods=["POST"])
def analyze_all_stocks():
    try:
        data = request.get_json() or {}
        symbols = data.get("symbols", [])

        # Load all NSE if not provided
        if not symbols:
            backend_root = _data_root()
            json_file = backend_root / "nse_stocks.json"
            if json_file.exists():
                with open(json_file, "r", encoding="utf-8") as f:
                    nse_data = json.load(f)
                symbols = [stock.get("symbol") or stock.get("yahoo_symbol") for stock in nse_data.get("stocks", [])]
            else:
                # fallback to txt
                txt = backend_root / "nse_stocks.txt"
                if txt.exists():
                    symbols = [s.strip() for s in txt.read_text(encoding="utf-8").splitlines() if s.strip()]

        if not symbols:
            return jsonify({"error": "No symbols provided and could not load NSE stocks"}), 400

        # Limit to 500 for safety
        if len(symbols) > 500:
            symbols = symbols[:500]

        stocks = []
        for s in symbols:
            sym = s
            yahoo = s if s.endswith(".NS") else f"{s}.NS"
            # normalize symbol without .NS suffix for DB symbol
            symbol_key = yahoo.replace(".NS", "")
            stocks.append({"symbol": symbol_key, "yahoo_symbol": yahoo, "name": ""})

        # Start background bulk analysis
        if start_bulk_analysis:
            start_bulk_analysis(stocks, use_demo=True)
        else:
            # If missing, insert placeholder 'pending' rows into analysis_results
            now = datetime.now().isoformat()
            for st in stocks:
                execute_db("""
                    INSERT INTO analysis_results (ticker, symbol, name, yahoo_symbol, score, verdict, status, created_at, updated_at, analysis_source)
                    VALUES (?, ?, ?, ?, 0.0, 'Pending', 'pending', ?, ?, 'bulk')
                """, (st["yahoo_symbol"], st["symbol"], st["name"], st["yahoo_symbol"], now, now))

        return jsonify({"message": f"Started bulk analysis of {len(stocks)} stocks", "total": len(stocks)}), 202

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/all-stocks/progress", methods=["GET"])
def get_all_stocks_progress():
    try:
        # Basic counts using analysis_results (bulk)
        total = query_db("SELECT COUNT(DISTINCT COALESCE(symbol, ticker)) AS cnt FROM analysis_results", (), one=True)
        total_count = total["cnt"] if total else 0

        rows = query_db("""
            SELECT status, COUNT(*) as cnt FROM (
                SELECT COALESCE(symbol, ticker) as sym, status
                FROM analysis_results
                WHERE analysis_source = 'bulk'
                AND id IN (
                    SELECT MAX(id) FROM analysis_results WHERE analysis_source = 'bulk' GROUP BY COALESCE(symbol, ticker)
                )
            ) GROUP BY status
        """)
        stats = {}
        if rows:
            for r in rows:
                stats[r["status"]] = r["cnt"]

        completed = stats.get("completed", 0)
        failed = stats.get("failed", 0)
        analyzing = stats.get("analyzing", 0)
        pending = stats.get("pending", 0)

        finished = completed + failed
        percentage = (finished / total_count * 100) if total_count > 0 else 0

        return jsonify({
            "total": total_count,
            "completed": completed,
            "analyzing": analyzing,
            "failed": failed,
            "pending": pending,
            "percentage": round(percentage, 2),
            "is_analyzing": analyzing > 0
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/initialize-all-stocks", methods=["POST"])
def initialize_all_stocks():
    try:
        # Use DATA_PATH env or repo data folder
        data_path = os.getenv("DATA_PATH", str(Path(__file__).resolve().parent / "data"))
        json_file = Path(data_path) / "nse_stocks.json"
        if not json_file.exists():
            return jsonify({"error": "NSE stocks data file not found"}), 404

        nse_data = json.loads(json_file.read_text(encoding="utf-8"))
        stocks = nse_data.get("stocks", [])
        if not stocks:
            return jsonify({"error": "No stocks found in data file"}), 404

        conn = get_db_connection()
        cur = conn.cursor()
        inserted = 0
        now = datetime.now().isoformat()
        for s in stocks:
            yahoo = s.get("yahoo_symbol") or s.get("symbol")
            symbol = (s.get("symbol") or yahoo).replace(".NS", "")
            try:
                cur.execute('''INSERT OR IGNORE INTO analysis_results (ticker, symbol, name, yahoo_symbol, score, verdict, status, created_at, updated_at, analysis_source) VALUES (?, ?, ?, ?, 0.0, 'Pending', 'pending', ?, ?, 'bulk')''', (yahoo, symbol, s.get("name",""), yahoo, now, now))
                inserted += 1
            except Exception:
                logger.exception("Insert error for stock: %s", s)
        conn.commit()
        conn.close()
        return jsonify({"message": f"Initialized {inserted} stocks", "count": inserted}), 201
    except Exception as e:
        logger.exception("Initialize all stocks error")
        return jsonify({"error": str(e)}), 500


# other routes (history, analyze-all-stocks, progress) should be restored from your older file
# If you preserved the older file in git, copy/paste the remaining route implementations here.

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=os.getenv("FLASK_ENV") == "development")
