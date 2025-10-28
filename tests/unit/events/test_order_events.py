"""
Tests for Order Events
"""

import pytest
from decimal import Decimal
from datetime import datetime, UTC

from src.matching_engine.core.order import Order, OrderSide, OrderType, OrderStatus
from src.matching_engine.core.matching_engine import Trade
from src.matching_engine.events.order_events import (
    OrderEvent,
    OrderEventType,
    OrderSubmittedEvent,
    OrderCancelledEvent,
    OrderFilledEvent,
    OrderPartiallyFilledEvent,
    OrderRejectedEvent,
    OrderAmendedEvent,
    OrderExpiredEvent,
)


class TestOrderEvents:
    """Test order event classes"""
    
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
    
    @pytest.fixture
    def sample_trades(self, sample_order):
        """Create sample trades"""
        return [
            Trade(
                trade_id="trade1",
                symbol="BTC-USD",
                buyer_order_id=sample_order.order_id,
                seller_order_id="seller1",
                price=Decimal("50000"),
                quantity=Decimal("0.5"),
                timestamp=datetime.now(UTC)
            ),
            Trade(
                trade_id="trade2",
                symbol="BTC-USD",
                buyer_order_id=sample_order.order_id,
                seller_order_id="seller2",
                price=Decimal("50100"),
                quantity=Decimal("0.5"),
                timestamp=datetime.now(UTC)
            ),
        ]
    
    def test_order_submitted_event(self, sample_order):
        """Test OrderSubmittedEvent"""
        event = OrderSubmittedEvent(sample_order)
        
        assert event.event_type == OrderEventType.SUBMITTED
        assert event.order == sample_order
        assert event.timestamp is not None
        assert isinstance(event.metadata, dict)
        
        # Test to_dict
        data = event.to_dict()
        assert data["event_type"] == "submitted"
        assert data["order_id"] == sample_order.order_id
        assert data["user_id"] == "user1"
        assert data["symbol"] == "BTC-USD"
    
    def test_order_cancelled_event(self, sample_order):
        """Test OrderCancelledEvent"""
        event = OrderCancelledEvent(
            sample_order,
            cancelled_by="user1",
            reason="User requested"
        )
        
        assert event.event_type == OrderEventType.CANCELLED
        assert event.cancelled_by == "user1"
        assert event.reason == "User requested"
        
        # Test to_dict
        data = event.to_dict()
        assert data["event_type"] == "cancelled"
        assert data["cancelled_by"] == "user1"
        assert data["reason"] == "User requested"
    
    def test_order_filled_event(self, sample_order, sample_trades):
        """Test OrderFilledEvent"""
        sample_order.status = OrderStatus.FILLED
        sample_order.filled_quantity = Decimal("1.0")
        
        event = OrderFilledEvent(sample_order, sample_trades)
        
        assert event.event_type == OrderEventType.FILLED
        assert len(event.trades) == 2
        assert event.total_filled == Decimal("1.0")
        assert event.average_price == Decimal("50050")  # (50000*0.5 + 50100*0.5) / 1.0
        
        # Test to_dict
        data = event.to_dict()
        assert data["event_type"] == "filled"
        assert data["trade_count"] == 2
        assert data["total_filled"] == "1.0"
        assert "trades" in data
    
    def test_order_partially_filled_event(self, sample_order, sample_trades):
        """Test OrderPartiallyFilledEvent"""
        sample_order.status = OrderStatus.PARTIALLY_FILLED
        sample_order.filled_quantity = Decimal("0.5")
        
        event = OrderPartiallyFilledEvent(sample_order, [sample_trades[0]])
        
        assert event.event_type == OrderEventType.PARTIALLY_FILLED
        assert event.filled_quantity == Decimal("0.5")
        assert event.remaining_quantity == Decimal("0.5")
        
        # Test to_dict
        data = event.to_dict()
        assert data["event_type"] == "partially_filled"
        assert data["filled_quantity"] == "0.5"
        assert data["remaining_quantity"] == "0.5"
    
    def test_order_rejected_event(self, sample_order):
        """Test OrderRejectedEvent"""
        event = OrderRejectedEvent(
            sample_order,
            reason="Insufficient balance",
            error_code="ERR_BALANCE"
        )
        
        assert event.event_type == OrderEventType.REJECTED
        assert event.reason == "Insufficient balance"
        assert event.error_code == "ERR_BALANCE"
        
        # Test to_dict
        data = event.to_dict()
        assert data["event_type"] == "rejected"
        assert data["reason"] == "Insufficient balance"
        assert data["error_code"] == "ERR_BALANCE"
    
    def test_order_amended_event(self, sample_order):
        """Test OrderAmendedEvent"""
        old_price = Decimal("50000")
        old_quantity = Decimal("1.0")
        
        # Amend order
        sample_order.price = Decimal("51000")
        sample_order.quantity = Decimal("2.0")
        
        event = OrderAmendedEvent(
            sample_order,
            old_order_id="old_order_123",
            old_price=old_price,
            old_quantity=old_quantity
        )
        
        assert event.event_type == OrderEventType.AMENDED
        assert event.old_order_id == "old_order_123"
        assert event.old_price == Decimal("50000")
        assert event.old_quantity == Decimal("1.0")
        assert event.new_price == Decimal("51000")
        assert event.new_quantity == Decimal("2.0")
        
        # Test to_dict
        data = event.to_dict()
        assert data["event_type"] == "amended"
        assert data["old_price"] == "50000"
        assert data["new_price"] == "51000"
    
    def test_order_expired_event(self, sample_order):
        """Test OrderExpiredEvent"""
        expiry_time = datetime.now(UTC)
        event = OrderExpiredEvent(sample_order, expiry_time)
        
        assert event.event_type == OrderEventType.EXPIRED
        assert event.expiry_time == expiry_time
        
        # Test to_dict
        data = event.to_dict()
        assert data["event_type"] == "expired"
        assert "expiry_time" in data
    
    def test_event_with_metadata(self, sample_order):
        """Test event with custom metadata"""
        metadata = {"source": "api", "ip": "127.0.0.1"}
        event = OrderSubmittedEvent(sample_order, metadata=metadata)
        
        assert event.metadata == metadata
        
        data = event.to_dict()
        assert data["metadata"] == metadata
