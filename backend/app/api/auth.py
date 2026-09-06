from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sqlite3
import hashlib
import secrets
import jwt

from app.mongo import (
    get_events_collection,
    get_database,
)


# =========================================================
# CONFIGURATION
# =========================================================

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)

BASE_DIR = Path(__file__).resolve().parent.parent

# SQLite is kept ONLY for the existing users table.
DATABASE_PATH = BASE_DIR / "database" / "aegis_security.db"

JWT_SECRET_FILE = BASE_DIR / "core" / ".jwt_secret"

JWT_ALGORITHM = "HS256"

TOKEN_EXPIRATION_MINUTES = 60


# =========================================================
# JWT SECRET
# =========================================================

def get_jwt_secret():

    JWT_SECRET_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    if not JWT_SECRET_FILE.exists():

        secret = secrets.token_urlsafe(64)

        JWT_SECRET_FILE.write_text(
            secret,
            encoding="utf-8"
        )

    return JWT_SECRET_FILE.read_text(
        encoding="utf-8"
    ).strip()


JWT_SECRET = get_jwt_secret()


# =========================================================
# SQLITE DATABASE
# =========================================================
# IMPORTANT:
# SQLite is used ONLY to read/update the existing
# authentication user account.
#
# Activity logs are NO LONGER stored in SQLite.
# =========================================================

def get_connection():

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = sqlite3.Row

    return connection


# =========================================================
# PASSWORD HASHING
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


def verify_password(
    password: str,
    stored_hash: str
) -> bool:

    try:

        salt_hex, hash_hex = stored_hash.split(":")

        salt = bytes.fromhex(
            salt_hex
        )

        expected_hash = bytes.fromhex(
            hash_hex
        )

        actual_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            600_000
        )

        return secrets.compare_digest(
            actual_hash,
            expected_hash
        )

    except Exception:

        return False


# =========================================================
# REQUEST MODEL
# =========================================================

class LoginRequest(BaseModel):

    username: str

    password: str


# =========================================================
# MONGODB AUTHENTICATION LOG
# =========================================================
# ALL authentication activity is stored here.
#
# LOGIN SUCCESS
# LOGIN FAILED
# LOGIN ACCOUNT DISABLED
# LOGOUT
# =========================================================

def create_mongodb_auth_log(
    username: str,
    action: str,
    status: str,
    ip_address: str,
    user_agent: str = "",
    role: str = "",
    user_id=None,
    reason: str = None
):

    try:

        events_collection = get_events_collection()

        if events_collection is None:

            print(
                "MongoDB authentication logging skipped:"
                " database unavailable"
            )

            return False

        event_document = {

            "event_type":
                "AUTHENTICATION",

            "action":
                action,

            "status":
                status,

            "username":
                username,

            "user_id":
                user_id,

            "role":
                role,

            "ip_address":
                ip_address,

            "user_agent":
                user_agent,

            "reason":
                reason,

            "timestamp":
                datetime.now(
                    timezone.utc
                )

        }

        result = events_collection.insert_one(
            event_document
        )

        print(
            "MongoDB authentication activity saved:",
            action,
            status,
            result.inserted_id
        )

        return True

    except Exception as error:

        print(
            "MongoDB authentication logging error:",
            error
        )

        return False


# =========================================================
# LOGIN
# =========================================================

