"""
Order Validator Service

Validates orders before they are submitted to the matching engine.
Implements various validation rules including price, quantity, balance checks, etc.
"""

from typing import Dict, List, Optional, Callable
from decimal import Decimal
from datetime import datetime, UTC
from enum import Enum
import logging

from ..core.order import Order, OrderType, OrderSide

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when order validation fails"""
    
    def __init__(self, message: str, field: Optional[str] = None):
        self.message = message
        self.field = field
        super().__init__(self.message)


class ValidationRule(Enum):
    """Validation rule types"""
    PRICE_RANGE = "price_range"
    QUANTITY_RANGE = "quantity_range"
    TICK_SIZE = "tick_size"
    LOT_SIZE = "lot_size"
    SYMBOL_VALID = "symbol_valid"
    MARKET_HOURS = "market_hours"
    RATE_LIMIT = "rate_limit"
    DUPLICATE = "duplicate"
    BALANCE = "balance"


class OrderValidatorConfig:
    """Configuration for order validator"""
    
    def __init__(
        self,
        min_price: Decimal = Decimal("0.01"),
        max_price: Decimal = Decimal("1000000"),
        min_quantity: Decimal = Decimal("0.001"),
        max_quantity: Decimal = Decimal("1000000"),
        tick_size: Decimal = Decimal("0.01"),
        lot_size: Decimal = Decimal("0.001"),
        max_orders_per_second: int = 100,
        check_balance: bool = False,
        check_market_hours: bool = False,
        allowed_symbols: Optional[List[str]] = None,
    ):
        self.min_price = min_price
        self.max_price = max_price
        self.min_quantity = min_quantity
        self.max_quantity = max_quantity
        self.tick_size = tick_size
        self.lot_size = lot_size
        self.max_orders_per_second = max_orders_per_second
        self.check_balance = check_balance
        self.check_market_hours = check_market_hours
        self.allowed_symbols = allowed_symbols or []


class OrderValidator:
    """
    Validates orders before submission to matching engine.
    
    Performs various checks including:
    - Price and quantity ranges
    - Tick size and lot size compliance
    - Symbol validation
    - Rate limiting
    - Market hours (optional)
    - Balance checks (optional)
    """
    
    def __init__(self, config: Optional[OrderValidatorConfig] = None):
        self.config = config or OrderValidatorConfig()
        self._order_history: Dict[str, List[datetime]] = {}  # user_id -> timestamps
        self._recent_order_ids: set = set()  # For duplicate detection
        
        logger.info("OrderValidator initialized with config: %s", self.config)
    
    def validate(self, order: Order) -> bool:
        """
        Validate an order against all configured rules.
        
        Args:
            order: Order to validate
            
        Returns:
            True if order is valid
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            # Run all validation checks
            self._validate_order_type(order)
            self._validate_price(order)
            self._validate_quantity(order)
            self._validate_tick_size(order)
            self._validate_lot_size(order)
            self._validate_symbol(order)
            self._validate_rate_limit(order)
            self._validate_duplicate(order)
            
            if self.config.check_market_hours:
                self._validate_market_hours(order)
            
            logger.debug(f"Order {order.order_id} passed all validations")
            return True
            
        except ValidationError as e:
            logger.warning(f"Order {order.order_id} validation failed: {e.message}")
            raise
    
    def _validate_order_type(self, order: Order) -> None:
        """Validate order type specific requirements"""
        if order.order_type == OrderType.LIMIT and order.price is None:
            raise ValidationError("Limit orders must have a price", "price")
        
        if order.order_type == OrderType.MARKET and order.price is not None:
            raise ValidationError("Market orders cannot have a price", "price")
    
    def _validate_price(self, order: Order) -> None:
        """Validate price is within acceptable range"""
        if order.price is None:
            return  # Market orders don't have price
        
        if order.price < self.config.min_price:
            raise ValidationError(
                f"Price {order.price} below minimum {self.config.min_price}",
                "price"
            )
        
        if order.price > self.config.max_price:
            raise ValidationError(
                f"Price {order.price} above maximum {self.config.max_price}",
                "price"
            )
    
    def _validate_quantity(self, order: Order) -> None:
        """Validate quantity is within acceptable range"""
        if order.quantity < self.config.min_quantity:
            raise ValidationError(
                f"Quantity {order.quantity} below minimum {self.config.min_quantity}",
                "quantity"
            )
        
        if order.quantity > self.config.max_quantity:
            raise ValidationError(
                f"Quantity {order.quantity} above maximum {self.config.max_quantity}",
                "quantity"
            )
    
    def _validate_tick_size(self, order: Order) -> None:
        """Validate price conforms to tick size"""
        if order.price is None:
            return
        
        remainder = order.price % self.config.tick_size
        if remainder != 0:
            raise ValidationError(
                f"Price {order.price} does not conform to tick size {self.config.tick_size}",
                "price"
            )
    
    def _validate_lot_size(self, order: Order) -> None:
        """Validate quantity conforms to lot size"""
        remainder = order.quantity % self.config.lot_size
        if remainder != 0:
            raise ValidationError(
                f"Quantity {order.quantity} does not conform to lot size {self.config.lot_size}",
                "quantity"
            )
    
    def _validate_symbol(self, order: Order) -> None:
        """Validate trading symbol is allowed"""
        if not self.config.allowed_symbols:
            return  # No symbol restrictions
        
        if order.symbol not in self.config.allowed_symbols:
            raise ValidationError(
                f"Symbol {order.symbol} is not allowed. Allowed: {self.config.allowed_symbols}",
                "symbol"
            )
    
    def _validate_rate_limit(self, order: Order) -> None:
        """Validate user hasn't exceeded rate limit"""
        now = datetime.now(UTC)
        user_id = order.user_id
        
        # Initialize user history if needed
        if user_id not in self._order_history:
            self._order_history[user_id] = []
        
        # Remove timestamps older than 1 second
        cutoff = now.timestamp() - 1.0
        self._order_history[user_id] = [
            ts for ts in self._order_history[user_id]
            if ts.timestamp() > cutoff
        ]
        
        # Check rate limit
        if len(self._order_history[user_id]) >= self.config.max_orders_per_second:
            raise ValidationError(
                f"Rate limit exceeded: {self.config.max_orders_per_second} orders/second",
                "rate_limit"
            )
        
        # Add current timestamp
        self._order_history[user_id].append(now)
    
    def _validate_duplicate(self, order: Order) -> None:
        """Check for duplicate order IDs"""
        if order.order_id in self._recent_order_ids:
            raise ValidationError(
                f"Duplicate order ID: {order.order_id}",
                "order_id"
            )
        
        # Add to recent orders (keep last 10000)
        self._recent_order_ids.add(order.order_id)
        if len(self._recent_order_ids) > 10000:
            # Remove oldest (this is approximate, good enough for duplicate detection)
            self._recent_order_ids.pop()
    
    def _validate_market_hours(self, order: Order) -> None:
        """Validate order is placed during market hours"""
        now = datetime.now(UTC)
        hour = now.hour
        
        # Simple market hours: 9 AM - 4 PM UTC (example)
        if hour < 9 or hour >= 16:
            raise ValidationError(
                f"Market is closed. Trading hours: 09:00-16:00 UTC",
                "market_hours"
            )
    
    def validate_balance(
        self,
        order: Order,
        available_balance: Decimal,
        get_balance: Optional[Callable[[str], Decimal]] = None
    ) -> bool:
        """
        Validate user has sufficient balance for the order.
        
        Args:
            order: Order to validate
            available_balance: User's available balance
            get_balance: Optional function to get user balance
            
        Returns:
            True if balance is sufficient
            
        Raises:
            ValidationError: If insufficient balance
        """
        if get_balance:
            available_balance = get_balance(order.user_id)
        
        required_balance = self._calculate_required_balance(order)
        
        if available_balance < required_balance:
            raise ValidationError(
                f"Insufficient balance. Required: {required_balance}, Available: {available_balance}",
                "balance"
            )
        
        return True
    
    def _calculate_required_balance(self, order: Order) -> Decimal:
        """Calculate required balance for an order"""
        if order.side == OrderSide.BUY:
            # For buy orders, need price * quantity
            if order.price:
                return order.price * order.quantity
            else:
                # Market orders: estimate with a buffer
                return Decimal("999999")  # High estimate for market orders
        else:
            # For sell orders, need the quantity of the asset
            return order.quantity
    
    def clear_history(self, user_id: Optional[str] = None) -> None:
        """Clear order history for rate limiting"""
        if user_id:
            self._order_history.pop(user_id, None)
        else:
            self._order_history.clear()
            self._recent_order_ids.clear()
    
    def get_validation_stats(self) -> Dict:
        """Get validation statistics"""
        return {
            "tracked_users": len(self._order_history),
            "recent_orders": len(self._recent_order_ids),
            "config": {
                "min_price": str(self.config.min_price),
                "max_price": str(self.config.max_price),
                "min_quantity": str(self.config.min_quantity),
                "max_quantity": str(self.config.max_quantity),
                "tick_size": str(self.config.tick_size),
                "lot_size": str(self.config.lot_size),
                "max_orders_per_second": self.config.max_orders_per_second,
            }
        }
