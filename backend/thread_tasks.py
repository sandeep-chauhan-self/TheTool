"""
Threading-based background task processor (Redis-free alternative)
This module provides async job processing without requiring Redis/Celery
"""

import threading
import logging
import time
import json
import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Optional
from database import get_db_connection, _convert_query_params
from utils.compute_score import analyze_ticker

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


# Global dictionary to track running jobs and their threads
active_jobs: Dict[str, Dict[str, Any]] = {}
job_threads: Dict[str, threading.Thread] = {}


def analyze_stocks_batch(job_id: str, tickers: List[str], capital: float, indicators: Optional[List[str]] = None, use_demo_data: bool = True):
    """
    Background task to analyze multiple stocks
    Runs in separate thread, updates database with progress
    """
    try:
        logger.info("=" * 60)
        logger.info(f"THREAD TASK STARTED - Job ID: {job_id}")
        logger.info(f"Total stocks to analyze: {len(tickers)}")
        logger.info(f"Demo mode: {use_demo_data}")
        logger.info("=" * 60)
        
        # Mark job as processing
        conn = get_db_connection()
        cursor = conn.cursor()
        query = '''
            UPDATE analysis_jobs 
            SET status = 'processing', started_at = ?
            WHERE job_id = ?
        '''
        query, args = _convert_query_params(query, (datetime.now().isoformat(), job_id))
        cursor.execute(query, args)
        conn.commit()
        
        total = len(tickers)
        completed = 0
        successful = 0
        errors = []
        
        # Track in active_jobs
        active_jobs[job_id] = {
            'status': 'processing',
            'total': total,
            'completed': 0,
            'successful': 0,
            'cancelled': False
        }
        
        # Process each stock
        for idx, ticker in enumerate(tickers, 1):
            # Check if job was cancelled
            if active_jobs.get(job_id, {}).get('cancelled'):
                logger.warning(f"Job {job_id}: CANCELLED by user at {completed}/{total}")
                query = '''
                    UPDATE analysis_jobs 
                    SET status = 'cancelled', completed_at = ?
                    WHERE job_id = ?
                '''
                query, args = _convert_query_params(query, (datetime.now().isoformat(), job_id))
                cursor.execute(query, args)
                conn.commit()
                break
            
            try:
                logger.info(f"START analyzing {ticker} ({idx}/{total})")
                
                # Analyze the stock
                result = analyze_ticker(ticker, indicator_list=indicators, capital=capital, use_demo_data=use_demo_data)
                
                if result:
                    # Store analysis result regardless of success/failure
                    # This ensures we capture all analysis data, even if trade validation failed
                    raw_data = json.dumps(result.get('indicators', []), cls=NumpyEncoder)
                    query = '''
                        INSERT INTO analysis_results 
                        (job_id, ticker, score, verdict, entry, stop_loss, target, entry_method, data_source, is_demo_data, raw_data, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    '''
                    query, args = _convert_query_params(query, (
                        job_id,
                        ticker,
                        result.get('score', 0),
                        result.get('verdict', 'Neutral'),
                        result.get('entry'),
                        result.get('stop'),  # Note: key is 'stop' not 'stop_loss'
                        result.get('target'),
                        result.get('entry_method', 'Market Order'),
                        result.get('data_source', 'real'),
                        result.get('is_demo_data', 0),
                        raw_data,
                        datetime.now().isoformat()
                    ))
                    cursor.execute(query, args)
                    conn.commit()
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
            
            # Update progress in database
            query = '''
                UPDATE analysis_jobs 
                SET progress = ?, completed = ?, successful = ?, errors = ?
                WHERE job_id = ?
            '''
            query, args = _convert_query_params(query, (progress, completed, successful, json.dumps(errors, cls=NumpyEncoder), job_id))
            cursor.execute(query, args)
            conn.commit()
            
            # Update active_jobs tracker
            active_jobs[job_id].update({
                'completed': completed,
                'successful': successful,
                'progress': progress
            })
            
            # Log progress
            if total == 1 or completed % 10 == 0 or completed == total:
                logger.info(f"Progress: {completed}/{total} ({progress}%) | Successful: {successful} | Errors: {len(errors)}")
        
        # Mark as completed
        final_status = 'cancelled' if active_jobs.get(job_id, {}).get('cancelled') else 'completed'
        query = '''
            UPDATE analysis_jobs 
            SET status = ?, completed_at = ?, errors = ?
            WHERE job_id = ?
        '''
        query, args = _convert_query_params(query, (final_status, datetime.now().isoformat(), json.dumps(errors, cls=NumpyEncoder), job_id))
        cursor.execute(query, args)
        conn.commit()
        conn.close()
        
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
            conn = get_db_connection()
            cursor = conn.cursor()
            query = '''
                UPDATE analysis_jobs 
                SET status = 'failed', completed_at = ?, errors = ?
                WHERE job_id = ?
            '''
            query, args = _convert_query_params(query, (datetime.now().isoformat(), json.dumps([{'error': str(e)}]), job_id))
            cursor.execute(query, args)
            conn.commit()
            conn.close()
        except:
            pass
    
    finally:
        # Cleanup
        if job_id in active_jobs:
            del active_jobs[job_id]
        if job_id in job_threads:
            del job_threads[job_id]


