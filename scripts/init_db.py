"""
Database initialization script
Initializes the database with all tables from models
"""

import asyncio
import logging

from app.core.database import init_db, close_db

logger = logging.getLogger(__name__)


async def main():
    """Initialize database tables"""
    try:
        logger.info("Initializing database...")
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())
