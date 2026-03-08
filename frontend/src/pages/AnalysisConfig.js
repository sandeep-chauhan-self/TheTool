import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { analyzeStocks, getConfig, getJobStatus, getWatchlist } from '../api/api';
import Breadcrumbs from '../components/Breadcrumbs';
import PasswordModal from '../components/PasswordModal';
import Header from '../components/Header';
import NavigationBar from '../components/NavigationBar';

function AnalysisConfig() {
  const [stocks, setStocks] = useState([]);
  const [selectedStock, setSelectedStock] = useState('all');
  const [indicators, setIndicators] = useState({
    'RSI': true,
    'MACD': true,
    'ADX': true,
    'Parabolic SAR': true,
    'EMA Crossover': true,
    'Stochastic': true,
    'CCI': true,
    'Williams %R': true,
    'ATR': true,
    'Bollinger Bands': true,
    'OBV': true,
    'Chaikin Money Flow': true,
  });
  const [config, setConfig] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [passwordVerified, setPasswordVerified] = useState(() => sessionStorage.getItem('bulkAnalysisVerified') === 'true');
  const navigate = useNavigate();

  useEffect(() => {
    loadStocks();
    loadConfig();
  }, []);

  const loadStocks = async () => {
    try {
      const data = await getWatchlist();
      setStocks(data);
    } catch (error) {
      console.error('Failed to load stocks:', error);
    }
  };

  const loadConfig = async () => {
    try {
      const data = await getConfig();
      setConfig(data);
    } catch (error) {
      console.error('Failed to load config:', error);
    }
  };

  const handleIndicatorToggle = (indicator) => {
    setIndicators((prev) => ({
      ...prev,
      [indicator]: !prev[indicator],
    }));
  };

  const handleAnalyze = async () => {
    const tickersToAnalyze =
      selectedStock === 'all'
        ? stocks.map((s) => s.symbol)
        : [selectedStock];

    if (tickersToAnalyze.length === 0) {
      alert('No stocks to analyze');
      return;
    }

    if (selectedStock === 'all' && !passwordVerified) {
      setShowPasswordModal(true);
      return;
    }

    const enabledIndicators = Object.keys(indicators).filter((k) => indicators[k]);

    try {
      setAnalyzing(true);
      setProgress(0);

      const result = await analyzeStocks(tickersToAnalyze, enabledIndicators);
      const jobId = result.job_id;

      const interval = setInterval(async () => {
        try {
          const status = await getJobStatus(jobId);
          setProgress(status.progress);

          if (status.status === 'completed') {
            clearInterval(interval);
            setAnalyzing(false);
            
            if (selectedStock !== 'all') {
              navigate(`/results/${selectedStock}`);
            } else {
              navigate('/');
            }
          }
        } catch (error) {
          clearInterval(interval);
          setAnalyzing(false);
        }
      }, 1000);
    } catch (error) {
      setAnalyzing(false);
      alert('Analysis failed. Please try again.');
    }
  };

  const getCategoryBias = (indicator) => {
    if (!config) return '1.0';
    const categories = {
      'RSI': 'momentum', 'MACD': 'trend', 'ADX': 'trend', 'Parabolic SAR': 'trend',
      'EMA Crossover': 'trend', 'Stochastic': 'momentum', 'CCI': 'momentum', 'Williams %R': 'momentum',
      'ATR': 'volatility', 'Bollinger Bands': 'volatility', 'OBV': 'volume', 'Chaikin Money Flow': 'volume',
    };
    return config.type_bias[categories[indicator] || 'momentum'].toFixed(1);
  };

  return (
    <div className="min-h-screen mesh-bg">
      <NavigationBar />
      <Header title="Deep Dive Analysis Config" subtitle="Fine-tune your technical indicator models before running batch backtests or scans." />

      <div className="max-w-4xl mx-auto px-4 py-8 pb-20">
        <Breadcrumbs items={[{ label: 'Dashboard', path: '/' }, { label: 'Analysis Config', path: null }]} />

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-6">
          <div className="md:col-span-2 space-y-8">
             {/* Indicator Toggle Board */}
             <div className="glass-card p-8 animate-slide-up">
               <h2 className="text-xl font-bold text-slate-900 mb-6 flex items-center gap-2">
                 <svg className="w-5 h-5 text-accent-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" /></svg>
                 Indicator Weights & Selection
               </h2>

               <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                 {Object.keys(indicators).map((indicator) => (
                   <label key={indicator} className={`flex items-start p-4 rounded-xl border border-slate-200 cursor-pointer transition-all ${indicators[indicator] ? 'bg-primary-50/50 border-primary-200 shadow-inner' : 'bg-white hover:bg-slate-50'}`}>
                      <div className="flex h-6 items-center">
                        <input
                          type="checkbox"
                          checked={indicators[indicator]}
                          onChange={() => handleIndicatorToggle(indicator)}
                          disabled={analyzing}
                          className="h-5 w-5 rounded border-slate-300 text-primary-600 focus:ring-primary-600"
                        />
                      </div>
                      <div className="ml-3 text-sm">
                        <span className={`font-bold block ${indicators[indicator] ? 'text-primary-900' : 'text-slate-700'}`}>{indicator}</span>
                        <span className="text-slate-500 text-xs mt-0.5 block tracking-wide">
                          Model Weight: {getCategoryBias(indicator)}x
                        </span>
                      </div>
                   </label>
                 ))}
               </div>
             </div>
          </div>

          <div className="space-y-8">
            {/* Target Select */}
            <div className="glass-card p-6 animate-slide-up shadow-glow-primary">
              <h2 className="text-lg font-bold text-slate-900 mb-4 tracking-tight">Select Target</h2>
              <select
                value={selectedStock}
                onChange={(e) => setSelectedStock(e.target.value)}
                className="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl mb-6 font-semibold text-slate-800 shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 appearance-none bg-[url('data:image/svg+xml;charset=US-ASCII,%3Csvg%20width%3D%2224%22%20height%3D%2224%22%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%3E%3Cpath%20d%3D%22M7%2010l5%205%205-5z%22%20fill%3D%22%239CA3AF%22%2F%3E%3C%2Fsvg%3E')] bg-no-repeat bg-[position:calc(100%-1rem)_center]"
                disabled={analyzing}
              >
                <option value="all">Analyze ENTIRE Watchlist ({stocks.length})</option>
                {stocks.map((stock) => (
                  <option key={stock.symbol} value={stock.symbol}>
                    {stock.symbol} - {stock.name || 'Unknown'}
                  </option>
                ))}
              </select>

              <button
                onClick={handleAnalyze}
                disabled={analyzing}
                className={`w-full py-4 text-center rounded-xl font-bold text-white shadow-lg transition-all transform flex items-center justify-center gap-2 ${analyzing ? 'bg-slate-300 shadow-none' : 'bg-gradient-to-br from-primary-600 to-accent-600 hover:from-primary-700 hover:to-accent-700 hover:-translate-y-0.5 shadow-glow-primary'}`}
              >
                {analyzing ? (
                  <><svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg> Analyzing...</>
                ) : (
                  <>Run Engine Now <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" /></svg></>
                )}
              </button>

              {analyzing && (
                <div className="mt-6">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-xs font-bold text-primary-700 uppercase tracking-widest">Job Progress</span>
                    <span className="text-sm font-semibold text-slate-700">{progress}%</span>
                  </div>
                  <div className="w-full bg-slate-100 rounded-full h-3 overflow-hidden shadow-inner">
                    <div className="bg-gradient-to-r from-accent-400 to-primary-500 h-full transition-all duration-300 rounded-full relative overflow-hidden" style={{ width: `${progress}%` }}>
                       <div className="absolute inset-0 bg-white/20 animate-shimmer" style={{ backgroundSize: '200% 100%' }}></div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {showPasswordModal && (
        <PasswordModal
          onClose={() => setShowPasswordModal(false)}
          onSuccess={() => { setPasswordVerified(true); setShowPasswordModal(false); handleAnalyze(); }}
        />
      )}
    </div>
  );
}

export default AnalysisConfig;
