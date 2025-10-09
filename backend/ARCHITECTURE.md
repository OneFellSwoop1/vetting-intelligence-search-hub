# Backend Architecture Documentation

## Overview

The Vetting Intelligence Search Hub backend is a FastAPI application that aggregates data from multiple government data sources to provide comprehensive search capabilities for due diligence, compliance, and investigative research.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (React)                       │
└────────────────────────────┬────────────────────────────────┘
                             │ HTTP/WebSocket
┌────────────────────────────┴────────────────────────────────┐
│                      FastAPI Backend                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Routers    │  │  Middleware  │  │  WebSocket   │      │
│  │ - Search     │  │ - CORS       │  │  - Real-time │      │
│  │ - Auth       │  │ - Rate Limit │  │    Search    │      │
│  │ - Analytics  │  │ - Error      │  └──────────────┘      │
│  └──────┬───────┘  └──────────────┘                         │
│         │                                                     │
│  ┌──────┴───────────────────────────────────────┐          │
│  │              Service Layer                    │          │
│  │  - User Management (Database-backed)          │          │
│  │  - Search Orchestration                       │          │
│  │  - Cache Management (Redis)                   │          │
│  │  - Database Service                           │          │
│  └──────┬───────────────────────────────────────┘          │
│         │                                                     │
│  ┌──────┴───────────────────────────────────────┐          │
│  │              Adapter Layer                    │          │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐     │          │
│  │  │Checkbook │ │Senate LDA│ │NYS Ethics│     │          │
│  │  │(HTTP)    │ │(HTTP)    │ │(HTTP)    │     │          │
│  │  └──────────┘ └──────────┘ └──────────┘     │          │
│  └───────────────────────────────────────────────          │
└────────────────────────────────────────────────────────────┘
         │                    │                    │
    ┌────┴────┐          ┌───┴────┐          ┌───┴────┐
    │SQLite/  │          │ Redis  │          │External│
    │PostgreSQL│         │ Cache  │          │Gov APIs│
    └──────────┘          └────────┘          └────────┘
```

## Core Components

### 1. Routers (`app/routers/`)
Handle HTTP requests and route them to appropriate services.

#### **Search Router** (`search.py`)
- **POST /api/v1/search**: Multi-source parallel search
- **GET /api/v1/history**: Search history from database
- **GET /api/v1/data-sources/status**: Data source health monitoring
- **GET /api/v1/analytics/{query}**: Detailed search analytics

#### **Authentication Router** (`auth.py`)
- **POST /auth/register**: User registration with database persistence
- **POST /auth/login**: User authentication with JWT tokens
- **POST /auth/logout**: Token invalidation
- **GET /auth/profile**: User profile management

#### **Correlation Router** (`correlation.py`)
- **POST /api/v1/correlation**: Cross-jurisdictional analysis
- **GET /api/v1/correlation/{id}**: Retrieve correlation results

### 2. Adapters (`app/adapters/`)
Interface with external data sources using standardized BaseAdapter pattern.

#### **Base Adapter Architecture**
```python
class BaseAdapter(ABC):
    """Base class providing common functionality."""
    
    # Abstract methods (must implement)
    async def search(query, year) -> List[Dict]
    def _normalize_result(raw_data) -> Dict
    
    # Provided functionality
    def _parse_amount(amount) -> float
    def _parse_date(date) -> str
    def _deduplicate_results(results) -> List[Dict]
    async def _cached_search(query, year, search_func) -> List[Dict]
