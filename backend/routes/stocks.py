"""
Stocks routes - NSE stock list and bulk analysis
"""
import csv
import json
import uuid
import time
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
            SELECT id, ticker, symbol, verdict, score, entry, stop_loss, target, created_at
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


def _get_active_job_for_symbols(symbols: list) -> dict:
    """
    Check if an identical job is already running for the exact same symbol set.
    Returns the existing job info or None if safe to create new job.
    
    Only considers jobs "duplicate" if:
    - Same symbols (in any order) - normalized by uppercase + trim
    - Status is 'queued' or 'processing'
    - Within last 5 minutes (to avoid stale locks)
    
    Different symbol sets are NOT blocked and can run concurrently.
    """
    try:
        # Normalize requested symbols: uppercase, trim, sort
        normalized_symbols = sorted([s.upper().strip() for s in symbols])
        requested_json = json.dumps(normalized_symbols)
        
        # Get active jobs from last 5 minutes
        from datetime import datetime, timedelta
        five_min_ago = (datetime.now() - timedelta(minutes=5)).isoformat()
        
        active_jobs = query_db("""
            SELECT job_id, status, total, completed, created_at, tickers_json
            FROM analysis_jobs
            WHERE status IN ('queued', 'processing')
              AND created_at > ?
            ORDER BY created_at DESC
            LIMIT 20
        """, (five_min_ago,))
        
        if not active_jobs:
            return None
        
        # Check each active job for exact symbol match
        for job_id, status, total, completed, created_at, tickers_json in active_jobs:
            # Skip jobs with no tickers_json (shouldn't happen, but be safe)
            if not tickers_json:
                continue
            
            try:
                job_symbols = json.loads(tickers_json)
                # Compare normalized symbol sets
                if job_symbols == normalized_symbols:
                    logger.info(f"Found active job {job_id} with matching symbols, status {status}")
                    return {
                        "job_id": job_id,
                        "status": status,
                        "total": total,
                        "completed": completed,
                        "created_at": created_at
                    }
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse tickers_json for job {job_id}")
                continue
        
        # No matching job found
        return None
    except Exception as e:
        logger.error(f"Error checking for active jobs: {e}")
        return None


