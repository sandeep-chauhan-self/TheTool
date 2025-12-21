import _ from 'lodash';
import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { analyzeAllStocks, getAllStocksProgress } from '../api/api';
import AddToWatchlistModal from '../components/AddToWatchlistModal';
import AnalysisConfigModal from '../components/AnalysisConfigModal';
import Header from '../components/Header';
import NavigationBar from '../components/NavigationBar';
import { useStocks } from '../context/StocksContext';
import { TradingViewLink } from '../utils/tradingViewUtils';

// Define verdict sort order (higher priority first) - outside component to avoid recreating on every render
const VERDICT_PRIORITY = {
  'STRONG BUY': 5,
  'BUY': 4,
  'HOLD': 3,
  'SELL': 2,
  'STRONG SELL': 1,
  '-': 0 // No analysis
};

// Memoized table row component to prevent unnecessary re-renders
const StockRow = React.memo(function StockRow({ 
  stock, 
  isSelected, 
  onToggleSelection, 
  onViewDetails,
  getStatusBadge 
}) {
  return (
    <tr className="hover:bg-gray-50">
      <td className="px-2 sm:px-4 py-2 sm:py-3 whitespace-nowrap">
        <input
          type="checkbox"
          checked={isSelected}
          onChange={() => onToggleSelection(stock.yahoo_symbol)}
          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
        />
      </td>
      <td className="px-2 sm:px-4 py-2 sm:py-3 whitespace-nowrap">
        <TradingViewLink 
          ticker={stock.yahoo_symbol} 
          displayText={stock.symbol}
          className="text-xs sm:text-sm font-medium text-gray-900"
        />
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
            onClick={() => onViewDetails(stock.ticker)}
            className="text-blue-600 hover:text-blue-800 text-xs sm:text-sm font-medium"
          >
            View
          </button>
        )}
      </td>
    </tr>
  );
});

