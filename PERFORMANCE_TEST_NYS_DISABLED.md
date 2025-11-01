# ⚡ Performance Test: NYS Ethics Adapter Disabled

## 🎯 Test Purpose

Testing search response times **without** the NYS Ethics (NY State lobbying) adapter to determine its performance impact.

---

## ✅ Changes Applied

### **Files Modified:**

1. **`backend/app/routers/search.py`** (lines 330-334)
   - Commented out NYS Ethics adapter initialization
   - Adapter will not be queried during searches

2. **`backend/app/websocket.py`** (lines 43-46)
   - Commented out NYS Ethics from WebSocket searches
   - Real-time search won't include NYS data

---

## 📊 How to Test Performance

### **Before Testing:**
Clear your browser cache or use incognito mode to avoid cached results.

### **Test Steps:**

1. **Navigate to the application:**
   ```
   http://localhost:3000/app
   ```

2. **Perform searches and time them:**
   
   **Test Query 1: "Google"**
   - Type "Google" in the search box
   - Click Search
   - Note the time displayed in the UI or check browser DevTools Network tab
   - Record: _________ seconds
   
   **Test Query 2: "Microsoft"**
   - Search for "Microsoft"
   - Record time: _________ seconds
   
   **Test Query 3: "Stephanie Distafano"**
   - Search for "Stephanie Distafano"
   - Record time: _________ seconds

3. **Check backend logs for timing:**
   ```bash
   tail -f /Users/nicholas/Projects/vetting-intelligence-search-hub/backend_restart.log
   ```
   
   Look for lines like:
   ```
   INFO: Search completed in 1234ms
   ```

---

## 📈 Expected Results

### **Active Data Sources (NYS Ethics DISABLED):**
- ✅ CheckbookNYC (NYC Contracts)
- ✅ Senate LDA (Federal Lobbying)
- ✅ NYC Lobbyist (NYC Lobbying)
- ✅ FEC (Campaign Finance)
- ❌ **NYS Ethics (DISABLED for this test)**

### **Performance Impact:**

If NYS Ethics was the bottleneck:
- ✅ Faster search response times
- ✅ More consistent timing
- ✅ Fewer timeout issues

If NYS Ethics was NOT the bottleneck:
- ⚠️ Similar response times
- ⚠️ Other adapters may be slow
- ⚠️ Network/API issues elsewhere

---

## 🔍 What to Look For

### **In the Application UI:**

1. **Total Results**
   - Will be lower (no NYS Ethics results)
   - Check if other sources compensate

2. **Source Breakdown**
   - Should show 4 sources instead of 5
   - No "NY State Ethics" badge

3. **Response Time**
   - Displayed in search results (if implemented)
   - Check browser DevTools → Network tab → search request

### **In Backend Logs:**

```bash
# Watch for search timing
grep -i "search.*time\|completed.*ms" backend_restart.log | tail -20

# Check for adapter errors
grep -i "error\|timeout\|failed" backend_restart.log | tail -20

# See which adapters are being called
grep -i "adapter" backend_restart.log | tail -30
```

---

## 🔬 Detailed Timing Analysis

### **Check Individual Adapter Performance:**

```bash
# View the full log with timestamps
tail -100 backend_restart.log | grep -E "search|adapter|completed"
```

Look for patterns like:
```
[timestamp] Starting search for query: 'Google'
[timestamp] CheckbookNYC adapter: 500ms
[timestamp] Senate LDA adapter: 300ms
[timestamp] NYC Lobbyist adapter: 200ms
[timestamp] FEC adapter: 400ms
[timestamp] Total search time: 550ms (parallel execution)
```

---

## 📊 Performance Comparison

### **Document Your Findings:**

| Metric | With NYS Ethics | Without NYS Ethics | Improvement |
|--------|----------------|-------------------|-------------|
| Average search time | _____ sec | _____ sec | _____ % |
| Slowest search | _____ sec | _____ sec | _____ % |
| Fastest search | _____ sec | _____ sec | _____ % |
| Total results | _____ | _____ | _____ |
| Timeout errors | _____ | _____ | _____ |

---

## 🔄 How to Re-Enable NYS Ethics Adapter

If you want to restore the NYS Ethics adapter after testing:

### **Option 1: Manual Re-enable**

**File 1: `backend/app/routers/search.py`**

Uncomment lines 330-334:
```python
# Change this:
# PERFORMANCE TEST: NYS Ethics adapter temporarily disabled to test speed impact
# elif source == "nys_ethics":
#     # FIXED: Disable ultra-fast mode to use real NY State API instead of hardcoded results
#     adapter = NYSEthicsAdapter()
#     search_tasks.append(("nys_ethics", adapter.search(request.query, year_int, ultra_fast_mode=False)))

# To this:
elif source == "nys_ethics":
    # FIXED: Disable ultra-fast mode to use real NY State API instead of hardcoded results
    adapter = NYSEthicsAdapter()
    search_tasks.append(("nys_ethics", adapter.search(request.query, year_int, ultra_fast_mode=False)))
```

