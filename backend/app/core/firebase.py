"""
Firebase Admin SDK initializer.
Called once at app startup.

Place your downloaded service-account.json inside the backend/ folder,
then set FIREBASE_SERVICE_ACCOUNT_PATH in .env to the filename.
"""
import os
import firebase_admin
from firebase_admin import credentials
import logging

logger = logging.getLogger(__name__)

def initialize_firebase():
    if firebase_admin._apps:
        return  # Already initialised

    service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH", "")

    if service_account_path and os.path.exists(service_account_path):
        cred = credentials.Certificate(service_account_path)
        firebase_admin.initialize_app(cred)
        logger.info("Firebase Admin SDK initialized with service account.")
    else:
        # If no file provided, try Application Default Credentials (useful for Cloud Run)
        try:
            firebase_admin.initialize_app()
            logger.info("Firebase Admin SDK initialized with default credentials.")
        except Exception as e:
            logger.warning(f"Firebase Admin SDK not initialized: {e}. Admin auth endpoints will fail.")
