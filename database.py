import os
import sqlite3
import psycopg2
from psycopg2 import OperationalError
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

load_dotenv()

def is_postgres():
    url = os.getenv('DATABASE_URL')
    return url and 'postgres' in url

def get_db_connection():
    database_url = os.getenv('DATABASE_URL')
    

    if database_url:
        
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)

        try:
            conn = psycopg2.connect(database_url, sslmode='require')  
            print("[SUCCESS] Connected to PostgreSQL")
            return conn
        except Exception as err:
            print(f"[ERROR] PostgreSQL connection failed: {err}")
            return None
        
    else:
        # Use SQLite for Local Development
        try:
            conn = sqlite3.connect('local.db', check_same_thread=False)
            print("[SUCCESS] Connected to SQLite")
            return conn
        except Exception as err:
            print(f"[ERROR] SQLite connection failed: {err}")
            return None

def get_param_style(conn):
    if conn.__class__.__module__.startswith('psycopg2'):
        return '%s'
    return '?'

def init():
    print("========== INIT DATABASE ==========")
    conn = get_db_connection()

    if conn is None:
        print("[ERROR] Database not available. Skipping initialization.")
        return

    try:
        cursor = conn.cursor()

        # Dynamic Primary Key Syntax
        if is_postgres():
            id_column = "id SERIAL PRIMARY KEY"
        else:
            id_column = "id INTEGER PRIMARY KEY AUTOINCREMENT"

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

    except Exception as err:
        print(f"[ERROR] Database initialization failed: {err}")
        if conn:
            conn.rollback()
            conn.close()