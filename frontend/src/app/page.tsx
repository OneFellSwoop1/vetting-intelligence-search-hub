'use client';

import React, { useState, useEffect } from 'react';
import { Search, Filter, Calendar, Building, DollarSign, ExternalLink, Eye, FileText, TrendingUp } from 'lucide-react';
import InteractiveBarChart from '@/components/InteractiveBarChart';
import TimelineChart from '@/components/TimelineChart';
import NetworkDiagram from '@/components/NetworkDiagram';
import DetailedResultView from '@/components/enhanced-results/DetailedResultView';
import CheckbookStyleResults from '@/components/enhanced-search/CheckbookStyleResults';

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
  dbnyc: { name: 'FEC Campaign Finance', color: 'bg-blue-100 text-blue-800', icon: '💰' },
  nys_ethics: { name: 'NY State', color: 'bg-yellow-100 text-yellow-800', icon: '🏛️' },
  nyc_lobbyist: { name: 'NYC Lobbyist', color: 'bg-orange-100 text-orange-800', icon: '🤝' }
};



export default function VettingIntelligenceHub() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [totalHits, setTotalHits] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [currentView, setCurrentView] = useState<'search' | 'analytics' | 'details'>('search');
  const [selectedResult, setSelectedResult] = useState<SearchResult | null>(null);
  const [filters, setFilters] = useState<SearchFilters>({});
  const [showFilters, setShowFilters] = useState(false);
  const [displayCount, setDisplayCount] = useState(15);

  // Helper function to group NYC Lobbyist results by year
  const groupNYCResultsByYear = React.useCallback((results: SearchResult[]): SearchResult[] => {
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
      const response = await fetch('http://127.0.0.1:8000/search', {
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

      const data: SearchResponse = await response.json();
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
  }, [filteredResults]);

  const ResultCard = ({ result, onClick }: { result: SearchResult; onClick: () => void }) => {
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
      <div className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow cursor-pointer"
           onClick={onClick}>
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
            <button className="text-blue-600 hover:text-blue-800 text-xs font-medium flex items-center gap-1 hover:bg-blue-50 px-2 py-1 rounded">
              <Eye className="w-3 h-3" />
              Full Details
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
      .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

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
        <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <TrendingUp className="w-6 h-6" />
          Interactive Analytics Dashboard
        </h2>
        
        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {Object.entries(totalHits).map(([source, count]) => {
            const sourceInfo = sourceConfig[source as keyof typeof sourceConfig] || 
                             { name: source, color: 'bg-gray-100 text-gray-800', icon: '📄' };
            return (
              <div key={source} className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${sourceInfo.color}`}>
                      {sourceInfo.icon} {sourceInfo.name}
                    </span>
                  </div>
                  <span className="text-2xl font-bold text-gray-900">{count}</span>
                </div>
                <div className="mt-2 text-sm text-gray-600">
                  {results.length > 0 ? ((count / results.length) * 100).toFixed(1) : 0}% of total
                </div>
              </div>
            );
          })}
        </div>

        {/* Interactive Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Bar Chart */}
          <div className="w-full min-h-[500px]">
            <InteractiveBarChart data={chartData} onSelectionChange={(selection) => console.log('Chart selection:', selection)} />
          </div>

          {/* Timeline Chart */}
          <div className="w-full min-h-[500px]">
            <TimelineChart data={timelineData} onEventClick={(event) => console.log('Timeline event:', event)} />
          </div>
        </div>

        {/* Network Diagram */}
        <div className="w-full min-h-[600px]">
          <NetworkDiagram nodes={networkData.nodes} edges={networkData.edges} onNodeClick={(node) => console.log('Network node:', node)} />
        </div>

        {/* Detailed Statistics */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4">Detailed Statistics</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div>
              <h4 className="font-medium text-gray-900 mb-2">Data Sources</h4>
              <div className="space-y-2">
                {Object.entries(totalHits).map(([source, count]) => {
                  const percentage = results.length > 0 ? (count / results.length * 100).toFixed(1) : 0;
                  const sourceInfo = sourceConfig[source as keyof typeof sourceConfig] || 
                                   { name: source, color: 'bg-gray-100 text-gray-800', icon: '📄' };
                  return (
                    <div key={source} className="flex items-center justify-between text-sm">
                      <span className="flex items-center gap-2">
                        <span className={`px-2 py-1 rounded-full text-xs ${sourceInfo.color}`}>
                          {sourceInfo.name}
                        </span>
                      </span>
                      <span className="text-gray-600">{count} ({percentage}%)</span>
                    </div>
                  );
                })}
              </div>
            </div>

            <div>
              <h4 className="font-medium text-gray-900 mb-2">Total Amounts</h4>
              <div className="space-y-2">
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
                          <span className={`px-2 py-1 rounded-full text-xs ${sourceInfo.color}`}>
                            {sourceInfo.name}
                          </span>
                          <span className="font-medium text-gray-900">
                            ${amount.toLocaleString()}
                          </span>
                        </div>
                      );
                    });
                })()}
              </div>
            </div>

            <div>
              <h4 className="font-medium text-gray-900 mb-2">Key Metrics</h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Total Records:</span>
                  <span className="font-medium">{results.length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Unique Vendors:</span>
                  <span className="font-medium">{entities.size}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Unique Agencies:</span>
                  <span className="font-medium">{agencies.size}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Date Range:</span>
                  <span className="font-medium">
                    {timelineData.length > 0 
                      ? `${new Date(timelineData[0].date).getFullYear()} - ${new Date(timelineData[timelineData.length - 1].date).getFullYear()}`
                      : 'N/A'
                    }
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
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
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            🔍 Vetting Intelligence Search Hub
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Comprehensive search across government data sources including lobbying records, 
            campaign finance, federal spending, and public contracts
          </p>
        </div>

        {/* Search Bar */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
          <div className="flex gap-4 mb-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Search for companies, individuals, or organizations..."
                className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-lg"
              />
            </div>
            <button
              onClick={searchData}
              disabled={loading || !query.trim()}
              className="px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
            >
              {loading ? 'Searching...' : 'Search'}
            </button>
            <button
              onClick={() => setShowFilters(!showFilters)}
              className="px-4 py-3 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 flex items-center gap-2"
            >
              <Filter className="w-5 h-5" />
              Filters
            </button>
          </div>

          {/* Filters */}
          {showFilters && (
            <div className="border-t border-gray-200 pt-4 mt-4">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Year</label>
                  <select
                    value={filters.year || ''}
                    onChange={(e) => setFilters({...filters, year: e.target.value || undefined})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">All Years</option>
                    {[2024, 2023, 2022, 2021, 2020].map(year => (
                      <option key={year} value={year}>{year}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Source</label>
                  <select
                    value={filters.source || ''}
                    onChange={(e) => setFilters({...filters, source: e.target.value || undefined})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">All Sources</option>
                    {Object.entries(sourceConfig).map(([key, config]) => (
                      <option key={key} value={key}>{config.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Record Type</label>
                  <select
                    value={filters.recordType || ''}
                    onChange={(e) => setFilters({...filters, recordType: e.target.value || undefined})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">All Types</option>
                    <option value="lobbying">Lobbying</option>
                    <option value="campaign_finance">Campaign Finance</option>
                    <option value="federal_spending">Federal Spending</option>
                    <option value="contracts">Contracts</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Min Amount ($)</label>
                  <input
                    type="number"
                    value={filters.minAmount || ''}
                    onChange={(e) => setFilters({...filters, minAmount: e.target.value || undefined})}
                    placeholder="0"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Navigation Tabs */}
        {results.length > 0 && (
          <div className="flex gap-4 mb-6">
            <button
              onClick={() => setCurrentView('search')}
              className={`px-4 py-2 rounded-lg font-medium ${currentView === 'search' ? 'bg-blue-600 text-white' : 'bg-white text-gray-700 border border-gray-300'}`}
            >
              <FileText className="w-4 h-4 inline mr-2" />
              Results ({displayResults.length})
            </button>
            <button
              onClick={() => setCurrentView('analytics')}
              className={`px-4 py-2 rounded-lg font-medium ${currentView === 'analytics' ? 'bg-blue-600 text-white' : 'bg-white text-gray-700 border border-gray-300'}`}
            >
              <TrendingUp className="w-4 h-4 inline mr-2" />
              Analytics
            </button>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {/* Main Content */}
        {currentView === 'analytics' && results.length > 0 ? (
          <div className="w-full overflow-x-auto">
            <AnalyticsView />
          </div>
        ) : (
          <div className="space-y-6">
            {/* Results - CheckbookNYC Style */}
            {displayResults.length > 0 && (
              <CheckbookStyleResults 
                results={displayResults.map(result => ({
                  id: `${result.source}-${Math.random()}`,
                  source: result.source,
                  title: result.title,
                  vendor: result.vendor,
                  agency: result.agency,
                  amount: typeof result.amount === 'string' 
                    ? parseFloat(result.amount.replace(/[$,]/g, '')) || undefined
                    : result.amount,
                  description: result.description,
                  date: result.date,
                  year: result.year ? parseInt(result.year) : undefined,
                  url: result.url,
                  raw_records: []
                }))}
                isLoading={loading}
              />
            )}

            {/* No Results */}
            {!loading && query && displayResults.length === 0 && results.length > 0 && (
              <div className="text-center py-12">
                <h3 className="text-xl font-semibold text-gray-900 mb-2">No results match your filters</h3>
                <p className="text-gray-600">Try adjusting your search criteria</p>
              </div>
            )}

            {/* No Results for Query */}
            {!loading && query && results.length === 0 && (
              <div className="text-center py-12">
                <h3 className="text-xl font-semibold text-gray-900 mb-2">No results found</h3>
                <p className="text-gray-600">Try a different search term</p>
              </div>
            )}

            {/* Initial State */}
            {!query && results.length === 0 && (
              <div className="text-center py-12">
                <div className="bg-white rounded-lg border border-gray-200 p-8 max-w-2xl mx-auto">
                  <h3 className="text-xl font-semibold text-gray-900 mb-4">How to Use</h3>
                  <ul className="text-left text-gray-600 space-y-2">
                    <li>• Search for companies, individuals, or organizations</li>
                    <li>• View lobbying records from Senate and House LDA</li>
                    <li>• Check contract and payment data</li>
                    <li>• Review federal spending and NYC contracts</li>
                    <li>• Use filters to narrow down results</li>
                    <li>• Click on results for detailed information</li>
                  </ul>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
} 