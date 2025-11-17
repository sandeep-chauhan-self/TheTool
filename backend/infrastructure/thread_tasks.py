"""
Threading-based background task processor

CRITICAL FIX (ISSUE_010): Thread-safe database connections
EVOLUTIONARY_RISK_001: Redis-based job state for distributed systems

This module provides async job processing with:
- Thread-local database connections
- Optional Redis-based job state (distributed-ready)
- Fallback to in-memory tracking (single server)
"""

import threading
import logging
import time
import json
import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Optional
from database import get_db_connection, get_db_session, close_thread_connection
from utils.compute_score import analyze_ticker
from models.job_state import get_job_state_manager

logger = logging.getLogger('thread_tasks')
logger.setLevel(logging.DEBUG)


# Custom JSON encoder to handle numpy types
class NumpyEncoder(json.JSONEncoder):
    """Handle numpy data types in JSON serialization"""
    def default(self, o):
        if isinstance(o, np.integer):
            return int(o)
        elif isinstance(o, np.floating):
            return float(o)
        elif isinstance(o, np.ndarray):
            return o.tolist()
        elif isinstance(o, np.bool_):
            return bool(o)
        return super().default(o)


# Global dictionary to track running threads (thread management only)
# Job state is now managed by JobStateManager (Redis or in-memory)
job_threads: Dict[str, threading.Thread] = {}

# Get job state manager (Redis or in-memory)
job_state = get_job_state_manager()


