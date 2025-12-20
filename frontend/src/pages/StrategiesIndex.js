import { Link } from 'react-router-dom';
import Header from '../components/Header';

/**
 * StrategiesIndex - Overview page listing all available trading strategies
 */

const strategies = [
  {
    id: 1,
    name: 'Balanced Analysis',
    slug: 'balanced',
    shortDesc: 'Equal weight to all 12 indicators',
    fullDesc: 'A comprehensive approach that weighs all technical indicators equally. Perfect for beginners and general market scanning when conditions are unclear.',
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
  blue: 'bg-blue-50 border-blue-200 hover:border-blue-400',
  green: 'bg-green-50 border-green-200 hover:border-green-400',
  purple: 'bg-purple-50 border-purple-200 hover:border-purple-400',
  orange: 'bg-orange-50 border-orange-200 hover:border-orange-400',
  red: 'bg-red-50 border-red-200 hover:border-red-400'
};

const badgeColors = {
  blue: 'bg-blue-100 text-blue-800',
  green: 'bg-green-100 text-green-800',
  purple: 'bg-purple-100 text-purple-800',
  orange: 'bg-orange-100 text-orange-800',
  red: 'bg-red-100 text-red-800'
};

function StrategiesIndex() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      
      {/* Hero Section */}
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white py-12">
        <div className="max-w-6xl mx-auto px-6">
          <h1 className="text-4xl font-bold mb-4">Trading Strategies</h1>
          <p className="text-xl text-indigo-100 max-w-3xl">
            Choose the right strategy for your trading style and market conditions. 
            Each strategy uses different indicator weights and risk parameters.
          </p>
        </div>
      </div>

      {/* Quick Comparison */}
      <div className="max-w-6xl mx-auto px-6 -mt-8">
        <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">📊 Quick Comparison</h2>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-3 px-4 font-medium text-gray-600">Strategy</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600">Target</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600">Stop Loss</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600">Holding</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600">Risk Level</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-600">Best For</th>
                </tr>
              </thead>
              <tbody>
                {strategies.map((strategy) => (
                  <tr key={strategy.id} className="border-b hover:bg-gray-50">
                    <td className="py-3 px-4 font-medium">
                      <span className="mr-2">{strategy.icon}</span>
                      {strategy.name}
                    </td>
                    <td className="py-3 px-4 text-green-600 font-medium">{strategy.targetPct}%</td>
                    <td className="py-3 px-4 text-red-600 font-medium">{strategy.stopLossPct}%</td>
                    <td className="py-3 px-4 text-gray-600">{strategy.holdingPeriod}</td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        strategy.riskLevel === 'High' ? 'bg-red-100 text-red-700' :
                        strategy.riskLevel === 'Medium-High' ? 'bg-orange-100 text-orange-700' :
                        'bg-yellow-100 text-yellow-700'
                      }`}>
                        {strategy.riskLevel}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-gray-600">{strategy.bestFor[0]}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Strategy Cards */}
      <div className="max-w-6xl mx-auto px-6 pb-12">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {strategies.map((strategy) => (
            <Link
              key={strategy.id}
              to={`/strategies/${strategy.slug}`}
              className={`block rounded-xl border-2 p-6 transition-all duration-200 ${colorClasses[strategy.color]} hover:shadow-lg hover:-translate-y-1`}
            >
              <div className="flex items-start justify-between mb-4">
                <span className="text-4xl">{strategy.icon}</span>
                <span className={`px-3 py-1 rounded-full text-xs font-semibold ${badgeColors[strategy.color]}`}>
                  Strategy {strategy.id}
                </span>
              </div>
              
              <h3 className="text-xl font-bold text-gray-800 mb-2">{strategy.name}</h3>
              <p className="text-gray-600 mb-4">{strategy.fullDesc}</p>
              
              {/* Key Metrics */}
              <div className="grid grid-cols-3 gap-2 mb-4">
                <div className="text-center p-2 bg-white rounded-lg">
                  <div className="text-green-600 font-bold">{strategy.targetPct}%</div>
                  <div className="text-xs text-gray-500">Target</div>
                </div>
                <div className="text-center p-2 bg-white rounded-lg">
                  <div className="text-red-600 font-bold">{strategy.stopLossPct}%</div>
                  <div className="text-xs text-gray-500">Stop Loss</div>
                </div>
                <div className="text-center p-2 bg-white rounded-lg">
                  <div className="text-blue-600 font-bold text-sm">{strategy.holdingPeriod.split(' ')[0]}</div>
                  <div className="text-xs text-gray-500">Weeks</div>
                </div>
              </div>

              {/* Best For Tags */}
              <div className="flex flex-wrap gap-1">
                {strategy.bestFor.map((item, idx) => (
                  <span key={idx} className="px-2 py-1 bg-white/50 rounded text-xs text-gray-600">
                    {item}
                  </span>
                ))}
              </div>

              <div className="mt-4 text-sm font-medium text-gray-700 flex items-center gap-1">
                Learn more <span className="text-lg">→</span>
              </div>
            </Link>
          ))}
        </div>

        {/* Help Section */}
        <div className="mt-12 bg-white rounded-xl shadow-sm border p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-4">🤔 Which Strategy Should I Use?</h2>
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <h3 className="font-semibold text-gray-700 mb-2">For Beginners</h3>
              <p className="text-gray-600 text-sm mb-3">
                Start with <strong>Strategy 1 (Balanced)</strong>. It gives equal weight to all indicators, 
                helping you understand how different signals work together without bias.
              </p>
            </div>
            <div>
              <h3 className="font-semibold text-gray-700 mb-2">For Trending Markets</h3>
              <p className="text-gray-600 text-sm mb-3">
                Use <strong>Strategy 2 (Trend Following)</strong> when stocks are making clear directional moves. 
                It ignores oscillator noise that would exit too early.
              </p>
            </div>
            <div>
              <h3 className="font-semibold text-gray-700 mb-2">For Sideways Markets</h3>
              <p className="text-gray-600 text-sm mb-3">
                Choose <strong>Strategy 3 (Mean Reversion)</strong> when stocks are range-bound. 
                Buy near support, sell near resistance.
              </p>
            </div>
            <div>
              <h3 className="font-semibold text-gray-700 mb-2">For Active Traders</h3>
              <p className="text-gray-600 text-sm mb-3">
                Try <strong>Strategy 5 (Weekly 4% Target)</strong>. It has our most refined filters 
                for high-probability swing trades with clear targets.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default StrategiesIndex;
