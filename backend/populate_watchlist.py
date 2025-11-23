"""
Bulk populate watchlist with all NSE stocks from CSV
"""
import csv
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from database import get_db_connection, _convert_query_params
from utils.logger import setup_logger

logger = setup_logger()

def populate_watchlist():
    """Populate watchlist with all NSE stocks from CSV"""
    csv_path = Path(__file__).parent / "data" / "nse_stocks_complete.csv"
    
    if not csv_path.exists():
        logger.error(f"CSV file not found: {csv_path}")
        return 0
    
    conn = get_db_connection()
    conn.row_factory = None  # Don't need row factory for bulk insert
    cursor = conn.cursor()
    
    # Read CSV and prepare data
    stocks_to_insert = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            symbol = row['symbol'].strip()
            name = row.get('name', '').strip()
            yahoo_symbol = row.get('yahoo_symbol', '').strip()
            
            # Use symbol as ticker, yahoo_symbol as symbol
            ticker = yahoo_symbol if yahoo_symbol else f"{symbol}.NS"
            stocks_to_insert.append((ticker, symbol, name))
    
    logger.info(f"Read {len(stocks_to_insert)} stocks from CSV")
    
    # Clear existing watchlist
    cursor.execute("DELETE FROM watchlist")
    logger.info("Cleared existing watchlist")
    
    # Bulk insert
    inserted = 0
    failed = 0
    
    for ticker, symbol, notes in stocks_to_insert:
        try:
            query = "INSERT INTO watchlist (ticker, symbol, notes) VALUES (?, ?, ?)"
            query, args = _convert_query_params(query, (ticker, symbol, notes))
            cursor.execute(query, args)
            inserted += 1
            if inserted % 100 == 0:
                logger.info(f"Inserted {inserted} stocks...")
        except Exception as e:
            logger.warning(f"Failed to insert {ticker}: {e}")
            failed += 1
    
    conn.commit()
    conn.close()
    
    logger.info(f"✅ Watchlist population complete:")
    logger.info(f"   - Inserted: {inserted}")
    logger.info(f"   - Failed: {failed}")
    logger.info(f"   - Total: {len(stocks_to_insert)}")
    
    return inserted


if __name__ == "__main__":
    count = populate_watchlist()
    print(f"\n✅ Successfully added {count} stocks to watchlist")
