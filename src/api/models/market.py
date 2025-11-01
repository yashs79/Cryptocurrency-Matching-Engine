"""
Market Data API Models

Request and response models for market data endpoints.
"""

from typing import List, Optional
from decimal import Decimal
from pydantic import BaseModel


class OrderBookLevel(BaseModel):
    """Single level in order book"""
    price: Decimal
    quantity: Decimal
    order_count: int = 1


class OrderBookResponse(BaseModel):
    """Response model for order book snapshot"""
    
    symbol: str
    bids: List[OrderBookLevel]
    asks: List[OrderBookLevel]
    timestamp: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "BTC-USD",
                "bids": [
                    {"price": "50000.00", "quantity": "1.5", "order_count": 2},
                    {"price": "49999.00", "quantity": "2.0", "order_count": 1}
                ],
                "asks": [
                    {"price": "50001.00", "quantity": "1.0", "order_count": 1},
                    {"price": "50002.00", "quantity": "3.0", "order_count": 2}
                ],
                "timestamp": "2025-11-02T00:00:00Z"
            }
        }


class TickerResponse(BaseModel):
    """Response model for ticker data"""
    
    symbol: str
    last_price: Optional[Decimal] = None
    bid_price: Optional[Decimal] = None
    ask_price: Optional[Decimal] = None
    volume_24h: Decimal = Decimal("0")
    high_24h: Optional[Decimal] = None
    low_24h: Optional[Decimal] = None
    price_change_24h: Optional[Decimal] = None
    timestamp: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "BTC-USD",
                "last_price": "50000.00",
                "bid_price": "49999.00",
                "ask_price": "50001.00",
                "volume_24h": "125.50",
                "high_24h": "51000.00",
                "low_24h": "49000.00",
                "price_change_24h": "1000.00",
                "timestamp": "2025-11-02T00:00:00Z"
            }
        }


class SymbolInfo(BaseModel):
    """Information about a trading symbol"""
    
    symbol: str
    base_asset: str
    quote_asset: str
    active: bool = True
    
    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "BTC-USD",
                "base_asset": "BTC",
                "quote_asset": "USD",
                "active": True
            }
        }


class SymbolsResponse(BaseModel):
    """Response model for available symbols"""
    
    symbols: List[SymbolInfo]
    total: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "symbols": [
                    {
                        "symbol": "BTC-USD",
                        "base_asset": "BTC",
                        "quote_asset": "USD",
                        "active": True
                    },
                    {
                        "symbol": "ETH-USD",
                        "base_asset": "ETH",
                        "quote_asset": "USD",
                        "active": True
                    }
                ],
                "total": 2
            }
        }


class MarketStatsResponse(BaseModel):
    """Response model for market statistics"""
    
    symbol: str
    total_orders: int
    active_orders: int
    total_trades: int
    total_volume: Decimal
    best_bid: Optional[Decimal] = None
    best_ask: Optional[Decimal] = None
    spread: Optional[Decimal] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "BTC-USD",
                "total_orders": 150,
                "active_orders": 25,
                "total_trades": 75,
                "total_volume": "125.50",
                "best_bid": "49999.00",
                "best_ask": "50001.00",
                "spread": "2.00"
            }
        }
