import React, { useState, useMemo, useEffect } from 'react';
import { ChevronDownIcon, ChevronUpIcon, ArrowTopRightOnSquareIcon, FunnelIcon, ChartBarIcon, CurrencyDollarIcon, BuildingOfficeIcon, DocumentTextIcon } from '@heroicons/react/24/outline';

interface CheckbookResult {
  id?: string;
  source: string;
  title: string;
  vendor?: string;
  agency?: string;
  amount?: number | string;
  description?: string;
  date?: string;
  year?: number;
  url?: string;
  raw_records?: any[];
  client_count?: number;
  registration_count?: number;
  record_type?: string;
  entity_name?: string;
  document_id?: string;
}

interface CheckbookNYCStyleResultsProps {
  results: CheckbookResult[];
  isLoading?: boolean;
  searchQuery?: string;
  onViewDetails?: (result: CheckbookResult) => void;
}

const CheckbookNYCStyleResults: React.FC<CheckbookNYCStyleResultsProps> = ({ 
  results, 
  isLoading, 
  searchQuery = "Search Results",
  onViewDetails
}) => {
  const [sortConfig, setSortConfig] = useState<{key: string, direction: 'asc' | 'desc'} | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(25);
  
  // 🔧 FIX: Scroll to top when page changes
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, [currentPage]);
  
  // Helper function to safely parse amount
  const parseAmount = (amount: number | string | undefined): number => {
    if (typeof amount === 'number') return amount;
    if (typeof amount === 'string') return parseFloat(amount.replace(/[$,]/g, '')) || 0;
    return 0;
  };
  
  // Filter results to only include checkbook data
  const checkbookResults = useMemo(() => {
    return results.filter(result => result.source === 'checkbook');
  }, [results]);

  // Calculate financial summaries like CheckbookNYC
  const financialSummary = useMemo(() => {
    const totalSpending = checkbookResults.reduce((sum, result) => {
      return sum + parseAmount(result.amount);
    }, 0);

    // Group by year for trending
    const spendingByYear: Record<string, number> = {};
    checkbookResults.forEach(result => {
      const year = result.year?.toString() || new Date(result.date || '').getFullYear().toString() || 'Unknown';
      if (year !== 'Unknown' && year !== 'NaN') {
        spendingByYear[year] = (spendingByYear[year] || 0) + parseAmount(result.amount);
      }
    });

    // Group by agency
    const spendingByAgency: Record<string, number> = {};
    checkbookResults.forEach(result => {
      const agency = result.agency || 'Unknown Agency';
      spendingByAgency[agency] = (spendingByAgency[agency] || 0) + parseAmount(result.amount);
    });

    return {
      totalSpending,
      totalContracts: checkbookResults.length,
      spendingByYear,
      topAgencies: Object.entries(spendingByAgency)
        .sort(([,a], [,b]) => b - a)
        .slice(0, 5),
      yearRange: Object.keys(spendingByYear).sort()
    };
  }, [checkbookResults]);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const formatLargeCurrency = (amount: number) => {
    if (amount >= 1000000) {
      return `$${(amount / 1000000).toFixed(1)}M`;
    } else if (amount >= 1000) {
      return `$${(amount / 1000).toFixed(0)}K`;
    }
    return formatCurrency(amount);
  };

  // Sort and paginate results
  const sortedResults = useMemo(() => {
    if (!sortConfig) return checkbookResults;
    
    return [...checkbookResults].sort((a, b) => {
      const aVal = a[sortConfig.key as keyof CheckbookResult] ?? '';
      const bVal = b[sortConfig.key as keyof CheckbookResult] ?? '';
      
      if (sortConfig.key === 'amount') {
        const aNum = parseAmount(aVal as number | string);
        const bNum = parseAmount(bVal as number | string);
        return sortConfig.direction === 'asc' ? aNum - bNum : bNum - aNum;
      }
      
      const aStr = String(aVal).toLowerCase();
      const bStr = String(bVal).toLowerCase();
      
      if (sortConfig.direction === 'asc') {
        return aStr < bStr ? -1 : aStr > bStr ? 1 : 0;
      } else {
        return aStr > bStr ? -1 : aStr < bStr ? 1 : 0;
      }
    });
  }, [checkbookResults, sortConfig]);

  const totalPages = Math.ceil(sortedResults.length / itemsPerPage);
  const paginatedResults = sortedResults.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  const handleSort = (key: string) => {
    setSortConfig(current => ({
      key,
      direction: current?.key === key && current.direction === 'desc' ? 'asc' : 'desc'
    }));
  };

  const SortableHeader = ({ label, sortKey }: { label: string; sortKey: string }) => (
    <th 
      className="px-4 py-3 text-left text-sm font-semibold text-white bg-blue-600 cursor-pointer hover:bg-blue-700 transition-colors"
      onClick={() => handleSort(sortKey)}
    >
      <div className="flex items-center gap-1">
        {label}
        {sortConfig?.key === sortKey ? (
          sortConfig.direction === 'desc' ? 
            <ChevronDownIcon className="w-4 h-4" /> : 
            <ChevronUpIcon className="w-4 h-4" />
        ) : (
          <div className="w-4 h-4" />
        )}
      </div>
    </th>
  );

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-4">
        <div className="h-8 bg-gray-200 rounded w-1/3"></div>
        <div className="h-64 bg-gray-200 rounded"></div>
      </div>
    );
  }

  if (checkbookResults.length === 0) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-500">No CheckbookNYC results found.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header - CheckbookNYC Style */}
      <div className="bg-blue-600 text-white rounded-lg p-6">
        <h1 className="text-2xl font-bold mb-2">{searchQuery}</h1>
        <p className="text-blue-100">NYC Contract Spending Analysis</p>
      </div>

      {/* Financial Summary Cards - Like CheckbookNYC */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white border border-gray-300 rounded-lg p-4 text-center">
          <div className="flex items-center justify-center mb-2">
            <CurrencyDollarIcon className="w-8 h-8 text-green-600" />
          </div>
          <div className="text-sm text-gray-600 mb-1">Total Spending</div>
          <div className="text-xl font-bold text-green-600">
            {formatCurrency(financialSummary.totalSpending)}
          </div>
        </div>

        <div className="bg-white border border-gray-300 rounded-lg p-4 text-center">
          <div className="flex items-center justify-center mb-2">
            <DocumentTextIcon className="w-8 h-8 text-blue-600" />
          </div>
          <div className="text-sm text-gray-600 mb-1">Total Contracts</div>
          <div className="text-xl font-bold text-blue-600">
            {financialSummary.totalContracts}
          </div>
        </div>

        <div className="bg-white border border-gray-300 rounded-lg p-4 text-center">
          <div className="flex items-center justify-center mb-2">
            <BuildingOfficeIcon className="w-8 h-8 text-purple-600" />
          </div>
          <div className="text-sm text-gray-600 mb-1">Agencies</div>
          <div className="text-xl font-bold text-purple-600">
            {financialSummary.topAgencies.length}
          </div>
        </div>

        <div className="bg-white border border-gray-300 rounded-lg p-4 text-center">
          <div className="flex items-center justify-center mb-2">
            <ChartBarIcon className="w-8 h-8 text-orange-600" />
          </div>
          <div className="text-sm text-gray-600 mb-1">Year Range</div>
          <div className="text-xl font-bold text-orange-600">
            {financialSummary.yearRange.length > 0 ? 
              `${financialSummary.yearRange[0]}-${financialSummary.yearRange[financialSummary.yearRange.length - 1]}` : 
              'N/A'}
          </div>
        </div>
      </div>

      {/* Top 5 Agencies - CheckbookNYC Style */}
      <div className="bg-white border border-gray-300 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Top 5 Agencies</h3>
        <div className="space-y-3">
          {financialSummary.topAgencies.map(([agency, amount], index) => (
            <div key={agency} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-b-0">
              <div className="flex items-center gap-3">
                <div className="w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-bold">
                  {index + 1}
                </div>
                <div className="font-medium text-gray-900">{agency}</div>
              </div>
              <div className="font-bold text-green-600">{formatCurrency(amount)}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Contract Details Table - CheckbookNYC Style */}
      <div className="bg-white border border-gray-300 rounded-lg overflow-hidden">
        <div className="bg-blue-600 px-4 py-3">
          <h2 className="text-lg font-semibold text-white">
            Contract Details ({sortedResults.length} records found)
          </h2>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full">
            <thead>
              <tr>
                <SortableHeader label="Contract ID" sortKey="document_id" />
                <SortableHeader label="Purpose" sortKey="title" />
                <SortableHeader label="Contracting Agency" sortKey="agency" />
                <SortableHeader label="Prime Vendor" sortKey="vendor" />
                <SortableHeader label="YTD Spending" sortKey="amount" />
                <SortableHeader label="Start Date" sortKey="date" />
                <th className="px-4 py-3 text-left text-sm font-semibold text-white bg-blue-600">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {paginatedResults.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-gray-500">
                    No contract records found.
                  </td>
                </tr>
              ) : (
                paginatedResults.map((result, index) => {
                  const amount = parseAmount(result.amount);
                  
                  return (
                    <tr key={result.id || index} className="hover:bg-gray-50 transition-colors">
                      <td className="px-4 py-3 text-sm">
                        <div className="font-mono text-blue-600">
                          {result.document_id || 'N/A'}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-sm">
                        <div className="font-medium text-gray-900 max-w-md">
                          {result.title || result.description || 'No description available'}
                        </div>
                        {result.description && result.title !== result.description && (
                          <div className="text-xs text-gray-500 mt-1 line-clamp-2">
                            {result.description.substring(0, 150)}
                            {result.description.length > 150 && '...'}
                          </div>
                        )}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-900">
                        <div className="font-medium">
                          {result.agency || 'Unknown Agency'}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-sm">
                        <div className="font-medium text-gray-900">
                          {result.vendor || result.entity_name || 'Unknown Vendor'}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-sm">
                        <span className="font-bold text-green-600 text-base">
                          {formatCurrency(amount)}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-500">
                        {result.date ? new Date(result.date).toLocaleDateString() : 
                         result.year ? result.year.toString() : 'N/A'}
                      </td>
                      <td className="px-4 py-3 text-sm">
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
                            View Details
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

        {/* Pagination - CheckbookNYC Style */}
        {totalPages > 1 && (
          <div className="bg-gray-50 px-4 py-3 border-t border-gray-200">
            <div className="flex items-center justify-between">
              <div className="text-sm text-gray-700">
                Showing {((currentPage - 1) * itemsPerPage) + 1} to {Math.min(currentPage * itemsPerPage, sortedResults.length)} of {sortedResults.length} results
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                  disabled={currentPage === 1}
                  className="px-3 py-1 text-sm border border-gray-300 rounded-md hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Previous
                </button>
                <span className="text-sm text-gray-700">
                  Page {currentPage} of {totalPages}
                </span>
                <button
                  onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                  disabled={currentPage === totalPages}
                  className="px-3 py-1 text-sm border border-gray-300 rounded-md hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Next
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CheckbookNYCStyleResults; 