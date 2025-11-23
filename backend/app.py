import os
import uuid
import json
import traceback
import sqlite3
import logging
from datetime import datetime
from pathlib import Path
import threading
from flask import Flask, request, jsonify, send_file, Response
from flask_cors import CORS
from dotenv import load_dotenv
from auth import require_auth, MASTER_API_KEY
from config import config
import sys

# Create Flask app instance
app = Flask(__name__)

from utils.logger import get_logger
from database import init_db, init_db_if_needed, get_db_connection, close_db, query_db, execute_db

try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    LIMITER_AVAILABLE = True
except ImportError:
    LIMITER_AVAILABLE = False
    get_remote_address = None
    get_remote_address = None


try:
    from infrastructure.thread_tasks import (
        start_analysis_job as infra_start_analysis_job,
        cancel_job as infra_cancel_job,
        start_bulk_analysis as infra_start_bulk_analysis
    )
except Exception:
    infra_start_analysis_job = None
    infra_cancel_job = None
    infra_start_bulk_analysis = None


if LIMITER_AVAILABLE and config.RATE_LIMIT_ENABLED:
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=[f"{config.RATE_LIMIT_PER_MINUTE} per minute"],
        storage_uri="memory://",
    )
else:
    class MockLimiter:
        @staticmethod
        def limit(limit_value):
            def decorator(f):
                return f
            return decorator
    limiter = MockLimiter()


def get_analyze_ticker():
    from utils.analysis.orchestrator import analyze_ticker, export_to_excel
    return analyze_ticker, export_to_excel

# Setup logging with DEBUG level
logger = get_logger()
logger.setLevel('DEBUG')  # Enable debug logging

# Also log to console for development

if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.DEBUG)
    formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
    console.setFormatter(formatter)
    logger.addHandler(console)





_allowed_origins = getattr(config, "CORS_ORIGINS",
    ["https://the-tool-theta.vercel.app", "http://localhost:3000"])

CORS(
    app,
    resources={r"/*": {"origins": _allowed_origins}},
    supports_credentials=False,
    allow_headers=["Content-Type", "Authorization", "X-API-Key"],
    expose_headers=["Content-Type", "X-API-Key"],
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
)



# Post-process response to ensure Access-Control headers for strict preflight handling
@app.after_request
def _set_cors_headers(response):
    origin = request.headers.get("Origin")
    if origin and origin in _allowed_origins:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Vary"] = "Origin"
    return response

# Handle OPTIONS as early-return (some proxies expect explicit response)
@app.route("/", methods=["OPTIONS"])
@app.route("/<path:unused>", methods=["OPTIONS"])
def _options_passthrough(unused=None):
    resp = jsonify({"status": "ok"})
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type, X-API-Key, Authorization"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    return resp, 200

# Ensure DB connection closed after each request
app.teardown_appcontext(close_db)


# ---------------------------
# DB init - gunicorn-safe
# ---------------------------
# We call init_db_if_needed() at before_request time so each worker will ensure DB exists.
@app.before_request
def _ensure_db_initialized():
    # Skip for preflight
    if request.method == "OPTIONS":
        return
    try:
        init_db_if_needed()
    except Exception:
        # Log but do not abort startup — the route handlers will catch DB errors
        app.logger.exception("DB init failed in before_request")


def _cancel_job(job_id: str) -> bool:
    try:
        if infra_cancel_job:
            return bool(infra_cancel_job(job_id))
        return False
    except Exception:
        app.logger.exception("Cancel job error")
        return False

# ---------------------------
# Data path helper
# ---------------------------
def _data_root() -> Path:
    # Respect DATA_PATH env var to allow Railway volume mapping
    data_path = os.getenv("DATA_PATH")
    if data_path:
        return Path(data_path)
    return Path(__file__).resolve().parent / "data"

@app.route("/", methods=["GET"])
def index():
    return {"status": "ok", "message": "Backend running (merged)"}

