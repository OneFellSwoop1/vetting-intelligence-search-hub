'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { Filter, X, Calendar, DollarSign, Building, FileText, RotateCcw, Save, Clock, ChevronDown, ChevronUp } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

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

interface SearchFilters {
  year?: string;
  jurisdiction?: string;
  source?: string;
  minAmount?: string;
  maxAmount?: string;
  recordType?: string;
  dateRange?: { start: string; end: string };
  agency?: string;
}

interface FilterPreset {
  id: string;
  name: string;
  filters: SearchFilters;
  createdAt: string;
}

interface FilterSidebarProps {
  results: SearchResult[];
  totalHits: Record<string, number>;
  filters: SearchFilters;
  onFiltersChange: (filters: SearchFilters) => void;
  isVisible: boolean;
  onToggle: () => void;
}

const sourceConfig = {
  senate_lda: { name: 'Senate LDA (House & Senate Lobbying)', color: 'bg-red-100 text-red-800', icon: '🏛️' },
  checkbook: { name: 'NYC Contracts', color: 'bg-green-100 text-green-800', icon: '📋' },
  nys_ethics: { name: 'NY State', color: 'bg-yellow-100 text-yellow-800', icon: '🏛️' },
  nyc_lobbyist: { name: 'NYC Lobbyist', color: 'bg-orange-100 text-orange-800', icon: '🤝' }
};

const jurisdictionOptions = [
  { value: 'federal', label: 'Federal' },
  { value: 'state', label: 'State (NY)' },
  { value: 'local', label: 'Local (NYC)' }
];

const recordTypeOptions = [
  { value: 'contracts', label: 'Contracts' },
  { value: 'lobbying', label: 'Lobbying' },
  { value: 'payroll', label: 'Payroll' },
  { value: 'contributions', label: 'Contributions' },
  { value: 'spending', label: 'Federal Spending' }
];

const amountRanges = [
  { label: 'Any Amount', min: '', max: '' },
  { label: '$1K - $10K', min: '1000', max: '10000' },
  { label: '$10K - $100K', min: '10000', max: '100000' },
  { label: '$100K - $1M', min: '100000', max: '1000000' },
  { label: '$1M+', min: '1000000', max: '' }
];

const datePresets = [
  { label: 'All Time', value: '' },
  { label: 'Last 30 days', value: '30' },
  { label: 'Last 3 months', value: '90' },
  { label: 'Last 6 months', value: '180' },
  { label: 'Last year', value: '365' },
  { label: 'Last 2 years', value: '730' }
];

