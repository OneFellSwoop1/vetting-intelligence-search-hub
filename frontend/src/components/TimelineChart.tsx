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
  
  const sortedData = data.sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

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
    <div className="bg-white p-6 rounded-lg shadow-sm border">
      <h3 className="text-lg font-semibold mb-4">Timeline View</h3>
      <div className="relative">
        {/* Timeline line */}
        <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-gray-300"></div>
        
        <div className="space-y-4 max-h-96 overflow-y-auto">
          {sortedData.slice(0, 20).map((item, index) => {
            const isSelected = selectedEvent === item.id;
            const isHovered = hoveredEvent === item.id;
            
            return (
              <div key={item.id} className="relative flex items-start">
                {/* Timeline dot */}
                <div className={`relative z-10 flex items-center justify-center w-12 h-12 rounded-full border-4 border-white shadow-lg ${getSourceColor(item.source)} flex-shrink-0`}>
                  <span className="text-white text-lg">{getSourceIcon(item.source)}</span>
                </div>
                
                {/* Content */}
                <div 
                  className={`ml-6 flex-1 p-4 rounded-lg cursor-pointer transition-all duration-200 ${
                    isSelected ? 'bg-blue-50 border-blue-200 border-2' : 
                    isHovered ? 'bg-gray-50 border-gray-200 border' : 'bg-white border border-gray-200'
                  }`}
                  onClick={() => handleEventClick(item)}
                  onMouseEnter={() => setHoveredEvent(item.id)}
                  onMouseLeave={() => setHoveredEvent(null)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <h4 className="font-semibold text-gray-900 text-sm">{item.title}</h4>
                        {item.amount && (
                          <span className="text-sm font-medium text-green-600">
                            {formatAmount(item.amount)}
                          </span>
                        )}
                      </div>
                      <p className="text-gray-600 text-xs mb-2 line-clamp-2">{item.description}</p>
                      <div className="flex items-center gap-4 text-xs text-gray-500">
                        <span>📅 {formatDate(item.date)}</span>
                        <span>🏷️ {item.type}</span>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          item.source === 'checkbook' ? 'bg-green-100 text-green-800' :
                          item.source === 'senate_lda' ? 'bg-red-100 text-red-800' :
                          item.source === 'nys_ethics' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-orange-100 text-orange-800'
                        }`}>
                          {item.source.replace('_', ' ').toUpperCase()}
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  {(isHovered || isSelected) && (
                    <div className="mt-3 pt-3 border-t border-gray-200">
                      <div className="text-xs text-gray-600">
                        <strong>Full Description:</strong> {item.description}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
        
        {sortedData.length > 20 && (
          <div className="mt-4 text-center text-sm text-gray-500">
            Showing 20 of {sortedData.length} events
          </div>
        )}
        
        {selectedEvent && (
          <div className="mt-4 p-3 bg-blue-50 rounded-lg text-sm text-blue-800">
            Selected: {sortedData.find(d => d.id === selectedEvent)?.title}
          </div>
        )}
      </div>
    </div>
  );
};

export default TimelineChart; 