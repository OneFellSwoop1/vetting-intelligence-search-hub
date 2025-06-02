'use client';

import React, { useState, useEffect } from 'react';
import { Search, Filter, Calendar, Building, DollarSign, ExternalLink, Eye, FileText, TrendingUp } from 'lucide-react';

// Main search page for the Vetting Intelligence Search Hub
// This will eventually replace pages/index.js

interface SearchResult {
  title: string;
  description: string;
  amount?: string;
  date?: string;
  source: string;
  vendor?: string;
  agency?: string;
  url?: string;
  record_type?: string;
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
  senate_lda: { name: 'Senate LDA', color: 'bg-red-100 text-red-800', icon: '🏛️' },
  house_lda: { name: 'House LDA', color: 'bg-red-100 text-red-800', icon: '🏛️' },
  fec: { name: 'FEC', color: 'bg-purple-100 text-purple-800', icon: '🗳️' },
  dbnyc: { name: 'Federal Spending', color: 'bg-blue-100 text-blue-800', icon: '💰' },
  checkbook: { name: 'NYC Contracts', color: 'bg-green-100 text-green-800', icon: '📋' },
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

  const searchData = async () => {
    if (!query.trim()) return;
    
    setLoading(true);
    setError('');
    
    try {
      const response = await fetch('http://127.0.0.1:8001/search', {
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

  const filteredResults = results.filter(result => {
    if (filters.source && result.source !== filters.source) return false;
    if (filters.recordType && result.record_type !== filters.recordType) return false;
    if (filters.minAmount && result.amount) {
      const amount = parseFloat(result.amount.replace(/[$,]/g, ''));
      const minAmount = parseFloat(filters.minAmount);
      if (amount < minAmount) return false;
    }
    return true;
  });

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      searchData();
    }
  };

  const ResultCard = ({ result, onClick }: { result: SearchResult; onClick: () => void }) => {
    const sourceInfo = sourceConfig[result.source as keyof typeof sourceConfig] || 
                      { name: result.source, color: 'bg-gray-100 text-gray-800', icon: '📄' };

    return (
      <div className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow cursor-pointer"
           onClick={onClick}>
        <div className="flex justify-between items-start mb-3">
          <div className="flex items-center gap-2">
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${sourceInfo.color}`}>
              {sourceInfo.icon} {sourceInfo.name}
            </span>
            {result.record_type && (
              <span className="px-2 py-1 bg-gray-100 text-gray-700 rounded-full text-xs">
                {result.record_type}
              </span>
            )}
          </div>
          <div className="flex items-center gap-2 text-sm text-gray-500">
            {result.date && (
              <span className="flex items-center gap-1">
                <Calendar className="w-4 h-4" />
                {new Date(result.date).toLocaleDateString()}
              </span>
            )}
            {result.amount && (
              <span className="flex items-center gap-1 font-semibold text-green-600">
                <DollarSign className="w-4 h-4" />
                {result.amount}
              </span>
            )}
          </div>
        </div>

        <h3 className="text-lg font-semibold text-gray-900 mb-2 line-clamp-2">
          {result.title}
        </h3>

        <p className="text-gray-600 mb-3 line-clamp-3">
          {result.description}
        </p>

        <div className="flex justify-between items-center">
          <div className="flex items-center gap-4 text-sm text-gray-500">
            {result.vendor && (
              <span className="flex items-center gap-1">
                <Building className="w-4 h-4" />
                {result.vendor}
              </span>
            )}
            {result.agency && (
              <span>{result.agency}</span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <button className="flex items-center gap-1 text-blue-600 hover:text-blue-800">
              <Eye className="w-4 h-4" />
              View Details
            </button>
            {result.url && (
              <a href={result.url} target="_blank" rel="noopener noreferrer"
                 onClick={(e) => e.stopPropagation()}
                 className="flex items-center gap-1 text-blue-600 hover:text-blue-800">
                <ExternalLink className="w-4 h-4" />
                Source
              </a>
            )}
          </div>
        </div>
      </div>
    );
  };

  const AnalyticsView = () => (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
        <TrendingUp className="w-6 h-6" />
        Search Analytics
      </h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {Object.entries(totalHits).map(([source, count]) => {
          const sourceInfo = sourceConfig[source as keyof typeof sourceConfig] || 
                           { name: source, color: 'bg-gray-100 text-gray-800', icon: '📄' };
          return (
            <div key={source} className="bg-white border border-gray-200 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${sourceInfo.color}`}>
                    {sourceInfo.icon} {sourceInfo.name}
                  </span>
                </div>
                <span className="text-2xl font-bold text-gray-900">{count}</span>
              </div>
            </div>
          );
        })}
      </div>

      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold mb-4">Total Results: {results.length}</h3>
        <div className="space-y-2">
          {Object.entries(totalHits).map(([source, count]) => {
            const percentage = results.length > 0 ? (count / results.length * 100).toFixed(1) : 0;
            const sourceInfo = sourceConfig[source as keyof typeof sourceConfig] || 
                             { name: source, color: 'bg-gray-100 text-gray-800', icon: '📄' };
            return (
              <div key={source} className="flex items-center justify-between">
                <span className="flex items-center gap-2">
                  <span className={`px-2 py-1 rounded-full text-xs ${sourceInfo.color}`}>
                    {sourceInfo.name}
                  </span>
                </span>
                <span className="text-sm text-gray-600">{count} ({percentage}%)</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );

  const DetailView = ({ result }: { result: SearchResult }) => (
    <div className="space-y-6">
      <div className="flex items-center gap-4 mb-6">
        <button onClick={() => {setCurrentView('search'); setSelectedResult(null);}}
                className="text-blue-600 hover:text-blue-800">
          ← Back to Results
        </button>
        <h2 className="text-2xl font-bold text-gray-900">Record Details</h2>
      </div>

      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h3 className="text-lg font-semibold mb-4">Basic Information</h3>
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-500">Title</label>
                <p className="text-gray-900">{result.title}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-500">Source</label>
                <span className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${sourceConfig[result.source as keyof typeof sourceConfig]?.color || 'bg-gray-100 text-gray-800'}`}>
                  {sourceConfig[result.source as keyof typeof sourceConfig]?.name || result.source}
                </span>
              </div>
              {result.date && (
                <div>
                  <label className="block text-sm font-medium text-gray-500">Date</label>
                  <p className="text-gray-900">{new Date(result.date).toLocaleDateString()}</p>
                </div>
              )}
              {result.amount && (
                <div>
                  <label className="block text-sm font-medium text-gray-500">Amount</label>
                  <p className="text-gray-900 font-semibold text-green-600">{result.amount}</p>
                </div>
              )}
            </div>
          </div>

          <div>
            <h3 className="text-lg font-semibold mb-4">Additional Details</h3>
            <div className="space-y-3">
              {result.vendor && (
                <div>
                  <label className="block text-sm font-medium text-gray-500">Vendor/Entity</label>
                  <p className="text-gray-900">{result.vendor}</p>
                </div>
              )}
              {result.agency && (
                <div>
                  <label className="block text-sm font-medium text-gray-500">Agency</label>
                  <p className="text-gray-900">{result.agency}</p>
                </div>
              )}
              {result.record_type && (
                <div>
                  <label className="block text-sm font-medium text-gray-500">Record Type</label>
                  <p className="text-gray-900">{result.record_type}</p>
                </div>
              )}
              {result.url && (
                <div>
                  <label className="block text-sm font-medium text-gray-500">Source URL</label>
                  <a href={result.url} target="_blank" rel="noopener noreferrer"
                     className="text-blue-600 hover:text-blue-800 flex items-center gap-1">
                    <ExternalLink className="w-4 h-4" />
                    View Original Record
                  </a>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="mt-6">
          <h3 className="text-lg font-semibold mb-4">Description</h3>
          <p className="text-gray-700 leading-relaxed">{result.description}</p>
        </div>
      </div>
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
              Results ({filteredResults.length})
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
          <AnalyticsView />
        ) : (
          <div className="space-y-6">
            {/* Results */}
            {filteredResults.length > 0 && (
              <>
                <div className="flex justify-between items-center">
                  <h2 className="text-2xl font-bold text-gray-900">
                    Search Results ({filteredResults.length})
                  </h2>
                  {filteredResults.length > displayCount && (
                    <button
                      onClick={() => setDisplayCount(displayCount + 15)}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                    >
                      Load More
                    </button>
                  )}
                </div>

                <div className="space-y-4">
                  {filteredResults.slice(0, displayCount).map((result, index) => (
                    <ResultCard
                      key={index}
                      result={result}
                      onClick={() => {
                        setSelectedResult(result);
                        setCurrentView('details');
                      }}
                    />
                  ))}
                </div>

                {filteredResults.length > displayCount && (
                  <div className="text-center">
                    <button
                      onClick={() => setDisplayCount(displayCount + 15)}
                      className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
                    >
                      Load More Results
                    </button>
                  </div>
                )}
              </>
            )}

            {/* No Results */}
            {!loading && query && filteredResults.length === 0 && results.length > 0 && (
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
                    <li>• Check campaign finance data from FEC</li>
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