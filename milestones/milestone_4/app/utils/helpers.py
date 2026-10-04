import hashlib
import secrets
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

ALLOWED_PAYMENT_METHODS = ("COD", "CARD", "UPI", "NET_BANKING")


def hash_password(password: str) -> str:
    """keep salt and hash together as salt$hex,so no extra column is needed."""
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
    return f"{salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
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
