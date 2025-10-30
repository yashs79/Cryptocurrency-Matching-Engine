"""
Unit tests for TradeRepository
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta, UTC

from src.matching_engine.core.trade import Trade, SettlementStatus
from src.matching_engine.repositories import TradeRepository, TradeFilter
from src.matching_engine.config.database import init_db


class TestTradeRepository:
    """Test TradeRepository"""
    
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
    def sample_trade(self):
        """Create sample trade"""
        return Trade(
            symbol='BTC-USD',
            buyer_order_id='buy-123',
            seller_order_id='sell-456',
            buyer_user_id='alice',
            seller_user_id='bob',
            price=Decimal('50000.00'),
            quantity=Decimal('1.5')
        )
    
    def test_save_and_get_trade(self, repository, sample_trade):
        """Test saving and retrieving a trade"""
        repository.save(sample_trade)
        
        retrieved = repository.get(sample_trade.trade_id)
        
        assert retrieved is not None
        assert retrieved.trade_id == sample_trade.trade_id
        assert retrieved.symbol == sample_trade.symbol
        assert retrieved.buyer_user_id == sample_trade.buyer_user_id
        assert retrieved.seller_user_id == sample_trade.seller_user_id
        assert retrieved.price == sample_trade.price
        assert retrieved.quantity == sample_trade.quantity
    
    def test_get_nonexistent_trade(self, repository):
        """Test getting a trade that doesn't exist"""
        result = repository.get('nonexistent-id')
        assert result is None
    
    def test_save_updates_existing_trade(self, repository, sample_trade):
        """Test that saving updates existing trade"""
        repository.save(sample_trade)
        
        # Settle the trade
        sample_trade.settle()
        repository.save(sample_trade)
        
        retrieved = repository.get(sample_trade.trade_id)
        assert retrieved.settlement_status == SettlementStatus.SETTLED
        assert retrieved.settled_at is not None
    
    def test_find_all_trades(self, repository):
        """Test finding all trades"""
        # Create multiple trades
        trades = []
        for i in range(5):
            trade = Trade(
                symbol='BTC-USD',
                buyer_order_id=f'buy-{i}',
                seller_order_id=f'sell-{i}',
                buyer_user_id=f'buyer{i}',
                seller_user_id=f'seller{i}',
                price=Decimal(f'{50000 + i * 100}'),
                quantity=Decimal('1.0')
            )
            trades.append(trade)
            repository.save(trade)
        
        results = repository.find()
        
        assert len(results) == 5
    
    def test_find_with_limit(self, repository):
        """Test finding trades with limit"""
        # Create 10 trades
        for i in range(10):
            trade = Trade(
                symbol='BTC-USD',
                buyer_order_id=f'buy-{i}',
                seller_order_id=f'sell-{i}',
                buyer_user_id=f'buyer{i}',
                seller_user_id=f'seller{i}',
                price=Decimal('50000'),
                quantity=Decimal('1.0')
            )
            repository.save(trade)
        
        results = repository.find(limit=5)
        
        assert len(results) == 5
    
    def test_find_with_offset(self, repository):
        """Test finding trades with offset"""
        # Create 10 trades
        for i in range(10):
            trade = Trade(
                symbol='BTC-USD',
                buyer_order_id=f'buy-{i}',
                seller_order_id=f'sell-{i}',
                buyer_user_id=f'buyer{i}',
                seller_user_id=f'seller{i}',
                price=Decimal('50000'),
                quantity=Decimal('1.0')
            )
            repository.save(trade)
        
        results = repository.find(limit=5, offset=5)
        
        assert len(results) == 5
    
    def test_find_by_symbol(self, repository):
        """Test finding trades by symbol"""
        # Create trades for different symbols
        btc_trade = Trade(
            symbol='BTC-USD',
            buyer_order_id='buy-1',
            seller_order_id='sell-1',
            buyer_user_id='alice',
            seller_user_id='bob',
            price=Decimal('50000'),
            quantity=Decimal('1.0')
        )
        repository.save(btc_trade)
        
        eth_trade = Trade(
            symbol='ETH-USD',
            buyer_order_id='buy-2',
            seller_order_id='sell-2',
            buyer_user_id='alice',
            seller_user_id='bob',
            price=Decimal('3000'),
            quantity=Decimal('10.0')
        )
        repository.save(eth_trade)
        
        btc_results = repository.find_by_symbol('BTC-USD')
        eth_results = repository.find_by_symbol('ETH-USD')
        
        assert len(btc_results) == 1
        assert len(eth_results) == 1
        assert btc_results[0].symbol == 'BTC-USD'
        assert eth_results[0].symbol == 'ETH-USD'
    
    def test_find_by_user(self, repository):
        """Test finding trades by user"""
        # Create trades
        trade1 = Trade(
            symbol='BTC-USD',
            buyer_order_id='buy-1',
            seller_order_id='sell-1',
            buyer_user_id='alice',
            seller_user_id='bob',
            price=Decimal('50000'),
            quantity=Decimal('1.0')
        )
        repository.save(trade1)
        
        trade2 = Trade(
            symbol='ETH-USD',
            buyer_order_id='buy-2',
            seller_order_id='sell-2',
            buyer_user_id='charlie',
            seller_user_id='alice',
            price=Decimal('3000'),
            quantity=Decimal('10.0')
        )
        repository.save(trade2)
        
        alice_trades = repository.find_by_user('alice')
        bob_trades = repository.find_by_user('bob')
        charlie_trades = repository.find_by_user('charlie')
        
        assert len(alice_trades) == 2  # Alice is buyer in trade1, seller in trade2
        assert len(bob_trades) == 1
        assert len(charlie_trades) == 1
    
    def test_find_by_order(self, repository):
        """Test finding trades by order ID"""
        trade = Trade(
            symbol='BTC-USD',
            buyer_order_id='buy-123',
            seller_order_id='sell-456',
            buyer_user_id='alice',
            seller_user_id='bob',
            price=Decimal('50000'),
            quantity=Decimal('1.0')
        )
        repository.save(trade)
        
        buyer_trades = repository.find_by_order('buy-123')
        seller_trades = repository.find_by_order('sell-456')
        
        assert len(buyer_trades) == 1
        assert len(seller_trades) == 1
        assert buyer_trades[0].buyer_order_id == 'buy-123'
        assert seller_trades[0].seller_order_id == 'sell-456'
    
    def test_find_by_time_range(self, repository):
        """Test finding trades by time range"""
        now = datetime.now(UTC)
        
        # Create trades at different times
        old_trade = Trade(
            symbol='BTC-USD',
            buyer_order_id='buy-1',
            seller_order_id='sell-1',
            buyer_user_id='alice',
            seller_user_id='bob',
            price=Decimal('50000'),
            quantity=Decimal('1.0')
        )
        old_trade.timestamp = now - timedelta(hours=2)
        repository.save(old_trade)
        
        recent_trade = Trade(
            symbol='BTC-USD',
            buyer_order_id='buy-2',
            seller_order_id='sell-2',
            buyer_user_id='alice',
            seller_user_id='bob',
            price=Decimal('50000'),
            quantity=Decimal('1.0')
        )
        recent_trade.timestamp = now - timedelta(minutes=30)
        repository.save(recent_trade)
        
        # Find trades in last hour
        start_time = now - timedelta(hours=1)
        end_time = now
        
        results = repository.find_by_time_range(start_time, end_time)
        
        assert len(results) == 1
        assert results[0].trade_id == recent_trade.trade_id
    
    def test_find_with_filter(self, repository):
        """Test finding trades with complex filter"""
        # Create trades
        for i in range(5):
            trade = Trade(
                symbol='BTC-USD' if i % 2 == 0 else 'ETH-USD',
                buyer_order_id=f'buy-{i}',
                seller_order_id=f'sell-{i}',
                buyer_user_id='alice',
                seller_user_id='bob',
                price=Decimal(f'{50000 + i * 1000}'),
                quantity=Decimal('1.0')
            )
            if i >= 3:
                trade.settle()
            repository.save(trade)
        
        # Filter for BTC-USD settled trades
        filter = TradeFilter(
            symbol='BTC-USD',
            settlement_status=SettlementStatus.SETTLED
        )
        
        results = repository.find(filter=filter)
        
        assert len(results) == 1  # Only one BTC-USD trade with i=4 is settled
    
    def test_get_volume_by_symbol(self, repository):
        """Test getting trading volume by symbol"""
        # Create settled trades
        trade1 = Trade(
            symbol='BTC-USD',
            buyer_order_id='buy-1',
            seller_order_id='sell-1',
            buyer_user_id='alice',
            seller_user_id='bob',
            price=Decimal('50000'),
            quantity=Decimal('1.5')
        )
        trade1.settle()
        repository.save(trade1)
        
        trade2 = Trade(
            symbol='BTC-USD',
            buyer_order_id='buy-2',
            seller_order_id='sell-2',
            buyer_user_id='alice',
            seller_user_id='bob',
            price=Decimal('50000'),
            quantity=Decimal('2.5')
        )
        trade2.settle()
        repository.save(trade2)
        
        volume = repository.get_volume_by_symbol('BTC-USD')
        
        assert volume == Decimal('4.0')
    
    def test_get_volume_by_user(self, repository):
        """Test getting trading volume by user"""
        # Create settled trades
        trade1 = Trade(
            symbol='BTC-USD',
            buyer_order_id='buy-1',
            seller_order_id='sell-1',
            buyer_user_id='alice',
            seller_user_id='bob',
            price=Decimal('50000'),
            quantity=Decimal('1.5')
        )
        trade1.settle()
        repository.save(trade1)
        
        trade2 = Trade(
            symbol='ETH-USD',
            buyer_order_id='buy-2',
            seller_order_id='sell-2',
            buyer_user_id='charlie',
            seller_user_id='alice',
            price=Decimal('3000'),
            quantity=Decimal('10.0')
        )
        trade2.settle()
        repository.save(trade2)
        
        alice_volume = repository.get_volume_by_user('alice')
        
        # Alice is in both trades
        assert alice_volume == Decimal('11.5')
    
    def test_get_statistics(self, repository):
        """Test getting trade statistics"""
        # Create trades with different statuses
        for i in range(5):
            trade = Trade(
                symbol='BTC-USD',
                buyer_order_id=f'buy-{i}',
                seller_order_id=f'sell-{i}',
                buyer_user_id=f'user{i}',
                seller_user_id=f'user{i+5}',
                price=Decimal('50000'),
                quantity=Decimal('1.0')
            )
            if i < 3:
                trade.settle()
            repository.save(trade)
        
        stats = repository.get_statistics()
        
        assert stats['total_trades'] == 5
        assert stats['status_breakdown']['settled'] == 3
        assert stats['status_breakdown']['pending'] == 2
        assert stats['unique_symbols'] == 1
    
    def test_count_trades(self, repository):
        """Test counting trades"""
        # Create trades
        for i in range(10):
            trade = Trade(
                symbol='BTC-USD',
                buyer_order_id=f'buy-{i}',
                seller_order_id=f'sell-{i}',
                buyer_user_id='alice',
                seller_user_id='bob',
                price=Decimal('50000'),
                quantity=Decimal('1.0')
            )
            repository.save(trade)
        
        count = repository.count()
        
        assert count == 10
    
    def test_count_with_filter(self, repository):
        """Test counting trades with filter"""
        # Create trades
        for i in range(5):
            trade = Trade(
                symbol='BTC-USD' if i % 2 == 0 else 'ETH-USD',
                buyer_order_id=f'buy-{i}',
                seller_order_id=f'sell-{i}',
                buyer_user_id='alice',
                seller_user_id='bob',
                price=Decimal('50000'),
                quantity=Decimal('1.0')
            )
            repository.save(trade)
        
        filter = TradeFilter(symbol='BTC-USD')
        count = repository.count(filter=filter)
        
        assert count == 3  # Indices 0, 2, 4
    
    def test_delete_trade(self, repository, sample_trade):
        """Test deleting a trade"""
        repository.save(sample_trade)
        
        # Verify it exists
        assert repository.get(sample_trade.trade_id) is not None
        
        # Delete it
        result = repository.delete(sample_trade.trade_id)
        
        assert result is True
        assert repository.get(sample_trade.trade_id) is None
    
    def test_delete_nonexistent_trade(self, repository):
        """Test deleting a trade that doesn't exist"""
        result = repository.delete('nonexistent-id')
        
        assert result is False
    
    def test_filter_by_price_range(self, repository):
        """Test filtering trades by price range"""
        # Create trades with different prices
        for i in range(5):
            trade = Trade(
                symbol='BTC-USD',
                buyer_order_id=f'buy-{i}',
                seller_order_id=f'sell-{i}',
                buyer_user_id='alice',
                seller_user_id='bob',
                price=Decimal(f'{50000 + i * 1000}'),
                quantity=Decimal('1.0')
            )
            repository.save(trade)
        
        # Find trades between 51000 and 53000
        filter = TradeFilter(
            min_price=Decimal('51000'),
            max_price=Decimal('53000')
        )
        
        results = repository.find(filter=filter)
        
        assert len(results) == 3  # Prices: 51000, 52000, 53000
    
    def test_filter_by_quantity_range(self, repository):
        """Test filtering trades by quantity range"""
        # Create trades with different quantities
        for i in range(5):
            trade = Trade(
                symbol='BTC-USD',
                buyer_order_id=f'buy-{i}',
                seller_order_id=f'sell-{i}',
                buyer_user_id='alice',
                seller_user_id='bob',
                price=Decimal('50000'),
                quantity=Decimal(f'{i + 1}.0')
            )
            repository.save(trade)
        
        # Find trades with quantity between 2 and 4
        filter = TradeFilter(
            min_quantity=Decimal('2.0'),
            max_quantity=Decimal('4.0')
        )
        
        results = repository.find(filter=filter)
        
        assert len(results) == 3  # Quantities: 2, 3, 4
    
    def test_repository_close(self, repository):
        """Test closing repository"""
        repository.close()
        # Should not raise any errors
