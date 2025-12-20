import { createContext, useCallback, useContext, useState } from 'react';
import { getAllAnalysisResults, getAllNSEStocks, getWatchlist as fetchWatchlist, getStockHistory } from '../api/api';

// Cache TTL in milliseconds (5 minutes)
const CACHE_TTL = 5 * 60 * 1000;

const StocksContext = createContext(null);

export function StocksProvider({ children }) {
  // All NSE stocks cache
  const [allStocks, setAllStocks] = useState([]);
  const [allStocksLastFetch, setAllStocksLastFetch] = useState(null);
  const [allStocksLoading, setAllStocksLoading] = useState(false);

  // Analysis results cache (map of symbol -> result)
  const [analysisResults, setAnalysisResults] = useState({});
  const [analysisLastFetch, setAnalysisLastFetch] = useState(null);

  // Watchlist cache
  const [watchlist, setWatchlist] = useState([]);
  const [watchlistLastFetch, setWatchlistLastFetch] = useState(null);
  const [watchlistLoading, setWatchlistLoading] = useState(false);

  /**
   * Check if cache is still valid
   */
  const isCacheValid = (lastFetch) => {
    if (!lastFetch) return false;
    return Date.now() - lastFetch < CACHE_TTL;
  };

  /**
   * Get time since last fetch in human readable format
   */
  const getTimeSinceLastFetch = (lastFetch) => {
    if (!lastFetch) return 'Never';
    const seconds = Math.floor((Date.now() - lastFetch) / 1000);
    if (seconds < 60) return `${seconds}s ago`;
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    return `${hours}h ago`;
  };

  /**
   * Fetch all NSE stocks (with caching)
   */
  const fetchAllStocks = useCallback(async (forceRefresh = false) => {
    // Return cached data if valid and not forcing refresh
    if (!forceRefresh && isCacheValid(allStocksLastFetch) && allStocks.length > 0) {
      console.log('[StocksContext] Using cached stocks data');
      return allStocks;
    }

    console.log('[StocksContext] Fetching all stocks from server...');
    setAllStocksLoading(true);

    try {
      // Fetch first page to get total_pages
      const firstStocksPage = await getAllNSEStocks(1, 500);
      const totalStockPages = firstStocksPage?.total_pages || 1;

      let allLoadedStocks = [...(firstStocksPage?.stocks || [])];

      // Fetch remaining pages in parallel
      if (totalStockPages > 1) {
        const stockPagePromises = [];
        for (let page = 2; page <= totalStockPages; page++) {
          stockPagePromises.push(getAllNSEStocks(page, 500));
        }
        const stockResults = await Promise.all(stockPagePromises);
        stockResults.forEach(data => {
          if (data?.stocks) {
            allLoadedStocks = [...allLoadedStocks, ...data.stocks];
          }
        });
      }

      setAllStocks(allLoadedStocks);
      setAllStocksLastFetch(Date.now());
      console.log(`[StocksContext] Loaded ${allLoadedStocks.length} stocks`);
      return allLoadedStocks;
    } catch (error) {
      console.error('[StocksContext] Failed to fetch stocks:', error);
      throw error;
    } finally {
      setAllStocksLoading(false);
    }
  }, [allStocks, allStocksLastFetch]);

  /**
   * Fetch all analysis results (with caching)
   */
  const fetchAnalysisResults = useCallback(async (forceRefresh = false) => {
    // Return cached data if valid
    if (!forceRefresh && isCacheValid(analysisLastFetch) && Object.keys(analysisResults).length > 0) {
      console.log('[StocksContext] Using cached analysis results');
      return analysisResults;
    }

    console.log('[StocksContext] Fetching analysis results from server...');

    try {
      const firstResultsPage = await getAllAnalysisResults(1, 500);
      const totalResultPages = firstResultsPage?.total_pages || 1;

      let allResults = [...(firstResultsPage?.results || [])];

      if (totalResultPages > 1) {
        const resultPagePromises = [];
        for (let page = 2; page <= totalResultPages; page++) {
          resultPagePromises.push(getAllAnalysisResults(page, 500));
        }
        const resultsData = await Promise.all(resultPagePromises);
        resultsData.forEach(data => {
          if (data?.results) {
            allResults = [...allResults, ...data.results];
          }
        });
      }

      // Create map of symbol -> result (only first occurrence = newest)
      const resultsMap = {};
      allResults.forEach(result => {
        const key = result.symbol || result.ticker;
        if (key) {
          const upperKey = key.toUpperCase();
          if (!resultsMap[upperKey]) {
            resultsMap[upperKey] = result;
          }
        }
      });

      setAnalysisResults(resultsMap);
      setAnalysisLastFetch(Date.now());
      console.log(`[StocksContext] Loaded ${Object.keys(resultsMap).length} analysis results`);
      return resultsMap;
    } catch (error) {
      console.error('[StocksContext] Failed to fetch analysis results:', error);
      throw error;
    }
  }, [analysisResults, analysisLastFetch]);

  /**
   * Fetch watchlist (with caching)
   */
  const fetchWatchlistData = useCallback(async (forceRefresh = false) => {
    // Return cached data if valid
    if (!forceRefresh && isCacheValid(watchlistLastFetch) && watchlist.length > 0) {
      console.log('[StocksContext] Using cached watchlist');
      return watchlist;
    }

    console.log('[StocksContext] Fetching watchlist from server...');
    setWatchlistLoading(true);

    try {
      const data = await fetchWatchlist();

      // Filter out invalid items
      const validWatchlist = data.filter(stock => {
        if (!stock.ticker || stock.ticker.trim() === '') {
          console.warn('[StocksContext] Skipping watchlist item with empty ticker');
          return false;
        }
        return true;
      });

      // Enrich with analysis results
      const watchlistWithResults = await Promise.all(
        validWatchlist.map(async (stock) => {
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
            return { ...stock, verdict: 'No analysis available', confidence: 0, has_analysis: false };
          } catch (error) {
            console.error(`[StocksContext] Error fetching history for ${stock.ticker}:`, error);
            return { ...stock, verdict: 'No analysis available', confidence: 0, has_analysis: false };
          }
        })
      );

      setWatchlist(watchlistWithResults);
      setWatchlistLastFetch(Date.now());
      console.log(`[StocksContext] Loaded ${watchlistWithResults.length} watchlist items`);
      return watchlistWithResults;
    } catch (error) {
      console.error('[StocksContext] Failed to fetch watchlist:', error);
      throw error;
    } finally {
      setWatchlistLoading(false);
    }
  }, [watchlist, watchlistLastFetch]);

  /**
   * Add stock to watchlist cache (after successful API call)
   */
  const addToWatchlistCache = useCallback((stock) => {
    setWatchlist(prev => [...prev, stock]);
  }, []);

  /**
   * Remove stock from watchlist cache (after successful API call)
   */
  const removeFromWatchlistCache = useCallback((ticker) => {
    setWatchlist(prev => prev.filter(s => s.ticker !== ticker));
  }, []);

  /**
   * Update a single stock's analysis in cache (after re-analysis)
   */
  const updateStockAnalysis = useCallback((symbol, analysisData) => {
    const upperSymbol = symbol.toUpperCase();
    setAnalysisResults(prev => ({
      ...prev,
      [upperSymbol]: analysisData
    }));
    console.log(`[StocksContext] Updated analysis cache for ${symbol}`);
  }, []);

  /**
   * Update multiple stocks' analysis in cache (after bulk analysis)
   */
  const updateBulkAnalysis = useCallback((results) => {
    setAnalysisResults(prev => {
      const updated = { ...prev };
      results.forEach(result => {
        const key = (result.symbol || result.ticker)?.toUpperCase();
        if (key) {
          updated[key] = result;
        }
      });
      return updated;
    });
    console.log(`[StocksContext] Updated analysis cache for ${results.length} stocks`);
  }, []);

  /**
   * Force refresh all data
   */
  const refreshAll = useCallback(async () => {
    await Promise.all([
      fetchAllStocks(true),
      fetchAnalysisResults(true),
      fetchWatchlistData(true)
    ]);
  }, [fetchAllStocks, fetchAnalysisResults, fetchWatchlistData]);

  /**
   * Get merged stocks with analysis data
   */
  const getStocksWithAnalysis = useCallback(() => {
    return allStocks.map(stock => {
      const result = analysisResults[stock.symbol?.toUpperCase()];
      if (result) {
        return {
          ...stock,
          ticker: result.ticker,
          status: 'completed',
          score: result.score,
          verdict: result.verdict,
          entry: result.entry,
          target: result.target,
          has_analysis: true,
          stop_loss: result.stop_loss,
          created_at: result.created_at
        };
      }
      return {
        ...stock,
        status: 'pending',
        score: null,
        verdict: '-',
        entry: null,
        target: null,
        has_analysis: false
      };
    });
  }, [allStocks, analysisResults]);

  const value = {
    // All stocks
    allStocks,
    allStocksLoading,
    allStocksLastFetch,
    fetchAllStocks,

    // Analysis results
    analysisResults,
    analysisLastFetch,
    fetchAnalysisResults,
    updateStockAnalysis,
    updateBulkAnalysis,

    // Watchlist
    watchlist,
    watchlistLoading,
    watchlistLastFetch,
    fetchWatchlistData,
    addToWatchlistCache,
    removeFromWatchlistCache,

    // Utilities
    getStocksWithAnalysis,
    getTimeSinceLastFetch,
    isCacheValid,
    refreshAll,
    CACHE_TTL
  };

  return (
    <StocksContext.Provider value={value}>
      {children}
    </StocksContext.Provider>
  );
}

export function useStocks() {
  const context = useContext(StocksContext);
  if (!context) {
    throw new Error('useStocks must be used within a StocksProvider');
  }
  return context;
}

export default StocksContext;
