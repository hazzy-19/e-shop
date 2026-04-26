"""
promote_admin.py  —  Promote any registered user to admin.

Usage:
    .\\venv\\Scripts\\python.exe promote_admin.py anyona@eshop.com

Step 1: First REGISTER the account on the website:
  - Go to http://localhost:5173/login
  - Click Register tab
  - Full Name: Anyona
  - Email: anyona@eshop.com
  - Password: PETERonchoke254
  - Click Create Account

Step 2: Then run this script:
  .\\venv\\Scripts\\python.exe promote_admin.py anyona@eshop.com
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

EMAIL = sys.argv[1] if len(sys.argv) > 1 else "anyona@eshop.com"


async def main():
    from sqlalchemy.future import select
    from app.database import engine, async_session
    from app.auth.models import User
    from app.database import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        result = await db.execute(select(User).where(User.email == EMAIL))
        user = result.scalars().first()

        if not user:
            print(f"ERROR: No user found with email '{EMAIL}'")
            print()
            print("Make sure to REGISTER on the website first:")
            print("  1. Go to http://localhost:5173/login")
            print("  2. Register tab -> Email: anyona@eshop.com, Password: PETERonchoke254")
            print("  3. Then run this script again")
            return

        user.is_admin = True
        await db.commit()
        await db.refresh(user)
        print(f"SUCCESS: {user.email} is now an admin (id={user.id})")
        print()
        print("Admin login steps:")
        print("  1. Go to http://localhost:5173/login")
        print("  2. Sign In with anyona@eshop.com / PETERonchoke254")
        print("  3. Navigate to http://localhost:5173/admin")
        print("  4. Click 'Send Code to Telegram' -> check Telegram bot for the 6-digit code")
        print("  5. Enter the code -> dashboard unlocks")


if __name__ == "__main__":
    asyncio.run(main())
