"""
Unit tests for Trade model
"""

import pytest
from decimal import Decimal
from datetime import datetime, UTC

from src.matching_engine.core.trade import Trade, SettlementStatus


class TestTrade:
    """Test Trade model"""
    
    @pytest.fixture
    def sample_trade_data(self):
        """Sample trade data for testing"""
        return {
            'symbol': 'BTC-USD',
            'buyer_order_id': 'buy-123',
            'seller_order_id': 'sell-456',
            'buyer_user_id': 'alice',
            'seller_user_id': 'bob',
            'price': Decimal('50000.00'),
            'quantity': Decimal('1.5')
        }
    
    def test_trade_creation(self, sample_trade_data):
        """Test creating a trade"""
        trade = Trade(**sample_trade_data)
        
        assert trade.trade_id is not None
        assert len(trade.trade_id) > 0
        assert trade.symbol == 'BTC-USD'
        assert trade.buyer_order_id == 'buy-123'
        assert trade.seller_order_id == 'sell-456'
        assert trade.buyer_user_id == 'alice'
        assert trade.seller_user_id == 'bob'
        assert trade.price == Decimal('50000.00')
        assert trade.quantity == Decimal('1.5')
        assert trade.settlement_status == SettlementStatus.PENDING
        assert trade.maker_fee == Decimal('0')
        assert trade.taker_fee == Decimal('0')
        assert isinstance(trade.timestamp, datetime)
    
    def test_trade_validation_missing_symbol(self, sample_trade_data):
        """Test trade validation fails without symbol"""
        sample_trade_data['symbol'] = ''
        
        with pytest.raises(ValueError, match="Symbol is required"):
            Trade(**sample_trade_data)
    
    def test_trade_validation_missing_buyer_order(self, sample_trade_data):
        """Test trade validation fails without buyer order ID"""
        sample_trade_data['buyer_order_id'] = ''
        
        with pytest.raises(ValueError, match="Buyer order ID is required"):
            Trade(**sample_trade_data)
    
    def test_trade_validation_missing_seller_order(self, sample_trade_data):
        """Test trade validation fails without seller order ID"""
        sample_trade_data['seller_order_id'] = ''
        
        with pytest.raises(ValueError, match="Seller order ID is required"):
            Trade(**sample_trade_data)
    
    def test_trade_validation_missing_buyer_user(self, sample_trade_data):
        """Test trade validation fails without buyer user ID"""
        sample_trade_data['buyer_user_id'] = ''
        
        with pytest.raises(ValueError, match="Buyer user ID is required"):
            Trade(**sample_trade_data)
    
    def test_trade_validation_missing_seller_user(self, sample_trade_data):
        """Test trade validation fails without seller user ID"""
        sample_trade_data['seller_user_id'] = ''
        
        with pytest.raises(ValueError, match="Seller user ID is required"):
            Trade(**sample_trade_data)
    
    def test_trade_validation_invalid_price(self, sample_trade_data):
        """Test trade validation fails with invalid price"""
        sample_trade_data['price'] = Decimal('0')
        
        with pytest.raises(ValueError, match="Price must be positive"):
            Trade(**sample_trade_data)
    
    def test_trade_validation_negative_price(self, sample_trade_data):
        """Test trade validation fails with negative price"""
        sample_trade_data['price'] = Decimal('-100')
        
        with pytest.raises(ValueError, match="Price must be positive"):
            Trade(**sample_trade_data)
    
    def test_trade_validation_invalid_quantity(self, sample_trade_data):
        """Test trade validation fails with invalid quantity"""
        sample_trade_data['quantity'] = Decimal('0')
        
        with pytest.raises(ValueError, match="Quantity must be positive"):
            Trade(**sample_trade_data)
    
    def test_total_value_calculation(self, sample_trade_data):
        """Test total value calculation"""
        trade = Trade(**sample_trade_data)
        
        expected_value = Decimal('50000.00') * Decimal('1.5')
        assert trade.total_value == expected_value
        assert trade.total_value == Decimal('75000.00')
    
    def test_total_fees_calculation(self, sample_trade_data):
        """Test total fees calculation"""
        sample_trade_data['maker_fee'] = Decimal('10.00')
        sample_trade_data['taker_fee'] = Decimal('15.00')
        
        trade = Trade(**sample_trade_data)
        
        assert trade.total_fees == Decimal('25.00')
    
    def test_is_settled_property(self, sample_trade_data):
        """Test is_settled property"""
        trade = Trade(**sample_trade_data)
        
        assert not trade.is_settled
        
        trade.settlement_status = SettlementStatus.SETTLED
        assert trade.is_settled
    
    def test_is_pending_property(self, sample_trade_data):
        """Test is_pending property"""
        trade = Trade(**sample_trade_data)
        
        assert trade.is_pending
        
        trade.settlement_status = SettlementStatus.SETTLED
        assert not trade.is_pending
    
    def test_is_failed_property(self, sample_trade_data):
        """Test is_failed property"""
        trade = Trade(**sample_trade_data)
        
        assert not trade.is_failed
        
        trade.settlement_status = SettlementStatus.FAILED
        assert trade.is_failed
    
    def test_settle_trade(self, sample_trade_data):
        """Test settling a trade"""
        trade = Trade(**sample_trade_data)
        
        assert trade.settlement_status == SettlementStatus.PENDING
        assert trade.settled_at is None
        
        trade.settle()
        
        assert trade.settlement_status == SettlementStatus.SETTLED
        assert trade.settled_at is not None
        assert isinstance(trade.settled_at, datetime)
        assert trade.is_settled
    
    def test_settle_already_settled_trade(self, sample_trade_data):
        """Test settling an already settled trade fails"""
        trade = Trade(**sample_trade_data)
        trade.settle()
        
        with pytest.raises(ValueError, match="Cannot settle trade with status settled"):
            trade.settle()
    
    def test_fail_settlement(self, sample_trade_data):
        """Test failing trade settlement"""
        trade = Trade(**sample_trade_data)
        
        trade.fail_settlement("Insufficient funds")
        
        assert trade.settlement_status == SettlementStatus.FAILED
        assert trade.is_failed
        assert trade.metadata['failure_reason'] == "Insufficient funds"
    
    def test_fail_settlement_without_reason(self, sample_trade_data):
        """Test failing settlement without reason"""
        trade = Trade(**sample_trade_data)
        
        trade.fail_settlement()
        
        assert trade.settlement_status == SettlementStatus.FAILED
        assert 'failure_reason' not in trade.metadata
    
    def test_fail_already_settled_trade(self, sample_trade_data):
        """Test failing an already settled trade"""
        trade = Trade(**sample_trade_data)
        trade.settle()
        
        with pytest.raises(ValueError, match="Cannot fail trade with status settled"):
            trade.fail_settlement()
    
    def test_cancel_trade(self, sample_trade_data):
        """Test cancelling a trade"""
        trade = Trade(**sample_trade_data)
        
        trade.cancel("User requested cancellation")
        
        assert trade.settlement_status == SettlementStatus.CANCELLED
        assert trade.metadata['cancellation_reason'] == "User requested cancellation"
    
    def test_cancel_settled_trade(self, sample_trade_data):
        """Test cannot cancel settled trade"""
        trade = Trade(**sample_trade_data)
        trade.settle()
        
        with pytest.raises(ValueError, match="Cannot cancel settled trade"):
            trade.cancel()
    
    def test_to_dict(self, sample_trade_data):
        """Test converting trade to dictionary"""
        trade = Trade(**sample_trade_data)
        trade_dict = trade.to_dict()
        
        assert trade_dict['trade_id'] == trade.trade_id
        assert trade_dict['symbol'] == 'BTC-USD'
        assert trade_dict['buyer_order_id'] == 'buy-123'
        assert trade_dict['seller_order_id'] == 'sell-456'
        assert trade_dict['buyer_user_id'] == 'alice'
        assert trade_dict['seller_user_id'] == 'bob'
        assert Decimal(trade_dict['price']) == Decimal('50000.00')
        assert Decimal(trade_dict['quantity']) == Decimal('1.5')
        assert Decimal(trade_dict['total_value']) == Decimal('75000.00')
        assert trade_dict['settlement_status'] == 'pending'
        assert trade_dict['maker_fee'] == '0'
        assert trade_dict['taker_fee'] == '0'
        assert trade_dict['total_fees'] == '0'
        assert isinstance(trade_dict['timestamp'], str)
    
    def test_from_dict(self, sample_trade_data):
        """Test creating trade from dictionary"""
        trade = Trade(**sample_trade_data)
        trade_dict = trade.to_dict()
        
        restored_trade = Trade.from_dict(trade_dict)
        
        assert restored_trade.trade_id == trade.trade_id
        assert restored_trade.symbol == trade.symbol
        assert restored_trade.buyer_order_id == trade.buyer_order_id
        assert restored_trade.seller_order_id == trade.seller_order_id
        assert restored_trade.buyer_user_id == trade.buyer_user_id
        assert restored_trade.seller_user_id == trade.seller_user_id
        assert restored_trade.price == trade.price
        assert restored_trade.quantity == trade.quantity
        assert restored_trade.settlement_status == trade.settlement_status
    
    def test_trade_with_metadata(self, sample_trade_data):
        """Test trade with custom metadata"""
        sample_trade_data['metadata'] = {
            'source': 'api',
            'ip_address': '192.168.1.1',
            'tags': ['high_value', 'verified']
        }
        
        trade = Trade(**sample_trade_data)
        
        assert trade.metadata['source'] == 'api'
        assert trade.metadata['ip_address'] == '192.168.1.1'
        assert 'high_value' in trade.metadata['tags']
    
    def test_trade_repr(self, sample_trade_data):
        """Test trade string representation"""
        trade = Trade(**sample_trade_data)
        
        repr_str = repr(trade)
        assert 'Trade' in repr_str
        assert 'BTC-USD' in repr_str
        assert 'pending' in repr_str
    
    def test_trade_str(self, sample_trade_data):
        """Test trade human-readable string"""
        trade = Trade(**sample_trade_data)
        
        str_repr = str(trade)
        assert 'Trade' in str_repr
        assert '1.5' in str_repr
        assert 'BTC-USD' in str_repr
        assert '50000' in str_repr
    
    def test_settlement_status_transitions(self, sample_trade_data):
        """Test valid settlement status transitions"""
        trade = Trade(**sample_trade_data)
        
        # PENDING -> SETTLED
        assert trade.settlement_status == SettlementStatus.PENDING
        trade.settle()
        assert trade.settlement_status == SettlementStatus.SETTLED
        
        # Create new trade for PENDING -> FAILED
        trade2 = Trade(**sample_trade_data)
        trade2.fail_settlement()
        assert trade2.settlement_status == SettlementStatus.FAILED
        
        # Create new trade for PENDING -> CANCELLED
        trade3 = Trade(**sample_trade_data)
        trade3.cancel()
        assert trade3.settlement_status == SettlementStatus.CANCELLED
    
    def test_trade_with_fees(self, sample_trade_data):
        """Test trade with maker and taker fees"""
        sample_trade_data['maker_fee'] = Decimal('7.50')  # 0.01% of 75000
        sample_trade_data['taker_fee'] = Decimal('37.50')  # 0.05% of 75000
        
        trade = Trade(**sample_trade_data)
        
        assert trade.maker_fee == Decimal('7.50')
        assert trade.taker_fee == Decimal('37.50')
        assert trade.total_fees == Decimal('45.00')
