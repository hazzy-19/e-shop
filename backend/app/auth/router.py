from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import firebase_admin
from firebase_admin import auth as firebase_auth

from app.auth.models import User
from app.database import get_db

router = APIRouter()
bearer_scheme = HTTPBearer(auto_error=False)

@router.post("/sync")
async def sync_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    """
    Called by the frontend immediately after Firebase login.
    Verifies the Firebase token, then creates or fetches the user
    in our PostgreSQL database. Returns is_admin status.
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="No token provided")

    try:
        decoded = firebase_auth.verify_id_token(credentials.credentials)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid Firebase token")

    uid = decoded["uid"]
    email = decoded.get("email", "")

    # Find existing user by firebase_uid
    result = await db.execute(select(User).where(User.firebase_uid == uid))
    user = result.scalars().first()

    if not user:
        # New user — also check by email in case they had an old account
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalars().first()

        if user:
            # Link the old account to Firebase
            user.firebase_uid = uid
        else:
            # Brand new user
            user = User(email=email, firebase_uid=uid, is_active=True, is_admin=False)
            db.add(user)

    await db.commit()
    await db.refresh(user)

    return {
        "id": user.id,
        "email": user.email,
        "is_admin": user.is_admin,
        "is_active": user.is_active,
    }


@router.get("/me")
async def me(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    """Returns the current user profile based on Firebase token."""
    if not credentials:
        raise HTTPException(status_code=401, detail="No token")
    try:
        decoded = firebase_auth.verify_id_token(credentials.credentials)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    result = await db.execute(select(User).where(User.firebase_uid == decoded["uid"]))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {"id": user.id, "email": user.email, "is_admin": user.is_admin}
