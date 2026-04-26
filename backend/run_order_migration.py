import asyncio
from sqlalchemy import text
from app.database import engine

async def migrate():
    async with engine.begin() as conn:
        result = await conn.execute(
            text("SELECT column_name FROM information_schema.columns WHERE table_name='orders'")
        )
        existing = {row[0] for row in result.fetchall()}
        print("Existing order columns:", existing)
        added = []
        if "shipping_address" not in existing:
            await conn.execute(text("ALTER TABLE orders ADD COLUMN shipping_address VARCHAR"))
            added.append("shipping_address")
        if "delivered_at" not in existing:
            await conn.execute(text("ALTER TABLE orders ADD COLUMN delivered_at TIMESTAMP WITH TIME ZONE"))
            added.append("delivered_at")
        print("Added:", added if added else "nothing - already up to date")

asyncio.run(migrate())
