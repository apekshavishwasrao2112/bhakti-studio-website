import os
import sqlite3
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

load_dotenv()

def is_postgres_url(database_url: str) -> bool:
    if not database_url:
        return False
    return database_url.startswith(('postgresql://', 'postgres://'))


def get_db_connection():
    database_url = os.getenv('DATABASE_URL')

    if database_url:
        if is_postgres_url(database_url):
            try:
                import psycopg2
                return psycopg2.connect(database_url)
            except ImportError:
                print("psycopg2 not installed. Install with: pip install psycopg2-binary")
                return None
            except Exception as err:
                print(f"PostgreSQL connection failed: {err}")
                return None
        else:
            print("DATABASE_URL is set but is not a supported PostgreSQL URL.")
            return None

    try:
        return sqlite3.connect('bhakti_studio.db')
    except Exception as err:
        print(f"SQLite connection failed: {err}")
        return None


def is_postgres_connection(conn) -> bool:
    return conn is not None and hasattr(conn, 'closed') and 'psycopg2' in str(type(conn))


def get_param_style(conn):
    return '%s' if is_postgres_connection(conn) else '?'


def init():
    try:
        conn = get_db_connection()
        if conn is None:
            print("Database not available. Skipping initialization.")
            return

        cursor = conn.cursor()

        # Check if using PostgreSQL or SQLite
        is_postgres = hasattr(conn, 'closed') and 'psycopg2' in str(type(conn))

        if is_postgres:
            # PostgreSQL tables
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
            id SERIAL PRIMARY KEY,
            user_message TEXT,
            bot_reply TEXT
            )
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL
            )
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS bookings(
                id SERIAL PRIMARY KEY,
                name VARCHAR(100),
                phone VARCHAR(20),
                service VARCHAR(50),
                booking_date DATE,
                status VARCHAR(20) DEFAULT 'Pending' CHECK (status IN ('Pending', 'Confirmed', 'Completed', 'Rejected')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
        else:
            # SQLite tables
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_message TEXT,
            bot_reply TEXT
            )
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS bookings(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                phone TEXT,
                service TEXT,
                booking_date TEXT,
                status TEXT DEFAULT 'Pending',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """)

        # Check if admin exists, if not create with hashed password
        cursor.execute("SELECT COUNT(*) FROM admin")
        result = cursor.fetchone()
        if result[0] == 0:
           # 🔐 Read secure credentials from .env
            admin_username = os.getenv("ADMIN_USERNAME")
            admin_password = os.getenv("ADMIN_PASSWORD")

            if not admin_username or not admin_password:
                raise Exception("❌ ADMIN_USERNAME or ADMIN_PASSWORD not set in .env")

            hashed_password = generate_password_hash(admin_password)

            cursor.execute(
                "INSERT INTO admin (username, password) VALUES (?, ?)" if not is_postgres else
                "INSERT INTO admin (username, password) VALUES (%s, %s)",
                (admin_username, hashed_password)
            )
        conn.commit()
        cursor.close()
        conn.close()
        print("Database initialized successfully.")
    except Exception as err:
        print(f"Database initialization failed: {err}")
        print("Application will continue without database functionality.")