# 🔍 Vetting Intelligence Search Hub

> A comprehensive platform for researching business entities through multiple government data sources including federal lobbying records, NYC Checkbook financial data, and state/local disclosures.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Next.js](https://img.shields.io/badge/Next.js-14.x-black.svg)](https://nextjs.org/)

## 🎯 Overview

The Vetting Intelligence Search Hub aggregates data from multiple government transparency sources to provide comprehensive insights into:

- **NYC Checkbook**: Municipal spending and contracts
- **NYS Ethics**: State-level lobbying activities
- **Senate LDA**: Federal lobbying disclosures
- **House LDA**: Congressional lobbying reports (Federal spending data)
- **NYC Lobbyist Search**: Municipal lobbying activities

## ✨ Key Features

### 🔎 Multi-Source Search
- **Unified Search Interface**: Query across all data sources simultaneously
- **Smart Filtering**: Filter by jurisdiction (NYC/NYS/Federal), year, and data type
- **Real-time Results**: Live aggregation from multiple APIs

### 📊 Advanced Analytics
- **Correlation Analysis**: Identify relationships between entities across datasets
- **Spending Patterns**: Track financial flows and contracting patterns
- **Lobbying Insights**: Connect lobbying activities with policy outcomes
- **Entity Relationships**: Map connections between organizations, contracts, and political activities

### 💾 Performance & Reliability
- **Intelligent Caching**: Redis-based caching with configurable TTL
- **Rate Limiting**: Respectful API usage with built-in throttling
- **Error Handling**: Robust error recovery and fallback mechanisms
- **Async Processing**: High-performance concurrent data fetching

### 🎨 Modern UI/UX
- **Responsive Design**: Mobile-first responsive interface
- **Interactive Visualizations**: Charts and graphs for data exploration
- **Export Capabilities**: Download results in multiple formats
- **Advanced Filters**: Granular search and filtering options

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   Data Sources  │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│   (Gov APIs)    │
│                 │    │                 │    │                 │
│ • React UI      │    │ • API Routes    │    │ • NYC Checkbook │
│ • Tailwind CSS  │    │ • Data Adapters │    │ • Senate LDA    │
│ • TypeScript    │    │ • Caching Layer │    │ • House LDA     │
│ • Responsive    │    │ • Correlation   │    │ • NYS Ethics    │
└─────────────────┘    │   Analysis      │    │ • NYC Lobbyist  │
                       └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **Redis** (optional, for caching)
- **Git**

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/vetting-intelligence-search-hub.git
cd vetting-intelligence-search-hub
```

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp ../env.example .env

# Edit .env file with your API keys (see Configuration section)
nano .env
```

### 3. Frontend Setup

```bash
# Navigate to frontend directory
cd ../frontend

# Install dependencies
npm install

# Build the application
npm run build
```

### 4. Start the Application

```bash
# Terminal 1: Start the backend
cd backend
source venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

# Terminal 2: Start the frontend
cd frontend
npm run dev
```

Visit `http://localhost:3000` to access the application.

## ⚙️ Configuration

### Required API Keys

Copy `env.example` to `.env` and configure:

```env
# Socrata API (for NYC data)
SOCRATA_APP_TOKEN=your_socrata_token_here

# Optional: Senate LDA API (for higher rate limits)
LDA_API_KEY=your_senate_lda_api_key_here

# Optional: Redis configuration
REDIS_URL=redis://localhost:6379/0

# Optional: Database URL
DATABASE_URL=sqlite:///./vetting_hub.db
```

### Getting API Keys

1. **Socrata App Token**: [Register at NYC Open Data](https://opendata.cityofnewyork.us/)

### Optional: Senate LDA API Key (Recommended for Production)

For **U.S. Senate Lobbying Disclosure Act (LDA)** data, you can optionally register for an API key to increase your rate limits:

- **Without API Key**: 15 requests/minute (anonymous access) = ~7 user searches/minute
- **With API Key**: 120 requests/minute (authenticated access) = ~60 user searches/minute

To register:
1. Visit [Senate LDA API Documentation](https://lda.senate.gov/api/)
2. Contact them to request an API key for your application
3. Add it to your `.env` file:
   ```
   LDA_API_KEY=your_senate_lda_api_key_here
   ```

**Note**: The Senate LDA data source works without an API key, but with reduced rate limits.

## 🐳 Docker Deployment

```bash
# Start all services
docker-compose up --build

# Or start in detached mode
docker-compose up -d --build
```

Services will be available at:
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8001`
- API Documentation: `http://localhost:8001/docs`

## 📖 API Documentation

### Core Endpoints

- **`POST /search`**: Multi-source search across all data sources
- **`GET /health`**: Health check endpoint
- **`POST /correlation`**: Advanced correlation analysis
- **`GET /sources`**: List available data sources

### Example API Usage

```python
import requests

# Search across all sources
response = requests.post("http://localhost:8001/search", json={
    "query": "Microsoft",
    "year": 2024,
    "jurisdiction": "federal"
})

results = response.json()
print(f"Found {results['total_results']} results across {len(results['sources'])} sources")
```

## 🧪 Testing

```bash
# Backend tests
cd backend
python -m pytest tests/ -v

# Frontend tests
cd frontend
npm test

# Run with coverage
python -m pytest --cov=app tests/
```

## 📊 Data Sources

| Source | Type | Coverage | Update Frequency |
|--------|------|----------|------------------|
| NYC Checkbook | Contracts/Spending | NYC | Daily |
| NYS Ethics | Lobbying | New York State | Monthly |
| Senate LDA | Lobbying | Federal | Quarterly |
| House LDA | Federal Spending | Federal | Daily |
| NYC Lobbyist | Lobbying | NYC | Real-time |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🛠️ Tech Stack

### Backend
- **FastAPI**: Modern, fast web framework
- **Python 3.11+**: Latest Python features
- **Pydantic**: Data validation and serialization
- **HTTPX**: Async HTTP client
- **Redis**: Caching and session storage
- **SQLAlchemy**: Database ORM (optional)

### Frontend
- **Next.js 14**: React framework with App Router
- **TypeScript**: Type-safe JavaScript
- **Tailwind CSS**: Utility-first CSS framework
- **React Hook Form**: Form management
- **Chart.js**: Data visualization
- **Axios**: HTTP client

### Infrastructure
- **Docker**: Containerization
- **Redis**: Caching layer
- **GitHub Actions**: CI/CD (optional)

## 📞 Support

- 📧 **Email**: [Your email]
- 🐛 **Issues**: [GitHub Issues](https://github.com/YOUR_USERNAME/vetting-intelligence-search-hub/issues)
- 📖 **Wiki**: [Project Wiki](https://github.com/YOUR_USERNAME/vetting-intelligence-search-hub/wiki)

## 🗺️ Roadmap

- [ ] Advanced data visualization dashboard
- [ ] Export functionality (PDF, Excel, CSV)
- [ ] User authentication and saved searches
- [ ] Email alerts for new data
- [ ] Machine learning-powered recommendations
- [ ] Mobile app (React Native)

---

**Made with ❤️ for government transparency and accountability**

## 🔍 Data Sources

### NYC Checkbook (Socrata API)
Access to New York City's financial data through the NYC Open Data / Socrata API:
- **Contracts**: Active contracts, MWBE contracts, modifications
- **Spending**: Payroll, financial transactions, capital commitments  
- **Revenue**: Budget data, tax revenue, property tax, collections
- **Budget**: Expense budget, summary, modifications

**API Endpoint**: `https://data.cityofnewyork.us/resource`
**Authentication**: Socrata API Key ID + Secret + App Token

### Federal Lobbying Data
- **Senate LDA**: Lobbying Disclosure Act filings
- **House LDA**: House lobbying registrations

### State & Local Data
- **NYS Ethics**: Joint Commission on Public Ethics filings
- **NYC Lobbyist**: New York City lobbyist registrations

## 🛠 API Usage

### NYC Checkbook (Socrata API)

#### Unified Search (Recommended)
```bash
# Search across all financial data types
curl -X GET "http://localhost:8000/api/search?q=Apple&year=2024"
```

**Response format**:
```json
{
  "results": [
    {
      "title": "NYC Contract: Apple Inc.",
      "description": "Amount: $125,000.00 | Agency: Department of Technology | IT Services Contract",
      "amount": 125000.00,
      "date": "2024-01-15",
      "source": "checkbook",
      "vendor": "Apple Inc.",
      "agency": "Department of Technology",
      "record_type": "contract",
      "year": "2024"
    }
  ]
}
```

### Authentication Notes

**✅ Current Setup**: Your integration uses **Socrata/NYC Open Data API** with:
- **API Key ID**: For OAuth authentication
- **API Key Secret**: For OAuth authentication  
- **App Token**: For enhanced rate limits and identification

This provides access to all NYC Checkbook data through the official NYC Open Data platform.

### Rate Limiting & Caching

- **Rate Limit**: 2.0 seconds between API requests (respectful to Socrata)
- **Datasets**: 15 datasets across contracts, spending, revenue, and budget
- **Caching**: 24-hour Redis cache (if available)
- **Timeout**: 30 seconds per API request

## 🧪 Testing

### Run Full Test Suite
```bash
cd backend
pytest tests/ -v
```

### Test Checkbook Integration
```bash
cd backend
python -c "
import asyncio
from app.adapters.checkbook import search

async def test():
    results = await search('Apple', 2024)
    print(f'✅ Found {len(results)} results')
    for r in results[:3]:
        print(f'   • {r[\"vendor\"]} - ${r[\"amount\"]:,.2f}')

asyncio.run(test())
"
```

### Expected Output
```
✅ Found 28 results
   • Apple Inc. - $500,000.00
   • Apple Computer Inc. - $125,000.00
   • Big Apple Construction - $75,000.00
```

## 📊 Features

### Socrata API Benefits
- **Official Data**: Direct access to NYC's authoritative Open Data platform
- **High Rate Limits**: Enhanced with API Key authentication
- **Comprehensive**: 15+ datasets across all financial data types
- **Reliable**: Battle-tested infrastructure used by many applications

### Search Capabilities
- **Fuzzy Matching**: Find entities with variations in name formatting
- **Multi-dataset**: Search across 15+ datasets simultaneously
- **Filtering**: Filter by year, amount, agency, data type
- **Sorting**: Results sorted by relevance and financial impact

### Caching & Performance
- **Redis Caching**: 24-hour cache for frequently accessed data
- **Parallel Queries**: Multiple datasets queried simultaneously
- **Rate Limiting**: Respectful API usage with configurable delays
- **Error Handling**: Graceful fallbacks when services are unavailable

## 🔧 Configuration

### Environment Variables

```bash
# NYC Checkbook / Socrata API
SOCRATA_API_KEY_ID=your_socrata_key_id
SOCRATA_API_KEY_SECRET=your_socrata_key_secret
SOCRATA_APP_TOKEN=your_socrata_app_token
CHECKBOOK_BASE_URL=https://data.cityofnewyork.us/resource
CHECKBOOK_RATE_LIMIT=2.0

# Federal APIs
LDA_API_KEY=your_lda_key_here

# Caching
REDIS_URL=redis://localhost:6379/0
CACHE_TTL=86400

# Performance
MAX_CONCURRENT_REQUESTS=5
REQUEST_TIMEOUT=30
MAX_RESULTS_PER_SOURCE=50
```

### Feature Flags
```bash
# Enable/disable specific data sources
ENABLE_CHECKBOOK=true
ENABLE_NYS_ETHICS=true
ENABLE_SENATE_LDA=true
ENABLE_HOUSE_LDA=true
ENABLE_NYC_LOBBYIST=true
```

## 🚀 Deployment

### Production Environment
1. Set `ENVIRONMENT=production` in `.env`
2. Configure Redis for caching
3. Set up proper logging with `LOG_LEVEL=INFO`
4. Enable CORS for your frontend domain

### Docker Support
```bash
# Build and run with Docker Compose
docker-compose up --build
```

## 📝 API Documentation

Once running, visit:
- **Interactive API Docs**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

[Your License Here]

---

**Questions?** Check the [API documentation](http://localhost:8000/docs) or [open an issue](https://github.com/your-repo/issues).

## Setup Instructions

### Environment Configuration

Copy `env.example` to `environment.env` and configure the following:

```bash
cp env.example environment.env
```

### API Credentials

#### Socrata API (NYC Open Data)
The application uses Socrata API for NYC Checkbook data:

```env
# NYC Open Data / Socrata API Credentials (for NYC Checkbook data)
SOCRATA_API_KEY_ID=your_socrata_key_id
SOCRATA_API_KEY_SECRET=your_socrata_key_secret
SOCRATA_APP_TOKEN=your_socrata_app_token
```

**Important Notes:**
- Uses OAuth authentication with API Key ID + Secret
- The App Token is working correctly and provides enhanced rate limits
- Authentication confirmed working as of latest update
- Some datasets may require specific access permissions

---

**Made with ❤️ for government transparency and accountability**

## 🔍 Data Sources

### NYC Checkbook (Socrata API)
Access to New York City's financial data through the NYC Open Data / Socrata API:
- **Contracts**: Active contracts, MWBE contracts, modifications
- **Spending**: Payroll, financial transactions, capital commitments  
- **Revenue**: Budget data, tax revenue, property tax, collections
- **Budget**: Expense budget, summary, modifications

**API Endpoint**: `https://data.cityofnewyork.us/resource`
**Authentication**: Socrata API Key ID + Secret + App Token

### Federal Lobbying Data
- **Senate LDA**: Lobbying Disclosure Act filings
- **House LDA**: House lobbying registrations

### State & Local Data
- **NYS Ethics**: Joint Commission on Public Ethics filings
- **NYC Lobbyist**: New York City lobbyist registrations

## 🛠 API Usage

### NYC Checkbook (Socrata API)

#### Unified Search (Recommended)
```bash
# Search across all financial data types
curl -X GET "http://localhost:8000/api/search?q=Apple&year=2024"
```

**Response format**:
```json
{
  "results": [
    {
      "title": "NYC Contract: Apple Inc.",
      "description": "Amount: $125,000.00 | Agency: Department of Technology | IT Services Contract",
      "amount": 125000.00,
      "date": "2024-01-15",
      "source": "checkbook",
      "vendor": "Apple Inc.",
      "agency": "Department of Technology",
      "record_type": "contract",
      "year": "2024"
    }
  ]
}
```

### Authentication Notes

**✅ Current Setup**: Your integration uses **Socrata/NYC Open Data API** with:
- **API Key ID**: For OAuth authentication
- **API Key Secret**: For OAuth authentication  
- **App Token**: For enhanced rate limits and identification

This provides access to all NYC Checkbook data through the official NYC Open Data platform.

### Rate Limiting & Caching

- **Rate Limit**: 2.0 seconds between API requests (respectful to Socrata)
- **Datasets**: 15 datasets across contracts, spending, revenue, and budget
- **Caching**: 24-hour Redis cache (if available)
- **Timeout**: 30 seconds per API request

## 🧪 Testing

### Run Full Test Suite
```bash
cd backend
pytest tests/ -v
```

### Test Checkbook Integration
```bash
cd backend
python -c "
import asyncio
from app.adapters.checkbook import search

async def test():
    results = await search('Apple', 2024)
    print(f'✅ Found {len(results)} results')
    for r in results[:3]:
        print(f'   • {r[\"vendor\"]} - ${r[\"amount\"]:,.2f}')

asyncio.run(test())
"
```

### Expected Output
```
✅ Found 28 results
   • Apple Inc. - $500,000.00
   • Apple Computer Inc. - $125,000.00
   • Big Apple Construction - $75,000.00
```

## 📊 Features

### Socrata API Benefits
- **Official Data**: Direct access to NYC's authoritative Open Data platform
- **High Rate Limits**: Enhanced with API Key authentication
- **Comprehensive**: 15+ datasets across all financial data types
- **Reliable**: Battle-tested infrastructure used by many applications

### Search Capabilities
- **Fuzzy Matching**: Find entities with variations in name formatting
- **Multi-dataset**: Search across 15+ datasets simultaneously
- **Filtering**: Filter by year, amount, agency, data type
- **Sorting**: Results sorted by relevance and financial impact

### Caching & Performance
- **Redis Caching**: 24-hour cache for frequently accessed data
- **Parallel Queries**: Multiple datasets queried simultaneously
- **Rate Limiting**: Respectful API usage with configurable delays
- **Error Handling**: Graceful fallbacks when services are unavailable

## 🔧 Configuration

### Environment Variables

```bash
# NYC Checkbook / Socrata API
SOCRATA_API_KEY_ID=your_socrata_key_id
SOCRATA_API_KEY_SECRET=your_socrata_key_secret
SOCRATA_APP_TOKEN=your_socrata_app_token
CHECKBOOK_BASE_URL=https://data.cityofnewyork.us/resource
CHECKBOOK_RATE_LIMIT=2.0

# Federal APIs
LDA_API_KEY=your_lda_key_here

# Caching
REDIS_URL=redis://localhost:6379/0
CACHE_TTL=86400

# Performance
MAX_CONCURRENT_REQUESTS=5
REQUEST_TIMEOUT=30
MAX_RESULTS_PER_SOURCE=50
```

### Feature Flags
```bash
# Enable/disable specific data sources
ENABLE_CHECKBOOK=true
ENABLE_NYS_ETHICS=true
ENABLE_SENATE_LDA=true
ENABLE_HOUSE_LDA=true
ENABLE_NYC_LOBBYIST=true
```

## 🚀 Deployment

### Production Environment
1. Set `ENVIRONMENT=production` in `.env`
2. Configure Redis for caching
3. Set up proper logging with `LOG_LEVEL=INFO`
4. Enable CORS for your frontend domain

### Docker Support
```bash
# Build and run with Docker Compose
docker-compose up --build
```

## 📝 API Documentation

Once running, visit:
- **Interactive API Docs**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

[Your License Here]

---

**Questions?** Check the [API documentation](http://localhost:8000/docs) or [open an issue](https://github.com/your-repo/issues). 