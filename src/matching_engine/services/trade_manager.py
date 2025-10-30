"""
Trade Manager

Manages trade lifecycle, execution, and fee calculation.
"""

from typing import List, Dict, Optional, Tuple
from decimal import Decimal
from datetime import datetime, UTC
import logging

from ..core.trade import Trade, SettlementStatus
from ..core.order import Order
from ..repositories import TradeRepository
from ..events import (
    EventPublisher,
    TradeExecutedEvent,
    TradeSettledEvent,
    TradeFailedEvent,
    TradeCancelledEvent
)

logger = logging.getLogger(__name__)


class FeeConfig:
    """Fee configuration for trades"""
    
    def __init__(
        self,
        maker_fee_rate: Decimal = Decimal("0.001"),  # 0.1%
        taker_fee_rate: Decimal = Decimal("0.002"),  # 0.2%
        min_fee: Decimal = Decimal("0.01"),
        max_fee: Optional[Decimal] = None
    ):
        """
        Initialize fee configuration.
        
        Args:
            maker_fee_rate: Fee rate for maker (liquidity provider)
            taker_fee_rate: Fee rate for taker (liquidity taker)
            min_fee: Minimum fee per trade
            max_fee: Maximum fee per trade (None for no limit)
        """
        self.maker_fee_rate = maker_fee_rate
        self.taker_fee_rate = taker_fee_rate
        self.min_fee = min_fee
        self.max_fee = max_fee


