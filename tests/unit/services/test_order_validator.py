"""
Tests for Order Validator Service
"""

import pytest
from decimal import Decimal
from datetime import datetime, UTC
import time

from src.matching_engine.core.order import Order, OrderSide, OrderType
from src.matching_engine.services.order_validator import (
    OrderValidator,
    OrderValidatorConfig,
    ValidationError,
    ValidationRule
)


class TestOrderValidatorConfig:
    """Test OrderValidatorConfig"""
    
    def test_default_config(self):
        """Test default configuration"""
        config = OrderValidatorConfig()
        
        assert config.min_price == Decimal("0.01")
        assert config.max_price == Decimal("1000000")
        assert config.min_quantity == Decimal("0.001")
        assert config.max_quantity == Decimal("1000000")
        assert config.tick_size == Decimal("0.01")
        assert config.lot_size == Decimal("0.001")
        assert config.max_orders_per_second == 100
        assert config.check_balance == False
        assert config.check_market_hours == False
        assert config.allowed_symbols == []
    
    def test_custom_config(self):
        """Test custom configuration"""
        config = OrderValidatorConfig(
            min_price=Decimal("1"),
            max_price=Decimal("10000"),
            tick_size=Decimal("0.1"),
            allowed_symbols=["BTC-USD", "ETH-USD"]
        )
        
        assert config.min_price == Decimal("1")
        assert config.max_price == Decimal("10000")
        assert config.tick_size == Decimal("0.1")
        assert config.allowed_symbols == ["BTC-USD", "ETH-USD"]


