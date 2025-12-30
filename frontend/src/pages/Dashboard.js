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
import AnalysisConfigModal from '../components/AnalysisConfigModal';
import Breadcrumbs from '../components/Breadcrumbs';
import Header from '../components/Header';
import NavigationBar from '../components/NavigationBar';
import { TradingViewLink } from '../utils/tradingViewUtils';

// Verdict color helper
const getVerdictColor = (verdict) => {
  switch (verdict) {
    case 'Strong Buy':
      return 'text-green-700 font-bold';
    case 'Buy':
      return 'text-green-600';
    case 'Strong Sell':
      return 'text-red-700 font-bold';
    case 'Sell':
      return 'text-red-600';
    case 'Neutral':
    case 'Hold':
      return 'text-yellow-600';
    default:
      return 'text-gray-400';
  }
};

// Stock row component for the watchlist cards
const StockRow = ({ stock, isSelected, onSelect, onView, onRemove }) => {
  return (
    <tr className="border-t hover:bg-gray-50">
      <td className="px-4 py-3">
        <input
          type="checkbox"
          checked={isSelected}
          onChange={() => onSelect(stock.ticker)}
          className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
        />
      </td>
      <td className="px-4 py-3 font-mono">
        <TradingViewLink 
          ticker={stock.ticker}
          className="text-gray-900 hover:text-blue-600"
        />
      </td>
      <td className="px-4 py-3 text-gray-600 text-sm">{stock.name || '-'}</td>
      <td className={`px-4 py-3 ${getVerdictColor(stock.verdict)}`}>
        {stock.verdict}
        {!stock.has_analysis && (
          <span className="text-xs text-gray-400 block">(Not analyzed)</span>
        )}
      </td>
      <td className="px-4 py-3 text-gray-600">
        {stock.confidence ? `${(stock.confidence * 100).toFixed(0)}%` : '-'}
      </td>
      <td className="px-4 py-3">
        {stock.has_analysis ? (
          <button
            onClick={() => onView(stock.ticker)}
            className="text-blue-600 hover:underline mr-3"
          >
            View
          </button>
        ) : (
          <span className="text-gray-400 mr-3">-</span>
        )}
        <button
          onClick={() => onRemove(stock.ticker)}
          className="text-red-600 hover:underline"
        >
          Remove
        </button>
      </td>
    </tr>
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

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden border border-gray-200">
      {/* Card Header */}
      <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="p-1 rounded hover:bg-gray-200 transition-colors"
            >
              <svg 
                className={`w-5 h-5 text-gray-500 transition-transform duration-200 ${isExpanded ? 'rotate-0' : '-rotate-90'}`} 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            <div>
              <h3 className="text-lg font-semibold text-gray-800">{collection.name}</h3>
              <p className="text-sm text-gray-500">{stocks.length} stocks • {stats.analyzed} analyzed</p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            {/* Signal Pills */}
            {stats.buySignals > 0 && (
              <span className="px-2 py-1 rounded bg-green-100 text-green-700 text-xs font-medium">
                {stats.buySignals} Buy
              </span>
            )}
            {stats.sellSignals > 0 && (
              <span className="px-2 py-1 rounded bg-red-100 text-red-700 text-xs font-medium">
                {stats.sellSignals} Sell
              </span>
            )}
            {stats.holdSignals > 0 && (
              <span className="px-2 py-1 rounded bg-yellow-100 text-yellow-700 text-xs font-medium">
                {stats.holdSignals} Hold
              </span>
            )}
            
            {/* Delete Collection (only for non-default) */}
            {collection.id !== null && (
              <button
                onClick={() => onDeleteCollection(collection.id, collection.name)}
                className="p-1.5 rounded hover:bg-red-100 text-gray-400 hover:text-red-600 transition-colors"
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
          <div className="flex items-center gap-3 mt-3 pt-3 border-t border-gray-200">
            <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer hover:text-gray-800 transition-colors">
              <input
                type="checkbox"
                checked={allSelected}
                onChange={(e) => onSelectAll(collection.id, stocks, e.target.checked)}
                className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              Select All
            </label>
            {selectedInCollection > 0 && (
              <button
                onClick={() => onAnalyze(stocks.filter(s => selectedStocks.includes(s.ticker)).map(s => s.ticker))}
                className="px-3 py-1.5 rounded bg-green-600 hover:bg-green-700 text-white text-sm font-medium transition-colors"
              >
                Analyze {selectedInCollection} Selected
              </button>
            )}
          </div>
        )}
      </div>
      
      {/* Stock List */}
      {isExpanded && (
        <div className="max-h-[400px] overflow-y-auto">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-2 border-blue-600 border-t-transparent"></div>
            </div>
          ) : stocks.length === 0 ? (
            <div className="text-center py-12 px-4">
              <p className="text-gray-500 text-sm">No stocks in this watchlist</p>
              <p className="text-gray-400 text-xs mt-1">Add stocks from the All Stocks page</p>
            </div>
          ) : (
            <table className="min-w-full">
              <thead className="bg-gray-100">
                <tr>
                  <th className="px-4 py-2 text-left w-10"></th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Symbol</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Verdict</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Score</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
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
      )}
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
    <div className="min-h-screen bg-gray-100">
      <NavigationBar />
      <Header title="Trading Analysis Dashboard" />

      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Breadcrumbs */}
        <Breadcrumbs 
          items={[
            { label: 'Dashboard', path: null }
          ]} 
        />

        {/* Action Buttons */}
        <div className="flex flex-wrap gap-4 mb-6">
          <button
            onClick={() => setShowAddModal(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            + Add Stock
          </button>
          
          {selectedStocks.length > 0 && (
            <button
              onClick={() => handleAnalyze(selectedStocks)}
              disabled={analyzing}
              className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:bg-gray-400"
            >
              {analyzing ? 'Analyzing...' : `Analyze ${selectedStocks.length} Selected`}
            </button>
          )}
          
          <button
            onClick={loadAllData}
            disabled={loading}
            className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 disabled:bg-gray-400"
          >
            {loading ? 'Loading...' : 'Refresh'}
          </button>
          
          {/* Stats Summary */}
          <div className="flex items-center gap-4 ml-auto text-sm">
            <span className="text-gray-600">
              <strong>{globalStats.totalStocks}</strong> stocks
            </span>
            <span className="text-green-600">
              <strong>{globalStats.buySignals}</strong> buy
            </span>
            <span className="text-red-600">
              <strong>{globalStats.sellSignals}</strong> sell
            </span>
          </div>
        </div>

        {/* Analysis Progress */}
        {analyzing && (
          <div className="mb-6 bg-white p-4 rounded shadow">
            <div className="flex justify-between items-center mb-2">
              <div className="text-sm text-gray-600">
                Analysis Progress: {analysisProgress}% 
                {analysisStatus.completed !== undefined && (
                  <span className="ml-2">
                    ({analysisStatus.completed}/{analysisStatus.total} stocks)
                  </span>
                )}
              </div>
              <button
                onClick={handleCancelAnalysis}
                className="px-3 py-1 bg-red-500 text-white text-sm rounded hover:bg-red-600"
              >
                Cancel
              </button>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-4">
              <div
                className="bg-blue-600 h-4 rounded-full transition-all"
                style={{ width: `${analysisProgress}%` }}
              ></div>
            </div>
          </div>
        )}

        {/* Watchlist Cards Grid */}
        {loading && Object.keys(watchlistData).length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20">
            <div className="animate-spin rounded-full h-12 w-12 border-2 border-blue-600 border-t-transparent mb-4"></div>
            <p className="text-gray-500">Loading your watchlists...</p>
          </div>
        ) : collections.length === 0 ? (
          <div className="text-center py-20 bg-white rounded shadow">
            <p className="text-gray-500 mb-4">No watchlists yet. Add stocks to get started.</p>
            <button
              onClick={() => setShowAddModal(true)}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              + Add Your First Stock
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-12">
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
