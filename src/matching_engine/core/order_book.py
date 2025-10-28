"""
Order Book data structure.

This module implements an efficient order book using sorted containers
for O(log n) insertion and O(1) best price lookup.
"""

from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from sortedcontainers import SortedList
from collections import defaultdict
import logging

from .order import Order, OrderSide, OrderStatus

logger = logging.getLogger(__name__)


class PriceLevel:
    """
    Represents a single price level in the order book.
    Contains all orders at a specific price, ordered by time priority.
    """
    
    def __init__(self, price: Decimal):
        self.price = price
        self.orders: List[Order] = []
        self.total_quantity = Decimal("0")
    
    def add_order(self, order: Order) -> None:
        """Add an order to this price level"""
        self.orders.append(order)
        self.total_quantity += order.remaining_quantity
    
    def remove_order(self, order: Order) -> bool:
        """Remove an order from this price level"""
        try:
            self.orders.remove(order)
            self.total_quantity -= order.remaining_quantity
            return True
        except ValueError:
            return False
    
    def update_quantity(self, old_qty: Decimal, new_qty: Decimal) -> None:
        """Update total quantity when an order is filled"""
        self.total_quantity = self.total_quantity - old_qty + new_qty
    
    @property
    def is_empty(self) -> bool:
        """Check if this price level has no orders"""
        return len(self.orders) == 0
    
    def __repr__(self) -> str:
        return f"PriceLevel(price={self.price}, orders={len(self.orders)}, qty={self.total_quantity})"


