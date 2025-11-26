import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { analyzeStocks, downloadReport, getReport, getStockHistory } from '../api/api';
import Header from '../components/Header';

function Results() {
  const { ticker } = useParams();
  const navigate = useNavigate();
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [reanalyzing, setReanalyzing] = useState(false);
  const [history, setHistory] = useState([]);
  const [selectedHistoryIndex, setSelectedHistoryIndex] = useState(0);

  useEffect(() => {
    loadReport();
    loadHistory();
  }, [ticker]);

  const loadReport = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getReport(ticker);
      // Flatten the nested structure: extract analysis fields to top level
      if (data && data.analysis) {
        setReport({
          ...data,
          verdict: data.analysis.verdict,
          score: data.analysis.score,
          entry: data.analysis.entry,
          stop: data.analysis.stop_loss,  // Note: API returns stop_loss, but UI expects stop
          target: data.analysis.target
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
      // Load history but don't override report - history is just for the dropdown
      const historyData = await getStockHistory(ticker);
      if (historyData && historyData.history && historyData.history.length > 0) {
        setHistory(historyData.history);
      }
    } catch (err) {
      console.log('No history available, will use report data');
      // Fallback - history is optional
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
      stop: selectedAnalysis.stop_loss,  // Map stop_loss to stop for UI
      target: selectedAnalysis.target,
      indicators: selectedAnalysis.indicators || [],
      created_at: selectedAnalysis.created_at
    });
  };

  const handleDownload = async () => {
    try {
      await downloadReport(ticker);
    } catch (error) {
      console.error('Failed to download report:', error);
      alert('Failed to download report');
    }
  };

  const handleReanalyze = async () => {
    try {
      setReanalyzing(true);
      await analyzeStocks([ticker]);
      
      // Wait a bit and reload
      setTimeout(() => {
        loadReport();
        setReanalyzing(false);
      }, 3000);
    } catch (error) {
      setReanalyzing(false);
      console.error('Failed to reanalyze:', error);
      alert('Failed to reanalyze');
    }
  };

  const getVerdictColor = (verdict) => {
    switch (verdict) {
      case 'Strong Buy':
        return 'text-green-700 bg-green-100';
      case 'Buy':
        return 'text-green-600 bg-green-50';
      case 'Strong Sell':
        return 'text-red-700 bg-red-100';
      case 'Sell':
        return 'text-red-600 bg-red-50';
      case 'Neutral':
        return 'text-gray-600 bg-gray-100';
      default:
        return 'text-gray-400 bg-gray-50';
    }
  };

  const getVoteDisplay = (vote) => {
    if (vote === 1) return 'Buy';
    if (vote === -1) return 'Sell';
    return 'Neutral';
  };

  const getVoteColor = (vote) => {
    if (vote === 1) return 'text-green-600 font-bold';
    if (vote === -1) return 'text-red-600 font-bold';
    return 'text-gray-600';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100">
        <Header title="Analysis Results" />
        <div className="max-w-7xl mx-auto px-4 py-8">
          <div className="text-center py-12">Loading...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-100">
        <Header title="Analysis Results" />
        <div className="max-w-7xl mx-auto px-4 py-8">
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
          <button
            onClick={() => navigate('/')}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            &lt; Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      <Header title={`Analysis Results: ${ticker}`} />

      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Historical Analysis Dropdown */}
        {history.length > 1 && (
          <div className="mb-6 bg-white rounded-lg shadow-md p-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Analysis History ({history.length} available)
            </label>
            <select
              value={selectedHistoryIndex}
              onChange={(e) => handleHistoryChange(parseInt(e.target.value))}
              className="w-full md:w-auto px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {history.map((item, index) => (
                <option key={index} value={index}>
                  {index === 0 ? 'Latest - ' : ''}{new Date(item.created_at).toLocaleString('en-IN', {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                  })} - Score: {item.score} - {item.verdict}
                </option>
              ))}
            </select>
            {selectedHistoryIndex === 0 && (
              <p className="text-xs text-green-600 mt-1">[Showing Latest Analysis]</p>
            )}
            {selectedHistoryIndex > 0 && (
              <p className="text-xs text-gray-500 mt-1">
                [Historical Analysis from {new Date(history[selectedHistoryIndex].created_at || history[selectedHistoryIndex].analyzed_at).toLocaleDateString()}]
              </p>
            )}
          </div>
        )}
        
        {/* Demo Data Warning Banner */}
        {report.is_demo_data && (
          <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-6">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-yellow-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-yellow-800">
                  Demo Data Used - Network Issue Detected
                </h3>
                <div className="mt-2 text-sm text-yellow-700">
                  <p>
                    This analysis uses <strong>simulated demo data</strong> because real market data could not be fetched 
                    (Yahoo Finance may be blocked by your network). The analysis patterns and calculations are accurate, 
                    but prices and signals are not from real market data.
                  </p>
                  <p className="mt-2">
                    <strong>[WARNING] Do not use for actual trading decisions.</strong> To get real data:
                  </p>
                  <ul className="list-disc ml-5 mt-1">
                    <li>Check your network/firewall settings</li>
                    <li>Try from a different network</li>
                    <li>Contact admin to setup Alpha Vantage API</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Data Source Badge */}
        {report.data_source && !report.is_demo_data && (
          <div className="mb-4">
            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
              [VERIFIED] Real Market Data ({report.data_source === 'yahoo_finance' ? 'Yahoo Finance' : 
                                   report.data_source === 'alpha_vantage' ? 'Alpha Vantage' : 
                                   report.data_source})
            </span>
          </div>
        )}

        {/* Verdict Summary */}
        <div className="bg-white rounded shadow p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold">Final Verdict</h2>
            <span className={`px-4 py-2 rounded font-bold text-xl ${getVerdictColor(report.verdict || 'Neutral')}`}>
              {report.verdict || 'No verdict'}
            </span>
          </div>
          
          <div className="flex items-center gap-2 mb-6">
            <span className="text-gray-600">Score:</span>
            <span className="font-bold text-xl">
              {report.score != null ? `${report.score > 0 ? '+' : ''}${report.score}` : 'N/A'}
            </span>
          </div>

          <div className="grid grid-cols-3 gap-4 p-4 bg-gray-50 rounded">
            <div>
              <div className="text-sm text-gray-600">Entry Price</div>
              <div className="text-xl font-bold text-blue-600">
                {report.entry != null ? `Rs. ${Number(report.entry).toFixed(2)}` : 'N/A'}
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-600">Stop Loss</div>
              <div className="text-xl font-bold text-red-600">
                {report.stop != null ? `Rs. ${Number(report.stop).toFixed(2)}` : 'N/A'}
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-600">Target</div>
              <div className="text-xl font-bold text-green-600">
                {report.target != null ? `Rs. ${Number(report.target).toFixed(2)}` : 'N/A'}
              </div>
            </div>
          </div>
        </div>

        {/* Indicator Summary */}
        <div className="bg-white rounded shadow overflow-hidden mb-6">
          <div className="px-6 py-4 bg-gray-200">
            <h2 className="text-xl font-bold">Indicator Summary</h2>
          </div>

          <table className="min-w-full">
            <thead className="bg-gray-100">
              <tr>
                <th className="px-6 py-3 text-left">Indicator</th>
                <th className="px-6 py-3 text-left">Vote</th>
                <th className="px-6 py-3 text-left">Confidence</th>
                <th className="px-6 py-3 text-left">Category</th>
                <th className="px-6 py-3 text-left">Value</th>
              </tr>
            </thead>
            <tbody>
              {report.indicators && Array.isArray(report.indicators) && report.indicators.length > 0 ? (
                report.indicators.map((indicator, index) => (
                  <tr key={index} className="border-t hover:bg-gray-50">
                    <td className="px-6 py-3 font-medium">{indicator.name || 'N/A'}</td>
                    <td className={`px-6 py-3 font-bold ${getVoteColor(indicator.vote)}`}>
                      {getVoteDisplay(indicator.vote)}
                    </td>
                    <td className="px-6 py-3">
                      {indicator.confidence != null ? `${(indicator.confidence * 100).toFixed(0)}%` : 'N/A'}
                    </td>
                    <td className="px-6 py-3 capitalize">{indicator.category || 'N/A'}</td>
                    <td className="px-6 py-3 text-gray-600">{indicator.value || 'N/A'}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="5" className="px-6 py-3 text-center text-gray-500">
                    No indicator data available
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-4">
          <button
            onClick={handleDownload}
            className="px-6 py-3 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Download Excel Report
          </button>
          <button
            onClick={handleReanalyze}
            disabled={reanalyzing}
            className="px-6 py-3 bg-green-600 text-white rounded hover:bg-green-700 disabled:bg-gray-400"
          >
            {reanalyzing ? 'Reanalyzing...' : 'Re-Analyze'}
          </button>
          <button
            onClick={() => navigate('/')}
            className="px-6 py-3 bg-gray-600 text-white rounded hover:bg-gray-700"
          >
            &lt; Back
          </button>
        </div>

        {(report.analyzed_at || report.created_at) && (
          <div className="mt-6 text-sm text-gray-500">
            Last analyzed: {new Date(report.analyzed_at || report.created_at).toLocaleString()}
          </div>
        )}
      </div>
    </div>
  );
}

export default Results;
