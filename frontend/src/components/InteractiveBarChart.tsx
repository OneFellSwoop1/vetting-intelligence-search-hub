import React, { useState } from 'react';

interface ChartData {
  id: string;
  name: string;
  value: number;
  category: string;
  source: string;
}

interface InteractiveBarChartProps {
  data: ChartData[];
  onSelectionChange: (selection: any) => void;
}

const InteractiveBarChart: React.FC<InteractiveBarChartProps> = ({ data, onSelectionChange }) => {
  const [selectedItem, setSelectedItem] = useState<string | null>(null);
  const [hoveredItem, setHoveredItem] = useState<string | null>(null);

  const maxValue = Math.max(...data.map(d => d.value));
  
  const handleItemClick = (item: ChartData) => {
    setSelectedItem(item.id);
    onSelectionChange(item);
  };

  const getSourceColor = (source: string) => {
    const colors: Record<string, string> = {
      'checkbook': '#10B981', // green
      'senate_lda': '#EF4444', // red  
      'nys_ethics': '#F59E0B', // yellow
      'nyc_lobbyist': '#F97316', // orange
    };
    return colors[source] || '#6B7280';
  };

  return (
    <div className="h-full">
      <h3 className="text-2xl font-bold text-white mb-6 flex items-center gap-3">
        <div className="w-8 h-8 bg-gradient-to-r from-blue-400 to-purple-400 rounded-lg flex items-center justify-center">
          <span className="text-white text-sm">📊</span>
        </div>
        Data Sources Overview
      </h3>
      <div className="space-y-4">
        {data.map((item) => {
          const isSelected = selectedItem === item.id;
          const isHovered = hoveredItem === item.id;
          const percentage = Math.round((item.value / maxValue) * 100);
          
          return (
            <div 
              key={item.id} 
              className={`p-4 rounded-xl cursor-pointer transition-all duration-300 backdrop-blur-sm border ${
                isSelected 
                  ? 'bg-blue-500/20 border-blue-400/50 scale-105' 
                  : isHovered 
                    ? 'bg-white/10 border-white/30 scale-102' 
                    : 'bg-white/5 border-white/10 hover:bg-white/10'
              }`}
              onClick={() => handleItemClick(item)}
              onMouseEnter={() => setHoveredItem(item.id)}
              onMouseLeave={() => setHoveredItem(null)}
            >
              <div className="flex items-center justify-between mb-3">
                <span className="font-semibold text-white">{item.name}</span>
                <span className="text-sm font-bold text-gray-300">{item.value.toLocaleString()}</span>
              </div>
              <div className="relative">
                <div className="bg-white/10 h-3 rounded-full overflow-hidden backdrop-blur-sm">
                  <div 
                    className="h-full rounded-full transition-all duration-700 ease-out bg-gradient-to-r"
                    style={{ 
                      width: `${percentage}%`,
                      backgroundImage: `linear-gradient(90deg, ${getSourceColor(item.source)}, ${getSourceColor(item.source)}dd)`,
                    }}
                  />
                </div>
                <div className="absolute right-0 top-0 h-3 flex items-center pr-2">
                  <span className="text-xs text-white font-semibold">
                    {percentage}%
                  </span>
                </div>
              </div>
              {isHovered && (
                <div className="mt-3 text-xs text-gray-300 backdrop-blur-sm bg-white/5 rounded-lg p-2 border border-white/10">
                  Source: {item.source} • Category: {item.category}
                </div>
              )}
            </div>
          );
        })}
      </div>
      {selectedItem && (
        <div className="mt-6 p-4 bg-gradient-to-r from-blue-500/20 to-purple-500/20 rounded-xl text-sm text-blue-200 border border-blue-400/30 backdrop-blur-sm">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
            Selected: {data.find(d => d.id === selectedItem)?.name}
          </div>
        </div>
      )}
    </div>
  );
};

export default InteractiveBarChart; 