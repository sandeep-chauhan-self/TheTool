import React from 'react';

const SignalHeatMap = ({ data }) => {
  // data = { BUY: number, SELL: number, HOLD: number }
  const total = (data.BUY || 0) + (data.SELL || 0) + (data.HOLD || 0);
  
  if (total === 0) return null;

  const buyPct = ((data.BUY || 0) / total) * 100;
  const holdPct = ((data.HOLD || 0) / total) * 100;
  const sellPct = ((data.SELL || 0) / total) * 100;

  return (
    <div className="glass-card p-6 mb-8 animate-slide-up animation-delay-100">
      <div className="flex justify-between items-end mb-4">
        <div>
          <h2 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary-600 to-accent-500">
            Market Signal Overview
          </h2>
          <p className="text-sm text-slate-500 font-medium">Distribution across {total} analyzed stocks</p>
        </div>
        <div className="flex gap-4 text-sm font-semibold">
          <div className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-success-500 shadow-glow-success"></div> <span className="text-slate-700">{data.BUY || 0} Buy</span></div>
          <div className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-warning-500 shadow-glow-warning"></div> <span className="text-slate-700">{data.HOLD || 0} Hold</span></div>
          <div className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-danger-500 shadow-glow-danger"></div> <span className="text-slate-700">{data.SELL || 0} Sell</span></div>
        </div>
      </div>
      
      {/* The Heat Map Bar */}
      <div className="h-4 w-full flex rounded-full overflow-hidden bg-slate-100 shadow-inner">
        <div 
          className="h-full bg-success-500 transition-all duration-1000 ease-out"
          style={{ width: `${buyPct}%`, opacity: buyPct > 0 ? 1 : 0 }}
        ></div>
        <div 
          className="h-full bg-warning-500 transition-all duration-1000 ease-out"
          style={{ width: `${holdPct}%`, opacity: holdPct > 0 ? 1 : 0 }}
        ></div>
        <div 
          className="h-full bg-danger-500 transition-all duration-1000 ease-out"
          style={{ width: `${sellPct}%`, opacity: sellPct > 0 ? 1 : 0 }}
        ></div>
      </div>
    </div>
  );
};

export default SignalHeatMap;
