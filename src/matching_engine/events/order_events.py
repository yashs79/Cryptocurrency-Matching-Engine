"""
Order Event Definitions

Defines all order lifecycle events that can be published.
"""

from typing import Optional, List
from decimal import Decimal
from datetime import datetime, UTC
from enum import Enum
from dataclasses import dataclass

from ..core.order import Order, OrderStatus
from ..core.matching_engine import Trade


class OrderEventType(Enum):
    """Types of order events"""
    SUBMITTED = "submitted"
    CANCELLED = "cancelled"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    REJECTED = "rejected"
    AMENDED = "amended"
    EXPIRED = "expired"


@dataclass
class OrderEvent:
    """
    Base class for order events.
    
    All order events inherit from this class.
    """
    event_type: OrderEventType
    order: Order
    timestamp: datetime
    metadata: dict
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(UTC)
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> dict:
        """Convert event to dictionary"""
        return {
            "event_type": self.event_type.value,
            "order_id": self.order.order_id,
            "user_id": self.order.user_id,
            "symbol": self.order.symbol,
            "side": self.order.side.value,
            "order_type": self.order.order_type.value,
            "status": self.order.status.value,
            "price": str(self.order.price) if self.order.price else None,
            "quantity": str(self.order.quantity),
            "filled_quantity": str(self.order.filled_quantity),
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class OrderSubmittedEvent(OrderEvent):
    """
    Event published when an order is submitted.
    """
    
    def __init__(self, order: Order, metadata: Optional[dict] = None):
        super().__init__(
            event_type=OrderEventType.SUBMITTED,
            order=order,
            timestamp=datetime.now(UTC),
            metadata=metadata or {}
        )


@dataclass
class OrderCancelledEvent(OrderEvent):
    """
    Event published when an order is cancelled.
    """
    cancelled_by: str
    reason: Optional[str] = None
    
    def __init__(
        self,
        order: Order,
        cancelled_by: str,
        reason: Optional[str] = None,
        metadata: Optional[dict] = None
    ):
        super().__init__(
            event_type=OrderEventType.CANCELLED,
            order=order,
            timestamp=datetime.now(UTC),
            metadata=metadata or {}
        )
        self.cancelled_by = cancelled_by
        self.reason = reason
    
    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update({
            "cancelled_by": self.cancelled_by,
            "reason": self.reason,
        })
        return data


@dataclass
class OrderFilledEvent(OrderEvent):
    """
    Event published when an order is completely filled.
    """
    trades: List[Trade]
    average_price: Decimal
    total_filled: Decimal
    
    def __init__(
        self,
        order: Order,
        trades: List[Trade],
        metadata: Optional[dict] = None
    ):
        super().__init__(
            event_type=OrderEventType.FILLED,
            order=order,
            timestamp=datetime.now(UTC),
            metadata=metadata or {}
        )
        self.trades = trades
        self.total_filled = sum(t.quantity for t in trades)
        
        # Calculate average price
        if trades:
            total_value = sum(t.price * t.quantity for t in trades)
            self.average_price = total_value / self.total_filled
        else:
            self.average_price = Decimal(0)
    
    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update({
            "trades": [
                {
                    "trade_id": t.trade_id,
                    "price": str(t.price),
                    "quantity": str(t.quantity),
                    "timestamp": t.timestamp.isoformat(),
                }
                for t in self.trades
            ],
            "average_price": str(self.average_price),
            "total_filled": str(self.total_filled),
            "trade_count": len(self.trades),
        })
        return data


@dataclass
class OrderPartiallyFilledEvent(OrderEvent):
    """
    Event published when an order is partially filled.
    """
    trades: List[Trade]
    filled_quantity: Decimal
    remaining_quantity: Decimal
    
    def __init__(
        self,
        order: Order,
        trades: List[Trade],
        metadata: Optional[dict] = None
    ):
        super().__init__(
            event_type=OrderEventType.PARTIALLY_FILLED,
            order=order,
            timestamp=datetime.now(UTC),
            metadata=metadata or {}
        )
        self.trades = trades
        self.filled_quantity = order.filled_quantity
        self.remaining_quantity = order.remaining_quantity
    
    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update({
            "trades": [
                {
                    "trade_id": t.trade_id,
                    "price": str(t.price),
                    "quantity": str(t.quantity),
                }
                for t in self.trades
            ],
            "filled_quantity": str(self.filled_quantity),
            "remaining_quantity": str(self.remaining_quantity),
        })
        return data


@dataclass
class OrderRejectedEvent(OrderEvent):
    """
    Event published when an order is rejected.
    """
    reason: str
    error_code: Optional[str] = None
    
    def __init__(
        self,
        order: Order,
        reason: str,
        error_code: Optional[str] = None,
        metadata: Optional[dict] = None
    ):
        super().__init__(
            event_type=OrderEventType.REJECTED,
            order=order,
            timestamp=datetime.now(UTC),
            metadata=metadata or {}
        )
        self.reason = reason
        self.error_code = error_code
    
    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update({
            "reason": self.reason,
            "error_code": self.error_code,
        })
        return data


@dataclass
class OrderAmendedEvent(OrderEvent):
    """
    Event published when an order is amended.
    """
    old_order_id: str
    old_price: Optional[Decimal]
    old_quantity: Decimal
    new_price: Optional[Decimal]
    new_quantity: Decimal
    
    def __init__(
        self,
        order: Order,
        old_order_id: str,
        old_price: Optional[Decimal],
        old_quantity: Decimal,
        metadata: Optional[dict] = None
    ):
        super().__init__(
            event_type=OrderEventType.AMENDED,
            order=order,
            timestamp=datetime.now(UTC),
            metadata=metadata or {}
        )
        self.old_order_id = old_order_id
        self.old_price = old_price
        self.old_quantity = old_quantity
        self.new_price = order.price
        self.new_quantity = order.quantity
    
    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update({
            "old_order_id": self.old_order_id,
            "old_price": str(self.old_price) if self.old_price else None,
            "old_quantity": str(self.old_quantity),
            "new_price": str(self.new_price) if self.new_price else None,
            "new_quantity": str(self.new_quantity),
        })
        return data


@dataclass
class OrderExpiredEvent(OrderEvent):
    """
    Event published when an order expires.
    """
    expiry_time: datetime
    
    def __init__(
        self,
        order: Order,
        expiry_time: datetime,
        metadata: Optional[dict] = None
    ):
        super().__init__(
            event_type=OrderEventType.EXPIRED,
            order=order,
            timestamp=datetime.now(UTC),
            metadata=metadata or {}
        )
        self.expiry_time = expiry_time
    
    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update({
            "expiry_time": self.expiry_time.isoformat(),
        })
        return data
