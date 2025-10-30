"""
Tests for Persistent Matching Engine

Tests the integrated matching engine with built-in persistence.
"""

import pytest
from decimal import Decimal

from src.matching_engine.persistence.order_book_persistence import (
    PersistentMatchingEngine,
    PersistenceConfig
)
from src.matching_engine.core.order import Order, OrderSide, OrderType, OrderStatus
from src.matching_engine.config.database import init_db


class TestPersistentMatchingEngine:
    """Test PersistentMatchingEngine"""
    
    @pytest.fixture(scope="function")
    def db_config(self):
        """Initialize in-memory database"""
        init_db(database_url="sqlite:///:memory:", echo=False)
    
    @pytest.fixture
    def config(self):
        """Create persistence config"""
        return PersistenceConfig(
            database_url="sqlite:///:memory:",
            auto_save=True
        )
    
    @pytest.fixture
    def sample_order(self):
        """Create sample order"""
        return Order(
            user_id="alice",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1.0")
        )
    
    def test_initialization_without_restore(self, db_config, config):
        """Test initialization without auto-restore"""
        engine = PersistentMatchingEngine(config, auto_restore=False)
        assert engine is not None
        assert engine.persistence is not None
    
    def test_initialization_with_restore_empty(self, db_config, config):
        """Test initialization with auto-restore on empty database"""
        engine = PersistentMatchingEngine(config, auto_restore=True)
        assert len(engine.order_books) == 0
    
    def test_process_order_with_auto_save(self, db_config, config, sample_order):
        """Test that orders are automatically saved"""
        engine = PersistentMatchingEngine(config, auto_restore=False)
        
        # Process order
        processed, trades = engine.process_order(sample_order)
        
        # Verify saved to database
        retrieved = engine.persistence.repository.get(sample_order.order_id)
        assert retrieved is not None
        assert retrieved.order_id == sample_order.order_id
    
    def test_auto_restore_on_startup(self, db_config, config, sample_order):
        """Test automatic state restoration on startup"""
        # Session 1: Create and save order
        engine1 = PersistentMatchingEngine(config, auto_restore=False)
        engine1.process_order(sample_order)
        engine1.shutdown()
        
        # Session 2: Auto-restore
        engine2 = PersistentMatchingEngine(config, auto_restore=True)
        
        # Verify order restored
        assert "BTC-USD" in engine2.order_books
        order_book = engine2.order_books["BTC-USD"]
        assert sample_order.order_id in order_book.orders
    
    def test_matching_with_restored_orders(self, db_config, config):
        """Test that new orders can match with restored orders"""
        # Session 1: Create buy order
        buy_order = Order(
            user_id="alice",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1.0")
        )
        
        engine1 = PersistentMatchingEngine(config, auto_restore=False)
        engine1.process_order(buy_order)
        engine1.shutdown()
        
        # Session 2: Create matching sell order
        sell_order = Order(
            user_id="bob",
            symbol="BTC-USD",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("0.5")
        )
        
        engine2 = PersistentMatchingEngine(config, auto_restore=True)
        processed, trades = engine2.process_order(sell_order)
        
        # Should have matched
        assert len(trades) == 1
        assert trades[0].quantity == Decimal("0.5")
        assert trades[0].price == Decimal("50000")
    
    def test_shutdown_saves_state(self, db_config, config, sample_order):
        """Test that shutdown saves final state"""
        engine = PersistentMatchingEngine(config, auto_restore=False)
        engine.process_order(sample_order)
        
        # Shutdown
        engine.shutdown()
        
        # Verify saved
        # Create new persistence to check
        from src.matching_engine.persistence import OrderBookPersistence
        from src.matching_engine.core.matching_engine import MatchingEngine
        
        new_engine = MatchingEngine()
        persistence = OrderBookPersistence(new_engine, config)
        orders_restored, _ = persistence.restore_state()
        
        assert orders_restored == 1
    
    def test_context_manager(self, db_config, config, sample_order):
        """Test using engine as context manager"""
        with PersistentMatchingEngine(config, auto_restore=False) as engine:
            engine.process_order(sample_order)
        
        # Should have saved on exit
        # Verify by creating new engine
        engine2 = PersistentMatchingEngine(config, auto_restore=True)
        assert "BTC-USD" in engine2.order_books
    
    def test_multiple_sessions(self, db_config, config):
        """Test multiple trading sessions with persistence"""
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
                symbol="ETH-USD",
                side=OrderSide.SELL,
                order_type=OrderType.LIMIT,
                price=Decimal("3000"),
                quantity=Decimal("5.0")
            ),
        ]
        
        # Session 1: Add first order
        with PersistentMatchingEngine(config, auto_restore=False) as engine:
            engine.process_order(orders[0])
        
        # Session 2: Add second order
        with PersistentMatchingEngine(config, auto_restore=True) as engine:
            engine.process_order(orders[1])
        
        # Session 3: Add third order and verify all present
        with PersistentMatchingEngine(config, auto_restore=True) as engine:
            engine.process_order(orders[2])
            
            # Should have all 3 orders across 2 symbols
            assert len(engine.order_books) == 2
            assert "BTC-USD" in engine.order_books
            assert "ETH-USD" in engine.order_books
    
    def test_crash_during_trading(self, db_config, config):
        """Test recovery from crash during active trading"""
        # Start trading
        engine1 = PersistentMatchingEngine(config, auto_restore=False)
        
        # Add several orders (some will match)
        for i in range(5):
            order = Order(
                user_id=f"user{i}",
                symbol="BTC-USD",
                side=OrderSide.BUY if i % 2 == 0 else OrderSide.SELL,
                order_type=OrderType.LIMIT,
                price=Decimal(str(50000 + i * 100)),
                quantity=Decimal("1.0")
            )
            engine1.process_order(order)
        
        # Simulate crash (don't call shutdown)
        del engine1
        
        # Recover
        engine2 = PersistentMatchingEngine(config, auto_restore=True)
        
        # Some orders should be restored (unfilled ones)
        # Note: Some orders may have matched, so we just verify we have an order book
        assert "BTC-USD" in engine2.order_books
        order_book = engine2.order_books["BTC-USD"]
        assert len(order_book.orders) >= 1  # At least some orders restored
    
    def test_persistence_stats_accessible(self, db_config, config, sample_order):
        """Test that persistence stats are accessible"""
        engine = PersistentMatchingEngine(config, auto_restore=False)
        engine.process_order(sample_order)
        
        stats = engine.persistence.get_persistence_stats()
        
        assert 'total_orders' in stats
        assert 'auto_save_enabled' in stats
        assert stats['total_orders'] >= 1
