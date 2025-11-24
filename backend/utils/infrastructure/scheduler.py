import logging
import os
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    SCHEDULER_AVAILABLE = True
except ImportError:
    SCHEDULER_AVAILABLE = False
    BackgroundScheduler = None

# Initialize logger at module import time (used by functions below)
logger = logging.getLogger('trading_analyzer')

def get_log_directory():
    """
    Get log directory from environment variable with robust fallback.
    
    Priority:
    1. LOG_DIR environment variable (if set and valid)
    2. Fallback: project logs directory relative to this file
    
    Returns:
        pathlib.Path: Resolved absolute path to log directory
    
    Raises:
        ValueError: If computed path cannot be resolved or accessed
    """
    log_dir_env = os.getenv('LOG_DIR')
    
    if log_dir_env:
        try:
            log_dir = Path(log_dir_env).resolve()
            logger.debug(f"Using LOG_DIR from environment: {log_dir}")
            return log_dir
        except Exception as e:
            logger.warning(f"LOG_DIR environment variable invalid ({log_dir_env}): {e}. Using fallback.")
    
    # Fallback: construct path relative to this file
    try:
        # This file: backend/utils/infrastructure/scheduler.py
        # Target: backend/logs
        fallback_dir = Path(__file__).resolve().parent.parent.parent / 'logs'
        logger.debug(f"Using fallback log directory: {fallback_dir}")
        return fallback_dir
    except Exception as e:
        raise ValueError(f"Failed to resolve log directory: {e}")

# clean_old_cache doesn't exist, will implement stub
def clean_old_cache(days=7):
    """Stub for cache cleaning"""
    pass

def update_nse_universe():
    """
    Fetch and update NSE stock universe
    Runs daily at 6:00 AM IST
    """
    try:
        logger.info("Starting NSE universe update")
        
        # NSE API endpoint
        url = "https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%2050"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Parse symbols
        symbols = []
        if 'data' in data:
            for item in data['data']:
                if 'symbol' in item:
                    symbols.append({
                        "symbol": f"{item['symbol']}.NS",
                        "name": item.get('meta', {}).get('companyName', item['symbol'])
                    })
        
        # Save to file
        data_path = os.getenv('DATA_PATH', './data')
        os.makedirs(data_path, exist_ok=True)
        
        output_file = os.path.join(data_path, 'nse_universe.json')
        
        result = {
            "symbols": symbols,
            "updated_on": datetime.now().strftime('%Y-%m-%d'),
            "count": len(symbols)
        }
        
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        # Archive copy
        archive_file = os.path.join(
            data_path,
            f"nse_universe_{datetime.now().strftime('%Y%m%d')}.json"
        )
        with open(archive_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        # Clean old archives (keep last 7 days)
        clean_old_archives(data_path, days=7)
        
        logger.info(f"NSE universe updated: {len(symbols)} symbols")
        
    except Exception as e:
        logger.error(f"NSE universe update failed: {str(e)}")

def clean_old_archives(data_path, days=7):
    """Remove archive files older than specified days"""
    from datetime import timedelta
    
    try:
        cutoff_date = datetime.now() - timedelta(days=days)
        removed_count = 0
        
        for filename in os.listdir(data_path):
            if filename.startswith('nse_universe_') and filename.endswith('.json'):
                if filename == 'nse_universe.json':
                    continue
                
                filepath = os.path.join(data_path, filename)
                file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                
                if file_time < cutoff_date:
                    os.remove(filepath)
                    removed_count += 1
        
        if removed_count > 0:
            logger.info(f"Cleaned {removed_count} old archive files")
            
    except Exception as e:
        logger.error(f"Error cleaning archives: {str(e)}")

def compress_logs():
    """
    Compress old log files
    Runs weekly on Sunday midnight
    """
    try:
        import gzip
        import shutil
        
        logger.info("Starting log compression")
        
        # Get log directory with environment variable support
        log_dir = get_log_directory()
        archive_dir = log_dir / 'archive'
        
        # Create archive directory with permission error handling
        try:
            archive_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Archive directory ensured: {archive_dir}")
        except PermissionError as e:
            logger.exception(f"Permission denied creating archive directory {archive_dir}: {e}")
            return
        except OSError as e:
            logger.exception(f"OS error creating archive directory {archive_dir}: {e}")
            return
        
        log_file = log_dir / 'app.log'
        
        if log_file.exists():
            try:
                # Create compressed archive
                archive_name = f"app_{datetime.now().strftime('%Y%m%d')}.log.gz"
                archive_path = archive_dir / archive_name
                
                with open(log_file, 'rb') as f_in:
                    with gzip.open(archive_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                
                logger.info(f"Log compressed to {archive_name}")
            except PermissionError as e:
                logger.exception(f"Permission denied compressing log file {log_file}: {e}")
            except IOError as e:
                logger.exception(f"IO error during log compression: {e}")
        else:
            logger.debug(f"No log file found at {log_file}")
        
    except ValueError as e:
        logger.exception(f"Failed to resolve log directory for compression: {e}")
    except Exception as e:
        logger.exception(f"Log compression failed: {str(e)}")

def clean_old_data():
    """
    Clean old cached data and logs
    Runs daily at 3:00 AM IST
    """
    try:
        logger.info("Starting data cleanup")
        
        # Clean cache
        clean_old_cache(days=7)
        
        # Clean old logs
        log_dir = get_log_directory()
        archive_dir = log_dir / 'archive'
        
        if archive_dir.exists():
            try:
                cutoff_date = datetime.now() - timedelta(days=15)
                removed_count = 0
                
                for filepath in archive_dir.iterdir():
                    if filepath.is_file():
                        try:
                            file_time = datetime.fromtimestamp(filepath.stat().st_mtime)
                            
                            if file_time < cutoff_date:
                                filepath.unlink()
                                removed_count += 1
                                logger.debug(f"Deleted old log archive: {filepath.name}")
                        except (OSError, ValueError) as e:
                            logger.warning(f"Failed to process/delete archive file {filepath.name}: {e}")
                            continue
                
                if removed_count > 0:
                    logger.info(f"Cleaned {removed_count} old log archives")
            except PermissionError as e:
                logger.exception(f"Permission denied accessing archive directory {archive_dir}: {e}")
            except OSError as e:
                logger.exception(f"OS error while cleaning archives in {archive_dir}: {e}")
        else:
            logger.debug(f"Archive directory does not exist: {archive_dir}")
        
        logger.info("Data cleanup completed")
        
    except ValueError as e:
        logger.exception(f"Failed to resolve log directory for cleanup: {e}")
    except Exception as e:
        logger.exception(f"Data cleanup failed: {str(e)}")

def start_scheduler():
    """Start background scheduler for cron jobs"""
    if not SCHEDULER_AVAILABLE:
        logger.warning("apscheduler not installed - background tasks disabled")
        return None
    
    scheduler = BackgroundScheduler()
    
    # NSE universe update - daily at 6:00 AM IST
    scheduler.add_job(update_nse_universe, 'cron', hour=6, minute=0)
    
    # Data cleanup - daily at 3:00 AM IST
    scheduler.add_job(clean_old_data, 'cron', hour=3, minute=0)
    
    # Log compression - weekly on Sunday at midnight
    scheduler.add_job(compress_logs, 'cron', day_of_week='sun', hour=0, minute=0)
    
    scheduler.start()
    logger.info("Background scheduler started")
    return scheduler
