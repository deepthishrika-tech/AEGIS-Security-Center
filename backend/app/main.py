from datetime import datetime, timezone
import os
import time
import asyncio

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

# =========================================================
# AUDIT LOGGING
# =========================================================

from app.database.audit import (
    log_admin_activity,
    log_access_event,
)

# =========================================================
# API ROUTERS
# =========================================================

from app.api.auth import router as auth_router
from app.api.security import router as security_router
from app.api.history import router as history_router

# =========================================================
# MONGODB
# =========================================================

from app.mongo import (
    connect_mongodb,
    get_events_collection,
    get_dashboard_collection,
)

# =========================================================
# APPLICATION
# =========================================================

app = FastAPI(
    title="AI Attack Tool Detector & Blocker",
    description=(
        "Real-time AI attack detection, blocking, "
        "authorized override and security monitoring system"
    ),
    version="1.0.0",
)

# =========================================================
# CORS
# =========================================================

DEFAULT_CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:5175",
    "http://127.0.0.1:5175",
]

# Extra production origins (e.g. your deployed frontend URL)
# can be supplied as a comma-separated list via the
# CORS_ORIGINS environment variable, without removing the
# local dev origins above.
EXTRA_CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://aegis-security-center-frontend.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# =========================================================
# MONGODB ACTIVITY LOGGER
# =========================================================

@app.middleware("http")
async def activity_logger(request: Request, call_next):

    start_time = time.time()

    response = None
    error_message = None

    try:

        response = await call_next(request)

        return response

    except Exception as error:

        error_message = str(error)

        raise

    finally:

        try:

            execution_time = round(
                (time.time() - start_time) * 1000,
                2,
            )

            # =================================================
            # API ACTIVITY LOGGING
            # =================================================

            events_collection = get_events_collection()

            if events_collection is not None:

                event_document = {

                    "event_type":
                        "API_REQUEST",

                    "method":
                        request.method,

                    "path":
                        request.url.path,

                    "query":
                        str(request.url.query),

                    "client_ip": (
                        request.client.host
                        if request.client
                        else None
                    ),

                    "user_agent":
                        request.headers.get(
                            "user-agent"
                        ),

                    "status_code": (
                        response.status_code
                        if response
                        else 500
                    ),

                    "execution_time_ms":
                        execution_time,

                    "error":
                        error_message,

                    "timestamp":
                        datetime.now(timezone.utc),
                }

                events_collection.insert_one(
                    event_document
                )

            # =================================================
            # ADMIN / ACCESS AUDIT LOGGING
            # =================================================

            path = request.url.path
            method = request.method

            status_code = (
                response.status_code
                if response
                else 500
            )

            # =================================================
            # ADMIN LOGIN
            # =================================================

            if (
                method == "POST"
                and path == "/api/auth/login"
            ):

                log_access_event(

                    action="LOGIN",

                    request=request,

                    status=(
                        "SUCCESS"
                        if status_code < 400
                        else "FAILED"
                    ),

                    reason=(
                        None
                        if status_code < 400
                        else "Authentication failed"
                    ),
                )

            # =================================================
            # ADMIN LOGOUT
            # =================================================

            elif (
                method == "POST"
                and path == "/api/auth/logout"
            ):

                log_access_event(

                    action="LOGOUT",

                    request=request,

                    status=(
                        "SUCCESS"
                        if status_code < 400
                        else "FAILED"
                    ),
                )

            # =================================================
            # BLOCK SOURCE
            # =================================================

            elif (
                method == "POST"
                and path == "/api/security/block"
            ):

                log_admin_activity(

                    action="BLOCK",

                    request=request,

                    status=(
                        "SUCCESS"
                        if status_code < 400
                        else "FAILED"
                    ),

                    description=(
                        "Administrator blocked "
                        "a security source."
                    ),
                )

            # =================================================
            # UNBLOCK SOURCE
            # =================================================

            elif (
                method == "POST"
                and path == "/api/security/unblock"
            ):

                log_admin_activity(

                    action="UNBLOCK",

                    request=request,

                    status=(
                        "SUCCESS"
                        if status_code < 400
                        else "FAILED"
                    ),

                    description=(
                        "Administrator unblocked "
                        "a security source."
                    ),
                )

            # =================================================
            # SECURITY OVERRIDE
            # =================================================

            elif (
                method == "POST"
                and path == "/api/security/override"
            ):

                log_admin_activity(

                    action="OVERRIDE",

                    request=request,

                    status=(
                        "SUCCESS"
                        if status_code < 400
                        else "FAILED"
                    ),

                    description=(
                        "Administrator performed "
                        "an authorized security override."
                    ),
                )

            # =================================================
            # WHITELIST
            # =================================================

            elif (
                method == "POST"
                and path == "/api/security/whitelist"
            ):

                log_admin_activity(

                    action="WHITELIST",

                    request=request,

                    status=(
                        "SUCCESS"
                        if status_code < 400
                        else "FAILED"
                    ),

                    description=(
                        "Administrator changed "
                        "the security whitelist."
                    ),
                )

        except Exception as log_error:

            # Logging must NEVER break the application.

            print(
                "MongoDB activity logging error:",
                log_error,
            )


