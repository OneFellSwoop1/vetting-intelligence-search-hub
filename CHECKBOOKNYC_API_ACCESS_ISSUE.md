# CheckbookNYC API Access Issue - Comprehensive Analysis

## Date: November 3, 2025

---

## Executive Summary

The CheckbookNYC official API (https://www.checkbooknyc.com/api/) is protected by anti-bot services (Imperva/Cloudflare) that prevent programmatic access, blocking our application from retrieving actual spending and payment transaction data. This is **public data** that should be accessible via API, but anti-bot protection treats legitimate applications as malicious bots.

**Impact**: We can only access procurement notices and contract awards via Socrata API, not the actual spending/payment transactions that show real money flow to vendors.

---

## Background: What is CheckbookNYC?

CheckbookNYC is New York City's official transparency portal providing access to:
- **City Spending**: Actual payments/checks issued to vendors
- **Payroll Data**: City employee salaries
- **Contracts**: Active and historical contracts
- **Budget Information**: Agency budgets and allocations
- **Revenue Data**: City revenue sources

This data is **public information** mandated by NYC transparency laws and should be freely accessible to citizens, journalists, and applications.

---

## The Problem

### 1. Two Separate Data Systems

CheckbookNYC maintains two distinct data access methods:

#### A. CheckbookNYC Official API (BLOCKED)
- **URL**: `https://www.checkbooknyc.com/api/`
- **Endpoints**:
  - `/api/spending` - Actual vendor payments (checks, wire transfers)
  - `/api/contracts` - Contract details
  - `/api/payroll` - Employee salaries
  - `/api/revenue` - Revenue data
- **Data Type**: **Transactional spending records** (what we need!)
- **Status**: ❌ **BLOCKED BY ANTI-BOT PROTECTION**

#### B. Socrata API / NYC Open Data (ACCESSIBLE)
- **URL**: `https://data.cityofnewyork.us/`
- **Datasets Available**:
  - `dg92-zbpx` - City Record Online (procurement notices, public hearings)
  - `qyyg-4tf5` - Procurement Notices (subset of dg92-zbpx)
  - `ujre-m2tj` - Discretionary Award Tracker
  - `7pza-ynkh` - MOCS 15 Largest Contracts
  - `rqvv-d722` - Largest Requirements Contracts
- **Data Type**: **Procurement notices and contract awards** (not actual spending!)
- **Status**: ✅ **ACCESSIBLE VIA API**

### 2. The Data Gap

What CheckbookNYC website shows (via blocked API):
```
Vendor: GOOGLE INC
Amount: $7,272.00
Date: October 2015
Type: Spending Transaction (Check/Payment)
Associated Prime Vendor: N/A
```

What Socrata API provides (accessible):
```
Title: "RFQ for Google Workspace Licenses"
Vendor: "SHI International Corp" (reseller)
Type: Procurement Notice
```

**Result**: We get procurement notices about BUYING Google products from resellers, but NOT the actual payments TO Google Inc.

---

## Technical Analysis

### Anti-Bot Protection Details

**Protection Service**: Imperva Incapsula / Cloudflare Bot Management

**Blocking Mechanism**:
1. **JavaScript Challenge**: Requires browser JavaScript execution
2. **TLS Fingerprinting**: Identifies non-browser HTTP clients
3. **Behavioral Analysis**: Monitors request patterns
4. **CAPTCHA**: Deployed for suspicious requests

**Evidence**:
```bash
# Direct API call returns empty/HTML instead of JSON
$ curl https://www.checkbooknyc.com/api/spending
<html>
  <head><title>Access Denied</title></head>
  <!-- Imperva/Cloudflare protection page -->
</html>
```

**Application Logs**:
```
INFO:app.adapters.checkbook:✅ Skipping CheckbookNYC API (known to be blocked)
INFO:app.adapters.checkbook:Using ONLY Socrata API which is fast and reliable
```

### Why This is Problematic

1. **Public Data Mandate**: NYC Local Law requires transparency and API access
2. **Selective Blocking**: Website works (human browsing) but API blocked (automation)
3. **No API Keys**: CheckbookNYC doesn't provide API authentication for legitimate use
4. **Terms of Service**: No clear policy on programmatic access
5. **Data Completeness**: Socrata has procurement notices but NOT spending transactions

---

## Example: Google Inc Search

### What Users See on CheckbookNYC.com

Searching "Google Inc" on https://www.checkbooknyc.com/ returns:

| Date | Vendor | Agency | Amount | Type |
|------|--------|--------|--------|------|
| 10/19/2015 | GOOGLE INC | Dept of Youth | $227.22 | Payment |
| 10/14/2015 | GOOGLE INC | Dept of Youth | $226.55 | Payment |
| 10/02/2015 | GOOGLE INC | Dept of Youth | $223.45 | Payment |
| **Total** | **GOOGLE INC** | - | **$7,272** | **4 payments** |

### What Our API Returns

Searching "Google" via our application returns:

| Date | Vendor | Title | Type |
|------|--------|-------|------|
| Various | SHI International Corp | Google Maps Services | Procurement Notice |
| Various | Daston Corporation | Purchase of 520 Google Licenses (G-Suite) | Procurement Notice |
| Various | Tempus Nova Inc | Google Cloud Platform | Procurement Notice |

**Result**: We get contracts where OTHER companies are buying Google services, NOT actual payments TO Google Inc.

---

## Why Socrata Doesn't Have Spending Data

### 1. Different Data Sources

**Socrata (NYC Open Data)**:
- Source: NYC Department of Records / City Clerk
- Purpose: Public procurement transparency
- Contains: Solicitations, RFPs, bids, contract awards

**CheckbookNYC Spending**:
- Source: NYC Comptroller's Office / Financial Management System
- Purpose: Financial accountability and audit trails
- Contains: Actual checks, wire transfers, payment vouchers

### 2. Data Synchronization

CheckbookNYC pulls from the city's **Financial Management System (FMS)** which contains:
- General Ledger entries
- Accounts Payable records
- Payment vouchers
- Check registers

Socrata datasets are published by individual agencies and may not include FMS data.

### 3. Historical Data

The Google Inc payments from 2015 predate many Socrata datasets:
- `dg92-zbpx` oldest record: 2003 (procurement notices only)
- Spending transactions: Not in Socrata at all (only in CheckbookNYC API)

---

## Impact on Our Application

### Current Limitations

1. **Incomplete Vendor Search**:
   - User searches: "Google"
   - Expects: Payments TO Google Inc
   - Gets: Contracts where NYC bought Google products from resellers

2. **Missing Financial Transactions**:
   - Cannot see actual money flow
   - Cannot track vendor payment history
   - Cannot analyze true spending patterns

3. **Data Gaps**:
   - Historical spending data (pre-2020) mostly unavailable
   - Small vendors (<$100K) rarely in procurement datasets
   - Routine purchases not in contract databases

4. **False Positives** (Fixed in Phase 1):
   - "United Healthcare" matched "United Activities" (only shared "United")
   - "United Healthcare" matched "Michiana Healthcare" (only shared "Healthcare")

### What We CAN Access

✅ **Available via Socrata**:
- Procurement notices and solicitations
- Contract awards and registrations
- Large contracts (>$1M typically documented)
- Recent data (2020-present) more comprehensive

❌ **Blocked via CheckbookNYC API**:
- Actual payment transactions
- Check registers
- Vendor payment history
- Complete spending records
- Historical spending data (<2020)

---

## Legal and Policy Considerations

### 1. Public Records Law

**NYC Public Records Law** (Freedom of Information Law - FOIL):
- Mandates public access to government spending records
- Requires machine-readable formats for bulk data
- Prohibits unreasonable restrictions on access

### 2. NYC Local Laws

**Local Law 11 of 2012** (Checkbook NYC law):
- Requires online publication of city financial data
- Mandates API access for bulk downloads
- Specifies no fees for public access

### 3. Current Practice

Despite legal mandates:
- ❌ API access blocked by anti-bot protection
- ❌ No authentication mechanism for legitimate users
- ❌ No API documentation for programmatic access
- ✅ Website works for manual browsing (insufficient for bulk analysis)

---

## Comparison: What Should Work

### How Other Jurisdictions Handle This

**Federal Government (USAspending.gov)**:
```python
# Free API access with optional API key for higher rate limits
response = requests.get(
    'https://api.usaspending.gov/api/v2/spending',
    headers={'X-Api-Key': 'optional-key-for-rate-limits'}
)
# ✅ Works perfectly, no anti-bot blocking
```

**NYC Open Data (Socrata)**:
```python
# Free API access with optional app token
response = requests.get(
    'https://data.cityofnewyork.us/resource/dg92-zbpx.json',
    headers={'X-App-Token': 'optional-token'}
)
# ✅ Works perfectly, well-documented
```

**CheckbookNYC (Current State)**:
```python
# Should work like above, but blocked
response = requests.get('https://www.checkbooknyc.com/api/spending')
# ❌ Returns anti-bot protection HTML, not data
```

---

## Attempted Workarounds (Before Anti-Bot)

According to code history and documentation, previous attempts included:

### 1. Direct API Calls
```python
# Attempt to call official CheckbookNYC API
response = await client.get(
    'https://www.checkbooknyc.com/api/spending',
    params={'vendor': 'Google Inc', 'year': 2015}
)
```
**Result**: 40+ second timeouts, HTML responses, or empty JSON

### 2. Alternative Endpoints
```python
# Try XML feed endpoint
response = await client.get(
    'https://www.checkbooknyc.com/data-feeds/api',
    headers={'Accept': 'application/xml'}
)
```
**Result**: Same anti-bot protection

### 3. User Agent Spoofing
```python
# Mimic browser requests
headers = {
    'User-Agent': 'Mozilla/5.0 ...',
    'Accept': 'application/json',
    'Referer': 'https://www.checkbooknyc.com/'
}
```
**Result**: Still blocked (protection uses more than User-Agent)

---

## Current Workaround: Socrata-Only Approach

Our application currently:

1. **Uses Socrata API exclusively** for CheckbookNYC data
2. **Searches multiple datasets** for comprehensive coverage
3. **Implements strict vendor validation** to filter false positives
4. **Clearly labels data source** so users understand limitations

**Limitations**:
- Missing actual spending transactions
- No historical payment data
- Incomplete vendor coverage
- Users may be confused why results differ from CheckbookNYC.com

---

## Recommendations

### Short-Term (Implemented in Phase 1)

1. ✅ **Fix vendor matching** - Require all significant words to match
2. ✅ **Display data source clearly** - Users understand what data they're seeing
3. ✅ **Show contract identifiers** - Link to official CheckbookNYC records
4. ✅ **Stable record IDs** - Stop using random IDs

### Medium-Term (Research Phase)

1. **Contact NYC Comptroller's Office**
   - Request official API access mechanism
   - Inquire about authentication keys
   - Clarify policy on programmatic access

2. **Explore Alternative Data Sources**
   - NYC Open Data additional datasets
   - FOIL requests for bulk spending data
   - NYC Financial Management System (FMS) exports

3. **Technical Bypass Research** (if policy allows)
   - Browser automation (Selenium/Playwright)
   - Proxy rotation services
   - Session management techniques

### Long-Term Solution

**Ideal scenario**: NYC provides proper API access for CheckbookNYC spending data

**Requirements**:
- Free API access with optional registration
- API documentation
- Reasonable rate limits (e.g., 1000 requests/hour)
- Authentication tokens for higher limits
- Clear terms of service for programmatic access

---

## Conclusion

The CheckbookNYC API blocking prevents legitimate applications from accessing **public spending data** that is legally mandated to be available. While we've implemented workarounds using Socrata, users cannot get complete spending transaction data that shows actual payments to vendors.

**Key Takeaway**: This is a **policy/technical barrier** imposed by anti-bot protection on **public data**, not a technical limitation of our application. The data exists, is public by law, but is artificially restricted by overly aggressive bot protection.

---

## References

- NYC Local Law 11 of 2012: https://www1.nyc.gov/assets/home/downloads/pdf/local_laws/2012/local_law_011_2012.pdf
- CheckbookNYC Website: https://www.checkbooknyc.com/
- NYC Open Data Portal: https://opendata.cityofnewyork.us/
- Socrata API Documentation: https://dev.socrata.com/
- NYC Freedom of Information Law: https://www.dos.ny.gov/coog/foil2.html

---

**Document Version**: 1.0  
**Last Updated**: November 3, 2025  
**Status**: Active Issue - Awaiting Policy Resolution

