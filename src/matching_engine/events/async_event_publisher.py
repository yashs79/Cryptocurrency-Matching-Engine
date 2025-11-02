"""
Async Event Publisher

Non-blocking event publishing for better performance.
"""

import asyncio
from typing import List, Callable, Awaitable, Dict, Any
from dataclasses import dataclass
from datetime import datetime, UTC
import logging

logger = logging.getLogger(__name__)


@dataclass
class AsyncEvent:
    """Async event structure"""
    event_type: str
    data: Dict[str, Any]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(UTC)


class AsyncEventPublisher:
    """
    Async event publisher for non-blocking event handling.
    
    Features:
    - Async event publishing
    - Multiple subscribers per event type
    - Background event processing
    - Event queue management
    """
    
    def __init__(self, max_queue_size: int = 10000):
        """
        Initialize async event publisher.
        
        Args:
            max_queue_size: Maximum event queue size
        """
        self._subscribers: Dict[str, List[Callable[[AsyncEvent], Awaitable[None]]]] = {}
        self._event_queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        self._processing_task = None
        self._running = False
        
        # Statistics
        self._published_count = 0
        self._processed_count = 0
        self._failed_count = 0
        
        logger.info("AsyncEventPublisher initialized")
    
    def subscribe(self, event_type: str, handler: Callable[[AsyncEvent], Awaitable[None]]):
        """
        Subscribe to an event type.
        
        Args:
            event_type: Type of event to subscribe to
            handler: Async handler function
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        
        self._subscribers[event_type].append(handler)
        logger.info(f"Subscribed to event type: {event_type}")
    
    def unsubscribe(self, event_type: str, handler: Callable[[AsyncEvent], Awaitable[None]]):
        """
        Unsubscribe from an event type.
        
        Args:
            event_type: Type of event to unsubscribe from
            handler: Handler function to remove
        """
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(handler)
                logger.info(f"Unsubscribed from event type: {event_type}")
            except ValueError:
                pass
    
    async def publish(self, event: AsyncEvent):
        """
        Publish an event asynchronously.
        
        Args:
            event: Event to publish
        """
        try:
            await self._event_queue.put(event)
            self._published_count += 1
            logger.debug(f"Event published: {event.event_type}")
        except asyncio.QueueFull:
            logger.error(f"Event queue full, dropping event: {event.event_type}")
            self._failed_count += 1
    
    async def publish_sync(self, event: AsyncEvent):
        """
        Publish an event and wait for processing (synchronous).
        
        Args:
            event: Event to publish
        """
        handlers = self._subscribers.get(event.event_type, [])
        
        for handler in handlers:
            try:
                await handler(event)
                self._processed_count += 1
            except Exception as e:
                logger.error(f"Error in event handler: {e}", exc_info=True)
                self._failed_count += 1
    
    async def start_processing(self):
        """Start background event processing"""
        if self._running:
            logger.warning("Event processing already running")
            return
        
        self._running = True
        self._processing_task = asyncio.create_task(self._process_events())
        logger.info("Started async event processing")
    
    async def stop_processing(self):
        """Stop background event processing"""
        if not self._running:
            return
        
        self._running = False
        
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Stopped async event processing")
    
    async def _process_events(self):
        """Background task to process events from queue"""
        while self._running:
            try:
                # Get event from queue with timeout
                event = await asyncio.wait_for(
                    self._event_queue.get(),
                    timeout=1.0
                )
                
                # Get handlers for this event type
                handlers = self._subscribers.get(event.event_type, [])
                
                # Execute all handlers concurrently
                if handlers:
                    tasks = [handler(event) for handler in handlers]
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Count successes and failures
                    for result in results:
                        if isinstance(result, Exception):
                            logger.error(f"Event handler error: {result}", exc_info=result)
                            self._failed_count += 1
                        else:
                            self._processed_count += 1
                
                # Mark task as done
                self._event_queue.task_done()
                
            except asyncio.TimeoutError:
                # No events in queue, continue
                continue
            except asyncio.CancelledError:
                # Task cancelled, exit
                break
            except Exception as e:
                logger.error(f"Error processing event: {e}", exc_info=True)
                self._failed_count += 1
    
    async def wait_for_processing(self):
        """Wait for all queued events to be processed"""
        await self._event_queue.join()
    
    def get_stats(self) -> dict:
        """
        Get event publishing statistics.
        
        Returns:
            Dictionary with stats
        """
        return {
            "published": self._published_count,
            "processed": self._processed_count,
            "failed": self._failed_count,
            "queue_size": self._event_queue.qsize(),
            "running": self._running,
            "subscribers": {
                event_type: len(handlers)
                for event_type, handlers in self._subscribers.items()
            }
        }
    
    def reset_stats(self):
        """Reset statistics"""
        self._published_count = 0
        self._processed_count = 0
        self._failed_count = 0


# Global async event publisher instance
async_event_publisher = AsyncEventPublisher()
