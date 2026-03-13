import hashlib
import os
import secrets
from datetime import datetime, timedelta
from typing import Optional

class SecurityManager:
    def __init__(self, pepper: str = None):
        # Pepper is an additional secret stored in environment, not in DB
        self.pepper = pepper or os.environ.get('SECURITY_PEPPER', 'default-change-me')
    
    def hash_password(self, password: str) -> str:
        """Return a secure hash of the password with a random salt."""
        salt = secrets.token_hex(16)
        # Use hashlib.pbkdf2_hmac with many iterations
        hash_obj = hashlib.pbkdf2_hmac(
            'sha256',
            (password + self.pepper).encode('utf-8'),
            salt.encode('utf-8'),
            100000  # iterations
        )
        return f"{salt}${hash_obj.hex()}"
    
    def verify_password(self, password: str, stored_hash: str) -> bool:
        """Verify a password against a stored hash (format: salt$hash)."""
        if '$' not in stored_hash:
            return False
        salt, hash_hex = stored_hash.split('$', 1)
        new_hash = hashlib.pbkdf2_hmac(
            'sha256',
            (password + self.pepper).encode('utf-8'),
            salt.encode('utf-8'),
            100000
        ).hex()
        return new_hash == hash_hex