'use client';

import React, { useState, useEffect } from 'react';
import Image from 'next/image';
import { Search, Filter, Calendar, Building, DollarSign, ExternalLink, Eye, FileText, TrendingUp, Sparkles, Shield, Zap, Globe, BarChart3, Users, Database } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import InteractiveBarChart from '@/components/InteractiveBarChart';
import TimelineChart from '@/components/TimelineChart';
import NetworkDiagram from '@/components/NetworkDiagram';
import DetailedResultView from '@/components/enhanced-results/DetailedResultView';
import CheckbookStyleResults from '@/components/enhanced-search/CheckbookStyleResults';
import NYCLobbyistStyleResults from '@/components/enhanced-search/NYCLobbyistStyleResults';
import CheckbookNYCStyleResults from '@/components/enhanced-search/CheckbookNYCStyleResults';
import FECStyleResults from '@/components/enhanced-search/FECStyleResults';

// Chart interfaces
interface ChartData {
  id: string;
  name: string;
  value: number;
  category: string;
  source: string;
}

interface TimelineData {
  id: string;
  date: string;
  title: string;
  description: string;
  amount?: number;
  source: string;
  type: string;
}

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

interface NetworkData {
  nodes: NetworkNode[];
  edges: NetworkEdge[];
}

// Main search page for the Vetting Intelligence Search Hub
// This will eventually replace pages/index.js

interface SearchResult {
  id?: string;
  title: string;
  description: string;
  amount?: string | number;
  date?: string;
  source: string;
  vendor?: string;
  agency?: string;
  url?: string;
  record_type?: string;
  client_count?: number;
  registration_count?: number;
  year?: string;
}

interface SearchResponse {
  results: SearchResult[];
  total_hits: Record<string, number>;
  query: string;
  cache_hit: boolean;
}

interface SearchFilters {
  year?: string;
  jurisdiction?: string;
  source?: string;
  minAmount?: string;
  recordType?: string;
}

const sourceConfig = {
  senate_lda: { name: 'Senate LDA (House & Senate Lobbying)', color: 'bg-red-100 text-red-800', icon: '🏛️' },
  checkbook: { name: 'NYC Contracts', color: 'bg-green-100 text-green-800', icon: '📋' },
  fec: { name: 'FEC Campaign Finance', color: 'bg-blue-100 text-blue-800', icon: '🗳️' },
  nys_ethics: { name: 'NY State', color: 'bg-yellow-100 text-yellow-800', icon: '🏛️' },
  nyc_lobbyist: { name: 'NYC Lobbyist', color: 'bg-orange-100 text-orange-800', icon: '🤝' }
};



