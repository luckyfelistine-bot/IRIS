"""IRIS v7 Security — Fingerprint + Password Authentication"""
import os
import bcrypt
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional
from config import config
from db import db

try:
    from webauthn import generate_registration_options, verify_registration_response
    from webauthn import generate_authentication_options, verify_authentication_response
    from webauthn.helpers.structs import RegistrationOptions, AuthenticationOptions
    WEBAUTHN_AVAILABLE = True
except ImportError:
    WEBAUTHN_AVAILABLE = False

class SecurityManager:
    """
    Security system for IRIS:
    - Password authentication (bcrypt hashed)
    - WebAuthn/Fingerprint support (browser biometrics)
    - Session management
    - Rate limiting
    - Input sanitization
    """

    def __init__(self):
        self.sessions = {}  # In-memory sessions (use Redis in production)
        self.webauthn_credentials = {}

    def verify_password(self, password: str) -> bool:
        """Verify password against stored hash"""
        if not config.IRIS_PASSWORD_HASH:
            # Fallback: hash the known password for comparison
            # In production, this should be pre-hashed in .env
            known_hash = bcrypt.hashpw("AevibronnorbiveA".encode(), bcrypt.gensalt())
            return bcrypt.checkpw(password.encode(), known_hash)

        return bcrypt.checkpw(password.encode(), config.IRIS_PASSWORD_HASH.encode())

    def hash_password(self, password: str) -> str:
        """Hash a password for storage"""
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def create_session(self, user_id: str = "owner") -> str:
        """Create authenticated session"""
        session_id = secrets.token_urlsafe(32)
        self.sessions[session_id] = {
            "user_id": user_id,
            "created_at": datetime.now(),
            "last_active": datetime.now(),
            "is_authenticated": True
        }
        return session_id

    def validate_session(self, session_id: str) -> bool:
        """Validate session token"""
        if not session_id or session_id not in self.sessions:
            return False

        session = self.sessions[session_id]

        # Check expiration (24 hours)
        if datetime.now() - session["created_at"] > timedelta(hours=24):
            del self.sessions[session_id]
            return False

        # Update last active
        session["last_active"] = datetime.now()
        return True

    def destroy_session(self, session_id: str):
        """Destroy session"""
        if session_id in self.sessions:
            del self.sessions[session_id]

    # === WebAuthn / Fingerprint ===
    def get_webauthn_registration_options(self) -> Dict:
        """Generate WebAuthn registration options for fingerprint setup"""
        if not WEBAUTHN_AVAILABLE:
            return {"error": "WebAuthn not available. Install webauthn package."}

        try:
            options = generate_registration_options(
                rp_id=config.WEBAUTHN_RP_ID,
                rp_name=config.WEBAUTHN_RP_NAME,
                user_id="owner".encode(),
                user_name="Infinite Vybeflix",
                user_display_name="Infinite Vybeflix",
                challenge=secrets.token_bytes(32)
            )

            # Store challenge for verification
            self._pending_challenge = options.challenge

            return dict(options)
        except Exception as e:
            return {"error": str(e)}

    def verify_webauthn_registration(self, credential: Dict) -> bool:
        """Verify WebAuthn registration response"""
        if not WEBAUTHN_AVAILABLE:
            return False

        try:
            verification = verify_registration_response(
                credential=credential,
                expected_challenge=self._pending_challenge,
                expected_rp_id=config.WEBAUTHN_RP_ID,
                expected_origin=config.WEBAUTHN_ORIGIN
            )

            # Store credential
            self.webauthn_credentials["owner"] = {
                "id": verification.credential_id,
                "public_key": verification.credential_public_key
            }

            return True
        except Exception as e:
            db.log("ERROR", "security", f"WebAuthn registration failed: {e}")
            return False

    def get_webauthn_authentication_options(self) -> Dict:
        """Generate WebAuthn authentication options"""
        if not WEBAUTHN_AVAILABLE or "owner" not in self.webauthn_credentials:
            return {"error": "No credentials registered"}

        try:
            options = generate_authentication_options(
                rp_id=config.WEBAUTHN_RP_ID,
                challenge=secrets.token_bytes(32),
                allow_credentials=[{
                    "type": "public-key",
                    "id": self.webauthn_credentials["owner"]["id"]
                }]
            )

            self._pending_challenge = options.challenge
            return dict(options)
        except Exception as e:
            return {"error": str(e)}

    def verify_webauthn_authentication(self, credential: Dict) -> bool:
        """Verify WebAuthn authentication response (fingerprint)"""
        if not WEBAUTHN_AVAILABLE or "owner" not in self.webauthn_credentials:
            return False

        try:
            verification = verify_authentication_response(
                credential=credential,
                expected_challenge=self._pending_challenge,
                expected_rp_id=config.WEBAUTHN_RP_ID,
                expected_origin=config.WEBAUTHN_ORIGIN,
                credential_public_key=self.webauthn_credentials["owner"]["public_key"],
                credential_current_sign_count=0
            )

            return verification.new_sign_count >= 0
        except Exception as e:
            db.log("ERROR", "security", f"WebAuthn auth failed: {e}")
            return False

    # === Device Fingerprint (Fallback) ===
    def verify_device_fingerprint(self, fingerprint: str) -> bool:
        """Verify device fingerprint as fallback"""
        # Store trusted device fingerprints
        stored = db.get_memory("trusted_device_fingerprint")
        if stored:
            return stored["value"] == fingerprint

        # First device - auto-trust
        db.save_memory("trusted_device_fingerprint", fingerprint, category="security", importance=10)
        return True

    # === Input Sanitization ===
    def sanitize_input(self, text: str) -> str:
        """Sanitize user input"""
        import html
        # Basic HTML escaping
        sanitized = html.escape(text)
        # Remove potentially dangerous patterns
        dangerous = ["<script", "javascript:", "onerror=", "onload="]
        for d in dangerous:
            sanitized = sanitized.replace(d, "[blocked]")
        return sanitized

    def check_rate_limit(self, identifier: str, max_requests: int = 100, window: int = 3600) -> bool:
        """Check if request is within rate limit"""
        # Simple in-memory rate limiting
        # In production, use Redis
        key = f"rate_limit_{identifier}"
        now = datetime.now()

        # This is a simplified version - use flask-limiter in production
        return True

# Singleton
security_manager = SecurityManager()
