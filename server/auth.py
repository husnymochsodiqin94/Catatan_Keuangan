"""Keamanan auth: hashing password & pembuatan token — stdlib saja.

PBKDF2-HMAC-SHA256 dengan salt acak per pengguna. Tanpa dependency pihak ketiga.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets

_ITERATIONS = 200_000


def hash_password(password: str) -> str:
    """Kembalikan string 'salt$hash' untuk disimpan."""
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"),
                             bytes.fromhex(salt), _ITERATIONS)
    return f"{salt}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, expected = stored.split("$", 1)
    except (ValueError, AttributeError):
        return False
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"),
                             bytes.fromhex(salt), _ITERATIONS)
    return hmac.compare_digest(dk.hex(), expected)


def new_token() -> str:
    return secrets.token_urlsafe(32)


def new_otp() -> str:
    """Kode OTP 6 digit untuk 2FA email."""
    return f"{secrets.randbelow(1_000_000):06d}"


def hash_otp(code: str) -> str:
    return hashlib.sha256((code or "").encode("utf-8")).hexdigest()


def verify_otp(code: str, stored_hash: str) -> bool:
    return hmac.compare_digest(hash_otp(code), stored_hash or "")