class TradeManager:
    """
    Manages trade lifecycle and execution.
    
    Responsibilities:
    - Create trades from matched orders
    - Calculate fees
    - Publish trade events
    - Manage trade history
    """
    
    def __init__(
        self,
        repository: Optional[TradeRepository] = None,
        event_publisher: Optional[EventPublisher] = None,
        fee_config: Optional[FeeConfig] = None
    ):
        """
        Initialize trade manager.
        
        Args:
            repository: Trade repository for persistence
            event_publisher: Event publisher for trade events
            fee_config: Fee configuration
        """
        self.repository = repository or TradeRepository()
        self.event_publisher = event_publisher or EventPublisher()
        self.fee_config = fee_config or FeeConfig()
        
        logger.info("TradeManager initialized")
    
    def create_trade(
        self,
        buy_order: Order,
        sell_order: Order,
        price: Decimal,
        quantity: Decimal,
        maker_order: Order
    ) -> Trade:
        """
        Create a trade from matched orders.
        
        Args:
            buy_order: Buy order
            sell_order: Sell order
            price: Execution price
            quantity: Execution quantity
            maker_order: The order that was in the book (maker)
            
        Returns:
            Created trade
        """
        # Determine maker and taker
        is_buy_maker = (maker_order.order_id == buy_order.order_id)
        
        # Calculate fees
        maker_fee = self._calculate_fee(price, quantity, is_maker=True)
        taker_fee = self._calculate_fee(price, quantity, is_maker=False)
        
        # Create trade
        trade = Trade(
            symbol=buy_order.symbol,
            buyer_order_id=buy_order.order_id,
            seller_order_id=sell_order.order_id,
            buyer_user_id=buy_order.user_id,
            seller_user_id=sell_order.user_id,
            price=price,
            quantity=quantity,
            maker_fee=maker_fee,
            taker_fee=taker_fee,
            timestamp=datetime.now(UTC)
        )
        
        # Add metadata
        trade.metadata['maker_side'] = 'buy' if is_buy_maker else 'sell'
        trade.metadata['taker_side'] = 'sell' if is_buy_maker else 'buy'
        
        logger.info(
            f"Created trade {trade.trade_id}: {quantity} {trade.symbol} @ {price} "
            f"(maker_fee={maker_fee}, taker_fee={taker_fee})"
        )
        
        return trade
    
    def execute_trade(
        self,
        buy_order: Order,
        sell_order: Order,
        price: Decimal,
        quantity: Decimal,
        maker_order: Order
    ) -> Trade:
        """
        Execute a trade (create, save, and publish event).
        
        Args:
            buy_order: Buy order
            sell_order: Sell order
            price: Execution price
            quantity: Execution quantity
            maker_order: The order that was in the book (maker)
            
        Returns:
            Executed trade
        """
        # Create trade
        trade = self.create_trade(buy_order, sell_order, price, quantity, maker_order)
        
        # Save to database
        try:
            self.repository.save(trade)
            logger.debug(f"Trade {trade.trade_id} saved to database")
        except Exception as e:
            logger.error(f"Failed to save trade {trade.trade_id}: {e}")
            raise
        
        # Publish event
        self._publish_trade_executed(trade)
        
        return trade
    
    def settle_trade(self, trade_id: str) -> bool:
        """
        Mark a trade as settled.
        
        Args:
            trade_id: Trade ID
            
        Returns:
            True if settled successfully
        """
        trade = self.repository.get(trade_id)
        
        if not trade:
            logger.error(f"Trade {trade_id} not found")
            return False
        
        if trade.is_settled:
            logger.warning(f"Trade {trade_id} is already settled")
            return True
        
        try:
            # Mark as settled
            trade.settle()
            
            # Save to database
            self.repository.save(trade)
            
            # Publish event
            self._publish_trade_settled(trade)
            
            logger.info(f"Trade {trade_id} settled successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to settle trade {trade_id}: {e}")
            return False
    
    def fail_trade(self, trade_id: str, reason: str) -> bool:
        """
        Mark a trade as failed.
        
        Args:
            trade_id: Trade ID
            reason: Failure reason
            
        Returns:
            True if marked as failed successfully
        """
        trade = self.repository.get(trade_id)
        
        if not trade:
            logger.error(f"Trade {trade_id} not found")
            return False
        
        try:
            # Mark as failed
            trade.fail_settlement(reason)
            
            # Save to database
            self.repository.save(trade)
            
            # Publish event
            self._publish_trade_failed(trade, reason)
            
            logger.warning(f"Trade {trade_id} marked as failed: {reason}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to mark trade {trade_id} as failed: {e}")
            return False
    
    def cancel_trade(self, trade_id: str, reason: str) -> bool:
        """
        Cancel a trade.
        
        Args:
            trade_id: Trade ID
            reason: Cancellation reason
            
        Returns:
            True if cancelled successfully
        """
        trade = self.repository.get(trade_id)
        
        if not trade:
            logger.error(f"Trade {trade_id} not found")
            return False
        
        try:
            # Cancel trade
            trade.cancel(reason)
            
            # Save to database
            self.repository.save(trade)
            
            # Publish event
            self._publish_trade_cancelled(trade, reason)
            
            logger.info(f"Trade {trade_id} cancelled: {reason}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel trade {trade_id}: {e}")
            return False
    
    def get_trade(self, trade_id: str) -> Optional[Trade]:
        """
        Get a trade by ID.
        
        Args:
            trade_id: Trade ID
            
        Returns:
            Trade if found, None otherwise
        """
        return self.repository.get(trade_id)
    
    def get_trade_history(
        self,
        user_id: Optional[str] = None,
        symbol: Optional[str] = None,
        limit: int = 100
    ) -> List[Trade]:
        """
        Get trade history.
        
        Args:
            user_id: Filter by user ID
            symbol: Filter by symbol
            limit: Maximum number of trades
            
        Returns:
            List of trades
        """
        if user_id:
            return self.repository.find_by_user(user_id, limit=limit)
        elif symbol:
            return self.repository.find_by_symbol(symbol, limit=limit)
        else:
            return self.repository.find(limit=limit)
    
    def get_user_volume(self, user_id: str) -> Decimal:
        """
        Get total trading volume for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Total volume
        """
        return self.repository.get_volume_by_user(user_id)
    
    def get_symbol_volume(self, symbol: str) -> Decimal:
        """
        Get total trading volume for a symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Total volume
        """
        return self.repository.get_volume_by_symbol(symbol)
    
    def get_statistics(self) -> Dict:
        """
        Get trade statistics.
        
        Returns:
            Dictionary with statistics
        """
        return self.repository.get_statistics()
    
    def _calculate_fee(self, price: Decimal, quantity: Decimal, is_maker: bool) -> Decimal:
        """
        Calculate fee for a trade.
        
        Args:
            price: Trade price
            quantity: Trade quantity
            is_maker: True if maker, False if taker
            
        Returns:
            Fee amount
        """
        trade_value = price * quantity
        
        # Apply fee rate
        if is_maker:
            fee = trade_value * self.fee_config.maker_fee_rate
        else:
            fee = trade_value * self.fee_config.taker_fee_rate
        
        # Apply minimum fee
        if fee < self.fee_config.min_fee:
            fee = self.fee_config.min_fee
        
        # Apply maximum fee if set
        if self.fee_config.max_fee and fee > self.fee_config.max_fee:
            fee = self.fee_config.max_fee
        
        return fee
    
    def _publish_trade_executed(self, trade: Trade) -> None:
        """Publish trade executed event"""
        event = TradeExecutedEvent(
            trade_id=trade.trade_id,
            symbol=trade.symbol,
            buyer_order_id=trade.buyer_order_id,
            seller_order_id=trade.seller_order_id,
            buyer_user_id=trade.buyer_user_id,
            seller_user_id=trade.seller_user_id,
            price=trade.price,
            quantity=trade.quantity,
            timestamp=trade.timestamp
        )
        self.event_publisher.publish(event)
        logger.debug(f"Published TradeExecutedEvent for {trade.trade_id}")
    
    def _publish_trade_settled(self, trade: Trade) -> None:
        """Publish trade settled event"""
        event = TradeSettledEvent(
            trade_id=trade.trade_id,
            symbol=trade.symbol,
            buyer_user_id=trade.buyer_user_id,
            seller_user_id=trade.seller_user_id,
            settlement_status=trade.settlement_status,
            settled_at=trade.settled_at
        )
        self.event_publisher.publish(event)
        logger.debug(f"Published TradeSettledEvent for {trade.trade_id}")
    
    def _publish_trade_failed(self, trade: Trade, reason: str) -> None:
        """Publish trade failed event"""
        event = TradeFailedEvent(
            trade_id=trade.trade_id,
            symbol=trade.symbol,
            buyer_user_id=trade.buyer_user_id,
            seller_user_id=trade.seller_user_id,
            reason=reason,
            timestamp=datetime.now(UTC)
        )
        self.event_publisher.publish(event)
        logger.debug(f"Published TradeFailedEvent for {trade.trade_id}")
    
    def _publish_trade_cancelled(self, trade: Trade, reason: str) -> None:
        """Publish trade cancelled event"""
        event = TradeCancelledEvent(
            trade_id=trade.trade_id,
            symbol=trade.symbol,
            buyer_user_id=trade.buyer_user_id,
            seller_user_id=trade.seller_user_id,
            reason=reason,
            timestamp=datetime.now(UTC)
        )
        self.event_publisher.publish(event)
        logger.debug(f"Published TradeCancelledEvent for {trade.trade_id}")
