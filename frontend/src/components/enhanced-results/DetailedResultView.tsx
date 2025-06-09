import React, { useState } from 'react';
import { 
  ExternalLink, 
  Calendar, 
  DollarSign, 
  Building, 
  ChevronDown,
  ChevronRight,
  Download,
  Share2,
  Copy,
  MapPin,
  User,
  FileText,
  Gavel,
  Building2,
  CreditCard,
  Phone,
  Mail,
  Globe,
  Hash,
  Clock
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
  
  // Additional fields that might be present in different sources
  contract_id?: string;
  contract_amount?: string;
  start_date?: string;
  end_date?: string;
  award_method?: string;
  commodity_category?: string;
  
  // Senate/House LDA specific
  filing_date?: string;
  filing_period?: string;
  client_name?: string;
  registrant_name?: string;
  lobbying_issues?: string;
  lobbying_areas?: string[];
  
  // FEC specific
  contributor_name?: string;
  recipient_name?: string;
  contribution_date?: string;
  election_cycle?: string;
  committee_type?: string;
  
  // NYC Lobbyist specific
  lobbyist_name?: string;
  client_business_address?: string;
  compensation_amount?: string;
  expense_amount?: string;
  
  // NY State Ethics specific
  procurement_type?: string;
  buyer_agency?: string;
  award_date?: string;
}

interface DetailedResultViewProps {
  result: SearchResult;
  onClose?: () => void;
  className?: string;
}

const sourceConfig = {
  checkbook: { 
    name: 'NYC Contracts', 
    color: 'bg-blue-100 text-blue-800',
    icon: '🏛️',
    baseUrl: 'https://checkbook.nyc.gov',
    description: 'New York City government contracts and spending'
  },
  dbnyc: { 
    name: 'FEC Campaign Finance', 
    color: 'bg-green-100 text-green-800',
    icon: '🗳️',
    baseUrl: 'https://www.fec.gov',
    description: 'Federal Election Commission campaign finance data'
  },
  nys_ethics: { 
    name: 'NY State Ethics', 
    color: 'bg-purple-100 text-purple-800',
    icon: '⚖️',
    baseUrl: 'https://ethics.ny.gov',
    description: 'New York State ethics and procurement records'
  },
  senate_lda: { 
    name: 'Senate LDA', 
    color: 'bg-red-100 text-red-800',
    icon: '🏛️',
    baseUrl: 'https://lda.senate.gov',
    description: 'Senate Lobbying Disclosure Act filings'
  },
  house_lda: { 
    name: 'House LDA', 
    color: 'bg-orange-100 text-orange-800',
    icon: '🏛️',
    baseUrl: 'https://disclosurespreview.house.gov',
    description: 'House Lobbying Disclosure Act filings'
  },
  nyc_lobbyist: { 
    name: 'NYC Lobbyist', 
    color: 'bg-indigo-100 text-indigo-800',
    icon: '🏢',
    baseUrl: 'https://www.nyc.gov/site/coib',
    description: 'NYC Conflicts of Interest Board lobbyist registrations'
  }
};

