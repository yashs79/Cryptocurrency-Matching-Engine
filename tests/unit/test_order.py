"""
Unit tests for Order class.
"""

import pytest
from decimal import Decimal
from datetime import datetime

from src.matching_engine.core.order import (
    Order,
    OrderSide,
    OrderType,
    OrderStatus
)


class TestOrder:
    """Test Order class functionality"""
    
    def test_create_limit_order(self):
        """Test creating a valid limit order"""
        order = Order(
            user_id="user123",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1.5")
        )
        
        assert order.user_id == "user123"
        assert order.symbol == "BTC-USD"
        assert order.side == OrderSide.BUY
        assert order.order_type == OrderType.LIMIT
        assert order.price == Decimal("50000")
        assert order.quantity == Decimal("1.5")
        assert order.filled_quantity == Decimal("0")
        assert order.status == OrderStatus.PENDING
        assert order.order_id is not None
    
    def test_create_market_order(self):
        """Test creating a market order"""
        order = Order(
            user_id="user123",
            symbol="ETH-USD",
            side=OrderSide.SELL,
            order_type=OrderType.MARKET,
            quantity=Decimal("10")
        )
        
        assert order.price is None
        assert order.order_type == OrderType.MARKET
    
    def test_market_order_cannot_have_price(self):
        """Test that market orders cannot have a price"""
        with pytest.raises(ValueError, match="Market orders cannot have a price"):
            Order(
                user_id="user123",
                symbol="BTC-USD",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                price=Decimal("50000"),
                quantity=Decimal("1")
            )
    
    def test_limit_order_must_have_price(self):
        """Test that limit orders must have a price"""
        with pytest.raises(ValueError, match="Limit orders must have a price"):
            Order(
                user_id="user123",
                symbol="BTC-USD",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                quantity=Decimal("1")
            )
    
    def test_price_must_be_positive(self):
        """Test that price must be positive"""
        with pytest.raises(ValueError, match="Price must be positive"):
            Order(
                user_id="user123",
                symbol="BTC-USD",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                price=Decimal("-100"),
                quantity=Decimal("1")
            )
    
    def test_quantity_must_be_positive(self):
        """Test that quantity must be positive"""
        with pytest.raises(ValueError, match="Quantity must be positive"):
            Order(
                user_id="user123",
                symbol="BTC-USD",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                price=Decimal("50000"),
                quantity=Decimal("0")
            )
    
    def test_remaining_quantity(self):
        """Test remaining quantity calculation"""
        order = Order(
            user_id="user123",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("10")
        )
        
        assert order.remaining_quantity == Decimal("10")
        
        order.filled_quantity = Decimal("3")
        assert order.remaining_quantity == Decimal("7")
    
    def test_is_filled(self):
        """Test is_filled property"""
        order = Order(
            user_id="user123",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("10")
        )
        
        assert not order.is_filled
        
        order.filled_quantity = Decimal("10")
        assert order.is_filled
    
    def test_is_partially_filled(self):
        """Test is_partially_filled property"""
        order = Order(
            user_id="user123",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("10")
        )
        
        assert not order.is_partially_filled
        
        order.filled_quantity = Decimal("5")
        assert order.is_partially_filled
        
        order.filled_quantity = Decimal("10")
        assert not order.is_partially_filled
    
    def test_fill_order(self):
        """Test filling an order"""
        order = Order(
            user_id="user123",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("10")
        )
        
        order.fill(Decimal("3"))
        assert order.filled_quantity == Decimal("3")
        assert order.status == OrderStatus.PARTIALLY_FILLED
        
        order.fill(Decimal("7"))
        assert order.filled_quantity == Decimal("10")
        assert order.status == OrderStatus.FILLED
    
    def test_fill_invalid_quantity(self):
        """Test filling with invalid quantity"""
        order = Order(
            user_id="user123",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("10")
        )
        
        with pytest.raises(ValueError, match="Fill quantity must be positive"):
            order.fill(Decimal("0"))
        
        with pytest.raises(ValueError, match="Fill quantity exceeds remaining quantity"):
            order.fill(Decimal("15"))
    
    def test_cancel_order(self):
        """Test cancelling an order"""
        order = Order(
            user_id="user123",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("10")
        )
        
        order.status = OrderStatus.OPEN
        order.cancel()
        assert order.status == OrderStatus.CANCELLED
    
    def test_cannot_cancel_filled_order(self):
        """Test that filled orders cannot be cancelled"""
        order = Order(
            user_id="user123",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("10")
        )
        
        order.status = OrderStatus.FILLED
        with pytest.raises(ValueError, match="Cannot cancel order"):
            order.cancel()
    
    def test_order_comparison_buy_side(self):
        """Test order comparison for buy orders (higher price has priority)"""
        order1 = Order(
            user_id="user1",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1")
        )
        
        order2 = Order(
            user_id="user2",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("51000"),
            quantity=Decimal("1")
        )
        
        # Higher price should have priority (be "less than")
        assert order2 < order1
    
    def test_order_comparison_sell_side(self):
        """Test order comparison for sell orders (lower price has priority)"""
        order1 = Order(
            user_id="user1",
            symbol="BTC-USD",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1")
        )
        
        order2 = Order(
            user_id="user2",
            symbol="BTC-USD",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            price=Decimal("51000"),
            quantity=Decimal("1")
        )
        
        # Lower price should have priority (be "less than")
        assert order1 < order2
    
    def test_order_comparison_time_priority(self):
        """Test that earlier orders have priority at same price"""
        import time
        
        order1 = Order(
            user_id="user1",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1")
        )
        
        time.sleep(0.01)  # Ensure different timestamps
        
        order2 = Order(
            user_id="user2",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1")
        )
        
        # Earlier order should have priority
        assert order1 < order2
