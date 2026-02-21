import React, { useState, useMemo, useEffect, useRef } from 'react';

function pageNumbers(currentPage: number, totalPages: number): number[] {
  const start = Math.max(1, Math.min(currentPage - 2, totalPages - 4));
  const end = Math.min(totalPages, start + 4);
  return Array.from({ length: end - start + 1 }, (_, i) => start + i);
}
import { ChevronDownIcon, ChevronUpIcon, ArrowTopRightOnSquareIcon, DocumentIcon, CalendarIcon, CurrencyDollarIcon } from '@heroicons/react/24/outline';
interface SearchResult {
  id?: string;
  source: string;
  title: string;
  vendor?: string;
  agency?: string;
  amount?: number;
  description?: string;
  date?: string;
  year?: number;
  url?: string;
  raw_records?: any[];
}

interface CheckbookStyleResultsProps {
  results: SearchResult[];
  isLoading?: boolean;
}

interface GroupedResults {
  [source: string]: SearchResult[];
}

const ITEMS_PER_PAGE = 20;

const CheckbookStyleResults: React.FC<CheckbookStyleResultsProps> = ({ results, isLoading }) => {
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());
  const [activeTab, setActiveTab] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'date' | 'amount' | 'relevance'>('relevance');
  const [currentPage, setCurrentPage] = useState(1);
  const listTopRef = useRef<HTMLDivElement>(null);
  const userInitiatedPageChange = useRef(false);

  // Reset to page 1 when tab or sort changes
  useEffect(() => { setCurrentPage(1); }, [activeTab, sortBy]);

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

  // Group results by source
  const groupedResults = useMemo(() => {
    const grouped = results.reduce((acc: GroupedResults, result) => {
      if (!acc[result.source]) {
        acc[result.source] = [];
      }
      acc[result.source].push(result);
      return acc;
    }, {});

    // Sort each group
    Object.keys(grouped).forEach(source => {
      grouped[source].sort((a, b) => {
        if (sortBy === 'amount') {
          return (b.amount || 0) - (a.amount || 0);
        } else if (sortBy === 'date') {
          return new Date(b.date || '').getTime() - new Date(a.date || '').getTime();
        }
        return 0; // relevance (default order)
      });
    });

    return grouped;
  }, [results, sortBy]);

  const sourceTabs = [
    { id: 'all', label: 'All Results', count: results.length },
    { id: 'checkbook', label: 'NYC Contracts', count: groupedResults['checkbook']?.length || 0 },
    { id: 'nyc_lobbyist', label: 'NYC Lobbying', count: groupedResults['nyc_lobbyist']?.length || 0 },
    { id: 'senate_lda', label: 'Federal Lobbying', count: groupedResults['senate_lda']?.length || 0 },
    { id: 'nys_ethics', label: 'NY State', count: groupedResults['nys_ethics']?.length || 0 },
    { id: 'dbnyc', label: 'Federal Contracts', count: groupedResults['dbnyc']?.length || 0 },
  ].filter(tab => tab.count > 0 || tab.id === 'all');

  const displayResults = useMemo(() => {
    if (activeTab === 'all') {
      return results;
    }
    return groupedResults[activeTab] || [];
  }, [activeTab, results, groupedResults]);

  const totalPages = Math.ceil(displayResults.length / ITEMS_PER_PAGE);
  const pagedDisplayResults = displayResults.slice(
    (currentPage - 1) * ITEMS_PER_PAGE,
    currentPage * ITEMS_PER_PAGE
  );

  const toggleExpanded = (id: string) => {
    const newExpanded = new Set(expandedItems);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedItems(newExpanded);
  };

  const formatCurrency = (amount: number | undefined) => {
    if (!amount || amount === 0) return 'N/A';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const getSourceIcon = (source: string) => {
    switch (source) {
      case 'checkbook':
        return <DocumentIcon className="h-5 w-5 text-blue-600" />;
      case 'nyc_lobbyist':
        return <CurrencyDollarIcon className="h-5 w-5 text-green-600" />;
      case 'senate_lda':
        return <DocumentIcon className="h-5 w-5 text-purple-600" />;
      case 'nys_ethics':
        return <CalendarIcon className="h-5 w-5 text-orange-600" />;
      case 'dbnyc':
        return <DocumentIcon className="h-5 w-5 text-red-600" />;
      default:
        return <DocumentIcon className="h-5 w-5 text-gray-600" />;
    }
  };

  const getSourceColor = (source: string) => {
    switch (source) {
      case 'checkbook': return 'bg-blue-50 border-blue-200';
      case 'nyc_lobbyist': return 'bg-green-50 border-green-200';
      case 'senate_lda': return 'bg-purple-50 border-purple-200';
      case 'nys_ethics': return 'bg-orange-50 border-orange-200';
      case 'dbnyc': return 'bg-red-50 border-red-200';
      default: return 'bg-gray-50 border-gray-200';
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="bg-white border border-gray-200 rounded-lg p-6 animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
            <div className="h-3 bg-gray-200 rounded w-1/2 mb-2"></div>
            <div className="h-3 bg-gray-200 rounded w-1/4"></div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Results Header with Tabs */}
      <div className="bg-white border border-gray-200 rounded-lg">
        <div className="border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">
              Search Results ({results.length} total)
            </h2>
            <div className="flex items-center gap-4">
              <label className="text-sm font-medium text-gray-700">
                Sort by:
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as any)}
                  className="ml-2 border border-gray-300 rounded-md px-3 py-1 text-sm"
                >
                  <option value="relevance">Relevance</option>
                  <option value="amount">Amount</option>
                  <option value="date">Date</option>
                </select>
              </label>
            </div>
          </div>
        </div>

        {/* Source Tabs */}
        <div className="flex overflow-x-auto border-b border-gray-200">
          {sourceTabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-6 py-3 text-sm font-medium whitespace-nowrap border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600 bg-blue-50'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.label} ({tab.count})
            </button>
          ))}
        </div>
      </div>

      {/* Scroll anchor + result count */}
      <div ref={listTopRef} className="flex items-center justify-between text-sm text-gray-500 px-1">
        <span>{displayResults.length} result{displayResults.length !== 1 ? 's' : ''}</span>
        {totalPages > 1 && <span>Page {currentPage} of {totalPages}</span>}
      </div>

      {/* Results List */}
      <div className="space-y-3">
        {pagedDisplayResults.length === 0 ? (
          <div className="bg-white border border-gray-200 rounded-lg p-8 text-center">
            <p className="text-gray-500">No results found for the current filter.</p>
          </div>
        ) : (
          pagedDisplayResults.map((result) => {
            const isExpanded = expandedItems.has(result.id || '');
            return (
              <div
                key={result.id}
                className={`bg-white border rounded-lg overflow-hidden transition-all duration-200 ${getSourceColor(result.source)}`}
              >
                {/* Main Result Card */}
                <div className="p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      {/* Title and Source */}
                      <div className="flex items-center gap-2 mb-2">
                        {getSourceIcon(result.source)}
                        <h3 className="text-lg font-semibold text-gray-900 truncate">
                          {result.title}
                        </h3>
                        <span className="text-xs px-2 py-1 bg-gray-100 text-gray-600 rounded-full">
                          {result.source.replace('_', ' ').toUpperCase()}
                        </span>
                      </div>

                      {/* Key Information Row */}
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-3">
                        <div>
                          <span className="text-sm font-medium text-gray-500">Vendor/Entity:</span>
                          <p className="text-sm text-gray-900 truncate">{result.vendor || 'N/A'}</p>
                        </div>
                        <div>
                          <span className="text-sm font-medium text-gray-500">Agency:</span>
                          <p className="text-sm text-gray-900 truncate">{result.agency || 'N/A'}</p>
                        </div>
                        <div>
                          <span className="text-sm font-medium text-gray-500">Amount:</span>
                          <p className="text-sm font-semibold text-green-600">
                            {formatCurrency(result.amount)}
                          </p>
                        </div>
                      </div>

                      {/* Description */}
                      <p className="text-sm text-gray-600 mb-3 line-clamp-2">
                        {result.description}
                      </p>

                      {/* Date and Actions Row */}
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4 text-sm text-gray-500">
                          <span className="flex items-center gap-1">
                            <CalendarIcon className="h-4 w-4" />
                            {result.date ? new Date(result.date).toLocaleDateString() : 'N/A'}
                          </span>
                          {result.year && (
                            <span>Year: {result.year}</span>
                          )}
                        </div>
                        <div className="flex items-center gap-2">
                          {result.url && (
                            <a
                              href={result.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800"
                            >
                              <ArrowTopRightOnSquareIcon className="h-4 w-4" />
                              Original
                            </a>
                          )}
                          <button
                            onClick={() => toggleExpanded(result.id || '')}
                            className="inline-flex items-center gap-1 text-sm text-gray-600 hover:text-gray-800"
                          >
                            {isExpanded ? (
                              <>
                                <ChevronUpIcon className="h-4 w-4" />
                                Less Details
                              </>
                            ) : (
                              <>
                                <ChevronDownIcon className="h-4 w-4" />
                                Full Details
                              </>
                            )}
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Expanded Details */}
                {isExpanded && (
                  <div className="border-t border-gray-200 bg-gray-50 p-6">
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                      {/* All Available Fields */}
                      <div className="space-y-3">
                        <h4 className="font-semibold text-gray-900">Record Details</h4>
                        <dl className="space-y-2">
                          {Object.entries(result).map(([key, value]) => {
                            if (key === 'id' || key === 'raw_records' || !value) return null;
                            
                            const displayKey = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                            const displayValue = Array.isArray(value) ? value.join(', ') :
                                               typeof value === 'object' ? JSON.stringify(value) :
                                               String(value);

                            return (
                              <div key={key} className="grid grid-cols-3 gap-2">
                                <dt className="text-sm font-medium text-gray-500 truncate">
                                  {displayKey}:
                                </dt>
                                <dd className="text-sm text-gray-900 col-span-2 break-words">
                                  {displayValue.length > 100 ? 
                                    `${displayValue.substring(0, 100)}...` : 
                                    displayValue
                                  }
                                </dd>
                              </div>
                            );
                          })}
                        </dl>
                      </div>

                      {/* Raw Records Table (if available) */}
                      {result.raw_records && result.raw_records.length > 0 && (
                        <div className="space-y-3">
                          <h4 className="font-semibold text-gray-900">
                            Raw Records ({result.raw_records.length})
                          </h4>
                          <div className="max-h-64 overflow-auto">
                            <table className="min-w-full text-xs">
                              <thead className="bg-gray-100 sticky top-0">
                                <tr>
                                  <th className="px-2 py-1 text-left font-medium text-gray-700">Field</th>
                                  <th className="px-2 py-1 text-left font-medium text-gray-700">Value</th>
                                </tr>
                              </thead>
                              <tbody className="divide-y divide-gray-200">
                                {result.raw_records.slice(0, 5).map((record, idx) => (
                                  <React.Fragment key={idx}>
                                    {Object.entries(record).slice(0, 10).map(([key, value]) => (
                                      <tr key={`${idx}-${key}`} className="hover:bg-gray-50">
                                        <td className="px-2 py-1 text-gray-600 font-medium">
                                          {key.replace(/_/g, ' ')}
                                        </td>
                                        <td className="px-2 py-1 text-gray-900 truncate max-w-xs">
                                          {String(value || 'N/A')}
                                        </td>
                                      </tr>
                                    ))}
                                  </React.Fragment>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* Pagination controls */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between pt-2 border-t border-gray-200 flex-wrap gap-2">
          <div className="text-sm text-gray-500">
            {(currentPage - 1) * ITEMS_PER_PAGE + 1}–{Math.min(currentPage * ITEMS_PER_PAGE, displayResults.length)} of {displayResults.length} results
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

export default CheckbookStyleResults; 