"""
Order Repository

Provides efficient storage, indexing, and querying for orders.
Supports filtering, sorting, and pagination.
"""

from typing import Dict, List, Optional, Set
from decimal import Decimal
from datetime import datetime, UTC
from enum import Enum
from dataclasses import dataclass
import logging

from ..core.order import Order, OrderStatus, OrderSide, OrderType

logger = logging.getLogger(__name__)


class SortField(Enum):
    """Fields available for sorting"""
    TIMESTAMP = "timestamp"
    PRICE = "price"
    QUANTITY = "quantity"
    FILLED_QUANTITY = "filled_quantity"
    STATUS = "status"


class SortOrder(Enum):
    """Sort order"""
    ASC = "asc"
    DESC = "desc"


@dataclass
class OrderFilter:
    """Filter criteria for order queries"""
    user_id: Optional[str] = None
    symbol: Optional[str] = None
    side: Optional[OrderSide] = None
    order_type: Optional[OrderType] = None
    status: Optional[OrderStatus] = None
    statuses: Optional[List[OrderStatus]] = None
    min_price: Optional[Decimal] = None
    max_price: Optional[Decimal] = None
    min_quantity: Optional[Decimal] = None
    max_quantity: Optional[Decimal] = None
    from_timestamp: Optional[datetime] = None
    to_timestamp: Optional[datetime] = None


