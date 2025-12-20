"""
Analysis routes - Ticker analysis, job management, and status tracking
"""
import uuid
import json
import traceback
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file
from utils.logger import setup_logger
from utils.api_utils import (
    StandardizedErrorResponse,
    SafeJsonParser,
    validate_request,
    RequestValidator
)
from utils.timezone_util import get_ist_timestamp
from database import query_db, execute_db, get_db_connection
from models.job_state import get_job_state_manager
from utils.db_utils import JobStateTransactions, get_job_status
from utils.schemas import ResponseSchemas, validate_response

logger = setup_logger()
bp = Blueprint("analysis", __name__, url_prefix="/api/analysis")


def _get_active_job_for_tickers(tickers: list) -> dict:
    """
    Check if an identical job (same tickers) is already running.
    Returns the existing job info or None if safe to create new job.
    Tickers are normalized (sorted, uppercased) for reliable matching.
    """
    try:
        from datetime import timedelta
        from utils.timezone_util import get_ist_now
        
        # Normalize tickers for comparison: sort and uppercase
        normalized_tickers = json.dumps(sorted([t.upper().strip() for t in tickers]))
        five_min_ago = (get_ist_now() - timedelta(minutes=5)).isoformat()
        
        # Look for exact same tickers in queued/processing jobs from last 5 minutes
        active_job = query_db("""
            SELECT job_id, status, total, completed, created_at
            FROM analysis_jobs
            WHERE status IN ('queued', 'processing')
              AND tickers_json = ?
              AND created_at > ?
            ORDER BY created_at DESC
            LIMIT 1
        """, (normalized_tickers, five_min_ago), one=True)
        
        if not active_job:
            return None
        
        job_id, status, total, completed, created_at = active_job
        logger.info(f"Found active job {job_id} with status {status} for tickers {tickers}")
        
        return {
            "job_id": job_id,
            "status": status,
            "total": total,
            "completed": completed,
            "created_at": created_at
        }
    except Exception as e:
        logger.exception(f"Error checking for active jobs with tickers {tickers}: {e}")
        return None


def get_analyze_ticker():
    """Lazy load analyze_ticker to avoid circular imports"""
    from utils.analysis.orchestrator import analyze_ticker, export_to_excel
    return analyze_ticker, export_to_excel


@bp.route("/analyze", methods=["POST"])
def analyze():
    """
    Analyze one or more tickers with given capital allocation.
    
    Request body:
    {
        "tickers": ["TCS.NS", "INFY.NS"],
        "capital": 100000,
        "force": false  # Set true to bypass duplicate check
    }
    """
    try:
        data = request.get_json() or {}
        
        # Log incoming request for debugging
        logger.info(f"[ANALYZE] Incoming request - raw data: {data}")
        logger.debug(f"[ANALYZE] Request details - tickers_count: {len(data.get('tickers', []))}, "
                    f"capital: {data.get('capital', 'not-provided')}, "
                    f"use_demo: {data.get('use_demo_data', 'default')}")
        logger.debug(f"[ANALYZE] Raw tickers list: {data.get('tickers', [])}")
        
        # Validate request
        validated_data, error_response = validate_request(
            data,
            RequestValidator.AnalyzeRequest
        )
        if error_response:
            logger.warning(f"[ANALYZE] Validation failed - response: {error_response}")
            return error_response
        
        tickers = validated_data["tickers"]
        capital = validated_data["capital"]
        force = data.get("force", False)
        strategy_id = data.get("strategy_id", 1)  # Default to Strategy 1 (Balanced)
        
        # Validate strategy_id is a valid integer
        try:
            strategy_id = int(strategy_id)
            if strategy_id < 1:
                strategy_id = 1
        except (ValueError, TypeError):
            strategy_id = 1
        
        # Extract additional config parameters
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
        
        logger.info(f"[ANALYZE] Validation passed - tickers: {tickers}, capital: {capital}, force: {force}, strategy_id: {strategy_id}")
        logger.debug(f"[ANALYZE] Config: {analysis_config}")
        
        # Check for duplicate/active jobs (unless force=true)
        if not force:
            active_job = _get_active_job_for_tickers(tickers)
            if active_job:
                logger.info(f"Duplicate job request detected. Returning existing job {active_job['job_id']}")
                return jsonify({
                    "job_id": active_job["job_id"],
                    "status": active_job["status"],
                    "is_duplicate": True,
                    "message": "Analysis already running for these tickers",
                    "total": active_job["total"],
                    "completed": active_job["completed"],
                    "tickers": tickers,
                    "capital": capital
                }), 200
        
        # Create job ID
        job_id = str(uuid.uuid4())
        logger.info(f"[ANALYZE] Creating new job {job_id}")
        
        # Create job atomically with retries
        max_retries = 3
        created = False
        for attempt in range(max_retries):
            try:
                created = JobStateTransactions.create_job_atomic(
                    job_id=job_id,
                    status="queued",
                    total=len(tickers),
                    description=f"Analyze {len(tickers)} ticker(s) with capital {capital}",
                    tickers=tickers,
                    strategy_id=strategy_id
                )
                if created:
                    break
                else:
                    logger.warning(f"Job creation failed (attempt {attempt + 1}/{max_retries}), retrying...")
                    import time
                    time.sleep(0.1 * (attempt + 1))
            except Exception as e:
                logger.exception(f"Exception during job creation (attempt {attempt + 1}/{max_retries})")
                if attempt == max_retries - 1:
                    return StandardizedErrorResponse.format(
                        "JOB_CREATION_FAILED",
                        "Failed to create analysis job",
                        500,
                        {"error": str(e), "job_id": job_id}
                    )
        
        if not created:
            return StandardizedErrorResponse.format(
                "JOB_DUPLICATE",
                "Job already exists (potential race condition)",
                409,
                {"job_id": job_id}
            )
        
        # Start background job
        start_success = False
        try:
            from infrastructure.thread_tasks import start_analysis_job
            start_success = start_analysis_job(job_id, tickers, None, capital, False, analysis_config, strategy_id)
            if not start_success:
                logger.error(f"Failed to start thread for job {job_id}")
        except Exception as e:
            logger.exception(f"Failed to start analysis job {job_id}")
        
        logger.info(f"Analysis job created: {job_id} for {tickers} with strategy_id={strategy_id}")
        return jsonify({
            "job_id": job_id,
            "status": "queued",
            "tickers": tickers,
            "capital": capital,
            "strategy_id": strategy_id,
            "thread_started": start_success
        }), 201
        
    except Exception as e:
        logger.exception("analyze error")
        return StandardizedErrorResponse.format(
            "ANALYSIS_ERROR",
            "Analysis failed",
            500,
            {"error": str(e)}
        )


