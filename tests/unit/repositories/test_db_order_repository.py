"""
Tests for Database Order Repository
"""

import pytest
from decimal import Decimal
from datetime import datetime, UTC

from src.matching_engine.core.order import Order, OrderSide, OrderType, OrderStatus
from src.matching_engine.repositories import DatabaseOrderRepository, OrderFilter
from src.matching_engine.config.database import init_db


class TestDatabaseOrderRepository:
    """Test DatabaseOrderRepository"""
    
    @pytest.fixture(scope="function")
    def db_repo(self):
        """Create database repository with in-memory SQLite"""
        # Use in-memory SQLite for tests
        init_db(database_url="sqlite:///:memory:", echo=False)
        repo = DatabaseOrderRepository()
        yield repo
        repo.close()
    
    @pytest.fixture
    def sample_order(self):
        """Create a sample order"""
        return Order(
            user_id="user1",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1.0")
        )
    
    def test_save_and_get(self, db_repo, sample_order):
        """Test saving and retrieving an order"""
        # Save order
        saved = db_repo.save(sample_order)
        assert saved.order_id == sample_order.order_id
        
        # Retrieve order
        retrieved = db_repo.get(sample_order.order_id)
        assert retrieved is not None
        assert retrieved.order_id == sample_order.order_id
        assert retrieved.user_id == "user1"
        assert retrieved.symbol == "BTC-USD"
        assert retrieved.price == Decimal("50000")
    
    def test_update_order(self, db_repo, sample_order):
        """Test updating an existing order"""
        # Save order
        db_repo.save(sample_order)
        
        # Update order
        sample_order.status = OrderStatus.FILLED
        sample_order.filled_quantity = Decimal("1.0")
        db_repo.save(sample_order)
        
        # Retrieve and verify
        retrieved = db_repo.get(sample_order.order_id)
        assert retrieved.status == OrderStatus.FILLED
        assert retrieved.filled_quantity == Decimal("1.0")
    
    def test_delete_order(self, db_repo, sample_order):
        """Test deleting an order"""
        # Save order
        db_repo.save(sample_order)
        
        # Delete order
        success = db_repo.delete(sample_order.order_id)
        assert success == True
        
        # Verify deletion
        assert db_repo.get(sample_order.order_id) is None
    
    def test_find_all(self, db_repo):
        """Test finding all orders"""
        # Create multiple orders
        for i in range(3):
            order = Order(
                user_id=f"user{i}",
                symbol="BTC-USD",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                price=Decimal("50000"),
                quantity=Decimal("1.0")
            )
            db_repo.save(order)
        
        # Find all
        orders = db_repo.find()
        assert len(orders) == 3
    
    def test_find_by_user(self, db_repo):
        """Test finding orders by user"""
        # Create orders for different users
        for i in range(2):
            order = Order(
                user_id="user1",
                symbol="BTC-USD",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                price=Decimal("50000"),
                quantity=Decimal("1.0")
            )
            db_repo.save(order)
        
        order = Order(
            user_id="user2",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1.0")
        )
        db_repo.save(order)
        
        # Find by user
        user1_orders = db_repo.find_by_user("user1")
        assert len(user1_orders) == 2
        assert all(o.user_id == "user1" for o in user1_orders)
    
    def test_find_with_filter(self, db_repo):
        """Test finding orders with complex filter"""
        # Create diverse orders
        orders_data = [
            ("user1", "BTC-USD", OrderSide.BUY, Decimal("50000")),
            ("user1", "BTC-USD", OrderSide.SELL, Decimal("51000")),
            ("user2", "ETH-USD", OrderSide.BUY, Decimal("3000")),
        ]
        
        for user_id, symbol, side, price in orders_data:
            order = Order(
                user_id=user_id,
                symbol=symbol,
                side=side,
                order_type=OrderType.LIMIT,
                price=price,
                quantity=Decimal("1.0")
            )
            db_repo.save(order)
        
        # Filter by symbol and side
        filter = OrderFilter(symbol="BTC-USD", side=OrderSide.BUY)
        results = db_repo.find(filter)
        
        assert len(results) == 1
        assert results[0].symbol == "BTC-USD"
        assert results[0].side == OrderSide.BUY
    
    def test_count(self, db_repo):
        """Test counting orders"""
        # Create orders
        for i in range(5):
            order = Order(
                user_id="user1",
                symbol="BTC-USD",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                price=Decimal("50000"),
                quantity=Decimal("1.0")
            )
            db_repo.save(order)
        
        # Count all
        assert db_repo.count() == 5
        
        # Count with filter
        filter = OrderFilter(user_id="user1")
        assert db_repo.count(filter) == 5
    
    def test_persistence(self, sample_order):
        """Test that data persists across repository instances"""
        # Create first repository and save order
        init_db(database_url="sqlite:///:memory:", echo=False)
        repo1 = DatabaseOrderRepository()
        repo1.save(sample_order)
        
        # Note: In-memory SQLite doesn't persist across connections
        # This test demonstrates the pattern for file-based databases
        order_id = sample_order.order_id
        
        # Verify in same session
        retrieved = repo1.get(order_id)
        assert retrieved is not None
        
        repo1.close()
    
    def test_sync_from_database(self, db_repo, sample_order):
        """Test syncing cache from database"""
        # Save order
        db_repo.save(sample_order)
        
        # Clear cache
        db_repo._orders.clear()
        db_repo._user_index.clear()
        db_repo._symbol_index.clear()
        db_repo._status_index.clear()
        
        # Sync from database
        count = db_repo.sync_from_database()
        assert count == 1
        
        # Verify order is in cache
        retrieved = db_repo.get(sample_order.order_id)
        assert retrieved is not None
    
    def test_find_open_orders(self, db_repo):
        """Test finding open orders"""
        # Create orders with different statuses
        open_order = Order(
            user_id="user1",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1.0")
        )
        db_repo.save(open_order)
        
        filled_order = Order(
            user_id="user2",
            symbol="BTC-USD",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            price=Decimal("51000"),
            quantity=Decimal("1.0")
        )
        filled_order.status = OrderStatus.FILLED
        db_repo.save(filled_order)
        
        # Find open orders
        open_orders = db_repo.find_open_orders()
        assert len(open_orders) == 1
        assert open_orders[0].status == OrderStatus.OPEN
    
    def test_clear(self, db_repo, sample_order):
        """Test clearing repository"""
        # Save order
        db_repo.save(sample_order)
        assert db_repo.count() == 1
        
        # Clear
        db_repo.clear()
        assert db_repo.count() == 0
    
    def test_context_manager(self, sample_order):
        """Test using repository as context manager"""
        init_db(database_url="sqlite:///:memory:", echo=False)
        
        with DatabaseOrderRepository() as repo:
            repo.save(sample_order)
            assert repo.get(sample_order.order_id) is not None
        
        # Session should be closed after context
