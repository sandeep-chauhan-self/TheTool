"""
Stocks routes - NSE stock list and bulk analysis
"""
import csv
import json
import uuid
from datetime import datetime
from pathlib import Path
from flask import Blueprint, jsonify, request
from utils.logger import setup_logger
from utils.api_utils import StandardizedErrorResponse, validate_request, RequestValidator
from database import query_db, execute_db, get_db_connection
from utils.db_utils import JobStateTransactions, get_job_status

logger = setup_logger()
bp = Blueprint("stocks", __name__, url_prefix="/api/stocks")


def _data_root() -> Path:
    """Get root data directory"""
    return Path(__file__).parent.parent / "data"


@bp.route("/all", methods=["GET"])
def get_all_nse_stocks():
    """
    Get ALL NSE stocks from CSV (2,192 stocks).
    Used for Add Stock Modal and All Stocks Analysis page.
    Returns stocks in pagination-friendly format.
    """
    try:
        csv_path = _data_root() / "nse_stocks_complete.csv"
        
        if not csv_path.exists():
            logger.warning(f"NSE CSV not found at {csv_path}")
            return StandardizedErrorResponse.format(
                "FILE_NOT_FOUND",
                "NSE stock list not available",
                404
            )
        
        # Get pagination params
        page = request.args.get("page", default=1, type=int)
        per_page = request.args.get("per_page", default=50, type=int)
        
        # Validate pagination
        if page < 1:
            page = 1
        if per_page < 1 or per_page > 500:
            per_page = 50
        
        stocks = []
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                stocks.append({
                    'symbol': row.get('symbol', '').strip(),
                    'name': row.get('name', '').strip(),
                    'yahoo_symbol': row.get('yahoo_symbol', '').strip(),
                    'sector': row.get('sector', '').strip(),
                    'industry': row.get('industry', '').strip()
                })
        
        # Calculate pagination
        total = len(stocks)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated = stocks[start_idx:end_idx]
        
        logger.info(f"Retrieved {len(paginated)} stocks (page {page}) from NSE list")
        return jsonify({
            "stocks": paginated,
            "count": len(paginated),
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page
        }), 200
        
    except Exception as e:
        logger.exception("get_all_nse_stocks error")
        return StandardizedErrorResponse.format(
            "NSE_LIST_ERROR",
            "Failed to get NSE list",
            500,
            {"error": str(e)}
        )


@bp.route("/nse", methods=["GET"])
def get_nse_list():
    """Get list of NSE stocks from CSV"""
    try:
        csv_path = _data_root() / "nse_stocks_complete.csv"
        
        if not csv_path.exists():
            logger.warning(f"NSE CSV not found at {csv_path}")
            return StandardizedErrorResponse.format(
                "FILE_NOT_FOUND",
                "NSE stock list not available",
                404
            )
        
        stocks = []
        with open(csv_path, "r", encoding="utf-8") as f:
            header = f.readline().strip().split(",")
            for line in f:
                parts = line.strip().split(",")
                if len(parts) >= len(header):
                    stocks.append(dict(zip(header, parts[:len(header)])))
        
        logger.info(f"Retrieved {len(stocks)} stocks from NSE list")
        return jsonify({
            "stocks": stocks,
            "count": len(stocks)
        }), 200
        
    except Exception as e:
        logger.exception("get_nse_list error")
        return StandardizedErrorResponse.format(
            "NSE_LIST_ERROR",
            "Failed to get NSE list",
            500,
            {"error": str(e)}
        )


@bp.route("/nse-stocks", methods=["GET"])
def get_nse_stocks():
    """Get NSE stocks from database"""
    try:
        stocks = query_db("""
            SELECT ticker, symbol, name, sector, industry, market_cap
            FROM nse_stocks
            ORDER BY market_cap DESC
            LIMIT ?
        """, (100,))
        
        return jsonify({
            "stocks": [dict(s) for s in stocks],
            "count": len(stocks)
        }), 200
        
    except Exception as e:
        logger.exception("get_nse_stocks error")
        return StandardizedErrorResponse.format(
            "NSE_STOCKS_ERROR",
            "Failed to get NSE stocks",
            500,
            {"error": str(e)}
        )


