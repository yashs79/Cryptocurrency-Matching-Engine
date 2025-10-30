#!/usr/bin/env python3
"""
Example: Using Database Repository

Demonstrates how to use the database-backed repository.
"""

import sys
from pathlib import Path
from decimal import Decimal

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.matching_engine.config.database import init_db
from src.matching_engine.repositories import DatabaseOrderRepository, OrderFilter
from src.matching_engine.core.order import Order, OrderSide, OrderType, OrderStatus
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Example usage of database repository"""
    
    # 1. Initialize database
    logger.info("1. Initializing database...")
    db_config = init_db(database_url="sqlite:///./example.db", echo=False)
    
    # 2. Create repository
    logger.info("2. Creating database repository...")
    repo = DatabaseOrderRepository()
    
    # 3. Create and save orders
    logger.info("3. Creating orders...")
    
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
            price=Decimal("51000"),
            quantity=Decimal("2.0")
        ),
        Order(
            user_id="alice",
            symbol="ETH-USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            price=Decimal("3000"),
            quantity=Decimal("5.0")
        ),
    ]
    
    for order in orders:
        repo.save(order)
        side_val = order.side.value if hasattr(order.side, 'value') else order.side
        logger.info(f"   Saved: {order.order_id} - {order.user_id} {side_val} {order.quantity} {order.symbol}")
    
    # 4. Query orders
    logger.info("\n4. Querying orders...")
    
    # Get all orders
    all_orders = repo.find()
    logger.info(f"   Total orders: {len(all_orders)}")
    
    # Get orders by user
    alice_orders = repo.find_by_user("alice")
    logger.info(f"   Alice's orders: {len(alice_orders)}")
    
    # Get orders by symbol
    btc_orders = repo.find_by_symbol("BTC-USD")
    logger.info(f"   BTC-USD orders: {len(btc_orders)}")
    
    # Get open orders
    open_orders = repo.find_open_orders()
    logger.info(f"   Open orders: {len(open_orders)}")
    
    # 5. Advanced filtering
    logger.info("\n5. Advanced filtering...")
    
    filter = OrderFilter(
        symbol="BTC-USD",
        side=OrderSide.BUY,
        min_price=Decimal("40000"),
        max_price=Decimal("55000")
    )
    filtered = repo.find(filter)
    logger.info(f"   Filtered orders: {len(filtered)}")
    for order in filtered:
        side_val = order.side.value if hasattr(order.side, 'value') else order.side
        logger.info(f"      {order.order_id}: {side_val} {order.quantity} @ {order.price}")
    
    # 6. Update order
    logger.info("\n6. Updating order...")
    order_to_update = orders[0]
    order_to_update.status = OrderStatus.FILLED
    order_to_update.filled_quantity = order_to_update.quantity
    repo.save(order_to_update)
    logger.info(f"   Updated {order_to_update.order_id} to FILLED")
    
    # 7. Get statistics
    logger.info("\n7. Statistics...")
    stats = repo.get_statistics()
    logger.info(f"   Total orders: {stats['total_orders']}")
    logger.info(f"   Users: {stats['users']}")
    logger.info(f"   Symbols: {stats['symbols']}")
    logger.info(f"   Status breakdown: {stats['status_breakdown']}")
    
    # 8. Count queries
    logger.info("\n8. Count queries...")
    total = repo.count()
    btc_count = repo.count(OrderFilter(symbol="BTC-USD"))
    logger.info(f"   Total: {total}, BTC-USD: {btc_count}")
    
    # 9. Persistence test
    logger.info("\n9. Testing persistence...")
    logger.info("   Closing and reopening repository...")
    repo.close()
    
    # Create new repository instance
    repo2 = DatabaseOrderRepository()
    repo2.sync_from_database()
    
    # Verify data persisted
    persisted_orders = repo2.find()
    logger.info(f"   Orders after reload: {len(persisted_orders)}")
    
    # Cleanup
    repo2.close()
    
    logger.info("\n✅ Example completed successfully!")
    logger.info(f"Database file: example.db")


if __name__ == "__main__":
    main()
