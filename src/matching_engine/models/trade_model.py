"""
Trade Database Model

SQLAlchemy model for persisting trades.
"""

from sqlalchemy import Column, String, Numeric, DateTime, Index
from sqlalchemy.sql import func
from datetime import datetime
from decimal import Decimal
from typing import Optional

from ..config.database import Base
from ..core.trade import Trade, SettlementStatus


class TradeModel(Base):
    """
    Database model for trades.
    
    Maps to the Trade domain object.
    """
    __tablename__ = "trades"
    
    # Primary key
    trade_id = Column(String(36), primary_key=True, index=True)
    
    # Trade details
    symbol = Column(String(20), nullable=False, index=True)
    buyer_order_id = Column(String(36), nullable=False, index=True)
    seller_order_id = Column(String(36), nullable=False, index=True)
    buyer_user_id = Column(String(255), nullable=False, index=True)
    seller_user_id = Column(String(255), nullable=False, index=True)
    
    # Pricing and quantity
    price = Column(Numeric(20, 8), nullable=False)
    quantity = Column(Numeric(20, 8), nullable=False)
    
    # Settlement
    settlement_status = Column(String(50), nullable=False, default='pending', index=True)
    settled_at = Column(DateTime(timezone=True), nullable=True)
    
    # Fees
    maker_fee = Column(Numeric(20, 8), nullable=False, default=0)
    taker_fee = Column(Numeric(20, 8), nullable=False, default=0)
    
    # Timestamps
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Composite indexes for common queries
    __table_args__ = (
        Index('idx_symbol_timestamp', 'symbol', 'timestamp'),
        Index('idx_buyer_order', 'buyer_order_id'),
        Index('idx_seller_order', 'seller_order_id'),
        Index('idx_buyer_user', 'buyer_user_id'),
        Index('idx_seller_user', 'seller_user_id'),
        Index('idx_settlement_status', 'settlement_status'),
    )
    
    @classmethod
    def from_trade(cls, trade: Trade) -> "TradeModel":
        """
        Create TradeModel from Trade domain object.
        
        Args:
            trade: Trade domain object
            
        Returns:
            TradeModel instance
        """
        return cls(
            trade_id=trade.trade_id,
            symbol=trade.symbol,
            buyer_order_id=trade.buyer_order_id,
            seller_order_id=trade.seller_order_id,
            buyer_user_id=trade.buyer_user_id,
            seller_user_id=trade.seller_user_id,
            price=trade.price,
            quantity=trade.quantity,
            settlement_status=trade.settlement_status.value,
            settled_at=trade.settled_at,
            maker_fee=trade.maker_fee,
            taker_fee=trade.taker_fee,
            timestamp=trade.timestamp
        )
    
    def to_trade(self) -> Trade:
        """
        Convert TradeModel to Trade domain object.
        
        Returns:
            Trade domain object
        """
        return Trade(
            trade_id=self.trade_id,
            symbol=self.symbol,
            buyer_order_id=self.buyer_order_id,
            seller_order_id=self.seller_order_id,
            buyer_user_id=self.buyer_user_id,
            seller_user_id=self.seller_user_id,
            price=Decimal(str(self.price)),
            quantity=Decimal(str(self.quantity)),
            timestamp=self.timestamp,
            settlement_status=SettlementStatus(self.settlement_status),
            settled_at=self.settled_at,
            maker_fee=Decimal(str(self.maker_fee)),
            taker_fee=Decimal(str(self.taker_fee))
        )
    
    def __repr__(self) -> str:
        return (
            f"<TradeModel(trade_id='{self.trade_id}', "
            f"symbol='{self.symbol}', "
            f"price={self.price}, "
            f"quantity={self.quantity})>"
        )
