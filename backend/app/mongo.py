# backend/app/mongo.py

import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()


# =========================================================
# ENVIRONMENT
# =========================================================

MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb://127.0.0.1:27017"
)

MONGO_DB_NAME = os.getenv(
    "MONGO_DB_NAME",
    "aegis_security_center"
)

ATLAS_MONGO_URI = os.getenv("ATLAS_MONGO_URI")

ATLAS_MONGO_DB_NAME = os.getenv(
    "ATLAS_MONGO_DB_NAME",
    "aegis_security_center"
)


# Render automatically provides the PORT variable.
# RENDER is used to identify the production environment.
IS_RENDER = bool(os.getenv("RENDER"))


# =========================================================
# GLOBAL CONNECTIONS
# =========================================================

_local_client = None
_local_db = None

_atlas_client = None
_atlas_db = None


# =========================================================
# LOCAL MONGODB
# =========================================================

def connect_local():
    """
    Connect to local MongoDB.

    Used during local development.
    """

    global _local_client, _local_db

    try:
        print("----------------------------------------")
        print("Connecting to LOCAL MongoDB...")
        print("----------------------------------------")

        _local_client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000
        )

        _local_client.admin.command("ping")

        _local_db = _local_client[MONGO_DB_NAME]

        print("========================================")
        print("LOCAL MONGODB : CONNECTED")
        print("DATABASE      :", MONGO_DB_NAME)
        print("========================================")

        return _local_db

    except Exception as e:

        print("========================================")
        print("LOCAL MONGODB : CONNECTION FAILED")
        print("ERROR         :", e)
        print("========================================")

        _local_client = None
        _local_db = None

        return None


# =========================================================
# ATLAS MONGODB
# =========================================================

def connect_atlas():
    """
    Connect to MongoDB Atlas.
    """

    global _atlas_client, _atlas_db

    try:

        print("----------------------------------------")
        print("Connecting to MongoDB Atlas...")
        print("----------------------------------------")

        if not ATLAS_MONGO_URI:

            print("========================================")
            print("MONGODB ATLAS : URI NOT CONFIGURED")
            print("========================================")

            return None

        _atlas_client = MongoClient(
            ATLAS_MONGO_URI,
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=10000
        )

        _atlas_client.admin.command("ping")

        _atlas_db = _atlas_client[ATLAS_MONGO_DB_NAME]

        print("========================================")
        print("MONGODB ATLAS : CONNECTED")
        print("DATABASE      :", ATLAS_MONGO_DB_NAME)
        print("========================================")

        return _atlas_db

    except Exception as e:

        print("========================================")
        print("MONGODB ATLAS : CONNECTION FAILED")
        print("ERROR         :", e)
        print("========================================")

        _atlas_client = None
        _atlas_db = None

        return None


# =========================================================
# BACKWARD COMPATIBILITY
# =========================================================

def connect_mongodb():
    """
    Existing parts of the application may still import
    connect_mongodb(), so keep this function.
    """

    # On Render, Atlas is the production database.
    if IS_RENDER:

        return connect_atlas()

    return connect_local()


# =========================================================
# DATABASE GETTERS
# =========================================================

def get_database():
    """
    Return the primary database.

    Local development:
        Local MongoDB

    Render:
        MongoDB Atlas
    """

    global _local_db

    if IS_RENDER:

        if _atlas_db is None:
            connect_atlas()

        return _atlas_db

    if _local_db is None:
        connect_local()

    return _local_db


def get_atlas_database():
    """
    Return MongoDB Atlas database.
    """

    global _atlas_db

    if _atlas_db is None:
        connect_atlas()

    return _atlas_db


# =========================================================
# DUAL COLLECTION
# =========================================================

