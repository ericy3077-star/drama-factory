"""Password hashing and cryptographic utilities."""
from __future__ import annotations

import secrets
import string

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    """Return a bcrypt-hashed password string."""
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain-text password against a stored hash."""
    return pwd_context.verify(plain, hashed)


def generate_token(length: int = 32) -> str:
    """Generate a cryptographically secure URL-safe random token."""
    return secrets.token_urlsafe(length)


def generate_otp(digits: int = 6) -> str:
    """Generate a numeric OTP of *digits* length."""
    alphabet = string.digits
    return "".join(secrets.choice(alphabet) for _ in range(digits))
