'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { Search, Clock, TrendingUp, Filter, X, ChevronDown, ChevronUp } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import { debounce } from 'lodash';

interface SearchSuggestion {
  query: string;
  type: 'entity' | 'agency' | 'recent' | 'popular';
  count?: number;
}

interface SearchProgress {
  source: string;
  status: 'pending' | 'loading' | 'completed' | 'error';
  count?: number;
  error?: string;
}

interface SearchInterfaceProps {
  onSearch: (query: string, filters?: any) => void;
  loading?: boolean;
  className?: string;
}

const SearchInterface: React.FC<SearchInterfaceProps> = ({
  onSearch,
  loading = false,
  className = ''
}) => {
  const [query, setQuery] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [searchHistory, setSearchHistory] = useState<string[]>([]);
  const [searchProgress, setSearchProgress] = useState<SearchProgress[]>([]);
  const [filters, setFilters] = useState({
    year: '',
    jurisdiction: '',
    source: '',
    minAmount: '',
    recordType: ''
  });

  // Data sources for progress tracking
  const dataSources = [
    { id: 'checkbook', name: 'NYC Checkbook', icon: '🏛️' },

    { id: 'nys_ethics', name: 'NY State Ethics', icon: '⚖️' },
    { id: 'senate_lda', name: 'Senate LDA', icon: '🏛️' },

    { id: 'nyc_lobbyist', name: 'NYC Lobbyist', icon: '🏢' }
  ];

  // Load search history from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('searchHistory');
    if (saved) {
      try {
        setSearchHistory(JSON.parse(saved));
      } catch (e) {
        console.error('Failed to parse search history:', e);
      }
    }
  }, []);

  // Save search history to localStorage
  const saveSearchHistory = useCallback((newQuery: string) => {
    const updated = [newQuery, ...searchHistory.filter(q => q !== newQuery)].slice(0, 10);
    setSearchHistory(updated);
    localStorage.setItem('searchHistory', JSON.stringify(updated));
  }, [searchHistory]);

  // Fetch search suggestions
  const { data: suggestions = [] } = useQuery({
    queryKey: ['suggestions', query],
    queryFn: async () => {
      if (query.length < 2) return [];
      
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'}/api/v1/suggestions?q=${encodeURIComponent(query)}`);
        if (!response.ok) throw new Error('Failed to fetch suggestions');
        const data = await response.json();
        return data.suggestions || [];
      } catch (error) {
        console.error('Failed to fetch suggestions:', error);
        return [];
      }
    },
    enabled: query.length >= 2 && showSuggestions,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Debounced search function
  const debouncedSearch = useCallback(
    debounce((searchQuery: string) => {
      if (searchQuery.length >= 3) {
        // Initialize progress tracking
        setSearchProgress(dataSources.map(source => ({
          source: source.id,
          status: 'pending'
        })));
        
        saveSearchHistory(searchQuery);
        onSearch(searchQuery, filters);
        setShowSuggestions(false);
      }
    }, 300),
    [onSearch, filters, saveSearchHistory]
  );

  // Handle input change
  const handleInputChange = (value: string) => {
    setQuery(value);
    setShowSuggestions(value.length >= 2);
    
    if (value.length >= 3) {
      debouncedSearch(value);
    }
  };

  // Handle suggestion click
  const handleSuggestionClick = (suggestion: SearchSuggestion) => {
    setQuery(suggestion.query);
    setShowSuggestions(false);
    saveSearchHistory(suggestion.query);
    onSearch(suggestion.query, filters);
  };

  // Handle manual search
  const handleSearch = () => {
    if (query.trim().length >= 3) {
      saveSearchHistory(query.trim());
      onSearch(query.trim(), filters);
      setShowSuggestions(false);
    }
  };

  // Handle key press
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    } else if (e.key === 'Escape') {
      setShowSuggestions(false);
    }
  };

  // Clear search
  const clearSearch = () => {
    setQuery('');
    setShowSuggestions(false);
    setSearchProgress([]);
  };

  // Filter suggestions by type
  const recentSuggestions = suggestions.filter((s: SearchSuggestion) => s.type === 'recent');
  const entitySuggestions = suggestions.filter((s: SearchSuggestion) => s.type === 'entity');
  const agencySuggestions = suggestions.filter((s: SearchSuggestion) => s.type === 'agency');

  return (
    <div className={`relative ${className}`}>
      {/* Main Search Input */}
      <div className="relative">
        <div className="relative flex items-center">
          <div className="relative flex-1">
            <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input
              type="text"
              value={query}
              onChange={(e) => handleInputChange(e.target.value)}
              onKeyPress={handleKeyPress}
              onFocus={() => setShowSuggestions(query.length >= 2)}
              placeholder="Search for companies, individuals, or organizations..."
              className="w-full pl-12 pr-12 py-4 text-lg border border-gray-300 rounded-l-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            {query && (
              <button
                onClick={clearSearch}
                className="absolute right-4 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                <X className="w-5 h-5" />
              </button>
            )}
          </div>
          
          <button
            onClick={handleSearch}
            disabled={loading || query.length < 3}
            className="px-8 py-4 bg-blue-600 text-white font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? 'Searching...' : 'Search'}
          </button>
          
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`px-4 py-4 border-l border-gray-300 rounded-r-lg transition-colors ${
              showFilters ? 'bg-blue-50 text-blue-700' : 'bg-gray-50 text-gray-700 hover:bg-gray-100'
            }`}
          >
            <Filter className="w-5 h-5" />
          </button>
        </div>

        {/* Search Suggestions Dropdown */}
        <AnimatePresence>
          {showSuggestions && (suggestions.length > 0 || searchHistory.length > 0) && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-50 max-h-96 overflow-y-auto"
            >
              {/* Recent Searches */}
              {searchHistory.length > 0 && (
                <div className="p-3 border-b border-gray-100">
                  <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                    <Clock className="w-4 h-4" />
                    Recent Searches
                  </h4>
                  <div className="space-y-1">
                    {searchHistory.slice(0, 3).map((historyQuery, index) => (
                      <button
                        key={index}
                        onClick={() => handleSuggestionClick({ query: historyQuery, type: 'recent' })}
                        className="w-full text-left px-3 py-2 text-sm text-gray-600 hover:bg-gray-50 rounded"
                      >
                        {historyQuery}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Entity Suggestions */}
              {entitySuggestions.length > 0 && (
                <div className="p-3 border-b border-gray-100">
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Companies & Organizations</h4>
                  <div className="space-y-1">
                                         {entitySuggestions.slice(0, 5).map((suggestion: SearchSuggestion, index: number) => (
                      <button
                        key={index}
                        onClick={() => handleSuggestionClick(suggestion)}
                        className="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 rounded flex items-center justify-between"
                      >
                        <span>{suggestion.query}</span>
                        {suggestion.count && (
                          <span className="text-xs text-gray-500">{suggestion.count} records</span>
                        )}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Agency Suggestions */}
              {agencySuggestions.length > 0 && (
                <div className="p-3">
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Government Agencies</h4>
                  <div className="space-y-1">
                                         {agencySuggestions.slice(0, 5).map((suggestion: SearchSuggestion, index: number) => (
                      <button
                        key={index}
                        onClick={() => handleSuggestionClick(suggestion)}
                        className="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 rounded flex items-center justify-between"
                      >
                        <span>{suggestion.query}</span>
                        {suggestion.count && (
                          <span className="text-xs text-gray-500">{suggestion.count} records</span>
                        )}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Advanced Filters */}
      <AnimatePresence>
        {showFilters && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mt-4 p-4 bg-gray-50 border border-gray-200 rounded-lg"
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">Advanced Filters</h3>
              <button
                onClick={() => setShowFilters(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <ChevronUp className="w-5 h-5" />
              </button>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Year</label>
                <select
                  value={filters.year}
                  onChange={(e) => setFilters({...filters, year: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">All Years</option>
                  {[2024, 2023, 2022, 2021, 2020].map(year => (
                    <option key={year} value={year}>{year}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Jurisdiction</label>
                <select
                  value={filters.jurisdiction}
                  onChange={(e) => setFilters({...filters, jurisdiction: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">All Jurisdictions</option>
                  <option value="federal">Federal</option>
                  <option value="state">State</option>
                  <option value="local">Local</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Data Source</label>
                <select
                  value={filters.source}
                  onChange={(e) => setFilters({...filters, source: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">All Sources</option>
                  {dataSources.map(source => (
                    <option key={source.id} value={source.id}>{source.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Record Type</label>
                <select
                  value={filters.recordType}
                  onChange={(e) => setFilters({...filters, recordType: e.target.value})}
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
                  value={filters.minAmount}
                  onChange={(e) => setFilters({...filters, minAmount: e.target.value})}
                  placeholder="0"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>

            <div className="mt-4 flex items-center gap-2">
              <button
                onClick={() => setFilters({ year: '', jurisdiction: '', source: '', minAmount: '', recordType: '' })}
                className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800"
              >
                Clear Filters
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Search Progress */}
      <AnimatePresence>
        {loading && searchProgress.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg"
          >
            <div className="flex items-center gap-2 mb-3">
              <TrendingUp className="w-5 h-5 text-blue-600" />
              <h3 className="text-sm font-medium text-blue-900">Searching across data sources...</h3>
            </div>
            
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
              {dataSources.map(source => {
                const progress = searchProgress.find(p => p.source === source.id);
                const status = progress?.status || 'pending';
                
                return (
                  <div
                    key={source.id}
                    className={`p-3 rounded-lg border text-center transition-colors ${
                      status === 'completed' ? 'bg-green-50 border-green-200' :
                      status === 'loading' ? 'bg-yellow-50 border-yellow-200' :
                      status === 'error' ? 'bg-red-50 border-red-200' :
                      'bg-gray-50 border-gray-200'
                    }`}
                  >
                    <div className="text-lg mb-1">{source.icon}</div>
                    <div className="text-xs font-medium text-gray-700">{source.name}</div>
                    <div className="text-xs text-gray-500 mt-1">
                      {status === 'completed' && progress?.count !== undefined ? `${progress.count} results` :
                       status === 'loading' ? 'Searching...' :
                       status === 'error' ? 'Error' :
                       'Pending'}
                    </div>
                  </div>
                );
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default SearchInterface; 