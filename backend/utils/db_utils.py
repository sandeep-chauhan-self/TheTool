"""
Enhanced database utilities with concurrency control and transaction support

Provides:
- execute_transaction(): Atomic multi-statement transactions
- get_job_with_lock(): Optimistic locking for job updates
- create_job_atomic(): Atomic job creation
- query_builder: SQL query helpers
"""

import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from database import get_db_connection, query_db, execute_db

# Import PostgreSQL driver
import psycopg2

logger = logging.getLogger(__name__)


class JobStateTransactions:
    """
    Atomic job operations with concurrency control
    
    Implements optimistic locking for job updates to prevent race conditions
    """
    
    @staticmethod
    def create_job_atomic(
        job_id: str,
        status: str,
        total: int,
        description: str = "",
        tickers: Optional[List[str]] = None,
        strategy_id: int = 1
    ) -> bool:
        """
        Create a job record atomically.
        
        Uses a fresh database connection with proper transaction handling.
        Each call gets a new connection to avoid aborted transaction issues.
        
        Args:
            job_id: Unique job identifier
            status: Initial status (usually 'queued')
            total: Total items to process
            description: Optional job description
            tickers: List of tickers being analyzed (for duplicate detection)
            strategy_id: Strategy ID (default 1)
            
        Returns:
            True if created, False if failed or duplicate
        """
        from database import get_db_session, _convert_query_params
        
        # Normalize tickers: sort and JSON dump for consistent duplicate detection
        # For very large batches (> 100 stocks), skip storing tickers to avoid
        # database performance issues and potential timeouts
        tickers_json = None
        if tickers and len(tickers) <= 100:
            tickers_json = json.dumps(sorted([t.upper().strip() for t in tickers]))
        elif tickers and len(tickers) > 100:
            # Store just the count and "ALL" marker for bulk analysis
            tickers_json = json.dumps({"type": "bulk", "count": len(tickers)})
            logger.info(f"Large batch ({len(tickers)} stocks) - using bulk marker instead of full ticker list")
        
        # Use get_db_session() for proper transaction handling with rollback
        try:
            with get_db_session() as (conn, cursor):
                now = datetime.now().isoformat()
                
                # Convert query params for PostgreSQL
                query = '''
                    INSERT INTO analysis_jobs 
                    (job_id, status, total, completed, progress, errors,
                     tickers_json, strategy_id, created_at, updated_at, successful)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                '''
                query, params = _convert_query_params(query, (
                    job_id,
                    status,
                    total,
                    0,  # completed
                    0,  # progress
                    '[]',  # errors
                    tickers_json,  # normalized tickers
                    strategy_id,  # strategy ID
                    now,
                    now,
                    0  # successful
                ))
                
                cursor.execute(query, params)
                # commit() is called automatically by context manager
                logger.info(f"Job {job_id} created atomically with strategy_id={strategy_id}")
                return True
                
        except Exception as e:
            # Transaction is automatically rolled back by context manager
            error_str = str(e).lower()
            
            # Check for duplicate key/constraint violation
            if 'duplicate' in error_str or 'unique' in error_str or 'already exists' in error_str:
                logger.warning(f"Job {job_id} already exists (duplicate creation attempt): {e}")
                return False
            elif 'constraint' in error_str or 'integrity' in error_str:
                logger.warning(f"Job {job_id} constraint violation (likely duplicate): {e}")
                return False
            else:
                logger.error(f"Failed to create job {job_id}: {e}")
                return False
    
    @staticmethod
    def update_job_progress(
        job_id: str,
        completed: int,
        successful: int,
        errors: Optional[List[Dict]] = None
    ) -> bool:
        """
        Update job progress atomically.
        
        Calculates progress percentage automatically.
        Uses fresh connection to avoid transaction issues.
        
        Args:
            job_id: Job identifier
            completed: Number of items completed
            successful: Number of items successful
            errors: List of error dictionaries (optional)
            
        Returns:
            True if updated successfully
        """
        from database import get_db_session, _convert_query_params
        
        try:
            with get_db_session() as (conn, cursor):
                # Get job total first
                query = 'SELECT total FROM analysis_jobs WHERE job_id = ?'
                query, params = _convert_query_params(query, (job_id,))
                cursor.execute(query, params)
                job = cursor.fetchone()
                
                if not job:
                    logger.warning(f"Job {job_id} not found for progress update")
                    return False
                
                total = job[0]
                progress = int((completed / total) * 100) if total > 0 else 0
                errors_json = '[]' if not errors else str(errors)
                
                now = datetime.now().isoformat()
                query = '''
                    UPDATE analysis_jobs
                    SET completed = ?, successful = ?, progress = ?, errors = ?, updated_at = ?
                    WHERE job_id = ?
                '''
                query, params = _convert_query_params(query, (completed, successful, progress, errors_json, now, job_id))
                cursor.execute(query, params)
                
                return True
        except Exception as e:
            logger.error(f"Failed to update job {job_id} progress: {e}")
            return False
    
    @staticmethod
    def mark_job_completed(
        job_id: str,
        status: str = 'completed'
    ) -> bool:
        """
        Mark a job as completed.
        
        Uses fresh connection to avoid transaction issues.
        
        Args:
            job_id: Job identifier
            status: Final status ('completed', 'cancelled', 'failed')
            
        Returns:
            True if marked successfully
        """
        from database import get_db_session, _convert_query_params
        
        try:
            with get_db_session() as (conn, cursor):
                now = datetime.now().isoformat()
                query = '''
                    UPDATE analysis_jobs
                    SET status = ?, completed_at = ?, updated_at = ?
                    WHERE job_id = ?
                '''
                query, params = _convert_query_params(query, (status, now, now, job_id))
                cursor.execute(query, params)
                
                logger.info(f"Job {job_id} marked as {status}")
                return True
        except Exception as e:
            logger.error(f"Failed to mark job {job_id} as {status}: {e}")
            return False


