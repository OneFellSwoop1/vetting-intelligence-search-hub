import React, { useState, useMemo } from 'react';
import { 
  X, 
  ExternalLink, 
  Calendar, 
  DollarSign, 
  Building, 
  User, 
  TrendingUp, 
  Target, 
  MapPin,
  Clock,
  Copy,
  ArrowRight,
  BarChart3,
  PieChart,
  Activity,
  Users,
  FileText,
  Shield,
  AlertCircle,
  CheckCircle,
  Info
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface SearchResult {
  id?: string;
  title: string;
  description: string;
  amount?: string | number;
  date?: string;
  source: string;
  vendor?: string;
  agency?: string;
  url?: string;
  record_type?: string;
  client?: string;
  lobbyist?: string;
  subjects?: string;
  period?: string;
  relationship_type?: string;
  year?: string;
  contract_id?: string;
  raw_data?: any;
  [key: string]: any;
}

interface DetailedResultViewProps {
  result: SearchResult;
  onClose: () => void;
  className?: string;
  relatedResults?: SearchResult[];
}

// Enhanced source configuration with more details
const sourceConfig = {
  senate_lda: {
    name: 'Federal Lobbying (Senate)',
    color: 'bg-blue-50 border-blue-200 text-blue-800',
    icon: '🏛️',
    badgeColor: 'bg-blue-100 text-blue-700',
    baseUrl: 'https://lda.senate.gov',
    description: 'Senate Lobbying Disclosure Act filings'
  },
  house_lda: {
    name: 'Federal Lobbying (House)',
    color: 'bg-purple-50 border-purple-200 text-purple-800',
    icon: '🏛️',
    badgeColor: 'bg-purple-100 text-purple-700',
    baseUrl: 'https://disclosurespreview.house.gov',
    description: 'House Lobbying Disclosure Act filings'
  },
  checkbook: {
    name: 'NYC Contracts & Spending',
    color: 'bg-green-50 border-green-200 text-green-800',
    icon: '🏙️',
    badgeColor: 'bg-green-100 text-green-700',
    baseUrl: 'https://checkbook.nyc.gov',
    description: 'New York City financial transactions'
  },
  nyc_lobbyist: {
    name: 'NYC Lobbying',
    color: 'bg-cyan-50 border-cyan-200 text-cyan-800',
    icon: '🗽',
    badgeColor: 'bg-cyan-100 text-cyan-700',
    baseUrl: 'https://www.nyc.gov/site/coib/lobbying',
    description: 'NYC lobbying registrations and activities'
  },
  nys_ethics: {
    name: 'NY State Ethics',
    color: 'bg-orange-50 border-orange-200 text-orange-800',
    icon: '⚖️',
    badgeColor: 'bg-orange-100 text-orange-700',
    baseUrl: 'https://www.ethics.ny.gov',
    description: 'New York State lobbying and ethics'
  },
  dbnyc: {
    name: 'Federal Contracts',
    color: 'bg-red-50 border-red-200 text-red-800',
    icon: '📊',
    badgeColor: 'bg-red-100 text-red-700',
    baseUrl: 'https://www.usaspending.gov',
    description: 'Federal government spending data'
  }
};

const DetailedResultView: React.FC<DetailedResultViewProps> = ({ 
  result, 
  onClose, 
  className,
  relatedResults = []
}) => {
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    overview: true,
    financial: true,
    activities: true,
    timeline: true,
    relationships: true,
    technical: false
  });

  const sourceInfo = sourceConfig[result.source as keyof typeof sourceConfig] || {
    name: result.source,
    color: 'bg-gray-50 border-gray-200 text-gray-800',
    icon: '📄',
    badgeColor: 'bg-gray-100 text-gray-700',
    baseUrl: '',
    description: 'Government data source'
  };

  // Enhanced data analysis
  const analysisData = useMemo(() => {
    const amount = typeof result.amount === 'number' ? result.amount : 
                   typeof result.amount === 'string' ? parseFloat(result.amount.replace(/[$,]/g, '')) || 0 : 0;
    
    // Financial analysis
    const financialMetrics = {
      totalAmount: amount,
      amountCategory: amount >= 1000000 ? 'High Value' : amount >= 100000 ? 'Medium Value' : 'Standard',
      riskLevel: amount >= 1000000 ? 'high' : amount >= 100000 ? 'medium' : 'low',
      formattedAmount: amount.toLocaleString('en-US', { style: 'currency', currency: 'USD' })
    };

    // Activity analysis
    const activityType = result.source.includes('lobbyist') || result.source.includes('lda') ? 'lobbying' : 'financial';
    const recordAge = result.date ? new Date().getFullYear() - new Date(result.date).getFullYear() : 0;
    
    // Relationship analysis
    const keyEntities = {
      primaryEntity: result.vendor || result.client || 'Unknown',
      secondaryEntity: result.agency || result.lobbyist || 'Unknown',
      relationship: result.relationship_type || 'Business Relationship'
    };

    return {
      financial: financialMetrics,
      activity: { type: activityType, age: recordAge },
      entities: keyEntities,
      compliance: {
        hasUrl: !!result.url,
        hasDocumentation: !!(result.contract_id || result.raw_data),
        isRecent: recordAge <= 2
      }
    };
  }, [result]);

  const toggleSection = (section: string) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const formatAmount = (amount: string | number | undefined) => {
    if (!amount) return 'N/A';
    if (typeof amount === 'number') {
      return amount.toLocaleString('en-US', { style: 'currency', currency: 'USD' });
    }
    return amount;
  };

  const formatDate = (date: string | undefined) => {
    if (!date) return 'N/A';
    try {
      return new Date(date).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      });
    } catch {
      return date;
    }
  };

  const generateDirectLink = () => {
    if (result.url) return result.url;
    return sourceInfo.baseUrl;
  };

  const SectionHeader = ({ title, icon: Icon, expanded, onToggle, badge }: any) => (
    <div 
      className="flex items-center justify-between p-4 bg-gray-50 border-b cursor-pointer hover:bg-gray-100 transition-colors"
      onClick={onToggle}
    >
      <div className="flex items-center gap-3">
        <Icon className="w-5 h-5 text-gray-600" />
        <h3 className="font-semibold text-gray-900">{title}</h3>
        {badge && (
          <span className={`px-2 py-1 text-xs font-medium rounded-full ${badge.className}`}>
            {badge.text}
          </span>
        )}
      </div>
      <div className={`transform transition-transform ${expanded ? 'rotate-90' : ''}`}>
        <ArrowRight className="w-4 h-4 text-gray-400" />
      </div>
    </div>
  );

  return (
    <div className={cn("fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50", className)}>
      <div className="bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-start justify-between p-6 border-b bg-white">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-3 mb-2">
              <span className="text-2xl">{sourceInfo.icon}</span>
              <div>
                <h2 className="text-xl font-bold text-gray-900 leading-tight">
                  {result.title}
                </h2>
                <div className="flex items-center gap-2 mt-1">
                  <span className={cn("inline-flex items-center px-3 py-1 rounded-full text-sm font-medium", sourceInfo.badgeColor)}>
                    {sourceInfo.name}
                  </span>
                  {analysisData.financial.riskLevel === 'high' && (
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-700">
                      <AlertCircle className="w-3 h-3 mr-1" />
                      High Value
                    </span>
                  )}
                  {analysisData.compliance.isRecent && (
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700">
                      <CheckCircle className="w-3 h-3 mr-1" />
                      Recent
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="overflow-y-auto max-h-[calc(90vh-120px)]">
          
          {/* Overview Section */}
          <div className="border-b">
            <SectionHeader
              title="Overview"
              icon={Info}
              expanded={expandedSections.overview}
              onToggle={() => toggleSection('overview')}
            />
            {expandedSections.overview && (
              <div className="p-6 space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-blue-50 p-4 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <User className="w-4 h-4 text-blue-600" />
                      <span className="text-sm font-medium text-blue-900">Primary Entity</span>
                    </div>
                    <p className="font-semibold text-blue-900">{analysisData.entities.primaryEntity}</p>
                  </div>
                  <div className="bg-green-50 p-4 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <Building className="w-4 h-4 text-green-600" />
                      <span className="text-sm font-medium text-green-900">Agency/Target</span>
                    </div>
                    <p className="font-semibold text-green-900">{analysisData.entities.secondaryEntity}</p>
                  </div>
                  <div className="bg-purple-50 p-4 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <Shield className="w-4 h-4 text-purple-600" />
                      <span className="text-sm font-medium text-purple-900">Relationship</span>
                    </div>
                    <p className="font-semibold text-purple-900">{analysisData.entities.relationship}</p>
                  </div>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-gray-700 leading-relaxed">{result.description}</p>
                </div>
              </div>
            )}
          </div>

          {/* Financial Analysis Section */}
          <div className="border-b">
            <SectionHeader
              title="Financial Analysis"
              icon={DollarSign}
              expanded={expandedSections.financial}
              onToggle={() => toggleSection('financial')}
              badge={{
                text: analysisData.financial.amountCategory,
                className: analysisData.financial.riskLevel === 'high' ? 'bg-red-100 text-red-700' :
                          analysisData.financial.riskLevel === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                          'bg-green-100 text-green-700'
              }}
            />
            {expandedSections.financial && (
              <div className="p-6 space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-3">Transaction Details</h4>
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Amount:</span>
                        <span className="font-semibold text-green-600 text-lg">{analysisData.financial.formattedAmount}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Date:</span>
                        <span className="font-medium">{formatDate(result.date)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Fiscal Year:</span>
                        <span className="font-medium">{result.year || 'N/A'}</span>
                      </div>
                      {result.contract_id && (
                        <div className="flex justify-between">
                          <span className="text-gray-600">Contract ID:</span>
                          <span className="font-mono text-sm bg-gray-100 px-2 py-1 rounded">
                            {result.contract_id}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-3">Risk Assessment</h4>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-gray-600">Value Category:</span>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          analysisData.financial.riskLevel === 'high' ? 'bg-red-100 text-red-700' :
                          analysisData.financial.riskLevel === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                          'bg-green-100 text-green-700'
                        }`}>
                          {analysisData.financial.amountCategory}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-gray-600">Documentation:</span>
                        <span className={`flex items-center gap-1 ${analysisData.compliance.hasDocumentation ? 'text-green-600' : 'text-yellow-600'}`}>
                          {analysisData.compliance.hasDocumentation ? <CheckCircle className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
                          {analysisData.compliance.hasDocumentation ? 'Complete' : 'Limited'}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-gray-600">Data Freshness:</span>
                        <span className={`flex items-center gap-1 ${analysisData.compliance.isRecent ? 'text-green-600' : 'text-gray-600'}`}>
                          <Clock className="w-4 h-4" />
                          {analysisData.compliance.isRecent ? 'Recent' : `${analysisData.activity.age} years old`}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Activities & Lobbying Section */}
          {analysisData.activity.type === 'lobbying' && (
            <div className="border-b">
              <SectionHeader
                title="Lobbying Activities"
                icon={Target}
                expanded={expandedSections.activities}
                onToggle={() => toggleSection('activities')}
              />
              {expandedSections.activities && (
                <div className="p-6 space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h4 className="font-semibold text-gray-900 mb-3">Lobbying Details</h4>
                      <div className="space-y-3">
                        {result.subjects && (
                          <div>
                            <span className="text-gray-600 block mb-1">Subjects:</span>
                            <span className="font-medium">{result.subjects}</span>
                          </div>
                        )}
                        {result.period && (
                          <div>
                            <span className="text-gray-600 block mb-1">Reporting Period:</span>
                            <span className="font-medium">{result.period}</span>
                          </div>
                        )}
                        {result.lobbyist && (
                          <div>
                            <span className="text-gray-600 block mb-1">Lobbyist:</span>
                            <span className="font-medium">{result.lobbyist}</span>
                          </div>
                        )}
                      </div>
                    </div>
                    <div>
                      <h4 className="font-semibold text-gray-900 mb-3">Activity Summary</h4>
                      <div className="bg-blue-50 p-4 rounded-lg">
                        <div className="flex items-center gap-2 mb-2">
                          <Activity className="w-4 h-4 text-blue-600" />
                          <span className="font-medium text-blue-900">Activity Type</span>
                        </div>
                        <p className="text-blue-800 capitalize">{result.record_type?.replace('_', ' ') || 'Lobbying Activity'}</p>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Timeline Section */}
          <div className="border-b">
            <SectionHeader
              title="Timeline & Context"
              icon={Calendar}
              expanded={expandedSections.timeline}
              onToggle={() => toggleSection('timeline')}
            />
            {expandedSections.timeline && (
              <div className="p-6">
                <div className="relative">
                  <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-200"></div>
                  <div className="space-y-4">
                    <div className="relative flex items-start gap-4">
                      <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center relative z-10">
                        <Calendar className="w-4 h-4 text-blue-600" />
                      </div>
                      <div>
                        <h5 className="font-medium text-gray-900">Record Date</h5>
                        <p className="text-sm text-gray-600">{formatDate(result.date)}</p>
                      </div>
                    </div>
                    <div className="relative flex items-start gap-4">
                      <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center relative z-10">
                        <FileText className="w-4 h-4 text-green-600" />
                      </div>
                      <div>
                        <h5 className="font-medium text-gray-900">Data Source</h5>
                        <p className="text-sm text-gray-600">{sourceInfo.description}</p>
                      </div>
                    </div>
                    <div className="relative flex items-start gap-4">
                      <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center relative z-10">
                        <TrendingUp className="w-4 h-4 text-purple-600" />
                      </div>
                      <div>
                        <h5 className="font-medium text-gray-900">Activity Status</h5>
                        <p className="text-sm text-gray-600">
                          {analysisData.compliance.isRecent ? 'Active/Recent' : 'Historical Record'}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Technical Details Section */}
          <div className="border-b">
            <SectionHeader
              title="Technical Details"
              icon={FileText}
              expanded={expandedSections.technical}
              onToggle={() => toggleSection('technical')}
            />
            {expandedSections.technical && (
              <div className="p-6 space-y-4">
                <div className="grid grid-cols-1 gap-4">
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-3">All Available Fields</h4>
                    <div className="bg-gray-50 rounded-lg p-4 max-h-64 overflow-auto">
                      <dl className="space-y-2">
                        {Object.entries(result).map(([key, value]) => {
                          if (key === 'raw_data' || !value) return null;
                          
                          const displayKey = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                          const displayValue = Array.isArray(value) ? value.join(', ') :
                                             typeof value === 'object' ? JSON.stringify(value) :
                                             String(value);

                          return (
                            <div key={key} className="flex gap-4">
                              <dt className="text-sm font-medium text-gray-600 min-w-24 flex-shrink-0">
                                {displayKey}:
                              </dt>
                              <dd className="text-sm text-gray-900 break-words flex-1">
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
                  </div>
                  
                  {result.raw_data && (
                    <div>
                      <h4 className="font-semibold text-gray-900 mb-3">Raw API Data</h4>
                      <div className="bg-gray-900 text-green-400 rounded-lg p-4 max-h-64 overflow-auto text-xs font-mono">
                        <pre>{JSON.stringify(result.raw_data, null, 2)}</pre>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t bg-gray-50">
          <div className="flex items-center gap-3">
            {result.url && (
              <a
                href={result.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                <ExternalLink className="w-4 h-4" />
                View Original
              </a>
            )}
            <button
              onClick={() => copyToClipboard(JSON.stringify(result, null, 2))}
              className="inline-flex items-center gap-2 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
            >
              <Copy className="w-4 h-4" />
              Copy Data
            </button>
          </div>
          <div className="text-sm text-gray-500">
            Source: {sourceInfo.name}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DetailedResultView; 