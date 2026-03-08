import { useEffect, useRef, useState } from 'react';

/**
 * AnalysisConfigModal - Configuration popup for stock analysis
 */

const STRATEGIES = [
  { id: 1, name: 'Strategy 1 - Balanced', shortName: 'Balanced', description: 'Equal weights for all indicators - best for general market conditions', icon: '⚖️' },
  { id: 2, name: 'Strategy 2 - Trend Following', shortName: 'Trend', description: 'Emphasizes MACD, ADX, EMA - best for trending markets', icon: '📈' },
  { id: 3, name: 'Strategy 3 - Mean Reversion', shortName: 'Reversion', description: 'Emphasizes RSI, Bollinger, Stochastic - best for range-bound markets', icon: '🔄' },
  { id: 4, name: 'Strategy 4 - Momentum Breakout', shortName: 'Momentum', description: 'Emphasizes OBV, CMF, ATR - best for breakout plays', icon: '🚀' },
  { id: 5, name: 'Strategy 5 - Weekly 5% Target', shortName: '5% Weekly', description: 'AGGRESSIVE swing trading - 5% target, 3% stop, heavy momentum bias', icon: '🎯' }
];

const DEFAULT_CONFIG = {
  strategyId: 1,
  capital: 100000,
  riskPercent: 2,
  positionSizeLimit: 20,
  riskRewardRatio: 1.5,
  dataPeriod: '200d',
  useDemoData: false,
  categoryWeights: { trend: 1.0, momentum: 1.0, volatility: 0.9, volume: 0.9 },
  enabledIndicators: {
    macd: true, adx: true, ema_crossover: true, parabolic_sar: true,
    rsi: true, stochastic: true, cci: true, williams_r: true,
    bollinger_bands: true, atr: true,
    obv: true, cmf: true
  }
};

const PRESETS = {
  default: { name: 'Default', description: 'Balanced settings for most users', config: { ...DEFAULT_CONFIG } },
  conservative: { name: 'Conservative', description: 'Lower risk, higher R:R ratio', config: { ...DEFAULT_CONFIG, riskPercent: 1, positionSizeLimit: 10, riskRewardRatio: 2.5 } },
  aggressive: { name: 'Aggressive', description: 'Higher position sizes, standard risk', config: { ...DEFAULT_CONFIG, riskPercent: 3, positionSizeLimit: 30, riskRewardRatio: 1.5 } }
};

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

