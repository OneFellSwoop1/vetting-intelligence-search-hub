"""
Resource management for HTTP clients and other resources in the Vetting Intelligence Search Hub.
Ensures proper cleanup and prevents resource leaks.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional, AsyncGenerator
import httpx
from .error_handling import get_timeout_config

logger = logging.getLogger(__name__)

class HTTPClientManager:
    """
    Manages HTTP client instances with proper resource cleanup.
    Provides connection pooling and timeout management.
    """
    
    def __init__(self):
        self._clients: Dict[str, httpx.AsyncClient] = {}
        self._client_configs: Dict[str, Dict[str, Any]] = {}
        
    def register_client(
        self,
        name: str,
        base_url: Optional[str] = None,
        timeout: Optional[httpx.Timeout] = None,
        limits: Optional[httpx.Limits] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ):
        """
        Register a named HTTP client configuration.
        
        Args:
            name: Client identifier
            base_url: Base URL for the client
            timeout: Timeout configuration
            limits: Connection limits
            headers: Default headers
            **kwargs: Additional client options
        """
        if timeout is None:
            timeout = get_timeout_config("http_request")
        
        if limits is None:
            limits = httpx.Limits(
                max_keepalive_connections=20,
                max_connections=100,
                keepalive_expiry=30.0
            )
        
        config = {
            "base_url": base_url,
            "timeout": timeout,
            "limits": limits,
            "headers": headers or {},
            **kwargs
        }
        
        self._client_configs[name] = config
        logger.info(f"Registered HTTP client configuration: {name}")
    
    async def get_client(self, name: str) -> httpx.AsyncClient:
        """
        Get or create an HTTP client by name.
        
        Args:
            name: Client identifier
            
        Returns:
            HTTP client instance
            
        Raises:
            ValueError: If client configuration not found
        """
        if name not in self._client_configs:
            raise ValueError(f"HTTP client '{name}' not registered")
        
        if name not in self._clients:
            config = self._client_configs[name]
            self._clients[name] = httpx.AsyncClient(**config)
            logger.info(f"Created HTTP client: {name}")
        
        return self._clients[name]
    
    @asynccontextmanager
    async def client_context(self, name: str) -> AsyncGenerator[httpx.AsyncClient, None]:
        """
        Context manager for HTTP client usage.
        
        Args:
            name: Client identifier
            
        Yields:
            HTTP client instance
        """
        client = await self.get_client(name)
        try:
            yield client
        except Exception as e:
            logger.error(f"Error using HTTP client {name}: {e}")
            raise
    
    async def close_client(self, name: str):
        """
        Close a specific HTTP client.
        
        Args:
            name: Client identifier
        """
        if name in self._clients:
            await self._clients[name].aclose()
            del self._clients[name]
            logger.info(f"Closed HTTP client: {name}")
    
    async def close_all_clients(self):
        """Close all HTTP clients."""
        for name in list(self._clients.keys()):
            await self.close_client(name)
        logger.info("Closed all HTTP clients")
    
    def get_client_stats(self) -> Dict[str, Any]:
        """Get statistics about managed clients."""
        return {
            "registered_configs": len(self._client_configs),
            "active_clients": len(self._clients),
            "client_names": list(self._client_configs.keys())
        }

# Global HTTP client manager
http_manager = HTTPClientManager()

# Register default client configurations
http_manager.register_client(
    "default",
    timeout=get_timeout_config("http_request"),
    headers={"User-Agent": "Vetting-Intelligence-Search-Hub/2.0"}
)

http_manager.register_client(
    "checkbook",
    base_url="https://www.checkbooknyc.com/api",
    timeout=httpx.Timeout(connect=10.0, read=45.0, write=10.0, pool=5.0),
    headers={
        "User-Agent": "Vetting-Intelligence-Search-Hub/2.0",
        "Accept": "application/json"
    }
)

http_manager.register_client(
    "socrata",
    base_url="https://data.cityofnewyork.us",
    timeout=httpx.Timeout(connect=10.0, read=30.0, write=10.0, pool=5.0),
    headers={
        "User-Agent": "Vetting-Intelligence-Search-Hub/2.0",
        "Accept": "application/json"
    }
)

http_manager.register_client(
    "senate_lda",
    base_url="https://lda.senate.gov",
    timeout=httpx.Timeout(connect=15.0, read=60.0, write=15.0, pool=5.0),
    headers={
        "User-Agent": "Vetting-Intelligence-Search-Hub/2.0",
        "Accept": "application/json"
    }
)

class ResourceCleanupManager:
    """
    Manages cleanup of various resources during application shutdown.
    """
    
    def __init__(self):
        self._cleanup_tasks = []
        self._background_tasks = set()
    
    def register_cleanup(self, cleanup_func, *args, **kwargs):
        """
        Register a cleanup function to be called during shutdown.
        
        Args:
            cleanup_func: Function to call for cleanup
            *args: Arguments to pass to cleanup function
            **kwargs: Keyword arguments to pass to cleanup function
        """
        self._cleanup_tasks.append((cleanup_func, args, kwargs))
    
    def add_background_task(self, task: asyncio.Task):
        """
        Track a background task for proper cleanup.
        
        Args:
            task: Background task to track
        """
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)
    
    async def cleanup_all(self):
        """
        Execute all registered cleanup tasks.
        """
        logger.info("Starting resource cleanup...")
        
        # Cancel background tasks
        if self._background_tasks:
            logger.info(f"Cancelling {len(self._background_tasks)} background tasks")
            for task in self._background_tasks:
                task.cancel()
            
            # Wait for tasks to complete cancellation
            if self._background_tasks:
                await asyncio.gather(*self._background_tasks, return_exceptions=True)
        
        # Execute cleanup tasks
        for cleanup_func, args, kwargs in self._cleanup_tasks:
            try:
                if asyncio.iscoroutinefunction(cleanup_func):
                    await cleanup_func(*args, **kwargs)
                else:
                    cleanup_func(*args, **kwargs)
                logger.info(f"Completed cleanup: {cleanup_func.__name__}")
            except Exception as e:
                logger.error(f"Error during cleanup {cleanup_func.__name__}: {e}")
        
        # Close HTTP clients
        await http_manager.close_all_clients()
        
        logger.info("Resource cleanup completed")

# Global resource cleanup manager
cleanup_manager = ResourceCleanupManager()

# Register HTTP manager cleanup
cleanup_manager.register_cleanup(http_manager.close_all_clients)

@asynccontextmanager
async def managed_http_client(
    client_name: str = "default"
) -> AsyncGenerator[httpx.AsyncClient, None]:
    """
    Context manager for managed HTTP client usage.
    
    Args:
        client_name: Name of the HTTP client configuration
        
    Yields:
        HTTP client instance
    """
    async with http_manager.client_context(client_name) as client:
        yield client

async def safe_background_task(coro, *args, **kwargs):
    """
    Create and track a background task with proper error handling.
    
    Args:
        coro: Coroutine to run as background task
        *args: Arguments to pass to coroutine
        **kwargs: Keyword arguments to pass to coroutine
        
    Returns:
        Background task
    """
    async def wrapped_coro():
        try:
            if args or kwargs:
                await coro(*args, **kwargs)
            else:
                await coro
        except asyncio.CancelledError:
            logger.info(f"Background task cancelled: {coro}")
            raise
        except Exception as e:
            logger.error(f"Error in background task {coro}: {e}")
    
    task = asyncio.create_task(wrapped_coro())
    cleanup_manager.add_background_task(task)
    return task