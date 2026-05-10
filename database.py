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
            port=int(os.getenv("DB_PORT")),
            connection_timeout=10
        )

        return conn

    except Error as e:
        print(f"[ERROR] MySQL connection failed: {e}")
        return None


def init():

    conn = get_db_connection()

    if conn is None:
        return jsonify({"success": False, "message": "Database error"})

    cursor = conn.cursor()

    # BOOKINGS TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bookings (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255),
        phone VARCHAR(20),
        service VARCHAR(255),
        booking_date DATE,
        status VARCHAR(50) DEFAULT 'Pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # ADMIN TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS admin (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(255),
        password VARCHAR(255)
    )
    """)

    # CHAT TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chat_history (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_message TEXT,
        bot_reply TEXT
    )
    """)

    # CREATE ADMIN USER
    admin_username = os.getenv("ADMIN_USERNAME")
    admin_password = os.getenv("ADMIN_PASSWORD")

    cursor.execute(
        "SELECT * FROM admin WHERE username=%s",
        (admin_username,)
    )

    existing_admin = cursor.fetchone()

    if not existing_admin:

        hashed_password = generate_password_hash(admin_password)

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