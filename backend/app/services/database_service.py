"""Database service layer for CRUD operations."""

import time
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_, or_
from sqlalchemy.orm import selectinload

from ..models import (
    SearchQuery, SearchResult, CorrelationAnalysis, 
    SavedSearch, DataSourceStatus, ApiUsageLog, EntityProfile
)
from ..schemas import SearchRequest, SearchResponse


class DatabaseService:
    """Service for database operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_search_query(
        self, 
        request: SearchRequest, 
        user_ip: str = None, 
        user_agent: str = None
    ) -> SearchQuery:
        """Create a new search query record."""
        query = SearchQuery(
            query_text=request.query,
            year=request.year,
            jurisdiction=request.jurisdiction,
            user_ip=user_ip,
            user_agent=user_agent
        )
        self.session.add(query)
        await self.session.commit()
        await self.session.refresh(query)
        return query

    async def update_search_query_results(
        self, 
        query_id: int, 
        response: SearchResponse, 
        execution_time_ms: int
    ) -> SearchQuery:
        """Update search query with results metadata."""
        query = await self.session.get(SearchQuery, query_id)
        if query:
            query.total_results = response.total_results
            query.total_amount = response.analytics.financial_analysis.total_amount if response.analytics else 0.0
            query.sources_queried = list(response.results_by_source.keys()) if response.results_by_source else []
            query.execution_time_ms = execution_time_ms
            await self.session.commit()
            await self.session.refresh(query)
        return query

    async def create_search_results(
        self, 
        query_id: int, 
        results: List[Dict[str, Any]]
    ) -> List[SearchResult]:
        """Create search result records."""
        search_results = []
        for result_data in results:
            result = SearchResult(
                query_id=query_id,
                title=result_data.get("title", "")[:1000],  # Truncate if too long
                description=result_data.get("description", ""),
                amount=result_data.get("amount"),
                date=str(result_data.get("date", "")),
                source=result_data.get("source", ""),
                vendor=result_data.get("vendor", ""),
                agency=result_data.get("agency", ""),
                url=result_data.get("url", ""),
                record_type=result_data.get("record_type", ""),
                year=str(result_data.get("year", "")),
                raw_data=result_data
            )
            search_results.append(result)
            self.session.add(result)
        
        await self.session.commit()
        return search_results

    async def create_correlation_analysis(
        self, 
        query_id: int, 
        analysis_type: str,
        correlations: Dict[str, Any],
        execution_time_ms: int = None,
        memory_usage_mb: float = None
    ) -> CorrelationAnalysis:
        """Create correlation analysis record."""
        analysis = CorrelationAnalysis(
            query_id=query_id,
            analysis_type=analysis_type,
            entity_count=correlations.get("entity_count", 0),
            correlation_count=correlations.get("correlation_count", 0),
            correlations=correlations.get("correlations"),
            insights=correlations.get("insights"),
            patterns=correlations.get("patterns"),
            anomalies=correlations.get("anomalies"),
            execution_time_ms=execution_time_ms,
            memory_usage_mb=memory_usage_mb
        )
        self.session.add(analysis)
        await self.session.commit()
        await self.session.refresh(analysis)
        return analysis

    async def get_search_history(
        self, 
        user_ip: str = None, 
        limit: int = 50,
        offset: int = 0
    ) -> List[SearchQuery]:
        """Get search history for a user or globally."""
        query = select(SearchQuery).order_by(desc(SearchQuery.created_at))
        
        if user_ip:
            query = query.where(SearchQuery.user_ip == user_ip)
        
        query = query.offset(offset).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_popular_searches(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most popular search queries."""
        query = (
            select(
                SearchQuery.query_text,
                func.count(SearchQuery.id).label("search_count"),
                func.avg(SearchQuery.total_results).label("avg_results"),
                func.max(SearchQuery.created_at).label("last_searched")
            )
            .group_by(SearchQuery.query_text)
            .order_by(desc("search_count"))
            .limit(limit)
        )
        
        result = await self.session.execute(query)
        return [
            {
                "query": row.query_text,
                "count": row.search_count,
                "avg_results": row.avg_results,
                "last_searched": row.last_searched
            }
            for row in result
        ]

    async def get_search_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get search analytics for the specified period."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Total searches
        total_query = select(func.count(SearchQuery.id)).where(
            SearchQuery.created_at >= cutoff_date
        )
        total_searches = await self.session.scalar(total_query)
        
        # Average results per search
        avg_query = select(func.avg(SearchQuery.total_results)).where(
            SearchQuery.created_at >= cutoff_date
        )
        avg_results = await self.session.scalar(avg_query)
        
        # Top sources
        source_query = (
            select(
                SearchResult.source,
                func.count(SearchResult.id).label("count")
            )
            .join(SearchQuery)
            .where(SearchQuery.created_at >= cutoff_date)
            .group_by(SearchResult.source)
            .order_by(desc("count"))
            .limit(10)
        )
        source_result = await self.session.execute(source_query)
        top_sources = [{"source": row.source, "count": row.count} for row in source_result]
        
        return {
            "period_days": days,
            "total_searches": total_searches or 0,
            "average_results_per_search": round(avg_results or 0, 2),
            "top_sources": top_sources
        }

    async def save_search(
        self, 
        name: str, 
        query_text: str, 
        year: int = None, 
        jurisdiction: str = None,
        user_ip: str = None,
        description: str = None
    ) -> SavedSearch:
        """Save a search for later use."""
        saved_search = SavedSearch(
            name=name,
            description=description,
            query_text=query_text,
            year=year,
            jurisdiction=jurisdiction,
            user_ip=user_ip
        )
        self.session.add(saved_search)
        await self.session.commit()
        await self.session.refresh(saved_search)
        return saved_search

    async def get_saved_searches(self, user_ip: str) -> List[SavedSearch]:
        """Get saved searches for a user."""
        query = select(SavedSearch).where(
            SavedSearch.user_ip == user_ip
        ).order_by(desc(SavedSearch.created_at))
        
        result = await self.session.execute(query)
        return result.scalars().all()

    async def log_api_usage(
        self,
        endpoint: str,
        method: str,
        user_ip: str = None,
        user_agent: str = None,
        query_params: Dict = None,
        request_body: Dict = None,
        status_code: int = None,
        response_time_ms: int = None,
        response_size_bytes: int = None,
        error_message: str = None,
        error_type: str = None
    ) -> ApiUsageLog:
        """Log API usage for monitoring."""
        log_entry = ApiUsageLog(
            endpoint=endpoint,
            method=method,
            user_ip=user_ip,
            user_agent=user_agent,
            query_params=query_params,
            request_body=request_body,
            status_code=status_code,
            response_time_ms=response_time_ms,
            response_size_bytes=response_size_bytes,
            error_message=error_message,
            error_type=error_type
        )
        self.session.add(log_entry)
        await self.session.commit()
        return log_entry

    async def update_data_source_status(
        self,
        source_name: str,
        is_available: bool = True,
        response_time_ms: int = None,
        error_message: str = None
    ) -> DataSourceStatus:
        """Update data source status."""
        # Try to get existing record
        query = select(DataSourceStatus).where(DataSourceStatus.source_name == source_name)
        result = await self.session.execute(query)
        status = result.scalar_one_or_none()
        
        if not status:
            # Create new record
            status = DataSourceStatus(source_name=source_name)
            self.session.add(status)
        
        # Update status
        status.is_available = is_available
        status.total_queries += 1
        
        if is_available:
            status.last_successful_query = datetime.utcnow()
            if response_time_ms:
                # Update rolling average
                if status.average_response_time_ms:
                    status.average_response_time_ms = (
                        status.average_response_time_ms + response_time_ms
                    ) // 2
                else:
                    status.average_response_time_ms = response_time_ms
        else:
            status.error_count += 1
            status.last_error = error_message
            status.last_error_time = datetime.utcnow()
        
        # Calculate success rate
        status.success_rate = (
            (status.total_queries - status.error_count) / status.total_queries * 100
        ) if status.total_queries > 0 else 100.0
        
        await self.session.commit()
        await self.session.refresh(status)
        return status

    async def get_data_source_status(self) -> List[DataSourceStatus]:
        """Get status of all data sources."""
        query = select(DataSourceStatus).order_by(DataSourceStatus.source_name)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def create_or_update_entity_profile(
        self,
        entity_name: str,
        entity_type: str = None,
        source: str = None,
        amount: float = None,
        record_date: datetime = None
    ) -> EntityProfile:
        """Create or update entity profile with aggregated data."""
        # Try to find existing profile
        query = select(EntityProfile).where(EntityProfile.entity_name == entity_name)
        result = await self.session.execute(query)
        profile = result.scalar_one_or_none()
        
        if not profile:
            # Create new profile
            profile = EntityProfile(
                entity_name=entity_name,
                entity_type=entity_type,
                canonical_name=entity_name.strip().title(),
                sources={}
            )
            self.session.add(profile)
        
        # Update aggregated data
        if source:
            sources = profile.sources or {}
            sources[source] = sources.get(source, 0) + 1
            profile.sources = sources
        
        if amount:
            profile.total_amount = (profile.total_amount or 0) + amount
        
        if record_date:
            if not profile.first_seen_date or record_date < profile.first_seen_date:
                profile.first_seen_date = record_date
            if not profile.last_seen_date or record_date > profile.last_seen_date:
                profile.last_seen_date = record_date
        
        await self.session.commit()
        await self.session.refresh(profile)
        return profile

    async def search_entities(
        self, 
        query: str, 
        limit: int = 20
    ) -> List[EntityProfile]:
        """Search entity profiles by name."""
        search_query = select(EntityProfile).where(
            or_(
                EntityProfile.entity_name.ilike(f"%{query}%"),
                EntityProfile.canonical_name.ilike(f"%{query}%")
            )
        ).order_by(desc(EntityProfile.total_amount)).limit(limit)
        
        result = await self.session.execute(search_query)
        return result.scalars().all() 