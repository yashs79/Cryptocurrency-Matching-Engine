"""
Trade Repository

Handles persistence and querying of trades.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session
import logging

from ..core.trade import Trade, SettlementStatus
from ..models.trade_model import TradeModel
from ..config import database

logger = logging.getLogger(__name__)


class TradeFilter:
    """Filter criteria for trade queries"""
    
    def __init__(
        self,
        trade_id: Optional[str] = None,
        symbol: Optional[str] = None,
        buyer_user_id: Optional[str] = None,
        seller_user_id: Optional[str] = None,
        buyer_order_id: Optional[str] = None,
        seller_order_id: Optional[str] = None,
        settlement_status: Optional[SettlementStatus] = None,
        min_price: Optional[Decimal] = None,
        max_price: Optional[Decimal] = None,
        min_quantity: Optional[Decimal] = None,
        max_quantity: Optional[Decimal] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ):
        self.trade_id = trade_id
        self.symbol = symbol
        self.buyer_user_id = buyer_user_id
        self.seller_user_id = seller_user_id
        self.buyer_order_id = buyer_order_id
        self.seller_order_id = seller_order_id
        self.settlement_status = settlement_status
        self.min_price = min_price
        self.max_price = max_price
        self.min_quantity = min_quantity
        self.max_quantity = max_quantity
        self.start_time = start_time
        self.end_time = end_time


class TradeRepository:
    """Repository for trade persistence and queries"""
    
    def __init__(self, session: Optional[Session] = None):
        """
        Initialize repository.
        
        Args:
            session: Optional SQLAlchemy session. If not provided, will create new sessions.
        """
        self._session = session
        self._owns_session = session is None
    
    def _get_session(self) -> Session:
        """Get database session"""
        if self._session:
            return self._session
        if database._db_config is None:
            raise RuntimeError("Database not initialized. Call init_db() first.")
        return database._db_config.get_session()
    
    def save(self, trade: Trade) -> None:
        """
        Save trade to database.
        
        Args:
            trade: Trade to save
        """
        session = self._get_session()
        
        try:
            # Check if trade already exists
            existing = session.query(TradeModel).filter_by(trade_id=trade.trade_id).first()
            
            if existing:
                # Update existing trade
                existing.settlement_status = trade.settlement_status.value
                existing.settled_at = trade.settled_at
                existing.maker_fee = trade.maker_fee
                existing.taker_fee = trade.taker_fee
                logger.debug(f"Updated trade {trade.trade_id}")
            else:
                # Create new trade
                trade_model = TradeModel.from_trade(trade)
                session.add(trade_model)
                logger.debug(f"Saved new trade {trade.trade_id}")
            
            if self._owns_session:
                session.commit()
        except Exception as e:
            if self._owns_session:
                session.rollback()
            logger.error(f"Error saving trade: {e}")
            raise
        finally:
            if self._owns_session:
                session.close()
    
    def get(self, trade_id: str) -> Optional[Trade]:
        """
        Get trade by ID.
        
        Args:
            trade_id: Trade ID
            
        Returns:
            Trade if found, None otherwise
        """
        session = self._get_session()
        
        try:
            trade_model = session.query(TradeModel).filter_by(trade_id=trade_id).first()
            
            if trade_model:
                return trade_model.to_trade()
            return None
        finally:
            if self._owns_session:
                session.close()
    
    def find(
        self,
        filter: Optional[TradeFilter] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Trade]:
        """
        Find trades matching filter criteria.
        
        Args:
            filter: Filter criteria
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of matching trades
        """
        session = self._get_session()
        
        try:
            query = session.query(TradeModel)
            
            # Apply filters
            if filter:
                if filter.trade_id:
                    query = query.filter(TradeModel.trade_id == filter.trade_id)
                if filter.symbol:
                    query = query.filter(TradeModel.symbol == filter.symbol)
                if filter.buyer_user_id:
                    query = query.filter(TradeModel.buyer_user_id == filter.buyer_user_id)
                if filter.seller_user_id:
                    query = query.filter(TradeModel.seller_user_id == filter.seller_user_id)
                if filter.buyer_order_id:
                    query = query.filter(TradeModel.buyer_order_id == filter.buyer_order_id)
                if filter.seller_order_id:
                    query = query.filter(TradeModel.seller_order_id == filter.seller_order_id)
                if filter.settlement_status:
                    query = query.filter(TradeModel.settlement_status == filter.settlement_status.value)
                if filter.min_price:
                    query = query.filter(TradeModel.price >= filter.min_price)
                if filter.max_price:
                    query = query.filter(TradeModel.price <= filter.max_price)
                if filter.min_quantity:
                    query = query.filter(TradeModel.quantity >= filter.min_quantity)
                if filter.max_quantity:
                    query = query.filter(TradeModel.quantity <= filter.max_quantity)
                if filter.start_time:
                    query = query.filter(TradeModel.timestamp >= filter.start_time)
                if filter.end_time:
                    query = query.filter(TradeModel.timestamp <= filter.end_time)
            
            # Order by timestamp descending
            query = query.order_by(TradeModel.timestamp.desc())
            
            # Apply limit and offset
            query = query.limit(limit).offset(offset)
            
            trade_models = query.all()
            return [tm.to_trade() for tm in trade_models]
        finally:
            if self._owns_session:
                session.close()
    
    def find_by_user(self, user_id: str, limit: int = 100) -> List[Trade]:
        """
        Find all trades for a user (as buyer or seller).
        
        Args:
            user_id: User ID
            limit: Maximum number of results
            
        Returns:
            List of user's trades
        """
        session = self._get_session()
        
        try:
            query = session.query(TradeModel).filter(
                or_(
                    TradeModel.buyer_user_id == user_id,
                    TradeModel.seller_user_id == user_id
                )
            ).order_by(TradeModel.timestamp.desc()).limit(limit)
            
            trade_models = query.all()
            return [tm.to_trade() for tm in trade_models]
        finally:
            if self._owns_session:
                session.close()
    
    def find_by_symbol(self, symbol: str, limit: int = 100) -> List[Trade]:
        """
        Find all trades for a symbol.
        
        Args:
            symbol: Trading symbol
            limit: Maximum number of results
            
        Returns:
            List of trades for symbol
        """
        filter = TradeFilter(symbol=symbol)
        return self.find(filter=filter, limit=limit)
    
    def find_by_order(self, order_id: str) -> List[Trade]:
        """
        Find all trades involving an order.
        
        Args:
            order_id: Order ID
            
        Returns:
            List of trades involving the order
        """
        session = self._get_session()
        
        try:
            query = session.query(TradeModel).filter(
                or_(
                    TradeModel.buyer_order_id == order_id,
                    TradeModel.seller_order_id == order_id
                )
            ).order_by(TradeModel.timestamp.desc())
            
            trade_models = query.all()
            return [tm.to_trade() for tm in trade_models]
        finally:
            if self._owns_session:
                session.close()
    
    def find_by_time_range(
        self,
        start_time: datetime,
        end_time: datetime,
        symbol: Optional[str] = None
    ) -> List[Trade]:
        """
        Find trades within a time range.
        
        Args:
            start_time: Start of time range
            end_time: End of time range
            symbol: Optional symbol filter
            
        Returns:
            List of trades in time range
        """
        filter = TradeFilter(
            start_time=start_time,
            end_time=end_time,
            symbol=symbol
        )
        return self.find(filter=filter, limit=10000)
    
    def get_volume_by_symbol(self, symbol: str) -> Decimal:
        """
        Get total trading volume for a symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Total volume
        """
        session = self._get_session()
        
        try:
            result = session.query(
                func.sum(TradeModel.quantity)
            ).filter(
                TradeModel.symbol == symbol,
                TradeModel.settlement_status == SettlementStatus.SETTLED.value
            ).scalar()
            
            return Decimal(str(result)) if result else Decimal("0")
        finally:
            if self._owns_session:
                session.close()
    
    def get_volume_by_user(self, user_id: str) -> Decimal:
        """
        Get total trading volume for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Total volume
        """
        session = self._get_session()
        
        try:
            result = session.query(
                func.sum(TradeModel.quantity)
            ).filter(
                or_(
                    TradeModel.buyer_user_id == user_id,
                    TradeModel.seller_user_id == user_id
                ),
                TradeModel.settlement_status == SettlementStatus.SETTLED.value
            ).scalar()
            
            return Decimal(str(result)) if result else Decimal("0")
        finally:
            if self._owns_session:
                session.close()
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get trade statistics.
        
        Returns:
            Dictionary with statistics
        """
        session = self._get_session()
        
        try:
            total_trades = session.query(func.count(TradeModel.trade_id)).scalar()
            
            total_volume = session.query(
                func.sum(TradeModel.quantity)
            ).filter(
                TradeModel.settlement_status == SettlementStatus.SETTLED.value
            ).scalar()
            
            total_value = session.query(
                func.sum(TradeModel.price * TradeModel.quantity)
            ).filter(
                TradeModel.settlement_status == SettlementStatus.SETTLED.value
            ).scalar()
            
            # Count by status
            status_counts = {}
            for status in SettlementStatus:
                count = session.query(func.count(TradeModel.trade_id)).filter(
                    TradeModel.settlement_status == status.value
                ).scalar()
                status_counts[status.value] = count
            
            # Unique symbols
            unique_symbols = session.query(
                func.count(func.distinct(TradeModel.symbol))
            ).scalar()
            
            # Unique users
            buyer_count = session.query(
                func.count(func.distinct(TradeModel.buyer_user_id))
            ).scalar()
            seller_count = session.query(
                func.count(func.distinct(TradeModel.seller_user_id))
            ).scalar()
            
            return {
                'total_trades': total_trades or 0,
                'total_volume': str(total_volume) if total_volume else '0',
                'total_value': str(total_value) if total_value else '0',
                'status_breakdown': status_counts,
                'unique_symbols': unique_symbols or 0,
                'unique_buyers': buyer_count or 0,
                'unique_sellers': seller_count or 0
            }
        finally:
            if self._owns_session:
                session.close()
    
    def count(self, filter: Optional[TradeFilter] = None) -> int:
        """
        Count trades matching filter.
        
        Args:
            filter: Optional filter criteria
            
        Returns:
            Number of matching trades
        """
        session = self._get_session()
        
        try:
            query = session.query(func.count(TradeModel.trade_id))
            
            if filter:
                if filter.symbol:
                    query = query.filter(TradeModel.symbol == filter.symbol)
                if filter.settlement_status:
                    query = query.filter(TradeModel.settlement_status == filter.settlement_status.value)
                # Add other filters as needed
            
            return query.scalar() or 0
        finally:
            if self._owns_session:
                session.close()
    
    def delete(self, trade_id: str) -> bool:
        """
        Delete a trade (use with caution!).
        
        Args:
            trade_id: Trade ID
            
        Returns:
            True if deleted, False if not found
        """
        session = self._get_session()
        
        try:
            trade_model = session.query(TradeModel).filter_by(trade_id=trade_id).first()
            
            if trade_model:
                session.delete(trade_model)
                if self._owns_session:
                    session.commit()
                logger.warning(f"Deleted trade {trade_id}")
                return True
            return False
        except Exception as e:
            if self._owns_session:
                session.rollback()
            logger.error(f"Error deleting trade: {e}")
            raise
        finally:
            if self._owns_session:
                session.close()
    
    def close(self):
        """Close the repository and cleanup resources"""
        if self._owns_session and self._session:
            self._session.close()
