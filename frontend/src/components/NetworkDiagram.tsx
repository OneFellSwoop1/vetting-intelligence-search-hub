import React, { useState } from 'react';

interface NetworkNode {
  id: string;
  name: string;
  type: string;
  value?: number;
}

interface NetworkEdge {
  source: string;
  target: string;
  weight: number;
}

interface NetworkDiagramProps {
  nodes: NetworkNode[];
  edges: NetworkEdge[];
  onNodeClick: (node: NetworkNode) => void;
}

const NetworkDiagram: React.FC<NetworkDiagramProps> = ({ nodes, edges, onNodeClick }) => {
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);

  const getNodeColor = (type: string) => {
    const colors: Record<string, string> = {
      'entity': 'bg-blue-500',
      'vendor': 'bg-green-500',
      'agency': 'bg-purple-500',
      'lobbyist': 'bg-orange-500',
      'client': 'bg-red-500',
    };
    return colors[type] || 'bg-gray-500';
  };

  const getNodeIcon = (type: string) => {
    const icons: Record<string, string> = {
      'entity': '🏢',
      'vendor': '📦',
      'agency': '🏛️',
      'lobbyist': '🤝',
      'client': '👥',
    };
    return icons[type] || '🔵';
  };

  const getNodeSize = (value?: number) => {
    if (!value) return 'w-12 h-12';
    if (value > 1000000) return 'w-20 h-20 text-lg';
    if (value > 100000) return 'w-16 h-16';
    return 'w-12 h-12 text-sm';
  };

  const handleNodeClick = (node: NetworkNode) => {
    setSelectedNode(node.id);
    onNodeClick(node);
  };

  const getConnectedNodes = (nodeId: string) => {
    return edges.filter(edge => edge.source === nodeId || edge.target === nodeId);
  };

  const formatValue = (value?: number) => {
    if (!value) return '';
    if (value > 1000000) return `$${(value / 1000000).toFixed(1)}M`;
    if (value > 1000) return `$${(value / 1000).toFixed(0)}K`;
    return `$${value.toLocaleString()}`;
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border">
      <h3 className="text-lg font-semibold mb-4">Entity Relationships</h3>
      
      {/* Network visualization */}
      <div className="relative">
        {/* Grid layout for nodes */}
        <div className="grid grid-cols-4 md:grid-cols-6 gap-4 mb-6">
          {nodes.slice(0, 24).map((node) => {
            const isSelected = selectedNode === node.id;
            const isHovered = hoveredNode === node.id;
            const connections = getConnectedNodes(node.id);
            
            return (
              <div
                key={node.id}
                className={`relative flex flex-col items-center p-3 rounded-lg cursor-pointer transition-all duration-200 ${
                  isSelected ? 'bg-blue-50 border-blue-200 border-2 scale-110' : 
                  isHovered ? 'bg-gray-50 border-gray-200 border scale-105' : 'bg-white border border-gray-200'
                }`}
                onClick={() => handleNodeClick(node)}
                onMouseEnter={() => setHoveredNode(node.id)}
                onMouseLeave={() => setHoveredNode(null)}
              >
                {/* Node circle */}
                <div className={`${getNodeSize(node.value)} ${getNodeColor(node.type)} rounded-full flex items-center justify-center text-white font-bold shadow-lg border-4 border-white transition-all duration-200`}>
                  <span>{getNodeIcon(node.type)}</span>
                </div>
                
                {/* Node label */}
                <div className="mt-2 text-center">
                  <div className="text-xs font-medium text-gray-900 line-clamp-2 h-8">
                    {node.name}
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    {node.type}
                  </div>
                  {node.value && (
                    <div className="text-xs font-semibold text-green-600 mt-1">
                      {formatValue(node.value)}
                    </div>
                  )}
                </div>
                
                {/* Connection indicator */}
                {connections.length > 0 && (
                  <div className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                    {connections.length}
                  </div>
                )}
                
                {/* Hover details */}
                {isHovered && (
                  <div className="absolute bottom-full mb-2 left-1/2 transform -translate-x-1/2 bg-black text-white text-xs rounded py-1 px-2 whitespace-nowrap z-10">
                    {connections.length} connection{connections.length !== 1 ? 's' : ''}
                  </div>
                )}
              </div>
            );
          })}
        </div>
        
        {/* Connection summary */}
        {edges.length > 0 && (
          <div className="border-t pt-4">
            <h4 className="font-medium text-gray-900 mb-3">Connection Summary</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {edges.slice(0, 6).map((edge, index) => {
                const sourceNode = nodes.find(n => n.id === edge.source);
                const targetNode = nodes.find(n => n.id === edge.target);
                
                return (
                  <div key={index} className="flex items-center gap-2 p-2 bg-gray-50 rounded text-sm">
                    <span className="text-gray-600">{sourceNode?.name || edge.source}</span>
                    <span className="text-gray-400">↔</span>
                    <span className="text-gray-600">{targetNode?.name || edge.target}</span>
                    <span className="ml-auto text-xs font-medium text-blue-600">
                      {edge.weight}
                    </span>
                  </div>
                );
              })}
            </div>
            
            {edges.length > 6 && (
              <div className="mt-2 text-xs text-gray-500 text-center">
                Showing 6 of {edges.length} connections
              </div>
            )}
          </div>
        )}
        
        {nodes.length > 24 && (
          <div className="mt-4 text-center text-sm text-gray-500">
            Showing 24 of {nodes.length} entities
          </div>
        )}
        
        {selectedNode && (
          <div className="mt-4 p-3 bg-blue-50 rounded-lg text-sm text-blue-800">
            Selected: {nodes.find(n => n.id === selectedNode)?.name} 
            ({nodes.find(n => n.id === selectedNode)?.type})
          </div>
        )}
        
        {/* Legend */}
        <div className="mt-4 flex flex-wrap gap-3 text-xs">
          {['entity', 'vendor', 'agency', 'lobbyist', 'client'].map(type => (
            <div key={type} className="flex items-center gap-1">
              <div className={`w-3 h-3 ${getNodeColor(type)} rounded-full`} />
              <span className="capitalize text-gray-600">{type}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default NetworkDiagram; 