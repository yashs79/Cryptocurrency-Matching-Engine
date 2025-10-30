"""
Unit tests for Trade Events
"""

import pytest
from decimal import Decimal
from datetime import datetime, UTC

from src.matching_engine.events import (
    TradeExecutedEvent,
    TradeSettledEvent,
    TradeFailedEvent,
    TradeCancelledEvent,
    EventPublisher
)
from src.matching_engine.core.trade import SettlementStatus


class TestTradeExecutedEvent:
    """Test TradeExecutedEvent"""
    
    def test_create_trade_executed_event(self):
        """Test creating a trade executed event"""
        now = datetime.now(UTC)
        
        event = TradeExecutedEvent(
            trade_id='trade-123',
            symbol='BTC-USD',
            buyer_order_id='buy-123',
            seller_order_id='sell-456',
            buyer_user_id='alice',
            seller_user_id='bob',
            price=Decimal('50000.00'),
            quantity=Decimal('1.5'),
            timestamp=now
        )
        
        assert event.trade_id == 'trade-123'
        assert event.symbol == 'BTC-USD'
        assert event.buyer_order_id == 'buy-123'
        assert event.seller_order_id == 'sell-456'
        assert event.buyer_user_id == 'alice'
        assert event.seller_user_id == 'bob'
        assert event.price == Decimal('50000.00')
        assert event.quantity == Decimal('1.5')
        assert event.timestamp == now
    
    def test_event_type(self):
        """Test event type property"""
        event = TradeExecutedEvent(
            trade_id='trade-123',
            symbol='BTC-USD',
            buyer_order_id='buy-123',
            seller_order_id='sell-456',
            buyer_user_id='alice',
            seller_user_id='bob',
            price=Decimal('50000.00'),
            quantity=Decimal('1.5'),
            timestamp=datetime.now(UTC)
        )
        
        assert event.event_type == 'trade.executed'
    
    def test_to_dict(self):
        """Test converting event to dictionary"""
        now = datetime.now(UTC)
        
        event = TradeExecutedEvent(
            trade_id='trade-123',
            symbol='BTC-USD',
            buyer_order_id='buy-123',
            seller_order_id='sell-456',
            buyer_user_id='alice',
            seller_user_id='bob',
            price=Decimal('50000.00'),
            quantity=Decimal('1.5'),
            timestamp=now
        )
        
        event_dict = event.to_dict()
        
        assert event_dict['event_type'] == 'trade.executed'
        assert event_dict['trade_id'] == 'trade-123'
        assert event_dict['symbol'] == 'BTC-USD'
        assert event_dict['buyer_order_id'] == 'buy-123'
        assert event_dict['seller_order_id'] == 'sell-456'
        assert event_dict['buyer_user_id'] == 'alice'
        assert event_dict['seller_user_id'] == 'bob'
        assert Decimal(event_dict['price']) == Decimal('50000.00')
        assert Decimal(event_dict['quantity']) == Decimal('1.5')
        assert Decimal(event_dict['total_value']) == Decimal('75000.00')
        assert event_dict['timestamp'] == now.isoformat()


