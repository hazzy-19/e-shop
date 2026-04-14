"""Adds firebase_uid column to users table and makes hashed_password nullable."""
import asyncio
from sqlalchemy import text
from app.database import engine

async def migrate():
    async with engine.begin() as conn:
        print("Migrating users table for Firebase...")
        
        # Add firebase_uid column
        try:
            await conn.execute(text("ALTER TABLE users ADD COLUMN firebase_uid VARCHAR UNIQUE"))
            print("[OK] Added firebase_uid column.")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("[OK] firebase_uid already exists.")
            else:
                print(f"[WARN] {e}")

        # Make hashed_password nullable
        try:
            await conn.execute(text("ALTER TABLE users ALTER COLUMN hashed_password DROP NOT NULL"))
            print("[OK] hashed_password is now nullable.")
        except Exception as e:
            print(f"[WARN] {e}")

    print("Migration complete.")

if __name__ == "__main__":
    asyncio.run(migrate())