```

#### **Available Adapters**
- **CheckbookNYCAdapter**: NYC contracts and spending data
- **SenateHouseLDAAdapter**: Federal lobbying disclosures
- **NYSEthicsAdapter**: NY State lobbying records
- **NYCLobbyistAdapter**: NYC lobbying registrations

### 3. Services (`app/services/`)
Business logic layer providing specialized functionality.

#### **DatabaseService** (`database_service.py`)
- Search query persistence and analytics
- Search result storage and retrieval
- Data source status monitoring
- Performance metrics tracking

#### **CheckbookService** (`checkbook.py`)
- Specialized Checkbook NYC data processing
- Contract and spending analysis
- Vendor relationship mapping

### 4. Models (`app/models.py`)
SQLAlchemy ORM models for database persistence.

#### **Core Models**
- **User**: User accounts with authentication
- **SearchQuery**: Search history and metadata
- **SearchResult**: Individual search results
- **CorrelationAnalysis**: Cross-jurisdictional analysis results
- **DataSourceStatus**: Data source health monitoring
- **EntityProfile**: Consolidated entity information

### 5. Middleware (`app/middleware/`)
Request/response processing and security.

#### **IPRateLimitMiddleware** (`rate_limit.py`)
- IP-based rate limiting (60 requests/minute default)
- Redis-backed with in-memory fallback
- Configurable limits per endpoint
- Rate limit headers in responses

### 6. Configuration (`app/config.py`)
Centralized configuration management with Pydantic validation.

#### **Key Features**
- Type-safe configuration loading
- Environment variable validation
- Production readiness checks
- API key format validation
- Database URL validation

## Data Flow

### Search Request Flow

1. **Request arrives** at `/api/v1/search`
2. **Middleware processing**:
   - IP rate limiting check (60/min default)
   - CORS headers validation
3. **Authentication**: Extract and verify JWT token
4. **User rate limiting**: Check user tier limits
5. **Database logging**: Create SearchQuery record
6. **Cache check**: Look for cached results in Redis
7. **Parallel search** (if not cached):
   - Create tasks for each adapter
   - Execute with `asyncio.gather()` for parallelism
   - Handle timeouts and errors gracefully
8. **Result processing**:
   - Normalize all results to standard format
   - Deduplicate using BaseAdapter methods
   - Sort by relevance and priority
9. **Database persistence**: Save results and update metrics
10. **Cache storage**: Store in Redis (1-hour TTL)
11. **Response**: Return standardized JSON with analytics

### Authentication Flow

1. **User Registration**:
   - Validate input with Pydantic
   - Check for existing username/email in database
   - Hash password with bcrypt (12 rounds)
   - Save user to database
   - Generate JWT token with 24-hour expiration
   - Cache token in Redis for fast lookup

2. **User Login**:
   - Look up user in database by username
   - Verify password hash with bcrypt
   - Check account status (active/inactive)
   - Update last login timestamp
   - Generate new JWT token
   - Cache token in Redis

3. **Authenticated Request**:
   - Extract Bearer token from Authorization header
   - Check Redis cache for user_id (fast path)
   - If not cached, verify JWT signature
   - Load user profile from database
   - Attach UserProfile to request context

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(32) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'registered',
    rate_limit_tier VARCHAR(50) DEFAULT 'registered',
    is_active BOOLEAN DEFAULT TRUE,
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);

-- Indexes for performance
CREATE INDEX ix_users_email_active ON users(email, is_active);
CREATE INDEX ix_users_role_tier ON users(role, rate_limit_tier);
```

### Search Queries Table
```sql
CREATE TABLE search_queries (
    id SERIAL PRIMARY KEY,
    query_text VARCHAR(500) NOT NULL,
    year INTEGER,
    jurisdiction VARCHAR(100),
    user_ip VARCHAR(45),
    user_agent TEXT,
    total_results INTEGER DEFAULT 0,
    sources_queried JSONB,
    execution_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for analytics
CREATE INDEX ix_search_queries_text_date ON search_queries(query_text, created_at);
CREATE INDEX ix_search_queries_year_jurisdiction ON search_queries(year, jurisdiction);
```

### Search Results Table
```sql
CREATE TABLE search_results (
    id SERIAL PRIMARY KEY,
    query_id INTEGER REFERENCES search_queries(id),
    title VARCHAR(1000) NOT NULL,
    description TEXT,
    amount FLOAT,
    date VARCHAR(50),
    source VARCHAR(100) NOT NULL,
    vendor VARCHAR(500),
    agency VARCHAR(500),
    url TEXT,
    record_type VARCHAR(100),
    year VARCHAR(10),
    raw_data JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for search and analytics
CREATE INDEX ix_search_results_source_vendor ON search_results(source, vendor);
CREATE INDEX ix_search_results_amount_date ON search_results(amount, date);
```

## Caching Strategy

### Redis Cache Structure

1. **Search Results**: `search:{hash}` (1-hour TTL)
   - Complete search results with metadata
   - Keyed by query, year, jurisdiction hash

2. **User Tokens**: `token:{jwt}` (24-hour TTL)
   - JWT token to user_id mapping
   - Fast authentication lookup

3. **Rate Limits**: 
   - User: `rate_limit:{user_id}:{period}` (Dynamic TTL)
   - IP: `ip_rate_limit:{ip}:{minute}` (60-second TTL)

4. **Adapter Results**: `{adapter_name}:{query}:{year}` (1-hour TTL)
   - Individual adapter results
   - Reduces API calls to external services

### Cache Invalidation Strategy

- **Time-based expiration**: Most caches use TTL
- **Manual invalidation**: For data updates
- **Graceful degradation**: App works without cache

## Security Architecture

### Authentication & Authorization

1. **JWT Tokens**:
   - HS256 algorithm with 64+ character secret
   - 24-hour expiration (configurable)
   - Cached in Redis for performance
   - Automatic cleanup on expiration

