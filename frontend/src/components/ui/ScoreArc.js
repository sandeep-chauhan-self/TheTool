import React from 'react';

const ScoreArc = ({ score }) => {
  if (score === undefined || score === null) return <span className="text-slate-400 text-sm">-</span>;

  // Score is usually between -1.0 and 1.0. Let's map it to a 0-100 percentage for the arc.
  // -1.0 = 0%, 0 = 50%, 1.0 = 100%
  const numScore = parseFloat(score);
  const percentage = Math.max(0, Math.min(100, ((numScore + 1) / 2) * 100));
  
  // Color based on continuous score
  let color = '#3B82F6'; // default blue
  if (numScore >= 0.3) color = '#10B981'; // Green
  else if (numScore <= -0.3) color = '#EF4444'; // Red
  else color = '#F59E0B'; // Amber

  const radius = 14;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  return (
    <div className="flex items-center gap-2">
      <div className="relative w-8 h-8 flex items-center justify-center">
        {/* Background Arc */}
        <svg className="absolute top-0 left-0 w-full h-full transform -rotate-90">
          <circle
            cx="16" cy="16" r={radius}
            fill="transparent"
            stroke="#E2E8F0"
            strokeWidth="3"
          />
          {/* Foreground Progress Arc */}
          <circle
            cx="16" cy="16" r={radius}
            fill="transparent"
            stroke={color}
            strokeWidth="3"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            style={{ transition: 'stroke-dashoffset 1s ease-out' }}
          />
        </svg>
      </div>
      <span className="font-mono text-sm font-semibold text-slate-700 w-12 text-right">
        {numScore.toFixed(2)}
      </span>
    </div>
  );
};

export default ScoreArc;
