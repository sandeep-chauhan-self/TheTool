import { useEffect, useState } from 'react';
import { useLocation, useNavigate, useParams } from 'react-router-dom';
import { analyzeStocks, downloadReport, getReport, getStockHistory } from '../api/api';
import AIPromptSection from '../components/AIPromptSection';
import AnalysisConfigModal from '../components/AnalysisConfigModal';
import Breadcrumbs from '../components/Breadcrumbs';
import Header from '../components/Header';
import NavigationBar from '../components/NavigationBar';
import { extractBaseSymbol, getTradingViewUrl } from '../utils/tradingViewUtils';

// New UI Components
import VerdictBadge from '../components/ui/VerdictBadge';
import ScoreArc from '../components/ui/ScoreArc';

function Results() {
  const { ticker } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [reanalyzing, setReanalyzing] = useState(false);
  const [history, setHistory] = useState([]);
  const [selectedHistoryIndex, setSelectedHistoryIndex] = useState(0);
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [showAIPrompt, setShowAIPrompt] = useState(false);

  useEffect(() => {
    loadReport();
    loadHistory();
  }, [ticker]);

  const loadReport = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getReport(ticker);
      if (data && data.analysis) {
        setReport({
          ...data,
          verdict: data.analysis.verdict,
          score: data.analysis.score,
          entry: data.analysis.entry,
          stop: data.analysis.stop_loss,
          target: data.analysis.target,
          position_size: data.analysis.position_size || 0,
          risk_reward_ratio: data.analysis.risk_reward_ratio || 0,
          risk_message: data.analysis.risk_message || '',
          strategy_id: data.analysis.strategy_id || 5,
          analysis_config: data.analysis_config || null
        });
      } else {
        setReport(data);
      }
    } catch (err) {
      setError('Failed to load analysis report. The stock may not have been analyzed yet.');
      console.error('Failed to load report:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadHistory = async () => {
    try {
      const historyData = await getStockHistory(ticker);
      if (historyData && historyData.history && historyData.history.length > 0) {
        setHistory(historyData.history);
      }
    } catch (err) {
      console.log('No history available');
    }
  };

  const handleHistoryChange = (index) => {
    setSelectedHistoryIndex(index);
    const selectedAnalysis = history[index];
    setReport({
      ticker: ticker,
      verdict: selectedAnalysis.verdict,
      score: selectedAnalysis.score,
      entry: selectedAnalysis.entry,
      stop: selectedAnalysis.stop_loss,
      target: selectedAnalysis.target,
      position_size: selectedAnalysis.position_size || 0,
      risk_reward_ratio: selectedAnalysis.risk_reward_ratio || 0,
      indicators: selectedAnalysis.indicators || [],
      created_at: selectedAnalysis.created_at,
      strategy_id: selectedAnalysis.strategy_id || 5,
      analysis_config: selectedAnalysis.analysis_config || null
    });
  };

  const getCurrentStrategyId = () => report?.strategy_id || report?.analysis?.strategy_id || 5;

  const getStrategyName = (strategyId) => {
    const names = {
      1: 'Balanced Analysis',
      2: 'Trend Following',
      3: 'Mean Reversion',
      4: 'Momentum Breakout',
      5: 'Weekly 4% Target'
    };
    return names[strategyId] || `Strategy ${strategyId}`;
  };

  const handleDownload = async () => {
    try {
      await downloadReport(ticker);
    } catch (error) {
      console.error('Failed to download report:', error);
      alert('Failed to download report');
    }
  };

  const handleReanalyze = () => { if (!reanalyzing) setShowConfigModal(true); };

  const handleReanalyzeWithConfig = async (config) => {
    setShowConfigModal(false);
    try {
      setReanalyzing(true);
      await analyzeStocks([ticker], config);
      setTimeout(async () => {
        await loadReport();
        await loadHistory();
        setReanalyzing(false);
      }, 5000);
    } catch (error) {
      console.error('Failed to reanalyze:', error);
      alert('Failed to start re-analysis: ' + (error.message || 'Unknown error'));
      setReanalyzing(false);
    }
  };

  const getVoteDisplay = (vote) => {
    if (vote === 1) return 'Buy';
    if (vote === -1) return 'Sell';
    return 'Neutral';
  };

  const getVoteColor = (vote) => {
    if (vote === 1) return 'text-success-600 font-bold';
    if (vote === -1) return 'text-danger-600 font-bold';
    return 'text-slate-500';
  };

  if (loading) {
    return (
      <div className="min-h-screen mesh-bg">
        <NavigationBar />
        <Header title="Analysis Results" />
        <div className="max-w-7xl mx-auto px-4 py-8">
          <div className="flex flex-col items-center justify-center py-32">
            <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary-100 border-t-primary-600 mb-6 shadow-glow-primary"></div>
            <p className="text-slate-500 font-medium tracking-wide">Retrieving Market Data & AI Weights...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen mesh-bg">
        <NavigationBar />
        <Header title="Analysis Results" />
        <div className="max-w-7xl mx-auto px-4 py-8">
          <Breadcrumbs items={[{ label: 'Dashboard', path: '/' }, { label: 'All Stocks', path: '/all-stocks' }, { label: ticker, path: null }]} />
          <div className="bg-danger-50 border border-danger-200 text-danger-700 px-6 py-4 rounded-xl shadow-sm mb-4 mt-6 flex items-center gap-3">
             <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
            <span className="font-semibold">{error}</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen mesh-bg">
      <NavigationBar />
      <Header title={`${extractBaseSymbol(ticker)} Analysis`} subtitle="Dive deep into model evaluation and indicators for this asset." />

      <div className="max-w-7xl mx-auto px-4 pb-20">
        <Breadcrumbs items={[{ label: 'Dashboard', path: '/' }, { label: 'All Stocks', path: '/all-stocks' }, { label: extractBaseSymbol(ticker), path: null }]} />

        {/* Top actions */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mt-8 mb-8">
          <a href={getTradingViewUrl(ticker)} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-2 px-5 py-2.5 bg-slate-900 text-white rounded-xl hover:bg-slate-800 transition-colors shadow-md font-semibold text-sm">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4"><path fillRule="evenodd" d="M4.25 5.5a.75.75 0 00-.75.75v8.5c0 .414.336.75.75.75h8.5a.75.75 0 00.75-.75v-4a.75.75 0 011.5 0v4A2.25 2.25 0 0112.75 17h-8.5A2.25 2.25 0 012 14.75v-8.5A2.25 2.25 0 014.25 4h5a.75.75 0 010 1.5h-5z" clipRule="evenodd" /><path fillRule="evenodd" d="M6.194 12.753a.75.75 0 001.06.053L16.5 4.44v2.81a.75.75 0 001.5 0v-4.5a.75.75 0 00-.75-.75h-4.5a.75.75 0 000 1.5h2.553l-9.056 8.194a.75.75 0 00-.053 1.06z" clipRule="evenodd" /></svg>
            Live Chart (TradingView)
          </a>

          {history.length > 0 && (
            <div className="flex items-center gap-2 bg-white px-3 py-1.5 rounded-xl border border-slate-200 shadow-sm">
              <label className="text-sm font-bold text-slate-500 uppercase tracking-wide">Timeline</label>
              <select value={selectedHistoryIndex} onChange={(e) => handleHistoryChange(parseInt(e.target.value))} className="bg-transparent text-slate-800 font-medium text-sm focus:outline-none cursor-pointer">
                {history.map((item, index) => (
                  <option key={index} value={index}>
                    {index === 0 ? 'Current Analysis' : new Date(item.created_at).toLocaleDateString('en-IN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>

        {/* Demo Data Warning Banner */}
        {report.is_demo_data && (
          <div className="bg-warning-50 border-l-4 border-warning-500 p-5 rounded-r-xl shadow-sm mb-8 flex gap-4">
             <div className="text-warning-500 mt-1">
               <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
             </div>
             <div>
               <h3 className="text-warning-800 font-bold text-lg">Demo Data Detected</h3>
               <p className="text-warning-700 text-sm mt-1">This analysis is using <strong>simulated data</strong> endpoints due to failed Yahoo Finance fetching. Models and algorithms ran properly, but inputs are artificial. Do not use for trades.</p>
             </div>
          </div>
        )}

        {report.data_source && !report.is_demo_data && (
           <div className="mb-6 flex gap-2">
              <span className="px-3 py-1 rounded-full text-xs font-bold bg-success-50 text-success-700 border border-success-100 shadow-sm flex items-center gap-1">
                <div className="w-1.5 h-1.5 bg-success-500 rounded-full animate-pulse shadow-glow-success"></div>
                LIVE [{report.data_source}]
              </span>
              <span className="px-3 py-1 rounded-full text-xs font-bold bg-primary-50 text-primary-700 border border-primary-100 shadow-sm">
                Strategy: {getStrategyName(report.strategy_id || report.analysis?.strategy_id || 5)}
              </span>
           </div>
        )}

        {/* Final Verdict Summary Card */}
        <div className="glass-card mb-8 overflow-hidden relative">
           <div className="absolute top-0 right-0 p-8 opacity-5">
              <svg className="w-64 h-64 text-slate-900" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2L2 22h20L12 2zm0 4.1L18.4 19H5.6L12 6.1z"/></svg>
           </div>
           
           <div className="p-8 relative z-10 border-b border-slate-100 flex flex-col md:flex-row md:items-end justify-between gap-6">
              <div>
                <h2 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-slate-900 to-slate-600 mb-2">Model Verdict</h2>
                <div className="flex items-center gap-4">
                  <VerdictBadge verdict={report.verdict || 'Neutral'} />
                  {report.score != null && (
                    <div className="bg-white px-3 py-1 rounded-full border border-slate-200 shadow-sm">
                       <ScoreArc score={report.score / 100} />
                    </div>
                  )}
                </div>
              </div>

              <div className="flex gap-8">
                 <div className="text-right">
                   <div className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-1">Entry</div>
                   <div className="text-2xl font-bold text-primary-600">{report.entry != null ? `₹${Number(report.entry).toFixed(2)}` : 'N/A'}</div>
                 </div>
                 <div className="text-right border-l pl-8 border-slate-200">
                   <div className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-1">Target</div>
                   <div className="text-2xl font-bold text-success-600">{report.target != null ? `₹${Number(report.target).toFixed(2)}` : 'N/A'}</div>
                 </div>
                 <div className="text-right border-l pl-8 border-slate-200">
                   <div className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-1">Stop</div>
                   <div className="text-2xl font-bold text-danger-600">{report.stop != null ? `₹${Number(report.stop).toFixed(2)}` : 'N/A'}</div>
                 </div>
              </div>
           </div>

           {/* Position Sizing */}
           {report.position_size > 0 && (
             <div className="bg-slate-50/50 p-8">
                <h3 className="text-sm font-bold text-slate-500 uppercase tracking-wider mb-4 border-b border-slate-200 pb-2">Position & Risk Assessment</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                   <div>
                     <div className="text-xs font-bold text-slate-400 uppercase mb-1">Quantity</div>
                     <div className="text-xl font-bold text-slate-800">{report.position_size} <span className="text-sm font-medium text-slate-500">Shares</span></div>
                   </div>
                   <div>
                     <div className="text-xs font-bold text-slate-400 uppercase mb-1">Deployable Capital</div>
                     <div className="text-xl font-bold text-slate-800">₹{(report.position_size * report.entry).toLocaleString('en-IN', { maximumFractionDigits: 0 })}</div>
                   </div>
                   <div>
                     <div className="text-xs font-bold text-slate-400 uppercase mb-1">Value at Risk</div>
                     <div className="text-xl font-bold text-danger-600">₹{((report.entry - report.stop) * report.position_size).toLocaleString('en-IN', { maximumFractionDigits: 0 })}</div>
                   </div>
                   <div>
                     <div className="text-xs font-bold text-slate-400 uppercase mb-1">Reward Potential</div>
                     <div className="text-xl font-bold text-success-600">₹{((report.target - report.entry) * report.position_size).toLocaleString('en-IN', { maximumFractionDigits: 0 })}</div>
                   </div>
                </div>
                {report.risk_message && <p className="mt-4 text-sm text-slate-500 italic bg-white p-3 rounded-lg border border-slate-100">{report.risk_message}</p>}
             </div>
           )}
        </div>

        {/* Indicators Table */}
        <div className="glass-card mb-8">
          <div className="px-8 py-5 border-b border-slate-100">
            <h2 className="text-xl font-bold text-slate-900">Indicator Sub-Signals</h2>
          </div>
          <div className="overflow-x-auto">
             <table className="w-full text-sm">
                <thead className="bg-slate-50 border-b border-slate-100">
                  <tr>
                    <th className="px-8 py-4 text-left font-bold text-slate-400 uppercase tracking-wider text-xs">Indicator Model</th>
                    <th className="px-8 py-4 text-left font-bold text-slate-400 uppercase tracking-wider text-xs">Class</th>
                    <th className="px-8 py-4 text-left font-bold text-slate-400 uppercase tracking-wider text-xs">Output Value</th>
                    <th className="px-8 py-4 text-left font-bold text-slate-400 uppercase tracking-wider text-xs">Confidence</th>
                    <th className="px-8 py-4 text-left font-bold text-slate-400 uppercase tracking-wider text-xs">Final Vote</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 bg-white">
                  {report.indicators && report.indicators.length > 0 ? (
                    report.indicators.map((ind, idx) => (
                       <tr key={idx} className="hover:bg-slate-50 transition-colors">
                          <td className="px-8 py-4 font-bold text-slate-800">{ind.name}</td>
                          <td className="px-8 py-4 text-slate-500 capitalize font-medium">{ind.category}</td>
                          <td className="px-8 py-4 text-slate-700 font-mono text-xs">{ind.value}</td>
                          <td className="px-8 py-4 text-slate-700 font-medium">{ind.confidence != null ? `${(ind.confidence * 100).toFixed(0)}%` : '-'}</td>
                          <td className="px-8 py-4 whitespace-nowrap">
                            <span className={`inline-flex items-center px-2.5 py-1 rounded text-xs font-bold ${
                              ind.vote === 1 ? 'bg-success-50 text-success-700 border border-success-100' : 
                              ind.vote === -1 ? 'bg-danger-50 text-danger-700 border border-danger-100' : 
                              'bg-slate-100 text-slate-600 border border-slate-200'
                            }`}>
                              {getVoteDisplay(ind.vote)}
                            </span>
                          </td>
                       </tr>
                    ))
                  ) : (
                    <tr><td colSpan="5" className="px-8 py-12 text-center text-slate-500">Indicator stream unavailable for this model.</td></tr>
                  )}
                </tbody>
             </table>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex flex-wrap gap-4 items-center mb-12">
           <button onClick={handleReanalyze} disabled={reanalyzing || loading} className={`px-6 py-3 rounded-xl font-bold shadow-md transition-all flex items-center gap-2 ${reanalyzing ? 'bg-slate-200 text-slate-500' : 'bg-gradient-to-r from-primary-600 to-accent-600 text-white hover:from-primary-700 hover:to-accent-700 transform hover:-translate-y-0.5'}`}>
             {reanalyzing ? (
               <><svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg> Re-running Model...</>
             ) : (
               <><svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg> Re-Analyze Asset</>
             )}
           </button>

           <button onClick={() => navigate(`/backtest?ticker=${encodeURIComponent(ticker)}&strategy_id=${getCurrentStrategyId()}`)} className="px-6 py-3 rounded-xl font-bold bg-white text-slate-700 border border-slate-200 shadow-sm hover:bg-slate-50 transition-all flex items-center gap-2">
             <svg className="w-5 h-5 text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 13v-1m4 1v-3m4 3V8M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" /></svg>
             Run Backtest
           </button>
           
           <button onClick={() => setShowAIPrompt(!showAIPrompt)} className={`px-6 py-3 rounded-xl font-bold shadow-md transition-all flex items-center gap-2 ${showAIPrompt ? 'bg-slate-800 text-white' : 'bg-white text-slate-800 border border-slate-200 hover:bg-slate-50'}`}>
             <svg className={`w-5 h-5 ${showAIPrompt ? 'text-accent-400' : 'text-slate-400'}`} fill="currentColor" viewBox="0 0 20 20"><path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" /></svg>
             AI Prompts
           </button>

           <button onClick={handleDownload} className="ml-auto px-5 py-3 rounded-xl font-bold bg-white text-slate-500 border border-slate-200 shadow-sm hover:text-primary-600 transition-all">
             Download CSV
           </button>
        </div>

        {/* AI Section (Glass effect embedded) */}
        {showAIPrompt && (
          <div className="glass-card p-8 animate-slide-up border-accent-200">
            <AIPromptSection
              stockName={extractBaseSymbol(ticker)}
              ticker={ticker}
              strategyId={getCurrentStrategyId()}
              strategyName={getStrategyName(getCurrentStrategyId())}
              verdict={report.verdict || 'N/A'}
              score={report.score}
              entry={report.entry}
              stopLoss={report.stop}
              target={report.target}
            />
          </div>
        )}
      </div>

      {showConfigModal && <AnalysisConfigModal onClose={() => setShowConfigModal(false)} onConfirm={handleReanalyzeWithConfig} stockCount={1} stockNames={[ticker]} title={`Re-Analyze ${extractBaseSymbol(ticker)}`} />}
    </div>
  );
}

export default Results;