2. **Password Security**:
   - bcrypt hashing with 12 rounds
   - Salt automatically generated
   - Timing attack protection
   - Strong password validation

3. **Rate Limiting**:
   - **IP-based**: 60 requests/minute (configurable)
   - **User-based**: Tier-dependent limits
   - **Redis-backed**: Distributed rate limiting
   - **Graceful fallback**: In-memory if Redis unavailable

### Input Validation & Sanitization

1. **Pydantic Models**: Type-safe request validation
2. **SQL Injection Protection**: SQLAlchemy parameterization
3. **XSS Prevention**: Output encoding (frontend responsibility)
4. **API Key Validation**: Format and strength checks

### Security Headers

- **Rate Limit Headers**: X-RateLimit-* headers
- **CORS Configuration**: Configurable allowed origins
- **Error Sanitization**: No sensitive data in error responses

## Performance Optimizations

### 1. Parallel Execution
- All adapters run concurrently with `asyncio.gather()`
- Non-blocking I/O for database and HTTP operations
- Timeout handling prevents hanging requests

### 2. Connection Pooling
- **HTTP Clients**: Managed connection pools per adapter
- **Database**: SQLAlchemy async connection pooling
- **Redis**: Connection pool for cache operations

### 3. Intelligent Caching
- **Multi-layer caching**: Redis + adapter-level caching
- **Cache warming**: Popular queries stay cached
- **Selective caching**: Only successful results cached

### 4. Database Optimization
- **Indexes**: Strategic indexes for common queries
- **Connection pooling**: Configurable pool sizes
- **Async operations**: Non-blocking database I/O

## Error Handling

### Error Classification

1. **User Errors (4xx)**:
   - Invalid input parameters
   - Authentication failures
   - Rate limit exceeded
   - Resource not found

2. **Server Errors (5xx)**:
   - Database connection failures
   - External API timeouts
   - Internal processing errors
   - Configuration issues

### Error Response Format
```json
{
    "status": "error",
    "message": "Human-readable error message",
    "error_code": "SPECIFIC_ERROR_CODE",
    "timestamp": "2024-01-01T10:00:00Z",
    "request_id": "unique-request-identifier"
}
```

### Error Handling Strategy

1. **Graceful Degradation**: Partial results if some sources fail
2. **Comprehensive Logging**: All errors logged with context
3. **User-Friendly Messages**: No technical details exposed
4. **Automatic Recovery**: Retry logic for transient failures

## Monitoring & Observability

### Health Checks

- **GET /health**: Comprehensive system status
  - Database connectivity
  - Redis availability
  - External API status
  - Memory and CPU usage

