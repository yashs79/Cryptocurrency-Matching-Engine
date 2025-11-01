"""
API Routers

FastAPI routers for different endpoint groups.
"""

from .orders import router as orders_router

__all__ = ["orders_router"]
