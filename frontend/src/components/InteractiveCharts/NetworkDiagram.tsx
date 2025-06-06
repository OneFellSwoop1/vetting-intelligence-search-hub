'use client';

import React, { useEffect, useRef, useState } from 'react';
import { Search, ZoomIn, ZoomOut, RotateCcw, Filter, Download, Play, Pause, SkipForward } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export interface NetworkNode {
  id: string;
  label: string;
  type: 'entity' | 'agency' | 'vendor' | 'amount' | 'client';
  value?: number;
  color?: string;
  size?: number;
  metadata?: {
    totalAmount?: number;
    recordCount?: number;
    source?: string;
    year?: string;
  };
}

export interface NetworkEdge {
  id: string;
  from: string;
  to: string;
  label?: string;
  weight?: number;
  type?: 'contract' | 'lobbying' | 'funding' | 'relationship';
  color?: string;
  metadata?: {
    amount?: number;
    date?: string;
    source?: string;
  };
}

export interface NetworkData {
  nodes: NetworkNode[];
  edges: NetworkEdge[];
}

interface NetworkDiagramProps {
  data: NetworkData;
  width?: number;
  height?: number;
  onNodeClick?: (node: NetworkNode) => void;
  onEdgeClick?: (edge: NetworkEdge) => void;
  className?: string;
}

interface SimulationNode extends NetworkNode {
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
  fx?: number | null;
  fy?: number | null;
}

