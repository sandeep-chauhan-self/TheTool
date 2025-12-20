import { useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { Link, useParams } from 'react-router-dom';
import { getStrategy, getStrategyHelp } from '../api/api';
import Header from '../components/Header';

/**
 * StrategyHelp - Detailed help page for a specific strategy
 * 
 * Supports both numeric IDs (/strategies/5) and slugs (/strategies/weekly-target)
 */

// Slug to ID mapping
const slugToId = {
  'balanced': 1,
  'trend-following': 2,
  'mean-reversion': 3,
  'momentum-breakout': 4,
  'weekly-target': 5,
  // Also support numeric strings
  '1': 1,
  '2': 2,
  '3': 3,
  '4': 4,
  '5': 5
};

const strategyMeta = {
  1: { name: 'Balanced Analysis', icon: '⚖️', color: 'blue' },
  2: { name: 'Trend Following', icon: '📈', color: 'green' },
  3: { name: 'Mean Reversion', icon: '🔄', color: 'purple' },
  4: { name: 'Momentum Breakout', icon: '🚀', color: 'orange' },
  5: { name: 'Weekly 4% Target', icon: '🎯', color: 'red' }
};

function StrategyHelp() {
  const { id: urlParam } = useParams();
  const [strategy, setStrategy] = useState(null);
  const [helpContent, setHelpContent] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Convert slug or numeric string to ID
  const strategyId = slugToId[urlParam] || parseInt(urlParam);

  useEffect(() => {
    const fetchData = async () => {
      if (!strategyId || strategyId < 1 || strategyId > 5) {
        setError('Invalid strategy. Please select a valid strategy (1-5).');
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);
        
        // Fetch strategy details and help content in parallel
        const [strategyData, helpData] = await Promise.all([
          getStrategy(strategyId),
          getStrategyHelp(strategyId)
        ]);
        
        setStrategy(strategyData.strategy);
        setHelpContent(helpData.help_content || 'No help content available.');
      } catch (err) {
        console.error('Failed to fetch strategy help:', err);
        setError(err.response?.data?.message || 'Failed to load strategy documentation. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [strategyId]);

  const meta = strategyMeta[strategyId] || {};

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <div className="flex items-center justify-center py-20">
          <div className="text-center">
            <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-gray-600">Loading strategy documentation...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <div className="flex items-center justify-center py-20">
          <div className="text-center max-w-md">
            <div className="text-red-500 text-5xl mb-4">⚠️</div>
            <h1 className="text-xl font-bold text-gray-800 mb-2">Strategy Not Found</h1>
            <p className="text-gray-600 mb-4">{error}</p>
            <Link 
              to="/strategies" 
              className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
            >
              ← View All Strategies
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      
      {/* Hero Header */}
      <div className={`bg-gradient-to-r ${
        meta.color === 'blue' ? 'from-blue-600 to-blue-700' :
        meta.color === 'green' ? 'from-green-600 to-green-700' :
        meta.color === 'purple' ? 'from-purple-600 to-purple-700' :
        meta.color === 'orange' ? 'from-orange-500 to-orange-600' :
        'from-red-600 to-red-700'
      } text-white py-8`}>
        <div className="max-w-4xl mx-auto px-6">
          <Link 
            to="/strategies" 
            className="text-sm text-white/80 hover:text-white flex items-center gap-1 mb-4"
          >
            ← All Strategies
          </Link>
          <div className="flex items-center gap-4">
            <span className="text-5xl">{meta.icon}</span>
            <div>
              <div className="text-sm text-white/70 mb-1">Strategy {strategyId}</div>
              <h1 className="text-3xl font-bold">
                {strategy?.name || meta.name || `Strategy ${strategyId}`}
              </h1>
              {strategy?.description && (
                <p className="text-white/90 mt-2 max-w-xl">{strategy.description}</p>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Quick Navigation */}
      <div className="bg-white border-b shadow-sm sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-6 py-3">
          <div className="flex items-center justify-between">
            <div className="flex gap-2">
              {[1, 2, 3, 4, 5].map((id) => (
                <Link
                  key={id}
                  to={`/strategies/${Object.keys(slugToId).find(key => slugToId[key] === id && isNaN(key))}`}
                  className={`px-3 py-1.5 rounded-full text-sm font-medium transition ${
                    id === strategyId
                      ? 'bg-gray-800 text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {strategyMeta[id]?.icon} {id}
                </Link>
              ))}
            </div>
            <Link 
              to={`/backtest?strategy_id=${strategyId}`}
              className="px-4 py-1.5 bg-purple-600 text-white rounded-full text-sm font-medium hover:bg-purple-700 transition"
            >
              📊 Backtest This Strategy
            </Link>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-4xl mx-auto px-6 py-8">
        <div className="bg-white rounded-xl shadow-sm border p-8">
          {/* Markdown content with styling */}
          <article className="prose prose-slate max-w-none prose-headings:scroll-mt-20">
            <ReactMarkdown
              components={{
                // Style tables
                table: ({ children }) => (
                  <div className="overflow-x-auto my-4">
                    <table className="min-w-full divide-y divide-gray-200 border rounded-lg overflow-hidden">
                      {children}
                    </table>
                  </div>
                ),
                thead: ({ children }) => (
                  <thead className="bg-gray-50">{children}</thead>
                ),
                th: ({ children }) => (
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider border-b">
                    {children}
                  </th>
                ),
                td: ({ children }) => (
                  <td className="px-4 py-3 text-sm text-gray-700 border-b border-r last:border-r-0">
                    {children}
                  </td>
                ),
                tr: ({ children }) => (
                  <tr className="hover:bg-gray-50 transition">{children}</tr>
                ),
                // Style code blocks
                code: ({ inline, children, className }) => {
                  if (inline) {
                    return <code className="bg-gray-100 px-1.5 py-0.5 rounded text-sm text-red-600 font-mono">{children}</code>;
                  }
                  return (
                    <code className="block bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto text-sm font-mono">
                      {children}
                    </code>
                  );
                },
                pre: ({ children }) => (
                  <pre className="bg-gray-900 rounded-lg overflow-x-auto my-4">{children}</pre>
                ),
                // Style headings
                h1: ({ children }) => (
                  <h1 className="text-3xl font-bold text-gray-800 mb-6 pb-3 border-b-2 border-gray-200">{children}</h1>
                ),
                h2: ({ children }) => (
                  <h2 className="text-2xl font-bold text-gray-800 mt-10 mb-4 pb-2 border-b border-gray-100">{children}</h2>
                ),
                h3: ({ children }) => (
                  <h3 className="text-xl font-semibold text-gray-700 mt-8 mb-3">{children}</h3>
                ),
                h4: ({ children }) => (
                  <h4 className="text-lg font-medium text-gray-700 mt-6 mb-2">{children}</h4>
                ),
                // Style lists
                ul: ({ children }) => (
                  <ul className="list-disc list-outside ml-5 space-y-2 text-gray-600 my-4">{children}</ul>
                ),
                ol: ({ children }) => (
                  <ol className="list-decimal list-outside ml-5 space-y-2 text-gray-600 my-4">{children}</ol>
                ),
                li: ({ children }) => (
                  <li className="text-gray-600 pl-1">{children}</li>
                ),
                // Style blockquotes
                blockquote: ({ children }) => (
                  <blockquote className="border-l-4 border-blue-500 pl-4 py-3 my-4 bg-blue-50 rounded-r-lg text-gray-700 italic">
                    {children}
                  </blockquote>
                ),
                // Style paragraphs
                p: ({ children }) => (
                  <p className="text-gray-600 leading-relaxed my-4">{children}</p>
                ),
                // Style strong/bold
                strong: ({ children }) => (
                  <strong className="font-semibold text-gray-800">{children}</strong>
                ),
                // Style links
                a: ({ children, href }) => (
                  <a href={href} className="text-blue-600 hover:text-blue-800 hover:underline">{children}</a>
                ),
                // Style horizontal rules
                hr: () => (
                  <hr className="my-8 border-gray-200" />
                ),
              }}
            >
              {helpContent}
            </ReactMarkdown>
          </article>
        </div>

        {/* Bottom Actions */}
        <div className="mt-8 flex flex-col sm:flex-row justify-between items-center gap-4 bg-white rounded-xl shadow-sm border p-6">
          <Link 
            to="/strategies" 
            className="text-gray-600 hover:text-gray-800 flex items-center gap-2"
          >
            ← Back to All Strategies
          </Link>
          <div className="flex gap-3">
            <Link 
              to={`/backtest?strategy_id=${strategyId}`}
              className="px-5 py-2.5 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 transition flex items-center gap-2"
            >
              📊 Run Backtest
            </Link>
            <Link 
              to="/"
              className="px-5 py-2.5 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 transition"
            >
              Start Analyzing
            </Link>
          </div>
        </div>

        {/* Related Strategies */}
        <div className="mt-8 bg-white rounded-xl shadow-sm border p-6">
          <h3 className="font-semibold text-gray-800 mb-4">Explore Other Strategies</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[1, 2, 3, 4, 5].filter(id => id !== strategyId).map((id) => (
              <Link
                key={id}
                to={`/strategies/${Object.keys(slugToId).find(key => slugToId[key] === id && isNaN(key))}`}
                className="flex items-center gap-2 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition"
              >
                <span className="text-2xl">{strategyMeta[id]?.icon}</span>
                <div>
                  <div className="text-sm font-medium text-gray-800">{strategyMeta[id]?.name}</div>
                  <div className="text-xs text-gray-500">Strategy {id}</div>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default StrategyHelp;
