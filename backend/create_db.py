"""
Run once before starting the server.
Connects to the default 'postgres' catalog and creates the app database if missing.
"""
import asyncio
import asyncpg
from urllib.parse import urlparse

async def create_database():
    from app.core.config import settings

    url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    parsed = urlparse(url)

    user = parsed.username
    password = parsed.password
    host = parsed.hostname
    port = parsed.port or 5432
    dbname = parsed.path.lstrip("/")

    print(f"Attempting to create database '{dbname}' on {host}:{port}...")

    try:
        conn = await asyncpg.connect(
            user=user,
            password=password,
            host=host,
            port=port,
            database="postgres",
        )
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", dbname
        )
        if not exists:
            await conn.execute(f'CREATE DATABASE "{dbname}"')
            print(f"[OK] Database '{dbname}' created.")
        else:
            print(f"[OK] Database '{dbname}' already exists.")
        await conn.close()
    except Exception as e:
        print(f"[ERROR] Could not create database: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(create_database())