function AnalysisConfigModal({ onClose, onConfirm, stockCount = 1, stockNames = [], title = 'Engine Configuration' }) {
  const [config, setConfig] = useState(() => {
    const saved = localStorage.getItem('analysisConfig');
    if (saved) { try { return { ...DEFAULT_CONFIG, ...JSON.parse(saved) }; } catch (e) { return { ...DEFAULT_CONFIG }; } }
    return { ...DEFAULT_CONFIG };
  });
  
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [showIndicators, setShowIndicators] = useState(false);
  const [rememberSettings, setRememberSettings] = useState(true);
  const modalRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => { if (modalRef.current && !modalRef.current.contains(event.target)) onClose(); };
    const handleEscape = (event) => { if (event.key === 'Escape') onClose(); };
    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleEscape);
    return () => { document.removeEventListener('mousedown', handleClickOutside); document.removeEventListener('keydown', handleEscape); };
  }, [onClose]);

  const handleConfigChange = (key, value) => setConfig(prev => ({ ...prev, [key]: value }));
  const handleCategoryWeightChange = (category, value) => setConfig(prev => ({ ...prev, categoryWeights: { ...prev.categoryWeights, [category]: value } }));
  const handleIndicatorToggle = (indicatorKey) => setConfig(prev => ({ ...prev, enabledIndicators: { ...prev.enabledIndicators, [indicatorKey]: !prev.enabledIndicators[indicatorKey] } }));
  const handlePresetSelect = (presetKey) => { if (PRESETS[presetKey]) setConfig({ ...DEFAULT_CONFIG, ...PRESETS[presetKey].config }); };
  
  const handleConfirm = () => {
    if (rememberSettings) localStorage.setItem('analysisConfig', JSON.stringify(config));
    onConfirm(config);
  };

  const handleReset = () => { setConfig({ ...DEFAULT_CONFIG }); localStorage.removeItem('analysisConfig'); };

  const formatCurrency = (value) => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(value);

  const enabledIndicatorCount = Object.values(config.enabledIndicators).filter(Boolean).length;
  const totalIndicatorCount = Object.keys(config.enabledIndicators).length;

  return (
    <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center z-[100] p-4 animate-fade-in">
      <div ref={modalRef} className="bg-white/95 backdrop-blur-md rounded-2xl shadow-2xl border border-white/40 w-full max-w-xl max-h-[90vh] overflow-hidden flex flex-col transform animate-slide-up">
        
        {/* Header */}
        <div className="px-6 py-5 border-b border-slate-100 flex justify-between items-center bg-gradient-to-r from-slate-50 to-white">
          <div>
            <h2 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary-700 to-accent-600">{title}</h2>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-widest mt-1">
              {stockCount === 1 ? `Target: ${stockNames[0] || '1 asset'}` : `Batch Target: ${stockCount} assets`}
            </p>
          </div>
          <button onClick={onClose} className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-full transition-colors">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
          </button>
        </div>

        {/* Content (Scrollable) */}
        <div className="flex-1 overflow-y-auto custom-scrollbar p-6 space-y-8">
          
          {/* Strategy Selection */}
          <div>
            <div className="flex justify-between items-center mb-3">
              <label className="block text-sm font-bold text-slate-700">Core Strategy</label>
              <button onClick={() => window.open(`/strategies/${config.strategyId}`, '_blank')} className="text-xs font-semibold text-primary-600 hover:text-primary-800 transition-colors">Deep Dive →</button>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {STRATEGIES.map(strategy => (
                <button
                  key={strategy.id}
                  onClick={() => handleConfigChange('strategyId', strategy.id)}
                  className={`p-3 rounded-xl border text-left transition-all ${
                    config.strategyId === strategy.id
                      ? 'border-primary-500 bg-primary-50 shadow-inner'
                      : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50 bg-white'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">{strategy.icon}</span>
                    <div>
                      <div className={`font-bold text-sm ${config.strategyId === strategy.id ? 'text-primary-800' : 'text-slate-700'}`}>{strategy.shortName}</div>
                      <div className="text-xs text-slate-500 line-clamp-1">{strategy.description.split(' - ')[0]}</div>
                    </div>
                  </div>
                </button>
              ))}
            </div>
            <div className="mt-3 p-3 bg-slate-50 rounded-lg text-xs text-slate-600 border border-slate-100 font-medium">
              <span className="font-bold text-slate-700">Thesis: </span>{STRATEGIES.find(s => s.id === config.strategyId)?.description}
            </div>
          </div>

          {/* Quick Presets */}
          <div>
            <label className="block text-sm font-bold text-slate-700 mb-3">Quick Configuration Presets</label>
            <div className="flex gap-2 flex-wrap">
              {Object.entries(PRESETS).map(([key, preset]) => (
                <button
                  key={key}
                  onClick={() => handlePresetSelect(key)}
                  className="px-4 py-2 text-xs font-bold rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50 hover:border-slate-300 transition-all bg-white shadow-sm"
                  title={preset.description}
                >
                  {preset.name}
                </button>
              ))}
            </div>
          </div>

          <div className="h-px bg-slate-100 w-full"></div>

          {/* Capital Input */}
          <div>
            <label className="block text-sm font-bold text-slate-700 mb-3">Allocated Capital Base</label>
            <div className="relative">
              <span className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 font-bold">₹</span>
              <input
                type="number"
                value={config.capital}
                onChange={(e) => handleConfigChange('capital', Number(e.target.value))}
                min="1000"
                max="100000000"
                step="1000"
                className="w-full pl-9 pr-4 py-3 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 text-slate-800 font-bold bg-white/50"
              />
            </div>
            <div className="flex gap-2 mt-3 overflow-x-auto pb-1 custom-scrollbar">
              {[10000, 50000, 100000, 500000, 1000000].map(amount => (
                <button
                  key={amount}
                  onClick={() => handleConfigChange('capital', amount)}
                  className={`px-3 py-1.5 text-xs font-bold rounded-lg whitespace-nowrap transition-all ${
                    config.capital === amount 
                      ? 'bg-primary-100 text-primary-700 border border-primary-200 shadow-sm' 
                      : 'bg-white border text-slate-600 border-slate-200 hover:bg-slate-50 hover:text-slate-800'
                  }`}
                >
                  {formatCurrency(amount)}
                </button>
              ))}
            </div>
          </div>

          <div className="h-px bg-slate-100 w-full"></div>

          {/* Risk Management Section */}
          <div className="space-y-6">
            <h3 className="font-bold text-slate-900 text-lg">Risk Modeling Parameters</h3>
            
            <div>
              <div className="flex justify-between text-sm mb-2">
                <label className="font-medium text-slate-600">Max Value at Risk per Trade</label>
                <span className="font-bold text-slate-800">{config.riskPercent}%</span>
              </div>
              <input type="range" value={config.riskPercent} onChange={(e) => handleConfigChange('riskPercent', Number(e.target.value))} min="0.5" max="5" step="0.5" className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-primary-600" />
            </div>

            <div>
              <div className="flex justify-between text-sm mb-2">
                <label className="font-medium text-slate-600">Position Size Upper Limit</label>
                <span className="font-bold text-slate-800">{config.positionSizeLimit}%</span>
              </div>
              <input type="range" value={config.positionSizeLimit} onChange={(e) => handleConfigChange('positionSizeLimit', Number(e.target.value))} min="5" max="50" step="5" className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-primary-600" />
            </div>

            <div>
              <div className="flex justify-between text-sm mb-2">
                <label className="font-medium text-slate-600">Minimum Risk-Reward Target</label>
                <span className="font-bold text-slate-800">1 : {config.riskRewardRatio}</span>
              </div>
              <select value={config.riskRewardRatio} onChange={(e) => handleConfigChange('riskRewardRatio', Number(e.target.value))} className="w-full px-4 py-3 border border-slate-200 bg-white/50 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 text-slate-700 font-medium">
                <option value={1}>1:1 (Neutral Baseline)</option>
                <option value={1.5}>1:1.5 (Standard Target)</option>
                <option value={2}>1:2 (Conservative)</option>
                <option value={2.5}>1:2.5 (High R:R)</option>
                <option value={3}>1:3 (Extremely Conservative)</option>
              </select>
            </div>
          </div>

          <div className="h-px bg-slate-100 w-full"></div>

          {/* Data Environment */}
          <div className="space-y-6">
            <h3 className="font-bold text-slate-900 text-lg">Data Environment</h3>
            
            <div className="bg-slate-50 p-4 rounded-xl border border-slate-100 flex items-center justify-between">
              <div>
                <label className="text-sm font-bold text-slate-800 block">Simulation Mode / Dummy Data</label>
                <p className="text-xs font-medium text-slate-500 mt-0.5">Mock external API dependencies for rapid testing</p>
              </div>
              <button onClick={() => handleConfigChange('useDemoData', !config.useDemoData)} className={`relative min-w-[3rem] w-12 h-6 rounded-full transition-colors ${config.useDemoData ? 'bg-primary-500 shadow-inner' : 'bg-slate-300'}`}>
                <span className={`absolute top-1 left-1 w-4 h-4 bg-white rounded-full transition-transform shadow-sm ${config.useDemoData ? 'translate-x-6' : ''}`} />
              </button>
            </div>

            <div>
              <label className="block text-sm font-bold text-slate-700 mb-2">Lookback Period</label>
              <select value={config.dataPeriod} onChange={(e) => handleConfigChange('dataPeriod', e.target.value)} className="w-full px-4 py-3 border border-slate-200 bg-white/50 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 text-slate-700 font-medium">
                <option value="100d">100 Days (~3 Months)</option>
                <option value="200d">200 Days (~6 Months - Recommended)</option>
                <option value="365d">365 Days (~1 Year)</option>
                <option value="2y">2 Years</option>
              </select>
            </div>
          </div>

          {/* Advanced / Indicators Accordions */}
          <div className="space-y-3">
            <div className="bg-white border border-slate-200 rounded-xl overflow-hidden hover:border-slate-300 transition-colors">
              <button onClick={() => setShowAdvanced(!showAdvanced)} className="w-full px-5 py-4 flex justify-between items-center text-left bg-slate-50/50">
                <span className="font-bold text-slate-800">Advanced Algorithmic Weights</span>
                <span className="ml-4 flex-shrink-0 text-slate-400">
                   <svg className={`w-5 h-5 transition-transform ${showAdvanced ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
                </span>
              </button>
              {showAdvanced && (
                <div className="p-5 border-t border-slate-100 space-y-5 bg-white">
                  {Object.entries(config.categoryWeights).map(([category, weight]) => (
                    <div key={category}>
                      <div className="flex justify-between text-sm mb-2">
                        <label className="text-slate-600 font-bold capitalize">{category} Dominance</label>
                        <span className="font-bold text-primary-600">{weight.toFixed(1)}x</span>
                      </div>
                      <input type="range" value={weight} onChange={(e) => handleCategoryWeightChange(category, Number(e.target.value))} min="0.5" max="1.5" step="0.1" className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-primary-500" />
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="bg-white border border-slate-200 rounded-xl overflow-hidden hover:border-slate-300 transition-colors">
              <button onClick={() => setShowIndicators(!showIndicators)} className="w-full px-5 py-4 flex justify-between items-center text-left bg-slate-50/50">
                <div>
                  <span className="font-bold text-slate-800">Component Output Switches</span>
                  <span className="text-xs font-bold text-slate-400 uppercase tracking-widest ml-2 block sm:inline mt-1 sm:mt-0">({enabledIndicatorCount}/{totalIndicatorCount} ACTIVE)</span>
                </div>
                <span className="ml-4 flex-shrink-0 text-slate-400">
                   <svg className={`w-5 h-5 transition-transform ${showIndicators ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
                </span>
              </button>
              {showIndicators && (
                <div className="p-5 border-t border-slate-100 space-y-6 bg-white">
                  {Object.entries(INDICATORS).map(([category, indicatorsList]) => (
                    <div key={category}>
                      <h4 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-3 flex items-center gap-2">
                        <div className={`w-1.5 h-1.5 rounded-full ${category === 'trend' ? 'bg-primary-500' : category === 'momentum' ? 'bg-accent-500' : category === 'volatility' ? 'bg-warning-500' : 'bg-success-500'}`}></div>
                        {category} Layer
                      </h4>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        {indicatorsList.map(indicator => (
                          <label key={indicator.key} className={`flex items-start cursor-pointer p-3 rounded-xl border ${config.enabledIndicators[indicator.key] ? 'bg-slate-50 border-slate-200' : 'bg-white border-transparent hover:bg-slate-50'} transition-all`} title={indicator.description}>
                            <input type="checkbox" checked={config.enabledIndicators[indicator.key]} onChange={() => handleIndicatorToggle(indicator.key)} className="mt-0.5 w-4 h-4 text-primary-600 rounded border-slate-300 focus:ring-primary-500" />
                            <div className="ml-3">
                              <span className={`block text-sm font-bold ${config.enabledIndicators[indicator.key] ? 'text-slate-800' : 'text-slate-500'}`}>{indicator.name}</span>
                            </div>
                          </label>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
          
        </div>

        {/* Footer */}
        <div className="bg-slate-50 border-t border-slate-200 px-6 py-4">
          <div className="flex items-center justify-between text-xs font-semibold text-slate-500 mb-4 px-1">
             <label className="flex items-center space-x-2 cursor-pointer hover:text-slate-700 transition-colors">
                <input type="checkbox" checked={rememberSettings} onChange={(e) => setRememberSettings(e.target.checked)} className="w-4 h-4 text-primary-600 rounded border-slate-300 focus:ring-primary-500" />
                <span>Save state to local blueprint</span>
             </label>
             <button onClick={handleReset} className="hover:text-danger-600 transition-colors uppercase tracking-wider">Factory Reset</button>
          </div>
          <div className="flex gap-3">
            <button onClick={onClose} className="flex-1 px-5 py-3.5 bg-white border border-slate-200 text-slate-700 rounded-xl hover:bg-slate-50 font-bold transition-all shadow-sm">
              Discard
            </button>
            <button onClick={handleConfirm} className="flex-[2] px-5 py-3.5 bg-slate-900 text-white rounded-xl hover:bg-slate-800 font-bold transition-all shadow-md flex justify-center items-center gap-2">
              Run Execute <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" /></svg>
            </button>
          </div>
        </div>

      </div>
    </div>
  );
}

export default AnalysisConfigModal;