class TestTradeSettledEvent:
    """Test TradeSettledEvent"""
    
    def test_create_trade_settled_event(self):
        """Test creating a trade settled event"""
        now = datetime.now(UTC)
        
        event = TradeSettledEvent(
            trade_id='trade-123',
            symbol='BTC-USD',
            buyer_user_id='alice',
            seller_user_id='bob',
            settlement_status=SettlementStatus.SETTLED,
            settled_at=now
        )
        
        assert event.trade_id == 'trade-123'
        assert event.symbol == 'BTC-USD'
        assert event.buyer_user_id == 'alice'
        assert event.seller_user_id == 'bob'
        assert event.settlement_status == SettlementStatus.SETTLED
        assert event.settled_at == now
    
    def test_event_type(self):
        """Test event type property"""
        event = TradeSettledEvent(
            trade_id='trade-123',
            symbol='BTC-USD',
            buyer_user_id='alice',
            seller_user_id='bob',
            settlement_status=SettlementStatus.SETTLED,
            settled_at=datetime.now(UTC)
        )
        
        assert event.event_type == 'trade.settled'
    
    def test_to_dict(self):
        """Test converting event to dictionary"""
        now = datetime.now(UTC)
        
        event = TradeSettledEvent(
            trade_id='trade-123',
            symbol='BTC-USD',
            buyer_user_id='alice',
            seller_user_id='bob',
            settlement_status=SettlementStatus.SETTLED,
            settled_at=now
        )
        
        event_dict = event.to_dict()
        
        assert event_dict['event_type'] == 'trade.settled'
        assert event_dict['trade_id'] == 'trade-123'
        assert event_dict['symbol'] == 'BTC-USD'
        assert event_dict['buyer_user_id'] == 'alice'
        assert event_dict['seller_user_id'] == 'bob'
        assert event_dict['settlement_status'] == 'settled'
        assert event_dict['settled_at'] == now.isoformat()


class TestTradeFailedEvent:
    """Test TradeFailedEvent"""
    
    def test_create_trade_failed_event(self):
        """Test creating a trade failed event"""
        now = datetime.now(UTC)
        
        event = TradeFailedEvent(
            trade_id='trade-123',
            symbol='BTC-USD',
            buyer_user_id='alice',
            seller_user_id='bob',
            reason='Insufficient funds',
            timestamp=now
        )
        
        assert event.trade_id == 'trade-123'
        assert event.symbol == 'BTC-USD'
        assert event.buyer_user_id == 'alice'
        assert event.seller_user_id == 'bob'
        assert event.reason == 'Insufficient funds'
        assert event.timestamp == now
    
    def test_event_type(self):
        """Test event type property"""
        event = TradeFailedEvent(
            trade_id='trade-123',
            symbol='BTC-USD',
            buyer_user_id='alice',
            seller_user_id='bob',
            reason='Insufficient funds',
            timestamp=datetime.now(UTC)
        )
        
        assert event.event_type == 'trade.failed'
    
    def test_to_dict(self):
        """Test converting event to dictionary"""
        now = datetime.now(UTC)
        
        event = TradeFailedEvent(
            trade_id='trade-123',
            symbol='BTC-USD',
            buyer_user_id='alice',
            seller_user_id='bob',
            reason='Insufficient funds',
            timestamp=now
        )
        
        event_dict = event.to_dict()
        
        assert event_dict['event_type'] == 'trade.failed'
        assert event_dict['trade_id'] == 'trade-123'
        assert event_dict['symbol'] == 'BTC-USD'
        assert event_dict['buyer_user_id'] == 'alice'
        assert event_dict['seller_user_id'] == 'bob'
        assert event_dict['reason'] == 'Insufficient funds'
        assert event_dict['timestamp'] == now.isoformat()


class TestTradeCancelledEvent:
    """Test TradeCancelledEvent"""
    
    def test_create_trade_cancelled_event(self):
        """Test creating a trade cancelled event"""
        now = datetime.now(UTC)
        
        event = TradeCancelledEvent(
            trade_id='trade-123',
            symbol='BTC-USD',
            buyer_user_id='alice',
            seller_user_id='bob',
            reason='User requested',
            timestamp=now
        )
        
        assert event.trade_id == 'trade-123'
        assert event.symbol == 'BTC-USD'
        assert event.buyer_user_id == 'alice'
        assert event.seller_user_id == 'bob'
        assert event.reason == 'User requested'
        assert event.timestamp == now
    
    def test_event_type(self):
        """Test event type property"""
        event = TradeCancelledEvent(
            trade_id='trade-123',
            symbol='BTC-USD',
            buyer_user_id='alice',
            seller_user_id='bob',
            reason='User requested',
            timestamp=datetime.now(UTC)
        )
        
        assert event.event_type == 'trade.cancelled'
    
    def test_to_dict(self):
        """Test converting event to dictionary"""
        now = datetime.now(UTC)
        
        event = TradeCancelledEvent(
            trade_id='trade-123',
            symbol='BTC-USD',
            buyer_user_id='alice',
            seller_user_id='bob',
            reason='User requested',
            timestamp=now
        )
        
        event_dict = event.to_dict()
        
        assert event_dict['event_type'] == 'trade.cancelled'
        assert event_dict['trade_id'] == 'trade-123'
        assert event_dict['symbol'] == 'BTC-USD'
        assert event_dict['buyer_user_id'] == 'alice'
        assert event_dict['seller_user_id'] == 'bob'
        assert event_dict['reason'] == 'User requested'
        assert event_dict['timestamp'] == now.isoformat()


