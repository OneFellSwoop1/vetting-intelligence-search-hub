import aiohttp
import logging
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class NYSEthicsAdapter:
    def __init__(self):
        self.name = "NYS Ethics Lobbying"
        self.base_url = "https://data.ny.gov/resource"
        
    async def search(self, query: str, year: int = None) -> List[Dict[str, Any]]:
        """Search NY State lobbying data from Commission on Ethics and Lobbying in Government"""
        try:
            results = []
            
            async with aiohttp.ClientSession() as session:
                # Search multiple lobbying datasets
                
                # 1. Lobbyist Bi-Monthly Reports (most comprehensive data)
                await self._search_bimonthly_reports(session, query, year, results)
                
                # 2. Client Semi-Annual Reports
                await self._search_client_reports(session, query, year, results)
                
                # 3. Lobbyist Registration Statements
                await self._search_registrations(session, query, year, results)
                
            # Remove duplicates and sort by amount/date
            unique_results = self._deduplicate_results(results)
            sorted_results = sorted(unique_results, key=lambda x: (x.get('amount', 0) or 0), reverse=True)
            
            logger.info(f"NY State Ethics returned {len(sorted_results)} lobbying results for query: {query}")
            return sorted_results[:20]  # Limit to 20 results
            
        except Exception as e:
            logger.error(f"Error in NYSEthicsAdapter: {e}")
            return []
    
    async def _search_bimonthly_reports(self, session: aiohttp.ClientSession, query: str, year: int, results: List[Dict[str, Any]]):
        """Search Lobbyist Bi-Monthly Reports dataset"""
        try:
            # Updated dataset IDs for bi-monthly reports (found from data.ny.gov)
            dataset_ids = ["uxyi-nem6", "3bqx-tqde", "qym9-xzj6", "e6wn-kzub"]  # 2024, 2023, 2019+, 2022
            
            for dataset_id in dataset_ids:
                try:
                    url = f"{self.base_url}/{dataset_id}.json"
                    
                    # Build search conditions for lobbying data using correct field names
                    search_conditions = []
                    search_conditions.append(f"upper(contractual_client_name) like upper('%{query}%')")
                    search_conditions.append(f"upper(beneficial_client) like upper('%{query}%')")
                    search_conditions.append(f"upper(principal_lobbyist) like upper('%{query}%')")
                    search_conditions.append(f"upper(lobbying_subjects) like upper('%{query}%')")
                    
                    where_clause = " OR ".join(search_conditions)
                    
                    if year:
                        where_clause += f" AND reporting_year = '{year}'"
                    
                    params = {
                        "$limit": "50",
                        "$order": "current_period_compensation DESC NULLS LAST",
                        "$where": where_clause
                    }
                    
                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            logger.info(f"NY State Lobbying Reports ({dataset_id}) returned {len(data)} records")
                            
                            for item in data:
                                result = self._parse_lobbying_record(item)
                                if result:
                                    results.append(result)
                        else:
                            logger.debug(f"NY State dataset {dataset_id} returned status {response.status}")
                            
                except Exception as e:
                    logger.debug(f"Error searching dataset {dataset_id}: {e}")
                    continue
                    
        except Exception as e:
            logger.warning(f"Error searching bi-monthly reports: {e}")
    
    async def _search_client_reports(self, session: aiohttp.ClientSession, query: str, year: int, results: List[Dict[str, Any]]):
        """Search Client Semi-Annual Reports dataset"""
        try:
            # Same datasets as bi-monthly (they contain client data)
            dataset_ids = ["uxyi-nem6", "3bqx-tqde", "qym9-xzj6", "e6wn-kzub"]  # Client semi-annual reports
            
            for dataset_id in dataset_ids:
                try:
                    url = f"{self.base_url}/{dataset_id}.json"
                    
                    search_conditions = []
                    search_conditions.append(f"upper(contractual_client_name) like upper('%{query}%')")
                    search_conditions.append(f"upper(beneficial_client) like upper('%{query}%')")
                    search_conditions.append(f"upper(lobbying_subjects) like upper('%{query}%')")
                    search_conditions.append(f"upper(principal_lobbyist) like upper('%{query}%')")
                    
                    where_clause = " OR ".join(search_conditions)
                    
                    if year:
                        where_clause += f" AND reporting_year = '{year}'"
                    
                    params = {
                        "$limit": "30",
                        "$order": "current_period_compensation DESC NULLS LAST",
                        "$where": where_clause
                    }
                    
                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            logger.info(f"NY State Client Reports ({dataset_id}) returned {len(data)} records")
                            
                            for item in data:
                                result = self._parse_lobbying_record(item)
                                if result:
                                    results.append(result)
                                    
                except Exception as e:
                    logger.debug(f"Error searching client dataset {dataset_id}: {e}")
                    continue
                    
        except Exception as e:
            logger.warning(f"Error searching client reports: {e}")
    
    async def _search_registrations(self, session: aiohttp.ClientSession, query: str, year: int, results: List[Dict[str, Any]]):
        """Search Lobbyist Registration Statements dataset"""
        try:
            # Skip registrations for now since client semi-annual reports have more comprehensive data
            # We can add these later if needed
            pass
                    
        except Exception as e:
            logger.warning(f"Error searching registrations: {e}")
    
    def _parse_lobbying_record(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Parse a NY State lobbying record using correct field names"""
        try:
            # Extract key information using correct field names
            client_name = item.get('contractual_client_name', '') or item.get('beneficial_client', '')
            lobbyist_name = item.get('principal_lobbyist', '')
            compensation_amount = self._parse_amount(item.get('current_period_compensation'))
            reimbursement_amount = self._parse_amount(item.get('current_period_reimbursement'))
            total_amount = (compensation_amount or 0) + (reimbursement_amount or 0)
            
            # Build description
            description_parts = []
            if lobbyist_name:
                description_parts.append(f"Lobbyist: {lobbyist_name}")
            if item.get('lobbying_subjects'):
                subjects = item.get('lobbying_subjects', '').replace(';', ', ')
                description_parts.append(f"Subjects: {subjects}")
            if item.get('reporting_period'):
                description_parts.append(f"Period: {item.get('reporting_period')}")
            if item.get('type_of_lobbying_relationship'):
                description_parts.append(f"Type: {item.get('type_of_lobbying_relationship')}")
            if compensation_amount and compensation_amount > 0:
                description_parts.append(f"Compensation: ${compensation_amount:,.2f}")
            if reimbursement_amount and reimbursement_amount > 0:
                description_parts.append(f"Reimbursement: ${reimbursement_amount:,.2f}")
            
            description = " | ".join(description_parts)
            
            # Determine title
            title = f"NY State Lobbying: {client_name or 'Unknown Client'}"
            if item.get('reporting_year'):
                title += f" ({item.get('reporting_year')})"
            
            return {
                'title': title,
                'description': description,
                'amount': total_amount if total_amount > 0 else None,
                'date': f"{item.get('reporting_year', '')}-01-01",  # Use reporting year as date
                'source': 'nys_ethics',
                'vendor': lobbyist_name or client_name,
                'agency': 'NY State Commission on Ethics and Lobbying',
                'url': "https://ethics.ny.gov/public-data",
                'record_type': 'lobbying',
                'year': item.get('reporting_year'),
                'client': client_name,
                'lobbyist': lobbyist_name,
                'subjects': item.get('lobbying_subjects', ''),
                'filing_type': item.get('filing_type', ''),
                'raw_data': item
            }
            
        except Exception as e:
            logger.warning(f"Error parsing lobbying record: {e}")
            return None
    
    def _parse_amount(self, amount_str) -> float:
        """Safely parse amount string to float"""
        if not amount_str:
            return 0.0
        
        try:
            # Remove dollar signs, commas, and convert to float
            cleaned = str(amount_str).replace('$', '').replace(',', '').strip()
            if not cleaned or cleaned.lower() in ['n/a', 'none', 'null', '']:
                return 0.0
            return float(cleaned)
        except (ValueError, TypeError):
            return 0.0
    
    def _deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate results based on title and key characteristics"""
        seen = set()
        unique_results = []
        
        for result in results:
            # Create a key based on title, client, lobbyist, and year
            key = (
                result.get('title', ''),
                result.get('client', ''),
                result.get('lobbyist', ''),
                result.get('year', ''),
                result.get('date', '')
            )
            
            if key not in seen:
                seen.add(key)
                unique_results.append(result)
        
        return unique_results

# Module-level search function for backward compatibility
async def search(query: str, year: int = None) -> List[Dict[str, Any]]:
    """Module-level search function for NY State Ethics lobbying data"""
    adapter = NYSEthicsAdapter()
    return await adapter.search(query, year) 