@bp.route("/status/<job_id>", methods=["GET"])
def get_analysis_job_status(job_id):
    """Get status of a specific analysis job"""
    try:
        status = get_job_status(job_id)
        
        if not status:
            return StandardizedErrorResponse.format(
                "JOB_NOT_FOUND",
                f"Job {job_id} not found",
                404
            )
        
        # Try to include analysis results if job is complete
        if status["status"] == "completed":
            try:
                results = query_db(
                    """
                    SELECT ticker, symbol, verdict, score, entry, stop_loss, target, created_at
                    FROM analysis_results 
                    WHERE job_id = ?
                    ORDER BY created_at DESC
                    LIMIT 50
                    """,
                    (job_id,)
                )
                status["results"] = [dict(r) for r in results]
            except Exception as e:
                logger.warning(f"Could not fetch analysis results for {job_id}: {e}")
        
        return jsonify(status), 200
        
    except Exception as e:
        logger.exception(f"get_status error for {job_id}")
        return StandardizedErrorResponse.format(
            "STATUS_ERROR",
            "Failed to get job status",
            500,
            {"error": str(e)}
        )


@bp.route("/cancel/<job_id>", methods=["POST"])
def cancel_job(job_id):
    """Cancel a running analysis job"""
    try:
        # Get current job status
        status = get_job_status(job_id)
        if not status:
            return StandardizedErrorResponse.format(
                "JOB_NOT_FOUND",
                f"Job {job_id} not found",
                404
            )
        
        # Only allow canceling queued/processing jobs
        if status["status"] not in ["queued", "processing"]:
            return StandardizedErrorResponse.format(
                "JOB_CANCEL_INVALID",
                f"Cannot cancel job in {status['status']} state",
                400,
                {"current_status": status["status"]}
            )
        
        # Update job status to cancelled
        try:
            JobStateTransactions.mark_job_completed(job_id, "cancelled")
        except Exception as e:
            logger.error(f"Failed to mark job {job_id} as cancelled: {e}")
            return StandardizedErrorResponse.format(
                "JOB_UPDATE_FAILED",
                "Failed to cancel job",
                500,
                {"error": str(e)}
            )
        
        logger.info(f"Job {job_id} cancelled by user")
        return jsonify({
            "job_id": job_id,
            "status": "cancelled"
        }), 200
        
    except Exception as e:
        logger.exception(f"cancel_job error for {job_id}")
        return StandardizedErrorResponse.format(
            "CANCEL_ERROR",
            "Failed to cancel job",
            500,
            {"error": str(e)}
        )


