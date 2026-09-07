import getpass
import sys
from datetime import datetime, timezone
import hashlib
import secrets
import os

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()


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


password_hash = hash_password(password)


# =========================================================
# MONGODB ATLAS CONNECTION
# =========================================================

try:

    atlas_uri = os.getenv(
        "ATLAS_MONGO_URI"
    )

    atlas_db_name = os.getenv(
        "ATLAS_MONGO_DB_NAME",
        "aegis_security_center"
    )


    # -----------------------------------------------------
    # CHECK ATLAS URI
    # -----------------------------------------------------

    if not atlas_uri:

        print()
        print(
            "ERROR: ATLAS_MONGO_URI is not set."
        )
        print()
        print(
            "Make sure your .env contains:"
        )
        print(
            "ATLAS_MONGO_URI=<your Atlas connection string>"
        )
        print()

        sys.exit(1)


    # -----------------------------------------------------
    # CONNECT TO ATLAS
    # -----------------------------------------------------

    print("----------------------------------------")
    print("Connecting to MongoDB Atlas...")
    print("----------------------------------------")


    client = MongoClient(
        atlas_uri,
        serverSelectionTimeoutMS=10000
    )


    # Force connection test
    client.admin.command("ping")


    database = client[
        atlas_db_name
    ]


    users_collection = database[
        "users"
    ]


    print(
        "========================================"
    )
    print(
        "MONGODB ATLAS : CONNECTED"
    )
    print(
        f"DATABASE      : {atlas_db_name}"
    )
    print(
        "========================================"
    )


    # =====================================================
    # ENSURE USERNAME IS UNIQUE
    # =====================================================

    users_collection.create_index(
        "username",
        unique=True
    )


    # =====================================================
    # CHECK IF USER ALREADY EXISTS
    # =====================================================

    existing_user = users_collection.find_one(
        {
            "username": username
        }
    )


    if existing_user:

        print()
        print(
            f"ERROR: Username '{username}' already exists "
            "in MongoDB Atlas."
        )
        print()

        client.close()

        sys.exit(1)


    # =====================================================
    # CREATE ADMIN USER IN ATLAS
    # =====================================================

    users_collection.insert_one(
        {
            "username": username,

            "password_hash":
                password_hash,

            "role":
                "SECURITY_ADMIN",

            "is_active":
                True,

            "created_at":
                datetime.now(
                    timezone.utc
                ),

            "last_login":
                None
        }
    )


    # =====================================================
    # SUCCESS
    # =====================================================

    print()
    print("=" * 60)
    print(
        " ADMIN ACCOUNT CREATED SUCCESSFULLY"
    )
    print("=" * 60)
    print()

    print(
        f"Username  : {username}"
    )

    print(
        "Role      : SECURITY_ADMIN"
    )

    print(
        "Password  : STORED AS SECURE HASH"
    )

    print()

    print(
        "Database  : MongoDB Atlas"
    )

    print(
        "Collection: users"
    )

    print()

    print(
        "IMPORTANT:"
    )

    print(
        "The password will NOT be displayed or stored"
    )

    print(
        "in plain text."
    )

    print()


    client.close()


# =========================================================
# DUPLICATE USER
# =========================================================

except DuplicateKeyError:

    print()
    print(
        f"ERROR: Username '{username}' already exists "
        "in MongoDB Atlas."
    )
    print()


# =========================================================
# OTHER ERRORS
# =========================================================

except Exception as error:

    print()
    print("=" * 60)
    print(
        " ERROR CONNECTING TO MONGODB ATLAS"
    )
    print("=" * 60)
    print()

    print(
        f"Reason: {error}"
    )

    print()

    print(
        "Check ATLAS_MONGO_URI and "
        "ATLAS_MONGO_DB_NAME."
    )

    print()