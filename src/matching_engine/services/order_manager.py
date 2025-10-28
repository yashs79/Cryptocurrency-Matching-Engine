"""
Order Manager Service

Manages the complete order lifecycle including submission, cancellation,
amendment, and status tracking. Integrates with validator and matching engine.
"""

from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from datetime import datetime, UTC
from enum import Enum
import logging
import uuid

from ..core.order import Order, OrderStatus, OrderSide, OrderType
from ..core.matching_engine import MatchingEngine, Trade
from .order_validator import OrderValidator, ValidationError

logger = logging.getLogger(__name__)


class OrderAction(Enum):
    """Order action types"""
    SUBMIT = "submit"
    CANCEL = "cancel"
    AMEND = "amend"
    FILL = "fill"
    PARTIAL_FILL = "partial_fill"
    REJECT = "reject"
    EXPIRE = "expire"


class OrderManagerError(Exception):
    """Raised when order management operation fails"""
    pass


class OrderManager:
    """
    Manages order lifecycle and coordinates between validator and matching engine.
    
    Responsibilities:
    - Validate orders before submission
    - Submit orders to matching engine
    - Cancel orders
    - Amend orders (cancel-replace)
    - Track order status
    - Publish order events
    """
    
    def __init__(
        self,
        matching_engine: MatchingEngine,
        validator: Optional[OrderValidator] = None
    ):
        self.matching_engine = matching_engine
        self.validator = validator or OrderValidator()
        self._order_history: Dict[str, List[Tuple[OrderAction, datetime, str]]] = {}
        
        logger.info("OrderManager initialized")
    
    def submit_order(
        self,
        order: Order,
        skip_validation: bool = False
    ) -> Tuple[Order, List[Trade]]:
        """
        Submit an order to the matching engine.
        
        Args:
            order: Order to submit
            skip_validation: Skip validation (use with caution)
            
        Returns:
            Tuple of (processed_order, trades)
            
        Raises:
            ValidationError: If validation fails
            OrderManagerError: If submission fails
        """
        try:
            # Validate order
            if not skip_validation:
                self.validator.validate(order)
                logger.debug(f"Order {order.order_id} validated successfully")
            
            # Submit to matching engine
            processed_order, trades = self.matching_engine.process_order(order)
            
            # Record action
            self._record_action(
                order.order_id,
                OrderAction.SUBMIT,
                f"Order submitted: {order.side.value} {order.quantity} @ {order.price or 'MARKET'}"
            )
            
            # Record fills if any
            if trades:
                self._record_action(
                    order.order_id,
                    OrderAction.FILL if processed_order.status == OrderStatus.FILLED else OrderAction.PARTIAL_FILL,
                    f"Filled {processed_order.filled_quantity} @ avg price"
                )
            
            logger.info(
                f"Order {order.order_id} processed: status={processed_order.status.value}, "
                f"filled={processed_order.filled_quantity}, trades={len(trades)}"
            )
            
            return processed_order, trades
            
        except ValidationError as e:
            self._record_action(
                order.order_id,
                OrderAction.REJECT,
                f"Validation failed: {e.message}"
            )
            logger.warning(f"Order {order.order_id} rejected: {e.message}")
            raise
        
        except Exception as e:
            self._record_action(
                order.order_id,
                OrderAction.REJECT,
                f"Submission failed: {str(e)}"
            )
            logger.error(f"Order {order.order_id} submission failed: {e}")
            raise OrderManagerError(f"Failed to submit order: {e}")
    
    def cancel_order(
        self,
        symbol: str,
        order_id: str,
        user_id: Optional[str] = None
    ) -> bool:
        """
        Cancel an order.
        
        Args:
            symbol: Trading symbol
            order_id: Order ID to cancel
            user_id: User ID (for authorization check)
            
        Returns:
            True if cancelled successfully
            
        Raises:
            OrderManagerError: If cancellation fails
        """
        try:
            # Get order from matching engine
            order = self.matching_engine.get_order(symbol, order_id)
            
            if not order:
                raise OrderManagerError(f"Order {order_id} not found")
            
            # Check authorization if user_id provided
            if user_id and order.user_id != user_id:
                raise OrderManagerError(f"User {user_id} not authorized to cancel order {order_id}")
            
            # Check if order can be cancelled
            if order.status not in [OrderStatus.OPEN, OrderStatus.PARTIALLY_FILLED]:
                raise OrderManagerError(
                    f"Cannot cancel order {order_id} with status {order.status.value}"
                )
            
            # Cancel order
            success = self.matching_engine.cancel_order(symbol, order_id)
            
            if success:
                self._record_action(
                    order_id,
                    OrderAction.CANCEL,
                    f"Order cancelled by {user_id or 'system'}"
                )
                logger.info(f"Order {order_id} cancelled successfully")
            else:
                logger.warning(f"Order {order_id} cancellation returned False")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            raise OrderManagerError(f"Failed to cancel order: {e}")
    
    def amend_order(
        self,
        symbol: str,
        order_id: str,
        new_price: Optional[Decimal] = None,
        new_quantity: Optional[Decimal] = None,
        user_id: Optional[str] = None
    ) -> Tuple[Order, List[Trade]]:
        """
        Amend an order (cancel and replace).
        
        Args:
            symbol: Trading symbol
            order_id: Order ID to amend
            new_price: New price (None to keep current)
            new_quantity: New quantity (None to keep current)
            user_id: User ID (for authorization)
            
        Returns:
            Tuple of (new_order, trades)
            
        Raises:
            OrderManagerError: If amendment fails
        """
        try:
            # Get original order
            original_order = self.matching_engine.get_order(symbol, order_id)
            
            if not original_order:
                raise OrderManagerError(f"Order {order_id} not found")
            
            # Check authorization
            if user_id and original_order.user_id != user_id:
                raise OrderManagerError(f"User {user_id} not authorized to amend order {order_id}")
            
            # Check if order can be amended
            if original_order.status not in [OrderStatus.OPEN, OrderStatus.PARTIALLY_FILLED]:
                raise OrderManagerError(
                    f"Cannot amend order {order_id} with status {original_order.status.value}"
                )
            
            # Cancel original order
            self.cancel_order(symbol, order_id, user_id)
            
            # Create new order with amendments
            new_order = Order(
                user_id=original_order.user_id,
                symbol=original_order.symbol,
                side=original_order.side,
                order_type=original_order.order_type,
                price=new_price if new_price is not None else original_order.price,
                quantity=new_quantity if new_quantity is not None else original_order.remaining_quantity,
            )
            
            # Submit new order
            processed_order, trades = self.submit_order(new_order)
            
            self._record_action(
                order_id,
                OrderAction.AMEND,
                f"Amended to order {new_order.order_id}: price={new_price}, quantity={new_quantity}"
            )
            
            logger.info(
                f"Order {order_id} amended to {new_order.order_id}: "
                f"price={new_price}, quantity={new_quantity}"
            )
            
            return processed_order, trades
            
        except Exception as e:
            logger.error(f"Failed to amend order {order_id}: {e}")
            raise OrderManagerError(f"Failed to amend order: {e}")
    
    def get_order_status(self, symbol: str, order_id: str) -> Optional[Order]:
        """
        Get current order status.
        
        Args:
            symbol: Trading symbol
            order_id: Order ID
            
        Returns:
            Order object or None if not found
        """
        return self.matching_engine.get_order(symbol, order_id)
    
    def get_user_orders(
        self,
        user_id: str,
        symbol: Optional[str] = None,
        status: Optional[OrderStatus] = None
    ) -> List[Order]:
        """
        Get all orders for a user.
        
        Args:
            user_id: User ID
            symbol: Filter by symbol (optional)
            status: Filter by status (optional)
            
        Returns:
            List of orders
        """
        all_orders = []
        
        # Get symbols to check
        if symbol:
            symbols = [symbol]
        else:
            # Get all symbols from matching engine
            symbols = list(self.matching_engine.order_books.keys())
        
        # Collect orders from each symbol
        for sym in symbols:
            book = self.matching_engine.get_order_book(sym)
            if book:
                # Get all orders from the book
                for order_id, order in book.orders.items():
                    if order.user_id == user_id:
                        if status is None or order.status == status:
                            all_orders.append(order)
        
        return all_orders
    
    def get_open_orders(
        self,
        symbol: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> List[Order]:
        """
        Get all open orders.
        
        Args:
            symbol: Filter by symbol (optional)
            user_id: Filter by user (optional)
            
        Returns:
            List of open orders
        """
        open_orders = []
        
        # Get symbols to check
        if symbol:
            symbols = [symbol]
        else:
            symbols = list(self.matching_engine.order_books.keys())
        
        # Collect open orders
        for sym in symbols:
            book = self.matching_engine.get_order_book(sym)
            if book:
                for order_id, order in book.orders.items():
                    if order.status in [OrderStatus.OPEN, OrderStatus.PARTIALLY_FILLED]:
                        if user_id is None or order.user_id == user_id:
                            open_orders.append(order)
        
        return open_orders
    
    def cancel_all_orders(
        self,
        user_id: str,
        symbol: Optional[str] = None
    ) -> int:
        """
        Cancel all orders for a user.
        
        Args:
            user_id: User ID
            symbol: Filter by symbol (optional)
            
        Returns:
            Number of orders cancelled
        """
        orders = self.get_user_orders(
            user_id,
            symbol=symbol,
            status=None  # Get all statuses, we'll filter in cancel
        )
        
        cancelled_count = 0
        for order in orders:
            if order.status in [OrderStatus.OPEN, OrderStatus.PARTIALLY_FILLED]:
                try:
                    if self.cancel_order(order.symbol, order.order_id, user_id):
                        cancelled_count += 1
                except Exception as e:
                    logger.warning(f"Failed to cancel order {order.order_id}: {e}")
        
        logger.info(f"Cancelled {cancelled_count} orders for user {user_id}")
        return cancelled_count
    
    def get_order_history(self, order_id: str) -> List[Tuple[OrderAction, datetime, str]]:
        """
        Get action history for an order.
        
        Args:
            order_id: Order ID
            
        Returns:
            List of (action, timestamp, description) tuples
        """
        return self._order_history.get(order_id, [])
    
    def _record_action(
        self,
        order_id: str,
        action: OrderAction,
        description: str
    ) -> None:
        """Record an order action in history"""
        if order_id not in self._order_history:
            self._order_history[order_id] = []
        
        self._order_history[order_id].append((
            action,
            datetime.now(UTC),
            description
        ))
    
    def get_statistics(self) -> Dict:
        """Get order manager statistics"""
        total_orders = len(self._order_history)
        
        # Count actions
        action_counts = {}
        for actions in self._order_history.values():
            for action, _, _ in actions:
                action_counts[action.value] = action_counts.get(action.value, 0) + 1
        
        return {
            "total_orders_processed": total_orders,
            "action_counts": action_counts,
            "validator_stats": self.validator.get_validation_stats(),
            "matching_engine_stats": self.matching_engine.get_statistics(),
        }
