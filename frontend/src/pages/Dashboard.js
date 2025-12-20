import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { addToWatchlist, analyzeStocks, cancelJob, getJobStatus, removeFromWatchlist } from '../api/api';
import AddStockModal from '../components/AddStockModal';
import AnalysisConfigModal from '../components/AnalysisConfigModal';
import Header from '../components/Header';
import NavigationBar from '../components/NavigationBar';
import { useStocks } from '../context/StocksContext';
import { TradingViewLink } from '../utils/tradingViewUtils';

function Dashboard() {
  // Use global stocks context for watchlist caching
  const { 
    watchlist: cachedWatchlist, 
    watchlistLoading, 
    fetchWatchlistData,
    addToWatchlistCache,
    removeFromWatchlistCache,
    getTimeSinceLastFetch,
    lastWatchlistFetch
  } = useStocks();

  const [selectedStocks, setSelectedStocks] = useState([]);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState(0);
  const [jobId, setJobId] = useState(null);
  const [analysisStatus, setAnalysisStatus] = useState({});
  const navigate = useNavigate();

  // Use cached watchlist
  const watchlist = cachedWatchlist;
  const loading = watchlistLoading;

  useEffect(() => {
    // Load watchlist from cache or fetch if needed (respects TTL)
    loadWatchlist();
    
    // Check for active job in sessionStorage
    const savedJobId = sessionStorage.getItem('activeJobId');
    if (savedJobId) {
      setJobId(savedJobId);
      setAnalyzing(true);
      pollJobStatus(savedJobId);
    }
  }, []);

  const loadWatchlist = async (forceRefresh = false) => {
    // Use context's fetch function - it handles caching automatically
    await fetchWatchlistData(forceRefresh);
  };

  const handleAddStock = async (symbol, name) => {
    try {
      const result = await addToWatchlist(symbol, name);
      setShowAddModal(false);
      // Update cache immediately with the new stock
      addToWatchlistCache({
        ticker: symbol,
        name: name,
        verdict: 'No analysis available',
        confidence: 0,
        has_analysis: false
      });
    } catch (error) {
      console.error('Failed to add stock:', error);
      alert('Failed to add stock. Please try again.');
    }
  };

  const handleRemoveStock = async (symbol) => {
    if (window.confirm(`Remove ${symbol} from watchlist?`)) {
      try {
        // symbol here is the ticker (full yahoo symbol)
        await removeFromWatchlist(symbol);
        // Update cache immediately
        removeFromWatchlistCache(symbol);
      } catch (error) {
        console.error('Failed to remove stock:', error);
      }
    }
  };

  const handleSelectStock = (symbol) => {
    setSelectedStocks((prev) =>
      prev.includes(symbol)
        ? prev.filter((s) => s !== symbol)
        : [...prev, symbol]
    );
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
            // Force refresh watchlist to get new analysis results
            await loadWatchlist(true);
            alert(`Analysis completed! ${status.successful || status.completed}/${status.total} stocks analyzed successfully.`);
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
    }, 2000); // Poll every 2 seconds
  };

  const handleAnalyzeSelected = async () => {
    if (selectedStocks.length === 0) {
      alert('Please select at least one stock to analyze');
      return;
    }
    // Open config modal instead of directly analyzing
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
      
      // Save to sessionStorage for persistence
      sessionStorage.setItem('activeJobId', newJobId);

      // Start polling
      pollJobStatus(newJobId);
    } catch (error) {
      setAnalyzing(false);
      console.error('Failed to analyze stocks:', error);
      alert('Analysis failed. Please try again.');
    }
  };

  const handleCancelAnalysis = async () => {
    if (!jobId) return;

    if (window.confirm('Cancel the running analysis?')) {
      try {
        await cancelJob(jobId);
        setAnalyzing(false);
        sessionStorage.removeItem('activeJobId');
        alert('Analysis cancelled');
      } catch (error) {
        console.error('Failed to cancel:', error);
      }
    }
  };

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
        return 'text-gray-600';
      default:
        return 'text-gray-400';
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <NavigationBar />
      <Header title="Trading Analysis Dashboard" />

      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Action Buttons */}
        <div className="flex gap-4 mb-6">
          <button
            onClick={() => setShowAddModal(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            + Add Stock
          </button>
          <button
            onClick={handleAnalyzeSelected}
            disabled={selectedStocks.length === 0 || analyzing}
            className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:bg-gray-400"
          >
            {analyzing ? 'Analyzing...' : 'Analyze Selected Stocks'}
          </button>
          <button
            onClick={() => loadWatchlist(true)}
            className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
          >
            {loading ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>

        {/* Last Synced Indicator */}
        {lastWatchlistFetch && !loading && (
          <div className="mb-2 text-xs text-gray-500 text-right">
            Last synced: {getTimeSinceLastFetch(lastWatchlistFetch)}
          </div>
        )}

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
                {analysisStatus.successful !== undefined && analysisStatus.completed > 0 && (
                  <span className="ml-2 text-green-600">
                    [OK] {analysisStatus.successful} successful
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
            {analysisStatus.errors && analysisStatus.errors.length > 0 && (
              <div className="mt-2 text-xs text-red-600">
                {analysisStatus.errors.length} error(s) occurred
              </div>
            )}
          </div>
        )}

        {/* Watchlist Table */}
        <div className="bg-white rounded shadow overflow-hidden">
          <table className="min-w-full">
            <thead className="bg-gray-200">
              <tr>
                <th className="px-4 py-3 text-left">
                  <input
                    type="checkbox"
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedStocks(watchlist.map((s) => s.ticker));
                      } else {
                        setSelectedStocks([]);
                      }
                    }}
                  />
                </th>
                <th className="px-4 py-3 text-left">Symbol</th>
                <th className="px-4 py-3 text-left">Name</th>
                <th className="px-4 py-3 text-left">Verdict</th>
                <th className="px-4 py-3 text-left">Confidence</th>
                <th className="px-4 py-3 text-left">Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="6" className="text-center py-8 text-gray-500">
                    Loading...
                  </td>
                </tr>
              ) : watchlist.length === 0 ? (
                <tr>
                  <td colSpan="6" className="text-center py-8 text-gray-500">
                    No stocks in watchlist. Click "Add Stock" to get started.
                  </td>
                </tr>
              ) : (
                watchlist.map((stock) => (
                  <tr key={stock.ticker} className="border-t hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <input
                        type="checkbox"
                        checked={selectedStocks.includes(stock.ticker)}
                        onChange={() => handleSelectStock(stock.ticker)}
                      />
                    </td>
                    <td className="px-4 py-3 font-mono">
                      <TradingViewLink 
                        ticker={stock.ticker}
                        className="text-gray-900"
                      />
                    </td>
                    <td className="px-4 py-3">{stock.name || '-'}</td>
                    <td className={`px-4 py-3 ${getVerdictColor(stock.verdict)}`}>
                      {stock.verdict}
                      {!stock.has_analysis && (
                        <span className="text-xs text-gray-400 block">(Not analyzed yet)</span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      {stock.confidence ? `${(stock.confidence * 100).toFixed(0)}%` : '-'}
                    </td>
                    <td className="px-4 py-3">
                      {stock.has_analysis ? (
                        <button
                          onClick={() => navigate(`/results/${stock.ticker}`)}
                          className="text-blue-600 hover:underline mr-3"
                        >
                          View
                        </button>
                      ) : (
                        <span className="text-gray-400 mr-3">No analysis</span>
                      )}
                      <button
                        onClick={() => handleRemoveStock(stock.ticker)}
                        className="text-red-600 hover:underline"
                      >
                        Remove
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {showAddModal && (
        <AddStockModal
          onClose={() => setShowAddModal(false)}
          onAdd={handleAddStock}
          existingSymbols={watchlist.map(stock => stock.ticker)}
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
