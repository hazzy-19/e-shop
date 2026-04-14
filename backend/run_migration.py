import asyncio
from sqlalchemy import text
from app.database import engine, Base
from app.categories import models as cat_models
from app.products import models as prod_models

async def migrate():
    async with engine.begin() as conn:
        print("Creating categories table...")
        # create_all will create any missing tables like 'categories'
        await conn.run_sync(Base.metadata.create_all)
        
        print("Adding category_id to products table if missing...")
        try:
            # We use text() to execute raw SQL to add the column safely
            await conn.execute(text('ALTER TABLE products ADD COLUMN category_id INTEGER REFERENCES categories(id)'))
            print("Successfully added category_id to products.")
        except Exception as e:
            if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                print("Column category_id already exists.")
            else:
                print(f"Error checking/adding column: {e}")

if __name__ == "__main__":
    asyncio.run(migrate())
