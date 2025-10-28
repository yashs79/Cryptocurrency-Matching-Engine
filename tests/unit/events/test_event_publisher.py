"""
Tests for Event Publisher
"""

import pytest
import asyncio
from decimal import Decimal

from src.matching_engine.core.order import Order, OrderSide, OrderType
from src.matching_engine.events.order_events import (
    OrderSubmittedEvent,
    OrderCancelledEvent,
    OrderEventType,
)
from src.matching_engine.events.event_publisher import EventPublisher, EventSubscriber


class TestSubscriber(EventSubscriber):
    """Test subscriber implementation"""
    
    def __init__(self):
        self.events_received = []
    
    def on_event(self, event):
        self.events_received.append(event)
    
    async def on_event_async(self, event):
        self.events_received.append(event)


class TestEventPublisher:
    """Test EventPublisher"""
    
    @pytest.fixture
    def publisher(self):
        """Create event publisher"""
        return EventPublisher(max_history=100)
    
    @pytest.fixture
    def sample_order(self):
        """Create sample order"""
        return Order(
            user_id="user1",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1.0")
        )
    
    def test_initialization(self, publisher):
        """Test publisher initialization"""
        assert publisher.max_history == 100
        assert len(publisher._event_history) == 0
        assert publisher._total_events == 0
    
    def test_subscribe_to_all_events(self, publisher):
        """Test subscribing to all events"""
        subscriber = TestSubscriber()
        publisher.subscribe(subscriber)
        
        assert subscriber in publisher._global_subscribers
    
    def test_subscribe_to_specific_event(self, publisher):
        """Test subscribing to specific event type"""
        subscriber = TestSubscriber()
        publisher.subscribe(subscriber, OrderEventType.SUBMITTED)
        
        assert subscriber in publisher._subscribers[OrderEventType.SUBMITTED]
    
    def test_unsubscribe(self, publisher):
        """Test unsubscribing"""
        subscriber = TestSubscriber()
        publisher.subscribe(subscriber)
        publisher.unsubscribe(subscriber)
        
        assert subscriber not in publisher._global_subscribers
    
    def test_publish_to_global_subscriber(self, publisher, sample_order):
        """Test publishing to global subscriber"""
        subscriber = TestSubscriber()
        publisher.subscribe(subscriber)
        
        event = OrderSubmittedEvent(sample_order)
        publisher.publish(event)
        
        assert len(subscriber.events_received) == 1
        assert subscriber.events_received[0] == event
    
    def test_publish_to_type_specific_subscriber(self, publisher, sample_order):
        """Test publishing to type-specific subscriber"""
        subscriber = TestSubscriber()
        publisher.subscribe(subscriber, OrderEventType.SUBMITTED)
        
        # Publish matching event
        event1 = OrderSubmittedEvent(sample_order)
        publisher.publish(event1)
        
        assert len(subscriber.events_received) == 1
        
        # Publish non-matching event
        event2 = OrderCancelledEvent(sample_order, cancelled_by="user1")
        publisher.publish(event2)
        
        # Should still be 1 (didn't receive cancelled event)
        assert len(subscriber.events_received) == 1
    
    def test_multiple_subscribers(self, publisher, sample_order):
        """Test multiple subscribers"""
        subscriber1 = TestSubscriber()
        subscriber2 = TestSubscriber()
        
        publisher.subscribe(subscriber1)
        publisher.subscribe(subscriber2)
        
        event = OrderSubmittedEvent(sample_order)
        publisher.publish(event)
        
        assert len(subscriber1.events_received) == 1
        assert len(subscriber2.events_received) == 1
    
    def test_callback_decorator(self, publisher, sample_order):
        """Test callback decorator"""
        events_received = []
        
        @publisher.on(OrderEventType.SUBMITTED)
        def handle_submitted(event):
            events_received.append(event)
        
        event = OrderSubmittedEvent(sample_order)
        publisher.publish(event)
        
        assert len(events_received) == 1
        assert events_received[0] == event
    
    def test_global_callback(self, publisher, sample_order):
        """Test global callback"""
        events_received = []
        
        @publisher.on()
        def handle_all(event):
            events_received.append(event)
        
        event1 = OrderSubmittedEvent(sample_order)
        event2 = OrderCancelledEvent(sample_order, cancelled_by="user1")
        
        publisher.publish(event1)
        publisher.publish(event2)
        
        assert len(events_received) == 2
    
    def test_event_history(self, publisher, sample_order):
        """Test event history tracking"""
        event1 = OrderSubmittedEvent(sample_order)
        event2 = OrderCancelledEvent(sample_order, cancelled_by="user1")
        
        publisher.publish(event1)
        publisher.publish(event2)
        
        history = publisher.get_history()
        assert len(history) == 2
        assert history[0] == event1
        assert history[1] == event2
    
    def test_event_history_by_type(self, publisher, sample_order):
        """Test filtering event history by type"""
        event1 = OrderSubmittedEvent(sample_order)
        event2 = OrderCancelledEvent(sample_order, cancelled_by="user1")
        
        publisher.publish(event1)
        publisher.publish(event2)
        
        submitted_history = publisher.get_history(OrderEventType.SUBMITTED)
        assert len(submitted_history) == 1
        assert submitted_history[0].event_type == OrderEventType.SUBMITTED
    
    def test_event_history_limit(self, publisher, sample_order):
        """Test event history with limit"""
        for i in range(10):
            event = OrderSubmittedEvent(sample_order)
            publisher.publish(event)
        
        history = publisher.get_history(limit=5)
        assert len(history) == 5
    
    def test_event_history_max_size(self, sample_order):
        """Test event history respects max size"""
        publisher = EventPublisher(max_history=5)
        
        for i in range(10):
            event = OrderSubmittedEvent(sample_order)
            publisher.publish(event)
        
        history = publisher.get_history()
        assert len(history) == 5  # Only keeps last 5
    
    def test_get_events_for_order(self, publisher):
        """Test getting events for specific order"""
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
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            price=Decimal("51000"),
            quantity=Decimal("1.0")
        )
        
        event1 = OrderSubmittedEvent(order1)
        event2 = OrderSubmittedEvent(order2)
        event3 = OrderCancelledEvent(order1, cancelled_by="user1")
        
        publisher.publish(event1)
        publisher.publish(event2)
        publisher.publish(event3)
        
        order1_events = publisher.get_events_for_order(order1.order_id)
        assert len(order1_events) == 2
        assert all(e.order.order_id == order1.order_id for e in order1_events)
    
    def test_clear_history(self, publisher, sample_order):
        """Test clearing event history"""
        event = OrderSubmittedEvent(sample_order)
        publisher.publish(event)
        
        assert len(publisher.get_history()) == 1
        
        publisher.clear_history()
        assert len(publisher.get_history()) == 0
    
    def test_statistics(self, publisher, sample_order):
        """Test getting statistics"""
        event1 = OrderSubmittedEvent(sample_order)
        event2 = OrderCancelledEvent(sample_order, cancelled_by="user1")
        
        publisher.publish(event1)
        publisher.publish(event2)
        
        stats = publisher.get_statistics()
        
        assert stats["total_events"] == 2
        assert stats["event_counts"]["submitted"] == 1
        assert stats["event_counts"]["cancelled"] == 1
        assert stats["history_size"] == 2
    
    def test_reset_statistics(self, publisher, sample_order):
        """Test resetting statistics"""
        event = OrderSubmittedEvent(sample_order)
        publisher.publish(event)
        
        assert publisher._total_events == 1
        
        publisher.reset_statistics()
        assert publisher._total_events == 0
        assert len(publisher._event_counts) == 0
    
    @pytest.mark.asyncio
    async def test_publish_async(self, publisher, sample_order):
        """Test async event publishing"""
        subscriber = TestSubscriber()
        publisher.subscribe(subscriber)
        
        event = OrderSubmittedEvent(sample_order)
        await publisher.publish_async(event)
        
        assert len(subscriber.events_received) == 1
    
    def test_subscriber_error_handling(self, publisher, sample_order):
        """Test that subscriber errors don't break publishing"""
        
        class ErrorSubscriber(EventSubscriber):
            def on_event(self, event):
                raise Exception("Test error")
        
        good_subscriber = TestSubscriber()
        error_subscriber = ErrorSubscriber()
        
        publisher.subscribe(good_subscriber)
        publisher.subscribe(error_subscriber)
        
        event = OrderSubmittedEvent(sample_order)
        publisher.publish(event)  # Should not raise
        
        # Good subscriber should still receive event
        assert len(good_subscriber.events_received) == 1