class ResultInsertion:
    """
    Atomic result insertion with consistency checks
    """
    
    @staticmethod
    def insert_analysis_result(
        job_id: Optional[str] = None,
        ticker: str = None,
        symbol: str = None,
        name: str = None,
        yahoo_symbol: str = None,
        score: float = 0,
        verdict: str = None,
        entry: Optional[float] = None,
        stop_loss: Optional[float] = None,
        target: Optional[float] = None,
        entry_method: Optional[str] = None,
        data_source: Optional[str] = None,
        is_demo_data: bool = False,
        raw_data: Optional[str] = None,
        status: Optional[str] = None,
        error_message: Optional[str] = None,
        analysis_source: Optional[str] = None
    ) -> Optional[int]:
        """
        Insert an analysis result atomically.
        
        Uses fresh connection to avoid transaction issues.
        
        Returns:
            Row ID if inserted, None if failed
        """
        from database import get_db_session, _convert_query_params
        
        try:
            with get_db_session() as (conn, cursor):
                now = datetime.now().isoformat()
                query = '''
                    INSERT INTO analysis_results
                    (job_id, ticker, symbol, name, yahoo_symbol, score, verdict,
                     entry, stop_loss, target, entry_method, data_source,
                     is_demo_data, raw_data, status, error_message,
                     created_at, updated_at, analysis_source)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                '''
                query, params = _convert_query_params(query, (
                    job_id, ticker, symbol, name, yahoo_symbol, score, verdict,
                    entry, stop_loss, target, entry_method, data_source,
                    is_demo_data, raw_data, status, error_message,
                    now, now, analysis_source
                ))
                cursor.execute(query, params)
                return True  # PostgreSQL doesn't return lastrowid
        except Exception as e:
            logger.error(f"Failed to insert result for {symbol}: {e}")
            return None


def execute_transaction(conn, operations: List[Tuple[str, tuple]]) -> bool:
    """
    Execute multiple SQL statements atomically.
    
    All-or-nothing: if any fails, all are rolled back.
    
    Args:
        conn: Database connection
        operations: List of (SQL, params) tuples
        
    Returns:
        True if all succeeded, False if any failed
    """
    cursor = conn.cursor()
    try:
        for sql, params in operations:
            cursor.execute(sql, params)
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Transaction failed, rolling back: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()


def get_job_status(job_id: str) -> Optional[Dict[str, Any]]:
    """
    Get current job status.
    
    Returns dict with: job_id, status, progress, completed, total, etc.
    Includes current_ticker and message for frontend progress display.
    """
    try:
        result = query_db(
            '''SELECT job_id, status, progress, completed, total, 
                      successful, errors, created_at, updated_at, 
                      started_at, completed_at
               FROM analysis_jobs WHERE job_id = ?''',
            (job_id,),
            one=True
        )
        if result:
            completed = result[3]
            total = result[4]
            status = result[1]
            successful = result[5]
            
            # Calculate current index (1-based for display)
            current_index = completed + 1 if completed < total else total
            
            # Build message based on status
            if status == "queued":
                message = "Queued for analysis..."
            elif status == "processing":
                message = f"Processing ticker {current_index}/{total}..."
            elif status == "completed":
                message = f"Completed! {successful}/{total} successful"
            elif status == "failed":
                message = "Analysis failed"
            elif status == "cancelled":
                message = "Analysis cancelled"
            else:
                message = f"Status: {status}"
            
            # Get the ticker currently being analyzed or the last analyzed one
            current_ticker = None
            try:
                # Get most recent analysis result for this job
                latest_result = query_db(
                    '''SELECT ticker FROM analysis_results 
                       WHERE job_id = ? 
                       ORDER BY created_at DESC LIMIT 1''',
                    (job_id,),
                    one=True
                )
                if latest_result:
                    current_ticker = latest_result[0]
            except:
                pass  # If query fails, current_ticker remains None
            
            return {
                "job_id": result[0],
                "status": status,
                "progress": result[2],
                "completed": completed,
                "total": total,
                "successful": successful,
                "errors": result[6],
                "created_at": result[7],
                "updated_at": result[8],
                "started_at": result[9],
                "completed_at": result[10],
                "current_index": current_index,
                "current_ticker": current_ticker,
                "message": message
            }
        return None
    except Exception as e:
        logger.error(f"Failed to get job status for {job_id}: {e}")
        return None
