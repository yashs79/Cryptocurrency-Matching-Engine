"""
Order Database Model

SQLAlchemy model for persisting orders.
"""

from sqlalchemy import Column, String, Enum, Numeric, DateTime, Integer, Index
from sqlalchemy.sql import func
from datetime import datetime, UTC
from decimal import Decimal

from ..config.database import Base
from ..core.order import Order, OrderSide, OrderType, OrderStatus


class OrderModel(Base):
    """
    Database model for orders.
    
    Maps to the Order domain object.
    """
    __tablename__ = "orders"
    
    # Primary key
    order_id = Column(String(36), primary_key=True, index=True)
    
    # Order details
    user_id = Column(String(100), nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(Enum(OrderSide), nullable=False, index=True)
    order_type = Column(Enum(OrderType), nullable=False)
    status = Column(Enum(OrderStatus), nullable=False, index=True)
    
    # Pricing and quantity
    price = Column(Numeric(20, 8), nullable=True)  # Null for market orders
    quantity = Column(Numeric(20, 8), nullable=False)
    filled_quantity = Column(Numeric(20, 8), nullable=False, default=0)
    
    # Timestamps
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Composite indexes for common queries
    __table_args__ = (
        Index('idx_user_symbol', 'user_id', 'symbol'),
        Index('idx_symbol_status', 'symbol', 'status'),
        Index('idx_user_status', 'user_id', 'status'),
        Index('idx_symbol_side_status', 'symbol', 'side', 'status'),
    )
    
    @classmethod
    def from_order(cls, order: Order) -> "OrderModel":
        """
        Create OrderModel from Order domain object.
        
        Args:
            order: Order domain object
            
        Returns:
            OrderModel instance
        """
        return cls(
            order_id=order.order_id,
            user_id=order.user_id,
            symbol=order.symbol,
            side=order.side,
            order_type=order.order_type,
            status=order.status,
            price=order.price,
            quantity=order.quantity,
            filled_quantity=order.filled_quantity,
            timestamp=order.timestamp
        )
    
    def to_order(self) -> Order:
        """
        Convert OrderModel to Order domain object.
        
        Returns:
            Order domain object
        """
        order = Order(
            user_id=self.user_id,
            symbol=self.symbol,
            side=self.side,
            order_type=self.order_type,
            price=Decimal(str(self.price)) if self.price else None,
            quantity=Decimal(str(self.quantity))
        )
        
        # Set additional fields
        order.order_id = self.order_id
        order.status = self.status
        order.filled_quantity = Decimal(str(self.filled_quantity))
        order.timestamp = self.timestamp
        
        return order
    
    def update_from_order(self, order: Order) -> None:
        """
        Update model fields from Order domain object.
        
        Args:
            order: Order domain object
        """
        self.status = order.status
        self.price = order.price
        self.quantity = order.quantity
        self.filled_quantity = order.filled_quantity
        self.timestamp = order.timestamp
    
    def __repr__(self) -> str:
        return (
            f"<OrderModel(order_id='{self.order_id}', "
            f"user_id='{self.user_id}', "
            f"symbol='{self.symbol}', "
            f"side={self.side.value}, "
            f"status={self.status.value})>"
        )
