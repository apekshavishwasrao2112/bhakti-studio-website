#!/usr/bin/env python3

try:
    from flask import Flask
    print("Flask imported successfully")
except ImportError as e:
    print(f"Flask import failed: {e}")

try:
    import mysql.connector
    print("MySQL connector imported successfully")
except ImportError as e:
    print(f"MySQL connector import failed: {e}")

try:
    from database import get_db_connection
    print("Database module imported successfully")
    conn = get_db_connection()
    if conn:
        print("Database connection successful")
        conn.close()
    else:
        print("Database connection returned None (expected if DB not available)")
except Exception as e:
    print(f"Database module import/connection failed: {e}")

print("Test completed")