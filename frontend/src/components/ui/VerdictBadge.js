import React from 'react';

const VerdictBadge = ({ verdict }) => {
  if (!verdict) return <span className="text-slate-400 text-sm">-</span>;
  
  const v = verdict.toUpperCase();
  let baseClass = "px-3 py-1 text-xs font-bold rounded-full font-mono tracking-wider inline-flex items-center justify-center border ";
  
  if (v.includes('BUY')) {
    baseClass += "bg-success-50 text-success-600 border-success-100 shadow-glow-success";
  } else if (v.includes('SELL')) {
    baseClass += "bg-danger-50 text-danger-600 border-danger-100 shadow-glow-danger";
  } else if (v.includes('HOLD') || v.includes('NEUTRAL')) {
    baseClass += "bg-warning-50 text-warning-600 border-warning-100";
  } else if (v.includes('WAIT')) {
    baseClass += "bg-slate-50 text-slate-500 border-slate-200";
  } else {
    baseClass += "bg-primary-50 text-primary-600 border-primary-100";
  }

  return (
    <span className={baseClass}>
      {v}
    </span>
  );
};

export default VerdictBadge;
