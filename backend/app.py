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
from auth import require_auth, MASTER_API_KEY
from config import config

# SECURITY FIX (ISSUE_023): Optional rate limiting (graceful degradation)
try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    LIMITER_AVAILABLE = True
except ImportError:
    LIMITER_AVAILABLE = False
    print("WARNING: flask-limiter not installed. Rate limiting disabled.")
    print("Install with: pip install Flask-Limiter>=3.5.0")

load_dotenv()

app = Flask(__name__)

# SECURITY FIX (ISSUE_021): Added Authorization header to CORS
CORS(app, resources={
    r"/*": {
        "origins": config.CORS_ORIGINS,
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "X-API-Key"]
    }
})

# SECURITY FIX (ISSUE_023): Rate limiting to prevent DoS attacks
if LIMITER_AVAILABLE and config.RATE_LIMIT_ENABLED:
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=[f"{config.RATE_LIMIT_PER_MINUTE} per minute"],
        storage_uri="memory://",
    )
else:
    # Mock limiter for graceful degradation
    class MockLimiter:
        @staticmethod
        def limit(limit_value):
            def decorator(f):
                return f
            return decorator
    limiter = MockLimiter()

# Lazy imports - only load when needed
def get_logger():
    from utils.infrastructure.logging import setup_logger
    return setup_logger()

def get_analyze_ticker():
    from utils.analysis.orchestrator import analyze_ticker, export_to_excel
    return analyze_ticker, export_to_excel

# Setup logging with DEBUG level
logger = get_logger()
logger.setLevel('DEBUG')  # Enable debug logging

# Also log to console for development
import sys
console_handler = logger.handlers[0] if logger.handlers else None
if not console_handler or not isinstance(console_handler, type(sys.stdout)):
    import logging
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.DEBUG)
    formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
    console.setFormatter(formatter)
    logger.addHandler(console)
    
logger.info("=" * 60)
logger.info("FLASK APPLICATION STARTING")
logger.info("Async Job Processing with Threading (Redis-free)")
logger.info("=" * 60)
logger.info(f"MASTER API KEY: {MASTER_API_KEY}")
logger.info("SECURITY: API authentication enabled for all endpoints")
logger.info("=" * 60)

# Initialize database (lightweight operation)
from database import init_db, get_db_connection
init_db()

# Start background scheduler (lazy - will be imported on first use)
_scheduler_started = False
def ensure_scheduler():
    global _scheduler_started
    if not _scheduler_started:
        from utils.infrastructure.scheduler import start_scheduler
        start_scheduler()
        _scheduler_started = True

# Job storage
jobs = {}
MAX_THREADS = min(10, (os.cpu_count() or 1) * 2)

