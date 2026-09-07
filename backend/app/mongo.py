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


def get_database():
    global db

    if db is None:
        return connect_mongodb()

    return db


def get_events_collection():
    database = get_database()

    if database is None:
        return None

    return database["security_events"]


def get_sessions_collection():
    database = get_database()

    if database is None:
        return None

    return database["sessions"]


def get_dashboard_collection():
    database = get_database()

    if database is None:
        return None

    return database["dashboard_history"]