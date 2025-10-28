"""
Performance benchmarks for the matching engine.

Run with: pytest tests/performance/benchmark_matching_engine.py --benchmark-only
"""

import pytest
from decimal import Decimal
import random

from src.matching_engine.core import MatchingEngine, Order, OrderSide, OrderType


class TestMatchingEnginePerformance:
    """Performance benchmarks for matching engine"""
    
    def test_benchmark_order_insertion(self, benchmark):
        """Benchmark order insertion speed"""
        engine = MatchingEngine()
        
        def insert_order():
            order = Order(
                user_id="user1",
                symbol="BTC-USD",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                price=Decimal(str(random.randint(45000, 55000))),
                quantity=Decimal("1.0")
            )
            engine.process_order(order)
        
        result = benchmark(insert_order)
        print(f"\nOrder insertion: {result.stats.mean * 1000:.3f}ms avg")
    
    def test_benchmark_order_matching(self, benchmark):
        """Benchmark order matching speed"""
        engine = MatchingEngine()
        
        # Pre-populate order book
        for i in range(100):
            sell_order = Order(
                user_id=f"seller{i}",
                symbol="BTC-USD",
                side=OrderSide.SELL,
                order_type=OrderType.LIMIT,
                price=Decimal("50000"),
                quantity=Decimal("1.0")
            )
            engine.process_order(sell_order)
        
        def match_order():
            buy_order = Order(
                user_id="buyer",
                symbol="BTC-USD",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                price=Decimal("50000"),
                quantity=Decimal("1.0")
            )
            engine.process_order(buy_order)
        
        result = benchmark(match_order)
        print(f"\nOrder matching: {result.stats.mean * 1000:.3f}ms avg")
    
    def test_benchmark_market_order(self, benchmark):
        """Benchmark market order execution"""
        engine = MatchingEngine()
        
        # Pre-populate order book with multiple price levels
        for price in range(50000, 50100, 10):
            for i in range(10):
                sell_order = Order(
                    user_id=f"seller{price}{i}",
                    symbol="BTC-USD",
                    side=OrderSide.SELL,
                    order_type=OrderType.LIMIT,
                    price=Decimal(str(price)),
                    quantity=Decimal("0.1")
                )
                engine.process_order(sell_order)
        
        def execute_market_order():
            market_order = Order(
                user_id="buyer",
                symbol="BTC-USD",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=Decimal("5.0")
            )
            engine.process_order(market_order)
        
        result = benchmark(execute_market_order)
        print(f"\nMarket order execution: {result.stats.mean * 1000:.3f}ms avg")
    
    def test_benchmark_order_cancellation(self, benchmark):
        """Benchmark order cancellation speed"""
        engine = MatchingEngine()
        
        # Pre-populate with orders
        order_ids = []
        for i in range(1000):
            order = Order(
                user_id=f"user{i}",
                symbol="BTC-USD",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                price=Decimal(str(random.randint(45000, 55000))),
                quantity=Decimal("1.0")
            )
            engine.process_order(order)
            order_ids.append(order.order_id)
        
        idx = [0]
        def cancel_order():
            if idx[0] < len(order_ids):
                engine.cancel_order("BTC-USD", order_ids[idx[0]])
                idx[0] += 1
        
        result = benchmark(cancel_order)
        print(f"\nOrder cancellation: {result.stats.mean * 1000:.3f}ms avg")
    
    def test_benchmark_order_book_depth(self, benchmark):
        """Benchmark order book depth calculation"""
        engine = MatchingEngine()
        
        # Build large order book
        for i in range(500):
            buy_order = Order(
                user_id=f"buyer{i}",
                symbol="BTC-USD",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                price=Decimal(str(50000 - i)),
                quantity=Decimal("1.0")
            )
            engine.process_order(buy_order)
            
            sell_order = Order(
                user_id=f"seller{i}",
                symbol="BTC-USD",
                side=OrderSide.SELL,
                order_type=OrderType.LIMIT,
                price=Decimal(str(51000 + i)),
                quantity=Decimal("1.0")
            )
            engine.process_order(sell_order)
        
        book = engine.get_order_book("BTC-USD")
        
        def get_depth():
            book.get_depth(levels=20)
        
        result = benchmark(get_depth)
        print(f"\nOrder book depth: {result.stats.mean * 1000:.3f}ms avg")
    
    def test_benchmark_high_frequency_trading(self, benchmark):
        """Benchmark high-frequency trading scenario"""
        engine = MatchingEngine()
        
        def hft_scenario():
            # Rapid order placement and cancellation
            orders = []
            
            # Place 10 orders
            for i in range(10):
                order = Order(
                    user_id="hft_trader",
                    symbol="BTC-USD",
                    side=random.choice([OrderSide.BUY, OrderSide.SELL]),
                    order_type=OrderType.LIMIT,
                    price=Decimal(str(random.randint(49000, 51000))),
                    quantity=Decimal("0.1")
                )
                engine.process_order(order)
                orders.append(order)
            
            # Cancel half of them
            for order in orders[:5]:
                engine.cancel_order("BTC-USD", order.order_id)
        
        result = benchmark(hft_scenario)
        print(f"\nHFT scenario (10 orders + 5 cancels): {result.stats.mean * 1000:.3f}ms avg")
    
    def test_benchmark_large_order_sweep(self, benchmark):
        """Benchmark large order sweeping through order book"""
        engine = MatchingEngine()
        
        # Build deep order book
        for price in range(50000, 50500, 10):
            for i in range(5):
                sell_order = Order(
                    user_id=f"seller{price}{i}",
                    symbol="BTC-USD",
                    side=OrderSide.SELL,
                    order_type=OrderType.LIMIT,
                    price=Decimal(str(price)),
                    quantity=Decimal("1.0")
                )
                engine.process_order(sell_order)
        
        def large_sweep():
            buy_order = Order(
                user_id="whale",
                symbol="BTC-USD",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=Decimal("100.0")
            )
            engine.process_order(buy_order)
        
        result = benchmark(large_sweep)
        print(f"\nLarge order sweep: {result.stats.mean * 1000:.3f}ms avg")
    
    def test_benchmark_multi_symbol_trading(self, benchmark):
        """Benchmark multi-symbol trading"""
        engine = MatchingEngine()
        
        symbols = ["BTC-USD", "ETH-USD", "SOL-USD", "AVAX-USD", "MATIC-USD"]
        
        def multi_symbol_trade():
            for symbol in symbols:
                # Place buy and sell order for each symbol
                buy_order = Order(
                    user_id="trader",
                    symbol=symbol,
                    side=OrderSide.BUY,
                    order_type=OrderType.LIMIT,
                    price=Decimal("1000"),
                    quantity=Decimal("1.0")
                )
                engine.process_order(buy_order)
                
                sell_order = Order(
                    user_id="trader2",
                    symbol=symbol,
                    side=OrderSide.SELL,
                    order_type=OrderType.LIMIT,
                    price=Decimal("1000"),
                    quantity=Decimal("1.0")
                )
                engine.process_order(sell_order)
        
        result = benchmark(multi_symbol_trade)
        print(f"\nMulti-symbol trading (5 symbols): {result.stats.mean * 1000:.3f}ms avg")


