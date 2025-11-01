"""
Order API Models

Request and response models for order endpoints.
"""

from typing import Optional, List
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field, field_validator

from ...matching_engine.core.order import OrderSide, OrderType, OrderStatus


class OrderRequest(BaseModel):
    """Request model for submitting an order"""
    
    user_id: str = Field(..., description="User ID", min_length=1, max_length=100)
    symbol: str = Field(..., description="Trading symbol (e.g., BTC-USD)", min_length=1, max_length=20)
    side: str = Field(..., description="Order side: 'buy' or 'sell'")
    order_type: str = Field(..., description="Order type: 'limit' or 'market'")
    price: Optional[Decimal] = Field(None, description="Price (required for limit orders)", gt=0)
    quantity: Decimal = Field(..., description="Quantity", gt=0)
    time_in_force: str = Field(default="GTC", description="Time in force: GTC, IOC, FOK")
    
    @field_validator('side')
    @classmethod
    def validate_side(cls, v: str) -> str:
        """Validate order side"""
        v = v.lower()
        if v not in ['buy', 'sell']:
            raise ValueError("side must be 'buy' or 'sell'")
        return v
    
    @field_validator('order_type')
    @classmethod
    def validate_order_type(cls, v: str) -> str:
        """Validate order type"""
        v = v.lower()
        if v not in ['limit', 'market']:
            raise ValueError("order_type must be 'limit' or 'market'")
        return v
    
    @field_validator('time_in_force')
    @classmethod
    def validate_time_in_force(cls, v: str) -> str:
        """Validate time in force"""
        v = v.upper()
        if v not in ['GTC', 'IOC', 'FOK']:
            raise ValueError("time_in_force must be 'GTC', 'IOC', or 'FOK'")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "alice",
                "symbol": "BTC-USD",
                "side": "buy",
                "order_type": "limit",
                "price": "50000.00",
                "quantity": "1.5",
                "time_in_force": "GTC"
            }
        }


class OrderResponse(BaseModel):
    """Response model for order operations"""
    
    order_id: str
    user_id: str
    symbol: str
    side: str
    order_type: str
    price: Optional[Decimal]
    quantity: Decimal
    filled_quantity: Decimal
    remaining_quantity: Decimal
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "order_id": "ord_123abc",
                "user_id": "alice",
                "symbol": "BTC-USD",
                "side": "buy",
                "order_type": "limit",
                "price": "50000.00",
                "quantity": "1.5",
                "filled_quantity": "0.5",
                "remaining_quantity": "1.0",
                "status": "partially_filled",
                "created_at": "2025-10-31T10:00:00Z",
                "updated_at": "2025-10-31T10:01:00Z"
            }
        }


class OrderListResponse(BaseModel):
    """Response model for listing orders"""
    
    orders: List[OrderResponse]
    total: int
    page: int = 1
    page_size: int = 100
    
    class Config:
        json_schema_extra = {
            "example": {
                "orders": [
                    {
                        "order_id": "ord_123abc",
                        "user_id": "alice",
                        "symbol": "BTC-USD",
                        "side": "buy",
                        "order_type": "limit",
                        "price": "50000.00",
                        "quantity": "1.5",
                        "filled_quantity": "0.0",
                        "remaining_quantity": "1.5",
                        "status": "open",
                        "created_at": "2025-10-31T10:00:00Z",
                        "updated_at": "2025-10-31T10:00:00Z"
                    }
                ],
                "total": 1,
                "page": 1,
                "page_size": 100
            }
        }


class CancelOrderResponse(BaseModel):
    """Response model for canceling an order"""
    
    order_id: str
    status: str
    message: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "order_id": "ord_123abc",
                "status": "cancelled",
                "message": "Order cancelled successfully"
            }
        }


class AmendOrderRequest(BaseModel):
    """Request model for amending an order"""
    
    price: Optional[Decimal] = Field(None, description="New price", gt=0)
    quantity: Optional[Decimal] = Field(None, description="New quantity", gt=0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "price": "51000.00",
                "quantity": "2.0"
            }
        }
