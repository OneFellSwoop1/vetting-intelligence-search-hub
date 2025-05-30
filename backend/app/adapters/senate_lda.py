import asyncio
import httpx
import os
from typing import List, Optional, Dict, Any
from app.schemas import SearchResult
import logging

logger = logging.getLogger(__name__)

# Real Senate LDA API v1 endpoints
LDA_API_BASE = "https://lda.senate.gov/api/v1"

async def search_senate_lda(query: str, year: Optional[str] = None) -> List[SearchResult]:
    """
    Search the U.S. Senate LDA API v1 for federal lobbying registrations and reports.
    Uses the official REST API endpoint with API authentication.
    """
    results = []
    
    # Get API key from environment
    api_key = os.getenv('SENATE_LDA_API_KEY')
    
    try:
        # Add small delay for respectful API usage
        await asyncio.sleep(0.5)
        
        headers = {
            'User-Agent': 'Vetting-Intelligence-Search-Hub/1.0',
            'Accept': 'application/json'
        }
        
        # Add API key to headers if available
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'
            # Also try X-API-Key header format
            headers['X-API-Key'] = api_key
        
        # Search registrations
        async with httpx.AsyncClient(timeout=10) as client:
            # Try registrations endpoint
            registrations_url = "https://lda.senate.gov/api/v1/registrations"
            registrations_params = {
                'limit': 50,
                'registrant_name': query
            }
            
            if api_key:
                registrations_params['api_key'] = api_key
            
            response = await client.get(registrations_url, headers=headers, params=registrations_params)
            
            if response.status_code == 200:
                data = response.json()
                if 'results' in data and data['results']:
                    for item in data['results']:
                        # Extract detailed information for modal display
                        description_parts = []
                        
                        # Build comprehensive description
                        if item.get('client_name'):
                            description_parts.append(f"Client: {item['client_name']}")
                        if item.get('client_general_description'):
                            description_parts.append(f"Business: {item['client_general_description']}")
                        if item.get('registrant_general_description'):
                            description_parts.append(f"Registrant: {item['registrant_general_description']}")
                        if item.get('lobbying_issues'):
                            issues = item['lobbying_issues']
                            if isinstance(issues, list):
                                description_parts.append(f"Issues: {', '.join(issues[:3])}{'...' if len(issues) > 3 else ''}")
                            else:
                                description_parts.append(f"Issues: {issues}")
                        
                        # Create enriched result
                        result = SearchResult(
                            source="senate_lda",
                            jurisdiction="Federal",
                            entity_name=item.get('registrant_name', query),
                            role_or_title=f"Lobbying Registration - {item.get('client_name', 'Unknown Client')}",
                            description='; '.join(description_parts) if description_parts else f"Federal lobbying registration for {query}",
                            amount_or_value=item.get('income_amount') or item.get('expense_amount') or "Amount not disclosed",
                            filing_date=item.get('dt_posted', item.get('effective_date', '')),
                            url_to_original_record=f"https://lda.senate.gov/filings/public/filing/registration/{item.get('registration_id', '')}" if item.get('registration_id') else "https://lda.senate.gov",
                            # Additional metadata for modal
                            metadata={
                                'filing_type': 'Lobbying Registration',
                                'client_name': item.get('client_name'),
                                'client_description': item.get('client_general_description'),
                                'registrant_description': item.get('registrant_general_description'),
                                'lobbying_issues': item.get('lobbying_issues'),
                                'registration_id': item.get('registration_id'),
                                'contact_name': item.get('contact_name'),
                                'principal_place_of_business': item.get('principal_place_of_business'),
                                'income_amount': item.get('income_amount'),
                                'expense_amount': item.get('expense_amount')
                            }
                        )
                        results.append(result)
            
            # Also search quarterly reports
            reports_url = "https://lda.senate.gov/api/v1/reports"
            reports_params = {
                'limit': 50,
                'registrant_name': query
            }
            
            if api_key:
                reports_params['api_key'] = api_key
                
            response = await client.get(reports_url, headers=headers, params=reports_params)
            
            if response.status_code == 200:
                data = response.json()
                if 'results' in data and data['results']:
                    for item in data['results']:
                        # Extract detailed information for reports
                        description_parts = []
                        
                        if item.get('client_name'):
                            description_parts.append(f"Client: {item['client_name']}")
                        if item.get('lobbying_activities'):
                            activities = item['lobbying_activities']
                            if isinstance(activities, list) and activities:
                                description_parts.append(f"Activities: {activities[0][:100]}{'...' if len(activities[0]) > 100 else ''}")
                            elif isinstance(activities, str):
                                description_parts.append(f"Activities: {activities[:100]}{'...' if len(activities) > 100 else ''}")
                        if item.get('houses_and_agencies'):
                            description_parts.append(f"Lobbied: {', '.join(item['houses_and_agencies'][:3]) if isinstance(item['houses_and_agencies'], list) else item['houses_and_agencies']}")
                        
                        result = SearchResult(
                            source="senate_lda",
                            jurisdiction="Federal", 
                            entity_name=item.get('registrant_name', query),
                            role_or_title=f"Quarterly Lobbying Report - {item.get('client_name', 'Unknown Client')}",
                            description='; '.join(description_parts) if description_parts else f"Federal lobbying report for {query}",
                            amount_or_value=item.get('income_amount') or item.get('expense_amount') or "Amount not disclosed",
                            filing_date=item.get('dt_posted', item.get('reporting_period_end', '')),
                            url_to_original_record=f"https://lda.senate.gov/filings/public/filing/report/{item.get('filing_uuid', '')}" if item.get('filing_uuid') else "https://lda.senate.gov",
                            # Additional metadata for modal
                            metadata={
                                'filing_type': 'Quarterly Report',
                                'client_name': item.get('client_name'),
                                'lobbying_activities': item.get('lobbying_activities'),
                                'houses_and_agencies': item.get('houses_and_agencies'),
                                'filing_uuid': item.get('filing_uuid'),
                                'reporting_period_start': item.get('reporting_period_start'),
                                'reporting_period_end': item.get('reporting_period_end'),
                                'income_amount': item.get('income_amount'),
                                'expense_amount': item.get('expense_amount'),
                                'posted_by_name': item.get('posted_by_name')
                            }
                        )
                        results.append(result)
    
    except Exception as e:
        logger.error(f"Error searching Senate LDA: {str(e)}")
    
    logger.info(f"Senate LDA search for '{query}' returned {len(results)} results")
    return results