# =========================================================
# REGISTER API ROUTERS
# =========================================================

app.include_router(auth_router)
app.include_router(security_router)
app.include_router(history_router)


# =========================================================
# ROOT
# =========================================================

@app.get("/")
def root():

    return {

        "application":
            "AI Attack Tool Detector & Blocker",

        "status":
            "online",

        "version":
            "1.0.0",

        "message":
            "Security monitoring system is running",
    }


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/api/health")
def health_check():

    timestamp = datetime.now(timezone.utc)

    return {

        "status":
            "healthy",

        "service":
            "detection-engine",

        "timestamp":
            timestamp.isoformat(),
    }


# =========================================================
# CREATE DASHBOARD DATA
# =========================================================

def create_dashboard_data():

    timestamp = datetime.now(timezone.utc)

    dashboard_data = {

        "active_alerts": 47,

        "protected_assets": 2847,

        "attack_sources": 23,

        "system_health": 98.7,

        "risk_score": 92,

        "critical_risks": 9,

        "high_risks": 17,

        "system_status":
            "OPERATIONAL",

        # =================================================
        # SERVICES
        # =================================================

        "services": [

            {
                "name":
                    "Detection Engine",

                "status":
                    "healthy",
            },

            {
                "name":
                    "FastAPI Backend",

                "status":
                    "healthy",
            },

            {
                "name":
                    "Database",

                "status":
                    "healthy",
            },

            {
                "name":
                    "Threat Simulator",

                "status":
                    "warning",
            },
        ],

        # =================================================
        # THREAT DISTRIBUTION
        # =================================================

        "threat_distribution": {

            "ai_tools":
                36,

            "scanning":
                28,

            "payloads":
                16,

            "authentication":
                9,

            # Keep "auth" for existing frontend
            "auth":
                9,

            "other":
                5,
        },

        "timestamp":
            timestamp.isoformat(),
    }

    return dashboard_data


# =========================================================
# SAVE DASHBOARD HISTORY
# =========================================================

def save_dashboard_history(dashboard_data):

    try:

        dashboard_collection = (
            get_dashboard_collection()
        )

        if dashboard_collection is None:

            print(
                "Dashboard history: collection unavailable"
            )

            return False

        timestamp = datetime.now(timezone.utc)

        dashboard_history = {

            "record_type":
                "DASHBOARD_SNAPSHOT",

            "active_alerts":
                dashboard_data["active_alerts"],

            "protected_assets":
                dashboard_data["protected_assets"],

            "attack_sources":
                dashboard_data["attack_sources"],

            "system_health":
                dashboard_data["system_health"],

            "risk_score":
                dashboard_data["risk_score"],

            "critical_risks":
                dashboard_data["critical_risks"],

            "high_risks":
                dashboard_data["high_risks"],

            "system_status":
                dashboard_data["system_status"],

            "threat_distribution":
                dashboard_data["threat_distribution"],

            "services":
                dashboard_data["services"],

            "timestamp":
                timestamp,
        }

        result = dashboard_collection.insert_one(
            dashboard_history
        )

        print(
            "Dashboard history saved:",
            result.inserted_id
        )

        return True

    except Exception as error:

        print(
            "Dashboard history logging error:",
            error
        )

        return False


