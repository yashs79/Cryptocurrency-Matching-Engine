"""
Unit tests for TradeManager
"""

import pytest
from decimal import Decimal
from datetime import datetime, UTC

from src.matching_engine.services import TradeManager, FeeConfig
from src.matching_engine.core.order import Order, OrderSide, OrderType
from src.matching_engine.core.trade import Trade, SettlementStatus
from src.matching_engine.repositories import TradeRepository
from src.matching_engine.events import EventPublisher
from src.matching_engine.config.database import init_db


class TestFeeConfig:
    """Test FeeConfig"""
    
    def test_default_fee_config(self):
        """Test default fee configuration"""
        config = FeeConfig()
        
        assert config.maker_fee_rate == Decimal("0.001")
        assert config.taker_fee_rate == Decimal("0.002")
        assert config.min_fee == Decimal("0.01")
        assert config.max_fee is None
    
    def test_custom_fee_config(self):
        """Test custom fee configuration"""
        config = FeeConfig(
            maker_fee_rate=Decimal("0.0005"),
            taker_fee_rate=Decimal("0.0015"),
            min_fee=Decimal("0.001"),
            max_fee=Decimal("100.0")
        )
        
        assert config.maker_fee_rate == Decimal("0.0005")
        assert config.taker_fee_rate == Decimal("0.0015")
        assert config.min_fee == Decimal("0.001")
        assert config.max_fee == Decimal("100.0")


