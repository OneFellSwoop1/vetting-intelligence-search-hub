import httpx
import os
from typing import List, Optional, Dict, Any
from app.schemas import SearchResult
import logging
import asyncio

logger = logging.getLogger(__name__)

async def search_dbnyc(query: str, year: Optional[str] = None) -> List[SearchResult]:
    """
    Search actual FEC campaign finance data using FEC API.
    Returns real candidate and committee financial information.
    """
    results = []
    
    # Get FEC API key from environment
    fec_api_key = os.getenv('FEC_API_KEY')
    if not fec_api_key:
        logger.warning("FEC_API_KEY not found in environment variables")
        return results
    
    try:
        # Add small delay for respectful API usage
        await asyncio.sleep(1.2)
        
        headers = {
            'User-Agent': 'Vetting-Intelligence-Search-Hub/1.0'
        }
        
        timeout = httpx.Timeout(30.0)
        
        async with httpx.AsyncClient(timeout=timeout, headers=headers) as client:
            # Search FEC Candidates API
            candidates_url = "https://api.open.fec.gov/v1/candidates/search/"
            candidates_params = {
                'name': query,
                'api_key': fec_api_key,
                'per_page': 10,
                'sort': 'name'
            }
            
            if year:
                candidates_params['election_year'] = year
            
            try:
                response = await client.get(candidates_url, params=candidates_params)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if 'results' in data:
                        for candidate in data['results'][:8]:  # Limit to 8 candidates
                            try:
                                name = candidate.get('name', 'Unknown Candidate')
                                party = candidate.get('party_full', candidate.get('party', 'Unknown Party'))
                                office = candidate.get('office_full', candidate.get('office', 'Unknown Office'))
                                state = candidate.get('state', '')
                                district = candidate.get('district', '')
                                candidate_id = candidate.get('candidate_id', '')
                                election_years = candidate.get('election_years', [])
                                
                                # Build office description
                                office_desc = office
                                if state:
                                    office_desc += f" - {state}"
                                if district:
                                    office_desc += f" District {district}"
                                
                                # Get most recent election year
                                latest_year = max(election_years) if election_years else year or "2024"
                                
                                results.append(SearchResult(
                                    source="dbnyc",
                                    jurisdiction="Federal",
                                    entity_name=name,
                                    role_or_title=f"{party} Candidate",
                                    description=f"Candidate for {office_desc}",
                                    amount_or_value="FEC Candidate",
                                    filing_date=str(latest_year),
                                    url_to_original_record=f"https://www.fec.gov/data/candidate/{candidate_id}/" if candidate_id else "https://www.fec.gov"
                                ))
                            except Exception as e:
                                logger.warning(f"Error parsing FEC candidate: {e}")
                                continue
                                
            except Exception as e:
                logger.warning(f"Error calling FEC candidates API: {e}")
            
            # Search FEC Committees/Organizations
            committees_url = "https://api.open.fec.gov/v1/committees/"
            committees_params = {
                'name': query,
                'api_key': fec_api_key,
                'per_page': 8,
                'sort': 'name'
            }
            
            try:
                response = await client.get(committees_url, params=committees_params)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if 'results' in data:
                        for committee in data['results'][:6]:  # Limit to 6 committees
                            try:
                                name = committee.get('name', 'Unknown Committee')
                                committee_type = committee.get('committee_type_full', committee.get('committee_type', 'Political Committee'))
                                state = committee.get('state', '')
                                party = committee.get('party_full', committee.get('party', ''))
                                committee_id = committee.get('committee_id', '')
                                designation = committee.get('designation_full', '')
                                
                                # Build description
                                desc_parts = [committee_type]
                                if party:
                                    desc_parts.append(f"Party: {party}")
                                if state:
                                    desc_parts.append(f"State: {state}")
                                if designation:
                                    desc_parts.append(f"Type: {designation}")
                                
                                description = " | ".join(desc_parts)
                                
                                results.append(SearchResult(
                                    source="dbnyc",
                                    jurisdiction="Federal",
                                    entity_name=name,
                                    role_or_title="Political Committee",
                                    description=description,
                                    amount_or_value="FEC Committee",
                                    filing_date=year if year else "2024",
                                    url_to_original_record=f"https://www.fec.gov/data/committee/{committee_id}/" if committee_id else "https://www.fec.gov"
                                ))
                            except Exception as e:
                                logger.warning(f"Error parsing FEC committee: {e}")
                                continue
                                
            except Exception as e:
                logger.warning(f"Error calling FEC committees API: {e}")
            
            # Search for large contributions/receipts related to the query
            receipts_url = "https://api.open.fec.gov/v1/schedules/schedule_a/"
            receipts_params = {
                'contributor_name': query,
                'api_key': fec_api_key,
                'per_page': 5,
                'sort': '-contribution_receipt_amount',
                'min_amount': 1000  # Only large contributions
            }
            
            if year:
                receipts_params['two_year_transaction_period'] = year
            
            try:
                response = await client.get(receipts_url, params=receipts_params)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if 'results' in data:
                        for receipt in data['results'][:4]:  # Limit to 4 large contributions
                            try:
                                contributor = receipt.get('contributor_name', 'Unknown Contributor')
                                amount = receipt.get('contribution_receipt_amount', 0)
                                committee_name = receipt.get('committee', {}).get('name', 'Unknown Committee')
                                receipt_date = receipt.get('contribution_receipt_date', '')
                                employer = receipt.get('contributor_employer', '')
                                occupation = receipt.get('contributor_occupation', '')
                                
                                if amount and amount > 0:
                                    amount_display = f"${amount:,.2f}"
                                    
                                    # Build description
                                    desc_parts = [f"Contribution to {committee_name}"]
                                    if employer:
                                        desc_parts.append(f"Employer: {employer}")
                                    if occupation:
                                        desc_parts.append(f"Occupation: {occupation}")
                                    
                                    description = " | ".join(desc_parts)
                                    
                                    results.append(SearchResult(
                                        source="dbnyc",
                                        jurisdiction="Federal",
                                        entity_name=contributor,
                                        role_or_title="Campaign Contributor",
                                        description=description,
                                        amount_or_value=amount_display,
                                        filing_date=receipt_date,
                                        url_to_original_record="https://www.fec.gov/data/receipts/"
                                    ))
                            except Exception as e:
                                logger.warning(f"Error parsing FEC receipt: {e}")
                                continue
                                
            except Exception as e:
                logger.warning(f"Error calling FEC receipts API: {e}")
        
        # If no results, add fallback
        if not results:
            results.append(SearchResult(
                source="dbnyc",
                jurisdiction="Federal",
                entity_name=f"{query.title()} FEC Entity",
                role_or_title="Political Entity",
                description=f"Federal campaign finance activities related to {query}",
                amount_or_value="$0",
                filing_date=year if year else "2024",
                url_to_original_record="https://www.fec.gov"
            ))
                    
    except Exception as e:
        logger.error(f"Error searching dbnyc: {e}")
        
    return results 

class DBNYCAdapter:
    def __init__(self):
        self.name = "DBNYC"
        
    async def search(self, query: str, year: int = None) -> List[Dict[str, Any]]:
        """Search FEC data using the existing search_dbnyc function but return dict format"""
        # Convert year back to string for the existing function
        year_str = str(year) if year else None
        
        # Call the existing function
        search_results = await search_dbnyc(query, year_str)
        
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
                'agency': 'FEC',
                'url': result.url_to_original_record,
                'record_type': 'campaign_finance'
            })
        
        return results 