function AllStocksAnalysis() {
  // Use global stocks context for caching
  const { 
    stocks: cachedStocks, 
    stocksLoading, 
    fetchAllStocks, 
    fetchAnalysisResults,
    getStocksWithAnalysis,
    getTimeSinceLastFetch,
    lastStocksFetch,
    updateBulkAnalysis
  } = useStocks();

  // Local UI state only
  const [selectedStocks, setSelectedStocks] = useState([]);
  const [analyzing, setAnalyzing] = useState(false);
  const [refreshingResults, setRefreshingResults] = useState(false);
  const [progress, setProgress] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState(null);
  const [sortDirection, setSortDirection] = useState('asc');
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [showWatchlistModal, setShowWatchlistModal] = useState(false);
  const [pendingAnalysisType, setPendingAnalysisType] = useState(null); // 'all' or 'selected'
  
  // Filter states
  const [filters, setFilters] = useState({
    verdict: 'all',        // 'all', 'Strong Buy', 'Buy', 'Hold', 'Sell', 'Strong Sell', 'Not Analyzed'
    status: 'all',         // 'all', 'completed', 'pending', 'analyzing', 'failed'
    scoreMin: '',          // min score filter
    scoreMax: '',          // max score filter
    hasAnalysis: 'all'     // 'all', 'yes', 'no'
  });
  const [showFilters, setShowFilters] = useState(false);
  
  const navigate = useNavigate();

  // Get merged stocks with analysis data from context
  const stocks = getStocksWithAnalysis();
  const loading = stocksLoading;

  useEffect(() => {
    // Load stocks from cache or fetch if needed (respects TTL)
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
              // Wait for DB to settle, then refresh analysis results only
              setTimeout(async () => {
                setAnalyzing(false);
                setRefreshingResults(true);
                // Force refresh analysis results to get new data
                await fetchAnalysisResults(true);
                setRefreshingResults(false);
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
  }, [analyzing, fetchAnalysisResults]);

  const loadAllStocks = async (forceRefresh = false) => {
    // Use context's fetch functions - they handle caching automatically
    await Promise.all([
      fetchAllStocks(forceRefresh),
      fetchAnalysisResults(forceRefresh)
    ]);
  };

  // Memoized sorted + filtered stocks with stable Lodash ordering
  // NOTE: Defined before handleSelectAll which depends on it
  const filteredStocks = useMemo(() => {
    const query = searchQuery.toLowerCase();

    // --- 1. FILTERING ---
    let filtered = stocks.filter(stock => {
      // Text search filter
      const matchesSearch = 
        stock.symbol.toLowerCase().includes(query) ||
        stock.name.toLowerCase().includes(query) ||
        stock.yahoo_symbol.toLowerCase().includes(query) ||
        (stock.verdict || '').toLowerCase().includes(query);
      
      if (!matchesSearch) return false;
      
      // Verdict filter
      if (filters.verdict !== 'all') {
        if (filters.verdict === 'Not Analyzed') {
          if (stock.verdict && stock.verdict !== '-') return false;
        } else {
          if ((stock.verdict || '').toUpperCase() !== filters.verdict.toUpperCase()) return false;
        }
      }
      
      // Status filter
      if (filters.status !== 'all') {
        if ((stock.status || 'pending') !== filters.status) return false;
      }
      
      // Has Analysis filter
      if (filters.hasAnalysis !== 'all') {
        const hasAnalysis = stock.has_analysis || (stock.score !== null && stock.score !== undefined);
        if (filters.hasAnalysis === 'yes' && !hasAnalysis) return false;
        if (filters.hasAnalysis === 'no' && hasAnalysis) return false;
      }
      
      // Score range filter
      if (filters.scoreMin !== '') {
        const minScore = parseFloat(filters.scoreMin);
        if (!isNaN(minScore) && (stock.score === null || stock.score < minScore)) return false;
      }
      if (filters.scoreMax !== '') {
        const maxScore = parseFloat(filters.scoreMax);
        if (!isNaN(maxScore) && (stock.score === null || stock.score > maxScore)) return false;
      }
      
      return true;
    });

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

  }, [stocks, searchQuery, sortBy, sortDirection, filters]);

  // Count active filters
  const activeFilterCount = useMemo(() => {
    let count = 0;
    if (filters.verdict !== 'all') count++;
    if (filters.status !== 'all') count++;
    if (filters.hasAnalysis !== 'all') count++;
    if (filters.scoreMin !== '') count++;
    if (filters.scoreMax !== '') count++;
    return count;
  }, [filters]);

  const clearAllFilters = useCallback(() => {
    setFilters({
      verdict: 'all',
      status: 'all',
      scoreMin: '',
      scoreMax: '',
      hasAnalysis: 'all'
    });
    setSearchQuery('');
  }, []);

  const handleSelectAll = useCallback(() => {
    // Use memoized filtered stocks (already sorted) to respect current sort order
    // Note: filteredStocks is computed in useMemo and available here
    setSelectedStocks(filteredStocks.map(s => s.yahoo_symbol));
  }, [filteredStocks]);

  const handleDeselectAll = useCallback(() => {
    setSelectedStocks([]);
  }, []);

  const toggleStockSelection = useCallback((yahooSymbol) => {
    setSelectedStocks(prev => 
      prev.includes(yahooSymbol)
        ? prev.filter(s => s !== yahooSymbol)
        : [...prev, yahooSymbol]
    );
  }, []);

  const handleAnalyzeAll = useCallback(() => {
    if (window.confirm(`Are you sure you want to analyze all ${stocks.length} stocks? This will take several hours.`)) {
      setPendingAnalysisType('all');
      setShowConfigModal(true);
    }
  }, [stocks.length]);

  const handleAnalyzeSelected = useCallback(() => {
    if (selectedStocks.length === 0) {
      alert('Please select at least one stock');
      return;
    }
    
    if (window.confirm(`Analyze ${selectedStocks.length} selected stocks?`)) {
      setPendingAnalysisType('selected');
      setShowConfigModal(true);
    }
  }, [selectedStocks.length]);

  const handleAnalyzeWithConfig = useCallback(async (config) => {
    setShowConfigModal(false);
    
    const symbolsToAnalyze = pendingAnalysisType === 'all' ? [] : selectedStocks;
    
    try {
      setAnalyzing(true);
      const response = await analyzeAllStocks(symbolsToAnalyze, config);
      
      // Only alert if duplicate job (useful feedback)
      if (response.is_duplicate) {
        alert(`Analysis already running for these stocks.\nProgress: ${response.completed}/${response.total}`);
      }
      // Success case: no popup needed, progress bar shows status
    } catch (error) {
      console.error('Failed to start analysis:', error);
      alert('Failed to start analysis. Please try again.');
      setAnalyzing(false);
    }
  }, [pendingAnalysisType, selectedStocks]);

  const handleAddToWatchlist = useCallback(() => {
    if (selectedStocks.length === 0) {
      alert('Please select at least one stock');
      return;
    }
    setShowWatchlistModal(true);
  }, [selectedStocks.length]);

  const handleWatchlistSuccess = useCallback(() => {
    // Clear selection after successful add
    setSelectedStocks([]);
  }, []);

  const handleViewDetails = useCallback((ticker) => {
    navigate(`/results/${ticker}`);
  }, [navigate]);

  const getStatusBadge = useCallback((status) => {
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
  }, []);

  const handleSort = useCallback((column) => {
    // If clicking the same column, toggle direction; otherwise, set new column and reset to asc
    setSortBy(prevSortBy => {
      if (prevSortBy === column) {
        setSortDirection(prev => prev === 'asc' ? 'desc' : 'asc');
        return prevSortBy;
      } else {
        setSortDirection('asc');
        return column;
      }
    });
  }, []);

  const getSortIndicator = useCallback((column) => {
    if (sortBy !== column) return '';
    return sortDirection === 'asc' ? ' ↑' : ' ↓';
  }, [sortBy, sortDirection]);

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

        {/* Analysis Starting - shows immediately when analysis begins before first progress poll */}
        {analyzing && !progress && (
          <div className="mb-6 p-3 sm:p-4 bg-blue-50 border border-blue-200 rounded-lg shadow-md">
            <div className="flex items-center gap-3">
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600 flex-shrink-0"></div>
              <div>
                <p className="text-xs sm:text-sm font-medium text-blue-800">
                  Starting Analysis...
                </p>
                <p className="text-xs text-blue-600 mt-1">
                  Preparing to analyze {pendingAnalysisType === 'all' ? 'all stocks' : `${selectedStocks.length} selected stocks`}. Please wait...
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

        {/* Refreshing Results - shows after analysis completes while fetching new data */}
        {refreshingResults && (
          <div className="mb-6 p-3 sm:p-4 bg-yellow-50 border border-yellow-200 rounded-lg shadow-md">
            <div className="flex items-center gap-3">
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-yellow-600 flex-shrink-0"></div>
              <div>
                <p className="text-xs sm:text-sm font-medium text-yellow-800">
                  Refreshing Results...
                </p>
                <p className="text-xs text-yellow-600 mt-1">
                  Loading updated analysis data. Almost there!
                </p>
              </div>
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
            onClick={handleAddToWatchlist}
            disabled={selectedStocks.length === 0 || loading}
            className="flex-1 sm:flex-none px-3 sm:px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-gray-400 font-medium text-xs sm:text-sm whitespace-nowrap"
          >
            + Watchlist ({selectedStocks.length})
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
            onClick={() => loadAllStocks(true)}
            disabled={loading}
            className="flex-1 sm:flex-none px-3 sm:px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 text-xs sm:text-sm ml-0 sm:ml-auto whitespace-nowrap"
          >
            {loading ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>

        {/* Last Synced Indicator */}
        {lastStocksFetch && !loading && (
          <div className="mb-2 text-xs text-gray-500 text-right">
            Last synced: {getTimeSinceLastFetch(lastStocksFetch)}
          </div>
        )}

        {/* Search Bar and Filters */}
        <div className="mb-4 space-y-3">
          {/* Search and Filter Toggle Row */}
          <div className="flex gap-2 items-center">
            <div className="flex-1 relative">
              <input
                type="text"
                placeholder="Search by symbol, name, or verdict..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full px-3 sm:px-4 py-2 pl-10 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
              />
              <svg className="w-4 h-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`px-3 py-2 rounded-lg border text-sm font-medium flex items-center gap-2 transition-colors ${
                showFilters || activeFilterCount > 0
                  ? 'bg-blue-50 border-blue-300 text-blue-700'
                  : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
              }`}
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
              </svg>
              Filters
              {activeFilterCount > 0 && (
                <span className="bg-blue-600 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                  {activeFilterCount}
                </span>
              )}
            </button>
            {activeFilterCount > 0 && (
              <button
                onClick={clearAllFilters}
                className="px-3 py-2 text-sm text-red-600 hover:text-red-700 hover:bg-red-50 rounded-lg transition-colors"
              >
                Clear All
              </button>
            )}
          </div>

          {/* Filter Panel */}
          {showFilters && (
            <div className="bg-white border rounded-lg p-4 shadow-sm">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
                {/* Verdict Filter */}
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">Verdict</label>
                  <select
                    value={filters.verdict}
                    onChange={(e) => setFilters(prev => ({ ...prev, verdict: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="all">All Verdicts</option>
                    <option value="Strong Buy">Strong Buy</option>
                    <option value="Buy">Buy</option>
                    <option value="Hold">Hold</option>
                    <option value="Sell">Sell</option>
                    <option value="Strong Sell">Strong Sell</option>
                    <option value="Not Analyzed">Not Analyzed</option>
                  </select>
                </div>

                {/* Status Filter */}
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">Status</label>
                  <select
                    value={filters.status}
                    onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="all">All Status</option>
                    <option value="completed">Completed</option>
                    <option value="analyzing">Analyzing</option>
                    <option value="pending">Pending</option>
                    <option value="failed">Failed</option>
                  </select>
                </div>

                {/* Has Analysis Filter */}
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">Analysis</label>
                  <select
                    value={filters.hasAnalysis}
                    onChange={(e) => setFilters(prev => ({ ...prev, hasAnalysis: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="all">All Stocks</option>
                    <option value="yes">With Analysis</option>
                    <option value="no">Without Analysis</option>
                  </select>
                </div>

                {/* Score Range - Min */}
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">Min Score</label>
                  <input
                    type="number"
                    placeholder="e.g., 50"
                    value={filters.scoreMin}
                    onChange={(e) => setFilters(prev => ({ ...prev, scoreMin: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    min="0"
                    max="100"
                  />
                </div>

                {/* Score Range - Max */}
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">Max Score</label>
                  <input
                    type="number"
                    placeholder="e.g., 100"
                    value={filters.scoreMax}
                    onChange={(e) => setFilters(prev => ({ ...prev, scoreMax: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    min="0"
                    max="100"
                  />
                </div>
              </div>

              {/* Quick Filter Buttons */}
              <div className="mt-3 pt-3 border-t border-gray-200">
                <span className="text-xs font-medium text-gray-500 mr-3">Quick filters:</span>
                <div className="inline-flex flex-wrap gap-2 mt-1">
                  <button
                    onClick={() => setFilters(prev => ({ ...prev, verdict: 'Strong Buy' }))}
                    className="px-2 py-1 text-xs bg-green-100 text-green-700 rounded hover:bg-green-200 transition-colors"
                  >
                    Strong Buy
                  </button>
                  <button
                    onClick={() => setFilters(prev => ({ ...prev, verdict: 'Buy' }))}
                    className="px-2 py-1 text-xs bg-green-50 text-green-600 rounded hover:bg-green-100 transition-colors"
                  >
                    Buy
                  </button>
                  <button
                    onClick={() => setFilters(prev => ({ ...prev, scoreMin: '70', scoreMax: '' }))}
                    className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition-colors"
                  >
                    Score ≥ 70
                  </button>
                  <button
                    onClick={() => setFilters(prev => ({ ...prev, hasAnalysis: 'yes' }))}
                    className="px-2 py-1 text-xs bg-purple-100 text-purple-700 rounded hover:bg-purple-200 transition-colors"
                  >
                    Analyzed Only
                  </button>
                  <button
                    onClick={() => setFilters(prev => ({ ...prev, status: 'completed' }))}
                    className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors"
                  >
                    Completed
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Results count */}
          <p className="text-xs sm:text-sm text-gray-500">
            Showing {filteredStocks.length} of {stocks.length} stocks
            {activeFilterCount > 0 && (
              <span className="ml-2 text-blue-600">
                ({activeFilterCount} filter{activeFilterCount > 1 ? 's' : ''} applied)
              </span>
            )}
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
                    <StockRow
                      key={stock.yahoo_symbol}
                      stock={stock}
                      isSelected={selectedStocks.includes(stock.yahoo_symbol)}
                      onToggleSelection={toggleStockSelection}
                      onViewDetails={handleViewDetails}
                      getStatusBadge={getStatusBadge}
                    />
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

      {/* Add to Watchlist Modal */}
      {showWatchlistModal && (
        <AddToWatchlistModal
          stocks={selectedStocks.map(symbol => {
            const stock = stocks.find(s => s.yahoo_symbol === symbol);
            return { symbol, name: stock?.name || '' };
          })}
          onClose={() => setShowWatchlistModal(false)}
          onSuccess={handleWatchlistSuccess}
        />
      )}
    </div>
  );
}

export default AllStocksAnalysis;
