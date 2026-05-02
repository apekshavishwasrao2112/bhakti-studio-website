#!/usr/bin/env python3

try:
    from flask import Flask
    print("Flask import successful")
except ImportError as e:
    print(f"Flask import failed: {e}")
    exit(1)

try:
    from database import get_db_connection
    print("Database import successful")
except ImportError as e:
    print(f"Database import failed: {e}")
    exit(1)

try:
    app = Flask(__name__)
    print("Flask app created successfully")
except Exception as e:
    print(f"Flask app creation failed: {e}")
    exit(1)

try:
    with app.app_context():
        from flask import render_template
        print("Template rendering test successful")
except Exception as e:
    print(f"Template rendering test failed: {e}")
    exit(1)

print("All basic tests passed!")