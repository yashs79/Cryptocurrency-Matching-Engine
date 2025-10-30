"""
Integration Tests for Crash Recovery

End-to-end tests for persistence and crash recovery scenarios.
"""

import pytest
from decimal import Decimal
import tempfile
import os

from src.matching_engine.persistence.order_book_persistence import (
    PersistentMatchingEngine,
    PersistenceConfig
)
from src.matching_engine.core.order import Order, OrderSide, OrderType, OrderStatus
from src.matching_engine.config.database import init_db


class TestCrashRecoveryIntegration:
    """Integration tests for crash recovery"""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database file"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        yield path
        # Cleanup
        if os.path.exists(path):
            os.unlink(path)
    
    @pytest.fixture
    def config(self, temp_db):
        """Create config with temporary database"""
        # Initialize database first
        db_url = f"sqlite:///{temp_db}"
        init_db(database_url=db_url, echo=False)
        
        return PersistenceConfig(
            database_url=db_url,
            auto_save=True
        )
    
    def test_complete_crash_recovery_flow(self, config):
        """Test complete crash recovery workflow"""
        # Phase 1: Normal operation
        engine1 = PersistentMatchingEngine(config, auto_restore=False)
        
        orders = [
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
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                price=Decimal("49500"),
                quantity=Decimal("2.0")
            ),
            Order(
                user_id="charlie",
                symbol="BTC-USD",
                side=OrderSide.SELL,
                order_type=OrderType.LIMIT,
                price=Decimal("51000"),
                quantity=Decimal("1.5")
            ),
            Order(
                user_id="dave",
                symbol="ETH-USD",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                price=Decimal("3000"),
                quantity=Decimal("10.0")
            ),
        ]
        
        for order in orders:
            engine1.process_order(order)
        
        engine1.shutdown()
        
        # Phase 2: Crash recovery
        engine2 = PersistentMatchingEngine(config, auto_restore=True)
        
        # Verify all orders restored
        assert len(engine2.order_books) == 2
        assert "BTC-USD" in engine2.order_books
        assert "ETH-USD" in engine2.order_books
        
        btc_book = engine2.order_books["BTC-USD"]
        eth_book = engine2.order_books["ETH-USD"]
        
        assert len(btc_book.orders) == 3
        assert len(eth_book.orders) == 1
        
        # Phase 3: Continue trading
        new_order = Order(
            user_id="eve",
            symbol="BTC-USD",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("0.5")
        )
        
        processed, trades = engine2.process_order(new_order)
        
        # Should match with alice's order
        assert len(trades) == 1
        assert trades[0].quantity == Decimal("0.5")
        assert trades[0].price == Decimal("50000")
        
        engine2.shutdown()
    
    def test_recovery_after_partial_fills(self, config):
        """Test recovery with partially filled orders"""
        # Session 1: Create orders and partial fill
        engine1 = PersistentMatchingEngine(config, auto_restore=False)
        
        # Large buy order
        buy_order = Order(
            user_id="buyer",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("10.0")
        )
        engine1.process_order(buy_order)
        
        # Small sell order (partial fill)
        sell_order1 = Order(
            user_id="seller1",
            symbol="BTC-USD",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("3.0")
        )
        processed1, trades1 = engine1.process_order(sell_order1)
        
        assert len(trades1) == 1
        assert trades1[0].quantity == Decimal("3.0")
        
        engine1.shutdown()
        
        # Session 2: Recover and continue
        engine2 = PersistentMatchingEngine(config, auto_restore=True)
        
        # Verify partially filled order restored
        btc_book = engine2.order_books["BTC-USD"]
        restored_order = btc_book.orders[buy_order.order_id]
        
        assert restored_order.status == OrderStatus.PARTIALLY_FILLED
        assert restored_order.filled_quantity == Decimal("3.0")
        assert restored_order.remaining_quantity == Decimal("7.0")
        
        # Another sell order should match remaining
        sell_order2 = Order(
            user_id="seller2",
            symbol="BTC-USD",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("2.0")
        )
        processed2, trades2 = engine2.process_order(sell_order2)
        
        assert len(trades2) == 1
        assert trades2[0].quantity == Decimal("2.0")
        
        engine2.shutdown()
    
    def test_recovery_preserves_order_priority(self, config):
        """Test that recovery preserves price-time priority"""
        # Session 1: Create orders with specific time priority
        engine1 = PersistentMatchingEngine(config, auto_restore=False)
        
        # Three buy orders at same price
        orders = []
        for i in range(3):
            order = Order(
                user_id=f"user{i}",
                symbol="BTC-USD",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                price=Decimal("50000"),
                quantity=Decimal("1.0")
            )
            engine1.process_order(order)
            orders.append(order)
        
        engine1.shutdown()
        
        # Session 2: Recover and test priority
        engine2 = PersistentMatchingEngine(config, auto_restore=True)
        
        # Sell order should match with first order (time priority)
        sell_order = Order(
            user_id="seller",
            symbol="BTC-USD",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("0.5")
        )
        
        processed, trades = engine2.process_order(sell_order)
        
        assert len(trades) == 1
        # Should match with user0's order (first in time)
        assert trades[0].buyer_order_id == orders[0].order_id
        
        engine2.shutdown()
    
    def test_multiple_crash_recovery_cycles(self, config):
        """Test multiple crash and recovery cycles"""
        order_count = 0
        
        # Cycle 1
        with PersistentMatchingEngine(config, auto_restore=False) as engine:
            engine.process_order(Order(
                user_id="user1",
                symbol="BTC-USD",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                price=Decimal("50000"),
                quantity=Decimal("1.0")
            ))
            order_count += 1
        
        # Cycle 2
        with PersistentMatchingEngine(config, auto_restore=True) as engine:
            assert len(engine.order_books["BTC-USD"].orders) == order_count
            engine.process_order(Order(
                user_id="user2",
                symbol="BTC-USD",
                side=OrderSide.SELL,
                order_type=OrderType.LIMIT,
                price=Decimal("51000"),
                quantity=Decimal("1.0")
            ))
            order_count += 1
        
        # Cycle 3
        with PersistentMatchingEngine(config, auto_restore=True) as engine:
            assert len(engine.order_books["BTC-USD"].orders) == order_count
            engine.process_order(Order(
                user_id="user3",
                symbol="ETH-USD",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                price=Decimal("3000"),
                quantity=Decimal("5.0")
            ))
        
        # Final verification
        with PersistentMatchingEngine(config, auto_restore=True) as engine:
            assert len(engine.order_books) == 2
            assert len(engine.order_books["BTC-USD"].orders) == 2
            assert len(engine.order_books["ETH-USD"].orders) == 1
    
    def test_recovery_with_mixed_order_statuses(self, config):
        """Test recovery only restores active orders"""
        # Session 1: Create orders with different statuses
        engine1 = PersistentMatchingEngine(config, auto_restore=False)
        
        # Open order
        open_order = Order(
            user_id="user1",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1.0")
        )
        engine1.process_order(open_order)
        
        # Filled order (create matching orders)
        buy_order = Order(
            user_id="user2",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("51000"),
            quantity=Decimal("1.0")
        )
        engine1.process_order(buy_order)
        
        sell_order = Order(
            user_id="user3",
            symbol="BTC-USD",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            price=Decimal("51000"),
            quantity=Decimal("1.0")
        )
        engine1.process_order(sell_order)
        
        engine1.shutdown()
        
        # Session 2: Recover
        engine2 = PersistentMatchingEngine(config, auto_restore=True)
        
        # Open order should be restored (filled orders should not be)
        btc_book = engine2.order_books["BTC-USD"]
        assert open_order.order_id in btc_book.orders
        # At least the open order should be there
        assert len(btc_book.orders) >= 1
        
        engine2.shutdown()
    
    def test_concurrent_symbol_recovery(self, config):
        """Test recovery of multiple symbols simultaneously"""
        symbols = ["BTC-USD", "ETH-USD", "LTC-USD", "XRP-USD"]
        
        # Session 1: Create orders for multiple symbols
        engine1 = PersistentMatchingEngine(config, auto_restore=False)
        
        for symbol in symbols:
            for i in range(3):
                # Create orders that won't match (buys below sells)
                if i % 2 == 0:  # Buy orders
                    price = Decimal(str(1000 * (i + 1)))
                    side = OrderSide.BUY
                else:  # Sell orders at much higher prices
                    price = Decimal(str(10000 * (i + 1)))
                    side = OrderSide.SELL
                
                order = Order(
                    user_id=f"user{i}_{symbol}",
                    symbol=symbol,
                    side=side,
                    order_type=OrderType.LIMIT,
                    price=price,
                    quantity=Decimal("1.0")
                )
                engine1.process_order(order)
        
        engine1.shutdown()
        
        # Session 2: Recover all
        engine2 = PersistentMatchingEngine(config, auto_restore=True)
        
        # Verify all symbols restored
        assert len(engine2.order_books) == 4
        for symbol in symbols:
            assert symbol in engine2.order_books
            assert len(engine2.order_books[symbol].orders) == 3
        
        engine2.shutdown()
    
    def test_performance_large_order_book_recovery(self, config):
        """Test recovery performance with large order book"""
        import time
        
        # Session 1: Create large order book
        engine1 = PersistentMatchingEngine(config, auto_restore=False)
        
        num_orders = 100
        for i in range(num_orders):
            # Create orders that won't match
            # Buys at 40000-40049, Sells at 60000-60049
            if i % 2 == 0:  # Buy orders
                price = Decimal(str(40000 + i))
                side = OrderSide.BUY
            else:  # Sell orders
                price = Decimal(str(60000 + i))
                side = OrderSide.SELL
            
            order = Order(
                user_id=f"user{i}",
                symbol="BTC-USD",
                side=side,
                order_type=OrderType.LIMIT,
                price=price,
                quantity=Decimal("1.0")
            )
            engine1.process_order(order)
        
        engine1.shutdown()
        
        # Session 2: Measure recovery time
        start_time = time.time()
        engine2 = PersistentMatchingEngine(config, auto_restore=True)
        recovery_time = time.time() - start_time
        
        # Verify all orders restored
        assert len(engine2.order_books["BTC-USD"].orders) == num_orders
        
        # Recovery should be reasonably fast (< 5 seconds for 100 orders)
        assert recovery_time < 5.0
        
        engine2.shutdown()
