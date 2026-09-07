from datetime import datetime, timezone

from app.mongo import get_access_logs_collection


# =========================================================
# ACCESS LOGGING
# =========================================================

def log_access_event(
    request=None,
    username=None,
    user_id=None,
    role=None,
    action=None,
    status=None,
    endpoint=None,
    method=None,
    response_status=None,
    ip_address=None,
    user_agent=None,
    details=None,
):
    """
    Store API access activity in MongoDB.

    Because get_access_logs_collection() uses the dual
    MongoDB collection, the same record is written to:

        Local MongoDB
        MongoDB Atlas
    """

    try:
        # -------------------------------------------------
        # REQUEST INFORMATION
        # -------------------------------------------------

        if request is not None:

            if not ip_address:
                ip_address = (
                    request.client.host
                    if request.client
                    else "unknown"
                )

            if not user_agent:
                user_agent = request.headers.get(
                    "user-agent",
                    ""
                )

            if not endpoint:
                endpoint = request.url.path

            if not method:
                method = request.method

        # -------------------------------------------------
        # DEFAULT VALUES
        # -------------------------------------------------

        ip_address = ip_address or "unknown"
        user_agent = user_agent or ""
        endpoint = endpoint or ""
        method = method or ""
        action = action or "API_ACCESS"
        status = status or "UNKNOWN"

        # -------------------------------------------------
        # DOCUMENT
        # -------------------------------------------------

        log_document = {
            "event_type": "ACCESS_LOG",

            "action": action,
            "status": status,

            "username": username,
            "user_id": user_id,
            "role": role,

            "method": method,
            "endpoint": endpoint,
            "response_status": response_status,

            "ip_address": ip_address,
            "user_agent": user_agent,

            "details": details,

            "timestamp": datetime.now(
                timezone.utc
            ),
        }

        # -------------------------------------------------
        # DUAL MONGODB WRITE
        # -------------------------------------------------

        access_logs_collection = (
            get_access_logs_collection()
        )

        if access_logs_collection is None:
            print(
                "Access logging skipped: "
                "MongoDB unavailable"
            )
            return False

        result = access_logs_collection.insert_one(
            log_document
        )

        print(
            "Access log saved:",
            action,
            status,
            result.inserted_id
        )

        return True

    except Exception as error:

        print(
            "Access logging error:",
            error
        )

        return False


# =========================================================
# ADMIN ACTIVITY LOGGING
# =========================================================

def log_admin_activity(
    request=None,
    username=None,
    user_id=None,
    role=None,
    action=None,
    status=None,
    endpoint=None,
    method=None,
    response_status=None,
    ip_address=None,
    user_agent=None,
    details=None,
):
    """
    Store administrator activity.

    This is kept as a separate function because main.py
    imports and uses log_admin_activity().

    The actual database storage is handled by
    log_access_event(), so the record is automatically
    written to BOTH:

        Local MongoDB
        MongoDB Atlas
    """

    try:

        # -------------------------------------------------
        # ADMIN ACTIVITY DETAILS
        # -------------------------------------------------

        if details is None:
            details = {}

        if not isinstance(details, dict):
            details = {
                "message": str(details)
            }

        details = {
            **details,
            "activity_type": "ADMIN_ACTIVITY",
        }

        # -------------------------------------------------
        # WRITE THROUGH ACCESS LOGGER
        # -------------------------------------------------

        return log_access_event(
            request=request,

            username=username,
            user_id=user_id,
            role=role,

            action=action or "ADMIN_ACTIVITY",
            status=status or "SUCCESS",

            endpoint=endpoint,
            method=method,
            response_status=response_status,

            ip_address=ip_address,
            user_agent=user_agent,

            details=details,
        )

    except Exception as error:

        print(
            "Admin activity logging error:",
            error
        )

        return False


# =========================================================
# TEST FUNCTION
# =========================================================

def test_audit_logging():
    """
    Simple test for the audit logger.
    """

    return log_access_event(
        username="system",
        role="SYSTEM",
        action="AUDIT_TEST",
        status="SUCCESS",
        endpoint="/internal/audit-test",
        method="TEST",
        response_status=200,
        ip_address="127.0.0.1",
        user_agent="AEGIS",
        details={
            "message": "Audit logging test"
        },
    )