class OrderRepository:
    """
    In-memory order repository with efficient indexing.
    
    Provides:
    - Fast lookups by order_id
    - Indexed queries by user_id, symbol, status
    - Filtering and sorting
    - Pagination support
    """
    
    def __init__(self):
        # Primary storage
        self._orders: Dict[str, Order] = {}
        
        # Indexes for fast lookups
        self._user_index: Dict[str, Set[str]] = {}  # user_id -> order_ids
        self._symbol_index: Dict[str, Set[str]] = {}  # symbol -> order_ids
        self._status_index: Dict[OrderStatus, Set[str]] = {}  # status -> order_ids
        self._side_index: Dict[OrderSide, Set[str]] = {}  # side -> order_ids
        
        logger.info("OrderRepository initialized")
    
    def save(self, order: Order) -> Order:
        """
        Save or update an order.
        
        Args:
            order: Order to save
            
        Returns:
            Saved order
        """
        order_id = order.order_id
        
        # If updating, remove old indexes
        if order_id in self._orders:
            self._remove_from_indexes(self._orders[order_id])
        
        # Save order
        self._orders[order_id] = order
        
        # Update indexes
        self._add_to_indexes(order)
        
        logger.debug(f"Order {order_id} saved to repository")
        return order
    
    def get(self, order_id: str) -> Optional[Order]:
        """
        Get order by ID.
        
        Args:
            order_id: Order ID
            
        Returns:
            Order or None if not found
        """
        return self._orders.get(order_id)
    
    def delete(self, order_id: str) -> bool:
        """
        Delete an order.
        
        Args:
            order_id: Order ID
            
        Returns:
            True if deleted, False if not found
        """
        if order_id not in self._orders:
            return False
        
        order = self._orders[order_id]
        self._remove_from_indexes(order)
        del self._orders[order_id]
        
        logger.debug(f"Order {order_id} deleted from repository")
        return True
    
    def find(
        self,
        filter: Optional[OrderFilter] = None,
        sort_by: Optional[SortField] = None,
        sort_order: SortOrder = SortOrder.DESC,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Order]:
        """
        Find orders matching filter criteria.
        
        Args:
            filter: Filter criteria
            sort_by: Field to sort by
            sort_order: Sort order (ASC/DESC)
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of matching orders
        """
        # Start with all orders or use indexes for optimization
        candidate_ids = self._get_candidate_ids(filter)
        
        # Filter candidates
        results = []
        for order_id in candidate_ids:
            order = self._orders.get(order_id)
            if order and self._matches_filter(order, filter):
                results.append(order)
        
        # Sort results
        if sort_by:
            results = self._sort_orders(results, sort_by, sort_order)
        
        # Apply pagination
        if offset > 0:
            results = results[offset:]
        if limit is not None:
            results = results[:limit]
        
        return results
    
    def find_by_user(
        self,
        user_id: str,
        status: Optional[OrderStatus] = None,
        symbol: Optional[str] = None
    ) -> List[Order]:
        """
        Find all orders for a user.
        
        Args:
            user_id: User ID
            status: Filter by status (optional)
            symbol: Filter by symbol (optional)
            
        Returns:
            List of user's orders
        """
        filter = OrderFilter(
            user_id=user_id,
            status=status,
            symbol=symbol
        )
        return self.find(filter)
    
    def find_by_symbol(
        self,
        symbol: str,
        status: Optional[OrderStatus] = None
    ) -> List[Order]:
        """
        Find all orders for a symbol.
        
        Args:
            symbol: Trading symbol
            status: Filter by status (optional)
            
        Returns:
            List of orders
        """
        filter = OrderFilter(
            symbol=symbol,
            status=status
        )
        return self.find(filter)
    
    def find_by_status(self, status: OrderStatus) -> List[Order]:
        """
        Find all orders with given status.
        
        Args:
            status: Order status
            
        Returns:
            List of orders
        """
        filter = OrderFilter(status=status)
        return self.find(filter)
    
    def find_open_orders(
        self,
        user_id: Optional[str] = None,
        symbol: Optional[str] = None
    ) -> List[Order]:
        """
        Find all open orders.
        
        Args:
            user_id: Filter by user (optional)
            symbol: Filter by symbol (optional)
            
        Returns:
            List of open orders
        """
        filter = OrderFilter(
            user_id=user_id,
            symbol=symbol,
            statuses=[OrderStatus.OPEN, OrderStatus.PARTIALLY_FILLED]
        )
        return self.find(filter)
    
    def count(self, filter: Optional[OrderFilter] = None) -> int:
        """
        Count orders matching filter.
        
        Args:
            filter: Filter criteria
            
        Returns:
            Number of matching orders
        """
        if filter is None:
            return len(self._orders)
        
        candidate_ids = self._get_candidate_ids(filter)
        count = 0
        for order_id in candidate_ids:
            order = self._orders.get(order_id)
            if order and self._matches_filter(order, filter):
                count += 1
        
        return count
    
    def exists(self, order_id: str) -> bool:
        """Check if order exists"""
        return order_id in self._orders
    
    def clear(self) -> None:
        """Clear all orders and indexes"""
        self._orders.clear()
        self._user_index.clear()
        self._symbol_index.clear()
        self._status_index.clear()
        self._side_index.clear()
        logger.info("Repository cleared")
    
    def _add_to_indexes(self, order: Order) -> None:
        """Add order to all indexes"""
        order_id = order.order_id
        
        # User index
        if order.user_id not in self._user_index:
            self._user_index[order.user_id] = set()
        self._user_index[order.user_id].add(order_id)
        
        # Symbol index
        if order.symbol not in self._symbol_index:
            self._symbol_index[order.symbol] = set()
        self._symbol_index[order.symbol].add(order_id)
        
        # Status index
        if order.status not in self._status_index:
            self._status_index[order.status] = set()
        self._status_index[order.status].add(order_id)
        
        # Side index
        if order.side not in self._side_index:
            self._side_index[order.side] = set()
        self._side_index[order.side].add(order_id)
    
    def _remove_from_indexes(self, order: Order) -> None:
        """Remove order from all indexes"""
        order_id = order.order_id
        
        # User index
        if order.user_id in self._user_index:
            self._user_index[order.user_id].discard(order_id)
            if not self._user_index[order.user_id]:
                del self._user_index[order.user_id]
        
        # Symbol index
        if order.symbol in self._symbol_index:
            self._symbol_index[order.symbol].discard(order_id)
            if not self._symbol_index[order.symbol]:
                del self._symbol_index[order.symbol]
        
        # Status index
        if order.status in self._status_index:
            self._status_index[order.status].discard(order_id)
            if not self._status_index[order.status]:
                del self._status_index[order.status]
        
        # Side index
        if order.side in self._side_index:
            self._side_index[order.side].discard(order_id)
            if not self._side_index[order.side]:
                del self._side_index[order.side]
    
    def _get_candidate_ids(self, filter: Optional[OrderFilter]) -> Set[str]:
        """Get candidate order IDs using indexes"""
        if filter is None:
            return set(self._orders.keys())
        
        # Use most selective index
        candidates = None
        
        if filter.user_id:
            candidates = self._user_index.get(filter.user_id, set()).copy()
        
        if filter.symbol:
            symbol_ids = self._symbol_index.get(filter.symbol, set())
            candidates = symbol_ids if candidates is None else candidates & symbol_ids
        
        if filter.status:
            status_ids = self._status_index.get(filter.status, set())
            candidates = status_ids if candidates is None else candidates & status_ids
        
        if filter.statuses:
            status_ids = set()
            for status in filter.statuses:
                status_ids.update(self._status_index.get(status, set()))
            candidates = status_ids if candidates is None else candidates & status_ids
        
        if filter.side:
            side_ids = self._side_index.get(filter.side, set())
            candidates = side_ids if candidates is None else candidates & side_ids
        
        return candidates if candidates is not None else set(self._orders.keys())
    
    def _matches_filter(self, order: Order, filter: Optional[OrderFilter]) -> bool:
        """Check if order matches filter criteria"""
        if filter is None:
            return True
        
        if filter.user_id and order.user_id != filter.user_id:
            return False
        
        if filter.symbol and order.symbol != filter.symbol:
            return False
        
        if filter.side and order.side != filter.side:
            return False
        
        if filter.order_type and order.order_type != filter.order_type:
            return False
        
        if filter.status and order.status != filter.status:
            return False
        
        if filter.statuses and order.status not in filter.statuses:
            return False
        
        if filter.min_price and order.price and order.price < filter.min_price:
            return False
        
        if filter.max_price and order.price and order.price > filter.max_price:
            return False
        
        if filter.min_quantity and order.quantity < filter.min_quantity:
            return False
        
        if filter.max_quantity and order.quantity > filter.max_quantity:
            return False
        
        if filter.from_timestamp and order.timestamp < filter.from_timestamp:
            return False
        
        if filter.to_timestamp and order.timestamp > filter.to_timestamp:
            return False
        
        return True
    
    def _sort_orders(
        self,
        orders: List[Order],
        sort_by: SortField,
        sort_order: SortOrder
    ) -> List[Order]:
        """Sort orders by specified field"""
        reverse = (sort_order == SortOrder.DESC)
        
        if sort_by == SortField.TIMESTAMP:
            return sorted(orders, key=lambda o: o.timestamp, reverse=reverse)
        elif sort_by == SortField.PRICE:
            return sorted(orders, key=lambda o: o.price or Decimal(0), reverse=reverse)
        elif sort_by == SortField.QUANTITY:
            return sorted(orders, key=lambda o: o.quantity, reverse=reverse)
        elif sort_by == SortField.FILLED_QUANTITY:
            return sorted(orders, key=lambda o: o.filled_quantity, reverse=reverse)
        elif sort_by == SortField.STATUS:
            return sorted(orders, key=lambda o: o.status.value, reverse=reverse)
        
        return orders
    
    def get_statistics(self) -> Dict:
        """Get repository statistics"""
        return {
            "total_orders": len(self._orders),
            "users": len(self._user_index),
            "symbols": len(self._symbol_index),
            "status_breakdown": {
                (status.value if hasattr(status, 'value') else status): len(order_ids)
                for status, order_ids in self._status_index.items()
            },
            "side_breakdown": {
                (side.value if hasattr(side, 'value') else side): len(order_ids)
                for side, order_ids in self._side_index.items()
            }
        }
