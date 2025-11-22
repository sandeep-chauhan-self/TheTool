import axios from 'axios';

// Use environment variable for API base URL
// Production: https://thetool-production.up.railway.app
// Development: http://localhost:5000
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL;

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': process.env.REACT_APP_API_KEY
  },
});

export const analyzeStocks = async (tickers, indicators = null) => {
  const response = await api.post('/analyze', { tickers, indicators });
  return response.data;
};

export const getJobStatus = async (jobId) => {
  const response = await api.get(`/status/${jobId}`);
  return response.data;
};

export const getReport = async (ticker) => {
  const response = await api.get(`/report/${ticker}`);
  return response.data;
};

export const downloadReport = async (ticker) => {
  const response = await api.get(`/report/${ticker}/download`, {
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
  const response = await api.get('/nse');
  return response.data;
};

export const getNSEStocks = async () => {
  const response = await api.get('/nse-stocks');
  return response.data;
};

export const getConfig = async () => {
  const response = await api.get('/config');
  return response.data;
};

export const getWatchlist = async () => {
  const response = await api.get('/watchlist');
  return response.data;
};

export const addToWatchlist = async (symbol, name = '') => {
  const response = await api.post('/watchlist', { symbol, name });
  return response.data;
};

export const removeFromWatchlist = async (symbol) => {
  const response = await api.delete('/watchlist', { data: { symbol } });
  return response.data;
};

export const getHealth = async () => {
  const response = await api.get('/health');
  return response.data;
};

// All Stocks Analysis APIs
export const initializeAllStocks = async () => {
  const response = await api.post('/initialize-all-stocks');
  return response.data;
};

export const getAllStocks = async () => {
  const response = await api.get('/all-stocks');
  return response.data;
};

export const getStockHistory = async (symbol) => {
  const response = await api.get(`/all-stocks/${symbol}/history`);
  return response.data;
};

export const analyzeAllStocks = async (symbols = []) => {
  const response = await api.post('/analyze-all-stocks', { symbols });
  return response.data;
};

export const getAllStocksProgress = async () => {
  const response = await api.get('/all-stocks/progress');
  return response.data;
};

export const cancelJob = async (jobId) => {
  const response = await api.post(`/cancel-job/${jobId}`);
  return response.data;
};

export default api;
