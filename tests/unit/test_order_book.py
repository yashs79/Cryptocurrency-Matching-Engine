"""
Unit tests for OrderBook class.
"""

import pytest
from decimal import Decimal

from src.matching_engine.core.order import Order, OrderSide, OrderType, OrderStatus
from src.matching_engine.core.order_book import OrderBook, PriceLevel


class TestPriceLevel:
    """Test PriceLevel class"""
    
    def test_create_price_level(self):
        """Test creating a price level"""
        level = PriceLevel(Decimal("50000"))
        assert level.price == Decimal("50000")
        assert len(level.orders) == 0
        assert level.total_quantity == Decimal("0")
        assert level.is_empty
    
    def test_add_order_to_level(self):
        """Test adding orders to a price level"""
        level = PriceLevel(Decimal("50000"))
        
        order1 = Order(
            user_id="user1",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1.5")
        )
        
        level.add_order(order1)
        assert len(level.orders) == 1
        assert level.total_quantity == Decimal("1.5")
        assert not level.is_empty
    
    def test_remove_order_from_level(self):
        """Test removing orders from a price level"""
        level = PriceLevel(Decimal("50000"))
        
        order1 = Order(
            user_id="user1",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1.5")
        )
        
        level.add_order(order1)
        assert level.remove_order(order1)
        assert level.is_empty
        assert level.total_quantity == Decimal("0")


