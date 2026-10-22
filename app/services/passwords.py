
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, InvalidHashError


_password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    """Validate and securely hash a password using Argon2id."""

    if not isinstance(password, str):
        raise ValueError("Password must be a string.")

    if len(password) < 12:
        raise ValueError("Password must contain at least 12 characters.")

    return _password_hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    """Return True only when the supplied password matches."""

    try:
        return _password_hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False