@bp.route("/history/<ticker>", methods=["GET"])
def get_history(ticker):
    """Get analysis history for a specific ticker"""
    try:
        # Validate ticker
        if not ticker or len(ticker.strip()) == 0:
            return StandardizedErrorResponse.format(
                "INVALID_TICKER",
                "Ticker cannot be empty",
                400
            )
        
        # Query analysis results including raw_data for indicators and position_size
        results = query_db(
            """
            SELECT id, ticker, symbol, verdict, score, entry, stop_loss, target, created_at, raw_data,
                   position_size, risk_reward_ratio, strategy_id, analysis_config
            FROM analysis_results
            WHERE LOWER(ticker) = LOWER(?)
            ORDER BY created_at DESC
            LIMIT 50
            """,
            (ticker,)
        )
        
        if not results:
            return jsonify({
                "ticker": ticker,
                "history": []
            }), 200
        
        # Handle both tuple (PostgreSQL) and dict (SQLite) return types
        history = []
        for r in results:
            if isinstance(r, (tuple, list)):
                # PostgreSQL returns tuples: (id, ticker, symbol, verdict, score, entry, stop_loss, target, created_at, raw_data, position_size, risk_reward_ratio, strategy_id, analysis_config)
                raw_data = r[9]
                indicators = []
                if raw_data:
                    try:
                        indicators = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
                    except json.JSONDecodeError:
                        indicators = []
                
                # Parse analysis_config
                config_data = None
                if r[13]:
                    try:
                        config_data = json.loads(r[13]) if isinstance(r[13], str) else r[13]
                    except json.JSONDecodeError:
                        config_data = None
                
                history.append({
                    "id": r[0],
                    "ticker": r[1],
                    "symbol": r[2],
                    "verdict": r[3],
                    "score": r[4],
                    "entry": r[5],
                    "stop_loss": r[6],
                    "target": r[7],
                    "created_at": str(r[8]) if r[8] else None,
                    "indicators": indicators,
                    "position_size": r[10] or 0,
                    "risk_reward_ratio": r[11] or 0,
                    "strategy_id": r[12] or 5,
                    "analysis_config": config_data
                })
            else:
                # SQLite returns Row objects
                item_dict = dict(r)
                raw_data = item_dict.get('raw_data')
                indicators = []
                if raw_data:
                    try:
                        indicators = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
                    except json.JSONDecodeError:
                        indicators = []
                item_dict['indicators'] = indicators
                item_dict['position_size'] = item_dict.get('position_size', 0) or 0
                item_dict['risk_reward_ratio'] = item_dict.get('risk_reward_ratio', 0) or 0
                item_dict['strategy_id'] = item_dict.get('strategy_id', 5) or 5
                # Parse analysis_config
                config_str = item_dict.get('analysis_config')
                if config_str:
                    try:
                        item_dict['analysis_config'] = json.loads(config_str) if isinstance(config_str, str) else config_str
                    except json.JSONDecodeError:
                        item_dict['analysis_config'] = None
                history.append(item_dict)
        
        return jsonify({
            "ticker": ticker,
            "history": history
        }), 200
        
    except Exception as e:
        logger.exception(f"get_history error for {ticker}")
        return StandardizedErrorResponse.format(
            "HISTORY_ERROR",
            "Failed to get history",
            500,
            {"error": str(e)}
        )


