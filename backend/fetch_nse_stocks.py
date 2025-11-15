"""
Fetch all NSE stock symbols with company names and save to CSV/JSON/TXT
This script fetches ALL NSE equity stocks (2500+) from NSE India with complete information
"""

import requests
import json
import csv
import logging
from pathlib import Path
import time
import pandas as pd
from io import StringIO

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# NSE API endpoints for complete equity list
NSE_EQUITY_LIST_URL = 'https://www.nseindia.com/api/equity-stockIndices?index=SECURITIES%20IN%20F%26O'
NSE_ALL_EQUITY_URL = 'https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv'  # Complete equity list

NSE_EQUITY_LIST_URL = 'https://www.nseindia.com/api/equity-stockIndices?index=SECURITIES%20IN%20F%26O'
NSE_ALL_EQUITY_URL = 'https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv'  # Complete equity list

def fetch_all_nse_stocks_from_csv():
    """
    Fetch complete NSE equity list from official NSE CSV
    Returns: List of dictionaries with symbol and company name
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/csv,application/csv,text/plain',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.nseindia.com/'
    }
    
    session = requests.Session()
    all_stocks = []
    
    try:
        logger.info("Fetching complete NSE equity list from official CSV...")
        
        # First visit main page to get cookies
        session.get('https://www.nseindia.com/', headers=headers, timeout=10)
        time.sleep(1)
        
        # Fetch the CSV
        response = session.get(NSE_ALL_EQUITY_URL, headers=headers, timeout=15)
        
        if response.status_code == 200:
            # Parse CSV
            csv_data = StringIO(response.text)
            df = pd.read_csv(csv_data)
            
            # Expected columns: SYMBOL, NAME OF COMPANY, SERIES, etc.
            if 'SYMBOL' in df.columns and 'NAME OF COMPANY' in df.columns:
                # Filter only EQ (Equity) series stocks
                if 'SERIES' in df.columns:
                    df = df[df['SERIES'] == 'EQ']
                
                for _, row in df.iterrows():
                    symbol = str(row['SYMBOL']).strip()
                    name = str(row['NAME OF COMPANY']).strip()
                    
                    if symbol and symbol != 'nan':
                        all_stocks.append({
                            'symbol': symbol,
                            'name': name,
                            'yahoo_symbol': f"{symbol}.NS"
                        })
                
                logger.info(f"? Fetched {len(all_stocks)} stocks from NSE CSV")
            else:
                logger.error(f"Unexpected CSV format. Columns: {df.columns.tolist()}")
        else:
            logger.error(f"Failed to fetch CSV: HTTP {response.status_code}")
            
    except Exception as e:
        logger.error(f"Failed to fetch from NSE CSV: {e}")
    finally:
        session.close()
    
    return all_stocks


def fetch_nse_stocks_from_api():
    """
    Fetch NSE stocks from NSE India API (fallback method)
    Returns: List of dictionaries with symbol and company name
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.nseindia.com/'
    }
    
    all_stocks = []
    session = requests.Session()
    
    try:
        logger.info("Fetching stocks from NSE API (fallback)...")
        
        # Visit main page first
        session.get('https://www.nseindia.com/', headers=headers, timeout=10)
        time.sleep(1)
        
        # Fetch from multiple indices
        indices = [
            'NIFTY%2050', 'NIFTY%20NEXT%2050', 'NIFTY%20100', 'NIFTY%20200', 
            'NIFTY%20500', 'NIFTY%20MIDCAP%2050', 'NIFTY%20MIDCAP%20100', 
            'NIFTY%20SMALLCAP%20100', 'NIFTY%20SMALLCAP%20250'
        ]
        
        for index in indices:
            try:
                url = f'https://www.nseindia.com/api/equity-stockIndices?index={index}'
                response = session.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if 'data' in data:
                        for stock in data['data']:
                            if 'symbol' in stock:
                                symbol = stock['symbol']
                                # Skip index names
                                if not any(x in symbol for x in ['NIFTY', 'INDIA VIX']):
                                    all_stocks.append({
                                        'symbol': symbol,
                                        'name': symbol,  # API doesn't provide full names
                                        'yahoo_symbol': f"{symbol}.NS"
                                    })
                
                time.sleep(0.5)
            except Exception as e:
                logger.warning(f"Failed to fetch {index}: {e}")
                continue
        
        # Remove duplicates
        seen = set()
        unique_stocks = []
        for stock in all_stocks:
            if stock['symbol'] not in seen:
                seen.add(stock['symbol'])
                unique_stocks.append(stock)
        
        logger.info(f"? Fetched {len(unique_stocks)} unique stocks from API")
        return unique_stocks
        
    except Exception as e:
        logger.error(f"Failed to fetch from NSE API: {e}")
        return []
    finally:
        session.close()


