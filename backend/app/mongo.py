from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb://127.0.0.1:27017"
)

MONGO_DB_NAME = os.getenv(
    "MONGO_DB_NAME",
    "aegis_security_center"
)

client = None
db = None


# =========================================================
# CONNECT TO MONGODB
# =========================================================

def connect_mongodb():
    global client, db

    try:

        client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=5000
        )

        # Test connection
        client.admin.command("ping")

        db = client[MONGO_DB_NAME]

        print("========================================")
        print("AEGIS SECURITY CENTER")
        print("MongoDB Status : CONNECTED")
        print(f"Database       : {MONGO_DB_NAME}")
        print("========================================")

        return db

    except Exception as error:

        print("========================================")
        print("AEGIS SECURITY CENTER")
        print("MongoDB Status : CONNECTION FAILED")
        print(f"Error          : {error}")
        print("========================================")

        return None


# =========================================================
# GET DATABASE
# =========================================================

def get_database():
    global db

    if db is None:
        return connect_mongodb()

    return db


# =========================================================
# SECURITY EVENTS
# =========================================================

def get_events_collection():

    database = get_database()

    if database is None:
        return None

    return database["security_events"]


# =========================================================
# SESSIONS
# =========================================================

def get_sessions_collection():

    database = get_database()

    if database is None:
        return None

    return database["sessions"]


# =========================================================
# DASHBOARD HISTORY
# =========================================================

def get_dashboard_collection():

    database = get_database()

    if database is None:
        return None

    return database["dashboard_history"]


# =========================================================
# USERS
# =========================================================

def get_users_collection():

    database = get_database()

    if database is None:
        return None

    return database["users"]


# =========================================================
# ACCESS LOGS
# =========================================================

def get_access_logs_collection():

    database = get_database()

    if database is None:
        return None

    return database["access_logs"]


# =========================================================
# ALERTS
# =========================================================

def get_alerts_collection():

    database = get_database()

    if database is None:
        return None

    return database["alerts"]


# =========================================================
# BLOCKED SOURCES
# =========================================================

def get_blocked_sources_collection():

    database = get_database()

    if database is None:
        return None

    return database["blocked_sources"]


# =========================================================
# WHITELIST
# =========================================================

def get_whitelist_collection():

    database = get_database()

    if database is None:
        return None

    return database["whitelist"]


# =========================================================
# OVERRIDE ACTIONS
# =========================================================

def get_override_actions_collection():

    database = get_database()

    if database is None:
        return None

    return database["override_actions"]