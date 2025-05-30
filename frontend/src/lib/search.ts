// Search API client utility
// Wraps the current POST /search endpoint for easy migration later

import { 
  SearchRequest, 
  SearchResponse, 
  VetRecord, 
  BackendSearchResponse, 
  DataSource, 
  Jurisdiction 
} from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8001';

export class SearchClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  /**
   * Search for records using the current backend API
   */
  async search(request: SearchRequest): Promise<SearchResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: request.query,
          year: request.year,
          jurisdiction: request.jurisdiction,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: BackendSearchResponse = await response.json();
      
      // Map backend response to our unified format
      return this.mapBackendResponse(data);
    } catch (error) {
      console.error('Search error:', error);
      throw error;
    }
  }

  /**
   * Health check for the API
   */
  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/health`);
      return response.ok;
    } catch {
      return false;
    }
  }

  /**
   * Map backend response format to our VetRecord format
   */
  private mapBackendResponse(backendResponse: BackendSearchResponse): SearchResponse {
    const records: VetRecord[] = backendResponse.results.map((result, index) => ({
      id: `${result.source}-${index}`, // Generate ID for frontend use
      source: this.mapDataSource(result.source),
      jurisdiction: this.mapJurisdiction(result.jurisdiction),
      entity_name: result.entity_name,
      role_or_title: result.role_or_title,
      description: result.description,
      amount_or_value: result.amount_or_value,
      filing_date: result.filing_date,
      url_to_original_record: result.url_to_original_record,
      metadata: result.metadata,
    }));

    return {
      total_hits: this.mapTotalHits(backendResponse.total_hits),
      search_stats: backendResponse.search_stats ? {
        total_results: backendResponse.search_stats.total_results,
        per_source: this.mapPerSource(backendResponse.search_stats.per_source),
      } : undefined,
      results: records,
      analytics: backendResponse.analytics,
    };
  }

  private mapDataSource(source: string): DataSource {
    // Map backend source strings to our DataSource enum
    const sourceMap: Record<string, DataSource> = {
      'checkbook': 'checkbook',
      'dbnyc': 'dbnyc', 
      'nys_ethics': 'nys_ethics',
      'senate_lda': 'senate_lda',
      'house_lda': 'house_lda',
      'nyc_lobbyist': 'nyc_lobbyist',
    };
    
    return sourceMap[source] || 'checkbook'; // fallback
  }

  private mapJurisdiction(jurisdiction: string): Jurisdiction {
    // Map backend jurisdiction strings to our Jurisdiction enum
    const jurisdictionMap: Record<string, Jurisdiction> = {
      'NYC': 'NYC',
      'NYS': 'NYS', 
      'Federal': 'Federal',
    };
    
    return jurisdictionMap[jurisdiction] || 'Federal'; // fallback
  }

  private mapTotalHits(backendHits: Record<string, number>): Record<DataSource, number> {
    const mapped: Record<DataSource, number> = {
      checkbook: 0,
      dbnyc: 0,
      nys_ethics: 0,
      senate_lda: 0,
      house_lda: 0,
      nyc_lobbyist: 0,
    };

    Object.entries(backendHits).forEach(([key, value]) => {
      const mappedKey = this.mapDataSource(key);
      mapped[mappedKey] = value;
    });

    return mapped;
  }

  private mapPerSource(backendPerSource: Record<string, number>): Record<DataSource, number> {
    return this.mapTotalHits(backendPerSource);
  }
}

// Default instance
export const searchClient = new SearchClient();

// Utility functions for common operations
export const formatAmount = (amount?: string): string => {
  if (!amount) return 'Not specified';
  
  // Clean and format monetary amounts
  const cleanAmount = amount.replace(/[^0-9.-]/g, '');
  const numAmount = parseFloat(cleanAmount);
  
  if (isNaN(numAmount)) return amount;
  
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(numAmount);
};

export const formatDate = (date?: string): string => {
  if (!date) return 'Not specified';
  
  try {
    return new Date(date).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  } catch {
    return date;
  }
};

export const getSourceIcon = (source: DataSource): string => {
  const iconMap: Record<DataSource, string> = {
    checkbook: '🏙️',
    dbnyc: '💰',
    nys_ethics: '⚖️',
    senate_lda: '🏛️',
    house_lda: '🏛️',
    nyc_lobbyist: '🗽',
  };
  
  return iconMap[source] || '📄';
};

export const getSourceName = (source: DataSource): string => {
  const nameMap: Record<DataSource, string> = {
    checkbook: 'NYC Checkbook',
    dbnyc: 'FEC Campaign Finance',
    nys_ethics: 'NYS Ethics',
    senate_lda: 'Senate Lobbying',
    house_lda: 'House Lobbying',
    nyc_lobbyist: 'NYC Lobbyist',
  };
  
  return nameMap[source] || source;
}; 