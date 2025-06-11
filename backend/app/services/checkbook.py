import httpx
import logging
import asyncio
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import xmltodict
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

logger = logging.getLogger(__name__)

class CheckbookNYCService:
    """
    Service for NYC Checkbook using the official XML API
    Supports Contracts, Spending, Revenue, and custom Data-Feeds
    """
    
    def __init__(self):
        self.api_url = "https://www.checkbooknyc.com/api"
        self.app_token = os.getenv('NYC_CHECKBOOK_APP_TOKEN')
        
        # Setup Jinja2 templates
        template_dir = Path(__file__).parent.parent.parent / "templates" / "checkbook"
        self.jinja_env = Environment(loader=FileSystemLoader(template_dir))
        
        if not self.app_token:
            logger.warning("NYC_CHECKBOOK_APP_TOKEN not found in environment variables")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get required headers for Checkbook NYC API"""
        headers = {
            'Content-Type': 'application/xml',
            'User-Agent': 'Vetting-Intelligence-Search-Hub/1.0'
        }
        
        if self.app_token:
            headers['X-App-Token'] = self.app_token
            
        return headers
    
    def _render_xml_template(self, domain: str, **kwargs) -> str:
        """Render XML template for the given domain"""
        template_map = {
            'contracts': 'contracts.xml',
            'spending': 'spending.xml', 
            'revenue': 'revenue.xml',
            'data_feed': 'data_feed.xml'
        }
        
        template_file = template_map.get(domain.lower())
        if not template_file:
            raise ValueError(f"Unknown domain: {domain}")
        
        template = self.jinja_env.get_template(template_file)
        return template.render(**kwargs)
    
    def _normalize_xml_response(self, xml_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert XML response to normalized list of records"""
        records = []
        
        try:
            # Handle different response structures
            if 'response' in xml_data:
                data = xml_data['response']
            else:
                data = xml_data
            
            # Extract records - could be under different keys
            record_keys = ['record', 'records', 'row', 'rows', 'data']
            raw_records = None
            
            for key in record_keys:
                if key in data:
                    raw_records = data[key]
                    break
            
            if not raw_records:
                logger.warning("No records found in XML response")
                return []
            
            # Ensure it's a list
            if not isinstance(raw_records, list):
                raw_records = [raw_records]
            
            # Normalize each record
            for record in raw_records:
                normalized = self._normalize_record(record)
                if normalized:
                    records.append(normalized)
                    
        except Exception as e:
            logger.error(f"Error normalizing XML response: {e}")
            
        return records
    
    def _normalize_record(self, record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Normalize a single record to standard format"""
        try:
            # Common field mappings
            vendor = (record.get('vendor_name') or 
                     record.get('payee_name') or 
                     record.get('contractor_name') or 
                     record.get('entity_name', 'Unknown'))
            
            amount = (record.get('contract_amount') or
                     record.get('check_amount') or
                     record.get('amount') or
                     record.get('total_amount') or 0)
            
            # Convert amount to float
            if isinstance(amount, str):
                amount = float(amount.replace('$', '').replace(',', ''))
            else:
                amount = float(amount) if amount else 0
            
            agency = (record.get('agency_name') or 
                     record.get('department') or 
                     record.get('agency', 'Unknown'))
            
            date_field = (record.get('issue_date') or
                         record.get('contract_start_date') or
                         record.get('fiscal_year') or
                         record.get('date', ''))
            
            # Extract year from date
            year = None
            if date_field:
                if isinstance(date_field, str) and len(date_field) >= 4:
                    year = date_field[:4]
                elif isinstance(date_field, (int, float)):
                    year = str(int(date_field))
            
            description = (record.get('description') or
                          record.get('contract_purpose') or
                          record.get('purpose') or
                          f"{vendor} - {agency}")
            
            return {
                'title': f"NYC {record.get('type_of_data', 'Record')}: {vendor}",
                'description': f"Amount: ${amount:,.2f} | Agency: {agency} | {description[:100]}",
                'amount': amount,
                'date': str(date_field).split('T')[0] if date_field else '',
                'source': 'checkbook',
                'vendor': vendor,
                'agency': agency,
                'record_type': record.get('type_of_data', '').lower(),
                'year': year,
                'raw_data': record  # Keep original for debugging
            }
            
        except Exception as e:
            logger.error(f"Error normalizing record: {e}")
            return None
    
    async def fetch(self, 
                   domain: str,
                   fiscal_year: int = None,
                   feed_id: str = None,
                   records_from: int = 1,
                   max_records: int = 20000) -> List[Dict[str, Any]]:
        """
        Fetch data from Checkbook NYC official XML API
        
        Args:
            domain: One of 'contracts', 'spending', 'revenue', 'data_feed'
            fiscal_year: Optional fiscal year filter
            feed_id: Optional feed ID for data_feed domain
            records_from: Starting record number for pagination
            max_records: Maximum records per request (up to 20,000)
        """
        
        all_records = []
        current_from = records_from
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                while True:
                    # Prepare template context
                    context = {
                        'records_from': current_from,
                        'max_records': min(max_records, 20000),
                        'fiscal_year': fiscal_year,
                        'feed_id': feed_id,
                        'search_criteria': {}
                    }
                    
                    # Add search criteria if needed
                    if fiscal_year:
                        context['search_criteria']['fiscal_year'] = fiscal_year
                    
                    # Render XML request body
                    xml_body = self._render_xml_template(domain, **context)
                    logger.info(f"Requesting {domain} data from record {current_from}")
                    
                    # Make API request
                    response = await client.post(
                        self.api_url,
                        headers=self._get_headers(),
                        content=xml_body
                    )
                    
                    if response.status_code != 200:
                        logger.error(f"API request failed: {response.status_code} - {response.text}")
                        break
                    
                    # Parse XML response
                    try:
                        xml_data = xmltodict.parse(response.text)
                        records = self._normalize_xml_response(xml_data)
                        
                        if not records:
                            logger.info("No more records returned, ending pagination")
                            break
                        
                        all_records.extend(records)
                        logger.info(f"Retrieved {len(records)} records, total: {len(all_records)}")
                        
                        # Check if we should continue pagination
                        if len(records) < max_records:
                            # Less records than requested means we've reached the end
                            break
                        
                        current_from += len(records)
                        
                        # Safety limit to prevent infinite loops
                        if len(all_records) >= 100000:  # 100k record safety limit
                            logger.warning("Safety limit reached, stopping pagination")
                            break
                            
                    except Exception as e:
                        logger.error(f"Error parsing XML response: {e}")
                        break
                
        except Exception as e:
            logger.error(f"Error fetching {domain} data: {e}")
        
        logger.info(f"Completed {domain} fetch: {len(all_records)} total records")
        return all_records

# Helper function for backward compatibility
async def fetch_checkbook_data(domain: str, fiscal_year: int = None, feed_id: str = None) -> List[Dict[str, Any]]:
    """Convenience function for fetching Checkbook NYC data"""
    service = CheckbookNYCService()
    return await service.fetch(domain, fiscal_year=fiscal_year, feed_id=feed_id) 