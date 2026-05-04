import os
import psycopg2
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    database_url = os.getenv('DATABASE_URL')

    if not database_url:
        print("[ERROR] DATABASE_URL is not set in environment variables.")
        return None

    # Railway's PostgreSQL URL might start with postgres://, which some libraries
    # struggle with, though psycopg2 is usually fine. We replace it just in case.
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    print("========== DATABASE DEBUG ==========")
    print("Connecting to PostgreSQL...")

    try:
        # Use sslmode='prefer' which handles both internal (no SSL) and external (SSL) connections well
        conn = psycopg2.connect(
            database_url,
            sslmode='prefer'
        )
        print("[SUCCESS] PostgreSQL connected successfully")
        return conn

    except Exception as err:
        print(f"[ERROR] PostgreSQL connection failed: {err}")
        return None

def get_param_style(conn=None):
    # We are strictly using PostgreSQL now
    return '%s'

def init():
    print("========== INIT DATABASE ==========")
    conn = get_db_connection()

    if conn is None:
        print("[ERROR] Database not available. Skipping initialization.")
        return

    try:
        cursor = conn.cursor()

        # =========================
        # PostgreSQL Tables
        # =========================
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
        CREATE TABLE IF NOT EXISTS bookings (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100),
            phone VARCHAR(20),
            service VARCHAR(50),
            booking_date DATE,
            status VARCHAR(20) DEFAULT 'Pending'
                CHECK (status IN ('Pending', 'Confirmed', 'Completed', 'Rejected')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # =========================
        # Create Admin If Not Exists
        # =========================
        cursor.execute("SELECT COUNT(*) FROM admin;")
        result = cursor.fetchone()

        if result[0] == 0:
            admin_username = os.getenv("ADMIN_USERNAME")
            admin_password = os.getenv("ADMIN_PASSWORD")

            if not admin_username or not admin_password:
                print("[ERROR] ADMIN_USERNAME or ADMIN_PASSWORD not set in environment variables")
            else:
                hashed_password = generate_password_hash(admin_password)
                cursor.execute(
                    """
                    INSERT INTO admin (username, password)
                    VALUES (%s, %s)
                    """,
                    (admin_username, hashed_password)
                )
                print("[SUCCESS] Admin account created successfully")

        conn.commit()
        cursor.close()
        conn.close()

        print("[SUCCESS] Database initialized successfully.")

    except Exception as err:
        print(f"[ERROR] Database initialization failed: {err}")
        if conn:
            conn.rollback()
            conn.close()