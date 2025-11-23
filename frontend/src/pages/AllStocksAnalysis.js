import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { analyzeAllStocks, getAllNSEStocks, getAllStocksProgress, getAllAnalysisResults } from '../api/api';
import Header from '../components/Header';
import NavigationBar from '../components/NavigationBar';

function AllStocksAnalysis() {
  const [stocks, setStocks] = useState([]);
  const [selectedStocks, setSelectedStocks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [progress, setProgress] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    loadAllStocks();
  }, []);

  // Poll progress when analyzing
  useEffect(() => {
    let intervalId;
    
    if (analyzing) {
      intervalId = setInterval(async () => {
        try {
          const progressData = await getAllStocksProgress();
          setProgress(progressData);
          
          // Stop polling if no stocks are being analyzed
          if (!progressData.is_analyzing && progressData.analyzing === 0) {
            setAnalyzing(false);
            loadAllStocks(); // Refresh the list
          }
        } catch (error) {
          console.error('Failed to fetch progress:', error);
        }
      }, 5000); // Poll every 5 seconds
    }
    
    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [analyzing]);

  const loadAllStocks = async () => {
    try {
      setLoading(true);
      
      // Load all 2,192 NSE stocks from the new endpoint
      let allLoadedStocks = [];
      let currentPage = 1;
      let hasMore = true;
      
      while (hasMore) {
        const data = await getAllNSEStocks(currentPage, 200);
        if (data && data.stocks) {
          allLoadedStocks = [...allLoadedStocks, ...data.stocks];
          currentPage++;
          hasMore = currentPage <= data.total_pages;
        } else {
          hasMore = false;
        }
      }
      
      // Fetch all analysis results to enrich stocks with analysis data
      let allResults = [];
      let resultsPage = 1;
      let resultsHasMore = true;
      
      while (resultsHasMore) {
        try {
          const resultsData = await getAllAnalysisResults(resultsPage, 200);
          if (resultsData && resultsData.results) {
            allResults = [...allResults, ...resultsData.results];
            resultsPage++;
            resultsHasMore = resultsPage <= resultsData.total_pages;
          } else {
            resultsHasMore = false;
          }
        } catch (error) {
          console.error('Error fetching analysis results:', error);
          resultsHasMore = false;
        }
      }
      
      // Create a map of symbol -> analysis result for quick lookup
      const resultsMap = {};
      allResults.forEach(result => {
        const key = result.symbol || result.ticker;
        if (key) {
          resultsMap[key.toUpperCase()] = result;
        }
      });
      
      // Map stocks to include status field for UI and enrich with analysis data
      const stocksWithStatus = allLoadedStocks.map(stock => {
        const result = resultsMap[stock.symbol.toUpperCase()];
        if (result) {
          return {
            ...stock,
            status: 'completed',
            score: result.score,
            verdict: result.verdict,
            entry: result.entry,
            target: result.target,
            has_analysis: true,
            stop_loss: result.stop_loss,
            created_at: result.created_at
          };
        }
        return {
          ...stock,
          status: 'pending',
          score: null,
          verdict: '-',
          entry: null,
          target: null,
          has_analysis: false
        };
      });
      
      setStocks(stocksWithStatus);
      
    } catch (error) {
      console.error('Failed to load stocks:', error);
      alert('Failed to load stocks. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectAll = () => {
    const filtered = getFilteredStocks();
    setSelectedStocks(filtered.map(s => s.yahoo_symbol));
  };

  const handleDeselectAll = () => {
    setSelectedStocks([]);
  };

  const toggleStockSelection = (yahooSymbol) => {
    if (selectedStocks.includes(yahooSymbol)) {
      setSelectedStocks(selectedStocks.filter(s => s !== yahooSymbol));
    } else {
      setSelectedStocks([...selectedStocks, yahooSymbol]);
    }
  };

  const handleAnalyzeAll = async () => {
    if (window.confirm(`Are you sure you want to analyze all ${stocks.length} stocks? This will take several hours.`)) {
      try {
        setAnalyzing(true);
        await analyzeAllStocks([]); // Empty array means all stocks
      } catch (error) {
        console.error('Failed to start analysis:', error);
        alert('Failed to start analysis. Please try again.');
        setAnalyzing(false);
      }
    }
  };

  const handleAnalyzeSelected = async () => {
    if (selectedStocks.length === 0) {
      alert('Please select at least one stock');
      return;
    }
    
    if (window.confirm(`Analyze ${selectedStocks.length} selected stocks?`)) {
      try {
        setAnalyzing(true);
        await analyzeAllStocks(selectedStocks);
      } catch (error) {
        console.error('Failed to start analysis:', error);
        alert('Failed to start analysis. Please try again.');
        setAnalyzing(false);
      }
    }
  };

  const handleViewDetails = (symbol) => {
    navigate(`/results/${symbol}`);
  };

  const getStatusBadge = (status) => {
    const badges = {
      pending: { text: 'Pending', color: 'bg-gray-200 text-gray-700' },
      analyzing: { text: 'Analyzing...', color: 'bg-blue-100 text-blue-700' },
      completed: { text: 'Completed', color: 'bg-green-100 text-green-700' },
      failed: { text: 'Failed', color: 'bg-red-100 text-red-700' }
    };
    
    const badge = badges[status] || badges.pending;
    
    return (
      <span className={`px-2 py-1 rounded text-xs font-medium ${badge.color}`}>
        {badge.text}
      </span>
    );
  };

  const getFilteredStocks = () => {
    if (!searchQuery.trim()) return stocks;
    
    const query = searchQuery.toLowerCase();
    return stocks.filter(stock => 
      stock.symbol.toLowerCase().includes(query) ||
      stock.name.toLowerCase().includes(query) ||
      stock.yahoo_symbol.toLowerCase().includes(query)
    );
  };

  const filteredStocks = getFilteredStocks();

  return (
    <div className="min-h-screen bg-gray-100">
      <NavigationBar />
      <Header title="All Stocks Analysis" subtitle={`${stocks.length} NSE Stocks`} />

      <div className="max-w-7xl mx-auto px-4 py-8">
        
        {/* Progress Bar */}
        {analyzing && progress && (
          <div className="mb-6 p-4 bg-white rounded-lg shadow-md">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium text-gray-700">
                Analyzing {progress.completed}/{progress.total} stocks ({progress.percentage}% complete)
              </span>
              <span className="text-sm text-gray-500">
                ETA: {progress.estimated_time_remaining}
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2.5">
              <div 
                className="bg-blue-600 h-2.5 rounded-full transition-all duration-500"
                style={{ width: `${progress.percentage}%` }}
              ></div>
            </div>
            <div className="mt-2 flex justify-between text-xs text-gray-600">
              <span>Completed: {progress.completed}</span>
              <span>Analyzing: {progress.analyzing}</span>
              <span>Failed: {progress.failed}</span>
              <span>Pending: {progress.pending}</span>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-4 mb-6 flex-wrap">
          <button
            onClick={handleAnalyzeAll}
            disabled={analyzing || loading}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 font-medium"
          >
            {analyzing ? 'Analysis Running...' : `Analyze All ${stocks.length} Stocks`}
          </button>
          
          <button
            onClick={handleAnalyzeSelected}
            disabled={selectedStocks.length === 0 || analyzing || loading}
            className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 font-medium"
          >
            Analyze Selected ({selectedStocks.length})
          </button>
          
          <button
            onClick={handleSelectAll}
            disabled={loading}
            className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 text-sm"
          >
            Select All
          </button>
          
          <button
            onClick={handleDeselectAll}
            disabled={loading || selectedStocks.length === 0}
            className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 text-sm disabled:bg-gray-100"
          >
            Deselect All
          </button>
          
          <button
            onClick={loadAllStocks}
            disabled={loading}
            className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 text-sm ml-auto"
          >
            Refresh
          </button>
        </div>

        {/* Search Bar */}
        <div className="mb-4">
          <input
            type="text"
            placeholder="Search stocks by symbol or name..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <p className="text-sm text-gray-500 mt-1">
            Showing {filteredStocks.length} of {stocks.length} stocks
          </p>
        </div>

        {/* Stocks List */}
        {loading ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
            <p className="text-gray-600">Loading all 2,192 NSE stocks...</p>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow-md overflow-hidden">
            <div className="overflow-x-auto max-h-[600px] overflow-y-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50 sticky top-0">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-12">
                      Select
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Symbol
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Company Name
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Score
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Verdict
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Entry
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Target
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredStocks.map((stock) => (
                    <tr key={stock.yahoo_symbol} className="hover:bg-gray-50">
                      <td className="px-4 py-3 whitespace-nowrap">
                        <input
                          type="checkbox"
                          checked={selectedStocks.includes(stock.yahoo_symbol)}
                          onChange={() => toggleStockSelection(stock.yahoo_symbol)}
                          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                        />
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">{stock.symbol}</div>
                        <div className="text-xs text-gray-500">{stock.yahoo_symbol}</div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="text-sm text-gray-900 truncate max-w-xs">{stock.name}</div>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        {getStatusBadge(stock.status)}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          {stock.score !== null ? stock.score.toFixed(1) : '-'}
                        </div>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          {stock.verdict || '-'}
                        </div>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          {stock.entry ? `Rs. ${stock.entry.toFixed(2)}` : '-'}
                        </div>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          {stock.target ? `Rs. ${stock.target.toFixed(2)}` : '-'}
                        </div>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        {stock.has_analysis && (
                          <button
                            onClick={() => handleViewDetails(stock.yahoo_symbol)}
                            className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                          >
                            View Details
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {!loading && filteredStocks.length === 0 && (
          <div className="text-center py-12 bg-white rounded-lg shadow-md">
            <p className="text-gray-600">No stocks found matching your search</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default AllStocksAnalysis;
