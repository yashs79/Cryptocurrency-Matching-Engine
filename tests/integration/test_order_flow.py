"""
Integration Tests for Complete Order Flow

Tests the integration of all Phase 2 components:
- Order Validator
- Order Manager
- Order Repository
- Event Publisher
- Matching Engine
"""

import pytest
from decimal import Decimal
from datetime import datetime, UTC

from src.matching_engine.core.order import Order, OrderSide, OrderType, OrderStatus
from src.matching_engine.core.matching_engine import MatchingEngine
from src.matching_engine.services.order_validator import OrderValidator, OrderValidatorConfig, ValidationError
from src.matching_engine.services.order_manager import OrderManager, OrderManagerError
from src.matching_engine.repositories.order_repository import OrderRepository, OrderFilter, SortField, SortOrder
from src.matching_engine.events.event_publisher import EventPublisher, EventSubscriber
from src.matching_engine.events.order_events import (
    OrderEventType,
    OrderSubmittedEvent,
    OrderCancelledEvent,
    OrderFilledEvent,
    OrderPartiallyFilledEvent,
)


class OrderEventCollector(EventSubscriber):
    """Collects events for testing"""
    
    def __init__(self):
        self.events = []
        self.events_by_type = {}
    
    def on_event(self, event):
        self.events.append(event)
        event_type = event.event_type
        if event_type not in self.events_by_type:
            self.events_by_type[event_type] = []
        self.events_by_type[event_type].append(event)
    
    def get_events(self, event_type=None):
        if event_type:
            return self.events_by_type.get(event_type, [])
        return self.events
    
    def clear(self):
        self.events.clear()
        self.events_by_type.clear()