def get_fallback_stocks():
    """
    Extended fallback list of popular NSE stocks with proper names
    """
    return [
        {"symbol": "RELIANCE", "name": "Reliance Industries Ltd."},
        {"symbol": "TCS", "name": "Tata Consultancy Services Ltd."},
        {"symbol": "HDFCBANK", "name": "HDFC Bank Ltd."},
        {"symbol": "INFY", "name": "Infosys Ltd."},
        {"symbol": "ICICIBANK", "name": "ICICI Bank Ltd."},
        {"symbol": "HINDUNILVR", "name": "Hindustan Unilever Ltd."},
        {"symbol": "ITC", "name": "ITC Ltd."},
        {"symbol": "SBIN", "name": "State Bank of India"},
        {"symbol": "BHARTIARTL", "name": "Bharti Airtel Ltd."},
        {"symbol": "KOTAKBANK", "name": "Kotak Mahindra Bank Ltd."},
        {"symbol": "LT", "name": "Larsen & Toubro Ltd."},
        {"symbol": "AXISBANK", "name": "Axis Bank Ltd."},
        {"symbol": "ASIANPAINT", "name": "Asian Paints Ltd."},
        {"symbol": "MARUTI", "name": "Maruti Suzuki India Ltd."},
        {"symbol": "TITAN", "name": "Titan Company Ltd."},
        {"symbol": "BAJFINANCE", "name": "Bajaj Finance Ltd."},
        {"symbol": "HCLTECH", "name": "HCL Technologies Ltd."},
        {"symbol": "SUNPHARMA", "name": "Sun Pharmaceutical Industries Ltd."},
        {"symbol": "ULTRACEMCO", "name": "UltraTech Cement Ltd."},
        {"symbol": "NESTLEIND", "name": "Nestle India Ltd."},
        {"symbol": "WIPRO", "name": "Wipro Ltd."},
        {"symbol": "TATAMOTORS", "name": "Tata Motors Ltd."},
        {"symbol": "ONGC", "name": "Oil & Natural Gas Corporation Ltd."},
        {"symbol": "NTPC", "name": "NTPC Ltd."},
        {"symbol": "POWERGRID", "name": "Power Grid Corporation of India Ltd."},
        {"symbol": "M&M", "name": "Mahindra & Mahindra Ltd."},
        {"symbol": "TECHM", "name": "Tech Mahindra Ltd."},
        {"symbol": "ADANIPORTS", "name": "Adani Ports and Special Economic Zone Ltd."},
        {"symbol": "COALINDIA", "name": "Coal India Ltd."},
        {"symbol": "TATASTEEL", "name": "Tata Steel Ltd."},
    ]


def save_to_csv(stocks, output_file='data/nse_stocks_complete.csv'):
    """Save stocks to CSV with all details"""
    try:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save as CSV
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['symbol', 'name', 'yahoo_symbol'])
            writer.writeheader()
            writer.writerows(stocks)
        
        logger.info(f"? Saved {len(stocks)} stocks to {output_file}")
        return True
    except Exception as e:
        logger.error(f"Failed to save CSV: {e}")
        return False


