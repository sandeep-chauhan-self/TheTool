import axios from 'axios';

/**
 * API Base URL Selection Strategy:
 * 
 * Auto-detection based on frontend hostname:
 * - localhost / 127.0.0.1 / 192.168.x.x -> Local backend (http://localhost:5000)
 * - the-tool-git-development*.vercel.app -> Development Railway backend
 * - the-tool-theta.vercel.app -> Production Railway backend
 * 
 * Override with environment variables:
 * - REACT_APP_API_BASE_URL: Full backend URL override (highest priority)
 * - REACT_APP_DEBUG: "true" | "false" - Enable verbose logging
 */

const getApiBaseUrl = () => {
  // Explicit override takes highest priority
  if (process.env.REACT_APP_API_BASE_URL) {
    return process.env.REACT_APP_API_BASE_URL;
  }

  // Auto-detect environment from frontend hostname
  const hostname = typeof window !== 'undefined' ? window.location.hostname : '';
  
  let env = 'development'; // Default to development (safer than production)
  
  // Check if running locally (localhost, 127.0.0.1, or local network IP)
  const isLocal = hostname === 'localhost' || 
                  hostname === '127.0.0.1' || 
                  hostname.startsWith('192.168.') ||
                  hostname.startsWith('10.') ||
                  hostname === '';
  
  if (isLocal) {
    env = 'local';
  } else if (hostname === 'the-tool-theta.vercel.app') {
    // Exact match for production frontend
    env = 'production';
  } else {
    // Everything else (including all Vercel preview/branch deployments) -> development
    env = 'development';
  }

  const backendUrls = {
    local: 'http://localhost:5000',
    development: 'https://thetool-development.up.railway.app',
    production: 'https://thetool-production.up.railway.app',
  };

  const url = backendUrls[env];
  
  // Always log for debugging CORS issues - LOUD LOGGING
  console.warn(`%c[API ROUTING] Frontend hostname: "${hostname}" → Detected env: "${env}" → Using backend: "${url}"`, 'background: #ff9900; color: #000; font-weight: bold; padding: 5px;');
  
  if (process.env.REACT_APP_DEBUG === 'true') {
    console.log(`[API DEBUG]`, {
      hostname,
      env,
      url,
      REACT_APP_API_BASE_URL: process.env.REACT_APP_API_BASE_URL,
      REACT_APP_DEBUG: process.env.REACT_APP_DEBUG
    });
  }
  
  return url;
};

const API_BASE_URL = getApiBaseUrl();

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': process.env.REACT_APP_API_KEY
  },
});

export const analyzeStocks = async (tickers, config = {}) => {
  // Support both old signature (tickers, indicators, capital) and new (tickers, config)
  const analysisConfig = typeof config === 'number' 
    ? { capital: config } // Legacy: third param was capital
    : config;
  
  const payload = {
    tickers,
    capital: analysisConfig.capital || 100000,
    strategy_id: analysisConfig.strategyId || 1,  // Default to Strategy 1 (Balanced)
    risk_percent: analysisConfig.riskPercent,
    position_size_limit: analysisConfig.positionSizeLimit,
    risk_reward_ratio: analysisConfig.riskRewardRatio,
    data_period: analysisConfig.dataPeriod,
    use_demo_data: analysisConfig.useDemoData,
    category_weights: analysisConfig.categoryWeights,
    enabled_indicators: analysisConfig.enabledIndicators,
    indicators: analysisConfig.indicators // Legacy support
  };
  
  const response = await api.post('/api/analysis/analyze', payload);
  return response.data;
};

export const getJobStatus = async (jobId) => {
  const response = await api.get(`/api/analysis/status/${jobId}`);
  return response.data;
};

export const getReport = async (ticker) => {
  const response = await api.get(`/api/analysis/report/${ticker}`);
  return response.data;
};

export const downloadReport = async (ticker) => {
  const response = await api.get(`/api/analysis/report/${ticker}/download`, {
    responseType: 'blob',
  });
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `${ticker}_analysis.xlsx`);
  document.body.appendChild(link);
  link.click();
  link.remove();
};

export const getNSEList = async () => {
  const response = await api.get('/api/stocks/nse');
  return response.data;
};

export const getAllNSEStocks = async (page = 1, per_page = 50) => {
  const response = await api.get(`/api/stocks/all?page=${page}&per_page=${per_page}`);
  return response.data;
};

export const getNSEStocks = async () => {
  const response = await api.get('/api/stocks/nse-stocks');
  return response.data;
};

export const getConfig = async () => {
  const response = await api.get('/config');
  return response.data;
};

export const getWatchlist = async () => {
  const response = await api.get('/api/watchlist');
  // The backend returns { count, watchlist }, but we only need the watchlist array
  return response.data.watchlist || [];
};

export const addToWatchlist = async (symbol, name = '') => {
  // Backend RequestValidator.WatchlistAddRequest expects: symbol, name (optional)
  // The backend converts symbol to ticker format (adds .NS if no exchange code)
  // Frontend passes: symbol (ticker or short symbol), name (company name)
  const response = await api.post('/api/watchlist', { 
    symbol: symbol,      // Can be "RELIANCE" or "RELIANCE.NS"
    name: name           // Company name (optional)
  });
  return response.data;
};

export const removeFromWatchlist = async (symbol) => {
  // symbol here contains the full ticker (e.g., "ACEINTEG.NS")
  const response = await api.delete('/api/watchlist', { data: { ticker: symbol } });
  return response.data;
};

export const getHealth = async () => {
  const response = await api.get('/health');
  return response.data;
};

export const getAllStocks = async () => {
  const response = await api.get('/api/stocks/all-stocks');
  return response.data;
};

export const getStockHistory = async (symbol) => {
  const response = await api.get(`/api/analysis/history/${symbol}`);
  return response.data;
};

export const analyzeAllStocks = async (symbols = [], config = {}) => {
  const payload = {
    symbols,
    capital: config.capital || 100000,
    risk_percent: config.riskPercent,
    position_size_limit: config.positionSizeLimit,
    risk_reward_ratio: config.riskRewardRatio,
    data_period: config.dataPeriod,
    use_demo_data: config.useDemoData,
    category_weights: config.categoryWeights,
    enabled_indicators: config.enabledIndicators
  };
  
  const response = await api.post('/api/stocks/analyze-all-stocks', payload);
  return response.data;
};

export const getAllStocksProgress = async () => {
  const response = await api.get('/api/stocks/all-stocks/progress');
  return response.data;
};

export const getAllAnalysisResults = async (page = 1, per_page = 100) => {
  const response = await api.get(`/api/stocks/all-stocks/results?page=${page}&per_page=${per_page}`);
  return response.data;
};

export const cancelJob = async (jobId) => {
  const response = await api.post(`/api/analysis/cancel/${jobId}`);
  return response.data;
};

// Strategy API functions
export const getStrategies = async () => {
  const response = await api.get('/api/strategies');
  return response.data;
};

export const getStrategy = async (strategyId) => {
  const response = await api.get(`/api/strategies/${strategyId}`);
  return response.data;
};

export const getStrategyHelp = async (strategyId) => {
  const response = await api.get(`/api/strategies/${strategyId}/help`);
  return response.data;
};

export const getStrategyWeights = async (strategyId) => {
  const response = await api.get(`/api/strategies/${strategyId}/weights`);
  return response.data;
};

export default api;
