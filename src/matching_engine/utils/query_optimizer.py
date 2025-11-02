"""
Query Optimization Utilities

Tools for optimizing database queries and batch operations.
"""

from typing import List, Any, Callable
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)


class QueryOptimizer:
    """
    Utilities for optimizing database queries.
    
    Features:
    - Batch inserts
    - Bulk updates
    - Query result caching
    - Query timing
    """
    
    @staticmethod
    def batch_insert(session: Session, models: List[Any], batch_size: int = 1000):
        """
        Insert models in batches for better performance.
        
        Args:
            session: Database session
            models: List of model instances to insert
            batch_size: Number of records per batch
        """
        total = len(models)
        for i in range(0, total, batch_size):
            batch = models[i:i + batch_size]
            session.bulk_save_objects(batch)
            session.commit()
            logger.debug(f"Inserted batch {i//batch_size + 1}: {len(batch)} records")
        
        logger.info(f"Batch insert complete: {total} records")
    
    @staticmethod
    def batch_update(session: Session, model_class: Any, updates: List[dict], batch_size: int = 1000):
        """
        Update records in batches.
        
        Args:
            session: Database session
            model_class: Model class
            updates: List of update dictionaries with 'id' and fields to update
            batch_size: Number of records per batch
        """
        total = len(updates)
        for i in range(0, total, batch_size):
            batch = updates[i:i + batch_size]
            session.bulk_update_mappings(model_class, batch)
            session.commit()
            logger.debug(f"Updated batch {i//batch_size + 1}: {len(batch)} records")
        
        logger.info(f"Batch update complete: {total} records")
    
    @staticmethod
    def execute_with_timing(func: Callable, *args, **kwargs) -> tuple:
        """
        Execute a function and measure its execution time.
        
        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Tuple of (result, execution_time_ms)
        """
        import time
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = (time.time() - start) * 1000  # Convert to milliseconds
        return result, elapsed
    
    @staticmethod
    def optimize_query(query):
        """
        Apply common optimizations to a query.
        
        Args:
            query: SQLAlchemy query
            
        Returns:
            Optimized query
        """
        # Add common optimizations
        # - Use yield_per for large result sets
        # - Add execution options
        return query.execution_options(
            stream_results=True,
            max_row_buffer=1000
        )


# Singleton instance
query_optimizer = QueryOptimizer()
