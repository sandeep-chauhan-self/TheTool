"""
Celery Tasks for Background Stock Analysis
"""

from celery_config import celery_app
from utils.compute_score import analyze_ticker
from database import get_db_connection, cleanup_old_analyses, _convert_query_params
from datetime import datetime
import logging
import json
import traceback

# Configure logging with DEBUG level
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger('celery_tasks')
logger.setLevel(logging.DEBUG)


@celery_app.task(bind=True, name='analyze_stocks_batch')
def analyze_stocks_batch(self, job_id, tickers, indicators=None, capital=100000, use_demo=True):
    """
    Background task to analyze multiple stocks
    
    Args:
        self: Celery task instance (for progress updates)
        job_id: Unique job identifier
        tickers: List of stock symbols to analyze
        indicators: List of indicators to use (None = all)
        capital: Capital for position sizing
        use_demo: Use demo data if real data fails
    
    Returns:
        dict with job results
    """
    total = len(tickers)
    completed = 0
    errors = []
    batch_size = 100
    
    # Update job status in database
    def update_job_status(status, progress=None, error=None):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        update_data = {
            'status': status,
            'completed': completed,
            'updated_at': datetime.now().isoformat()
        }
        
        if progress is not None:
            update_data['progress'] = progress
        
        if error:
            update_data['errors'] = json.dumps(errors)
        
        if status == 'completed' or status == 'failed':
            update_data['completed_at'] = datetime.now().isoformat()
        
        # Build UPDATE query with parameter conversion
        set_clause = ', '.join([f"{key} = ?" for key in update_data.keys()])
        values = list(update_data.values()) + [job_id]
        
        query = f'''
            UPDATE analysis_jobs
            SET {set_clause}
            WHERE job_id = ?
        '''
        
        # Convert query parameters for database compatibility
        query, values = _convert_query_params(query, values)
        cursor.execute(query, values)
        
        conn.commit()
        conn.close()
    
    try:
        logger.info("=" * 60)
        logger.info(f"CELERY TASK STARTED - Job ID: {job_id}")
        logger.info("=" * 60)
        logger.info(f"Total stocks to analyze: {total}")
        logger.info(f"Indicators: {indicators if indicators else 'ALL'}")
        logger.info(f"Capital: {capital}")
        logger.info(f"Use demo data: {use_demo}")
        logger.info(f"Batch size: {batch_size}")
        
        update_job_status('processing', 0)
        logger.info(f"Job {job_id}: Status updated to 'processing'")
        
        # Process in batches
        for i in range(0, total, batch_size):
            batch = tickers[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total + batch_size - 1) // batch_size
            
            logger.info("=" * 60)
            logger.info(f"Job {job_id}: BATCH {batch_num}/{total_batches}")
            logger.info(f"Batch contains {len(batch)} stocks: {batch}")
            logger.info("=" * 60)
            
            for idx, ticker in enumerate(batch, 1):
                logger.debug(f"Job {job_id}: Processing stock {idx}/{len(batch)} in batch {batch_num}")
                
                # Check if task was revoked (cancelled)
                if self.is_aborted():
                    logger.warning(f"Job {job_id}: Task cancelled by user")
                    update_job_status('cancelled')
                    return {
                        'job_id': job_id,
                        'status': 'cancelled',
                        'completed': completed,
                        'total': total,
                        'errors': errors
                    }
                
                try:
                    logger.info(f"Job {job_id}: START analyzing {ticker} ({completed + 1}/{total})")
                    result = analyze_ticker(ticker, indicators, capital, use_demo_data=use_demo)
                    logger.debug(f"Job {job_id}: Analysis result for {ticker}: {result.get('verdict', 'UNKNOWN')}, score={result.get('score', 0)}")
                    
                    # Check for data validation failure
                    if not result.get('data_valid', True):
                        error_msg = f"Data validation failed: {result.get('validation_errors', [])}"
                        errors.append({'ticker': ticker, 'error': error_msg})
                        logger.warning(f"Job {job_id}: {ticker} - {error_msg}")
                        completed += 1
                        progress = int((completed / total) * 100)
                        logger.info(f"Job {job_id}: Progress: {progress}% ({completed}/{total})")
                        continue
                    
                    # Store in database
                    logger.debug(f"Job {job_id}: Storing {ticker} results in database")
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    query = '''
                        INSERT INTO analysis_results 
                        (ticker, score, verdict, entry, stop_loss, target, entry_method, 
                         data_source, is_demo_data, raw_data, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    '''
                    query, args = _convert_query_params(query, (
                        ticker,
                        result['score'],
                        result['verdict'],
                        result['entry'],
                        result['stop'],
                        result['target'],
                        result.get('entry_method', 'UNKNOWN'),
                        result.get('data_source', 'unknown'),
                        result.get('is_demo_data', False),
                        str(result.get('indicators', [])),
                        datetime.now().isoformat()
                    ))
                    cursor.execute(query, args)
                    conn.commit()
                    conn.close()
                    logger.debug(f"Job {job_id}: {ticker} saved to database")
                    
                    # Cleanup old analyses (keep last 10)
                    cleanup_old_analyses(ticker, keep_last=10)
                    
                    completed += 1
                    progress = int((completed / total) * 100)
                    
                    # Update progress every stock for single stock or every 10 for batches
                    update_frequency = 1 if total == 1 else 10
                    if completed % update_frequency == 0 or completed == total:
                        logger.info(f"Job {job_id}: Updating progress to {progress}% ({completed}/{total})")
                        update_job_status('processing', progress)
                        self.update_state(
                            state='PROGRESS',
                            meta={'completed': completed, 'total': total, 'progress': progress}
                        )
                    
                    logger.info(f"Job {job_id}: ? {ticker} COMPLETED ({completed}/{total}, {progress}%)")
                    
                except Exception as e:
                    error_msg = str(e)
                    errors.append({'ticker': ticker, 'error': error_msg})
                    logger.error(f"Job {job_id}: ? FAILED to analyze {ticker}: {error_msg}")
                    logger.error(traceback.format_exc())
                    completed += 1
                    progress = int((completed / total) * 100)
                    logger.info(f"Job {job_id}: Progress: {progress}% ({completed}/{total}) - with error")
            
            # Log batch completion
            logger.info(f"Job {job_id}: ? Batch {batch_num}/{total_batches} completed")
        
        # Job completed
        logger.info("=" * 60)
        logger.info(f"Job {job_id}: ALL STOCKS ANALYZED")
        logger.info(f"Completed: {completed}/{total}")
        logger.info(f"Errors: {len(errors)}")
        logger.info("=" * 60)
        
        update_job_status('completed', 100)
        logger.info(f"Job {job_id}: Status updated to 'completed'")
        
        return {
            'job_id': job_id,
            'status': 'completed',
            'completed': completed,
            'total': total,
            'errors': errors,
            'progress': 100
        }
        
    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"Job {job_id}: CRITICAL ERROR")
        logger.error(f"Error: {str(e)}")
        logger.error(traceback.format_exc())
        logger.error("=" * 60)
        update_job_status('failed', error=str(e))
        raise
