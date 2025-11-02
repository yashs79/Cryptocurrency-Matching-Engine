"""
Database-backed Order Repository

Extends OrderRepository with persistent database storage.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from decimal import Decimal
import logging

from .order_repository import OrderRepository, OrderFilter, SortField, SortOrder
from ..core.order import Order, OrderStatus, OrderSide, OrderType
from ..models.order_model import OrderModel
from ..config.database import get_db_config
from ..cache import cache_manager

logger = logging.getLogger(__name__)


class DatabaseOrderRepository(OrderRepository):
    """
    Database-backed order repository.
    
    Provides persistent storage while maintaining the same interface
    as the in-memory repository.
    """
    
    def __init__(self, session: Optional[Session] = None):
        """
        Initialize database repository.
        
        Args:
            session: SQLAlchemy session (optional, will create if not provided)
        """
        # Initialize parent (in-memory) for fast lookups
        super().__init__()
        
        # Database session
        self._session = session
        self._owns_session = session is None
        
        if self._session is None:
            db_config = get_db_config()
            self._session = db_config.get_session()
        
        logger.info("DatabaseOrderRepository initialized")
    
    def save(self, order: Order) -> Order:
        """
        Save order to database and in-memory cache.
        
        Args:
            order: Order to save
            
        Returns:
            Saved order
        """
        # Save to in-memory cache first
        super().save(order)
        
        # Update cache
        cache_manager.set_order(order.order_id, order, ttl_seconds=300)
        
        # Invalidate user orders cache
        cache_manager.delete_user_orders(order.user_id)
        
        # Save to database
        try:
            # Check if order exists
            existing = self._session.query(OrderModel).filter_by(
                order_id=order.order_id
            ).first()
            
            if existing:
                # Update existing
                existing.update_from_order(order)
            else:
                # Create new
                order_model = OrderModel.from_order(order)
                self._session.add(order_model)
            
            self._session.commit()
            logger.debug(f"Order {order.order_id} saved to database")
            
        except Exception as e:
            self._session.rollback()
            logger.error(f"Error saving order to database: {e}")
            raise
        
        return order
    
    def get(self, order_id: str) -> Optional[Order]:
        """
        Get order by ID (checks cache first, then database).
        
        Args:
            order_id: Order ID
            
        Returns:
            Order or None if not found
        """
        # Check cache first
        cached_order = cache_manager.get_order(order_id)
        if cached_order:
            return cached_order
        
        # Check in-memory cache
        order = super().get(order_id)
        if order:
            # Cache for future requests
            cache_manager.set_order(order_id, order, ttl_seconds=300)
            return order
        
        # Check database
        try:
            order_model = self._session.query(OrderModel).filter_by(
                order_id=order_id
            ).first()
            
            if order_model:
                order = order_model.to_order()
                # Add to in-memory cache
                super().save(order)
                # Add to cache manager
                cache_manager.set_order(order_id, order, ttl_seconds=300)
                return order
            
        except Exception as e:
            logger.error(f"Error getting order from database: {e}")
        
        return None
    
    def delete(self, order_id: str) -> bool:
        """
        Delete order from database and cache.
        
        Args:
            order_id: Order ID
            
        Returns:
            True if deleted, False if not found
        """
        # Delete from in-memory cache
        cache_deleted = super().delete(order_id)
        
        # Delete from cache manager
        cache_manager.delete_order(order_id)
        
        # Delete from database
        try:
            result = self._session.query(OrderModel).filter_by(
                order_id=order_id
            ).delete()
            self._session.commit()
            
            if result > 0:
                logger.debug(f"Order {order_id} deleted from database")
                return True
            
        except Exception as e:
            self._session.rollback()
            logger.error(f"Error deleting order from database: {e}")
        
        return cache_deleted
    
    def find(
        self,
        filter: Optional[OrderFilter] = None,
        sort_by: Optional[SortField] = None,
        sort_order: SortOrder = SortOrder.DESC,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Order]:
        """
        Find orders in database with filtering and sorting.
        
        Args:
            filter: Filter criteria
            sort_by: Field to sort by
            sort_order: Sort order (ASC/DESC)
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of matching orders
        """
        try:
            # Build query
            query = self._session.query(OrderModel)
            
            # Apply filters
            if filter:
                conditions = []
                
                if filter.user_id:
                    conditions.append(OrderModel.user_id == filter.user_id)
                
                if filter.symbol:
                    conditions.append(OrderModel.symbol == filter.symbol)
                
                if filter.side:
                    conditions.append(OrderModel.side == filter.side)
                
                if filter.order_type:
                    conditions.append(OrderModel.order_type == filter.order_type)
                
                if filter.status:
                    conditions.append(OrderModel.status == filter.status)
                
                if filter.statuses:
                    conditions.append(OrderModel.status.in_(filter.statuses))
                
                if filter.min_price:
                    conditions.append(OrderModel.price >= filter.min_price)
                
                if filter.max_price:
                    conditions.append(OrderModel.price <= filter.max_price)
                
                if filter.min_quantity:
                    conditions.append(OrderModel.quantity >= filter.min_quantity)
                
                if filter.max_quantity:
                    conditions.append(OrderModel.quantity <= filter.max_quantity)
                
                if filter.from_timestamp:
                    conditions.append(OrderModel.timestamp >= filter.from_timestamp)
                
                if filter.to_timestamp:
                    conditions.append(OrderModel.timestamp <= filter.to_timestamp)
                
                if conditions:
                    query = query.filter(and_(*conditions))
            
            # Apply sorting
            if sort_by:
                sort_column = self._get_sort_column(sort_by)
                if sort_order == SortOrder.DESC:
                    query = query.order_by(sort_column.desc())
                else:
                    query = query.order_by(sort_column.asc())
            
            # Apply pagination
            if offset > 0:
                query = query.offset(offset)
            if limit is not None:
                query = query.limit(limit)
            
            # Execute query
            order_models = query.all()
            
            # Convert to domain objects
            orders = [model.to_order() for model in order_models]
            
            # Update cache
            for order in orders:
                super().save(order)
            
            return orders
            
        except Exception as e:
            logger.error(f"Error finding orders in database: {e}")
            # Fallback to in-memory search
            return super().find(filter, sort_by, sort_order, limit, offset)
    
    def _get_sort_column(self, sort_by: SortField):
        """Get SQLAlchemy column for sorting"""
        if sort_by == SortField.TIMESTAMP:
            return OrderModel.timestamp
        elif sort_by == SortField.PRICE:
            return OrderModel.price
        elif sort_by == SortField.QUANTITY:
            return OrderModel.quantity
        elif sort_by == SortField.FILLED_QUANTITY:
            return OrderModel.filled_quantity
        elif sort_by == SortField.STATUS:
            return OrderModel.status
        return OrderModel.timestamp
    
    def count(self, filter: Optional[OrderFilter] = None) -> int:
        """
        Count orders in database.
        
        Args:
            filter: Filter criteria
            
        Returns:
            Number of matching orders
        """
        try:
            query = self._session.query(OrderModel)
            
            # Apply filters (same as find method)
            if filter:
                conditions = []
                
                if filter.user_id:
                    conditions.append(OrderModel.user_id == filter.user_id)
                if filter.symbol:
                    conditions.append(OrderModel.symbol == filter.symbol)
                if filter.side:
                    conditions.append(OrderModel.side == filter.side)
                if filter.order_type:
                    conditions.append(OrderModel.order_type == filter.order_type)
                if filter.status:
                    conditions.append(OrderModel.status == filter.status)
                if filter.statuses:
                    conditions.append(OrderModel.status.in_(filter.statuses))
                
                if conditions:
                    query = query.filter(and_(*conditions))
            
            return query.count()
            
        except Exception as e:
            logger.error(f"Error counting orders in database: {e}")
            return super().count(filter)
    
    def clear(self) -> None:
        """Clear all orders from database and cache"""
        super().clear()
        
        try:
            self._session.query(OrderModel).delete()
            self._session.commit()
            logger.info("Database repository cleared")
        except Exception as e:
            self._session.rollback()
            logger.error(f"Error clearing database: {e}")
    
    def sync_from_database(self) -> int:
        """
        Sync in-memory cache from database.
        
        Returns:
            Number of orders loaded
        """
        try:
            order_models = self._session.query(OrderModel).all()
            
            for model in order_models:
                order = model.to_order()
                super().save(order)
            
            logger.info(f"Synced {len(order_models)} orders from database")
            return len(order_models)
            
        except Exception as e:
            logger.error(f"Error syncing from database: {e}")
            return 0
    
    def close(self):
        """Close database session"""
        if self._owns_session and self._session:
            self._session.close()
            logger.debug("Database session closed")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