def start_analysis_job(job_id: str, tickers: List[str], indicators: Optional[List[str]], capital: float, use_demo: bool) -> bool:
    """
    Start a new analysis job in background thread
    Returns True if started successfully
    
    CRITICAL: On Railway (and cloud platforms), we MUST use daemon=False
    to ensure threads actually run. Daemon threads are killed immediately
    on serverless/containerized platforms.
    """
    try:
        thread = threading.Thread(
            target=analyze_stocks_batch,
            args=(job_id, tickers, capital, indicators, use_demo),
            daemon=False,  # CRITICAL: Must be False on Railway for threads to execute
            name=f"AnalysisJob-{job_id[:8]}"
        )
        thread.start()
        job_threads[job_id] = thread
        logger.info(f"Started background thread for job {job_id} (daemon=False)")
        return True
    except Exception as e:
        logger.error(f"Failed to start thread for job {job_id}: {e}")
        return False


def cancel_job(job_id: str) -> bool:
    """
    Cancel a running job
    Returns True if job was cancelled
    """
    if job_id in active_jobs:
        active_jobs[job_id]['cancelled'] = True
        logger.info(f"Cancellation requested for job {job_id}")
        return True
    return False


def get_active_jobs() -> Dict[str, Dict[str, Any]]:
    """Get information about all active jobs"""
    return active_jobs.copy()


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
    Analyze a single stock for bulk analysis
    Updates analysis_results table (unified table)
    """
    from database import cleanup_old_analyses
    
    try:
        logger.info(f"Analyzing {symbol} for bulk analysis")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Update status to 'analyzing'
        query = '''
            UPDATE analysis_results 
            SET status = 'analyzing', updated_at = ?
            WHERE symbol = ? AND id = (
                SELECT MAX(id) FROM analysis_results WHERE symbol = ?
            )
        '''
        query, args = _convert_query_params(query, (datetime.now().isoformat(), symbol, symbol))
        cursor.execute(query, args)
        conn.commit()
        
        # Run analysis
        result = analyze_ticker(yahoo_symbol, indicator_list=None, capital=100000, use_demo_data=use_demo)
        
        if result:
            # Store all analysis results (regardless of validation status)
            raw_data = json.dumps(result.get('indicators', []), cls=NumpyEncoder)
            
            query = '''
                INSERT INTO analysis_results 
                (symbol, name, yahoo_symbol, status, score, verdict, entry, stop_loss, target, 
                 entry_method, data_source, is_demo_data, raw_data, created_at, updated_at)
                VALUES (?, ?, ?, 'completed', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            query, args = _convert_query_params(query, (
                symbol,
                name,
                yahoo_symbol,
                result.get('score', 0),
                result.get('verdict', 'Neutral'),
                result.get('entry'),
                result.get('stop'),  # Note: key is 'stop' not 'stop_loss'
                result.get('target'),
                result.get('entry_method', 'Market Order'),
                result.get('data_source', 'real'),
                use_demo,
                raw_data,
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            cursor.execute(query, args)
            conn.commit()
            
            # Auto-cleanup old analyses (keep last 10)
            cleanup_old_analyses(symbol=symbol, keep_last=10)
            
            conn.close()
            
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
            conn = get_db_connection()
            cursor = conn.cursor()
            query = '''
                INSERT INTO analysis_results 
                (symbol, name, yahoo_symbol, status, error_message, created_at, updated_at)
                VALUES (?, ?, ?, 'failed', ?, ?, ?)
            '''
            query, args = _convert_query_params(query, (
                symbol,
                name,
                yahoo_symbol,
                str(e),
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            cursor.execute(query, args)
            conn.commit()
            conn.close()
        except:
            pass
        
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
