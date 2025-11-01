"""
Trade Endpoints

REST API endpoints for trade data and statistics.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from datetime import datetime
import logging

from ..models.trades import (
    TradeResponse,
    TradeListResponse,
    TradeStatsResponse,
    UserVolumeResponse
)
from ...matching_engine.core.trade import Trade
from ...matching_engine.services import TradeManager
from ...matching_engine.repositories import TradeRepository

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/trades", tags=["Trades"])

# Global instances
_trade_manager = None
_trade_repository = None


def get_trade_manager() -> TradeManager:
    """Get or create trade manager instance"""
    global _trade_manager
    if _trade_manager is None:
        _trade_manager = TradeManager()
    return _trade_manager


def get_trade_repository() -> TradeRepository:
    """Get or create trade repository instance"""
    global _trade_repository
    if _trade_repository is None:
        _trade_repository = TradeRepository()
    return _trade_repository


def trade_to_response(trade: Trade) -> TradeResponse:
    """Convert Trade to TradeResponse"""
    # Handle both enum and string values
    settlement_status = trade.settlement_status.value if hasattr(trade.settlement_status, 'value') else str(trade.settlement_status)
    
    return TradeResponse(
        trade_id=trade.trade_id,
        symbol=trade.symbol,
        buyer_order_id=trade.buyer_order_id,
        seller_order_id=trade.seller_order_id,
        buyer_user_id=trade.buyer_user_id,
        seller_user_id=trade.seller_user_id,
        price=trade.price,
        quantity=trade.quantity,
        maker_fee=trade.maker_fee,
        taker_fee=trade.taker_fee,
        total_fees=trade.total_fees,
        settlement_status=settlement_status,
        timestamp=trade.timestamp,
        settled_at=trade.settled_at
    )


@router.get("", response_model=TradeListResponse)
async def list_trades(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    status: Optional[str] = Query(None, description="Filter by settlement status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(100, ge=1, le=1000, description="Page size"),
    trade_manager: TradeManager = Depends(get_trade_manager)
):
    """
    List trades with optional filters.
    
    - **user_id**: Filter by user (buyer or seller)
    - **symbol**: Filter by trading pair
    - **status**: Filter by settlement status
    - **page**: Page number (default: 1)
    - **page_size**: Results per page (default: 100, max: 1000)
    """
    try:
        # Get trades based on filters
        trades = trade_manager.get_trade_history(
            user_id=user_id,
            symbol=symbol,
            limit=page_size
        )
        
        # Filter by status if provided
        if status:
            status_upper = status.upper()
            trades = [t for t in trades if str(t.settlement_status).upper() == status_upper]
        
        # Convert to response models
        trade_responses = [trade_to_response(t) for t in trades]
        
        return TradeListResponse(
            trades=trade_responses,
            total=len(trade_responses),
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        logger.error(f"Error listing trades: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list trades")


@router.get("/{trade_id}", response_model=TradeResponse)
async def get_trade(
    trade_id: str,
    trade_manager: TradeManager = Depends(get_trade_manager)
):
    """
    Get trade details by ID.
    
    - **trade_id**: Trade identifier
    """
    try:
        trade = trade_manager.get_trade(trade_id)
        
        if not trade:
            raise HTTPException(status_code=404, detail="Trade not found")
        
        return trade_to_response(trade)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting trade: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get trade")


@router.get("/user/{user_id}", response_model=TradeListResponse)
async def get_user_trades(
    user_id: str,
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    page_size: int = Query(100, ge=1, le=1000, description="Page size"),
    trade_manager: TradeManager = Depends(get_trade_manager)
):
    """
    Get all trades for a specific user.
    
    - **user_id**: User identifier
    - **symbol**: Optional symbol filter
    - **page_size**: Results per page (default: 100, max: 1000)
    """
    try:
        trades = trade_manager.get_trade_history(
            user_id=user_id,
            symbol=symbol,
            limit=page_size
        )
        
        trade_responses = [trade_to_response(t) for t in trades]
        
        return TradeListResponse(
            trades=trade_responses,
            total=len(trade_responses),
            page=1,
            page_size=page_size
        )
        
    except Exception as e:
        logger.error(f"Error getting user trades: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get user trades")


@router.get("/symbol/{symbol}", response_model=TradeListResponse)
async def get_symbol_trades(
    symbol: str,
    page_size: int = Query(100, ge=1, le=1000, description="Page size"),
    trade_manager: TradeManager = Depends(get_trade_manager)
):
    """
    Get all trades for a specific symbol.
    
    - **symbol**: Trading pair symbol
    - **page_size**: Results per page (default: 100, max: 1000)
    """
    try:
        trades = trade_manager.get_trade_history(
            symbol=symbol,
            limit=page_size
        )
        
        trade_responses = [trade_to_response(t) for t in trades]
        
        return TradeListResponse(
            trades=trade_responses,
            total=len(trade_responses),
            page=1,
            page_size=page_size
        )
        
    except Exception as e:
        logger.error(f"Error getting symbol trades: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get symbol trades")


@router.get("/stats/all", response_model=TradeStatsResponse)
async def get_trade_statistics(
    trade_manager: TradeManager = Depends(get_trade_manager)
):
    """
    Get overall trade statistics.
    
    Returns aggregated statistics across all trades.
    """
    try:
        stats = trade_manager.get_statistics()
        
        return TradeStatsResponse(
            total_trades=stats.get('total_trades', 0),
            total_volume=stats.get('total_volume', 0),
            total_fees=stats.get('total_fees', 0),
            symbols=stats.get('symbols', []),
            status_breakdown=stats.get('status_breakdown', {})
        )
        
    except Exception as e:
        logger.error(f"Error getting trade statistics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get trade statistics")


@router.get("/volume/user/{user_id}", response_model=UserVolumeResponse)
async def get_user_volume(
    user_id: str,
    trade_manager: TradeManager = Depends(get_trade_manager)
):
    """
    Get trading volume for a specific user.
    
    - **user_id**: User identifier
    """
    try:
        volume = trade_manager.get_user_volume(user_id)
        trades = trade_manager.get_trade_history(user_id=user_id, limit=1000)
        
        # Get unique symbols
        symbols = list(set(t.symbol for t in trades))
        
        return UserVolumeResponse(
            user_id=user_id,
            total_volume=volume,
            trade_count=len(trades),
            symbols=symbols
        )
        
    except Exception as e:
        logger.error(f"Error getting user volume: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get user volume")


@router.get("/volume/symbol/{symbol}")
async def get_symbol_volume(
    symbol: str,
    trade_manager: TradeManager = Depends(get_trade_manager)
):
    """
    Get trading volume for a specific symbol.
    
    - **symbol**: Trading pair symbol
    """
    try:
        volume = trade_manager.get_symbol_volume(symbol)
        
        return {
            "symbol": symbol,
            "total_volume": volume
        }
        
    except Exception as e:
        logger.error(f"Error getting symbol volume: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get symbol volume")
