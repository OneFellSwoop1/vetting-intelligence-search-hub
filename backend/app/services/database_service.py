"""Database service for search history and analytics persistence."""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from sqlalchemy.orm import selectinload

from ..models import SearchQuery, SearchResult, CorrelationAnalysis, DataSourceStatus
from ..input_validation import ValidatedSearchRequest

logger = logging.getLogger(__name__)


class DatabaseService:
    """
    Service for database operations related to search history and analytics.
    
    Provides methods for:
    - Creating and managing search queries
    - Storing search results
    - Tracking data source performance
    - Analytics and reporting
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize database service.
        
        Args:
            db: Async database session
        """
        self.db = db
    
    async def create_search_query(
        self,
        request: ValidatedSearchRequest,
        user_ip: str,
        user_agent: Optional[str] = None
    ) -> SearchQuery:
        """
        Create a new search query record.
        
        Args:
            request: Search request parameters
            user_ip: Client IP address
            user_agent: Client user agent string
            
        Returns:
            Created SearchQuery instance
        """
        try:
            search_query = SearchQuery(
                query_text=request.query,
                year=request.year,
                jurisdiction=request.jurisdiction,
                user_ip=user_ip,
                user_agent=user_agent,
                sources_queried=[]  # Will be updated after search
            )
            
            self.db.add(search_query)
            await self.db.commit()
            await self.db.refresh(search_query)
            
            logger.info(f"✅ Created search query record: ID {search_query.id}")
            return search_query
            
        except Exception as e:
            logger.error(f"❌ Failed to create search query: {e}")
            await self.db.rollback()
            raise
    
    async def create_search_results(
        self,
        query_id: int,
        results: List[Dict[str, Any]]
    ) -> List[SearchResult]:
        """
        Store search results in database.
        
        Args:
            query_id: ID of the search query
            results: List of search result dictionaries
            
        Returns:
            List of created SearchResult instances
        """
        try:
            search_results = []
            
            for result_data in results:
                search_result = SearchResult(
                    query_id=query_id,
                    title=result_data.get('title', ''),
                    description=result_data.get('description', ''),
                    amount=result_data.get('amount'),
                    date=result_data.get('date'),
                    source=result_data.get('source', ''),
                    vendor=result_data.get('vendor'),
                    agency=result_data.get('agency'),
                    url=result_data.get('url'),
                    record_type=result_data.get('record_type'),
                    year=result_data.get('year'),
                    raw_data=result_data.get('raw_data')
                )
                
                search_results.append(search_result)
                self.db.add(search_result)
            
            await self.db.commit()
            
            logger.info(f"✅ Stored {len(search_results)} search results for query {query_id}")
            return search_results
            
        except Exception as e:
            logger.error(f"❌ Failed to store search results: {e}")
            await self.db.rollback()
            raise
    
    async def update_search_query_results(
        self,
        query_id: int,
        results_metadata: Dict[str, Any],
        execution_time_ms: int
    ) -> None:
        """
        Update search query with results metadata.
        
        Args:
            query_id: ID of the search query
            results_metadata: Metadata about results (total_hits, etc.)
            execution_time_ms: Query execution time in milliseconds
        """
        try:
            # Calculate totals
            total_results = results_metadata.get('total_results', 0)
            total_hits = results_metadata.get('total_hits', {})
            
            # Update query record
            await self.db.execute(
                update(SearchQuery)
                .where(SearchQuery.id == query_id)
                .values(
                    total_results=total_results,
                    sources_queried=list(total_hits.keys()),
                    execution_time_ms=execution_time_ms
                )
            )
            
            await self.db.commit()
            
            logger.info(f"✅ Updated search query {query_id} with results metadata")
            
        except Exception as e:
            logger.error(f"❌ Failed to update search query metadata: {e}")
            await self.db.rollback()
    
    async def update_data_source_status(
        self,
        source_name: str,
        is_available: bool,
        response_time_ms: Optional[int] = None,
        error_message: Optional[str] = None
    ) -> None:
        """
        Update data source status and performance metrics.
        
        Args:
            source_name: Name of the data source
            is_available: Whether the source is currently available
            response_time_ms: Response time in milliseconds
            error_message: Error message if source failed
        """
        try:
            # Check if data source status record exists
            query = select(DataSourceStatus).where(DataSourceStatus.source_name == source_name)
            result = await self.db.execute(query)
            status_record = result.scalar_one_or_none()
            
            current_time = datetime.utcnow()
            
            if status_record:
                # Update existing record
                status_record.is_available = is_available
                status_record.updated_at = current_time
                
                if is_available:
                    status_record.last_successful_query = current_time
                    status_record.total_queries += 1
                    
                    # Update average response time
                    if response_time_ms is not None:
                        if status_record.average_response_time_ms:
                            # Calculate running average
                            status_record.average_response_time_ms = int(
                                (status_record.average_response_time_ms + response_time_ms) / 2
                            )
                        else:
                            status_record.average_response_time_ms = response_time_ms
                else:
                    status_record.error_count += 1
                    status_record.last_error = error_message
                    status_record.last_error_time = current_time
                
                # Calculate success rate
                if status_record.total_queries > 0:
                    success_count = status_record.total_queries - status_record.error_count
                    status_record.success_rate = (success_count / status_record.total_queries) * 100
            else:
                # Create new record
                status_record = DataSourceStatus(
                    source_name=source_name,
                    is_available=is_available,
                    last_successful_query=current_time if is_available else None,
                    last_error=error_message if not is_available else None,
                    last_error_time=current_time if not is_available else None,
                    average_response_time_ms=response_time_ms,
                    total_queries=1,
                    error_count=0 if is_available else 1,
                    success_rate=100.0 if is_available else 0.0
                )
                
                self.db.add(status_record)
            
            await self.db.commit()
            
            logger.debug(f"✅ Updated data source status: {source_name} (available: {is_available})")
            
        except Exception as e:
            logger.error(f"❌ Failed to update data source status for {source_name}: {e}")
            await self.db.rollback()
    
    async def get_search_history(
        self,
        limit: int = 100,
        user_ip: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get recent search history.
        
        Args:
            limit: Maximum number of queries to return
            user_ip: Optional IP filter for user-specific history
            
        Returns:
            List of search query dictionaries with metadata
        """
        try:
            query = select(SearchQuery).order_by(SearchQuery.created_at.desc())
            
            if user_ip:
                query = query.where(SearchQuery.user_ip == user_ip)
            
            query = query.limit(limit)
            
            result = await self.db.execute(query)
            queries = result.scalars().all()
            
            history = []
            for query_record in queries:
                history.append({
                    'id': query_record.id,
                    'query_text': query_record.query_text,
                    'year': query_record.year,
                    'jurisdiction': query_record.jurisdiction,
                    'total_results': query_record.total_results,
                    'sources_queried': query_record.sources_queried,
                    'execution_time_ms': query_record.execution_time_ms,
                    'created_at': query_record.created_at.isoformat()
                })
            
            return history
            
        except Exception as e:
            logger.error(f"❌ Failed to get search history: {e}")
            return []
    
    async def get_data_source_status(self) -> List[Dict[str, Any]]:
        """
        Get current status of all data sources.
        
        Returns:
            List of data source status dictionaries
        """
        try:
            query = select(DataSourceStatus).order_by(DataSourceStatus.source_name)
            result = await self.db.execute(query)
            status_records = result.scalars().all()
            
            status_list = []
            for record in status_records:
                status_list.append({
                    'source_name': record.source_name,
                    'is_available': record.is_available,
                    'last_successful_query': record.last_successful_query.isoformat() if record.last_successful_query else None,
                    'last_error': record.last_error,
                    'last_error_time': record.last_error_time.isoformat() if record.last_error_time else None,
                    'average_response_time_ms': record.average_response_time_ms,
                    'total_queries': record.total_queries,
                    'error_count': record.error_count,
                    'success_rate': record.success_rate,
                    'updated_at': record.updated_at.isoformat() if record.updated_at else None
                })
            
            return status_list
            
        except Exception as e:
            logger.error(f"❌ Failed to get data source status: {e}")
            return []
    
    async def get_search_analytics(
        self,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get search analytics for the specified time period.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Analytics dictionary with search statistics
        """
        try:
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Query search statistics
            query = select(
                func.count(SearchQuery.id).label('total_searches'),
                func.avg(SearchQuery.execution_time_ms).label('avg_execution_time'),
                func.sum(SearchQuery.total_results).label('total_results_found')
            ).where(
                SearchQuery.created_at >= start_date
            )
            
            result = await self.db.execute(query)
            stats = result.first()
            
            # Query top search terms
            top_queries_query = select(
                SearchQuery.query_text,
                func.count(SearchQuery.id).label('search_count')
            ).where(
                SearchQuery.created_at >= start_date
            ).group_by(
                SearchQuery.query_text
            ).order_by(
                func.count(SearchQuery.id).desc()
            ).limit(10)
            
            result = await self.db.execute(top_queries_query)
            top_queries = result.all()
            
            return {
                'period_days': days,
                'total_searches': stats.total_searches or 0,
                'avg_execution_time_ms': int(stats.avg_execution_time or 0),
                'total_results_found': stats.total_results_found or 0,
                'top_queries': [
                    {'query': query, 'count': count}
                    for query, count in top_queries
                ],
                'generated_at': end_date.isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get search analytics: {e}")
            return {
                'period_days': days,
                'total_searches': 0,
                'avg_execution_time_ms': 0,
                'total_results_found': 0,
                'top_queries': [],
                'generated_at': datetime.utcnow().isoformat()
            }