@app.route("/health", methods=["GET"])
def health():
    """
    Unified health check endpoint.
    - Public endpoint (no auth)
    - Includes uptime, cache stats, and readiness info
    - Safe fallback if cache module or start_time is missing
    """
    try:
        # Uptime calculation with fallback
        start_time = app.config.get("start_time")
        if not start_time:
            start_time = datetime.now()
            app.config["start_time"] = start_time
        uptime = (datetime.now() - start_time).total_seconds()

        # Try cache stats safely
        cache_stats = {}
        try:
            from cache import get_cache_stats
            cache_stats = get_cache_stats() or {}
        except Exception:
            cache_stats = {"enabled": False}

        return jsonify({
            "status": "ok",
            "message": "backend running",
            "uptime_seconds": uptime,
            "authentication": "enabled",
            "cache": cache_stats,
        }), 200

    except Exception as e:
        logger.error(f"/health error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500



@app.route("/analyze", methods=["POST"])
@require_auth
@limiter.limit(f"{config.ANALYZE_RATE_LIMIT} per minute")
def analyze():
    """
    Unified async analysis endpoint (best of both implementations).
    
    Features:
    - API key authentication
    - Rate limiting
    - Pydantic request validation
    - UUID job creation
    - DB job record
    - Background thread execution
    - Safe fallback if thread cannot start
    - Uniform response schema
    """

    try:
        logger.info("=" * 60)
        logger.info("ANALYSIS REQUEST RECEIVED")
        logger.info("=" * 60)

        # -------------------------------
        # 1. Parse + validate input
        # -------------------------------
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request data required"}), 400

        logger.debug(f"Incoming request payload: {data}")

        try:
            from models.validation import TickerAnalysisRequest, validate_request
            validated, error = validate_request(TickerAnalysisRequest, data)
            if error:
                logger.error(f"Validation error: {error}")
                return jsonify(error), 400

            tickers = validated.tickers
            indicators = validated.indicators
            capital = validated.capital
            use_demo = validated.use_demo_data

        except Exception:
            logger.warning("Pydantic validation missing — using fallback parsing")
            tickers = data.get("tickers", [])
            indicators = data.get("indicators")
            capital = data.get("capital", 100000)
            use_demo = data.get("use_demo_data", False)

        if not tickers:
            return jsonify({"error": "tickers list required"}), 400
        if len(tickers) > 500:
            return jsonify({"error": "Too many tickers (max 500)"}), 400

        # -------------------------------
        # 2. Generate Job ID
        # -------------------------------
        job_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        logger.info(f"Generated job_id = {job_id}")
        logger.info(f"Tickers count = {len(tickers)} | use_demo={use_demo}")

        # -------------------------------
        # 3. Insert job record into DB
        # -------------------------------
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('''
                INSERT INTO analysis_jobs 
                (job_id, status, total, completed, progress, errors,
                 created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                job_id,
                "queued",
                len(tickers),
                0,
                0,
                json.dumps([]),
                now,
                now
            ))
            conn.commit()
            conn.close()

            logger.info(f"Job record created for {job_id}")

        except Exception as db_err:
            logger.error(f"Failed to create job record: {db_err}")
            logger.error(traceback.format_exc())
            return jsonify({"error": "Failed creating job record"}), 500

        # -------------------------------
        # 4. Start Background Thread
        # -------------------------------
        try:
            from infrastructure.thread_tasks import start_analysis_job
            thread_started = start_analysis_job(job_id, tickers, indicators, capital, use_demo)

            if not thread_started:
                raise Exception("start_analysis_job returned False")

            logger.info(f"Background worker started successfully for {job_id}")

        except Exception as worker_err:
            logger.error(f"Failed starting worker for {job_id}: {worker_err}")
            logger.error(traceback.format_exc())

            # Mark job as failed
            try:
                execute_db('''
                    UPDATE analysis_jobs
                    SET status = 'failed', errors = ?
                    WHERE job_id = ?
                ''', (json.dumps([{"error": str(worker_err)}]), job_id))

            except Exception as update_err:
                logger.error(f"Failed marking job as failed: {update_err}")

            return jsonify({"error": "Failed to start background job"}), 500

        # -------------------------------
        # 5. Response
        # -------------------------------
        response = {
            "status": "queued",
            "job_id": job_id,
            "count": len(tickers),
            "message": f"Analysis started. Track via /status/{job_id}"
        }

        logger.info(f"Returning analyze response: {response}")
        return jsonify(response), 202

    except Exception as e:
        logger.error(f"ANALYZE endpoint error: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500



@app.route("/status/<job_id>", methods=["GET"])
@require_auth
def get_status(job_id):
    """
    Unified job-status endpoint.
    Combines:
    - In-memory job state (fast)
    - Database fallback
    - Full enriched metadata
    - Safe JSON parsing for errors
    """

    try:
        logger.debug(f"Status check requested for job_id: {job_id}")

        # -------------------------------------------------
        # 1. Try In-Memory Job State Manager First
        # -------------------------------------------------
        try:
            from models.job_state import get_job_state_manager
            jm = get_job_state_manager()
            mem_job = jm.get_job(job_id)

            if mem_job:  # Already a nice JSON-friendly dict
                logger.debug(f"In-memory state found for job {job_id}")
                return jsonify(mem_job)
        except Exception as e:
            logger.debug(f"In-memory job state unavailable: {e}")

        # -------------------------------------------------
        # 2. Fallback to Database
        # -------------------------------------------------
        row = query_db(
            """
            SELECT 
                job_id,
                status,
                progress,
                total,
                completed,
                successful,
                errors,
                created_at,
                started_at,
                completed_at,
                updated_at
            FROM analysis_jobs
            WHERE job_id = ?
            """,
            (job_id,),
            one=True
        )

        if not row:
            logger.warning(f"Job not found: {job_id}")
            return jsonify({"error": "Job not found"}), 404

        # -------------------------------------------------
        # 3. Parse Errors Safely
        # -------------------------------------------------
        errors_data = []
        raw_errors = row.get("errors")

        if raw_errors:
            try:
                errors_data = json.loads(raw_errors)
            except json.JSONDecodeError:
                logger.error(f"Unable to parse errors for job {job_id}: {raw_errors[:200]}")
                errors_data = [{"error": f"Parse failed: {raw_errors[:200]}"}]

        # -------------------------------------------------
        # 4. Build Unified Response
        # -------------------------------------------------
        response = {
            "job_id": row.get("job_id"),
            "status": row.get("status"),
            "progress": row.get("progress") or 0,
            "total": row.get("total") or 0,
            "completed": row.get("completed") or 0,
            "successful": row.get("successful") or 0,
            "errors": errors_data,
            "created_at": row.get("created_at"),
            "started_at": row.get("started_at"),
            "completed_at": row.get("completed_at"),
            "updated_at": row.get("updated_at"),
        }

        logger.debug(f"Status response for {job_id}: {response}")
        return jsonify(response)

    except Exception as e:
        logger.error(f"Status endpoint error: {e}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500



@app.route('/cancel/<job_id>', methods=['POST'])
@require_auth
def cancel_job(job_id):
    """Cancel a running analysis job (requires authentication)"""
    try:
        from infrastructure.thread_tasks import cancel_job as thread_cancel_job
        
        # Cancel the thread
        cancelled = thread_cancel_job(job_id)
        
        if not cancelled:
            # Check if job exists in database
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT status FROM analysis_jobs WHERE job_id = ?', (job_id,))
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return jsonify({"error": "Job not found"}), 404
            
            return jsonify({"error": "Job is not currently running"}), 400
        
        # Update database status
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE analysis_jobs
            SET status = 'cancelled', updated_at = ?, completed_at = ?
            WHERE job_id = ?
        ''', (datetime.now().isoformat(), datetime.now().isoformat(), job_id))
        conn.commit()
        conn.close()
        
        logger.info(f"Job {job_id} cancelled by user")
        return jsonify({"message": "Job cancelled successfully", "job_id": job_id})
        
    except Exception as e:
        logger.error(f"Cancel endpoint error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/history/<ticker>', methods=['GET'])
@require_auth
def get_history(ticker):
    """Get analysis history for a ticker (requires authentication)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, ticker, score, verdict, entry, stop_loss, target, 
                   entry_method, data_source, is_demo_data, created_at
            FROM analysis_results
            WHERE ticker = ?
            ORDER BY created_at DESC
            LIMIT 10
        ''', (ticker,))
        
        rows = cursor.fetchall()
        conn.close()
        
        history = []
        for row in rows:
            history.append({
                "id": row[0],
                "ticker": row[1],
                "score": row[2],
                "verdict": row[3],
                "entry": row[4],
                "stop": row[5],
                "target": row[6],
                "entry_method": row[7],
                "data_source": row[8],
                "is_demo_data": bool(row[9]),
                "analyzed_at": row[10]
            })
        
        return jsonify({"ticker": ticker, "history": history, "count": len(history)})
        
    except Exception as e:
        logger.error(f"History endpoint error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/report/<ticker>", methods=["GET"])
@require_auth
def get_report(ticker):
    """
    Unified & production-ready report endpoint.
    - Looks up by ticker or symbol
    - Returns full enriched metadata
    - Safely parses raw_data / indicators
    - Uses strongest parts of both prior implementations
    """
    try:
        logger.debug(f"Report requested for ticker: {ticker}")

        row = query_db(
            '''
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
                created_at,
                updated_at,
                analysis_source
            FROM analysis_results
            WHERE ticker = ? OR symbol = ?
            ORDER BY created_at DESC
            LIMIT 1
            ''',
            (ticker, ticker),
            one=True
        )

        if not row:
            logger.warning(f"No analysis found for: {ticker}")
            return jsonify({"error": "No analysis found for this ticker"}), 404

        # ---------- RAW DATA / INDICATORS PARSING ----------
        indicators = []
        raw_block = row.get("raw_data")

        if raw_block:
            try:
                indicators = json.loads(raw_block)
            except json.JSONDecodeError:
                try:
                    indicators = json.loads(raw_block.replace("'", '"'))
                except Exception as e:
                    logger.error(f"Failed to parse raw_data for {ticker}: {e}")
                    logger.error(f"Raw data sample: {str(raw_block)[:200]}...")
                    indicators = []

        # ---------- FINAL RESPONSE ----------
        response = {
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
            "indicators": indicators,
            "status": row["status"],
            "error_message": row["error_message"],
            "analyzed_at": row["created_at"],
            "updated_at": row["updated_at"],
            "analysis_source": row["analysis_source"]
        }

        logger.debug(f"Report response for {ticker}: {response}")
        return jsonify(response)

    except Exception as e:
        logger.error(f"Report endpoint error: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500




@app.route('/report/<ticker>/download', methods=['GET'])
@require_auth
def download_report(ticker):
    """Download analysis report as Excel (requires authentication)"""
    try:
        # Lazy load export function
        _, export_to_excel = get_analyze_ticker()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT ticker, score, verdict, entry, stop_loss, target, raw_data
            FROM analysis_results
            WHERE ticker = ?
            ORDER BY created_at DESC
            LIMIT 1
        ''', (ticker,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return jsonify({"error": "No analysis found"}), 404
        
        import json
        try:
            indicators = json.loads(row[6])
        except json.JSONDecodeError:
            logger.error(f"Failed to parse raw_data for {ticker} in download")
            indicators = []
        result = {
            "ticker": row[0],
            "score": row[1],
            "verdict": row[2],
            "entry": row[3],
            "stop": row[4],
            "target": row[5],
            "indicators": indicators
        }
        
        filepath = export_to_excel(result)
        return send_file(filepath, as_attachment=True, download_name=f"{ticker}_analysis.xlsx")
        
    except Exception as e:
        logger.error(f"Download endpoint error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/nse', methods=['GET'])
def get_nse_list():
    """Get NSE stock universe"""
    try:
        import json
        data_path = os.getenv('DATA_PATH', './data')
        filepath = os.path.join(data_path, 'nse_universe.json')
        
        if not os.path.exists(filepath):
            return jsonify({"symbols": [], "updated_on": None})
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        return jsonify(data)
        
    except Exception as e:
        logger.error(f"NSE endpoint error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/config', methods=['GET'])
def get_config():
    """Get configuration"""
    return jsonify({
        "type_bias": {
            "trend": 1.0,
            "momentum": 1.0,
            "volatility": 0.9,
            "volume": 0.9
        },
        "atr_multiplier": 1.5
    })

@app.route("/nse-stocks", methods=["GET"])
def get_nse_stocks():
    """
    Unified NSE stocks loader:
    - Uses _data_root() for consistent paths
    - Prefers JSON (metadata-rich)
    - Falls back to TXT (simple list)
    - Produces a consistent schema
    - Fully exception-safe
    """
    try:
        backend_root = _data_root()

        json_file = backend_root / "nse_stocks.json"
        txt_file = backend_root / "nse_stocks.txt"

        # ----------------------------------------------------
        # 1. Try JSON file first (full metadata)
        # ----------------------------------------------------
        if json_file.exists():
            try:
                data = json.loads(json_file.read_text(encoding="utf-8"))
                # enforce schema consistency
                if isinstance(data, dict) and "stocks" in data:
                    return jsonify({
                        "count": len(data.get("stocks", [])),
                        "stocks": data.get("stocks", [])
                    })
                return jsonify(data)
            except Exception as e:
                logger.error(f"Failed reading NSE JSON: {e}")
                # fallback continues

        # ----------------------------------------------------
        # 2. Fallback: TXT file (symbol list only)
        # ----------------------------------------------------
        if txt_file.exists():
            try:
                lines = [
                    line.strip()
                    for line in txt_file.read_text(encoding="utf-8").splitlines()
                    if line.strip()
                ]
                stocks = []
                for sym in lines:
                    # Ensure yahoo_symbol consistency
                    yahoo = sym if sym.endswith(".NS") else f"{sym}.NS"
                    stocks.append({
                        "symbol": yahoo.replace(".NS", ""),
                        "yahoo_symbol": yahoo,
                        "name": yahoo.replace(".NS", "")
                    })

                return jsonify({
                    "count": len(stocks),
                    "stocks": stocks
                })
            except Exception as e:
                logger.error(f"Failed processing NSE TXT file: {e}")

        # ----------------------------------------------------
        # 3. Nothing found
        # ----------------------------------------------------
        return jsonify({
            "error": "NSE stocks list not found.",
            "count": 0,
            "stocks": []
        }), 404

    except Exception as e:
        logger.error(f"get_nse_stocks error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/watchlist", methods=["GET", "POST", "DELETE"])
@require_auth
def watchlist():
    """
    Unified watchlist endpoint.
    - GET: List all watchlist items
    - POST: Add symbol (prevents duplicates)
    - DELETE: Remove symbol
    """

    try:
        # -------------------------
        # GET — fetch watchlist
        # -------------------------
        if request.method == "GET":
            rows = query_db("SELECT id, symbol, name FROM watchlist")
            return jsonify([
                {"id": r["id"], "symbol": r["symbol"], "name": r["name"]}
                for r in (rows or [])
            ])

        # -------------------------
        # POST — add symbol
        # -------------------------
        if request.method == "POST":
            data = request.get_json() or {}
            symbol = data.get("symbol")
            name   = data.get("name", "")

            if not symbol:
                return jsonify({"error": "Symbol is required"}), 400

            # Does it already exist?
            existing = query_db(
                "SELECT id FROM watchlist WHERE symbol = ?",
                (symbol,),
                one=True
            )
            if existing:
                return jsonify({
                    "error": "Symbol already in watchlist",
                    "already_exists": True
                }), 409

            # Insert (support optional created_at + user_id)
            try:
                execute_db(
                    """
                    INSERT INTO watchlist (symbol, name, created_at, user_id)
                    VALUES (?, ?, datetime('now'), 1)
                    """,
                    (symbol, name)
                )
            except Exception as insert_err:
                logger.error(f"Failed to insert watchlist item: {insert_err}")
                return jsonify({"error": "Failed to add to watchlist"}), 500

            return jsonify({
                "message": "Added to watchlist",
                "symbol": symbol
            }), 201

        # -------------------------
        # DELETE — remove symbol
        # -------------------------
        if request.method == "DELETE":
            data = request.get_json() or {}
            symbol = data.get("symbol")

            if not symbol:
                return jsonify({"error": "Symbol is required"}), 400

            execute_db(
                "DELETE FROM watchlist WHERE symbol = ?",
                (symbol,)
            )

            return jsonify({"message": "Removed from watchlist"})

        # -------------------------
        # Unsupported method safety
        # -------------------------
        return jsonify({"error": "Method not allowed"}), 405

    except Exception as e:
        logger.error(f"Watchlist endpoint error: {e}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500





# --- All-stocks (latest per symbol) ---
@app.route("/all-stocks", methods=["GET"])
def get_all_stocks():
    try:
        rows = query_db("""
            SELECT
                COALESCE(symbol, ticker) AS symbol,
                name,
                yahoo_symbol,
                status, 
                score,
                verdict,
                entry,
                stop_loss,
                target,
                entry_method,
                data_source,
                error_message,
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
                "status": r["status"],
                    "score": r["score"],
                    "verdict": r["verdict"],
                    "entry": r["entry"],
                    "stop_loss": r["stop_loss"],
                    "target": r["target"],
                "entry_method": r["entry_method"],
                "data_source": r["data_source"],
                "error_message": r["error_message"],
                    "analyzed_at": r["analyzed_at"],
                    "updated_at": r["updated_at"],
                    "analysis_source": r["analysis_source"]
                })
        return jsonify({"count": len(stocks), "stocks": stocks})
    except Exception as e:
        app.logger.exception("get_all_stocks error")
        return jsonify({"error": str(e)}), 500