def save_stocks_to_files(stocks):
    """
    Save stock symbols to multiple formats (TXT, JSON, CSV)
    """
    try:
        # Ensure data directory exists
        data_dir = Path(__file__).parent / 'data'
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # Sort stocks alphabetically by symbol
        sorted_stocks = sorted(stocks, key=lambda x: x['symbol'])
        
        # 1. Save CSV (primary source with all details)
        csv_file = data_dir / 'nse_stocks_complete.csv'
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['symbol', 'name', 'yahoo_symbol'])
            writer.writeheader()
            writer.writerows(sorted_stocks)
        logger.info(f"? Saved CSV: {csv_file}")
        
        # 2. Save TXT (Yahoo Finance format for backward compatibility)
        txt_file = data_dir / 'nse_stocks.txt'
        with open(txt_file, 'w', encoding='utf-8') as f:
            for stock in sorted_stocks:
                f.write(f"{stock['yahoo_symbol']}\n")
        logger.info(f"? Saved TXT: {txt_file}")
        
        # 3. Save JSON (with complete metadata)
        json_file = data_dir / 'nse_stocks.json'
        json_data = {
            'count': len(sorted_stocks),
            'last_updated': time.strftime('%Y-%m-%d %H:%M:%S'),
            'source': 'NSE India Official',
            'stocks': sorted_stocks
        }
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        logger.info(f"? Saved JSON: {json_file}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to save files: {e}")
        return False


def main():
    """
    Main function to fetch and save ALL NSE stocks with company names
    """
    logger.info("=" * 60)
    logger.info("NSE Stock Fetcher - Complete List (2500+ stocks)")
    logger.info("=" * 60)
    
    all_stocks = []
    
    # Method 1: Try fetching from official NSE CSV (contains ALL stocks)
    logger.info("\n[Method 1] Fetching from NSE CSV (complete list)...")
    stocks_from_csv = fetch_all_nse_stocks_from_csv()
    
    if stocks_from_csv and len(stocks_from_csv) > 1000:
        logger.info(f"? Successfully fetched {len(stocks_from_csv)} stocks from CSV")
        all_stocks = stocks_from_csv
    else:
        # Method 2: Fallback to API (limited to indices)
        logger.info("\n[Method 2] CSV failed, trying NSE API (indices only)...")
        stocks_from_api = fetch_nse_stocks_from_api()
        
        if stocks_from_api and len(stocks_from_api) > 100:
            logger.info(f"? Fetched {len(stocks_from_api)} stocks from API")
            all_stocks = stocks_from_api
        else:
            # Method 3: Ultimate fallback
            logger.warning("\n[Method 3] Using fallback list...")
            fallback = get_fallback_stocks()
            all_stocks = fallback
    
    # Ensure all stocks have proper format
    for stock in all_stocks:
        if 'yahoo_symbol' not in stock:
            stock['yahoo_symbol'] = f"{stock['symbol']}.NS"
        if 'name' not in stock or not stock['name']:
            stock['name'] = stock['symbol']  # Use symbol as name if missing
    
    if all_stocks:
        logger.info(f"\n{'=' * 60}")
        logger.info(f"Total stocks collected: {len(all_stocks)}")
        logger.info(f"{'=' * 60}")
        
        # Save to multiple formats
        if save_stocks_to_files(all_stocks):
            logger.info("\n? SUCCESS! NSE stock list created in multiple formats.")
            logger.info("Files created:")
            logger.info("  - data/nse_stocks_complete.csv (CSV with names)")
            logger.info("  - data/nse_stocks.txt (Yahoo symbols)")
            logger.info("  - data/nse_stocks.json (JSON with metadata)")
            
            # Show sample
            logger.info("\nSample stocks:")
            for stock in all_stocks[:5]:
                logger.info(f"  {stock['symbol']:15} | {stock['name'][:40]:40} | {stock['yahoo_symbol']}")
            
        else:
            logger.error("\n? FAILED to save stock list")
            return False
    else:
        logger.error("\n? FAILED to fetch any stocks")
        return False
    
    return True


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