class TestTradeEventPublishing:
    """Test publishing trade events"""
    
    def test_publish_trade_executed_event(self):
        """Test publishing a trade executed event"""
        publisher = EventPublisher()
        events_received = []
        
        def subscriber(event):
            events_received.append(event)
        
        publisher.subscribe('trade.executed', subscriber)
        
        event = TradeExecutedEvent(
            trade_id='trade-123',
            symbol='BTC-USD',
            buyer_order_id='buy-123',
            seller_order_id='sell-456',
            buyer_user_id='alice',
            seller_user_id='bob',
            price=Decimal('50000.00'),
            quantity=Decimal('1.5'),
            timestamp=datetime.now(UTC)
        )
        
        publisher.publish(event)
        
        assert len(events_received) == 1
        assert events_received[0] == event
    
    def test_publish_trade_settled_event(self):
        """Test publishing a trade settled event"""
        publisher = EventPublisher()
        events_received = []
        
        def subscriber(event):
            events_received.append(event)
        
        publisher.subscribe('trade.settled', subscriber)
        
        event = TradeSettledEvent(
            trade_id='trade-123',
            symbol='BTC-USD',
            buyer_user_id='alice',
            seller_user_id='bob',
            settlement_status=SettlementStatus.SETTLED,
            settled_at=datetime.now(UTC)
        )
        
        publisher.publish(event)
        
        assert len(events_received) == 1
        assert events_received[0] == event
    
    def test_multiple_subscribers(self):
        """Test multiple subscribers for trade events"""
        publisher = EventPublisher()
        events_received_1 = []
        events_received_2 = []
        
        def subscriber1(event):
            events_received_1.append(event)
        
        def subscriber2(event):
            events_received_2.append(event)
        
        publisher.subscribe('trade.executed', subscriber1)
        publisher.subscribe('trade.executed', subscriber2)
        
        event = TradeExecutedEvent(
            trade_id='trade-123',
            symbol='BTC-USD',
            buyer_order_id='buy-123',
            seller_order_id='sell-456',
            buyer_user_id='alice',
            seller_user_id='bob',
            price=Decimal('50000.00'),
            quantity=Decimal('1.5'),
            timestamp=datetime.now(UTC)
        )
        
        publisher.publish(event)
        
        assert len(events_received_1) == 1
        assert len(events_received_2) == 1
        assert events_received_1[0] == event
        assert events_received_2[0] == event
    
    def test_unsubscribe_from_trade_events(self):
        """Test unsubscribing from trade events"""
        publisher = EventPublisher()
        events_received = []
        
        def subscriber(event):
            events_received.append(event)
        
        publisher.subscribe('trade.executed', subscriber)
        publisher.unsubscribe('trade.executed', subscriber)
        
        event = TradeExecutedEvent(
            trade_id='trade-123',
            symbol='BTC-USD',
            buyer_order_id='buy-123',
            seller_order_id='sell-456',
            buyer_user_id='alice',
            seller_user_id='bob',
            price=Decimal('50000.00'),
            quantity=Decimal('1.5'),
            timestamp=datetime.now(UTC)
        )
        
        publisher.publish(event)
        
        assert len(events_received) == 0