# =========================================================
# DASHBOARD API
# =========================================================

@app.get("/api/dashboard")
def dashboard():

    dashboard_data = create_dashboard_data()

    # Save every API request to MongoDB
    save_dashboard_history(
        dashboard_data
    )

    return dashboard_data


# =========================================================
# AUTOMATIC REAL-TIME DASHBOARD HISTORY
# =========================================================

async def automatic_dashboard_history():

    print(
        " MongoDB History : AUTO UPDATE ENABLED"
    )

    while True:

        try:

            # Create fresh dashboard data
            dashboard_data = create_dashboard_data()

            # Store snapshot in MongoDB
            save_dashboard_history(
                dashboard_data
            )

        except Exception as error:

            print(
                "Automatic history error:",
                error
            )

        # =================================================
        # UPDATE EVERY 5 SECONDS
        # =================================================

        await asyncio.sleep(5)


# =========================================================
# SYSTEM STATUS
# =========================================================

@app.get("/api/system/status")
def system_status():

    timestamp = datetime.now(timezone.utc)

    return {

        "status":
            "OPERATIONAL",

        "services": {

            "backend":
                "healthy",

            "database":
                "healthy",

            "detection_engine":
                "healthy",

            "threat_simulator":
                "warning",
        },

        "timestamp":
            timestamp.isoformat(),
    }


# =========================================================
# API INFORMATION
# =========================================================

@app.get("/api")
def api_information():

    return {

        "application":
            "AI Attack Tool Detector & Blocker",

        "version":
            "1.0.0",

        "status":
            "online",

        "modules": [

            "Authentication",

            "Live Security Monitoring",

            "Attack Detection",

            "Source Blocking",

            "Authorized Override",

            "Whitelist Management",

            "Access Logging",

            "Threat Simulation",

            "History Management",
        ],
    }


# =========================================================
# MONGODB TEST ENDPOINT
# =========================================================

@app.get("/api/database/status")
def database_status():

    try:

        database = connect_mongodb()

        if database is None:

            return {

                "status":
                    "disconnected",

                "database":
                    "aegis_security_center",
            }

        # Test database with ping
        database.command("ping")

        return {

            "status":
                "connected",

            "database":
                "aegis_security_center",

            "collections":
                database.list_collection_names(),

            "timestamp":
                datetime.now(
                    timezone.utc
                ).isoformat(),
        }

    except Exception as error:

        return {

            "status":
                "error",

            "message":
                str(error),

            "timestamp":
                datetime.now(
                    timezone.utc
                ).isoformat(),
        }


# =========================================================
# APPLICATION STARTUP
# =========================================================

@app.on_event("startup")
async def startup_event():

    print()

    print("=" * 60)

    print(
        " AEGIS SECURITY CENTER"
    )

    print(
        " AI Attack Tool Detector & Blocker"
    )

    print("=" * 60)

    # =====================================================
    # CONNECT MONGODB
    # =====================================================

    database = connect_mongodb()

    if database is not None:

        print(
            " MongoDB       : CONNECTED"
        )

    else:

        print(
            " MongoDB       : CONNECTION FAILED"
        )

    # =====================================================
    # START AUTOMATIC HISTORY LOGGER
    # =====================================================

    if database is not None:

        asyncio.create_task(
            automatic_dashboard_history()
        )

        print(
            " MongoDB History : AUTO UPDATE ENABLED"
        )

    else:

        print(
            " MongoDB History : DISABLED"
        )

    print(
        " Backend Status : ONLINE"
    )

    print(
        " Authentication : ENABLED"
    )

    print(
        " Security API   : ENABLED"
    )

    print(
        " History API    : ENABLED"
    )

    print(
        " Override       : ENABLED"
    )

    print(
        " Access Logging : ENABLED"
    )

    print("=" * 60)

    print()