class TestCompleteOrderFlow:
    """Test complete order flow with all components"""
    
    @pytest.fixture
    def matching_engine(self):
        """Create matching engine"""
        return MatchingEngine()
    
    @pytest.fixture
    def validator(self):
        """Create validator with reasonable config"""
        config = OrderValidatorConfig(
            min_price=Decimal("1"),
            max_price=Decimal("1000000"),
            min_quantity=Decimal("0.001"),
            max_quantity=Decimal("10000"),
            tick_size=Decimal("0.01"),
            lot_size=Decimal("0.001"),
            max_orders_per_second=100,
        )
        return OrderValidator(config)
    
    @pytest.fixture
    def order_manager(self, matching_engine, validator):
        """Create order manager"""
        return OrderManager(matching_engine, validator)
    
    @pytest.fixture
    def repository(self):
        """Create order repository"""
        return OrderRepository()
    
    @pytest.fixture
    def event_publisher(self):
        """Create event publisher"""
        return EventPublisher()
    
    @pytest.fixture
    def event_collector(self, event_publisher):
        """Create and subscribe event collector"""
        collector = OrderEventCollector()
        event_publisher.subscribe(collector)
        return collector
    
    def test_simple_order_submission(self, order_manager, repository, event_publisher, event_collector):
        """Test simple order submission flow"""
        # Create order
        order = Order(
            user_id="user1",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1.0")
        )
        
        # Submit order
        processed_order, trades = order_manager.submit_order(order)
        
        # Publish event
        event_publisher.publish(OrderSubmittedEvent(processed_order))
        
        # Save to repository
        repository.save(processed_order)
        
        # Verify order was processed
        assert processed_order.status == OrderStatus.OPEN
        assert len(trades) == 0
        
        # Verify event was published
        assert len(event_collector.get_events(OrderEventType.SUBMITTED)) == 1
        
        # Verify order is in repository
        retrieved = repository.get(processed_order.order_id)
        assert retrieved is not None
        assert retrieved.order_id == processed_order.order_id
    
    def test_order_matching_flow(self, order_manager, repository, event_publisher, event_collector):
        """Test order matching with events and storage"""
        # Submit sell order
        sell_order = Order(
            user_id="seller",
            symbol="BTC-USD",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1.0")
        )
        
        sell_processed, _ = order_manager.submit_order(sell_order)
        event_publisher.publish(OrderSubmittedEvent(sell_processed))
        repository.save(sell_processed)
        
        # Submit matching buy order
        buy_order = Order(
            user_id="buyer",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1.0")
        )
        
        buy_processed, trades = order_manager.submit_order(buy_order)
        event_publisher.publish(OrderSubmittedEvent(buy_processed))
        
        # Publish fill events
        if buy_processed.status == OrderStatus.FILLED:
            event_publisher.publish(OrderFilledEvent(buy_processed, trades))
        
        repository.save(buy_processed)
        
        # Update sell order status
        sell_updated = order_manager.get_order_status("BTC-USD", sell_order.order_id)
        repository.save(sell_updated)
        
        # Verify trade occurred
        assert len(trades) == 1
        assert trades[0].quantity == Decimal("1.0")
        
        # Verify both orders are filled
        assert buy_processed.status == OrderStatus.FILLED
        assert sell_updated.status == OrderStatus.FILLED
        
        # Verify events
        submitted_events = event_collector.get_events(OrderEventType.SUBMITTED)
        assert len(submitted_events) == 2
        
        filled_events = event_collector.get_events(OrderEventType.FILLED)
        assert len(filled_events) == 1
        
        # Verify repository state
        buy_from_repo = repository.get(buy_order.order_id)
        sell_from_repo = repository.get(sell_order.order_id)
        
        assert buy_from_repo.status == OrderStatus.FILLED
        assert sell_from_repo.status == OrderStatus.FILLED
    
    def test_order_cancellation_flow(self, order_manager, repository, event_publisher, event_collector):
        """Test order cancellation with all components"""
        # Submit order
        order = Order(
            user_id="user1",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1.0")
        )
        
        processed_order, _ = order_manager.submit_order(order)
        event_publisher.publish(OrderSubmittedEvent(processed_order))
        repository.save(processed_order)
        
        # Cancel order
        success = order_manager.cancel_order("BTC-USD", order.order_id, "user1")
        assert success == True
        
        # Get updated order
        cancelled_order = order_manager.get_order_status("BTC-USD", order.order_id)
        
        # Publish cancel event
        event_publisher.publish(OrderCancelledEvent(cancelled_order, cancelled_by="user1"))
        
        # Update in repository
        repository.save(cancelled_order)
        
        # Verify cancellation
        assert cancelled_order.status == OrderStatus.CANCELLED
        
        # Verify events
        cancelled_events = event_collector.get_events(OrderEventType.CANCELLED)
        assert len(cancelled_events) == 1
        
        # Verify repository
        from_repo = repository.get(order.order_id)
        assert from_repo.status == OrderStatus.CANCELLED
    
    def test_validation_rejection_flow(self, order_manager, event_publisher, event_collector):
        """Test order rejection due to validation"""
        # Create invalid order (price too low)
        order = Order(
            user_id="user1",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("0.001"),  # Below minimum
            quantity=Decimal("1.0")
        )
        
        # Try to submit
        with pytest.raises(ValidationError) as exc_info:
            order_manager.submit_order(order)
        
        # Verify error
        assert "below minimum" in str(exc_info.value)
        
        # Check order history shows rejection
        history = order_manager.get_order_history(order.order_id)
        assert len(history) > 0
        assert any("reject" in action.value.lower() for action, _, _ in history)
    
    def test_multi_user_scenario(self, order_manager, repository, event_publisher, event_collector):
        """Test multiple users trading"""
        users = ["user1", "user2", "user3"]
        
        # Each user submits a buy order
        for i, user in enumerate(users):
            order = Order(
                user_id=user,
                symbol="BTC-USD",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                price=Decimal(f"{50000 + i * 100}"),
                quantity=Decimal("1.0")
            )
            
            processed, _ = order_manager.submit_order(order)
            event_publisher.publish(OrderSubmittedEvent(processed))
            repository.save(processed)
        
        # Verify all orders in repository
        for user in users:
            user_orders = repository.find_by_user(user)
            assert len(user_orders) == 1
            assert user_orders[0].user_id == user
        
        # Verify events
        submitted_events = event_collector.get_events(OrderEventType.SUBMITTED)
        assert len(submitted_events) == 3
    
    def test_partial_fill_flow(self, order_manager, repository, event_publisher, event_collector):
        """Test partial order fill"""
        # Submit large sell order
        sell_order = Order(
            user_id="seller",
            symbol="BTC-USD",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("10.0")
        )
        
        sell_processed, _ = order_manager.submit_order(sell_order)
        event_publisher.publish(OrderSubmittedEvent(sell_processed))
        repository.save(sell_processed)
        
        # Submit smaller buy order
        buy_order = Order(
            user_id="buyer",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("3.0")
        )
        
        buy_processed, trades = order_manager.submit_order(buy_order)
        event_publisher.publish(OrderSubmittedEvent(buy_processed))
        
        if buy_processed.status == OrderStatus.FILLED:
            event_publisher.publish(OrderFilledEvent(buy_processed, trades))
        
        repository.save(buy_processed)
        
        # Get updated sell order
        sell_updated = order_manager.get_order_status("BTC-USD", sell_order.order_id)
        
        if sell_updated.status == OrderStatus.PARTIALLY_FILLED:
            event_publisher.publish(OrderPartiallyFilledEvent(sell_updated, trades))
        
        repository.save(sell_updated)
        
        # Verify partial fill
        assert sell_updated.status == OrderStatus.PARTIALLY_FILLED
        assert sell_updated.filled_quantity == Decimal("3.0")
        assert sell_updated.remaining_quantity == Decimal("7.0")
        
        # Verify buy order is filled
        assert buy_processed.status == OrderStatus.FILLED
        
        # Verify events
        partial_events = event_collector.get_events(OrderEventType.PARTIALLY_FILLED)
        assert len(partial_events) >= 1
    
    def test_order_amendment_flow(self, order_manager, repository, event_publisher, event_collector):
        """Test order amendment"""
        # Submit order
        order = Order(
            user_id="user1",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1.0")
        )
        
        processed_order, _ = order_manager.submit_order(order)
        event_publisher.publish(OrderSubmittedEvent(processed_order))
        repository.save(processed_order)
        
        # Amend order
        new_order, _ = order_manager.amend_order(
            "BTC-USD",
            order.order_id,
            new_price=Decimal("51000"),
            new_quantity=Decimal("2.0"),
            user_id="user1"
        )
        
        event_publisher.publish(OrderSubmittedEvent(new_order))
        repository.save(new_order)
        
        # Verify amendment
        assert new_order.price == Decimal("51000")
        assert new_order.quantity == Decimal("2.0")
        assert new_order.order_id != order.order_id
        
        # Verify old order is cancelled
        old_order = repository.get(order.order_id)
        assert old_order.status == OrderStatus.CANCELLED
        
        # Verify new order is open
        assert new_order.status == OrderStatus.OPEN
    
    def test_repository_queries_with_live_data(self, order_manager, repository):
        """Test repository queries with real order data"""
        # Create diverse set of orders
        orders_data = [
            ("user1", "BTC-USD", OrderSide.BUY, Decimal("50000"), Decimal("1.0")),
            ("user1", "BTC-USD", OrderSide.SELL, Decimal("51000"), Decimal("2.0")),
            ("user2", "ETH-USD", OrderSide.BUY, Decimal("3000"), Decimal("5.0")),
            ("user2", "BTC-USD", OrderSide.BUY, Decimal("49000"), Decimal("1.5")),
            ("user3", "BTC-USD", OrderSide.SELL, Decimal("52000"), Decimal("3.0")),
        ]
        
        for user_id, symbol, side, price, quantity in orders_data:
            order = Order(
                user_id=user_id,
                symbol=symbol,
                side=side,
                order_type=OrderType.LIMIT,
                price=price,
                quantity=quantity
            )
            processed, _ = order_manager.submit_order(order)
            repository.save(processed)
        
        # Test various queries
        
        # Query by user
        user1_orders = repository.find_by_user("user1")
        assert len(user1_orders) == 2
        
        # Query by symbol
        btc_orders = repository.find_by_symbol("BTC-USD")
        assert len(btc_orders) == 4
        
        # Query with filter
        filter = OrderFilter(
            symbol="BTC-USD",
            side=OrderSide.BUY,
            min_price=Decimal("49000"),
            max_price=Decimal("50000")
        )
        filtered = repository.find(filter)
        assert len(filtered) == 2
        
        # Query with sorting
        sorted_orders = repository.find(
            OrderFilter(symbol="BTC-USD"),
            sort_by=SortField.PRICE,
            sort_order=SortOrder.ASC
        )
        assert len(sorted_orders) == 4
        prices = [o.price for o in sorted_orders]
        assert prices == sorted(prices)
        
        # Count queries
        total = repository.count()
        assert total == 5
        
        btc_count = repository.count(OrderFilter(symbol="BTC-USD"))
        assert btc_count == 4
    
    def test_event_history_tracking(self, order_manager, event_publisher, event_collector):
        """Test event history is properly tracked"""
        # Submit multiple orders
        for i in range(5):
            order = Order(
                user_id=f"user{i}",
                symbol="BTC-USD",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                price=Decimal("50000"),
                quantity=Decimal("1.0")
            )
            
            processed, _ = order_manager.submit_order(order)
            event_publisher.publish(OrderSubmittedEvent(processed))
        
        # Verify event history
        history = event_publisher.get_history()
        assert len(history) == 5
        
        # Verify all are submitted events
        submitted = event_publisher.get_history(OrderEventType.SUBMITTED)
        assert len(submitted) == 5
        
        # Get events for specific order
        first_order_id = event_collector.events[0].order.order_id
        order_events = event_publisher.get_events_for_order(first_order_id)
        assert len(order_events) >= 1
    
    def test_statistics_across_components(self, order_manager, repository, event_publisher):
        """Test statistics from all components"""
        # Submit some orders
        for i in range(3):
            order = Order(
                user_id=f"user{i}",
                symbol="BTC-USD",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                price=Decimal("50000"),
                quantity=Decimal("1.0")
            )
            
            processed, _ = order_manager.submit_order(order)
            event_publisher.publish(OrderSubmittedEvent(processed))
            repository.save(processed)
        
        # Get statistics
        manager_stats = order_manager.get_statistics()
        repo_stats = repository.get_statistics()
        event_stats = event_publisher.get_statistics()
        
        # Verify statistics
        assert manager_stats["total_orders_processed"] == 3
        assert repo_stats["total_orders"] == 3
        assert event_stats["total_events"] == 3
        
        # Verify consistency
        assert repo_stats["users"] == 3
        assert repo_stats["symbols"] == 1
