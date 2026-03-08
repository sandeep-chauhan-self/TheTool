import { Link } from 'react-router-dom';
import Breadcrumbs from '../components/Breadcrumbs';
import Header from '../components/Header';
import NavigationBar from '../components/NavigationBar';

/**
 * StrategiesIndex - Overview page listing all available trading strategies
 */

const strategies = [
  {
    id: 1,
    name: 'Balanced Analysis',
    slug: 'balanced',
    shortDesc: 'Equal weight to all 12 indicators',
    fullDesc: 'A comprehensive approach that weighs all technical indicators equally. Perfect for general market scanning when conditions are unclear.',
    icon: '⚖️',
    color: 'blue',
    bestFor: ['General market scanning', 'Beginners', 'Unclear market conditions'],
    riskLevel: 'Medium',
    targetPct: 4,
    stopLossPct: 2,
    holdingPeriod: '2-4 weeks'
  },
  {
    id: 2,
    name: 'Trend Following',
    slug: 'trend-following',
    shortDesc: 'Ride strong market trends',
    fullDesc: 'Designed for trending markets. Emphasizes MACD, ADX, and EMA to capture sustained directional moves while filtering out noise.',
    icon: '📈',
    color: 'green',
    bestFor: ['Trending markets', 'Breakout trades', 'Swing trading'],
    riskLevel: 'Medium-High',
    targetPct: 6,
    stopLossPct: 2.5,
    holdingPeriod: '3-5 weeks'
  },
  {
    id: 3,
    name: 'Mean Reversion',
    slug: 'mean-reversion',
    shortDesc: 'Buy oversold, sell overbought',
    fullDesc: 'Focuses on oscillators (RSI, Bollinger, Stochastic) to identify overbought/oversold conditions. Best for range-bound markets.',
    icon: '🔄',
    color: 'purple',
    bestFor: ['Sideways markets', 'Range-bound stocks', 'Counter-trend trades'],
    riskLevel: 'Medium',
    targetPct: 2.5,
    stopLossPct: 1.5,
    holdingPeriod: '1-2 weeks'
  },
  {
    id: 4,
    name: 'Momentum Breakout',
    slug: 'momentum-breakout',
    shortDesc: 'Volume-confirmed breakouts',
    fullDesc: 'Catches breakouts with institutional backing. Heavy focus on OBV, CMF, and volume analysis to confirm strong moves.',
    icon: '🚀',
    color: 'orange',
    bestFor: ['Breakout trades', 'High volume moves', 'Earnings plays'],
    riskLevel: 'High',
    targetPct: 5,
    stopLossPct: 3,
    holdingPeriod: '1-2 weeks'
  },
  {
    id: 5,
    name: 'Weekly 4% Target',
    slug: 'weekly-target',
    shortDesc: 'Optimized swing trading',
    fullDesc: 'Our most refined strategy with intelligent filters. Targets 4% gains with smart stop-loss, trend filters, and momentum validation.',
    icon: '🎯',
    color: 'red',
    bestFor: ['Swing trading', 'Quick profits', 'Active traders'],
    riskLevel: 'Medium-High',
    targetPct: 4,
    stopLossPct: 3,
    holdingPeriod: '1-3 weeks'
  }
];

const colorClasses = {
  blue: 'bg-primary-50 border-primary-200 hover:border-primary-400',
  green: 'bg-success-50 border-success-200 hover:border-success-400',
  purple: 'bg-accent-50 border-accent-200 hover:border-accent-400',
  orange: 'bg-warning-50 border-warning-200 hover:border-warning-400',
  red: 'bg-danger-50 border-danger-200 hover:border-danger-400'
};

const badgeColors = {
  blue: 'bg-primary-100 text-primary-800',
  green: 'bg-success-100 text-success-800',
  purple: 'bg-accent-100 text-accent-800',
  orange: 'bg-warning-100 text-warning-800',
  red: 'bg-danger-100 text-danger-800'
};

