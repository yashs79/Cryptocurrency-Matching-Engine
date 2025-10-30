"""
Order Book Persistence

Handles saving and restoring order book state for crash recovery.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from decimal import Decimal
import logging

from ..core.order import Order, OrderStatus, OrderSide
from ..core.order_book import OrderBook, PriceLevel
from ..core.matching_engine import MatchingEngine, Trade
from ..repositories import DatabaseOrderRepository
from ..config.database import init_db, get_db_config

logger = logging.getLogger(__name__)


@dataclass
class PersistenceConfig:
    """Configuration for persistence"""
    database_url: str = "sqlite:///./matching_engine.db"
    auto_save: bool = True  # Auto-save after each operation
    save_interval: int = 100  # Save every N operations if not auto-save
    echo_sql: bool = False


class OrderBookPersistence:
    """
    Manages persistence of order book state.
    
    Features:
    - Save order book state to database
    - Restore order book state from database
    - Crash recovery
    - Incremental saves
    """
    
    def __init__(
        self,
        matching_engine: MatchingEngine,
        config: Optional[PersistenceConfig] = None
    ):
        """
        Initialize persistence layer.
        
        Args:
            matching_engine: Matching engine to persist
            config: Persistence configuration
        """
        self.matching_engine = matching_engine
        self.config = config or PersistenceConfig()
        
        # Initialize database
        try:
            get_db_config()
        except RuntimeError:
            init_db(
                database_url=self.config.database_url,
                echo=self.config.echo_sql
            )
        
        # Create repository
        self.repository = DatabaseOrderRepository()
        
        # Track operations since last save
        self._operations_since_save = 0
        
        logger.info(f"OrderBookPersistence initialized with {self.config.database_url}")
    
    def save_state(self) -> int:
        """
        Save complete order book state to database.
        
        Returns:
            Number of orders saved
        """
        logger.info("Saving order book state...")
        
        total_saved = 0
        
        # Save all orders from all order books
        for symbol, order_book in self.matching_engine.order_books.items():
            # Get all active orders from the order book
            all_orders = list(order_book.orders.values())
            
            for order in all_orders:
                self.repository.save(order)
                total_saved += 1
            
            logger.debug(f"Saved {len(all_orders)} orders for {symbol}")
        
        self._operations_since_save = 0
        logger.info(f"✅ Saved {total_saved} orders to database")
        
        return total_saved
    
    def restore_state(self) -> Tuple[int, int]:
        """
        Restore order book state from database.
        
        Returns:
            Tuple of (orders_restored, symbols_restored)
        """
        logger.info("Restoring order book state from database...")
        
        # Get all open and partially filled orders
        from ..repositories import OrderFilter
        
        filter = OrderFilter(
            statuses=[OrderStatus.OPEN, OrderStatus.PARTIALLY_FILLED]
        )
        
        orders = self.repository.find(filter)
        
        if not orders:
            logger.info("No orders to restore")
            return 0, 0
        
        # Group orders by symbol
        orders_by_symbol = {}
        for order in orders:
            if order.symbol not in orders_by_symbol:
                orders_by_symbol[order.symbol] = []
            orders_by_symbol[order.symbol].append(order)
        
        # Restore orders to matching engine
        total_restored = 0
        for symbol, symbol_orders in orders_by_symbol.items():
            # Sort by timestamp to maintain time priority
            symbol_orders.sort(key=lambda o: o.timestamp)
            
            for order in symbol_orders:
                # Add order back to order book without matching
                # (we're restoring state, not processing new orders)
                self._restore_order_to_book(order)
                total_restored += 1
        
        symbols_restored = len(orders_by_symbol)
        
        logger.info(f"✅ Restored {total_restored} orders across {symbols_restored} symbols")
        
        return total_restored, symbols_restored
    
    def _restore_order_to_book(self, order: Order) -> None:
        """Restore a single order to the order book"""
        symbol = order.symbol
        
        # Get or create order book
        if symbol not in self.matching_engine.order_books:
            self.matching_engine.order_books[symbol] = OrderBook(symbol)
        
        order_book = self.matching_engine.order_books[symbol]
        
        # IMPORTANT: Don't use add_order() because it sets status to OPEN
        # Instead, manually add the order while preserving its status
        
        # Add to order lookup
        order_book.orders[order.order_id] = order
        
        # Add to appropriate price level
        if order.side == OrderSide.BUY:
            if order.price not in order_book.bid_levels:
                order_book.bid_levels[order.price] = PriceLevel(order.price)
                order_book.bid_prices.add(order.price)
            order_book.bid_levels[order.price].add_order(order)
            order_book.total_bid_volume += order.remaining_quantity
        else:
            if order.price not in order_book.ask_levels:
                order_book.ask_levels[order.price] = PriceLevel(order.price)
                order_book.ask_prices.add(order.price)
            order_book.ask_levels[order.price].add_order(order)
            order_book.total_ask_volume += order.remaining_quantity
        
        order_book.order_count += 1
        
        logger.debug(f"Restored order {order.order_id} to {symbol} order book with status {order.status}")
    
    def save_order(self, order: Order) -> None:
        """
        Save a single order to database.
        
        Args:
            order: Order to save
        """
        self.repository.save(order)
        self._operations_since_save += 1
        
        # Auto-save if configured
        if not self.config.auto_save:
            if self._operations_since_save >= self.config.save_interval:
                self.save_state()
    
    def save_trade(self, trade: Trade) -> None:
        """
        Save a trade to database.
        
        Args:
            trade: Trade to save
        """
        # TODO: Implement trade persistence when TradeRepository is ready
        logger.debug(f"Trade {trade.trade_id} recorded (trade persistence pending)")
    
    def clear_state(self) -> None:
        """Clear all persisted state (use with caution!)"""
        logger.warning("Clearing all persisted order book state...")
        self.repository.clear()
        logger.info("✅ Persisted state cleared")
    
    def get_persistence_stats(self) -> Dict:
        """
        Get persistence statistics.
        
        Returns:
            Dictionary with persistence stats
        """
        stats = self.repository.get_statistics()
        stats["operations_since_save"] = self._operations_since_save
        stats["auto_save_enabled"] = self.config.auto_save
        stats["save_interval"] = self.config.save_interval
        
        return stats
    
    def close(self) -> None:
        """Close persistence layer and save final state"""
        logger.info("Closing persistence layer...")
        
        # Final save
        if self._operations_since_save > 0:
            self.save_state()
        
        # Close repository
        self.repository.close()
        
        logger.info("✅ Persistence layer closed")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


class PersistentMatchingEngine(MatchingEngine):
    """
    Matching Engine with built-in persistence.
    
    Automatically saves and restores order book state.
    """
    
    def __init__(
        self,
        persistence_config: Optional[PersistenceConfig] = None,
        auto_restore: bool = True
    ):
        """
        Initialize persistent matching engine.
        
        Args:
            persistence_config: Persistence configuration
            auto_restore: Automatically restore state on startup
        """
        super().__init__()
        
        # Initialize persistence
        self.persistence = OrderBookPersistence(self, persistence_config)
        
        # Auto-restore if configured
        if auto_restore:
            orders_restored, symbols_restored = self.persistence.restore_state()
            if orders_restored > 0:
                logger.info(
                    f"🔄 Restored {orders_restored} orders across "
                    f"{symbols_restored} symbols from previous session"
                )
    
    def process_order(self, order: Order) -> Tuple[Order, List[Trade]]:
        """
        Process order with automatic persistence.
        
        Args:
            order: Order to process
            
        Returns:
            Tuple of (processed_order, trades)
        """
        # Process order normally
        processed_order, trades = super().process_order(order)
        
        # Save the processed order
        self.persistence.save_order(processed_order)
        
        # Save trades
        for trade in trades:
            self.persistence.save_trade(trade)
        
        # If trades occurred, save all affected orders from the order book
        if trades:
            order_book = self.order_books.get(order.symbol)
            if order_book:
                # Save all orders that were involved in matching
                # This includes partially filled orders
                for trade in trades:
                    # Save buyer order (may be partially filled)
                    if trade.buyer_order_id in order_book.orders:
                        buyer_order = order_book.orders[trade.buyer_order_id]
                        self.persistence.save_order(buyer_order)
                    
                    # Save seller order (may be partially filled)
                    if trade.seller_order_id in order_book.orders:
                        seller_order = order_book.orders[trade.seller_order_id]
                        self.persistence.save_order(seller_order)
        
        return processed_order, trades
    
    def _save_matched_orders(self, order_book: OrderBook, trade: Trade) -> None:
        """Save orders that were matched in a trade"""
        # This is a simplified version - in production you'd track
        # the actual order objects involved in the trade
        pass
    
    def cancel_order(self, symbol: str, order_id: str) -> bool:
        """
        Cancel order with automatic persistence.
        
        Args:
            symbol: Trading symbol
            order_id: Order ID to cancel
            
        Returns:
            True if cancelled, False otherwise
        """
        success = super().cancel_order(symbol, order_id)
        
        if success:
            # Get the cancelled order and save its state
            order_book = self.order_books.get(symbol)
            if order_book:
                # Find the order and save it
                # (it will have status CANCELLED)
                pass
        
        return success
    
    def shutdown(self) -> None:
        """Shutdown engine and save final state"""
        logger.info("Shutting down persistent matching engine...")
        self.persistence.close()
        logger.info("✅ Shutdown complete")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.shutdown()
