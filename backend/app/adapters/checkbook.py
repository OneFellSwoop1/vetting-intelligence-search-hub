import httpx
import logging
import asyncio
import os
from typing import List, Dict, Any
from datetime import datetime
import json

# Import the official XML service
from ..services.checkbook import CheckbookNYCService

logger = logging.getLogger(__name__)

class CheckbookNYCAdapter:
    """
    Adapter for NYC Checkbook using the official XML API
    Routes calls to the CheckbookNYCService for consistency
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
        """Search NYC budget data - maps to revenue for XML API"""
        logger.info(f"Budget search (mapped to revenue) for: {query}, year: {year}")
        # For the XML API, budget data comes through revenue endpoint
        return await self.search_revenue(query, year)

    async def search(self, query: str, year: int = None) -> List[Dict[str, Any]]:
        """
        Unified search across all NYC financial data types using official XML API
        """
        logger.info(f"Starting unified CheckbookNYC search for: '{query}' (year: {year})")
        
        try:
            # Search all three main data types in parallel
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
            
            # Remove duplicates and sort by amount
            seen = set()
            unique_results = []
            for result in all_results:
                key = (result.get('vendor', ''), result.get('agency', ''), result.get('amount', 0))
                if key not in seen:
                    seen.add(key)
                    unique_results.append(result)
            
            unique_results.sort(key=lambda x: x.get('amount', 0) or 0, reverse=True)
            final_results = unique_results[:50]  # Limit total results
            
            logger.info(f"Unified CheckbookNYC search completed: {len(final_results)} total results for '{query}'")
            return final_results
            
        except Exception as e:
            logger.error(f"Error in unified CheckbookNYC search: {e}")
            return []

# Module-level search function for backward compatibility
async def search(query: str, year: int = None) -> List[Dict[str, Any]]:
    """Module-level search function for CheckbookNYC data"""
    adapter = CheckbookNYCAdapter()
    return await adapter.search(query, year)