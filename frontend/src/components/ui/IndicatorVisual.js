import React from 'react';

/**
 * IndicatorVisual - Visualizes indicator output values based on their type
 */

// Oscillator Gauge (RSI, Stochastic, etc.)
const OscillatorGauge = ({ value, label, min = 0, max = 100, lowBound = 30, highBound = 70 }) => {
  const numericValue = parseFloat(value) || 0;
  const percentage = Math.min(Math.max(((numericValue - min) / (max - min)) * 100, 0), 100);
  
  let color = 'bg-slate-300';
  if (numericValue <= lowBound) color = 'bg-success-500 shadow-glow-success';
  else if (numericValue >= highBound) color = 'bg-danger-500 shadow-glow-danger';
  else color = 'bg-primary-500 shadow-glow-primary';

  return (
    <div className="w-full max-w-[120px]">
      <div className="flex justify-between text-[10px] font-bold text-slate-400 mb-1 uppercase tracking-tighter">
        <span>OS</span>
        <span>{numericValue.toFixed(1)}</span>
        <span>OB</span>
      </div>
      <div className="h-1.5 w-full bg-slate-100 rounded-full relative overflow-hidden border border-slate-200/50">
        {/* Bounds Markers */}
        <div className="absolute left-[30%] top-0 bottom-0 w-px bg-slate-200"></div>
        <div className="absolute left-[70%] top-0 bottom-0 w-px bg-slate-200"></div>
        
        {/* Value Bar */}
        <div 
          className={`h-full ${color} transition-all duration-1000 ease-out rounded-full`}
          style={{ width: `${percentage}%` }}
        ></div>
      </div>
    </div>
  );
};

// Trend Meter (MACD, ADX, etc.)
const TrendMeter = ({ vote, confidence }) => {
  const isPositive = vote === 1;
  const isNegative = vote === -1;
  const strength = (confidence || 0) * 100;

  return (
    <div className="flex items-center gap-2">
      <div className={`w-6 h-6 rounded-lg flex items-center justify-center shadow-sm border ${
        isPositive ? 'bg-success-50 border-success-100 text-success-600' : 
        isNegative ? 'bg-danger-50 border-danger-100 text-danger-600' : 
        'bg-slate-50 border-slate-100 text-slate-400'
      }`}>
        <svg className={`w-4 h-4 transition-transform ${isPositive ? 'rotate-0' : isNegative ? 'rotate-180' : 'rotate-90'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 10l7-7m0 0l7 7m-7-7v18" />
        </svg>
      </div>
      <div className="flex-1 min-w-[60px]">
        <div className="h-1 w-full bg-slate-100 rounded-full overflow-hidden">
          <div 
            className={`h-full ${isPositive ? 'bg-success-500' : isNegative ? 'bg-danger-500' : 'bg-slate-300'} transition-all duration-700`}
            style={{ width: `${strength}%` }}
          ></div>
        </div>
      </div>
    </div>
  );
};

// Volume/Money Flow Gauge (OBV, CMF)
const FlowGauge = ({ value }) => {
  const val = parseFloat(value) || 0;
  const isPositive = val > 0;
  const absVal = Math.min(Math.abs(val) * 100, 100); // Scaled for display

  return (
    <div className="flex items-center gap-2">
      <div className="w-full h-1.5 bg-slate-100 rounded-full flex overflow-hidden border border-slate-200/50">
        <div className="flex-1 flex justify-end">
          {!isPositive && (
            <div className="h-full bg-danger-400 rounded-l-full transition-all duration-700" style={{ width: `${absVal}%` }}></div>
          )}
        </div>
        <div className="w-px bg-slate-300 h-full"></div>
        <div className="flex-1">
          {isPositive && (
            <div className="h-full bg-success-400 rounded-r-full transition-all duration-700" style={{ width: `${absVal}%` }}></div>
          )}
        </div>
      </div>
    </div>
  );
};

const IndicatorVisual = ({ name, category, value, vote, confidence }) => {
  const cat = (category || '').toLowerCase();
  const lowerName = (name || '').toLowerCase();

  // Route to correct visualization
  if (cat === 'momentum' || lowerName.includes('rsi') || lowerName.includes('stochastic') || lowerName.includes('cci') || lowerName.includes('williams')) {
    let min = 0, max = 100, low = 30, high = 70;
    if (lowerName.includes('williams')) { min = -100; max = 0; low = -80; high = -20; }
    if (lowerName.includes('cci')) { min = -200; max = 200; low = -100; high = 100; }
    return <OscillatorGauge value={value} min={min} max={max} lowBound={low} highBound={high} />;
  }

  if (cat === 'trend' || lowerName.includes('macd') || lowerName.includes('adx') || lowerName.includes('ema') || lowerName.includes('sar')) {
    return <TrendMeter vote={vote} confidence={confidence} />;
  }

  if (cat === 'volume' || lowerName.includes('obv') || lowerName.includes('cmf')) {
    return <FlowGauge value={value} />;
  }

  // Default fallback
  return <span className="text-xs font-mono font-bold text-slate-600">{value}</span>;
};

export default IndicatorVisual;
