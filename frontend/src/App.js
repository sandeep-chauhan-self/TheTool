import { Route, BrowserRouter as Router, Routes } from 'react-router-dom';
import AllStocksAnalysis from './pages/AllStocksAnalysis';
import AnalysisConfig from './pages/AnalysisConfig';
import Dashboard from './pages/Dashboard';
import Results from './pages/Results';
import StrategyHelp from './pages/StrategyHelp';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-100">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/config" element={<AnalysisConfig />} />
          <Route path="/results/:ticker" element={<Results />} />
          <Route path="/all-stocks" element={<AllStocksAnalysis />} />
          <Route path="/strategies/:id" element={<StrategyHelp />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