class TestTradeManager:
    """Test TradeManager"""
    
    @pytest.fixture(autouse=True)
    def setup_db(self):
        """Setup test database"""
        init_db(database_url="sqlite:///:memory:", echo=False)
        yield
    
    @pytest.fixture
    def repository(self):
        """Create repository instance"""
        return TradeRepository()
    
    @pytest.fixture
    def event_publisher(self):
        """Create event publisher instance"""
        return EventPublisher()
    
    @pytest.fixture
    def fee_config(self):
        """Create fee config"""
        return FeeConfig(
            maker_fee_rate=Decimal("0.001"),
            taker_fee_rate=Decimal("0.002"),
            min_fee=Decimal("0.01")
        )
    
    @pytest.fixture
    def trade_manager(self, repository, event_publisher, fee_config):
        """Create trade manager instance"""
        return TradeManager(repository, event_publisher, fee_config)
    
    @pytest.fixture
    def buy_order(self):
        """Create sample buy order"""
        return Order(
            user_id='alice',
            symbol='BTC-USD',
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal('50000'),
            quantity=Decimal('1.0')
        )
    
    @pytest.fixture
    def sell_order(self):
        """Create sample sell order"""
        return Order(
            user_id='bob',
            symbol='BTC-USD',
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            price=Decimal('50000'),
            quantity=Decimal('1.0')
        )
    
    def test_create_trade(self, trade_manager, buy_order, sell_order):
        """Test creating a trade"""
        trade = trade_manager.create_trade(
            buy_order=buy_order,
            sell_order=sell_order,
            price=Decimal('50000'),
            quantity=Decimal('1.0'),
            maker_order=buy_order  # Buy order was in book first
        )
        
        assert trade.symbol == 'BTC-USD'
        assert trade.buyer_order_id == buy_order.order_id
        assert trade.seller_order_id == sell_order.order_id
        assert trade.buyer_user_id == 'alice'
        assert trade.seller_user_id == 'bob'
        assert trade.price == Decimal('50000')
        assert trade.quantity == Decimal('1.0')
        assert trade.maker_fee > 0
        assert trade.taker_fee > 0
        assert trade.settlement_status == SettlementStatus.PENDING
    
    def test_create_trade_with_maker_buy(self, trade_manager, buy_order, sell_order):
        """Test creating trade where buy order is maker"""
        trade = trade_manager.create_trade(
            buy_order=buy_order,
            sell_order=sell_order,
            price=Decimal('50000'),
            quantity=Decimal('1.0'),
            maker_order=buy_order
        )
        
        assert trade.metadata['maker_side'] == 'buy'
        assert trade.metadata['taker_side'] == 'sell'
    
    def test_create_trade_with_maker_sell(self, trade_manager, buy_order, sell_order):
        """Test creating trade where sell order is maker"""
        trade = trade_manager.create_trade(
            buy_order=buy_order,
            sell_order=sell_order,
            price=Decimal('50000'),
            quantity=Decimal('1.0'),
            maker_order=sell_order
        )
        
        assert trade.metadata['maker_side'] == 'sell'
        assert trade.metadata['taker_side'] == 'buy'
    
    def test_execute_trade(self, trade_manager, buy_order, sell_order):
        """Test executing a trade"""
        trade = trade_manager.execute_trade(
            buy_order=buy_order,
            sell_order=sell_order,
            price=Decimal('50000'),
            quantity=Decimal('1.0'),
            maker_order=buy_order
        )
        
        # Verify trade was created
        assert trade.trade_id is not None
        
        # Verify trade was saved
        retrieved = trade_manager.get_trade(trade.trade_id)
        assert retrieved is not None
        assert retrieved.trade_id == trade.trade_id
    
    def test_execute_trade_publishes_event(self, trade_manager, buy_order, sell_order):
        """Test that executing trade publishes event"""
        events_received = []
        
        def subscriber(event):
            events_received.append(event)
        
        trade_manager.event_publisher.subscribe('trade.executed', subscriber)
        
        trade = trade_manager.execute_trade(
            buy_order=buy_order,
            sell_order=sell_order,
            price=Decimal('50000'),
            quantity=Decimal('1.0'),
            maker_order=buy_order
        )
        
        assert len(events_received) == 1
        assert events_received[0].trade_id == trade.trade_id
    
    def test_settle_trade(self, trade_manager, buy_order, sell_order):
        """Test settling a trade"""
        # Execute trade
        trade = trade_manager.execute_trade(
            buy_order=buy_order,
            sell_order=sell_order,
            price=Decimal('50000'),
            quantity=Decimal('1.0'),
            maker_order=buy_order
        )
        
        # Settle trade
        result = trade_manager.settle_trade(trade.trade_id)
        
        assert result is True
        
        # Verify trade is settled
        retrieved = trade_manager.get_trade(trade.trade_id)
        assert retrieved.is_settled
        assert retrieved.settled_at is not None
    
    def test_settle_trade_publishes_event(self, trade_manager, buy_order, sell_order):
        """Test that settling trade publishes event"""
        events_received = []
        
        def subscriber(event):
            events_received.append(event)
        
        trade_manager.event_publisher.subscribe('trade.settled', subscriber)
        
        # Execute and settle trade
        trade = trade_manager.execute_trade(
            buy_order=buy_order,
            sell_order=sell_order,
            price=Decimal('50000'),
            quantity=Decimal('1.0'),
            maker_order=buy_order
        )
        
        trade_manager.settle_trade(trade.trade_id)
        
        assert len(events_received) == 1
        assert events_received[0].trade_id == trade.trade_id
    
    def test_settle_nonexistent_trade(self, trade_manager):
        """Test settling a trade that doesn't exist"""
        result = trade_manager.settle_trade('nonexistent-id')
        
        assert result is False
    
    def test_settle_already_settled_trade(self, trade_manager, buy_order, sell_order):
        """Test settling an already settled trade"""
        # Execute and settle trade
        trade = trade_manager.execute_trade(
            buy_order=buy_order,
            sell_order=sell_order,
            price=Decimal('50000'),
            quantity=Decimal('1.0'),
            maker_order=buy_order
        )
        
        trade_manager.settle_trade(trade.trade_id)
        
        # Try to settle again
        result = trade_manager.settle_trade(trade.trade_id)
        
        assert result is True  # Should return True but not change anything
    
    def test_fail_trade(self, trade_manager, buy_order, sell_order):
        """Test failing a trade"""
        # Execute trade
        trade = trade_manager.execute_trade(
            buy_order=buy_order,
            sell_order=sell_order,
            price=Decimal('50000'),
            quantity=Decimal('1.0'),
            maker_order=buy_order
        )
        
        # Fail trade
        result = trade_manager.fail_trade(trade.trade_id, "Insufficient funds")
        
        assert result is True
        
        # Verify trade is failed
        retrieved = trade_manager.get_trade(trade.trade_id)
        assert retrieved.is_failed
        # Note: metadata is not persisted to database yet
    
    def test_fail_trade_publishes_event(self, trade_manager, buy_order, sell_order):
        """Test that failing trade publishes event"""
        events_received = []
        
        def subscriber(event):
            events_received.append(event)
        
        trade_manager.event_publisher.subscribe('trade.failed', subscriber)
        
        # Execute and fail trade
        trade = trade_manager.execute_trade(
            buy_order=buy_order,
            sell_order=sell_order,
            price=Decimal('50000'),
            quantity=Decimal('1.0'),
            maker_order=buy_order
        )
        
        trade_manager.fail_trade(trade.trade_id, "Test failure")
        
        assert len(events_received) == 1
        assert events_received[0].trade_id == trade.trade_id
        assert events_received[0].reason == "Test failure"
    
    def test_cancel_trade(self, trade_manager, buy_order, sell_order):
        """Test cancelling a trade"""
        # Execute trade
        trade = trade_manager.execute_trade(
            buy_order=buy_order,
            sell_order=sell_order,
            price=Decimal('50000'),
            quantity=Decimal('1.0'),
            maker_order=buy_order
        )
        
        # Cancel trade
        result = trade_manager.cancel_trade(trade.trade_id, "User requested")
        
        assert result is True
        
        # Verify trade is cancelled
        retrieved = trade_manager.get_trade(trade.trade_id)
        assert retrieved.settlement_status == SettlementStatus.CANCELLED
    
    def test_cancel_trade_publishes_event(self, trade_manager, buy_order, sell_order):
        """Test that cancelling trade publishes event"""
        events_received = []
        
        def subscriber(event):
            events_received.append(event)
        
        trade_manager.event_publisher.subscribe('trade.cancelled', subscriber)
        
        # Execute and cancel trade
        trade = trade_manager.execute_trade(
            buy_order=buy_order,
            sell_order=sell_order,
            price=Decimal('50000'),
            quantity=Decimal('1.0'),
            maker_order=buy_order
        )
        
        trade_manager.cancel_trade(trade.trade_id, "Test cancellation")
        
        assert len(events_received) == 1
        assert events_received[0].trade_id == trade.trade_id
        assert events_received[0].reason == "Test cancellation"
    
    def test_get_trade_history_by_user(self, trade_manager, buy_order, sell_order):
        """Test getting trade history by user"""
        # Execute multiple trades
        for i in range(3):
            trade_manager.execute_trade(
                buy_order=buy_order,
                sell_order=sell_order,
                price=Decimal('50000'),
                quantity=Decimal('1.0'),
                maker_order=buy_order
            )
        
        # Get alice's trades
        alice_trades = trade_manager.get_trade_history(user_id='alice')
        
        assert len(alice_trades) == 3
        assert all(t.buyer_user_id == 'alice' or t.seller_user_id == 'alice' for t in alice_trades)
    
    def test_get_trade_history_by_symbol(self, trade_manager, buy_order, sell_order):
        """Test getting trade history by symbol"""
        # Execute trades
        trade_manager.execute_trade(
            buy_order=buy_order,
            sell_order=sell_order,
            price=Decimal('50000'),
            quantity=Decimal('1.0'),
            maker_order=buy_order
        )
        
        # Get BTC-USD trades
        btc_trades = trade_manager.get_trade_history(symbol='BTC-USD')
        
        assert len(btc_trades) == 1
        assert btc_trades[0].symbol == 'BTC-USD'
    
    def test_get_user_volume(self, trade_manager, buy_order, sell_order):
        """Test getting user trading volume"""
        # Execute trades and settle them
        for i in range(3):
            trade = trade_manager.execute_trade(
                buy_order=buy_order,
                sell_order=sell_order,
                price=Decimal('50000'),
                quantity=Decimal('1.0'),
                maker_order=buy_order
            )
            trade_manager.settle_trade(trade.trade_id)
        
        # Get alice's volume
        volume = trade_manager.get_user_volume('alice')
        
        assert volume == Decimal('3.0')
    
    def test_get_symbol_volume(self, trade_manager, buy_order, sell_order):
        """Test getting symbol trading volume"""
        # Execute trades and settle them
        for i in range(2):
            trade = trade_manager.execute_trade(
                buy_order=buy_order,
                sell_order=sell_order,
                price=Decimal('50000'),
                quantity=Decimal('1.5'),
                maker_order=buy_order
            )
            trade_manager.settle_trade(trade.trade_id)
        
        # Get BTC-USD volume
        volume = trade_manager.get_symbol_volume('BTC-USD')
        
        assert volume == Decimal('3.0')
    
    def test_get_statistics(self, trade_manager, buy_order, sell_order):
        """Test getting trade statistics"""
        # Execute some trades
        for i in range(5):
            trade = trade_manager.execute_trade(
                buy_order=buy_order,
                sell_order=sell_order,
                price=Decimal('50000'),
                quantity=Decimal('1.0'),
                maker_order=buy_order
            )
            if i < 3:
                trade_manager.settle_trade(trade.trade_id)
        
        stats = trade_manager.get_statistics()
        
        assert stats['total_trades'] == 5
        assert stats['status_breakdown']['settled'] == 3
        assert stats['status_breakdown']['pending'] == 2
    
    def test_fee_calculation_maker(self, trade_manager):
        """Test fee calculation for maker"""
        fee = trade_manager._calculate_fee(
            price=Decimal('50000'),
            quantity=Decimal('1.0'),
            is_maker=True
        )
        
        # 50000 * 1.0 * 0.001 = 50
        assert fee == Decimal('50.0')
    
    def test_fee_calculation_taker(self, trade_manager):
        """Test fee calculation for taker"""
        fee = trade_manager._calculate_fee(
            price=Decimal('50000'),
            quantity=Decimal('1.0'),
            is_maker=False
        )
        
        # 50000 * 1.0 * 0.002 = 100
        assert fee == Decimal('100.0')
    
    def test_fee_calculation_minimum(self, trade_manager):
        """Test minimum fee is applied"""
        fee = trade_manager._calculate_fee(
            price=Decimal('1.0'),
            quantity=Decimal('0.001'),
            is_maker=True
        )
        
        # Trade value = 0.001, fee would be 0.000001, but min is 0.01
        assert fee == Decimal('0.01')
    
    def test_fee_calculation_maximum(self):
        """Test maximum fee is applied"""
        fee_config = FeeConfig(
            maker_fee_rate=Decimal('0.001'),
            max_fee=Decimal('50.0')
        )
        manager = TradeManager(fee_config=fee_config)
        
        fee = manager._calculate_fee(
            price=Decimal('100000'),
            quantity=Decimal('1.0'),
            is_maker=True
        )
        
        # Fee would be 100, but max is 50
        assert fee == Decimal('50.0')
