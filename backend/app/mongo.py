from pymongo import MongoClient
import os
from dotenv import load_dotenv


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()


# =========================================================
# LOCAL MONGODB CONFIGURATION
# =========================================================

MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb://127.0.0.1:27017"
)

MONGO_DB_NAME = os.getenv(
    "MONGO_DB_NAME",
    "aegis_security_center"
)


# =========================================================
# MONGODB ATLAS CONFIGURATION
# =========================================================

ATLAS_MONGO_URI = os.getenv(
    "ATLAS_MONGO_URI"
)

ATLAS_MONGO_DB_NAME = os.getenv(
    "ATLAS_MONGO_DB_NAME",
    "aegis_security_center"
)


# =========================================================
# CONNECTION OBJECTS
# =========================================================

local_client = None
local_db = None

atlas_client = None
atlas_db = None


# =========================================================
# CONNECT TO LOCAL MONGODB
# =========================================================

def connect_local():

    global local_client
    global local_db

    try:

        # Already connected
        if local_db is not None:
            return local_db

        print("----------------------------------------")
        print("Connecting to LOCAL MongoDB...")
        print("----------------------------------------")

        local_client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=5000
        )

        # Test connection
        local_client.admin.command("ping")

        local_db = local_client[MONGO_DB_NAME]

        print("========================================")
        print("LOCAL MONGODB : CONNECTED")
        print(f"DATABASE      : {MONGO_DB_NAME}")
        print("========================================")

        return local_db

    except Exception as error:

        print("========================================")
        print("LOCAL MONGODB : CONNECTION FAILED")
        print(f"ERROR         : {error}")
        print("========================================")

        local_db = None

        return None


# =========================================================
# CONNECT TO MONGODB ATLAS
# =========================================================

def connect_atlas():

    global atlas_client
    global atlas_db

    try:

        # Atlas URI not configured
        if not ATLAS_MONGO_URI:

            print("========================================")
            print("MONGODB ATLAS : URI NOT CONFIGURED")
            print("========================================")

            return None

        # Already connected
        if atlas_db is not None:
            return atlas_db

        print("----------------------------------------")
        print("Connecting to MongoDB Atlas...")
        print("----------------------------------------")

        atlas_client = MongoClient(
            ATLAS_MONGO_URI,
            serverSelectionTimeoutMS=5000
        )

        # Test connection
        atlas_client.admin.command("ping")

        atlas_db = atlas_client[
            ATLAS_MONGO_DB_NAME
        ]

        print("========================================")
        print("MONGODB ATLAS : CONNECTED")
        print(f"DATABASE      : {ATLAS_MONGO_DB_NAME}")
        print("========================================")

        return atlas_db

    except Exception as error:

        print("========================================")
        print("MONGODB ATLAS : CONNECTION FAILED")
        print(f"ERROR         : {error}")
        print("========================================")

        atlas_db = None

        return None


# =========================================================
# BACKWARD COMPATIBILITY
# =========================================================
#
# Your existing audit.py imports:
#
# from app.mongo import connect_mongodb
#
# Therefore DO NOT remove this function.
#
# It keeps the existing application compatible.
# =========================================================

def connect_mongodb():

    return connect_local()


# =========================================================
# GET LOCAL DATABASE
# =========================================================

def get_database():

    global local_db

    if local_db is None:
        connect_local()

    return local_db


# =========================================================
# GET ATLAS DATABASE
# =========================================================

def get_atlas_database():

    global atlas_db

    if atlas_db is None:
        connect_atlas()

    return atlas_db


# =========================================================
# DUAL COLLECTION
# =========================================================
#
# Every WRITE operation is sent to:
#
# 1. Local MongoDB
# 2. MongoDB Atlas
#
# This means the same application data exists
# in both databases automatically.
# =========================================================