**File 2: `backend/app/websocket.py`**

Uncomment line 46:
```python
# Change this:
search_tasks = [
    ("checkbook", get_adapter_instance('checkbook').search(query, year_int)),
    # ("nys_ethics", get_adapter_instance('nys_ethics').search(query, year_int)),
    ("senate_lda", get_adapter_instance('senate_lda').search(query, year_int)),
    ("nyc_lobbyist", get_adapter_instance('nyc_lobbyist').search(query, year_int)),
]

# To this:
search_tasks = [
    ("checkbook", get_adapter_instance('checkbook').search(query, year_int)),
    ("nys_ethics", get_adapter_instance('nys_ethics').search(query, year_int)),
    ("senate_lda", get_adapter_instance('senate_lda').search(query, year_int)),
    ("nyc_lobbyist", get_adapter_instance('nyc_lobbyist').search(query, year_int)),
]
```

**Restart Backend:**
```bash
pkill -f "uvicorn"
cd backend
source ../venv/bin/activate
python start_server.py
```

### **Option 2: Git Revert**

```bash
# Discard changes to restore NYS Ethics
cd /Users/nicholas/Projects/vetting-intelligence-search-hub
git checkout backend/app/routers/search.py
git checkout backend/app/websocket.py

# Restart backend
pkill -f "uvicorn"
cd backend
source ../venv/bin/activate  
python start_server.py
```

---

## 🎯 Alternative: Optimize NYS Ethics Instead

If NYS Ethics IS the bottleneck, consider these optimizations:

### **1. Add Caching**
The adapter already has Redis caching, but check cache hit rate:
```bash
grep "cache hit" backend_restart.log | grep nys_ethics
```

### **2. Reduce Timeout**
Adjust timeout in the adapter to fail faster:
```python
# In nys_ethics.py
timeout = aiohttp.ClientTimeout(total=5)  # Reduce from 10 to 5 seconds
```

### **3. Reduce Result Limit**
```python
# Fetch fewer results from NYS
limit = 25  # Instead of 50
```

### **4. Add Query Filtering**
Pre-filter queries that are unlikely to have NYS results:
```python
# Skip NYS for certain query patterns
if len(query) < 3 or query.isnumeric():
    skip_nys = True
```

### **5. Make It Optional**
Add a flag to disable NYS for faster searches:
```python
# In search endpoint
include_nys_ethics: bool = Query(default=False, description="Include NY State data (slower)")
```

---

## 📝 Test Results Template

### **Test Date:** _____________________

### **Test Environment:**
- Backend: Running
- Frontend: Running
- Cache: Cleared / Not Cleared
- Network: Fast / Slow

### **Test Queries:**

**Query 1: "Google"**
- With NYS: _____ sec
- Without NYS: _____ sec
- **Difference: _____ sec (_____ % faster/slower)**

**Query 2: "Microsoft"**
- With NYS: _____ sec
- Without NYS: _____ sec
- **Difference: _____ sec (_____ % faster/slower)**

**Query 3: Custom Query: "__________"**
- With NYS: _____ sec
- Without NYS: _____ sec
- **Difference: _____ sec (_____ % faster/slower)**

### **Observations:**
- _____________________________________
- _____________________________________
- _____________________________________

### **Recommendation:**
- [ ] Keep NYS Ethics disabled (performance improved significantly)
- [ ] Re-enable NYS Ethics (no significant impact)
- [ ] Re-enable with optimizations (see suggestions above)

---

## 🚨 Important Notes

1. **Data Completeness**: With NYS Ethics disabled, you'll miss NY State lobbying data
2. **User Impact**: Users won't see comprehensive NY State results
3. **Temporary Test**: This is a performance diagnostic, not a permanent solution
4. **Cache Effects**: First search will be slower, subsequent searches faster

---

## 🔧 Quick Commands

```bash
# View real-time backend logs
tail -f /Users/nicholas/Projects/vetting-intelligence-search-hub/backend_restart.log

# Check which adapters are active
grep "Initialized.*Adapter" backend_restart.log | tail -10

# Monitor search timing
grep -i "search.*completed\|execution.*time" backend_restart.log | tail -20

# Restart backend after changes
pkill -f uvicorn && cd backend && source ../venv/bin/activate && python start_server.py
```

---

## ✅ Current Status

**NYS Ethics Adapter:** ❌ **DISABLED**

**Active Sources:**
- ✅ CheckbookNYC
- ✅ Senate LDA
- ✅ NYC Lobbyist
- ✅ FEC Campaign Finance

**To Test Performance:** Search in the application and compare response times

**To Re-enable:** Follow instructions above or revert changes with Git

---

**Ready to test!** Perform some searches and compare the timing. 🚀