export default function FilterSidebar({ 
  results, 
  totalHits, 
  filters, 
  onFiltersChange, 
  isVisible, 
  onToggle 
}: FilterSidebarProps) {
  const [localFilters, setLocalFilters] = useState<SearchFilters>(filters);
  const [filterPresets, setFilterPresets] = useState<FilterPreset[]>([]);
  const [showPresets, setShowPresets] = useState(false);
  const [presetName, setPresetName] = useState('');
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(['sources', 'dateRange', 'amount'])
  );
  const [filteredResultCounts, setFilteredResultCounts] = useState<Record<string, number>>({});

  // Load filter presets from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('vetting-filter-presets');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        setFilterPresets(parsed);
      } catch (e) {
        console.warn('Failed to load filter presets:', e);
      }
    }
  }, []);

  // Calculate filtered result counts in real-time
  const calculateFilteredCounts = useCallback(() => {
    const counts: Record<string, number> = {};
    
    // Count results for each source with current filters applied
    Object.keys(sourceConfig).forEach(source => {
      counts[source] = results.filter(result => {
        if (result.source !== source) return false;
        
        // Apply all other filters except source
        if (localFilters.recordType && result.record_type !== localFilters.recordType) return false;
        if (localFilters.minAmount && result.amount) {
          const amount = typeof result.amount === 'number' 
            ? result.amount 
            : parseFloat(result.amount.toString().replace(/[$,]/g, ''));
          if (amount < parseFloat(localFilters.minAmount)) return false;
        }
        if (localFilters.maxAmount && result.amount) {
          const amount = typeof result.amount === 'number' 
            ? result.amount 
            : parseFloat(result.amount.toString().replace(/[$,]/g, ''));
          if (amount > parseFloat(localFilters.maxAmount)) return false;
        }
        if (localFilters.year && result.date) {
          const resultYear = new Date(result.date).getFullYear().toString();
          if (resultYear !== localFilters.year) return false;
        }
        if (localFilters.agency && result.agency) {
          if (!result.agency.toLowerCase().includes(localFilters.agency.toLowerCase())) return false;
        }
        
        return true;
      }).length;
    });
    
    setFilteredResultCounts(counts);
  }, [results, localFilters]);

  useEffect(() => {
    calculateFilteredCounts();
  }, [calculateFilteredCounts]);

  // Update local filters when parent filters change
  useEffect(() => {
    setLocalFilters(filters);
  }, [filters]);

  // Apply filters with debouncing
  const applyFilters = useCallback(() => {
    onFiltersChange(localFilters);
  }, [localFilters, onFiltersChange]);

  useEffect(() => {
    const timeoutId = setTimeout(applyFilters, 300);
    return () => clearTimeout(timeoutId);
  }, [localFilters, applyFilters]);

  const handleFilterChange = (key: keyof SearchFilters, value: string) => {
    setLocalFilters(prev => ({
      ...prev,
      [key]: value || undefined
    }));
  };

  const handleAmountRangeChange = (min: string, max: string) => {
    setLocalFilters(prev => ({
      ...prev,
      minAmount: min || undefined,
      maxAmount: max || undefined
    }));
  };

  const clearAllFilters = () => {
    const emptyFilters: SearchFilters = {};
    setLocalFilters(emptyFilters);
    onFiltersChange(emptyFilters);
  };

  const saveFilterPreset = () => {
    if (!presetName.trim()) return;
    
    const newPreset: FilterPreset = {
      id: Date.now().toString(),
      name: presetName.trim(),
      filters: { ...localFilters },
      createdAt: new Date().toISOString()
    };
    
    const newPresets = [...filterPresets, newPreset];
    setFilterPresets(newPresets);
    localStorage.setItem('vetting-filter-presets', JSON.stringify(newPresets));
    setPresetName('');
    setShowPresets(false);
  };

  const loadFilterPreset = (preset: FilterPreset) => {
    setLocalFilters(preset.filters);
    onFiltersChange(preset.filters);
    setShowPresets(false);
  };

  const deleteFilterPreset = (presetId: string) => {
    const newPresets = filterPresets.filter(p => p.id !== presetId);
    setFilterPresets(newPresets);
    localStorage.setItem('vetting-filter-presets', JSON.stringify(newPresets));
  };

  const toggleSection = (section: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(section)) {
      newExpanded.delete(section);
    } else {
      newExpanded.add(section);
    }
    setExpandedSections(newExpanded);
  };

  const getActiveFilterCount = () => {
    return Object.values(localFilters).filter(value => value !== undefined && value !== '').length;
  };

  const getTotalFilteredResults = () => {
    return Object.values(filteredResultCounts).reduce((sum, count) => sum + count, 0);
  };

  if (!isVisible) {
    return (
      <button
        onClick={onToggle}
        className="fixed left-4 top-1/2 transform -translate-y-1/2 bg-blue-600 text-white p-3 rounded-lg shadow-lg hover:bg-blue-700 transition-colors z-50"
      >
        <Filter className="w-5 h-5" />
        {getActiveFilterCount() > 0 && (
          <span className="absolute -top-2 -right-2 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
            {getActiveFilterCount()}
          </span>
        )}
      </button>
    );
  }

  return (
    <motion.div
      initial={{ x: -300 }}
      animate={{ x: 0 }}
      exit={{ x: -300 }}
      className="fixed left-0 top-0 bottom-0 w-80 bg-white border-r border-gray-200 shadow-lg z-40 overflow-y-auto"
    >
      {/* Header */}
      <div className="p-4 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center justify-between mb-2">
          <h3 className="font-semibold text-gray-900 flex items-center gap-2">
            <Filter className="w-5 h-5" />
            Filters
          </h3>
          <button
            onClick={onToggle}
            className="text-gray-500 hover:text-gray-700"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        
        <div className="flex items-center justify-between text-sm text-gray-600">
          <span>{getTotalFilteredResults()} results</span>
          {getActiveFilterCount() > 0 && (
            <button
              onClick={clearAllFilters}
              className="text-blue-600 hover:text-blue-700 flex items-center gap-1"
            >
              <RotateCcw className="w-3 h-3" />
              Clear all
            </button>
          )}
        </div>
      </div>

      {/* Filter Presets */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700">Filter Presets</span>
          <button
            onClick={() => setShowPresets(!showPresets)}
            className="text-blue-600 hover:text-blue-700"
          >
            <Save className="w-4 h-4" />
          </button>
        </div>
        
        <AnimatePresence>
          {showPresets && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="space-y-2"
            >
              <div className="flex gap-2">
                <input
                  type="text"
                  value={presetName}
                  onChange={(e) => setPresetName(e.target.value)}
                  placeholder="Preset name"
                  className="flex-1 px-2 py-1 text-sm border border-gray-300 rounded"
                />
                <button
                  onClick={saveFilterPreset}
                  disabled={!presetName.trim()}
                  className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400"
                >
                  Save
                </button>
              </div>
              
              {filterPresets.map(preset => (
                <div key={preset.id} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                  <button
                    onClick={() => loadFilterPreset(preset)}
                    className="flex-1 text-left text-sm text-gray-700 hover:text-gray-900"
                  >
                    {preset.name}
                  </button>
                  <button
                    onClick={() => deleteFilterPreset(preset.id)}
                    className="text-red-500 hover:text-red-700"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </div>
              ))}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Data Sources */}
      <div className="border-b border-gray-200">
        <button
          onClick={() => toggleSection('sources')}
          className="w-full p-4 flex items-center justify-between text-left hover:bg-gray-50"
        >
          <span className="font-medium text-gray-700">Data Sources</span>
          {expandedSections.has('sources') ? (
            <ChevronUp className="w-4 h-4 text-gray-500" />
          ) : (
            <ChevronDown className="w-4 h-4 text-gray-500" />
          )}
        </button>
        
        <AnimatePresence>
          {expandedSections.has('sources') && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="px-4 pb-4 space-y-2"
            >
              {Object.entries(sourceConfig).map(([key, config]) => (
                <label key={key} className="flex items-center justify-between cursor-pointer">
                  <div className="flex items-center">
                    <input
                      type="radio"
                      name="source"
                      value={key}
                      checked={localFilters.source === key}
                      onChange={(e) => handleFilterChange('source', e.target.checked ? key : '')}
                      className="mr-2"
                    />
                    <span className="text-sm text-gray-700">{config.name}</span>
                  </div>
                  <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                    {filteredResultCounts[key] || totalHits[key] || 0}
                  </span>
                </label>
              ))}
              <label className="flex items-center">
                <input
                  type="radio"
                  name="source"
                  value=""
                  checked={!localFilters.source}
                  onChange={() => handleFilterChange('source', '')}
                  className="mr-2"
                />
                <span className="text-sm text-gray-700">All Sources</span>
              </label>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Date Range */}
      <div className="border-b border-gray-200">
        <button
          onClick={() => toggleSection('dateRange')}
          className="w-full p-4 flex items-center justify-between text-left hover:bg-gray-50"
        >
          <span className="font-medium text-gray-700 flex items-center gap-2">
            <Calendar className="w-4 h-4" />
            Date Range
          </span>
          {expandedSections.has('dateRange') ? (
            <ChevronUp className="w-4 h-4 text-gray-500" />
          ) : (
            <ChevronDown className="w-4 h-4 text-gray-500" />
          )}
        </button>
        
        <AnimatePresence>
          {expandedSections.has('dateRange') && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="px-4 pb-4 space-y-2"
            >
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Year</label>
                <select
                  value={localFilters.year || ''}
                  onChange={(e) => handleFilterChange('year', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                >
                  <option value="">All Years</option>
                  {Array.from({ length: 10 }, (_, i) => new Date().getFullYear() - i).map(year => (
                    <option key={year} value={year.toString()}>{year}</option>
                  ))}
                </select>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Amount Range */}
      <div className="border-b border-gray-200">
        <button
          onClick={() => toggleSection('amount')}
          className="w-full p-4 flex items-center justify-between text-left hover:bg-gray-50"
        >
          <span className="font-medium text-gray-700 flex items-center gap-2">
            <DollarSign className="w-4 h-4" />
            Amount Range
          </span>
          {expandedSections.has('amount') ? (
            <ChevronUp className="w-4 h-4 text-gray-500" />
          ) : (
            <ChevronDown className="w-4 h-4 text-gray-500" />
          )}
        </button>
        
        <AnimatePresence>
          {expandedSections.has('amount') && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="px-4 pb-4 space-y-2"
            >
              {amountRanges.map((range, index) => (
                <label key={index} className="flex items-center cursor-pointer">
                  <input
                    type="radio"
                    name="amountRange"
                    checked={localFilters.minAmount === range.min && localFilters.maxAmount === range.max}
                    onChange={() => handleAmountRangeChange(range.min, range.max)}
                    className="mr-2"
                  />
                  <span className="text-sm text-gray-700">{range.label}</span>
                </label>
              ))}
              
              <div className="pt-2 border-t border-gray-200">
                <label className="block text-sm font-medium text-gray-700 mb-1">Custom Range</label>
                <div className="flex gap-2">
                  <input
                    type="number"
                    placeholder="Min"
                    value={localFilters.minAmount || ''}
                    onChange={(e) => handleFilterChange('minAmount', e.target.value)}
                    className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm"
                  />
                  <input
                    type="number"
                    placeholder="Max"
                    value={localFilters.maxAmount || ''}
                    onChange={(e) => handleFilterChange('maxAmount', e.target.value)}
                    className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm"
                  />
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Record Type */}
      <div className="border-b border-gray-200">
        <button
          onClick={() => toggleSection('recordType')}
          className="w-full p-4 flex items-center justify-between text-left hover:bg-gray-50"
        >
          <span className="font-medium text-gray-700 flex items-center gap-2">
            <FileText className="w-4 h-4" />
            Record Type
          </span>
          {expandedSections.has('recordType') ? (
            <ChevronUp className="w-4 h-4 text-gray-500" />
          ) : (
            <ChevronDown className="w-4 h-4 text-gray-500" />
          )}
        </button>
        
        <AnimatePresence>
          {expandedSections.has('recordType') && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="px-4 pb-4 space-y-2"
            >
              {recordTypeOptions.map(option => (
                <label key={option.value} className="flex items-center cursor-pointer">
                  <input
                    type="radio"
                    name="recordType"
                    value={option.value}
                    checked={localFilters.recordType === option.value}
                    onChange={(e) => handleFilterChange('recordType', e.target.checked ? option.value : '')}
                    className="mr-2"
                  />
                  <span className="text-sm text-gray-700">{option.label}</span>
                </label>
              ))}
              <label className="flex items-center">
                <input
                  type="radio"
                  name="recordType"
                  value=""
                  checked={!localFilters.recordType}
                  onChange={() => handleFilterChange('recordType', '')}
                  className="mr-2"
                />
                <span className="text-sm text-gray-700">All Types</span>
              </label>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Agency Filter */}
      <div className="p-4">
        <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
          <Building className="w-4 h-4" />
          Agency
        </label>
        <input
          type="text"
          value={localFilters.agency || ''}
          onChange={(e) => handleFilterChange('agency', e.target.value)}
          placeholder="Filter by agency name..."
          className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
        />
      </div>
    </motion.div>
  );
} 