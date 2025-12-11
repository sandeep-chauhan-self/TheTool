import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

function NavigationBar() {
  const location = useLocation();
  const navigate = useNavigate();

  const isActive = (path) => {
    return location.pathname === path;
  };

  return (
    <nav className="sticky top-0 z-50 bg-white shadow-md border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo/Brand */}
          <div className="flex-shrink-0 flex items-center">
            <span className="text-2xl font-bold text-blue-600">TheTool</span>
          </div>

          {/* Navigation Links */}
          <div className="flex space-x-1">
            <button
              onClick={() => navigate('/')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                isActive('/')
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
              }`}
            >
              Dashboard
            </button>

            <span className="flex items-center text-gray-300 px-2">|</span>

            <button
              onClick={() => navigate('/all-stocks')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                isActive('/all-stocks')
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
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
