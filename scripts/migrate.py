#!/usr/bin/env python3
"""Database migration script."""

import asyncio

from consciousness.database import create_tables, init_db


async def main():
    await init_db()
    await create_tables()
    print("Database initialized successfully!")


if __name__ == "__main__":
    asyncio.run(main())