# --- History per symbol ---
@app.route("/all-stocks/<symbol>/history", methods=["GET"])
def get_stock_history(symbol):
    try:
        rows = query_db("""
            SELECT
                ticker, 
		symbol, 
		name, 
		yahoo_symbol, 
		status, 
		score, 
		verdict, 
		entry, 
		stop_loss, 
		target,
                entry_method, 
		data_source, 
		is_demo_data, 
		raw_data, 		
		error_message, 
		created_at, 
		updated_at, 
		analysis_source
            FROM analysis_results
            WHERE COALESCE(symbol, ticker) = ?
            ORDER BY created_at DESC
            LIMIT 10
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
                    "created_at": r["created_at"],
                    "updated_at": r["updated_at"],
                    "analysis_source": r["analysis_source"]
                })
        return jsonify({
            "symbol": symbol,
            "name": rows[0]["name"] if rows else "",
            "yahoo_symbol": rows[0]["yahoo_symbol"] if rows else "",
            "current_status": rows[0]["status"] if rows else "unknown",
            "history": history,
            "count": len(history)
        })
    except Exception as e:
        app.logger.exception("get_stock_history error")
        return jsonify({"error": str(e)}), 500


@app.route("/analyze-all-stocks", methods=["POST"])
@require_auth
@limiter.limit("5 per hour")
def analyze_all_stocks():
    """
    Unified bulk-analysis endpoint.
    - Accepts manual symbol list
    - Or loads from DB latest rows
    - Or loads NSE files (json/txt)
    - Normalizes symbols
    - Starts threaded bulk analysis
    - Inserts pending rows if worker unavailable
    """

    try:
        from infrastructure.thread_tasks import start_bulk_analysis
        logger.info("=" * 70)
        logger.info("BULK ANALYSIS REQUEST (Unified Handler)")
        logger.info("=" * 70)

        data = request.get_json() or {}
        symbols = data.get("symbols", [])
        use_demo = data.get("use_demo_data", True)

        backend_root = _data_root()

        # ---------------------------------------------------
        # 1. GET SYMBOL LIST (PRIORITY-BASED)
        # ---------------------------------------------------

        if symbols:
            logger.info(f"Client supplied symbols: {len(symbols)}")
            raw_list = symbols

        else:
            # Try load from DB
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT yahoo_symbol 
                FROM all_stocks_analysis
                WHERE id IN (
                    SELECT MAX(id) 
                    FROM all_stocks_analysis 
                    GROUP BY symbol
                )
            """)
            db_symbols = [r[0] for r in cursor.fetchall()]
            conn.close()

            if db_symbols:
                logger.info(f"Loaded symbols from DB: {len(db_symbols)}")
                raw_list = db_symbols

            else:
                # Fallback to NSE files
                json_file = backend_root / "nse_stocks.json"
                txt_file = backend_root / "nse_stocks.txt"

                if json_file.exists():
                    logger.info("Loading NSE stock list from JSON")
                    with open(json_file, "r", encoding="utf-8") as f:
                        nse_data = json.load(f)
                    raw_list = [
                        stock.get("symbol") or stock.get("yahoo_symbol")
                        for stock in nse_data.get("stocks", [])
                    ]
                elif txt_file.exists():
                    logger.info("Loading NSE stock list from TXT")
                    raw_list = [
                        s.strip()
                        for s in txt_file.read_text(encoding="utf-8").splitlines()
                        if s.strip()
                    ]
                else:
                    return jsonify({
                        "error": "No symbols provided, DB empty, and NSE files not found."
                    }), 400

        if not raw_list:
            return jsonify({"error": "No symbols available for analysis"}), 400

        # Hard limit for safety
        if len(raw_list) > 1000:
            raw_list = raw_list[:1000]

        logger.info(f"Final symbol count: {len(raw_list)}")

        # ---------------------------------------------------
        # 2. NORMALIZE STOCK STRUCTURE
        # ---------------------------------------------------
        stocks = []
        for sym in raw_list:
            yahoo = sym if sym.endswith(".NS") else f"{sym}.NS"
            symbol_key = yahoo.replace(".NS", "")
            stocks.append({
                "symbol": symbol_key,
                "yahoo_symbol": yahoo,
                "name": ""
            })

        # ---------------------------------------------------
        # 3. START BACKGROUND BULK ANALYSIS
        # ---------------------------------------------------
        try:
            thread = threading.Thread(
                target=start_bulk_analysis,
                args=(stocks, use_demo, 5),     # 5 concurrent workers
                daemon=True,
                name="BulkAnalysisThread"
            )
            thread.start()
            started = True
        except Exception as e:
            logger.error("Fallback: start_bulk_analysis unavailable")
            logger.error(str(e))
            started = False

        # ---------------------------------------------------
        # 4. FALLBACK: INSERT PENDING ROWS IF WORKER FAILED
        # ---------------------------------------------------
        if not started:
            logger.info("Worker unavailable → inserting pending rows")
            now = datetime.now().isoformat()

            for st in stocks:
                try:
                    execute_db("""
                        INSERT INTO analysis_results 
                        (ticker, symbol, name, yahoo_symbol, score, verdict, status, created_at, updated_at, analysis_source)
                        VALUES (?, ?, ?, ?, 0.0, 'Pending', 'pending', ?, ?, 'bulk')
                    """, (
                        st["yahoo_symbol"],
                        st["symbol"],
                        st["name"],
                        st["yahoo_symbol"],
                        now, now
                    ))
                except Exception:
                    continue  # ignore duplicates

        # ---------------------------------------------------
        # 5. RESPONSE
        # ---------------------------------------------------
        return jsonify({
            "message": f"Bulk analysis started for {len(stocks)} stocks",
            "total": len(stocks),
            "symbols": [s["yahoo_symbol"] for s in stocks],
            "started_worker": started
        }), 202

    except Exception as e:
        logger.error("Unified bulk analysis error")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


