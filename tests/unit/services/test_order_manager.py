"""
Tests for Order Manager Service
"""

import pytest
from decimal import Decimal

from src.matching_engine.core.order import Order, OrderSide, OrderType, OrderStatus
from src.matching_engine.core.matching_engine import MatchingEngine
from src.matching_engine.services.order_validator import OrderValidator, OrderValidatorConfig, ValidationError
from src.matching_engine.services.order_manager import OrderManager, OrderAction, OrderManagerError


class TestOrderManager:
    """Test OrderManager"""
    
    @pytest.fixture
    def matching_engine(self):
        """Create matching engine"""
        return MatchingEngine()
    
    @pytest.fixture
    def validator(self):
        """Create validator"""
        return OrderValidator()
    
    @pytest.fixture
    def order_manager(self, matching_engine, validator):
        """Create order manager"""
        return OrderManager(matching_engine, validator)
    
    def test_initialization(self, order_manager):
        """Test order manager initialization"""
        assert order_manager.matching_engine is not None
        assert order_manager.validator is not None
        assert isinstance(order_manager._order_history, dict)
    
    def test_submit_valid_order(self, order_manager):
        """Test submitting a valid order"""
        order = Order(
            user_id="user1",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1.0")
        )
        
        processed_order, trades = order_manager.submit_order(order)
        
        assert processed_order.order_id == order.order_id
        assert processed_order.status == OrderStatus.OPEN
        assert len(trades) == 0  # No matching orders
        
        # Check history
        history = order_manager.get_order_history(order.order_id)
        assert len(history) == 1
        assert history[0][0] == OrderAction.SUBMIT
    
    def test_submit_order_with_match(self, order_manager):
        """Test submitting order that matches"""
        # Submit sell order first
        sell_order = Order(
            user_id="seller",
            symbol="BTC-USD",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1.0")
        )
        order_manager.submit_order(sell_order)
        
        # Submit matching buy order
        buy_order = Order(
            user_id="buyer",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1.0")
        )
        
        processed_order, trades = order_manager.submit_order(buy_order)
        
        assert processed_order.status == OrderStatus.FILLED
        assert len(trades) == 1
        assert trades[0].quantity == Decimal("1.0")
        
        # Check history includes fill action
        history = order_manager.get_order_history(buy_order.order_id)
        assert len(history) == 2
        assert history[0][0] == OrderAction.SUBMIT
        assert history[1][0] == OrderAction.FILL
    
    def test_submit_invalid_order(self, order_manager):
        """Test submitting invalid order fails validation"""
        order = Order(
            user_id="user1",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("0.001"),  # Below minimum
            quantity=Decimal("1.0")
        )
        
        with pytest.raises(ValidationError):
            order_manager.submit_order(order)
        
        # Check rejection was recorded
        history = order_manager.get_order_history(order.order_id)
        assert len(history) == 1
        assert history[0][0] == OrderAction.REJECT
    
    def test_submit_order_skip_validation(self, order_manager):
        """Test submitting order with validation skipped"""
        order = Order(
            user_id="user1",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("0.001"),  # Would fail validation
            quantity=Decimal("1.0")
        )
        
        # Should succeed when skipping validation
        processed_order, trades = order_manager.submit_order(order, skip_validation=True)
        assert processed_order.status == OrderStatus.OPEN
    
    def test_cancel_order(self, order_manager):
        """Test cancelling an order"""
        # Submit order
        order = Order(
            user_id="user1",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1.0")
        )
        order_manager.submit_order(order)
        
        # Cancel order
        success = order_manager.cancel_order("BTC-USD", order.order_id, "user1")
        
        assert success == True
        
        # Check order status
        cancelled_order = order_manager.get_order_status("BTC-USD", order.order_id)
        assert cancelled_order.status == OrderStatus.CANCELLED
        
        # Check history
        history = order_manager.get_order_history(order.order_id)
        assert any(action == OrderAction.CANCEL for action, _, _ in history)
    
    def test_cancel_nonexistent_order(self, order_manager):
        """Test cancelling non-existent order fails"""
        with pytest.raises(OrderManagerError) as exc_info:
            order_manager.cancel_order("BTC-USD", "nonexistent", "user1")
        
        assert "not found" in str(exc_info.value)
    
    def test_cancel_order_wrong_user(self, order_manager):
        """Test cancelling order by wrong user fails"""
        # Submit order
        order = Order(
            user_id="user1",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1.0")
        )
        order_manager.submit_order(order)
        
        # Try to cancel as different user
        with pytest.raises(OrderManagerError) as exc_info:
            order_manager.cancel_order("BTC-USD", order.order_id, "user2")
        
        assert "not authorized" in str(exc_info.value)
    
    def test_cancel_filled_order(self, order_manager):
        """Test cancelling filled order fails"""
        # Submit and match orders
        sell_order = Order(
            user_id="seller",
            symbol="BTC-USD",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1.0")
        )
        order_manager.submit_order(sell_order)
        
        buy_order = Order(
            user_id="buyer",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1.0")
        )
        order_manager.submit_order(buy_order)
        
        # Try to cancel filled order
        with pytest.raises(OrderManagerError) as exc_info:
            order_manager.cancel_order("BTC-USD", buy_order.order_id, "buyer")
        
        assert "Cannot cancel" in str(exc_info.value)
    
    def test_amend_order(self, order_manager):
        """Test amending an order"""
        # Submit order
        order = Order(
            user_id="user1",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1.0")
        )
        order_manager.submit_order(order)
        
        # Amend order
        new_order, trades = order_manager.amend_order(
            "BTC-USD",
            order.order_id,
            new_price=Decimal("51000"),
            new_quantity=Decimal("2.0"),
            user_id="user1"
        )
        
        assert new_order.price == Decimal("51000")
        assert new_order.quantity == Decimal("2.0")
        assert new_order.order_id != order.order_id  # New order ID
        
        # Original order should be cancelled
        original = order_manager.get_order_status("BTC-USD", order.order_id)
        assert original.status == OrderStatus.CANCELLED
        
        # Check history
        history = order_manager.get_order_history(order.order_id)
        assert any(action == OrderAction.AMEND for action, _, _ in history)
    
    def test_amend_order_price_only(self, order_manager):
        """Test amending only price"""
        order = Order(
            user_id="user1",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1.0")
        )
        order_manager.submit_order(order)
        
        new_order, _ = order_manager.amend_order(
            "BTC-USD",
            order.order_id,
            new_price=Decimal("51000"),
            user_id="user1"
        )
        
        assert new_order.price == Decimal("51000")
        assert new_order.quantity == Decimal("1.0")  # Unchanged
    
    def test_amend_order_quantity_only(self, order_manager):
        """Test amending only quantity"""
        order = Order(
            user_id="user1",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1.0")
        )
        order_manager.submit_order(order)
        
        new_order, _ = order_manager.amend_order(
            "BTC-USD",
            order.order_id,
            new_quantity=Decimal("2.0"),
            user_id="user1"
        )
        
        assert new_order.price == Decimal("50000")  # Unchanged
        assert new_order.quantity == Decimal("2.0")
    
    def test_get_user_orders(self, order_manager):
        """Test getting all orders for a user"""
        # Submit multiple orders
        for i in range(3):
            order = Order(
                user_id="user1",
                symbol="BTC-USD",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                price=Decimal(f"{50000 + i * 100}"),
                quantity=Decimal("1.0")
            )
            order_manager.submit_order(order)
        
        # Get user orders
        orders = order_manager.get_user_orders("user1")
        
        assert len(orders) == 3
        assert all(o.user_id == "user1" for o in orders)
    
    def test_get_user_orders_filtered_by_symbol(self, order_manager):
        """Test getting user orders filtered by symbol"""
        # Submit orders for different symbols
        order1 = Order(
            user_id="user1",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1.0")
        )
        order_manager.submit_order(order1)
        
        order2 = Order(
            user_id="user1",
            symbol="ETH-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("3000"),
            quantity=Decimal("1.0")
        )
        order_manager.submit_order(order2)
        
        # Get orders for specific symbol
        btc_orders = order_manager.get_user_orders("user1", symbol="BTC-USD")
        
        assert len(btc_orders) == 1
        assert btc_orders[0].symbol == "BTC-USD"
    
    def test_get_open_orders(self, order_manager):
        """Test getting all open orders"""
        # Submit orders
        order1 = Order(
            user_id="user1",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1.0")
        )
        order_manager.submit_order(order1)
        
        order2 = Order(
            user_id="user2",
            symbol="BTC-USD",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            price=Decimal("51000"),
            quantity=Decimal("1.0")
        )
        order_manager.submit_order(order2)
        
        # Get open orders
        open_orders = order_manager.get_open_orders()
        
        assert len(open_orders) == 2
        assert all(o.status == OrderStatus.OPEN for o in open_orders)
    
    def test_cancel_all_orders(self, order_manager):
        """Test cancelling all orders for a user"""
        # Submit multiple orders
        for i in range(3):
            order = Order(
                user_id="user1",
                symbol="BTC-USD",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                price=Decimal(f"{50000 + i * 100}"),
                quantity=Decimal("1.0")
            )
            order_manager.submit_order(order)
        
        # Cancel all
        cancelled_count = order_manager.cancel_all_orders("user1")
        
        assert cancelled_count == 3
        
        # Verify all cancelled
        orders = order_manager.get_user_orders("user1")
        assert all(o.status == OrderStatus.CANCELLED for o in orders)
    
    def test_get_statistics(self, order_manager):
        """Test getting order manager statistics"""
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
            order_manager.submit_order(order)
        
        stats = order_manager.get_statistics()
        
        assert stats["total_orders_processed"] == 3
        assert "action_counts" in stats
        assert stats["action_counts"]["submit"] == 3
        assert "validator_stats" in stats
        assert "matching_engine_stats" in stats
