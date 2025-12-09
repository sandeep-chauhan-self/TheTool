import { useEffect, useRef, useState } from 'react';

/**
 * AnalysisConfigModal - Configuration popup for stock analysis
 * 
 * Opens before any analysis operation to allow users to configure:
 * - Strategy selection (Strategy 1, 2, 3, 4...)
 * - Capital/Investment amount
 * - Risk management settings
 * - Data settings
 * - Indicator selection (collapsible advanced section)
 */

// Strategy definitions (synced with backend strategies module)
const STRATEGIES = [
  {
    id: 1,
    name: 'Strategy 1 - Balanced',
    shortName: 'Balanced',
    description: 'Equal weights for all indicators - best for general market conditions',
    icon: '⚖️'
  },
  {
    id: 2,
    name: 'Strategy 2 - Trend Following',
    shortName: 'Trend',
    description: 'Emphasizes MACD, ADX, EMA - best for trending markets',
    icon: '📈'
  },
  {
    id: 3,
    name: 'Strategy 3 - Mean Reversion',
    shortName: 'Reversion',
    description: 'Emphasizes RSI, Bollinger, Stochastic - best for range-bound markets',
    icon: '🔄'
  },
  {
    id: 4,
    name: 'Strategy 4 - Momentum Breakout',
    shortName: 'Momentum',
    description: 'Emphasizes OBV, CMF, ATR - best for breakout plays',
    icon: '🚀'
  },
  {
    id: 5,
    name: 'Strategy 5 - Weekly 4% Target',
    shortName: '4% Target',
    description: 'Aggressive swing trading - 3% stop, 4% profit target (1.33:1 R:R)',
    icon: '💹'
  }
];

// Default configuration values
const DEFAULT_CONFIG = {
  strategyId: 1,              // Default to Strategy 1 (Balanced)
  capital: 100000,
  riskPercent: 2,             // Max risk per trade (%)
  positionSizeLimit: 20,      // Max position size as % of capital
  riskRewardRatio: 1.5,       // Minimum risk-reward ratio
  dataPeriod: '200d',         // Historical data period
  useDemoData: false,         // Use demo/simulated data
  // Indicator weights by category
  categoryWeights: {
    trend: 1.0,
    momentum: 1.0,
    volatility: 0.9,
    volume: 0.9
  },
  // Individual indicator toggles
  enabledIndicators: {
    // Trend
    macd: true,
    adx: true,
    ema_crossover: true,
    parabolic_sar: true,
    // Momentum
    rsi: true,
    stochastic: true,
    cci: true,
    williams_r: true,
    // Volatility
    bollinger_bands: true,
    atr: true,
    // Volume
    obv: true,
    cmf: true
  }
};

// Preset configurations
const PRESETS = {
  default: {
    name: 'Default',
    description: 'Balanced settings for most users',
    config: { ...DEFAULT_CONFIG }
  },
  conservative: {
    name: 'Conservative',
    description: 'Lower risk, higher R:R ratio',
    config: {
      ...DEFAULT_CONFIG,
      riskPercent: 1,
      positionSizeLimit: 10,
      riskRewardRatio: 2.5
    }
  },
  aggressive: {
    name: 'Aggressive',
    description: 'Higher position sizes, standard risk',
    config: {
      ...DEFAULT_CONFIG,
      riskPercent: 3,
      positionSizeLimit: 30,
      riskRewardRatio: 1.5
    }
  }
};

// Indicator metadata for display
const INDICATORS = {
  trend: [
    { key: 'macd', name: 'MACD', description: 'Moving Average Convergence Divergence' },
    { key: 'adx', name: 'ADX', description: 'Average Directional Index' },
    { key: 'ema_crossover', name: 'EMA Crossover', description: '9/21 EMA Crossover' },
    { key: 'parabolic_sar', name: 'Parabolic SAR', description: 'Stop and Reverse' }
  ],
  momentum: [
    { key: 'rsi', name: 'RSI', description: 'Relative Strength Index' },
    { key: 'stochastic', name: 'Stochastic', description: 'Stochastic Oscillator' },
    { key: 'cci', name: 'CCI', description: 'Commodity Channel Index' },
    { key: 'williams_r', name: 'Williams %R', description: 'Williams Percent Range' }
  ],
  volatility: [
    { key: 'bollinger_bands', name: 'Bollinger Bands', description: '20-period with 2 std dev' },
    { key: 'atr', name: 'ATR', description: 'Average True Range' }
  ],
  volume: [
    { key: 'obv', name: 'OBV', description: 'On Balance Volume' },
    { key: 'cmf', name: 'CMF', description: 'Chaikin Money Flow' }
  ]
};

