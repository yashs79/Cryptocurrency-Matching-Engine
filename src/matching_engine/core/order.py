"""
Order data structures and validation.

This module defines the Order class and related enums for representing
individual orders in the matching engine.
"""

from enum import Enum
from decimal import Decimal
from typing import Optional
from datetime import datetime, UTC
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
import uuid


class OrderSide(str, Enum):
    """Order side: BUY or SELL"""
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    """Order type"""
    LIMIT = "LIMIT"           # Limit order (price specified)
    MARKET = "MARKET"         # Market order (execute at best available price)
    STOP_LOSS = "STOP_LOSS"   # Stop loss order
    STOP_LIMIT = "STOP_LIMIT" # Stop limit order
    IOC = "IOC"               # Immediate or Cancel
    FOK = "FOK"               # Fill or Kill


class OrderStatus(str, Enum):
    """Order status"""
    PENDING = "PENDING"           # Order received, not yet processed
    OPEN = "OPEN"                 # Order in order book
    PARTIALLY_FILLED = "PARTIALLY_FILLED"  # Order partially executed
    FILLED = "FILLED"             # Order fully executed
    CANCELLED = "CANCELLED"       # Order cancelled
    REJECTED = "REJECTED"         # Order rejected
    EXPIRED = "EXPIRED"           # Order expired


class Order(BaseModel):
    """
    Represents a single order in the matching engine.
    
    Attributes:
        order_id: Unique order identifier
        user_id: User who placed the order
        symbol: Trading pair symbol (e.g., "BTC-USD")
        side: Order side (BUY or SELL)
        order_type: Type of order (LIMIT, MARKET, etc.)
        price: Order price (None for market orders)
        quantity: Order quantity
        filled_quantity: Quantity that has been filled
        status: Current order status
        timestamp: Order creation timestamp
        updated_at: Last update timestamp
    """
    
    order_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    price: Optional[Decimal] = None
    quantity: Decimal
    filled_quantity: Decimal = Decimal("0")
    status: OrderStatus = OrderStatus.PENDING
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    
    # Optional fields
    stop_price: Optional[Decimal] = None  # For stop orders
    time_in_force: str = "GTC"  # Good Till Cancel, IOC, FOK
    client_order_id: Optional[str] = None
    
    model_config = ConfigDict(
        use_enum_values=True,
        json_encoders={
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }
    )
    
    @model_validator(mode='after')
    def validate_order(self):
        """Validate order fields"""
        # Market orders should not have a price
        if self.order_type == OrderType.MARKET and self.price is not None:
            raise ValueError("Market orders cannot have a price")
        
        # Limit orders must have a price
        if self.order_type == OrderType.LIMIT and self.price is None:
            raise ValueError("Limit orders must have a price")
        
        # Price must be positive
        if self.price is not None and self.price <= 0:
            raise ValueError("Price must be positive")
        
        # Quantity must be positive
        if self.quantity <= 0:
            raise ValueError("Quantity must be positive")
        
        # Filled quantity validation
        if self.filled_quantity < 0:
            raise ValueError("Filled quantity cannot be negative")
        
        if self.filled_quantity > self.quantity:
            raise ValueError("Filled quantity cannot exceed order quantity")
        
        return self
    
    @property
    def remaining_quantity(self) -> Decimal:
        """Calculate remaining quantity to be filled"""
        return self.quantity - self.filled_quantity
    
    @property
    def is_filled(self) -> bool:
        """Check if order is fully filled"""
        return self.filled_quantity >= self.quantity
    
    @property
    def is_partially_filled(self) -> bool:
        """Check if order is partially filled"""
        return Decimal("0") < self.filled_quantity < self.quantity
    
    def fill(self, quantity: Decimal) -> None:
        """
        Fill the order by the specified quantity.
        
        Args:
            quantity: Quantity to fill
            
        Raises:
            ValueError: If fill quantity is invalid
        """
        if quantity <= 0:
            raise ValueError("Fill quantity must be positive")
        
        if quantity > self.remaining_quantity:
            raise ValueError("Fill quantity exceeds remaining quantity")
        
        self.filled_quantity += quantity
        self.updated_at = datetime.now(UTC)
        
        # Update status
        if self.is_filled:
            self.status = OrderStatus.FILLED
        elif self.is_partially_filled:
            self.status = OrderStatus.PARTIALLY_FILLED
    
    def cancel(self) -> None:
        """Cancel the order"""
        if self.status in [OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED]:
            raise ValueError(f"Cannot cancel order with status {self.status}")
        
        self.status = OrderStatus.CANCELLED
        self.updated_at = datetime.now(UTC)
    
    def __lt__(self, other: 'Order') -> bool:
        """
        Compare orders for priority in order book.
        Price-Time Priority: Better price first, then earlier timestamp.
        """
        if not isinstance(other, Order):
            return NotImplemented
        
        # For BUY orders: higher price has priority
        # For SELL orders: lower price has priority
        if self.side == OrderSide.BUY:
            if self.price != other.price:
                return self.price > other.price
        else:  # SELL
            if self.price != other.price:
                return self.price < other.price
        
        # Same price: earlier timestamp has priority
        return self.timestamp < other.timestamp
    
    def __repr__(self) -> str:
        return (
            f"Order(id={self.order_id[:8]}, {self.side.value} {self.quantity} "
            f"{self.symbol} @ {self.price}, status={self.status.value})"
        )
