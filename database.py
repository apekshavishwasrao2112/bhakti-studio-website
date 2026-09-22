import os
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

load_dotenv()


def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            port=int(os.getenv("DB_PORT", 3306))
        )

        if conn.is_connected():
            return conn

        return None

    except Error as e:
        print(f"[ERROR] MySQL connection failed: {e}")
        return None


def get_param_style(conn):
    return "%s"


def init():
    conn = get_db_connection()

    if conn is None:
        print("[ERROR] Database initialization failed.")
        return False

    cursor = None

    try:
        cursor = conn.cursor()

        # Bookings table
        cursor.execute("""
           CREATE TABLE IF NOT EXISTS bookings (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255),
                phone VARCHAR(20),
                service VARCHAR(255),
                booking_date DATE,
                language VARCHAR(10) DEFAULT 'en',
                booking_time VARCHAR(50),
                status VARCHAR(50) DEFAULT 'Pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Admin table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255),
                password VARCHAR(255)
            )
        """)

        # Chat history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_message TEXT,
                bot_reply TEXT
            )
        """)

        # Demos
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

        # Add category if old demos table doesn't have it
        cursor.execute("SHOW COLUMNS FROM demos LIKE 'category'")

        if cursor.fetchone() is None:
            cursor.execute("""
                ALTER TABLE demos
                ADD COLUMN category VARCHAR(50)
                NOT NULL DEFAULT 'general'
                AFTER language
            """)

        # Create admin account if credentials exist
        admin_username = os.getenv("ADMIN_USERNAME")
        admin_password = os.getenv("ADMIN_PASSWORD")

        if admin_username and admin_password:

            cursor.execute(
                "SELECT id FROM admin WHERE username=%s",
                (admin_username,)
            )

            if cursor.fetchone() is None:

                hashed_password = generate_password_hash(admin_password)

                cursor.execute(
                    """
                    INSERT INTO admin (username, password)
                    VALUES (%s, %s)
                    """,
                    (admin_username, hashed_password)
                )

        conn.commit()

        print("[SUCCESS] MySQL Database Initialized")

        return True

    except Error as e:

        conn.rollback()

        print(f"[ERROR] Database initialization failed: {e}")

        return False

    finally:

        if cursor:
            cursor.close()

        conn.close()