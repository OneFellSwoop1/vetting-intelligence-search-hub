import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.adapters.checkbook import search_checkbook
from app.adapters.dbnyc import search_dbnyc
from app.adapters.nys_ethics import search_nys_ethics
from app.adapters.senate_lda import search_senate_lda
from app.adapters.house_lda import search_house_lda
from app.adapters.nyc_lobbyist import search_nyc_lobbyist
from app.schemas import SearchResult
from app.cache import cache_service

client = TestClient(app)

class TestSearchEndpoint:
    """Test the main search endpoint functionality."""
    
    def test_health_check(self):
        """Test basic health check endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data
    
    @patch('app.routers.search.asyncio.gather')
    def test_search_endpoint_success(self, mock_gather):
        """Test successful search with mocked results."""
        # Mock results from different sources
        mock_results = [
            [SearchResult(
                source="checkbook",
                jurisdiction="NYC",
                entity_name="Test Entity 1",
                role_or_title="Contract",
                description="Test description",
                amount_or_value="$1,000",
                filing_date="2024-01-01",
                url_to_original_record="https://example.com/1"
            )],
            [],  # dbnyc - no results
            [SearchResult(
                source="nys_ethics",
                jurisdiction="NYS",
                entity_name="Test Entity 2",
                role_or_title="Lobbyist",
                description="Test lobbyist",
                amount_or_value=None,
                filing_date="2024-01-02",
                url_to_original_record="https://example.com/2"
            )],
            [],  # senate_lda
            [],  # house_lda
            []   # nyc_lobbyist
        ]
        
        mock_gather.return_value = mock_results
        
        response = client.post("/search", json={
            "query": "test query",
            "year": "2024",
            "jurisdiction": None
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_hits" in data
        assert "results" in data
        assert len(data["results"]) == 2
        assert data["total_hits"]["checkbook"] == 1
        assert data["total_hits"]["nys_ethics"] == 1
    
    def test_search_endpoint_validation(self):
        """Test search endpoint input validation."""
        # Missing query
        response = client.post("/search", json={
            "year": "2024"
        })
        assert response.status_code == 422
        
        # Empty query
        response = client.post("/search", json={
            "query": "",
            "year": "2024"
        })
        assert response.status_code == 422
    
    def test_search_jurisdiction_filter(self):
        """Test jurisdiction filtering."""
        with patch('app.routers.search.asyncio.gather') as mock_gather:
            mock_gather.return_value = [[], [], []]  # Only 3 tasks for NYC
            
            response = client.post("/search", json={
                "query": "test",
                "jurisdiction": "NYC"
            })
            
            assert response.status_code == 200
            # Should only call NYC sources (checkbook, dbnyc, nyc_lobbyist)
            assert mock_gather.call_count == 1
            args = mock_gather.call_args[0]
            assert len(args[0]) == 3  # 3 tasks for NYC sources


class TestAdapters:
    """Test individual data source adapters."""
    
    @pytest.mark.asyncio
    async def test_checkbook_adapter(self):
        """Test the checkbook adapter with mocked HTTP responses."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = [
                {
                    "vendor_legal_name": "Test Vendor",
                    "document_id": "12345",
                    "purpose": "Test purpose",
                    "total_amount": 1000.00,
                    "issue_date": "2024-01-01"
                }
            ]
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            results = await search_checkbook("test query")
            
            assert len(results) > 0
            assert results[0].source == "checkbook"
            assert results[0].jurisdiction == "NYC"
            assert results[0].entity_name == "Test Vendor"
    
    @pytest.mark.asyncio
    async def test_adapter_error_handling(self):
        """Test adapter error handling with network failures."""
        with patch('httpx.AsyncClient') as mock_client:
            # Simulate network error
            mock_client.return_value.__aenter__.side_effect = Exception("Network error")
            
            # Should not raise exception, should return empty list
            results = await search_checkbook("test query")
            assert results == []
    
    @pytest.mark.asyncio
    async def test_senate_lda_missing_api_key(self):
        """Test Senate LDA adapter when API key is missing."""
        with patch.dict('os.environ', {}, clear=True):
            results = await search_senate_lda("test query")
            assert results == []


