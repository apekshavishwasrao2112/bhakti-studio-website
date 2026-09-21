import os
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

load_dotenv()


def get_param_style(conn):
    return "%s"


def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            port=int(os.getenv("DB_PORT", 3306)),
            connection_timeout=10
        )

        return conn

    except Error as e:
        print(f"[ERROR] MySQL connection failed: {e}")
        return None


def init():

    conn = get_db_connection()

    if conn is None:
        print("[ERROR] Database initialization failed.")
        return False

    try:

        cursor = conn.cursor()

        # ================= BOOKINGS TABLE =================

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

        # ================= ADMIN TABLE =================

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255),
                password VARCHAR(255)
            )
        """)

        # ================= CHAT HISTORY TABLE =================

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_message TEXT,
                bot_reply TEXT
            )
        """)

        # ================= DEMOS TABLE =================

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

        # ================= ENSURE CATEGORY COLUMN EXISTS =================

        cursor.execute("SHOW COLUMNS FROM demos LIKE 'category'")

        if cursor.fetchone() is None:

            cursor.execute("""
                ALTER TABLE demos
                ADD COLUMN category VARCHAR(50) NOT NULL DEFAULT 'general'
                AFTER language
            """)

        # ================= CREATE ADMIN USER =================

        admin_username = os.getenv("ADMIN_USERNAME")
        admin_password = os.getenv("ADMIN_PASSWORD")

        if admin_username and admin_password:

            cursor.execute(
                "SELECT id FROM admin WHERE username=%s",
                (admin_username,)
            )

            existing_admin = cursor.fetchone()

            if not existing_admin:

                hashed_password = generate_password_hash(
                    admin_password
                )

                cursor.execute(
                    """
                    INSERT INTO admin (username, password)
                    VALUES (%s, %s)
                    """,
                    (admin_username, hashed_password)
                )

        conn.commit()

        cursor.close()
        conn.close()

        print("[SUCCESS] MySQL Database Initialized")

        return True

    except Error as e:

        print(f"[ERROR] Database initialization error: {e}")

        try:
            conn.rollback()
        except Exception:
            pass

        try:
            cursor.close()
        except Exception:
            pass

        try:
            conn.close()
        except Exception:
            pass

        return False