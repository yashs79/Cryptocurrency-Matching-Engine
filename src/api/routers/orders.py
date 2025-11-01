"""
Order Endpoints

REST API endpoints for order management.
"""

from typing import Optional, List
from decimal import Decimal
from fastapi import APIRouter, HTTPException, Query, Depends
from datetime import datetime, UTC
import logging

from ..models.orders import (
    OrderRequest,
    OrderResponse,
    OrderListResponse,
    CancelOrderResponse,
    AmendOrderRequest
)
from ...matching_engine.core.order import Order, OrderSide, OrderType, OrderStatus
from ...matching_engine.core.matching_engine import MatchingEngine
from ...matching_engine.services import OrderManager, TradeManager
from ...matching_engine.repositories import OrderRepository

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/orders", tags=["Orders"])

# Global instances (in production, use dependency injection)
_matching_engine = None
_order_manager = None
_trade_manager = None
_order_repository = None


def get_matching_engine() -> MatchingEngine:
    """Get or create matching engine instance"""
    global _matching_engine
    if _matching_engine is None:
        _matching_engine = MatchingEngine()
    return _matching_engine


def get_order_manager() -> OrderManager:
    """Get or create order manager instance"""
    global _order_manager
    if _order_manager is None:
        _order_manager = OrderManager(
            matching_engine=get_matching_engine()
        )
    return _order_manager


def get_trade_manager() -> TradeManager:
    """Get or create trade manager instance"""
    global _trade_manager
    if _trade_manager is None:
        _trade_manager = TradeManager()
    return _trade_manager


def get_order_repository() -> OrderRepository:
    """Get or create order repository instance"""
    global _order_repository
    if _order_repository is None:
        _order_repository = OrderRepository()
    return _order_repository


def order_to_response(order: Order) -> OrderResponse:
    """Convert Order to OrderResponse"""
    # Handle both enum and string values
    side_value = order.side.value if hasattr(order.side, 'value') else str(order.side)
    order_type_value = order.order_type.value if hasattr(order.order_type, 'value') else str(order.order_type)
    status_value = order.status.value if hasattr(order.status, 'value') else str(order.status)
    
    return OrderResponse(
        order_id=order.order_id,
        user_id=order.user_id,
        symbol=order.symbol,
        side=side_value,
        order_type=order_type_value,
        price=order.price,
        quantity=order.quantity,
        filled_quantity=order.filled_quantity,
        remaining_quantity=order.remaining_quantity,
        status=status_value,
        created_at=order.timestamp,
        updated_at=order.timestamp
    )


@router.post("", response_model=OrderResponse, status_code=201)
async def submit_order(
    request: OrderRequest,
    order_manager: OrderManager = Depends(get_order_manager),
    trade_manager: TradeManager = Depends(get_trade_manager)
):
    """
    Submit a new order.
    
    - **user_id**: User identifier
    - **symbol**: Trading pair (e.g., BTC-USD)
    - **side**: 'buy' or 'sell'
    - **order_type**: 'limit' or 'market'
    - **price**: Price (required for limit orders)
    - **quantity**: Order quantity
    - **time_in_force**: GTC, IOC, or FOK
    """
    try:
        # Validate price for limit orders
        if request.order_type == 'limit' and request.price is None:
            raise HTTPException(
                status_code=400,
                detail="Price is required for limit orders"
            )
        
        # Create order
        order = Order(
            user_id=request.user_id,
            symbol=request.symbol,
            side=OrderSide.BUY if request.side == 'buy' else OrderSide.SELL,
            order_type=OrderType.LIMIT if request.order_type == 'limit' else OrderType.MARKET,
            price=request.price,
            quantity=request.quantity
        )
        
        # Submit order through order manager
        processed_order, trades = order_manager.submit_order(order)
        
        # Execute trades through trade manager
        for trade in trades:
            # Get the buy and sell orders
            buy_order = processed_order if processed_order.side == OrderSide.BUY else None
            sell_order = processed_order if processed_order.side == OrderSide.SELL else None
            
            # Determine maker order (the one that was in the book)
            maker_order = buy_order if trade.buyer_order_id != processed_order.order_id else sell_order
            
            # Execute trade
            trade_manager.execute_trade(
                buy_order=buy_order or processed_order,
                sell_order=sell_order or processed_order,
                price=trade.price,
                quantity=trade.quantity,
                maker_order=maker_order or processed_order
            )
        
        logger.info(f"Order submitted: {processed_order.order_id}, trades: {len(trades)}")
        
        return order_to_response(processed_order)
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error submitting order: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to submit order")


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    order_repository: OrderRepository = Depends(get_order_repository)
):
    """
    Get order details by ID.
    
    - **order_id**: Order identifier
    """
    try:
        order = order_repository.get(order_id)
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        return order_to_response(order)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting order: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get order")


