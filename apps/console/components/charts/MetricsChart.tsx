"use client";

import React from 'react';

interface DataPoint {
  timestamp: string;
  value: number;
  label?: string;
}

interface MetricsChartProps {
  data: DataPoint[];
  title: string;
  color?: string;
  height?: number;
  showTrend?: boolean;
}

export function MetricsChart({ 
  data, 
  title, 
  color = '#3B82F6', 
  height = 200,
  showTrend = true 
}: MetricsChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="bg-white rounded-lg p-4 border border-gray-200">
        <h3 className="font-medium text-gray-900 mb-4">{title}</h3>
        <div className="flex items-center justify-center h-32 text-gray-500">
          <div className="text-center">
            <div className="text-2xl mb-2">📊</div>
            <div className="text-sm">No data available</div>
          </div>
        </div>
      </div>
    );
  }

  // Calculate basic statistics
  const values = data.map(d => d.value);
  const minValue = Math.min(...values);
  const maxValue = Math.max(...values);
  const avgValue = values.reduce((a, b) => a + b, 0) / values.length;
  const range = maxValue - minValue;
  
  // Calculate trend
  const trend = values.length > 1 ? 
    ((values[values.length - 1] - values[0]) / values[0] * 100) : 0;

  // Generate SVG path for the line chart
  const generatePath = () => {
    if (data.length < 2) return '';
    
    const width = 300;
    const chartHeight = height - 40;
    
    const points = data.map((point, index) => {
      const x = (index / (data.length - 1)) * width;
      const y = chartHeight - ((point.value - minValue) / range) * chartHeight;
      return `${x},${y}`;
    });
    
    return `M ${points.join(' L ')}`;
  };

  const formatValue = (value: number) => {
    if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`;
    if (value >= 1000) return `${(value / 1000).toFixed(1)}K`;
    return value.toFixed(2);
  };

  return (
    <div className="bg-white rounded-lg p-4 border border-gray-200 hover:shadow-md transition-shadow">
      <div className="flex justify-between items-start mb-4">
        <h3 className="font-medium text-gray-900">{title}</h3>
        {showTrend && (
          <div className={`text-sm font-medium ${
            trend > 0 ? 'text-green-600' : trend < 0 ? 'text-red-600' : 'text-gray-600'
          }`}>
            {trend > 0 ? '↗' : trend < 0 ? '↘' : '→'} {Math.abs(trend).toFixed(1)}%
          </div>
        )}
      </div>
      
      <div className="mb-4">
        <div className="text-2xl font-bold text-gray-900">
          {formatValue(values[values.length - 1])}
        </div>
        <div className="text-sm text-gray-500">
          Avg: {formatValue(avgValue)} | Range: {formatValue(minValue)} - {formatValue(maxValue)}
        </div>
      </div>

      <div className="relative" style={{ height: `${height}px` }}>
        <svg width="100%" height={height} className="overflow-visible">
          {/* Grid lines */}
          <defs>
            <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
              <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#f3f4f6" strokeWidth="1"/>
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" />
          
          {/* Area under curve */}
          {data.length > 1 && (
            <path
              d={`${generatePath()} L 300,${height - 20} L 0,${height - 20} Z`}
              fill={color}
              fillOpacity="0.1"
            />
          )}
          
          {/* Main line */}
          {data.length > 1 && (
            <path
              d={generatePath()}
              fill="none"
              stroke={color}
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          )}
          
          {/* Data points */}
          {data.map((point, index) => {
            const x = (index / (data.length - 1)) * 300;
            const y = (height - 40) - ((point.value - minValue) / range) * (height - 40);
            
            return (
              <g key={index}>
                <circle
                  cx={x}
                  cy={y}
                  r="4"
                  fill={color}
                  stroke="white"
                  strokeWidth="2"
                  className="hover:r-6 transition-all cursor-pointer"
                />
                {/* Tooltip on hover */}
                <title>
                  {point.label || new Date(point.timestamp).toLocaleString()}: {formatValue(point.value)}
                </title>
              </g>
            );
          })}
        </svg>
      </div>
      
      {/* Time axis labels */}
      <div className="flex justify-between text-xs text-gray-500 mt-2">
        <span>{new Date(data[0]?.timestamp).toLocaleTimeString()}</span>
        <span>{new Date(data[data.length - 1]?.timestamp).toLocaleTimeString()}</span>
      </div>
    </div>
  );
}

interface SparklineProps {
  data: number[];
  color?: string;
  width?: number;
  height?: number;
}

export function Sparkline({ data, color = '#3B82F6', width = 100, height = 30 }: SparklineProps) {
  if (!data || data.length === 0) {
    return <div className="inline-block bg-gray-100 rounded" style={{ width, height }} />;
  }

  const minValue = Math.min(...data);
  const maxValue = Math.max(...data);
  const range = maxValue - minValue;

  const points = data.map((value, index) => {
    const x = (index / (data.length - 1)) * width;
    const y = height - ((value - minValue) / range) * height;
    return `${x},${y}`;
  });

  const path = `M ${points.join(' L ')}`;

  return (
    <svg width={width} height={height} className="inline-block">
      <path
        d={path}
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

interface DonutChartProps {
  data: { label: string; value: number; color: string }[];
  size?: number;
  centerText?: string;
}

export function DonutChart({ data, size = 120, centerText }: DonutChartProps) {
  const total = data.reduce((sum, item) => sum + item.value, 0);
  const radius = size / 2 - 10;
  const circumference = 2 * Math.PI * radius;
  
  let cumulativePercentage = 0;

  return (
    <div className="relative inline-block">
      <svg width={size} height={size}>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="#f3f4f6"
          strokeWidth="8"
        />
        {data.map((item, index) => {
          const percentage = (item.value / total) * 100;
          const strokeDasharray = `${(percentage / 100) * circumference} ${circumference}`;
          const strokeDashoffset = -((cumulativePercentage / 100) * circumference);
          
          cumulativePercentage += percentage;
          
          return (
            <circle
              key={index}
              cx={size / 2}
              cy={size / 2}
              r={radius}
              fill="none"
              stroke={item.color}
              strokeWidth="8"
              strokeDasharray={strokeDasharray}
              strokeDashoffset={strokeDashoffset}
              strokeLinecap="round"
              transform={`rotate(-90 ${size / 2} ${size / 2})`}
            />
          );
        })}
      </svg>
      
      {centerText && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center">
            <div className="text-lg font-bold text-gray-900">{centerText}</div>
          </div>
        </div>
      )}
    </div>
  );
}
