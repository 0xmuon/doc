import hashlib
import secrets
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

from pwdlib import PasswordHash

ALLOWED_PAYMENT_METHODS = ("COD", "CARD", "UPI", "NET_BANKING")
_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """argon2 hash.the salt lives inside the hash string."""
    return _hasher.hash(password)


def verify_password(password: str, stored: str) -> bool:
    if stored.startswith("$argon2"):
        try:
            return _hasher.verify(password, stored)
        except Exception:
            return False
    # rows hashed before argon2 are salt$hex.they still match until the account is recreated.
    try:
        salt, digest = stored.split("$", 1)
    except ValueError:
        return False
    check = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
    return secrets.compare_digest(check.hex(), digest)


def to_money(value) -> Decimal:
    """keep 2 decimal places so total matches the postgres numeric column."""
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def utcnow() -> datetime:
    """utc time saved in OrderDate column."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
