"""
Trade API Models

Request and response models for trade endpoints.
"""

from typing import Optional, List
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field


class TradeResponse(BaseModel):
    """Response model for trade operations"""
    
    trade_id: str
    symbol: str
    buyer_order_id: str
    seller_order_id: str
    buyer_user_id: str
    seller_user_id: str
    price: Decimal
    quantity: Decimal
    maker_fee: Decimal
    taker_fee: Decimal
    total_fees: Decimal
    settlement_status: str
    timestamp: datetime
    settled_at: Optional[datetime] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "trade_id": "trade_123abc",
                "symbol": "BTC-USD",
                "buyer_order_id": "ord_buy123",
                "seller_order_id": "ord_sell456",
                "buyer_user_id": "alice",
                "seller_user_id": "bob",
                "price": "50000.00",
                "quantity": "1.5",
                "maker_fee": "75.00",
                "taker_fee": "150.00",
                "total_fees": "225.00",
                "settlement_status": "settled",
                "timestamp": "2025-11-02T00:00:00Z",
                "settled_at": "2025-11-02T00:01:00Z"
            }
        }


class TradeListResponse(BaseModel):
    """Response model for listing trades"""
    
    trades: List[TradeResponse]
    total: int
    page: int = 1
    page_size: int = 100
    
    class Config:
        json_schema_extra = {
            "example": {
                "trades": [
                    {
                        "trade_id": "trade_123abc",
                        "symbol": "BTC-USD",
                        "buyer_order_id": "ord_buy123",
                        "seller_order_id": "ord_sell456",
                        "buyer_user_id": "alice",
                        "seller_user_id": "bob",
                        "price": "50000.00",
                        "quantity": "1.5",
                        "maker_fee": "75.00",
                        "taker_fee": "150.00",
                        "total_fees": "225.00",
                        "settlement_status": "settled",
                        "timestamp": "2025-11-02T00:00:00Z",
                        "settled_at": "2025-11-02T00:01:00Z"
                    }
                ],
                "total": 1,
                "page": 1,
                "page_size": 100
            }
        }


class TradeStatsResponse(BaseModel):
    """Response model for trade statistics"""
    
    total_trades: int
    total_volume: Decimal
    total_fees: Decimal
    symbols: List[str]
    status_breakdown: dict
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_trades": 150,
                "total_volume": "1500.50",
                "total_fees": "3750.25",
                "symbols": ["BTC-USD", "ETH-USD"],
                "status_breakdown": {
                    "settled": 140,
                    "pending": 8,
                    "failed": 2
                }
            }
        }


class UserVolumeResponse(BaseModel):
    """Response model for user trading volume"""
    
    user_id: str
    total_volume: Decimal
    trade_count: int
    symbols: List[str]
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "alice",
                "total_volume": "250.75",
                "trade_count": 45,
                "symbols": ["BTC-USD", "ETH-USD"]
            }
        }
