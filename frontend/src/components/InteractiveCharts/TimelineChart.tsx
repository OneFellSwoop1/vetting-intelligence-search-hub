'use client';

import React, { useState, useRef, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, ReferenceLine, Brush } from 'recharts';
import { Play, Pause, SkipBack, SkipForward, Calendar, Filter, Download, ZoomIn, ZoomOut } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export interface TimelineData {
  id: string;
  date: string;
  title: string;
  description: string;
  amount?: number;
  source: string;
  type: string;
  metadata?: Record<string, any>;
}

interface TimelineChartProps {
  data: TimelineData[];
  title: string;
  height?: number;
  showAnimation?: boolean;
  animationSpeed?: number;
  onEventClick?: (event: TimelineData) => void;
  onTimeRangeChange?: (startDate: string, endDate: string) => void;
}

interface ProcessedTimelineData {
  date: string;
  [key: string]: any;
}

const sourceColors = {
  'checkbook': '#3B82F6',
  'senate_lda': '#EF4444',
  'house_lda': '#F59E0B',
  'nyc_lobbyist': '#10B981',
  
  'nys_ethics': '#06B6D4',
  'default': '#6B7280'
};

export default function TimelineChart({
  data,
  title,
  height = 400,
  showAnimation = true,
  animationSpeed = 1000,
  onEventClick,
  onTimeRangeChange
}: TimelineChartProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTimeIndex, setCurrentTimeIndex] = useState(0);
  const [selectedSources, setSelectedSources] = useState<Set<string>>(new Set());
  const [timeRange, setTimeRange] = useState<[string, string] | null>(null);
  const [zoomLevel, setZoomLevel] = useState(1);
  const [selectedEvent, setSelectedEvent] = useState<TimelineData | null>(null);

  const animationRef = useRef<number>();
  const lastAnimationTime = useRef<number>(0);

  // Process data for chart display
  const processedData = React.useMemo(() => {
    // Group events by date and source
    const groupedByDate: Record<string, Record<string, TimelineData[]>> = {};
    
    data.forEach(event => {
      const date = new Date(event.date).toISOString().split('T')[0];
      if (!groupedByDate[date]) {
        groupedByDate[date] = {};
      }
      if (!groupedByDate[date][event.source]) {
        groupedByDate[date][event.source] = [];
      }
      groupedByDate[date][event.source].push(event);
    });

    // Convert to chart data format
    const chartData: ProcessedTimelineData[] = [];
    const allDates = Object.keys(groupedByDate).sort();
    
    allDates.forEach(date => {
      const dayData: ProcessedTimelineData = { date };
      
      // Add data for each source
      Object.keys(sourceColors).forEach(source => {
        if (source === 'default') return;
        
        const eventsForSource = groupedByDate[date][source] || [];
        const totalAmount = eventsForSource.reduce((sum, event) => sum + (event.amount || 0), 0);
        const eventCount = eventsForSource.length;
        
        dayData[source] = totalAmount;
        dayData[`${source}_count`] = eventCount;
        dayData[`${source}_events`] = eventsForSource;
      });
      
      chartData.push(dayData);
    });

    return chartData;
  }, [data]);

  // Get unique sources from data
  const availableSources = React.useMemo(() => {
    return Array.from(new Set(data.map(event => event.source)));
  }, [data]);

  // Filter data based on selected sources and time range
  const filteredData = React.useMemo(() => {
    let filtered = processedData;
    
    if (timeRange) {
      filtered = filtered.filter(item => 
        item.date >= timeRange[0] && item.date <= timeRange[1]
      );
    }
    
    return filtered;
  }, [processedData, timeRange]);

  // Animation logic
  useEffect(() => {
    if (isPlaying && showAnimation) {
      const animate = (timestamp: number) => {
        if (timestamp - lastAnimationTime.current > animationSpeed) {
          setCurrentTimeIndex(prev => {
            const next = prev + 1;
            if (next >= filteredData.length) {
              setIsPlaying(false);
              return 0;
            }
            return next;
          });
          lastAnimationTime.current = timestamp;
        }
        animationRef.current = requestAnimationFrame(animate);
      };
      
      animationRef.current = requestAnimationFrame(animate);
      
      return () => {
        if (animationRef.current) {
          cancelAnimationFrame(animationRef.current);
        }
      };
    }
  }, [isPlaying, showAnimation, animationSpeed, filteredData.length]);

  const formatValue = (value: number): string => {
    if (value >= 1000000) {
      return `$${(value / 1000000).toFixed(1)}M`;
    } else if (value >= 1000) {
      return `$${(value / 1000).toFixed(1)}K`;
    }
    return `$${value.toLocaleString()}`;
  };

  const formatDate = (dateStr: string): string => {
    return new Date(dateStr).toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric',
      year: 'numeric'
    });
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload || !payload.length) return null;

    const date = label;
    const relevantPayload = payload.filter((item: any) => 
      !item.dataKey.includes('_count') && !item.dataKey.includes('_events')
    );

    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-white p-4 border border-gray-200 rounded-lg shadow-lg max-w-sm"
      >
        <div className="font-semibold text-gray-900 mb-2">{formatDate(date)}</div>
        <div className="space-y-2">
          {relevantPayload.map((item: any, index: number) => {
            const events = payload.find((p: any) => p.dataKey === `${item.dataKey}_events`)?.value || [];
            return (
              <div key={index} className="text-sm">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div 
                      className="w-3 h-3 rounded-full" 
                      style={{ backgroundColor: item.color }}
                    />
                    <span className="font-medium">{item.dataKey}</span>
                  </div>
                  <span>{formatValue(item.value)}</span>
                </div>
                {events.length > 0 && (
                  <div className="text-xs text-gray-600 ml-5">
                    {events.length} event{events.length !== 1 ? 's' : ''}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </motion.div>
    );
  };

  const togglePlayPause = () => {
    setIsPlaying(!isPlaying);
  };

  const handleReset = () => {
    setIsPlaying(false);
    setCurrentTimeIndex(0);
  };

  const handleStepForward = () => {
    setCurrentTimeIndex(prev => Math.min(prev + 1, filteredData.length - 1));
  };

  const handleStepBack = () => {
    setCurrentTimeIndex(prev => Math.max(prev - 1, 0));
  };

  const toggleSource = (source: string) => {
    const newSelected = new Set(selectedSources);
    if (newSelected.has(source)) {
      newSelected.delete(source);
    } else {
      newSelected.add(source);
    }
    setSelectedSources(newSelected);
  };

  const handleBrushChange = (range: any) => {
    if (range && range.startIndex !== undefined && range.endIndex !== undefined) {
      const startDate = filteredData[range.startIndex]?.date;
      const endDate = filteredData[range.endIndex]?.date;
      if (startDate && endDate) {
        setTimeRange([startDate, endDate]);
        onTimeRangeChange?.(startDate, endDate);
      }
    }
  };

  const clearTimeRange = () => {
    setTimeRange(null);
    onTimeRangeChange?.('', '');
  };

  const currentDate = filteredData[currentTimeIndex]?.date;

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        
        <div className="flex items-center gap-2">
          <button
            onClick={() => setZoomLevel(prev => Math.max(prev - 0.2, 0.5))}
            className="p-2 rounded-lg bg-gray-100 text-gray-600 hover:bg-gray-200 transition-colors"
            title="Zoom out"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          
          <button
            onClick={() => setZoomLevel(prev => Math.min(prev + 0.2, 2))}
            className="p-2 rounded-lg bg-gray-100 text-gray-600 hover:bg-gray-200 transition-colors"
            title="Zoom in"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
          
          <button className="p-2 rounded-lg bg-gray-100 text-gray-600 hover:bg-gray-200 transition-colors">
            <Download className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Source Filters */}
      <div className="mb-4">
        <div className="flex items-center gap-2 mb-2">
          <Filter className="w-4 h-4 text-gray-600" />
          <span className="text-sm font-medium text-gray-700">Data Sources:</span>
        </div>
        <div className="flex flex-wrap gap-2">
          {availableSources.map(source => (
            <button
              key={source}
              onClick={() => toggleSource(source)}
              className={`px-3 py-1 text-sm rounded-full border transition-colors ${
                selectedSources.has(source) || selectedSources.size === 0
                  ? 'bg-blue-100 text-blue-700 border-blue-300'
                  : 'bg-gray-100 text-gray-600 border-gray-300'
              }`}
            >
              <div className="flex items-center gap-2">
                <div 
                  className="w-2 h-2 rounded-full" 
                  style={{ backgroundColor: sourceColors[source as keyof typeof sourceColors] || sourceColors.default }}
                />
                {source}
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Time Range Info */}
      {timeRange && (
        <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm text-blue-700">
              <Calendar className="w-4 h-4" />
              <span>Filtered: {formatDate(timeRange[0])} - {formatDate(timeRange[1])}</span>
            </div>
            <button
              onClick={clearTimeRange}
              className="text-blue-600 hover:text-blue-800 text-sm"
            >
              Clear filter
            </button>
          </div>
        </div>
      )}

      {/* Animation Controls */}
      {showAnimation && (
        <div className="mb-6 p-4 bg-gray-50 rounded-lg">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <button
                onClick={handleReset}
                className="p-2 rounded-lg bg-white border border-gray-300 hover:bg-gray-50 transition-colors"
                title="Reset to start"
              >
                <SkipBack className="w-4 h-4" />
              </button>
              
              <button
                onClick={handleStepBack}
                className="p-2 rounded-lg bg-white border border-gray-300 hover:bg-gray-50 transition-colors"
                title="Step back"
                disabled={currentTimeIndex === 0}
              >
                <SkipBack className="w-4 h-4" />
              </button>
              
              <button
                onClick={togglePlayPause}
                className="p-3 rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors"
                title={isPlaying ? "Pause" : "Play"}
              >
                {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
              </button>
              
              <button
                onClick={handleStepForward}
                className="p-2 rounded-lg bg-white border border-gray-300 hover:bg-gray-50 transition-colors"
                title="Step forward"
                disabled={currentTimeIndex >= filteredData.length - 1}
              >
                <SkipForward className="w-4 h-4" />
              </button>
            </div>
            
            {currentDate && (
              <div className="text-sm font-medium text-gray-700">
                Current: {formatDate(currentDate)}
              </div>
            )}
          </div>
          
          {/* Progress bar */}
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-blue-600 h-2 rounded-full transition-all duration-200"
              style={{ 
                width: `${filteredData.length > 0 ? (currentTimeIndex / (filteredData.length - 1)) * 100 : 0}%` 
              }}
            />
          </div>
        </div>
      )}

      {/* Chart */}
      <div style={{ transform: `scale(${zoomLevel})`, transformOrigin: 'top left' }}>
        <ResponsiveContainer width="100%" height={height}>
          <LineChart data={filteredData} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
            <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
            <XAxis 
              dataKey="date"
              tick={{ fontSize: 12 }}
              tickFormatter={formatDate}
              angle={-45}
              textAnchor="end"
              height={80}
            />
            <YAxis 
              tick={{ fontSize: 12 }}
              tickFormatter={formatValue}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            
            {/* Reference line for current time in animation */}
            {showAnimation && currentDate && (
              <ReferenceLine x={currentDate} stroke="#EF4444" strokeDasharray="2 2" />
            )}
            
            {/* Lines for each source */}
            {availableSources.map(source => {
              const isVisible = selectedSources.size === 0 || selectedSources.has(source);
              if (!isVisible) return null;
              
              return (
                <Line
                  key={source}
                  type="monotone"
                  dataKey={source}
                  stroke={sourceColors[source as keyof typeof sourceColors] || sourceColors.default}
                  strokeWidth={2}
                  dot={{ r: 4 }}
                  activeDot={{ r: 6 }}
                  connectNulls={false}
                />
              );
            })}
            
            {/* Brush for time range selection */}
            <Brush 
              dataKey="date" 
              height={30}
              tickFormatter={formatDate}
              onChange={handleBrushChange}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Summary Stats */}
      <div className="mt-6 grid grid-cols-4 gap-4 text-center text-sm">
        <div className="p-3 bg-gray-50 rounded-lg">
          <div className="font-medium text-gray-900">{data.length}</div>
          <div className="text-gray-600">Total Events</div>
        </div>
        <div className="p-3 bg-gray-50 rounded-lg">
          <div className="font-medium text-gray-900">{availableSources.length}</div>
          <div className="text-gray-600">Data Sources</div>
        </div>
        <div className="p-3 bg-gray-50 rounded-lg">
          <div className="font-medium text-gray-900">
            {formatValue(data.reduce((sum, event) => sum + (event.amount || 0), 0))}
          </div>
          <div className="text-gray-600">Total Value</div>
        </div>
        <div className="p-3 bg-gray-50 rounded-lg">
          <div className="font-medium text-gray-900">
            {data.length > 0 ? 
              `${Math.ceil((new Date(Math.max(...data.map(d => new Date(d.date).getTime()))).getTime() - 
                            new Date(Math.min(...data.map(d => new Date(d.date).getTime()))).getTime()) / 
                           (1000 * 60 * 60 * 24))} days` : '0 days'
            }
          </div>
          <div className="text-gray-600">Time Span</div>
        </div>
      </div>

      {/* Selected Event Details */}
      <AnimatePresence>
        {selectedEvent && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg"
          >
            <div className="flex items-center justify-between mb-2">
              <h4 className="font-medium text-blue-900">Selected Event</h4>
              <button
                onClick={() => setSelectedEvent(null)}
                className="text-blue-600 hover:text-blue-800"
              >
                ×
              </button>
            </div>
            
            <div className="text-sm space-y-1">
              <div><strong>Title:</strong> {selectedEvent.title}</div>
              <div><strong>Date:</strong> {formatDate(selectedEvent.date)}</div>
              <div><strong>Source:</strong> {selectedEvent.source}</div>
              {selectedEvent.amount && (
                <div><strong>Amount:</strong> {formatValue(selectedEvent.amount)}</div>
              )}
              <div><strong>Description:</strong> {selectedEvent.description}</div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
} 