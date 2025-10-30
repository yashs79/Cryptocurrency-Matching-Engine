#!/usr/bin/env python3
"""
Initialize Database

Creates all database tables and optionally seeds with sample data.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.matching_engine.config.database import init_db
from src.matching_engine.models import OrderModel, TradeModel
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Initialize database"""
    # Get database URL from environment or use default
    database_url = os.getenv("DATABASE_URL", "sqlite:///./matching_engine.db")
    
    logger.info(f"Initializing database: {database_url}")
    
    # Initialize database
    db_config = init_db(database_url=database_url, echo=True)
    
    logger.info("✅ Database initialized successfully!")
    logger.info(f"Tables created: orders, trades")
    
    # Print connection info
    if database_url.startswith("sqlite"):
        db_file = database_url.replace("sqlite:///", "")
        logger.info(f"SQLite database file: {db_file}")
    else:
        logger.info(f"Connected to: {database_url.split('@')[1] if '@' in database_url else database_url}")


if __name__ == "__main__":
    main()
