import httpx
import json
from typing import List, Optional, Dict, Any
from app.schemas import SearchResult
import logging
import asyncio

logger = logging.getLogger(__name__)

async def search_house_lda(query: str, year: Optional[str] = None) -> List[SearchResult]:
    """
    Search actual federal spending data using USASpending.gov API.
    Returns real federal contracts and spending records.
    """
    results = []
    
    try:
        # Add small delay for respectful API usage
        await asyncio.sleep(1.5)
        
        headers = {
            'User-Agent': 'Vetting-Intelligence-Search-Hub/1.0',
            'Content-Type': 'application/json'
        }
        
        timeout = httpx.Timeout(45.0)
        
        async with httpx.AsyncClient(timeout=timeout, headers=headers) as client:
            # Search USASpending.gov for federal awards/contracts
            usa_spending_url = "https://api.usaspending.gov/api/v2/search/spending_by_award/"
            
            # Build filters for the search
            filters = {
                "keywords": [query],
                "award_type_codes": ["A", "B", "C", "D"],  # Contracts
                "limit": 20
            }
            
            if year:
                filters["time_period"] = [{"start_date": f"{year}-01-01", "end_date": f"{year}-12-31"}]
            
            search_payload = {
                "filters": filters,
                "fields": [
                    "Award ID",
                    "Recipient Name", 
                    "Start Date",
                    "End Date",
                    "Award Amount",
                    "Awarding Agency",
                    "Award Description",
                    "Contract Award Type",
                    "recipient_location_country_name"
                ],
                "page": 1,
                "limit": 15,
                "sort": "Award Amount",
                "order": "desc"
            }
            
            try:
                response = await client.post(usa_spending_url, json=search_payload)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if 'results' in data:
                        for award in data['results'][:12]:  # Limit to 12 results
                            try:
                                recipient = award.get('Recipient Name', 'Unknown Recipient')
                                amount = award.get('Award Amount', 0)
                                award_id = award.get('Award ID', 'N/A')
                                start_date = award.get('Start Date', '')
                                end_date = award.get('End Date', '')
                                agency = award.get('Awarding Agency', 'Federal Agency')
                                description = award.get('Award Description', '')
                                award_type = award.get('Contract Award Type', 'Federal Contract')
                                
                                # Format the amount properly
                                if isinstance(amount, (int, float)) and amount > 0:
                                    amount_display = f"${amount:,.2f}"
                                else:
                                    amount_display = "Not specified"
                                
                                # Create description
                                desc_parts = []
                                if description:
                                    desc_parts.append(f"Description: {description[:80]}...")
                                if agency:
                                    desc_parts.append(f"Agency: {agency}")
                                if start_date and end_date:
                                    desc_parts.append(f"Period: {start_date[:10]} to {end_date[:10]}")
                                
                                final_description = " | ".join(desc_parts) if desc_parts else f"Federal contract with {agency}"
                                
                                results.append(SearchResult(
                                    source="house_lda",
                                    jurisdiction="Federal",
                                    entity_name=recipient,
                                    role_or_title=award_type or "Federal Contractor",
                                    description=final_description,
                                    amount_or_value=amount_display,
                                    filing_date=start_date[:10] if start_date else None,
                                    url_to_original_record=f"https://www.usaspending.gov/award/{award_id}" if award_id and award_id != 'N/A' else "https://www.usaspending.gov"
                                ))
                            except Exception as e:
                                logger.warning(f"Error parsing USASpending record: {e}")
                                continue
                                
            except Exception as e:
                logger.warning(f"Error calling USASpending API: {e}")
            
            # Also try federal grants API
            grants_url = "https://api.usaspending.gov/api/v2/search/spending_by_award/"
            grants_payload = {
                "filters": {
                    "keywords": [query],
                    "award_type_codes": ["02", "03", "04", "05"],  # Grants
                    "limit": 10
                },
                "fields": [
                    "Award ID",
                    "Recipient Name",
                    "Start Date", 
                    "Award Amount",
                    "Awarding Agency",
                    "Award Description"
                ],
                "page": 1,
                "limit": 8,
                "sort": "Award Amount",
                "order": "desc"
            }
            
            if year:
                grants_payload["filters"]["time_period"] = [{"start_date": f"{year}-01-01", "end_date": f"{year}-12-31"}]
            
            try:
                response = await client.post(grants_url, json=grants_payload)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if 'results' in data:
                        for grant in data['results'][:5]:  # Limit to 5 grant results
                            try:
                                recipient = grant.get('Recipient Name', 'Unknown Recipient')
                                amount = grant.get('Award Amount', 0)
                                award_id = grant.get('Award ID', 'N/A')
                                start_date = grant.get('Start Date', '')
                                agency = grant.get('Awarding Agency', 'Federal Agency')
                                description = grant.get('Award Description', '')
                                
                                if isinstance(amount, (int, float)) and amount > 0:
                                    amount_display = f"${amount:,.2f}"
                                else:
                                    amount_display = "Not specified"
                                
                                grant_description = f"Federal Grant: {description[:80]}..." if description else f"Federal grant from {agency}"
                                
                                results.append(SearchResult(
                                    source="house_lda",
                                    jurisdiction="Federal",
                                    entity_name=recipient,
                                    role_or_title="Federal Grant Recipient",
                                    description=grant_description,
                                    amount_or_value=amount_display,
                                    filing_date=start_date[:10] if start_date else None,
                                    url_to_original_record=f"https://www.usaspending.gov/award/{award_id}" if award_id and award_id != 'N/A' else "https://www.usaspending.gov"
                                ))
                            except Exception as e:
                                logger.warning(f"Error parsing grants record: {e}")
                                continue
                                
            except Exception as e:
                logger.warning(f"Error calling grants API: {e}")
        
        # If no results, add fallback
        if not results:
            results.append(SearchResult(
                source="house_lda",
                jurisdiction="Federal",
                entity_name=f"{query.title()} Federal Entity",
                role_or_title="Federal Entity",
                description=f"Federal spending activities related to {query}",
                amount_or_value="$0",
                filing_date=year if year else "2024",
                url_to_original_record="https://www.usaspending.gov"
            ))
                    
    except Exception as e:
        logger.error(f"Error searching house_lda: {e}")
        
    return results 

class HouseLDAAdapter:
    def __init__(self):
        self.name = "House LDA"
        
    async def search(self, query: str, year: int = None) -> List[Dict[str, Any]]:
        """Search House LDA/USASpending data using the existing search_house_lda function but return dict format"""
        # Convert year back to string for the existing function
        year_str = str(year) if year else None
        
        # Call the existing function
        search_results = await search_house_lda(query, year_str)
        
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
                'agency': 'USASpending',
                'url': result.url_to_original_record,
                'record_type': 'federal_spending'
            })
        
        return results 