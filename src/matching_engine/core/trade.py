"""
Trade Model

Represents a completed trade between two orders with full lifecycle tracking.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from datetime import datetime, UTC
from typing import Dict, Any, Optional
from enum import Enum
import uuid


class SettlementStatus(Enum):
    """Trade settlement status"""
    PENDING = "pending"
    SETTLED = "settled"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Trade:
    """
    Represents a completed trade between two orders.
    
    Attributes:
        trade_id: Unique trade identifier
        symbol: Trading pair symbol (e.g., 'BTC-USD')
        buyer_order_id: ID of the buy order
        seller_order_id: ID of the sell order
        buyer_user_id: ID of the buyer
        seller_user_id: ID of the seller
        price: Execution price
        quantity: Executed quantity
        timestamp: Trade execution timestamp
        settlement_status: Current settlement status
        maker_fee: Fee charged to maker (liquidity provider)
        taker_fee: Fee charged to taker (liquidity taker)
        settled_at: Timestamp when trade was settled
        metadata: Additional trade metadata
    """
    
    # Core trade information
    trade_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    symbol: str = ""
    buyer_order_id: str = ""
    seller_order_id: str = ""
    buyer_user_id: str = ""
    seller_user_id: str = ""
    price: Decimal = Decimal("0")
    quantity: Decimal = Decimal("0")
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    
    # Settlement information
    settlement_status: SettlementStatus = SettlementStatus.PENDING
    settled_at: Optional[datetime] = None
    
    # Fee information
    maker_fee: Decimal = Decimal("0")
    taker_fee: Decimal = Decimal("0")
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate trade data after initialization"""
        if not self.symbol:
            raise ValueError("Symbol is required")
        if not self.buyer_order_id:
            raise ValueError("Buyer order ID is required")
        if not self.seller_order_id:
            raise ValueError("Seller order ID is required")
        if not self.buyer_user_id:
            raise ValueError("Buyer user ID is required")
        if not self.seller_user_id:
            raise ValueError("Seller user ID is required")
        if self.price <= 0:
            raise ValueError("Price must be positive")
        if self.quantity <= 0:
            raise ValueError("Quantity must be positive")
    
    @property
    def total_value(self) -> Decimal:
        """Calculate total trade value (price * quantity)"""
        return self.price * self.quantity
    
    @property
    def total_fees(self) -> Decimal:
        """Calculate total fees (maker + taker)"""
        return self.maker_fee + self.taker_fee
    
    @property
    def is_settled(self) -> bool:
        """Check if trade is settled"""
        return self.settlement_status == SettlementStatus.SETTLED
    
    @property
    def is_pending(self) -> bool:
        """Check if trade is pending settlement"""
        return self.settlement_status == SettlementStatus.PENDING
    
    @property
    def is_failed(self) -> bool:
        """Check if trade settlement failed"""
        return self.settlement_status == SettlementStatus.FAILED
    
    def settle(self) -> None:
        """Mark trade as settled"""
        if self.settlement_status != SettlementStatus.PENDING:
            raise ValueError(f"Cannot settle trade with status {self.settlement_status.value}")
        
        self.settlement_status = SettlementStatus.SETTLED
        self.settled_at = datetime.now(UTC)
    
    def fail_settlement(self, reason: str = "") -> None:
        """Mark trade settlement as failed"""
        if self.settlement_status != SettlementStatus.PENDING:
            raise ValueError(f"Cannot fail trade with status {self.settlement_status.value}")
        
        self.settlement_status = SettlementStatus.FAILED
        if reason:
            self.metadata['failure_reason'] = reason
    
    def cancel(self, reason: str = "") -> None:
        """Cancel the trade"""
        if self.settlement_status == SettlementStatus.SETTLED:
            raise ValueError("Cannot cancel settled trade")
        
        self.settlement_status = SettlementStatus.CANCELLED
        if reason:
            self.metadata['cancellation_reason'] = reason
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert trade to dictionary representation.
        
        Returns:
            Dictionary with trade data
        """
        return {
            'trade_id': self.trade_id,
            'symbol': self.symbol,
            'buyer_order_id': self.buyer_order_id,
            'seller_order_id': self.seller_order_id,
            'buyer_user_id': self.buyer_user_id,
            'seller_user_id': self.seller_user_id,
            'price': str(self.price),
            'quantity': str(self.quantity),
            'total_value': str(self.total_value),
            'timestamp': self.timestamp.isoformat(),
            'settlement_status': self.settlement_status.value,
            'settled_at': self.settled_at.isoformat() if self.settled_at else None,
            'maker_fee': str(self.maker_fee),
            'taker_fee': str(self.taker_fee),
            'total_fees': str(self.total_fees),
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Trade':
        """
        Create trade from dictionary.
        
        Args:
            data: Dictionary with trade data
            
        Returns:
            Trade instance
        """
        return cls(
            trade_id=data.get('trade_id', str(uuid.uuid4())),
            symbol=data['symbol'],
            buyer_order_id=data['buyer_order_id'],
            seller_order_id=data['seller_order_id'],
            buyer_user_id=data['buyer_user_id'],
            seller_user_id=data['seller_user_id'],
            price=Decimal(str(data['price'])),
            quantity=Decimal(str(data['quantity'])),
            timestamp=datetime.fromisoformat(data['timestamp']) if isinstance(data.get('timestamp'), str) else data.get('timestamp', datetime.now(UTC)),
            settlement_status=SettlementStatus(data.get('settlement_status', 'pending')),
            settled_at=datetime.fromisoformat(data['settled_at']) if data.get('settled_at') else None,
            maker_fee=Decimal(str(data.get('maker_fee', 0))),
            taker_fee=Decimal(str(data.get('taker_fee', 0))),
            metadata=data.get('metadata', {})
        )
    
    def __repr__(self) -> str:
        """String representation of trade"""
        return (
            f"Trade(id={self.trade_id[:8]}..., symbol={self.symbol}, "
            f"price={self.price}, quantity={self.quantity}, "
            f"value={self.total_value}, status={self.settlement_status.value})"
        )
    
    def __str__(self) -> str:
        """Human-readable string representation"""
        return (
            f"Trade {self.trade_id[:8]}: {self.quantity} {self.symbol} @ ${self.price} "
            f"(Total: ${self.total_value}) - {self.settlement_status.value}"
        )
