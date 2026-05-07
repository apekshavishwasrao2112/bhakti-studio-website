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
            port=int(os.getenv("DB_PORT", 3306)),
            connection_timeout=10
        )
        if conn.is_connected():
            return conn
    except Error as e:
        print(f"[ERROR] MySQL connection failed: {e}")
        return None

def get_param_style(conn):
    return '%s'

def init():
    print("========== INIT DATABASE ==========")
    conn = get_db_connection()

    if conn is None:
        print("[ERROR] Database not available. Skipping initialization.")
        return

    try:
        cursor = conn.cursor(buffered=True)

        # MySQL Primary Key Syntax
        id_column = "id INT AUTO_INCREMENT PRIMARY KEY"

        # =========================
        # Table Creation
        # =========================
        cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS chat_history (
            {id_column},
            user_message TEXT,
            bot_reply TEXT
        )
        """)

        cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS admin (
            {id_column},
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL
        )
        """)

        cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS bookings (
            {id_column},
            name VARCHAR(100),
            phone VARCHAR(20),
            service VARCHAR(50),
            booking_date DATE,
            status VARCHAR(20) DEFAULT 'Pending',
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
                placeholder = get_param_style(conn)
                cursor.execute(
                    f"""
                    INSERT INTO admin (username, password)
                    VALUES ({placeholder}, {placeholder})
                    """,
                    (admin_username, hashed_password)
                )
                print("[SUCCESS] Admin account created successfully")

        conn.commit()
        cursor.close()
        conn.close()

        print("[SUCCESS] Database initialized successfully.")

    except Error as err:
        print(f"[ERROR] Database initialization failed: {err}")
        if conn and conn.is_connected():
            conn.rollback()
            conn.close()