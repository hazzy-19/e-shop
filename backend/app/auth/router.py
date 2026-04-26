from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import firebase_admin
from firebase_admin import auth as firebase_auth
import logging

from app.auth.models import User
from app.auth.schemas import UserResponse, UserProfileUpdate
from app.auth.deps import get_current_active_user
from app.database import get_db

router = APIRouter()
bearer_scheme = HTTPBearer(auto_error=False)
logger = logging.getLogger(__name__)


@router.post("/sync", response_model=UserResponse)
async def sync_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    """
    Called by the frontend immediately after Firebase login/registration.
    Verifies the Firebase token, then upserts the user in our PostgreSQL database.

    - Safe to call multiple times (idempotent).
    - Syncs display_name and photo_url from Firebase on each login.
    - Returns full user profile including admin status.
    """
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No token provided")

    try:
        decoded = firebase_auth.verify_id_token(credentials.credentials)
    except firebase_admin.exceptions.InvalidArgumentError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Malformed Firebase token")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired Firebase token. Please sign in again.")

    uid = decoded["uid"]
    email = decoded.get("email", "")
    display_name = decoded.get("name") or decoded.get("display_name")
    photo_url = decoded.get("picture") or decoded.get("photo_url")

    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Firebase account has no email address")

    # ── Try to find by firebase_uid first (most common path) ──────────────────
    result = await db.execute(select(User).where(User.firebase_uid == uid))
    user = result.scalars().first()

    if not user:
        # ── Fallback: find by email (handles legacy accounts / email-link logins) ──
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalars().first()

        if user:
            # Link the existing account to this Firebase UID
            user.firebase_uid = uid
            logger.info(f"Linked existing account {email} to Firebase UID {uid}")
        else:
            # Brand new user — create the DB record
            user = User(
                email=email,
                firebase_uid=uid,
                is_active=True,
                is_admin=False,
                display_name=display_name,
                photo_url=photo_url,
            )
            db.add(user)
            logger.info(f"Created new user account for {email}")

    # ── Always sync profile fields from Firebase (latest data wins) ───────────
    if display_name and user.display_name != display_name:
        user.display_name = display_name
    if photo_url and user.photo_url != photo_url:
        user.photo_url = photo_url

    try:
        await db.commit()
        await db.refresh(user)
    except Exception as e:
        await db.rollback()
        logger.error(f"Database error during user sync for {email}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to save user data")

    return user


@router.get("/me", response_model=UserResponse)
async def me(
    current_user: User = Depends(get_current_active_user),
):
    """Returns the current user's full profile. Requires a valid Firebase token."""
    return current_user


@router.patch("/profile", response_model=UserResponse)
async def update_profile(
    updates: UserProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Allows the user to update their display_name and/or photo_url.
    Only updates fields that are explicitly provided.
    """
    changed = False
    if updates.display_name is not None:
        current_user.display_name = updates.display_name
        changed = True
    if updates.photo_url is not None:
        current_user.photo_url = updates.photo_url
        changed = True
    if updates.shipping_address is not None:
        current_user.shipping_address = updates.shipping_address
        changed = True

    if changed:
        try:
            await db.commit()
            await db.refresh(current_user)
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to update profile for user {current_user.id}: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Profile update failed")

    return current_user


# ── Admin 2FA ─────────────────────────────────────────────────────

from pydantic import BaseModel

class TwoFAVerify(BaseModel):
    code: str


@router.post("/admin/request-2fa")
async def request_admin_2fa(
    current_user: User = Depends(get_current_active_user),
):
    """Generates a 6-digit code and sends it to the admin's Telegram."""
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    from app.bot.handlers import send_2fa_code as _gen_and_send
    from app.core.config import settings

    # Generate and store the code via the bot module
    import secrets
    from datetime import datetime, timezone, timedelta
    from app.bot.handlers import _2fa_codes

    uid = str(current_user.firebase_uid or current_user.id)
    code = f"{secrets.randbelow(1000000):06d}"
    _2fa_codes[uid] = {
        "code": code,
        "expires": datetime.now(timezone.utc) + timedelta(minutes=5),
    }

    # Send via Telegram to the admin
    try:
        from app.bot.main import bot_app
        await bot_app.bot.send_message(
            chat_id=settings.TELEGRAM_ADMIN_ID,
            text=(
                f"🔐 *Admin 2FA Code*\n\n"
                f"  `{code}`\n\n"
                f"⏱️ Valid for 5 minutes."
            ),
            parse_mode="Markdown",
        )
    except Exception as e:
        logger.warning(f"Could not send 2FA via Telegram: {e}")

    return {"status": "sent", "message": "Code sent to your Telegram"}


@router.post("/admin/verify-2fa")
async def verify_admin_2fa(
    payload: TwoFAVerify,
    current_user: User = Depends(get_current_active_user),
):
    """Verifies the 6-digit 2FA code. Returns success or raises 401."""
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    from app.bot.handlers import verify_2fa_code
    uid = str(current_user.firebase_uid or current_user.id)

    if not verify_2fa_code(uid, payload.code):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired code. Request a new one.",
        )

    return {"status": "verified", "message": "2FA verified successfully"}