class DualCollection:
    """
    Collection wrapper.

    LOCAL DEVELOPMENT:
        Writes go to Local MongoDB + Atlas.

    RENDER:
        Writes go to Atlas only.

    Reads:
        Prefer local when available, otherwise Atlas.
    """

    def __init__(self, collection_name):

        self.collection_name = collection_name

    # -----------------------------------------------------
    # COLLECTIONS
    # -----------------------------------------------------

    def _local_collection(self):

        db = get_database()

        if db is None:
            return None

        return db[self.collection_name]

    def _atlas_collection(self):

        db = get_atlas_database()

        if db is None:
            return None

        return db[self.collection_name]

    # -----------------------------------------------------
    # INSERT ONE
    # -----------------------------------------------------

    def insert_one(self, document, *args, **kwargs):

        local_result = None
        atlas_result = None

        # Render = Atlas only
        if IS_RENDER:

            collection = self._atlas_collection()

            if collection is None:
                raise RuntimeError(
                    "MongoDB Atlas connection is not available."
                )

            return collection.insert_one(
                document,
                *args,
                **kwargs
            )

        # Local + Atlas
        local_collection = self._local_collection()

        if local_collection is not None:

            local_result = local_collection.insert_one(
                document.copy(),
                *args,
                **kwargs
            )

        atlas_collection = self._atlas_collection()

        if atlas_collection is not None:

            atlas_result = atlas_collection.insert_one(
                document.copy(),
                *args,
                **kwargs
            )

        if atlas_result is not None:
            return atlas_result

        if local_result is not None:
            return local_result

        raise RuntimeError(
            "Neither Local MongoDB nor MongoDB Atlas is available."
        )

    # -----------------------------------------------------
    # INSERT MANY
    # -----------------------------------------------------

    def insert_many(self, documents, *args, **kwargs):

        documents = list(documents)

        if IS_RENDER:

            collection = self._atlas_collection()

            if collection is None:
                raise RuntimeError(
                    "MongoDB Atlas connection is not available."
                )

            return collection.insert_many(
                documents,
                *args,
                **kwargs
            )

        local_result = None
        atlas_result = None

        local_collection = self._local_collection()

        if local_collection is not None:

            local_result = local_collection.insert_many(
                [doc.copy() for doc in documents],
                *args,
                **kwargs
            )

        atlas_collection = self._atlas_collection()

        if atlas_collection is not None:

            atlas_result = atlas_collection.insert_many(
                [doc.copy() for doc in documents],
                *args,
                **kwargs
            )

        if atlas_result is not None:
            return atlas_result

        if local_result is not None:
            return local_result

        raise RuntimeError(
            "Neither Local MongoDB nor MongoDB Atlas is available."
        )

    # -----------------------------------------------------
    # UPDATE ONE
    # -----------------------------------------------------

    def update_one(
        self,
        filter,
        update,
        *args,
        **kwargs
    ):

        if IS_RENDER:

            collection = self._atlas_collection()

            if collection is None:
                raise RuntimeError(
                    "MongoDB Atlas connection is not available."
                )

            return collection.update_one(
                filter,
                update,
                *args,
                **kwargs
            )

        local_result = None
        atlas_result = None

        local_collection = self._local_collection()

        if local_collection is not None:

            local_result = local_collection.update_one(
                filter,
                update,
                *args,
                **kwargs
            )

        atlas_collection = self._atlas_collection()

        if atlas_collection is not None:

            atlas_result = atlas_collection.update_one(
                filter,
                update,
                *args,
                **kwargs
            )

        return atlas_result or local_result

    # -----------------------------------------------------
    # UPDATE MANY
    # -----------------------------------------------------

    def update_many(
        self,
        filter,
        update,
        *args,
        **kwargs
    ):

        if IS_RENDER:

            collection = self._atlas_collection()

            if collection is None:
                raise RuntimeError(
                    "MongoDB Atlas connection is not available."
                )

            return collection.update_many(
                filter,
                update,
                *args,
                **kwargs
            )

        local_result = None
        atlas_result = None

        local_collection = self._local_collection()

        if local_collection is not None:

            local_result = local_collection.update_many(
                filter,
                update,
                *args,
                **kwargs
            )

        atlas_collection = self._atlas_collection()

        if atlas_collection is not None:

            atlas_result = atlas_collection.update_many(
                filter,
                update,
                *args,
                **kwargs
            )

        return atlas_result or local_result

    # -----------------------------------------------------
    # REPLACE ONE
    # -----------------------------------------------------

    def replace_one(
        self,
        filter,
        replacement,
        *args,
        **kwargs
    ):

        if IS_RENDER:

            collection = self._atlas_collection()

            if collection is None:
                raise RuntimeError(
                    "MongoDB Atlas connection is not available."
                )

            return collection.replace_one(
                filter,
                replacement,
                *args,
                **kwargs
            )

        local_result = None
        atlas_result = None

        local_collection = self._local_collection()

        if local_collection is not None:

            local_result = local_collection.replace_one(
                filter,
                replacement.copy(),
                *args,
                **kwargs
            )

        atlas_collection = self._atlas_collection()

        if atlas_collection is not None:

            atlas_result = atlas_collection.replace_one(
                filter,
                replacement.copy(),
                *args,
                **kwargs
            )

        return atlas_result or local_result

    # -----------------------------------------------------
    # DELETE ONE
    # -----------------------------------------------------

    def delete_one(
        self,
        filter,
        *args,
        **kwargs
    ):

        if IS_RENDER:

            collection = self._atlas_collection()

            if collection is None:
                raise RuntimeError(
                    "MongoDB Atlas connection is not available."
                )

            return collection.delete_one(
                filter,
                *args,
                **kwargs
            )

        local_result = None
        atlas_result = None

        local_collection = self._local_collection()

        if local_collection is not None:

            local_result = local_collection.delete_one(
                filter,
                *args,
                **kwargs
            )

        atlas_collection = self._atlas_collection()

        if atlas_collection is not None:

            atlas_result = atlas_collection.delete_one(
                filter,
                *args,
                **kwargs
            )

        return atlas_result or local_result

    # -----------------------------------------------------
    # DELETE MANY
    # -----------------------------------------------------

    def delete_many(
        self,
        filter,
        *args,
        **kwargs
    ):

        if IS_RENDER:

            collection = self._atlas_collection()

            if collection is None:
                raise RuntimeError(
                    "MongoDB Atlas connection is not available."
                )

            return collection.delete_many(
                filter,
                *args,
                **kwargs
            )

        local_result = None
        atlas_result = None

        local_collection = self._local_collection()

        if local_collection is not None:

            local_result = local_collection.delete_many(
                filter,
                *args,
                **kwargs
            )

        atlas_collection = self._atlas_collection()

        if atlas_collection is not None:

            atlas_result = atlas_collection.delete_many(
                filter,
                *args,
                **kwargs
            )

        return atlas_result or local_result

    # -----------------------------------------------------
    # FIND
    # -----------------------------------------------------

    def find(self, *args, **kwargs):

        if IS_RENDER:

            collection = self._atlas_collection()

            if collection is None:
                raise RuntimeError(
                    "MongoDB Atlas connection is not available."
                )

            return collection.find(
                *args,
                **kwargs
            )

        local_collection = self._local_collection()

        if local_collection is not None:

            return local_collection.find(
                *args,
                **kwargs
            )

        atlas_collection = self._atlas_collection()

        if atlas_collection is not None:

            return atlas_collection.find(
                *args,
                **kwargs
            )

        raise RuntimeError(
            "Neither Local MongoDB nor MongoDB Atlas is available."
        )

    # -----------------------------------------------------
    # FIND ONE
    # -----------------------------------------------------

    def find_one(self, *args, **kwargs):

        if IS_RENDER:

            collection = self._atlas_collection()

            if collection is None:
                raise RuntimeError(
                    "MongoDB Atlas connection is not available."
                )

            return collection.find_one(
                *args,
                **kwargs
            )

        local_collection = self._local_collection()

        if local_collection is not None:

            result = local_collection.find_one(
                *args,
                **kwargs
            )

            if result is not None:
                return result

        atlas_collection = self._atlas_collection()

        if atlas_collection is not None:

            return atlas_collection.find_one(
                *args,
                **kwargs
            )

        return None

    # -----------------------------------------------------
    # COUNT DOCUMENTS
    # -----------------------------------------------------

    def count_documents(self, *args, **kwargs):

        if IS_RENDER:

            collection = self._atlas_collection()

            if collection is None:
                raise RuntimeError(
                    "MongoDB Atlas connection is not available."
                )

            return collection.count_documents(
                *args,
                **kwargs
            )

        local_collection = self._local_collection()

        if local_collection is not None:

            return local_collection.count_documents(
                *args,
                **kwargs
            )

        atlas_collection = self._atlas_collection()

        if atlas_collection is not None:

            return atlas_collection.count_documents(
                *args,
                **kwargs
            )

        return 0

    # -----------------------------------------------------
    # CREATE INDEX
    # -----------------------------------------------------

    def create_index(self, *args, **kwargs):

        results = []

        if IS_RENDER:

            collection = self._atlas_collection()

            if collection is not None:

                return collection.create_index(
                    *args,
                    **kwargs
                )

            return None

        local_collection = self._local_collection()

        if local_collection is not None:

            results.append(
                local_collection.create_index(
                    *args,
                    **kwargs
                )
            )

        atlas_collection = self._atlas_collection()

        if atlas_collection is not None:

            results.append(
                atlas_collection.create_index(
                    *args,
                    **kwargs
                )
            )

        return results[-1] if results else None


