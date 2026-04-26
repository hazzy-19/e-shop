"""
run_migration.py  —  Safe migration to add new user columns.
Run once from the backend directory:

    python run_user_migration.py

This script uses raw SQL so it works even if Alembic is not set up.
It is idempotent — safe to run multiple times.
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import text
from app.database import engine


async def migrate():
    async with engine.begin() as conn:
        db_url = str(engine.url)
        is_sqlite = "sqlite" in db_url

        # Detect existing columns
        if is_sqlite:
            result = await conn.execute(text("PRAGMA table_info(users)"))
            existing = {row[1] for row in result.fetchall()}
        else:
            result = await conn.execute(text("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'users'
            """))
            existing = {row[0] for row in result.fetchall()}

        print(f"Existing user columns: {existing}")

        # Add columns if missing
        migrations = []

        if "display_name" not in existing:
            migrations.append("ALTER TABLE users ADD COLUMN display_name VARCHAR")

        if "photo_url" not in existing:
            migrations.append("ALTER TABLE users ADD COLUMN photo_url VARCHAR")

        if "created_at" not in existing:
            if is_sqlite:
                migrations.append("ALTER TABLE users ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP")
            else:
                migrations.append(
                    "ALTER TABLE users ADD COLUMN created_at TIMESTAMP WITH TIME ZONE "
                    "DEFAULT (NOW() AT TIME ZONE 'utc')"
                )

        if not migrations:
            print("✅ All user columns already exist — nothing to do.")
            return

        for stmt in migrations:
            print(f"Running: {stmt}")
            await conn.execute(text(stmt))

        print(f"✅ Migration complete — added {len(migrations)} column(s).")


if __name__ == "__main__":
    asyncio.run(migrate())
