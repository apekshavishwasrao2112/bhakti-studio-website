import os
import logging
import threading
import time
from urllib.parse import unquote, urlsplit

import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
_schema_ready = False
_schema_lock = threading.Lock()


def _get_database_config():
    """Read Railway-linked MySQL settings, with DB_* compatibility fallbacks."""
    mysql_url = os.getenv("MYSQL_URL")
    url_config = {}
    if mysql_url:
        parsed_url = urlsplit(mysql_url)
        url_config = {
            "host": parsed_url.hostname,
            "port": parsed_url.port,
            "user": unquote(parsed_url.username) if parsed_url.username else None,
            "password": unquote(parsed_url.password) if parsed_url.password else None,
            "database": parsed_url.path.lstrip("/") or None,
        }

    host = os.getenv("MYSQLHOST") or url_config.get("host") or os.getenv("DB_HOST")
    user = os.getenv("MYSQLUSER") or url_config.get("user") or os.getenv("DB_USER")
    password = os.getenv("MYSQLPASSWORD") or url_config.get("password") or os.getenv("DB_PASSWORD")
    database = os.getenv("MYSQLDATABASE") or url_config.get("database") or os.getenv("DB_NAME")
    port_value = os.getenv("MYSQLPORT") or url_config.get("port") or os.getenv("DB_PORT") or "3306"

    try:
        port = int(port_value)
    except (TypeError, ValueError):
        raise ValueError("DB_PORT/MYSQLPORT must be a valid integer")

    missing = [
        name for name, value in (
            ("MYSQLHOST/DB_HOST", host),
            ("MYSQLUSER/DB_USER", user),
            ("MYSQLPASSWORD/DB_PASSWORD", password),
            ("MYSQLDATABASE/DB_NAME", database),
        )
        if not value
    ]
    if missing:
        raise ValueError("Missing database configuration: " + ", ".join(missing))

    return {
        "host": host,
        "user": user,
        "password": password,
        "database": database,
        "port": port,
        "connection_timeout": 10,
    }


def get_param_style(conn):
    return "%s"


def _retry_settings():
    try:
        attempts = max(1, int(os.getenv("DB_CONNECT_ATTEMPTS", "5")))
        delay = max(0, float(os.getenv("DB_CONNECT_DELAY_SECONDS", "3")))
    except ValueError:
        attempts, delay = 5, 3
    return attempts, delay


def _connect_with_retries():
    try:
        config = _get_database_config()
    except (TypeError, ValueError) as error:
        logger.error("MySQL configuration is invalid: %s", error)
        return None

    attempts, delay = _retry_settings()
    for attempt in range(1, attempts + 1):
        try:
            return mysql.connector.connect(**config)
        except (Error, TypeError, ValueError) as error:
            error_code = getattr(error, "errno", "configuration")
            logger.error(
                "MySQL connection failed (attempt %d/%d, code=%s, type=%s).",
                attempt,
                attempts,
                error_code,
                type(error).__name__,
            )
            if attempt < attempts:
                time.sleep(delay)
    return None


def _initialize_schema(conn):
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255),
                phone VARCHAR(20),
                service VARCHAR(255),
                booking_date DATE,
                language VARCHAR(10) DEFAULT 'en',
                status VARCHAR(50) DEFAULT 'Pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255),
                password VARCHAR(255)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_message TEXT,
                bot_reply TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS demos (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                language VARCHAR(20) NOT NULL,
                category VARCHAR(50) NOT NULL DEFAULT 'general',
                video_url TEXT NOT NULL,
                is_new BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("SHOW COLUMNS FROM demos LIKE 'category'")
        if cursor.fetchone() is None:
            cursor.execute("""
                ALTER TABLE demos
                ADD COLUMN category VARCHAR(50) NOT NULL DEFAULT 'general'
                AFTER language
            """)

        admin_username = os.getenv("ADMIN_USERNAME")
        admin_password = os.getenv("ADMIN_PASSWORD")
        if admin_username and admin_password:
            cursor.execute(
                "SELECT id FROM admin WHERE username=%s",
                (admin_username,),
            )
            if cursor.fetchone() is None:
                cursor.execute(
                    "INSERT INTO admin (username, password) VALUES (%s, %s)",
                    (admin_username, generate_password_hash(admin_password)),
                )
        conn.commit()
        return True
    except (Error, TypeError, ValueError) as error:
        try:
            conn.rollback()
        except Exception:
            pass
        logger.error(
            "MySQL schema initialization failed (code=%s, type=%s).",
            getattr(error, "errno", "unknown"),
            type(error).__name__,
        )
        return False
    finally:
        if cursor is not None:
            try:
                cursor.close()
            except Exception:
                pass


def get_db_connection():
    global _schema_ready

    conn = _connect_with_retries()
    if conn is None:
        return None

    if not _schema_ready:
        with _schema_lock:
            if not _schema_ready and not _initialize_schema(conn):
                try:
                    conn.close()
                except Exception:
                    pass
                return None
            _schema_ready = True
    return conn


def init():
    conn = get_db_connection()
    if conn is None:
        logger.error("Database initialization is unavailable; the application will remain online and retry on the next database request.")
        return False
    conn.close()
    logger.info("MySQL database connection and schema are ready.")
    return True