# =========================================================
# GENERIC DUAL COLLECTION
# =========================================================

def get_dual_collection(collection_name):

    return DualCollection(collection_name)


# =========================================================
# SECURITY EVENTS
# =========================================================

def get_events_collection():

    return get_dual_collection(
        "security_events"
    )


# =========================================================
# SESSIONS
# =========================================================

def get_sessions_collection():

    return get_dual_collection(
        "sessions"
    )


# =========================================================
# DASHBOARD HISTORY
# =========================================================

def get_dashboard_collection():

    return get_dual_collection(
        "dashboard_history"
    )


# =========================================================
# ACCESS LOGS
# =========================================================

def get_access_logs_collection():

    return get_dual_collection(
        "access_logs"
    )


# =========================================================
# TEST CONNECTIONS
# =========================================================

def test_mongodb_connections():

    print("")
    print("============================================================")
    print(" MONGODB CONNECTION TEST")
    print("============================================================")

    local = None
    atlas = None

    if not IS_RENDER:

        local = connect_local()

    atlas = connect_atlas()

    print("")

    if local is not None:

        print("Local MongoDB : OK")

    else:

        print("Local MongoDB : NOT AVAILABLE")

    if atlas is not None:

        print("MongoDB Atlas : OK")

    else:

        print("MongoDB Atlas : NOT AVAILABLE")

    print("============================================================")

    return {
        "local": local is not None,
        "atlas": atlas is not None
    }