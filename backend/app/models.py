"""Database models for the Vetting Intelligence Search Hub."""

from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import Column, Integer, String, DateTime, Float, Text, JSON, Boolean, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from .database import Base


class SearchQuery(Base):
    """Model for storing search queries and metadata."""
    
    __tablename__ = "search_queries"
    
    id = Column(Integer, primary_key=True, index=True)
    query_text = Column(String(500), nullable=False, index=True)
    year = Column(Integer, nullable=True, index=True)
    jurisdiction = Column(String(100), nullable=True, index=True)
    user_ip = Column(String(45), nullable=True)  # Support IPv6
    user_agent = Column(Text, nullable=True)
    
    # Results metadata
    total_results = Column(Integer, default=0)
    total_amount = Column(Float, default=0.0)
    sources_queried = Column(JSON, nullable=True)  # List of data sources
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    execution_time_ms = Column(Integer, nullable=True)  # Query execution time
    
    # Relationships
    results = relationship("SearchResult", back_populates="query", cascade="all, delete-orphan")
    correlations = relationship("CorrelationAnalysis", back_populates="query", cascade="all, delete-orphan")

    # Indexes for performance
    __table_args__ = (
        Index("ix_search_queries_text_date", "query_text", "created_at"),
        Index("ix_search_queries_year_jurisdiction", "year", "jurisdiction"),
    )


class SearchResult(Base):
    """Model for storing individual search results."""
    
    __tablename__ = "search_results"
    
    id = Column(Integer, primary_key=True, index=True)
    query_id = Column(Integer, ForeignKey("search_queries.id"), nullable=False, index=True)
    
    # Core result data
    title = Column(String(1000), nullable=False)
    description = Column(Text, nullable=True)
    amount = Column(Float, nullable=True, index=True)
    date = Column(String(50), nullable=True)  # Store as string since formats vary
    source = Column(String(100), nullable=False, index=True)
    vendor = Column(String(500), nullable=True, index=True)
    agency = Column(String(500), nullable=True, index=True)
    url = Column(Text, nullable=True)
    record_type = Column(String(100), nullable=True, index=True)
    year = Column(String(10), nullable=True, index=True)
    
    # Additional metadata as JSON
    raw_data = Column(JSON, nullable=True)  # Store original API response
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    query = relationship("SearchQuery", back_populates="results")

    # Indexes for performance
    __table_args__ = (
        Index("ix_search_results_source_vendor", "source", "vendor"),
        Index("ix_search_results_amount_date", "amount", "date"),
        Index("ix_search_results_agency_type", "agency", "record_type"),
    )


class CorrelationAnalysis(Base):
    """Model for storing correlation analysis results."""
    
    __tablename__ = "correlation_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    query_id = Column(Integer, ForeignKey("search_queries.id"), nullable=False, index=True)
    
    # Analysis metadata
    analysis_type = Column(String(100), nullable=False)  # 'enhanced', 'basic', etc.
    entity_count = Column(Integer, default=0)
    correlation_count = Column(Integer, default=0)
    
    # Analysis results as JSON
    correlations = Column(JSON, nullable=True)  # Correlation pairs and scores
    insights = Column(JSON, nullable=True)     # Generated insights
    patterns = Column(JSON, nullable=True)     # Detected patterns
    anomalies = Column(JSON, nullable=True)    # Detected anomalies
    
    # Performance metrics
    execution_time_ms = Column(Integer, nullable=True)
    memory_usage_mb = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    query = relationship("SearchQuery", back_populates="correlations")

    # Indexes
    __table_args__ = (
        Index("ix_correlation_analyses_type_date", "analysis_type", "created_at"),
    )


class SavedSearch(Base):
    """Model for user-saved searches and alerts."""
    
    __tablename__ = "saved_searches"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # Search parameters
    query_text = Column(String(500), nullable=False)
    year = Column(Integer, nullable=True)
    jurisdiction = Column(String(100), nullable=True)
    
    # Alert settings
    is_alert_enabled = Column(Boolean, default=False)
    alert_frequency = Column(String(50), nullable=True)  # 'daily', 'weekly', 'monthly'
    last_alert_sent = Column(DateTime(timezone=True), nullable=True)
    
    # User identification (simple IP-based for now)
    user_ip = Column(String(45), nullable=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Indexes
    __table_args__ = (
        Index("ix_saved_searches_user_alerts", "user_ip", "is_alert_enabled"),
        Index("ix_saved_searches_query_text", "query_text"),
    )


class DataSourceStatus(Base):
    """Model for tracking data source health and performance."""
    
    __tablename__ = "data_source_status"
    
    id = Column(Integer, primary_key=True, index=True)
    source_name = Column(String(100), nullable=False, index=True, unique=True)
    
    # Status information
    is_available = Column(Boolean, default=True)
    last_successful_query = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(Text, nullable=True)
    last_error_time = Column(DateTime(timezone=True), nullable=True)
    
    # Performance metrics
    average_response_time_ms = Column(Integer, nullable=True)
    total_queries = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    success_rate = Column(Float, nullable=True)  # Percentage
    
    # Rate limiting info
    rate_limit_per_minute = Column(Integer, nullable=True)
    current_usage = Column(Integer, default=0)
    reset_time = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class ApiUsageLog(Base):
    """Model for logging API usage and performance."""
    
    __tablename__ = "api_usage_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Request information
    endpoint = Column(String(200), nullable=False, index=True)
    method = Column(String(10), nullable=False)
    user_ip = Column(String(45), nullable=True, index=True)
    user_agent = Column(Text, nullable=True)
    
    # Request parameters
    query_params = Column(JSON, nullable=True)
    request_body = Column(JSON, nullable=True)
    
    # Response information
    status_code = Column(Integer, nullable=False, index=True)
    response_time_ms = Column(Integer, nullable=True)
    response_size_bytes = Column(Integer, nullable=True)
    
    # Error information
    error_message = Column(Text, nullable=True)
    error_type = Column(String(100), nullable=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Indexes for performance monitoring
    __table_args__ = (
        Index("ix_api_usage_logs_endpoint_status", "endpoint", "status_code"),
        Index("ix_api_usage_logs_user_date", "user_ip", "created_at"),
        Index("ix_api_usage_logs_response_time", "response_time_ms"),
    )


class EntityProfile(Base):
    """Model for storing consolidated entity profiles across data sources."""
    
    __tablename__ = "entity_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Entity identification
    entity_name = Column(String(500), nullable=False, index=True)
    entity_type = Column(String(100), nullable=True, index=True)  # 'company', 'individual', 'organization'
    canonical_name = Column(String(500), nullable=True, index=True)  # Normalized name
    
    # Aggregate statistics
    total_contracts = Column(Integer, default=0)
    total_lobbying_records = Column(Integer, default=0)
    total_amount = Column(Float, default=0.0, index=True)
    first_seen_date = Column(DateTime(timezone=True), nullable=True)
    last_seen_date = Column(DateTime(timezone=True), nullable=True)
    
    # Data sources where this entity appears
    sources = Column(JSON, nullable=True)  # List of sources with record counts
    
    # Risk assessment
    risk_score = Column(Float, nullable=True, index=True)  # 0-100 risk score
    risk_factors = Column(JSON, nullable=True)  # List of risk factors
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Indexes
    __table_args__ = (
        Index("ix_entity_profiles_name_type", "entity_name", "entity_type"),
        Index("ix_entity_profiles_amount_risk", "total_amount", "risk_score"),
    ) 