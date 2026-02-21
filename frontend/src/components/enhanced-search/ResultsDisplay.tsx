import React, { useState, useEffect, useRef } from 'react';

function pageNumbers(currentPage: number, totalPages: number): number[] {
  const start = Math.max(1, Math.min(currentPage - 2, totalPages - 4));
  const end = Math.min(totalPages, start + 4);
  return Array.from({ length: end - start + 1 }, (_, i) => start + i);
}
import { 
  ExternalLink, 
  Calendar, 
  DollarSign, 
  Building, 
  Eye, 
  ChevronRight,
  Users,
  FileText,
  TrendingUp,
  MapPin
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

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

interface ResultsDisplayProps {
  results: SearchResult[];
  onResultClick: (result: SearchResult) => void;
  loading?: boolean;
}

const sourceConfig = {
  senate_lda: { 
    name: 'Senate LDA (House & Senate Lobbying)', 
    color: 'bg-red-50 border-red-200 text-red-800', 
    icon: '🏛️',
    badgeColor: 'bg-red-100 text-red-700'
  },
  checkbook: { 
    name: 'NYC Contracts', 
    color: 'bg-green-50 border-green-200 text-green-800', 
    icon: '📋',
    badgeColor: 'bg-green-100 text-green-700'
  },
  dbnyc: { 
    name: 'FEC Campaign Finance', 
    color: 'bg-blue-50 border-blue-200 text-blue-800', 
    icon: '💰',
    badgeColor: 'bg-blue-100 text-blue-700'
  },
  nys_ethics: { 
    name: 'NY State', 
    color: 'bg-yellow-50 border-yellow-200 text-yellow-800', 
    icon: '🏛️',
    badgeColor: 'bg-yellow-100 text-yellow-700'
  },
  nyc_lobbyist: { 
    name: 'NYC Lobbyist', 
    color: 'bg-orange-50 border-orange-200 text-orange-800', 
    icon: '🤝',
    badgeColor: 'bg-orange-100 text-orange-700'
  }
};

const ITEMS_PER_PAGE = 20;

const EnhancedResultsDisplay: React.FC<ResultsDisplayProps> = ({ 
  results, 
  onResultClick, 
  loading = false 
}) => {
  const [expandedResults, setExpandedResults] = useState<Set<number>>(new Set());
  const [hoveredResult, setHoveredResult] = useState<number | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const listTopRef = useRef<HTMLDivElement>(null);
  const userInitiatedPageChange = useRef(false);

  // Reset to page 1 when the result set changes
  useEffect(() => { setCurrentPage(1); }, [results]);

  useEffect(() => {
    if (!userInitiatedPageChange.current) return;
    userInitiatedPageChange.current = false;
    if (listTopRef.current) {
      const top = listTopRef.current.getBoundingClientRect().top + window.scrollY - 80;
      window.scrollTo({ top: Math.max(0, top), behavior: 'smooth' });
    }
  }, [currentPage]);

  const goToPage = (page: number) => {
    userInitiatedPageChange.current = true;
    setCurrentPage(page);
  };

  const totalPages = Math.ceil(results.length / ITEMS_PER_PAGE);
  const pagedResults = results.slice((currentPage - 1) * ITEMS_PER_PAGE, currentPage * ITEMS_PER_PAGE);

  const toggleExpanded = (index: number, e: React.MouseEvent) => {
    e.stopPropagation();
    const newExpanded = new Set(expandedResults);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedResults(newExpanded);
  };

  const formatAmount = (amount: string | number | undefined) => {
    if (!amount) return null;
    const numAmount = typeof amount === 'number' ? amount : parseFloat(amount.replace(/[$,]/g, ''));
    if (isNaN(numAmount)) return amount;
    
    if (numAmount >= 1000000) {
      return `$${(numAmount / 1000000).toFixed(1)}M`;
    } else if (numAmount >= 1000) {
      return `$${(numAmount / 1000).toFixed(0)}K`;
    } else {
      return `$${numAmount.toLocaleString()}`;
    }
  };

  const formatDate = (date: string | undefined) => {
    if (!date) return null;
    try {
      return new Date(date).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    } catch {
      return date;
    }
  };

  const getResultIcon = (source: string, recordType?: string) => {
    if (recordType === 'lobbying') return <Users className="w-4 h-4" />;
    if (recordType === 'campaign_finance') return <DollarSign className="w-4 h-4" />;
    if (recordType === 'contracts') return <FileText className="w-4 h-4" />;
    return <Building className="w-4 h-4" />;
  };

  if (loading) {
    return (
      <div className="space-y-4">
        {[...Array(3)].map((_, i) => (
          <Card key={i} className="animate-pulse">
            <CardContent className="p-6">
              <div className="flex justify-between items-start mb-4">
                <div className="flex-1">
                  <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                  <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                </div>
                <div className="h-6 bg-gray-200 rounded w-20"></div>
              </div>
              <div className="h-3 bg-gray-200 rounded w-full mb-2"></div>
              <div className="h-3 bg-gray-200 rounded w-2/3"></div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Result count + pagination summary */}
      <div ref={listTopRef} className="flex items-center justify-between text-sm text-gray-500 px-1">
        <span>{results.length} result{results.length !== 1 ? 's' : ''} found</span>
        {totalPages > 1 && (
          <span>Page {currentPage} of {totalPages}</span>
        )}
      </div>

      {pagedResults.map((result, index) => {
        const isExpanded = expandedResults.has(index);
        const isHovered = hoveredResult === index;
        const config = sourceConfig[result.source as keyof typeof sourceConfig];
        const isYearHeader = result.source === 'nyc_lobbyist_year_header';

        if (isYearHeader) {
          return (
            <div key={index} className="relative">
              <div className="flex items-center gap-4 py-3">
                <div className="flex-1 h-px bg-gradient-to-r from-transparent via-gray-300 to-transparent"></div>
                <div className="flex items-center gap-3 px-4 py-2 bg-orange-50 border border-orange-200 rounded-lg">
                  <TrendingUp className="w-5 h-5 text-orange-600" />
                  <div className="text-center">
                    <div className="font-semibold text-orange-900">{result.title}</div>
                    <div className="text-sm text-orange-700">
                      {result.registration_count} registrations • {result.client_count} total clients
                    </div>
                  </div>
                </div>
                <div className="flex-1 h-px bg-gradient-to-r from-gray-300 via-transparent to-transparent"></div>
              </div>
            </div>
          );
        }

        return (
          <Card 
            key={index}
            className={cn(
              "transition-all duration-200 cursor-pointer hover:shadow-md",
              isHovered && "shadow-md scale-[1.01]",
              config?.color || "bg-gray-50 border-gray-200"
            )}
            onMouseEnter={() => setHoveredResult(index)}
            onMouseLeave={() => setHoveredResult(null)}
            onClick={() => onResultClick(result)}
          >
            <CardContent className="p-4">
              {/* Header Section */}
              <div className="flex justify-between items-start mb-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 mt-1">
                      {getResultIcon(result.source, result.record_type)}
                    </div>
                    <div className="min-w-0 flex-1">
                      <h3 className="font-semibold text-gray-900 text-lg leading-tight mb-1 line-clamp-2">
                        {result.title}
                      </h3>
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className={cn(
                          "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium",
                          config?.badgeColor || "bg-gray-100 text-gray-700"
                        )}>
                          {config?.icon} {config?.name || result.source}
                        </span>
                        {result.record_type && (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-700">
                            {result.record_type.replace('_', ' ').toUpperCase()}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Amount Badge */}
                {result.amount && (
                  <div className="flex-shrink-0 ml-4">
                    <div className="flex items-center gap-1 px-3 py-1.5 bg-white rounded-lg border shadow-sm">
                      <DollarSign className="w-4 h-4 text-green-600" />
                      <span className="font-semibold text-gray-900">
                        {formatAmount(result.amount)}
                      </span>
                    </div>
                  </div>
                )}
              </div>

              {/* Description */}
              <p className={cn(
                "text-gray-700 leading-relaxed mb-4",
                isExpanded ? "" : "line-clamp-2"
              )}>
                {result.description}
              </p>

              {/* Metadata Row */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4 text-sm text-gray-500">
                  {result.date && (
                    <div className="flex items-center gap-1">
                      <Calendar className="w-4 h-4" />
                      <span>{formatDate(result.date)}</span>
                    </div>
                  )}
                  {result.agency && (
                    <div className="flex items-center gap-1">
                      <Building className="w-4 h-4" />
                      <span className="truncate max-w-32">{result.agency}</span>
                    </div>
                  )}
                  {result.vendor && (
                    <div className="flex items-center gap-1">
                      <MapPin className="w-4 h-4" />
                      <span className="truncate max-w-32">{result.vendor}</span>
                    </div>
                  )}
                </div>

                <div className="flex items-center gap-2">
                  {result.url && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        window.open(result.url, '_blank');
                      }}
                      className="text-gray-500 hover:text-gray-700"
                    >
                      <ExternalLink className="w-4 h-4" />
                    </Button>
                  )}
                  
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => toggleExpanded(index, e)}
                    className="text-gray-500 hover:text-gray-700"
                  >
                    <ChevronRight className={cn(
                      "w-4 h-4 transition-transform",
                      isExpanded && "rotate-90"
                    )} />
                  </Button>

                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      onResultClick(result);
                    }}
                    className="text-primary-600 hover:text-primary-700"
                  >
                    <Eye className="w-4 h-4" />
                  </Button>
                </div>
              </div>

              {/* Expanded Details */}
              {isExpanded && (
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                    {result.client_count && (
                      <div>
                        <span className="font-medium text-gray-700">Client Count:</span>
                        <span className="ml-2 text-gray-600">{result.client_count}</span>
                      </div>
                    )}
                    {result.registration_count && (
                      <div>
                        <span className="font-medium text-gray-700">Registrations:</span>
                        <span className="ml-2 text-gray-600">{result.registration_count}</span>
                      </div>
                    )}
                    {result.year && (
                      <div>
                        <span className="font-medium text-gray-700">Year:</span>
                        <span className="ml-2 text-gray-600">{result.year}</span>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        );
      })}

      {/* Pagination controls */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between pt-2 border-t border-gray-200 flex-wrap gap-2">
          <div className="text-sm text-gray-500">
            {(currentPage - 1) * ITEMS_PER_PAGE + 1}–{Math.min(currentPage * ITEMS_PER_PAGE, results.length)} of {results.length} results
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={() => goToPage(Math.max(1, currentPage - 1))}
              disabled={currentPage === 1}
              className="px-3 py-1.5 text-sm border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              ← Prev
            </button>
            {pageNumbers(currentPage, totalPages).map(page => (
              <button
                key={page}
                onClick={() => goToPage(page)}
                className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                  page === currentPage
                    ? 'bg-blue-600 text-white font-semibold'
                    : 'border border-gray-300 hover:bg-gray-50 text-gray-700'
                }`}
              >
                {page}
              </button>
            ))}
            <button
              onClick={() => goToPage(Math.min(totalPages, currentPage + 1))}
              disabled={currentPage === totalPages}
              className="px-3 py-1.5 text-sm border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Next →
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default EnhancedResultsDisplay; 