import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getWatchlist, analyzeStocks, getJobStatus, getConfig } from '../api/api';
import Header from '../components/Header';

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
              alert('Analysis completed!');
              navigate('/');
            }
          }
        } catch (error) {
          clearInterval(interval);
          setAnalyzing(false);
          console.error('Failed to get status:', error);
        }
      }, 1000);
    } catch (error) {
      setAnalyzing(false);
      console.error('Analysis failed:', error);
      alert('Analysis failed. Please try again.');
    }
  };

  const getCategoryBias = (indicator) => {
    if (!config) return '1.0';
    
    const categories = {
      'RSI': 'momentum',
      'MACD': 'trend',
      'ADX': 'trend',
      'Parabolic SAR': 'trend',
      'EMA Crossover': 'trend',
      'Stochastic': 'momentum',
      'CCI': 'momentum',
      'Williams %R': 'momentum',
      'ATR': 'volatility',
      'Bollinger Bands': 'volatility',
      'OBV': 'volume',
      'Chaikin Money Flow': 'volume',
    };
    
    const category = categories[indicator] || 'momentum';
    return config.type_bias[category].toFixed(1);
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <Header title="Analysis Configuration" />

      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="bg-white rounded shadow p-6 mb-6">
          <h2 className="text-xl font-bold mb-4">Select Stock</h2>
          
          <select
            value={selectedStock}
            onChange={(e) => setSelectedStock(e.target.value)}
            className="w-full p-2 border rounded mb-4"
            disabled={analyzing}
          >
            <option value="all">All Stocks</option>
            {stocks.map((stock) => (
              <option key={stock.symbol} value={stock.symbol}>
                {stock.symbol} - {stock.name}
              </option>
            ))}
          </select>

          <button
            onClick={() => navigate('/')}
            className="text-blue-600 hover:underline"
          >
            &lt; Back to Dashboard
          </button>
        </div>

        <div className="bg-white rounded shadow p-6 mb-6">
          <h2 className="text-xl font-bold mb-4">Indicators Configuration</h2>

          <div className="space-y-3">
            {Object.keys(indicators).map((indicator) => (
              <div key={indicator} className="flex items-center justify-between py-2 border-b">
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    checked={indicators[indicator]}
                    onChange={() => handleIndicatorToggle(indicator)}
                    disabled={analyzing}
                    className="mr-3"
                  />
                  <span className="font-medium">{indicator}</span>
                </div>
                <span className="text-gray-600">
                  Confidence Weight: {getCategoryBias(indicator)}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded shadow p-6">
          <button
            onClick={handleAnalyze}
            disabled={analyzing}
            className="w-full py-3 bg-green-600 text-white rounded font-bold hover:bg-green-700 disabled:bg-gray-400"
          >
            {analyzing ? 'Analyzing...' : 'Analyze Now >'}
          </button>

          {analyzing && (
            <div className="mt-4">
              <div className="text-sm text-gray-600 mb-2">
                Progress: {progress}%
              </div>
              <div className="w-full bg-gray-200 rounded-full h-6">
                <div
                  className="bg-green-600 h-6 rounded-full transition-all flex items-center justify-center text-white text-xs"
                  style={{ width: `${progress}%` }}
                >
                  {progress > 10 && `${progress}%`}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default AnalysisConfig;