export default function VettingIntelligenceHub() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [totalHits, setTotalHits] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [currentView, setCurrentView] = useState<'search' | 'analytics' | 'details'>('analytics');
  const [selectedResult, setSelectedResult] = useState<SearchResult | null>(null);
  const [filters, setFilters] = useState<SearchFilters>({});
  const [showFilters, setShowFilters] = useState(false);
  const [displayCount, setDisplayCount] = useState(15);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [activeDataSource, setActiveDataSource] = useState<string>('all');
  
  // Refs for scrolling to specific sections
  const checkbookRef = React.useRef<HTMLDivElement>(null);
  const senateLdaRef = React.useRef<HTMLDivElement>(null);
  const nycLobbyistRef = React.useRef<HTMLDivElement>(null);
  const fecRef = React.useRef<HTMLDivElement>(null);
  const nysEthicsRef = React.useRef<HTMLDivElement>(null);

  // Helper function to scroll to specific data source section
  const scrollToDataSource = (source: string) => {
    setActiveDataSource(source);
    
    if (source === 'all') {
      window.scrollTo({ top: 0, behavior: 'smooth' });
      return;
    }
    
    // Map source names to refs
    const refMap: { [key: string]: React.RefObject<HTMLDivElement> } = {
      'checkbook': checkbookRef,
      'senate_lda': senateLdaRef,
      'nyc_lobbyist': nycLobbyistRef,
      'fec': fecRef,
      'nys_ethics': nysEthicsRef
    };
    
    const targetRef = refMap[source];
    if (targetRef && targetRef.current) {
      // Scroll to the section with some offset for better visibility
      const elementPosition = targetRef.current.getBoundingClientRect().top + window.pageYOffset;
      const offsetPosition = elementPosition - 100; // 100px offset from top
      
      window.scrollTo({
        top: offsetPosition,
        behavior: 'smooth'
      });
    }
  };

  // Group NYC Lobbyist results by year for better organization
  const groupNYCResultsByYear = React.useCallback((results: SearchResult[]) => {
    const nycResults = results.filter(r => r.source === 'nyc_lobbyist');
    const otherResults = results.filter(r => r.source !== 'nyc_lobbyist');
    
    if (nycResults.length === 0) return results;
    
    // Group NYC results by year
    const yearGroups: { [year: string]: SearchResult[] } = {};
    nycResults.forEach(result => {
      const year = result.year || new Date(result.date || '').getFullYear().toString();
      if (!yearGroups[year]) yearGroups[year] = [];
      yearGroups[year].push(result);
    });
    
    // Sort years in descending order
    const sortedYears = Object.keys(yearGroups).sort((a, b) => parseInt(b) - parseInt(a));
    
    // Create grouped results
    const groupedResults: SearchResult[] = [];
    
    // Add other results first
    groupedResults.push(...otherResults);
    
    // Add NYC results grouped by year
    sortedYears.forEach(year => {
      // Add a year header result
      groupedResults.push({
        title: `NYC Lobbying Activities - ${year}`,
        description: `${yearGroups[year].length} lobbying records from ${year}`,
        source: 'nyc_lobbyist_year_header',
        year: year,
        client_count: yearGroups[year].reduce((sum, r) => sum + (r.client_count || 0), 0),
        registration_count: yearGroups[year].length
      });
      
      // Add the actual results for this year
      groupedResults.push(...yearGroups[year]);
    });
    
    return groupedResults;
  }, []);

  const searchData = async () => {
    if (!query.trim()) return;
    
    setLoading(true);
    setError('');
    
    try {
      const response = await fetch('http://127.0.0.1:8000/api/v1/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: query.trim(),
          year: filters.year || null,
          jurisdiction: filters.jurisdiction || null
        }),
      });

      if (!response.ok) {
        throw new Error('Search failed');
      }

      const responseData = await response.json();
      // Handle both old and new response formats
      const data = responseData.data || responseData;
      setResults(data.results || []);
      setTotalHits(data.total_hits || {});
    } catch (err) {
      setError('Failed to search. Please check your connection.');
      console.error('Search error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      searchData();
    }
  };

  const handleViewDetails = (result: SearchResult) => {
    setSelectedResult(result);
    setShowDetailModal(true);
  };

  const handleCloseDetailModal = () => {
    setShowDetailModal(false);
    setSelectedResult(null);
  };

  // Filtered results based on active filters
  const filteredResults = React.useMemo(() => {
    return results.filter(result => {
      if (filters.source && result.source !== filters.source) return false;
      if (filters.recordType && result.record_type !== filters.recordType) return false;
      if (filters.minAmount && result.amount) {
        const amount = typeof result.amount === 'number' 
          ? result.amount 
          : parseFloat(result.amount.replace(/[$,]/g, ''));
        const minAmount = parseFloat(filters.minAmount);
        if (amount < minAmount) return false;
      }
      return true;
    });
  }, [results, filters]);

  // Apply year grouping for NYC Lobbyist results
  const displayResults = React.useMemo(() => {
    return groupNYCResultsByYear(filteredResults);
  }, [filteredResults, groupNYCResultsByYear]);

  const ResultCard = ({ result }: { result: SearchResult }) => {
    const sourceInfo = sourceConfig[result.source as keyof typeof sourceConfig] || 
                      { name: result.source, color: 'bg-gray-100 text-gray-800', icon: '📄' };

    // Handle year header cards for NYC Lobbyist grouping
    if (result.source === 'nyc_lobbyist_year_header') {
      return (
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-4 mb-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-500 rounded-lg flex items-center justify-center">
                <Calendar className="w-5 h-5 text-white" />
              </div>
              <div>
                <h3 className="font-semibold text-blue-900">{result.title}</h3>
                <p className="text-sm text-blue-700">{result.description}</p>
              </div>
            </div>
            <div className="flex gap-2">
              <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
                {result.client_count} Total Clients
              </span>
              <span className="px-3 py-1 bg-indigo-100 text-indigo-800 rounded-full text-sm font-medium">
                {result.registration_count} Records
              </span>
            </div>
          </div>
        </div>
      );
    }

    return (
      <div className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow">
        <div className="flex justify-between items-start mb-3">
          <div className="flex items-center gap-2 flex-wrap">
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${sourceInfo.color}`}>
              {sourceInfo.icon} {sourceInfo.name}
            </span>
            
            {result.record_type && (
              <span className="px-2 py-1 bg-purple-50 text-purple-700 rounded-full text-xs">
                {result.record_type}
              </span>
            )}
            
            {/* NYC Lobbyist specific badges */}
            {result.source === 'nyc_lobbyist' && (
              <>
                {result.client_count && (
                  <span className="px-2 py-1 bg-blue-50 text-blue-700 rounded-full text-xs">
                    {result.client_count} Client{result.client_count !== 1 ? 's' : ''}
                  </span>
                )}
                {result.registration_count && result.registration_count > 1 && (
                  <span className="px-2 py-1 bg-green-50 text-green-700 rounded-full text-xs">
                    {result.registration_count} Registrations
                  </span>
                )}
                {result.year && (
                  <span className="px-2 py-1 bg-purple-50 text-purple-700 rounded-full text-xs">
                    Year {result.year}
                  </span>
                )}
              </>
            )}
          </div>
          
          <div className="flex items-center gap-3 text-sm text-gray-500">
            {result.amount && (
              <span className="flex items-center gap-1 font-semibold text-green-600">
                <DollarSign className="w-4 h-4" />
                {typeof result.amount === 'number' 
                  ? `$${result.amount.toLocaleString()}` 
                  : result.amount}
              </span>
            )}
            {result.date && (
              <span className="flex items-center gap-1">
                <Calendar className="w-4 h-4" />
                {new Date(result.date).toLocaleDateString()}
              </span>
            )}
          </div>
        </div>
        
        <h3 className="font-semibold text-gray-900 mb-2 line-clamp-2">{result.title}</h3>
        <p className="text-gray-600 text-sm mb-3 line-clamp-3">{result.description}</p>
        
        <div className="flex justify-between items-center">
          <div className="flex gap-3 text-xs text-gray-500">
            {result.vendor && <span>Vendor: {result.vendor.length > 30 ? `${result.vendor.substring(0, 30)}...` : result.vendor}</span>}
            {result.agency && <span>Agency: {result.agency.length > 30 ? `${result.agency.substring(0, 30)}...` : result.agency}</span>}
          </div>
          <div className="flex items-center gap-2">
            {result.url && (
              <a href={result.url} target="_blank" rel="noopener noreferrer"
                 className="text-blue-600 hover:text-blue-800 text-xs flex items-center gap-1"
                 onClick={(e) => e.stopPropagation()}>
                <ExternalLink className="w-3 h-3" />
                Original
              </a>
            )}
            <button 
              onClick={() => handleViewDetails(result)}
              className="text-blue-600 hover:text-blue-800 text-xs font-medium flex items-center gap-1 hover:bg-blue-50 px-2 py-1 rounded transition-colors"
            >
              <Eye className="w-3 h-3" />
              View Details
            </button>
          </div>
        </div>
      </div>
    );
  };

  const AnalyticsView = () => {
    // Prepare data for interactive charts
    const chartData: ChartData[] = Object.keys(totalHits).length > 0 
      ? Object.entries(totalHits).map(([source, count]) => ({
          id: source,
          name: sourceConfig[source as keyof typeof sourceConfig]?.name || source,
          value: count,
          category: 'source',
          source: source
        }))
      : [
          { id: 'checkbook', name: 'NYC Contracts', value: 0, category: 'source', source: 'checkbook' },
          { id: 'dbnyc', name: 'FEC Campaign Finance', value: 0, category: 'source', source: 'dbnyc' },
          { id: 'senate_lda', name: 'Senate LDA', value: 0, category: 'source', source: 'senate_lda' },
          { id: 'nys_ethics', name: 'NY State', value: 0, category: 'source', source: 'nys_ethics' },
          { id: 'nyc_lobbyist', name: 'NYC Lobbyist', value: 0, category: 'source', source: 'nyc_lobbyist' }
        ];

    const timelineData: TimelineData[] = results
      .filter(r => r.date)
      .map(r => ({
        id: r.title,
        date: r.date!,
        title: r.title,
        description: r.description,
        amount: typeof r.amount === 'number' ? r.amount : (r.amount ? parseFloat(r.amount.replace(/[$,]/g, '')) : undefined),
        source: r.source,
        type: r.record_type || 'unknown'
      }))
      .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());

    // Create network data for entity relationships
    const networkNodes: NetworkNode[] = [];
    const networkEdges: NetworkEdge[] = [];
    const entities = new Set<string>();
    const agencies = new Set<string>();

    results.forEach(result => {
      // Extract entities from titles and descriptions
      if (result.vendor) entities.add(result.vendor);
      if (result.agency) agencies.add(result.agency);
      
      // Add nodes for entities and agencies
      if (result.vendor && !networkNodes.find(n => n.id === result.vendor)) {
        const totalAmount = results
          .filter(r => r.vendor === result.vendor)
          .reduce((sum, r) => {
            if (typeof r.amount === 'number') return sum + r.amount;
            if (r.amount) return sum + parseFloat(r.amount.replace(/[$,]/g, ''));
            return sum;
          }, 0);
          
        networkNodes.push({
          id: result.vendor,
          name: result.vendor,
          type: 'vendor',
          value: totalAmount
        });
      }

      if (result.agency && !networkNodes.find(n => n.id === result.agency)) {
        const totalAmount = results
          .filter(r => r.agency === result.agency)
          .reduce((sum, r) => {
            if (typeof r.amount === 'number') return sum + r.amount;
            if (r.amount) return sum + parseFloat(r.amount.replace(/[$,]/g, ''));
            return sum;
          }, 0);
          
        networkNodes.push({
          id: result.agency,
          name: result.agency,
          type: 'agency',
          value: totalAmount > 0 ? totalAmount : results.filter(r => r.agency === result.agency).length
        });
      }

      // Create edges between vendors and agencies
      if (result.vendor && result.agency) {
        const existingEdge = networkEdges.find(e => 
          (e.source === result.vendor && e.target === result.agency) ||
          (e.source === result.agency && e.target === result.vendor)
        );
        
        if (!existingEdge) {
          networkEdges.push({
            source: result.vendor,
            target: result.agency,
            weight: 1
          });
        } else {
          existingEdge.weight += 1;
        }
      }
    });

    const networkData: NetworkData = {
      nodes: networkNodes.length > 0 ? networkNodes : [
        { id: 'sample-entity', name: 'Sample Entity', type: 'entity', value: 100 },
        { id: 'sample-vendor', name: 'Sample Vendor', type: 'vendor', value: 50 },
        { id: 'sample-agency', name: 'Sample Agency', type: 'agency', value: 25 }
      ],
      edges: networkEdges.length > 0 ? networkEdges : [
        { source: 'sample-entity', target: 'sample-vendor', weight: 2 },
        { source: 'sample-vendor', target: 'sample-agency', weight: 1 }
      ]
    };

    return (
      <div className="space-y-8 w-full">
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center justify-between"
        >
          <h2 className="text-3xl font-bold text-white flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-500 rounded-xl flex items-center justify-center">
              <TrendingUp className="w-6 h-6 text-white" />
            </div>
            {query ? `Comprehensive Profile: ${query}` : 'Interactive Analytics Dashboard'}
          </h2>
          {query && (
            <div className="text-sm text-gray-300 backdrop-blur-sm bg-white/10 px-4 py-2 rounded-full border border-white/20">
              Multi-jurisdictional search across {Object.keys(totalHits).length} data sources
            </div>
          )}
        </motion.div>
        
        {/* Executive Summary for Company Profile */}
        {query && results.length > 0 && (
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="backdrop-blur-xl bg-gradient-to-r from-blue-500/20 to-purple-500/20 border border-white/20 rounded-2xl p-8"
          >
            <h3 className="text-2xl font-bold text-white mb-6 flex items-center gap-3">
              <div className="w-8 h-8 bg-gradient-to-r from-blue-400 to-purple-400 rounded-lg flex items-center justify-center">
                <BarChart3 className="w-5 h-5 text-white" />
              </div>
              Executive Summary
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <motion.div 
                whileHover={{ scale: 1.02, y: -2 }}
                className="text-center backdrop-blur-sm bg-white/10 rounded-xl p-6 border border-white/10"
              >
                <div className="text-4xl font-bold text-blue-400 mb-2">{results.length}</div>
                <div className="text-sm text-gray-300">Total Records Found</div>
              </motion.div>
              <motion.div 
                whileHover={{ scale: 1.02, y: -2 }}
                className="text-center backdrop-blur-sm bg-white/10 rounded-xl p-6 border border-white/10"
              >
                <div className="text-4xl font-bold text-green-400 mb-2">
                  {(() => {
                    const totalAmount = results.reduce((sum, r) => {
                      if (typeof r.amount === 'number') return sum + r.amount;
                      if (r.amount) return sum + parseFloat(r.amount.replace(/[$,]/g, ''));
                      return sum;
                    }, 0);
                    return totalAmount >= 1000000 ? `$${(totalAmount / 1000000).toFixed(1)}M` : 
                           totalAmount >= 1000 ? `$${(totalAmount / 1000).toFixed(0)}K` : 
                           `$${totalAmount.toLocaleString()}`;
                  })()}
                </div>
                <div className="text-sm text-gray-300">Total Financial Activity</div>
              </motion.div>
              <motion.div 
                whileHover={{ scale: 1.02, y: -2 }}
                className="text-center backdrop-blur-sm bg-white/10 rounded-xl p-6 border border-white/10"
              >
                <div className="text-4xl font-bold text-purple-400 mb-2">
                  {(() => {
                    const years = results.filter(r => r.date).map(r => new Date(r.date!).getFullYear());
                    const minYear = Math.min(...years);
                    const maxYear = Math.max(...years);
                    return years.length > 0 ? `${maxYear - minYear + 1}` : '0';
                  })()}
                </div>
                <div className="text-sm text-gray-300">Years of Activity</div>
              </motion.div>
            </div>
          </motion.div>
        )}
        
        {/* Activity Categories */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="grid grid-cols-1 lg:grid-cols-2 gap-8"
        >
          {/* Lobbying Activities */}
          <motion.div 
            whileHover={{ scale: 1.02, y: -4 }}
            className="backdrop-blur-xl bg-white/10 border border-white/20 rounded-2xl p-8 shadow-2xl"
          >
            <h3 className="text-2xl font-bold text-white mb-6 flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-pink-500 rounded-xl flex items-center justify-center">
                <Globe className="w-6 h-6 text-white" />
              </div>
              Lobbying & Political Activities
            </h3>
            <div className="space-y-4">
              {['senate_lda', 'nys_ethics', 'nyc_lobbyist', 'fec'].map((source, index) => {
                const count = totalHits[source] || 0;
                const sourceInfo = sourceConfig[source as keyof typeof sourceConfig];
                if (!sourceInfo) return null;
                return (
                  <motion.div 
                    key={source}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.5 + index * 0.1 }}
                    whileHover={{ scale: 1.02 }}
                    className="flex items-center justify-between p-4 backdrop-blur-sm bg-white/5 rounded-xl border border-white/10"
                  >
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg flex items-center justify-center">
                        <span className="text-xl">{sourceInfo.icon}</span>
                      </div>
                      <div>
                        <div className="font-semibold text-white">{sourceInfo.name}</div>
                        <div className="text-sm text-gray-300">
                          {count > 0 ? `${((count / results.length) * 100).toFixed(1)}% of records` : 'No records found'}
                        </div>
                      </div>
                    </div>
                    <div className="text-2xl font-bold text-blue-400">{count}</div>
                  </motion.div>
                );
              })}
            </div>
          </motion.div>

          {/* Financial Activities */}
          <motion.div 
            whileHover={{ scale: 1.02, y: -4 }}
            className="backdrop-blur-xl bg-white/10 border border-white/20 rounded-2xl p-8 shadow-2xl"
          >
            <h3 className="text-2xl font-bold text-white mb-6 flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-r from-green-500 to-emerald-500 rounded-xl flex items-center justify-center">
                <DollarSign className="w-6 h-6 text-white" />
              </div>
              Financial & Contract Activities
            </h3>
            <div className="space-y-4">
              {['checkbook', 'fec'].map((source, index) => {
                const count = totalHits[source] || 0;
                const sourceInfo = sourceConfig[source as keyof typeof sourceConfig];
                if (!sourceInfo) return null;
                
                // Calculate total amount for this source
                const totalAmount = results.filter(r => r.source === source).reduce((sum, r) => {
                  if (typeof r.amount === 'number') return sum + r.amount;
                  if (r.amount) return sum + parseFloat(r.amount.replace(/[$,]/g, ''));
                  return sum;
                }, 0);
                
                const formattedAmount = totalAmount >= 1000000 ? `$${(totalAmount / 1000000).toFixed(1)}M` : 
                                      totalAmount >= 1000 ? `$${(totalAmount / 1000).toFixed(0)}K` : 
                                      totalAmount > 0 ? `$${totalAmount.toLocaleString()}` : '';
                
                return (
                  <motion.div 
                    key={source}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.5 + index * 0.1 }}
                    whileHover={{ scale: 1.02 }}
                    className="flex items-center justify-between p-4 backdrop-blur-sm bg-white/5 rounded-xl border border-white/10"
                  >
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 bg-gradient-to-r from-green-500 to-emerald-500 rounded-lg flex items-center justify-center">
                        <span className="text-xl">{sourceInfo.icon}</span>
                      </div>
                      <div>
                        <div className="font-semibold text-white">{sourceInfo.name}</div>
                        <div className="text-sm text-gray-300">
                          {count > 0 ? (
                            <>
                              {count} records
                              {formattedAmount && <span className="text-green-400 ml-2">• {formattedAmount}</span>}
                            </>
                          ) : 'No records found'}
                        </div>
                      </div>
                    </div>
                    <div className="text-2xl font-bold text-green-400">{count}</div>
                  </motion.div>
                );
              })}
            </div>
          </motion.div>
        </motion.div>

        {/* Interactive Charts Grid */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="grid grid-cols-1 lg:grid-cols-2 gap-8"
        >
          {/* Bar Chart */}
          <motion.div 
            whileHover={{ scale: 1.01, y: -2 }}
            className="w-full min-h-[500px] backdrop-blur-xl bg-white/10 rounded-2xl border border-white/20 p-6 shadow-2xl"
          >
            <InteractiveBarChart data={chartData} onSelectionChange={(selection) => console.log('Chart selection:', selection)} />
          </motion.div>

          {/* Timeline Chart */}
          <motion.div 
            whileHover={{ scale: 1.01, y: -2 }}
            className="w-full min-h-[500px] backdrop-blur-xl bg-white/10 rounded-2xl border border-white/20 p-6 shadow-2xl"
          >
            <TimelineChart data={timelineData} onEventClick={(event) => console.log('Timeline event:', event)} />
          </motion.div>
        </motion.div>

        {/* Network Diagram */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8 }}
          whileHover={{ scale: 1.005, y: -2 }}
          className="w-full min-h-[600px] backdrop-blur-xl bg-white/10 rounded-2xl border border-white/20 p-6 shadow-2xl"
        >
          <NetworkDiagram nodes={networkData.nodes} edges={networkData.edges} onNodeClick={(node) => console.log('Network node:', node)} />
        </motion.div>

        {/* Detailed Statistics */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.0 }}
          className="backdrop-blur-xl bg-white/10 border border-white/20 rounded-2xl p-8 shadow-2xl"
        >
          <h3 className="text-2xl font-bold text-white mb-8 flex items-center gap-3">
            <div className="w-8 h-8 bg-gradient-to-r from-cyan-500 to-blue-500 rounded-lg flex items-center justify-center">
              <BarChart3 className="w-5 h-5 text-white" />
            </div>
            Detailed Statistics
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            <motion.div
              whileHover={{ scale: 1.02 }}
              className="backdrop-blur-sm bg-white/5 rounded-xl p-6 border border-white/10"
            >
              <h4 className="font-semibold text-white mb-4 flex items-center gap-2">
                <Database className="w-5 h-5 text-blue-400" />
                Data Sources
              </h4>
              <div className="space-y-3">
                {Object.entries(totalHits).map(([source, count]) => {
                  const percentage = results.length > 0 ? (count / results.length * 100).toFixed(1) : 0;
                  const sourceInfo = sourceConfig[source as keyof typeof sourceConfig] || 
                                   { name: source, color: 'bg-gray-100 text-gray-800', icon: '📄' };
                  return (
                    <div key={source} className="flex items-center justify-between text-sm">
                      <span className="flex items-center gap-2">
                        <div className="w-3 h-3 bg-gradient-to-r from-blue-400 to-purple-400 rounded-full"></div>
                        <span className="text-gray-300">{sourceInfo.name}</span>
                      </span>
                      <span className="text-white font-medium">{count} ({percentage}%)</span>
                    </div>
                  );
                })}
              </div>
            </motion.div>

            <motion.div
              whileHover={{ scale: 1.02 }}
              className="backdrop-blur-sm bg-white/5 rounded-xl p-6 border border-white/10"
            >
              <h4 className="font-semibold text-white mb-4 flex items-center gap-2">
                <DollarSign className="w-5 h-5 text-green-400" />
                Total Amounts
              </h4>
              <div className="space-y-3">
                {(() => {
                  const amountsBySource: Record<string, number> = {};
                  results.forEach(result => {
                    if (result.amount) {
                      const amount = typeof result.amount === 'number' 
                        ? result.amount 
                        : parseFloat(result.amount.replace(/[$,]/g, ''));
                      amountsBySource[result.source] = (amountsBySource[result.source] || 0) + amount;
                    }
                  });
                  
                  return Object.entries(amountsBySource)
                    .sort(([, a], [, b]) => b - a)
                    .slice(0, 5)
                    .map(([source, amount]) => {
                      const sourceInfo = sourceConfig[source as keyof typeof sourceConfig] || 
                                       { name: source, color: 'bg-gray-100 text-gray-800', icon: '📄' };
                      return (
                        <div key={source} className="flex items-center justify-between text-sm">
                          <span className="flex items-center gap-2">
                            <div className="w-3 h-3 bg-gradient-to-r from-green-400 to-emerald-400 rounded-full"></div>
                            <span className="text-gray-300">{sourceInfo.name}</span>
                          </span>
                          <span className="font-semibold text-green-400">
                            ${amount.toLocaleString()}
                          </span>
                        </div>
                      );
                    });
                })()}
              </div>
            </motion.div>

            <motion.div
              whileHover={{ scale: 1.02 }}
              className="backdrop-blur-sm bg-white/5 rounded-xl p-6 border border-white/10"
            >
              <h4 className="font-semibold text-white mb-4 flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-purple-400" />
                Key Metrics
              </h4>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-300">Total Records:</span>
                  <span className="font-semibold text-white">{results.length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-300">Unique Vendors:</span>
                  <span className="font-semibold text-white">{entities.size}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-300">Unique Agencies:</span>
                  <span className="font-semibold text-white">{agencies.size}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-300">Date Range:</span>
                  <span className="font-semibold text-white">
                    {timelineData.length > 0 
                      ? `${new Date(timelineData[0].date).getFullYear()} - ${new Date(timelineData[timelineData.length - 1].date).getFullYear()}`
                      : 'N/A'
                    }
                  </span>
                </div>
              </div>
            </motion.div>
          </div>
        </motion.div>
      </div>
    );
  };

  const DetailView = ({ result }: { result: SearchResult }) => (
    <div className="space-y-6">
      <div className="flex items-center gap-4 mb-6">
        <button onClick={() => {setCurrentView('search'); setSelectedResult(null);}}
                className="text-blue-600 hover:text-blue-800 flex items-center gap-2">
          ← Back to Results
        </button>
      </div>
      
      <DetailedResultView 
        result={result} 
        onClose={() => {setCurrentView('search'); setSelectedResult(null);}}
      />
    </div>
  );

  if (selectedResult && currentView === 'details') {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
          <DetailView result={selectedResult} />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Animated Background Elements */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -inset-10 opacity-50">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-pulse"></div>
          <div className="absolute top-1/3 right-1/4 w-96 h-96 bg-purple-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-pulse animation-delay-2000"></div>
          <div className="absolute bottom-1/4 left-1/3 w-96 h-96 bg-pink-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-pulse animation-delay-4000"></div>
        </div>
      </div>

      {/* App Navigation Header */}
      <div className="relative z-20 backdrop-blur-xl bg-white/5 border-b border-white/10 sticky top-0">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
          <div className="flex justify-between items-center">
            <a href="/" className="flex items-center gap-3 hover:opacity-80 transition-opacity">
              <Image 
                src="/images/poissonai_logo.png"
                alt="POISSON AI Logo"
                width={35}
                height={35}
                className="w-[30px] h-[30px] md:w-[35px] md:h-[35px] rounded-lg shadow-lg shadow-purple-500/30"
              />
              <div>
                <h1 className="text-sm font-bold text-white">POISSON AI®</h1>
                <p className="text-xs text-gray-400 hidden sm:block">Vetting Intelligence</p>
              </div>
            </a>
            <a href="/" className="text-sm text-gray-300 hover:text-white transition-colors flex items-center gap-2">
              ← Back to Home
            </a>
          </div>
        </div>
      </div>

      <div className="relative z-10 max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        {/* Modern Hero Section */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="text-center mb-16"
        >
          <div className="relative">
            {/* Floating Icons */}
            <motion.div
              animate={{ 
                y: [0, -10, 0],
                rotate: [0, 5, 0]
              }}
              transition={{ 
                duration: 4,
                repeat: Infinity,
                ease: "easeInOut"
              }}
              className="absolute -top-8 -left-8 w-16 h-16 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-2xl flex items-center justify-center shadow-2xl"
            >
              <Shield className="w-8 h-8 text-white" />
            </motion.div>
            
            <motion.div
              animate={{ 
                y: [0, 10, 0],
                rotate: [0, -5, 0]
              }}
              transition={{ 
                duration: 3,
                repeat: Infinity,
                ease: "easeInOut",
                delay: 1
              }}
              className="absolute -top-4 -right-4 w-12 h-12 bg-gradient-to-r from-purple-500 to-pink-500 rounded-xl flex items-center justify-center shadow-2xl"
            >
              <Sparkles className="w-6 h-6 text-white" />
            </motion.div>

            <motion.div
              animate={{ 
                y: [0, -8, 0],
                x: [0, 5, 0]
              }}
              transition={{ 
                duration: 5,
                repeat: Infinity,
                ease: "easeInOut",
                delay: 2
              }}
              className="absolute top-16 -left-12 w-10 h-10 bg-gradient-to-r from-green-500 to-emerald-500 rounded-lg flex items-center justify-center shadow-2xl"
            >
              <Zap className="w-5 h-5 text-white" />
            </motion.div>

            {/* Main Hero Content */}
            <div className="relative backdrop-blur-sm bg-white/10 rounded-3xl p-12 border border-white/20 shadow-2xl">
              <motion.div
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ duration: 0.6, delay: 0.2 }}
                className="flex items-center justify-center gap-4 mb-8"
              >
                <div className="relative">
                  <div className="w-20 h-20 bg-gradient-to-r from-blue-600 via-purple-600 to-blue-800 rounded-2xl flex items-center justify-center shadow-2xl">
                    <Search className="w-10 h-10 text-white" />
                  </div>
                  <div className="absolute -inset-1 bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl blur opacity-30"></div>
                </div>
                <div>
                  <h1 className="text-5xl md:text-6xl font-bold bg-gradient-to-r from-white via-blue-100 to-purple-100 bg-clip-text text-transparent leading-tight">
                    Vetting Intelligence
                  </h1>
                  <h2 className="text-3xl md:text-4xl font-semibold text-blue-200 mt-2">
                    Search Hub
                  </h2>
                </div>
              </motion.div>

              <motion.p 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.4 }}
                className="text-xl text-gray-200 max-w-4xl mx-auto mb-8 leading-relaxed"
              >
                Uncover hidden connections and insights across government transparency data. 
                Search lobbying records, campaign finance, federal spending, and public contracts 
                with AI-powered intelligence.
              </motion.p>

              {/* Feature Pills */}
              <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.6 }}
                className="flex flex-wrap justify-center gap-3 mb-8"
              >
                {[
                  { icon: Globe, label: "Federal Lobbying (LDA)", color: "from-blue-500 to-blue-600" },
                  { icon: Building, label: "NYC Contracts", color: "from-green-500 to-green-600" },
                  { icon: DollarSign, label: "FEC Campaign Finance", color: "from-purple-500 to-purple-600" },
                  { icon: Shield, label: "NY State Ethics", color: "from-orange-500 to-orange-600" },
                  { icon: Users, label: "NYC Lobbying", color: "from-cyan-500 to-cyan-600" }
                ].map((item, index) => (
                  <motion.div
                    key={item.label}
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.4, delay: 0.8 + index * 0.1 }}
                    whileHover={{ scale: 1.05, y: -2 }}
                    className={`px-4 py-2 bg-gradient-to-r ${item.color} rounded-full text-white text-sm font-medium shadow-lg backdrop-blur-sm border border-white/20 flex items-center gap-2`}
                  >
                    <item.icon className="w-4 h-4" />
                    {item.label}
                  </motion.div>
                ))}
              </motion.div>

              {/* Stats */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 1.0 }}
                className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-2xl mx-auto"
              >
                {[
                  { icon: Database, value: "5M+", label: "Records Indexed" },
                  { icon: BarChart3, value: "50+", label: "Data Sources" },
                  { icon: Zap, value: "<1s", label: "Search Speed" }
                ].map((stat, index) => (
                  <motion.div
                    key={stat.label}
                    whileHover={{ scale: 1.05 }}
                    className="text-center p-4 backdrop-blur-sm bg-white/5 rounded-xl border border-white/10"
                  >
                    <stat.icon className="w-8 h-8 text-blue-400 mx-auto mb-2" />
                    <div className="text-2xl font-bold text-white">{stat.value}</div>
                    <div className="text-sm text-gray-300">{stat.label}</div>
                  </motion.div>
                ))}
              </motion.div>
            </div>
          </div>
        </motion.div>

        {/* Modern Search Bar */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="backdrop-blur-xl bg-white/10 rounded-2xl border border-white/20 p-8 mb-8 shadow-2xl"
        >
          <div className="flex gap-4 mb-4">
            <div className="flex-1 relative group">
              <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-300 w-6 h-6 group-focus-within:text-blue-400 transition-colors" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Search for companies, individuals, or organizations..."
                className="w-full pl-12 pr-4 py-4 bg-white/10 backdrop-blur-sm border border-white/20 rounded-xl focus:ring-2 focus:ring-blue-400 focus:border-blue-400 text-lg text-white placeholder-gray-300 transition-all duration-300"
              />
              <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-blue-500/20 to-purple-500/20 opacity-0 group-focus-within:opacity-100 transition-opacity pointer-events-none"></div>
            </div>
            
            <motion.button
              whileHover={{ scale: 1.02, y: -1 }}
              whileTap={{ scale: 0.98 }}
              onClick={searchData}
              disabled={loading || !query.trim()}
              className="px-8 py-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed font-semibold shadow-lg transition-all duration-300 flex items-center gap-2"
            >
              {loading ? (
                <>
                  <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                  Searching...
                </>
              ) : (
                <>
                  <Search className="w-5 h-5" />
                  Search
                </>
              )}
            </motion.button>
            
            <motion.button
              whileHover={{ scale: 1.02, y: -1 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => setShowFilters(!showFilters)}
              className={`px-6 py-4 backdrop-blur-sm rounded-xl flex items-center gap-2 font-medium transition-all duration-300 ${
                showFilters 
                  ? 'bg-blue-500/20 text-blue-300 border border-blue-400/30' 
                  : 'bg-white/10 text-gray-300 border border-white/20 hover:bg-white/20'
              }`}
            >
              <Filter className="w-5 h-5" />
              Filters
            </motion.button>
          </div>

          {/* Modern Filters */}
          <AnimatePresence>
            {showFilters && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.3 }}
                className="border-t border-white/20 pt-6 mt-6"
              >
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-200 mb-2">Year</label>
                    <select
                      value={filters.year || ''}
                      onChange={(e) => setFilters({...filters, year: e.target.value || undefined})}
                      className="w-full px-4 py-3 bg-white/10 backdrop-blur-sm border border-white/20 rounded-xl text-white focus:ring-2 focus:ring-blue-400 focus:border-blue-400 transition-all"
                    >
                      <option value="" className="bg-gray-800">All Years</option>
                      {[2024, 2023, 2022, 2021, 2020].map(year => (
                        <option key={year} value={year} className="bg-gray-800">{year}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-200 mb-2">Source</label>
                    <select
                      value={filters.source || ''}
                      onChange={(e) => setFilters({...filters, source: e.target.value || undefined})}
                      className="w-full px-4 py-3 bg-white/10 backdrop-blur-sm border border-white/20 rounded-xl text-white focus:ring-2 focus:ring-blue-400 focus:border-blue-400 transition-all"
                    >
                      <option value="" className="bg-gray-800">All Sources</option>
                      {Object.entries(sourceConfig).map(([key, config]) => (
                        <option key={key} value={key} className="bg-gray-800">{config.name}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-200 mb-2">Record Type</label>
                    <select
                      value={filters.recordType || ''}
                      onChange={(e) => setFilters({...filters, recordType: e.target.value || undefined})}
                      className="w-full px-4 py-3 bg-white/10 backdrop-blur-sm border border-white/20 rounded-xl text-white focus:ring-2 focus:ring-blue-400 focus:border-blue-400 transition-all"
                    >
                      <option value="" className="bg-gray-800">All Types</option>
                      <option value="lobbying" className="bg-gray-800">Lobbying</option>
                      <option value="campaign_finance" className="bg-gray-800">Campaign Finance</option>
                      <option value="federal_spending" className="bg-gray-800">Federal Spending</option>
                      <option value="contracts" className="bg-gray-800">Contracts</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-200 mb-2">Min Amount ($)</label>
                    <input
                      type="number"
                      value={filters.minAmount || ''}
                      onChange={(e) => setFilters({...filters, minAmount: e.target.value || undefined})}
                      placeholder="0"
                      className="w-full px-4 py-3 bg-white/10 backdrop-blur-sm border border-white/20 rounded-xl text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-400 focus:border-blue-400 transition-all"
                    />
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>

        {/* Modern Navigation Tabs */}
        {results.length > 0 && (
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className="flex gap-4 mb-8"
          >
            <motion.button
              whileHover={{ scale: 1.02, y: -1 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => {
                setCurrentView('search');
                window.scrollTo({ top: 0, behavior: 'smooth' });
              }}
              className={`px-6 py-3 rounded-xl font-semibold transition-all duration-300 flex items-center gap-2 ${
                currentView === 'search' 
                  ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg' 
                  : 'backdrop-blur-sm bg-white/10 text-gray-300 border border-white/20 hover:bg-white/20'
              }`}
            >
              <FileText className="w-5 h-5" />
              Results ({filteredResults.length})
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.02, y: -1 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => {
                setCurrentView('analytics');
                window.scrollTo({ top: 0, behavior: 'smooth' });
              }}
              className={`px-6 py-3 rounded-xl font-semibold transition-all duration-300 flex items-center gap-2 ${
                currentView === 'analytics' 
                  ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg' 
                  : 'backdrop-blur-sm bg-white/10 text-gray-300 border border-white/20 hover:bg-white/20'
              }`}
            >
              <TrendingUp className="w-5 h-5" />
              Analytics
            </motion.button>
          </motion.div>
        )}

        {/* Modern Error Message */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -10, scale: 0.95 }}
              className="backdrop-blur-sm bg-red-500/10 border border-red-400/30 rounded-xl p-4 mb-6"
            >
              <p className="text-red-200 flex items-center gap-2">
                <div className="w-5 h-5 rounded-full bg-red-500 flex items-center justify-center">
                  <span className="text-white text-xs">!</span>
                </div>
                {error}
              </p>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Main Content */}
        {currentView === 'analytics' && results.length > 0 ? (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5 }}
            className="w-full overflow-x-auto"
          >
            <AnalyticsView />
          </motion.div>
        ) : (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5 }}
            className="space-y-8"
          >
            {/* Results Summary Header with Data Source Filters */}
            {results.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="backdrop-blur-xl bg-white/10 border border-white/20 rounded-2xl p-6"
              >
                <h2 className="text-2xl font-bold text-white mb-4">Search Results for "{query}"</h2>
                
                {/* Data Source Filter Tabs */}
                <div className="mb-4">
                  <p className="text-sm text-gray-300 mb-3">Filter by Data Source:</p>
                  <div className="flex flex-wrap gap-2">
                    {/* All Sources Button */}
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={() => scrollToDataSource('all')}
                      className={`px-4 py-2 rounded-xl font-medium transition-all duration-300 flex items-center gap-2 ${
                        activeDataSource === 'all'
                          ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg'
                          : 'backdrop-blur-sm bg-white/5 text-gray-300 border border-white/20 hover:bg-white/10'
                      }`}
                    >
                      <span>All Sources</span>
                      <span className="text-xs bg-white/20 px-2 py-0.5 rounded-full">{results.length}</span>
                    </motion.button>

                    {/* Individual Source Buttons */}
                    {Object.entries(totalHits).map(([source, count]) => {
                      if (count === 0) return null;
                      const sourceInfo = sourceConfig[source as keyof typeof sourceConfig];
                      if (!sourceInfo) return null;
                      return (
                        <motion.button
                          key={source}
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                          onClick={() => scrollToDataSource(source)}
                          className={`px-4 py-2 rounded-xl font-medium transition-all duration-300 flex items-center gap-2 ${
                            activeDataSource === source
                              ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg'
                              : 'backdrop-blur-sm bg-white/5 text-gray-300 border border-white/20 hover:bg-white/10'
                          }`}
                        >
                          <span>{sourceInfo.icon}</span>
                          <span>{sourceInfo.name}</span>
                          <span className="text-xs bg-white/20 px-2 py-0.5 rounded-full">{count}</span>
                        </motion.button>
                      );
                    })}
                  </div>
                </div>

                {/* Summary Stats */}
                <div className="flex flex-wrap gap-4 pt-4 border-t border-white/10">
                  <div className="text-sm text-gray-300">
                    <span className="font-semibold text-white">
                      {activeDataSource === 'all' 
                        ? results.length 
                        : displayResults.filter(r => r.source === activeDataSource || r.source === activeDataSource + '_year_header').length}
                    </span> {activeDataSource === 'all' ? 'total' : ''} results
                  </div>
                  {activeDataSource === 'all' && (
                    <div className="text-sm text-gray-300">
                      across <span className="font-semibold text-white">{Object.keys(totalHits).filter(s => totalHits[s] > 0).length}</span> data sources
                    </div>
                  )}
                </div>
              </motion.div>
            )}

            {/* NYC Contracts - CheckbookNYC */}
            {displayResults.some(r => r.source === 'checkbook') && (activeDataSource === 'all' || activeDataSource === 'checkbook') && (
              <motion.div
                ref={checkbookRef}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-4"
              >
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-12 h-12 bg-gradient-to-r from-green-500 to-emerald-500 rounded-xl flex items-center justify-center">
                    <span className="text-2xl">📋</span>
                  </div>
                  <div>
                    <h3 className="text-2xl font-bold text-white">NYC Contracts</h3>
                    <p className="text-gray-300 text-sm">{displayResults.filter(r => r.source === 'checkbook').length} contracts found</p>
                  </div>
                </div>
                <CheckbookNYCStyleResults 
                  results={displayResults.filter(r => r.source === 'checkbook').map(result => ({
                    id: result.id || `${result.source}-${(result.vendor || '').replace(/\s+/g, '-')}-${result.amount || 0}`,
                    source: result.source,
                    title: result.title,
                    vendor: result.vendor,
                    agency: result.agency,
                    amount: typeof result.amount === 'string' 
                      ? parseFloat(result.amount.replace(/[$,]/g, '')) || undefined
                      : result.amount,
                    description: result.description || '',
                    date: result.date,
                    year: result.year ? (typeof result.year === 'string' ? parseInt(result.year) : result.year) : undefined,
                    url: result.url,
                    raw_records: [],
                    client_count: result.client_count,
                    registration_count: result.registration_count,
                    record_type: result.record_type,
                    entity_name: result.vendor,
                    document_id: result.record_type
                  }))}
                  searchQuery={query}
                  isLoading={loading}
                  onViewDetails={(result) => handleViewDetails(result as any)}
                />
              </motion.div>
            )}

            {/* Federal Lobbying - Senate LDA */}
            {displayResults.some(r => r.source === 'senate_lda') && (activeDataSource === 'all' || activeDataSource === 'senate_lda') && (
              <motion.div
                ref={senateLdaRef}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-4"
              >
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-12 h-12 bg-gradient-to-r from-red-500 to-pink-500 rounded-xl flex items-center justify-center">
                    <span className="text-2xl">🏛️</span>
                  </div>
                  <div>
                    <h3 className="text-2xl font-bold text-white">Federal Lobbying (Senate LDA)</h3>
                    <p className="text-gray-300 text-sm">{displayResults.filter(r => r.source === 'senate_lda').length} lobbying records found</p>
                  </div>
                </div>
                <NYCLobbyistStyleResults 
                  results={displayResults.filter(r => r.source === 'senate_lda').map(result => ({
                    id: result.id || `${result.source}-${(result.vendor || '').replace(/\s+/g, '-')}-${result.amount || 0}`,
                    source: result.source,
                    title: result.title,
                    vendor: result.vendor,
                    agency: result.agency,
                    amount: typeof result.amount === 'string' 
                      ? parseFloat(result.amount.replace(/[$,]/g, '')) || undefined
                      : result.amount,
                    description: result.description || '',
                    date: result.date,
                    year: result.year ? (typeof result.year === 'string' ? parseInt(result.year) : result.year) : undefined,
                    url: result.url,
                    raw_records: [],
                    client_count: result.client_count,
                    registration_count: result.registration_count,
                    record_type: result.record_type
                  }))}
                  isLoading={loading}
                  onViewDetails={(result) => handleViewDetails(result as any)}
                />
              </motion.div>
            )}
            
            {/* NYC Lobbying */}
            {displayResults.some(r => r.source === 'nyc_lobbyist') && (activeDataSource === 'all' || activeDataSource === 'nyc_lobbyist') && (
              <motion.div
                ref={nycLobbyistRef}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-4"
              >
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-12 h-12 bg-gradient-to-r from-orange-500 to-amber-500 rounded-xl flex items-center justify-center">
                    <span className="text-2xl">🤝</span>
                  </div>
                  <div>
                    <h3 className="text-2xl font-bold text-white">NYC Lobbying</h3>
                    <p className="text-gray-300 text-sm">{displayResults.filter(r => r.source === 'nyc_lobbyist' || r.source === 'nyc_lobbyist_year_header').length} lobbying records found</p>
                  </div>
                </div>
                <NYCLobbyistStyleResults 
                  results={displayResults.filter(r => r.source === 'nyc_lobbyist' || r.source === 'nyc_lobbyist_year_header').map(result => ({
                    id: result.id || `${result.source}-${(result.vendor || '').replace(/\s+/g, '-')}-${result.amount || 0}`,
                    source: result.source,
                    title: result.title,
                    vendor: result.vendor,
                    agency: result.agency,
                    amount: typeof result.amount === 'string' 
                      ? parseFloat(result.amount.replace(/[$,]/g, '')) || undefined
                      : result.amount,
                    description: result.description || '',
                    date: result.date,
                    year: result.year ? (typeof result.year === 'string' ? parseInt(result.year) : result.year) : undefined,
                    url: result.url,
                    raw_records: [],
                    client_count: result.client_count,
                    registration_count: result.registration_count,
                    record_type: result.record_type
                  }))}
                  isLoading={loading}
                  onViewDetails={(result) => handleViewDetails(result as any)}
                />
              </motion.div>
            )}

            {/* FEC Campaign Finance Results */}
            {displayResults.some(r => r.source === 'fec') && (activeDataSource === 'all' || activeDataSource === 'fec') && (
              <motion.div
                ref={fecRef}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-4"
              >
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-xl flex items-center justify-center">
                    <span className="text-2xl">🗳️</span>
                  </div>
                  <div>
                    <h3 className="text-2xl font-bold text-white">FEC Campaign Finance</h3>
                    <p className="text-gray-300 text-sm">{displayResults.filter(r => r.source === 'fec').length} campaign finance records found</p>
                  </div>
                </div>
                <FECStyleResults 
                  results={displayResults.filter(r => r.source === 'fec').map(result => ({
                    id: result.id || `${result.source}-${(result.vendor || '').replace(/\s+/g, '-')}-${result.amount || 0}`,
                    source: result.source,
                    title: result.title,
                    vendor: result.vendor,
                    agency: result.agency,
                    amount: typeof result.amount === 'string' 
                      ? parseFloat(result.amount.replace(/[$,]/g, '')) || undefined
                      : result.amount,
                    description: result.description || 'FEC Campaign Finance Record',
                    date: result.date,
                    year: result.year ? String(result.year) : undefined,
                    url: result.url,
                    record_type: result.record_type,
                    // FEC-specific fields
                    candidate_id: (result as any).candidate_id,
                    committee_id: (result as any).committee_id,
                    party: (result as any).party,
                    office: (result as any).office,
                    state: (result as any).state,
                    district: (result as any).district,
                    contributor_name: (result as any).contributor_name,
                    contributor_employer: (result as any).contributor_employer,
                    contributor_occupation: (result as any).contributor_occupation,
                    contributor_city: (result as any).contributor_city,
                    contributor_state: (result as any).contributor_state,
                    committee_name: (result as any).committee_name,
                    election_type: (result as any).election_type,
                    two_year_transaction_period: (result as any).two_year_transaction_period,
                    raw_data: (result as any).raw_data
                  }))}
                  searchQuery={query}
                  isLoading={loading}
                  onViewDetails={handleViewDetails}
                />
              </motion.div>
            )}

            {/* NY State Ethics */}
            {displayResults.some(r => r.source === 'nys_ethics') && (activeDataSource === 'all' || activeDataSource === 'nys_ethics') && (
              <motion.div
                ref={nysEthicsRef}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-4"
              >
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-12 h-12 bg-gradient-to-r from-yellow-500 to-orange-500 rounded-xl flex items-center justify-center">
                    <span className="text-2xl">⚖️</span>
                  </div>
                  <div>
                    <h3 className="text-2xl font-bold text-white">NY State Ethics</h3>
                    <p className="text-gray-300 text-sm">{displayResults.filter(r => r.source === 'nys_ethics').length} ethics records found</p>
                  </div>
                </div>
                <NYCLobbyistStyleResults 
                  results={displayResults.filter(r => r.source === 'nys_ethics').map(result => ({
                    id: result.id || `${result.source}-${(result.vendor || '').replace(/\s+/g, '-')}-${result.amount || 0}`,
                    source: result.source,
                    title: result.title,
                    vendor: result.vendor,
                    agency: result.agency,
                    amount: typeof result.amount === 'string' 
                      ? parseFloat(result.amount.replace(/[$,]/g, '')) || undefined
                      : result.amount,
                    description: result.description || '',
                    date: result.date,
                    year: result.year ? (typeof result.year === 'string' ? parseInt(result.year) : result.year) : undefined,
                    url: result.url,
                    raw_records: [],
                    client_count: result.client_count,
                    registration_count: result.registration_count,
                    record_type: result.record_type
                  }))}
                  isLoading={loading}
                  onViewDetails={(result) => handleViewDetails(result as any)}
                />
              </motion.div>
            )}

            {/* No Results - Filtered */}
            {!loading && query && displayResults.length === 0 && results.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-center py-16"
              >
                <div className="backdrop-blur-sm bg-white/10 rounded-2xl border border-white/20 p-12 max-w-lg mx-auto">
                  <div className="w-16 h-16 bg-gradient-to-r from-yellow-500 to-orange-500 rounded-full flex items-center justify-center mx-auto mb-6">
                    <Filter className="w-8 h-8 text-white" />
                  </div>
                  <h3 className="text-2xl font-bold text-white mb-3">No results match your filters</h3>
                  <p className="text-gray-300 mb-6">Try adjusting your search criteria or removing some filters</p>
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => setFilters({})}
                    className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl font-semibold"
                  >
                    Clear All Filters
                  </motion.button>
                </div>
              </motion.div>
            )}

            {/* No Results for Query */}
            {!loading && query && results.length === 0 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-center py-16"
              >
                <div className="backdrop-blur-sm bg-white/10 rounded-2xl border border-white/20 p-12 max-w-lg mx-auto">
                  <div className="w-16 h-16 bg-gradient-to-r from-red-500 to-pink-500 rounded-full flex items-center justify-center mx-auto mb-6">
                    <Search className="w-8 h-8 text-white" />
                  </div>
                  <h3 className="text-2xl font-bold text-white mb-3">No results found</h3>
                  <p className="text-gray-300">Try a different search term or check your spelling</p>
                </div>
              </motion.div>
            )}

            {/* Initial State - How to Use */}
            {!query && results.length === 0 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-center py-16"
              >
                <div className="backdrop-blur-sm bg-white/10 rounded-2xl border border-white/20 p-12 max-w-4xl mx-auto">
                  <div className="w-20 h-20 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center mx-auto mb-8">
                    <Sparkles className="w-10 h-10 text-white" />
                  </div>
                  <h3 className="text-3xl font-bold text-white mb-6">Ready to Uncover Insights?</h3>
                  <p className="text-xl text-gray-300 mb-8">Search across millions of government transparency records</p>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 text-left">
                    {[
                      { icon: Globe, title: "Federal Lobbying", desc: "Senate and House LDA records" },
                      { icon: Building, title: "NYC Contracts", desc: "Public contract and payment data" },
                      { icon: DollarSign, title: "FEC Campaign Finance", desc: "Federal campaign contributions and expenditures" },
                      { icon: Shield, title: "NY State Ethics", desc: "State procurement and ethics data" },
                      { icon: Users, title: "NYC Lobbying", desc: "Local lobbying registrations" },
                      { icon: BarChart3, title: "Analytics", desc: "Interactive charts and insights" }
                    ].map((feature, index) => (
                      <motion.div
                        key={feature.title}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.1 * index }}
                        className="backdrop-blur-sm bg-white/5 rounded-xl p-6 border border-white/10"
                      >
                        <feature.icon className="w-8 h-8 text-blue-400 mb-3" />
                        <h4 className="text-lg font-semibold text-white mb-2">{feature.title}</h4>
                        <p className="text-gray-300 text-sm">{feature.desc}</p>
                      </motion.div>
                    ))}
                  </div>
                </div>
              </motion.div>
            )}
          </motion.div>
        )}

        {/* Detail Modal */}
        <AnimatePresence>
          {showDetailModal && selectedResult && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
              onClick={handleCloseDetailModal}
            >
              <motion.div
                initial={{ opacity: 0, scale: 0.95, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95, y: 20 }}
                transition={{ duration: 0.2 }}
                className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden"
                onClick={(e) => e.stopPropagation()}
              >
                <DetailedResultView 
                  result={selectedResult} 
                  onClose={handleCloseDetailModal}
                />
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
} 