const DetailedResultView: React.FC<DetailedResultViewProps> = ({ 
  result, 
  onClose, 
  className 
}) => {
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    overview: true,
    financial: true,
    parties: true,
    details: false,
    metadata: false
  });

  const sourceInfo = sourceConfig[result.source as keyof typeof sourceConfig] || {
    name: result.source,
    color: 'bg-gray-100 text-gray-800',
    icon: '📄',
    baseUrl: '',
    description: 'Government data source'
  };

  const toggleSection = (section: string) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const generateDirectLink = () => {
    if (result.url) return result.url;
    
    // Generate best-effort direct links based on source
    switch (result.source) {
      case 'senate_lda':
        return 'https://lda.senate.gov/filings/public/';
      case 'house_lda':
        return 'https://disclosurespreview.house.gov/';
      case 'checkbook':
        return 'https://checkbook.nyc.gov/spending_landing/yeartype/B/year/2024';
      case 'dbnyc':
        return 'https://www.fec.gov/data/';
      case 'nys_ethics':
        return 'https://www.ethics.ny.gov/';
      case 'nyc_lobbyist':
        return 'https://www.nyc.gov/site/coib/lobbying/lobbyist-search.page';
      default:
        return sourceInfo.baseUrl;
    }
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

  const SectionHeader = ({ title, isExpanded, onToggle, icon }: {
    title: string;
    isExpanded: boolean;
    onToggle: () => void;
    icon: React.ReactNode;
  }) => (
    <button
      onClick={onToggle}
      className="w-full flex items-center justify-between p-3 bg-gray-50 hover:bg-gray-100 transition-colors border-b"
    >
      <div className="flex items-center gap-2">
        {icon}
        <span className="font-medium text-gray-900">{title}</span>
      </div>
      {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
    </button>
  );

  const InfoRow = ({ label, value, icon, copyable = false }: {
    label: string;
    value: string | number | undefined;
    icon?: React.ReactNode;
    copyable?: boolean;
  }) => {
    if (!value) return null;
    
    return (
      <div className="flex items-center justify-between py-2 border-b border-gray-100 last:border-b-0">
        <div className="flex items-center gap-2 text-sm text-gray-600">
          {icon}
          <span>{label}:</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-gray-900">{value}</span>
          {copyable && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => copyToClipboard(String(value))}
              className="h-6 w-6 p-0"
            >
              <Copy className="w-3 h-3" />
            </Button>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className={cn("bg-white border border-gray-200 rounded-lg shadow-lg", className)}>
      {/* Header */}
      <div className="border-b border-gray-200 p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className={cn("px-3 py-1 rounded-full text-sm font-medium", sourceInfo.color)}>
              {sourceInfo.icon} {sourceInfo.name}
            </div>
            {result.record_type && (
              <div className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm">
                {result.record_type}
              </div>
            )}
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => copyToClipboard(window.location.href)}
            >
              <Share2 className="w-4 h-4 mr-1" />
              Share
            </Button>
            {onClose && (
              <Button variant="outline" size="sm" onClick={onClose}>
                Close
              </Button>
            )}
          </div>
        </div>
        
        <h1 className="text-xl font-bold text-gray-900 mb-2">{result.title}</h1>
        <p className="text-gray-600 leading-relaxed">{result.description}</p>
        
        {/* Quick Stats */}
        <div className="flex items-center gap-6 mt-4 pt-4 border-t border-gray-100">
          {result.amount && (
            <div className="flex items-center gap-2 text-green-600">
              <DollarSign className="w-4 h-4" />
              <span className="font-semibold">{formatAmount(result.amount)}</span>
            </div>
          )}
          {result.date && (
            <div className="flex items-center gap-2 text-gray-600">
              <Calendar className="w-4 h-4" />
              <span>{formatDate(result.date)}</span>
            </div>
          )}
          {result.agency && (
            <div className="flex items-center gap-2 text-gray-600">
              <Building className="w-4 h-4" />
              <span>{result.agency}</span>
            </div>
          )}
        </div>
      </div>

      {/* Overview Section */}
      <div className="border-b border-gray-200">
        <SectionHeader
          title="Overview"
          isExpanded={expandedSections.overview}
          onToggle={() => toggleSection('overview')}
          icon={<FileText className="w-4 h-4" />}
        />
        {expandedSections.overview && (
          <div className="p-4 space-y-2">
            <InfoRow label="Source" value={sourceInfo.description} icon={<Globe className="w-4 h-4" />} />
            <InfoRow label="Record Type" value={result.record_type} icon={<Hash className="w-4 h-4" />} />
            <InfoRow label="Year" value={result.year} icon={<Clock className="w-4 h-4" />} />
            {result.contract_id && (
              <InfoRow 
                label="Contract ID" 
                value={result.contract_id} 
                icon={<Hash className="w-4 h-4" />} 
                copyable 
              />
            )}
          </div>
        )}
      </div>

      {/* Financial Information */}
      {(result.amount || result.contract_amount || result.compensation_amount) && (
        <div className="border-b border-gray-200">
          <SectionHeader
            title="Financial Information"
            isExpanded={expandedSections.financial}
            onToggle={() => toggleSection('financial')}
            icon={<DollarSign className="w-4 h-4" />}
          />
          {expandedSections.financial && (
            <div className="p-4 space-y-2">
              <InfoRow label="Amount" value={formatAmount(result.amount)} icon={<DollarSign className="w-4 h-4" />} />
              <InfoRow label="Contract Amount" value={formatAmount(result.contract_amount)} icon={<CreditCard className="w-4 h-4" />} />
              <InfoRow label="Compensation" value={formatAmount(result.compensation_amount)} icon={<DollarSign className="w-4 h-4" />} />
              <InfoRow label="Expenses" value={formatAmount(result.expense_amount)} icon={<DollarSign className="w-4 h-4" />} />
            </div>
          )}
        </div>
      )}

      {/* Parties Involved */}
      {(result.vendor || result.client_name || result.contributor_name || result.lobbyist_name) && (
        <div className="border-b border-gray-200">
          <SectionHeader
            title="Parties Involved"
            isExpanded={expandedSections.parties}
            onToggle={() => toggleSection('parties')}
            icon={<User className="w-4 h-4" />}
          />
          {expandedSections.parties && (
            <div className="p-4 space-y-2">
              <InfoRow label="Vendor" value={result.vendor} icon={<Building2 className="w-4 h-4" />} />
              <InfoRow label="Client" value={result.client_name} icon={<User className="w-4 h-4" />} />
              <InfoRow label="Contributor" value={result.contributor_name} icon={<User className="w-4 h-4" />} />
              <InfoRow label="Recipient" value={result.recipient_name} icon={<User className="w-4 h-4" />} />
              <InfoRow label="Lobbyist" value={result.lobbyist_name} icon={<User className="w-4 h-4" />} />
              <InfoRow label="Registrant" value={result.registrant_name} icon={<Building2 className="w-4 h-4" />} />
              {result.client_business_address && (
                <InfoRow 
                  label="Address" 
                  value={result.client_business_address} 
                  icon={<MapPin className="w-4 h-4" />} 
                />
              )}
            </div>
          )}
        </div>
      )}

      {/* Additional Details */}
      <div className="border-b border-gray-200">
        <SectionHeader
          title="Additional Details"
          isExpanded={expandedSections.details}
          onToggle={() => toggleSection('details')}
          icon={<FileText className="w-4 h-4" />}
        />
        {expandedSections.details && (
          <div className="p-4 space-y-2">
            <InfoRow label="Award Method" value={result.award_method} icon={<Gavel className="w-4 h-4" />} />
            <InfoRow label="Commodity Category" value={result.commodity_category} icon={<FileText className="w-4 h-4" />} />
            <InfoRow label="Procurement Type" value={result.procurement_type} icon={<FileText className="w-4 h-4" />} />
            <InfoRow label="Filing Period" value={result.filing_period} icon={<Calendar className="w-4 h-4" />} />
            <InfoRow label="Election Cycle" value={result.election_cycle} icon={<Calendar className="w-4 h-4" />} />
            <InfoRow label="Committee Type" value={result.committee_type} icon={<Building className="w-4 h-4" />} />
            {result.lobbying_issues && (
              <div className="py-2">
                <div className="text-sm text-gray-600 mb-2">Lobbying Issues:</div>
                <div className="text-sm text-gray-900 bg-gray-50 p-3 rounded">
                  {result.lobbying_issues}
                </div>
              </div>
            )}
            {result.lobbying_areas && result.lobbying_areas.length > 0 && (
              <div className="py-2">
                <div className="text-sm text-gray-600 mb-2">Lobbying Areas:</div>
                <div className="flex flex-wrap gap-2">
                  {result.lobbying_areas.map((area, index) => (
                    <span 
                      key={index}
                      className="px-2 py-1 bg-blue-50 text-blue-700 text-xs rounded"
                    >
                      {area}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Metadata */}
      <div>
        <SectionHeader
          title="Metadata"
          isExpanded={expandedSections.metadata}
          onToggle={() => toggleSection('metadata')}
          icon={<Hash className="w-4 h-4" />}
        />
        {expandedSections.metadata && (
          <div className="p-4 space-y-2">
            <InfoRow label="Start Date" value={formatDate(result.start_date)} icon={<Calendar className="w-4 h-4" />} />
            <InfoRow label="End Date" value={formatDate(result.end_date)} icon={<Calendar className="w-4 h-4" />} />
            <InfoRow label="Filing Date" value={formatDate(result.filing_date)} icon={<Calendar className="w-4 h-4" />} />
            <InfoRow label="Award Date" value={formatDate(result.award_date)} icon={<Calendar className="w-4 h-4" />} />
            <InfoRow label="Contribution Date" value={formatDate(result.contribution_date)} icon={<Calendar className="w-4 h-4" />} />
            <InfoRow label="Client Count" value={result.client_count} icon={<Hash className="w-4 h-4" />} />
            <InfoRow label="Registration Count" value={result.registration_count} icon={<Hash className="w-4 h-4" />} />
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="p-6 bg-gray-50 border-t border-gray-200">
        <div className="flex items-center justify-between">
          <div className="text-sm text-gray-600">
            Last updated: {formatDate(result.date || new Date().toISOString())}
          </div>
          <div className="flex items-center gap-2">
            {generateDirectLink() && (
              <Button
                variant="default"
                size="sm"
                onClick={() => window.open(generateDirectLink(), '_blank')}
              >
                <ExternalLink className="w-4 h-4 mr-1" />
                View Source
              </Button>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                const data = JSON.stringify(result, null, 2);
                const blob = new Blob([data], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `${result.source}_${result.title.replace(/[^a-zA-Z0-9]/g, '_')}.json`;
                a.click();
              }}
            >
              <Download className="w-4 h-4 mr-1" />
              Export
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DetailedResultView; 