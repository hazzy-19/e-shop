"""
create_admin.py  —  One-time admin account setup.
Run from the backend directory:

    .\\venv\\Scripts\\python.exe create_admin.py

This script:
1. Creates a Firebase user (anyona@eshop.com / PETERonchoke254)
2. Creates or updates the database record and sets is_admin=True
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

ADMIN_EMAIL = "anyona@eshop.com"
ADMIN_PASSWORD = "PETERonchoke254"
ADMIN_DISPLAY_NAME = "Anyona Admin"

async def main():
    # ── Init Firebase Admin SDK ────────────────────────────────
    from app.core.firebase import initialize_firebase
    initialize_firebase()

    import firebase_admin
    from firebase_admin import auth as firebase_auth

    # ── Step 1: Create or fetch Firebase user ───────────────────
    print(f"Setting up admin: {ADMIN_EMAIL}")
    try:
        fb_user = firebase_auth.get_user_by_email(ADMIN_EMAIL)
        print(f"  Firebase user already exists (uid={fb_user.uid})")
    except firebase_admin.auth.UserNotFoundError:
        fb_user = firebase_auth.create_user(
            email=ADMIN_EMAIL,
            password=ADMIN_PASSWORD,
            display_name=ADMIN_DISPLAY_NAME,
            email_verified=True,
        )
        print(f"  Firebase user created (uid={fb_user.uid})")

    # ── Step 2: Upsert in our database ──────────────────────────
    from sqlalchemy.future import select
    from app.database import engine, async_session
    from app.auth.models import User
    from app.database import Base

    # Ensure tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        result = await db.execute(
            select(User).where(User.firebase_uid == fb_user.uid)
        )
        user = result.scalars().first()

        if not user:
            result = await db.execute(
                select(User).where(User.email == ADMIN_EMAIL)
            )
            user = result.scalars().first()

        if user:
            user.firebase_uid = fb_user.uid
            user.is_admin = True
            user.is_active = True
            user.display_name = ADMIN_DISPLAY_NAME
        else:
            user = User(
                email=ADMIN_EMAIL,
                firebase_uid=fb_user.uid,
                display_name=ADMIN_DISPLAY_NAME,
                is_admin=True,
                is_active=True,
            )
            db.add(user)

        await db.commit()
        await db.refresh(user)
        print(f"  DB user: id={user.id}, email={user.email}, is_admin={user.is_admin}")

    print()
    print("Admin account ready!")
    print(f"  Email:    {ADMIN_EMAIL}")
    print(f"  Password: {ADMIN_PASSWORD}")
    print()
    print("How to log in as admin:")
    print("  1. Go to /login")
    print("  2. Sign In tab, enter the email and password above")
    print("  3. Then go to /admin — it will ask for a 2FA code")
    print("  4. The code will be sent to your Telegram bot")
    print()


if __name__ == "__main__":
    asyncio.run(main())