def analyze_stocks_batch(job_id: str, tickers: List[str], capital: float, indicators: Optional[List[str]] = None, use_demo_data: bool = True):
    """
    Background task to analyze multiple stocks.
    Runs in separate thread with thread-safe database connections.
    
    CRITICAL FIX (ISSUE_010):
    Uses thread-local database connections to prevent SQLite thread-safety violations.
    Each thread gets its own connection, which is properly closed when done.
    
    Args:
        job_id: Unique job identifier
        tickers: List of stock ticker symbols
        capital: Trading capital amount
        indicators: Optional list of specific indicators to use
        use_demo_data: Whether to use demo data for testing
    """
    try:
        logger.info("=" * 60)
        logger.info(f"THREAD TASK STARTED - Job ID: {job_id}")
        logger.info(f"Total stocks to analyze: {len(tickers)}")
        logger.info(f"Demo mode: {use_demo_data}")
        logger.info("=" * 60)
        
        # Mark job as processing using thread-safe connection
        with get_db_session() as (conn, cursor):
            cursor.execute('''
                UPDATE analysis_jobs 
                SET status = 'processing', started_at = ?
                WHERE job_id = ?
            ''', (datetime.now().isoformat(), job_id))
        
        total = len(tickers)
        completed = 0
        successful = 0
        errors = []
        
        # Create job state in Redis/memory
        job_state.create_job(job_id, {
            'status': 'processing',
            'total': total,
            'completed': 0,
            'successful': 0,
            'cancelled': False,
            'started_at': datetime.now().isoformat()
        })
        
        # Process each stock
        for idx, ticker in enumerate(tickers, 1):
            # Check if job was cancelled (check Redis/memory)
            current_job = job_state.get_job(job_id)
            if current_job and current_job.get('cancelled'):
                logger.warning(f"Job {job_id}: CANCELLED by user at {completed}/{total}")
                with get_db_session() as (conn, cursor):
                    cursor.execute('''
                        UPDATE analysis_jobs 
                        SET status = 'cancelled', completed_at = ?
                        WHERE job_id = ?
                    ''', (datetime.now().isoformat(), job_id))
                job_state.update_job(job_id, {'status': 'cancelled'})
                break
            
            try:
                logger.info(f"START analyzing {ticker} ({idx}/{total})")
                
                # Analyze the stock
                result = analyze_ticker(ticker, indicator_list=indicators, capital=capital, use_demo_data=use_demo_data)
                
                if result:
                    # Store analysis result using thread-safe connection
                    # UNIFIED TABLE: Now includes symbol, name, yahoo_symbol, status, analysis_source
                    raw_data = json.dumps(result.get('indicators', []), cls=NumpyEncoder)
                    
                    # Extract symbol (remove exchange suffix like .NS, .BO)
                    if '.' in ticker:
                        symbol = ticker.rsplit('.', 1)[0]
                    else:
                        symbol = ticker
                    
                    with get_db_session() as (conn, cursor):
                        cursor.execute('''
                            INSERT INTO analysis_results 
                            (ticker, symbol, name, yahoo_symbol, score, verdict, entry, stop_loss, target, 
                             entry_method, data_source, is_demo_data, raw_data, status, 
                             created_at, updated_at, analysis_source)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            ticker,
                            symbol,
                            None,  # name not available from watchlist analysis
                            ticker,  # yahoo_symbol same as ticker
                            result.get('score', 0),
                            result.get('verdict', 'Neutral'),
                            result.get('entry'),
                            result.get('stop_loss'),
                            result.get('target'),
                            result.get('entry_method', 'Market Order'),
                            result.get('data_source', 'real'),
                            result.get('is_demo_data', 0),
                            raw_data,
                            'completed',
                            datetime.now().isoformat(),
                            datetime.now().isoformat(),
                            'watchlist'  # Mark as watchlist analysis
                        ))
                    successful += 1
                    
                    # Log status - check if success flag exists
                    if result.get('success'):
                        logger.info(f"✓ {ticker} COMPLETED - Score: {result.get('score')}, Verdict: {result.get('verdict')}")
                    else:
                        # Still log as completed even if validation failed - we still have analysis data
                        error_msg = result.get('error', 'Trade validation failed')
                        if result.get('trade_issues'):
                            error_msg = f"Validation: {', '.join(result.get('trade_issues', []))}"
                        logger.warning(f"✓ {ticker} ANALYZED (Validation failed) - Score: {result.get('score')}, Reason: {error_msg}")
                else:
                    error_msg = 'No result returned from analyzer'
                    errors.append({'ticker': ticker, 'error': error_msg})
                    logger.error(f"✗ {ticker} FAILED - {error_msg}")
                
            except Exception as e:
                error_msg = str(e)
                errors.append({'ticker': ticker, 'error': error_msg})
                logger.error(f"? {ticker} ERROR - {error_msg}", exc_info=True)
            
            completed += 1
            progress = int((completed / total) * 100)
            
            # Update progress in database using thread-safe connection
            with get_db_session() as (conn, cursor):
                cursor.execute('''
                    UPDATE analysis_jobs 
                    SET progress = ?, completed = ?, successful = ?, errors = ?
                    WHERE job_id = ?
                ''', (progress, completed, successful, json.dumps(errors, cls=NumpyEncoder), job_id))
            
            # Update job state (Redis/memory)
            job_state.update_job(job_id, {
                'completed': completed,
                'successful': successful,
                'progress': progress,
                'errors': errors
            })
            
            # Log progress
            if total == 1 or completed % 10 == 0 or completed == total:
                logger.info(f"Progress: {completed}/{total} ({progress}%) | Successful: {successful} | Errors: {len(errors)}")
        
        # Mark as completed
        current_job = job_state.get_job(job_id)
        final_status = 'cancelled' if (current_job and current_job.get('cancelled')) else 'completed'
        
        with get_db_session() as (conn, cursor):
            cursor.execute('''
                UPDATE analysis_jobs 
                SET status = ?, completed_at = ?, errors = ?
                WHERE job_id = ?
            ''', (final_status, datetime.now().isoformat(), json.dumps(errors, cls=NumpyEncoder), job_id))
        
        # Update job state
        job_state.update_job(job_id, {
            'status': final_status,
            'completed_at': datetime.now().isoformat()
        })
        
        logger.info("=" * 60)
        logger.info(f"JOB {job_id} FINISHED")
        logger.info(f"Status: {final_status}")
        logger.info(f"Completed: {completed}/{total}")
        logger.info(f"Successful: {successful}")
        logger.info(f"Errors: {len(errors)}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"FATAL ERROR in job {job_id}: {e}", exc_info=True)
        try:
            with get_db_session() as (conn, cursor):
                cursor.execute('''
                    UPDATE analysis_jobs 
                    SET status = 'failed', completed_at = ?, errors = ?
                    WHERE job_id = ?
                ''', (datetime.now().isoformat(), json.dumps([{'error': str(e)}]), job_id))
            
            # Update job state
            job_state.update_job(job_id, {
                'status': 'failed',
                'completed_at': datetime.now().isoformat(),
                'errors': [{'error': str(e)}]
            })
        except Exception as cleanup_error:
            logger.error(f"Failed to update job status: {cleanup_error}")
    
    finally:
        # Cleanup thread-local connection
        close_thread_connection()
        
        # Cleanup thread tracking (Redis job state is kept for monitoring)
        if job_id in job_threads:
            del job_threads[job_id]


def start_analysis_job(job_id: str, tickers: List[str], indicators: Optional[List[str]], capital: float, use_demo: bool) -> bool:
    """
    Start a new analysis job in background thread
    Returns True if started successfully
    """
    try:
        thread = threading.Thread(
            target=analyze_stocks_batch,
            args=(job_id, tickers, capital, indicators, use_demo),
            daemon=True,
            name=f"AnalysisJob-{job_id[:8]}"
        )
        thread.start()
        job_threads[job_id] = thread
        logger.info(f"Started background thread for job {job_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to start thread for job {job_id}: {e}")
        return False


def cancel_job(job_id: str) -> bool:
    """
    Cancel a running job.
    
    Args:
        job_id: Job identifier
    
    Returns:
        True if job was cancelled successfully
    """
    return job_state.cancel_job(job_id)


def get_active_jobs() -> Dict[str, Dict[str, Any]]:
    """
    Get information about all active jobs.
    
    Returns:
        Dictionary mapping job_id -> job_state
    """
    return job_state.get_all_jobs()


def cleanup_old_threads():
    """Clean up completed threads from tracking"""
    to_remove = []
    for job_id, thread in job_threads.items():
        if not thread.is_alive():
            to_remove.append(job_id)
    
    for job_id in to_remove:
        del job_threads[job_id]
        logger.debug(f"Cleaned up completed thread for job {job_id}")


def analyze_single_stock_bulk(symbol: str, yahoo_symbol: str, name: str, use_demo: bool):
    """
    Analyze a single stock for bulk analysis with thread-safe database operations.
    Updates all_stocks_analysis table directly.
    
    CRITICAL FIX (ISSUE_010):
    Uses thread-safe database connections for concurrent bulk analysis.
    
    Args:
        symbol: Stock symbol
        yahoo_symbol: Yahoo Finance symbol
        name: Company name
        use_demo: Whether to use demo data
        
    Returns:
        bool: True if analysis succeeded
    """
    from database import cleanup_old_analyses
    
    try:
        logger.info(f"Analyzing {symbol} for bulk analysis")
        
        # Run analysis
        result = analyze_ticker(yahoo_symbol, indicator_list=None, capital=100000, use_demo_data=use_demo)
        
        if result:
            # Store analysis result in UNIFIED analysis_results table
            raw_data = json.dumps(result.get('indicators', []), cls=NumpyEncoder)
            
            with get_db_session() as (conn, cursor):
                cursor.execute('''
                    INSERT INTO analysis_results 
                    (ticker, symbol, name, yahoo_symbol, score, verdict, entry, stop_loss, target, 
                     entry_method, data_source, is_demo_data, raw_data, status, 
                     created_at, updated_at, analysis_source)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    yahoo_symbol,  # ticker = yahoo_symbol
                    symbol,        # symbol without suffix
                    name,          # company name
                    yahoo_symbol,  # yahoo_symbol with suffix
                    result.get('score', 0),
                    result.get('verdict', 'Neutral'),
                    result.get('entry'),
                    result.get('stop_loss'),
                    result.get('target'),
                    result.get('entry_method', 'Market Order'),
                    result.get('data_source', 'real'),
                    use_demo,
                    raw_data,
                    'completed',
                    datetime.now().isoformat(),
                    datetime.now().isoformat(),
                    'bulk'  # Mark as bulk analysis
                ))
            
            # Auto-cleanup old analyses (keep last 10) - using symbol parameter
            cleanup_old_analyses(symbol=symbol, keep_last=10)
            
            # Log with full context
            if result.get('success'):
                logger.info(f"✓ {symbol} completed - Score: {result.get('score')}, Verdict: {result.get('verdict')}")
            else:
                error_msg = result.get('error', 'Analysis completed with validation notes')
                logger.info(f"✓ {symbol} analyzed - Score: {result.get('score')}, Verdict: {result.get('verdict')} (Validation: {error_msg})")
            return True
            
    except Exception as e:
        logger.error(f"? {symbol} ERROR - {str(e)}", exc_info=True)
        
        try:
            with get_db_session() as (conn, cursor):
                cursor.execute('''
                    INSERT INTO analysis_results 
                    (ticker, symbol, name, yahoo_symbol, score, verdict, status, error_message, 
                     created_at, updated_at, analysis_source)
                    VALUES (?, ?, ?, ?, 0.0, 'Pending', 'failed', ?, ?, ?, 'bulk')
                ''', (
                    yahoo_symbol,
                    symbol,
                    name,
                    yahoo_symbol,
                    str(e),
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
        except Exception as cleanup_error:
            logger.error(f"Failed to log error for {symbol}: {cleanup_error}")
        
        return False


def start_bulk_analysis(stocks: List[Dict[str, str]], use_demo: bool = True, max_workers: int = 5):
    """
    Start bulk analysis for multiple stocks
    Each stock runs as a separate job in thread pool
    
    Args:
        stocks: List of dicts with keys: symbol, name, yahoo_symbol
        use_demo: Whether to use demo data
        max_workers: Number of concurrent analysis threads
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    logger.info(f"Starting bulk analysis for {len(stocks)} stocks with {max_workers} workers")
    
    # Use thread pool for parallel processing
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(analyze_single_stock_bulk, stock['symbol'], stock['yahoo_symbol'], stock['name'], use_demo): stock
            for stock in stocks
        }
        
        completed_count = 0
        for future in as_completed(futures):
            stock = futures[future]
            try:
                success = future.result()
                completed_count += 1
                
                if completed_count % 10 == 0 or completed_count == len(stocks):
                    logger.info(f"Bulk progress: {completed_count}/{len(stocks)} stocks processed")
                    
            except Exception as e:
                logger.error(f"Bulk analysis error for {stock['symbol']}: {e}")
    
    logger.info(f"Bulk analysis completed - Processed {completed_count}/{len(stocks)} stocks")