class TestOrderValidator:
    """Test OrderValidator"""
    
    @pytest.fixture
    def validator(self):
        """Create validator with default config"""
        return OrderValidator()
    
    @pytest.fixture
    def strict_validator(self):
        """Create validator with strict config"""
        config = OrderValidatorConfig(
            min_price=Decimal("100"),
            max_price=Decimal("1000"),
            min_quantity=Decimal("1"),
            max_quantity=Decimal("100"),
            tick_size=Decimal("1"),
            lot_size=Decimal("1"),
            max_orders_per_second=5,
            allowed_symbols=["BTC-USD"]
        )
        return OrderValidator(config)
    
    def test_valid_limit_order(self, validator):
        """Test validation of valid limit order"""
        order = Order(
            user_id="user1",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1.0")
        )
        
        assert validator.validate(order) == True
    
    def test_valid_market_order(self, validator):
        """Test validation of valid market order"""
        order = Order(
            user_id="user1",
            symbol="BTC-USD",
            side=OrderSide.SELL,
            order_type=OrderType.MARKET,
            quantity=Decimal("1.0")
        )
        
        assert validator.validate(order) == True
    
    def test_limit_order_without_price(self, validator):
        """Test limit order without price fails"""
        with pytest.raises(ValidationError) as exc_info:
            order = Order(
                user_id="user1",
                symbol="BTC-USD",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                quantity=Decimal("1.0")
            )
            validator.validate(order)
        
        assert "must have a price" in str(exc_info.value)
        assert exc_info.value.field == "price"
    
    def test_market_order_with_price(self, validator):
        """Test market order with price fails"""
        with pytest.raises(ValidationError) as exc_info:
            order = Order(
                user_id="user1",
                symbol="BTC-USD",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                price=Decimal("50000"),
                quantity=Decimal("1.0")
            )
            validator.validate(order)
        
        assert "cannot have a price" in str(exc_info.value)
    
    def test_price_below_minimum(self, validator):
        """Test price below minimum fails"""
        with pytest.raises(ValidationError) as exc_info:
            order = Order(
                user_id="user1",
                symbol="BTC-USD",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                price=Decimal("0.001"),  # Below min of 0.01
                quantity=Decimal("1.0")
            )
            validator.validate(order)
        
        assert "below minimum" in str(exc_info.value)
        assert exc_info.value.field == "price"
    
    def test_price_above_maximum(self, validator):
        """Test price above maximum fails"""
        with pytest.raises(ValidationError) as exc_info:
            order = Order(
                user_id="user1",
                symbol="BTC-USD",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                price=Decimal("2000000"),  # Above max of 1000000
                quantity=Decimal("1.0")
            )
            validator.validate(order)
        
        assert "above maximum" in str(exc_info.value)
        assert exc_info.value.field == "price"
    
    def test_quantity_below_minimum(self, validator):
        """Test quantity below minimum fails"""
        with pytest.raises(ValidationError) as exc_info:
            order = Order(
                user_id="user1",
                symbol="BTC-USD",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                price=Decimal("50000"),
                quantity=Decimal("0.0001")  # Below min of 0.001
            )
            validator.validate(order)
        
        assert "below minimum" in str(exc_info.value)
        assert exc_info.value.field == "quantity"
    
    def test_quantity_above_maximum(self, validator):
        """Test quantity above maximum fails"""
        with pytest.raises(ValidationError) as exc_info:
            order = Order(
                user_id="user1",
                symbol="BTC-USD",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                price=Decimal("50000"),
                quantity=Decimal("2000000")  # Above max of 1000000
            )
            validator.validate(order)
        
        assert "above maximum" in str(exc_info.value)
        assert exc_info.value.field == "quantity"
    
    def test_tick_size_validation(self, strict_validator):
        """Test tick size validation"""
        # Valid: price conforms to tick size of 1
        order = Order(
            user_id="user1",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("500"),  # Conforms to tick size 1
            quantity=Decimal("1")
        )
        assert strict_validator.validate(order) == True
        
        # Invalid: price doesn't conform to tick size
        with pytest.raises(ValidationError) as exc_info:
            order = Order(
                user_id="user1",
                symbol="BTC-USD",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                price=Decimal("500.5"),  # Doesn't conform to tick size 1
                quantity=Decimal("1")
            )
            strict_validator.validate(order)
        
        assert "tick size" in str(exc_info.value)
    
    def test_lot_size_validation(self, strict_validator):
        """Test lot size validation"""
        # Valid: quantity conforms to lot size of 1
        order = Order(
            user_id="user1",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("500"),
            quantity=Decimal("5")  # Conforms to lot size 1
        )
        assert strict_validator.validate(order) == True
        
        # Invalid: quantity doesn't conform to lot size
        with pytest.raises(ValidationError) as exc_info:
            order = Order(
                user_id="user1",
                symbol="BTC-USD",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                price=Decimal("500"),
                quantity=Decimal("5.5")  # Doesn't conform to lot size 1
            )
            strict_validator.validate(order)
        
        assert "lot size" in str(exc_info.value)
    
    def test_symbol_validation(self, strict_validator):
        """Test symbol validation"""
        # Valid: allowed symbol
        order = Order(
            user_id="user1",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("500"),
            quantity=Decimal("1")
        )
        assert strict_validator.validate(order) == True
        
        # Invalid: not allowed symbol
        with pytest.raises(ValidationError) as exc_info:
            order = Order(
                user_id="user1",
                symbol="ETH-USD",  # Not in allowed list
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                price=Decimal("500"),
                quantity=Decimal("1")
            )
            strict_validator.validate(order)
        
        assert "not allowed" in str(exc_info.value)
        assert exc_info.value.field == "symbol"
    
    def test_rate_limiting(self, strict_validator):
        """Test rate limiting (max 5 orders/second)"""
        # Submit 5 orders (should pass)
        for i in range(5):
            order = Order(
                user_id="user1",
                symbol="BTC-USD",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                price=Decimal("500"),
                quantity=Decimal("1")
            )
            assert strict_validator.validate(order) == True
        
        # 6th order should fail
        with pytest.raises(ValidationError) as exc_info:
            order = Order(
                user_id="user1",
                symbol="BTC-USD",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                price=Decimal("500"),
                quantity=Decimal("1")
            )
            strict_validator.validate(order)
        
        assert "Rate limit exceeded" in str(exc_info.value)
        assert exc_info.value.field == "rate_limit"
    
    def test_rate_limiting_different_users(self, strict_validator):
        """Test rate limiting is per-user"""
        # User1 submits 5 orders
        for i in range(5):
            order = Order(
                user_id="user1",
                symbol="BTC-USD",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                price=Decimal("500"),
                quantity=Decimal("1")
            )
            strict_validator.validate(order)
        
        # User2 should still be able to submit
        order = Order(
            user_id="user2",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("500"),
            quantity=Decimal("1")
        )
        assert strict_validator.validate(order) == True
    
    def test_duplicate_order_detection(self, validator):
        """Test duplicate order ID detection"""
        order1 = Order(
            user_id="user1",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1.0")
        )
        
        # First submission should pass
        assert validator.validate(order1) == True
        
        # Duplicate should fail
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(order1)
        
        assert "Duplicate order ID" in str(exc_info.value)
        assert exc_info.value.field == "order_id"
    
    def test_balance_validation_buy_order(self, validator):
        """Test balance validation for buy orders"""
        order = Order(
            user_id="user1",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("2.0")
        )
        
        # Sufficient balance
        assert validator.validate_balance(order, Decimal("100000")) == True
        
        # Insufficient balance
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_balance(order, Decimal("50000"))
        
        assert "Insufficient balance" in str(exc_info.value)
        assert exc_info.value.field == "balance"
    
    def test_balance_validation_sell_order(self, validator):
        """Test balance validation for sell orders"""
        order = Order(
            user_id="user1",
            symbol="BTC-USD",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("2.0")
        )
        
        # Sufficient balance (need 2.0 BTC)
        assert validator.validate_balance(order, Decimal("3.0")) == True
        
        # Insufficient balance
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_balance(order, Decimal("1.0"))
        
        assert "Insufficient balance" in str(exc_info.value)
    
    def test_clear_history(self, strict_validator):
        """Test clearing validation history"""
        # Submit orders
        for i in range(3):
            order = Order(
                user_id="user1",
                symbol="BTC-USD",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                price=Decimal("500"),
                quantity=Decimal("1")
            )
            strict_validator.validate(order)
        
        # Clear user1's history
        strict_validator.clear_history("user1")
        
        # Should be able to submit more orders now
        for i in range(5):
            order = Order(
                user_id="user1",
                symbol="BTC-USD",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                price=Decimal("500"),
                quantity=Decimal("1")
            )
            assert strict_validator.validate(order) == True
    
    def test_validation_stats(self, validator):
        """Test getting validation statistics"""
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
            validator.validate(order)
        
        stats = validator.get_validation_stats()
        
        assert stats["tracked_users"] == 3
        assert stats["recent_orders"] == 3
        assert "config" in stats
        assert stats["config"]["min_price"] == "0.01"
        assert stats["config"]["max_orders_per_second"] == 100


class TestValidationError:
    """Test ValidationError exception"""
    
    def test_validation_error_with_field(self):
        """Test ValidationError with field"""
        error = ValidationError("Invalid price", "price")
        
        assert error.message == "Invalid price"
        assert error.field == "price"
        assert str(error) == "Invalid price"
    
    def test_validation_error_without_field(self):
        """Test ValidationError without field"""
        error = ValidationError("General validation error")
        
        assert error.message == "General validation error"
        assert error.field is None
