import React, { useState, useMemo, useEffect } from 'react';
import { ChevronDownIcon, ChevronUpIcon, ArrowTopRightOnSquareIcon, FunnelIcon } from '@heroicons/react/24/outline';

function pageNumbers(currentPage: number, totalPages: number): number[] {
  const start = Math.max(1, Math.min(currentPage - 2, totalPages - 4));
  const end = Math.min(totalPages, start + 4);
  return Array.from({ length: end - start + 1 }, (_, i) => start + i);
}

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
  client_count?: number;
  registration_count?: number;
  record_type?: string;
}

interface NYCLobbyistStyleResultsProps {
  results: SearchResult[];
  isLoading?: boolean;
  onViewDetails?: (result: SearchResult) => void;
}

const NYCLobbyistStyleResults: React.FC<NYCLobbyistStyleResultsProps> = ({ results, isLoading, onViewDetails }) => {
  const [sortConfig, setSortConfig] = useState<{ key: string; direction: 'asc' | 'desc' } | null>(null);
  const [searchBy, setSearchBy] = useState<'entity' | 'client' | 'all'>('all');
  const [selectedYear, setSelectedYear] = useState<string>('');
  const [selectedSource, setSelectedSource] = useState<string>('');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 20;
  const tableTopRef = React.useRef<HTMLDivElement>(null);
  const userInitiatedPageChange = React.useRef(false);

  // Reset to page 1 on filter changes without triggering scroll
  useEffect(() => { setCurrentPage(1); }, [selectedYear, selectedSource, searchBy]);

  // Scroll only on explicit user page navigation
  useEffect(() => {
    if (!userInitiatedPageChange.current) return;
    userInitiatedPageChange.current = false;
    if (tableTopRef.current) {
      const top = tableTopRef.current.getBoundingClientRect().top + window.scrollY - 80;
      window.scrollTo({ top: Math.max(0, top), behavior: 'smooth' });
    }
  }, [currentPage]);

  const goToPage = (page: number) => {
    userInitiatedPageChange.current = true;
    setCurrentPage(page);
  };

  // Source configuration matching your existing setup
  const sourceConfig = {
    senate_lda: { name: 'Federal LDA (Senate)', color: '#1e40af', bgColor: '#dbeafe' },
    house_lda: { name: 'Federal LDA (House)', color: '#7c3aed', bgColor: '#ede9fe' },
    checkbook: { name: 'NYC Contracts', color: '#059669', bgColor: '#d1fae5' },
    dbnyc: { name: 'Federal Spending', color: '#dc2626', bgColor: '#fee2e2' },
    nys_ethics: { name: 'NY State Ethics', color: '#ea580c', bgColor: '#fed7aa' },
    nyc_lobbyist: { name: 'NYC Lobbying', color: '#0891b2', bgColor: '#cffafe' }
  };

  // Get unique years from results
  const availableYears = useMemo(() => {
    const years = new Set<string>();
    results.forEach(result => {
      if (result.year) years.add(result.year.toString());
      if (result.date) {
        const year = new Date(result.date).getFullYear().toString();
        years.add(year);
      }
    });
    return Array.from(years).sort().reverse();
  }, [results]);

  // Filter and sort results
  const filteredAndSortedResults = useMemo(() => {
    let filtered = results.filter(result => {
      if (selectedYear) {
        const resultYear = result.year?.toString() || 
                          (result.date ? new Date(result.date).getFullYear().toString() : '');
        if (resultYear !== selectedYear) return false;
      }
      if (selectedSource && result.source !== selectedSource) return false;
      return true;
    });

    // Sort results
    if (sortConfig) {
      filtered.sort((a, b) => {
        let aValue = a[sortConfig.key as keyof SearchResult];
        let bValue = b[sortConfig.key as keyof SearchResult];

        // Handle different types
        if (sortConfig.key === 'amount') {
          aValue = (a.amount || 0) as number;
          bValue = (b.amount || 0) as number;
        } else if (sortConfig.key === 'date') {
          aValue = new Date(a.date || '').getTime();
          bValue = new Date(b.date || '').getTime();
        } else {
          aValue = String(aValue || '').toLowerCase();
          bValue = String(bValue || '').toLowerCase();
        }

        if (aValue < bValue) {
          return sortConfig.direction === 'asc' ? -1 : 1;
        }
        if (aValue > bValue) {
          return sortConfig.direction === 'asc' ? 1 : -1;
        }
        return 0;
      });
    }

    return filtered;
  }, [results, selectedYear, selectedSource, sortConfig]);

  // Pagination
  const totalPages = Math.ceil(filteredAndSortedResults.length / itemsPerPage);
  const paginatedResults = filteredAndSortedResults.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  const handleSort = (key: string) => {
    let direction: 'asc' | 'desc' = 'asc';
    if (sortConfig && sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
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

  const SortableHeader = ({ label, sortKey }: { label: string; sortKey: string }) => (
    <th 
      className="px-4 py-3 text-left text-sm font-semibold text-white bg-blue-600 cursor-pointer hover:bg-blue-700 transition-colors"
      onClick={() => handleSort(sortKey)}
    >
      <div className="flex items-center gap-1">
        {label}
        {sortConfig?.key === sortKey && (
          sortConfig.direction === 'asc' ? 
            <ChevronUpIcon className="w-4 h-4" /> : 
            <ChevronDownIcon className="w-4 h-4" />
        )}
      </div>
    </th>
  );

  if (isLoading) {
    return (
      <div className="bg-white border border-gray-300 rounded-lg overflow-hidden">
        <div className="animate-pulse p-6">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-12 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Search and Filter Controls - NYC Style */}
      <div className="bg-gray-100 border border-gray-300 rounded-lg p-4">
        <div className="flex items-center gap-2 mb-4">
          <FunnelIcon className="w-5 h-5 text-gray-600" />
          <h3 className="text-lg font-semibold text-gray-900">Search Filters</h3>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Year</label>
            <select
              value={selectedYear}
              onChange={(e) => setSelectedYear(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">All Years</option>
              {availableYears.map(year => (
                <option key={year} value={year}>{year}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Sort By</label>
            <select
              value={sortConfig ? `${sortConfig.key}-${sortConfig.direction}` : ''}
              onChange={(e) => {
                if (!e.target.value) { setSortConfig(null); return; }
                const [key, dir] = e.target.value.split('-');
                setSortConfig({ key, direction: dir as 'asc' | 'desc' });
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-md bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">Default</option>
              <option value="date-desc">Date (Newest)</option>
              <option value="date-asc">Date (Oldest)</option>
              <option value="amount-desc">Amount (High → Low)</option>
              <option value="amount-asc">Amount (Low → High)</option>
              <option value="vendor-asc">Lobbyist (A → Z)</option>
            </select>
          </div>

          <div className="flex items-end">
            <button
              onClick={() => {
                setSelectedYear('');
                setSelectedSource('');
                setSearchBy('all');
                setSortConfig(null);
                setCurrentPage(1);
              }}
              className="px-4 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600 transition-colors w-full"
            >
              Reset Filters
            </button>
          </div>
        </div>
      </div>

      {/* Scroll anchor — sits at the true top of the table block */}
      <div ref={tableTopRef} />

      {/* Results Table - NYC Lobbying Style */}
      <div className="bg-white border border-gray-300 rounded-lg overflow-hidden">
        <div className="bg-blue-600 px-4 py-3">
          <h2 className="text-lg font-semibold text-white">
            Search Results ({filteredAndSortedResults.length} records found)
          </h2>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full">
            <thead className="sticky top-0 z-10">
              <tr>
                <SortableHeader label="Lobbyist" sortKey="vendor" />
                <SortableHeader label="Client / Description" sortKey="title" />
                <SortableHeader label="Agency Targets" sortKey="agency" />
                <SortableHeader label="Compensation" sortKey="amount" />
                <SortableHeader label="Year" sortKey="date" />
                <th className="px-4 py-3 text-left text-sm font-semibold text-white bg-blue-600">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-100">
              {paginatedResults.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-gray-500">
                    No results found. Try adjusting your filters.
                  </td>
                </tr>
              ) : (
                paginatedResults.map((result, index) => {
                  return (
                    <tr key={result.id || index} className="hover:bg-gray-50 transition-colors">
                      <td className="px-3 py-2 text-sm">
                        <div className="font-semibold text-gray-900">
                          {result.vendor || result.title?.replace(/NYC Lobbyist: /, '').replace(/ \(\d+\)$/, '') || 'N/A'}
                        </div>
                        {result.registration_count != null && result.registration_count > 0 && (
                          <div className="text-xs text-gray-500 mt-0.5">
                            {result.registration_count} filing{result.registration_count !== 1 ? 's' : ''}
                          </div>
                        )}
                      </td>
                      <td className="px-3 py-2 text-sm">
                        {result.client_count != null && result.client_count > 0 && (
                          <div className="text-xs font-medium text-blue-700 mb-0.5">
                            {result.client_count} client{result.client_count !== 1 ? 's' : ''}
                          </div>
                        )}
                        {result.description && (
                          <div className="text-xs text-gray-600 line-clamp-2">
                            {result.description.substring(0, 180)}
                            {result.description.length > 180 && '...'}
                          </div>
                        )}
                      </td>
                      <td className="px-3 py-2 text-sm text-gray-700 max-w-xs">
                        <div className="line-clamp-2 text-xs">{result.agency || '—'}</div>
                      </td>
                      <td className="px-3 py-2 text-sm">
                        <span className={`font-semibold ${result.amount ? 'text-green-600' : 'text-gray-400'}`}>
                          {formatCurrency(result.amount)}
                        </span>
                      </td>
                      <td className="px-3 py-2 text-sm font-medium text-gray-700">
                        {result.year ? result.year.toString() : 
                         (result.date ? new Date(result.date).getFullYear() : '—')}
                      </td>
                      <td className="px-3 py-2 text-sm">
                        <div className="flex items-center gap-2">
                          {result.url && (
                            <a
                              href={result.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-blue-600 hover:text-blue-800 text-xs flex items-center gap-1"
                            >
                              <ArrowTopRightOnSquareIcon className="w-3 h-3" />
                              View
                            </a>
                          )}
                          <button 
                            onClick={() => onViewDetails?.(result)}
                            className="text-blue-600 hover:text-blue-800 text-xs hover:bg-blue-50 px-2 py-1 rounded transition-colors"
                          >
                            Details
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="bg-gray-50 px-4 py-3 border-t border-gray-200">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <div className="text-sm text-gray-700">
                {((currentPage - 1) * itemsPerPage) + 1}–{Math.min(currentPage * itemsPerPage, filteredAndSortedResults.length)} of {filteredAndSortedResults.length} results
              </div>
              <div className="flex items-center gap-1">
                <button
                  onClick={() => goToPage(Math.max(1, currentPage - 1))}
                  disabled={currentPage === 1}
                  className="px-3 py-1 text-sm border border-gray-300 rounded-md hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  ← Prev
                </button>
                {pageNumbers(currentPage, totalPages).map(page => (
                  <button
                    key={page}
                    onClick={() => goToPage(page)}
                    className={`px-3 py-1 text-sm rounded-md transition-colors ${
                      page === currentPage
                        ? 'bg-blue-600 text-white font-semibold'
                        : 'border border-gray-300 hover:bg-gray-100 text-gray-700'
                    }`}
                  >
                    {page}
                  </button>
                ))}
                <button
                  onClick={() => goToPage(Math.min(totalPages, currentPage + 1))}
                  disabled={currentPage === totalPages}
                  className="px-3 py-1 text-sm border border-gray-300 rounded-md hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  Next →
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default NYCLobbyistStyleResults; 