import { useLocation, useNavigate } from 'react-router-dom';
import React, { useState, useEffect } from 'react';

function NavigationBar() {
  const location = useLocation();
  const navigate = useNavigate();
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 10);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const isActive = (path) => location.pathname === path;

  return (
    <nav className={`sticky top-0 z-50 transition-all duration-300 ${
      scrolled 
        ? 'bg-white/80 backdrop-blur-lg shadow-sm border-b border-slate-200/50' 
        : 'bg-white border-b border-transparent'
    }`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo & Brand */}
          <div className="flex-shrink-0 flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center text-white font-bold text-lg shadow-glow-primary">
              T
            </div>
            <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-slate-900 to-slate-600">
              TheTool
            </span>
            <div className="hidden sm:flex items-center ml-4 px-2.5 py-1 rounded-full bg-slate-100 border border-slate-200">
               <div className="w-1.5 h-1.5 rounded-full bg-success-500 animate-pulse mr-2 shadow-glow-success"></div>
               <span className="text-xs font-medium text-slate-600">System Online</span>
            </div>
          </div>

          {/* Navigation Links */}
          <div className="flex space-x-2 items-center">
            {/* Search Hint (Command Palette) */}
            <div className="hidden md:flex items-center mr-6 text-sm text-slate-400">
               <svg className="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
               Press <kbd className="mx-1 font-mono text-xs bg-slate-100 border border-slate-200 rounded px-1 text-slate-500">⌘K</kbd> to search
            </div>

            <button
              onClick={() => navigate('/')}
              className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all duration-200 ${
                isActive('/')
                  ? 'bg-slate-900 text-white shadow-md'
                  : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
              }`}
            >
              Dashboard
            </button>

            <button
              onClick={() => navigate('/all-stocks')}
              className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all duration-200 ${
                isActive('/all-stocks')
                  ? 'bg-slate-900 text-white shadow-md'
                  : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
              }`}
            >
              All Stocks Analysis
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
}

export default NavigationBar;
