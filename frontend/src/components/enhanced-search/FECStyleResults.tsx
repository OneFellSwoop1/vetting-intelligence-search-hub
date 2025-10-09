import React, { useState, useMemo } from 'react';
import { 
  ChevronDownIcon, 
  ChevronUpIcon, 
  ArrowTopRightOnSquareIcon, 
  UserIcon,
  BuildingOfficeIcon,
  CurrencyDollarIcon,
  CalendarIcon,
  MapPinIcon,
  BriefcaseIcon
} from '@heroicons/react/24/outline';
import { motion, AnimatePresence } from 'framer-motion';

interface FECResult {
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
  record_type?: string;
  
  // FEC-specific fields
  candidate_id?: string;
  committee_id?: string;
  party?: string;
  office?: string;
  state?: string;
  district?: string;
  contributor_name?: string;
  contributor_employer?: string;
  contributor_occupation?: string;
  contributor_city?: string;
  contributor_state?: string;
  committee_name?: string;
  election_type?: string;
  two_year_transaction_period?: number;
  raw_data?: any;
}

interface FECStyleResultsProps {
  results: FECResult[];
  isLoading?: boolean;
  searchQuery?: string;
  onViewDetails?: (result: FECResult) => void;
}

const FECStyleResults: React.FC<FECStyleResultsProps> = ({ 
  results, 
  isLoading, 
  searchQuery = "Campaign Finance Results",
  onViewDetails
}) => {
  const [sortConfig, setSortConfig] = useState<{key: string, direction: 'asc' | 'desc'} | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedRecordType, setSelectedRecordType] = useState<string>('all');
  const [selectedParty, setSelectedParty] = useState<string>('all');
  const itemsPerPage = 20;
  
  // Filter results to only include FEC data
  const fecResults = useMemo(() => {
    return results.filter(result => result.source === 'fec');
  }, [results]);

  // Filter by record type and party
  const filteredResults = useMemo(() => {
    let filtered = fecResults;
    
    if (selectedRecordType !== 'all') {
      filtered = filtered.filter(result => result.record_type === selectedRecordType);
    }
    
    if (selectedParty !== 'all') {
      filtered = filtered.filter(result => result.party === selectedParty);
    }
    
    return filtered;
  }, [fecResults, selectedRecordType, selectedParty]);

  // Calculate financial summaries
  const financialSummary = useMemo(() => {
    const totalAmount = filteredResults.reduce((sum, result) => {
      return sum + (result.amount || 0);
    }, 0);

    // Group by record type
    const byRecordType: Record<string, number> = {};
    filteredResults.forEach(result => {
      const type = result.record_type || 'unknown';
      byRecordType[type] = (byRecordType[type] || 0) + (result.amount || 0);
    });

    // Group by party
    const byParty: Record<string, number> = {};
    filteredResults.forEach(result => {
      const party = result.party || 'Unknown';
      byParty[party] = (byParty[party] || 0) + (result.amount || 0);
    });

    // Get unique election cycles
    const cycles = new Set<number>();
    filteredResults.forEach(result => {
      if (result.two_year_transaction_period) {
        cycles.add(result.two_year_transaction_period);
      }
    });

    return {
      totalAmount,
      totalRecords: filteredResults.length,
      byRecordType: Object.entries(byRecordType).sort(([,a], [,b]) => b - a),
      byParty: Object.entries(byParty).sort(([,a], [,b]) => b - a),
      electionCycles: Array.from(cycles).sort((a, b) => b - a)
    };
  }, [filteredResults]);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const getPartyColor = (party?: string) => {
    switch (party?.toUpperCase()) {
      case 'DEM': return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'REP': return 'bg-red-100 text-red-800 border-red-200';
      case 'IND': return 'bg-purple-100 text-purple-800 border-purple-200';
      case 'GRE': return 'bg-green-100 text-green-800 border-green-200';
      case 'LIB': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getRecordTypeIcon = (recordType?: string) => {
    switch (recordType) {
      case 'candidate': return <UserIcon className="w-5 h-5" />;
      case 'committee': return <BuildingOfficeIcon className="w-5 h-5" />;
      case 'contribution': return <CurrencyDollarIcon className="w-5 h-5 text-green-600" />;
      case 'disbursement': return <CurrencyDollarIcon className="w-5 h-5 text-red-600" />;
      default: return <BuildingOfficeIcon className="w-5 h-5" />;
    }
  };

  // Sort and paginate results
  const sortedResults = useMemo(() => {
    if (!sortConfig) return filteredResults;
    
    return [...filteredResults].sort((a, b) => {
      const aVal = a[sortConfig.key as keyof FECResult] ?? '';
      const bVal = b[sortConfig.key as keyof FECResult] ?? '';
      
      if (sortConfig.key === 'amount') {
        const aNum = (aVal as number) || 0;
        const bNum = (bVal as number) || 0;
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
  }, [filteredResults, sortConfig]);

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

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-4">
        <div className="h-8 bg-gray-200 rounded w-1/3"></div>
        <div className="h-64 bg-gray-200 rounded"></div>
      </div>
    );
  }

  if (fecResults.length === 0) {
    return (
      <div className="text-center py-8">
        <div className="backdrop-blur-sm bg-white/10 rounded-2xl border border-white/20 p-8">
          <CurrencyDollarIcon className="w-16 h-16 text-blue-400 mx-auto mb-4" />
          <p className="text-gray-300">No FEC campaign finance results found.</p>
        </div>
      </div>
    );
  }

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      {/* Header */}
      <div className="backdrop-blur-xl bg-gradient-to-r from-blue-500/20 to-purple-500/20 border border-white/20 rounded-2xl p-6">
        <h1 className="text-2xl font-bold text-white mb-2 flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-500 rounded-xl flex items-center justify-center">
            <CurrencyDollarIcon className="w-6 h-6 text-white" />
          </div>
          {searchQuery} - Campaign Finance
        </h1>
        <p className="text-blue-100">Federal Election Commission (FEC) Data</p>
      </div>

      {/* Financial Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <motion.div 
          whileHover={{ scale: 1.02 }}
          className="backdrop-blur-sm bg-white/10 border border-white/20 rounded-xl p-4 text-center"
        >
          <CurrencyDollarIcon className="w-8 h-8 text-green-400 mx-auto mb-2" />
          <div className="text-sm text-gray-300 mb-1">Total Amount</div>
          <div className="text-xl font-bold text-green-400">
            {formatCurrency(financialSummary.totalAmount)}
          </div>
        </motion.div>

        <motion.div 
          whileHover={{ scale: 1.02 }}
          className="backdrop-blur-sm bg-white/10 border border-white/20 rounded-xl p-4 text-center"
        >
          <BuildingOfficeIcon className="w-8 h-8 text-blue-400 mx-auto mb-2" />
          <div className="text-sm text-gray-300 mb-1">Total Records</div>
          <div className="text-xl font-bold text-blue-400">
            {financialSummary.totalRecords}
          </div>
        </motion.div>

        <motion.div 
          whileHover={{ scale: 1.02 }}
          className="backdrop-blur-sm bg-white/10 border border-white/20 rounded-xl p-4 text-center"
        >
          <UserIcon className="w-8 h-8 text-purple-400 mx-auto mb-2" />
          <div className="text-sm text-gray-300 mb-1">Record Types</div>
          <div className="text-xl font-bold text-purple-400">
            {financialSummary.byRecordType.length}
          </div>
        </motion.div>

        <motion.div 
          whileHover={{ scale: 1.02 }}
          className="backdrop-blur-sm bg-white/10 border border-white/20 rounded-xl p-4 text-center"
        >
          <CalendarIcon className="w-8 h-8 text-orange-400 mx-auto mb-2" />
          <div className="text-sm text-gray-300 mb-1">Election Cycles</div>
          <div className="text-xl font-bold text-orange-400">
            {financialSummary.electionCycles.length}
          </div>
        </motion.div>
      </div>

      {/* Filters */}
      <div className="backdrop-blur-sm bg-white/10 border border-white/20 rounded-xl p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Record Type</label>
            <select
              value={selectedRecordType}
              onChange={(e) => setSelectedRecordType(e.target.value)}
              className="w-full px-3 py-2 bg-white/10 backdrop-blur-sm border border-white/20 rounded-lg text-white focus:ring-2 focus:ring-blue-400"
            >
              <option value="all" className="bg-gray-800">All Types</option>
              <option value="candidate" className="bg-gray-800">Candidates</option>
              <option value="committee" className="bg-gray-800">Committees</option>
              <option value="contribution" className="bg-gray-800">Contributions</option>
              <option value="disbursement" className="bg-gray-800">Disbursements</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Political Party</label>
            <select
              value={selectedParty}
              onChange={(e) => setSelectedParty(e.target.value)}
              className="w-full px-3 py-2 bg-white/10 backdrop-blur-sm border border-white/20 rounded-lg text-white focus:ring-2 focus:ring-blue-400"
            >
              <option value="all" className="bg-gray-800">All Parties</option>
              <option value="DEM" className="bg-gray-800">Democratic</option>
              <option value="REP" className="bg-gray-800">Republican</option>
              <option value="IND" className="bg-gray-800">Independent</option>
              <option value="GRE" className="bg-gray-800">Green</option>
              <option value="LIB" className="bg-gray-800">Libertarian</option>
            </select>
          </div>
        </div>
      </div>

      {/* Results List */}
      <div className="space-y-4">
        <AnimatePresence>
          {paginatedResults.map((result, index) => (
            <motion.div
              key={result.id || index}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ delay: index * 0.05 }}
              whileHover={{ scale: 1.01, y: -2 }}
              className="backdrop-blur-sm bg-white/10 border border-white/20 rounded-xl p-6 shadow-lg"
            >
              {/* Header */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg flex items-center justify-center">
                    {getRecordTypeIcon(result.record_type)}
                  </div>
                  <div>
                    <h3 className="font-semibold text-white text-lg">{result.title}</h3>
                    <div className="flex items-center gap-2 mt-1">
                      <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getPartyColor(result.party)}`}>
                        {result.party ? `${result.party} Party` : 'Campaign Finance'}
                      </span>
                      <span className="px-3 py-1 bg-blue-500/20 text-blue-300 rounded-full text-xs font-medium border border-blue-400/30">
                        {result.record_type?.replace('_', ' ').toUpperCase() || 'FEC Record'}
                      </span>
                    </div>
                  </div>
                </div>
                
                {result.amount && (
                  <div className="text-right">
                    <div className="text-2xl font-bold text-green-400">
                      {formatCurrency(result.amount)}
                    </div>
                    {result.date && (
                      <div className="text-sm text-gray-300 flex items-center gap-1">
                        <CalendarIcon className="w-4 h-4" />
                        {new Date(result.date).toLocaleDateString()}
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Content */}
              <div className="mb-4">
                <p className="text-gray-300 mb-3">{result.description}</p>
                
                {/* FEC-specific details */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Left column */}
                  <div className="space-y-2">
                    {result.contributor_name && (
                      <div className="flex items-center gap-2 text-sm">
                        <UserIcon className="w-4 h-4 text-gray-400" />
                        <span className="text-gray-300">Contributor:</span>
                        <span className="text-white font-medium">{result.contributor_name}</span>
                      </div>
                    )}
                    
                    {result.contributor_employer && (
                      <div className="flex items-center gap-2 text-sm">
                        <BriefcaseIcon className="w-4 h-4 text-gray-400" />
                        <span className="text-gray-300">Employer:</span>
                        <span className="text-white">{result.contributor_employer}</span>
                      </div>
                    )}
                    
                    {result.office && (
                      <div className="flex items-center gap-2 text-sm">
                        <BuildingOfficeIcon className="w-4 h-4 text-gray-400" />
                        <span className="text-gray-300">Office:</span>
                        <span className="text-white">{result.office} - {result.state}</span>
                      </div>
                    )}
                  </div>
                  
                  {/* Right column */}
                  <div className="space-y-2">
                    {result.committee_name && (
                      <div className="flex items-center gap-2 text-sm">
                        <BuildingOfficeIcon className="w-4 h-4 text-gray-400" />
                        <span className="text-gray-300">Committee:</span>
                        <span className="text-white font-medium">{result.committee_name}</span>
                      </div>
                    )}
                    
                    {(result.contributor_city || result.contributor_state) && (
                      <div className="flex items-center gap-2 text-sm">
                        <MapPinIcon className="w-4 h-4 text-gray-400" />
                        <span className="text-gray-300">Location:</span>
                        <span className="text-white">
                          {result.contributor_city && result.contributor_state 
                            ? `${result.contributor_city}, ${result.contributor_state}`
                            : result.contributor_state || result.contributor_city}
                        </span>
                      </div>
                    )}
                    
                    {result.two_year_transaction_period && (
                      <div className="flex items-center gap-2 text-sm">
                        <CalendarIcon className="w-4 h-4 text-gray-400" />
                        <span className="text-gray-300">Election Cycle:</span>
                        <span className="text-white">{result.two_year_transaction_period}</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div className="flex items-center justify-between pt-4 border-t border-white/20">
                <div className="flex items-center gap-3">
                  {result.url && (
                    <a
                      href={result.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-400 hover:text-blue-300 text-sm flex items-center gap-1 hover:bg-blue-500/20 px-3 py-1 rounded-lg transition-colors"
                    >
                      <ArrowTopRightOnSquareIcon className="w-4 h-4" />
                      View on FEC.gov
                    </a>
                  )}
                  <button 
                    onClick={() => onViewDetails?.(result)}
                    className="text-purple-400 hover:text-purple-300 text-sm hover:bg-purple-500/20 px-3 py-1 rounded-lg transition-colors"
                  >
                    View Details
                  </button>
                </div>
                
                <div className="text-xs text-gray-400">
                  ID: {result.candidate_id || result.committee_id || 'N/A'}
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="backdrop-blur-sm bg-white/10 border border-white/20 rounded-xl p-4">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-300">
              Showing {((currentPage - 1) * itemsPerPage) + 1} to {Math.min(currentPage * itemsPerPage, sortedResults.length)} of {sortedResults.length} results
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                disabled={currentPage === 1}
                className="px-4 py-2 text-sm bg-white/10 border border-white/20 rounded-lg hover:bg-white/20 disabled:opacity-50 disabled:cursor-not-allowed text-white transition-colors"
              >
                Previous
              </button>
              <span className="text-sm text-gray-300 px-3">
                Page {currentPage} of {totalPages}
              </span>
              <button
                onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                disabled={currentPage === totalPages}
                className="px-4 py-2 text-sm bg-white/10 border border-white/20 rounded-lg hover:bg-white/20 disabled:opacity-50 disabled:cursor-not-allowed text-white transition-colors"
              >
                Next
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Summary Statistics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* By Record Type */}
        <div className="backdrop-blur-sm bg-white/10 border border-white/20 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">By Record Type</h3>
          <div className="space-y-3">
            {financialSummary.byRecordType.map(([type, amount]) => (
              <div key={type} className="flex items-center justify-between">
                <span className="text-gray-300 capitalize">{type.replace('_', ' ')}</span>
                <span className="font-semibold text-green-400">{formatCurrency(amount)}</span>
              </div>
            ))}
          </div>
        </div>

        {/* By Political Party */}
        <div className="backdrop-blur-sm bg-white/10 border border-white/20 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">By Political Party</h3>
          <div className="space-y-3">
            {financialSummary.byParty.slice(0, 5).map(([party, amount]) => (
              <div key={party} className="flex items-center justify-between">
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getPartyColor(party)}`}>
                  {party === 'DEM' ? 'Democratic' : 
                   party === 'REP' ? 'Republican' : 
                   party === 'IND' ? 'Independent' : party}
                </span>
                <span className="font-semibold text-green-400">{formatCurrency(amount)}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export default FECStyleResults;
