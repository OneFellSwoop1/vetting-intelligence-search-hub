'use client';

import React, { useState, useRef, useCallback } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, Cell } from 'recharts';
import { Download, ZoomIn, ZoomOut, RotateCcw, Eye, Info } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export interface ChartData {
  id: string;
  name: string;
  value: number;
  category?: string;
  source?: string;
  metadata?: Record<string, any>;
}

interface InteractiveBarChartProps {
  data: ChartData[];
  title: string;
  xAxisKey?: string;
  yAxisKey?: string;
  colorScheme?: 'default' | 'categorical' | 'sequential';
  onBarClick?: (data: ChartData) => void;
  onExport?: (format: 'png' | 'svg' | 'csv') => void;
  height?: number;
  showLegend?: boolean;
  groupBy?: string;
  formatType?: 'currency' | 'number';
}

const colorPalettes = {
  default: ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4', '#84CC16', '#F97316'],
  categorical: ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3', '#54A0FF', '#5F27CD'],
  sequential: ['#FEF3E2', '#FEC868', '#FB8500', '#F77F00', '#FCBF49', '#F77F00', '#D62828', '#A4161A']
};

export default function InteractiveBarChart({
  data,
  title,
  xAxisKey = 'name',
  yAxisKey = 'value',
  colorScheme = 'default',
  onBarClick,
  onExport,
  height = 400,
  showLegend = true,
  groupBy,
  formatType = 'currency'
}: InteractiveBarChartProps) {
  const [selectedBar, setSelectedBar] = useState<ChartData | null>(null);
  const [zoomLevel, setZoomLevel] = useState(1);
  const [showTooltip, setShowTooltip] = useState(true);
  const chartRef = useRef<HTMLDivElement>(null);

  const colors = colorPalettes[colorScheme];

  // Group data if needed
  const processedData = groupBy ? groupDataBy(data, groupBy) : data;

  function groupDataBy(data: ChartData[], groupKey: string): ChartData[] {
    const grouped = data.reduce((acc, item) => {
      const key = item.metadata?.[groupKey] || item.category || 'Other';
      if (!acc[key]) {
        acc[key] = {
          id: key,
          name: key,
          value: 0,
          category: key,
          source: 'grouped',
          metadata: { count: 0, items: [] }
        };
      }
      acc[key].value += item.value;
      acc[key].metadata!.count += 1;
      acc[key].metadata!.items.push(item);
      return acc;
    }, {} as Record<string, ChartData>);

    return Object.values(grouped).sort((a, b) => b.value - a.value);
  }

  const formatValue = (value: number): string => {
    if (formatType === 'number') {
      // Format as plain numbers for counts
      if (value >= 1000000) {
        return `${(value / 1000000).toFixed(1)}M`;
      } else if (value >= 1000) {
        return `${(value / 1000).toFixed(1)}K`;
      }
      return value.toLocaleString();
    } else {
      // Format as currency
      if (value >= 1000000) {
        return `$${(value / 1000000).toFixed(1)}M`;
      } else if (value >= 1000) {
        return `$${(value / 1000).toFixed(1)}K`;
      }
      return `$${value.toLocaleString()}`;
    }
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload || !showTooltip) return null;

    const data = payload[0]?.payload;
    if (!data) return null;

    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-white p-4 border border-gray-200 rounded-lg shadow-lg max-w-xs"
      >
        <div className="font-semibold text-gray-900 mb-2">{label}</div>
        <div className="space-y-1">
          <div className="flex justify-between">
            <span className="text-gray-600">Value:</span>
            <span className="font-medium">{formatValue(data.value)}</span>
          </div>
          {data.source && (
            <div className="flex justify-between">
              <span className="text-gray-600">Source:</span>
              <span className="text-sm">{data.source}</span>
            </div>
          )}
          {data.metadata?.count && (
            <div className="flex justify-between">
              <span className="text-gray-600">Items:</span>
              <span className="text-sm">{data.metadata.count}</span>
            </div>
          )}
        </div>
        {onBarClick && (
          <div className="mt-2 pt-2 border-t border-gray-100">
            <div className="text-xs text-blue-600">Click to drill down</div>
          </div>
        )}
      </motion.div>
    );
  };

  const handleBarClick = (data: ChartData) => {
    setSelectedBar(data);
    onBarClick?.(data);
  };

  const handleZoomIn = () => {
    setZoomLevel(prev => Math.min(prev * 1.2, 3));
  };

  const handleZoomOut = () => {
    setZoomLevel(prev => Math.max(prev / 1.2, 0.5));
  };

  const handleReset = () => {
    setZoomLevel(1);
    setSelectedBar(null);
  };

  const exportChart = useCallback((format: 'png' | 'svg' | 'csv') => {
    if (format === 'csv') {
      const csvContent = [
        ['Name', 'Value', 'Category', 'Source'],
        ...processedData.map(item => [
          item.name,
          item.value.toString(),
          item.category || '',
          item.source || ''
        ])
      ].map(row => row.join(',')).join('\n');

      const blob = new Blob([csvContent], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${title.replace(/\s+/g, '_').toLowerCase()}.csv`;
      a.click();
      URL.revokeObjectURL(url);
    } else {
      // For PNG/SVG export, we'd need html2canvas or similar
      // This is a simplified implementation
      onExport?.(format);
    }
  }, [processedData, title, onExport]);

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowTooltip(!showTooltip)}
            className={`p-2 rounded-lg transition-colors ${
              showTooltip ? 'bg-blue-100 text-blue-600' : 'bg-gray-100 text-gray-600'
            }`}
            title="Toggle tooltips"
          >
            <Info className="w-4 h-4" />
          </button>
          
          <button
            onClick={handleZoomOut}
            className="p-2 rounded-lg bg-gray-100 text-gray-600 hover:bg-gray-200 transition-colors"
            title="Zoom out"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          
          <button
            onClick={handleZoomIn}
            className="p-2 rounded-lg bg-gray-100 text-gray-600 hover:bg-gray-200 transition-colors"
            title="Zoom in"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
          
          <button
            onClick={handleReset}
            className="p-2 rounded-lg bg-gray-100 text-gray-600 hover:bg-gray-200 transition-colors"
            title="Reset view"
          >
            <RotateCcw className="w-4 h-4" />
          </button>

          <div className="relative group">
            <button className="p-2 rounded-lg bg-gray-100 text-gray-600 hover:bg-gray-200 transition-colors">
              <Download className="w-4 h-4" />
            </button>
            
            <div className="absolute right-0 top-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-10">
              <button
                onClick={() => exportChart('csv')}
                className="block w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-50 first:rounded-t-lg"
              >
                Export CSV
              </button>
              <button
                onClick={() => exportChart('png')}
                className="block w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-50"
              >
                Export PNG
              </button>
              <button
                onClick={() => exportChart('svg')}
                className="block w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-50 last:rounded-b-lg"
              >
                Export SVG
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Chart */}
      <div ref={chartRef} style={{ transform: `scale(${zoomLevel})`, transformOrigin: 'top left' }}>
        <ResponsiveContainer width="100%" height={height}>
          <BarChart data={processedData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
            <XAxis 
              dataKey={xAxisKey}
              tick={{ fontSize: 12 }}
              angle={-45}
              textAnchor="end"
              height={80}
            />
            <YAxis 
              tick={{ fontSize: 12 }}
              tickFormatter={formatValue}
            />
            <Tooltip content={<CustomTooltip />} />
            {showLegend && <Legend />}
            <Bar 
              dataKey={yAxisKey}
              cursor="pointer"
              onClick={handleBarClick}
            >
              {processedData.map((entry, index) => (
                <Cell 
                  key={`cell-${index}`} 
                  fill={colors[index % colors.length]}
                  opacity={selectedBar?.id === entry.id ? 1 : 0.8}
                  stroke={selectedBar?.id === entry.id ? '#374151' : 'transparent'}
                  strokeWidth={selectedBar?.id === entry.id ? 2 : 0}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Selection Details */}
      <AnimatePresence>
        {selectedBar && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg"
          >
            <div className="flex items-center justify-between mb-2">
              <h4 className="font-medium text-blue-900">Selected: {selectedBar.name}</h4>
              <button
                onClick={() => setSelectedBar(null)}
                className="text-blue-600 hover:text-blue-800"
              >
                <Eye className="w-4 h-4" />
              </button>
            </div>
            
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-blue-700">Value:</span>
                <span className="ml-2 font-medium">{formatValue(selectedBar.value)}</span>
              </div>
              {selectedBar.source && (
                <div>
                  <span className="text-blue-700">Source:</span>
                  <span className="ml-2">{selectedBar.source}</span>
                </div>
              )}
              {selectedBar.metadata?.count && (
                <div>
                  <span className="text-blue-700">Items:</span>
                  <span className="ml-2">{selectedBar.metadata.count}</span>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Summary Stats */}
      <div className="mt-4 grid grid-cols-3 gap-4 text-center text-sm">
        <div className="p-3 bg-gray-50 rounded-lg">
          <div className="font-medium text-gray-900">{processedData.length}</div>
          <div className="text-gray-600">Categories</div>
        </div>
        <div className="p-3 bg-gray-50 rounded-lg">
          <div className="font-medium text-gray-900">
            {formatValue(processedData.reduce((sum, item) => sum + item.value, 0))}
          </div>
          <div className="text-gray-600">Total Value</div>
        </div>
        <div className="p-3 bg-gray-50 rounded-lg">
          <div className="font-medium text-gray-900">
            {formatValue(Math.max(...processedData.map(item => item.value)))}
          </div>
          <div className="text-gray-600">Max Value</div>
        </div>
      </div>
    </div>
  );
} 