import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import { getStrategyHelp, getStrategy } from '../api/api';

/**
 * StrategyHelp - Detailed help page for a specific strategy
 * 
 * Opens in a new tab when user clicks "Learn more" on strategy selector
 * Displays markdown help content from backend
 */
function StrategyHelp() {
  const { id } = useParams();
  const [strategy, setStrategy] = useState(null);
  const [helpContent, setHelpContent] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Fetch strategy details and help content in parallel
        const [strategyData, helpData] = await Promise.all([
          getStrategy(id),
          getStrategyHelp(id)
        ]);
        
        setStrategy(strategyData.strategy);
        setHelpContent(helpData.help_content || 'No help content available.');
      } catch (err) {
        console.error('Failed to fetch strategy help:', err);
        setError(err.response?.data?.message || 'Failed to load strategy help');
      } finally {
        setLoading(false);
      }
    };

    if (id) {
      fetchData();
    }
  }, [id]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading strategy documentation...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md">
          <div className="text-red-500 text-5xl mb-4">⚠️</div>
          <h1 className="text-xl font-bold text-gray-800 mb-2">Strategy Not Found</h1>
          <p className="text-gray-600 mb-4">{error}</p>
          <Link 
            to="/" 
            className="text-blue-600 hover:text-blue-800 hover:underline"
          >
            ← Back to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-4xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <Link 
                to="/" 
                className="text-sm text-gray-500 hover:text-gray-700 flex items-center gap-1"
              >
                ← Back to Dashboard
              </Link>
              <h1 className="text-2xl font-bold text-gray-800 mt-1">
                {strategy?.name || `Strategy ${id}`}
              </h1>
              {strategy?.description && (
                <p className="text-gray-600 mt-1">{strategy.description}</p>
              )}
            </div>
            <div className="text-sm text-gray-500">
              Strategy ID: {id}
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-4xl mx-auto px-6 py-8">
        <div className="bg-white rounded-lg shadow-sm border p-8">
          {/* Markdown content with styling */}
          <article className="prose prose-slate max-w-none">
            <ReactMarkdown
              components={{
                // Style tables
                table: ({ children }) => (
                  <div className="overflow-x-auto my-4">
                    <table className="min-w-full divide-y divide-gray-200 border">
                      {children}
                    </table>
                  </div>
                ),
                thead: ({ children }) => (
                  <thead className="bg-gray-50">{children}</thead>
                ),
                th: ({ children }) => (
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-b">
                    {children}
                  </th>
                ),
                td: ({ children }) => (
                  <td className="px-4 py-3 text-sm text-gray-600 border-b border-r last:border-r-0">
                    {children}
                  </td>
                ),
                // Style code blocks
                code: ({ inline, children }) => (
                  inline 
                    ? <code className="bg-gray-100 px-1 py-0.5 rounded text-sm text-red-600">{children}</code>
                    : <code className="block bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto">{children}</code>
                ),
                // Style headings
                h1: ({ children }) => (
                  <h1 className="text-3xl font-bold text-gray-800 mb-4 pb-2 border-b">{children}</h1>
                ),
                h2: ({ children }) => (
                  <h2 className="text-2xl font-semibold text-gray-800 mt-8 mb-4">{children}</h2>
                ),
                h3: ({ children }) => (
                  <h3 className="text-xl font-medium text-gray-700 mt-6 mb-3">{children}</h3>
                ),
                // Style lists
                ul: ({ children }) => (
                  <ul className="list-disc list-inside space-y-1 text-gray-600">{children}</ul>
                ),
                ol: ({ children }) => (
                  <ol className="list-decimal list-inside space-y-1 text-gray-600">{children}</ol>
                ),
                // Style blockquotes
                blockquote: ({ children }) => (
                  <blockquote className="border-l-4 border-blue-500 pl-4 py-2 my-4 bg-blue-50 text-gray-700 italic">
                    {children}
                  </blockquote>
                ),
              }}
            >
              {helpContent}
            </ReactMarkdown>
          </article>
        </div>

        {/* Quick Actions */}
        <div className="mt-6 flex justify-between items-center">
          <Link 
            to="/" 
            className="text-blue-600 hover:text-blue-800 hover:underline flex items-center gap-1"
          >
            ← Return to Dashboard
          </Link>
          <div className="text-sm text-gray-500">
            Need help? Strategy documentation is automatically updated with the latest insights.
          </div>
        </div>
      </div>
    </div>
  );
}

export default StrategyHelp;
