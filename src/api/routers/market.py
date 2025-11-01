"""
Market Data Endpoints

REST API endpoints for market data and order book information.
"""

from typing import Optional
from decimal import Decimal
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, UTC
import logging

from ..models.market import (
    OrderBookResponse,
    OrderBookLevel,
    TickerResponse,
    SymbolsResponse,
    SymbolInfo,
    MarketStatsResponse
)
from ...matching_engine.core.matching_engine import MatchingEngine
from ...matching_engine.repositories import OrderRepository, TradeRepository

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/market", tags=["Market Data"])

# Global instances
_matching_engine = None
_order_repository = None
_trade_repository = None


def get_matching_engine() -> MatchingEngine:
    """Get or create matching engine instance"""
    global _matching_engine
    if _matching_engine is None:
        _matching_engine = MatchingEngine()
    return _matching_engine


def get_order_repository() -> OrderRepository:
    """Get or create order repository instance"""
    global _order_repository
    if _order_repository is None:
        _order_repository = OrderRepository()
    return _order_repository


def get_trade_repository() -> TradeRepository:
    """Get or create trade repository instance"""
    global _trade_repository
    if _trade_repository is None:
        _trade_repository = TradeRepository()
    return _trade_repository


@router.get("/orderbook/{symbol}", response_model=OrderBookResponse)
async def get_order_book(
    symbol: str,
    depth: int = 10,
    matching_engine: MatchingEngine = Depends(get_matching_engine)
):
    """
    Get order book snapshot for a symbol.
    
    - **symbol**: Trading pair symbol
    - **depth**: Number of levels to return (default: 10)
    """
    try:
        # Get order book from matching engine
        if symbol not in matching_engine.order_books:
            # Return empty order book if symbol doesn't exist
            return OrderBookResponse(
                symbol=symbol,
                bids=[],
                asks=[],
                timestamp=datetime.now(UTC).isoformat()
            )
        
        order_book = matching_engine.order_books[symbol]
        
        # Get bids (buy orders)
        bids = []
        for price_level in list(order_book.bids.keys())[:depth]:
            orders = order_book.bids[price_level]
            total_quantity = sum(o.remaining_quantity for o in orders)
            bids.append(OrderBookLevel(
                price=price_level,
                quantity=total_quantity,
                order_count=len(orders)
            ))
        
        # Get asks (sell orders)
        asks = []
        for price_level in list(order_book.asks.keys())[:depth]:
            orders = order_book.asks[price_level]
            total_quantity = sum(o.remaining_quantity for o in orders)
            asks.append(OrderBookLevel(
                price=price_level,
                quantity=total_quantity,
                order_count=len(orders)
            ))
        
        return OrderBookResponse(
            symbol=symbol,
            bids=bids,
            asks=asks,
            timestamp=datetime.now(UTC).isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error getting order book: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get order book")


@router.get("/ticker/{symbol}", response_model=TickerResponse)
async def get_ticker(
    symbol: str,
    matching_engine: MatchingEngine = Depends(get_matching_engine),
    trade_repository: TradeRepository = Depends(get_trade_repository)
):
    """
    Get ticker data for a symbol.
    
    - **symbol**: Trading pair symbol
    """
    try:
        # Get order book for bid/ask prices
        bid_price = None
        ask_price = None
        
        if symbol in matching_engine.order_books:
            order_book = matching_engine.order_books[symbol]
            if order_book.bids:
                bid_price = list(order_book.bids.keys())[0]
            if order_book.asks:
                ask_price = list(order_book.asks.keys())[0]
        
        # Get recent trades for last price and volume
        trades = trade_repository.find_by_symbol(symbol, limit=100)
        
        last_price = None
        volume_24h = Decimal("0")
        
        if trades:
            last_price = trades[0].price
            # Calculate volume (simplified - not actually 24h)
            volume_24h = sum(t.quantity for t in trades)
        
        return TickerResponse(
            symbol=symbol,
            last_price=last_price,
            bid_price=bid_price,
            ask_price=ask_price,
            volume_24h=volume_24h,
            timestamp=datetime.now(UTC).isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error getting ticker: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get ticker")


@router.get("/symbols", response_model=SymbolsResponse)
async def get_symbols(
    matching_engine: MatchingEngine = Depends(get_matching_engine)
):
    """
    Get list of available trading symbols.
    """
    try:
        # Get symbols from order books
        symbols = []
        for symbol in matching_engine.order_books.keys():
            # Parse symbol (e.g., "BTC-USD" -> base="BTC", quote="USD")
            parts = symbol.split('-')
            base_asset = parts[0] if len(parts) > 0 else symbol
            quote_asset = parts[1] if len(parts) > 1 else "USD"
            
            symbols.append(SymbolInfo(
                symbol=symbol,
                base_asset=base_asset,
                quote_asset=quote_asset,
                active=True
            ))
        
        return SymbolsResponse(
            symbols=symbols,
            total=len(symbols)
        )
        
    except Exception as e:
        logger.error(f"Error getting symbols: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get symbols")


@router.get("/stats/{symbol}", response_model=MarketStatsResponse)
async def get_market_stats(
    symbol: str,
    matching_engine: MatchingEngine = Depends(get_matching_engine),
    order_repository: OrderRepository = Depends(get_order_repository),
    trade_repository: TradeRepository = Depends(get_trade_repository)
):
    """
    Get market statistics for a symbol.
    
    - **symbol**: Trading pair symbol
    """
    try:
        # Get order statistics
        all_orders = order_repository.find_by_symbol(symbol)
        active_orders = [o for o in all_orders if o.status.value in ['OPEN', 'PARTIALLY_FILLED']]
        
        # Get trade statistics
        trades = trade_repository.find_by_symbol(symbol)
        total_volume = sum(t.quantity for t in trades)
        
        # Get best bid/ask
        best_bid = None
        best_ask = None
        spread = None
        
        if symbol in matching_engine.order_books:
            order_book = matching_engine.order_books[symbol]
            if order_book.bids:
                best_bid = list(order_book.bids.keys())[0]
            if order_book.asks:
                best_ask = list(order_book.asks.keys())[0]
            
            if best_bid and best_ask:
                spread = best_ask - best_bid
        
        return MarketStatsResponse(
            symbol=symbol,
            total_orders=len(all_orders),
            active_orders=len(active_orders),
            total_trades=len(trades),
            total_volume=total_volume,
            best_bid=best_bid,
            best_ask=best_ask,
            spread=spread
        )
        
    except Exception as e:
        logger.error(f"Error getting market stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get market stats")
