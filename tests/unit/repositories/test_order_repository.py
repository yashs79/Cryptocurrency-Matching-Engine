"""
Tests for Order Repository
"""

import pytest
from decimal import Decimal
from datetime import datetime, UTC, timedelta

from src.matching_engine.core.order import Order, OrderSide, OrderType, OrderStatus
from src.matching_engine.repositories.order_repository import (
    OrderRepository,
    OrderFilter,
    SortField,
    SortOrder
)


class TestOrderRepository:
    """Test OrderRepository"""
    
    @pytest.fixture
    def repository(self):
        """Create repository"""
        return OrderRepository()
    
    @pytest.fixture
    def sample_orders(self):
        """Create sample orders"""
        return [
            Order(
                user_id="user1",
                symbol="BTC-USD",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                price=Decimal("50000"),
                quantity=Decimal("1.0")
            ),
            Order(
                user_id="user1",
                symbol="BTC-USD",
                side=OrderSide.SELL,
                order_type=OrderType.LIMIT,
                price=Decimal("51000"),
                quantity=Decimal("2.0")
            ),
            Order(
                user_id="user2",
                symbol="ETH-USD",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                price=Decimal("3000"),
                quantity=Decimal("5.0")
            ),
        ]
    
    def test_save_and_get(self, repository):
        """Test saving and retrieving an order"""
        order = Order(
            user_id="user1",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1.0")
        )
        
        # Save order
        saved = repository.save(order)
        assert saved.order_id == order.order_id
        
        # Retrieve order
        retrieved = repository.get(order.order_id)
        assert retrieved is not None
        assert retrieved.order_id == order.order_id
        assert retrieved.user_id == "user1"
        assert retrieved.symbol == "BTC-USD"
    
    def test_get_nonexistent(self, repository):
        """Test getting non-existent order"""
        result = repository.get("nonexistent")
        assert result is None
    
    def test_update_order(self, repository):
        """Test updating an existing order"""
        order = Order(
            user_id="user1",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1.0")
        )
        repository.save(order)
        
        # Update order status
        order.status = OrderStatus.FILLED
        repository.save(order)
        
        # Verify update
        retrieved = repository.get(order.order_id)
        assert retrieved.status == OrderStatus.FILLED
    
    def test_delete_order(self, repository):
        """Test deleting an order"""
        order = Order(
            user_id="user1",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1.0")
        )
        repository.save(order)
        
        # Delete order
        success = repository.delete(order.order_id)
        assert success == True
        
        # Verify deletion
        assert repository.get(order.order_id) is None
    
    def test_delete_nonexistent(self, repository):
        """Test deleting non-existent order"""
        success = repository.delete("nonexistent")
        assert success == False
    
    def test_find_all(self, repository, sample_orders):
        """Test finding all orders"""
        for order in sample_orders:
            repository.save(order)
        
        results = repository.find()
        assert len(results) == 3
    
    def test_find_by_user(self, repository, sample_orders):
        """Test finding orders by user"""
        for order in sample_orders:
            repository.save(order)
        
        results = repository.find_by_user("user1")
        assert len(results) == 2
        assert all(o.user_id == "user1" for o in results)
    
    def test_find_by_symbol(self, repository, sample_orders):
        """Test finding orders by symbol"""
        for order in sample_orders:
            repository.save(order)
        
        results = repository.find_by_symbol("BTC-USD")
        assert len(results) == 2
        assert all(o.symbol == "BTC-USD" for o in results)
    
    def test_find_by_status(self, repository, sample_orders):
        """Test finding orders by status"""
        for order in sample_orders:
            repository.save(order)
        
        results = repository.find_by_status(OrderStatus.OPEN)
        assert len(results) == 3
        assert all(o.status == OrderStatus.OPEN for o in results)
    
    def test_find_open_orders(self, repository, sample_orders):
        """Test finding open orders"""
        for order in sample_orders:
            repository.save(order)
        
        # Mark one as filled
        sample_orders[0].status = OrderStatus.FILLED
        repository.save(sample_orders[0])
        
        results = repository.find_open_orders()
        assert len(results) == 2
        assert all(o.status in [OrderStatus.OPEN, OrderStatus.PARTIALLY_FILLED] for o in results)
    
    def test_filter_by_side(self, repository, sample_orders):
        """Test filtering by order side"""
        for order in sample_orders:
            repository.save(order)
        
        filter = OrderFilter(side=OrderSide.BUY)
        results = repository.find(filter)
        
        assert len(results) == 2
        assert all(o.side == OrderSide.BUY for o in results)
    
    def test_filter_by_order_type(self, repository, sample_orders):
        """Test filtering by order type"""
        # Add a market order
        market_order = Order(
            user_id="user1",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=Decimal("1.0")
        )
        sample_orders.append(market_order)
        
        for order in sample_orders:
            repository.save(order)
        
        filter = OrderFilter(order_type=OrderType.MARKET)
        results = repository.find(filter)
        
        assert len(results) == 1
        assert results[0].order_type == OrderType.MARKET
    
    def test_filter_by_price_range(self, repository, sample_orders):
        """Test filtering by price range"""
        for order in sample_orders:
            repository.save(order)
        
        filter = OrderFilter(
            min_price=Decimal("40000"),
            max_price=Decimal("50500")
        )
        results = repository.find(filter)
        
        assert len(results) == 1
        assert results[0].price == Decimal("50000")
    
    def test_filter_by_quantity_range(self, repository, sample_orders):
        """Test filtering by quantity range"""
        for order in sample_orders:
            repository.save(order)
        
        filter = OrderFilter(
            min_quantity=Decimal("2.0"),
            max_quantity=Decimal("10.0")
        )
        results = repository.find(filter)
        
        assert len(results) == 2
        assert all(Decimal("2.0") <= o.quantity <= Decimal("10.0") for o in results)
    
    def test_filter_by_timestamp_range(self, repository):
        """Test filtering by timestamp range"""
        now = datetime.now(UTC)
        
        # Create orders with different timestamps
        old_order = Order(
            user_id="user1",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1.0")
        )
        old_order.timestamp = now - timedelta(hours=2)
        
        new_order = Order(
            user_id="user1",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("51000"),
            quantity=Decimal("1.0")
        )
        new_order.timestamp = now
        
        repository.save(old_order)
        repository.save(new_order)
        
        # Filter for recent orders
        filter = OrderFilter(from_timestamp=now - timedelta(hours=1))
        results = repository.find(filter)
        
        assert len(results) == 1
        assert results[0].order_id == new_order.order_id
    
    def test_combined_filters(self, repository, sample_orders):
        """Test combining multiple filters"""
        for order in sample_orders:
            repository.save(order)
        
        filter = OrderFilter(
            user_id="user1",
            symbol="BTC-USD",
            side=OrderSide.BUY
        )
        results = repository.find(filter)
        
        assert len(results) == 1
        assert results[0].user_id == "user1"
        assert results[0].symbol == "BTC-USD"
        assert results[0].side == OrderSide.BUY
    
    def test_sort_by_timestamp(self, repository, sample_orders):
        """Test sorting by timestamp"""
        for order in sample_orders:
            repository.save(order)
        
        # Sort ascending
        results = repository.find(sort_by=SortField.TIMESTAMP, sort_order=SortOrder.ASC)
        assert results[0].timestamp <= results[-1].timestamp
        
        # Sort descending
        results = repository.find(sort_by=SortField.TIMESTAMP, sort_order=SortOrder.DESC)
        assert results[0].timestamp >= results[-1].timestamp
    
    def test_sort_by_price(self, repository, sample_orders):
        """Test sorting by price"""
        for order in sample_orders:
            repository.save(order)
        
        results = repository.find(sort_by=SortField.PRICE, sort_order=SortOrder.ASC)
        prices = [o.price for o in results if o.price]
        assert prices == sorted(prices)
    
    def test_sort_by_quantity(self, repository, sample_orders):
        """Test sorting by quantity"""
        for order in sample_orders:
            repository.save(order)
        
        results = repository.find(sort_by=SortField.QUANTITY, sort_order=SortOrder.DESC)
        quantities = [o.quantity for o in results]
        assert quantities == sorted(quantities, reverse=True)
    
    def test_pagination(self, repository, sample_orders):
        """Test pagination with limit and offset"""
        for order in sample_orders:
            repository.save(order)
        
        # Get first page
        page1 = repository.find(limit=2, offset=0)
        assert len(page1) == 2
        
        # Get second page
        page2 = repository.find(limit=2, offset=2)
        assert len(page2) == 1
        
        # Verify no overlap
        page1_ids = {o.order_id for o in page1}
        page2_ids = {o.order_id for o in page2}
        assert page1_ids.isdisjoint(page2_ids)
    
    def test_count(self, repository, sample_orders):
        """Test counting orders"""
        for order in sample_orders:
            repository.save(order)
        
        # Count all
        assert repository.count() == 3
        
        # Count with filter
        filter = OrderFilter(user_id="user1")
        assert repository.count(filter) == 2
    
    def test_exists(self, repository):
        """Test checking if order exists"""
        order = Order(
            user_id="user1",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1.0")
        )
        
        assert repository.exists(order.order_id) == False
        
        repository.save(order)
        assert repository.exists(order.order_id) == True
        
        repository.delete(order.order_id)
        assert repository.exists(order.order_id) == False
    
    def test_clear(self, repository, sample_orders):
        """Test clearing repository"""
        for order in sample_orders:
            repository.save(order)
        
        assert repository.count() == 3
        
        repository.clear()
        assert repository.count() == 0
        assert len(repository._user_index) == 0
        assert len(repository._symbol_index) == 0
    
    def test_statistics(self, repository, sample_orders):
        """Test getting repository statistics"""
        for order in sample_orders:
            repository.save(order)
        
        stats = repository.get_statistics()
        
        assert stats["total_orders"] == 3
        assert stats["users"] == 2
        assert stats["symbols"] == 2
        assert "status_breakdown" in stats
        assert "side_breakdown" in stats
        assert stats["status_breakdown"]["open"] == 3
        assert stats["side_breakdown"]["buy"] == 2
        assert stats["side_breakdown"]["sell"] == 1
    
    def test_index_maintenance_on_update(self, repository):
        """Test that indexes are maintained correctly on updates"""
        order = Order(
            user_id="user1",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1.0")
        )
        repository.save(order)
        
        # Verify initial indexes
        assert order.order_id in repository._user_index["user1"]
        assert order.order_id in repository._symbol_index["BTC-USD"]
        assert order.order_id in repository._status_index[OrderStatus.OPEN]
        
        # Update status
        order.status = OrderStatus.FILLED
        repository.save(order)
        
        # Verify indexes updated
        assert order.order_id not in repository._status_index.get(OrderStatus.OPEN, set())
        assert order.order_id in repository._status_index[OrderStatus.FILLED]
    
    def test_filter_by_multiple_statuses(self, repository, sample_orders):
        """Test filtering by multiple statuses"""
        for order in sample_orders:
            repository.save(order)
        
        # Mark one as partially filled
        sample_orders[0].status = OrderStatus.PARTIALLY_FILLED
        repository.save(sample_orders[0])
        
        filter = OrderFilter(statuses=[OrderStatus.OPEN, OrderStatus.PARTIALLY_FILLED])
        results = repository.find(filter)
        
        assert len(results) == 3
        assert all(o.status in [OrderStatus.OPEN, OrderStatus.PARTIALLY_FILLED] for o in results)