@app.route("/all-stocks/progress", methods=["GET"])
@require_auth
def get_all_stocks_progress():
    try:
        # 1. Get total unique stocks
        total_row = query_db("""
            SELECT COUNT(DISTINCT COALESCE(symbol, ticker)) AS cnt
            FROM analysis_results
            WHERE analysis_source = 'bulk'
        """, (), one=True)

        total = total_row["cnt"] if total_row else 0

        # 2. Get latest status per symbol/ticker
        rows = query_db("""
            SELECT status, COUNT(*) AS cnt 
            FROM (
                SELECT COALESCE(symbol, ticker) AS sym, status
                FROM analysis_results
                WHERE analysis_source = 'bulk'
                AND id IN (
                    SELECT MAX(id)
                    FROM analysis_results
                    WHERE analysis_source = 'bulk'
                    GROUP BY COALESCE(symbol, ticker)
                )
            ) AS latest
            GROUP BY status
        """)

        # Build stats dictionary
        stats = {}
        if rows:
            for r in rows:
                stats[r["status"]] = r["cnt"]

        completed = stats.get("completed", 0)
        failed = stats.get("failed", 0)
        analyzing = stats.get("analyzing", 0)
        pending = stats.get("pending", 0)

        finished = completed + failed
        percentage = (finished / total * 100) if total > 0 else 0

        # 3. ETA calculation (from first version)
        remaining = total - finished
        estimated_seconds = (remaining / 5) * 10 if remaining > 0 else 0
        estimated_minutes = int(estimated_seconds / 60)

        if estimated_minutes > 60:
            hours = estimated_minutes // 60
            mins = estimated_minutes % 60
            eta_text = f"{hours}h {mins}m"
        elif estimated_minutes > 0:
            eta_text = f"{estimated_minutes} minutes"
        else:
            eta_text = "Less than a minute"

        # 4. Response
        return jsonify({
            "total": total,
            "completed": completed,
            "analyzing": analyzing,
            "failed": failed,
            "pending": pending,
            "percentage": round(percentage, 2),
            "estimated_time_remaining": eta_text,
            "is_analyzing": analyzing > 0
        })

    except Exception as e:
        app.logger.exception("get_all_stocks_progress error")
        return jsonify({"error": str(e)}), 500




