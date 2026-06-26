"""IRIS v8 Security — Authentication & Session Management"""
import os
import hashlib
import secrets
import hmac
from datetime import datetime, timedelta
from typing import Optional
from config import config
from core.db import db

class SecurityManager:
    """Handles password auth, fingerprint, and session management."""

    def __init__(self):
        self._password_hash = config.IRIS_PASSWORD_HASH

    def _hash_password(self, password: str) -> str:
        """PBKDF2 password hashing."""
        salt = b"iris_v8_salt_2026"
        return hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000).hex()

    def verify_password(self, password: str) -> bool:
        if not self._password_hash:
            # Fallback for development
            return password == "Infinite"
        return hmac.compare_digest(self._hash_password(password), self._password_hash)

    def verify_device_fingerprint(self, fingerprint: str) -> bool:
        """Verify WebAuthn/device fingerprint."""
        # In production: validate against stored fingerprints
        stored = db.search_memory("fingerprint", category="security", limit=1)
        if stored:
            return hmac.compare_digest(stored[0].get("value", ""), fingerprint)
        return False

    def create_session(self, user_id: str = "owner") -> str:
        session_id = secrets.token_urlsafe(32)
        db.create_session(session_id, user_id, expires_hours=24)
        return session_id

    def validate_session(self, session_id: str) -> bool:
        if not session_id:
            return False
        return db.validate_session(session_id)

    def hash_password_for_storage(self, password: str) -> str:
        """Generate hash for .env file."""
        return self._hash_password(password)

# Singleton
security_manager = SecurityManager()
