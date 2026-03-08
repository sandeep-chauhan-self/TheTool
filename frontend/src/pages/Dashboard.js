import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    addToWatchlist,
    analyzeStocks,
    cancelJob,
    deleteWatchlistCollection,
    getJobStatus,
    getStockHistory,
    getWatchlist,
    getWatchlistCollections,
    removeFromWatchlist
} from '../api/api';
import AddStockModal from '../components/AddStockModal';
import PasswordModal from '../components/PasswordModal';
import AnalysisConfigModal from '../components/AnalysisConfigModal';
import Breadcrumbs from '../components/Breadcrumbs';
import Header from '../components/Header';
import NavigationBar from '../components/NavigationBar';
import { TradingViewLink } from '../utils/tradingViewUtils';

// New UI Components
import SignalHeatMap from '../components/ui/SignalHeatMap';
import VerdictBadge from '../components/ui/VerdictBadge';
import ScoreArc from '../components/ui/ScoreArc';
import MicroSparkline from '../components/ui/MicroSparkline';
import CommandPalette from '../components/ui/CommandPalette';

// Stock row component for the watchlist cards (Redesigned)
const StockRow = ({ stock, isSelected, onSelect, onView, onRemove }) => {
  return (
    <tr className="table-row-modern group">
      <td className="px-5 py-4 w-12 text-center">
        <input
          type="checkbox"
          checked={isSelected}
          onChange={() => onSelect(stock.ticker)}
          className="w-4 h-4 rounded border-slate-300 text-primary-600 focus:ring-primary-500 cursor-pointer"
        />
      </td>
      <td className="px-5 py-4 font-mono font-bold text-slate-900">
        <TradingViewLink 
          ticker={stock.ticker}
          className="hover:text-primary-600 transition-colors"
        />
      </td>
      <td className="px-5 py-4 text-slate-500 font-medium truncate max-w-xs">{stock.name || '-'}</td>
      
      {/* 7-Day Trend Sparkline (Mocked or real history) */}
      <td className="px-5 py-4 hidden sm:table-cell">
        <MicroSparkline data={stock.history || []} />
      </td>

      <td className="px-5 py-4">
        {stock.has_analysis ? <VerdictBadge verdict={stock.verdict} /> : <span className="text-xs text-slate-400 italic">Unanalyzed</span>}
      </td>
      <td className="px-5 py-4">
        {stock.has_analysis ? <ScoreArc score={stock.rawScore} /> : <span className="text-slate-400">-</span>}
      </td>
      <td className="px-5 py-4 text-right">
        <div className="flex justify-end gap-3 opacity-0 group-hover:opacity-100 transition-opacity">
          {stock.has_analysis && (
            <button
              onClick={() => onView(stock.ticker)}
              className="text-primary-600 hover:text-primary-800 font-medium text-sm transition-colors"
            >
              View Analysis
            </button>
          )}
          <button
            onClick={() => onRemove(stock.ticker)}
            className="text-slate-400 hover:text-danger-600 transition-colors"
            title="Remove from Watchlist"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </td>
    </tr>
  );
};

