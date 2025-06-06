# 🔍 Vetting Intelligence Search Hub

> A comprehensive platform for searching and analyzing government contracts, lobbying activities, and political financial data across multiple NYC and federal sources.

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