function AnalysisConfigModal({ 
  onClose, 
  onConfirm, 
  stockCount = 1,
  stockNames = [],
  title = 'Analysis Configuration'
}) {
  // Load saved config from localStorage or use defaults
  const [config, setConfig] = useState(() => {
    const saved = localStorage.getItem('analysisConfig');
    if (saved) {
      try {
        return { ...DEFAULT_CONFIG, ...JSON.parse(saved) };
      } catch (e) {
        return { ...DEFAULT_CONFIG };
      }
    }
    return { ...DEFAULT_CONFIG };
  });
  
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [showIndicators, setShowIndicators] = useState(false);
  const [rememberSettings, setRememberSettings] = useState(true);
  const modalRef = useRef(null);

  // Close on outside click
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (modalRef.current && !modalRef.current.contains(event.target)) {
        onClose();
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [onClose]);

  // Close on Escape key
  useEffect(() => {
    const handleEscape = (event) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [onClose]);

  const handleConfigChange = (key, value) => {
    setConfig(prev => ({ ...prev, [key]: value }));
  };

  const handleCategoryWeightChange = (category, value) => {
    setConfig(prev => ({
      ...prev,
      categoryWeights: {
        ...prev.categoryWeights,
        [category]: value
      }
    }));
  };

  const handleIndicatorToggle = (indicatorKey) => {
    setConfig(prev => ({
      ...prev,
      enabledIndicators: {
        ...prev.enabledIndicators,
        [indicatorKey]: !prev.enabledIndicators[indicatorKey]
      }
    }));
  };

  const handlePresetSelect = (presetKey) => {
    const preset = PRESETS[presetKey];
    if (preset) {
      setConfig({ ...DEFAULT_CONFIG, ...preset.config });
    }
  };

  const handleConfirm = () => {
    // Save to localStorage if remember is checked
    if (rememberSettings) {
      localStorage.setItem('analysisConfig', JSON.stringify(config));
    }
    onConfirm(config);
  };

  const handleReset = () => {
    setConfig({ ...DEFAULT_CONFIG });
    localStorage.removeItem('analysisConfig');
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    }).format(value);
  };

  const enabledIndicatorCount = Object.values(config.enabledIndicators).filter(Boolean).length;
  const totalIndicatorCount = Object.keys(config.enabledIndicators).length;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div 
        ref={modalRef}
        className="bg-white rounded-lg shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto"
      >
        {/* Header */}
        <div className="sticky top-0 bg-white border-b px-6 py-4 flex justify-between items-center">
          <div>
            <h2 className="text-xl font-bold text-gray-800">{title}</h2>
            <p className="text-sm text-gray-500 mt-1">
              {stockCount === 1 
                ? `Analyzing: ${stockNames[0] || '1 stock'}`
                : `Analyzing ${stockCount} stocks`
              }
            </p>
          </div>
          <button 
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl leading-none"
          >
            ×
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Strategy Selection */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <label className="block text-sm font-medium text-gray-700">
                Analysis Strategy
              </label>
              <button
                onClick={() => {
                  const strategy = STRATEGIES.find(s => s.id === config.strategyId);
                  if (strategy) {
                    window.open(`/strategies/${strategy.id}`, '_blank');
                  }
                }}
                className="text-xs text-blue-600 hover:text-blue-800 hover:underline"
              >
                Learn more →
              </button>
            </div>
            <div className="grid grid-cols-2 gap-2">
              {STRATEGIES.map(strategy => (
                <button
                  key={strategy.id}
                  onClick={() => handleConfigChange('strategyId', strategy.id)}
                  className={`p-3 rounded-lg border-2 text-left transition-all ${
                    config.strategyId === strategy.id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <span className="text-xl">{strategy.icon}</span>
                    <div>
                      <div className={`font-medium text-sm ${
                        config.strategyId === strategy.id ? 'text-blue-700' : 'text-gray-700'
                      }`}>
                        {strategy.shortName}
                      </div>
                      <div className="text-xs text-gray-500 line-clamp-1">
                        {strategy.description.split(' - ')[0]}
                      </div>
                    </div>
                  </div>
                </button>
              ))}
            </div>
            {/* Selected strategy description */}
            <div className="mt-2 p-2 bg-gray-50 rounded text-xs text-gray-600">
              {STRATEGIES.find(s => s.id === config.strategyId)?.description}
            </div>
          </div>

          {/* Quick Presets */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Quick Presets
            </label>
            <div className="flex gap-2 flex-wrap">
              {Object.entries(PRESETS).map(([key, preset]) => (
                <button
                  key={key}
                  onClick={() => handlePresetSelect(key)}
                  className="px-3 py-1.5 text-sm rounded-full border border-gray-300 hover:bg-blue-50 hover:border-blue-300 transition-colors"
                  title={preset.description}
                >
                  {preset.name}
                </button>
              ))}
            </div>
          </div>

          {/* Capital Input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Investment Capital
            </label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">₹</span>
              <input
                type="number"
                value={config.capital}
                onChange={(e) => handleConfigChange('capital', Number(e.target.value))}
                min="1000"
                max="100000000"
                step="1000"
                className="w-full pl-8 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div className="flex gap-2 mt-2">
              {[10000, 50000, 100000, 500000, 1000000].map(amount => (
                <button
                  key={amount}
                  onClick={() => handleConfigChange('capital', amount)}
                  className={`px-2 py-1 text-xs rounded border transition-colors ${
                    config.capital === amount 
                      ? 'bg-blue-100 border-blue-300 text-blue-700' 
                      : 'bg-gray-50 border-gray-200 hover:bg-gray-100'
                  }`}
                >
                  {formatCurrency(amount)}
                </button>
              ))}
            </div>
          </div>

          {/* Risk Management Section */}
          <div className="bg-gray-50 rounded-lg p-4 space-y-4">
            <h3 className="font-medium text-gray-800">Risk Management</h3>
            
            {/* Risk Per Trade */}
            <div>
              <div className="flex justify-between text-sm mb-1">
                <label className="text-gray-600">Max Risk Per Trade</label>
                <span className="font-medium text-gray-800">{config.riskPercent}%</span>
              </div>
              <input
                type="range"
                value={config.riskPercent}
                onChange={(e) => handleConfigChange('riskPercent', Number(e.target.value))}
                min="0.5"
                max="5"
                step="0.5"
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
              />
              <div className="flex justify-between text-xs text-gray-400 mt-1">
                <span>0.5%</span>
                <span>5%</span>
              </div>
            </div>

            {/* Position Size Limit */}
            <div>
              <div className="flex justify-between text-sm mb-1">
                <label className="text-gray-600">Max Position Size</label>
                <span className="font-medium text-gray-800">{config.positionSizeLimit}%</span>
              </div>
              <input
                type="range"
                value={config.positionSizeLimit}
                onChange={(e) => handleConfigChange('positionSizeLimit', Number(e.target.value))}
                min="5"
                max="50"
                step="5"
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
              />
              <div className="flex justify-between text-xs text-gray-400 mt-1">
                <span>5%</span>
                <span>50%</span>
              </div>
            </div>

            {/* Risk-Reward Ratio */}
            <div>
              <div className="flex justify-between text-sm mb-1">
                <label className="text-gray-600">Min Risk-Reward Ratio</label>
                <span className="font-medium text-gray-800">1:{config.riskRewardRatio}</span>
              </div>
              <select
                value={config.riskRewardRatio}
                onChange={(e) => handleConfigChange('riskRewardRatio', Number(e.target.value))}
                className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value={1}>1:1 (Equal risk and reward)</option>
                <option value={1.5}>1:1.5 (Standard)</option>
                <option value={2}>1:2 (Conservative)</option>
                <option value={2.5}>1:2.5 (Careful)</option>
                <option value={3}>1:3 (Very Conservative)</option>
              </select>
            </div>
          </div>

          {/* Data Settings */}
          <div>
            <h3 className="font-medium text-gray-800 mb-3">Data Settings</h3>
            
            <div className="space-y-3">
              {/* Historical Period */}
              <div>
                <label className="block text-sm text-gray-600 mb-1">Historical Data Period</label>
                <select
                  value={config.dataPeriod}
                  onChange={(e) => handleConfigChange('dataPeriod', e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="100d">100 Days</option>
                  <option value="200d">200 Days (Recommended)</option>
                  <option value="365d">1 Year</option>
                  <option value="2y">2 Years</option>
                </select>
              </div>

              {/* Demo Data Toggle */}
              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm text-gray-600">Use Demo Data</label>
                  <p className="text-xs text-gray-400">For testing without real market data</p>
                </div>
                <button
                  onClick={() => handleConfigChange('useDemoData', !config.useDemoData)}
                  className={`relative w-12 h-6 rounded-full transition-colors ${
                    config.useDemoData ? 'bg-blue-600' : 'bg-gray-300'
                  }`}
                >
                  <span 
                    className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full transition-transform ${
                      config.useDemoData ? 'translate-x-6' : ''
                    }`}
                  />
                </button>
              </div>
            </div>
          </div>

          {/* Advanced Settings (Collapsible) */}
          <div className="border rounded-lg">
            <button
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="w-full px-4 py-3 flex justify-between items-center text-left hover:bg-gray-50 transition-colors"
            >
              <span className="font-medium text-gray-700">Advanced Settings</span>
              <span className={`transform transition-transform ${showAdvanced ? 'rotate-180' : ''}`}>
                ▼
              </span>
            </button>
            
            {showAdvanced && (
              <div className="px-4 pb-4 space-y-4 border-t">
                {/* Category Weights */}
                <div className="pt-4">
                  <h4 className="text-sm font-medium text-gray-700 mb-3">Category Weights</h4>
                  <div className="space-y-3">
                    {Object.entries(config.categoryWeights).map(([category, weight]) => (
                      <div key={category}>
                        <div className="flex justify-between text-sm mb-1">
                          <label className="text-gray-600 capitalize">{category}</label>
                          <span className="font-medium text-gray-800">{weight.toFixed(1)}</span>
                        </div>
                        <input
                          type="range"
                          value={weight}
                          onChange={(e) => handleCategoryWeightChange(category, Number(e.target.value))}
                          min="0.5"
                          max="1.5"
                          step="0.1"
                          className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                        />
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Indicators Section (Collapsible) */}
          <div className="border rounded-lg">
            <button
              onClick={() => setShowIndicators(!showIndicators)}
              className="w-full px-4 py-3 flex justify-between items-center text-left hover:bg-gray-50 transition-colors"
            >
              <div>
                <span className="font-medium text-gray-700">Indicators</span>
                <span className="text-sm text-gray-500 ml-2">
                  ({enabledIndicatorCount}/{totalIndicatorCount} enabled)
                </span>
              </div>
              <span className={`transform transition-transform ${showIndicators ? 'rotate-180' : ''}`}>
                ▼
              </span>
            </button>
            
            {showIndicators && (
              <div className="px-4 pb-4 space-y-4 border-t">
                {Object.entries(INDICATORS).map(([category, indicators]) => (
                  <div key={category} className="pt-3">
                    <h4 className="text-sm font-medium text-gray-700 capitalize mb-2 flex items-center">
                      <span className={`w-2 h-2 rounded-full mr-2 ${
                        category === 'trend' ? 'bg-blue-500' :
                        category === 'momentum' ? 'bg-green-500' :
                        category === 'volatility' ? 'bg-orange-500' :
                        'bg-purple-500'
                      }`}></span>
                      {category}
                    </h4>
                    <div className="grid grid-cols-2 gap-2">
                      {indicators.map(indicator => (
                        <label 
                          key={indicator.key}
                          className="flex items-center space-x-2 text-sm cursor-pointer hover:bg-gray-50 p-1.5 rounded"
                          title={indicator.description}
                        >
                          <input
                            type="checkbox"
                            checked={config.enabledIndicators[indicator.key]}
                            onChange={() => handleIndicatorToggle(indicator.key)}
                            className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                          />
                          <span className="text-gray-700">{indicator.name}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Remember Settings */}
          <div className="flex items-center justify-between text-sm">
            <label className="flex items-center space-x-2 cursor-pointer">
              <input
                type="checkbox"
                checked={rememberSettings}
                onChange={(e) => setRememberSettings(e.target.checked)}
                className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
              />
              <span className="text-gray-600">Remember my settings</span>
            </label>
            <button
              onClick={handleReset}
              className="text-gray-500 hover:text-gray-700 underline"
            >
              Reset to Defaults
            </button>
          </div>
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 bg-white border-t px-6 py-4 flex gap-3">
          <button
            onClick={handleConfirm}
            className="flex-1 px-4 py-2.5 bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium transition-colors"
          >
            Start Analysis
          </button>
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2.5 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 font-medium transition-colors"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}

export default AnalysisConfigModal;