// Watchlist Accordion Card
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

  return (
    <div className="glass-card mb-8 overflow-hidden transition-all duration-300">
      {/* Decorative gradient top border */}
      <div className="h-1 w-full bg-gradient-to-r from-primary-400 via-accent-400 to-success-400"></div>
      
      {/* Card Header */}
      <div className="px-6 py-5 bg-white flex flex-col sm:flex-row sm:items-center justify-between gap-4 cursor-pointer" onClick={() => setIsExpanded(!isExpanded)}>
        <div className="flex items-center gap-4">
          <div className={`p-2 rounded-lg bg-slate-50 border border-slate-100 transition-transform duration-300 ${isExpanded ? 'rotate-180' : 'rotate-0'}`}>
            <svg className="w-5 h-5 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </div>
          <div>
            <h3 className="text-xl font-bold text-slate-800 tracking-tight">{collection.name}</h3>
            <div className="flex items-center gap-2 mt-1 text-sm font-medium text-slate-500">
              <span>{stocks.length} assets</span>
              <span className="w-1 h-1 rounded-full bg-slate-300"></span>
              <span>{stats.analyzed} analyzed</span>
            </div>
          </div>
        </div>
        
        <div className="flex items-center gap-3" onClick={e => e.stopPropagation()}>
          {/* Signal summary pills (compact) */}
          <div className="flex bg-slate-50 border border-slate-200 rounded-lg p-1">
            <div className="px-3 py-1 flex items-center gap-1.5"><div className="w-1.5 h-1.5 rounded-full bg-success-500"></div><span className="text-xs font-bold text-slate-700">{stats.buySignals}</span></div>
            <div className="px-3 py-1 border-l border-slate-200 flex items-center gap-1.5"><div className="w-1.5 h-1.5 rounded-full bg-warning-500"></div><span className="text-xs font-bold text-slate-700">{stats.holdSignals}</span></div>
            <div className="px-3 py-1 border-l border-slate-200 flex items-center gap-1.5"><div className="w-1.5 h-1.5 rounded-full bg-danger-500"></div><span className="text-xs font-bold text-slate-700">{stats.sellSignals}</span></div>
          </div>
          
          {/* Delete Collection */}
          {collection.id !== null && (
            <button
              onClick={() => onDeleteCollection(collection.id, collection.name)}
              className="p-2 rounded-lg hover:bg-danger-50 text-slate-400 hover:text-danger-600 transition-colors"
              title="Delete Collection"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
            </button>
          )}
        </div>
      </div>
      
      {/* Expanded Content */}
      <div className={`transition-all duration-300 ease-in-out ${isExpanded ? 'opacity-100 max-h-[800px]' : 'opacity-0 max-h-0'}`}>
        {/* Quick Actions Bar */}
        <div className="px-6 py-3 bg-slate-50/50 border-t border-b border-slate-100 flex items-center justify-between">
          <label className="flex items-center gap-2 text-sm font-semibold text-slate-700 cursor-pointer hover:text-primary-600 transition-colors">
            <input
              type="checkbox"
              checked={allSelected}
              onChange={(e) => onSelectAll(collection.id, stocks, e.target.checked)}
              className="w-4 h-4 rounded border-slate-300 text-primary-600 focus:ring-primary-500 cursor-pointer"
            />
            Select All
          </label>
          
          {selectedInCollection > 0 && (
            <button
              onClick={() => onAnalyze(stocks.filter(s => selectedStocks.includes(s.ticker)).map(s => s.ticker))}
              className="px-4 py-1.5 rounded-full bg-slate-900 border border-slate-700 text-white text-sm font-semibold hover:bg-slate-800 transition-all shadow-md flex items-center gap-2"
            >
              <svg className="w-4 h-4 text-accent-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
              Analyze {selectedInCollection} Selected
            </button>
          )}
        </div>
        
        {/* Stock List Table */}
        <div className="overflow-x-auto max-h-[500px] custom-scrollbar">
          {loading ? (
            <div className="flex items-center justify-center py-16">
              <div className="animate-spin rounded-full h-10 w-10 border-4 border-primary-200 border-t-primary-600"></div>
            </div>
          ) : stocks.length === 0 ? (
            <div className="text-center py-16 bg-white">
              <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" /></svg>
              </div>
              <p className="text-slate-600 font-medium">Empty Watchlist</p>
              <p className="text-slate-400 text-sm mt-1">Add assets to start analyzing</p>
            </div>
          ) : (
            <table className="min-w-full bg-white">
              <thead className="bg-white sticky top-0 z-10 border-b border-slate-200">
                <tr>
                  <th className="px-5 py-4 text-left w-12"></th>
                  <th className="px-5 py-4 text-left text-xs font-bold text-slate-400 uppercase tracking-wider">Symbol</th>
                  <th className="px-5 py-4 text-left text-xs font-bold text-slate-400 uppercase tracking-wider">Company Name</th>
                  <th className="px-5 py-4 text-left text-xs font-bold text-slate-400 uppercase tracking-wider hidden sm:table-cell">7D Trend</th>
                  <th className="px-5 py-4 text-left text-xs font-bold text-slate-400 uppercase tracking-wider">Signal AI</th>
                  <th className="px-5 py-4 text-left text-xs font-bold text-slate-400 uppercase tracking-wider">Conviction</th>
                  <th className="px-5 py-4 text-right text-xs font-bold text-slate-400 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody>
                {stocks.map((stock) => (
                  <StockRow
                    key={stock.ticker}
                    stock={stock}
                    isSelected={selectedStocks.includes(stock.ticker)}
                    onSelect={onSelectStock}
                    onView={onViewStock}
                    onRemove={onRemoveStock}
                  />
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
};

function Dashboard() {
  const [collections, setCollections] = useState([]);
  const [watchlistData, setWatchlistData] = useState({}); // { collectionId: stocks[] }
  const [loading, setLoading] = useState(true);
  const [selectedStocks, setSelectedStocks] = useState([]);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [passwordVerified, setPasswordVerified] = useState(() => sessionStorage.getItem('bulkAnalysisVerified') === 'true');
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState(0);
  const [jobId, setJobId] = useState(null);
  const [analysisStatus, setAnalysisStatus] = useState({});
  const navigate = useNavigate();

  // Load all data on mount
  useEffect(() => {
    loadAllData();
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
      const collectionsData = await getWatchlistCollections();
      setCollections(collectionsData);
      
      const watchlistPromises = collectionsData.map(async (col) => {
        const collectionId = col.id === null ? 'default' : col.id;
        const stocks = await getWatchlist(collectionId);
        
        const enrichedStocks = await Promise.all(
          stocks.filter(s => s.ticker && s.ticker.trim()).map(async (stock) => {
            try {
              const historyData = await getStockHistory(stock.ticker);
              if (historyData?.history?.length > 0) {
                const latest = historyData.history[0];
                return {
                  ...stock,
                  verdict: latest.verdict || '-',
                  rawScore: latest.score ? (latest.score / 100) : 0, 
                  has_analysis: true,
                  // Map history scores for sparklines
                  history: historyData.history.slice(0, 10).map(h => (h.score/100) || 0).reverse()
                };
              }
            } catch (err) {
              console.error(`Error fetching history for ${stock.ticker}:`, err);
            }
            return { ...stock, verdict: '-', rawScore: 0, has_analysis: false, history: [] };
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

  const globalStats = useMemo(() => {
    const allStocks = Object.values(watchlistData).flat();
    const buySignals = allStocks.filter(s => s.verdict === 'Buy' || s.verdict === 'Strong Buy').length;
    const sellSignals = allStocks.filter(s => s.verdict === 'Sell' || s.verdict === 'Strong Sell').length;
    const holdSignals = allStocks.filter(s => s.verdict === 'Neutral' || s.verdict === 'Hold').length;
    
    return {
      BUY: buySignals,
      SELL: sellSignals,
      HOLD: holdSignals
    };
  }, [watchlistData]);

  const allStocksFlat = useMemo(() => Object.values(watchlistData).flat(), [watchlistData]);

  const handleSelectStock = (ticker) => setSelectedStocks(prev => prev.includes(ticker) ? prev.filter(t => t !== ticker) : [...prev, ticker]);
  
  const handleSelectAll = (collectionId, stocks, checked) => {
    const tickers = stocks.map(s => s.ticker);
    if (checked) setSelectedStocks(prev => [...new Set([...prev, ...tickers])]);
    else setSelectedStocks(prev => prev.filter(t => !tickers.includes(t)));
  };

  const handleViewStock = (ticker) => navigate(`/results/${ticker}`);

  const handleRemoveStock = async (ticker) => {
    if (window.confirm(`Remove ${ticker} from watchlist?`)) {
      try {
        await removeFromWatchlist(ticker);
        setWatchlistData(prev => {
          const updated = { ...prev };
          Object.keys(updated).forEach(k => updated[k] = updated[k].filter(s => s.ticker !== ticker));
          return updated;
        });
        setSelectedStocks(prev => prev.filter(t => t !== ticker));
      } catch (error) { console.error('Failed to remove stock:', error); }
    }
  };

  const handleDeleteCollection = async (collectionId, name) => {
    if (window.confirm(`Delete "${name}"? Stocks will be moved to Default watchlist.`)) {
      try {
        await deleteWatchlistCollection(collectionId);
        await loadAllData();
      } catch (error) { console.error('Failed to delete collection:', error); }
    }
  };

  const handleAnalyze = (tickers) => {
    if (tickers.length === 0) { alert('Please select at least one stock'); return; }
    setSelectedStocks(tickers);
    if (tickers.length > 1 && !passwordVerified) setShowPasswordModal(true);
    else setShowConfigModal(true);
  };

  const handlePasswordSuccess = () => {
    setPasswordVerified(true);
    setShowPasswordModal(false);
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
      alert('Analysis failed. Please try again.');
    }
  };

  const pollJobStatus = async (jobIdToPoll) => {
    const interval = setInterval(async () => {
      try {
        const status = await getJobStatus(jobIdToPoll);
        setAnalysisProgress(status.progress);
        setAnalysisStatus(status);
        if (['completed', 'failed', 'cancelled'].includes(status.status)) {
          clearInterval(interval);
          setAnalyzing(false);
          sessionStorage.removeItem('activeJobId');
          if (status.status === 'completed') {
            await loadAllData();
          }
        }
      } catch (error) {
        clearInterval(interval);
        setAnalyzing(false);
        sessionStorage.removeItem('activeJobId');
      }
    }, 2000);
  };

  const handleCancelAnalysis = async () => {
    if (!jobId) return;
    if (window.confirm('Cancel running analysis?')) {
      try {
        await cancelJob(jobId);
        setAnalyzing(false);
        sessionStorage.removeItem('activeJobId');
      } catch (error) { console.error('Failed to cancel:', error); }
    }
  };

  const handleAddStock = async (symbol, name) => {
    try {
      await addToWatchlist(symbol, name);
      setShowAddModal(false);
      await loadAllData();
    } catch (error) { alert('Failed to add stock.'); }
  };

  return (
    <div className="min-h-screen mesh-bg">
      <NavigationBar />
      <Header title="Trading Analysis Dashboard" subtitle="Manage your watchlists and monitor AI-driven trading signals in real time." />
      
      <CommandPalette allStocks={allStocksFlat} />

      <div className="max-w-7xl mx-auto px-4 pb-20">
        <Breadcrumbs items={[{ label: 'Dashboard', path: null }]} />

        {/* Top Actions & Summary Row */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-8 mt-4">
          <div className="flex flex-wrap gap-3">
            <button
              onClick={() => setShowAddModal(true)}
              className="px-5 py-2.5 bg-gradient-to-r from-primary-600 to-primary-700 hover:from-primary-700 hover:to-primary-800 text-white font-semibold rounded-xl shadow-md transition-all flex items-center gap-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>
              Add Stock
            </button>
            <button
              onClick={loadAllData}
              disabled={loading}
              className="px-5 py-2.5 bg-white border border-slate-200 text-slate-700 font-semibold rounded-xl shadow-sm hover:bg-slate-50 transition-all flex items-center gap-2"
            >
              <svg className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
              Refresh Data
            </button>
          </div>
        </div>

        {/* Global Signal Heat Map */}
        {!loading && Object.keys(watchlistData).length > 0 && (
          <SignalHeatMap data={globalStats} />
        )}

        {/* Analysis Progress */}
        {analyzing && (
          <div className="mb-8 glass-card p-6 border-accent-200 animate-slide-up">
            <div className="flex justify-between items-center mb-3">
              <div>
                <h3 className="font-bold text-slate-800 flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-accent-500 animate-pulse"></div>
                  AI Analysis in Progress
                </h3>
                <p className="text-sm text-slate-500 mt-1">
                  Processing data with advanced models... {analysisStatus.completed || 0}/{analysisStatus.total || 0}
                </p>
              </div>
              <button onClick={handleCancelAnalysis} className="px-4 py-2 bg-slate-100 hover:bg-danger-50 text-slate-600 hover:text-danger-600 font-semibold rounded-lg transition-colors text-sm">
                Cancel Halt
              </button>
            </div>
            <div className="w-full bg-slate-100 rounded-full h-3 overflow-hidden shadow-inner">
              <div 
                className="bg-gradient-to-r from-accent-400 to-primary-500 h-full transition-all duration-500 rounded-full shadow-glow-primary relative overflow-hidden"
                style={{ width: `${analysisProgress}%` }}
              >
                <div className="absolute inset-0 bg-white/20 animate-shimmer" style={{ backgroundSize: '200% 100%' }}></div>
              </div>
            </div>
          </div>
        )}

        {/* Watchlists */}
        {loading && Object.keys(watchlistData).length === 0 ? (
          <div className="flex flex-col items-center justify-center py-32">
            <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary-100 border-t-primary-600 mb-6 shadow-glow-primary"></div>
            <p className="text-slate-500 font-medium">Synchronizing with Market Data...</p>
          </div>
        ) : collections.length === 0 ? (
          <div className="text-center py-24 glass-card">
            <div className="w-20 h-20 bg-primary-50 rounded-full flex items-center justify-center mx-auto mb-6">
              <svg className="w-10 h-10 text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 002-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" /></svg>
            </div>
            <h3 className="text-xl font-bold text-slate-800 mb-2">Portfolio Empty</h3>
            <p className="text-slate-500 mb-8 max-w-sm mx-auto">Create your first watchlist and let our AI models discover trading opportunities.</p>
            <button onClick={() => setShowAddModal(true)} className="px-6 py-3 bg-slate-900 text-white font-bold rounded-xl shadow-lg hover:bg-slate-800 transition-colors">
              Add Your First Stock
            </button>
          </div>
        ) : (
          <div className="space-y-6">
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

      {showAddModal && <AddStockModal onClose={() => setShowAddModal(false)} onAdd={handleAddStock} existingSymbols={allStocksFlat.map(s => s.ticker)} />}
      {showConfigModal && <AnalysisConfigModal onClose={() => setShowConfigModal(false)} onConfirm={handleAnalyzeWithConfig} stockCount={selectedStocks.length} stockNames={selectedStocks} title="Deep Dive Analysis Configuration" />}
      {showPasswordModal && <PasswordModal onClose={() => setShowPasswordModal(false)} onSuccess={handlePasswordSuccess} />}
    </div>
  );
}

export default Dashboard;
