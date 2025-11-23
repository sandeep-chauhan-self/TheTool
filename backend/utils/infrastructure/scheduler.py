import logging
import os
import json
import requests
from datetime import datetime, timedelta

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    SCHEDULER_AVAILABLE = True
except ImportError:
    SCHEDULER_AVAILABLE = False
    BackgroundScheduler = None

# clean_old_cache doesn't exist, will implement stub
def clean_old_cache(days=7):
    """Stub for cache cleaning"""
    pass

logger = logging.getLogger('trading_analyzer')

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
        
        archive_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'logs', 'archive'))
        os.makedirs(archive_dir, exist_ok=True)
        
        log_dir = os.path.dirname(archive_dir)
        log_file = os.path.join(log_dir, 'app.log')
        
        if os.path.exists(log_file):
            # Create compressed archive
            archive_name = f"app_{datetime.now().strftime('%Y%m%d')}.log.gz"
            archive_path = os.path.join(archive_dir, archive_name)
            
            with open(log_file, 'rb') as f_in:
                with gzip.open(archive_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            logger.info(f"Log compressed to {archive_name}")
        
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
        archive_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'logs', 'archive'))
        
        if os.path.exists(archive_dir):
            cutoff_date = datetime.now() - timedelta(days=15)
            removed_count = 0
            
            for filename in os.listdir(archive_dir):
                filepath = os.path.join(archive_dir, filename)
                file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                
                if file_time < cutoff_date:
                    os.remove(filepath)
                    removed_count += 1
            
            if removed_count > 0:
                logger.info(f"Cleaned {removed_count} old log archives")
        
        logger.info("Data cleanup completed")
        
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
