
import pytest

from app.services.passwords import hash_password, verify_password


def test_hash_password_does_not_store_plaintext():
    password = "SecurePassword123!"

    hashed = hash_password(password)

    assert hashed != password
    assert hashed.startswith("$argon2id$")


def test_correct_password_is_accepted():
    password = "SecurePassword123!"
    hashed = hash_password(password)

    assert verify_password(hashed, password) is True


def test_incorrect_password_is_rejected():
    hashed = hash_password("SecurePassword123!")

    assert verify_password(hashed, "WrongPassword123!") is False


def test_password_hashes_use_random_salts():
    password = "SecurePassword123!"

    first_hash = hash_password(password)
    second_hash = hash_password(password)

    assert first_hash != second_hash


def test_short_password_is_rejected():
    with pytest.raises(ValueError):
        hash_password("short")
