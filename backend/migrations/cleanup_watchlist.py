"""
Migration to clean up orphaned/duplicate watchlist entries
This runs automatically on app startup
"""
import logging
from database import query_db, execute_db

logger = logging.getLogger(__name__)

def migrate_cleanup_watchlist_duplicates(db=None):
    """Remove duplicate watchlist entries, keeping the oldest"""
    try:
        logger.info("[MIGRATION] Checking for duplicate watchlist entries...")
        
        # Check for duplicates
        duplicates = query_db("""
            SELECT LOWER(symbol), COUNT(*) as count
            FROM watchlist
            GROUP BY LOWER(symbol)
            HAVING COUNT(*) > 1
        """)
        
        if not duplicates:
            logger.info("[MIGRATION] No duplicates found")
            return
        
        dup_list = []
        for dup in duplicates:
            if isinstance(dup, (tuple, list)):
                dup_list.append(f"{dup[0]} (count: {dup[1]})")
            else:
                d = dict(dup)
                dup_list.append(f"{d.get('symbol', 'UNKNOWN')} (count: {d.get('count', 0)})")
        
        logger.warning(f"[MIGRATION] Found duplicates: {', '.join(dup_list)}")
        
        # Delete duplicates, keeping oldest
        deleted = execute_db("""
            DELETE FROM watchlist 
            WHERE id NOT IN (
                SELECT MIN(id) FROM watchlist GROUP BY LOWER(symbol)
            )
        """)
        
        logger.info(f"[MIGRATION] Cleaned up {deleted} duplicate watchlist entries")
        
    except Exception as e:
        logger.error(f"[MIGRATION] Error cleaning up watchlist duplicates: {e}")
        # Don't fail the migration, just log it
