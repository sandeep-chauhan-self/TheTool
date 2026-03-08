import React from 'react';

const MicroSparkline = ({ data }) => {
  // data is an array of numbers, e.g., scores or prices over the last 7 days
  if (!data || data.length < 2) {
    return <div className="w-16 h-6 flex items-center justify-center text-slate-300 text-xs">-</div>;
  }

  // Define SVG dimensions
  const width = 64;
  const height = 24;
  const padding = 2;

  // Find min and max to scale the line
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min === 0 ? 1 : max - min; // avoid division by zero

  // Generate points for the SVG polygon/polyline
  const points = data.map((val, i) => {
    const x = (i / (data.length - 1)) * (width - padding * 2) + padding;
    // Invert Y so higher values are higher up
    const y = height - padding - ((val - min) / range) * (height - padding * 2);
    return `${x},${y}`;
  }).join(' ');

  // Determine trend color (last vs first)
  const isUp = data[data.length - 1] >= data[0];
  const color = isUp ? '#10B981' : '#EF4444'; 

  return (
    <div className="w-16 h-6">
      <svg width={width} height={height} className="overflow-visible">
        <polyline
          fill="none"
          stroke={color}
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          points={points}
          className="animate-fade-in"
        />
        {/* Fill Area Gradient (Optional for extra premium feel) */}
        <polygon
          fill={`url(#gradient-${color.replace('#', '')})`}
          points={`${padding},${height} ${points} ${width-padding},${height}`}
          opacity="0.2"
        />
        <defs>
          <linearGradient id={`gradient-${color.replace('#', '')}`} x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity="1" />
            <stop offset="100%" stopColor={color} stopOpacity="0" />
          </linearGradient>
        </defs>
      </svg>
    </div>
  );
};

export default MicroSparkline;
