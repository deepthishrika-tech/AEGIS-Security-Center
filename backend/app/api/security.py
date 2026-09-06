from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from app.mongo import get_dashboard_collection


# =========================================================
# SECURITY ROUTER
# =========================================================

router = APIRouter(
    prefix="/api/security",
    tags=["Security Operations"]
)


# =========================================================
# REQUEST MODELS
# =========================================================

class BlockRequest(BaseModel):

    source: str

    reason: Optional[str] = "Suspicious activity"


class UnblockRequest(BaseModel):

    source: str


class OverrideRequest(BaseModel):

    source: str

    action: str = "UNBLOCK"


class WhitelistRequest(BaseModel):

    source: str

    duration: Optional[str] = "temporary"


# =========================================================
# DEVELOPMENT STORAGE
# =========================================================

blocked_sources = [

    {
        "source": "192.168.1.105",

        "reason": "High request rate",

        "risk_score": 96,

        "blocked_at":
            datetime.now(timezone.utc).isoformat(),

        "status": "BLOCKED"
    },

    {
        "source": "10.0.0.42",

        "reason": "Sequential port scanning",

        "risk_score": 91,

        "blocked_at":
            datetime.now(timezone.utc).isoformat(),

        "status": "BLOCKED"
    }

]


whitelisted_sources = []


# =========================================================
# MONGODB HISTORY LOGGER
# =========================================================

def save_dashboard_history(
    action: str,
    category: str = "SECURITY",
    details: Optional[dict] = None
):

    try:

        history_collection = (
            get_dashboard_collection()
        )

        if history_collection is None:

            return


        history_document = {

            "event_type":
                "DASHBOARD_ACTIVITY",

            "category":
                category,

            "action":
                action,

            "details":
                details or {},

            "timestamp":
                datetime.now(timezone.utc)

        }


        history_collection.insert_one(
            history_document
        )


    except Exception as error:

        # History logging must NEVER
        # stop the actual security operation.

        print(
            "MongoDB dashboard history error:",
            error
        )


# =========================================================
# GET BLOCKED SOURCES
# =========================================================

@router.get("/blocked")
def get_blocked_sources():

    save_dashboard_history(
        action="BLOCKED_SOURCES_VIEWED",
        category="SECURITY",
        details={
            "count": len(blocked_sources)
        }
    )

    return {

        "success": True,

        "count":
            len(blocked_sources),

        "blocked_sources":
            blocked_sources

    }


# =========================================================
# BLOCK SOURCE
# =========================================================

@router.post("/block")
def block_source(
    request: BlockRequest
):

    # -----------------------------------------------------
    # CHECK IF ALREADY BLOCKED
    # -----------------------------------------------------

    for item in blocked_sources:

        if item["source"] == request.source:

            save_dashboard_history(
                action="BLOCK_SOURCE_ALREADY_BLOCKED",
                category="BLOCKING",
                details={
                    "source": request.source
                }
            )

            return {

                "success": False,

                "message":
                    "Source is already blocked",

                "source":
                    request.source

            }


    # -----------------------------------------------------
    # CREATE BLOCK
    # -----------------------------------------------------

    new_block = {

        "source":
            request.source,

        "reason":
            request.reason,

        "risk_score":
            90,

        "blocked_at":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "status":
            "BLOCKED"

    }


    blocked_sources.append(
        new_block
    )


    # -----------------------------------------------------
    # SAVE HISTORY
    # -----------------------------------------------------

    save_dashboard_history(
        action="SOURCE_BLOCKED",
        category="BLOCKING",
        details={
            "source":
                request.source,

            "reason":
                request.reason,

            "risk_score":
                90
        }
    )


    return {

        "success": True,

        "message":
            "Source blocked successfully",

        "source":
            request.source,

        "data":
            new_block

    }


# =========================================================
# UNBLOCK SOURCE
# =========================================================

@router.post("/unblock")
def unblock_source(
    request: UnblockRequest
):

    global blocked_sources


    original_count = len(
        blocked_sources
    )


    blocked_sources = [

        item

        for item in blocked_sources

        if item["source"] != request.source

    ]


    # -----------------------------------------------------
    # SOURCE NOT FOUND
    # -----------------------------------------------------

    if len(blocked_sources) == original_count:

        save_dashboard_history(
            action="UNBLOCK_SOURCE_NOT_FOUND",
            category="BLOCKING",
            details={
                "source":
                    request.source
            }
        )

        return {

            "success": False,

            "message":
                "Source was not found in blocked list",

            "source":
                request.source

        }


    # -----------------------------------------------------
    # SUCCESS
    # -----------------------------------------------------

    save_dashboard_history(
        action="SOURCE_UNBLOCKED",
        category="BLOCKING",
        details={
            "source":
                request.source
        }
    )


    return {

        "success": True,

        "message":
            "Source unblocked successfully",

        "source":
            request.source

    }


