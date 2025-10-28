"""
Core matching engine logic.

This module implements the matching engine that processes orders
and executes trades using price-time priority algorithm.
"""

from typing import List, Dict, Optional, Tuple
from decimal import Decimal
from datetime import datetime, UTC
import logging
import uuid

from .order import Order, OrderSide, OrderType, OrderStatus
from .order_book import OrderBook

logger = logging.getLogger(__name__)


class Trade:
    """
    Represents a completed trade between two orders.
    
    Attributes:
        trade_id: Unique trade identifier
        symbol: Trading pair symbol
        buyer_order_id: ID of the buy order
        seller_order_id: ID of the sell order
        price: Execution price
        quantity: Executed quantity
        timestamp: Trade execution timestamp
    """
    
    def __init__(
        self,
        symbol: str,
        buyer_order_id: str,
        seller_order_id: str,
        price: Decimal,
        quantity: Decimal
    ):
        self.trade_id = str(uuid.uuid4())
        self.symbol = symbol
        self.buyer_order_id = buyer_order_id
        self.seller_order_id = seller_order_id
        self.price = price
        self.quantity = quantity
        self.timestamp = datetime.now(UTC)
    
    def to_dict(self) -> Dict:
        """Convert trade to dictionary"""
        return {
            'trade_id': self.trade_id,
            'symbol': self.symbol,
            'buyer_order_id': self.buyer_order_id,
            'seller_order_id': self.seller_order_id,
            'price': str(self.price),
            'quantity': str(self.quantity),
            'timestamp': self.timestamp.isoformat()
        }
    
    def __repr__(self) -> str:
        return (
            f"Trade(id={self.trade_id[:8]}, {self.symbol}, "
            f"{self.quantity} @ {self.price})"
        )


