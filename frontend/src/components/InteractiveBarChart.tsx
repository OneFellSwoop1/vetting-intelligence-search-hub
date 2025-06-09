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
    <div className="bg-white p-6 rounded-lg shadow-sm border">
      <h3 className="text-lg font-semibold mb-4">Data Sources Overview</h3>
      <div className="space-y-3">
        {data.map((item) => {
          const isSelected = selectedItem === item.id;
          const isHovered = hoveredItem === item.id;
          const barWidth = Math.max(20, (item.value / maxValue) * 300);
          
          return (
            <div 
              key={item.id} 
              className={`p-3 rounded-lg cursor-pointer transition-all duration-200 ${
                isSelected ? 'bg-blue-50 border-blue-200 border-2' : 
                isHovered ? 'bg-gray-50' : 'bg-white border border-gray-200'
              }`}
              onClick={() => handleItemClick(item)}
              onMouseEnter={() => setHoveredItem(item.id)}
              onMouseLeave={() => setHoveredItem(null)}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium text-gray-900">{item.name}</span>
                <span className="text-sm font-semibold text-gray-700">{item.value.toLocaleString()}</span>
              </div>
              <div className="relative">
                <div className="bg-gray-200 h-6 rounded-full overflow-hidden">
                  <div 
                    className="h-full rounded-full transition-all duration-500 ease-out"
                    style={{ 
                      width: `${barWidth}px`,
                      backgroundColor: getSourceColor(item.source),
                      maxWidth: '100%'
                    }}
                  />
                </div>
                <div className="absolute right-0 top-0 h-6 flex items-center pr-2">
                  <span className="text-xs text-white font-medium">
                    {Math.round((item.value / maxValue) * 100)}%
                  </span>
                </div>
              </div>
              {isHovered && (
                <div className="mt-2 text-xs text-gray-600">
                  Source: {item.source} • Category: {item.category}
                </div>
              )}
            </div>
          );
        })}
      </div>
      {selectedItem && (
        <div className="mt-4 p-3 bg-blue-50 rounded-lg text-sm text-blue-800">
          Selected: {data.find(d => d.id === selectedItem)?.name}
        </div>
      )}
    </div>
  );
};

export default InteractiveBarChart; 