class TestOrderBook:
    """Test OrderBook class"""
    
    def test_create_order_book(self):
        """Test creating an order book"""
        book = OrderBook("BTC-USD")
        assert book.symbol == "BTC-USD"
        assert len(book.orders) == 0
        assert book.order_count == 0
        assert book.best_bid is None
        assert book.best_ask is None
    
    def test_add_buy_order(self):
        """Test adding a buy order"""
        book = OrderBook("BTC-USD")
        
        order = Order(
            user_id="user1",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1.5")
        )
        
        book.add_order(order)
        assert book.order_count == 1
        assert book.best_bid == Decimal("50000")
        assert order.status == OrderStatus.OPEN
    
    def test_add_sell_order(self):
        """Test adding a sell order"""
        book = OrderBook("BTC-USD")
        
        order = Order(
            user_id="user1",
            symbol="BTC-USD",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            price=Decimal("51000"),
            quantity=Decimal("2.0")
        )
        
        book.add_order(order)
        assert book.order_count == 1
        assert book.best_ask == Decimal("51000")
    
    def test_cannot_add_market_order(self):
        """Test that market orders cannot be added to order book"""
        book = OrderBook("BTC-USD")
        
        order = Order(
            user_id="user1",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=Decimal("1.0")
        )
        
        with pytest.raises(ValueError, match="Cannot add market order"):
            book.add_order(order)
    
    def test_cannot_add_duplicate_order(self):
        """Test that duplicate orders cannot be added"""
        book = OrderBook("BTC-USD")
        
        order = Order(
            user_id="user1",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1.0")
        )
        
        book.add_order(order)
        with pytest.raises(ValueError, match="already exists"):
            book.add_order(order)
    
    def test_remove_order(self):
        """Test removing an order"""
        book = OrderBook("BTC-USD")
        
        order = Order(
            user_id="user1",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1.0")
        )
        
        book.add_order(order)
        removed = book.remove_order(order.order_id)
        
        assert removed == order
        assert book.order_count == 0
        assert book.best_bid is None
    
    def test_remove_nonexistent_order(self):
        """Test removing an order that doesn't exist"""
        book = OrderBook("BTC-USD")
        removed = book.remove_order("nonexistent")
        assert removed is None
    
    def test_best_bid_multiple_levels(self):
        """Test best bid with multiple price levels"""
        book = OrderBook("BTC-USD")
        
        # Add orders at different prices
        for price in [Decimal("49000"), Decimal("50000"), Decimal("48000")]:
            order = Order(
                user_id="user1",
                symbol="BTC-USD",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                price=price,
                quantity=Decimal("1.0")
            )
            book.add_order(order)
        
        # Best bid should be highest price
        assert book.best_bid == Decimal("50000")
    
    def test_best_ask_multiple_levels(self):
        """Test best ask with multiple price levels"""
        book = OrderBook("BTC-USD")
        
        # Add orders at different prices
        for price in [Decimal("51000"), Decimal("50000"), Decimal("52000")]:
            order = Order(
                user_id="user1",
                symbol="BTC-USD",
                side=OrderSide.SELL,
                order_type=OrderType.LIMIT,
                price=price,
                quantity=Decimal("1.0")
            )
            book.add_order(order)
        
        # Best ask should be lowest price
        assert book.best_ask == Decimal("50000")
    
    def test_spread_calculation(self):
        """Test bid-ask spread calculation"""
        book = OrderBook("BTC-USD")
        
        buy_order = Order(
            user_id="user1",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1.0")
        )
        
        sell_order = Order(
            user_id="user2",
            symbol="BTC-USD",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            price=Decimal("51000"),
            quantity=Decimal("1.0")
        )
        
        book.add_order(buy_order)
        book.add_order(sell_order)
        
        assert book.spread == Decimal("1000")
    
    def test_mid_price_calculation(self):
        """Test mid price calculation"""
        book = OrderBook("BTC-USD")
        
        buy_order = Order(
            user_id="user1",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1.0")
        )
        
        sell_order = Order(
            user_id="user2",
            symbol="BTC-USD",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            price=Decimal("52000"),
            quantity=Decimal("1.0")
        )
        
        book.add_order(buy_order)
        book.add_order(sell_order)
        
        assert book.mid_price == Decimal("51000")
    
    def test_get_depth(self):
        """Test getting order book depth"""
        book = OrderBook("BTC-USD")
        
        # Add multiple buy orders
        for i, price in enumerate([Decimal("50000"), Decimal("49000"), Decimal("48000")]):
            order = Order(
                user_id=f"user{i}",
                symbol="BTC-USD",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                price=price,
                quantity=Decimal("1.0")
            )
            book.add_order(order)
        
        # Add multiple sell orders
        for i, price in enumerate([Decimal("51000"), Decimal("52000"), Decimal("53000")]):
            order = Order(
                user_id=f"seller{i}",
                symbol="BTC-USD",
                side=OrderSide.SELL,
                order_type=OrderType.LIMIT,
                price=price,
                quantity=Decimal("2.0")
            )
            book.add_order(order)
        
        depth = book.get_depth(levels=5)
        
        assert depth['symbol'] == "BTC-USD"
        assert len(depth['bids']) == 3
        assert len(depth['asks']) == 3
        assert depth['bids'][0]['price'] == "50000"  # Best bid
        assert depth['asks'][0]['price'] == "51000"  # Best ask
    
    def test_get_orders_at_price(self):
        """Test getting all orders at a specific price"""
        book = OrderBook("BTC-USD")
        
        # Add multiple orders at same price
        for i in range(3):
            order = Order(
                user_id=f"user{i}",
                symbol="BTC-USD",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                price=Decimal("50000"),
                quantity=Decimal("1.0")
            )
            book.add_order(order)
        
        orders = book.get_orders_at_price(Decimal("50000"), OrderSide.BUY)
        assert len(orders) == 3
    
    def test_clear_order_book(self):
        """Test clearing the order book"""
        book = OrderBook("BTC-USD")
        
        # Add some orders
        for i in range(5):
            order = Order(
                user_id=f"user{i}",
                symbol="BTC-USD",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                price=Decimal("50000"),
                quantity=Decimal("1.0")
            )
            book.add_order(order)
        
        book.clear()
        
        assert book.order_count == 0
        assert book.best_bid is None
        assert book.best_ask is None
        assert len(book.orders) == 0
    
    def test_volume_tracking(self):
        """Test volume tracking"""
        book = OrderBook("BTC-USD")
        
        buy_order = Order(
            user_id="user1",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1.5")
        )
        
        sell_order = Order(
            user_id="user2",
            symbol="BTC-USD",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            price=Decimal("51000"),
            quantity=Decimal("2.5")
        )
        
        book.add_order(buy_order)
        book.add_order(sell_order)
        
        assert book.total_bid_volume == Decimal("1.5")
        assert book.total_ask_volume == Decimal("2.5")
    
    def test_price_level_cleanup(self):
        """Test that empty price levels are removed"""
        book = OrderBook("BTC-USD")
        
        order = Order(
            user_id="user1",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1.0")
        )
        
        book.add_order(order)
        assert Decimal("50000") in book.bid_levels
        
        book.remove_order(order.order_id)
        assert Decimal("50000") not in book.bid_levels
        assert len(book.bid_prices) == 0
