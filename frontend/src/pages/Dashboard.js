import { useEffect, useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  addToWatchlist, 
  analyzeStocks, 
  cancelJob, 
  getJobStatus, 
  getWatchlistCollections,
  getWatchlist,
  getStockHistory,
  removeFromWatchlist,
  deleteWatchlistCollection
} from '../api/api';
import AddStockModal from '../components/AddStockModal';
import AnalysisConfigModal from '../components/AnalysisConfigModal';
import NavigationBar from '../components/NavigationBar';
import { TradingViewLink } from '../utils/tradingViewUtils';

// Verdict styling helper
const getVerdictStyle = (verdict) => {
  switch (verdict) {
    case 'Strong Buy':
      return { bg: 'bg-emerald-500', text: 'text-emerald-500', pill: 'bg-emerald-500/10 text-emerald-600 border-emerald-500/20' };
    case 'Buy':
      return { bg: 'bg-green-500', text: 'text-green-500', pill: 'bg-green-500/10 text-green-600 border-green-500/20' };
    case 'Strong Sell':
      return { bg: 'bg-red-600', text: 'text-red-600', pill: 'bg-red-500/10 text-red-600 border-red-500/20' };
    case 'Sell':
      return { bg: 'bg-rose-500', text: 'text-rose-500', pill: 'bg-rose-500/10 text-rose-600 border-rose-500/20' };
    case 'Neutral':
    case 'Hold':
      return { bg: 'bg-amber-500', text: 'text-amber-500', pill: 'bg-amber-500/10 text-amber-600 border-amber-500/20' };
    default:
      return { bg: 'bg-slate-400', text: 'text-slate-400', pill: 'bg-slate-500/10 text-slate-500 border-slate-500/20' };
  }
};

// Confidence bar component
const ConfidenceBar = ({ value, size = 'md' }) => {
  const percentage = Math.abs(value * 100);
  const isPositive = value >= 0;
  const height = size === 'sm' ? 'h-1' : 'h-1.5';
  
  return (
    <div className={`w-full bg-slate-700/50 rounded-full ${height} overflow-hidden`}>
      <div 
        className={`${height} rounded-full transition-all duration-500 ${isPositive ? 'bg-emerald-500' : 'bg-rose-500'}`}
        style={{ width: `${Math.min(percentage, 100)}%` }}
      />
    </div>
  );
};

