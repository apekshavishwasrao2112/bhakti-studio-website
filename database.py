def get_db_connection():
    database_url = os.getenv('DATABASE_URL')

    if not database_url:
        print("[ERROR] DATABASE_URL is not set")
        return None

    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    print("========== DATABASE DEBUG ==========")

    try:
        conn = psycopg2.connect(
            database_url,
            sslmode='require',   # ✅ IMPORTANT CHANGE
            connect_timeout=10
        )
        print("[SUCCESS] PostgreSQL connected successfully")
        return conn

    except Exception as err:
        print(f"[ERROR] PostgreSQL connection failed: {err}")
        return None