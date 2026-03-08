import _ from 'lodash';
import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { analyzeAllStocks, getAllStocksProgress } from '../api/api';
import AddToWatchlistModal from '../components/AddToWatchlistModal';
import PasswordModal from '../components/PasswordModal';
import AnalysisConfigModal from '../components/AnalysisConfigModal';
import Breadcrumbs from '../components/Breadcrumbs';
import Header from '../components/Header';
import NavigationBar from '../components/NavigationBar';
import { useStocks } from '../context/StocksContext';
import { TradingViewLink } from '../utils/tradingViewUtils';

// New UI Components
import VerdictBadge from '../components/ui/VerdictBadge';
import ScoreArc from '../components/ui/ScoreArc';
import CommandPalette from '../components/ui/CommandPalette';

// Define verdict sort order
const VERDICT_PRIORITY = { 
  'STRONG BUY': 5,
  'BUY': 4,
  'HOLD': 3,
  'SELL': 2,
  'STRONG SELL': 1,
  '-': 0
};

const StockRow = React.memo(function StockRow({ 
  stock, 
  isSelected, 
  onToggleSelection, 
  onViewDetails,
  getStatusBadge 
}) {
  return (
    <tr className="table-row-modern group">
      <td className="px-5 py-4 w-12 text-center whitespace-nowrap">
        <input
          type="checkbox"
          checked={isSelected}
          onChange={() => onToggleSelection(stock.yahoo_symbol)}
          className="w-4 h-4 text-primary-600 focus:ring-primary-500 border-slate-300 rounded cursor-pointer"
        />
      </td>
      <td className="px-5 py-4 whitespace-nowrap">
        <TradingViewLink 
          ticker={stock.yahoo_symbol} 
          displayText={stock.symbol}
          className="font-mono font-bold text-slate-900 group-hover:text-primary-600 transition-colors"
        />
        <div className="text-xs text-slate-500 font-mono mt-1">{stock.yahoo_symbol}</div>
      </td>
      <td className="hidden md:table-cell px-5 py-4">
        <div className="text-sm text-slate-600 font-medium truncate max-w-xs">{stock.name}</div>
      </td>
      <td className="hidden lg:table-cell px-5 py-4 whitespace-nowrap">
        {getStatusBadge(stock.status)}
      </td>
      <td className="px-5 py-4 whitespace-nowrap">
        {stock.score !== null && stock.score !== undefined ? (
          <ScoreArc score={stock.score} />
        ) : <span className="text-slate-400">-</span>}
      </td>
      <td className="px-5 py-4 whitespace-nowrap">
        {stock.verdict ? <VerdictBadge verdict={stock.verdict} /> : <span className="text-slate-400">-</span>}
      </td>
      <td className="hidden sm:table-cell px-5 py-4 whitespace-nowrap">
        <div className="text-sm font-semibold text-slate-700">
          {stock.entry ? `₹${stock.entry.toFixed(2)}` : '-'}
        </div>
      </td>
      <td className="hidden md:table-cell px-5 py-4 whitespace-nowrap">
        <div className="text-sm font-semibold text-slate-700">
          {stock.target ? `₹${stock.target.toFixed(2)}` : '-'}
        </div>
      </td>
      <td className="px-5 py-4 text-right whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity">
        {stock.has_analysis && (
          <button
            onClick={() => onViewDetails(stock.ticker)}
            className="text-primary-600 hover:text-primary-800 font-medium text-sm transition-colors"
          >
            View
          </button>
        )}
      </td>
    </tr>
  );
});

