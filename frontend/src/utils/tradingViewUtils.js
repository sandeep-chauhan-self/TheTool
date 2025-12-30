/**
 * TradingView URL utility functions
 * Converts stock symbols to TradingView chart URLs
 */

/**
 * Extract base symbol from Yahoo Finance ticker
 * Removes exchange suffix (.NS, .BO, etc.)
 * 
 * @param {string} ticker - Yahoo Finance ticker (e.g., "RELIANCE.NS")
 * @returns {string} - Base symbol (e.g., "RELIANCE")
 */
export const extractBaseSymbol = (ticker) => {
  if (!ticker) return '';
  // Remove exchange suffix (.NS, .BO, etc.)
  return ticker.split('.')[0].toUpperCase();
};

/**
 * Generate TradingView URL for an NSE stock
 * 
 * @param {string} ticker - Yahoo Finance ticker or base symbol
 * @returns {string} - TradingView URL
 */
export const getTradingViewUrl = (ticker) => {
  const baseSymbol = extractBaseSymbol(ticker);
  return `https://www.screener.in/company/${baseSymbol}/consolidated/`;
};

/**
 * TradingView external link icon component (inline SVG)
 * Small icon that indicates external link
 */
export const TradingViewIcon = () => (
  <svg 
    xmlns="http://www.w3.org/2000/svg" 
    viewBox="0 0 20 20" 
    fill="currentColor" 
    className="w-3 h-3 ml-1 inline-block opacity-0 group-hover:opacity-70 transition-opacity"
  >
    <path 
      fillRule="evenodd" 
      d="M4.25 5.5a.75.75 0 00-.75.75v8.5c0 .414.336.75.75.75h8.5a.75.75 0 00.75-.75v-4a.75.75 0 011.5 0v4A2.25 2.25 0 0112.75 17h-8.5A2.25 2.25 0 012 14.75v-8.5A2.25 2.25 0 014.25 4h5a.75.75 0 010 1.5h-5z" 
      clipRule="evenodd" 
    />
    <path 
      fillRule="evenodd" 
      d="M6.194 12.753a.75.75 0 001.06.053L16.5 4.44v2.81a.75.75 0 001.5 0v-4.5a.75.75 0 00-.75-.75h-4.5a.75.75 0 000 1.5h2.553l-9.056 8.194a.75.75 0 00-.053 1.06z" 
      clipRule="evenodd" 
    />
  </svg>
);

/**
 * Styled TradingView link component
 * Opens in new tab, hover underline styling
 * 
 * @param {Object} props
 * @param {string} props.ticker - Yahoo Finance ticker or base symbol
 * @param {string} props.displayText - Text to display (optional, defaults to ticker)
 * @param {string} props.className - Additional CSS classes
 */
export const TradingViewLink = ({ ticker, displayText, className = '' }) => {
  if (!ticker) return null;
  
  const url = getTradingViewUrl(ticker);
  const text = displayText || ticker;
  
  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      className={`group hover:underline hover:text-blue-600 transition-colors ${className}`}
      title={`View ${extractBaseSymbol(ticker)} on TradingView`}
    >
      {text}
      <TradingViewIcon />
    </a>
  );
};

export default {
  extractBaseSymbol,
  getTradingViewUrl,
  TradingViewIcon,
  TradingViewLink
};
