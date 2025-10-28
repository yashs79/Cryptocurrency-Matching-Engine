"""
Unit tests for MatchingEngine class.
"""

import pytest
from decimal import Decimal

from src.matching_engine.core.order import Order, OrderSide, OrderType, OrderStatus
from src.matching_engine.core.matching_engine import MatchingEngine, Trade


class TestTrade:
    """Test Trade class"""
    
    def test_create_trade(self):
        """Test creating a trade"""
        trade = Trade(
            symbol="BTC-USD",
            buyer_order_id="buy123",
            seller_order_id="sell456",
            price=Decimal("50000"),
            quantity=Decimal("1.5")
        )
        
        assert trade.symbol == "BTC-USD"
        assert trade.buyer_order_id == "buy123"
        assert trade.seller_order_id == "sell456"
        assert trade.price == Decimal("50000")
        assert trade.quantity == Decimal("1.5")
        assert trade.trade_id is not None
    
    def test_trade_to_dict(self):
        """Test converting trade to dictionary"""
        trade = Trade(
            symbol="BTC-USD",
            buyer_order_id="buy123",
            seller_order_id="sell456",
            price=Decimal("50000"),
            quantity=Decimal("1.5")
        )
        
        trade_dict = trade.to_dict()
        assert trade_dict['symbol'] == "BTC-USD"
        assert trade_dict['price'] == "50000"
        assert trade_dict['quantity'] == "1.5"