@bp.route("/all-stocks", methods=["GET"])
def get_all_stocks():
    """Get all analyzed stocks"""
    try:
        limit = request.args.get("limit", default=50, type=int)
        offset = request.args.get("offset", default=0, type=int)
        
        # Validate pagination params
        if limit < 1 or limit > 1000:
            limit = 50
        if offset < 0:
            offset = 0
        
        stocks = query_db("""
            SELECT DISTINCT ticker, symbol, MAX(created_at) as latest_analysis
            FROM analysis_results
            GROUP BY ticker, symbol
            ORDER BY latest_analysis DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))
        
        total = query_db(
            "SELECT COUNT(DISTINCT ticker) as count FROM analysis_results",
            one=True
        )
        
        return jsonify({
            "stocks": [dict(s) for s in stocks],
            "count": len(stocks),
            "total": total['count'] if total else 0,
            "limit": limit,
            "offset": offset
        }), 200
        
    except Exception as e:
        logger.exception("get_all_stocks error")
        return StandardizedErrorResponse.format(
            "ALL_STOCKS_ERROR",
            "Failed to get stocks",
            500,
            {"error": str(e)}
        )


@bp.route("/all-stocks/<symbol>/history", methods=["GET"])
def get_stock_history(symbol):
    """Get analysis history for a specific stock"""
    try:
        if not symbol or len(symbol.strip()) == 0:
            return StandardizedErrorResponse.format(
                "INVALID_SYMBOL",
                "Symbol cannot be empty",
                400
            )
        
        results = query_db("""
            SELECT id, ticker, symbol, analysis_data, created_at, job_id
            FROM analysis_results
            WHERE LOWER(symbol) = LOWER(?)
            ORDER BY created_at DESC
            LIMIT 50
        """, (symbol,))
        
        return jsonify({
            "symbol": symbol,
            "history": [dict(r) for r in results],
            "count": len(results)
        }), 200
        
    except Exception as e:
        logger.exception(f"get_stock_history error for {symbol}")
        return StandardizedErrorResponse.format(
            "HISTORY_ERROR",
            "Failed to get history",
            500,
            {"error": str(e)}
        )


@bp.route("/analyze-all-stocks", methods=["POST"])
def analyze_all_stocks():
    """
    Start bulk analysis of multiple stocks.
    
    Request body:
    {
        "symbols": ["TCS.NS", "INFY.NS"],  # Empty array [] means analyze ALL stocks
        "capital": 100000
    }
    """
    try:
        data = request.get_json() or {}
        
        # Validate request
        validated_data, error_response = validate_request(
            data,
            RequestValidator.BulkAnalyzeRequest
        )
        if error_response:
            return error_response
        
        symbols = validated_data.get("symbols") if validated_data else []
        if symbols is None:
            symbols = []
        capital = validated_data.get("capital", 100000) if validated_data else 100000
        
        # Handle empty array: means "analyze ALL stocks"
        if len(symbols) == 0:
            logger.info("Empty symbols array received - analyzing ALL stocks")
            try:
                # Get all stocks from database
                all_stocks = query_db("""
                    SELECT DISTINCT ticker FROM analysis_results
                    UNION
                    SELECT DISTINCT ticker FROM watchlist
                    ORDER BY ticker
                """)
                
                if not all_stocks:
                    return StandardizedErrorResponse.format(
                        "NO_STOCKS_FOUND",
                        "No stocks found to analyze. Add stocks to watchlist first.",
                        400
                    )
                
                symbols = [stock[0] for stock in all_stocks]
                logger.info(f"Found {len(symbols)} stocks to analyze: {symbols[:10]}...")
            except Exception as e:
                logger.error(f"Failed to get all stocks: {e}")
                return StandardizedErrorResponse.format(
                    "STOCK_LOOKUP_ERROR",
                    "Failed to retrieve stocks for analysis",
                    500,
                    {"error": str(e)}
                )
        
        # Create job ID
        job_id = str(uuid.uuid4())
        
        # Create job atomically
        created = JobStateTransactions.create_job_atomic(
            job_id=job_id,
            status="queued",
            total=len(symbols),
            description=f"Bulk analyze {len(symbols)} stock(s)"
        )
        
        if not created:
            return StandardizedErrorResponse.format(
                "JOB_DUPLICATE",
                "Job already exists",
                409,
                {"job_id": job_id}
            )
        
        # Start background job
        try:
            from infrastructure.thread_tasks import start_analysis_job
            start_analysis_job(job_id, symbols, None, capital, False)
        except Exception as e:
            logger.error(f"Failed to start bulk analysis job {job_id}: {e}")
            return StandardizedErrorResponse.format(
                "JOB_START_FAILED",
                "Failed to start bulk analysis",
                500,
                {"error": str(e)}
            )
        
        logger.info(f"Bulk analysis job created: {job_id} for {len(symbols)} stocks")
        
        return jsonify({
            "job_id": job_id,
            "status": "queued",
            "symbols": symbols,
            "capital": capital,
            "count": len(symbols)
        }), 201
        
    except Exception as e:
        logger.exception("analyze_all_stocks error")
        return StandardizedErrorResponse.format(
            "BULK_ANALYSIS_ERROR",
            "Bulk analysis failed",
            500,
            {"error": str(e)}
        )


@bp.route("/all-stocks/progress", methods=["GET"])
def get_all_stocks_progress():
    """Get progress of bulk analysis jobs"""
    try:
        # Get all non-completed jobs
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, job_id, status, total, completed, successful, errors
            FROM analysis_jobs
            WHERE status IN ('queued', 'processing')
            ORDER BY created_at DESC
            LIMIT 20
        """)
        
        jobs = []
        for row in cursor.fetchall():
            try:
                errors_list = json.loads(row[6]) if row[6] else []
            except (json.JSONDecodeError, TypeError):
                errors_list = []
            
            progress_pct = 0
            if row[4] > 0:
                progress_pct = int((row[4] / row[4]) * 100)
            
            jobs.append({
                "id": row[0],
                "job_id": row[1],
                "status": row[2],
                "total": row[3],
                "completed": row[4],
                "successful": row[5],
                "errors_count": len(errors_list),
                "progress_percent": progress_pct
            })
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "jobs": jobs,
            "active_count": len(jobs)
        }), 200
        
    except Exception as e:
        logger.exception("get_all_stocks_progress error")
        return StandardizedErrorResponse.format(
            "PROGRESS_ERROR",
            "Failed to get progress",
            500,
            {"error": str(e)}
        )


