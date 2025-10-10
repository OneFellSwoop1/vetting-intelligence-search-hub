# 🚀 Vetting Intelligence Search Hub - Startup Instructions

## ✅ Quick Start (Recommended)

The easiest way to start the application:

```bash
./start_application.sh
```

This script automatically:
- ✅ Uses the correct API keys from `backend/environment.env`
- ✅ Activates the virtual environment
- ✅ Starts both backend and frontend
- ✅ Includes FEC campaign finance integration
- ✅ Works immediately without manual configuration

## 📊 Application URLs

Once started:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 🔧 Alternative Startup Methods

### Method 1: Comprehensive Startup (with verification)
```bash
./fix_and_start.sh
```
This script provides detailed verification and troubleshooting.

### Method 2: Clean Startup (with environment reset)
```bash
./clean_and_start.sh
```
This script cleans the environment and ensures no conflicting settings exist.

### Method 3: Manual Startup
```bash
# 1. Load environment variables
export $(cat backend/environment.env | grep -v '^#' | grep -v '^$' | xargs)

# 2. Start backend
source venv/bin/activate
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload &

# 3. Start frontend (in new terminal)
cd frontend
npm run dev &
```

## 🛑 Stopping the Application

```bash
./stop_application.sh
```

Or manually:
```bash
pkill -f uvicorn
pkill -f "npm run dev"
```

## 🔍 Environment Check

To verify your environment setup:
```bash
./check_environment.sh
```

## 🔑 API Key Configuration

The application uses the **correct** API key from `backend/environment.env`:
```
LDA_API_KEY=your_lda_api_key_starting_with_065
```

**Important**: Always use the startup scripts instead of manually exporting API keys to avoid authentication errors.

## 🚨 Common Issues & Solutions

### Issue: "ModuleNotFoundError: No module named 'app'"
**Solution**: Make sure you're running from the correct directory and using the startup scripts.

### Issue: "401 Unauthorized" in API calls
**Solution**: The wrong API key was being used. Use the startup scripts which load the correct key from `environment.env`.

### Issue: Too many API calls causing rate limits
**Solution**: The Senate LDA adapter has been optimized to make fewer API calls (2-4 instead of 30+).

### Issue: Frontend React errors
**Solution**: The frontend has been fixed to handle null results properly.

## 📈 Performance Optimizations Applied

1. **Senate LDA Adapter**: Reduced from 30+ API calls to 2-4 calls per search
2. **Rate Limiting**: Proper delays between API calls to respect limits
3. **Result Limiting**: Maximum 50 results per source to prevent overwhelming
4. **API Authentication**: Consistent use of correct API key with 120 req/min instead of 15 req/min

## ✅ Verification Steps

After starting the application:

1. **Backend Health Check**:
   ```bash
   curl http://localhost:8000/health
   ```

2. **Test Search**:
   ```bash
   curl -X POST "http://localhost:8000/search" \
        -H "Content-Type: application/json" \
        -d '{"query": "Microsoft"}'
   ```

3. **Frontend Access**: Open http://localhost:3000 in your browser

## 🎯 Expected Search Results

A successful search for "Google" returns:
- **FEC Campaign Finance**: 42 results (political contributions & expenditures)
- **Senate LDA**: 50 results (federal lobbying filings)
- **NYC Checkbook**: 6 results (contracts totaling $923K+)
- **NYC Lobbyist**: 19 results (local lobbying registrations)
- **NY State Ethics**: 0 results (no state-level activity)

Total: 117+ results across 5 data sources with $178.9M+ financial activity

## 🆘 Troubleshooting

If you encounter issues:

1. **Check Environment**:
   ```bash
   ./check_environment.sh
   ```

2. **View Logs**:
   ```bash
   # Backend logs
   tail -f logs/backend.log
   
   # Frontend logs  
   tail -f logs/frontend.log
   ```

3. **Clean Restart**:
   ```bash
   ./stop_application.sh
   ./clean_and_start.sh
   ```

4. **Manual Debug**:
   ```bash
   # Test API key
   export $(cat backend/environment.env | grep -v '^#' | grep -v '^$' | xargs)
   echo $LDA_API_KEY
   # Should show: your API key starting with 065
   ```

## 🔐 Security Notes

- The API key in `environment.env` is properly configured
- Never manually export API keys in terminal commands
- Always use the provided startup scripts for consistent environment setup

---

**Last Updated**: June 2025  
**Status**: ✅ All major issues resolved 