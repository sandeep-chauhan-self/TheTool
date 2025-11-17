"""
Test script to verify SSL certificate fix for Yahoo Finance
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.fetch_data import fetch_ticker_data

def test_fetch():
    """Test fetching data from Yahoo Finance"""
    print("Testing Yahoo Finance data fetch with SSL fix...")
    print("-" * 50)
    
    # Test with multiple tickers
    tickers = ["AAPL", "TCS.NS", "INFY.NS"]
    
    for ticker in tickers:
        print(f"\nFetching data for {ticker}...")
        
        try:
            df = fetch_ticker_data(ticker, period="5d")
            print(f"? Success! Retrieved {len(df)} rows of data")
            print(f"Latest close: {df['Close'].iloc[-1]:.2f}")
            return True
        except Exception as e:
            print(f"? Error: {str(e)}")
            continue
    
    print("\n? All tickers failed")
    return False

if __name__ == "__main__":
    success = test_fetch()
    sys.exit(0 if success else 1)