class DualCollection:

    def __init__(
        self,
        local_collection,
        atlas_collection
    ):

        self.local = local_collection
        self.atlas = atlas_collection


    # =====================================================
    # INSERT ONE
    # =====================================================

    def insert_one(
        self,
        document,
        *args,
        **kwargs
    ):

        local_result = None
        atlas_result = None

        errors = []

        # Local MongoDB
        try:

            if self.local is not None:

                local_result = self.local.insert_one(
                    document.copy(),
                    *args,
                    **kwargs
                )

        except Exception as error:

            errors.append(
                f"Local MongoDB: {error}"
            )


        # MongoDB Atlas
        try:

            if self.atlas is not None:

                atlas_result = self.atlas.insert_one(
                    document.copy(),
                    *args,
                    **kwargs
                )

        except Exception as error:

            errors.append(
                f"MongoDB Atlas: {error}"
            )


        if errors:

            print(
                "MongoDB dual-write warning:",
                " | ".join(errors)
            )


        return local_result or atlas_result


    # =====================================================
    # INSERT MANY
    # =====================================================

    def insert_many(
        self,
        documents,
        *args,
        **kwargs
    ):

        documents = list(documents)

        local_result = None
        atlas_result = None

        errors = []

        # Local
        try:

            if self.local is not None:

                local_result = self.local.insert_many(
                    [doc.copy() for doc in documents],
                    *args,
                    **kwargs
                )

        except Exception as error:

            errors.append(
                f"Local MongoDB: {error}"
            )


        # Atlas
        try:

            if self.atlas is not None:

                atlas_result = self.atlas.insert_many(
                    [doc.copy() for doc in documents],
                    *args,
                    **kwargs
                )

        except Exception as error:

            errors.append(
                f"MongoDB Atlas: {error}"
            )


        if errors:

            print(
                "MongoDB dual-write warning:",
                " | ".join(errors)
            )


        return local_result or atlas_result


    # =====================================================
    # UPDATE ONE
    # =====================================================

    def update_one(
        self,
        filter,
        update,
        *args,
        **kwargs
    ):

        local_result = None
        atlas_result = None

        # Local
        try:

            if self.local is not None:

                local_result = self.local.update_one(
                    filter,
                    update,
                    *args,
                    **kwargs
                )

        except Exception as error:

            print(
                "Local MongoDB update error:",
                error
            )


        # Atlas
        try:

            if self.atlas is not None:

                atlas_result = self.atlas.update_one(
                    filter,
                    update,
                    *args,
                    **kwargs
                )

        except Exception as error:

            print(
                "MongoDB Atlas update error:",
                error
            )


        return local_result or atlas_result


    # =====================================================
    # UPDATE MANY
    # =====================================================

    def update_many(
        self,
        filter,
        update,
        *args,
        **kwargs
    ):

        local_result = None
        atlas_result = None

        # Local
        try:

            if self.local is not None:

                local_result = self.local.update_many(
                    filter,
                    update,
                    *args,
                    **kwargs
                )

        except Exception as error:

            print(
                "Local MongoDB update error:",
                error
            )


        # Atlas
        try:

            if self.atlas is not None:

                atlas_result = self.atlas.update_many(
                    filter,
                    update,
                    *args,
                    **kwargs
                )

        except Exception as error:

            print(
                "MongoDB Atlas update error:",
                error
            )


        return local_result or atlas_result


    # =====================================================
    # REPLACE ONE
    # =====================================================

    def replace_one(
        self,
        filter,
        replacement,
        *args,
        **kwargs
    ):

        local_result = None
        atlas_result = None

        try:

            if self.local is not None:

                local_result = self.local.replace_one(
                    filter,
                    replacement.copy(),
                    *args,
                    **kwargs
                )

        except Exception as error:

            print(
                "Local MongoDB replace error:",
                error
            )


        try:

            if self.atlas is not None:

                atlas_result = self.atlas.replace_one(
                    filter,
                    replacement.copy(),
                    *args,
                    **kwargs
                )

        except Exception as error:

            print(
                "MongoDB Atlas replace error:",
                error
            )


        return local_result or atlas_result


    # =====================================================
    # DELETE ONE
    # =====================================================

    def delete_one(
        self,
        filter,
        *args,
        **kwargs
    ):

        local_result = None
        atlas_result = None

        # Local
        try:

            if self.local is not None:

                local_result = self.local.delete_one(
                    filter,
                    *args,
                    **kwargs
                )

        except Exception as error:

            print(
                "Local MongoDB delete error:",
                error
            )


        # Atlas
        try:

            if self.atlas is not None:

                atlas_result = self.atlas.delete_one(
                    filter,
                    *args,
                    **kwargs
                )

        except Exception as error:

            print(
                "MongoDB Atlas delete error:",
                error
            )


        return local_result or atlas_result


    # =====================================================
    # DELETE MANY
    # =====================================================

    def delete_many(
        self,
        filter,
        *args,
        **kwargs
    ):

        local_result = None
        atlas_result = None

        try:

            if self.local is not None:

                local_result = self.local.delete_many(
                    filter,
                    *args,
                    **kwargs
                )

        except Exception as error:

            print(
                "Local MongoDB delete error:",
                error
            )


        try:

            if self.atlas is not None:

                atlas_result = self.atlas.delete_many(
                    filter,
                    *args,
                    **kwargs
                )

        except Exception as error:

            print(
                "MongoDB Atlas delete error:",
                error
            )


        return local_result or atlas_result


    # =====================================================
    # FIND
    # =====================================================

    def find(
        self,
        *args,
        **kwargs
    ):

        # Prefer local database
        if self.local is not None:

            return self.local.find(
                *args,
                **kwargs
            )


        # Fallback to Atlas
        if self.atlas is not None:

            return self.atlas.find(
                *args,
                **kwargs
            )


        return []


    # =====================================================
    # FIND ONE
    # =====================================================

    def find_one(
        self,
        *args,
        **kwargs
    ):

        if self.local is not None:

            return self.local.find_one(
                *args,
                **kwargs
            )


        if self.atlas is not None:

            return self.atlas.find_one(
                *args,
                **kwargs
            )


        return None


    # =====================================================
    # COUNT DOCUMENTS
    # =====================================================

    def count_documents(
        self,
        *args,
        **kwargs
    ):

        if self.local is not None:

            return self.local.count_documents(
                *args,
                **kwargs
            )


        if self.atlas is not None:

            return self.atlas.count_documents(
                *args,
                **kwargs
            )


        return 0


    # =====================================================
    # CREATE INDEX
    # =====================================================

    def create_index(
        self,
        *args,
        **kwargs
    ):

        local_result = None
        atlas_result = None

        # Local
        try:

            if self.local is not None:

                local_result = self.local.create_index(
                    *args,
                    **kwargs
                )

        except Exception as error:

            print(
                "Local MongoDB index error:",
                error
            )


        # Atlas
        try:

            if self.atlas is not None:

                atlas_result = self.atlas.create_index(
                    *args,
                    **kwargs
                )

        except Exception as error:

            print(
                "MongoDB Atlas index error:",
                error
            )


        return local_result or atlas_result


