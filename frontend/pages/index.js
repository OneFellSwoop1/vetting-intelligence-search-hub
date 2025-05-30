import React, { useState, useEffect } from 'react';
import Head from 'next/head';

const Dashboard = () => {
  const [query, setQuery] = useState('');
  const [year, setYear] = useState('');
  const [jurisdiction, setJurisdiction] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [searchStats, setSearchStats] = useState(null);
  const [viewMode, setViewMode] = useState('table'); // 'table', 'chart', 'summary'
  const [selectedRecord, setSelectedRecord] = useState(null); // For modal
  const [showModal, setShowModal] = useState(false);

  const handleSearch = async () => {
    if (!query.trim()) {
      setError('Please enter a search term');
      return;
    }

    setLoading(true);
    setError('');
    setResults([]);
    setSearchStats(null);

    try {
      const response = await fetch('http://localhost:8001/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: query.trim(),
          year: year || null,
          jurisdiction: jurisdiction || null,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setResults(data.results || []);
      setSearchStats(data.search_stats || null);
    } catch (err) {
      setError(`Search failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleViewRecord = (record) => {
    setSelectedRecord(record);
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
    setSelectedRecord(null);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const downloadCSV = () => {
    if (results.length === 0) return;

    const headers = ['Source', 'Jurisdiction', 'Entity Name', 'Role/Title', 'Description', 'Amount/Value', 'Filing Date', 'URL'];
    const csvContent = [
      headers.join(','),
      ...results.map(row => [
        row.source,
        row.jurisdiction,
        `"${row.entity_name || ''}"`,
        `"${row.role_or_title || ''}"`,
        `"${row.description || ''}"`,
        `"${row.amount_or_value || ''}"`,
        row.filing_date || '',
        row.url_to_original_record || ''
      ].join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `search-results-${query}-${Date.now()}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Data analysis functions
  const getYearlyBreakdown = () => {
    const yearMap = {};
    results.forEach(result => {
      if (result.filing_date) {
        const year = result.filing_date.substring(0, 4);
        if (year && year !== '0000') {
          yearMap[year] = (yearMap[year] || 0) + 1;
        }
      }
    });
    return Object.entries(yearMap).sort(([a], [b]) => b.localeCompare(a));
  };

  const getJurisdictionBreakdown = () => {
    const jurisdictionMap = {};
    results.forEach(result => {
      const jurisdiction = result.jurisdiction || 'Unknown';
      jurisdictionMap[jurisdiction] = (jurisdictionMap[jurisdiction] || 0) + 1;
    });
    return Object.entries(jurisdictionMap).sort(([,a], [,b]) => b - a);
  };

  const getSourceBreakdown = () => {
    const sourceMap = {};
    results.forEach(result => {
      const source = result.source || 'Unknown';
      sourceMap[source] = (sourceMap[source] || 0) + 1;
    });
    return Object.entries(sourceMap).sort(([,a], [,b]) => b - a);
  };

  const getAmountAnalysis = () => {
    const amounts = results
      .map(r => r.amount_or_value)
      .filter(amount => amount && amount.includes('$'))
      .map(amount => {
        const cleanAmount = amount.replace(/[$,]/g, '');
        const num = parseFloat(cleanAmount);
        return isNaN(num) ? 0 : num;
      })
      .filter(num => num > 0);

    if (amounts.length === 0) return null;

    const total = amounts.reduce((sum, amount) => sum + amount, 0);
    const average = total / amounts.length;
    const max = Math.max(...amounts);
    const min = Math.min(...amounts);

    return { total, average, max, min, count: amounts.length };
  };

  const yearlyData = getYearlyBreakdown();
  const jurisdictionData = getJurisdictionBreakdown();
  const sourceData = getSourceBreakdown();
  const amountAnalysis = getAmountAnalysis();

  // Modal Component for displaying detailed record information
  const RecordModal = ({ record, onClose }) => {
    if (!record) return null;

    const renderDetailedInfo = () => {
      switch (record.source) {
        case 'senate_lda':
          return (
            <div className="space-y-4">
              <div className="bg-blue-50 p-4 rounded-lg">
                <h4 className="font-semibold text-blue-800 mb-2">🏛️ Federal Lobbying Filing</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                  <div><strong>Registrant:</strong> {record.entity_name}</div>
                  <div><strong>Type:</strong> {record.metadata?.filing_type || record.role_or_title}</div>
                  {record.metadata?.client_name && (
                    <div><strong>Client:</strong> {record.metadata.client_name}</div>
                  )}
                  <div><strong>Amount:</strong> {record.amount_or_value || 'Not specified'}</div>
                  <div><strong>Filing Date:</strong> {record.filing_date}</div>
                  {record.metadata?.reporting_period_start && record.metadata?.reporting_period_end && (
                    <div><strong>Period:</strong> {record.metadata.reporting_period_start} to {record.metadata.reporting_period_end}</div>
                  )}
                </div>
                
                {record.metadata?.client_description && (
                  <div className="mt-3 pt-3 border-t border-blue-200">
                    <strong className="text-blue-800">Client Business:</strong>
                    <p className="text-sm mt-1">{record.metadata.client_description}</p>
                  </div>
                )}
                
                {record.metadata?.lobbying_issues && (
                  <div className="mt-3 pt-3 border-t border-blue-200">
                    <strong className="text-blue-800">Lobbying Issues:</strong>
                    <p className="text-sm mt-1">
                      {Array.isArray(record.metadata.lobbying_issues) 
                        ? record.metadata.lobbying_issues.join(', ')
                        : record.metadata.lobbying_issues}
                    </p>
                  </div>
                )}
                
                {record.metadata?.lobbying_activities && (
                  <div className="mt-3 pt-3 border-t border-blue-200">
                    <strong className="text-blue-800">Lobbying Activities:</strong>
                    <p className="text-sm mt-1">
                      {Array.isArray(record.metadata.lobbying_activities) 
                        ? record.metadata.lobbying_activities.join('; ')
                        : record.metadata.lobbying_activities}
                    </p>
                  </div>
                )}
                
                {record.metadata?.houses_and_agencies && (
                  <div className="mt-3 pt-3 border-t border-blue-200">
                    <strong className="text-blue-800">Lobbied Entities:</strong>
                    <p className="text-sm mt-1">
                      {Array.isArray(record.metadata.houses_and_agencies) 
                        ? record.metadata.houses_and_agencies.join(', ')
                        : record.metadata.houses_and_agencies}
                    </p>
                  </div>
                )}
                
                {(record.metadata?.income_amount || record.metadata?.expense_amount) && (
                  <div className="mt-3 pt-3 border-t border-blue-200">
                    <strong className="text-blue-800">Financial Details:</strong>
                    <div className="text-sm mt-1 grid grid-cols-2 gap-2">
                      {record.metadata.income_amount && <div>Income: {record.metadata.income_amount}</div>}
                      {record.metadata.expense_amount && <div>Expenses: {record.metadata.expense_amount}</div>}
                    </div>
                  </div>
                )}
                
                <div className="mt-3 pt-3 border-t border-blue-200 text-xs text-blue-600">
                  <strong>Description:</strong> {record.description}
                </div>
              </div>
              <div className="bg-gray-50 p-3 rounded text-sm">
                <strong>Data Source:</strong> U.S. Senate Lobbying Disclosure Database
                {record.metadata?.registration_id && (
                  <div className="mt-1 text-xs">Registration ID: {record.metadata.registration_id}</div>
                )}
                {record.metadata?.filing_uuid && (
                  <div className="mt-1 text-xs">Filing ID: {record.metadata.filing_uuid}</div>
                )}
              </div>
            </div>
          );

        case 'dbnyc':
          return (
            <div className="space-y-4">
              <div className="bg-green-50 p-4 rounded-lg">
                <h4 className="font-semibold text-green-800 mb-2">💰 FEC Campaign Finance</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                  <div><strong>Entity:</strong> {record.entity_name}</div>
                  <div><strong>Type:</strong> {record.role_or_title}</div>
                  <div><strong>Amount:</strong> {record.amount_or_value}</div>
                  <div><strong>Date:</strong> {record.filing_date}</div>
                  <div className="md:col-span-2"><strong>Details:</strong> {record.description}</div>
                </div>
              </div>
              <div className="bg-gray-50 p-3 rounded text-sm">
                <strong>Data Source:</strong> Federal Election Commission (FEC)
              </div>
            </div>
          );

        case 'checkbook':
          return (
            <div className="space-y-4">
              <div className="bg-purple-50 p-4 rounded-lg">
                <h4 className="font-semibold text-purple-800 mb-2">🏙️ NYC Government Data</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                  <div><strong>Entity:</strong> {record.entity_name}</div>
                  <div><strong>Type:</strong> {record.role_or_title}</div>
                  <div><strong>Amount:</strong> {record.amount_or_value}</div>
                  <div><strong>Date:</strong> {record.filing_date}</div>
                  <div className="md:col-span-2"><strong>Details:</strong> {record.description}</div>
                </div>
              </div>
              <div className="bg-gray-50 p-3 rounded text-sm">
                <strong>Data Source:</strong> NYC Checkbook / NYC Open Data
              </div>
            </div>
          );

        case 'nys_ethics':
          return (
            <div className="space-y-4">
              <div className="bg-yellow-50 p-4 rounded-lg">
                <h4 className="font-semibold text-yellow-800 mb-2">⚖️ NY State Ethics Filing</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                  <div><strong>Entity:</strong> {record.entity_name}</div>
                  <div><strong>Type:</strong> {record.role_or_title}</div>
                  <div><strong>Amount:</strong> {record.amount_or_value || 'Not specified'}</div>
                  <div><strong>Date:</strong> {record.filing_date}</div>
                  <div className="md:col-span-2"><strong>Details:</strong> {record.description}</div>
                </div>
              </div>
              <div className="bg-gray-50 p-3 rounded text-sm">
                <strong>Data Source:</strong> New York State Ethics Commission
              </div>
            </div>
          );

        case 'house_lda':
          return (
            <div className="space-y-4">
              <div className="bg-red-50 p-4 rounded-lg">
                <h4 className="font-semibold text-red-800 mb-2">🏛️ House Lobbying Filing</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                  <div><strong>Entity:</strong> {record.entity_name}</div>
                  <div><strong>Type:</strong> {record.role_or_title}</div>
                  <div><strong>Amount:</strong> {record.amount_or_value || 'Not specified'}</div>
                  <div><strong>Date:</strong> {record.filing_date}</div>
                  <div className="md:col-span-2"><strong>Details:</strong> {record.description}</div>
                </div>
              </div>
              <div className="bg-gray-50 p-3 rounded text-sm">
                <strong>Data Source:</strong> U.S. House of Representatives Lobbying Disclosure
              </div>
            </div>
          );

        default:
          return (
            <div className="space-y-4">
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-semibold text-gray-800 mb-2">📄 Government Record</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                  <div><strong>Entity:</strong> {record.entity_name}</div>
                  <div><strong>Type:</strong> {record.role_or_title}</div>
                  <div><strong>Amount:</strong> {record.amount_or_value || 'Not specified'}</div>
                  <div><strong>Date:</strong> {record.filing_date}</div>
                  <div className="md:col-span-2"><strong>Details:</strong> {record.description}</div>
                </div>
              </div>
              <div className="bg-gray-50 p-3 rounded text-sm">
                <strong>Data Source:</strong> {record.source}
              </div>
            </div>
          );
      }
    };

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
          <div className="p-6">
            <div className="flex justify-between items-start mb-4">
              <h3 className="text-xl font-bold text-gray-900">Record Details</h3>
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-gray-600 text-2xl font-bold"
              >
                ×
              </button>
            </div>

            {renderDetailedInfo()}

            <div className="mt-6 flex gap-3">
              <button
                onClick={onClose}
                className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
              >
                Close
              </button>
              {record.url_to_original_record && (
                <a
                  href={record.url_to_original_record}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  View Original Source →
                </a>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      <Head>
        <title>Vetting Intelligence Search Hub</title>
        <meta name="description" content="Government data search and analysis platform" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold bg-gradient-to-r from-blue-600 via-purple-600 to-indigo-600 bg-clip-text text-transparent mb-4">
            Vetting Intelligence Search Hub
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Search and analyze government data across multiple jurisdictions and data sources
          </p>
        </div>

        {/* Search Interface */}
        <div className="bg-white rounded-2xl shadow-xl p-8 mb-8 border border-gray-100">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="md:col-span-2">
              <label className="block text-sm font-semibold text-gray-700 mb-2">Search Term</label>
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Enter name, organization, or keyword..."
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Year</label>
              <select
                value={year}
                onChange={(e) => setYear(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
              >
                <option value="">All Years</option>
                <option value="2024">2024</option>
                <option value="2023">2023</option>
                <option value="2022">2022</option>
                <option value="2021">2021</option>
                <option value="2020">2020</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Jurisdiction</label>
              <select
                value={jurisdiction}
                onChange={(e) => setJurisdiction(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
              >
                <option value="">All Jurisdictions</option>
                <option value="NYC">New York City</option>
                <option value="NYS">New York State</option>
                <option value="Federal">Federal</option>
              </select>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row gap-4">
            <button
              onClick={handleSearch}
              disabled={loading}
              className="flex-1 bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-8 py-3 rounded-lg font-semibold hover:from-blue-700 hover:to-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-xl"
            >
              {loading ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Searching...
                </span>
              ) : (
                'Search'
              )}
            </button>
            {results.length > 0 && (
              <button
                onClick={downloadCSV}
                className="px-6 py-3 bg-green-600 text-white rounded-lg font-semibold hover:bg-green-700 transition-colors shadow-lg hover:shadow-xl"
              >
                Download CSV
              </button>
            )}
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <div className="text-red-600 font-medium">
              {error}
            </div>
          </div>
        )}

        {/* Results Section */}
        {results.length > 0 && (
          <div className="space-y-6">
            {/* Stats Summary */}
            {searchStats && (
              <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-100">
                <h3 className="text-xl font-bold text-gray-800 mb-4">Search Statistics</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
                  <div className="bg-blue-50 rounded-lg p-4 text-center">
                    <div className="text-2xl font-bold text-blue-600">{searchStats.total_results}</div>
                    <div className="text-sm text-gray-600">Total Results</div>
                  </div>
                  {Object.entries(searchStats.per_source || {}).map(([source, count]) => (
                    <div key={source} className="bg-purple-50 rounded-lg p-4 text-center">
                      <div className="text-2xl font-bold text-purple-600">{count}</div>
                      <div className="text-sm text-gray-600 capitalize">{source}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* View Mode Toggle */}
            <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-100">
              <div className="flex flex-wrap gap-2 mb-4">
                <button
                  onClick={() => setViewMode('table')}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    viewMode === 'table' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  📊 Data Table
                </button>
                <button
                  onClick={() => setViewMode('chart')}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    viewMode === 'chart' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  📈 Analytics
                </button>
                <button
                  onClick={() => setViewMode('summary')}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    viewMode === 'summary' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  📋 Summary
                </button>
              </div>

              {/* Table View */}
              {viewMode === 'table' && (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-gray-200">
                        <th className="text-left py-3 px-4 font-semibold text-gray-700">Source</th>
                        <th className="text-left py-3 px-4 font-semibold text-gray-700">Jurisdiction</th>
                        <th className="text-left py-3 px-4 font-semibold text-gray-700">Entity</th>
                        <th className="text-left py-3 px-4 font-semibold text-gray-700">Role/Title</th>
                        <th className="text-left py-3 px-4 font-semibold text-gray-700">Description</th>
                        <th className="text-left py-3 px-4 font-semibold text-gray-700">Amount</th>
                        <th className="text-left py-3 px-4 font-semibold text-gray-700">Date</th>
                        <th className="text-left py-3 px-4 font-semibold text-gray-700">Record</th>
                      </tr>
                    </thead>
                    <tbody>
                      {results.map((result, index) => (
                        <tr key={index} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                          <td className="py-3 px-4">
                            <span className="inline-block bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs font-medium capitalize">
                              {result.source}
                            </span>
                          </td>
                          <td className="py-3 px-4">
                            <span className="inline-block bg-purple-100 text-purple-800 px-2 py-1 rounded text-xs font-medium">
                              {result.jurisdiction}
                            </span>
                          </td>
                          <td className="py-3 px-4 font-medium text-gray-900">{result.entity_name}</td>
                          <td className="py-3 px-4 text-gray-600">{result.role_or_title}</td>
                          <td className="py-3 px-4 text-gray-600 max-w-xs truncate" title={result.description}>
                            {result.description}
                          </td>
                          <td className="py-3 px-4 font-semibold text-green-600">{result.amount_or_value}</td>
                          <td className="py-3 px-4 text-gray-600">{result.filing_date}</td>
                          <td className="py-3 px-4">
                            <button
                              onClick={() => handleViewRecord(result)}
                              className="text-blue-600 hover:text-blue-800 text-sm font-medium hover:underline"
                            >
                              View Record
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* Analytics View */}
              {viewMode === 'chart' && (
                <div className="space-y-8">
                  {/* Amount Analysis */}
                  {amountAnalysis && (
                    <div className="bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg p-6 border border-green-200">
                      <h4 className="text-lg font-bold text-gray-800 mb-4">💰 Financial Analysis</h4>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="text-center">
                          <div className="text-2xl font-bold text-green-600">${amountAnalysis.total.toLocaleString()}</div>
                          <div className="text-sm text-gray-600">Total Amount</div>
                        </div>
                        <div className="text-center">
                          <div className="text-2xl font-bold text-green-600">${amountAnalysis.average.toLocaleString()}</div>
                          <div className="text-sm text-gray-600">Average</div>
                        </div>
                        <div className="text-center">
                          <div className="text-2xl font-bold text-green-600">${amountAnalysis.max.toLocaleString()}</div>
                          <div className="text-sm text-gray-600">Highest</div>
                        </div>
                        <div className="text-center">
                          <div className="text-2xl font-bold text-green-600">{amountAnalysis.count}</div>
                          <div className="text-sm text-gray-600">Records with Amount</div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Year Breakdown */}
                  <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-6 border border-blue-200">
                    <h4 className="text-lg font-bold text-gray-800 mb-4">📅 Year-over-Year Breakdown</h4>
                    <div className="space-y-3">
                      {yearlyData.map(([year, count]) => (
                        <div key={year} className="flex items-center">
                          <div className="w-16 text-sm font-medium text-gray-700">{year}</div>
                          <div className="flex-1 bg-gray-200 rounded-full h-6 mx-4">
                            <div
                              className="bg-gradient-to-r from-blue-500 to-indigo-500 h-6 rounded-full flex items-center justify-end pr-2"
                              style={{ width: `${(count / Math.max(...yearlyData.map(([,c]) => c))) * 100}%` }}
                            >
                              <span className="text-white text-xs font-medium">{count}</span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Jurisdiction Breakdown */}
                  <div className="bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg p-6 border border-purple-200">
                    <h4 className="text-lg font-bold text-gray-800 mb-4">🏛️ Jurisdiction Distribution</h4>
                    <div className="space-y-3">
                      {jurisdictionData.map(([jurisdiction, count]) => (
                        <div key={jurisdiction} className="flex items-center">
                          <div className="w-20 text-sm font-medium text-gray-700">{jurisdiction}</div>
                          <div className="flex-1 bg-gray-200 rounded-full h-6 mx-4">
                            <div
                              className="bg-gradient-to-r from-purple-500 to-pink-500 h-6 rounded-full flex items-center justify-end pr-2"
                              style={{ width: `${(count / Math.max(...jurisdictionData.map(([,c]) => c))) * 100}%` }}
                            >
                              <span className="text-white text-xs font-medium">{count}</span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Source Breakdown */}
                  <div className="bg-gradient-to-r from-orange-50 to-red-50 rounded-lg p-6 border border-orange-200">
                    <h4 className="text-lg font-bold text-gray-800 mb-4">🗃️ Data Source Distribution</h4>
                    <div className="space-y-3">
                      {sourceData.map(([source, count]) => (
                        <div key={source} className="flex items-center">
                          <div className="w-24 text-sm font-medium text-gray-700 capitalize">{source}</div>
                          <div className="flex-1 bg-gray-200 rounded-full h-6 mx-4">
                            <div
                              className="bg-gradient-to-r from-orange-500 to-red-500 h-6 rounded-full flex items-center justify-end pr-2"
                              style={{ width: `${(count / Math.max(...sourceData.map(([,c]) => c))) * 100}%` }}
                            >
                              <span className="text-white text-xs font-medium">{count}</span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Summary View */}
              {viewMode === 'summary' && (
                <div className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {results.map((result, index) => (
                      <div key={index} className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg p-6 border border-gray-200 hover:shadow-lg transition-shadow">
                        <div className="flex justify-between items-start mb-3">
                          <span className="inline-block bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide">
                            {result.source}
                          </span>
                          <span className="inline-block bg-purple-100 text-purple-800 px-3 py-1 rounded-full text-xs font-bold">
                            {result.jurisdiction}
                          </span>
                        </div>
                        <h4 className="font-bold text-lg text-gray-900 mb-2">{result.entity_name}</h4>
                        <p className="text-sm text-gray-600 mb-2">{result.role_or_title}</p>
                        <p className="text-sm text-gray-700 mb-4 line-clamp-3">{result.description}</p>
                        <div className="flex justify-between items-center">
                          <span className="font-bold text-green-600">{result.amount_or_value}</span>
                          <span className="text-sm text-gray-500">{result.filing_date}</span>
                        </div>
                        <div className="mt-4">
                          <button
                            onClick={() => handleViewRecord(result)}
                            className="inline-flex items-center text-blue-600 hover:text-blue-800 text-sm font-medium hover:underline"
                          >
                            View Details 
                            <svg className="ml-1 w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                            </svg>
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* No Results */}
        {!loading && results.length === 0 && query && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-8 text-center">
            <div className="text-yellow-600 text-lg font-medium mb-2">
              No results found for "{query}"
            </div>
            <div className="text-yellow-600 text-sm">
              Try adjusting your search terms or removing filters
            </div>
          </div>
        )}

        {/* Footer */}
        <footer className="mt-12 text-center text-gray-500 text-sm">
          <p>Vetting Intelligence Search Hub - Government Data Analysis Platform</p>
          <p className="mt-2">Search across NYC, NYS, and Federal data sources</p>
        </footer>
      </div>

      {/* Record Modal */}
      {showModal && (
        <RecordModal record={selectedRecord} onClose={closeModal} />
      )}
    </div>
  );
};

export default Dashboard; 