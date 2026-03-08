import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import Breadcrumbs from './Breadcrumbs';
import Header from './Header';
import NavigationBar from './NavigationBar';

// New UI Components
import VerdictBadge from './ui/VerdictBadge';

const STRATEGIES = {
  1: { name: 'Balanced Analysis', icon: '⚖️', description: 'Equal weight to all 12 indicators' },
  2: { name: 'Trend Following', icon: '📈', description: 'Best for trending markets' },
  3: { name: 'Mean Reversion', icon: '🔄', description: 'Best for range-bound markets' },
  4: { name: 'Momentum Breakout', icon: '🚀', description: 'Volume-confirmed breakouts' },
  5: { name: 'Weekly 4% Target', icon: '🎯', description: 'Optimized swing trading' }
};

export default function BacktestResults() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const initialTicker = searchParams.get('ticker') || '';
  const initialStrategyId = parseInt(searchParams.get('strategy_id')) || 5;
  
  const [ticker, setTicker] = useState(initialTicker);
  const [days, setDays] = useState(90);
  const [strategyId, setStrategyId] = useState(initialStrategyId);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showDetailedTrades, setShowDetailedTrades] = useState(false);
  
  const API_BASE_URL = window.location.hostname === 'localhost' 
                         ? 'http://localhost:5000' 
                         : 'https://thetool-production.up.railway.app';

  useEffect(() => {
    if (initialTicker) runBacktest(initialTicker, initialStrategyId);
  }, [initialTicker, initialStrategyId]);

  const runBacktest = async (tickerToTest = ticker, strategyToTest = strategyId) => {
    if (!tickerToTest.trim()) { setError('Please enter a ticker symbol'); return; }
    setLoading(true); setError(null); setResults(null);
    try {
      const response = await fetch(`${API_BASE_URL}/api/backtest/ticker/${tickerToTest}?days=${days}&strategy_id=${strategyToTest}`);
      if (!response.ok) throw new Error(`API Error: ${response.status}`);
      const data = await response.json();
      if (data.error) setError(data.error); else setResults(data);
    } catch (err) {
      setError(err.message || 'Backtest failed. Please try again.');
    } finally { setLoading(false); }
  };

  const handleKeyPress = (e) => { if (e.key === 'Enter') runBacktest(); };

  return (
    <div className="min-h-screen mesh-bg">
      <NavigationBar />
      <Header title="Backtest Engine" subtitle={`Evaluating ${ticker || 'historical performance'} using Strategy ${strategyId}`} />

      <div className="max-w-7xl mx-auto px-4 pb-20">
        <Breadcrumbs items={[{ label: 'Dashboard', path: '/' }, { label: 'Strategies', path: '/strategies' }, { label: 'Backtest', path: null }]} />

        {/* Configuration Bar */}
        <div className="glass-card p-6 mb-8 mt-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 items-end">
            <div>
              <label className="block text-xs font-bold text-slate-500 uppercase tracking-widest mb-2">Stock Ticker</label>
              <input type="text" placeholder="e.g. RELIANCE.NS" value={ticker} onChange={(e) => setTicker(e.target.value.toUpperCase())} onKeyPress={handleKeyPress} className="w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-primary-500 font-bold text-slate-800" />
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-500 uppercase tracking-widest mb-2">Model</label>
              <select value={strategyId} onChange={(e) => setStrategyId(parseInt(e.target.value))} className="w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-primary-500 font-medium text-slate-700">
                {Object.entries(STRATEGIES).map(([id, s]) => <option key={id} value={id}>Strategy {id}: {s.name}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-500 uppercase tracking-widest mb-2">Period</label>
              <select value={days} onChange={(e) => setDays(parseInt(e.target.value))} className="w-full px-4 py-2.5 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-primary-500 font-medium text-slate-700">
                <option value={30}>Last 30 days</option>
                <option value={90}>Last 90 days</option>
                <option value={180}>Last 6 months</option>
                <option value={365}>Last 1 year</option>
              </select>
            </div>
            <button onClick={() => runBacktest()} disabled={loading} className="py-2.5 bg-gradient-to-r from-primary-600 to-accent-600 text-white rounded-xl font-bold shadow-md hover:shadow-lg transition-all flex items-center justify-center gap-2">
              {loading ? <><div className="animate-spin rounded-full h-4 w-4 border-2 border-white/20 border-t-white" /> Executing...</> : '▶ Run Backtest'}
            </button>
          </div>
        </div>

        {error && (
          <div className="bg-danger-50 border border-danger-200 text-danger-700 px-6 py-4 rounded-2xl shadow-sm mb-8 animate-fade-in flex items-center gap-3">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
            <span className="font-semibold">{error}</span>
          </div>
        )}

        {loading && (
          <div className="flex flex-col items-center justify-center py-32">
            <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary-100 border-t-primary-600 mb-6 shadow-glow-primary"></div>
            <p className="text-slate-500 font-medium tracking-wide">Crunching Historical Signals & P&L...</p>
          </div>
        )}

        {results && !loading && (
          <div className="animate-slide-up">
            {/* Macro Stats Section */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              <div className="glass-card p-6">
                <div className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">Win Rate</div>
                <div className={`text-3xl font-bold ${results.win_rate >= 50 ? 'text-success-600' : 'text-danger-600'}`}>{results.win_rate}%</div>
                <div className="text-xs font-semibold text-slate-500 mt-2">{results.winning_trades}W / {results.losing_trades}L</div>
              </div>
              <div className="glass-card p-6">
                <div className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">Total Profit</div>
                <div className={`text-3xl font-bold ${results.total_profit_pct > 0 ? 'text-success-600' : 'text-danger-600'}`}>
                  {results.total_profit_pct > 0 ? '+' : ''}{results.total_profit_pct}%
                </div>
                <div className="text-xs font-semibold text-slate-500 mt-2">Net change in period</div>
              </div>
              <div className="glass-card p-6">
                <div className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">Profit Factor</div>
                <div className="text-3xl font-bold text-slate-800">{results.profit_factor}x</div>
                <div className="text-xs font-semibold text-slate-500 mt-2">Win/Loss Ratio</div>
              </div>
              <div className="glass-card p-6">
                <div className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">Max Drawdown</div>
                <div className="text-3xl font-bold text-danger-500">{results.max_drawdown}%</div>
                <div className="text-xs font-semibold text-slate-500 mt-2">Peak decline</div>
              </div>
            </div>

            {/* Empty signals handler */}
            {results.total_signals === 0 ? (
               <div className="glass-card p-12 text-center bg-white/50 border-warning-100">
                  <div className="text-5xl mb-6 opacity-30">📊</div>
                  <h3 className="text-xl font-bold text-slate-800 mb-2">No Trading Signals Identified</h3>
                  <p className="text-slate-500 max-w-md mx-auto">The {STRATEGIES[results.strategy_id]?.name} model didn't find any actionable entry points for {ticker} in the last {results.backtest_period}.</p>
               </div>
            ) : (
              <>
                {/* Trades History Table */}
                <div className="glass-card mb-8">
                  <div className="px-8 py-5 border-b border-slate-100 flex justify-between items-center bg-slate-50/30">
                    <h3 className="text-lg font-bold text-slate-900">Trade Sequence Log</h3>
                    <div className="flex gap-2">
                       <span className="px-3 py-1 bg-white border border-slate-200 rounded-full text-xs font-bold text-slate-500">{results.trades.length} Positions</span>
                    </div>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead className="bg-white border-b border-slate-100">
                        <tr>
                          <th className="px-8 py-4 text-left font-bold text-slate-400 uppercase tracking-wider text-xs">Date</th>
                          <th className="px-8 py-4 text-left font-bold text-slate-400 uppercase tracking-wider text-xs">Entry</th>
                          <th className="px-8 py-4 text-left font-bold text-slate-400 uppercase tracking-wider text-xs">Exit</th>
                          <th className="px-8 py-4 text-left font-bold text-slate-400 uppercase tracking-wider text-xs">P&L (%)</th>
                          <th className="px-8 py-4 text-left font-bold text-slate-400 uppercase tracking-wider text-xs">Outcome</th>
                          <th className="px-8 py-4 text-left font-bold text-slate-400 uppercase tracking-wider text-xs">Strategy Context</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 bg-white">
                        {results.trades.map((trade, idx) => (
                          <tr key={idx} className="hover:bg-slate-50/50 transition-colors">
                            <td className="px-8 py-4 font-medium text-slate-600">{trade.entry_date}</td>
                            <td className="px-8 py-4 font-bold text-slate-800">₹{trade.entry_price.toFixed(2)}</td>
                            <td className="px-8 py-4 font-bold text-slate-800">₹{trade.exit_price.toFixed(2)}</td>
                            <td className={`px-8 py-4 font-bold ${trade.pnl_pct > 0 ? 'text-success-600' : 'text-danger-600'}`}>
                              {trade.pnl_pct > 0 ? '+' : ''}{trade.pnl_pct.toFixed(2)}%
                            </td>
                            <td className="px-8 py-4">
                               <span className={`inline-flex items-center px-2.5 py-1 rounded-md text-[10px] font-bold uppercase tracking-wider border ${
                                 trade.outcome === 'WIN' ? 'bg-success-50 text-success-700 border-success-100' : 'bg-danger-50 text-danger-700 border-danger-100'
                               }`}>
                                 {trade.outcome}
                               </span>
                            </td>
                            <td className="px-8 py-4">
                               <div className="text-xs text-slate-500 max-w-[200px] truncate" title={trade.reason}>{trade.reason}</div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Analysis Deep Dive */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                   <div className="glass-card p-8">
                      <h3 className="text-lg font-bold text-slate-900 mb-6 flex items-center gap-2">
                        <svg className="w-5 h-5 text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>
                        Performance Verdict
                      </h3>
                      <div className="space-y-4">
                        <div className="flex items-start gap-4 p-4 rounded-xl border border-slate-100 bg-slate-50/50">
                           <div className="mt-1">{results.win_rate >= 50 ? '✅' : '⚠️'}</div>
                           <div>
                             <div className="text-sm font-bold text-slate-800">{results.win_rate >= 50 ? 'Strategy Validated' : 'Statistical Edge Warning'}</div>
                             <p className="text-xs text-slate-500 mt-1">The model maintained a {results.win_rate}% strike across {results.total_signals} samples.</p>
                           </div>
                        </div>
                        <div className="flex items-start gap-4 p-4 rounded-xl border border-slate-100 bg-slate-50/50">
                           <div className="mt-1">{results.profit_factor >= 1.5 ? '💰' : '📉'}</div>
                           <div>
                             <div className="text-sm font-bold text-slate-800">Profitability Ratio</div>
                             <p className="text-xs text-slate-500 mt-1">Wins were {results.profit_factor} times larger than total cumulative losses.</p>
                           </div>
                        </div>
                      </div>
                   </div>

                   <div className="glass-card p-8 border-accent-100">
                      <h3 className="text-lg font-bold text-slate-900 mb-6 flex items-center gap-2">
                        <svg className="w-5 h-5 text-accent-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m14 4a2 2 0 100-4m0 4a2 2 0 110-4M6 20h12M6 5H2M22 5h-4m-7 15h2m8 0h-4M6 15H2m22 0h-4" /></svg>
                        Model Constraints
                      </h3>
                      <div className="grid grid-cols-2 gap-4">
                        <div className="p-4 rounded-xl bg-white border border-slate-100">
                           <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Target Threshold</div>
                           <div className="text-lg font-bold text-slate-800">{results.strategy_params?.target_pct || '4'}%</div>
                        </div>
                        <div className="p-4 rounded-xl bg-white border border-slate-100">
                           <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Stop Threshold</div>
                           <div className="text-lg font-bold text-slate-800">{results.strategy_params?.stop_loss_pct || '2'}%</div>
                        </div>
                        <div className="p-4 rounded-xl bg-white border border-slate-100">
                           <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Hold Ceiling</div>
                           <div className="text-lg font-bold text-slate-800">{results.strategy_params?.max_bars || '15'} Days</div>
                        </div>
                        <div className="p-4 rounded-xl bg-white border border-slate-100">
                           <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Exclusions</div>
                           <div className="text-lg font-bold text-slate-800">{results.excluded_trades || '0'}</div>
                        </div>
                      </div>
                   </div>
                </div>
              </>
            )}
          </div>
        )}

        {!results && !loading && !error && (
          <div className="flex flex-col items-center justify-center py-40 border-2 border-dashed border-slate-200 rounded-3xl mt-8">
            <div className="text-6xl mb-6 opacity-20">📊</div>
            <h3 className="text-xl font-bold text-slate-400">Backtest Engine Idle</h3>
            <p className="text-slate-400 mt-2">Specify a ticker and strategy above to begin evaluation.</p>
          </div>
        )}
      </div>
    </div>
  );
}
