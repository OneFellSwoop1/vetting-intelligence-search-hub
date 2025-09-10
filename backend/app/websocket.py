import asyncio
import json
import logging
from typing import Dict, List, Set
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

# Import adapters directly
from .adapters.checkbook import CheckbookNYCAdapter
from .adapters.nys_ethics import NYSEthicsAdapter  
from .adapters.senate_lda import SenateHouseLDAAdapter
from .adapters.nyc_lobbyist import NYCLobbyistAdapter

async def search_all_sources(query: str, year: str = None, jurisdiction: str = None):
    """Search all sources for WebSocket streaming."""
    # Convert year to int if provided
    year_int = int(year) if year and year.isdigit() else None
    
    # Define all search tasks
    search_tasks = [
        ("checkbook", CheckbookNYCAdapter().search(query, year_int)),
        ("nys_ethics", NYSEthicsAdapter().search(query, year_int)),
        ("senate_lda", SenateHouseLDAAdapter().search(query, year_int)),
        ("nyc_lobbyist", NYCLobbyistAdapter().search(query, year_int)),
    ]
    
    # Execute all searches in parallel
    results = []
    total_hits = {}
    
    # Run all tasks concurrently
    task_results = await asyncio.gather(*[task for _, task in search_tasks], return_exceptions=True)
    
    # Process results
    for i, (source, _) in enumerate(search_tasks):
        try:
            task_result = task_results[i]
            
            if isinstance(task_result, Exception):
                logger.error(f"Error in {source} search: {task_result}")
                total_hits[source] = 0
            else:
                source_results = task_result
                total_hits[source] = len(source_results)
                results.extend(source_results)
        except Exception as e:
            logger.error(f"Unexpected error processing {source} results: {e}")
            total_hits[source] = 0
    
    return {
        'results': results,
        'total_hits': total_hits
    }

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.search_sessions: Dict[str, Dict] = {}
        self.session_cleanup_task = None

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"WebSocket client {client_id} connected")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.search_sessions:
            del self.search_sessions[client_id]
        logger.info(f"WebSocket client {client_id} disconnected")
        
        # Start cleanup task if needed
        if not self.session_cleanup_task or self.session_cleanup_task.done():
            self.session_cleanup_task = asyncio.create_task(self._cleanup_stale_sessions())
    
    async def _cleanup_stale_sessions(self):
        """Clean up stale search sessions to prevent memory leaks."""
        import time
        try:
            await asyncio.sleep(300)  # Wait 5 minutes before cleanup
            current_time = time.time()
            stale_sessions = []
            
            for client_id, session in self.search_sessions.items():
                # Remove sessions older than 30 minutes or for disconnected clients
                session_age = current_time - session.get('created_at', current_time)
                if session_age > 1800 or client_id not in self.active_connections:
                    stale_sessions.append(client_id)
            
            for client_id in stale_sessions:
                if client_id in self.search_sessions:
                    del self.search_sessions[client_id]
                    logger.info(f"Cleaned up stale search session for {client_id}")
                    
        except Exception as e:
            logger.error(f"Error during session cleanup: {e}")

    async def send_personal_message(self, message: dict, client_id: str):
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to {client_id}: {e}")
                self.disconnect(client_id)

    async def broadcast(self, message: dict):
        disconnected_clients = []
        for client_id, connection in self.active_connections.items():
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error broadcasting to {client_id}: {e}")
                disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            self.disconnect(client_id)

    async def stream_search_progress(self, client_id: str, query: str, year: str = None, jurisdiction: str = None):
        """Stream real-time search progress to a specific client."""
        if client_id not in self.active_connections:
            return

        # Initialize search session
        import time
        self.search_sessions[client_id] = {
            'query': query,
            'year': year,
            'jurisdiction': jurisdiction,
            'status': 'started',
            'sources_completed': 0,
            'total_sources': 4,
            'results': [],
            'total_hits': {},
            'created_at': time.time()
        }

        # Send initial status
        await self.send_personal_message({
            'type': 'search_started',
            'query': query,
            'session_id': client_id,
            'total_sources': 4
        }, client_id)

        # Data sources to search
        sources = [
            {'name': 'checkbook', 'display_name': 'NYC Checkbook'},
            {'name': 'nys_ethics', 'display_name': 'NY State Ethics'},
            {'name': 'senate_lda', 'display_name': 'Federal Lobbying (Senate LDA)'},
            {'name': 'nyc_lobbyist', 'display_name': 'NYC Lobbyist'}
        ]

        try:
            # Perform search once and distribute results by source
            logger.info(f"🔍 Performing unified search for all sources")
            search_results = await search_all_sources(query, year, jurisdiction)
            all_results = search_results.get('results', [])
            total_hits = search_results.get('total_hits', {})
            
            # Group results by source
            results_by_source = {}
            for result in all_results:
                source_name = result.get('source', 'unknown')
                if source_name not in results_by_source:
                    results_by_source[source_name] = []
                results_by_source[source_name].append(result)

            # Stream results for each source
            for i, source in enumerate(sources):
                if client_id not in self.active_connections:
                    break

                # Send source start notification
                await self.send_personal_message({
                    'type': 'source_started',
                    'source': source['name'],
                    'display_name': source['display_name'],
                    'progress': i + 1,
                    'total': len(sources)
                }, client_id)

                try:
                    # Add realistic delay for user experience
                    await asyncio.sleep(0.3)
                    
                    # Get results for this specific source
                    source_results = results_by_source.get(source['name'], [])
                    source_count = len(source_results)

                    # Update session
                    if client_id in self.search_sessions:
                        self.search_sessions[client_id]['sources_completed'] += 1
                        self.search_sessions[client_id]['results'].extend(source_results)
                        self.search_sessions[client_id]['total_hits'][source['name']] = source_count

                    # Send source completion notification
                    await self.send_personal_message({
                        'type': 'source_completed',
                        'source': source['name'],
                        'display_name': source['display_name'],
                        'count': source_count,
                        'results': source_results[:5],  # Send first 5 results for preview
                        'progress': i + 1,
                        'total': len(sources)
                    }, client_id)

                except Exception as e:
                    logger.error(f"Error processing {source['name']} results: {e}")
                    await self.send_personal_message({
                        'type': 'source_error',
                        'source': source['name'],
                        'display_name': source['display_name'],
                        'error': str(e),
                        'progress': i + 1,
                        'total': len(sources)
                    }, client_id)

            # Send final completion
            if client_id in self.search_sessions:
                session = self.search_sessions[client_id]
                await self.send_personal_message({
                    'type': 'search_completed',
                    'query': query,
                    'total_results': len(session['results']),
                    'total_hits': session['total_hits'],
                    'session_id': client_id
                }, client_id)

        except Exception as e:
            logger.error(f"Error in search stream for {client_id}: {e}")
            await self.send_personal_message({
                'type': 'search_error',
                'error': str(e),
                'session_id': client_id
            }, client_id)

    async def handle_message(self, websocket: WebSocket, client_id: str, data: dict):
        """Handle incoming WebSocket messages."""
        message_type = data.get('type')
        
        if message_type == 'search':
            query = data.get('query', '').strip()
            year = data.get('year')
            jurisdiction = data.get('jurisdiction')
            
            if len(query) >= 3:
                # Start streaming search in background
                asyncio.create_task(self.stream_search_progress(client_id, query, year, jurisdiction))
            else:
                await self.send_personal_message({
                    'type': 'error',
                    'message': 'Query must be at least 3 characters long'
                }, client_id)
        
        elif message_type == 'ping':
            await self.send_personal_message({
                'type': 'pong',
                'timestamp': data.get('timestamp')
            }, client_id)
        
        elif message_type == 'cancel_search':
            if client_id in self.search_sessions:
                del self.search_sessions[client_id]
            await self.send_personal_message({
                'type': 'search_cancelled'
            }, client_id)
        
        else:
            await self.send_personal_message({
                'type': 'error',
                'message': f'Unknown message type: {message_type}'
            }, client_id)

# Global connection manager instance
manager = ConnectionManager()

async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """Main WebSocket endpoint handler."""
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                await manager.handle_message(websocket, client_id, message)
            except json.JSONDecodeError:
                await manager.send_personal_message({
                    'type': 'error',
                    'message': 'Invalid JSON format'
                }, client_id)
            except Exception as e:
                logger.error(f"Error handling message from {client_id}: {e}")
                await manager.send_personal_message({
                    'type': 'error',
                    'message': 'Internal server error'
                }, client_id)
                
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error for {client_id}: {e}")
        manager.disconnect(client_id) 