@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint (public - no authentication required).
    Used by load balancers and monitoring systems.
    """
    from cache import get_cache_stats
    
    uptime = (datetime.now() - app.config.get('start_time', datetime.now())).total_seconds()
    cache_stats = get_cache_stats()
    
    return jsonify({
        "status": "ok",
        "uptime": uptime,
        "authentication": "enabled",
        "cache": cache_stats
    })

@app.route('/analyze', methods=['POST'])
@require_auth
@limiter.limit(f"{config.ANALYZE_RATE_LIMIT} per minute")
def analyze():
    """
    Analyze one or more tickers (async with Threading).
    
    SECURITY FIX (ISSUE_021): Requires API key authentication.
    SECURITY FIX (ISSUE_022): Input validation using Pydantic schemas.
    SECURITY FIX (ISSUE_023): Rate limited to prevent DoS attacks.
    """
    try:
        logger.info("=" * 50)
        logger.info("NEW ANALYSIS REQUEST")
        logger.info("=" * 50)
        
        from infrastructure.thread_tasks import start_analysis_job
        from models.validation import TickerAnalysisRequest, validate_request
        
        data = request.get_json()
        logger.debug(f"Request data: {data}")
        
        # Validate request data (ISSUE_022)
        validated, error = validate_request(TickerAnalysisRequest, data)
        if error:
            logger.error(f"Validation failed: {error}")
            return jsonify(error), 400
        
        tickers = validated.tickers
        indicators = validated.indicators
        capital = validated.capital
        use_demo = validated.use_demo_data
        
        job_id = str(uuid.uuid4())
        logger.info(f"Generated job_id: {job_id}")
        logger.info(f"Tickers to analyze: {tickers}")
        logger.info(f"Total stocks: {len(tickers)}")
        logger.info(f"Use demo data: {use_demo}")
        
        # Create job record in database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO analysis_jobs 
            (job_id, status, total, completed, progress, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            job_id,
            'queued',
            len(tickers),
            0,
            0,
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
        conn.commit()
        conn.close()
        
        logger.info(f"Job record created in database: {job_id}")
        
        # Start background thread
        logger.info(f"Starting background thread for job {job_id}")
        try:
            success = start_analysis_job(job_id, tickers, indicators, capital, use_demo)
            if success:
                logger.info(f"Background thread started successfully: {job_id}")
            else:
                raise Exception("Failed to start background thread")
        except Exception as thread_error:
            logger.error(f"Failed to start background thread: {thread_error}")
            logger.error(traceback.format_exc())
            # Update job status to failed
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE analysis_jobs
                SET status = 'failed', errors = ?
                WHERE job_id = ?
            ''', (json.dumps([{"error": f"Thread start failed: {str(thread_error)}"}]), job_id))
            conn.commit()
            conn.close()
            raise
        
        response = {
            "status": "queued",
            "job_id": job_id,
            "count": len(tickers),
            "message": "Analysis job started. Use /status/{job_id} to track progress."
        }
        logger.info(f"Returning response: {response}")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Analysis endpoint error: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route('/status/<job_id>', methods=['GET'])
@require_auth
def get_status(job_id):
    """Get analysis job status (requires authentication)"""
    try:
        logger.debug(f"Status check requested for job_id: {job_id}")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT job_id, status, progress, total, completed, errors, created_at, updated_at
            FROM analysis_jobs
            WHERE job_id = ?
        ''', (job_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            logger.warning(f"Job not found: {job_id}")
            return jsonify({"error": "Job not found"}), 404
        
        # Parse errors safely
        errors_data = []
        if row[5]:
            try:
                errors_data = json.loads(row[5])
            except json.JSONDecodeError as je:
                logger.error(f"Failed to parse errors JSON for job {job_id}: {je}")
                errors_data = []
        
        response = {
            "job_id": row[0],
            "status": row[1],
            "progress": row[2] or 0,
            "total": row[3] or 0,
            "completed": row[4] or 0,
            "errors": errors_data,
            "created_at": row[6],
            "updated_at": row[7]
        }
        
        logger.debug(f"Status response for {job_id}: {response}")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Status endpoint error: {str(e)}")
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

@app.route('/report/<ticker>', methods=['GET'])
@require_auth
def get_report(ticker):
    """Get analysis report for a specific ticker (requires authentication)"""
    try:
        logger.debug(f"Report requested for ticker: {ticker}")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT ticker, score, verdict, entry, stop_loss, target, raw_data, created_at
            FROM analysis_results
            WHERE ticker = ?
            ORDER BY created_at DESC
            LIMIT 1
        ''', (ticker,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            logger.warning(f"No analysis found for ticker: {ticker}")
            return jsonify({"error": "No analysis found for this ticker"}), 404
        
        # Parse raw_data safely
        indicators = []
        if row[6]:
            try:
                # Try to parse as JSON first
                indicators = json.loads(row[6])
            except json.JSONDecodeError:
                try:
                    # Try with single quotes replaced
                    indicators = json.loads(row[6].replace("'", '"'))
                except json.JSONDecodeError as je:
                    logger.error(f"Failed to parse indicators JSON for {ticker}: {je}")
                    logger.error(f"Raw data: {row[6][:200]}...")  # Log first 200 chars
                    indicators = []
        
        response = {
            "ticker": row[0],
            "score": row[1],
            "verdict": row[2],
            "entry": row[3],
            "stop": row[4],
            "target": row[5],
            "indicators": indicators,
            "analyzed_at": row[7]
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
        result = {
            "ticker": row[0],
            "score": row[1],
            "verdict": row[2],
            "entry": row[3],
            "stop": row[4],
            "target": row[5],
            "indicators": json.loads(row[6].replace("'", '"'))
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

@app.route('/nse-stocks', methods=['GET'])
def get_nse_stocks():
    """Get list of all NSE stocks"""
    try:
        import os
        from pathlib import Path
        
        # Path to NSE stocks file
        stocks_file = Path(__file__).parent / 'data' / 'nse_stocks.txt'
        json_file = Path(__file__).parent / 'data' / 'nse_stocks.json'
        
        # If JSON file exists, return it (includes metadata)
        if json_file.exists():
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return jsonify(data)
        
        # Fallback: read TXT file
        if stocks_file.exists():
            with open(stocks_file, 'r', encoding='utf-8') as f:
                stocks = [line.strip() for line in f if line.strip()]
            return jsonify({
                'count': len(stocks),
                'stocks': [{'symbol': s, 'yahoo_symbol': s, 'name': s.replace('.NS', '')} for s in stocks]
            })
        
        # If file doesn't exist, return error
        return jsonify({
            'error': 'NSE stocks list not found. Run fetch_nse_stocks.py first.',
            'count': 0,
            'stocks': []
        }), 404
        
    except Exception as e:
        logger.error(f"NSE stocks endpoint error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/watchlist', methods=['GET', 'POST', 'DELETE'])
@require_auth
def manage_watchlist() -> Union[Response, Tuple[Response, int]]:
    """Manage watchlist (requires authentication)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if request.method == 'GET':
            cursor.execute('SELECT id, symbol, name FROM watchlist')
            rows = cursor.fetchall()
            conn.close()
            return jsonify([{"id": r[0], "symbol": r[1], "name": r[2]} for r in rows])
        
        elif request.method == 'POST':
            data = request.get_json()
            symbol = data.get('symbol')
            name = data.get('name', '')
            
            if not symbol:
                return jsonify({"error": "Symbol is required"}), 400
            
            # Check if symbol already exists
            cursor.execute('SELECT id FROM watchlist WHERE symbol = ?', (symbol,))
            existing = cursor.fetchone()
            
            if existing:
                conn.close()
                return jsonify({"error": "Symbol already in watchlist", "already_exists": True}), 409
            
            cursor.execute('INSERT INTO watchlist (symbol, name) VALUES (?, ?)', (symbol, name))
            conn.commit()
            conn.close()
            return jsonify({"message": "Added to watchlist", "symbol": symbol}), 201
        
        elif request.method == 'DELETE':
            data = request.get_json()
            symbol = data.get('symbol')
            
            cursor.execute('DELETE FROM watchlist WHERE symbol = ?', (symbol,))
            conn.commit()
            conn.close()
            return jsonify({"message": "Removed from watchlist"})
        
        # Explicit return for any unhandled methods
        conn.close()
        return jsonify({"error": "Method not allowed"}), 405
        
    except Exception as e:
        logger.error(f"Watchlist endpoint error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/initialize-all-stocks', methods=['POST'])
@require_auth
def initialize_all_stocks():
    """
    Initialize UNIFIED analysis_results table with all NSE stocks
    Only runs if table is empty for bulk analysis (idempotent)
    
    MIGRATION NOTE: Now inserts into unified analysis_results table with analysis_source='bulk'
    """
    try:
        logger.info("Initialize all stocks requested")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if already initialized (check bulk analysis records)
        cursor.execute("SELECT COUNT(*) FROM analysis_results WHERE analysis_source = 'bulk'")
        count = cursor.fetchone()[0]
        
        if count > 0:
            logger.info(f"Already initialized with {count} bulk stocks")
            conn.close()
            return jsonify({
                "message": "Already initialized",
                "count": count,
                "already_initialized": True
            })
        
        # Load NSE stocks from JSON file
        nse_stocks_path = os.path.join(os.getenv('DATA_PATH', './data'), 'nse_stocks.json')
        
        if not os.path.exists(nse_stocks_path):
            return jsonify({"error": "NSE stocks data file not found"}), 404
        
        with open(nse_stocks_path, 'r', encoding='utf-8') as f:
            nse_data = json.load(f)
        
        stocks = nse_data.get('stocks', [])
        
        if not stocks:
            return jsonify({"error": "No stocks found in data file"}), 404
        
        # Insert all stocks with status='pending' into UNIFIED table
        from datetime import datetime
        now = datetime.now().isoformat()
        
        for stock in stocks:
            cursor.execute('''
                INSERT INTO analysis_results 
                (ticker, symbol, name, yahoo_symbol, score, verdict, status, 
                 created_at, updated_at, analysis_source) 
                VALUES (?, ?, ?, ?, 0.0, 'Pending', 'pending', ?, ?, 'bulk')
            ''', (stock['yahoo_symbol'], stock['symbol'], stock['name'], 
                  stock['yahoo_symbol'], now, now))
        
        conn.commit()
        inserted_count = len(stocks)
        conn.close()
        
        logger.info(f"Initialized {inserted_count} stocks")
        
        return jsonify({
            "message": f"Initialized {inserted_count} stocks",
            "count": inserted_count
        }), 201
        
    except Exception as e:
        logger.error(f"Initialize all stocks error: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


@app.route('/all-stocks', methods=['GET'])
@require_auth
def get_all_stocks():
    """
    Get all stocks from UNIFIED analysis_results table (analysis_source='bulk')
    Returns latest analysis for each stock
    
    MIGRATION NOTE: Now queries unified analysis_results table instead of 
    deprecated all_stocks_analysis table.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get latest record for each stock from UNIFIED table (bulk analyses only)
        cursor.execute('''
            SELECT 
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
                error_message,
                created_at,
                updated_at
            FROM analysis_results
            WHERE analysis_source = 'bulk'
            AND id IN (
                SELECT MAX(id) 
                FROM analysis_results 
                WHERE analysis_source = 'bulk'
                GROUP BY symbol
            )
            ORDER BY symbol ASC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        stocks = []
        for row in rows:
            has_analysis = row[4] is not None  # Check if score exists
            
            stock = {
                "symbol": row[0],
                "name": row[1],
                "yahoo_symbol": row[2],
                "status": row[3],
                "score": row[4],
                "verdict": row[5],
                "entry": row[6],
                "stop_loss": row[7],
                "target": row[8],
                "entry_method": row[9],
                "data_source": row[10],
                "error_message": row[11],
                "analyzed_at": row[12],
                "updated_at": row[13],
                "has_analysis": has_analysis
            }
            stocks.append(stock)
        
        return jsonify({
            "count": len(stocks),
            "stocks": stocks
        })
        
    except Exception as e:
        logger.error(f"Get all stocks error: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


@app.route('/all-stocks/<symbol>/history', methods=['GET'])
@require_auth
def get_stock_history(symbol):
    """
    Get analysis history for a specific stock (last 10 analyses from bulk analysis)
    
    MIGRATION NOTE: Now queries unified analysis_results table with analysis_source='bulk'
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                id,
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
                created_at
            FROM analysis_results
            WHERE symbol = ? AND analysis_source = 'bulk'
            ORDER BY created_at DESC
            LIMIT 10
        ''', (symbol,))
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return jsonify({"error": "No analysis found for this stock"}), 404
        
        history = []
        current_status = rows[0][4]  # Latest status
        
        for row in rows:
            # Parse raw_data if exists
            indicators = []
            if row[13]:
                try:
                    indicators = json.loads(row[13])
                except:
                    try:
                        indicators = json.loads(row[13].replace("'", '"'))
                    except:
                        indicators = []
            
            history.append({
                "id": row[0],
                "score": row[5],
                "verdict": row[6],
                "entry": row[7],
                "stop_loss": row[8],
                "target": row[9],
                "entry_method": row[10],
                "data_source": row[11],
                "is_demo_data": bool(row[12]),
                "indicators": indicators,
                "error_message": row[14],
                "analyzed_at": row[15]
            })
        
        return jsonify({
            "symbol": symbol,
            "name": rows[0][2],
            "yahoo_symbol": rows[0][3],
            "current_status": current_status,
            "history": history,
            "count": len(history)
        })
        
    except Exception as e:
        logger.error(f"Get stock history error: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


@app.route('/all-stocks/progress', methods=['GET'])
@require_auth
def get_all_stocks_progress():
    """
    Get real-time progress of bulk analysis
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Count stocks by status
        cursor.execute('''
            SELECT status, COUNT(*) 
            FROM (
                SELECT symbol, status
                FROM all_stocks_analysis
                WHERE id IN (
                    SELECT MAX(id) 
                    FROM all_stocks_analysis 
                    GROUP BY symbol
                )
            )
            GROUP BY status
        ''')
        
        rows = cursor.fetchall()
        stats = {row[0]: row[1] for row in rows}
        
        # Get total count
        cursor.execute('''
            SELECT COUNT(DISTINCT symbol) 
            FROM all_stocks_analysis
        ''')
        total = cursor.fetchone()[0]
        
        conn.close()
        
        completed = stats.get('completed', 0)
        failed = stats.get('failed', 0)
        analyzing = stats.get('analyzing', 0)
        pending = stats.get('pending', 0)
        
        finished = completed + failed
        percentage = (finished / total * 100) if total > 0 else 0
        
        # Simple ETA calculation (rough estimate)
        # Assume ~10 seconds per stock with 5 parallel threads
        remaining = total - finished
        estimated_seconds = (remaining / 5) * 10 if remaining > 0 else 0
        estimated_minutes = int(estimated_seconds / 60)
        
        eta_text = ""
        if estimated_minutes > 60:
            hours = estimated_minutes // 60
            mins = estimated_minutes % 60
            eta_text = f"{hours}h {mins}m"
        elif estimated_minutes > 0:
            eta_text = f"{estimated_minutes} minutes"
        else:
            eta_text = "Less than a minute"
        
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
        logger.error(f"Get progress error: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


@app.route('/analyze-all-stocks', methods=['POST'])
@require_auth
@limiter.limit("5 per hour")
def analyze_all_stocks():
    """
    Trigger bulk analysis for all or selected stocks.
    SECURITY: Very resource-intensive, rate limited to 5 per hour.
    """
    try:
        from infrastructure.thread_tasks import start_bulk_analysis
        
        data = request.get_json() or {}
        symbols = data.get('symbols', [])  # If empty, analyze all
        use_demo = data.get('use_demo_data', True)
        
        logger.info("=" * 60)
        logger.info("BULK ANALYSIS REQUEST")
        logger.info(f"Selected symbols: {len(symbols) if symbols else 'ALL'}")
        logger.info("=" * 60)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get stocks to analyze
        if symbols:
            # Analyze selected stocks
            placeholders = ','.join('?' * len(symbols))
            cursor.execute(f'''
                SELECT symbol, name, yahoo_symbol
                FROM all_stocks_analysis
                WHERE yahoo_symbol IN ({placeholders})
                AND id IN (
                    SELECT MAX(id) FROM all_stocks_analysis GROUP BY symbol
                )
            ''', symbols)
        else:
            # Analyze all stocks
            cursor.execute('''
                SELECT symbol, name, yahoo_symbol
                FROM all_stocks_analysis
                WHERE id IN (
                    SELECT MAX(id) FROM all_stocks_analysis GROUP BY symbol
                )
            ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return jsonify({"error": "No stocks found to analyze"}), 404
        
        stocks = [{"symbol": r[0], "name": r[1], "yahoo_symbol": r[2]} for r in rows]
        
        # Start analysis in background thread
        thread = threading.Thread(
            target=start_bulk_analysis,
            args=(stocks, use_demo, 5),  # 5 concurrent workers
            daemon=True,
            name="BulkAnalysisThread"
        )
        thread.start()
        
        logger.info(f"Started bulk analysis for {len(stocks)} stocks")
        
        return jsonify({
            "message": f"Bulk analysis started for {len(stocks)} stocks",
            "total": len(stocks),
            "symbols": [s['yahoo_symbol'] for s in stocks]
        }), 202
        
    except Exception as e:
        logger.error(f"Bulk analysis error: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.config['start_time'] = datetime.now()
    app.run(host='0.0.0.0', port=5000, debug=os.getenv('FLASK_ENV') == 'development')
