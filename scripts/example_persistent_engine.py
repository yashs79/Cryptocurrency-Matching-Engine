#!/usr/bin/env python3
"""
Example: Using Persistent Matching Engine

Simple example showing how to use the matching engine with automatic persistence.
"""

import sys
from pathlib import Path
from decimal import Decimal

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.matching_engine.persistence.order_book_persistence import PersistentMatchingEngine, PersistenceConfig
from src.matching_engine.core.order import Order, OrderSide, OrderType
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Example usage of persistent matching engine"""
    
    logger.info("🚀 Starting Persistent Matching Engine\n")
    
    # Configure persistence
    config = PersistenceConfig(
        database_url="sqlite:///./matching_engine.db",
        auto_save=True,  # Automatically save after each operation
        echo_sql=False
    )
    
    # Create persistent matching engine
    # It will automatically restore previous state if available
    with PersistentMatchingEngine(config, auto_restore=True) as engine:
        
        logger.info("📝 Submitting orders...\n")
        
        # Submit some orders
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
                side=OrderSide.SELL,
                order_type=OrderType.LIMIT,
                price=Decimal("50000"),
                quantity=Decimal("0.5")
            ),
        ]
        
        for order in orders:
            processed, trades = engine.process_order(order)
            
            side_str = "BUY" if order.side.value == "buy" else "SELL"
            logger.info(
                f"✓ {order.user_id}: {side_str} {order.quantity} {order.symbol} @ ${order.price}"
            )
            
            if trades:
                logger.info(f"  🎯 Matched! {len(trades)} trade(s)")
                for trade in trades:
                    logger.info(f"     Trade: {trade.quantity} @ ${trade.price}")
        
        # Show current state
        logger.info("\n📊 Current Order Book State:")
        for symbol, order_book in engine.order_books.items():
            buy_count = sum(len(orders) for orders in order_book.buy_orders.values())
            sell_count = sum(len(orders) for orders in order_book.sell_orders.values())
            logger.info(f"   {symbol}: {buy_count} buy orders, {sell_count} sell orders")
        
        # Get persistence stats
        stats = engine.persistence.get_persistence_stats()
        logger.info(f"\n📈 Persistence Stats:")
        logger.info(f"   Total orders in DB: {stats['total_orders']}")
        logger.info(f"   Auto-save: {stats['auto_save_enabled']}")
        
        logger.info("\n✅ All operations automatically persisted!")
        logger.info("💾 State saved to: matching_engine.db")
        logger.info("\n🔄 Restart this script to see state restoration in action!")
    
    # Engine automatically saves on shutdown (context manager exit)


if __name__ == "__main__":
    main()
