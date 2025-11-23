"""
Analysis routes - Ticker analysis, job management, and status tracking
"""
import uuid
import json
import traceback
import sqlite3
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file
from utils.logger import setup_logger
from utils.api_utils import (
    StandardizedErrorResponse,
    SafeJsonParser,
    validate_request,
    RequestValidator
)
from database import query_db, execute_db, get_db_connection
from models.job_state import get_job_state_manager
from utils.db_utils import JobStateTransactions, get_job_status
from utils.schemas import ResponseSchemas, validate_response

logger = setup_logger()
bp = Blueprint("analysis", __name__, url_prefix="/api/analysis")


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
        "capital": 100000
    }
    """
    try:
        data = request.get_json() or {}
        
        # Validate request
        validated_data, error_response = validate_request(
            data,
            RequestValidator.AnalyzeRequest
        )
        if error_response:
            return error_response
        
        tickers = validated_data["tickers"]
        capital = validated_data["capital"]
        
        # Create job ID
        job_id = str(uuid.uuid4())
        
        # Create job atomically
        created = JobStateTransactions.create_job_atomic(
            job_id=job_id,
            status="queued",
            total=len(tickers),
            description=f"Analyze {len(tickers)} ticker(s) with capital {capital}"
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
            start_analysis_job(job_id, tickers, None, capital, False)
        except Exception as e:
            logger.error(f"Failed to start analysis job {job_id}: {e}")
            return StandardizedErrorResponse.format(
                "JOB_START_FAILED",
                "Failed to start analysis",
                500,
                {"error": str(e)}
            )
        
        logger.info(f"Analysis job created: {job_id} for {tickers}")
        return jsonify({
            "job_id": job_id,
            "status": "queued",
            "tickers": tickers,
            "capital": capital
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
def get_job_status(job_id):
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
                    ORDER BY created_at DESC
                    LIMIT 50
                    """,
                    ()
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
        
        # Query analysis results
        results = query_db(
            """
            SELECT id, ticker, symbol, verdict, score, entry, stop_loss, target, created_at
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
        
        return jsonify({
            "ticker": ticker,
            "history": [dict(r) for r in results]
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
        
        # Get latest analysis
        result = query_db(
            """
            SELECT verdict, score, entry, stop_loss, target, created_at
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
        
        analysis_data = {
            "verdict": result['verdict'],
            "score": result['score'],
            "entry": result['entry'],
            "stop_loss": result['stop_loss'],
            "target": result['target']
        }
        
        return jsonify({
            "ticker": ticker,
            "analysis": analysis_data,
            "created_at": result['created_at']
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
        
        # Get latest analysis
        result = query_db(
            """
            SELECT verdict, score, entry, stop_loss, target, created_at
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
        
        analysis_data = {
            "verdict": result['verdict'],
            "score": result['score'],
            "entry": result['entry'],
            "stop_loss": result['stop_loss'],
            "target": result['target']
        }
        
        # Export to Excel
        analyze_ticker, export_to_excel = get_analyze_ticker()
        excel_file = export_to_excel(ticker, analysis_data)
        
        if not excel_file or not excel_file.exists():
            return StandardizedErrorResponse.format(
                "EXPORT_FAILED",
                "Failed to generate Excel report",
                500
            )
        
        return send_file(
            excel_file,
            as_attachment=True,
            download_name=f"{ticker}_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
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