@app.route("/initialize-all-stocks", methods=["POST"])
@require_auth
def initialize_all_stocks():
    """
    Initialize unified analysis_results table with NSE stocks (analysis_source='bulk').

    Behavior:
    - Default: idempotent. If any bulk rows exist, it returns 'already_initialized' = True.
    - Optional: force=true either as query param or in JSON body to remove existing bulk rows and reinitialize.
    - Accepts robust JSON file format; tolerant of older dumps.
    - Strict inserts (no INSERT OR IGNORE) but will catch duplicates and log them (so the endpoint doesn't crash).
    """
    try:
        logger.info("initialize_all_stocks called")

        # --- get force flag ---
        force = False
        # 1) query param
        if request.args.get("force", "").lower() in ("1", "true", "yes"):
            force = True
        # 2) json body override
        try:
            body = request.get_json(silent=True) or {}
            if body.get("force") is True:
                force = True
        except Exception:
            body = {}

        # --- locate data file ---
        data_path = os.getenv("DATA_PATH", str(Path(__file__).resolve().parent / "data"))
        json_file = Path(data_path) / "nse_stocks.json"
        txt_file = Path(data_path) / "nse_stocks.txt"

        if not json_file.exists() and not txt_file.exists():
            logger.warning("NSE stocks data file not found at %s or %s", json_file, txt_file)
            return jsonify({"error": "NSE stocks data file not found"}), 404

        # --- parse stocks from file (prefer json, fallback to txt) ---
        stocks_raw = []
        if json_file.exists():
            logger.info("Loading NSE stocks from JSON: %s", json_file)
            try:
                nse_data = json.loads(json_file.read_text(encoding="utf-8"))
                stocks_raw = nse_data.get("stocks", []) if isinstance(nse_data, dict) else []
            except Exception as e:
                logger.exception("Failed to parse JSON stocks file: %s", e)
                return jsonify({"error": "Failed to parse NSE JSON file", "details": str(e)}), 500
        elif txt_file.exists():
            logger.info("Loading NSE stocks from TXT: %s", txt_file)
            try:
                content = txt_file.read_text(encoding="utf-8")
                # Each line may be a symbol or "symbol,ticker" - tolerate simple lists
                lines = [l.strip() for l in content.splitlines() if l.strip()]
                for l in lines:
                    # if CSV-like, take first column as symbol
                    if "," in l:
                        parts = [p.strip() for p in l.split(",") if p.strip()]
                        stocks_raw.append({"symbol": parts[0], "yahoo_symbol": parts[0]})
                    else:
                        stocks_raw.append(l)
            except Exception as e:
                logger.exception("Failed to read TXT stocks file: %s", e)
                return jsonify({"error": "Failed to read NSE TXT file", "details": str(e)}), 500

        if not stocks_raw:
            return jsonify({"error": "No stocks found in data file"}), 404

        # --- connect db and check existing bulk rows ---
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM analysis_results WHERE analysis_source = 'bulk'")
        existing_bulk_count = cursor.fetchone()[0]

        if existing_bulk_count > 0 and not force:
            conn.close()
            logger.info("Bulk analysis already initialized with %d rows; aborting (use force=true to override)", existing_bulk_count)
            return jsonify({
                "message": "Already initialized",
                "count": existing_bulk_count,
                "already_initialized": True,
                "force_used": False
            }), 200

        # If force is True, delete existing bulk rows (destructive)
        if existing_bulk_count > 0 and force:
            logger.info("Force reinitialize requested - deleting existing %d bulk rows", existing_bulk_count)
            try:
                cursor.execute("DELETE FROM analysis_results WHERE analysis_source = 'bulk'")
                conn.commit()
            except Exception as e:
                logger.exception("Failed to delete existing bulk rows: %s", e)
                conn.close()
                return jsonify({"error": "Failed to clear existing bulk rows", "details": str(e)}), 500

        # --- normalize parsed stocks into canonical objects ---
        normalized_stocks = []
        for item in stocks_raw:
            # item may be dict or string
            if isinstance(item, dict):
                yahoo = (item.get("yahoo_symbol") or item.get("ticker") or item.get("symbol") or "").strip()
                symbol_field = (item.get("symbol") or item.get("ticker") or yahoo or "").strip()
                name = item.get("name", "") or ""
            else:
                # string: could be "RELIANCE.NS" or "RELIANCE"
                yahoo = str(item).strip()
                symbol_field = yahoo
                name = ""

            # ensure yahoo has .NS suffix for NSE tickers if it's likely an NSE symbol
            if yahoo and not yahoo.upper().endswith(".NS"):
                # If symbol_field already contains .NS, prefer that formatting
                if symbol_field.upper().endswith(".NS"):
                    yahoo = symbol_field
                else:
                    # append .NS (safe default)
                    yahoo = f"{yahoo}.NS" if ".NS" not in yahoo.upper() else yahoo

            # derive DB-stored symbol (no .NS)
            db_symbol = (symbol_field or yahoo).replace(".NS", "").replace(".ns", "")

            if not db_symbol or not yahoo:
                # skip any empty entries; log for visibility
                logger.debug("Skipping invalid stock entry during normalization: %s", item)
                continue

            normalized_stocks.append({
                "symbol": db_symbol,
                "yahoo_symbol": yahoo,
                "name": name
            })

        if not normalized_stocks:
            conn.close()
            return jsonify({"error": "No valid stocks found after normalization"}), 400

        # Hard safety limit (configurable): avoid blowing up DB by mistake
        MAX_INSERT = int(os.getenv("INITIALIZE_MAX_INSERT", "5000"))
        if len(normalized_stocks) > MAX_INSERT:
            logger.warning("Truncating stock list from %d to %d (safety limit)", len(normalized_stocks), MAX_INSERT)
            normalized_stocks = normalized_stocks[:MAX_INSERT]

        # --- insert rows strictly but safely (log duplicates) ---
        now = datetime.now().isoformat()
        inserted = 0
        skipped_duplicates = 0
        other_errors = []

        insert_sql = """
            INSERT INTO analysis_results
            (ticker, symbol, name, yahoo_symbol, score, verdict, status, created_at, updated_at, analysis_source)
            VALUES (?, ?, ?, ?, 0.0, 'Pending', 'pending', ?, ?, 'bulk')
        """

        for s in normalized_stocks:
            try:
                cursor.execute(insert_sql, (
                    s["yahoo_symbol"],
                    s["symbol"],
                    s.get("name", ""),
                    s["yahoo_symbol"],
                    now,
                    now
                ))
                inserted += 1
            except sqlite3.IntegrityError as ie:
                # likely a UNIQUE constraint violation; count as skipped duplicate but continue
                skipped_duplicates += 1
                logger.debug("Duplicate/IntegrityError for %s: %s", s, ie)
            except Exception as e:
                # log unexpected error and continue; collect a small sample for response
                logger.exception("Error inserting stock %s: %s", s, e)
                other_errors.append({"stock": s, "error": str(e)})
                # keep going - insertion of other rows should continue

        # commit once at end
        try:
            conn.commit()
        except Exception as e:
            logger.exception("Commit failed after inserts: %s", e)
            conn.close()
            return jsonify({"error": "DB commit failed", "details": str(e)}), 500

        conn.close()

        # --- final response ---
        total_candidates = len(normalized_stocks)
        response = {
            "message": "Initialization complete",
            "requested_count": total_candidates,
            "inserted": inserted,
            "skipped_duplicates": skipped_duplicates,
            "other_errors_count": len(other_errors),
            "force_used": force,
            "already_initialized_before": existing_bulk_count > 0 and not force is True
        }
        # include small diagnostics only when present
        if other_errors:
            response["other_errors_sample"] = other_errors[:10]

        logger.info("Initialization finished. requested=%d inserted=%d skipped=%d errors=%d",
                    total_candidates, inserted, skipped_duplicates, len(other_errors))

        return jsonify(response), 201

    except Exception as e:
        logger.exception("initialize_all_stocks error")
        return jsonify({"error": str(e)}), 500


# ---------------------------
# Run
# ---------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=os.getenv("FLASK_ENV") == "development")
