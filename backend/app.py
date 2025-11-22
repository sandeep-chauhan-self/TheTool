from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from pathlib import Path
import os
import json
import uuid
import traceback
from datetime import datetime

# Lightweight DB wrapper (Railway-safe)
from db import init_db_if_needed, query_db, execute_db, close_db

# Job/thread helpers (assumed present)
try:
    from infrastructure.thread_tasks import start_analysis_job, start_bulk_analysis, cancel_job
except Exception:
    # Graceful fallback if infrastructure module isn't available at import time.
    start_analysis_job = None
    start_bulk_analysis = None
    cancel_job = None

# Job state manager (in-memory job info)
try:
    from models.job_state import get_job_state_manager
except Exception:
    def get_job_state_manager():
        # Minimal fallback manager
        class _M:
            def get_job(self, job_id):
                return None
        return _M()

app = Flask(__name__)

# --------- CORS (restrict to frontend domain for security) ----------
CORS(
    app,
    resources={r"/*": {"origins": ["https://the-tool-theta.vercel.app"]}},
    supports_credentials=True,
    allow_headers=["Content-Type", "X-API-Key", "Authorization"],
    expose_headers=["Content-Type", "X-API-Key"]
)

# Ensure DB connection cleanup after each request
app.teardown_appcontext(close_db)

# Ensure DB initialized in Gunicorn worker before handling requests
@app.before_request
def ensure_db():
    init_db_if_needed()


# ---------- Lightweight API Key auth ----------
# For now we check X-API-Key header on protected endpoints.
# NOTE: in the old code require_auth decorator also checked MASTER_API_KEY; adapt if needed.
def _require_api_key_or_abort():
    # Skip checks for health and OPTIONS and local testing
    if request.path in ("/", "/health") or request.method == "OPTIONS":
        return
    if app.config.get("TESTING"):
        return
    api_key = request.headers.get("X-API-Key") or request.headers.get("Authorization")
    if not api_key:
        return jsonify({"error": "Unauthorized", "message": "Missing X-API-Key"}), 401
    # Optionally validate api_key here (MASTER key etc) if you have one in env.

@app.before_request
def lightweight_auth_hook():
    # Run lightweight auth for all requests (hook can return a response)
    resp = _require_api_key_or_abort()
    if resp:
        return resp


# -------------- Utilities --------------
def _data_root() -> Path:
    """Return the backend data folder path. Respects DATA_PATH env var."""
    dp = os.getenv("DATA_PATH", None)
    if dp:
        return Path(dp)
    return Path(__file__).resolve().parent / "data"


# -------------- Routes (core + restored enterprise behavior) --------------

@app.route("/")
def index():
    return {"status": "ok", "message": "Backend running"}

@app.route("/health")
def health():
    return jsonify({"status": "ok", "message": "backend running"})


# ---------- Watchlist ----------
@app.route("/watchlist", methods=["GET"])
def get_watchlist():
    rows = query_db("SELECT id, symbol, name FROM watchlist")
    if not rows:
        return jsonify([])
    return jsonify([{"id": r["id"], "symbol": r["symbol"], "name": r["name"]} for r in rows])

@app.route("/watchlist", methods=["POST"])
def add_watchlist():
    data = request.get_json() or {}
    symbol = data.get("symbol")
    name = data.get("name", "")
    if not symbol:
        return {"error": "Symbol required"}, 400
    existing = query_db("SELECT id FROM watchlist WHERE symbol = ?", (symbol,), one=True)
    if existing:
        return {"error": "Symbol exists", "already_exists": True}, 409
    execute_db("INSERT INTO watchlist (symbol, name, created_at, user_id) VALUES (?, ?, datetime('now'), 1)", (symbol, name))
    return {"message": "Added", "symbol": symbol}, 201

@app.route("/watchlist", methods=["DELETE"])
def delete_watchlist():
    data = request.get_json() or {}
    symbol = data.get("symbol")
    execute_db("DELETE FROM watchlist WHERE symbol = ?", (symbol,))
    return {"message": "Removed"}


# ---------- NSE stocks (json / txt fallback) ----------
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
        return jsonify({"error": str(e)}), 500