const NetworkDiagram: React.FC<NetworkDiagramProps> = ({
  data,
  width = 800,
  height = 600,
  onNodeClick,
  onEdgeClick,
  className = ''
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const [zoomLevel, setZoomLevel] = useState(1);
  const [selectedNode, setSelectedNode] = useState<NetworkNode | null>(null);
  const [selectedEdge, setSelectedEdge] = useState<NetworkEdge | null>(null);
  const [isAnimating, setIsAnimating] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [nodeFilter, setNodeFilter] = useState<string>('all');
  const [edgeFilter, setEdgeFilter] = useState<string>('all');
  const [showFilters, setShowFilters] = useState(false);
  const [simulationNodes, setSimulationNodes] = useState<SimulationNode[]>([]);
  const [animationSpeed, setAnimationSpeed] = useState(1);

  // Colors for different node types
  const nodeColors = {
    entity: '#3B82F6',     // Blue
    agency: '#10B981',     // Green
    vendor: '#F59E0B',     // Yellow
    amount: '#EF4444',     // Red
    client: '#8B5CF6'      // Purple
  };

  // Colors for different edge types
  const edgeColors = {
    contract: '#6B7280',
    lobbying: '#DC2626',
    funding: '#059669',
    relationship: '#7C3AED'
  };

  // Initialize simulation nodes
  useEffect(() => {
    const nodes: SimulationNode[] = data.nodes.map(node => ({
      ...node,
      x: Math.random() * width,
      y: Math.random() * height,
      vx: 0,
      vy: 0,
      fx: null,
      fy: null
    }));
    setSimulationNodes(nodes);
  }, [data.nodes, width, height]);

  // Simple physics simulation
  useEffect(() => {
    if (!isAnimating) return;

    const interval = setInterval(() => {
      setSimulationNodes(prevNodes => {
        const newNodes = [...prevNodes];
        const alpha = 0.1 * animationSpeed;

        // Apply forces
        for (let i = 0; i < newNodes.length; i++) {
          const node = newNodes[i];
          if (node.fx !== null && node.fy !== null) continue;

          let fx = 0, fy = 0;

          // Repulsion between nodes
          for (let j = 0; j < newNodes.length; j++) {
            if (i === j) continue;
            const other = newNodes[j];
            const dx = (node.x || 0) - (other.x || 0);
            const dy = (node.y || 0) - (other.y || 0);
            const distance = Math.sqrt(dx * dx + dy * dy) || 1;
            const force = 500 / (distance * distance);
            fx += (dx / distance) * force;
            fy += (dy / distance) * force;
          }

          // Attraction along edges
          data.edges.forEach(edge => {
            if (edge.from === node.id) {
              const target = newNodes.find(n => n.id === edge.to);
              if (target) {
                const dx = (target.x || 0) - (node.x || 0);
                const dy = (target.y || 0) - (node.y || 0);
                const distance = Math.sqrt(dx * dx + dy * dy) || 1;
                const force = 0.1 * (edge.weight || 1);
                fx += (dx / distance) * force;
                fy += (dy / distance) * force;
              }
            }
            if (edge.to === node.id) {
              const source = newNodes.find(n => n.id === edge.from);
              if (source) {
                const dx = (source.x || 0) - (node.x || 0);
                const dy = (source.y || 0) - (node.y || 0);
                const distance = Math.sqrt(dx * dx + dy * dy) || 1;
                const force = 0.1 * (edge.weight || 1);
                fx += (dx / distance) * force;
                fy += (dy / distance) * force;
              }
            }
          });

          // Center force
          const centerX = width / 2;
          const centerY = height / 2;
          fx += (centerX - (node.x || 0)) * 0.01;
          fy += (centerY - (node.y || 0)) * 0.01;

          // Update velocity and position
          node.vx = ((node.vx || 0) + fx) * 0.9;
          node.vy = ((node.vy || 0) + fy) * 0.9;
          
          if (node.fx === null) {
            node.x = (node.x || 0) + (node.vx || 0) * alpha;
          }
          if (node.fy === null) {
            node.y = (node.y || 0) + (node.vy || 0) * alpha;
          }

          // Boundary constraints
          node.x = Math.max(20, Math.min(width - 20, node.x || 0));
          node.y = Math.max(20, Math.min(height - 20, node.y || 0));
        }

        return newNodes;
      });
    }, 50);

    return () => clearInterval(interval);
  }, [isAnimating, data.edges, width, height, animationSpeed]);

  // Filter nodes and edges based on search and filters
  const filteredNodes = simulationNodes.filter(node => {
    if (searchTerm && !node.label.toLowerCase().includes(searchTerm.toLowerCase())) {
      return false;
    }
    if (nodeFilter !== 'all' && node.type !== nodeFilter) {
      return false;
    }
    return true;
  });

  const filteredEdges = data.edges.filter(edge => {
    if (edgeFilter !== 'all' && edge.type !== edgeFilter) {
      return false;
    }
    // Only show edges where both nodes are visible
    return filteredNodes.some(n => n.id === edge.from) && 
           filteredNodes.some(n => n.id === edge.to);
  });

  const handleNodeClick = (node: NetworkNode) => {
    setSelectedNode(selectedNode?.id === node.id ? null : node);
    setSelectedEdge(null);
    onNodeClick?.(node);
  };

  const handleEdgeClick = (edge: NetworkEdge) => {
    setSelectedEdge(selectedEdge?.id === edge.id ? null : edge);
    setSelectedNode(null);
    onEdgeClick?.(edge);
  };

  const handleNodeDrag = (nodeId: string, x: number, y: number) => {
    setSimulationNodes(prev => prev.map(node => 
      node.id === nodeId ? { ...node, x, y, fx: x, fy: y } : node
    ));
  };

  const resetLayout = () => {
    setSimulationNodes(prev => prev.map(node => ({
      ...node,
      x: Math.random() * width,
      y: Math.random() * height,
      vx: 0,
      vy: 0,
      fx: null,
      fy: null
    })));
  };

  const exportDiagram = () => {
    if (!svgRef.current) return;
    
    const svgData = new XMLSerializer().serializeToString(svgRef.current);
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    const img = new Image();
    
    canvas.width = width;
    canvas.height = height;
    
    img.onload = function() {
      ctx?.drawImage(img, 0, 0);
      const link = document.createElement('a');
      link.download = 'network-diagram.png';
      link.href = canvas.toDataURL();
      link.click();
    };
    
    img.src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgData)));
  };

  const nodeTypes = Array.from(new Set(data.nodes.map(n => n.type)));
  const edgeTypes = Array.from(new Set(data.edges.map(e => e.type).filter(Boolean) as Array<'contract' | 'lobbying' | 'funding' | 'relationship'>));

  return (
    <div className={`bg-white border border-gray-200 rounded-lg p-4 ${className}`}>
      {/* Controls */}
      <div className="flex flex-wrap items-center justify-between mb-4 gap-4">
        <div className="flex items-center gap-2">
          <h3 className="text-lg font-semibold text-gray-900">Network Analysis</h3>
          <span className="px-2 py-1 bg-blue-100 text-blue-800 text-sm rounded">
            {filteredNodes.length} nodes, {filteredEdges.length} edges
          </span>
        </div>

        <div className="flex items-center gap-2">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search nodes..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 pr-4 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* Filters */}
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`p-2 rounded-md transition-colors ${
              showFilters ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            <Filter className="w-4 h-4" />
          </button>

          {/* Animation Controls */}
          <button
            onClick={() => setIsAnimating(!isAnimating)}
            className={`p-2 rounded-md transition-colors ${
              isAnimating ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'
            }`}
          >
            {isAnimating ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
          </button>

          {/* Zoom Controls */}
          <div className="flex items-center gap-1 border border-gray-300 rounded-md">
            <button
              onClick={() => setZoomLevel(prev => Math.max(0.5, prev - 0.2))}
              className="p-2 hover:bg-gray-100"
            >
              <ZoomOut className="w-4 h-4" />
            </button>
            <span className="px-2 text-sm">{Math.round(zoomLevel * 100)}%</span>
            <button
              onClick={() => setZoomLevel(prev => Math.min(3, prev + 0.2))}
              className="p-2 hover:bg-gray-100"
            >
              <ZoomIn className="w-4 h-4" />
            </button>
          </div>

          {/* Reset */}
          <button
            onClick={resetLayout}
            className="p-2 bg-gray-100 hover:bg-gray-200 rounded-md"
          >
            <RotateCcw className="w-4 h-4" />
          </button>

          {/* Export */}
          <button
            onClick={exportDiagram}
            className="p-2 bg-gray-100 hover:bg-gray-200 rounded-md"
          >
            <Download className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Filters Panel */}
      <AnimatePresence>
        {showFilters && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mb-4 p-4 bg-gray-50 rounded-lg"
          >
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Node Type</label>
                <select
                  value={nodeFilter}
                  onChange={(e) => setNodeFilter(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                >
                  <option value="all">All Types</option>
                  {nodeTypes.map(type => (
                    <option key={type} value={type}>
                      {type.charAt(0).toUpperCase() + type.slice(1)}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Edge Type</label>
                <select
                  value={edgeFilter}
                  onChange={(e) => setEdgeFilter(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                >
                  <option value="all">All Types</option>
                  {edgeTypes.map(type => (
                    <option key={type} value={type}>
                      {type ? type.charAt(0).toUpperCase() + type.slice(1) : 'Unknown'}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Animation Speed</label>
                <input
                  type="range"
                  min="0.1"
                  max="2"
                  step="0.1"
                  value={animationSpeed}
                  onChange={(e) => setAnimationSpeed(parseFloat(e.target.value))}
                  className="w-full"
                />
                <span className="text-sm text-gray-500">{animationSpeed}x</span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* SVG Network Diagram */}
      <div className="border border-gray-300 rounded-lg overflow-hidden">
        <svg
          ref={svgRef}
          width={width}
          height={height}
          viewBox={`0 0 ${width} ${height}`}
          style={{ transform: `scale(${zoomLevel})`, transformOrigin: 'center' }}
          className="bg-gray-50"
        >
          {/* Define arrowhead marker */}
          <defs>
            <marker
              id="arrowhead"
              markerWidth="10"
              markerHeight="7"
              refX="9"
              refY="3.5"
              orient="auto"
            >
              <polygon points="0 0, 10 3.5, 0 7" fill="#6B7280" />
            </marker>
          </defs>

          {/* Edges */}
          {filteredEdges.map(edge => {
            const fromNode = filteredNodes.find(n => n.id === edge.from);
            const toNode = filteredNodes.find(n => n.id === edge.to);
            
            if (!fromNode || !toNode) return null;

            const isSelected = selectedEdge?.id === edge.id;
            const strokeWidth = edge.weight ? Math.max(1, edge.weight * 2) : 2;
            
            return (
              <line
                key={edge.id}
                x1={fromNode.x}
                y1={fromNode.y}
                x2={toNode.x}
                y2={toNode.y}
                stroke={isSelected ? '#DC2626' : (edge.color || edgeColors[edge.type || 'relationship'])}
                strokeWidth={isSelected ? strokeWidth + 2 : strokeWidth}
                strokeOpacity={0.7}
                markerEnd="url(#arrowhead)"
                className="cursor-pointer hover:stroke-opacity-100"
                onClick={() => handleEdgeClick(edge)}
              />
            );
          })}

          {/* Nodes */}
          {filteredNodes.map(node => {
            const isSelected = selectedNode?.id === node.id;
            const radius = (node.size || 10) + (isSelected ? 5 : 0);
            const color = node.color || nodeColors[node.type];

            return (
              <g key={node.id} className="cursor-pointer">
                <circle
                  cx={node.x}
                  cy={node.y}
                  r={radius}
                  fill={color}
                  stroke={isSelected ? '#DC2626' : '#FFFFFF'}
                  strokeWidth={isSelected ? 3 : 2}
                  className="hover:opacity-80"
                  onClick={() => handleNodeClick(node)}
                  onMouseDown={(e) => {
                    const svg = svgRef.current;
                    if (!svg) return;

                    const rect = svg.getBoundingClientRect();
                    const startX = e.clientX - rect.left;
                    const startY = e.clientY - rect.top;

                    const handleMouseMove = (e: MouseEvent) => {
                      const x = (e.clientX - rect.left) / zoomLevel;
                      const y = (e.clientY - rect.top) / zoomLevel;
                      handleNodeDrag(node.id, x, y);
                    };

                    const handleMouseUp = () => {
                      document.removeEventListener('mousemove', handleMouseMove);
                      document.removeEventListener('mouseup', handleMouseUp);
                    };

                    document.addEventListener('mousemove', handleMouseMove);
                    document.addEventListener('mouseup', handleMouseUp);
                  }}
                />
                
                {/* Node Label */}
                <text
                  x={node.x}
                  y={(node.y || 0) + radius + 15}
                  textAnchor="middle"
                  fontSize="12"
                  fill="#374151"
                  className="pointer-events-none select-none"
                >
                  {node.label.length > 15 ? node.label.substring(0, 12) + '...' : node.label}
                </text>
                
                {/* Value indicator */}
                {node.value && (
                  <text
                    x={node.x}
                    y={(node.y || 0) + 4}
                    textAnchor="middle"
                    fontSize="10"
                    fill="#FFFFFF"
                    fontWeight="bold"
                    className="pointer-events-none select-none"
                  >
                    {node.value > 1000000 ? `${(node.value / 1000000).toFixed(1)}M` :
                     node.value > 1000 ? `${(node.value / 1000).toFixed(1)}K` :
                     node.value.toString()}
                  </text>
                )}
              </g>
            );
          })}
        </svg>
      </div>

      {/* Selection Info Panel */}
      <AnimatePresence>
        {(selectedNode || selectedEdge) && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg"
          >
            {selectedNode && (
              <div>
                <h4 className="font-semibold text-blue-900 mb-2">Node: {selectedNode.label}</h4>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="font-medium">Type:</span> {selectedNode.type}
                  </div>
                  {selectedNode.metadata?.totalAmount && (
                    <div>
                      <span className="font-medium">Total Amount:</span> ${selectedNode.metadata.totalAmount.toLocaleString()}
                    </div>
                  )}
                  {selectedNode.metadata?.recordCount && (
                    <div>
                      <span className="font-medium">Records:</span> {selectedNode.metadata.recordCount}
                    </div>
                  )}
                  {selectedNode.metadata?.source && (
                    <div>
                      <span className="font-medium">Source:</span> {selectedNode.metadata.source}
                    </div>
                  )}
                </div>
              </div>
            )}

            {selectedEdge && (
              <div>
                <h4 className="font-semibold text-blue-900 mb-2">
                  Connection: {selectedEdge.label || `${selectedEdge.from} → ${selectedEdge.to}`}
                </h4>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="font-medium">Type:</span> {selectedEdge.type || 'relationship'}
                  </div>
                  {selectedEdge.metadata?.amount && (
                    <div>
                      <span className="font-medium">Amount:</span> ${selectedEdge.metadata.amount.toLocaleString()}
                    </div>
                  )}
                  {selectedEdge.metadata?.date && (
                    <div>
                      <span className="font-medium">Date:</span> {selectedEdge.metadata.date}
                    </div>
                  )}
                  {selectedEdge.metadata?.source && (
                    <div>
                      <span className="font-medium">Source:</span> {selectedEdge.metadata.source}
                    </div>
                  )}
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Legend */}
      <div className="mt-4 flex flex-wrap gap-4 text-sm">
        <div className="flex items-center gap-2">
          <span className="font-medium">Node Types:</span>
          {Object.entries(nodeColors).map(([type, color]) => (
            <div key={type} className="flex items-center gap-1">
              <div className="w-3 h-3 rounded-full" style={{ backgroundColor: color }} />
              <span>{type}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default NetworkDiagram; 