function StrategiesIndex() {
  return (
    <div className="min-h-screen mesh-bg pb-20">
      <NavigationBar />
      <Header title="Trading Strategies" subtitle="Choose the right model for your market environment" />
      
      <div className="max-w-7xl mx-auto px-4">
        <Breadcrumbs items={[{ label: 'Dashboard', path: '/' }, { label: 'Strategies', path: null }]} />

        {/* Quick Comparison Table */}
        <div className="glass-card mb-12 mt-8 overflow-hidden">
          <div className="px-8 py-5 border-b border-slate-100 flex justify-between items-center bg-slate-50/30">
            <h2 className="text-lg font-bold text-slate-900">📊 Comparative Matrix</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-white border-b border-slate-100">
                <tr>
                  <th className="px-8 py-4 text-left font-bold text-slate-400 uppercase tracking-wider text-xs">Strategy</th>
                  <th className="px-8 py-4 text-left font-bold text-slate-400 uppercase tracking-wider text-xs">Target</th>
                  <th className="px-8 py-4 text-left font-bold text-slate-400 uppercase tracking-wider text-xs">Stop Loss</th>
                  <th className="px-8 py-4 text-left font-bold text-slate-400 uppercase tracking-wider text-xs">Horizon</th>
                  <th className="px-8 py-4 text-left font-bold text-slate-400 uppercase tracking-wider text-xs">Risk Profile</th>
                  <th className="px-8 py-4 text-left font-bold text-slate-400 uppercase tracking-wider text-xs">Primary Focus</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {strategies.map((strategy) => (
                  <tr key={strategy.id} className="hover:bg-slate-50/50 transition-colors">
                    <td className="px-8 py-4 font-bold text-slate-800 flex items-center gap-3">
                      <span className="text-xl">{strategy.icon}</span>
                      {strategy.name}
                    </td>
                    <td className="px-8 py-4 font-bold text-success-600">{strategy.targetPct}%</td>
                    <td className="px-8 py-4 font-bold text-danger-600">{strategy.stopLossPct}%</td>
                    <td className="px-8 py-4 font-medium text-slate-600">{strategy.holdingPeriod}</td>
                    <td className="px-8 py-4">
                      <span className={`inline-flex px-2.5 py-1 rounded-md text-[10px] font-bold uppercase tracking-wider border ${
                        strategy.riskLevel.includes('High') ? 'bg-danger-50 text-danger-700 border-danger-100' : 'bg-success-50 text-success-700 border-success-100'
                      }`}>
                        {strategy.riskLevel}
                      </span>
                    </td>
                    <td className="px-8 py-4 text-slate-500 font-medium">{strategy.bestFor[0]}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Strategy Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {strategies.map((strategy) => (
            <Link
              key={strategy.id}
              to={`/strategies/${strategy.slug}`}
              className={`glass-card p-8 transition-all hover:shadow-xl hover:-translate-y-1 block relative group ${colorClasses[strategy.color]}`}
            >
              <div className="flex items-center justify-between mb-6">
                <span className="text-5xl drop-shadow-sm">{strategy.icon}</span>
                <span className={`px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest ${badgeColors[strategy.color]}`}>
                  Model {strategy.id}
                </span>
              </div>
              
              <h3 className="text-2xl font-black text-slate-900 mb-3 tracking-tight">{strategy.name}</h3>
              <p className="text-slate-600 mb-8 leading-relaxed font-medium">{strategy.fullDesc}</p>
              
              <div className="grid grid-cols-3 gap-4 mb-8">
                <div className="px-4 py-2 bg-white rounded-xl border border-slate-100 shadow-sm">
                  <div className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-1">Gain</div>
                  <div className="text-lg font-black text-success-600">{strategy.targetPct}%</div>
                </div>
                <div className="px-4 py-2 bg-white rounded-xl border border-slate-100 shadow-sm">
                  <div className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-1">Stop</div>
                  <div className="text-lg font-black text-danger-600">{strategy.stopLossPct}%</div>
                </div>
                <div className="px-4 py-2 bg-white rounded-xl border border-slate-100 shadow-sm">
                  <div className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-1">Wait</div>
                  <div className="text-lg font-black text-primary-600">{strategy.holdingPeriod.split(' ')[0]}W</div>
                </div>
              </div>

              <div className="pt-6 border-t border-slate-100 flex items-center justify-between">
                <span className="text-sm font-bold text-slate-800 group-hover:text-primary-600 transition-colors flex items-center gap-2">
                  Engine Architecture Details
                  <svg className="w-4 h-4 transition-transform group-hover:translate-x-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" /></svg>
                </span>
              </div>
            </Link>
          ))}
        </div>

        {/* Advisor Section */}
        <div className="mt-16 glass-card p-10 bg-slate-900 text-white border-none shadow-2xl relative overflow-hidden">
           <div className="absolute top-0 right-0 w-64 h-64 bg-primary-600/20 blur-[100px] rounded-full -mr-32 -mt-32"></div>
           <div className="relative z-10">
              <h2 className="text-2xl font-black mb-8 tracking-tight">🧠 Algorithmic Selection Advisor</h2>
              <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
                <div>
                  <h3 className="font-bold text-primary-400 text-xs uppercase tracking-widest mb-3">Beginners / Safe-Scan</h3>
                  <p className="text-sm text-slate-300 leading-relaxed">
                    <strong>Balanced Analysis</strong> is your anchor. It normalizes all 12 indicator inputs to find high-conviction crossovers.
                  </p>
                </div>
                <div>
                  <h3 className="font-bold text-success-400 text-xs uppercase tracking-widest mb-3">Expansionary Phases</h3>
                  <p className="text-sm text-slate-300 leading-relaxed">
                    <strong>Trend Following</strong> filters out oscillation noise to let your winners run during macro bull cycles.
                  </p>
                </div>
                <div>
                  <h3 className="font-bold text-accent-400 text-xs uppercase tracking-widest mb-3">Range-Bound Consolation</h3>
                  <p className="text-sm text-slate-300 leading-relaxed">
                    <strong>Mean Reversion</strong> excels in sideways drift. It buys the blood near support and exits near resistance clusters.
                  </p>
                </div>
                <div>
                  <h3 className="font-bold text-danger-400 text-xs uppercase tracking-widest mb-3">High-Velocity Swings</h3>
                  <p className="text-sm text-slate-300 leading-relaxed">
                    <strong>Weekly 4% Target</strong> is our most aggressive engine, verified to seek rapid liquidity exits.
                  </p>
                </div>
              </div>
           </div>
        </div>
      </div>
    </div>
  );
}

export default StrategiesIndex;