class OrderBook:
    """
    Order book for a single trading pair.
    
    Maintains separate sorted lists for buy and sell orders.
    Provides efficient order matching using price-time priority.
    
    Attributes:
        symbol: Trading pair symbol (e.g., "BTC-USD")
        bids: Buy orders (sorted by price descending, then time)
        asks: Sell orders (sorted by price ascending, then time)
    """
    
    def __init__(self, symbol: str):
        self.symbol = symbol
        
        # Price levels: price -> PriceLevel
        self.bid_levels: Dict[Decimal, PriceLevel] = {}
        self.ask_levels: Dict[Decimal, PriceLevel] = {}
        
        # Sorted prices for efficient best price lookup
        # Bids: highest price first
        self.bid_prices = SortedList(key=lambda x: -x)
        # Asks: lowest price first
        self.ask_prices = SortedList()
        
        # Order lookup: order_id -> Order
        self.orders: Dict[str, Order] = {}
        
        # Statistics
        self.total_bid_volume = Decimal("0")
        self.total_ask_volume = Decimal("0")
        self.order_count = 0
    
    def add_order(self, order: Order) -> None:
        """
        Add an order to the order book.
        
        Args:
            order: Order to add
            
        Raises:
            ValueError: If order is invalid or already exists
        """
        if order.order_id in self.orders:
            raise ValueError(f"Order {order.order_id} already exists in order book")
        
        if order.symbol != self.symbol:
            raise ValueError(f"Order symbol {order.symbol} does not match order book {self.symbol}")
        
        if order.price is None:
            raise ValueError("Cannot add market order to order book")
        
        # Add to order lookup
        self.orders[order.order_id] = order
        order.status = OrderStatus.OPEN
        
        # Add to appropriate side
        if order.side == OrderSide.BUY:
            self._add_bid(order)
        else:
            self._add_ask(order)
        
        self.order_count += 1
        logger.debug(f"Added order {order.order_id} to {self.symbol} order book")
    
    def _add_bid(self, order: Order) -> None:
        """Add a buy order to the bid side"""
        price = order.price
        
        if price not in self.bid_levels:
            self.bid_levels[price] = PriceLevel(price)
            self.bid_prices.add(price)
        
        self.bid_levels[price].add_order(order)
        self.total_bid_volume += order.remaining_quantity
    
    def _add_ask(self, order: Order) -> None:
        """Add a sell order to the ask side"""
        price = order.price
        
        if price not in self.ask_levels:
            self.ask_levels[price] = PriceLevel(price)
            self.ask_prices.add(price)
        
        self.ask_levels[price].add_order(order)
        self.total_ask_volume += order.remaining_quantity
    
    def remove_order(self, order_id: str) -> Optional[Order]:
        """
        Remove an order from the order book.
        
        Args:
            order_id: ID of order to remove
            
        Returns:
            Removed order, or None if not found
        """
        order = self.orders.get(order_id)
        if not order:
            return None
        
        # Remove from price level
        if order.side == OrderSide.BUY:
            self._remove_bid(order)
        else:
            self._remove_ask(order)
        
        # Remove from order lookup
        del self.orders[order_id]
        self.order_count -= 1
        
        logger.debug(f"Removed order {order_id} from {self.symbol} order book")
        return order
    
    def _remove_bid(self, order: Order) -> None:
        """Remove a buy order from the bid side"""
        price = order.price
        level = self.bid_levels.get(price)
        
        if level:
            level.remove_order(order)
            self.total_bid_volume -= order.remaining_quantity
            
            # Remove empty price level
            if level.is_empty:
                del self.bid_levels[price]
                self.bid_prices.remove(price)
    
    def _remove_ask(self, order: Order) -> None:
        """Remove a sell order from the ask side"""
        price = order.price
        level = self.ask_levels.get(price)
        
        if level:
            level.remove_order(order)
            self.total_ask_volume -= order.remaining_quantity
            
            # Remove empty price level
            if level.is_empty:
                del self.ask_levels[price]
                self.ask_prices.remove(price)
    
    def get_order(self, order_id: str) -> Optional[Order]:
        """Get an order by ID"""
        return self.orders.get(order_id)
    
    @property
    def best_bid(self) -> Optional[Decimal]:
        """Get the best (highest) bid price"""
        return self.bid_prices[0] if self.bid_prices else None
    
    @property
    def best_ask(self) -> Optional[Decimal]:
        """Get the best (lowest) ask price"""
        return self.ask_prices[0] if self.ask_prices else None
    
    @property
    def spread(self) -> Optional[Decimal]:
        """Get the bid-ask spread"""
        if self.best_bid and self.best_ask:
            return self.best_ask - self.best_bid
        return None
    
    @property
    def mid_price(self) -> Optional[Decimal]:
        """Get the mid price (average of best bid and ask)"""
        if self.best_bid and self.best_ask:
            return (self.best_bid + self.best_ask) / 2
        return None
    
    def get_depth(self, levels: int = 10) -> Dict:
        """
        Get order book depth (top N price levels on each side).
        
        Args:
            levels: Number of price levels to return
            
        Returns:
            Dictionary with bids and asks
        """
        bids = []
        for i, price in enumerate(self.bid_prices[:levels]):
            level = self.bid_levels[price]
            bids.append({
                'price': str(price),
                'quantity': str(level.total_quantity),
                'orders': len(level.orders)
            })
        
        asks = []
        for i, price in enumerate(self.ask_prices[:levels]):
            level = self.ask_levels[price]
            asks.append({
                'price': str(price),
                'quantity': str(level.total_quantity),
                'orders': len(level.orders)
            })
        
        return {
            'symbol': self.symbol,
            'bids': bids,
            'asks': asks,
            'spread': str(self.spread) if self.spread else None,
            'mid_price': str(self.mid_price) if self.mid_price else None
        }
    
    def get_orders_at_price(self, price: Decimal, side: OrderSide) -> List[Order]:
        """Get all orders at a specific price level"""
        if side == OrderSide.BUY:
            level = self.bid_levels.get(price)
        else:
            level = self.ask_levels.get(price)
        
        return level.orders.copy() if level else []
    
    def clear(self) -> None:
        """Clear all orders from the order book"""
        self.bid_levels.clear()
        self.ask_levels.clear()
        self.bid_prices.clear()
        self.ask_prices.clear()
        self.orders.clear()
        self.total_bid_volume = Decimal("0")
        self.total_ask_volume = Decimal("0")
        self.order_count = 0
        logger.info(f"Cleared order book for {self.symbol}")
    
    def __repr__(self) -> str:
        return (
            f"OrderBook(symbol={self.symbol}, "
            f"bids={len(self.bid_prices)} levels, "
            f"asks={len(self.ask_prices)} levels, "
            f"orders={self.order_count})"
        )
    
    def __str__(self) -> str:
        """Pretty print order book"""
        lines = [f"\n{'='*60}"]
        lines.append(f"Order Book: {self.symbol}")
        lines.append(f"{'='*60}")
        lines.append(f"{'ASKS':<30}{'BIDS':>30}")
        lines.append(f"{'-'*60}")
        
        max_levels = max(len(self.ask_prices), len(self.bid_prices))
        
        for i in range(min(10, max_levels)):
            ask_str = ""
            bid_str = ""
            
            if i < len(self.ask_prices):
                price = self.ask_prices[-(i+1)]  # Reverse order for asks
                level = self.ask_levels[price]
                ask_str = f"{level.total_quantity:>10} @ {price:<15}"
            
            if i < len(self.bid_prices):
                price = self.bid_prices[i]
                level = self.bid_levels[price]
                bid_str = f"{price:>15} @ {level.total_quantity:<10}"
            
            lines.append(f"{ask_str:<30}{bid_str:>30}")
        
        lines.append(f"{'='*60}")
        lines.append(f"Spread: {self.spread}, Mid: {self.mid_price}")
        lines.append(f"Total Orders: {self.order_count}")
        lines.append(f"{'='*60}\n")
        
        return '\n'.join(lines)
