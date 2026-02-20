"""
NYS Ethics Lobbying Adapter
Queries the NY State Commission on Ethics and Lobbying in Government datasets
hosted on data.ny.gov (Open NY / Socrata platform).

Datasets used:
  - se5j-cmbb : Lobbyist Statement of Registration  (smaller, faster)
  - t9kf-dqbc : Lobbyist Bi-Monthly Reports          (large, 278M+ rows)

Key improvements over previous version:
  - Full Socrata BasicAuth (API key id + secret) + App Token header
  - Targeted $where clauses on indexed name fields instead of $q full-text
  - $q full-text used only as a fallback when $where returns nothing
  - Both datasets searched in parallel via asyncio.gather
  - Per-dataset timeout of 20 s; overall adapter budget of 22 s
  - 1 automatic retry (with $q fallback) on timeout
  - Proper date fields used for recency sorting and normalization
  - Redis cache with 24-hour TTL so results survive server slowness
"""

import asyncio
import aiohttp
import logging
import hashlib
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Dataset definitions
# ---------------------------------------------------------------------------

# Registration dataset – smaller (~hundreds of thousands of rows), faster
DATASET_REGISTRATION = {
    "id": "se5j-cmbb",
    "name": "registration",
    "client_field": "contractual_client_name",
    "beneficial_field": "beneficial_client_name",
    "lobbyist_field": "principal_lobbyist_name",
    "date_field": "contract_start_date",       # calendar_date
    "year_field": "reporting_year",
    "compensation_field": "compensation_amount",
    "subjects_field": "lobbying_subjects",
    "order_field": "contract_start_date DESC",
}

# Bi-monthly dataset – very large (278M+ rows), used as secondary source
DATASET_BIMONTHLY = {
    "id": "t9kf-dqbc",
    "name": "bi_monthly",
    "client_field": "contractual_client_name",
    "beneficial_field": "beneficial_client_name",
    "lobbyist_field": "principal_lobbyist_name",
    "date_field": "expense_date",              # calendar_date
    "year_field": "reporting_year",
    "compensation_field": "compensation",
    "subjects_field": "lobbying_subjects",
    "order_field": "reporting_year DESC",      # expense_date has many nulls
}

BASE_URL = "https://data.ny.gov/resource"
OVERALL_TIMEOUT = 15       # hard cap on the whole adapter call
RESULT_LIMIT = 20          # max rows per dataset per query
CACHE_TTL = 86400          # 24 hours – NYS data is updated monthly at most

# Socrata NBE (New Backend Engine) parameters – dramatically faster on large datasets.
# Without these the old OBE (Original Backend Engine) is used, which hangs indefinitely on
# the 278M-row bi-monthly table.
NBE_PARAMS = {"$$read_from_nbe": "true", "$$version": "2.1"}

# Per-dataset query settings.  Registration is small/fast; bi-monthly is huge.
# allow_retry=False on bi-monthly avoids a second 8-second wait that would exceed budget.
DATASET_QUERY_CONFIG = {
    "registration": {"timeout": 8, "retry_timeout": 8, "allow_retry": True},
    "bi_monthly":   {"timeout": 8, "retry_timeout": 0, "allow_retry": False},
}


