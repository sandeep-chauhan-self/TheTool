import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import AnalysisConfig from './pages/AnalysisConfig';
import Results from './pages/Results';
import AllStocksAnalysis from './pages/AllStocksAnalysis';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-100">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/config" element={<AnalysisConfig />} />
          <Route path="/results/:ticker" element={<Results />} />
          <Route path="/all-stocks" element={<AllStocksAnalysis />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
