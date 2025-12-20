import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams, useLocation } from 'react-router-dom';
import './BacktestResults.css';

// Strategy definitions with descriptions
const STRATEGIES = {
  1: { name: 'Balanced Analysis', description: 'Equal weight to all 12 indicators' },
  2: { name: 'Trend Following', description: 'Best for trending markets' },
  3: { name: 'Mean Reversion', description: 'Best for range-bound markets' },
  4: { name: 'Momentum Breakout', description: 'Volume-confirmed breakouts' },
  5: { name: 'Weekly 4% Target', description: 'Optimized swing trading' }
};

export default function BacktestResults() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const location = useLocation();
  const initialTicker = searchParams.get('ticker') || '';
  const initialStrategyId = parseInt(searchParams.get('strategy_id')) || 5;
  
  const [ticker, setTicker] = useState(initialTicker);
  const [days, setDays] = useState(90);
  const [strategyId, setStrategyId] = useState(initialStrategyId);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showDetailedTrades, setShowDetailedTrades] = useState(false);
  
  // Get the page we came from (if any)
  const previousPage = location.state?.from || null;
  const previousTicker = location.state?.ticker || null;

  const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 
                       (window.location.hostname === 'localhost' 
                         ? 'http://localhost:5000' 
                         : 'https://thetool-production.up.railway.app');

  // Auto-run backtest if ticker is provided via URL
  useEffect(() => {
    if (initialTicker) {
      runBacktest(initialTicker, initialStrategyId);
    }
  }, [initialTicker, initialStrategyId]);

  const runBacktest = async (tickerToTest = ticker, strategyToTest = strategyId) => {
    if (!tickerToTest.trim()) {
      setError('Please enter a ticker symbol');
      return;
    }

    setLoading(true);
    setError(null);
    setResults(null);
    
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/backtest/ticker/${tickerToTest}?days=${days}&strategy_id=${strategyToTest}`
      );

      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
      }

      const data = await response.json();

      if (data.error) {
        setError(data.error);
      } else {
        setResults(data);
      }
    } catch (err) {
      setError(err.message || 'Backtest failed. Please try again.');
      console.error('Backtest error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      runBacktest();
    }
  };

  const handleStrategyChange = (e) => {
    const newStrategyId = parseInt(e.target.value);
    setStrategyId(newStrategyId);
    // Don't auto-run on change - let user click Run button
  };

  const handleBackClick = () => {
    // If we came from an analysis page, go back there
    if (previousPage === '/results' && previousTicker) {
      navigate(`/results/${encodeURIComponent(previousTicker)}`);
    } else if (previousPage) {
      // Otherwise go back to wherever we came from
      navigate(-1);
    } else {
      // If we don't know where we came from, go to dashboard
      navigate('/');
    }
  };

  return (
    <div className="backtest-container">
      <div className="backtest-header">
        <h1>📊 Strategy Backtest Analysis</h1>
        <p>Test trading strategies on historical data</p>
        <button 
          onClick={handleBackClick}
          className="back-to-analysis-btn"
        >
          ← Back
        </button>
      </div>

      <div className="backtest-inputs">
        <div className="input-group">
          <label htmlFor="ticker">Stock Ticker</label>
          <input
            id="ticker"
            type="text"
            placeholder="e.g., RELIANCE.NS, TCS.NS, INFY.NS"
            value={ticker}
            onChange={(e) => setTicker(e.target.value.toUpperCase())}
            onKeyPress={handleKeyPress}
            disabled={loading}
          />
        </div>

        <div className="input-group">
          <label htmlFor="strategy">Strategy</label>
          <select 
            id="strategy"
            value={strategyId} 
            onChange={handleStrategyChange}
            disabled={loading}
          >
            {Object.entries(STRATEGIES).map(([id, strategy]) => (
              <option key={id} value={id}>
                Strategy {id}: {strategy.name}
              </option>
            ))}
          </select>
          <div className="strategy-hint">{STRATEGIES[strategyId]?.description}</div>
        </div>

        <div className="input-group">
          <label htmlFor="days">Period</label>
          <select 
            id="days"
            value={days} 
            onChange={(e) => setDays(parseInt(e.target.value))}
            disabled={loading}
          >
            <option value={30}>Last 30 days</option>
            <option value={60}>Last 60 days</option>
            <option value={90}>Last 90 days</option>
            <option value={180}>Last 6 months</option>
            <option value={365}>Last 1 year</option>
          </select>
        </div>

        <button 
          onClick={() => runBacktest(ticker, strategyId)} 
          disabled={loading}
          className="backtest-button"
        >
          {loading ? (
            <>
              <span className="spinner"></span>
              Running...
            </>
          ) : (
            '▶ Run Backtest'
          )}
        </button>
      </div>

      {error && (
        <div className="error-message">
          <span className="error-icon">⚠️</span>
          {error}
        </div>
      )}

      {results && !error && (
        <div className="backtest-results">
          {/* Summary Section */}
          <div className="results-summary">
            <h2>
              {results.ticker}
              <span className="strategy-badge">Strategy {results.strategy_id}: {results.strategy_name}</span>
              <span className="period-badge">{results.backtest_period}</span>
            </h2>

            {/* No Signals Message */}
            {results.total_signals === 0 && (
              <div className="no-signals-message">
                <div className="no-signals-icon">📭</div>
                <h3>No Buy Signals Generated</h3>
                <p>{results.message || 'No trading opportunities were identified during this period based on the strategy criteria.'}</p>
                <div className="no-signals-tips">
                  <p><strong>This could mean:</strong></p>
                  <ul>
                    <li>The stock is in a downtrend (not meeting trend filter criteria)</li>
                    <li>RSI or momentum indicators are outside the buy zone</li>
                    <li>Volatility conditions don't match the strategy</li>
                  </ul>
                  <p><strong>Try:</strong> Testing with a different strategy or extending the time period</p>
                </div>
              </div>
            )}

            {/* Strategy Parameters - only show if we have signals */}
            {results.strategy_params && results.total_signals > 0 && (
              <div className="strategy-params">
                <span className="param">Target: {results.strategy_params.target_pct}%</span>
                <span className="param">Stop: {results.strategy_params.stop_loss_pct}%</span>
                <span className="param">Max Bars: {results.strategy_params.max_bars}</span>
                <span className="param">RSI: {results.strategy_params.rsi_range}</span>
              </div>
            )}

            {/* Key Metrics Grid - only show if we have signals */}
            {results.total_signals > 0 && (
            <div className="metrics-grid">
              <div className="metric-card">
                <div className="metric-label">Win Rate</div>
                <div className={`metric-value ${results.win_rate >= 50 ? 'positive' : 'negative'}`}>
                  {results.win_rate}%
                </div>
                <div className="metric-detail">
                  {results.winning_trades}W / {results.losing_trades}L
                </div>
              </div>

              <div className="metric-card">
                <div className="metric-label">Profit Factor</div>
                <div className={`metric-value ${results.profit_factor >= 1.5 ? 'positive' : 'neutral'}`}>
                  {results.profit_factor}x
                </div>
                <div className="metric-detail">Wins ÷ Losses</div>
              </div>

              <div className="metric-card">
                <div className="metric-label">Total P&L</div>
                <div className={`metric-value ${results.total_profit_pct > 0 ? 'positive' : 'negative'}`}>
                  {results.total_profit_pct > 0 ? '+' : ''}{results.total_profit_pct}%
                </div>
                <div className="metric-detail">Net Profit</div>
              </div>

              <div className="metric-card">
                <div className="metric-label">Avg Win</div>
                <div className="metric-value positive">
                  +{results.avg_win}%
                </div>
                <div className="metric-detail">Per winning trade</div>
              </div>

              <div className="metric-card">
                <div className="metric-label">Avg Loss</div>
                <div className="metric-value negative">
                  {results.avg_loss}%
                </div>
                <div className="metric-detail">Per losing trade</div>
              </div>

              <div className="metric-card">
                <div className="metric-label">Max Drawdown</div>
                <div className="metric-value negative">
                  {results.max_drawdown}%
                </div>
                <div className="metric-detail">Worst peak-to-trough</div>
              </div>

              <div className="metric-card">
                <div className="metric-label">Consecutive Wins</div>
                <div className="metric-value positive">
                  {results.consecutive_wins}
                </div>
                <div className="metric-detail">Longest streak</div>
              </div>

              <div className="metric-card">
                <div className="metric-label">Total Signals</div>
                <div className="metric-value neutral">
                  {results.total_signals}
                </div>
                <div className="metric-detail">Trades analyzed</div>
              </div>

              {/* Excluded Trades Info */}
              {results.excluded_trades > 0 && (
                <div className="metric-card excluded-card">
                  <div className="metric-label">Excluded</div>
                  <div className="metric-value neutral">
                    {results.excluded_trades}
                  </div>
                  <div className="metric-detail">Insufficient data</div>
                </div>
              )}
            </div>
            )}

            {/* Exclusion Note */}
            {results.exclusion_note && results.total_signals > 0 && (
              <div className="exclusion-note">
                <span className="info-icon">ℹ️</span>
                {results.exclusion_note}
              </div>
            )}

            {/* Analysis Summary - only show if we have signals */}
            {results.total_signals > 0 && (
            <div className="analysis-summary">
              <h3>📈 Analysis Summary</h3>
              <div className="summary-text">
                {results.win_rate >= 60 && (
                  <p>✅ <strong>Strong Performance:</strong> {results.win_rate}% win rate shows consistent profitability</p>
                )}
                {results.win_rate < 60 && results.win_rate >= 40 && (
                  <p>⚠️ <strong>Moderate Performance:</strong> {results.win_rate}% win rate is acceptable</p>
                )}
                {results.win_rate < 40 && (
                  <p>❌ <strong>Needs Improvement:</strong> {results.win_rate}% win rate is below target</p>
                )}
                
                {results.profit_factor >= 2 && (
                  <p>✅ <strong>Excellent Profit Factor:</strong> {results.profit_factor}x shows wins are {Math.round(results.profit_factor)}x larger than losses</p>
                )}
                {results.profit_factor < 2 && results.profit_factor >= 1.5 && (
                  <p>⚠️ <strong>Good Profit Factor:</strong> {results.profit_factor}x</p>
                )}
                
                {results.max_drawdown < 5 && (
                  <p>✅ <strong>Low Drawdown:</strong> {Math.abs(results.max_drawdown)}% shows good risk management</p>
                )}
                {results.max_drawdown >= 5 && (
                  <p>⚠️ <strong>Watch Drawdown:</strong> {Math.abs(results.max_drawdown)}% peak decline - consider position sizing</p>
                )}
              </div>
            </div>
            )}
          </div>

          {/* Trades Section */}
          {results.trades && results.trades.length > 0 && (
            <div className="trades-section">
              <div className="trades-header">
                <h3>📋 Trade History ({results.trades.length} trades)</h3>
                <button 
                  className="toggle-button"
                  onClick={() => setShowDetailedTrades(!showDetailedTrades)}
                >
                  {showDetailedTrades ? '▼ Hide Details' : '▶ Show All Details'}
                </button>
              </div>

              {/* Quick Summary Table */}
              <div className="trades-quick">
                <h4>Recent Trades</h4>
                <table className="trades-table">
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Entry</th>
                      <th>Exit</th>
                      <th>Outcome</th>
                      <th>P&L</th>
                      <th>Bars</th>
                      <th>Reason</th>
                    </tr>
                  </thead>
                  <tbody>
                    {results.trades.slice(-10).map((trade, idx) => (
                      <tr key={idx} className={`trade-${trade.outcome.toLowerCase()}`}>
                        <td className="date">{trade.entry_date}</td>
                        <td className="price">₹{trade.entry_price.toFixed(2)}</td>
                        <td className="price">₹{trade.exit_price.toFixed(2)}</td>
                        <td className="outcome">
                          <span className={`badge badge-${trade.outcome.toLowerCase()}`}>
                            {trade.outcome}
                          </span>
                        </td>
                        <td className={`pnl ${trade.pnl_pct > 0 ? 'positive' : 'negative'}`}>
                          {trade.pnl_pct > 0 ? '+' : ''}{trade.pnl_pct.toFixed(2)}%
                        </td>
                        <td className="bars">{trade.bars_held}</td>
                        <td className="reason">{trade.reason}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Detailed Trades View */}
              {showDetailedTrades && (
                <div className="trades-detailed">
                  <h4>All Trades Detailed View</h4>
                  <div className="trades-grid">
                    {results.trades.map((trade, idx) => (
                      <div key={idx} className={`trade-card trade-card-${trade.outcome.toLowerCase()}`}>
                        <div className="trade-header">
                          <h5>Trade #{idx + 1}</h5>
                          <span className={`badge badge-${trade.outcome.toLowerCase()}`}>
                            {trade.outcome}
                          </span>
                        </div>
                        <div className="trade-details">
                          <div className="detail-row">
                            <span className="label">Date:</span>
                            <span className="value">{trade.entry_date}</span>
                          </div>
                          <div className="detail-row">
                            <span className="label">Entry:</span>
                            <span className="value">₹{trade.entry_price.toFixed(2)}</span>
                          </div>
                          <div className="detail-row">
                            <span className="label">Exit:</span>
                            <span className="value">₹{trade.exit_price.toFixed(2)}</span>
                          </div>
                          <div className="detail-row">
                            <span className="label">Target:</span>
                            <span className="value">₹{trade.target.toFixed(2)}</span>
                          </div>
                          <div className="detail-row">
                            <span className="label">Stop Loss:</span>
                            <span className="value">₹{trade.stop_loss.toFixed(2)}</span>
                          </div>
                          <div className="detail-row">
                            <span className="label">P&L:</span>
                            <span className={`value pnl ${trade.pnl_pct > 0 ? 'positive' : 'negative'}`}>
                              {trade.pnl_pct > 0 ? '+' : ''}{trade.pnl_pct.toFixed(2)}%
                            </span>
                          </div>
                          <div className="detail-row">
                            <span className="label">Bars Held:</span>
                            <span className="value">{trade.bars_held}</span>
                          </div>
                          <div className="detail-row">
                            <span className="label">Reason:</span>
                            <span className="value">{trade.reason}</span>
                          </div>
                          <div className="detail-row">
                            <span className="label">Confidence:</span>
                            <span className="value">{trade.confidence}%</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {results.total_signals === 0 && (
            <div className="no-trades">
              <p>No trading signals generated for this period.</p>
              <p>Try a longer period or different stock symbol.</p>
            </div>
          )}
        </div>
      )}

      {!results && !loading && !error && (
        <div className="empty-state">
          <div className="empty-icon">📊</div>
          <h3>No backtest run yet</h3>
          <p>Enter a ticker symbol, select a strategy, and click "Run Backtest" to analyze performance</p>
          <p className="hint">📌 Tip: Try RELIANCE.NS, TCS.NS, or INFY.NS</p>
        </div>
      )}
    </div>
  );
}
