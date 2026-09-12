import hashlib
import secrets

from app.config.settings import get_settings

settings = get_settings()


def _hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)

    digest = hashlib.pbkdf2_hmac(
        settings.PASSWORD_HASH_ALGORITHM,
        password.encode("utf-8"),
        salt,
        settings.PASSWORD_HASH_ITERATIONS,
    )

    return (
        f"{settings.PASSWORD_HASH_SCHEME}"
        f"${settings.PASSWORD_HASH_ITERATIONS}"
        f"${salt.hex()}"
        f"${digest.hex()}"
    )


def _verify_password(password: str, stored_password: str) -> bool:
    scheme, iterations, salt_hex, stored_hash = stored_password.split("$")

    salt = bytes.fromhex(salt_hex)

    digest = hashlib.pbkdf2_hmac(
        settings.PASSWORD_HASH_ALGORITHM,
        password.encode("utf-8"),
        salt,
        int(iterations),
    )

    return secrets.compare_digest(
        digest.hex(),
        stored_hash,
    )
    

characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"

def _generate_email_code() -> str:
    """Generate a random 6-digit code for email verification."""
    return "".join(secrets.choice(characters) for _ in range(6))