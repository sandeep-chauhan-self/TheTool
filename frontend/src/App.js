import { Route, BrowserRouter as Router, Routes } from 'react-router-dom';
import BacktestResults from './components/BacktestResults';
import { StocksProvider } from './context/StocksContext';
import AllStocksAnalysis from './pages/AllStocksAnalysis';
import AnalysisConfig from './pages/AnalysisConfig';
import Dashboard from './pages/Dashboard';
import Results from './pages/Results';
import StrategiesIndex from './pages/StrategiesIndex';
import StrategyHelp from './pages/StrategyHelp';

function App() {
  return (
    <Router>
      <StocksProvider>
        <div className="min-h-screen bg-gray-100">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/config" element={<AnalysisConfig />} />
            <Route path="/results/:ticker" element={<Results />} />
            <Route path="/all-stocks" element={<AllStocksAnalysis />} />
            <Route path="/strategies" element={<StrategiesIndex />} />
            <Route path="/strategies/:id" element={<StrategyHelp />} />
            <Route path="/backtest" element={<BacktestResults />} />
          </Routes>
        </div>
      </StocksProvider>
    </Router>
  );
}

export default App;
