import asyncio
import httpx
import os
from typing import List, Optional, Dict, Any
import logging
from ..schemas import SearchResult

logger = logging.getLogger(__name__)

# The correct base URL for Senate LDA API
LDA_API_BASE = "https://lda.senate.gov/api/v1"

def get_lda_api_key():
    """Get LDA API key from environment variables at runtime"""
    return os.getenv("LDA_API_KEY")

async def search_senate_lda(query: str, year: Optional[str] = None) -> List[SearchResult]:
    """
    Search the U.S. Senate LDA API v1 for federal lobbying registrations and reports.
    Uses the correct /filings/ endpoint with comprehensive data.
    """
    results = []
    logger.info(f"🔍 Starting Senate LDA search for query: '{query}', year: {year}")
    
    try:
        # Add small delay for respectful API usage
        await asyncio.sleep(0.5)
        
        headers = {
            'User-Agent': 'Vetting-Intelligence-Search-Hub/1.0',
            'Accept': 'application/json'
        }
        
        # Add API key authentication if available
        lda_api_key = get_lda_api_key()
        if lda_api_key:
            headers['Authorization'] = f'Bearer {lda_api_key}'
            logger.info("🔑 Using authenticated API access (120 req/min)")
        else:
            logger.info("🌐 Using anonymous API access (15 req/min)")
        
        async with httpx.AsyncClient(timeout=15) as client:
            # Search filings with both client and registrant name matching
            params = {
                'page_size': 100,
                'client_name': query,  # Use client_name for direct client matching
                'filing_year': 2024,  # Get 2024 data first
                'order_by': '-dt_posted'  # Sort by most recent first
            }
            
            if year:
                params['filing_year'] = year
            else:
                # Default to recent years for better relevance
                params['filing_year'] = 2024
            
            api_url = f"{LDA_API_BASE}/filings/"
            logger.info(f"📡 Making API call to: {api_url}")
            logger.info(f"📋 Search params: {params}")
            
            response = await client.get(api_url, headers=headers, params=params)
            
            logger.info(f"📊 API Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"📈 API returned {data.get('count', 'unknown')} total records")
                
                if 'results' in data and data['results']:
                    logger.info(f"📝 Processing {len(data['results'])} results from API")
                    
                    for i, filing in enumerate(data['results']):
                        # Since we're using client_name parameter, all results should be matches
                        client_name = filing.get('client', {}).get('name', '')
                        registrant_name = filing.get('registrant', {}).get('name', '')
                        
                        logger.info(f"🔎 Filing {i+1}: Client='{client_name}', Registrant='{registrant_name}'")
                        
                        # All results from client_name search are matches, so process them all
                        logger.info(f"✅ Processing filing {i+1}: Client='{client_name}', Registrant='{registrant_name}'")
                        
                        # Extract comprehensive filing information
                        filing_type = filing.get('filing_type_display', 'Unknown Report')
                        income = filing.get('income')
                        expenses = filing.get('expenses')
                        filing_year = filing.get('filing_year')
                        filing_period = filing.get('filing_period_display', '')
                        filing_uuid = filing.get('filing_uuid', '')
                        posted_date = filing.get('dt_posted', '')
                        
                        logger.debug(f"💰 Financial data - Income: {income}, Expenses: {expenses}")
                        logger.debug(f"📅 Filing info - Type: {filing_type}, Year: {filing_year}, UUID: {filing_uuid}")
                        
                        # Extract financial information - handle potential string values
                        income = filing.get('income', 0) or 0
                        expenses = filing.get('expenses', 0) or 0
                        
                        # Safely convert to int if they are strings
                        try:
                            income = int(income) if income and str(income).replace('.', '').replace(',', '').isdigit() else 0
                        except (ValueError, TypeError):
                            income = 0
                            
                        try:
                            expenses = int(expenses) if expenses and str(expenses).replace('.', '').replace(',', '').isdigit() else 0
                        except (ValueError, TypeError):
                            expenses = 0
                        
                        # Build amount string
                        amount_str = None
                        if income and income > 0:
                            amount_str = f"${income:,}"
                        elif expenses and expenses > 0:
                            amount_str = f"${expenses:,}"
                        
                        # Build description with lobbying activities
                        description_parts = []
                        if client_name and client_name != registrant_name:
                            description_parts.append(f"Client: {client_name}")
                        
                        # Extract lobbying activities/issues
                        lobbying_activities = filing.get('lobbying_activities', [])
                        if lobbying_activities:
                            logger.debug(f"🏛️ Found {len(lobbying_activities)} lobbying activities")
                            issues = []
                            for activity in lobbying_activities[:3]:  # Limit to first 3
                                issue = activity.get('general_issue_code_display', '')
                                if issue and issue not in issues:
                                    issues.append(issue)
                            if issues:
                                description_parts.append(f"Issues: {', '.join(issues)}")
                                logger.debug(f"📋 Lobbying issues: {issues}")
                        
                        # Determine primary entity name (prioritize match)
                        if client_name:
                            entity_name = client_name
                            role = f"Lobbying Client - {filing_type}"
                        else:
                            entity_name = registrant_name
                            role = f"Lobbyist/Registrant - {filing_type}"
                        
                        result = SearchResult(
                            source="senate_lda",
                            jurisdiction="Federal",
                            entity_name=entity_name or query,
                            role_or_title=role,
                            description='; '.join(description_parts) if description_parts else f"Federal lobbying {filing_type.lower()} for {filing_year}",
                            amount_or_value=amount_str,
                            filing_date=posted_date[:10] if posted_date else None,
                            url_to_original_record=f"https://lda.senate.gov/filings/public/filing/{filing_uuid}/" if filing_uuid else "https://lda.senate.gov",
                            metadata={
                                'filing_type': filing_type,
                                'filing_period': filing_period,
                                'filing_year': filing_year,
                                'client_name': client_name,
                                'registrant_name': registrant_name,
                                'income': income,
                                'expenses': expenses,
                                'lobbying_activities': lobbying_activities,
                                'filing_uuid': filing_uuid,
                                'posted_date': posted_date,
                                'registrant_address': filing.get('registrant', {}).get('address_1'),
                                'registrant_city': filing.get('registrant', {}).get('city'),
                                'registrant_state': filing.get('registrant', {}).get('state_display'),
                            }
                        )
                        results.append(result)
                        logger.info(f"✅ Added result: {entity_name} - {role}")
                        
                        # Limit results to prevent overwhelming response
                        if len(results) >= 50:
                            logger.info("🛑 Reached limit of 50 results, stopping")
                            break
                    
                    logger.info(f"📊 Finished processing. Found {len(results)} matching results out of {len(data['results'])} API results")
                else:
                    logger.warning("⚠️ No results returned from API response")
            else:
                logger.error(f"❌ API call failed with status {response.status_code}")
                logger.error(f"❌ Response text: {response.text[:200]}...")
    
    except Exception as e:
        logger.error(f"💥 Error searching Senate LDA: {str(e)}")
        import traceback
        logger.error(f"💥 Full traceback: {traceback.format_exc()}")
    
    logger.info(f"🏁 Senate LDA search for '{query}' completed. Returning {len(results)} results")
    return results

class SenateLDAAdapter:
    def __init__(self):
        self.name = "Senate LDA"
        
    async def search(self, query: str, year: int = None) -> List[Dict[str, Any]]:
        """Search Senate LDA data with enhanced historical data support"""
        logger.info(f"🔍 Starting enhanced Senate LDA search for query: '{query}', year: {year}")
        
        try:
            results = []
            base_url = "https://lda.senate.gov/api/v1/filings/"
            
            # Enhanced year handling for comprehensive historical analysis
            years_to_search = []
            if year:
                years_to_search = [year]
            else:
                # For comprehensive analysis, search recent years first, then expand if needed
                current_year = 2024
                years_to_search = [current_year, current_year - 1]  # Start with recent years
            
            # Enhanced query variations for better matching
            query_variations = self._generate_query_variations(query)
            
            # Set up headers with API key if available
            headers = {
                'User-Agent': 'Vetting-Intelligence-Search-Hub/1.0',
                'Accept': 'application/json'
            }
            
            lda_api_key = get_lda_api_key()
            if lda_api_key:
                headers['Authorization'] = f'Bearer {lda_api_key}'
                logger.info("🔑 Using authenticated API access (120 req/min)")
            else:
                logger.info("🌐 Using anonymous API access (15 req/min)")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                for search_year in years_to_search:
                    logger.info(f"📅 Searching Senate LDA for year: {search_year}")
                    
                    # Try different query variations
                    for query_variant in query_variations:
                        params = {
                            'page_size': 50,  # Increased for better coverage
                            'client_name': query_variant,
                            'filing_year': search_year,
                            'ordering': '-dt_posted'  # Get most recent first
                        }
                        
                        logger.info(f"📡 Making API call with query: '{query_variant}' for year {search_year}")
                        
                        try:
                            response = await client.get(base_url, params=params, headers=headers)
                            logger.info(f"📊 API Response Status: {response.status_code}")
                            
                            if response.status_code == 200:
                                data = response.json()
                                total_records = data.get('count', 0)
                                api_results = data.get('results', [])
                                
                                logger.info(f"📈 API returned {total_records} total records for {search_year} with query '{query_variant}'")
                                
                                # Process results for this year/query combo
                                for filing in api_results:
                                    if len(results) >= 100:  # Total limit across all searches
                                        break
                                        
                                    processed_result = await self._process_filing_enhanced(filing, query)
                                    if processed_result:
                                        results.append(processed_result)
                                        logger.debug(f"✅ Added Senate LDA result: {processed_result.get('title', 'Unknown')}")
                                
                                # If we found significant results for this variant/year, log success
                                if total_records > 0:
                                    logger.info(f"✅ Found {total_records} results for '{query_variant}' in {search_year}")
                                    break  # Move to next year after successful variant
                                    
                        except Exception as api_error:
                            logger.warning(f"⚠️ API error for year {search_year}, query '{query_variant}': {api_error}")
                            continue
                    
                    # If we found enough results, stop searching more years
                    if len(results) >= 50:
                        break
            
            logger.info(f"🏁 Enhanced Senate LDA search for '{query}' completed. Returning {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"❌ Senate LDA search error: {e}")
            return []
    
    async def search_historical_comprehensive(self, query: str, start_year: int = 2008, end_year: int = 2024) -> List[Dict[str, Any]]:
        """Comprehensive historical search across multiple years - used for correlation analysis"""
        logger.info(f"🏛️ Starting comprehensive historical Senate LDA search for '{query}' from {start_year} to {end_year}")
        
        try:
            all_results = []
            base_url = "https://lda.senate.gov/api/v1/filings/"
            query_variations = self._generate_query_variations(query)
            
            # Set up headers with API key if available
            headers = {
                'User-Agent': 'Vetting-Intelligence-Search-Hub/1.0',
                'Accept': 'application/json'
            }
            
            lda_api_key = get_lda_api_key()
            if lda_api_key:
                headers['Authorization'] = f'Bearer {lda_api_key}'
                logger.info("🔑 Using authenticated API access for historical search (120 req/min)")
            else:
                logger.info("🌐 Using anonymous API access for historical search (15 req/min)")
            
            async with httpx.AsyncClient(timeout=60.0) as client:  # Longer timeout for historical searches
                
                # Search year by year for comprehensive coverage
                for search_year in range(end_year, start_year - 1, -1):  # Start from most recent
                    year_results = []
                    
                    logger.info(f"📅 Historical search for year: {search_year}")
                    
                    for query_variant in query_variations:
                        try:
                            params = {
                                'page_size': 100,  # Maximum per page
                                'client_name': query_variant,
                                'filing_year': search_year,
                                'ordering': '-dt_posted'
                            }
                            
                            response = await client.get(base_url, params=params, headers=headers)
                            
                            if response.status_code == 200:
                                data = response.json()
                                total_count = data.get('count', 0)
                                api_results = data.get('results', [])
                                
                                if total_count > 0:
                                    logger.info(f"📊 Found {total_count} records for '{query_variant}' in {search_year}")
                                    
                                    # Process all results for this year/variant
                                    for filing in api_results:
                                        processed_result = await self._process_filing_enhanced(filing, query, include_detailed_metadata=True)
                                        if processed_result:
                                            year_results.append(processed_result)
                                    
                                    # If we found results with this variant, no need to try other variants for this year
                                    if year_results:
                                        break
                            
                            # Rate limiting for historical searches
                            await asyncio.sleep(0.2)
                            
                        except Exception as e:
                            logger.warning(f"⚠️ Error searching {search_year} with '{query_variant}': {e}")
                            continue
                    
                    all_results.extend(year_results)
                    
                    # Log progress every few years
                    if search_year % 3 == 0:
                        logger.info(f"📈 Historical search progress: {end_year - search_year + 1}/{end_year - start_year + 1} years complete, {len(all_results)} total results")
                    
                    # Stop if we've accumulated too many results
                    if len(all_results) >= 500:
                        logger.info(f"🛑 Reached historical result limit of 500, stopping at year {search_year}")
                        break
            
            logger.info(f"🏁 Comprehensive historical search complete. Found {len(all_results)} results across {end_year - start_year + 1} years")
            return all_results
            
        except Exception as e:
            logger.error(f"❌ Historical Senate LDA search error: {e}")
            return []
    
    def _generate_query_variations(self, query: str) -> List[str]:
        """Generate query variations for better matching"""
        variations = [query]
        
        # Add common corporate variations
        if not any(suffix in query.upper() for suffix in ['LLC', 'INC', 'CORP', 'COMPANY']):
            variations.extend([
                f"{query} LLC",
                f"{query} Inc",
                f"{query} Client Services LLC",
                f"{query} Client Services",
                f"{query} Corporation"
            ])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_variations = []
        for variation in variations:
            if variation not in seen:
                seen.add(variation)
                unique_variations.append(variation)
        
        logger.debug(f"📝 Generated query variations: {unique_variations}")
        return unique_variations
    
    async def _process_filing_enhanced(self, filing, original_query, include_detailed_metadata=False):
        """Enhanced processing of Senate LDA filing with detailed metadata for correlation analysis"""
        try:
            # Extract basic information
            client_info = filing.get('client', {})
            registrant_info = filing.get('registrant', {})
            
            client_name = client_info.get('name', '')
            registrant_name = registrant_info.get('name', '')
            filing_type = filing.get('filing_type_display', 'Unknown Filing')
            filing_year = filing.get('filing_year', '')
            filing_period = filing.get('filing_period_display', '')
            posted_date = filing.get('dt_posted', '')
            filing_uuid = filing.get('filing_uuid', '')
            
            # Enhanced financial information extraction
            income = filing.get('income', 0) or 0
            expenses = filing.get('expenses', 0) or 0
            
            # Safely convert to numeric values
            try:
                income = float(income) if income and str(income).replace('.', '').replace(',', '').replace('-', '').isdigit() else 0
            except (ValueError, TypeError):
                income = 0
                
            try:
                expenses = float(expenses) if expenses and str(expenses).replace('.', '').replace(',', '').replace('-', '').isdigit() else 0
            except (ValueError, TypeError):
                expenses = 0
            
            # Determine the primary amount (use the larger of income or expenses)
            total_amount = max(income, expenses)
            
            # Build amount string
            amount_str = None
            if total_amount > 0:
                amount_str = f"${total_amount:,.0f}"
            
            # Determine entity name and role
            if client_name:
                entity_name = client_name
                role = f"Federal Lobbying Client - {filing_type}"
            else:
                entity_name = registrant_name or original_query
                role = f"Federal Lobbying Registrant - {filing_type}"
            
            # Enhanced lobbying activities extraction
            lobbying_activities = filing.get('lobbying_activities', [])
            issues = []
            specific_issues = []
            
            for activity in lobbying_activities:
                if activity.get('general_issue_code_display'):
                    issues.append(activity.get('general_issue_code_display'))
                if activity.get('specific_issues'):
                    specific_issues.append(activity.get('specific_issues'))
            
            # Remove duplicates while preserving order
            issues = list(dict.fromkeys(issues))  
            
            # Build description
            description_parts = []
            if client_name:
                description_parts.append(f"Client: {client_name}")
            if registrant_name and registrant_name != client_name:
                description_parts.append(f"Registrant: {registrant_name}")
            if issues:
                description_parts.append(f"Issues: {', '.join(issues[:3])}")  # Limit to top 3
            
            description = '; '.join(description_parts) if description_parts else f"Federal lobbying {filing_type.lower()} for {filing_year}"
            
            # Enhanced metadata for correlation analysis
            enhanced_metadata = {
                'filing_type': filing_type,
                'filing_period': filing_period,
                'filing_year': filing_year,
                'client_name': client_name,
                'registrant_name': registrant_name,
                'income': income,
                'expenses': expenses,
                'total_amount': total_amount,
                'lobbying_activities': lobbying_activities,
                'filing_uuid': filing_uuid,
                'posted_date': posted_date,
                'issues': issues,
                'specific_issues': specific_issues[:5] if specific_issues else [],  # Limit to top 5
                'registrant_address': registrant_info.get('address_1'),
                'registrant_city': registrant_info.get('city'),
                'registrant_state': registrant_info.get('state_display'),
                'client_contact_name': client_info.get('contact_name'),
                'client_address': client_info.get('address_1'),
                'client_city': client_info.get('city'),
                'client_state': client_info.get('state_display')
            }
            
            # Build result dict
            result = {
                'title': role,
                'description': description,
                'amount': total_amount,  # Store as numeric for easier analysis
                'amount_display': amount_str,  # String version for display
                'date': posted_date[:10] if posted_date else None,
                'source': 'senate_lda',
                'vendor': entity_name,
                'agency': 'U.S. Senate LDA',
                'url': f"https://lda.senate.gov/filings/public/filing/{filing_uuid}/" if filing_uuid else "https://lda.senate.gov",
                'record_type': 'federal_lobbying',
                'metadata': enhanced_metadata
            }
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error processing enhanced Senate LDA filing: {e}")
            return None

# Module-level search function for backward compatibility
async def search(query: str, year: int = None) -> List[Dict[str, Any]]:
    """Module-level search function for Senate LDA data"""
    adapter = SenateLDAAdapter()
    return await adapter.search(query, year) 