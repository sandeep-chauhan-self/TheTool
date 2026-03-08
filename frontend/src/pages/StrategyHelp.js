import { useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { Link, useParams } from 'react-router-dom';
import { getStrategy, getStrategyHelp } from '../api/api';
import Breadcrumbs from '../components/Breadcrumbs';
import Header from '../components/Header';
import NavigationBar from '../components/NavigationBar';

/**
 * StrategyHelp - Detailed help page for a specific strategy
 */

const slugToId = {
  'balanced': 1, 'trend-following': 2, 'mean-reversion': 3, 'momentum-breakout': 4, 'weekly-target': 5,
  '1': 1, '2': 2, '3': 3, '4': 4, '5': 5
};

const strategyMeta = {
  1: { name: 'Balanced Analysis', icon: '⚖️', color: 'primary' },
  2: { name: 'Trend Following', icon: '📈', color: 'success' },
  3: { name: 'Mean Reversion', icon: '🔄', color: 'accent' },
  4: { name: 'Momentum Breakout', icon: '🚀', color: 'warning' },
  5: { name: 'Weekly 4% Target', icon: '🎯', color: 'danger' }
};

function StrategyHelp() {
  const { id: urlParam } = useParams();
  const [strategy, setStrategy] = useState(null);
  const [helpContent, setHelpContent] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const strategyId = slugToId[urlParam] || parseInt(urlParam);

  useEffect(() => {
    const fetchData = async () => {
      if (!strategyId || strategyId < 1 || strategyId > 5) {
        setError('Invalid core strategy ID.'); setLoading(false); return;
      }
      try {
        setLoading(true); setError(null);
        const [sData, hData] = await Promise.all([getStrategy(strategyId), getStrategyHelp(strategyId)]);
        setStrategy(sData.strategy); setHelpContent(hData.help_content || '');
      } catch (err) {
        setError('Failed to fetch model documentation.');
      } finally { setLoading(false); }
    };
    fetchData();
  }, [strategyId]);

  const meta = strategyMeta[strategyId] || {};

  if (loading) {
    return (
      <div className="min-h-screen mesh-bg">
        <NavigationBar />
        <div className="flex flex-col items-center justify-center py-40">
           <div className="animate-spin rounded-full h-12 w-12 border-4 border-slate-100 border-t-primary-600 shadow-glow-primary"></div>
           <p className="mt-6 font-bold text-slate-500 uppercase tracking-widest text-xs">Accessing Model Repository...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen mesh-bg pb-20">
      <NavigationBar />
      <Header title={meta.name} subtitle={`Model Architecture Details for Strategy ${strategyId}`} />

      <div className="max-w-5xl mx-auto px-4">
        <Breadcrumbs items={[{ label: 'Dashboard', path: '/' }, { label: 'Strategies', path: '/strategies' }, { label: meta.name, path: null }]} />

        {/* Floating Quick Navigation */}
        <div className="flex gap-2 mb-8 mt-6 overflow-x-auto pb-2 -mx-4 px-4 no-scrollbar">
          {[1,2,3,4,5].map(id => (
            <Link key={id} to={`/strategies/${id}`} className={`px-5 py-2 rounded-xl border font-bold text-sm transition-all whitespace-nowrap shadow-sm ${id === strategyId ? 'bg-slate-900 border-slate-900 text-white shadow-lg' : 'bg-white border-slate-200 text-slate-500 hover:border-primary-500 hover:text-primary-600'}`}>
               {strategyMeta[id].icon} Strategy {id}
            </Link>
          ))}
        </div>

        {/* Content Body */}
        <div className="glass-card p-10 animate-slide-up bg-white/95">
           <div className="flex flex-col md:flex-row gap-10 items-start">
              <div className="flex-1">
                 <div className="flex items-center gap-4 mb-8">
                    <div className={`w-16 h-16 rounded-2xl flex items-center justify-center text-3xl shadow-lg border border-white/50 bg-${meta.color}-50`}>
                       {meta.icon}
                    </div>
                    <div>
                        <h2 className="text-3xl font-black text-slate-900 tracking-tighter">{strategy?.name || meta.name}</h2>
                        <div className="flex items-center gap-2 mt-1">
                           <span className={`px-2 py-0.5 rounded text-[10px] font-black uppercase tracking-widest bg-${meta.color}-100 text-${meta.color}-700 border border-${meta.color}-200`}>Active Production Model</span>
                           <Link to={`/backtest?strategy_id=${strategyId}`} className="text-xs font-bold text-primary-600 hover:underline flex items-center gap-1 ml-2">📊 Run Real-time Simulation</Link>
                        </div>
                    </div>
                 </div>

                 <article className="prose prose-slate max-w-none prose-headings:text-slate-900 prose-p:text-slate-600 prose-p:leading-relaxed prose-strong:text-slate-900 prose-pre:bg-slate-900 prose-pre:text-primary-300">
                    <ReactMarkdown
                      components={{
                        // Custom styled components for markdown mapping
                        h1: ({children}) => <h1 className="text-4xl font-black tracking-tight mb-8 pb-4 border-b border-slate-100">{children}</h1>,
                        h2: ({children}) => <h2 className="text-2xl font-bold tracking-tight mt-12 mb-6 text-slate-800">{children}</h2>,
                        h3: ({children}) => <h3 className="text-xl font-bold mt-8 mb-4 text-slate-800">{children}</h3>,
                        ul: ({children}) => <ul className="list-disc list-outside ml-6 space-y-3 my-6">{children}</ul>,
                        li: ({children}) => <li className="text-slate-600 font-medium pl-2">{children}</li>,
                        blockquote: ({children}) => <blockquote className="border-l-4 border-primary-500 bg-primary-50/50 p-6 my-8 rounded-r-2xl italic text-slate-700 font-medium">{children}</blockquote>,
                        table: ({children}) => <div className="overflow-x-auto my-8 rounded-2xl border border-slate-100 shadow-sm"><table className="w-full text-sm border-collapse">{children}</table></div>,
                        thead: ({children}) => <thead className="bg-slate-50 border-b border-slate-100">{children}</thead>,
                        th: ({children}) => <th className="px-6 py-4 text-left font-bold text-slate-500 uppercase tracking-widest text-[10px]">{children}</th>,
                        td: ({children}) => <td className="px-6 py-4 border-b border-slate-50 font-medium text-slate-600">{children}</td>,
                        code: ({inline, children}) => inline ? <code className="bg-slate-100 px-1.5 py-0.5 rounded text-primary-700 font-bold font-mono text-xs">{children}</code> : <code className="block p-2 text-primary-300">{children}</code>
                      }}
                    >
                      {helpContent}
                    </ReactMarkdown>
                 </article>
              </div>

              {/* Sidebar Diagnostics */}
              <div className="w-full md:w-80 shrink-0 space-y-8">
                 <div className="p-6 rounded-2xl bg-slate-50 border border-slate-100">
                    <h4 className="text-xs font-black text-slate-400 uppercase tracking-widest mb-6 flex items-center gap-2">
                       <div className="w-1.5 h-1.5 rounded-full bg-primary-500"></div>
                       Global Parameters
                    </h4>
                    <div className="space-y-4">
                       <div className="flex justify-between items-center">
                          <span className="text-sm font-bold text-slate-500">Conviction Cap</span>
                          <span className="text-sm font-black text-slate-900">{strategy?.target_pct || '4.0'}%</span>
                       </div>
                       <div className="flex justify-between items-center">
                          <span className="text-sm font-bold text-slate-500">Risk Stop</span>
                          <span className="text-sm font-black text-danger-600">{strategy?.stop_loss_pct || '2.0'}%</span>
                       </div>
                       <div className="flex justify-between items-center">
                          <span className="text-sm font-bold text-slate-500">Maximum Hold</span>
                          <span className="text-sm font-black text-slate-900">15 Days</span>
                       </div>
                    </div>
                 </div>

                 <Link to={`/backtest?strategy_id=${strategyId}`} className="block p-6 rounded-2xl bg-slate-900 text-white group shadow-xl hover:shadow-primary-200/50 transition-all border border-slate-800">
                    <div className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">Backtest Engine</div>
                    <div className="text-lg font-black tracking-tight mb-4">Simulate Strategy {strategyId} Performance</div>
                    <div className="flex items-center gap-2 text-primary-400 font-bold text-sm">
                       Access Simulator
                       <svg className="w-4 h-4 transition-transform group-hover:translate-x-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" /></svg>
                    </div>
                 </Link>
              </div>
           </div>
        </div>

        {/* Footer Navigation */}
        <div className="mt-12 flex justify-between items-center">
            <Link to="/strategies" className="text-sm font-bold text-slate-500 hover:text-primary-600 transition-colors flex items-center gap-2 border-b border-transparent hover:border-primary-600 pb-1">
               <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>
               Back to Research Index
            </Link>
        </div>
      </div>
    </div>
  );
}

export default StrategyHelp;