- **GET /**: Basic health check for load balancers

### Performance Metrics

1. **Request Metrics**:
   - Response times per endpoint
   - Request counts and rates
   - Error rates and types

2. **Data Source Metrics**:
   - API response times
   - Success/failure rates
   - Availability status

3. **Cache Metrics**:
   - Hit/miss rates
   - Cache size and memory usage
   - Eviction rates

### Logging Strategy

- **Structured Logging**: JSON format for parsing
- **Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Context**: Request IDs, user IDs, IP addresses
- **Security Events**: Authentication, rate limiting, errors

## Development Workflow

### Setup Process

1. **Environment Setup**:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configuration**:
   ```bash
   cp env.example environment.env
   # Edit environment.env with your API keys
   ```

3. **Database Setup**:
   ```bash
   # Creates SQLite database automatically
   python -c "from app.database import engine, Base; from app.models import *; Base.metadata.create_all(bind=engine)"
   ```

4. **Testing**:
   ```bash
   pytest --cov=app --cov-report=html
   ```

5. **Development Server**:
   ```bash
   python start_server.py
   ```

### Code Standards

1. **Type Hints**: All functions have type annotations
2. **Docstrings**: Comprehensive documentation for all public methods
3. **Error Handling**: All exceptions caught and handled appropriately
4. **Logging**: Appropriate log levels and context
5. **Testing**: Unit tests for all new functionality

## Deployment Architecture

### Production Deployment

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │    │   Application   │    │    Database     │
│   (Nginx/HAProxy)│◄──►│   (FastAPI)     │◄──►│  (PostgreSQL)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                       ┌─────────────────┐
                       │      Cache      │
                       │     (Redis)     │
                       └─────────────────┘
```

### Environment Configuration

#### **Development**
- SQLite database (automatic)
- In-memory fallbacks for Redis
- Debug logging enabled
- CORS allows localhost origins

#### **Production**
- PostgreSQL database (required)
- Redis cluster for caching
- WARNING level logging
- Strict CORS configuration
- SSL/TLS termination at load balancer

### Scaling Considerations

1. **Horizontal Scaling**:
   - Stateless application design
   - Redis for shared state
   - Database connection pooling

2. **Performance Tuning**:
   - Connection pool sizing
   - Cache TTL optimization
   - Rate limit adjustment

3. **Monitoring**:
   - Application metrics
   - Database performance
   - Cache hit rates
   - External API health

## Security Considerations

### Production Security Checklist

- [ ] Strong JWT_SECRET_KEY (64+ characters)
- [ ] PostgreSQL with encrypted connections
- [ ] Redis with authentication
- [ ] HTTPS termination at load balancer
- [ ] Rate limiting configured appropriately
- [ ] CORS origins restricted to production domains
- [ ] Debug mode disabled
- [ ] Sensitive data not logged
- [ ] Regular security updates
- [ ] Database backups configured

### API Security

1. **Authentication**: JWT tokens with proper expiration
2. **Authorization**: Role-based access control
3. **Rate Limiting**: Multiple layers (IP + user)
4. **Input Validation**: Pydantic models for all inputs
5. **Output Sanitization**: No sensitive data in responses

## Troubleshooting Guide

### Common Issues

#### **Database Connection Errors**
```
ERROR: Multiple exceptions: [Errno 61] Connect call failed
```
**Solution**: 
- Check DATABASE_URL in environment.env
- Verify PostgreSQL is running
- App will fallback to SQLite automatically

#### **Redis Connection Issues**
```
WARNING: Redis cache not available
```
**Solution**:
- Check REDIS_URL in environment.env
- Verify Redis is running
- App continues without cache (degraded performance)

#### **JWT Token Errors**
```
ERROR: JWT_SECRET_KEY environment variable not set!
```
**Solution**:
- Add JWT_SECRET_KEY to environment.env
- Generate with: `python -c 'import secrets; print(secrets.token_urlsafe(64))'`

#### **Rate Limit Issues**
```
HTTP 429: Rate limit exceeded
```
**Solution**:
- Check IP_RATE_LIMIT_PER_MINUTE setting
- Verify Redis is working for distributed rate limiting
- Check user tier rate limits

### Performance Issues

#### **Slow Search Responses**
1. Check external API response times
2. Verify Redis cache is working
3. Check database query performance
4. Monitor connection pool usage

#### **High Memory Usage**
1. Check cache size and TTL settings
2. Monitor database connection pools
3. Check for memory leaks in adapters

## API Reference

### Search API

#### **POST /api/v1/search**

**Request:**
```json
{
    "query": "Microsoft Corporation",
    "year": 2024,
    "jurisdiction": "all"
}
```

**Response:**
```json
{
    "status": "success",
    "message": "Search completed for 'Microsoft Corporation'",
    "data": {
        "total_hits": {
            "checkbook": 15,
            "senate_lda": 8,
            "nys_ethics": 0,
            "nyc_lobbyist": 2
        },
        "results": [
            {
                "source": "checkbook",
                "title": "NYC Contract: Microsoft Corporation",
                "vendor": "Microsoft Corporation",
                "agency": "Department of Information Technology",
                "amount": 500000.0,
                "date": "2024-01-15",
                "description": "Cloud services contract",
                "url": "https://checkbooknyc.com/...",
                "raw_data": {...}
            }
        ],
        "search_stats": {
            "total_results": 25,
            "execution_time_ms": 1250,
            "cache_hit": false
        }
    }
}
```

### Authentication API

#### **POST /auth/register**

**Request:**
```json
{
    "username": "newuser",
    "email": "user@example.com",
    "password": "secure_password_123"
}
```

**Response:**
```json
{
    "success": true,
    "message": "User registered successfully",
    "data": {
        "user_id": "abc123def456",
        "username": "newuser",
        "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "expires_in": 86400,
        "role": "registered",
        "rate_limit_tier": "registered"
    }
}
```

## Development Guidelines

### Adding New Adapters

1. **Inherit from BaseAdapter or HTTPAdapter**
2. **Implement required abstract methods**
3. **Use base class utilities** (_parse_amount, _parse_date, etc.)
4. **Add comprehensive error handling**
5. **Include unit tests**
6. **Update router to include new adapter**

### Adding New Endpoints

1. **Create Pydantic request/response models**
2. **Add proper authentication dependencies**
3. **Include comprehensive docstrings**
4. **Add error handling**
5. **Include unit and integration tests**
6. **Update API documentation**

### Database Changes

1. **Create migration scripts** (if using Alembic)
2. **Update models.py** with new tables/fields
3. **Add database service methods** if needed
4. **Update tests** to cover new functionality
5. **Test migration** on development database

---

*This architecture supports enterprise-scale government transparency research with high performance, security, and reliability.*