@bp.route("/analyze-all-stocks", methods=["POST"])
def analyze_all_stocks():
    """
    Start bulk analysis of multiple stocks.
    
    Request body:
    {
        "symbols": ["TCS.NS", "INFY.NS"],  # Empty array [] means analyze ALL stocks
        "capital": 100000,
        "force": false  # Set true to bypass duplicate check and force new analysis
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
        force = data.get("force", False)  # Force new job even if one is running
        
        # Handle empty array: means "analyze ALL stocks"
        if len(symbols) == 0:
            logger.info("Empty symbols array received - analyzing ALL stocks")
            try:
                # Get all stocks from database
                all_stocks = query_db("""
                    SELECT DISTINCT ticker FROM analysis_results
                    UNION
                    SELECT DISTINCT symbol AS ticker FROM watchlist
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
        
        # Check for duplicate/active jobs (unless force=true)
        if not force:
            active_job = _get_active_job_for_symbols(symbols)
            if active_job:
                logger.info(f"Duplicate job request detected. Returning existing job {active_job['job_id']}")
                return jsonify({
                    "job_id": active_job["job_id"],
                    "status": active_job["status"],
                    "is_duplicate": True,
                    "message": "Analysis already running for these symbols",
                    "total": active_job["total"],
                    "completed": active_job["completed"],
                    "symbols": symbols,
                    "capital": capital,
                    "count": len(symbols)
                }), 200
        
        # Create job ID
        job_id = str(uuid.uuid4())
        logger.info(f"Creating new analysis job {job_id} for {len(symbols)} symbols")
        
        # Create job atomically with retries on db lock
        max_retries = 3
        created = False
        for attempt in range(max_retries):
            try:
                created = JobStateTransactions.create_job_atomic(
                    job_id=job_id,
                    status="queued",
                    total=len(symbols),
                    description=f"Bulk analyze {len(symbols)} stock(s)",
                    tickers=symbols  # Include symbols for duplicate detection
                )
                if created:
                    break
                else:
                    # Job creation returned False, likely due to race condition
                    # Retry with fresh check in case another thread just created it
                    logger.warning(f"Job creation failed (attempt {attempt + 1}/{max_retries}), retrying...")
                    time.sleep(0.1 * (attempt + 1))  # Exponential backoff
                    
                    # Check if job was created by concurrent request
                    if attempt == max_retries - 1:
                        try:
                            active_job = _get_active_job_for_symbols(symbols)
                            if active_job:
                                logger.info(f"Found existing job {active_job['job_id']} created by concurrent request")
                                return jsonify({
                                    "job_id": active_job["job_id"],
                                    "status": active_job["status"],
                                    "is_duplicate": True,
                                    "message": "Analysis already running for these symbols",
                                    "total": active_job["total"],
                                    "completed": active_job["completed"],
                                    "symbols": symbols,
                                    "capital": capital,
                                    "count": len(symbols)
                                }), 200
                        except Exception as check_err:
                            logger.warning(f"Could not check for existing job on final retry: {check_err}")
                            # Continue to error response
            except Exception as e:
                logger.error(f"Exception during job creation (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    return StandardizedErrorResponse.format(
                        "JOB_CREATION_FAILED",
                        "Failed to create analysis job",
                        500,
                        {"error": str(e), "job_id": job_id}
                    )
        
        if not created:
            return StandardizedErrorResponse.format(
                "JOB_CREATION_FAILED",
                "Failed to create analysis job after retries",
                500,
                {"job_id": job_id}
            )
        
        # Start background job - MUST happen after successful db insert
        start_success = False
        try:
            from infrastructure.thread_tasks import start_analysis_job
            start_success = start_analysis_job(job_id, symbols, None, capital, False)
            if not start_success:
                logger.error(f"Failed to start thread for job {job_id}")
        except Exception as e:
            logger.error(f"Failed to start bulk analysis job {job_id}: {e}")
        
        logger.info(f"Bulk analysis job {job_id} created and started for {len(symbols)} stocks")
        
        return jsonify({
            "job_id": job_id,
            "status": "queued",
            "symbols": symbols,
            "capital": capital,
            "count": len(symbols),
            "thread_started": start_success
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
        from config import config
        from datetime import datetime, timedelta
        
        # Get all non-completed jobs (queued/processing)
        jobs_rows = query_db("""
            SELECT job_id, status, total, completed, successful, errors
            FROM analysis_jobs
            WHERE status IN ('queued', 'processing')
            ORDER BY created_at DESC
            LIMIT 20
        """)
        
        # Calculate cutoff time for completed jobs (last 1 hour)
        cutoff_time = (datetime.now() - timedelta(hours=1)).isoformat()
        
        # Also check for recently completed jobs (last 1 hour) - for continuity
        if config.DATABASE_TYPE == 'postgres':
            completed_jobs_rows = query_db("""
                SELECT job_id, status, total, completed, successful, errors
                FROM analysis_jobs
                WHERE status IN ('completed', 'cancelled', 'failed')
                AND completed_at > %s
                ORDER BY completed_at DESC
                LIMIT 5
            """, (cutoff_time,))
        else:
            completed_jobs_rows = query_db("""
                SELECT job_id, status, total, completed, successful, errors
                FROM analysis_jobs
                WHERE status IN ('completed', 'cancelled', 'failed')
                AND completed_at > ?
                ORDER BY completed_at DESC
                LIMIT 5
            """, (cutoff_time,))
        
        jobs = []
        total_jobs = 0
        total_completed = 0
        total_successful = 0
        total_analyzing = 0
        total_errors = 0
        
        # Process active jobs
        for row in jobs_rows:
            try:
                errors_list = json.loads(row[5]) if row[5] else []
            except (json.JSONDecodeError, TypeError):
                errors_list = []
            
            progress_pct = 0
            if row[3] > 0 and row[2] > 0:
                progress_pct = int((row[3] / row[2]) * 100)
            
            jobs.append({
                "job_id": row[0],
                "status": row[1],
                "total": row[2],
                "completed": row[3],
                "successful": row[4],
                "errors_count": len(errors_list),
                "progress_percent": progress_pct
            })
            
            total_jobs += 1
            total_completed += row[3]
            total_successful += row[4]
            total_analyzing += row[2] - row[3]  # pending = total - completed
            total_errors += len(errors_list)
        
        # Process completed jobs (for continuity during final polling)
        for row in completed_jobs_rows:
            try:
                errors_list = json.loads(row[5]) if row[5] else []
            except (json.JSONDecodeError, TypeError):
                errors_list = []
            
            # Only add if not already in active jobs
            if not any(j['job_id'] == row[0] for j in jobs):
                progress_pct = 100 if row[1] == 'completed' else 0
                
                jobs.append({
                    "job_id": row[0],
                    "status": row[1],
                    "total": row[2],
                    "completed": row[3],
                    "successful": row[4],
                    "errors_count": len(errors_list),
                    "progress_percent": progress_pct
                })
                
                total_jobs += 1
                total_completed += row[3]
                total_successful += row[4]
                total_errors += len(errors_list)
        
        # Calculate overall progress
        is_analyzing = len([j for j in jobs if j['status'] in ('queued', 'processing')]) > 0
        overall_total = sum(j['total'] for j in jobs) if jobs else 0
        overall_completed = sum(j['completed'] for j in jobs) if jobs else 0
        overall_percentage = 0
        if overall_total > 0:
            overall_percentage = int((overall_completed / overall_total) * 100)
        
        # Estimate time remaining
        estimated_remaining = "N/A"
        if is_analyzing and overall_total > overall_completed:
            # Rough estimate: assume 1 stock/second
            pending = overall_total - overall_completed
            estimated_seconds = pending
            if estimated_seconds < 60:
                estimated_remaining = f"{estimated_seconds}s"
            elif estimated_seconds < 3600:
                estimated_remaining = f"{estimated_seconds // 60}m"
            else:
                estimated_remaining = f"{estimated_seconds // 3600}h"
        
        logger.info(f"[PROGRESS] Retrieved {len(jobs)} jobs. Active: {len([j for j in jobs if j['status'] in ('queued', 'processing')])}, Completed: {overall_completed}/{overall_total} ({overall_percentage}%)")
        
        return jsonify({
            "is_analyzing": is_analyzing,
            "analyzing": len([j for j in jobs if j['status'] in ('queued', 'processing')]),
            "completed": overall_completed,
            "total": overall_total,
            "percentage": overall_percentage,
            "estimated_time_remaining": estimated_remaining,
            "pending": total_analyzing,
            "failed": total_errors,
            "successful": total_successful,
            "jobs": jobs,
            "active_count": len([j for j in jobs if j['status'] in ('queued', 'processing')])
        }), 200
        
    except Exception as e:
        logger.exception("get_all_stocks_progress error")
        return StandardizedErrorResponse.format(
            "PROGRESS_ERROR",
            "Failed to get progress",
            500,
            {"error": str(e)}
        )


@bp.route("/all-stocks/results", methods=["GET"])
def get_all_analysis_results():
    """Get all completed analysis results"""
    try:
        # Get pagination params
        page = request.args.get("page", default=1, type=int)
        per_page = request.args.get("per_page", default=50, type=int)
        
        # Validate pagination
        if page < 1:
            page = 1
        if per_page < 1 or per_page > 500:
            per_page = 50
        
        # Get total count - include all records with verdict/score (completed analysis)
        total_result = query_db("""
            SELECT COUNT(*) FROM analysis_results 
            WHERE verdict IS NOT NULL
        """, one=True)
        total = total_result[0] if total_result else 0
        
        # Get paginated results
        offset = (page - 1) * per_page
        rows = query_db("""
            SELECT id, ticker, symbol, name, yahoo_symbol, score, verdict, entry, stop_loss, target, created_at
            FROM analysis_results
            WHERE verdict IS NOT NULL
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, (per_page, offset))
        
        results = []
        for row in rows:
            if isinstance(row, (tuple, list)):
                results.append({
                    "id": row[0],
                    "ticker": row[1],
                    "symbol": row[2],
                    "name": row[3],
                    "yahoo_symbol": row[4],
                    "score": row[5],
                    "verdict": row[6],
                    "entry": row[7],
                    "stop_loss": row[8],
                    "target": row[9],
                    "created_at": row[10]
                })
            else:
                # SQLite Row object
                results.append(dict(row))
        
        logger.info(f"[RESULTS] Retrieved {len(results)} analysis results (page {page})")
        
        return jsonify({
            "results": results,
            "count": len(results),
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page
        }), 200
        
    except Exception as e:
        logger.exception("get_all_analysis_results error")
        return StandardizedErrorResponse.format(
            "RESULTS_ERROR",
            "Failed to get analysis results",
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
        existing_count_result = query_db("SELECT COUNT(*) FROM analysis_results", one=True)
        existing_bulk_count = existing_count_result[0] if existing_count_result else 0
        
        if existing_bulk_count > 0 and not force:
            return jsonify({
                "message": "Stocks already initialized",
                "exists": True,
                "hint": "Use force=true to reinitialize"
            }), 200
        
        # Insert stocks using database abstraction
        from database import get_db_connection, _convert_query_params
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            inserted = 0
            skipped_duplicates = 0
            other_errors = []
            
            for stock in normalized_stocks:
                try:
                    ticker = stock["ticker"]
                    
                    # Check if exists - use parameterized query
                    check_query = "SELECT id FROM analysis_results WHERE ticker = ? LIMIT 1"
                    check_query, check_args = _convert_query_params(check_query, (ticker,))
                    cursor.execute(check_query, check_args)
                    if cursor.fetchone():
                        skipped_duplicates += 1
                        continue
                    
                    # Insert stock with parameterized query
                    insert_query = """
                        INSERT INTO analysis_results (ticker, symbol, verdict, score, status)
                        VALUES (?, ?, ?, ?, ?)
                    """
                    insert_query, insert_args = _convert_query_params(insert_query, (
                        ticker, stock.get("symbol", ""), "HOLD", 0.0, "initialized"
                    ))
                    cursor.execute(insert_query, insert_args)
                    inserted += 1
                    
                except Exception as e:
                    other_errors.append(str(e))
                    if len(other_errors) > 100:
                        break
            
            conn.commit()
        except Exception as db_error:
            conn.rollback()
            logger.error(f"DB operation failed: {db_error}")
            return jsonify({"error": "DB operation failed", "details": str(db_error)}), 500
        finally:
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
