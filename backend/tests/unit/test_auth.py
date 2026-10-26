from app.core.auth import hash_password, verify_password


def test_password_hash_is_not_the_password_and_verifies():
    password = "a unique test password"
    encoded = hash_password(password)

    assert encoded != password
    assert verify_password(password, encoded)
    assert not verify_password("incorrect password", encoded)