class NYSEthicsAdapter:
    def __init__(self):
        self.name = "NYS Ethics Lobbying"
        self.base_url = BASE_URL

        # Credentials – loaded from environment at construction time
        self.app_token = os.getenv("SOCRATA_APP_TOKEN")
        self.api_key_id = os.getenv("SOCRATA_API_KEY_ID")
        self.api_key_secret = os.getenv("SOCRATA_API_KEY_SECRET")

        # Cache
        self.cache: Optional[Any] = None
        self.cache_ttl = CACHE_TTL
        try:
            from ..cache import CacheService
            self.cache = CacheService()
            logger.info("Redis caching enabled for NYS Ethics adapter")
        except ImportError:
            logger.info("Redis caching not available for NYS Ethics adapter")

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    async def search(
        self,
        query: str,
        year: Optional[int] = None,
        ultra_fast_mode: bool = False,  # kept for API compatibility – ignored
    ) -> List[Dict[str, Any]]:
        """Search NYS lobbying records. Returns up to 40 normalized results."""
        logger.info(
            f"🔍 NY State Ethics search called with query: '{query}', year: {year}"
        )

        # 1. Try Redis cache first
        cache_key = self._cache_key(query, year)
        cached = await self._read_cache(cache_key)
        if cached is not None:
            logger.info(
                f"✅ Cache hit: returning {len(cached)} cached NYS Ethics results for '{query}'"
            )
            return cached

        # 2. Run within overall time budget
        try:
            results = await asyncio.wait_for(
                self._search_all_datasets(query, year),
                timeout=OVERALL_TIMEOUT,
            )
        except asyncio.TimeoutError:
            logger.warning(
                f"⏰ NYS Ethics overall timeout ({OVERALL_TIMEOUT}s) for query: '{query}'"
            )
            results = []
        except Exception as exc:
            logger.error(f"❌ NYS Ethics unexpected error for '{query}': {exc}")
            results = []

        # 3. Write through to cache (even an empty result – avoids hammering a slow server)
        if results:
            await self._write_cache(cache_key, results)

        logger.info(
            f"✅ NY State Ethics returning {len(results)} lobbying results for query: {query}"
        )
        return results

    # ------------------------------------------------------------------
    # Core search logic
    # ------------------------------------------------------------------

    async def _search_all_datasets(
        self, query: str, year: Optional[int]
    ) -> List[Dict[str, Any]]:
        """Query both datasets in parallel and merge results."""

        # Build a single authenticated aiohttp session shared across tasks
        auth = (
            aiohttp.BasicAuth(self.api_key_id, self.api_key_secret)
            if (self.api_key_id and self.api_key_secret)
            else None
        )
        headers = {"Accept": "application/json"}
        if self.app_token:
            headers["X-App-Token"] = self.app_token
            logger.debug("Using Socrata App Token for NY State API")
        if auth:
            logger.debug("Using Socrata BasicAuth for NY State API")

        connector = aiohttp.TCPConnector(limit=4, ttl_dns_cache=300)
        session_timeout = aiohttp.ClientTimeout(total=OVERALL_TIMEOUT + 2)

        async with aiohttp.ClientSession(
            timeout=session_timeout, connector=connector, auth=auth
        ) as session:
            reg_task = self._fetch_dataset(
                session, headers, DATASET_REGISTRATION, query, year
            )
            bim_task = self._fetch_dataset(
                session, headers, DATASET_BIMONTHLY, query, year
            )

            task_results = await asyncio.gather(
                reg_task, bim_task, return_exceptions=True
            )

        all_results: List[Dict[str, Any]] = []
        for i, result in enumerate(task_results):
            name = ("registration", "bi_monthly")[i]
            if isinstance(result, Exception):
                logger.warning(f"⚠️ NYS dataset '{name}' failed: {result}")
            else:
                all_results.extend(result)
                logger.info(f"📊 NYS dataset '{name}' returned {len(result)} results")

        return self._dedupe_and_sort(all_results)

    async def _fetch_dataset(
        self,
        session: aiohttp.ClientSession,
        headers: Dict[str, str],
        dataset: Dict[str, str],
        query: str,
        year: Optional[int],
    ) -> List[Dict[str, Any]]:
        """
        Fetch records from one dataset.
        Strategy:
          1. Try a targeted $where query on the name fields (fast with NBE).
          2. If that returns nothing AND this dataset allows retry, fall back to $q.
        The bi-monthly dataset (278M rows) does not retry to stay within the overall budget.
        """
        cfg = DATASET_QUERY_CONFIG.get(dataset["name"], {"timeout": 8, "allow_retry": False})

        # Attempt 1 – targeted $where
        results = await self._query_dataset(
            session,
            headers,
            dataset,
            query,
            year,
            use_fulltext=False,
            timeout_seconds=cfg["timeout"],
        )
        if results:
            return results

        if not cfg.get("allow_retry"):
            logger.info(
                f"↩️  NYS dataset '{dataset['name']}': no results from $where, retry disabled"
            )
            return []

        # Attempt 2 – $q full-text fallback (only for datasets that allow it)
        logger.info(
            f"🔄 NYS dataset '{dataset['name']}': $where returned nothing, trying $q fallback"
        )
        results = await self._query_dataset(
            session,
            headers,
            dataset,
            query,
            year,
            use_fulltext=True,
            timeout_seconds=cfg["retry_timeout"],
        )
        return results

    async def _query_dataset(
        self,
        session: aiohttp.ClientSession,
        headers: Dict[str, str],
        dataset: Dict[str, str],
        query: str,
        year: Optional[int],
        use_fulltext: bool,
        timeout_seconds: int,
    ) -> List[Dict[str, Any]]:
        """Execute a single Socrata request and return normalized records."""
        url = f"{self.base_url}/{dataset['id']}.json"
        params = self._build_params(dataset, query, year, use_fulltext)
        mode = "$q" if use_fulltext else "$where"

        logger.debug(
            f"NYS {dataset['name']} query [{mode}] url={url} params={params}"
        )

        try:
            per_request_timeout = aiohttp.ClientTimeout(total=timeout_seconds)
            async with session.get(
                url, params=params, headers=headers, timeout=per_request_timeout
            ) as response:
                if response.status != 200:
                    body = await response.text()
                    logger.warning(
                        f"⚠️ NYS {dataset['name']} API status {response.status}: {body[:200]}"
                    )
                    return []
                data = await response.json(content_type=None)
                if not isinstance(data, list):
                    logger.warning(
                        f"⚠️ NYS {dataset['name']} unexpected response type: {type(data)}"
                    )
                    return []

                logger.info(
                    f"✅ NYS {dataset['name']} [{mode}] returned {len(data)} raw records"
                )
                return [
                    r
                    for item in data
                    if (r := self._parse_record(item, dataset)) is not None
                ]

        except asyncio.TimeoutError:
            logger.warning(
                f"⏰ Timeout on NYS {dataset['name']} [{mode}] after {timeout_seconds}s"
            )
            return []
        except Exception as exc:
            logger.warning(
                f"❌ Error querying NYS {dataset['name']} [{mode}]: {exc}"
            )
            return []

    # ------------------------------------------------------------------
    # Query building
    # ------------------------------------------------------------------

    def _build_params(
        self,
        dataset: Dict[str, str],
        query: str,
        year: Optional[int],
        use_fulltext: bool,
    ) -> Dict[str, str]:
        """Build Socrata query parameters."""
        # Include NBE params first so they appear in the query string
        params: Dict[str, str] = {**NBE_PARAMS, "$limit": str(RESULT_LIMIT)}

        if use_fulltext:
            # $q searches the full-text index – slower but broader
            params["$q"] = query
        else:
            # Targeted $where on the three name columns – faster when fields are indexed
            safe = query.replace("'", "''")
            client_f = dataset["client_field"]
            beneficial_f = dataset["beneficial_field"]
            lobbyist_f = dataset["lobbyist_field"]
            params["$where"] = (
                f"upper({client_f}) like upper('%{safe}%') "
                f"OR upper({beneficial_f}) like upper('%{safe}%') "
                f"OR upper({lobbyist_f}) like upper('%{safe}%')"
            )

        # Prefer most-recent records
        params["$order"] = dataset["order_field"]

        # Optional year filter (registration dataset uses text for reporting_year)
        if year:
            year_field = dataset["year_field"]
            if use_fulltext:
                # Append to params as an equality filter
                params[year_field] = str(year)
            else:
                # Append to the $where clause
                params["$where"] += f" AND {year_field}='{year}'"

        return params

    # ------------------------------------------------------------------
    # Record normalization
    # ------------------------------------------------------------------

    def _parse_record(
        self, item: Dict[str, Any], dataset: Dict[str, str]
    ) -> Optional[Dict[str, Any]]:
        """Normalize a raw Socrata record into the standard result dict."""
        try:
            client_name = (
                item.get("contractual_client_name", "")
                or item.get("beneficial_client_name", "")
            ).strip()
            lobbyist_name = item.get("principal_lobbyist_name", "").strip()

            # Skip entirely empty records
            if not client_name and not lobbyist_name:
                return None

            reporting_year = item.get("reporting_year", "")

            # ---- Real date fields ----------------------------------------
            # Registration: contract_start_date  (calendar_date)
            # Bi-monthly:   expense_date         (calendar_date, often null)
            # Fall back to reporting_year if specific date is missing
            date_raw = item.get(dataset["date_field"], "")
            date_str = self._parse_date(date_raw, reporting_year)

            # ---- Amount --------------------------------------------------
            comp_raw = item.get(dataset["compensation_field"])
            reimb_raw = item.get("reimbursed_expenses")  # only bi-monthly
            amount = self._parse_amount(comp_raw) + self._parse_amount(reimb_raw)

            # ---- Description ---------------------------------------------
            parts: List[str] = []
            if lobbyist_name and lobbyist_name != client_name:
                parts.append(f"Lobbyist: {lobbyist_name}")

            subjects = item.get("lobbying_subjects", "").replace(";", ",").strip()
            if subjects:
                parts.append(f"Subjects: {subjects}")

            reporting_period = item.get("reporting_period", "")
            if reporting_period:
                parts.append(f"Period: {reporting_period}")

            filing_type = item.get("filing_type", "")
            if filing_type:
                parts.append(f"Filing: {filing_type}")

            if amount > 0:
                parts.append(f"Compensation: ${amount:,.2f}")

            description = " | ".join(parts)

            # ---- Title ---------------------------------------------------
            record_type = (
                "Registration" if dataset["name"] == "registration" else "Report"
            )
            title = f"NY State Lobbying {record_type}: {client_name or 'Unknown Client'}"
            if reporting_year:
                title += f" ({reporting_year})"

            return {
                "title": title,
                "description": description,
                "amount": amount if amount > 0 else None,
                "date": date_str,
                "source": "nys_ethics",
                "vendor": lobbyist_name or client_name,
                "agency": "NY State Commission on Ethics and Lobbying",
                "url": "https://reports.ethics.ny.gov/publicquery",
                "record_type": dataset["name"],
                "year": str(reporting_year),
                "client": client_name,
                "lobbyist": lobbyist_name,
                "subjects": subjects,
                "period": reporting_period,
                "raw_data": item,
            }

        except Exception as exc:
            logger.warning(f"Error parsing NYS lobbying record: {exc}")
            return None

    # ------------------------------------------------------------------
    # Deduplication and sorting
    # ------------------------------------------------------------------

    def _dedupe_and_sort(
        self, results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Remove duplicates (by client + lobbyist + year + period) and sort by recency."""
        seen: set = set()
        unique: List[Dict[str, Any]] = []
        for r in results:
            key = (
                (r.get("client") or "").lower(),
                (r.get("lobbyist") or "").lower(),
                r.get("year", ""),
                r.get("period", ""),
            )
            if key not in seen:
                seen.add(key)
                unique.append(r)

        # Sort by date descending, then amount descending
        unique.sort(
            key=lambda x: (x.get("date", ""), x.get("amount") or 0),
            reverse=True,
        )
        return unique[:40]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _parse_date(self, date_raw: Any, year_fallback: Any = "") -> str:
        """Return an ISO date string from raw Socrata date or year fallback."""
        if date_raw:
            date_str = str(date_raw)
            # Socrata returns calendar_date as "YYYY-MM-DDTHH:MM:SS.sss" or "YYYY-MM-DD"
            date_part = date_str.split("T")[0]
            if len(date_part) == 10 and date_part[4] == "-":
                return date_part
        # Fall back to year only
        if year_fallback:
            yr = str(year_fallback).strip()
            if yr.isdigit() and len(yr) == 4:
                return f"{yr}-01-01"
        return ""

    def _parse_amount(self, amount_raw: Any) -> float:
        """Safely parse an amount value to float."""
        if not amount_raw:
            return 0.0
        try:
            cleaned = str(amount_raw).replace("$", "").replace(",", "").strip()
            if not cleaned or cleaned.lower() in ("n/a", "none", "null", ""):
                return 0.0
            return float(cleaned)
        except (ValueError, TypeError):
            return 0.0

    def _cache_key(self, query: str, year: Optional[int]) -> str:
        key_data = f"nys_ethics:{query.lower()}:{year or 'all'}"
        return hashlib.sha256(key_data.encode()).hexdigest()

    async def _read_cache(self, key: str) -> Optional[List[Dict[str, Any]]]:
        if not self.cache:
            return None
        try:
            import json
            raw = await self.cache.get_async(key)
            if raw:
                return json.loads(raw)
        except Exception as exc:
            logger.debug(f"NYS cache read error: {exc}")
        return None

    async def _write_cache(self, key: str, results: List[Dict[str, Any]]) -> None:
        if not self.cache:
            return
        try:
            import json
            await self.cache.set_async(key, json.dumps(results), ttl=self.cache_ttl)
            logger.debug(f"✅ Cached {len(results)} NYS Ethics results")
        except Exception as exc:
            logger.debug(f"NYS cache write error: {exc}")


# ---------------------------------------------------------------------------
# Module-level function kept for backward compatibility
# ---------------------------------------------------------------------------
async def search(
    query: str,
    year: Optional[int] = None,
    ultra_fast_mode: bool = False,
) -> List[Dict[str, Any]]:
    adapter = NYSEthicsAdapter()
    return await adapter.search(query, year, ultra_fast_mode)