class TestCaching:
    """Test the Redis caching functionality."""
    
    def test_cache_key_generation(self):
        """Test cache key generation for consistency."""
        key1 = cache_service._get_cache_key("test query", "2024", "NYC")
        key2 = cache_service._get_cache_key("test query", "2024", "NYC")
        key3 = cache_service._get_cache_key("different query", "2024", "NYC")
        
        assert key1 == key2  # Same inputs should generate same key
        assert key1 != key3  # Different inputs should generate different keys
    
    def test_cache_disabled_fallback(self):
        """Test cache behavior when Redis is not available."""
        # Temporarily disable Redis
        original_client = cache_service.redis_client
        cache_service.redis_client = None
        
        try:
            # Should return None when cache is disabled
            result = cache_service.get_cached_results("test", "2024")
            assert result is None
            
            # Should not raise error when caching
            cache_service.cache_results("test", {}, [], "2024")
            
        finally:
            cache_service.redis_client = original_client
    
    @patch('redis.from_url')
    def test_cache_stats_with_mock_redis(self, mock_redis):
        """Test cache statistics with mocked Redis."""
        mock_client = MagicMock()
        mock_client.info.return_value = {
            'used_memory_human': '1MB',
            'connected_clients': 2,
            'db0': {'keys': 10}
        }
        mock_client.keys.return_value = ['search:key1', 'search:key2']
        mock_redis.return_value = mock_client
        
        # Create new cache service instance
        from app.cache import CacheService
        test_cache = CacheService()
        
        stats = test_cache.get_cache_stats()
        
        assert stats['status'] == 'connected'
        assert stats['search_keys'] == 2
        assert stats['memory_usage'] == '1MB'


class TestIntegration:
    """Integration tests for the complete search workflow."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_search_workflow(self):
        """Test complete search workflow from request to response."""
        # This would typically use a test database or mock external services
        with patch('app.routers.search.asyncio.gather') as mock_gather:
            # Mock a realistic mixed result set
            mock_results = [
                [SearchResult(
                    source="checkbook",
                    jurisdiction="NYC", 
                    entity_name="NYC Department of Transportation",
                    role_or_title="Vendor",
                    description="Road maintenance contract",
                    amount_or_value="$500,000",
                    filing_date="2024-01-15",
                    url_to_original_record="https://checkbook.nyc/contract/123"
                )],
                [],  # No results from other sources
                [],
                [],
                [],
                []
            ]
            
            mock_gather.return_value = mock_results
            
            response = client.post("/search", json={
                "query": "Department of Transportation",
                "year": "2024"
            })
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify response structure
            assert "total_hits" in data
            assert "results" in data
            assert len(data["results"]) == 1
            
            # Verify result data
            result = data["results"][0]
            assert result["source"] == "checkbook"
            assert result["jurisdiction"] == "NYC"
            assert result["entity_name"] == "NYC Department of Transportation"
            assert "$500,000" in result["amount_or_value"]
    
    def test_cache_integration(self):
        """Test that caching works in the search endpoint."""
        with patch('app.cache.cache_service') as mock_cache:
            # First call - cache miss
            mock_cache.get_cached_results.return_value = None
            
            with patch('app.routers.search.asyncio.gather') as mock_gather:
                mock_gather.return_value = [[] for _ in range(6)]  # Empty results
                
                response = client.post("/search", json={"query": "test"})
                assert response.status_code == 200
                
                # Verify cache was checked and results were cached
                mock_cache.get_cached_results.assert_called_once()
                mock_cache.cache_results.assert_called_once()


# Pytest fixtures for common test data
@pytest.fixture
def sample_search_result():
    """Fixture providing a sample SearchResult for testing."""
    return SearchResult(
        source="checkbook",
        jurisdiction="NYC",
        entity_name="Test Entity",
        role_or_title="Test Role",
        description="Test Description",
        amount_or_value="$1,000",
        filing_date="2024-01-01",
        url_to_original_record="https://example.com/test"
    )

@pytest.fixture
def mock_search_response():
    """Fixture providing a mock search response."""
    return {
        "total_hits": {"checkbook": 1, "dbnyc": 0},
        "results": [
            {
                "source": "checkbook",
                "jurisdiction": "NYC",
                "entity_name": "Test Entity",
                "role_or_title": "Test Role",
                "description": "Test Description",
                "amount_or_value": "$1,000",
                "filing_date": "2024-01-01",
                "url_to_original_record": "https://example.com/test"
            }
        ]
    } 