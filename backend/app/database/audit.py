from datetime import datetime, timezone

from app.mongo import connect_mongodb


def get_database():
    return connect_mongodb()


def get_admin_activity_collection():
    db = get_database()

    if db is None:
        return None

    return db["admin_activity"]


def get_access_logs_collection():
    db = get_database()

    if db is None:
        return None

    return db["access_logs"]


def log_admin_activity(
    action,
    username=None,
    role=None,
    source=None,
    description=None,
    request=None,
    status="SUCCESS",
):
    """
    Store administrator/security actions.

    Examples:
    BLOCK
    UNBLOCK
    OVERRIDE
    REVOKE_OVERRIDE
    WHITELIST

    Passwords and tokens are NEVER stored.
    """

    try:
        collection = get_admin_activity_collection()

        if collection is None:
            return

        document = {
            "record_type": "ADMIN_ACTIVITY",
            "action": action,
            "username": username,
            "role": role,
            "source": source,
            "description": description,
            "status": status,
            "timestamp": datetime.now(timezone.utc),
        }

        if request is not None:
            if request.client:
                document["client_ip"] = request.client.host

            document["user_agent"] = request.headers.get(
                "user-agent"
            )

        collection.insert_one(document)

    except Exception as error:
        print("Admin activity logging error:", error)


def log_access_event(
    action,
    username=None,
    role=None,
    request=None,
    status="SUCCESS",
    reason=None,
):
    """
    Store authentication/access events.

    Examples:
    LOGIN
    LOGOUT
    FAILED_LOGIN

    Passwords and tokens are NEVER stored.
    """

    try:
        collection = get_access_logs_collection()

        if collection is None:
            return

        document = {
            "record_type": "ACCESS_LOG",
            "action": action,
            "username": username,
            "role": role,
            "status": status,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc),
        }

        if request is not None:
            if request.client:
                document["client_ip"] = request.client.host

            document["user_agent"] = request.headers.get(
                "user-agent"
            )

        collection.insert_one(document)

    except Exception as error:
        print("Access log error:", error)