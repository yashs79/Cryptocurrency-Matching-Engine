"""
WebSocket Endpoints

Real-time WebSocket connections for market data and updates.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional
import logging
import json

from ..websocket.manager import connection_manager, WebSocketMessage

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/orderbook/{symbol}")
async def websocket_orderbook(
    websocket: WebSocket,
    symbol: str,
    user_id: Optional[str] = Query(None)
):
    """
    WebSocket endpoint for order book updates.
    
    Streams real-time order book changes for a specific symbol.
    
    **Usage:**
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/ws/orderbook/BTC-USD');
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('Order book update:', data);
    };
    ```
    """
    channel = f"orderbook:{symbol}"
    await connection_manager.connect(websocket, channel, user_id)
    
    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_text()
            
            # Echo back or handle commands
            try:
                message = json.loads(data)
                if message.get("type") == "ping":
                    pong = WebSocketMessage(
                        channel=channel,
                        event="pong",
                        data={"message": "pong"}
                    )
                    await connection_manager.send_personal_message(pong, websocket)
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received: {data}")
                
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
        logger.info(f"Client disconnected from {channel}")


@router.websocket("/ws/trades/{symbol}")
async def websocket_trades(
    websocket: WebSocket,
    symbol: str,
    user_id: Optional[str] = Query(None)
):
    """
    WebSocket endpoint for trade stream.
    
    Streams real-time trade executions for a specific symbol.
    
    **Usage:**
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/ws/trades/BTC-USD');
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('New trade:', data);
    };
    ```
    """
    channel = f"trades:{symbol}"
    await connection_manager.connect(websocket, channel, user_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                if message.get("type") == "ping":
                    pong = WebSocketMessage(
                        channel=channel,
                        event="pong",
                        data={"message": "pong"}
                    )
                    await connection_manager.send_personal_message(pong, websocket)
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received: {data}")
                
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
        logger.info(f"Client disconnected from {channel}")


@router.websocket("/ws/orders")
async def websocket_orders(
    websocket: WebSocket,
    user_id: str = Query(..., description="User ID for order updates")
):
    """
    WebSocket endpoint for user order updates.
    
    Streams real-time updates for a user's orders.
    
    **Usage:**
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/ws/orders?user_id=alice');
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('Order update:', data);
    };
    ```
    """
    channel = f"orders:{user_id}"
    await connection_manager.connect(websocket, channel, user_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                if message.get("type") == "ping":
                    pong = WebSocketMessage(
                        channel=channel,
                        event="pong",
                        data={"message": "pong"}
                    )
                    await connection_manager.send_personal_message(pong, websocket)
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received: {data}")
                
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
        logger.info(f"Client disconnected from {channel}")


@router.websocket("/ws/market")
async def websocket_market(
    websocket: WebSocket,
    user_id: Optional[str] = Query(None)
):
    """
    WebSocket endpoint for general market data.
    
    Streams real-time market updates across all symbols.
    
    **Usage:**
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/ws/market');
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('Market update:', data);
    };
    ```
    """
    channel = "market"
    await connection_manager.connect(websocket, channel, user_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                if message.get("type") == "ping":
                    pong = WebSocketMessage(
                        channel=channel,
                        event="pong",
                        data={"message": "pong"}
                    )
                    await connection_manager.send_personal_message(pong, websocket)
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received: {data}")
                
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
        logger.info(f"Client disconnected from {channel}")


@router.get("/ws/stats")
async def websocket_stats():
    """
    Get WebSocket connection statistics.
    
    Returns information about active WebSocket connections.
    """
    return {
        "total_connections": connection_manager.get_connection_count(),
        "channels": connection_manager.get_channels(),
        "connections_by_channel": {
            channel: connection_manager.get_connection_count(channel)
            for channel in connection_manager.get_channels()
        }
    }
