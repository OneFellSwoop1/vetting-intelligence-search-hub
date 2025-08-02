import React, { useState, useEffect, useRef } from 'react';
import { 
  Search, 
  Filter, 
  X, 
  Sparkles, 
  TrendingUp, 
  Clock, 
  Building2,
  DollarSign,
  FileText,
  Target,
  AlertCircle,
  BarChart3,
  PieChart,
  TrendingDown,
  Calendar,
  MapPin,
  Users,
  Shield,
  Activity,
  ExternalLink,
  Download,
  RefreshCw
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { cn } from '@/lib/utils';

interface SearchSuggestion {
  query: string;
  type: 'recent' | 'trending' | 'suggestion' | 'high_value' | 'lobbying';
  category?: string;
  resultCount?: number;
  totalAmount?: number;
  lastActivity?: string;
  riskLevel?: 'low' | 'medium' | 'high';
  sources?: string[];
}

interface SearchInterfaceProps {
  query: string;
  onQueryChange: (query: string) => void;
  onSearch: () => void;
  loading: boolean;
  onFiltersToggle: () => void;
  showFilters: boolean;
  totalResults?: number;
  results?: any[];
  onExport?: () => void;
  onRefresh?: () => void;
}

const EnhancedSearchInterface: React.FC<SearchInterfaceProps> = ({
  query,
  onQueryChange,
  onSearch,
  loading,
  onFiltersToggle,
  showFilters,
  totalResults,
  results = [],
  onExport,
  onRefresh
}) => {
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [suggestions, setSuggestions] = useState<SearchSuggestion[]>([]);
  const [focusedSuggestion, setFocusedSuggestion] = useState(-1);
  const inputRef = useRef<HTMLInputElement>(null);
  const suggestionsRef = useRef<HTMLDivElement>(null);

  // Enhanced search suggestions with financial context
  const mockSuggestions: SearchSuggestion[] = [
    { 
      query: 'Microsoft', 
      type: 'high_value', 
      resultCount: 264,
      totalAmount: 52000000,
      lastActivity: '2025-01-15',
      riskLevel: 'high',
      sources: ['checkbook', 'senate_lda', 'nys_ethics'],
      category: 'Technology'
    },
    { 
      query: 'Google', 
      type: 'lobbying', 
      resultCount: 52,
      totalAmount: 2580000,
      lastActivity: '2025-01-10',
      riskLevel: 'medium',
      sources: ['senate_lda', 'nyc_lobbyist'],
      category: 'Technology'
    },
    { 
      query: 'Apple', 
      type: 'trending', 
      resultCount: 86,
      totalAmount: 15000000,
      lastActivity: '2025-01-08',
      riskLevel: 'high',
      sources: ['checkbook', 'senate_lda'],
      category: 'Technology'
    },
    { 
      query: 'Amazon', 
      type: 'high_value', 
      resultCount: 143,
      totalAmount: 89000000,
      lastActivity: '2025-01-12',
      riskLevel: 'high',
      sources: ['checkbook', 'senate_lda', 'nys_ethics'],
      category: 'Technology'
    },
    { 
      query: 'Meta', 
      type: 'lobbying', 
      resultCount: 67,
      totalAmount: 3200000,
      lastActivity: '2025-01-09',
      riskLevel: 'medium',
      sources: ['senate_lda', 'nyc_lobbyist'],
      category: 'Technology'
    },
    { 
      query: 'Tesla', 
      type: 'trending', 
      resultCount: 43,
      totalAmount: 8500000,
      lastActivity: '2025-01-14',
      riskLevel: 'medium',
      sources: ['checkbook', 'senate_lda'],
      category: 'Technology'
    },
    { 
      query: 'JPMorgan Chase', 
      type: 'high_value', 
      resultCount: 198,
      totalAmount: 125000000,
      lastActivity: '2025-01-13',
      riskLevel: 'high',
      sources: ['checkbook', 'senate_lda', 'nys_ethics'],
      category: 'Financial'
    },
    { 
      query: 'Goldman Sachs', 
      type: 'lobbying', 
      resultCount: 89,
      totalAmount: 4800000,
      lastActivity: '2025-01-11',
      riskLevel: 'medium',
      sources: ['senate_lda', 'nyc_lobbyist', 'nys_ethics'],
      category: 'Financial'
    }
  ];

  useEffect(() => {
    if (query.length > 1) {
      // Filter suggestions based on query
      const filtered = mockSuggestions.filter(s => 
        s.query.toLowerCase().includes(query.toLowerCase())
      );
      setSuggestions(filtered);
      setShowSuggestions(true);
    } else {
      setSuggestions(mockSuggestions.slice(0, 6));
      setShowSuggestions(query.length === 0 && document.activeElement === inputRef.current);
    }
  }, [query]);

  // Calculate search result metrics
  const resultMetrics = React.useMemo(() => {
    if (!results || results.length === 0) return null;

    const totalAmount = results.reduce((sum, result) => {
      const amount = typeof result.amount === 'number' ? result.amount : 
                    typeof result.amount === 'string' ? parseFloat(result.amount.replace(/[$,]/g, '')) || 0 : 0;
      return sum + amount;
    }, 0);

    const sourceBreakdown = results.reduce((acc, result) => {
      acc[result.source] = (acc[result.source] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const highValueCount = results.filter(r => {
      const amount = typeof r.amount === 'number' ? r.amount : 
                    typeof r.amount === 'string' ? parseFloat(r.amount.replace(/[$,]/g, '')) || 0 : 0;
      return amount >= 1000000;
    }).length;

    const lobbyingCount = results.filter(r => 
      r.source.includes('lda') || r.source.includes('lobbyist')
    ).length;

    return {
      totalAmount,
      sourceBreakdown,
      highValueCount,
      lobbyingCount,
      averageAmount: totalAmount / results.length
    };
  }, [results]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!showSuggestions) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setFocusedSuggestion(prev => 
          prev < suggestions.length - 1 ? prev + 1 : prev
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setFocusedSuggestion(prev => prev > 0 ? prev - 1 : -1);
        break;
      case 'Enter':
        if (focusedSuggestion >= 0) {
          e.preventDefault();
          onQueryChange(suggestions[focusedSuggestion].query);
          setShowSuggestions(false);
          onSearch();
        } else {
          onSearch();
        }
        break;
      case 'Escape':
        setShowSuggestions(false);
        setFocusedSuggestion(-1);
        break;
    }
  };

  const handleSuggestionClick = (suggestion: SearchSuggestion) => {
    onQueryChange(suggestion.query);
    setShowSuggestions(false);
    onSearch();
  };

  const getSuggestionIcon = (type: string): React.ReactNode => {
    switch (type) {
      case 'recent': return <Clock className="w-4 h-4 text-gray-400" />;
      case 'trending': return <TrendingUp className="w-4 h-4 text-green-500" />;
      case 'high_value': return <DollarSign className="w-4 h-4 text-red-500" />;
      case 'lobbying': return <Target className="w-4 h-4 text-blue-500" />;
      default: return <Search className="w-4 h-4 text-gray-400" />;
    }
  };

  const getRiskBadge = (riskLevel: string) => {
    switch (riskLevel) {
      case 'high':
        return <span className="px-2 py-1 bg-red-100 text-red-700 text-xs rounded-full font-medium">High Risk</span>;
      case 'medium':
        return <span className="px-2 py-1 bg-yellow-100 text-yellow-700 text-xs rounded-full font-medium">Medium Risk</span>;
      case 'low':
        return <span className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full font-medium">Low Risk</span>;
      default:
        return null;
    }
  };

  const formatCurrency = (amount: number) => {
    if (amount >= 1000000) {
      return `$${(amount / 1000000).toFixed(1)}M`;
    } else if (amount >= 1000) {
      return `$${(amount / 1000).toFixed(0)}K`;
    }
    return `$${amount.toLocaleString()}`;
  };

  const getSourceIcons = (sources: string[]) => {
    const iconMap: Record<string, string> = {
      'checkbook': '🏙️',
      'senate_lda': '🏛️',
      'nys_ethics': '⚖️',
      'nyc_lobbyist': '🗽',
      'dbnyc': '📊'
    };
    return sources.map(s => iconMap[s] || '📄').join(' ');
  };

  return (
    <div className="relative w-full max-w-6xl mx-auto">
      <Card className="border-0 shadow-lg">
        <CardContent className="p-6">
          {/* Enhanced Search Bar */}
          <div className="flex gap-3 mb-6">
            <div className="flex-1 relative">
              <div className="relative">
                <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <input
                  ref={inputRef}
                  type="text"
                  value={query}
                  onChange={(e) => onQueryChange(e.target.value)}
                  onKeyDown={handleKeyDown}
                  onFocus={() => setShowSuggestions(true)}
                  onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
                  placeholder="Search companies, contracts, lobbying activities..."
                  className={cn(
                    "w-full pl-12 pr-12 py-4 border-2 rounded-xl text-lg",
                    "focus:ring-4 focus:ring-primary-100 focus:border-primary-500",
                    "transition-all duration-200 placeholder:text-gray-400",
                    showSuggestions ? "rounded-b-none border-b-0" : ""
                  )}
                />
                {query && (
                  <button
                    onClick={() => {
                      onQueryChange('');
                      setShowSuggestions(false);
                    }}
                    className="absolute right-4 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
                  >
                    <X className="w-5 h-5" />
                  </button>
                )}
              </div>

              {/* Enhanced Suggestions Dropdown */}
              {showSuggestions && suggestions.length > 0 && (
                <div 
                  ref={suggestionsRef}
                  className="absolute top-full left-0 right-0 bg-white border-2 border-t-0 border-primary-200 rounded-b-xl shadow-xl z-50 max-h-96 overflow-y-auto"
                >
                  {query.length === 0 && (
                    <div className="px-4 py-3 text-sm font-medium text-gray-500 border-b bg-gray-50">
                      <div className="flex items-center gap-2">
                        <Sparkles className="w-4 h-4" />
                        Recent & High-Value Searches
                      </div>
                    </div>
                  )}
                  
                  {suggestions.map((suggestion, index) => (
                    <div
                      key={suggestion.query}
                      onClick={() => handleSuggestionClick(suggestion)}
                      className={cn(
                        "px-4 py-4 cursor-pointer group transition-colors border-b border-gray-100 last:border-b-0",
                        focusedSuggestion === index 
                          ? "bg-primary-50 border-l-4 border-primary-500" 
                          : "hover:bg-gray-50"
                      )}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex items-start gap-3 flex-1">
                          <div className="mt-1">
                            {getSuggestionIcon(suggestion.type)}
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <div className="font-semibold text-gray-900">
                                {suggestion.query}
                              </div>
                              {suggestion.riskLevel && getRiskBadge(suggestion.riskLevel)}
                            </div>
                            
                            <div className="flex items-center gap-4 text-sm text-gray-600">
                              {suggestion.totalAmount && (
                                <div className="flex items-center gap-1">
                                  <DollarSign className="w-3 h-3" />
                                  <span className="font-medium">{formatCurrency(suggestion.totalAmount)}</span>
                                </div>
                              )}
                              {suggestion.resultCount && (
                                <div className="flex items-center gap-1">
                                  <FileText className="w-3 h-3" />
                                  <span>{suggestion.resultCount.toLocaleString()} records</span>
                                </div>
                              )}
                              {suggestion.lastActivity && (
                                <div className="flex items-center gap-1">
                                  <Calendar className="w-3 h-3" />
                                  <span>{new Date(suggestion.lastActivity).toLocaleDateString()}</span>
                                </div>
                              )}
                            </div>
                            
                            <div className="flex items-center gap-2 mt-2">
                              {suggestion.sources && (
                                <div className="flex items-center gap-1">
                                  <span className="text-xs text-gray-500">Sources:</span>
                                  <span className="text-sm">{getSourceIcons(suggestion.sources)}</span>
                                </div>
                              )}
                              {suggestion.category && (
                                <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full">
                                  {suggestion.category}
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                        
                        <div className="flex items-center gap-2 ml-4">
                          {suggestion.type === 'trending' && (
                            <span className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full font-medium">
                              <TrendingUp className="w-3 h-3 inline mr-1" />
                              Trending
                            </span>
                          )}
                          {suggestion.type === 'high_value' && (
                            <span className="px-2 py-1 bg-red-100 text-red-700 text-xs rounded-full font-medium">
                              <AlertCircle className="w-3 h-3 inline mr-1" />
                              High Value
                            </span>
                          )}
                          {suggestion.type === 'lobbying' && (
                            <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full font-medium">
                              <Target className="w-3 h-3 inline mr-1" />
                              Lobbying
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Enhanced Action Buttons */}
            <div className="flex gap-2">
              <Button
                onClick={onSearch}
                disabled={loading}
                className="px-6 py-4 text-lg font-medium"
              >
                {loading ? (
                  <>
                    <RefreshCw className="w-5 h-5 mr-2 animate-spin" />
                    Searching...
                  </>
                ) : (
                  <>
                    <Search className="w-5 h-5 mr-2" />
                    Search
                  </>
                )}
              </Button>
              
              <Button
                variant="outline"
                onClick={onFiltersToggle}
                className="px-4 py-4"
              >
                <Filter className="w-5 h-5" />
                {showFilters && <span className="ml-2">Hide Filters</span>}
              </Button>
              
              {onRefresh && (
                <Button
                  variant="outline"
                  onClick={onRefresh}
                  className="px-4 py-4"
                >
                  <RefreshCw className="w-5 h-5" />
                </Button>
              )}
            </div>
          </div>

          {/* Enhanced Results Summary */}
          {totalResults !== undefined && totalResults > 0 && (
            <div className="border-t pt-4">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-6">
                  <div className="flex items-center gap-2">
                    <FileText className="w-5 h-5 text-gray-600" />
                    <span className="text-lg font-semibold text-gray-900">
                      {totalResults.toLocaleString()} results
                    </span>
                  </div>
                  
                  {resultMetrics && (
                    <>
                      <div className="flex items-center gap-2">
                        <DollarSign className="w-5 h-5 text-green-600" />
                        <span className="text-lg font-semibold text-green-600">
                          {formatCurrency(resultMetrics.totalAmount)}
                        </span>
                        <span className="text-sm text-gray-500">total value</span>
                      </div>
                      
                      {resultMetrics.highValueCount > 0 && (
                        <div className="flex items-center gap-2">
                          <AlertCircle className="w-4 h-4 text-red-500" />
                          <span className="text-sm text-red-700 font-medium">
                            {resultMetrics.highValueCount} high-value transactions
                          </span>
                        </div>
                      )}
                      
                      {resultMetrics.lobbyingCount > 0 && (
                        <div className="flex items-center gap-2">
                          <Target className="w-4 h-4 text-blue-500" />
                          <span className="text-sm text-blue-700 font-medium">
                            {resultMetrics.lobbyingCount} lobbying records
                          </span>
                        </div>
                      )}
                    </>
                  )}
                </div>
                
                <div className="flex items-center gap-2">
                  {onExport && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={onExport}
                      className="flex items-center gap-2"
                    >
                      <Download className="w-4 h-4" />
                      Export
                    </Button>
                  )}
                  
                  {resultMetrics && (
                    <div className="flex items-center gap-2 bg-gray-50 px-3 py-1 rounded-lg">
                      <span className="text-sm text-gray-600">Sources:</span>
                      <div className="flex items-center gap-1">
                        {Object.entries(resultMetrics.sourceBreakdown).map(([source, count]) => (
                          <span key={source} className="text-sm bg-white px-2 py-1 rounded border">
                            {getSourceIcons([source])} {count as number}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default EnhancedSearchInterface; 