# ---------- Analyze (start job) ----------
@app.route("/analyze", methods=["POST"])
def analyze_stocks():
    try:
        body = request.get_json()
        if not body:
            return jsonify({"error": "Request body required"}), 400

        tickers = body.get("tickers", [])
        indicators = body.get("indicators")
        capital = body.get("capital", 100000)
        use_demo = body.get("use_demo_data", False)

        if not tickers or not isinstance(tickers, list):
            return jsonify({"error": "tickers list required"}), 400
        if len(tickers) > 200:
            return jsonify({"error": "Too many tickers (max 200)"}), 400

        job_id = str(uuid.uuid4())
        # Insert job into DB
        execute_db("""
            INSERT INTO analysis_jobs (job_id, status, total, created_at, updated_at)
            VALUES (?, ?, ?, datetime('now'), datetime('now'))
        """, (job_id, "queued", len(tickers)))

        # Try to start background job (infrastructure.thread_tasks must return True/False)
        success = False
        try:
            if start_analysis_job:
                success = start_analysis_job(job_id, tickers, indicators, capital, use_demo)
            else:
                # If thread helper missing, mark queued but not started
                success = True
        except Exception:
            # log to DB
            execute_db("UPDATE analysis_jobs SET status = 'failed', errors = ? WHERE job_id = ?", (json.dumps([traceback.format_exc()]), job_id))
            return jsonify({"error": "Failed to start analysis job"}), 500

        if not success:
            execute_db("UPDATE analysis_jobs SET status = 'failed' WHERE job_id = ?", (job_id,))
            return jsonify({"error": "Failed to start analysis job"}), 500

        return jsonify({"job_id": job_id, "status": "started", "total": len(tickers)}), 202

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------- Job Status ----------
@app.route("/status/<job_id>", methods=["GET"])
def get_job_status(job_id):
    try:
        job_mgr = get_job_state_manager()
        job = job_mgr.get_job(job_id)
        if job:
            return jsonify(job)

        row = query_db("""
            SELECT job_id, status, progress, total, completed, successful,
                   errors, created_at, started_at, completed_at
            FROM analysis_jobs WHERE job_id = ?
        """, (job_id,), one=True)

        if not row:
            return jsonify({"error": "Job not found"}), 404

        errors = []
        if row["errors"]:
            try:
                errors = json.loads(row["errors"])
            except Exception:
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
        return jsonify({"error": str(e)}), 500


# ---------- Report for single ticker ----------
@app.route("/report/<ticker>", methods=["GET"])
def get_analysis_report(ticker):
    try:
        row = query_db("""
            SELECT ticker, symbol, name, yahoo_symbol, score, verdict,
                   entry, stop_loss, target, entry_method, data_source,
                   is_demo_data, raw_data, status, error_message,
                   created_at, updated_at, analysis_source
            FROM analysis_results
            WHERE ticker = ? OR symbol = ?
            ORDER BY created_at DESC
            LIMIT 1
        """, (ticker, ticker), one=True)

        if not row:
            return jsonify({"error": "No analysis found for this stock"}), 404

        raw_data = None
        if row["raw_data"]:
            try:
                raw_data = json.loads(row["raw_data"])
            except Exception:
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
    """Idempotent initializer - inserts NSE stocks into analysis_results as bulk if not present"""
    try:
        # Check already initialized
        count_row = query_db("SELECT COUNT(*) AS cnt FROM analysis_results WHERE analysis_source = 'bulk'", (), one=True)
        if count_row and count_row["cnt"] > 0:
            return jsonify({"message": "Already initialized", "count": count_row["cnt"], "already_initialized": True})

        backend_root = _data_root()
        nse_json = backend_root / "nse_stocks.json"
        if not nse_json.exists():
            # fallback to txt
            txt = backend_root / "nse_stocks.txt"
            if not txt.exists():
                return jsonify({"error": "NSE stocks data file not found"}), 404
            symbols = [s.strip() for s in txt.read_text(encoding="utf-8").splitlines() if s.strip()]
            nse_list = [{"symbol": s, "yahoo_symbol": s, "name": s.replace(".NS", "")} for s in symbols]
        else:
            with open(nse_json, "r", encoding="utf-8") as f:
                nse_data = json.load(f)
            nse_list = nse_data.get("stocks", [])

        if not nse_list:
            return jsonify({"error": "No stocks found in data file"}), 404

        now = datetime.now().isoformat()
        inserted = 0
        for stock in nse_list:
            try:
                ticker = stock.get("yahoo_symbol") or stock.get("symbol")
                symbol = (stock.get("symbol") or ticker or "").replace(".NS", "")
                name = stock.get("name") or ""
                execute_db("""
                    INSERT INTO analysis_results (ticker, symbol, name, yahoo_symbol, score, verdict, status, created_at, updated_at, analysis_source)
                    VALUES (?, ?, ?, ?, 0.0, 'Pending', 'pending', ?, ?, 'bulk')
                """, (ticker, symbol, name, ticker, now, now))
                inserted += 1
            except Exception:
                # ignore duplicates or insertion problems but continue
                continue

        return jsonify({"message": f"Initialized {inserted} stocks", "count": inserted}), 201

    except Exception as e:
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
