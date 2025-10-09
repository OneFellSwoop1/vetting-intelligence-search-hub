# Changelog - Vetting Intelligence Search Hub

## [2.1.0] - 2025-09-19

### 🎉 Major Improvements & Bug Fixes

#### ✅ Fixed NYC Lobbyist Search Issues
- **Enhanced search patterns** to include substring matching for company names like "Amazon.com Services LLC"
- **Improved query variations** to catch more entity name formats
- **Result**: Amazon NYC lobbyist results increased from 0 to 14 records

#### 🔧 Completely Overhauled Checkbook Adapter
- **Fixed API blocking issues**: CheckbookNYC API endpoints are protected by anti-bot services, implemented Socrata API as primary source
- **Enhanced search strategies**: Dual approach using full-text search and targeted vendor/title searches
- **Fixed data serialization**: Changed from SearchResult objects to dictionaries for consistent field mapping
- **Proper field mapping**: Ensured vendor, agency, amount, title fields are correctly populated
- **Result**: Checkbook results now show proper vendor names, agencies, and amounts instead of "Unknown"

#### 📊 Search Performance Improvements
- **Enhanced company name variations** for better recall across all adapters
- **Improved error handling** and timeout management
- **Better deduplication** logic to prevent duplicate results
- **Optimized caching** for faster subsequent searches

#### 🛠️ Technical Enhancements
- **Added comprehensive error handling** with proper logging
- **Implemented input validation** for all search parameters  
- **Enhanced response standards** for consistent API responses
- **Added resource management** for HTTP clients
- **Improved search utilities** with company name normalization

### 📈 Performance Metrics
- **Amazon Search Results**: 
  - Before: 52 total (0 checkbook, 0 nyc_lobbyist)
  - After: 68 total (4 checkbook, 14 nyc_lobbyist)
- **Microsoft Search Results**: 75+ comprehensive results across all sources
- **Response Times**: Sub-second for most queries with caching

### 🔍 Data Source Status
- **NYC Checkbook**: ✅ Working (via Socrata API)
- **NYC Lobbyist**: ✅ Enhanced search patterns
- **Senate LDA**: ✅ Optimized API calls
- **NY State Ethics**: ✅ Timeout handling improved

### 🚀 New Features
- **Enhanced correlation analysis** with strategic insights
- **Multi-company comparison** capabilities
- **Quarterly trend analysis** for temporal patterns
- **Google-scale analysis** features
- **Comprehensive analytics dashboard**

### 🐛 Bug Fixes
- Fixed CheckbookNYC API blocking by implementing Socrata fallback
- Resolved field mapping issues causing "Unknown" values in frontend
- Fixed NYC lobbyist search patterns for complex company names
- Improved error handling for network timeouts
- Enhanced data normalization across all adapters

### 📚 Documentation
- Added comprehensive API documentation
- Created troubleshooting guides
- Enhanced startup instructions
- Added performance optimization notes

---

## Previous Versions

### [2.0.0] - 2025-09-13
- Initial enhanced search implementation
- Multi-source data integration
- Basic correlation analysis

### [1.0.0] - 2025-08-01
- Initial release
- Basic search functionality
- Core data adapters
