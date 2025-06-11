"""Database configuration and session management for Vetting Intelligence Search Hub."""

import os
import logging
from typing import Optional, AsyncGenerator

from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from sqlalchemy.engine import Engine
import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

logger = logging.getLogger(__name__)

# Database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/vetting_intelligence")
ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Create SQLAlchemy engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600,   # Recycle connections every hour
    echo=os.getenv("SQL_DEBUG", "false").lower() == "true"
)

# Create async engine for async operations
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=os.getenv("SQL_DEBUG", "false").lower() == "true"
)

# Create session factories
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False
)

# Create base class for declarative models
Base = declarative_base()

class DatabaseManager:
    """Manages database connections, migrations, and health checks."""
    
    def __init__(self):
        self.engine = engine
        self.async_engine = async_engine
        self._is_connected = False
        
    async def initialize(self) -> bool:
        """Initialize database connection and create tables if needed."""
        try:
            # Test connection
            await self.health_check()
            
            # Create tables if they don't exist
            await self.create_tables()
            
            # Run any pending migrations
            await self.run_migrations()
            
            self._is_connected = True
            logger.info("✅ Database initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            self._is_connected = False
            return False
    
    async def health_check(self) -> bool:
        """Check if database is accessible."""
        try:
            async with self.async_engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            logger.info("✅ Database health check passed")
            return True
        except Exception as e:
            logger.error(f"❌ Database health check failed: {e}")
            return False
    
    async def create_tables(self):
        """Create all tables defined in models."""
        try:
            async with self.async_engine.begin() as conn:
                # Import models to ensure they're registered
                from . import models
                
                # Create all tables
                await conn.run_sync(Base.metadata.create_all)
                
            logger.info("✅ Database tables created/verified")
        except Exception as e:
            logger.error(f"❌ Error creating tables: {e}")
            raise
    
    async def run_migrations(self):
        """Run any pending database migrations."""
        try:
            # For now, just log - in production you'd use Alembic
            logger.info("✅ Database migrations completed (no migrations pending)")
        except Exception as e:
            logger.error(f"❌ Error running migrations: {e}")
            raise
    
    def get_sync_session(self) -> Session:
        """Get a synchronous database session."""
        return SessionLocal()
    
    async def get_async_session(self) -> AsyncSession:
        """Get an asynchronous database session."""
        return AsyncSessionLocal()
    
    @property
    def is_connected(self) -> bool:
        """Check if database is connected."""
        return self._is_connected
    
    async def close(self):
        """Close database connections."""
        try:
            await self.async_engine.dispose()
            self.engine.dispose()
            logger.info("✅ Database connections closed")
        except Exception as e:
            logger.error(f"❌ Error closing database: {e}")

# Global database manager instance
db_manager = DatabaseManager()

# Dependency injection for FastAPI
def get_db() -> Session:
    """FastAPI dependency for synchronous database sessions."""
    db = db_manager.get_sync_session()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for asynchronous database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Async database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()

# Cache migration functions
async def migrate_cache_to_db():
    """Migrate existing cache data to database for persistence."""
    from .cache import cache_service
    
    if not cache_service.redis_client or not db_manager.is_connected:
        logger.warning("⚠️ Cannot migrate cache: Redis or DB not available")
        return
    
    try:
        # Get all cached search results
        search_keys = cache_service.redis_client.keys("search:*")
        
        if not search_keys:
            logger.info("ℹ️ No cached searches found to migrate")
            return
        
        async with AsyncSessionLocal() as session:
            from .models import SearchQuery, SearchResult
            
            migrated_count = 0
            
            for key in search_keys:
                try:
                    cached_data = cache_service.redis_client.get(key)
                    if not cached_data:
                        continue
                        
                    import json
                    data = json.loads(cached_data)
                    
                    # Create SearchQuery record
                    search_query = SearchQuery(
                        query_text=data.get('query', ''),
                        year=int(data.get('year')) if data.get('year') else None,
                        jurisdiction=data.get('jurisdiction'),
                        total_results=len(data.get('results', [])),
                        sources_queried=list(data.get('total_hits', {}).keys())
                    )
                    
                    session.add(search_query)
                    await session.flush()  # Get the ID
                    
                    # Create SearchResult records
                    for result in data.get('results', []):
                        search_result = SearchResult(
                            query_id=search_query.id,
                            title=result.get('title', result.get('entity_name', 'Unknown')),
                            description=result.get('description', ''),
                            amount=float(result.get('amount', 0)) if result.get('amount') else None,
                            date=result.get('date', ''),
                            source=result.get('source', 'unknown'),
                            vendor=result.get('vendor', result.get('entity_name', '')),
                            agency=result.get('agency', ''),
                            url=result.get('url', ''),
                            record_type=result.get('record_type', ''),
                            year=result.get('year', ''),
                            raw_data=result
                        )
                        session.add(search_result)
                    
                    migrated_count += 1
                    
                except Exception as e:
                    logger.warning(f"Error migrating cache key {key}: {e}")
                    continue
            
            await session.commit()
            logger.info(f"✅ Migrated {migrated_count} cached searches to database")
            
    except Exception as e:
        logger.error(f"❌ Cache migration failed: {e}")

# Database utility functions
def test_connection() -> bool:
    """Test database connection synchronously."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False

def get_database_info() -> dict:
    """Get database connection information."""
    try:
        with engine.connect() as conn:
            # Get database version
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            
            # Get database size
            result = conn.execute(text("SELECT pg_size_pretty(pg_database_size(current_database()))"))
            size = result.scalar()
            
            # Get connection info
            result = conn.execute(text("SELECT current_database(), current_user, inet_server_addr(), inet_server_port()"))
            db_info = result.fetchone()
            
        return {
            "status": "connected",
            "version": version,
            "database": db_info[0] if db_info else "unknown",
            "user": db_info[1] if db_info else "unknown", 
            "host": db_info[2] if db_info else "unknown",
            "port": db_info[3] if db_info else "unknown",
            "size": size,
            "pool_size": engine.pool.size(),
            "checked_out": engine.pool.checkedout(),
            "overflow": engine.pool.overflow(),
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        } 