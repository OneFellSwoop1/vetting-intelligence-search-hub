import httpx
import logging
import asyncio
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

async def search_checkbook(query: str, year: int = None) -> List[Dict[str, Any]]:
    """
    Search NYC Contract Awards and Spending data via accessible Socrata API
    Uses accessible datasets for NYC spending and contract information
    """
    results = []
    
    try:
        # Add delay for respectful API usage
        await asyncio.sleep(1.0)
        
        async with httpx.AsyncClient(timeout=45.0) as client:
            
            # Use multiple accessible NYC datasets
            datasets = [
                {
                    "id": "qyyg-4tf5",
                    "name": "Recent Contract Awards",
                    "url": "https://data.cityofnewyork.us/resource/qyyg-4tf5.json"
                }
            ]
            
            for dataset in datasets:
                try:
                    # Build search parameters for Socrata API
                    params = {
                        "$limit": 500,
                        "$where": f"upper(vendor_name) LIKE '%{query.upper()}%' OR upper(short_title) LIKE '%{query.upper()}%' OR upper(agency_name) LIKE '%{query.upper()}%'",
                        "$order": "contract_amount DESC"
                    }
                    
                    # Add year filter if specified
                    if year:
                        year_filter = f"date_extract_y(start_date) = {year}"
                        if "$where" in params:
                            params["$where"] += f" AND {year_filter}"
                        else:
                            params["$where"] = year_filter
                    
                    logger.info(f"Calling {dataset['name']} API for '{query}' with limit={params['$limit']}...")
                    
                    response = await client.get(dataset["url"], params=params)
                    
                    if response.status_code == 200:
                        data = response.json()
                        logger.info(f"{dataset['name']} returned {len(data)} raw results")
                        
                        for item in data:
                            try:
                                # Extract and format the contract/spending record
                                amount_str = item.get('contract_amount', item.get('start_amount_sum', item.get('amount', '0')))
                                try:
                                    amount = float(amount_str)
                                    amount_formatted = f"${amount:,.2f}"
                                except (ValueError, TypeError):
                                    amount = 0
                                    amount_formatted = "$0.00"
                                
                                result = {
                                    'entity_name': item.get('vendor_name', item.get('vendor', 'Unknown Vendor')),
                                    'amount': amount_formatted,
                                    'date': item.get('start_date', item.get('issue_date', 'Unknown Date'))[:10] if item.get('start_date') or item.get('issue_date') else 'Unknown Date',
                                    'agency': item.get('agency_name', item.get('agency', 'Unknown Agency')),
                                    'description': item.get('short_title', item.get('purpose', item.get('description', 'No description available'))),
                                    'document_id': item.get('pin', item.get('contract_number', item.get('document_id', ''))),
                                    'dataset': dataset['name'],
                                    'source': 'checkbook'
                                }
                                
                                results.append(result)
                                
                            except Exception as e:
                                logger.warning(f"Error processing {dataset['name']} record: {e}")
                                continue
                        
                    else:
                        logger.warning(f"{dataset['name']} API error: HTTP {response.status_code}")
                        logger.debug(f"Response: {response.text[:200]}")
                
                except Exception as e:
                    logger.warning(f"Error searching {dataset['name']}: {e}")
                    continue
        
        logger.info(f"NYC Checkbook search completed. Found {len(results)} total results for '{query}'")
        
        # Sort by amount (descending) and limit to top 200 results
        results.sort(key=lambda x: float(x['amount'].replace('$', '').replace(',', '')) if x['amount'] != '$0.00' else 0, reverse=True)
        return results[:200]
        
    except Exception as e:
        logger.error(f"NYC Checkbook search error: {e}")
        return []

# Add alias for compatibility with websocket imports
async def search(query: str, year: int = None) -> List[Dict[str, Any]]:
    """Alias for search_checkbook to maintain compatibility."""
    return await search_checkbook(query, year)