async def _search_registrations(client: httpx.AsyncClient, query: str, year: Optional[str] = None, api_key: Optional[str] = None) -> List[SearchResult]:
    """Search LDA registrations"""
    results = []
    
    try:
        params = {
            'limit': 50
        }
        
        # Add query parameters for search
        if query:
            params['registrant_name'] = query
        
        if year:
            params['filing_year'] = year
        
        response = await client.get(f"{LDA_API_BASE}/registrations", params=params)
        
        if response.status_code == 200:
            data = response.json()
            
            # Handle different response formats
            records = data.get('results', data.get('data', data))
            if isinstance(records, dict):
                records = [records]
            
            for record in records[:20]:  # Limit results
                try:
                    registrant_name = record.get('registrant_name', '')
                    client_name = record.get('client_name', '')
                    filing_date = record.get('filing_date', record.get('dt_posted', ''))
                    filing_id = record.get('filing_uuid', record.get('id', ''))
                    
                    # Create result for registrant
                    if registrant_name and query.lower() in registrant_name.lower():
                        result = SearchResult(
                            source="senate_lda",
                            jurisdiction="Federal",
                            entity_name=registrant_name,
                            role_or_title="Lobbying Registrant",
                            description=f"Federal Lobbying Registration for client: {client_name}" if client_name else "Federal Lobbying Registration",
                            amount_or_value=None,
                            filing_date=filing_date[:10] if filing_date else None,
                            url_to_original_record=f"https://lda.senate.gov/filings/public/filing/{filing_id}" if filing_id else None
                        )
                        results.append(result)
                    
                    # Create result for client if different from registrant
                    if client_name and query.lower() in client_name.lower() and client_name != registrant_name:
                        result = SearchResult(
                            source="senate_lda",
                            jurisdiction="Federal",
                            entity_name=client_name,
                            role_or_title="Lobbying Client",
                            description=f"Federal Lobbying Client (Registrant: {registrant_name})" if registrant_name else "Federal Lobbying Client",
                            amount_or_value=None,
                            filing_date=filing_date[:10] if filing_date else None,
                            url_to_original_record=f"https://lda.senate.gov/filings/public/filing/{filing_id}" if filing_id else None
                        )
                        results.append(result)
                        
                except Exception as e:
                    logger.warning(f"Error parsing registration record: {e}")
                    continue
                    
    except Exception as e:
        logger.error(f"Error searching registrations: {e}")
    
    return results

