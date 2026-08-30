import sqlite3

DB_NAME = "payments.db"

def create_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT,
        plan TEXT,
        status TEXT
    )
    """)

    conn.commit()
    conn.close()


def add_payment(user_id, username, plan, status="pending"):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO payments (user_id, username, plan, status) VALUES (?, ?, ?, ?)",
        (user_id, username, plan, status)
    )

    conn.commit()
    conn.close()