@bp.route("/initialize-all-stocks", methods=["POST"])
def initialize_all_stocks():
    """
    Initialize database with all NSE stocks.
    
    Request body:
    {
        "force": false
    }
    """
    try:
        data = request.get_json() or {}
        force = data.get("force", False)
        
        # Get NSE stocks CSV
        csv_path = _data_root() / "nse_stocks_complete.csv"
        
        if not csv_path.exists():
            return StandardizedErrorResponse.format(
                "FILE_NOT_FOUND",
                "NSE stock list not found",
                404
            )
        
        # Read and parse CSV
        stocks = []
        with open(csv_path, "r", encoding="utf-8") as f:
            header = f.readline().strip().split(",")
            for line in f:
                parts = line.strip().split(",")
                if len(parts) >= len(header):
                    stock_dict = dict(zip(header, parts[:len(header)]))
                    stocks.append(stock_dict)
        
        # Normalize tickers
        normalized_stocks = [
            {**s, "ticker": s.get("SYMBOL", "").strip()}
            for s in stocks
            if s.get("SYMBOL", "").strip()
        ]
        
        logger.info(f"Initializing {len(normalized_stocks)} stocks from CSV")
        
        # Check for existing data
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM analysis_results")
        existing_bulk_count = cursor.fetchone()[0]
        
        if existing_bulk_count > 0 and not force:
            cursor.close()
            conn.close()
            return jsonify({
                "message": "Stocks already initialized",
                "exists": True,
                "hint": "Use force=true to reinitialize"
            }), 200
        
        # Insert stocks
        inserted = 0
        skipped_duplicates = 0
        other_errors = []
        
        for stock in normalized_stocks:
            try:
                ticker = stock["ticker"]
                
                # Check if exists
                cursor.execute(
                    "SELECT id FROM analysis_results WHERE ticker = ? LIMIT 1",
                    (ticker,)
                )
                if cursor.fetchone():
                    skipped_duplicates += 1
                    continue
                
                # Insert stock
                cursor.execute(
                    """
                    INSERT INTO analysis_results (ticker, symbol, analysis_data, status)
                    VALUES (?, ?, ?, ?)
                    """,
                    (ticker, stock.get("symbol", ""), "{}", "initialized")
                )
                inserted += 1
                
            except Exception as e:
                other_errors.append(str(e))
                if len(other_errors) > 100:
                    break
        
        try:
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"DB commit failed: {e}")
            return jsonify({"error": "DB commit failed", "details": str(e)}), 500
        
        conn.close()
        
        # Final response
        total_candidates = len(normalized_stocks)
        response = {
            "message": "Initialization complete",
            "requested_count": total_candidates,
            "inserted": inserted,
            "skipped_duplicates": skipped_duplicates,
            "other_errors_count": len(other_errors),
            "force_used": force,
            "already_initialized_before": existing_bulk_count > 0 and not force
        }
        
        if other_errors:
            response["other_errors_sample"] = other_errors[:10]
        
        logger.info(
            f"Initialization finished. requested={total_candidates} "
            f"inserted={inserted} skipped={skipped_duplicates} errors={len(other_errors)}"
        )
        
        return jsonify(response), 201
        
    except Exception as e:
        logger.exception("initialize_all_stocks error")
        return StandardizedErrorResponse.format(
            "INIT_ERROR",
            "Initialization failed",
            500,
            {"error": str(e)}
        )
