import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';

const CommandPalette = ({ allStocks }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const inputRef = useRef(null);
  const navigate = useNavigate();

  // Keyboard shortcut listener
  useEffect(() => {
    const handleKeyDown = (e) => {
      // CMD+K (Mac) or CTRL+K (Win)
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setIsOpen((prev) => !prev);
      }
      if (e.key === 'Escape' && isOpen) {
        setIsOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen]);

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const filteredStocks = allStocks
    ? allStocks.filter(s => 
        s.ticker.toLowerCase().includes(searchTerm.toLowerCase()) || 
        (s.name && s.name.toLowerCase().includes(searchTerm.toLowerCase()))
      ).slice(0, 5) // limit results
    : [];

  const handleSelect = (ticker) => {
    setIsOpen(false);
    navigate(`/results/${ticker}`);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-32 bg-slate-900/40 backdrop-blur-sm animate-fade-in">
      <div className="bg-white/95 backdrop-blur-xl w-full max-w-lg rounded-2xl shadow-2xl border border-slate-200 overflow-hidden transform scale-100 transition-transform">
        <div className="flex items-center px-4 py-3 border-b border-slate-100">
          <svg className="w-5 h-5 text-slate-400 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            ref={inputRef}
            type="text"
            className="w-full bg-transparent border-none text-lg text-slate-800 focus:outline-none placeholder-slate-400"
            placeholder="Search stocks... (e.g. AAPL)"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <kbd className="hidden sm:inline-block px-2 py-1 text-xs font-semibold text-slate-500 bg-slate-100 border border-slate-200 rounded">
            ESC
          </kbd>
        </div>
        
        {searchTerm.length > 0 && (
          <div className="py-2">
            {filteredStocks.length > 0 ? (
              <ul>
                {filteredStocks.map((stock) => (
                  <li 
                    key={stock.ticker}
                    className="px-4 py-3 hover:bg-slate-50 cursor-pointer flex justify-between items-center group transition-colors"
                    onClick={() => handleSelect(stock.ticker)}
                  >
                    <div>
                      <span className="font-mono font-bold text-slate-800">{stock.ticker}</span>
                      <span className="ml-3 text-sm text-slate-500">{stock.name}</span>
                    </div>
                    <span className="text-primary-500 opacity-0 group-hover:opacity-100 text-sm font-medium transition-opacity">
                      View Analysis &rarr;
                    </span>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="px-4 py-8 text-center text-slate-500">
                No stocks found for "{searchTerm}"
              </div>
            )}
          </div>
        )}
        
        {searchTerm.length === 0 && (
          <div className="px-4 py-6 text-center text-slate-400 text-sm">
            Search by ticker symbol or company name. Press <kbd className="font-mono text-xs bg-slate-100 px-1 rounded border">Enter</kbd> to select.
          </div>
        )}
      </div>
    </div>
  );
};

export default CommandPalette;
