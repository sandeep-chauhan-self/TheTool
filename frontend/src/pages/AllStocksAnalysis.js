import _ from 'lodash';
import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { analyzeAllStocks, getAllAnalysisResults, getAllNSEStocks, getAllStocksProgress } from '../api/api';
import AnalysisConfigModal from '../components/AnalysisConfigModal';
import Header from '../components/Header';
import NavigationBar from '../components/NavigationBar';

// Define verdict sort order (higher priority first) - outside component to avoid recreating on every render
const VERDICT_PRIORITY = {
  'STRONG BUY': 5,
  'BUY': 4,
  'HOLD': 3,
  'SELL': 2,
  'STRONG SELL': 1,
  '-': 0 // No analysis
};

function AllStocksAnalysis() {
  const [stocks, setStocks] = useState([]);
  const [selectedStocks, setSelectedStocks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [progress, setProgress] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState(null);
  const [sortDirection, setSortDirection] = useState('asc');
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [pendingAnalysisType, setPendingAnalysisType] = useState(null); // 'all' or 'selected'
  const navigate = useNavigate();

  useEffect(() => {
    loadAllStocks();
  }, []);

  // Poll progress when analyzing
  useEffect(() => {
    let intervalId;
    let completionCheckCount = 0;
    
    if (analyzing) {
      intervalId = setInterval(async () => {
        try {
          const progressData = await getAllStocksProgress();
          setProgress(progressData);
          
          // Stop polling if no stocks are being analyzed
          if (!progressData.is_analyzing && progressData.analyzing === 0) {
            // Add small delay to ensure database is fully updated
            completionCheckCount++;
            if (completionCheckCount >= 2) {
              // Wait for DB to settle, then refresh
              setTimeout(() => {
                setAnalyzing(false);
                loadAllStocks(); // Refresh the list with results
              }, 1000);
            }
          } else {
            completionCheckCount = 0; // Reset counter if still analyzing
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
      
      // OPTIMIZED: Fetch first page to get total_pages, then fetch all pages in parallel
      const firstStocksPage = await getAllNSEStocks(1, 500); // Larger page size
      const totalStockPages = firstStocksPage?.total_pages || 1;
      
      // Fetch remaining stock pages in parallel
      let allLoadedStocks = [...(firstStocksPage?.stocks || [])];
      if (totalStockPages > 1) {
        const stockPagePromises = [];
        for (let page = 2; page <= totalStockPages; page++) {
          stockPagePromises.push(getAllNSEStocks(page, 500));
        }
        const stockResults = await Promise.all(stockPagePromises);
        stockResults.forEach(data => {
          if (data?.stocks) {
            allLoadedStocks = [...allLoadedStocks, ...data.stocks];
          }
        });
      }
      
      // OPTIMIZED: Same parallel approach for analysis results
      const firstResultsPage = await getAllAnalysisResults(1, 500);
      const totalResultPages = firstResultsPage?.total_pages || 1;
      
      let allResults = [...(firstResultsPage?.results || [])];
      if (totalResultPages > 1) {
        const resultPagePromises = [];
        for (let page = 2; page <= totalResultPages; page++) {
          resultPagePromises.push(getAllAnalysisResults(page, 500));
        }
        const resultsData = await Promise.all(resultPagePromises);
        resultsData.forEach(data => {
          if (data?.results) {
            allResults = [...allResults, ...data.results];
          }
        });
      }
      
      // Create a map of symbol -> analysis result for quick lookup
      // IMPORTANT: Only keep FIRST occurrence of each symbol (which is newest from backend DESC order)
      const resultsMap = {};
      allResults.forEach(result => {
        const key = result.symbol || result.ticker;
        if (key) {
          const upperKey = key.toUpperCase();
          // Only add if not already in map (first = newest from DESC ordering)
          if (!resultsMap[upperKey]) {
            resultsMap[upperKey] = result;
          }
        }
      });
      
      // Map stocks to include status field for UI and enrich with analysis data
      const stocksWithStatus = allLoadedStocks.map(stock => {
        const result = resultsMap[stock.symbol.toUpperCase()];
        if (result) {
          return {
            ...stock,
            ticker: result.ticker,  // Add ticker from analysis result
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
    // Use memoized filtered stocks (already sorted) to respect current sort order
    // Note: filteredStocks is computed in useMemo and available here
    setSelectedStocks(filteredStocks.map(s => s.yahoo_symbol));
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
      setPendingAnalysisType('all');
      setShowConfigModal(true);
    }
  };

  const handleAnalyzeSelected = async () => {
    if (selectedStocks.length === 0) {
      alert('Please select at least one stock');
      return;
    }
    
    if (window.confirm(`Analyze ${selectedStocks.length} selected stocks?`)) {
      setPendingAnalysisType('selected');
      setShowConfigModal(true);
    }
  };

  const handleAnalyzeWithConfig = async (config) => {
    setShowConfigModal(false);
    
    const symbolsToAnalyze = pendingAnalysisType === 'all' ? [] : selectedStocks;
    
    try {
      setAnalyzing(true);
      const response = await analyzeAllStocks(symbolsToAnalyze, config);
      
      // Handle both new job and duplicate job responses
      if (response.is_duplicate) {
        alert(`Analysis already running for these stocks. Job ID: ${response.job_id}\n` +
              `Progress: ${response.completed}/${response.total}`);
      } else {
        alert(`Analysis started. Job ID: ${response.job_id}`);
      }
    } catch (error) {
      console.error('Failed to start analysis:', error);
      alert('Failed to start analysis. Please try again.');
      setAnalyzing(false);
    }
  };

  const handleViewDetails = (ticker) => {
    navigate(`/results/${ticker}`);
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

  const handleSort = (column) => {
    // If clicking the same column, toggle direction; otherwise, set new column and reset to asc
    if (sortBy === column) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(column);
      setSortDirection('asc');
    }
  };

  // Memoized sorted + filtered stocks with stable Lodash ordering
  const filteredStocks = useMemo(() => {
    const query = searchQuery.toLowerCase();

    // --- 1. FILTERING ---
    let filtered = stocks.filter(stock =>
      stock.symbol.toLowerCase().includes(query) ||
      stock.name.toLowerCase().includes(query) ||
      stock.yahoo_symbol.toLowerCase().includes(query) ||
      (stock.verdict || '').toLowerCase().includes(query)
    );

    // --- 2. SORTING ---
    if (!sortBy) return filtered;

    const sortDirectionLodash = sortDirection === 'asc' ? 'asc' : 'desc';

    // MAPPING SORT COLUMNS TO ITERATEES
    const sortIteratees = {
      verdict: (s) => (s.verdict || '-').toLowerCase(),
      symbol: (s) => (s.symbol || '').toLowerCase(),
      score: (s) => s.score ?? -1,
      entry: (s) => s.entry ?? -1,
      target: (s) => s.target ?? -1
    };

    // Primary iteratee
    const primary = sortIteratees[sortBy];

    // Add secondary ordering for stability:
    // ALWAYS SORT BY SYMBOL after primary
    const secondary = (s) => (s.symbol || '').toLowerCase();

    // Apply orderBy with 2 keys
    return _.orderBy(
      filtered,
      [primary, secondary],
      [sortDirectionLodash, 'asc']
    );

  }, [stocks, searchQuery, sortBy, sortDirection]);

  const getSortIndicator = (column) => {
    if (sortBy !== column) return '';
    return sortDirection === 'asc' ? ' ↑' : ' ↓';
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <NavigationBar />
      <Header title="All Stocks Analysis" subtitle={`${stocks.length} NSE Stocks`} />

      <div className="w-full max-w-7xl mx-auto px-2 sm:px-4 py-4 sm:py-8">
        
        {/* Completion Message */}
        {progress && !analyzing && progress.percentage === 100 && (
          <div className="mb-6 p-3 sm:p-4 bg-green-50 border border-green-200 rounded-lg shadow-md">
            <div className="flex gap-3">
              <span className="text-xl flex-shrink-0">✓</span>
              <div>
                <p className="text-xs sm:text-sm font-medium text-green-800">
                  Analysis Completed Successfully!
                </p>
                <p className="text-xs text-green-700 mt-1">
                  Processed {progress.completed}/{progress.total} 
                  ({progress.successful} successful, {progress.failed} failed)
                </p>
              </div>
            </div>
          </div>
        )}
        
        {/* Progress Bar */}
        {analyzing && progress && (
          <div className="mb-6 p-3 sm:p-4 bg-white rounded-lg shadow-md">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 mb-2">
              <span className="text-xs sm:text-sm font-medium text-gray-700">
                Analyzing {progress.completed}/{progress.total} ({progress.percentage}%)
              </span>
              <span className="text-xs text-gray-500">
                ETA: {progress.estimated_time_remaining}
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2.5">
              <div 
                className="bg-blue-600 h-2.5 rounded-full transition-all duration-500"
                style={{ width: `${progress.percentage}%` }}
              ></div>
            </div>
            <div className="mt-2 grid grid-cols-2 sm:flex sm:justify-between gap-2 text-xs text-gray-600">
              <span>Completed: {progress.completed}</span>
              <span>Analyzing: {progress.analyzing}</span>
              <span>Failed: {progress.failed}</span>
              <span>Pending: {progress.pending}</span>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-2 sm:gap-4 mb-6 flex-wrap justify-center sm:justify-start">
          <button
            onClick={handleAnalyzeAll}
            disabled={analyzing || loading}
            className="flex-1 sm:flex-none px-3 sm:px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 font-medium text-xs sm:text-sm whitespace-nowrap"
          >
            {analyzing ? 'Running...' : `Analyze All`}
          </button>
          
          <button
            onClick={handleAnalyzeSelected}
            disabled={selectedStocks.length === 0 || analyzing || loading}
            className="flex-1 sm:flex-none px-3 sm:px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 font-medium text-xs sm:text-sm whitespace-nowrap"
          >
            Analyze ({selectedStocks.length})
          </button>
          
          <button
            onClick={handleSelectAll}
            disabled={loading}
            className="flex-1 sm:flex-none px-3 sm:px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 text-xs sm:text-sm whitespace-nowrap"
          >
            Select All
          </button>
          
          <button
            onClick={handleDeselectAll}
            disabled={loading || selectedStocks.length === 0}
            className="flex-1 sm:flex-none px-3 sm:px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 text-xs sm:text-sm disabled:bg-gray-100 whitespace-nowrap"
          >
            Deselect All
          </button>
          
          <button
            onClick={loadAllStocks}
            disabled={loading}
            className="flex-1 sm:flex-none px-3 sm:px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 text-xs sm:text-sm ml-0 sm:ml-auto whitespace-nowrap"
          >
            Refresh
          </button>
        </div>

        {/* Search Bar */}
        <div className="mb-4">
          <input
            type="text"
            placeholder="Search stocks..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full px-3 sm:px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
          />
          <p className="text-xs sm:text-sm text-gray-500 mt-1">
            Showing {filteredStocks.length} of {stocks.length} stocks
          </p>
        </div>

        {/* Stocks List */}
        {loading ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
            <p className="text-gray-600 text-sm">Loading all 2,192 NSE stocks...</p>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow-md overflow-hidden">
            <div className="w-full overflow-x-auto">
              <table className="w-full divide-y divide-gray-200 text-xs sm:text-sm">
                <thead className="bg-gray-50 sticky top-0">
                  <tr>
                    <th className="px-2 sm:px-4 py-2 sm:py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-8 sm:w-12">
                      Select
                    </th>
                    <th 
                      onClick={() => handleSort('symbol')}
                      className="px-2 sm:px-4 py-2 sm:py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 transition-colors"
                    >
                      Symbol{getSortIndicator('symbol')}
                    </th>
                    <th className="hidden md:table-cell px-2 sm:px-4 py-2 sm:py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Company Name
                    </th>
                    <th className="hidden lg:table-cell px-2 sm:px-4 py-2 sm:py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th 
                      onClick={() => handleSort('score')}
                      className="px-2 sm:px-4 py-2 sm:py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 transition-colors"
                    >
                      Score{getSortIndicator('score')}
                    </th>
                    <th 
                      onClick={() => handleSort('verdict')}
                      className="px-2 sm:px-4 py-2 sm:py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 transition-colors"
                    >
                      Verdict{getSortIndicator('verdict')}
                    </th>
                    <th 
                      onClick={() => handleSort('entry')}
                      className="hidden sm:table-cell px-2 sm:px-4 py-2 sm:py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 transition-colors"
                    >
                      Entry{getSortIndicator('entry')}
                    </th>
                    <th 
                      onClick={() => handleSort('target')}
                      className="hidden md:table-cell px-2 sm:px-4 py-2 sm:py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 transition-colors"
                    >
                      Target{getSortIndicator('target')}
                    </th>
                    <th className="hidden sm:table-cell px-2 sm:px-4 py-2 sm:py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredStocks.map((stock) => (
                    <tr key={stock.yahoo_symbol} className="hover:bg-gray-50">
                      <td className="px-2 sm:px-4 py-2 sm:py-3 whitespace-nowrap">
                        <input
                          type="checkbox"
                          checked={selectedStocks.includes(stock.yahoo_symbol)}
                          onChange={() => toggleStockSelection(stock.yahoo_symbol)}
                          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                        />
                      </td>
                      <td className="px-2 sm:px-4 py-2 sm:py-3 whitespace-nowrap">
                        <div className="text-xs sm:text-sm font-medium text-gray-900">{stock.symbol}</div>
                        <div className="text-xs text-gray-500">{stock.yahoo_symbol}</div>
                      </td>
                      <td className="hidden md:table-cell px-2 sm:px-4 py-2 sm:py-3">
                        <div className="text-xs sm:text-sm text-gray-900 truncate max-w-xs">{stock.name}</div>
                      </td>
                      <td className="hidden lg:table-cell px-2 sm:px-4 py-2 sm:py-3 whitespace-nowrap">
                        {getStatusBadge(stock.status)}
                      </td>
                      <td className="px-2 sm:px-4 py-2 sm:py-3 whitespace-nowrap">
                        <div className="text-xs sm:text-sm text-gray-900">
                          {stock.score !== null ? stock.score.toFixed(1) : '-'}
                        </div>
                      </td>
                      <td className="px-2 sm:px-4 py-2 sm:py-3 whitespace-nowrap">
                        <div className="text-xs sm:text-sm text-gray-900 font-medium">
                          {stock.verdict || '-'}
                        </div>
                      </td>
                      <td className="hidden sm:table-cell px-2 sm:px-4 py-2 sm:py-3 whitespace-nowrap">
                        <div className="text-xs sm:text-sm text-gray-900">
                          {stock.entry ? `Rs. ${stock.entry.toFixed(2)}` : '-'}
                        </div>
                      </td>
                      <td className="hidden md:table-cell px-2 sm:px-4 py-2 sm:py-3 whitespace-nowrap">
                        <div className="text-xs sm:text-sm text-gray-900">
                          {stock.target ? `Rs. ${stock.target.toFixed(2)}` : '-'}
                        </div>
                      </td>
                      <td className="hidden sm:table-cell px-2 sm:px-4 py-2 sm:py-3 whitespace-nowrap">
                        {stock.has_analysis && (
                          <button
                            onClick={() => handleViewDetails(stock.ticker)}
                            className="text-blue-600 hover:text-blue-800 text-xs sm:text-sm font-medium"
                          >
                            View
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
          <div className="text-center py-8 sm:py-12 bg-white rounded-lg shadow-md">
            <p className="text-gray-600 text-sm">No stocks found matching your search</p>
          </div>
        )}
      </div>

      {/* Analysis Config Modal */}
      {showConfigModal && (
        <AnalysisConfigModal
          onClose={() => setShowConfigModal(false)}
          onConfirm={handleAnalyzeWithConfig}
          stockCount={pendingAnalysisType === 'all' ? stocks.length : selectedStocks.length}
          stockNames={pendingAnalysisType === 'all' ? [] : selectedStocks}
          title={pendingAnalysisType === 'all' ? 'Configure Bulk Analysis' : 'Configure Analysis'}
        />
      )}
    </div>
  );
}

export default AllStocksAnalysis;
