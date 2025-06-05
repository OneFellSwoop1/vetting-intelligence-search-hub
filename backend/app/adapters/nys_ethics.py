import aiohttp
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class NYSEthicsAdapter:
    def __init__(self):
        self.name = "NYS Ethics"
        self.base_url = "https://data.ny.gov/resource"
        
    async def search(self, query: str, year: int = None) -> List[Dict[str, Any]]:
        """Search NY State procurement and grants data"""
        try:
            results = []
            
            # NY State Procurement dataset
            procurement_url = f"{self.base_url}/8w5p-k45m.json"
            
            # Build search query
            search_conditions = []
            search_conditions.append(f"upper(vendor_name) like upper('%{query}%')")
            search_conditions.append(f"upper(procurement_description) like upper('%{query}%')")
            search_conditions.append(f"upper(authority_name) like upper('%{query}%')")
            
            where_clause = " OR ".join(search_conditions)
            
            if year:
                where_clause += f" AND date_extract_y(award_date) = {year}"
                
            procurement_params = {
                "$limit": "20",
                "$order": "contract_amount DESC",
                "$where": where_clause
            }
            
            async with aiohttp.ClientSession() as session:
                # Get procurement data
                async with session.get(procurement_url, params=procurement_params) as response:
                    if response.status == 200:
                        procurement_data = await response.json()
                        logger.info(f"NY State Procurement API returned {len(procurement_data)} records")
                        for item in procurement_data:
                            try:
                                amount = float(item.get('contract_amount', 0))
                                date_str = item.get('award_date', '').split('T')[0] if item.get('award_date') else ''
                                
                                result = {
                                    'title': item.get('procurement_description', 'NY State Procurement'),
                                    'description': f"{item.get('type_of_procurement', '')} - {item.get('award_process', '')}",
                                    'amount': amount,
                                    'date': date_str,
                                    'source': 'NY State Procurement',
                                    'vendor': item.get('vendor_name', ''),
                                    'agency': item.get('authority_name', ''),
                                    'url': "https://data.ny.gov/Transparency/Authority-Procurement-Information/8w5p-k45m",
                                    'record_type': 'procurement'
                                }
                                results.append(result)
                            except (ValueError, TypeError) as e:
                                logger.warning(f"Error parsing procurement amount: {e}")
                                continue
                    else:
                        logger.error(f"NY State Procurement API error: {response.status} - {await response.text()}")
                        
            logger.info(f"NY State Ethics returned {len(results)} results for query: {query}")
            return results
            
        except Exception as e:
            logger.error(f"Error in NYSEthicsAdapter: {e}")
            return [] 