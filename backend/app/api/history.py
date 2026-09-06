from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.mongo import get_dashboard_collection, get_database


# =========================================================
# DASHBOARD HISTORY ROUTER
# =========================================================

router = APIRouter(
    prefix="/api/history",
    tags=["Dashboard History"]
)


# =========================================================
# REQUEST MODEL
# =========================================================

class HistoryRequest(BaseModel):
    username: Optional[str] = "Unknown"
    action: str
    section: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


# =========================================================
# STORE MANUAL DASHBOARD HISTORY
# =========================================================

@router.post("/log")
def log_dashboard_history(request: HistoryRequest):

    collection = get_dashboard_collection()

    if collection is None:
        raise HTTPException(
            status_code=503,
            detail="MongoDB is not available."
        )

    history_document = {
        "record_type": "DASHBOARD_ACTIVITY",
        "username": request.username,
        "action": request.action,
        "section": request.section,
        "details": request.details or {},
        "timestamp": datetime.now(timezone.utc),
    }

    result = collection.insert_one(history_document)

    return {
        "success": True,
        "message": "Dashboard activity stored successfully.",
        "history_id": str(result.inserted_id)
    }


# =========================================================
# GET COMPLETE REAL-TIME HISTORY
# =========================================================

@router.get("")
def get_dashboard_history(limit: int = 100):

    database = get_database()

    if database is None:
        raise HTTPException(
            status_code=503,
            detail="MongoDB is not available."
        )

    # =====================================================
    # MONGODB COLLECTIONS
    # =====================================================

    dashboard_collection = database["dashboard_history"]
    access_collection = database["access_logs"]
    security_collection = database["security_events"]

    # =====================================================
    # 1. DASHBOARD HISTORY
    # =====================================================

    dashboard_history = list(
        dashboard_collection
        .find({})
        .sort("timestamp", -1)
        .limit(limit)
    )

    for item in dashboard_history:

        item["_id"] = str(item["_id"])

        item["history_source"] = "DASHBOARD"

        item["display_action"] = item.get(
            "action",
            item.get("record_type", "DASHBOARD_SNAPSHOT")
        )

        item["display_username"] = item.get(
            "username",
            "SYSTEM"
        )

    # =====================================================
    # 2. LOGIN / LOGOUT / ACCESS HISTORY
    # =====================================================

    access_history = list(
        access_collection
        .find({})
        .sort("timestamp", -1)
        .limit(limit)
    )

    for item in access_history:

        item["_id"] = str(item["_id"])

        item["history_source"] = "ACCESS"

        item["display_action"] = item.get(
            "action",
            "ACCESS"
        )

        item["display_username"] = item.get(
            "username",
            "Unknown"
        )

    # =====================================================
    # 3. SECURITY / API ACTIVITY
    # =====================================================

    security_history = list(
        security_collection
        .find({})
        .sort("timestamp", -1)
        .limit(limit)
    )

    for item in security_history:

        item["_id"] = str(item["_id"])

        item["history_source"] = "SECURITY"

        # API request
        if item.get("event_type") == "API_REQUEST":

            method = item.get("method", "")
            path = item.get("path", "")

            item["display_action"] = (
                f"{method} {path}"
            ).strip()

        else:

            item["display_action"] = item.get(
                "action",
                item.get(
                    "event_type",
                    "SECURITY_EVENT"
                )
            )

        item["display_username"] = item.get(
            "username",
            "SYSTEM"
        )

    # =====================================================
    # 4. COMBINE EVERYTHING
    # =====================================================

    complete_history = (
        dashboard_history
        + access_history
        + security_history
    )

    # =====================================================
    # 5. SORT ALL EVENTS BY TIME
    # =====================================================

    def get_timestamp(item):

        timestamp = item.get("timestamp")

        if isinstance(timestamp, datetime):
            return timestamp

        return datetime.min.replace(
            tzinfo=timezone.utc
        )

    complete_history.sort(
        key=get_timestamp,
        reverse=True
    )

    # =====================================================
    # 6. FINAL LIMIT
    # =====================================================

    complete_history = complete_history[:limit]

    # =====================================================
    # 7. RESPONSE
    # =====================================================

    return {
        "success": True,
        "count": len(complete_history),
        "history": complete_history
    }