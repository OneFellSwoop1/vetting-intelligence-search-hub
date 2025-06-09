import React, { useState, useEffect, useRef } from 'react';
import { Search, Filter, X, Sparkles, TrendingUp, Clock, Building2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { cn } from '@/lib/utils';

interface SearchSuggestion {
  query: string;
  type: 'recent' | 'trending' | 'suggestion';
  category?: string;
  resultCount?: number;
}

interface SearchInterfaceProps {
  query: string;
  onQueryChange: (query: string) => void;
  onSearch: () => void;
  loading: boolean;
  onFiltersToggle: () => void;
  showFilters: boolean;
  totalResults?: number;
}

const EnhancedSearchInterface: React.FC<SearchInterfaceProps> = ({
  query,
  onQueryChange,
  onSearch,
  loading,
  onFiltersToggle,
  showFilters,
  totalResults
}) => {
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [suggestions, setSuggestions] = useState<SearchSuggestion[]>([]);
  const [focusedSuggestion, setFocusedSuggestion] = useState(-1);
  const inputRef = useRef<HTMLInputElement>(null);
  const suggestionsRef = useRef<HTMLDivElement>(null);

  // Mock data - in real app, this would come from API
  const mockSuggestions: SearchSuggestion[] = [
    { query: 'Microsoft', type: 'recent', resultCount: 264 },
    { query: 'Google', type: 'recent', resultCount: 52 },
    { query: 'Apple', type: 'trending', resultCount: 86 },
    { query: 'Amazon', type: 'suggestion', category: 'Technology' },
    { query: 'Meta', type: 'suggestion', category: 'Technology' },
    { query: 'Tesla', type: 'trending', resultCount: 43 },
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
      setSuggestions(mockSuggestions.slice(0, 4));
      setShowSuggestions(query.length === 0 && document.activeElement === inputRef.current);
    }
  }, [query]);

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

  const getSuggestionIcon = (type: string) => {
    switch (type) {
      case 'recent': return <Clock className="w-4 h-4 text-gray-400" />;
      case 'trending': return <TrendingUp className="w-4 h-4 text-green-500" />;
      default: return <Search className="w-4 h-4 text-gray-400" />;
    }
  };

  return (
    <div className="relative w-full max-w-4xl mx-auto">
      <Card className="border-0 shadow-lg">
        <CardContent className="p-6">
          {/* Main Search Bar */}
          <div className="flex gap-3 mb-4">
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
                  placeholder="Search companies, individuals, or organizations..."
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
                  className="absolute top-full left-0 right-0 bg-white border-2 border-t-0 border-primary-200 rounded-b-xl shadow-xl z-50 max-h-80 overflow-y-auto"
                >
                  {query.length === 0 && (
                    <div className="px-4 py-3 text-sm font-medium text-gray-500 border-b">
                      Recent & Trending Searches
                    </div>
                  )}
                  
                  {suggestions.map((suggestion, index) => (
                    <div
                      key={suggestion.query}
                      onClick={() => handleSuggestionClick(suggestion)}
                      className={cn(
                        "px-4 py-3 cursor-pointer flex items-center justify-between group transition-colors",
                        focusedSuggestion === index 
                          ? "bg-primary-50 border-l-4 border-primary-500" 
                          : "hover:bg-gray-50"
                      )}
                    >
                      <div className="flex items-center gap-3">
                        {getSuggestionIcon(suggestion.type)}
                        <div>
                          <div className="font-medium text-gray-900">
                            {suggestion.query}
                          </div>
                          {suggestion.category && (
                            <div className="text-xs text-gray-500">
                              {suggestion.category}
                            </div>
                          )}
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-2">
                        {suggestion.type === 'trending' && (
                          <span className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full font-medium">
                            Trending
                          </span>
                        )}
                        {suggestion.resultCount && (
                          <span className="text-sm text-gray-500">
                            {suggestion.resultCount.toLocaleString()} results
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Action Buttons */}
            <Button
              onClick={onSearch}
              disabled={loading || !query.trim()}
              size="lg"
              className="px-8 whitespace-nowrap"
            >
              {loading ? (
                <div className="flex items-center gap-2">
                  <div className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
                  Searching...
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <Sparkles className="w-4 h-4" />
                  Search
                </div>
              )}
            </Button>

            <Button
              onClick={onFiltersToggle}
              variant="outline"
              size="lg"
              className={cn(
                "flex items-center gap-2",
                showFilters && "bg-primary-50 border-primary-300"
              )}
            >
              <Filter className="w-4 h-4" />
              Filters
            </Button>
          </div>

          {/* Quick Stats */}
          {totalResults !== undefined && totalResults > 0 && (
            <div className="flex items-center gap-4 text-sm text-gray-600 mt-2">
              <div className="flex items-center gap-1">
                <Building2 className="w-4 h-4" />
                <span className="font-medium">{totalResults.toLocaleString()}</span>
                <span>total records found</span>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default EnhancedSearchInterface; 