@bp.route("/report/<ticker>", methods=["GET"])
def get_report(ticker):
    """Get detailed analysis report for a ticker"""
    try:
        if not ticker or len(ticker.strip()) == 0:
            return StandardizedErrorResponse.format(
                "INVALID_TICKER",
                "Ticker cannot be empty",
                400
            )
        
        logger.info(f"[REPORT] Querying for ticker: {ticker}")
        
        # Get latest analysis (including position_size, risk_reward_ratio, strategy_id, and analysis_config)
        result = query_db(
            """
            SELECT verdict, score, entry, stop_loss, target, created_at, raw_data,
                   position_size, risk_reward_ratio, analysis_config, strategy_id
            FROM analysis_results
            WHERE LOWER(ticker) = LOWER(?)
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (ticker,),
            one=True
        )
        
        logger.info(f"[REPORT] Query result for {ticker}: {result is not None}")
        
        if not result:
            # Log available tickers for debugging
            all_tickers = query_db("SELECT DISTINCT ticker FROM analysis_results LIMIT 10")
            available = [t[0] if isinstance(t, (tuple, list)) else t['ticker'] for t in all_tickers]
            logger.warning(f"[REPORT] No analysis found for {ticker}. Available tickers: {available}")
            
            return StandardizedErrorResponse.format(
                "REPORT_NOT_FOUND",
                f"No analysis found for {ticker}",
                404
            )
        
        # Handle both tuple (PostgreSQL) and dict (SQLite) return types
        if isinstance(result, (tuple, list)):
            analysis_data = {
                "verdict": result[0],
                "score": result[1],
                "entry": result[2],
                "stop_loss": result[3],
                "target": result[4],
                "position_size": result[7] or 0,
                "risk_reward_ratio": result[8] or 0,
                "strategy_id": result[10] or 5
            }
            created_at = result[5]
            raw_data = result[6]
            analysis_config = result[9]
        else:
            analysis_data = {
                "verdict": result['verdict'],
                "score": result['score'],
                "entry": result['entry'],
                "stop_loss": result['stop_loss'],
                "target": result['target'],
                "position_size": result.get('position_size', 0) or 0,
                "risk_reward_ratio": result.get('risk_reward_ratio', 0) or 0,
                "strategy_id": result.get('strategy_id', 5) or 5
            }
            created_at = result['created_at']
            raw_data = result['raw_data']
            analysis_config = result.get('analysis_config')
        
        # Parse analysis_config if present
        config_data = None
        if analysis_config:
            try:
                config_data = json.loads(analysis_config) if isinstance(analysis_config, str) else analysis_config
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse analysis_config JSON for {ticker}")
        
        # Parse indicators from raw_data JSON
        indicators = []
        if raw_data:
            try:
                indicators = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse raw_data JSON for {ticker}")
                indicators = []
        
        return jsonify({
            "ticker": ticker,
            "analysis": analysis_data,
            "indicators": indicators,
            "created_at": created_at,
            "analysis_config": config_data
        }), 200
        
    except Exception as e:
        logger.exception(f"get_report error for {ticker}")
        return StandardizedErrorResponse.format(
            "REPORT_ERROR",
            "Failed to get report",
            500,
            {"error": str(e)}
        )


@bp.route("/report/<ticker>/download", methods=["GET"])
def download_report(ticker):
    """Download analysis report as Excel file"""
    try:
        if not ticker or len(ticker.strip()) == 0:
            return StandardizedErrorResponse.format(
                "INVALID_TICKER",
                "Ticker cannot be empty",
                400
            )
        
        # Get latest analysis with raw_data (contains indicators)
        result = query_db(
            """
            SELECT verdict, score, entry, stop_loss, target, raw_data, created_at
            FROM analysis_results
            WHERE LOWER(ticker) = LOWER(?)
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (ticker,),
            one=True
        )
        
        if not result:
            return StandardizedErrorResponse.format(
                "REPORT_NOT_FOUND",
                f"No analysis found for {ticker}",
                404
            )
        
        # Handle both tuple (PostgreSQL) and dict (SQLite) return types
        if isinstance(result, (tuple, list)):
            raw_data_str = result[5]
            analysis_data = {
                "ticker": ticker,
                "verdict": result[0],
                "score": result[1],
                "entry": result[2],
                "stop": result[3],  # export_to_excel expects 'stop' not 'stop_loss'
                "target": result[4],
                "indicators": []
            }
        else:
            raw_data_str = result['raw_data']
            analysis_data = {
                "ticker": ticker,
                "verdict": result['verdict'],
                "score": result['score'],
                "entry": result['entry'],
                "stop": result['stop_loss'],  # export_to_excel expects 'stop' not 'stop_loss'
                "target": result['target'],
                "indicators": []
            }
        
        # Parse indicators from raw_data JSON
        if raw_data_str:
            try:
                analysis_data["indicators"] = json.loads(raw_data_str)
            except (json.JSONDecodeError, TypeError):
                analysis_data["indicators"] = []
        
        # Export to Excel - pass the full result dict (not ticker separately)
        analyze_ticker, export_to_excel = get_analyze_ticker()
        excel_file = export_to_excel(analysis_data)
        
        # excel_file is a string path, check if file exists
        import os
        if not excel_file or not os.path.exists(excel_file):
            return StandardizedErrorResponse.format(
                "EXPORT_FAILED",
                "Failed to generate Excel report",
                500
            )
        
        return send_file(
            excel_file,
            as_attachment=True,
            download_name=f"{ticker}_analysis_{get_ist_timestamp()[:19].replace(':', '-')}.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    except Exception as e:
        logger.exception(f"download_report error for {ticker}")
        return StandardizedErrorResponse.format(
            "DOWNLOAD_ERROR",
            "Failed to download report",
            500,
            {"error": str(e)}
        )