class TestMatchingEngine:
    """Test MatchingEngine class"""
    
    def test_create_matching_engine(self):
        """Test creating a matching engine"""
        engine = MatchingEngine()
        assert len(engine.order_books) == 0
        assert len(engine.trades) == 0
        assert engine.total_trades == 0
    
    def test_get_or_create_order_book(self):
        """Test getting or creating order book"""
        engine = MatchingEngine()
        
        book1 = engine.get_or_create_order_book("BTC-USD")
        assert book1.symbol == "BTC-USD"
        
        book2 = engine.get_or_create_order_book("BTC-USD")
        assert book1 is book2  # Same instance
    
    def test_process_limit_order_no_match(self):
        """Test processing a limit order with no match"""
        engine = MatchingEngine()
        
        order = Order(
            user_id="user1",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1.0")
        )
        
        processed_order, trades = engine.process_order(order)
        
        assert processed_order.status == OrderStatus.OPEN
        assert len(trades) == 0
        assert engine.total_trades == 0
    
    def test_process_limit_order_full_match(self):
        """Test processing a limit order with full match"""
        engine = MatchingEngine()
        
        # Add a sell order first
        sell_order = Order(
            user_id="seller",
            symbol="BTC-USD",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1.0")
        )
        engine.process_order(sell_order)
        
        # Add a matching buy order
        buy_order = Order(
            user_id="buyer",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1.0")
        )
        
        processed_order, trades = engine.process_order(buy_order)
        
        assert processed_order.status == OrderStatus.FILLED
        assert len(trades) == 1
        assert trades[0].quantity == Decimal("1.0")
        assert trades[0].price == Decimal("50000")
        assert engine.total_trades == 1
    
    def test_process_limit_order_partial_match(self):
        """Test processing a limit order with partial match"""
        engine = MatchingEngine()
        
        # Add a sell order
        sell_order = Order(
            user_id="seller",
            symbol="BTC-USD",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("0.5")
        )
        engine.process_order(sell_order)
        
        # Add a larger buy order
        buy_order = Order(
            user_id="buyer",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1.0")
        )
        
        processed_order, trades = engine.process_order(buy_order)
        
        # Order is partially filled and remaining goes to order book (OPEN status)
        assert processed_order.status == OrderStatus.OPEN
        assert processed_order.filled_quantity == Decimal("0.5")
        assert processed_order.remaining_quantity == Decimal("0.5")
        assert len(trades) == 1
        
        # Check order is in the book
        book = engine.get_order_book("BTC-USD")
        assert book.get_order(buy_order.order_id) is not None
    
    def test_process_market_order_buy(self):
        """Test processing a market buy order"""
        engine = MatchingEngine()
        
        # Add sell orders at different prices
        for price in [Decimal("50000"), Decimal("51000"), Decimal("52000")]:
            sell_order = Order(
                user_id="seller",
                symbol="BTC-USD",
                side=OrderSide.SELL,
                order_type=OrderType.LIMIT,
                price=price,
                quantity=Decimal("1.0")
            )
            engine.process_order(sell_order)
        
        # Market buy order
        market_order = Order(
            user_id="buyer",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=Decimal("2.5")
        )
        
        processed_order, trades = engine.process_order(market_order)
        
        assert processed_order.status == OrderStatus.FILLED
        assert len(trades) == 3  # Matched against 3 sell orders
        assert trades[0].price == Decimal("50000")  # Best price first
        assert trades[1].price == Decimal("51000")
        assert trades[2].price == Decimal("52000")
    
    def test_process_market_order_sell(self):
        """Test processing a market sell order"""
        engine = MatchingEngine()
        
        # Add buy orders at different prices
        for price in [Decimal("50000"), Decimal("49000"), Decimal("48000")]:
            buy_order = Order(
                user_id="buyer",
                symbol="BTC-USD",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                price=price,
                quantity=Decimal("1.0")
            )
            engine.process_order(buy_order)
        
        # Market sell order
        market_order = Order(
            user_id="seller",
            symbol="BTC-USD",
            side=OrderSide.SELL,
            order_type=OrderType.MARKET,
            quantity=Decimal("2.0")
        )
        
        processed_order, trades = engine.process_order(market_order)
        
        assert processed_order.status == OrderStatus.FILLED
        assert len(trades) == 2
        assert trades[0].price == Decimal("50000")  # Best price first
        assert trades[1].price == Decimal("49000")
    
    def test_market_order_insufficient_liquidity(self):
        """Test market order with insufficient liquidity"""
        engine = MatchingEngine()
        
        # Add only one small sell order
        sell_order = Order(
            user_id="seller",
            symbol="BTC-USD",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("0.5")
        )
        engine.process_order(sell_order)
        
        # Large market buy order
        market_order = Order(
            user_id="buyer",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=Decimal("2.0")
        )
        
        processed_order, trades = engine.process_order(market_order)
        
        # Market order fills what it can (0.5) and is marked as partially filled
        assert processed_order.status == OrderStatus.PARTIALLY_FILLED
        assert processed_order.filled_quantity == Decimal("0.5")
        assert len(trades) == 1
    
    def test_process_ioc_order_full_fill(self):
        """Test IOC order that fills completely"""
        engine = MatchingEngine()
        
        # Add sell order
        sell_order = Order(
            user_id="seller",
            symbol="BTC-USD",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1.0")
        )
        engine.process_order(sell_order)
        
        # IOC buy order
        ioc_order = Order(
            user_id="buyer",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.IOC,
            price=Decimal("50000"),
            quantity=Decimal("1.0")
        )
        
        processed_order, trades = engine.process_order(ioc_order)
        
        assert processed_order.status == OrderStatus.FILLED
        assert len(trades) == 1
    
    def test_process_ioc_order_partial_fill(self):
        """Test IOC order that fills partially and cancels remainder"""
        engine = MatchingEngine()
        
        # Add small sell order
        sell_order = Order(
            user_id="seller",
            symbol="BTC-USD",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("0.5")
        )
        engine.process_order(sell_order)
        
        # IOC buy order for more
        ioc_order = Order(
            user_id="buyer",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.IOC,
            price=Decimal("50000"),
            quantity=Decimal("1.0")
        )
        
        processed_order, trades = engine.process_order(ioc_order)
        
        assert processed_order.status == OrderStatus.CANCELLED
        assert processed_order.filled_quantity == Decimal("0.5")
        assert len(trades) == 1
    
    def test_process_fok_order_can_fill(self):
        """Test FOK order that can be completely filled"""
        engine = MatchingEngine()
        
        # Add enough sell orders
        for i in range(2):
            sell_order = Order(
                user_id=f"seller{i}",
                symbol="BTC-USD",
                side=OrderSide.SELL,
                order_type=OrderType.LIMIT,
                price=Decimal("50000"),
                quantity=Decimal("0.5")
            )
            engine.process_order(sell_order)
        
        # FOK buy order
        fok_order = Order(
            user_id="buyer",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.FOK,
            price=Decimal("50000"),
            quantity=Decimal("1.0")
        )
        
        processed_order, trades = engine.process_order(fok_order)
        
        assert processed_order.status == OrderStatus.FILLED
        assert len(trades) == 2
    
    def test_process_fok_order_cannot_fill(self):
        """Test FOK order that cannot be completely filled"""
        engine = MatchingEngine()
        
        # Add insufficient sell orders
        sell_order = Order(
            user_id="seller",
            symbol="BTC-USD",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("0.5")
        )
        engine.process_order(sell_order)
        
        # FOK buy order for more
        fok_order = Order(
            user_id="buyer",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.FOK,
            price=Decimal("50000"),
            quantity=Decimal("1.0")
        )
        
        processed_order, trades = engine.process_order(fok_order)
        
        assert processed_order.status == OrderStatus.REJECTED
        assert len(trades) == 0
    
    def test_price_time_priority(self):
        """Test that price-time priority is maintained"""
        engine = MatchingEngine()
        
        # Add sell orders at same price
        import time
        
        sell_order1 = Order(
            user_id="seller1",
            symbol="BTC-USD",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1.0")
        )
        engine.process_order(sell_order1)
        
        time.sleep(0.01)
        
        sell_order2 = Order(
            user_id="seller2",
            symbol="BTC-USD",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1.0")
        )
        engine.process_order(sell_order2)
        
        # Buy order should match with first sell order (time priority)
        buy_order = Order(
            user_id="buyer",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1.0")
        )
        
        processed_order, trades = engine.process_order(buy_order)
        
        assert len(trades) == 1
        assert trades[0].seller_order_id == sell_order1.order_id
    
    def test_cancel_order(self):
        """Test cancelling an order"""
        engine = MatchingEngine()
        
        order = Order(
            user_id="user1",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1.0")
        )
        
        engine.process_order(order)
        
        cancelled = engine.cancel_order("BTC-USD", order.order_id)
        
        assert cancelled is not None
        assert cancelled.status == OrderStatus.CANCELLED
        
        # Order should be removed from order book
        book = engine.get_order_book("BTC-USD")
        assert book.order_count == 0
    
    def test_cancel_nonexistent_order(self):
        """Test cancelling an order that doesn't exist"""
        engine = MatchingEngine()
        
        cancelled = engine.cancel_order("BTC-USD", "nonexistent")
        assert cancelled is None
    
    def test_get_order(self):
        """Test getting an order"""
        engine = MatchingEngine()
        
        order = Order(
            user_id="user1",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1.0")
        )
        
        engine.process_order(order)
        
        retrieved = engine.get_order("BTC-USD", order.order_id)
        assert retrieved == order
    
    def test_get_recent_trades(self):
        """Test getting recent trades"""
        engine = MatchingEngine()
        
        # Create some trades
        for i in range(5):
            sell_order = Order(
                user_id=f"seller{i}",
                symbol="BTC-USD",
                side=OrderSide.SELL,
                order_type=OrderType.LIMIT,
                price=Decimal("50000"),
                quantity=Decimal("1.0")
            )
            engine.process_order(sell_order)
            
            buy_order = Order(
                user_id=f"buyer{i}",
                symbol="BTC-USD",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                price=Decimal("50000"),
                quantity=Decimal("1.0")
            )
            engine.process_order(buy_order)
        
        trades = engine.get_recent_trades("BTC-USD", limit=3)
        assert len(trades) == 3
    
    def test_get_statistics(self):
        """Test getting engine statistics"""
        engine = MatchingEngine()
        
        # Add some orders
        for i in range(3):
            order = Order(
                user_id=f"user{i}",
                symbol="BTC-USD",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                price=Decimal("50000"),
                quantity=Decimal("1.0")
            )
            engine.process_order(order)
        
        stats = engine.get_statistics()
        
        assert stats['total_symbols'] == 1
        assert stats['total_trades'] == 0
        assert 'BTC-USD' in stats['order_books']
        assert stats['order_books']['BTC-USD']['orders'] == 3
    
    def test_multi_symbol_support(self):
        """Test handling multiple symbols"""
        engine = MatchingEngine()
        
        # Add orders for different symbols
        btc_order = Order(
            user_id="user1",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1.0")
        )
        
        eth_order = Order(
            user_id="user2",
            symbol="ETH-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("3000"),
            quantity=Decimal("10.0")
        )
        
        engine.process_order(btc_order)
        engine.process_order(eth_order)
        
        assert len(engine.order_books) == 2
        assert "BTC-USD" in engine.order_books
        assert "ETH-USD" in engine.order_books
    
    def test_volume_tracking(self):
        """Test total volume tracking"""
        engine = MatchingEngine()
        
        # Create matching orders
        sell_order = Order(
            user_id="seller",
            symbol="BTC-USD",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("2.5")
        )
        engine.process_order(sell_order)
        
        buy_order = Order(
            user_id="buyer",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("2.5")
        )
        engine.process_order(buy_order)
        
        assert engine.total_volume == Decimal("2.5")
