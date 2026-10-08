"""Persistência de contas do Gateway usando SQLite e hash de senha scrypt."""

import hashlib
import hmac
import os
from pathlib import Path
import secrets
import sqlite3


DATABASE_PATH = os.getenv(
    "AUTH_DATABASE_PATH",
    str(Path(__file__).with_name("users.sqlite3")),
)
_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1
_SALT_BYTES = 16
_KEY_BYTES = 32


def _connect() -> sqlite3.Connection:
    path = Path(DATABASE_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=10)
    connection.row_factory = sqlite3.Row
    return connection


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(_SALT_BYTES)
    digest = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=_SCRYPT_N,
        r=_SCRYPT_R,
        p=_SCRYPT_P,
        dklen=_KEY_BYTES,
    )
    return f"scrypt${_SCRYPT_N}${_SCRYPT_R}${_SCRYPT_P}${salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, n_value, r_value, p_value, salt_hex, digest_hex = encoded.split("$")
        if algorithm != "scrypt":
            return False
        expected = bytes.fromhex(digest_hex)
        actual = hashlib.scrypt(
            password.encode("utf-8"),
            salt=bytes.fromhex(salt_hex),
            n=int(n_value),
            r=int(r_value),
            p=int(p_value),
            dklen=len(expected),
        )
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError, MemoryError):
        return False


def _ensure_schema(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            email TEXT,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    columns = {
        row["name"] for row in connection.execute("PRAGMA table_info(users)")
    }
    if "email" not in columns:
        connection.execute("ALTER TABLE users ADD COLUMN email TEXT")
    connection.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS users_email_unique "
        "ON users (lower(email)) WHERE email IS NOT NULL"
    )


def ensure_demo_account(username: str, password: str) -> None:
    """Create the configured local demo account if enabled and not already present."""
    if os.getenv("DEMO_ACCOUNT_ENABLED", "true").lower() != "true":
        return
    normalized = username.strip().lower()
    with _connect() as connection:
        _ensure_schema(connection)
        existing = connection.execute(
            "SELECT 1 FROM users WHERE username = ?", (normalized,)
        ).fetchone()
        if existing is None:
            connection.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                (normalized, f"{normalized}@example.invalid", hash_password(password)),
            )


def create_user(username: str, email: str, password: str) -> bool:
    """Insert a user and return False if username or email is already registered."""
    normalized = username.strip().lower()
    normalized_email = email.strip().lower()
    with _connect() as connection:
        _ensure_schema(connection)
        try:
            connection.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                (normalized, normalized_email, hash_password(password)),
            )
        except sqlite3.IntegrityError:
            return False
    return True


def authenticate_user(username: str, password: str) -> str | None:
    """Return the normalized username for valid credentials, else None."""
    normalized = username.strip().lower()
    with _connect() as connection:
        _ensure_schema(connection)
        row = connection.execute(
            "SELECT password_hash FROM users WHERE username = ?", (normalized,)
        ).fetchone()
    if row is None or not verify_password(password, row["password_hash"]):
        return None
    return normalized