async def _search_reports(client: httpx.AsyncClient, query: str, year: Optional[str] = None, api_key: Optional[str] = None) -> List[SearchResult]:
    """Search LDA quarterly reports"""
    results = []
    
    try:
        params = {
            'limit': 50
        }
        
        # Add query parameters for search
        if query:
            params['registrant_name'] = query
        
        if year:
            params['filing_year'] = year
        
        response = await client.get(f"{LDA_API_BASE}/reports", params=params)
        
        if response.status_code == 200:
            data = response.json()
            
            # Handle different response formats
            records = data.get('results', data.get('data', data))
            if isinstance(records, dict):
                records = [records]
            
            for record in records[:20]:  # Limit results
                try:
                    registrant_name = record.get('registrant_name', '')
                    client_name = record.get('client_name', '')
                    amount = record.get('amount', record.get('income', ''))
                    filing_date = record.get('filing_date', record.get('dt_posted', ''))
                    filing_period = record.get('filing_period', '')
                    filing_id = record.get('filing_uuid', record.get('id', ''))
                    issues = record.get('lobbying_issues', [])
                    
                    # Create description from issues
                    description_parts = []
                    if filing_period:
                        description_parts.append(f"{filing_period} Report")
                    if isinstance(issues, list) and issues:
                        issue_codes = [issue.get('general_issue_code', '') for issue in issues[:3] if isinstance(issue, dict)]
                        if issue_codes:
                            description_parts.append(f"Issues: {', '.join(filter(None, issue_codes))}")
                    
                    description = " - ".join(description_parts) if description_parts else "Federal Lobbying Report"
                    
                    # Create result for registrant
                    if registrant_name and query.lower() in registrant_name.lower():
                        result = SearchResult(
                            source="senate_lda",
                            jurisdiction="Federal",
                            entity_name=registrant_name,
                            role_or_title="Lobbying Report",
                            description=f"{description} (Client: {client_name})" if client_name else description,
                            amount_or_value=f"${float(amount):,.2f}" if amount and str(amount).replace('.','').replace('-','').isdigit() else amount,
                            filing_date=filing_date[:10] if filing_date else None,
                            url_to_original_record=f"https://lda.senate.gov/filings/public/filing/{filing_id}" if filing_id else None
                        )
                        results.append(result)
                    
                    # Create result for client if different from registrant
                    if client_name and query.lower() in client_name.lower() and client_name != registrant_name:
                        result = SearchResult(
                            source="senate_lda",
                            jurisdiction="Federal",
                            entity_name=client_name,
                            role_or_title="Lobbying Client Report",
                            description=f"{description} (Registrant: {registrant_name})" if registrant_name else description,
                            amount_or_value=f"${float(amount):,.2f}" if amount and str(amount).replace('.','').replace('-','').isdigit() else amount,
                            filing_date=filing_date[:10] if filing_date else None,
                            url_to_original_record=f"https://lda.senate.gov/filings/public/filing/{filing_id}" if filing_id else None
                        )
                        results.append(result)
                        
                except Exception as e:
                    logger.warning(f"Error parsing report record: {e}")
                    continue
                    
    except Exception as e:
        logger.error(f"Error searching reports: {e}")
    
    return results 

class SenateLDAAdapter:
    def __init__(self):
        self.name = "Senate LDA"
        
    async def search(self, query: str, year: int = None) -> List[Dict[str, Any]]:
        """Search Senate LDA data using the existing search_senate_lda function but return dict format"""
        # Convert year back to string for the existing function
        year_str = str(year) if year else None
        
        # Call the existing function
        search_results = await search_senate_lda(query, year_str)
        
        # Convert SearchResult objects to dict format
        results = []
        for result in search_results:
            results.append({
                'title': result.role_or_title,
                'description': result.description,
                'amount': result.amount_or_value,
                'date': result.filing_date,
                'source': result.source,
                'vendor': result.entity_name,
                'agency': 'Senate LDA',
                'url': result.url_to_original_record,
                'record_type': 'lobbying'
            })
        
        return results 