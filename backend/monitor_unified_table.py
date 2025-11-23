"""
Monitoring script for unified table migration
Run every 6 hours for 48 hours to track stability
"""
import os
from datetime import datetime
import json

# Import config and database utilities
from config import config, DATABASE_PATH
from database import get_db_connection

LOG_FILE = os.path.join(os.path.dirname(__file__), 'migration_monitoring.log')

def log_metrics():
    """Collect and log key metrics"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'status': 'healthy'
        }
        
        # Total records
        cursor.execute("SELECT COUNT(*) FROM analysis_results")
        metrics['total_records'] = cursor.fetchone()[0]
        
        # By source
        cursor.execute("SELECT COUNT(*) FROM analysis_results WHERE analysis_source='watchlist'")
        metrics['watchlist_count'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM analysis_results WHERE analysis_source='bulk'")
        metrics['bulk_count'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM analysis_results WHERE analysis_source IS NULL")
        metrics['null_source_count'] = cursor.fetchone()[0]
        
        # Cross-visibility
        cursor.execute("""
            SELECT COUNT(DISTINCT symbol) 
            FROM (
                SELECT symbol, 
                       SUM(CASE WHEN analysis_source='watchlist' THEN 1 ELSE 0 END) as w,
                       SUM(CASE WHEN analysis_source='bulk' THEN 1 ELSE 0 END) as b
                FROM analysis_results
                WHERE symbol IS NOT NULL
                GROUP BY symbol
                HAVING w > 0 AND b > 0
            )
        """)
        metrics['cross_visible_stocks'] = cursor.fetchone()[0]
        
        # Recent activity (last 6 hours) - database-agnostic
        if config.DATABASE_TYPE == 'postgresql':
            cursor.execute("""
                SELECT COUNT(*) FROM analysis_results 
                WHERE created_at > NOW() - INTERVAL '6 hours'
            """)
        else:
            # SQLite
            cursor.execute("""
                SELECT COUNT(*) FROM analysis_results 
                WHERE created_at > datetime('now', '-6 hours')
            """)
        metrics['recent_analyses'] = cursor.fetchone()[0]
        
        # Database size - database-agnostic
        if config.DATABASE_TYPE == 'postgresql':
            cursor.execute("SELECT pg_database_size(current_database())")
            db_size_bytes = cursor.fetchone()[0]
            metrics['db_size_mb'] = round(db_size_bytes / (1024 * 1024), 2)
        else:
            # SQLite - use file size
            if os.path.exists(DATABASE_PATH):
                metrics['db_size_mb'] = round(os.path.getsize(DATABASE_PATH) / (1024 * 1024), 2)
            else:
                metrics['db_size_mb'] = 0
        
        # Check for errors
        cursor.execute("SELECT COUNT(*) FROM analysis_results WHERE status='failed'")
        metrics['failed_analyses'] = cursor.fetchone()[0]
        
        conn.close()
        
        # Write to log
        with open(LOG_FILE, 'a') as f:
            f.write(json.dumps(metrics) + '\n')
        
        # Print summary
        print("=" * 70)
        print(f"MONITORING REPORT - {metrics['timestamp']}")
        print("=" * 70)
        print(f"Status: {metrics['status']}")
        print(f"Total Records: {metrics['total_records']}")
        print(f"  - Watchlist: {metrics['watchlist_count']}")
        print(f"  - Bulk: {metrics['bulk_count']}")
        print(f"  - NULL source: {metrics['null_source_count']}")
        print(f"Cross-visible stocks: {metrics['cross_visible_stocks']}")
        print(f"Recent analyses (6h): {metrics['recent_analyses']}")
        print(f"Failed analyses: {metrics['failed_analyses']}")
        print(f"Database size: {metrics['db_size_mb']} MB")
        print("=" * 70)
        
        # Check for anomalies
        warnings = []
        
        if metrics['total_records'] < 2204:
            warnings.append("??  CRITICAL: Record count decreased!")
            metrics['status'] = 'warning'
        
        if metrics['null_source_count'] > 0:
            warnings.append(f"??  {metrics['null_source_count']} records with NULL analysis_source")
        
        if metrics['failed_analyses'] > 50:
            warnings.append(f"??  High failure rate: {metrics['failed_analyses']} failed")
        
        if warnings:
            print("\n".join(warnings))
            print("=" * 70)
        else:
            print("? All metrics within normal range")
            print("=" * 70)
        
        return metrics
        
    except Exception as e:
        print(f"? ERROR during monitoring: {e}")
        import traceback
        traceback.print_exc()
        
        error_metrics = {
            'timestamp': datetime.now().isoformat(),
            'status': 'error',
            'error': str(e)
        }
        
        with open(LOG_FILE, 'a') as f:
            f.write(json.dumps(error_metrics) + '\n')
        
        return error_metrics

def analyze_trends():
    """Analyze monitoring log for trends"""
    if not os.path.exists(LOG_FILE):
        print("No monitoring data yet")
        return
    
    print("\n" + "=" * 70)
    print("TREND ANALYSIS")
    print("=" * 70)
    
    with open(LOG_FILE, 'r') as f:
        logs = [json.loads(line) for line in f if line.strip()]
    
    if len(logs) < 2:
        print("Not enough data points for trend analysis")
        return
    
    # Compare first and last
    first = logs[0]
    last = logs[-1]
    
    print(f"Monitoring period: {len(logs)} data points")
    print(f"From: {first['timestamp']}")
    print(f"To:   {last['timestamp']}")
    print()
    
    if 'total_records' in first and 'total_records' in last:
        delta = last['total_records'] - first['total_records']
        print(f"Record growth: {delta:+d} ({first['total_records']} ? {last['total_records']})")
    
    if 'cross_visible_stocks' in first and 'cross_visible_stocks' in last:
        delta = last['cross_visible_stocks'] - first['cross_visible_stocks']
        print(f"Cross-visible stocks: {delta:+d} ({first['cross_visible_stocks']} ? {last['cross_visible_stocks']})")
    
    if 'db_size_mb' in first and 'db_size_mb' in last:
        delta = last['db_size_mb'] - first['db_size_mb']
        print(f"Database size: {delta:+.2f} MB ({first['db_size_mb']} ? {last['db_size_mb']})")
    
    # Check for errors
    error_count = sum(1 for log in logs if log.get('status') == 'error')
    warning_count = sum(1 for log in logs if log.get('status') == 'warning')
    
    print(f"\nHealth status:")
    print(f"  Errors: {error_count}")
    print(f"  Warnings: {warning_count}")
    print(f"  Healthy: {len(logs) - error_count - warning_count}")
    
    print("=" * 70)

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--trends':
        analyze_trends()
    else:
        log_metrics()
        print("\nTip: Run with --trends to see historical analysis")
