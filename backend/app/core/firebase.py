"""
Firebase Admin SDK initializer.

Token VERIFICATION works with just the project ID - no service account needed.
The service-account.json is only needed for CREATING users or other admin writes.

Place your downloaded service-account.json inside the backend/ folder if you
need admin write operations. For auth-only, the project ID is sufficient.
"""
import os
import firebase_admin
from firebase_admin import credentials
import logging

logger = logging.getLogger(__name__)

FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "eshop-2cb38")


def initialize_firebase():
    if firebase_admin._apps:
        return  # Already initialised

    service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH", "")

    if service_account_path and os.path.exists(service_account_path):
        # Full admin SDK — can verify tokens AND write to Firebase
        cred = credentials.Certificate(service_account_path)
        firebase_admin.initialize_app(cred)
        logger.info("Firebase Admin SDK initialized with service account.")
    else:
        # Token-verification-only mode using just the project ID.
        # Firebase verifies tokens against public JWKS — no private key needed.
        try:
            firebase_admin.initialize_app(
                options={"projectId": FIREBASE_PROJECT_ID}
            )
            logger.info(
                f"Firebase Admin SDK initialized (project={FIREBASE_PROJECT_ID}). "
                "Token verification only — no service account."
            )
        except Exception as e:
            logger.error(f"Firebase Admin SDK failed to initialize: {e}")
