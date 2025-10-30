"""
Trade Events

Events published during trade lifecycle.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any

from ..core.trade import SettlementStatus


@dataclass
class TradeExecutedEvent:
    """
    Published when a trade is executed.
    
    This event is fired immediately after two orders match and a trade is created.
    """
    
    trade_id: str
    symbol: str
    buyer_order_id: str
    seller_order_id: str
    buyer_user_id: str
    seller_user_id: str
    price: Decimal
    quantity: Decimal
    timestamp: datetime
    
    @property
    def event_type(self) -> str:
        return "trade.executed"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary"""
        return {
            'event_type': self.event_type,
            'trade_id': self.trade_id,
            'symbol': self.symbol,
            'buyer_order_id': self.buyer_order_id,
            'seller_order_id': self.seller_order_id,
            'buyer_user_id': self.buyer_user_id,
            'seller_user_id': self.seller_user_id,
            'price': str(self.price),
            'quantity': str(self.quantity),
            'total_value': str(self.price * self.quantity),
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class TradeSettledEvent:
    """
    Published when a trade is settled.
    
    This event is fired after settlement is complete (funds/assets transferred).
    """
    
    trade_id: str
    symbol: str
    buyer_user_id: str
    seller_user_id: str
    settlement_status: SettlementStatus
    settled_at: datetime
    
    @property
    def event_type(self) -> str:
        return "trade.settled"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary"""
        return {
            'event_type': self.event_type,
            'trade_id': self.trade_id,
            'symbol': self.symbol,
            'buyer_user_id': self.buyer_user_id,
            'seller_user_id': self.seller_user_id,
            'settlement_status': self.settlement_status.value,
            'settled_at': self.settled_at.isoformat()
        }


@dataclass
class TradeFailedEvent:
    """
    Published when a trade settlement fails.
    
    This event is fired when settlement cannot be completed.
    """
    
    trade_id: str
    symbol: str
    buyer_user_id: str
    seller_user_id: str
    reason: str
    timestamp: datetime
    
    @property
    def event_type(self) -> str:
        return "trade.failed"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary"""
        return {
            'event_type': self.event_type,
            'trade_id': self.trade_id,
            'symbol': self.symbol,
            'buyer_user_id': self.buyer_user_id,
            'seller_user_id': self.seller_user_id,
            'reason': self.reason,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class TradeCancelledEvent:
    """
    Published when a trade is cancelled.
    
    This event is fired when a trade is cancelled before settlement.
    """
    
    trade_id: str
    symbol: str
    buyer_user_id: str
    seller_user_id: str
    reason: str
    timestamp: datetime
    
    @property
    def event_type(self) -> str:
        return "trade.cancelled"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary"""
        return {
            'event_type': self.event_type,
            'trade_id': self.trade_id,
            'symbol': self.symbol,
            'buyer_user_id': self.buyer_user_id,
            'seller_user_id': self.seller_user_id,
            'reason': self.reason,
            'timestamp': self.timestamp.isoformat()
        }
