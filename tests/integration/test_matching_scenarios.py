"""
Integration tests for realistic matching scenarios.
"""

import pytest
from decimal import Decimal
from src.matching_engine.core import MatchingEngine, Order, OrderSide, OrderType


class TestMatchingScenarios:
    """Test realistic matching scenarios"""
    
    def test_simple_buy_sell_match(self):
        """Test simple buy-sell matching"""
        engine = MatchingEngine()
        
        # Seller places limit order
        sell_order = Order(
            user_id="alice",
            symbol="BTC-USD",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1.0")
        )
        _, trades1 = engine.process_order(sell_order)
        assert len(trades1) == 0  # No match yet
        
        # Buyer places matching limit order
        buy_order = Order(
            user_id="bob",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1.0")
        )
        _, trades2 = engine.process_order(buy_order)
        
        assert len(trades2) == 1
        assert trades2[0].price == Decimal("50000")
        assert trades2[0].quantity == Decimal("1.0")
        assert buy_order.status.value == "FILLED"
        assert sell_order.status.value == "FILLED"
    
    def test_multiple_partial_fills(self):
        """Test order filled by multiple smaller orders"""
        engine = MatchingEngine()
        
        # Multiple small sell orders
        for i in range(5):
            sell_order = Order(
                user_id=f"seller{i}",
                symbol="BTC-USD",
                side=OrderSide.SELL,
                order_type=OrderType.LIMIT,
                price=Decimal("50000"),
                quantity=Decimal("0.2")
            )
            engine.process_order(sell_order)
        
        # Large buy order
        buy_order = Order(
            user_id="buyer",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1.0")
        )
        _, trades = engine.process_order(buy_order)
        
        assert len(trades) == 5
        assert buy_order.status.value == "FILLED"
        assert sum(t.quantity for t in trades) == Decimal("1.0")
    
    def test_price_improvement(self):
        """Test that buyers get price improvement"""
        engine = MatchingEngine()
        
        # Sell orders at different prices
        sell_order1 = Order(
            user_id="seller1",
            symbol="BTC-USD",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            price=Decimal("49000"),
            quantity=Decimal("1.0")
        )
        engine.process_order(sell_order1)
        
        sell_order2 = Order(
            user_id="seller2",
            symbol="BTC-USD",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1.0")
        )
        engine.process_order(sell_order2)
        
        # Buy order willing to pay 50000
        buy_order = Order(
            user_id="buyer",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1.0")
        )
        _, trades = engine.process_order(buy_order)
        
        # Should match at 49000 (better price)
        assert len(trades) == 1
        assert trades[0].price == Decimal("49000")
    
    def test_market_order_sweeps_book(self):
        """Test market order sweeping through multiple price levels"""
        engine = MatchingEngine()
        
        # Build order book with multiple price levels
        prices = [Decimal("50000"), Decimal("50100"), Decimal("50200")]
        for price in prices:
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
            quantity=Decimal("3.0")
        )
        _, trades = engine.process_order(market_order)
        
        assert len(trades) == 3
        assert trades[0].price == Decimal("50000")
        assert trades[1].price == Decimal("50100")
        assert trades[2].price == Decimal("50200")
    
    def test_order_book_depth_after_trades(self):
        """Test order book depth after partial fills"""
        engine = MatchingEngine()
        
        # Add multiple orders
        for i in range(3):
            sell_order = Order(
                user_id=f"seller{i}",
                symbol="BTC-USD",
                side=OrderSide.SELL,
                order_type=OrderType.LIMIT,
                price=Decimal("50000") + Decimal(i * 100),
                quantity=Decimal("1.0")
            )
            engine.process_order(sell_order)
        
        # Partial match
        buy_order = Order(
            user_id="buyer",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1.0")
        )
        engine.process_order(buy_order)
        
        # Check remaining depth
        book = engine.get_order_book("BTC-USD")
        depth = book.get_depth(levels=5)
        
        assert len(depth['asks']) == 2  # One order filled
        assert depth['asks'][0]['price'] == "50100"
    
    def test_cancel_and_replace(self):
        """Test cancelling and replacing an order"""
        engine = MatchingEngine()
        
        # Place initial order
        order1 = Order(
            user_id="trader",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1.0")
        )
        engine.process_order(order1)
        
        # Cancel it
        engine.cancel_order("BTC-USD", order1.order_id)
        
        # Place new order at different price
        order2 = Order(
            user_id="trader",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("51000"),
            quantity=Decimal("1.0")
        )
        engine.process_order(order2)
        
        book = engine.get_order_book("BTC-USD")
        assert book.best_bid == Decimal("51000")
        assert book.order_count == 1
    
    def test_simultaneous_multi_symbol_trading(self):
        """Test trading multiple symbols simultaneously"""
        engine = MatchingEngine()
        
        symbols = ["BTC-USD", "ETH-USD", "SOL-USD"]
        
        for symbol in symbols:
            # Add sell order
            sell_order = Order(
                user_id="seller",
                symbol=symbol,
                side=OrderSide.SELL,
                order_type=OrderType.LIMIT,
                price=Decimal("1000"),
                quantity=Decimal("1.0")
            )
            engine.process_order(sell_order)
            
            # Add matching buy order
            buy_order = Order(
                user_id="buyer",
                symbol=symbol,
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                price=Decimal("1000"),
                quantity=Decimal("1.0")
            )
            engine.process_order(buy_order)
        
        assert len(engine.order_books) == 3
        assert engine.total_trades == 3
    
    def test_large_order_vs_small_orders(self):
        """Test large order matching against many small orders"""
        engine = MatchingEngine()
        
        # Add 100 small sell orders
        for i in range(100):
            sell_order = Order(
                user_id=f"seller{i}",
                symbol="BTC-USD",
                side=OrderSide.SELL,
                order_type=OrderType.LIMIT,
                price=Decimal("50000"),
                quantity=Decimal("0.01")
            )
            engine.process_order(sell_order)
        
        # Large buy order
        buy_order = Order(
            user_id="whale",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1.0")
        )
        _, trades = engine.process_order(buy_order)
        
        assert len(trades) == 100
        assert buy_order.status.value == "FILLED"
    
    def test_spread_maintenance(self):
        """Test that spread is maintained correctly"""
        engine = MatchingEngine()
        
        # Add bid
        buy_order = Order(
            user_id="buyer",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("49000"),
            quantity=Decimal("1.0")
        )
        engine.process_order(buy_order)
        
        # Add ask
        sell_order = Order(
            user_id="seller",
            symbol="BTC-USD",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            price=Decimal("51000"),
            quantity=Decimal("1.0")
        )
        engine.process_order(sell_order)
        
        book = engine.get_order_book("BTC-USD")
        assert book.spread == Decimal("2000")
        assert book.mid_price == Decimal("50000")
    
    def test_ioc_order_real_scenario(self):
        """Test IOC order in realistic scenario"""
        engine = MatchingEngine()
        
        # Build order book
        for i in range(3):
            sell_order = Order(
                user_id=f"seller{i}",
                symbol="BTC-USD",
                side=OrderSide.SELL,
                order_type=OrderType.LIMIT,
                price=Decimal("50000"),
                quantity=Decimal("0.5")
            )
            engine.process_order(sell_order)
        
        # IOC order for more than available
        ioc_order = Order(
            user_id="trader",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.IOC,
            price=Decimal("50000"),
            quantity=Decimal("2.0")
        )
        _, trades = engine.process_order(ioc_order)
        
        # Should fill 1.5 and cancel 0.5
        assert len(trades) == 3
        assert ioc_order.filled_quantity == Decimal("1.5")
        assert ioc_order.status.value == "CANCELLED"
    
    def test_fok_order_real_scenario(self):
        """Test FOK order in realistic scenario"""
        engine = MatchingEngine()
        
        # Build order book with exact amount
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
        
        # FOK order for exact amount
        fok_order = Order(
            user_id="trader",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.FOK,
            price=Decimal("50000"),
            quantity=Decimal("1.0")
        )
        _, trades = engine.process_order(fok_order)
        
        assert len(trades) == 2
        assert fok_order.status.value == "FILLED"
        
        # FOK order for more than available should be rejected
        fok_order2 = Order(
            user_id="trader2",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.FOK,
            price=Decimal("50000"),
            quantity=Decimal("1.0")
        )
        _, trades2 = engine.process_order(fok_order2)
        
        assert len(trades2) == 0
        assert fok_order2.status.value == "REJECTED"