class MatchingEngine:
    """
    Core matching engine that processes orders and generates trades.
    
    Uses price-time priority algorithm:
    1. Best price gets priority
    2. At same price, earlier orders get priority
    
    Attributes:
        order_books: Dictionary of symbol -> OrderBook
        trades: List of executed trades
    """
    
    def __init__(self):
        self.order_books: Dict[str, OrderBook] = {}
        self.trades: List[Trade] = []
        self.total_trades = 0
        self.total_volume = Decimal("0")
    
    def get_or_create_order_book(self, symbol: str) -> OrderBook:
        """Get existing order book or create new one"""
        if symbol not in self.order_books:
            self.order_books[symbol] = OrderBook(symbol)
            logger.info(f"Created new order book for {symbol}")
        return self.order_books[symbol]
    
    def process_order(self, order: Order) -> Tuple[Order, List[Trade]]:
        """
        Process an incoming order.
        
        Args:
            order: Order to process
            
        Returns:
            Tuple of (processed order, list of trades generated)
        """
        logger.info(f"Processing order: {order}")
        
        order_book = self.get_or_create_order_book(order.symbol)
        trades = []
        
        # Handle market orders
        if order.order_type == OrderType.MARKET:
            trades = self._match_market_order(order, order_book)
        
        # Handle limit orders
        elif order.order_type == OrderType.LIMIT:
            trades = self._match_limit_order(order, order_book)
        
        # Handle IOC (Immediate or Cancel)
        elif order.order_type == OrderType.IOC:
            trades = self._match_limit_order(order, order_book)
            # Cancel any remaining quantity
            if not order.is_filled:
                order.cancel()
        
        # Handle FOK (Fill or Kill)
        elif order.order_type == OrderType.FOK:
            # Check if order can be completely filled
            if self._can_fill_completely(order, order_book):
                trades = self._match_limit_order(order, order_book)
            else:
                order.status = OrderStatus.REJECTED
                logger.info(f"FOK order {order.order_id} rejected - cannot fill completely")
        
        # Store trades
        self.trades.extend(trades)
        self.total_trades += len(trades)
        
        for trade in trades:
            self.total_volume += trade.quantity
        
        logger.info(f"Order {order.order_id} processed: {len(trades)} trades generated")
        return order, trades
    
    def _match_market_order(self, order: Order, order_book: OrderBook) -> List[Trade]:
        """
        Match a market order against the order book.
        Market orders execute at the best available prices.
        """
        trades = []
        
        # Get opposite side of order book
        if order.side == OrderSide.BUY:
            # Buy market order matches against asks (sell orders)
            price_levels = order_book.ask_prices
            levels_dict = order_book.ask_levels
        else:
            # Sell market order matches against bids (buy orders)
            price_levels = order_book.bid_prices
            levels_dict = order_book.bid_levels
        
        # Match against best prices until order is filled
        while not order.is_filled and price_levels:
            best_price = price_levels[0]
            level = levels_dict[best_price]
            
            # Match against orders at this price level
            for resting_order in level.orders[:]:  # Copy list to avoid modification issues
                if order.is_filled:
                    break
                
                # Execute trade
                trade = self._execute_trade(order, resting_order, best_price)
                if trade:
                    trades.append(trade)
                
                # Remove filled resting order
                if resting_order.is_filled:
                    order_book.remove_order(resting_order.order_id)
        
        # Market orders that can't be filled at all are rejected
        if order.filled_quantity == Decimal("0"):
            order.status = OrderStatus.REJECTED
            logger.warning(f"Market order {order.order_id} rejected - insufficient liquidity")
        
        return trades
    
    def _match_limit_order(self, order: Order, order_book: OrderBook) -> List[Trade]:
        """
        Match a limit order against the order book.
        Limit orders only execute at their limit price or better.
        """
        trades = []
        
        # Get opposite side of order book
        if order.side == OrderSide.BUY:
            # Buy limit order matches against asks at or below limit price
            price_levels = order_book.ask_prices
            levels_dict = order_book.ask_levels
        else:
            # Sell limit order matches against bids at or above limit price
            price_levels = order_book.bid_prices
            levels_dict = order_book.bid_levels
        
        # Match against compatible prices
        while not order.is_filled and price_levels:
            best_price = price_levels[0]
            
            # Check if price is acceptable
            if order.side == OrderSide.BUY and best_price > order.price:
                break  # No more acceptable prices
            if order.side == OrderSide.SELL and best_price < order.price:
                break  # No more acceptable prices
            
            level = levels_dict[best_price]
            
            # Match against orders at this price level
            for resting_order in level.orders[:]:
                if order.is_filled:
                    break
                
                # Execute trade at the resting order's price (price-time priority)
                trade = self._execute_trade(order, resting_order, resting_order.price)
                if trade:
                    trades.append(trade)
                
                # Remove filled resting order
                if resting_order.is_filled:
                    order_book.remove_order(resting_order.order_id)
        
        # Add remaining quantity to order book if not fully filled
        if not order.is_filled and order.status != OrderStatus.CANCELLED:
            order_book.add_order(order)
        
        return trades
    
    def _execute_trade(
        self,
        incoming_order: Order,
        resting_order: Order,
        price: Decimal
    ) -> Optional[Trade]:
        """
        Execute a trade between two orders.
        
        Args:
            incoming_order: New order being processed
            resting_order: Order already in the order book
            price: Execution price
            
        Returns:
            Trade object if successful, None otherwise
        """
        # Calculate trade quantity (minimum of remaining quantities)
        trade_quantity = min(
            incoming_order.remaining_quantity,
            resting_order.remaining_quantity
        )
        
        if trade_quantity <= 0:
            return None
        
        # Fill both orders
        incoming_order.fill(trade_quantity)
        resting_order.fill(trade_quantity)
        
        # Create trade
        if incoming_order.side == OrderSide.BUY:
            buyer_order_id = incoming_order.order_id
            seller_order_id = resting_order.order_id
        else:
            buyer_order_id = resting_order.order_id
            seller_order_id = incoming_order.order_id
        
        trade = Trade(
            symbol=incoming_order.symbol,
            buyer_order_id=buyer_order_id,
            seller_order_id=seller_order_id,
            price=price,
            quantity=trade_quantity
        )
        
        logger.debug(f"Executed trade: {trade}")
        return trade
    
    def _can_fill_completely(self, order: Order, order_book: OrderBook) -> bool:
        """
        Check if a FOK order can be completely filled.
        
        Args:
            order: FOK order to check
            order_book: Order book to check against
            
        Returns:
            True if order can be completely filled
        """
        remaining = order.quantity
        
        # Get opposite side
        if order.side == OrderSide.BUY:
            price_levels = order_book.ask_prices
            levels_dict = order_book.ask_levels
        else:
            price_levels = order_book.bid_prices
            levels_dict = order_book.bid_levels
        
        # Check if enough liquidity exists
        for price in price_levels:
            # Check if price is acceptable
            if order.side == OrderSide.BUY and price > order.price:
                break
            if order.side == OrderSide.SELL and price < order.price:
                break
            
            level = levels_dict[price]
            remaining -= level.total_quantity
            
            if remaining <= 0:
                return True
        
        return False
    
    def cancel_order(self, symbol: str, order_id: str) -> Optional[Order]:
        """
        Cancel an order in the order book.
        
        Args:
            symbol: Trading pair symbol
            order_id: ID of order to cancel
            
        Returns:
            Cancelled order, or None if not found
        """
        order_book = self.order_books.get(symbol)
        if not order_book:
            return None
        
        order = order_book.remove_order(order_id)
        if order:
            order.cancel()
            logger.info(f"Cancelled order {order_id}")
        
        return order
    
    def get_order_book(self, symbol: str) -> Optional[OrderBook]:
        """Get order book for a symbol"""
        return self.order_books.get(symbol)
    
    def get_order(self, symbol: str, order_id: str) -> Optional[Order]:
        """Get an order by symbol and ID"""
        order_book = self.order_books.get(symbol)
        if order_book:
            return order_book.get_order(order_id)
        return None
    
    def get_recent_trades(self, symbol: str, limit: int = 100) -> List[Trade]:
        """Get recent trades for a symbol"""
        symbol_trades = [t for t in self.trades if t.symbol == symbol]
        return symbol_trades[-limit:]
    
    def get_statistics(self) -> Dict:
        """Get matching engine statistics"""
        return {
            'total_symbols': len(self.order_books),
            'total_trades': self.total_trades,
            'total_volume': str(self.total_volume),
            'order_books': {
                symbol: {
                    'orders': book.order_count,
                    'bid_levels': len(book.bid_prices),
                    'ask_levels': len(book.ask_prices),
                    'spread': str(book.spread) if book.spread else None
                }
                for symbol, book in self.order_books.items()
            }
        }
    
    def __repr__(self) -> str:
        return (
            f"MatchingEngine(symbols={len(self.order_books)}, "
            f"trades={self.total_trades}, volume={self.total_volume})"
        )
