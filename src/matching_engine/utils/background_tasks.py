"""
Background Task Manager

Manages background tasks for async operations.
"""

import asyncio
from typing import Callable, Awaitable, Dict, Optional
from datetime import datetime, UTC
import logging

logger = logging.getLogger(__name__)


class BackgroundTaskManager:
    """
    Manages background tasks and periodic jobs.
    
    Features:
    - Task scheduling
    - Periodic task execution
    - Task lifecycle management
    - Error handling and retry
    """
    
    def __init__(self):
        """Initialize background task manager"""
        self._tasks: Dict[str, asyncio.Task] = {}
        self._running = False
        
        # Statistics
        self._task_count = 0
        self._completed_count = 0
        self._failed_count = 0
        
        logger.info("BackgroundTaskManager initialized")
    
    async def start(self):
        """Start the background task manager"""
        self._running = True
        logger.info("Background task manager started")
    
    async def stop(self):
        """Stop all background tasks"""
        self._running = False
        
        # Cancel all running tasks
        for task_name, task in list(self._tasks.items()):
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                logger.info(f"Cancelled task: {task_name}")
        
        self._tasks.clear()
        logger.info("Background task manager stopped")
    
    def create_task(
        self,
        name: str,
        coro: Callable[[], Awaitable[None]],
        replace: bool = False
    ) -> asyncio.Task:
        """
        Create and register a background task.
        
        Args:
            name: Task name
            coro: Coroutine to execute
            replace: Replace existing task with same name
            
        Returns:
            Created task
        """
        # Check if task already exists
        if name in self._tasks and not replace:
            existing = self._tasks[name]
            if not existing.done():
                logger.warning(f"Task '{name}' already exists and is running")
                return existing
        
        # Create task
        task = asyncio.create_task(coro())
        task.add_done_callback(lambda t: self._task_done_callback(name, t))
        
        self._tasks[name] = task
        self._task_count += 1
        
        logger.info(f"Created background task: {name}")
        return task
    
    def schedule_periodic(
        self,
        name: str,
        coro: Callable[[], Awaitable[None]],
        interval_seconds: float,
        run_immediately: bool = False
    ) -> asyncio.Task:
        """
        Schedule a periodic task.
        
        Args:
            name: Task name
            coro: Coroutine to execute
            interval_seconds: Interval between executions
            run_immediately: Run immediately before waiting
            
        Returns:
            Created task
        """
        async def periodic_wrapper():
            if run_immediately:
                try:
                    await coro()
                except Exception as e:
                    logger.error(f"Error in periodic task '{name}': {e}", exc_info=True)
            
            while self._running:
                try:
                    await asyncio.sleep(interval_seconds)
                    await coro()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error in periodic task '{name}': {e}", exc_info=True)
        
        return self.create_task(name, periodic_wrapper, replace=True)
    
    def cancel_task(self, name: str) -> bool:
        """
        Cancel a background task.
        
        Args:
            name: Task name
            
        Returns:
            True if task was cancelled
        """
        if name not in self._tasks:
            return False
        
        task = self._tasks[name]
        if not task.done():
            task.cancel()
            logger.info(f"Cancelled task: {name}")
            return True
        
        return False
    
    def get_task(self, name: str) -> Optional[asyncio.Task]:
        """
        Get a task by name.
        
        Args:
            name: Task name
            
        Returns:
            Task or None if not found
        """
        return self._tasks.get(name)
    
    def is_running(self, name: str) -> bool:
        """
        Check if a task is running.
        
        Args:
            name: Task name
            
        Returns:
            True if task is running
        """
        task = self._tasks.get(name)
        return task is not None and not task.done()
    
    def _task_done_callback(self, name: str, task: asyncio.Task):
        """Callback when a task completes"""
        try:
            # Check if task raised an exception
            exception = task.exception()
            if exception:
                if not isinstance(exception, asyncio.CancelledError):
                    logger.error(f"Task '{name}' failed: {exception}", exc_info=exception)
                    self._failed_count += 1
            else:
                logger.debug(f"Task '{name}' completed successfully")
                self._completed_count += 1
        except asyncio.CancelledError:
            logger.debug(f"Task '{name}' was cancelled")
        except Exception as e:
            logger.error(f"Error in task callback: {e}", exc_info=True)
    
    def get_stats(self) -> dict:
        """
        Get task manager statistics.
        
        Returns:
            Dictionary with stats
        """
        active_tasks = sum(1 for t in self._tasks.values() if not t.done())
        
        return {
            "running": self._running,
            "total_tasks": self._task_count,
            "active_tasks": active_tasks,
            "completed": self._completed_count,
            "failed": self._failed_count,
            "task_names": list(self._tasks.keys())
        }
    
    def reset_stats(self):
        """Reset statistics"""
        self._task_count = 0
        self._completed_count = 0
        self._failed_count = 0


# Global background task manager instance
background_task_manager = BackgroundTaskManager()


# Convenience functions for common background tasks

async def cache_cleanup_task():
    """Periodic task to clean up expired cache entries"""
    from ..cache import cache_manager
    
    removed = cache_manager.cleanup_expired()
    if removed > 0:
        logger.info(f"Cache cleanup: removed {removed} expired entries")


async def connection_pool_monitor():
    """Periodic task to monitor database connection pool"""
    from ..config.database import get_db_config
    
    try:
        db_config = get_db_config()
        stats = db_config.get_pool_stats()
        
        logger.debug(
            f"Pool stats - Size: {stats['size']}, "
            f"Active: {stats['checked_out']}, "
            f"Idle: {stats['checked_in']}"
        )
    except Exception as e:
        logger.error(f"Error monitoring connection pool: {e}")


async def event_queue_monitor():
    """Periodic task to monitor event queue"""
    from ..events.async_event_publisher import async_event_publisher
    
    stats = async_event_publisher.get_stats()
    
    if stats['queue_size'] > 1000:
        logger.warning(f"Event queue size high: {stats['queue_size']}")
    
    logger.debug(
        f"Event stats - Published: {stats['published']}, "
        f"Processed: {stats['processed']}, "
        f"Queue: {stats['queue_size']}"
    )
