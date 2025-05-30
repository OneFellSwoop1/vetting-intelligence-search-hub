# Vetting Intelligence Search Hub

A production-ready web application to search and harmonise results from multiple government data sources for compliance, due diligence, and investigative research.

## Features

### Data Sources (6 Implemented)
- ✅ **NYC Checkbook** – spending, contracts & payroll via official API
- ✅ **Doing Business with NYC (DBNYC)** – campaign-finance database via respectful scraping
- ✅ **NYS Commission on Ethics & Lobbying** – lobbying & financial disclosure via scraping
- ✅ **U.S. Senate LDA API** – federal lobbying registrations & reports via REST API
- ✅ **U.S. House Lobbying Disclosures** – House lobbying data via JSON/XML feeds
- ✅ **NYC Lobbyist Search** – city lobbying filings via scraping/reverse-engineering

### Technical Features
- **FastAPI backend** with async/await for non-blocking parallel searches
- **React + Tailwind CSS frontend** with tabbed views and modern UI
- **Redis caching** with 24-hour TTL to avoid hammering public servers
- **Respectful rate limiting** for scraped sources (1-2s delays, proper User-Agent)
- **CSV download** functionality for results export
- **Jurisdiction filtering** (NYC/NYS/Federal)
- **Deep-linking** to original government records
- **Comprehensive error handling** and logging
- **Docker containerization** with Redis included
- **Production-ready** with CORS, health checks, and monitoring endpoints

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ (for local frontend development)
- Python 3.12+ (for local backend development)

### Environment Setup
1. Copy the environment template:
   ```bash
   cp env.example .env
   ```

2. **Required:** Set your Senate LDA API key in `.env`:
   ```bash
   LDA_API_KEY=your_senate_lda_api_key_here
   ```

3. Optionally customize other settings in `.env` (Redis URL, rate limits, etc.)

### Run with Docker (Recommended)
```bash
git clone <repo-url>
cd vetting-intelligence-search-hub
docker compose up --build
```

The application will be available at:
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs

### Local Development

#### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Usage

### Basic Search
1. Enter a **name, company, or keyword** in the search box
2. Optionally filter by **year** and **jurisdiction** (NYC/NYS/Federal)
3. Click **Search** to query all 6 data sources in parallel
4. Results are displayed with **tabbed views** by data source
5. **Download CSV** of results or view **original records**

### API Usage
```bash
# Search all sources
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "Smith", "year": "2024", "jurisdiction": "NYC"}'

# Health check
curl http://localhost:8000/health

# Cache statistics
curl http://localhost:8000/cache/stats
```

## Project Structure

```
vetting-intelligence-search-hub/
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── adapters/       # Data source adapters
│   │   │   ├── checkbook.py      # NYC Checkbook API
│   │   │   ├── dbnyc.py          # Doing Business NYC scraper
│   │   │   ├── nys_ethics.py     # NYS Ethics scraper
│   │   │   ├── senate_lda.py     # Senate LDA API
│   │   │   ├── house_lda.py      # House LDA JSON/XML
│   │   │   └── nyc_lobbyist.py   # NYC Lobbyist scraper
│   │   ├── routers/        # API endpoints
│   │   ├── cache.py        # Redis caching service
│   │   ├── schemas.py      # Pydantic models
│   │   └── main.py         # FastAPI app
│   ├── tests/              # Comprehensive test suite
│   ├── requirements.txt    # Python dependencies
│   └── Dockerfile
├── frontend/               # Next.js React application
│   ├── pages/
│   │   └── index.js        # Main search interface
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml      # Full stack with Redis
├── env.example            # Environment variables template
└── README.md
```

## Data Sources Details

### Official APIs
- **NYC Checkbook:** Uses official XML/JSON feeds from checkbooknyc.com
- **Senate LDA:** REST API v1 with authentication (requires API key)

### Respectful Scraping
- **Rate limited:** 1-2 second delays between requests
- **Proper headers:** Rotating User-Agent strings
- **Error handling:** Graceful degradation if sources are unavailable
- **Caching:** 24-hour Redis cache to minimize server load

## Testing

### Run Test Suite
```bash
cd backend
pytest tests/ -v
```

### Test Coverage
- Unit tests for individual adapters
- Integration tests for parallel search
- Cache functionality tests  
- API endpoint validation
- Error handling and edge cases

### Manual Testing
```bash
# Test individual data sources
curl -X POST http://localhost:8000/search -d '{"query":"Microsoft","jurisdiction":"Federal"}'

# Test caching
curl http://localhost:8000/cache/stats

# Clear cache
curl -X POST http://localhost:8000/cache/clear
```

## Performance & Monitoring

### Caching Strategy
- **Redis-based** with 24-hour TTL
- **Automatic cache key generation** based on query parameters
- **Graceful fallback** when Redis unavailable
- **Cache statistics** endpoint for monitoring

### Rate Limiting
- **Configurable delays** per data source
- **Respectful scraping** practices
- **Concurrent request limits**
- **Timeout handling** (30s default)

### Health Checks
- **Basic health:** `GET /`
- **Detailed health:** `GET /health` (includes cache status)
- **Cache monitoring:** `GET /cache/stats`

## Environment Variables

See `env.example` for complete configuration options:

| Variable | Required | Description |
|----------|----------|-------------|
| `LDA_API_KEY` | **Yes** | U.S. Senate LDA API key |
| `REDIS_URL` | No | Redis connection URL (default: redis://localhost:6379/0) |
| `LOG_LEVEL` | No | Logging level (default: INFO) |
| `CORS_ORIGINS` | No | Allowed CORS origins |
| Rate limiting settings | No | Delays between requests per source |

## Security & Best Practices

- **No secrets in code** – all keys in environment variables
- **CORS configuration** for production deployments  
- **Request validation** with Pydantic schemas
- **Error handling** without exposing internal details
- **Structured logging** for monitoring and debugging
- **Graceful degradation** when data sources unavailable

## Future Enhancements (Stretch Goals)

- [ ] **PostgreSQL integration** with full-text search indexing
- [ ] **Bulk CSV upload** for batch entity checks
- [ ] **Admin panel** for monitoring API quotas and error logs
- [ ] **API rate limiting** with Redis-based quotas
- [ ] **User authentication** and search history
- [ ] **Advanced filtering** by amount ranges, date ranges
- [ ] **Export formats** beyond CSV (JSON, PDF reports)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines, code style, and pull request process.

## License

MIT License - see [LICENSE](LICENSE) for details.

---

**Built with:** FastAPI, React, Redis, Docker | **Deployment:** `docker compose up` → http://localhost:8000 