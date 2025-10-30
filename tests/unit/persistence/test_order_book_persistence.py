"""
Tests for Order Book Persistence

Critical tests for crash recovery functionality.
"""

import pytest
from decimal import Decimal
from datetime import datetime, UTC

from src.matching_engine.core.matching_engine import MatchingEngine
from src.matching_engine.core.order import Order, OrderSide, OrderType, OrderStatus
from src.matching_engine.persistence import OrderBookPersistence, PersistenceConfig
from src.matching_engine.config.database import init_db


class TestOrderBookPersistence:
    """Test OrderBookPersistence"""
    
    @pytest.fixture(scope="function")
    def db_config(self):
        """Initialize in-memory database for each test"""
        init_db(database_url="sqlite:///:memory:", echo=False)
    
    @pytest.fixture
    def engine(self):
        """Create matching engine"""
        return MatchingEngine()
    
    @pytest.fixture
    def persistence(self, engine, db_config):
        """Create persistence layer"""
        config = PersistenceConfig(
            database_url="sqlite:///:memory:",
            auto_save=False
        )
        return OrderBookPersistence(engine, config)
    
    @pytest.fixture
    def sample_orders(self):
        """Create sample orders"""
        return [
            Order(
                user_id="alice",
                symbol="BTC-USD",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                price=Decimal("50000"),
                quantity=Decimal("1.0")
            ),
            Order(
                user_id="bob",
                symbol="BTC-USD",
                side=OrderSide.SELL,
                order_type=OrderType.LIMIT,
                price=Decimal("51000"),
                quantity=Decimal("2.0")
            ),
            Order(
                user_id="charlie",
                symbol="ETH-USD",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                price=Decimal("3000"),
                quantity=Decimal("5.0")
            ),
        ]
    
    def test_save_empty_state(self, persistence):
        """Test saving empty order book state"""
        saved_count = persistence.save_state()
        assert saved_count == 0
    
    def test_save_single_order(self, engine, persistence, sample_orders):
        """Test saving a single order"""
        # Process order
        order = sample_orders[0]
        engine.process_order(order)
        
        # Save state
        saved_count = persistence.save_state()
        assert saved_count == 1
        
        # Verify in repository
        retrieved = persistence.repository.get(order.order_id)
        assert retrieved is not None
        assert retrieved.order_id == order.order_id
    
    def test_save_multiple_orders(self, engine, persistence, sample_orders):
        """Test saving multiple orders"""
        # Process all orders
        for order in sample_orders:
            engine.process_order(order)
        
        # Save state
        saved_count = persistence.save_state()
        assert saved_count == 3
        
        # Verify all orders saved
        for order in sample_orders:
            retrieved = persistence.repository.get(order.order_id)
            assert retrieved is not None
    
    def test_save_multiple_symbols(self, engine, persistence, sample_orders):
        """Test saving orders across multiple symbols"""
        # Process orders
        for order in sample_orders:
            engine.process_order(order)
        
        # Save state
        saved_count = persistence.save_state()
        assert saved_count == 3
        
        # Verify symbols
        stats = persistence.repository.get_statistics()
        assert stats['symbols'] == 2  # BTC-USD and ETH-USD
    
    def test_restore_empty_state(self, persistence):
        """Test restoring from empty database"""
        orders_restored, symbols_restored = persistence.restore_state()
        assert orders_restored == 0
        assert symbols_restored == 0
    
    def test_restore_single_order(self, engine, persistence, sample_orders):
        """Test restoring a single order"""
        # Save order
        order = sample_orders[0]
        engine.process_order(order)
        persistence.save_state()
        
        # Create new engine and persistence
        new_engine = MatchingEngine()
        new_persistence = OrderBookPersistence(new_engine, persistence.config)
        
        # Restore state
        orders_restored, symbols_restored = new_persistence.restore_state()
        assert orders_restored == 1
        assert symbols_restored == 1
        
        # Verify order in order book
        assert "BTC-USD" in new_engine.order_books
        order_book = new_engine.order_books["BTC-USD"]
        assert order.order_id in order_book.orders
    
    def test_restore_multiple_orders(self, engine, persistence, sample_orders):
        """Test restoring multiple orders"""
        # Save orders
        for order in sample_orders:
            engine.process_order(order)
        persistence.save_state()
        
        # Create new engine and restore
        new_engine = MatchingEngine()
        new_persistence = OrderBookPersistence(new_engine, persistence.config)
        
        orders_restored, symbols_restored = new_persistence.restore_state()
        assert orders_restored == 3
        assert symbols_restored == 2
        
        # Verify all orders restored
        for order in sample_orders:
            order_book = new_engine.order_books[order.symbol]
            assert order.order_id in order_book.orders
    
    def test_restore_preserves_price_levels(self, engine, persistence):
        """Test that restore preserves price levels correctly"""
        # Create orders at different price levels
        orders = [
            Order(
                user_id="user1",
                symbol="BTC-USD",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                price=Decimal("50000"),
                quantity=Decimal("1.0")
            ),
            Order(
                user_id="user2",
                symbol="BTC-USD",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                price=Decimal("49000"),
                quantity=Decimal("2.0")
            ),
            Order(
                user_id="user3",
                symbol="BTC-USD",
                side=OrderSide.SELL,
                order_type=OrderType.LIMIT,
                price=Decimal("51000"),
                quantity=Decimal("1.5")
            ),
        ]
        
        for order in orders:
            engine.process_order(order)
        persistence.save_state()
        
        # Restore
        new_engine = MatchingEngine()
        new_persistence = OrderBookPersistence(new_engine, persistence.config)
        new_persistence.restore_state()
        
        # Verify price levels
        order_book = new_engine.order_books["BTC-USD"]
        assert Decimal("50000") in order_book.bid_levels
        assert Decimal("49000") in order_book.bid_levels
        assert Decimal("51000") in order_book.ask_levels
    
    def test_restore_preserves_time_priority(self, engine, persistence):
        """Test that restore preserves time priority"""
        # Create orders at same price level
        order1 = Order(
            user_id="user1",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1.0")
        )
        order2 = Order(
            user_id="user2",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("2.0")
        )
        
        engine.process_order(order1)
        engine.process_order(order2)
        persistence.save_state()
        
        # Restore
        new_engine = MatchingEngine()
        new_persistence = OrderBookPersistence(new_engine, persistence.config)
        new_persistence.restore_state()
        
        # Verify order in price level
        order_book = new_engine.order_books["BTC-USD"]
        level = order_book.bid_levels[Decimal("50000")]
        assert len(level.orders) == 2
        # First order should be first in queue
        assert level.orders[0].user_id == "user1"
        assert level.orders[1].user_id == "user2"
    
    def test_only_restores_open_orders(self, engine, persistence, sample_orders):
        """Test that only OPEN and PARTIALLY_FILLED orders are restored"""
        # Process orders
        for order in sample_orders:
            engine.process_order(order)
        
        # Mark one as filled
        filled_order = sample_orders[0]
        filled_order.status = OrderStatus.FILLED
        filled_order.filled_quantity = filled_order.quantity
        
        # Mark one as cancelled
        cancelled_order = sample_orders[1]
        cancelled_order.status = OrderStatus.CANCELLED
        
        # Save all
        persistence.save_order(filled_order)
        persistence.save_order(cancelled_order)
        persistence.save_state()
        
        # Restore
        new_engine = MatchingEngine()
        new_persistence = OrderBookPersistence(new_engine, persistence.config)
        orders_restored, _ = new_persistence.restore_state()
        
        # Only the open order should be restored
        assert orders_restored == 1
    
    def test_save_order_incremental(self, engine, persistence, sample_orders):
        """Test incremental order saving"""
        order = sample_orders[0]
        engine.process_order(order)
        
        # Save individual order
        persistence.save_order(order)
        
        # Verify saved
        retrieved = persistence.repository.get(order.order_id)
        assert retrieved is not None
    
    def test_auto_save_disabled(self, engine, db_config):
        """Test that auto-save can be disabled"""
        config = PersistenceConfig(
            database_url="sqlite:///:memory:",
            auto_save=False,
            save_interval=100
        )
        persistence = OrderBookPersistence(engine, config)
        
        # Process order
        order = Order(
            user_id="user1",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1.0")
        )
        engine.process_order(order)
        
        # Save order (should not trigger auto-save)
        persistence.save_order(order)
        
        # Operations counter should increment
        assert persistence._operations_since_save == 1
    
    def test_clear_state(self, engine, persistence, sample_orders):
        """Test clearing persisted state"""
        # Save orders
        for order in sample_orders:
            engine.process_order(order)
        persistence.save_state()
        
        # Verify saved
        assert persistence.repository.count() == 3
        
        # Clear
        persistence.clear_state()
        
        # Verify cleared
        assert persistence.repository.count() == 0
    
    def test_get_persistence_stats(self, engine, persistence, sample_orders):
        """Test getting persistence statistics"""
        # Save orders
        for order in sample_orders:
            engine.process_order(order)
        persistence.save_state()
        
        # Get stats
        stats = persistence.get_persistence_stats()
        
        assert stats['total_orders'] == 3
        assert stats['symbols'] == 2
        assert stats['users'] == 3
        assert 'auto_save_enabled' in stats
        assert 'save_interval' in stats
    
    def test_crash_recovery_scenario(self, engine, persistence, sample_orders):
        """Test complete crash recovery scenario"""
        # Phase 1: Normal operation
        for order in sample_orders:
            engine.process_order(order)
        persistence.save_state()
        
        # Simulate crash (close persistence)
        persistence.close()
        
        # Phase 2: Recovery
        new_engine = MatchingEngine()
        new_persistence = OrderBookPersistence(new_engine, persistence.config)
        orders_restored, symbols_restored = new_persistence.restore_state()
        
        assert orders_restored == 3
        assert symbols_restored == 2
        
        # Phase 3: Continue trading
        new_order = Order(
            user_id="dave",
            symbol="BTC-USD",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("0.5")
        )
        
        processed, trades = new_engine.process_order(new_order)
        
        # Should match with alice's buy order
        assert len(trades) == 1
        assert trades[0].quantity == Decimal("0.5")
    
    def test_partial_fill_restoration(self, engine, persistence):
        """Test restoring partially filled orders"""
        # Note: This test verifies that PARTIALLY_FILLED orders are restored
        # In practice, the matching engine updates order status, and we save that state
        
        # Create two orders that will partially match
        buy_order = Order(
            user_id="buyer",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("2.0")
        )
        
        sell_order = Order(
            user_id="seller",
            symbol="BTC-USD",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1.0")
        )
        
        # Process orders - buy order will be partially filled
        engine.process_order(buy_order)
        processed_sell, trades = engine.process_order(sell_order)
        
        # Verify partial fill occurred
        assert len(trades) == 1
        
        # The buy order in the order book should be partially filled
        order_book = engine.order_books["BTC-USD"]
        buy_order_in_book = order_book.orders[buy_order.order_id]
        
        # Save the current state (including the partially filled order)
        persistence.save_state()
        
        # Restore
        new_engine = MatchingEngine()
        new_persistence = OrderBookPersistence(new_engine, persistence.config)
        orders_restored, _ = new_persistence.restore_state()
        
        # Only the partially filled buy order should be restored (sell is filled)
        assert orders_restored == 1
        
        # Verify order was restored
        new_order_book = new_engine.order_books["BTC-USD"]
        assert buy_order.order_id in new_order_book.orders
    
    def test_multiple_save_restore_cycles(self, engine, persistence, sample_orders):
        """Test multiple save/restore cycles"""
        # Cycle 1
        engine.process_order(sample_orders[0])
        persistence.save_state()
        
        # Cycle 2
        new_engine = MatchingEngine()
        new_persistence = OrderBookPersistence(new_engine, persistence.config)
        new_persistence.restore_state()
        new_engine.process_order(sample_orders[1])
        new_persistence.save_state()
        
        # Cycle 3
        final_engine = MatchingEngine()
        final_persistence = OrderBookPersistence(final_engine, persistence.config)
        orders_restored, _ = final_persistence.restore_state()
        
        # Should have both orders
        assert orders_restored == 2
    
    def test_context_manager(self, engine, db_config):
        """Test using persistence as context manager"""
        config = PersistenceConfig(database_url="sqlite:///:memory:")
        
        with OrderBookPersistence(engine, config) as persistence:
            order = Order(
                user_id="user1",
                symbol="BTC-USD",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                price=Decimal("50000"),
                quantity=Decimal("1.0")
            )
            engine.process_order(order)
            persistence.save_state()
        
        # Persistence should be closed after context