function AllStocksAnalysis() {
  const { 
    stocks: cachedStocks, 
    stocksLoading, 
    fetchAllStocks, 
    fetchAnalysisResults,
    getStocksWithAnalysis,
    getTimeSinceLastFetch,
    lastStocksFetch,
  } = useStocks();

  const [selectedStocks, setSelectedStocks] = useState([]);
  const [analyzing, setAnalyzing] = useState(false);
  const [refreshingResults, setRefreshingResults] = useState(false);
  const [progress, setProgress] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState(null);
  const [sortDirection, setSortDirection] = useState('asc');
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [showWatchlistModal, setShowWatchlistModal] = useState(false);
  const [pendingAnalysisType, setPendingAnalysisType] = useState(null);
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [passwordVerified, setPasswordVerified] = useState(() => sessionStorage.getItem('bulkAnalysisVerified') === 'true');
  
  const [filters, setFilters] = useState({
    verdict: 'all',
    status: 'all',
    scoreMin: '',
    scoreMax: '',
    hasAnalysis: 'all'
  });
  const [showFilters, setShowFilters] = useState(false);
  const navigate = useNavigate();

  const stocks = getStocksWithAnalysis();
  const loading = stocksLoading;

  useEffect(() => {
    loadAllStocks();
  }, []);

  useEffect(() => {
    let intervalId;
    let completionCheckCount = 0;
    
    if (analyzing) {
      intervalId = setInterval(async () => {
        try {
          const progressData = await getAllStocksProgress();
          setProgress(progressData);
          
          if (!progressData.is_analyzing && progressData.analyzing === 0) {
            completionCheckCount++;
            if (completionCheckCount >= 2) {
              setTimeout(async () => {
                setAnalyzing(false);
                setRefreshingResults(true);
                await fetchAnalysisResults(true);
                setRefreshingResults(false);
              }, 1000);
            }
          } else {
            completionCheckCount = 0;
          }
        } catch (error) {
          console.error('Failed to fetch progress:', error);
        }
      }, 5000);
    }
    
    return () => { if (intervalId) clearInterval(intervalId); };
  }, [analyzing, fetchAnalysisResults]);

  const loadAllStocks = async (forceRefresh = false) => {
    await Promise.all([ fetchAllStocks(forceRefresh), fetchAnalysisResults(forceRefresh) ]);
  };

  const filteredStocks = useMemo(() => {
    const query = searchQuery.toLowerCase();
    let filtered = stocks.filter(stock => {
      const matchesSearch = 
        stock.symbol.toLowerCase().includes(query) ||
        stock.name.toLowerCase().includes(query) ||
        stock.yahoo_symbol.toLowerCase().includes(query) ||
        (stock.verdict || '').toLowerCase().includes(query);
      
      if (!matchesSearch) return false;
      if (filters.verdict !== 'all') {
        if (filters.verdict === 'Not Analyzed') {
          if (stock.verdict && stock.verdict !== '-') return false;
        } else {
          if ((stock.verdict || '').toUpperCase() !== filters.verdict.toUpperCase()) return false;
        }
      }
      if (filters.status !== 'all') {
        if ((stock.status || 'pending') !== filters.status) return false;
      }
      if (filters.hasAnalysis !== 'all') {
        const hasAnalysis = stock.has_analysis || (stock.score !== null && stock.score !== undefined);
        if (filters.hasAnalysis === 'yes' && !hasAnalysis) return false;
        if (filters.hasAnalysis === 'no' && hasAnalysis) return false;
      }
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

    if (!sortBy) return filtered;
    const sortDirectionLodash = sortDirection === 'asc' ? 'asc' : 'desc';
    const sortIteratees = {
      verdict: (s) => (s.verdict || '-').toLowerCase(),
      symbol: (s) => (s.symbol || '').toLowerCase(),
      score: (s) => s.score ?? -1,
      entry: (s) => s.entry ?? -1,
      target: (s) => s.target ?? -1
    };
    return _.orderBy(filtered, [sortIteratees[sortBy], (s) => (s.symbol || '').toLowerCase()], [sortDirectionLodash, 'asc']);
  }, [stocks, searchQuery, sortBy, sortDirection, filters]);

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
    setFilters({ verdict: 'all', status: 'all', scoreMin: '', scoreMax: '', hasAnalysis: 'all' });
    setSearchQuery('');
  }, []);

  const handleSelectAll = useCallback(() => setSelectedStocks(filteredStocks.map(s => s.yahoo_symbol)), [filteredStocks]);
  const handleDeselectAll = useCallback(() => setSelectedStocks([]), []);
  const toggleStockSelection = useCallback((yahooSymbol) => {
    setSelectedStocks(prev => prev.includes(yahooSymbol) ? prev.filter(s => s !== yahooSymbol) : [...prev, yahooSymbol]);
  }, []);

  const handleAnalyzeAll = useCallback(() => {
    if (window.confirm(`Are you sure you want to analyze all ${stocks.length} stocks? This will take several hours.`)) {
      setPendingAnalysisType('all');
      if (!passwordVerified) setShowPasswordModal(true);
      else setShowConfigModal(true);
    }
  }, [stocks.length, passwordVerified]);

  const handleAnalyzeSelected = useCallback(() => {
    if (selectedStocks.length === 0) { alert('Please select at least one stock'); return; }
    if (window.confirm(`Analyze ${selectedStocks.length} selected stocks?`)) {
      setPendingAnalysisType('selected');
      if (selectedStocks.length > 1 && !passwordVerified) setShowPasswordModal(true);
      else setShowConfigModal(true);
    }
  }, [selectedStocks.length, passwordVerified]);

  const handlePasswordSuccess = useCallback(() => {
    setPasswordVerified(true);
    setShowPasswordModal(false);
    setShowConfigModal(true);
  }, []);

  const handleAnalyzeWithConfig = useCallback(async (config) => {
    setShowConfigModal(false);
    const symbolsToAnalyze = pendingAnalysisType === 'all' ? [] : selectedStocks;
    try {
      setAnalyzing(true);
      const response = await analyzeAllStocks(symbolsToAnalyze, config);
      if (response.is_duplicate) {
        alert(`Analysis already running for these stocks.\nProgress: ${response.completed}/${response.total}`);
      }
    } catch (error) {
      console.error('Failed to start analysis:', error);
      alert('Failed to start analysis. Please try again.');
      setAnalyzing(false);
    }
  }, [pendingAnalysisType, selectedStocks]);

  const handleAddToWatchlist = useCallback(() => {
    if (selectedStocks.length === 0) { alert('Please select at least one stock'); return; }
    setShowWatchlistModal(true);
  }, [selectedStocks.length]);

  const handleWatchlistSuccess = useCallback(() => setSelectedStocks([]), []);
  const handleViewDetails = useCallback((ticker) => navigate(`/results/${ticker}`), [navigate]);

  const getStatusBadge = useCallback((status) => {
    const badges = {
      pending: { text: 'Pending', color: 'bg-slate-100 text-slate-600 border-slate-200' },
      analyzing: { text: 'Analyzing...', color: 'bg-accent-50 text-accent-600 border-accent-200' },
      completed: { text: 'Completed', color: 'bg-success-50 text-success-600 border-success-200' },
      failed: { text: 'Failed', color: 'bg-danger-50 text-danger-600 border-danger-200' }
    };
    const badge = badges[status] || badges.pending;
    return <span className={`px-2.5 py-1 rounded-md text-xs font-bold tracking-wide border ${badge.color}`}>{badge.text}</span>;
  }, []);

  const handleSort = useCallback((column) => {
    setSortBy(prev => {
      if (prev === column) {
        setSortDirection(p => p === 'asc' ? 'desc' : 'asc');
        return prev;
      }
      setSortDirection('asc');
      return column;
    });
  }, []);

  const getSortIndicator = useCallback((column) => {
    if (sortBy !== column) return '';
    return sortDirection === 'asc' ? ' ↑' : ' ↓';
  }, [sortBy, sortDirection]);

  return (
    <div className="min-h-screen mesh-bg">
      <NavigationBar />
      <Header title="All Stocks Analysis" subtitle={`Screener and full market overview for ${stocks.length} NSE Stocks.`} />
      <CommandPalette allStocks={stocks} />

      <div className="w-full max-w-7xl mx-auto px-4 pb-20">
        <Breadcrumbs items={[{ label: 'Dashboard', path: '/' }, { label: 'All Stocks', path: null }]} />
        
        {/* Completion Message */}
        {progress && !analyzing && progress.percentage === 100 && (
          <div className="mb-6 p-4 glass-card border-success-200 animate-slide-up">
            <div className="flex gap-3 items-center">
              <div className="flex-shrink-0 w-8 h-8 bg-success-100 text-success-600 rounded-full flex items-center justify-center font-bold">✓</div>
              <div>
                <p className="font-bold text-success-800">Analysis Completed Successfully!</p>
                <p className="text-sm text-success-700 mt-1">Processed {progress.completed}/{progress.total} ({progress.successful} successful, {progress.failed} failed)</p>
              </div>
            </div>
          </div>
        )}

        {/* Progress Bar */}
        {analyzing && progress && (
          <div className="mb-6 glass-card p-6 border-accent-200 animate-slide-up">
            <div className="flex justify-between items-center mb-3">
              <span className="font-bold text-slate-800">Analyzing {progress.completed}/{progress.total} ({progress.percentage}%)</span>
              <span className="text-sm font-medium text-slate-500">ETA: {progress.estimated_time_remaining}</span>
            </div>
            <div className="w-full bg-slate-100 rounded-full h-3 overflow-hidden shadow-inner">
              <div className="bg-gradient-to-r from-accent-400 to-primary-500 h-full transition-all duration-500 rounded-full shadow-glow-primary relative overflow-hidden" style={{ width: `${progress.percentage}%` }}>
                 <div className="absolute inset-0 bg-white/20 animate-shimmer" style={{ backgroundSize: '200% 100%' }}></div>
              </div>
            </div>
            <div className="mt-3 flex justify-between gap-2 text-xs font-semibold text-slate-500">
              <span>Completed: {progress.completed}</span>
              <span>Analyzing: {progress.analyzing}</span>
              <span>Failed: {progress.failed}</span>
              <span>Pending: {progress.pending}</span>
            </div>
          </div>
        )}

        {/* Action Row */}
        <div className="flex flex-wrap gap-3 mb-6 items-center">
          <button onClick={handleAnalyzeAll} disabled={analyzing || loading} className="px-5 py-2.5 bg-gradient-to-r from-primary-600 to-primary-700 hover:from-primary-700 hover:to-primary-800 text-white font-semibold rounded-xl shadow-md transition-all flex items-center gap-2">
            Analyze All Framework
          </button>
          
          <button onClick={handleAnalyzeSelected} disabled={selectedStocks.length === 0 || analyzing || loading} className="px-5 py-2.5 bg-slate-900 hover:bg-slate-800 text-white font-semibold rounded-xl shadow-md transition-all">
            Analyze Selected ({selectedStocks.length})
          </button>

          <button onClick={handleAddToWatchlist} disabled={selectedStocks.length === 0 || loading} className="px-5 py-2.5 bg-white border border-slate-200 text-slate-700 font-semibold rounded-xl shadow-sm hover:bg-slate-50 transition-all flex items-center gap-2">
            + To Watchlist
          </button>
          
          <div className="ml-auto flex items-center gap-3">
            <button onClick={() => loadAllStocks(true)} disabled={loading} className="p-2.5 bg-white border border-slate-200 text-slate-700 rounded-xl shadow-sm hover:bg-slate-50 transition-all">
              <svg className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
            </button>
          </div>
        </div>

        {/* Filter Bar (Glassmorphic) */}
        <div className="mb-8 glass-card p-4 flex flex-col sm:flex-row gap-4">
          <div className="flex-1 relative">
            <input type="text" placeholder="Search by symbol, name, or verdict... (or press ⌘K)" value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="w-full px-4 py-2.5 pl-10 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white/50 text-slate-800 font-medium" />
            <svg className="w-5 h-5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
          </div>
          <button onClick={() => setShowFilters(!showFilters)} className={`px-5 py-2.5 rounded-xl border font-semibold flex items-center gap-2 transition-all ${showFilters || activeFilterCount > 0 ? 'bg-primary-50 border-primary-200 text-primary-700' : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50'}`}>
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" /></svg>
            Filters
            {activeFilterCount > 0 && <span className="bg-primary-600 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center ml-1">{activeFilterCount}</span>}
          </button>
        </div>

        {/* Filter Panel */}
        {showFilters && (
          <div className="mb-8 glass-card p-6 animate-fade-in border-primary-100">
             <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-6">
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Verdict</label>
                  <select value={filters.verdict} onChange={(e) => setFilters(prev => ({ ...prev, verdict: e.target.value }))} className="w-full px-3 py-2 border border-slate-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-primary-500 font-medium text-slate-700">
                    <option value="all">All Verdicts</option>
                    <option value="Strong Buy">Strong Buy</option>
                    <option value="Buy">Buy</option>
                    <option value="Hold">Hold</option>
                    <option value="Sell">Sell</option>
                    <option value="Strong Sell">Strong Sell</option>
                    <option value="Not Analyzed">Not Analyzed</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Status</label>
                  <select value={filters.status} onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))} className="w-full px-3 py-2 border border-slate-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-primary-500 font-medium text-slate-700">
                    <option value="all">All Status</option>
                    <option value="completed">Completed</option>
                    <option value="analyzing">Analyzing</option>
                    <option value="pending">Pending</option>
                    <option value="failed">Failed</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Analysis</label>
                  <select value={filters.hasAnalysis} onChange={(e) => setFilters(prev => ({ ...prev, hasAnalysis: e.target.value }))} className="w-full px-3 py-2 border border-slate-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-primary-500 font-medium text-slate-700">
                    <option value="all">All Stocks</option>
                    <option value="yes">With Analysis</option>
                    <option value="no">Without Analysis</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Min Score</label>
                  <input type="number" placeholder="e.g., 50" value={filters.scoreMin} onChange={(e) => setFilters(prev => ({ ...prev, scoreMin: e.target.value }))} className="w-full px-3 py-2 border border-slate-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-primary-500 font-medium text-slate-700" min="-1" max="1" step="0.1" />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Max Score</label>
                  <input type="number" placeholder="e.g., 100" value={filters.scoreMax} onChange={(e) => setFilters(prev => ({ ...prev, scoreMax: e.target.value }))} className="w-full px-3 py-2 border border-slate-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-primary-500 font-medium text-slate-700" min="-1" max="1" step="0.1" />
                </div>
             </div>
             {activeFilterCount > 0 && (
               <div className="mt-4 pt-4 border-t border-slate-100 flex justify-end">
                 <button onClick={clearAllFilters} className="px-4 py-2 text-sm font-semibold text-danger-600 hover:bg-danger-50 rounded-lg transition-colors">Clear Filters</button>
               </div>
             )}
          </div>
        )}

        <div className="flex justify-between items-center mb-4 text-sm font-medium text-slate-500 px-1">
          <span>Showing {filteredStocks.length} of {stocks.length} stocks</span>
          {lastStocksFetch && !loading && <span>Last synced: {getTimeSinceLastFetch(lastStocksFetch)}</span>}
        </div>

        {/* Stocks Table */}
        <div className="glass-card overflow-hidden">
          {loading ? (
             <div className="text-center py-24">
                <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-primary-100 border-t-primary-600 mb-4 shadow-glow-primary"></div>
                <p className="text-slate-600 font-medium">Loading all NSE stocks...</p>
             </div>
          ) : (
            <div className="overflow-x-auto max-h-[800px] custom-scrollbar">
              <table className="min-w-full bg-white text-sm">
                <thead className="bg-white sticky top-0 z-10 border-b border-slate-200">
                  <tr>
                    <th className="px-5 py-4 w-12 text-center bg-white">
                      <input
                        type="checkbox"
                        checked={selectedStocks.length > 0 && selectedStocks.length === filteredStocks.length}
                        onChange={(e) => e.target.checked ? handleSelectAll() : handleDeselectAll()}
                        className="w-4 h-4 text-primary-600 border-slate-300 rounded focus:ring-primary-500 cursor-pointer"
                      />
                    </th>
                    <th onClick={() => handleSort('symbol')} className="px-5 py-4 text-left text-xs font-bold text-slate-400 uppercase tracking-wider cursor-pointer hover:bg-slate-50 transition-colors bg-white">Symbol{getSortIndicator('symbol')}</th>
                    <th className="hidden md:table-cell px-5 py-4 text-left text-xs font-bold text-slate-400 uppercase tracking-wider bg-white">Company Name</th>
                    <th className="hidden lg:table-cell px-5 py-4 text-left text-xs font-bold text-slate-400 uppercase tracking-wider bg-white">Status</th>
                    <th onClick={() => handleSort('score')} className="px-5 py-4 text-left text-xs font-bold text-slate-400 uppercase tracking-wider cursor-pointer hover:bg-slate-50 transition-colors bg-white">Score Arc{getSortIndicator('score')}</th>
                    <th onClick={() => handleSort('verdict')} className="px-5 py-4 text-left text-xs font-bold text-slate-400 uppercase tracking-wider cursor-pointer hover:bg-slate-50 transition-colors bg-white">Verdict{getSortIndicator('verdict')}</th>
                    <th onClick={() => handleSort('entry')} className="hidden sm:table-cell px-5 py-4 text-left text-xs font-bold text-slate-400 uppercase tracking-wider cursor-pointer hover:bg-slate-50 transition-colors bg-white">Entry{getSortIndicator('entry')}</th>
                    <th onClick={() => handleSort('target')} className="hidden md:table-cell px-5 py-4 text-left text-xs font-bold text-slate-400 uppercase tracking-wider cursor-pointer hover:bg-slate-50 transition-colors bg-white">Target{getSortIndicator('target')}</th>
                    <th className="hidden sm:table-cell px-5 py-4 text-right text-xs font-bold text-slate-400 uppercase tracking-wider bg-white">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
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
          )}
        </div>
      </div>

      {showWatchlistModal && (
        <AddToWatchlistModal
          onClose={() => setShowWatchlistModal(false)}
          onSuccess={handleWatchlistSuccess}
          selectedStocks={selectedStocks}
          stocksData={stocks}
        />
      )}
      {showConfigModal && (
        <AnalysisConfigModal
          onClose={() => setShowConfigModal(false)}
          onConfirm={handleAnalyzeWithConfig}
          stockCount={pendingAnalysisType === 'all' ? stocks.length : selectedStocks.length}
          stockNames={pendingAnalysisType === 'all' ? [] : selectedStocks}
          title="Deep Dive Analysis Configuration"
        />
      )}
      {showPasswordModal && <PasswordModal onClose={() => setShowPasswordModal(false)} onSuccess={handlePasswordSuccess} />}
    </div>
  );
}

export default AllStocksAnalysis;
