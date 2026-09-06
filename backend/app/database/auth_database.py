import sqlite3
from pathlib import Path


# =========================================================
# DATABASE LOCATION
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

DATABASE_PATH = BASE_DIR / "aegis_security.db"


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_connection():

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = sqlite3.Row

    return connection


# =========================================================
# INITIALIZE DATABASE
# =========================================================

def initialize_database():

    connection = get_connection()

    cursor = connection.cursor()

    # USERS
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'SECURITY_ANALYST',
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            last_login TEXT
        )
        """
    )

    # ACCESS LOGS
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS access_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            action TEXT NOT NULL,
            status TEXT NOT NULL,
            ip_address TEXT,
            user_agent TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # BLOCKED SOURCES
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS blocked_sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT UNIQUE NOT NULL,
            reason TEXT,
            risk_score INTEGER DEFAULT 0,
            blocked_at TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'BLOCKED',
            blocked_by TEXT
        )
        """
    )

    # WHITELIST
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS whitelist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT UNIQUE NOT NULL,
            duration TEXT DEFAULT 'temporary',
            added_at TEXT NOT NULL,
            added_by TEXT,
            status TEXT NOT NULL DEFAULT 'WHITELISTED'
        )
        """
    )

    # ALERTS
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT,
            attack_type TEXT,
            severity TEXT,
            risk_score INTEGER,
            description TEXT,
            status TEXT DEFAULT 'ACTIVE',
            created_at TEXT NOT NULL
        )
        """
    )

    # OVERRIDE ACTIONS
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS override_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            source TEXT NOT NULL,
            action TEXT NOT NULL,
            reason TEXT,
            ip_address TEXT,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )

    connection.commit()
    connection.close()


if __name__ == "__main__":
    initialize_database()
    print("DATABASE READY")