# =========================================================
# DUAL COLLECTION FACTORY
# =========================================================

def get_dual_collection(
    collection_name
):

    local_database = get_database()

    atlas_database = get_atlas_database()

    local_collection = None

    atlas_collection = None


    # Local collection
    if local_database is not None:

        local_collection = (
            local_database[
                collection_name
            ]
        )


    # Atlas collection
    if atlas_database is not None:

        atlas_collection = (
            atlas_database[
                collection_name
            ]
        )


    return DualCollection(
        local_collection,
        atlas_collection
    )


# =========================================================
# SECURITY EVENTS
# =========================================================

def get_events_collection():

    return get_dual_collection(
        "security_events"
    )


# =========================================================
# ACCESS LOGS
# =========================================================

def get_access_logs_collection():

    return get_dual_collection(
        "access_logs"
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
# TEST BOTH CONNECTIONS
# =========================================================

def test_mongodb_connections():

    print()
    print("========================================")
    print("       AEGIS MONGODB STATUS")
    print("========================================")

    local = connect_local()

    atlas = connect_atlas()


    if local is not None:

        print("LOCAL  : OK")

    else:

        print("LOCAL  : FAILED")


    if atlas is not None:

        print("ATLAS  : OK")

    else:

        print("ATLAS  : FAILED")


    print("========================================")
    print()