class TestScalabilityBenchmarks:
    """Scalability benchmarks"""
    
    def test_throughput_1000_orders(self):
        """Test throughput with 1000 orders"""
        import time
        
        engine = MatchingEngine()
        
        start = time.time()
        
        for i in range(1000):
            order = Order(
                user_id=f"user{i}",
                symbol="BTC-USD",
                side=random.choice([OrderSide.BUY, OrderSide.SELL]),
                order_type=OrderType.LIMIT,
                price=Decimal(str(random.randint(45000, 55000))),
                quantity=Decimal("1.0")
            )
            engine.process_order(order)
        
        elapsed = time.time() - start
        throughput = 1000 / elapsed
        
        print(f"\nThroughput (1000 orders): {throughput:.2f} orders/sec")
        print(f"Average latency: {elapsed/1000*1000:.3f}ms per order")
        
        assert throughput > 1000  # Should handle at least 1000 orders/sec
    
    def test_throughput_10000_orders(self):
        """Test throughput with 10,000 orders"""
        import time
        
        engine = MatchingEngine()
        
        start = time.time()
        
        for i in range(10000):
            order = Order(
                user_id=f"user{i}",
                symbol="BTC-USD",
                side=random.choice([OrderSide.BUY, OrderSide.SELL]),
                order_type=OrderType.LIMIT,
                price=Decimal(str(random.randint(45000, 55000))),
                quantity=Decimal("1.0")
            )
            engine.process_order(order)
        
        elapsed = time.time() - start
        throughput = 10000 / elapsed
        
        print(f"\nThroughput (10,000 orders): {throughput:.2f} orders/sec")
        print(f"Average latency: {elapsed/10000*1000:.3f}ms per order")
        
        assert throughput > 500  # Should handle at least 500 orders/sec
    
    def test_memory_usage(self):
        """Test memory usage with large order book"""
        import sys
        
        engine = MatchingEngine()
        
        # Add 10,000 orders
        for i in range(10000):
            order = Order(
                user_id=f"user{i}",
                symbol="BTC-USD",
                side=random.choice([OrderSide.BUY, OrderSide.SELL]),
                order_type=OrderType.LIMIT,
                price=Decimal(str(random.randint(45000, 55000))),
                quantity=Decimal("1.0")
            )
            engine.process_order(order)
        
        # Estimate memory usage
        book = engine.get_order_book("BTC-USD")
        order_count = book.order_count
        
        print(f"\nOrders in book: {order_count}")
        print(f"Bid levels: {len(book.bid_prices)}")
        print(f"Ask levels: {len(book.ask_prices)}")
        
        # Basic memory check
        assert order_count > 0
        assert len(book.bid_prices) > 0 or len(book.ask_prices) > 0


class TestLatencyBenchmarks:
    """Latency benchmarks for different scenarios"""
    
    def test_best_case_latency(self, benchmark):
        """Best case: Order matches immediately"""
        engine = MatchingEngine()
        
        # Pre-place sell order
        sell_order = Order(
            user_id="seller",
            symbol="BTC-USD",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1.0")
        )
        engine.process_order(sell_order)
        
        def immediate_match():
            buy_order = Order(
                user_id="buyer",
                symbol="BTC-USD",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                price=Decimal("50000"),
                quantity=Decimal("1.0")
            )
            engine.process_order(buy_order)
        
        result = benchmark(immediate_match)
        print(f"\nBest case latency: {result.stats.mean * 1000:.3f}ms")
    
    def test_worst_case_latency(self, benchmark):
        """Worst case: Order sweeps through many price levels"""
        engine = MatchingEngine()
        
        # Build deep order book
        for price in range(50000, 51000, 10):
            sell_order = Order(
                user_id=f"seller{price}",
                symbol="BTC-USD",
                side=OrderSide.SELL,
                order_type=OrderType.LIMIT,
                price=Decimal(str(price)),
                quantity=Decimal("0.1")
            )
            engine.process_order(sell_order)
        
        def sweep_book():
            buy_order = Order(
                user_id="buyer",
                symbol="BTC-USD",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=Decimal("10.0")
            )
            engine.process_order(buy_order)
        
        result = benchmark(sweep_book)
        print(f"\nWorst case latency: {result.stats.mean * 1000:.3f}ms")