// Stock row component for the watchlist cards
const StockRow = ({ stock, isSelected, onSelect, onView, onRemove }) => {
  const verdictStyle = getVerdictStyle(stock.verdict);
  
  return (
    <div className={`group flex items-center gap-3 px-4 py-3 border-b border-slate-700/50 last:border-0 hover:bg-slate-700/30 transition-colors ${isSelected ? 'bg-blue-500/10' : ''}`}>
      {/* Checkbox */}
      <input
        type="checkbox"
        checked={isSelected}
        onChange={() => onSelect(stock.ticker)}
        className="w-4 h-4 rounded border-slate-600 bg-slate-700 text-blue-500 focus:ring-blue-500 focus:ring-offset-0 focus:ring-offset-slate-800 cursor-pointer"
      />
      
      {/* Symbol & Name */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <TradingViewLink 
            ticker={stock.ticker}
            className="font-mono text-sm font-semibold text-white hover:text-blue-400 transition-colors"
          />
          {stock.has_analysis && (
            <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${verdictStyle.pill}`}>
              {stock.verdict}
            </span>
          )}
        </div>
        <p className="text-xs text-slate-400 truncate mt-0.5">{stock.name || 'Unknown'}</p>
      </div>
      
      {/* Confidence */}
      <div className="w-20 hidden sm:block">
        {stock.has_analysis ? (
          <div className="space-y-1">
            <div className="text-xs text-slate-400 text-right">
              {stock.confidence >= 0 ? '+' : ''}{(stock.confidence * 100).toFixed(0)}%
            </div>
            <ConfidenceBar value={stock.confidence} size="sm" />
          </div>
        ) : (
          <span className="text-xs text-slate-500">—</span>
        )}
      </div>
      
      {/* Actions */}
      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
        {stock.has_analysis && (
          <button
            onClick={() => onView(stock.ticker)}
            className="p-1.5 rounded-lg bg-blue-500/10 text-blue-400 hover:bg-blue-500/20 transition-colors"
            title="View Analysis"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
          </button>
        )}
        <button
          onClick={() => onRemove(stock.ticker)}
          className="p-1.5 rounded-lg bg-rose-500/10 text-rose-400 hover:bg-rose-500/20 transition-colors"
          title="Remove"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
        </button>
      </div>
    </div>
  );
};

// Watchlist Card component
const WatchlistCard = ({ 
  collection, 
  stocks, 
  loading, 
  selectedStocks, 
  onSelectStock, 
  onSelectAll,
  onViewStock,
  onRemoveStock,
  onDeleteCollection,
  onAnalyze
}) => {
  const [isExpanded, setIsExpanded] = useState(true);
  
  // Calculate stats
  const stats = useMemo(() => {
    const analyzed = stocks.filter(s => s.has_analysis);
    const buySignals = stocks.filter(s => s.verdict === 'Buy' || s.verdict === 'Strong Buy').length;
    const sellSignals = stocks.filter(s => s.verdict === 'Sell' || s.verdict === 'Strong Sell').length;
    const holdSignals = stocks.filter(s => s.verdict === 'Neutral' || s.verdict === 'Hold').length;
    
    return { analyzed: analyzed.length, buySignals, sellSignals, holdSignals };
  }, [stocks]);
  
  const selectedInCollection = stocks.filter(s => selectedStocks.includes(s.ticker)).length;
  const allSelected = stocks.length > 0 && selectedInCollection === stocks.length;
  
  // Collection color based on performance
  const getCollectionAccent = () => {
    if (stats.buySignals > stats.sellSignals) return 'from-emerald-500/20 to-emerald-500/5';
    if (stats.sellSignals > stats.buySignals) return 'from-rose-500/20 to-rose-500/5';
    return 'from-blue-500/20 to-blue-500/5';
  };

  return (
    <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl border border-slate-700/50 overflow-hidden shadow-xl hover:shadow-2xl transition-shadow duration-300">
      {/* Card Header */}
      <div className={`relative bg-gradient-to-r ${getCollectionAccent()} px-5 py-4`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="p-1 rounded-lg hover:bg-white/10 transition-colors"
            >
              <svg 
                className={`w-5 h-5 text-slate-300 transition-transform duration-200 ${isExpanded ? 'rotate-0' : '-rotate-90'}`} 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            <div>
              <h3 className="text-lg font-bold text-white">{collection.name}</h3>
              <p className="text-sm text-slate-400">{stocks.length} stocks • {stats.analyzed} analyzed</p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            {/* Signal Pills */}
            {stats.buySignals > 0 && (
              <span className="px-2 py-1 rounded-lg bg-emerald-500/20 text-emerald-400 text-xs font-semibold">
                {stats.buySignals} Buy
              </span>
            )}
            {stats.sellSignals > 0 && (
              <span className="px-2 py-1 rounded-lg bg-rose-500/20 text-rose-400 text-xs font-semibold">
                {stats.sellSignals} Sell
              </span>
            )}
            {stats.holdSignals > 0 && (
              <span className="px-2 py-1 rounded-lg bg-amber-500/20 text-amber-400 text-xs font-semibold">
                {stats.holdSignals} Hold
              </span>
            )}
            
            {/* Delete Collection (only for non-default) */}
            {collection.id !== null && (
              <button
                onClick={() => onDeleteCollection(collection.id, collection.name)}
                className="p-1.5 rounded-lg hover:bg-rose-500/20 text-slate-400 hover:text-rose-400 transition-colors"
                title="Delete Collection"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>
        </div>
        
        {/* Quick Actions Bar */}
        {isExpanded && stocks.length > 0 && (
          <div className="flex items-center gap-3 mt-3 pt-3 border-t border-white/10">
            <label className="flex items-center gap-2 text-sm text-slate-300 cursor-pointer hover:text-white transition-colors">
              <input
                type="checkbox"
                checked={allSelected}
                onChange={(e) => onSelectAll(collection.id, stocks, e.target.checked)}
                className="w-4 h-4 rounded border-slate-600 bg-slate-700 text-blue-500 focus:ring-blue-500 focus:ring-offset-0"
              />
              Select All
            </label>
            {selectedInCollection > 0 && (
              <button
                onClick={() => onAnalyze(stocks.filter(s => selectedStocks.includes(s.ticker)).map(s => s.ticker))}
                className="px-3 py-1.5 rounded-lg bg-blue-500 hover:bg-blue-600 text-white text-sm font-medium transition-colors"
              >
                Analyze {selectedInCollection} Selected
              </button>
            )}
          </div>
        )}
      </div>
      
      {/* Stock List */}
      {isExpanded && (
        <div className="max-h-[400px] overflow-y-auto custom-scrollbar">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-2 border-blue-500 border-t-transparent"></div>
            </div>
          ) : stocks.length === 0 ? (
            <div className="text-center py-12 px-4">
              <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-slate-700/50 flex items-center justify-center">
                <svg className="w-8 h-8 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
                </svg>
              </div>
              <p className="text-slate-400 text-sm">No stocks in this watchlist</p>
              <p className="text-slate-500 text-xs mt-1">Add stocks from the All Stocks page</p>
            </div>
          ) : (
            stocks.map((stock) => (
              <StockRow
                key={stock.ticker}
                stock={stock}
                isSelected={selectedStocks.includes(stock.ticker)}
                onSelect={onSelectStock}
                onView={onViewStock}
                onRemove={onRemoveStock}
              />
            ))
          )}
        </div>
      )}
    </div>
  );
};

// Summary Stats Card
const SummaryCard = ({ icon, label, value, subValue, color }) => (
  <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700/50 p-4">
    <div className="flex items-center gap-3">
      <div className={`p-2 rounded-lg ${color}`}>
        {icon}
      </div>
      <div>
        <p className="text-2xl font-bold text-white">{value}</p>
        <p className="text-sm text-slate-400">{label}</p>
        {subValue && <p className="text-xs text-slate-500">{subValue}</p>}
      </div>
    </div>
  </div>
);

function Dashboard() {
  const [collections, setCollections] = useState([]);
  const [watchlistData, setWatchlistData] = useState({}); // { collectionId: stocks[] }
  const [loading, setLoading] = useState(true);
  const [selectedStocks, setSelectedStocks] = useState([]);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState(0);
  const [jobId, setJobId] = useState(null);
  const [analysisStatus, setAnalysisStatus] = useState({});
  const navigate = useNavigate();

  // Load all data on mount
  useEffect(() => {
    loadAllData();
    
    // Check for active job
    const savedJobId = sessionStorage.getItem('activeJobId');
    if (savedJobId) {
      setJobId(savedJobId);
      setAnalyzing(true);
      pollJobStatus(savedJobId);
    }
  }, []);

  const loadAllData = async () => {
    setLoading(true);
    try {
      // Load collections
      const collectionsData = await getWatchlistCollections();
      setCollections(collectionsData);
      
      // Load stocks for each collection in parallel
      const watchlistPromises = collectionsData.map(async (col) => {
        const collectionId = col.id === null ? 'default' : col.id;
        const stocks = await getWatchlist(collectionId);
        
        // Enrich with analysis data
        const enrichedStocks = await Promise.all(
          stocks.filter(s => s.ticker && s.ticker.trim()).map(async (stock) => {
            try {
              const historyData = await getStockHistory(stock.ticker);
              if (historyData?.history?.length > 0) {
                const latest = historyData.history[0];
                return {
                  ...stock,
                  verdict: latest.verdict || '-',
                  confidence: (latest.score / 100) || 0,
                  has_analysis: true
                };
              }
            } catch (err) {
              console.error(`Error fetching history for ${stock.ticker}:`, err);
            }
            return { ...stock, verdict: '-', confidence: 0, has_analysis: false };
          })
        );
        
        return { collectionId, stocks: enrichedStocks };
      });
      
      const results = await Promise.all(watchlistPromises);
      const watchlistMap = {};
      results.forEach(({ collectionId, stocks }) => {
        watchlistMap[collectionId] = stocks;
      });
      setWatchlistData(watchlistMap);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  // Calculate global stats
  const globalStats = useMemo(() => {
    const allStocks = Object.values(watchlistData).flat();
    const analyzed = allStocks.filter(s => s.has_analysis);
    const buySignals = allStocks.filter(s => s.verdict === 'Buy' || s.verdict === 'Strong Buy').length;
    const sellSignals = allStocks.filter(s => s.verdict === 'Sell' || s.verdict === 'Strong Sell').length;
    
    return {
      totalStocks: allStocks.length,
      analyzed: analyzed.length,
      buySignals,
      sellSignals,
      watchlists: collections.length
    };
  }, [watchlistData, collections]);

  const handleSelectStock = (ticker) => {
    setSelectedStocks(prev => 
      prev.includes(ticker) ? prev.filter(t => t !== ticker) : [...prev, ticker]
    );
  };

  const handleSelectAll = (collectionId, stocks, checked) => {
    const tickers = stocks.map(s => s.ticker);
    if (checked) {
      setSelectedStocks(prev => [...new Set([...prev, ...tickers])]);
    } else {
      setSelectedStocks(prev => prev.filter(t => !tickers.includes(t)));
    }
  };

  const handleViewStock = (ticker) => {
    navigate(`/results/${ticker}`);
  };

  const handleRemoveStock = async (ticker) => {
    if (window.confirm(`Remove ${ticker} from watchlist?`)) {
      try {
        await removeFromWatchlist(ticker);
        // Update local state
        setWatchlistData(prev => {
          const updated = { ...prev };
          Object.keys(updated).forEach(key => {
            updated[key] = updated[key].filter(s => s.ticker !== ticker);
          });
          return updated;
        });
        setSelectedStocks(prev => prev.filter(t => t !== ticker));
      } catch (error) {
        console.error('Failed to remove stock:', error);
      }
    }
  };

  const handleDeleteCollection = async (collectionId, name) => {
    if (window.confirm(`Delete "${name}"? Stocks will be moved to Default watchlist.`)) {
      try {
        await deleteWatchlistCollection(collectionId);
        await loadAllData(); // Refresh all data
      } catch (error) {
        console.error('Failed to delete collection:', error);
      }
    }
  };

  const handleAnalyze = (tickers) => {
    if (tickers.length === 0) {
      alert('Please select at least one stock');
      return;
    }
    setSelectedStocks(tickers);
    setShowConfigModal(true);
  };

  const handleAnalyzeWithConfig = async (config) => {
    setShowConfigModal(false);
    
    try {
      setAnalyzing(true);
      setAnalysisProgress(0);

      const result = await analyzeStocks(selectedStocks, config);
      const newJobId = result.job_id;
      setJobId(newJobId);
      sessionStorage.setItem('activeJobId', newJobId);
      pollJobStatus(newJobId);
    } catch (error) {
      setAnalyzing(false);
      console.error('Failed to analyze:', error);
      alert('Analysis failed. Please try again.');
    }
  };

  const pollJobStatus = async (jobIdToPoll) => {
    const interval = setInterval(async () => {
      try {
        const status = await getJobStatus(jobIdToPoll);
        setAnalysisProgress(status.progress);
        setAnalysisStatus(status);

        if (status.status === 'completed' || status.status === 'failed' || status.status === 'cancelled') {
          clearInterval(interval);
          setAnalyzing(false);
          sessionStorage.removeItem('activeJobId');
          
          if (status.status === 'completed') {
            await loadAllData();
            alert(`Analysis completed! ${status.successful || status.completed}/${status.total} stocks analyzed.`);
          } else if (status.status === 'failed') {
            alert('Analysis failed. Please check the logs.');
          } else if (status.status === 'cancelled') {
            alert('Analysis was cancelled.');
          }
        }
      } catch (error) {
        clearInterval(interval);
        setAnalyzing(false);
        sessionStorage.removeItem('activeJobId');
        console.error('Failed to get status:', error);
      }
    }, 2000);
  };

  const handleCancelAnalysis = async () => {
    if (!jobId) return;
    if (window.confirm('Cancel the running analysis?')) {
      try {
        await cancelJob(jobId);
        setAnalyzing(false);
        sessionStorage.removeItem('activeJobId');
      } catch (error) {
        console.error('Failed to cancel:', error);
      }
    }
  };

  const handleAddStock = async (symbol, name) => {
    try {
      await addToWatchlist(symbol, name);
      setShowAddModal(false);
      await loadAllData(); // Refresh to show new stock
    } catch (error) {
      console.error('Failed to add stock:', error);
      alert('Failed to add stock. Please try again.');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-900 to-slate-800">
      <NavigationBar />
      
      {/* Hero Header */}
      <div className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-blue-500/10 via-purple-500/10 to-emerald-500/10"></div>
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiMyMDIwMjAiIGZpbGwtb3BhY2l0eT0iMC4xIj48Y2lyY2xlIGN4PSIxIiBjeT0iMSIgcj0iMSIvPjwvZz48L2c+PC9zdmc+')] opacity-50"></div>
        
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
            <div>
              <h1 className="text-3xl lg:text-4xl font-bold text-white tracking-tight">
                Trading Dashboard
              </h1>
              <p className="mt-2 text-slate-400">
                Monitor your watchlists and analyze market signals
              </p>
            </div>
            
            {/* Quick Actions */}
            <div className="flex flex-wrap items-center gap-3">
              <button
                onClick={() => setShowAddModal(true)}
                className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-700/50 border border-slate-600/50 text-white hover:bg-slate-700 transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                Add Stock
              </button>
              
              <button
                onClick={loadAllData}
                disabled={loading}
                className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-700/50 border border-slate-600/50 text-white hover:bg-slate-700 transition-colors disabled:opacity-50"
              >
                <svg className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                {loading ? 'Loading...' : 'Refresh'}
              </button>
              
              {selectedStocks.length > 0 && (
                <button
                  onClick={() => handleAnalyze(selectedStocks)}
                  disabled={analyzing}
                  className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-blue-500 to-blue-600 text-white font-semibold hover:from-blue-600 hover:to-blue-700 transition-all shadow-lg shadow-blue-500/25 disabled:opacity-50"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                  Analyze {selectedStocks.length} Selected
                </button>
              )}
            </div>
          </div>
          
          {/* Summary Stats */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mt-8">
            <SummaryCard
              icon={<svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" /></svg>}
              label="Total Stocks"
              value={globalStats.totalStocks}
              subValue={`${globalStats.analyzed} analyzed`}
              color="bg-blue-500/20"
            />
            <SummaryCard
              icon={<svg className="w-5 h-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" /></svg>}
              label="Watchlists"
              value={globalStats.watchlists}
              color="bg-purple-500/20"
            />
            <SummaryCard
              icon={<svg className="w-5 h-5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" /></svg>}
              label="Buy Signals"
              value={globalStats.buySignals}
              color="bg-emerald-500/20"
            />
            <SummaryCard
              icon={<svg className="w-5 h-5 text-rose-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" /></svg>}
              label="Sell Signals"
              value={globalStats.sellSignals}
              color="bg-rose-500/20"
            />
          </div>
        </div>
      </div>
      
      {/* Analysis Progress Banner */}
      {analyzing && (
        <div className="sticky top-0 z-40 bg-slate-800/95 backdrop-blur-sm border-b border-slate-700/50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <div className="flex items-center justify-between gap-4">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <div className="animate-pulse w-2 h-2 rounded-full bg-blue-500"></div>
                  <span className="text-sm font-medium text-white">
                    Analysis in Progress
                  </span>
                  <span className="text-sm text-slate-400">
                    {analysisProgress}% • {analysisStatus.completed || 0}/{analysisStatus.total || 0} stocks
                  </span>
                </div>
                <div className="w-full bg-slate-700 rounded-full h-2 overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-blue-500 to-blue-400 rounded-full transition-all duration-300"
                    style={{ width: `${analysisProgress}%` }}
                  ></div>
                </div>
              </div>
              <button
                onClick={handleCancelAnalysis}
                className="px-4 py-2 rounded-lg bg-rose-500/20 text-rose-400 hover:bg-rose-500/30 transition-colors text-sm font-medium"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* Watchlist Cards Grid */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {loading && Object.keys(watchlistData).length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20">
            <div className="animate-spin rounded-full h-12 w-12 border-2 border-blue-500 border-t-transparent mb-4"></div>
            <p className="text-slate-400">Loading your watchlists...</p>
          </div>
        ) : collections.length === 0 ? (
          <div className="text-center py-20">
            <div className="w-24 h-24 mx-auto mb-6 rounded-full bg-slate-800 flex items-center justify-center">
              <svg className="w-12 h-12 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">No Watchlists Yet</h3>
            <p className="text-slate-400 mb-6">Start by adding stocks to track your investments</p>
            <button
              onClick={() => setShowAddModal(true)}
              className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-blue-500 text-white font-semibold hover:bg-blue-600 transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Add Your First Stock
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {collections.map((collection) => {
              const collectionKey = collection.id === null ? 'default' : collection.id;
              return (
                <WatchlistCard
                  key={collectionKey}
                  collection={collection}
                  stocks={watchlistData[collectionKey] || []}
                  loading={loading}
                  selectedStocks={selectedStocks}
                  onSelectStock={handleSelectStock}
                  onSelectAll={handleSelectAll}
                  onViewStock={handleViewStock}
                  onRemoveStock={handleRemoveStock}
                  onDeleteCollection={handleDeleteCollection}
                  onAnalyze={handleAnalyze}
                />
              );
            })}
          </div>
        )}
      </div>
      
      {/* Custom Scrollbar Styles */}
      <style>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 6px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: rgba(30, 41, 59, 0.5);
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(100, 116, 139, 0.5);
          border-radius: 3px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(100, 116, 139, 0.7);
        }
      `}</style>

      {/* Modals */}
      {showAddModal && (
        <AddStockModal
          onClose={() => setShowAddModal(false)}
          onAdd={handleAddStock}
          existingSymbols={Object.values(watchlistData).flat().map(s => s.ticker)}
        />
      )}

      {showConfigModal && (
        <AnalysisConfigModal
          onClose={() => setShowConfigModal(false)}
          onConfirm={handleAnalyzeWithConfig}
          stockCount={selectedStocks.length}
          stockNames={selectedStocks}
          title="Configure Analysis"
        />
      )}
    </div>
  );
}

export default Dashboard;
