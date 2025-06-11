import httpx
import logging
import asyncio
import os
from typing import List, Dict, Any
from datetime import datetime
import json

# Import the new service
from ..services.checkbook import CheckbookNYCService

logger = logging.getLogger(__name__)

class CheckbookNYCAdapter:
    """
    Adapter for NYC Checkbook using the official XML API
    Maintains backward compatibility while using the new service layer
    """
    
    def __init__(self):
        self.service = CheckbookNYCService()
        
    async def search_contracts(self, query: str, year: int = None) -> List[Dict[str, Any]]:
        """Search NYC contracts data using official XML API"""
        logger.info(f"Searching contracts for: {query}, year: {year}")
        try:
            results = await self.service.fetch('contracts', fiscal_year=year)
            
            # Filter results based on query
            filtered_results = []
            query_lower = query.lower()
            
            for result in results:
                # Search in vendor, agency, and description fields
                searchable_text = (
                    result.get('vendor', '').lower() +
                    result.get('agency', '').lower() + 
                    result.get('description', '').lower()
                )
                
                if query_lower in searchable_text:
                    result['record_type'] = 'contract'
                    filtered_results.append(result)
            
            logger.info(f"Contracts search returned {len(filtered_results)} filtered results")
            return filtered_results[:20]  # Limit for backward compatibility
            
        except Exception as e:
            logger.error(f"Error searching contracts: {e}")
            return []

    async def search_spending(self, query: str, year: int = None) -> List[Dict[str, Any]]:
        """Search NYC spending data using official XML API"""
        logger.info(f"Searching spending for: {query}, year: {year}")
        try:
            results = await self.service.fetch('spending', fiscal_year=year)
            
            # Filter results based on query
            filtered_results = []
            query_lower = query.lower()
            
            for result in results:
                # Search in vendor, agency, and description fields
                searchable_text = (
                    result.get('vendor', '').lower() +
                    result.get('agency', '').lower() + 
                    result.get('description', '').lower()
                )
                
                if query_lower in searchable_text:
                    result['record_type'] = 'spending'
                    filtered_results.append(result)
            
            logger.info(f"Spending search returned {len(filtered_results)} filtered results")
            return filtered_results[:20]  # Limit for backward compatibility
            
        except Exception as e:
            logger.error(f"Error searching spending: {e}")
            return []

    async def search_revenue(self, query: str, year: int = None) -> List[Dict[str, Any]]:
        """Search NYC revenue data using official XML API"""
        logger.info(f"Searching revenue for: {query}, year: {year}")
        try:
            results = await self.service.fetch('revenue', fiscal_year=year)
            
            # Filter results based on query
            filtered_results = []
            query_lower = query.lower()
            
            for result in results:
                # Search in agency and description fields
                searchable_text = (
                    result.get('agency', '').lower() + 
                    result.get('description', '').lower()
                )
                
                if query_lower in searchable_text:
                    result['record_type'] = 'revenue'
                    filtered_results.append(result)
            
            logger.info(f"Revenue search returned {len(filtered_results)} filtered results")
            return filtered_results[:15]  # Limit for backward compatibility
            
        except Exception as e:
            logger.error(f"Error searching revenue: {e}")
            return []

    async def search_budget(self, query: str, year: int = None) -> List[Dict[str, Any]]:
        """Search NYC budget data - kept for backward compatibility"""
        logger.info(f"Budget search deprecated - using revenue data for: {query}, year: {year}")
        # For backward compatibility, redirect budget searches to revenue
        return await self.search_revenue(query, year)

    async def search(self, query: str, year: int = None) -> List[Dict[str, Any]]:
        """
        Search all NYC financial data types: contracts, spending, revenue
        Updated to use the official XML API with all four data types
        """
        logger.info(f"Starting unified CheckbookNYC search for: '{query}' (year: {year})")
        
        try:
            # Search all four data types in parallel
            tasks = [
                self.search_contracts(query, year),
                self.search_spending(query, year),
                self.search_revenue(query, year),
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Combine all results
            all_results = []
            data_types = ['contracts', 'spending', 'revenue']
            
            for i, result_set in enumerate(results):
                if isinstance(result_set, list):
                    all_results.extend(result_set)
                    logger.info(f"{data_types[i]} returned {len(result_set)} results")
                elif isinstance(result_set, Exception):
                    logger.error(f"Error in {data_types[i]} search: {result_set}")
            
            # Sort by amount (highest first) and limit results
            all_results.sort(key=lambda x: x.get('amount', 0) or 0, reverse=True)
            final_results = all_results[:50]  # Limit total results
            
            logger.info(f"CheckbookNYC unified search completed: {len(final_results)} total results for '{query}'")
            return final_results
            
        except Exception as e:
            logger.error(f"Error in unified CheckbookNYC search: {e}")
            return []

# Module-level search function for backward compatibility
async def search(query: str, year: int = None) -> List[Dict[str, Any]]:
    """Module-level search function for CheckbookNYC data"""
    adapter = CheckbookNYCAdapter()
    return await adapter.search(query, year)