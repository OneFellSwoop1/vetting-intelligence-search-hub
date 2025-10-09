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
    <div className="h-full">
      <h3 className="text-2xl font-bold text-white mb-6 flex items-center gap-3">
        <div className="w-8 h-8 bg-gradient-to-r from-green-400 to-emerald-400 rounded-lg flex items-center justify-center">
          <span className="text-white text-sm">🕸️</span>
        </div>
        Entity Relationships
      </h3>
      
      {/* Network visualization */}
      <div className="relative">
        {/* Grid layout for nodes */}
        <div className="grid grid-cols-4 md:grid-cols-6 gap-4 mb-8">
          {nodes.slice(0, 24).map((node) => {
            const isSelected = selectedNode === node.id;
            const isHovered = hoveredNode === node.id;
            const connections = getConnectedNodes(node.id);
            
            return (
              <div
                key={node.id}
                className={`relative flex flex-col items-center p-4 rounded-xl cursor-pointer transition-all duration-300 backdrop-blur-sm border ${
                  isSelected 
                    ? 'bg-blue-500/20 border-blue-400/50 scale-110 shadow-2xl' 
                    : isHovered 
                      ? 'bg-white/10 border-white/30 scale-105' 
                      : 'bg-white/5 border-white/10 hover:bg-white/10'
                }`}
                onClick={() => handleNodeClick(node)}
                onMouseEnter={() => setHoveredNode(node.id)}
                onMouseLeave={() => setHoveredNode(null)}
              >
                {/* Node circle */}
                <div className={`${getNodeSize(node.value)} rounded-full flex items-center justify-center text-white font-bold shadow-2xl border-4 border-slate-900 transition-all duration-300 bg-gradient-to-r ${
                  node.type === 'entity' ? 'from-blue-500 to-blue-600' :
                  node.type === 'vendor' ? 'from-green-500 to-green-600' :
                  node.type === 'agency' ? 'from-purple-500 to-purple-600' :
                  node.type === 'lobbyist' ? 'from-orange-500 to-orange-600' :
                  'from-red-500 to-red-600'
                }`}>
                  <span>{getNodeIcon(node.type)}</span>
                </div>
                
                {/* Node label */}
                <div className="mt-3 text-center">
                  <div className="text-xs font-semibold text-white line-clamp-2 h-8">
                    {node.name}
                  </div>
                  <div className="text-xs text-gray-300 mt-1 capitalize">
                    {node.type}
                  </div>
                  {node.value && (
                    <div className="text-xs font-bold text-green-400 mt-1 bg-green-500/20 px-2 py-1 rounded-lg">
                      {formatValue(node.value)}
                    </div>
                  )}
                </div>
                
                {/* Connection indicator */}
                {connections.length > 0 && (
                  <div className="absolute -top-2 -right-2 bg-gradient-to-r from-red-500 to-pink-500 text-white text-xs rounded-full w-6 h-6 flex items-center justify-center shadow-lg border-2 border-slate-900">
                    {connections.length}
                  </div>
                )}
                
                {/* Hover details */}
                {isHovered && (
                  <div className="absolute bottom-full mb-3 left-1/2 transform -translate-x-1/2 bg-black/80 backdrop-blur-sm text-white text-xs rounded-lg py-2 px-3 whitespace-nowrap z-10 border border-white/20">
                    {connections.length} connection{connections.length !== 1 ? 's' : ''}
                  </div>
                )}
              </div>
            );
          })}
        </div>
        
        {/* Connection summary */}
        {edges.length > 0 && (
          <div className="border-t border-white/20 pt-6">
            <h4 className="font-semibold text-white mb-4 flex items-center gap-2">
              <div className="w-5 h-5 bg-gradient-to-r from-cyan-400 to-blue-400 rounded-lg flex items-center justify-center">
                <span className="text-white text-xs">🔗</span>
              </div>
              Connection Summary
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {edges.slice(0, 6).map((edge, index) => {
                const sourceNode = nodes.find(n => n.id === edge.source);
                const targetNode = nodes.find(n => n.id === edge.target);
                
                return (
                  <div key={index} className="flex items-center gap-3 p-3 backdrop-blur-sm bg-white/5 rounded-xl text-sm border border-white/10">
                    <span className="text-gray-300 truncate flex-1">{sourceNode?.name || edge.source}</span>
                    <div className="w-6 h-6 bg-gradient-to-r from-blue-400 to-purple-400 rounded-full flex items-center justify-center">
                      <span className="text-white text-xs">↔</span>
                    </div>
                    <span className="text-gray-300 truncate flex-1">{targetNode?.name || edge.target}</span>
                    <span className="text-xs font-bold text-blue-400 bg-blue-500/20 px-2 py-1 rounded-lg">
                      {edge.weight}
                    </span>
                  </div>
                );
              })}
            </div>
            
            {edges.length > 6 && (
              <div className="mt-4 text-center text-sm text-gray-400 backdrop-blur-sm bg-white/5 rounded-lg p-3 border border-white/10">
                Showing 6 of {edges.length} connections
              </div>
            )}
          </div>
        )}
        
        {nodes.length > 24 && (
          <div className="mt-6 text-center text-sm text-gray-400 backdrop-blur-sm bg-white/5 rounded-lg p-3 border border-white/10">
            Showing 24 of {nodes.length} entities
          </div>
        )}
        
        {selectedNode && (
          <div className="mt-6 p-4 bg-gradient-to-r from-blue-500/20 to-purple-500/20 rounded-xl text-sm text-blue-200 border border-blue-400/30 backdrop-blur-sm">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
              Selected: {nodes.find(n => n.id === selectedNode)?.name} 
              ({nodes.find(n => n.id === selectedNode)?.type})
            </div>
          </div>
        )}
        
        {/* Legend */}
        <div className="mt-6 border-t border-white/20 pt-4">
          <h5 className="text-sm font-semibold text-white mb-3">Entity Types</h5>
          <div className="flex flex-wrap gap-4 text-xs">
            {['entity', 'vendor', 'agency', 'lobbyist', 'client'].map(type => (
              <div key={type} className="flex items-center gap-2 backdrop-blur-sm bg-white/5 rounded-lg px-3 py-2 border border-white/10">
                <div className={`w-4 h-4 rounded-full bg-gradient-to-r ${
                  type === 'entity' ? 'from-blue-500 to-blue-600' :
                  type === 'vendor' ? 'from-green-500 to-green-600' :
                  type === 'agency' ? 'from-purple-500 to-purple-600' :
                  type === 'lobbyist' ? 'from-orange-500 to-orange-600' :
                  'from-red-500 to-red-600'
                }`} />
                <span className="capitalize text-gray-300 font-medium">{type}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default NetworkDiagram; 