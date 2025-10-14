import React, { useState } from 'react';

interface TimelineData {
  id: string;
  date: string;
  title: string;
  description: string;
  amount?: number;
  source: string;
  type: string;
}

interface TimelineChartProps {
  data: TimelineData[];
  onEventClick: (event: TimelineData) => void;
}

const TimelineChart: React.FC<TimelineChartProps> = ({ data, onEventClick }) => {
  const [selectedEvent, setSelectedEvent] = useState<string | null>(null);
  const [hoveredEvent, setHoveredEvent] = useState<string | null>(null);
  
  const sortedData = data.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());

  const getSourceColor = (source: string) => {
    const colors: Record<string, string> = {
      'checkbook': 'bg-green-500',
      'senate_lda': 'bg-red-500',  
      'nys_ethics': 'bg-yellow-500',
      'nyc_lobbyist': 'bg-orange-500',
    };
    return colors[source] || 'bg-gray-500';
  };

  const getSourceIcon = (source: string) => {
    const icons: Record<string, string> = {
      'checkbook': '📋',
      'senate_lda': '🏛️',  
      'nys_ethics': '🏛️',
      'nyc_lobbyist': '🤝',
    };
    return icons[source] || '📄';
  };

  const formatDate = (dateStr: string) => {
    try {
      return new Date(dateStr).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    } catch {
      return dateStr;
    }
  };

  const formatAmount = (amount?: number) => {
    if (!amount) return '';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const handleEventClick = (event: TimelineData) => {
    setSelectedEvent(event.id);
    onEventClick(event);
  };

  return (
    <div className="h-full">
      <h3 className="text-2xl font-bold text-white mb-6 flex items-center gap-3">
        <div className="w-8 h-8 bg-gradient-to-r from-purple-400 to-pink-400 rounded-lg flex items-center justify-center">
          <span className="text-white text-sm">📅</span>
        </div>
        Timeline View
      </h3>
      <div className="relative">
        {/* Timeline line */}
        <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-gradient-to-b from-blue-400 via-purple-400 to-pink-400 opacity-60"></div>
        
        <div className="space-y-6 max-h-96 overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-white/20 scrollbar-track-transparent">
          {sortedData.slice(0, 20).map((item, index) => {
            const isSelected = selectedEvent === item.id;
            const isHovered = hoveredEvent === item.id;
            
            return (
              <div key={item.id} className="relative flex items-start">
                {/* Timeline dot */}
                <div className={`relative z-10 flex items-center justify-center w-12 h-12 rounded-full border-4 border-slate-900 shadow-2xl flex-shrink-0 bg-gradient-to-r ${
                  item.source === 'checkbook' ? 'from-green-500 to-emerald-500' :
                  item.source === 'senate_lda' ? 'from-red-500 to-pink-500' :
                  item.source === 'nys_ethics' ? 'from-yellow-500 to-orange-500' :
                  'from-orange-500 to-red-500'
                }`}>
                  <span className="text-white text-lg">{getSourceIcon(item.source)}</span>
                </div>
                
                {/* Content */}
                <div 
                  className={`ml-6 flex-1 p-4 rounded-xl cursor-pointer transition-all duration-300 backdrop-blur-sm border ${
                    isSelected 
                      ? 'bg-blue-500/20 border-blue-400/50 scale-105 shadow-lg' 
                      : isHovered 
                        ? 'bg-white/10 border-white/30 scale-102' 
                        : 'bg-white/5 border-white/10 hover:bg-white/10'
                  }`}
                  onClick={() => handleEventClick(item)}
                  onMouseEnter={() => setHoveredEvent(item.id)}
                  onMouseLeave={() => setHoveredEvent(null)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h4 className="font-semibold text-white text-sm">{item.title}</h4>
                        {item.amount && (
                          <span className="text-sm font-bold text-green-400 bg-green-500/20 px-2 py-1 rounded-lg">
                            {formatAmount(item.amount)}
                          </span>
                        )}
                      </div>
                      <p className="text-gray-300 text-xs mb-3 line-clamp-2">{item.description}</p>
                      <div className="flex items-center gap-3 text-xs">
                        <span className="text-blue-300 flex items-center gap-1">
                          📅 {formatDate(item.date)}
                        </span>
                        <span className="text-purple-300 flex items-center gap-1">
                          🏷️ {item.type}
                        </span>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium backdrop-blur-sm ${
                          item.source === 'checkbook' ? 'bg-green-500/20 text-green-300 border border-green-400/30' :
                          item.source === 'senate_lda' ? 'bg-red-500/20 text-red-300 border border-red-400/30' :
                          item.source === 'nys_ethics' ? 'bg-yellow-500/20 text-yellow-300 border border-yellow-400/30' :
                          'bg-orange-500/20 text-orange-300 border border-orange-400/30'
                        }`}>
                          {item.source.replace('_', ' ').toUpperCase()}
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  {(isHovered || isSelected) && (
                    <div className="mt-4 pt-4 border-t border-white/20">
                      <div className="text-xs text-gray-300 backdrop-blur-sm bg-white/5 rounded-lg p-3 border border-white/10">
                        <strong className="text-white">Full Description:</strong> {item.description}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
        
        {sortedData.length > 20 && (
          <div className="mt-6 text-center text-sm text-gray-400 backdrop-blur-sm bg-white/5 rounded-lg p-3 border border-white/10">
            Showing 20 of {sortedData.length} events
          </div>
        )}
        
        {selectedEvent && (
          <div className="mt-6 p-4 bg-gradient-to-r from-blue-500/20 to-purple-500/20 rounded-xl text-sm text-blue-200 border border-blue-400/30 backdrop-blur-sm">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
              Selected: {sortedData.find(d => d.id === selectedEvent)?.title}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default TimelineChart; 