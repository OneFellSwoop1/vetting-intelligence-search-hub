// Core domain types for the Vetting Intelligence Search Hub

export interface VetRecord {
  id?: string;
  source: DataSource;
  jurisdiction: Jurisdiction;
  entity_name: string;
  role_or_title?: string;
  description?: string;
  amount_or_value?: string;
  filing_date?: string;
  url_to_original_record?: string;
  metadata?: Record<string, any>;
}

export type DataSource = 
  | "checkbook" 
  | "dbnyc"
  | "nys_ethics" 
  | "senate_lda" 
  | "house_lda" 
  | "nyc_lobbyist";

export type Jurisdiction = "NYC" | "NYS" | "Federal";

export type EntityType = "All" | "People" | "Companies";

export interface SearchRequest {
  query: string;
  year?: number;
  jurisdiction?: Jurisdiction;
  jurisdictions?: Jurisdiction[];
  years?: number[];
  entity_type?: EntityType;
}

export interface SearchResponse {
  total_hits: Record<DataSource, number>;
  search_stats?: {
    total_results: number;
    per_source: Record<DataSource, number>;
  };
  results: VetRecord[];
  analytics?: {
    total_results: number;
    financial_analysis?: {
      total_amount: number;
      average_amount: number;
      max_amount: number;
      min_amount: number;
      count_with_amounts: number;
    };
    year_breakdown: [string, number][];
    jurisdiction_breakdown: [string, number][];
    source_breakdown: [string, number][];
  };
}

export interface SearchFilters {
  jurisdictions: Jurisdiction[];
  yearRange: [number, number];
  entityType: EntityType;
  dataSources: DataSource[];
}

export interface AppState {
  searchQuery: string;
  searchFilters: SearchFilters;
  recentSearches: string[];
  isDarkMode: boolean;
  sidebarOpen: boolean;
}

// UI Component Props
export interface SearchBarProps {
  onSearch: (query: string) => void;
  loading?: boolean;
  placeholder?: string;
  value?: string;
}

export interface ResultsTableProps {
  records: VetRecord[];
  loading?: boolean;
  onRecordClick?: (record: VetRecord) => void;
}

export interface RecordDetailProps {
  record: VetRecord;
  open: boolean;
  onClose: () => void;
}

// Analytics types
export interface AnalyticsData {
  totalValue: number;
  recordCount: number;
  topEntities: Array<{
    name: string;
    value: number;
    count: number;
  }>;
  yearlyBreakdown: Array<{
    year: string;
    value: number;
    count: number;
  }>;
  jurisdictionBreakdown: Array<{
    jurisdiction: Jurisdiction;
    value: number;
    count: number;
  }>;
}

// API Response types (for mapping from backend)
export interface BackendSearchResponse {
  total_hits: Record<string, number>;
  search_stats?: {
    total_results: number;
    per_source: Record<string, number>;
  };
  results: Array<{
    source: string;
    jurisdiction: string;
    entity_name: string;
    role_or_title?: string;
    description?: string;
    amount_or_value?: string;
    filing_date?: string;
    url_to_original_record?: string;
    metadata?: Record<string, any>;
  }>;
  analytics?: any;
} 