@router.get("", response_model=OrderListResponse)
async def list_orders(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    status: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(100, ge=1, le=1000, description="Page size"),
    order_repository: OrderRepository = Depends(get_order_repository)
):
    """
    List orders with optional filters.
    
    - **user_id**: Filter by user
    - **symbol**: Filter by trading pair
    - **status**: Filter by order status
    - **page**: Page number (default: 1)
    - **page_size**: Results per page (default: 100, max: 1000)
    """
    try:
        # Get orders based on filters
        if user_id:
            orders = order_repository.find_by_user(user_id, limit=page_size)
        elif symbol:
            orders = order_repository.find_by_symbol(symbol, limit=page_size)
        else:
            orders = order_repository.find(limit=page_size)
        
        # Filter by status if provided
        if status:
            try:
                status_enum = OrderStatus[status.upper()]
                orders = [o for o in orders if o.status == status_enum]
            except KeyError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        # Convert to response models
        order_responses = [order_to_response(o) for o in orders]
        
        return OrderListResponse(
            orders=order_responses,
            total=len(order_responses),
            page=page,
            page_size=page_size
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing orders: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list orders")


@router.delete("/{order_id}", response_model=CancelOrderResponse)
async def cancel_order(
    order_id: str,
    order_manager: OrderManager = Depends(get_order_manager)
):
    """
    Cancel an order.
    
    - **order_id**: Order identifier
    """
    try:
        success = order_manager.cancel_order(order_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Order not found or already cancelled")
        
        logger.info(f"Order cancelled: {order_id}")
        
        return CancelOrderResponse(
            order_id=order_id,
            status="cancelled",
            message="Order cancelled successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling order: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to cancel order")


@router.put("/{order_id}", response_model=OrderResponse)
async def amend_order(
    order_id: str,
    request: AmendOrderRequest,
    order_manager: OrderManager = Depends(get_order_manager)
):
    """
    Amend an order (modify price and/or quantity).
    
    - **order_id**: Order identifier
    - **price**: New price (optional)
    - **quantity**: New quantity (optional)
    """
    try:
        # At least one field must be provided
        if request.price is None and request.quantity is None:
            raise HTTPException(
                status_code=400,
                detail="At least one of price or quantity must be provided"
            )
        
        # Amend order
        amended_order = order_manager.amend_order(
            order_id=order_id,
            new_price=request.price,
            new_quantity=request.quantity
        )
        
        if not amended_order:
            raise HTTPException(status_code=404, detail="Order not found or cannot be amended")
        
        logger.info(f"Order amended: {order_id}")
        
        return order_to_response(amended_order)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error amending order: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to amend order")


@router.get("/active/all", response_model=OrderListResponse)
async def get_active_orders(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    page_size: int = Query(100, ge=1, le=1000, description="Page size"),
    order_repository: OrderRepository = Depends(get_order_repository)
):
    """
    Get all active (open) orders.
    
    - **user_id**: Filter by user
    - **symbol**: Filter by trading pair
    - **page_size**: Results per page (default: 100, max: 1000)
    """
    try:
        # Get orders based on filters
        if user_id:
            orders = order_repository.find_by_user(user_id, limit=page_size)
        elif symbol:
            orders = order_repository.find_by_symbol(symbol, limit=page_size)
        else:
            orders = order_repository.find(limit=page_size)
        
        # Filter for active orders only
        active_orders = [
            o for o in orders 
            if o.status in [OrderStatus.OPEN, OrderStatus.PARTIALLY_FILLED]
        ]
        
        # Convert to response models
        order_responses = [order_to_response(o) for o in active_orders]
        
        return OrderListResponse(
            orders=order_responses,
            total=len(order_responses),
            page=1,
            page_size=page_size
        )
        
    except Exception as e:
        logger.error(f"Error getting active orders: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get active orders")
