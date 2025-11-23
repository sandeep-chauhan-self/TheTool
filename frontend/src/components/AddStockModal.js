import { useEffect, useRef, useState } from 'react';
import { getAllNSEStocks } from '../api/api';

function AddStockModal({ onClose, onAdd, existingSymbols = [] }) {
  const [allStocks, setAllStocks] = useState([]);
  const [filteredStocks, setFilteredStocks] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedStocks, setSelectedStocks] = useState([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const dropdownRef = useRef(null);

  // Load stocks on mount - load all pages to have complete list
  useEffect(() => {
    const loadAllStocks = async () => {
      try {
        let allLoadedStocks = [];
        let currentPage = 1;
        let hasMore = true;
        
        // Load all 2,192 stocks by fetching all pages
        while (hasMore) {
          const data = await getAllNSEStocks(currentPage, 200);
          if (data && data.stocks) {
            allLoadedStocks = [...allLoadedStocks, ...data.stocks];
            currentPage++;
            hasMore = currentPage <= data.total_pages;
            setTotalPages(data.total_pages);
          } else {
            hasMore = false;
          }
        }
        
        // Filter out stocks already in watchlist
        const available = allLoadedStocks.filter(
          stock => !existingSymbols.includes(stock.yahoo_symbol)
        );
        
        setAllStocks(available);
        setFilteredStocks(available);
        setLoading(false);
      } catch (error) {
        console.error('Failed to load NSE stocks:', error);
        setLoading(false);
      }
    };
    
    loadAllStocks();
  }, [existingSymbols]);

  // Filter stocks based on search
  useEffect(() => {
    if (searchQuery.trim() === '') {
      setFilteredStocks(allStocks);
    } else {
      const query = searchQuery.toLowerCase();
      const filtered = allStocks.filter(stock => {
        const symbolMatch = stock.symbol.toLowerCase().includes(query);
        const nameMatch = stock.name.toLowerCase().includes(query);
        const yahooMatch = stock.yahoo_symbol.toLowerCase().includes(query);
        return symbolMatch || nameMatch || yahooMatch;
      });
      setFilteredStocks(filtered);
    }
  }, [searchQuery, allStocks]);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleStockSelect = (stock) => {
    // Add stock to selected list if not already selected
    if (!selectedStocks.find(s => s.yahoo_symbol === stock.yahoo_symbol)) {
      setSelectedStocks([...selectedStocks, stock]);
    }
    // Clear search to allow selecting next stock
    setSearchQuery('');
    setShowDropdown(false);
  };

  const handleRemoveStock = (yahooSymbol) => {
    setSelectedStocks(selectedStocks.filter(s => s.yahoo_symbol !== yahooSymbol));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (selectedStocks.length > 0) {
      // Add all selected stocks to watchlist
      selectedStocks.forEach(stock => {
        onAdd(stock.yahoo_symbol, stock.name);
      });
      setSearchQuery('');
      setSelectedStocks([]);
      onClose(); // Close modal after adding all stocks
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-md" ref={dropdownRef}>
        <h2 className="text-2xl font-bold mb-4">Add Stock to Watchlist</h2>
        
        {loading ? (
          <div className="text-center py-8">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <p className="mt-2 text-gray-600">Loading {allStocks.length === 0 ? 'all 2,192 NSE stocks' : 'stocks'}...</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit}>
            <div className="mb-4">
              <label className="block text-gray-700 font-medium mb-2">
                Search NSE Stock *
              </label>
              <div className="relative">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => {
                    setSearchQuery(e.target.value);
                    setShowDropdown(true);
                  }}
                  onFocus={() => setShowDropdown(true)}
                  placeholder="Search by symbol or company name (e.g., RELIANCE or Reliance Industries)"
                  className="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                
                {showDropdown && filteredStocks.length > 0 && (
                  <div 
                    className="absolute z-10 w-full mt-1 bg-white border rounded-lg shadow-lg max-h-60 overflow-y-auto"
                  >
                    {filteredStocks.slice(0, 50).map((stock) => (
                      <div
                        key={stock.yahoo_symbol}
                        onClick={() => handleStockSelect(stock)}
                        className="px-3 py-2 hover:bg-blue-50 cursor-pointer border-b last:border-b-0 transition-colors"
                      >
                        <div className="flex justify-between items-center">
                          <div className="flex-1">
                            <div className="font-semibold text-gray-900">{stock.symbol}</div>
                            <div className="text-xs text-gray-600 mt-0.5 truncate">{stock.name}</div>
                          </div>
                          <div className="text-xs text-gray-400 ml-2">{stock.yahoo_symbol}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                
                {showDropdown && searchQuery && filteredStocks.length === 0 && (
                  <div className="absolute z-10 w-full mt-1 bg-white border rounded-lg shadow-lg p-3">
                    <p className="text-gray-500 text-sm">No stocks found matching "{searchQuery}"</p>
                  </div>
                )}
              </div>
              
              <p className="text-sm text-gray-500 mt-1">
                {allStocks.length} NSE stocks available (excluding watchlist stocks)
              </p>
              
              {selectedStocks.length > 0 && (
                <div className="mt-3 space-y-2">
                  <p className="text-sm font-medium text-gray-700">Selected Stocks:</p>
                  {selectedStocks.map((stock) => (
                    <div key={stock.yahoo_symbol} className="flex items-center justify-between p-2 bg-green-50 border border-green-200 rounded">
                      <div className="flex-1">
                        <span className="text-sm text-green-800">
                          [SELECTED] <span className="font-medium">{stock.symbol}</span>
                        </span>
                        <span className="text-xs text-green-600 ml-2">- {stock.name}</span>
                      </div>
                      <button
                        type="button"
                        onClick={() => handleRemoveStock(stock.yahoo_symbol)}
                        className="ml-2 text-red-600 hover:text-red-800 font-bold text-lg leading-none"
                        title="Remove"
                      >
                        X
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="flex gap-3">
              <button
                type="submit"
                disabled={selectedStocks.length === 0}
                className={`flex-1 px-4 py-2 rounded font-medium ${
                  selectedStocks.length > 0
                    ? 'bg-blue-600 text-white hover:bg-blue-700'
                    : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                }`}
              >
                {selectedStocks.length === 0 
                  ? 'Add to Watchlist'
                  : selectedStocks.length === 1
                  ? 'Add 1 Stock to Watchlist'
                  : `Add ${selectedStocks.length} Stocks to Watchlist`
                }
              </button>
              <button
                type="button"
                onClick={onClose}
                className="flex-1 px-4 py-2 bg-gray-300 text-gray-700 rounded hover:bg-gray-400"
              >
                Cancel
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}

export default AddStockModal;
