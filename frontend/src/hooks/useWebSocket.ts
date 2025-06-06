import { useEffect, useRef, useState, useCallback } from 'react';

interface WebSocketMessage {
  type: string;
  [key: string]: any;
}

interface SearchProgress {
  source: string;
  status: 'pending' | 'loading' | 'completed' | 'error';
  count?: number;
  error?: string;
  display_name?: string;
  results?: any[];
}

interface UseWebSocketReturn {
  isConnected: boolean;
  searchProgress: SearchProgress[];
  searchResults: any[];
  totalHits: Record<string, number>;
  isSearching: boolean;
  error: string | null;
  startSearch: (query: string, filters?: any) => void;
  cancelSearch: () => void;
  reconnect: () => void;
}

export const useWebSocket = (url: string): UseWebSocketReturn => {
  const [isConnected, setIsConnected] = useState(false);
  const [searchProgress, setSearchProgress] = useState<SearchProgress[]>([]);
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [totalHits, setTotalHits] = useState<Record<string, number>>({});
  const [isSearching, setIsSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 5;

  const connect = useCallback(() => {
    try {
      // Generate a unique client ID
      const clientId = `client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      const wsUrl = `${url}/ws/${clientId}`;
      
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        // WebSocket connected
        setIsConnected(true);
        setError(null);
        reconnectAttemptsRef.current = 0;
        
        // Send ping to test connection
        wsRef.current?.send(JSON.stringify({
          type: 'ping',
          timestamp: Date.now()
        }));
      };

      wsRef.current.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          handleMessage(message);
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };

      wsRef.current.onclose = (event) => {
        // WebSocket disconnected
        setIsConnected(false);
        setIsSearching(false);
        
        // Attempt to reconnect if not a manual close
        if (event.code !== 1000 && reconnectAttemptsRef.current < maxReconnectAttempts) {
          const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 30000);
          // Attempting to reconnect
          
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttemptsRef.current++;
            connect();
          }, delay);
        }
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setError('WebSocket connection error');
      };

    } catch (err) {
      console.error('Failed to create WebSocket connection:', err);
      setError('Failed to establish WebSocket connection');
    }
  }, [url]);

  const handleMessage = useCallback((message: WebSocketMessage) => {
    switch (message.type) {
      case 'pong':
        // Connection is alive
        break;

      case 'search_started':
        setIsSearching(true);
        setSearchProgress([]);
        setSearchResults([]);
        setTotalHits({});
        setError(null);
        break;

      case 'source_started':
        setSearchProgress(prev => {
          const updated = [...prev];
          const existingIndex = updated.findIndex(p => p.source === message.source);
          
          if (existingIndex >= 0) {
            updated[existingIndex] = {
              ...updated[existingIndex],
              status: 'loading',
              display_name: message.display_name
            };
          } else {
            updated.push({
              source: message.source,
              status: 'loading',
              display_name: message.display_name
            });
          }
          
          return updated;
        });
        break;

      case 'source_completed':
        setSearchProgress(prev => {
          const updated = [...prev];
          const existingIndex = updated.findIndex(p => p.source === message.source);
          
          if (existingIndex >= 0) {
            updated[existingIndex] = {
              ...updated[existingIndex],
              status: 'completed',
              count: message.count,
              results: message.results
            };
          } else {
            updated.push({
              source: message.source,
              status: 'completed',
              count: message.count,
              display_name: message.display_name,
              results: message.results
            });
          }
          
          return updated;
        });

        // Add results to the main results array
        if (message.results && message.results.length > 0) {
          setSearchResults(prev => [...prev, ...message.results]);
        }

        // Update total hits
        if (message.count !== undefined) {
          setTotalHits(prev => ({
            ...prev,
            [message.source]: message.count
          }));
        }
        break;

      case 'source_error':
        setSearchProgress(prev => {
          const updated = [...prev];
          const existingIndex = updated.findIndex(p => p.source === message.source);
          
          if (existingIndex >= 0) {
            updated[existingIndex] = {
              ...updated[existingIndex],
              status: 'error',
              error: message.error
            };
          } else {
            updated.push({
              source: message.source,
              status: 'error',
              display_name: message.display_name,
              error: message.error
            });
          }
          
          return updated;
        });
        break;

      case 'search_completed':
        setIsSearching(false);
        if (message.total_hits) {
          setTotalHits(message.total_hits);
        }
        break;

      case 'search_error':
        setIsSearching(false);
        setError(message.error || 'Search failed');
        break;

      case 'search_cancelled':
        setIsSearching(false);
        setSearchProgress([]);
        break;

      case 'error':
        setError(message.message || 'Unknown error');
        break;

      default:
                    // Unknown message type
    }
  }, []);

  const startSearch = useCallback((query: string, filters?: any) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      setError('WebSocket not connected');
      return;
    }

    const searchMessage = {
      type: 'search',
      query: query.trim(),
      year: filters?.year || null,
      jurisdiction: filters?.jurisdiction || null
    };

    wsRef.current.send(JSON.stringify(searchMessage));
  }, []);

  const cancelSearch = useCallback(() => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      return;
    }

    wsRef.current.send(JSON.stringify({
      type: 'cancel_search'
    }));
  }, []);

  const reconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
    }
    reconnectAttemptsRef.current = 0;
    connect();
  }, [connect]);

  // Initialize connection
  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close(1000, 'Component unmounting');
      }
    };
  }, [connect]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close(1000, 'Component unmounting');
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, []);

  return {
    isConnected,
    searchProgress,
    searchResults,
    totalHits,
    isSearching,
    error,
    startSearch,
    cancelSearch,
    reconnect
  };
}; 