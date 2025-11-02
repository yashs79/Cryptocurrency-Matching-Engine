"""
WebSocket Connection Manager

Manages WebSocket connections and broadcasts.
"""

from typing import Dict, Set, Optional
from dataclasses import dataclass
from datetime import datetime, UTC
import json
import logging
from fastapi import WebSocket

logger = logging.getLogger(__name__)


@dataclass
class WebSocketMessage:
    """WebSocket message structure"""
    channel: str
    event: str
    data: dict
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(UTC).isoformat()
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps({
            "channel": self.channel,
            "event": self.event,
            "data": self.data,
            "timestamp": self.timestamp
        })


class ConnectionManager:
    """
    Manages WebSocket connections and message broadcasting.
    
    Supports multiple channels:
    - orderbook:{symbol} - Order book updates
    - trades:{symbol} - Trade stream
    - orders:{user_id} - User order updates
    - market - General market data
    """
    
    def __init__(self):
        # Active connections by channel
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        
        # Connection metadata
        self.connection_info: Dict[WebSocket, dict] = {}
        
        logger.info("ConnectionManager initialized")
    
    async def connect(self, websocket: WebSocket, channel: str, user_id: Optional[str] = None):
        """
        Accept and register a new WebSocket connection.
        
        Args:
            websocket: WebSocket connection
            channel: Channel to subscribe to
            user_id: Optional user ID for authentication
        """
        await websocket.accept()
        
        # Add to channel
        if channel not in self.active_connections:
            self.active_connections[channel] = set()
        self.active_connections[channel].add(websocket)
        
        # Store connection info
        self.connection_info[websocket] = {
            "channel": channel,
            "user_id": user_id,
            "connected_at": datetime.now(UTC).isoformat()
        }
        
        logger.info(f"WebSocket connected to channel '{channel}' (user: {user_id})")
        
        # Send welcome message
        welcome = WebSocketMessage(
            channel=channel,
            event="connected",
            data={
                "message": f"Connected to {channel}",
                "user_id": user_id
            }
        )
        await websocket.send_text(welcome.to_json())
    
    def disconnect(self, websocket: WebSocket):
        """
        Remove a WebSocket connection.
        
        Args:
            websocket: WebSocket connection to remove
        """
        # Get connection info
        info = self.connection_info.get(websocket, {})
        channel = info.get("channel")
        user_id = info.get("user_id")
        
        # Remove from channel
        if channel and channel in self.active_connections:
            self.active_connections[channel].discard(websocket)
            
            # Clean up empty channels
            if not self.active_connections[channel]:
                del self.active_connections[channel]
        
        # Remove connection info
        if websocket in self.connection_info:
            del self.connection_info[websocket]
        
        logger.info(f"WebSocket disconnected from channel '{channel}' (user: {user_id})")
    
    async def send_personal_message(self, message: WebSocketMessage, websocket: WebSocket):
        """
        Send a message to a specific connection.
        
        Args:
            message: Message to send
            websocket: Target WebSocket connection
        """
        try:
            await websocket.send_text(message.to_json())
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)
    
    async def broadcast_to_channel(self, message: WebSocketMessage, channel: str):
        """
        Broadcast a message to all connections in a channel.
        
        Args:
            message: Message to broadcast
            channel: Target channel
        """
        if channel not in self.active_connections:
            return
        
        # Get all connections for this channel
        connections = list(self.active_connections[channel])
        
        # Send to all connections
        disconnected = []
        for connection in connections:
            try:
                await connection.send_text(message.to_json())
            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected connections
        for connection in disconnected:
            self.disconnect(connection)
        
        logger.debug(f"Broadcasted to {len(connections) - len(disconnected)} connections in '{channel}'")
    
    async def broadcast_orderbook_update(self, symbol: str, orderbook_data: dict):
        """
        Broadcast order book update to subscribers.
        
        Args:
            symbol: Trading symbol
            orderbook_data: Order book data
        """
        message = WebSocketMessage(
            channel=f"orderbook:{symbol}",
            event="orderbook_update",
            data=orderbook_data
        )
        await self.broadcast_to_channel(message, f"orderbook:{symbol}")
    
    async def broadcast_trade(self, symbol: str, trade_data: dict):
        """
        Broadcast trade execution to subscribers.
        
        Args:
            symbol: Trading symbol
            trade_data: Trade data
        """
        message = WebSocketMessage(
            channel=f"trades:{symbol}",
            event="trade",
            data=trade_data
        )
        await self.broadcast_to_channel(message, f"trades:{symbol}")
    
    async def send_order_update(self, user_id: str, order_data: dict):
        """
        Send order update to a specific user.
        
        Args:
            user_id: User ID
            order_data: Order data
        """
        message = WebSocketMessage(
            channel=f"orders:{user_id}",
            event="order_update",
            data=order_data
        )
        await self.broadcast_to_channel(message, f"orders:{user_id}")
    
    def get_connection_count(self, channel: Optional[str] = None) -> int:
        """
        Get number of active connections.
        
        Args:
            channel: Optional channel filter
            
        Returns:
            Number of connections
        """
        if channel:
            return len(self.active_connections.get(channel, set()))
        return sum(len(conns) for conns in self.active_connections.values())
    
    def get_channels(self) -> list:
        """Get list of active channels"""
        return list(self.active_connections.keys())


# Global connection manager instance
connection_manager = ConnectionManager()
