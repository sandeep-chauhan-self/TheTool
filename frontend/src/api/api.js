import axios from 'axios';

/**
 * API Base URL Selection Strategy:
 * 
 * Priority Order:
 * 1. REACT_APP_API_BASE_URL - Explicit environment variable (production/staging builds)
 * 2. REACT_APP_ENV - Switch between development/production backends
 *    - "development" -> https://thetool-development.up.railway.app (debug Railway)
 *    - "production" -> https://thetool-production.up.railway.app (live Railway)
 * 3. localhost:5000 - Local development fallback
 * 
 * Environment Variables:
 * - REACT_APP_ENV: "development" | "production" | "local"
 * - REACT_APP_API_BASE_URL: Full backend URL override
 * - REACT_APP_DEBUG: "true" | "false" - Enable verbose logging
 */

const getApiBaseUrl = () => {
  // Development Railway backend override
  if (process.env.REACT_APP_DEV_API_BASE_URL) {
    return process.env.REACT_APP_DEV_API_BASE_URL;
  }

  // Production Railway backend override
  if (process.env.REACT_APP_API_BASE_URL) {
    return process.env.REACT_APP_API_BASE_URL;
  }

  // Check current hostname to auto-detect environment
  const hostname = typeof window !== 'undefined' ? window.location.hostname : '';
  let env = (process.env.REACT_APP_ENV || 'production').toLowerCase();
  
  // Auto-detect from Vercel preview URL
  if (hostname.includes('the-tool-git-development')) {
    env = 'development';
  } else if (hostname.includes('the-tool-theta') || hostname.includes('vercel.app')) {
    // Keep from REACT_APP_ENV if available, otherwise default to production
    env = process.env.REACT_APP_ENV ? env : 'production';
  }

  const backendUrls = {
    development: 'https://thetool-development.up.railway.app',
    production: 'https://thetool-production.up.railway.app',
    local: 'http://localhost:5000',
  };

  const url = backendUrls[env] || backendUrls.production;
  
  // Log environment info in development
  if (process.env.REACT_APP_DEBUG === 'true') {
    console.log(`[API] Hostname: ${hostname}, Environment: ${env}, Backend: ${url}`);
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
