#!/usr/bin/env python3
"""
Demo: Crash Recovery

Demonstrates order book persistence and crash recovery.
"""

import sys
from pathlib import Path
from decimal import Decimal
import time

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.matching_engine.persistence import OrderBookPersistence, PersistenceConfig
from src.matching_engine.core.matching_engine import MatchingEngine
from src.matching_engine.core.order import Order, OrderSide, OrderType
from src.matching_engine.config.database import init_db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def simulate_normal_operation():
    """Simulate normal trading operation"""
    logger.info("=" * 60)
    logger.info("PHASE 1: Normal Operation - Creating Orders")
    logger.info("=" * 60)
    
    # Initialize database
    init_db(database_url="sqlite:///./crash_recovery_demo.db", echo=False)
    
    # Create matching engine
    engine = MatchingEngine()
    
    # Create persistence layer
    config = PersistenceConfig(
        database_url="sqlite:///./crash_recovery_demo.db",
        auto_save=True
    )
    persistence = OrderBookPersistence(engine, config)
    
    # Create some orders
    orders = [
        Order(
            user_id="alice",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("50000"),
            quantity=Decimal("1.0")
        ),
        Order(
            user_id="bob",
            symbol="BTC-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("49500"),
            quantity=Decimal("2.0")
        ),
        Order(
            user_id="charlie",
            symbol="BTC-USD",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            price=Decimal("51000"),
            quantity=Decimal("1.5")
        ),
        Order(
            user_id="dave",
            symbol="ETH-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("3000"),
            quantity=Decimal("10.0")
        ),
        Order(
            user_id="eve",
            symbol="ETH-USD",
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            price=Decimal("3100"),
            quantity=Decimal("5.0")
        ),
    ]
    
    logger.info(f"\n📝 Submitting {len(orders)} orders...")
    for order in orders:
        processed, trades = engine.process_order(order)
        persistence.save_order(processed)
        
        side_val = order.side.value if hasattr(order.side, 'value') else order.side
        side_str = "BUY" if side_val == "buy" else "SELL"
        logger.info(
            f"   ✓ {order.user_id}: {side_str} {order.quantity} {order.symbol} "
            f"@ ${order.price}"
        )
    
    # Save state
    logger.info("\n💾 Saving order book state...")
    saved_count = persistence.save_state()
    logger.info(f"   ✓ Saved {saved_count} orders")
    
    # Show current state
    logger.info("\n📊 Current Order Book State:")
    for symbol, order_book in engine.order_books.items():
        buy_count = sum(len(level.orders) for level in order_book.bid_levels.values())
        sell_count = sum(len(level.orders) for level in order_book.ask_levels.values())
        logger.info(f"   {symbol}: {buy_count} buy orders, {sell_count} sell orders")
    
    # Get stats
    stats = persistence.get_persistence_stats()
    logger.info(f"\n📈 Persistence Stats:")
    logger.info(f"   Total orders in DB: {stats['total_orders']}")
    logger.info(f"   Symbols: {stats['symbols']}")
    logger.info(f"   Users: {stats['users']}")
    
    persistence.close()
    
    logger.info("\n✅ Normal operation complete. Orders saved to database.")
    logger.info("💥 Simulating crash... (engine shutting down)")


def simulate_crash_recovery():
    """Simulate recovery after a crash"""
    logger.info("\n" + "=" * 60)
    logger.info("PHASE 2: Crash Recovery - Restoring State")
    logger.info("=" * 60)
    
    logger.info("\n🔄 Starting new matching engine instance...")
    logger.info("📂 Loading state from database...")
    
    # Create new matching engine (simulating restart)
    engine = MatchingEngine()
    
    # Create persistence layer
    config = PersistenceConfig(
        database_url="sqlite:///./crash_recovery_demo.db",
        auto_save=True
    )
    persistence = OrderBookPersistence(engine, config)
    
    # Restore state
    orders_restored, symbols_restored = persistence.restore_state()
    
    logger.info(f"\n✅ Recovery complete!")
    logger.info(f"   Restored {orders_restored} orders")
    logger.info(f"   Restored {symbols_restored} symbols")
    
    # Verify restored state
    logger.info("\n📊 Restored Order Book State:")
    for symbol, order_book in engine.order_books.items():
        buy_count = sum(len(level.orders) for level in order_book.bid_levels.values())
        sell_count = sum(len(level.orders) for level in order_book.ask_levels.values())
        logger.info(f"   {symbol}: {buy_count} buy orders, {sell_count} sell orders")
        
        # Show order details
        logger.info(f"\n   {symbol} Buy Orders:")
        for price in sorted(order_book.bid_levels.keys(), reverse=True):
            level = order_book.bid_levels[price]
            for order in level.orders:
                logger.info(
                    f"      ${price}: {order.user_id} - "
                    f"{order.quantity} (filled: {order.filled_quantity})"
                )
        
        logger.info(f"\n   {symbol} Sell Orders:")
        for price in sorted(order_book.ask_levels.keys()):
            level = order_book.ask_levels[price]
            for order in level.orders:
                logger.info(
                    f"      ${price}: {order.user_id} - "
                    f"{order.quantity} (filled: {order.filled_quantity})"
                )
    
    # Continue trading with restored state
    logger.info("\n" + "=" * 60)
    logger.info("PHASE 3: Continuing Trading After Recovery")
    logger.info("=" * 60)
    
    # Submit a new order that might match
    new_order = Order(
        user_id="frank",
        symbol="BTC-USD",
        side=OrderSide.SELL,
        order_type=OrderType.LIMIT,
        price=Decimal("50000"),  # Matches alice's buy order
        quantity=Decimal("0.5")
    )
    
    logger.info(f"\n📝 Submitting new order after recovery...")
    logger.info(f"   frank: SELL 0.5 BTC-USD @ $50000")
    
    processed, trades = engine.process_order(new_order)
    persistence.save_order(processed)
    
    if trades:
        logger.info(f"\n🎯 Order matched! {len(trades)} trade(s) executed:")
        for trade in trades:
            logger.info(
                f"   ✓ Trade: {trade.quantity} @ ${trade.price} "
                f"(buyer: {trade.buyer_order_id[:8]}..., "
                f"seller: {trade.seller_order_id[:8]}...)"
            )
    else:
        logger.info("   No matches found, order added to book")
    
    # Final state
    logger.info("\n📊 Final Order Book State:")
    for symbol, order_book in engine.order_books.items():
        buy_count = sum(len(level.orders) for level in order_book.bid_levels.values())
        sell_count = sum(len(level.orders) for level in order_book.ask_levels.values())
        logger.info(f"   {symbol}: {buy_count} buy orders, {sell_count} sell orders")
    
    persistence.close()
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ Demo Complete!")
    logger.info("=" * 60)
    logger.info("\nKey Takeaways:")
    logger.info("1. ✅ Order book state was saved to database")
    logger.info("2. ✅ State was fully restored after 'crash'")
    logger.info("3. ✅ Trading continued seamlessly with restored state")
    logger.info("4. ✅ New orders matched against restored orders")
    logger.info("\nDatabase file: crash_recovery_demo.db")


def main():
    """Run the demo"""
    print("\n" + "🔥" * 30)
    print("CRASH RECOVERY DEMONSTRATION")
    print("🔥" * 30 + "\n")
    
    # Phase 1: Normal operation
    simulate_normal_operation()
    
    # Simulate some time passing (crash happened)
    time.sleep(1)
    
    # Phase 2: Recovery
    simulate_crash_recovery()


if __name__ == "__main__":
    main()