# =========================================================
# OVERRIDE ACTION
# =========================================================

@router.post("/override")
def override_source(
    request: OverrideRequest
):

    action = request.action.upper()


    # -----------------------------------------------------
    # UNBLOCK OVERRIDE
    # -----------------------------------------------------

    if action == "UNBLOCK":

        result = unblock_source(
            UnblockRequest(
                source=request.source
            )
        )


        if result["success"]:

            save_dashboard_history(
                action="SECURITY_OVERRIDE",
                category="OVERRIDE",
                details={

                    "source":
                        request.source,

                    "action":
                        "UNBLOCK"

                }
            )


            return {

                "success": True,

                "message":
                    "Security override completed",

                "source":
                    request.source,

                "action":
                    "UNBLOCK"

            }


        return result


    # -----------------------------------------------------
    # UNSUPPORTED ACTION
    # -----------------------------------------------------

    save_dashboard_history(
        action="UNSUPPORTED_OVERRIDE",
        category="OVERRIDE",
        details={

            "source":
                request.source,

            "action":
                request.action

        }
    )


    return {

        "success": False,

        "message":
            "Unsupported override action",

        "action":
            request.action

    }


# =========================================================
# ADD TO WHITELIST
# =========================================================

@router.post("/whitelist")
def whitelist_source(
    request: WhitelistRequest
):

    # -----------------------------------------------------
    # PREVENT DUPLICATES
    # -----------------------------------------------------

    for item in whitelisted_sources:

        if item["source"] == request.source:

            save_dashboard_history(
                action="WHITELIST_ALREADY_EXISTS",
                category="WHITELIST",
                details={
                    "source":
                        request.source
                }
            )

            return {

                "success": False,

                "message":
                    "Source is already whitelisted",

                "source":
                    request.source

            }


    # -----------------------------------------------------
    # CREATE WHITELIST ENTRY
    # -----------------------------------------------------

    whitelist_entry = {

        "source":
            request.source,

        "duration":
            request.duration,

        "added_at":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "status":
            "WHITELISTED"

    }


    whitelisted_sources.append(
        whitelist_entry
    )


    # -----------------------------------------------------
    # REMOVE FROM BLOCKED SOURCES
    # -----------------------------------------------------

    unblock_source(
        UnblockRequest(
            source=request.source
        )
    )


    # -----------------------------------------------------
    # SAVE HISTORY
    # -----------------------------------------------------

    save_dashboard_history(
        action="SOURCE_WHITELISTED",
        category="WHITELIST",
        details={

            "source":
                request.source,

            "duration":
                request.duration

        }
    )


    return {

        "success": True,

        "message":
            "Source added to whitelist",

        "data":
            whitelist_entry

    }


# =========================================================
# GET WHITELIST
# =========================================================

@router.get("/whitelist")
def get_whitelist():

    save_dashboard_history(
        action="WHITELIST_VIEWED",
        category="WHITELIST",
        details={
            "count":
                len(whitelisted_sources)
        }
    )


    return {

        "success": True,

        "count":
            len(whitelisted_sources),

        "whitelisted_sources":
            whitelisted_sources

    }


# =========================================================
# SECURITY STATUS
# =========================================================

@router.get("/status")
def security_status():

    timestamp = datetime.now(
        timezone.utc
    )


    save_dashboard_history(
        action="SECURITY_STATUS_VIEWED",
        category="SECURITY",
        details={

            "system_status":
                "OPERATIONAL",

            "blocked_sources":
                len(blocked_sources),

            "whitelisted_sources":
                len(whitelisted_sources)

        }
    )


    return {

        "system_status":
            "OPERATIONAL",

        "blocked_sources":
            len(blocked_sources),

        "whitelisted_sources":
            len(whitelisted_sources),

        "detection_engine":
            "ACTIVE",

        "blocking_engine":
            "ACTIVE",

        "authentication":
            "ENABLED",

        "timestamp":
            timestamp.isoformat()

    }


# =========================================================
# GET DASHBOARD HISTORY
# =========================================================

@router.get("/history")
def get_dashboard_history(
    limit: int = 100
):

    try:

        history_collection = (
            get_dashboard_collection()
        )


        if history_collection is None:

            return {

                "success":
                    False,

                "message":
                    "MongoDB is not connected",

                "history":
                    []

            }


        # -------------------------------------------------
        # LIMIT SAFETY
        # -------------------------------------------------

        if limit < 1:

            limit = 1


        if limit > 500:

            limit = 500


        # -------------------------------------------------
        # FETCH HISTORY
        # -------------------------------------------------

        records = list(

            history_collection
            .find(
                {},
                {
                    "_id": 0
                }
            )
            .sort(
                "timestamp",
                -1
            )
            .limit(limit)

        )


        return {

            "success":
                True,

            "count":
                len(records),

            "history":
                records

        }


    except Exception as error:

        return {

            "success":
                False,

            "message":
                str(error),

            "history":
                []

        }