"""
Event Publisher

Provides pub/sub mechanism for order events.
Supports synchronous and asynchronous event delivery.
"""

from typing import Callable, Dict, List, Set, Optional
from datetime import datetime, UTC
import logging
from collections import defaultdict
import asyncio

from .order_events import OrderEvent, OrderEventType

logger = logging.getLogger(__name__)


class EventSubscriber:
    """
    Event subscriber interface.
    
    Subscribers implement this to receive events.
    """
    
    def on_event(self, event: OrderEvent) -> None:
        """
        Handle an event.
        
        Args:
            event: The event to handle
        """
        raise NotImplementedError("Subscribers must implement on_event")
    
    async def on_event_async(self, event: OrderEvent) -> None:
        """
        Handle an event asynchronously.
        
        Args:
            event: The event to handle
        """
        # Default implementation calls sync version
        self.on_event(event)


class EventPublisher:
    """
    Event publisher with pub/sub support.
    
    Features:
    - Subscribe to specific event types or all events
    - Synchronous and asynchronous delivery
    - Event history tracking
    - Statistics and monitoring
    """
    
    def __init__(self, max_history: int = 1000):
        """
        Initialize event publisher.
        
        Args:
            max_history: Maximum number of events to keep in history
        """
        self.max_history = max_history
        
        # Subscribers by event type
        self._subscribers: Dict[OrderEventType, Set[EventSubscriber]] = defaultdict(set)
        
        # Subscribers for all events
        self._global_subscribers: Set[EventSubscriber] = set()
        
        # Callback functions (alternative to subscriber objects)
        self._callbacks: Dict[OrderEventType, List[Callable]] = defaultdict(list)
        self._global_callbacks: List[Callable] = []
        
        # Event history
        self._event_history: List[OrderEvent] = []
        
        # Statistics
        self._event_counts: Dict[OrderEventType, int] = defaultdict(int)
        self._total_events = 0
        
        logger.info("EventPublisher initialized")
    
    def subscribe(
        self,
        subscriber: EventSubscriber,
        event_type: Optional[OrderEventType] = None
    ) -> None:
        """
        Subscribe to events.
        
        Args:
            subscriber: Subscriber object
            event_type: Specific event type to subscribe to, or None for all events
        """
        if event_type is None:
            self._global_subscribers.add(subscriber)
            logger.debug(f"Subscriber {subscriber} subscribed to all events")
        else:
            self._subscribers[event_type].add(subscriber)
            logger.debug(f"Subscriber {subscriber} subscribed to {event_type.value} events")
    
    def unsubscribe(
        self,
        subscriber: EventSubscriber,
        event_type: Optional[OrderEventType] = None
    ) -> None:
        """
        Unsubscribe from events.
        
        Args:
            subscriber: Subscriber object
            event_type: Specific event type to unsubscribe from, or None for all events
        """
        if event_type is None:
            self._global_subscribers.discard(subscriber)
            # Also remove from all specific subscriptions
            for subscribers in self._subscribers.values():
                subscribers.discard(subscriber)
            logger.debug(f"Subscriber {subscriber} unsubscribed from all events")
        else:
            self._subscribers[event_type].discard(subscriber)
            logger.debug(f"Subscriber {subscriber} unsubscribed from {event_type.value} events")
    
    def on(
        self,
        event_type: Optional[OrderEventType] = None
    ) -> Callable:
        """
        Decorator for subscribing callback functions.
        
        Usage:
            @publisher.on(OrderEventType.SUBMITTED)
            def handle_submitted(event):
                print(f"Order submitted: {event.order.order_id}")
        
        Args:
            event_type: Event type to subscribe to, or None for all events
            
        Returns:
            Decorator function
        """
        def decorator(callback: Callable) -> Callable:
            if event_type is None:
                self._global_callbacks.append(callback)
            else:
                self._callbacks[event_type].append(callback)
            return callback
        
        return decorator
    
    def publish(self, event: OrderEvent) -> None:
        """
        Publish an event synchronously.
        
        Args:
            event: Event to publish
        """
        # Add to history
        self._add_to_history(event)
        
        # Update statistics
        self._event_counts[event.event_type] += 1
        self._total_events += 1
        
        # Notify global subscribers
        for subscriber in self._global_subscribers:
            try:
                subscriber.on_event(event)
            except Exception as e:
                logger.error(f"Error in subscriber {subscriber}: {e}")
        
        # Notify type-specific subscribers
        for subscriber in self._subscribers.get(event.event_type, set()):
            try:
                subscriber.on_event(event)
            except Exception as e:
                logger.error(f"Error in subscriber {subscriber}: {e}")
        
        # Call global callbacks
        for callback in self._global_callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Error in callback {callback}: {e}")
        
        # Call type-specific callbacks
        for callback in self._callbacks.get(event.event_type, []):
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Error in callback {callback}: {e}")
        
        logger.debug(f"Published {event.event_type.value} event for order {event.order.order_id}")
    
    async def publish_async(self, event: OrderEvent) -> None:
        """
        Publish an event asynchronously.
        
        Args:
            event: Event to publish
        """
        # Add to history
        self._add_to_history(event)
        
        # Update statistics
        self._event_counts[event.event_type] += 1
        self._total_events += 1
        
        # Collect all async tasks
        tasks = []
        
        # Notify global subscribers
        for subscriber in self._global_subscribers:
            tasks.append(self._call_subscriber_async(subscriber, event))
        
        # Notify type-specific subscribers
        for subscriber in self._subscribers.get(event.event_type, set()):
            tasks.append(self._call_subscriber_async(subscriber, event))
        
        # Execute all tasks concurrently
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.debug(f"Published {event.event_type.value} event async for order {event.order.order_id}")
    
    async def _call_subscriber_async(
        self,
        subscriber: EventSubscriber,
        event: OrderEvent
    ) -> None:
        """Call subscriber asynchronously with error handling"""
        try:
            await subscriber.on_event_async(event)
        except Exception as e:
            logger.error(f"Error in async subscriber {subscriber}: {e}")
    
    def _add_to_history(self, event: OrderEvent) -> None:
        """Add event to history, maintaining max size"""
        self._event_history.append(event)
        
        # Trim history if needed
        if len(self._event_history) > self.max_history:
            self._event_history = self._event_history[-self.max_history:]
    
    def get_history(
        self,
        event_type: Optional[OrderEventType] = None,
        limit: Optional[int] = None
    ) -> List[OrderEvent]:
        """
        Get event history.
        
        Args:
            event_type: Filter by event type (optional)
            limit: Maximum number of events to return (optional)
            
        Returns:
            List of events
        """
        events = self._event_history
        
        # Filter by type if specified
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        # Apply limit
        if limit:
            events = events[-limit:]
        
        return events
    
    def get_events_for_order(self, order_id: str) -> List[OrderEvent]:
        """
        Get all events for a specific order.
        
        Args:
            order_id: Order ID
            
        Returns:
            List of events for the order
        """
        return [e for e in self._event_history if e.order.order_id == order_id]
    
    def clear_history(self) -> None:
        """Clear event history"""
        self._event_history.clear()
        logger.info("Event history cleared")
    
    def get_statistics(self) -> Dict:
        """
        Get publisher statistics.
        
        Returns:
            Dictionary of statistics
        """
        return {
            "total_events": self._total_events,
            "event_counts": {
                event_type.value: count
                for event_type, count in self._event_counts.items()
            },
            "history_size": len(self._event_history),
            "max_history": self.max_history,
            "subscriber_counts": {
                "global": len(self._global_subscribers),
                "by_type": {
                    event_type.value: len(subscribers)
                    for event_type, subscribers in self._subscribers.items()
                },
            },
            "callback_counts": {
                "global": len(self._global_callbacks),
                "by_type": {
                    event_type.value: len(callbacks)
                    for event_type, callbacks in self._callbacks.items()
                },
            },
        }
    
    def reset_statistics(self) -> None:
        """Reset statistics counters"""
        self._event_counts.clear()
        self._total_events = 0
        logger.info("Statistics reset")