@router.post("/login")
def login(
    credentials: LoginRequest,
    request: Request
):

    username = credentials.username.strip()

    password = credentials.password

    ip_address = (
        request.client.host
        if request.client
        else "unknown"
    )

    user_agent = request.headers.get(
        "user-agent",
        ""
    )


    # =====================================================
    # FIND USER
    # =====================================================
    # Credentials continue to come from SQLite users table.
    # =====================================================

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            username,
            password_hash,
            role,
            is_active
        FROM users
        WHERE username = ?
        """,
        (username,)
    )

    user = cursor.fetchone()


    # =====================================================
    # USER NOT FOUND
    # =====================================================

    if not user:

        connection.close()

        create_mongodb_auth_log(
            username=username,
            action="LOGIN",
            status="FAILED",
            ip_address=ip_address,
            user_agent=user_agent,
            reason="User not found"
        )

        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )


    # =====================================================
    # ACCOUNT DISABLED
    # =====================================================

    if not user["is_active"]:

        connection.close()

        create_mongodb_auth_log(
            username=username,
            action="LOGIN",
            status="FAILED_ACCOUNT_DISABLED",
            ip_address=ip_address,
            user_agent=user_agent,
            role=user["role"],
            user_id=user["id"],
            reason="Account disabled"
        )

        raise HTTPException(
            status_code=403,
            detail="This account is disabled"
        )


    # =====================================================
    # VERIFY PASSWORD
    # =====================================================

    password_valid = verify_password(
        password,
        user["password_hash"]
    )


    # =====================================================
    # INVALID PASSWORD
    # =====================================================

    if not password_valid:

        connection.close()

        create_mongodb_auth_log(
            username=username,
            action="LOGIN",
            status="FAILED",
            ip_address=ip_address,
            user_agent=user_agent,
            role=user["role"],
            user_id=user["id"],
            reason="Invalid password"
        )

        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )


    # =====================================================
    # UPDATE LAST LOGIN
    # =====================================================
    # This remains in SQLite because the existing
    # authentication account is stored there.
    # =====================================================

    login_time = datetime.now(
        timezone.utc
    ).isoformat()

    cursor.execute(
        """
        UPDATE users
        SET last_login = ?
        WHERE id = ?
        """,
        (
            login_time,
            user["id"]
        )
    )

    connection.commit()

    connection.close()


    # =====================================================
    # CREATE JWT
    # =====================================================

    expiration = (
        datetime.now(
            timezone.utc
        )
        +
        timedelta(
            minutes=TOKEN_EXPIRATION_MINUTES
        )
    )

    token_payload = {

        "sub":
            str(user["id"]),

        "username":
            user["username"],

        "role":
            user["role"],

        "exp":
            expiration

    }

    token = jwt.encode(
        token_payload,
        JWT_SECRET,
        algorithm=JWT_ALGORITHM
    )


    # =====================================================
    # MONGODB LOGIN LOG
    # =====================================================

    create_mongodb_auth_log(
        username=username,
        action="LOGIN",
        status="SUCCESS",
        ip_address=ip_address,
        user_agent=user_agent,
        role=user["role"],
        user_id=user["id"],
        reason="Authentication successful"
    )


    # =====================================================
    # RESPONSE
    # =====================================================

    return {

        "success":
            True,

        "message":
            "Authentication successful",

        "access_token":
            token,

        "token_type":
            "bearer",

        "expires_in":
            TOKEN_EXPIRATION_MINUTES * 60,

        "user": {

            "id":
                user["id"],

            "username":
                user["username"],

            "role":
                user["role"]

        }

    }


# =========================================================
# CURRENT USER
# =========================================================

@router.get("/me")
def current_user(
    request: Request
):

    authorization = request.headers.get(
        "Authorization"
    )

    if not authorization:

        raise HTTPException(
            status_code=401,
            detail="Authorization token required"
        )


    if not authorization.startswith(
        "Bearer "
    ):

        raise HTTPException(
            status_code=401,
            detail="Invalid authorization format"
        )


    token = authorization.replace(
        "Bearer ",
        "",
        1
    )


    try:

        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM]
        )

        return {

            "authenticated":
                True,

            "user": {

                "id":
                    payload["sub"],

                "username":
                    payload["username"],

                "role":
                    payload["role"]

            }

        }

    except jwt.ExpiredSignatureError:

        raise HTTPException(
            status_code=401,
            detail="Session expired"
        )

    except jwt.InvalidTokenError:

        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token"
        )


# =========================================================
# LOGOUT
# =========================================================

@router.post("/logout")
def logout(
    request: Request
):

    authorization = request.headers.get(
        "Authorization"
    )

    username = "unknown"

    role = ""

    user_id = None


    # =====================================================
    # GET USER INFORMATION FROM JWT
    # =====================================================

    if authorization:

        try:

            token = authorization.replace(
                "Bearer ",
                "",
                1
            )

            payload = jwt.decode(
                token,
                JWT_SECRET,
                algorithms=[JWT_ALGORITHM]
            )

            username = payload.get(
                "username",
                "unknown"
            )

            role = payload.get(
                "role",
                ""
            )

            user_id = payload.get(
                "sub"
            )

        except Exception:

            pass


    # =====================================================
    # REQUEST INFORMATION
    # =====================================================

    ip_address = (
        request.client.host
        if request.client
        else "unknown"
    )

    user_agent = request.headers.get(
        "user-agent",
        ""
    )


    # =====================================================
    # MONGODB LOGOUT LOG
    # =====================================================
    # NO SQLITE LOGGING HERE.
    # =====================================================

    create_mongodb_auth_log(
        username=username,
        action="LOGOUT",
        status="SUCCESS",
        ip_address=ip_address,
        user_agent=user_agent,
        role=role,
        user_id=user_id,
        reason="User logged out"
    )


    # =====================================================
    # RESPONSE
    # =====================================================

    return {

        "success":
            True,

        "message":
            "Logged out successfully"

    }