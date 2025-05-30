// Main application store using Zustand
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { 
  VetRecord, 
  SearchFilters, 
  Jurisdiction, 
  EntityType, 
  DataSource 
} from '@/types';

interface AppState {
  // Search state
  searchQuery: string;
  searchResults: VetRecord[];
  searchLoading: boolean;
  searchError: string | null;
  
  // Filters
  searchFilters: SearchFilters;
  
  // UI state
  isDarkMode: boolean;
  sidebarOpen: boolean;
  selectedRecord: VetRecord | null;
  recordDetailOpen: boolean;
  
  // Recent searches (persisted)
  recentSearches: string[];
  
  // Actions
  setSearchQuery: (query: string) => void;
  setSearchResults: (results: VetRecord[]) => void;
  setSearchLoading: (loading: boolean) => void;
  setSearchError: (error: string | null) => void;
  addRecentSearch: (query: string) => void;
  clearRecentSearches: () => void;
  
  // Filter actions
  setJurisdictions: (jurisdictions: Jurisdiction[]) => void;
  setYearRange: (range: [number, number]) => void;
  setEntityType: (type: EntityType) => void;
  setDataSources: (sources: DataSource[]) => void;
  resetFilters: () => void;
  
  // UI actions
  toggleDarkMode: () => void;
  setSidebarOpen: (open: boolean) => void;
  setSelectedRecord: (record: VetRecord | null) => void;
  setRecordDetailOpen: (open: boolean) => void;
}

const defaultFilters: SearchFilters = {
  jurisdictions: ['NYC', 'NYS', 'Federal'],
  yearRange: [2020, new Date().getFullYear()],
  entityType: 'All',
  dataSources: ['checkbook', 'dbnyc', 'nys_ethics', 'senate_lda', 'house_lda', 'nyc_lobbyist'],
};

export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
      // Initial state
      searchQuery: '',
      searchResults: [],
      searchLoading: false,
      searchError: null,
      searchFilters: defaultFilters,
      isDarkMode: false,
      sidebarOpen: false,
      selectedRecord: null,
      recordDetailOpen: false,
      recentSearches: [],

      // Search actions
      setSearchQuery: (query: string) => set({ searchQuery: query }),
      
      setSearchResults: (results: VetRecord[]) => set({ 
        searchResults: results,
        searchLoading: false,
        searchError: null,
      }),
      
      setSearchLoading: (loading: boolean) => set({ searchLoading: loading }),
      
      setSearchError: (error: string | null) => set({ 
        searchError: error,
        searchLoading: false,
      }),
      
      addRecentSearch: (query: string) => {
        const trimmed = query.trim();
        if (!trimmed) return;
        
        const current = get().recentSearches;
        const filtered = current.filter(s => s !== trimmed);
        const updated = [trimmed, ...filtered].slice(0, 5); // Keep last 5
        
        set({ recentSearches: updated });
      },
      
      clearRecentSearches: () => set({ recentSearches: [] }),

      // Filter actions
      setJurisdictions: (jurisdictions: Jurisdiction[]) => set(state => ({
        searchFilters: { ...state.searchFilters, jurisdictions }
      })),
      
      setYearRange: (yearRange: [number, number]) => set(state => ({
        searchFilters: { ...state.searchFilters, yearRange }
      })),
      
      setEntityType: (entityType: EntityType) => set(state => ({
        searchFilters: { ...state.searchFilters, entityType }
      })),
      
      setDataSources: (dataSources: DataSource[]) => set(state => ({
        searchFilters: { ...state.searchFilters, dataSources }
      })),
      
      resetFilters: () => set({ searchFilters: defaultFilters }),

      // UI actions
      toggleDarkMode: () => set(state => ({ isDarkMode: !state.isDarkMode })),
      
      setSidebarOpen: (sidebarOpen: boolean) => set({ sidebarOpen }),
      
      setSelectedRecord: (selectedRecord: VetRecord | null) => set({ selectedRecord }),
      
      setRecordDetailOpen: (recordDetailOpen: boolean) => set({ 
        recordDetailOpen,
        selectedRecord: recordDetailOpen ? get().selectedRecord : null,
      }),
    }),
    {
      name: 'vetting-intelligence-store',
      partialize: (state) => ({
        // Only persist certain parts of the state
        recentSearches: state.recentSearches,
        isDarkMode: state.isDarkMode,
        searchFilters: state.searchFilters,
      }),
    }
  )
);

// Selectors for common derived state
export const useSearchState = () => useAppStore(state => ({
  query: state.searchQuery,
  results: state.searchResults,
  loading: state.searchLoading,
  error: state.searchError,
}));

export const useFilters = () => useAppStore(state => state.searchFilters);

export const useRecentSearches = () => useAppStore(state => state.recentSearches);

export const useUIState = () => useAppStore(state => ({
  isDarkMode: state.isDarkMode,
  sidebarOpen: state.sidebarOpen,
  selectedRecord: state.selectedRecord,
  recordDetailOpen: state.recordDetailOpen,
})); 