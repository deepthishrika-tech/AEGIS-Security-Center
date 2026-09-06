import getpass
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import secrets


# =========================================================
# DATABASE
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

DATABASE_PATH = (
    BASE_DIR
    / "app"
    / "database"
    / "aegis_security.db"
)


# =========================================================
# PASSWORD HASH
# =========================================================

def hash_password(password: str) -> str:

    salt = secrets.token_bytes(32)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        600_000
    )

    return (
        salt.hex()
        + ":"
        + password_hash.hex()
    )


# =========================================================
# CREATE ADMIN
# =========================================================

print()
print("=" * 60)
print(" AEGIS SECURITY CENTER")
print(" CREATE AUTHORIZED ADMIN")
print("=" * 60)
print()


username = input(
    "Enter admin username: "
).strip()


if not username:

    print("Username cannot be empty.")

    sys.exit(1)


password = getpass.getpass(
    "Enter admin password: "
)


confirm_password = getpass.getpass(
    "Confirm admin password: "
)


if password != confirm_password:

    print()
    print("ERROR: Passwords do not match.")

    sys.exit(1)


if len(password) < 8:

    print()
    print(
        "ERROR: Password must contain at least 8 characters."
    )

    sys.exit(1)


password_hash = hash_password(
    password
)


connection = sqlite3.connect(
    DATABASE_PATH
)

cursor = connection.cursor()


try:

    cursor.execute(
        """
        INSERT INTO users
        (
            username,
            password_hash,
            role,
            is_active,
            created_at
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            username,
            password_hash,
            "SECURITY_ADMIN",
            1,
            datetime.now(
                timezone.utc
            ).isoformat()
        )
    )

    connection.commit()

    print()
    print("=" * 60)
    print(" ADMIN ACCOUNT CREATED SUCCESSFULLY")
    print("=" * 60)
    print()
    print(f"Username : {username}")
    print("Role     : SECURITY_ADMIN")
    print("Password : STORED AS SECURE HASH")
    print()
    print("IMPORTANT:")
    print("The password will NOT be displayed or stored")
    print("in plain text.")
    print()


except sqlite3.IntegrityError:

    print()
    print(
        f"ERROR: Username '{username}' already exists."
    )


finally:

    connection.close()