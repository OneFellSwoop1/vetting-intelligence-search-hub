import asyncio
import json
import logging
from typing import Dict, List, Set
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

# Import adapters directly
from app.adapters.checkbook import CheckbookAdapter
  
from app.adapters.nys_ethics import NYSEthicsAdapter
from app.adapters.senate_lda import SenateLDAAdapter
from app.adapters.house_lda import HouseLDAAdapter
from app.adapters.nyc_lobbyist import NYCLobbyistAdapter

# Initialize adapters
checkbook_adapter = CheckbookAdapter()

nys_ethics_adapter = NYSEthicsAdapter()
senate_lda_adapter = SenateLDAAdapter()
house_lda_adapter = HouseLDAAdapter()
nyc_lobbyist_adapter = NYCLobbyistAdapter()

async def search_all_sources(query: str, year: str = None, jurisdiction: str = None):
    """Search all sources for WebSocket streaming."""
    # Convert year to int if provided
    year_int = int(year) if year and year.isdigit() else None
    
    # Define all search tasks
    search_tasks = [
        ("checkbook", checkbook_adapter.search(query, year_int)),

        ("nys_ethics", nys_ethics_adapter.search(query, year_int)),
        ("senate_lda", senate_lda_adapter.search(query, year_int)),
        ("house_lda", house_lda_adapter.search(query, year_int)),
        ("nyc_lobbyist", nyc_lobbyist_adapter.search(query, year_int)),
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
        self.search_sessions[client_id] = {
            'query': query,
            'year': year,
            'jurisdiction': jurisdiction,
            'status': 'started',
            'sources_completed': 0,
            'total_sources': 5,
            'results': [],
            'total_hits': {}
        }

        # Send initial status
        await self.send_personal_message({
            'type': 'search_started',
            'query': query,
            'session_id': client_id,
            'total_sources': 5
        }, client_id)

        # Data sources to search
        sources = [
            {'name': 'checkbook', 'display_name': 'NYC Checkbook'},
            {'name': 'nys_ethics', 'display_name': 'NY State Ethics'},
            {'name': 'senate_lda', 'display_name': 'Senate LDA'},
            {'name': 'house_lda', 'display_name': 'House LDA'},
            {'name': 'nyc_lobbyist', 'display_name': 'NYC Lobbyist'}
        ]

        try:
            # Search each source and stream results
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
                    # Simulate individual source search (in real implementation, this would call specific source APIs)
                    await asyncio.sleep(0.5)  # Simulate API call delay
                    
                    # For demo purposes, we'll use the existing search function
                    # In production, you'd want to search each source individually
                    if i == 0:  # Only do actual search on first iteration to avoid duplicates
                        search_results = await search_all_sources(query, year, jurisdiction)
                        all_results = search_results.get('results', [])
                        total_hits = search_results.get('total_hits', {})
                    else:
                        all_results = []
                        total_hits = {}

                    # Filter results for this source (demo)
                    source_results = [r for r in all_results if r.get('source') == source['name']]
                    source_count = len(source_results)

                    # Update session
                    if client_id in self.search_sessions:
                        self.search_sessions[client_id]['sources_completed'] += 1
                        self.search_sessions[client_id]['results'].extend(source_results)
                        if source['name'] in total_hits:
                            self.search_sessions[client_id]['total_hits'][source['name']] = total_hits[source['name']]

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
                    logger.error(f"Error searching {source['name']}: {e}")
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