"""
Integration tests for end-to-end trade execution flow
"""

import pytest
from decimal import Decimal
from datetime import datetime, UTC

from src.matching_engine.core.matching_engine import MatchingEngine
from src.matching_engine.core.order import Order, OrderSide, OrderType
from src.matching_engine.services import TradeManager, FeeConfig
from src.matching_engine.repositories import TradeRepository
from src.matching_engine.events import EventPublisher
from src.matching_engine.config.database import init_db


class TestTradeExecutionFlow:
    """Test end-to-end trade execution flow"""
    
    @pytest.fixture(autouse=True)
    def setup_db(self):
        """Setup test database"""
        init_db(database_url="sqlite:///:memory:", echo=False)
        yield
    
    @pytest.fixture
    def matching_engine(self):
        """Create matching engine"""
        return MatchingEngine()
    
    @pytest.fixture
    def trade_manager(self):
        """Create trade manager"""
        return TradeManager()
    
    def test_complete_trade_flow(self, matching_engine, trade_manager):
        """Test complete trade execution flow"""
        # Create buy order
        buy_order = Order(
            user_id='alice',
            symbol='BTC-USD',
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal('50000'),
            quantity=Decimal('1.0')
        )
        
        # Create sell order
        sell_order = Order(
            user_id='bob',
            symbol='BTC-USD',
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            price=Decimal('50000'),
            quantity=Decimal('1.0')
        )
        
        # Process orders through matching engine
        processed_buy, buy_trades = matching_engine.process_order(buy_order)
        assert len(buy_trades) == 0  # No match yet
        
        processed_sell, sell_trades = matching_engine.process_order(sell_order)
        assert len(sell_trades) == 1  # Match occurred
        
        # Get the trade from matching engine
        engine_trade = sell_trades[0]
        
        # Execute trade through trade manager
        managed_trade = trade_manager.execute_trade(
            buy_order=buy_order,
            sell_order=sell_order,
            price=engine_trade.price,
            quantity=engine_trade.quantity,
            maker_order=buy_order  # Buy was in book first
        )
        
        # Verify trade was created and saved
        assert managed_trade.trade_id is not None
        assert managed_trade.buyer_user_id == 'alice'
        assert managed_trade.seller_user_id == 'bob'
        assert managed_trade.price == Decimal('50000')
        assert managed_trade.quantity == Decimal('1.0')
        assert managed_trade.maker_fee > 0
        assert managed_trade.taker_fee > 0
        
        # Verify trade can be retrieved
        retrieved = trade_manager.get_trade(managed_trade.trade_id)
        assert retrieved is not None
        assert retrieved.trade_id == managed_trade.trade_id
    
    def test_partial_fill_trade_flow(self, matching_engine, trade_manager):
        """Test trade flow with partial fills"""
        # Create large buy order
        buy_order = Order(
            user_id='alice',
            symbol='BTC-USD',
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal('50000'),
            quantity=Decimal('5.0')
        )
        
        # Create smaller sell order
        sell_order = Order(
            user_id='bob',
            symbol='BTC-USD',
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            price=Decimal('50000'),
            quantity=Decimal('2.0')
        )
        
        # Process orders
        matching_engine.process_order(buy_order)
        _, trades = matching_engine.process_order(sell_order)
        
        assert len(trades) == 1
        assert trades[0].quantity == Decimal('2.0')
        
        # Execute trade through manager
        managed_trade = trade_manager.execute_trade(
            buy_order=buy_order,
            sell_order=sell_order,
            price=trades[0].price,
            quantity=trades[0].quantity,
            maker_order=buy_order
        )
        
        # Verify partial fill
        assert managed_trade.quantity == Decimal('2.0')
        assert buy_order.remaining_quantity == Decimal('3.0')
        assert sell_order.remaining_quantity == Decimal('0')
    
    def test_multiple_trades_same_symbol(self, matching_engine, trade_manager):
        """Test multiple trades for same symbol"""
        trades_executed = []
        
        # Create multiple buy orders
        for i in range(3):
            buy_order = Order(
                user_id=f'buyer{i}',
                symbol='BTC-USD',
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                price=Decimal('50000'),
                quantity=Decimal('1.0')
            )
            matching_engine.process_order(buy_order)
        
        # Create sell order that matches all
        sell_order = Order(
            user_id='seller',
            symbol='BTC-USD',
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            price=Decimal('50000'),
            quantity=Decimal('3.0')
        )
        
        _, trades = matching_engine.process_order(sell_order)
        
        assert len(trades) == 3
        
        # Execute all trades through manager
        for trade in trades:
            # Find corresponding buy order
            order_book = matching_engine.order_books['BTC-USD']
            buy_order = None
            for order_id in [trade.buyer_order_id]:
                if order_id in order_book.orders:
                    buy_order = order_book.orders[order_id]
                    break
            
            if not buy_order:
                # Order was filled and removed, create a dummy for the test
                buy_order = Order(
                    user_id=trade.buyer_user_id if hasattr(trade, 'buyer_user_id') else 'buyer',
                    symbol='BTC-USD',
                    side=OrderSide.BUY,
                    order_type=OrderType.LIMIT,
                    price=Decimal('50000'),
                    quantity=Decimal('1.0')
                )
                buy_order.order_id = trade.buyer_order_id
            
            managed_trade = trade_manager.execute_trade(
                buy_order=buy_order,
                sell_order=sell_order,
                price=trade.price,
                quantity=trade.quantity,
                maker_order=buy_order
            )
            trades_executed.append(managed_trade)
        
        assert len(trades_executed) == 3
        
        # Verify all trades are in database
        btc_trades = trade_manager.get_trade_history(symbol='BTC-USD')
        assert len(btc_trades) >= 3
    
    def test_trade_settlement_flow(self, matching_engine, trade_manager):
        """Test trade settlement flow"""
        # Create and match orders
        buy_order = Order(
            user_id='alice',
            symbol='BTC-USD',
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal('50000'),
            quantity=Decimal('1.0')
        )
        
        sell_order = Order(
            user_id='bob',
            symbol='BTC-USD',
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            price=Decimal('50000'),
            quantity=Decimal('1.0')
        )
        
        matching_engine.process_order(buy_order)
        _, trades = matching_engine.process_order(sell_order)
        
        # Execute trade
        managed_trade = trade_manager.execute_trade(
            buy_order=buy_order,
            sell_order=sell_order,
            price=trades[0].price,
            quantity=trades[0].quantity,
            maker_order=buy_order
        )
        
        # Verify trade is pending
        assert managed_trade.is_pending
        
        # Settle trade
        result = trade_manager.settle_trade(managed_trade.trade_id)
        assert result is True
        
        # Verify trade is settled
        settled_trade = trade_manager.get_trade(managed_trade.trade_id)
        assert settled_trade.is_settled
        assert settled_trade.settled_at is not None
    
    def test_trade_events_published(self, matching_engine, trade_manager):
        """Test that trade events are published"""
        events_received = []
        
        def event_subscriber(event):
            events_received.append(event)
        
        # Subscribe to trade events
        trade_manager.event_publisher.subscribe('trade.executed', event_subscriber)
        
        # Create and match orders
        buy_order = Order(
            user_id='alice',
            symbol='BTC-USD',
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal('50000'),
            quantity=Decimal('1.0')
        )
        
        sell_order = Order(
            user_id='bob',
            symbol='BTC-USD',
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            price=Decimal('50000'),
            quantity=Decimal('1.0')
        )
        
        matching_engine.process_order(buy_order)
        _, trades = matching_engine.process_order(sell_order)
        
        # Execute trade
        trade_manager.execute_trade(
            buy_order=buy_order,
            sell_order=sell_order,
            price=trades[0].price,
            quantity=trades[0].quantity,
            maker_order=buy_order
        )
        
        # Verify event was published
        assert len(events_received) == 1
        assert events_received[0].event_type == 'trade.executed'
    
    def test_fee_calculation_in_flow(self, matching_engine):
        """Test fee calculation in trade flow"""
        # Create trade manager with custom fees
        fee_config = FeeConfig(
            maker_fee_rate=Decimal('0.001'),  # 0.1%
            taker_fee_rate=Decimal('0.002')   # 0.2%
        )
        trade_manager = TradeManager(fee_config=fee_config)
        
        # Create and match orders
        buy_order = Order(
            user_id='alice',
            symbol='BTC-USD',
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal('50000'),
            quantity=Decimal('1.0')
        )
        
        sell_order = Order(
            user_id='bob',
            symbol='BTC-USD',
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            price=Decimal('50000'),
            quantity=Decimal('1.0')
        )
        
        matching_engine.process_order(buy_order)
        _, trades = matching_engine.process_order(sell_order)
        
        # Execute trade
        managed_trade = trade_manager.execute_trade(
            buy_order=buy_order,
            sell_order=sell_order,
            price=trades[0].price,
            quantity=trades[0].quantity,
            maker_order=buy_order
        )
        
        # Verify fees
        # Trade value = 50000 * 1.0 = 50000
        # Maker fee = 50000 * 0.001 = 50
        # Taker fee = 50000 * 0.002 = 100
        assert managed_trade.maker_fee == Decimal('50.0')
        assert managed_trade.taker_fee == Decimal('100.0')
        assert managed_trade.total_fees == Decimal('150.0')
    
    def test_user_volume_tracking(self, matching_engine, trade_manager):
        """Test user volume tracking across multiple trades"""
        # Execute multiple trades for same user
        for i in range(3):
            buy_order = Order(
                user_id='alice',
                symbol='BTC-USD',
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                price=Decimal('50000'),
                quantity=Decimal('1.0')
            )
            
            sell_order = Order(
                user_id='bob',
                symbol='BTC-USD',
                side=OrderSide.SELL,
                order_type=OrderType.LIMIT,
                price=Decimal('50000'),
                quantity=Decimal('1.0')
            )
            
            matching_engine.process_order(buy_order)
            _, trades = matching_engine.process_order(sell_order)
            
            # Execute and settle trade
            managed_trade = trade_manager.execute_trade(
                buy_order=buy_order,
                sell_order=sell_order,
                price=trades[0].price,
                quantity=trades[0].quantity,
                maker_order=buy_order
            )
            trade_manager.settle_trade(managed_trade.trade_id)
        
        # Check alice's volume
        alice_volume = trade_manager.get_user_volume('alice')
        assert alice_volume == Decimal('3.0')
        
        # Check bob's volume
        bob_volume = trade_manager.get_user_volume('bob')
        assert bob_volume == Decimal('3.0')
