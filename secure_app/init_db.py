"""
init_db.py — builds app.db for the SECURE demo app.

Schema is IDENTICAL to vulnerable_app/init_db.py on purpose: same tables, same
rows, same credentials. That is what lets the exact same attack payloads be
replayed against this app so the audience sees them fail against nothing but the
query-building change.

Run once before starting app.py:   python init_db.py
"""
import sqlite3
import os

DB = os.path.join(os.path.dirname(__file__), "app.db")

if os.path.exists(DB):
    os.remove(DB)

con = sqlite3.connect(DB)
cur = con.cursor()

cur.executescript(
    """
    CREATE TABLE users (
        id       INTEGER PRIMARY KEY,
        username TEXT NOT NULL,
        password TEXT NOT NULL,
        role     TEXT NOT NULL
    );

    CREATE TABLE products (
        id    INTEGER PRIMARY KEY,
        name  TEXT NOT NULL,
        price TEXT NOT NULL
    );

    CREATE TABLE secrets (
        id          INTEGER PRIMARY KEY,
        label       TEXT NOT NULL,
        secret_hash TEXT NOT NULL
    );
    """
)

cur.executemany(
    "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
    [
        ("admin",  "S3cr3tAdminPass!", "admin"),
        ("nhung",  "hunter2",          "user"),
        ("harrel", "letmein",          "user"),
    ],
)

cur.executemany(
    "INSERT INTO products (name, price) VALUES (?, ?)",
    [
        ("Laptop",   "1200"),
        ("Keyboard", "45"),
        ("Monitor",  "300"),
        ("Webcam",   "80"),
    ],
)

cur.executemany(
    "INSERT INTO secrets (label, secret_hash) VALUES (?, ?)",
    [
        ("api_key",      "AKIA-DEMO-9f3c2b1a"),
        ("db_root_hash", "5f4dcc3b5aa765d61d8327deb882cf99"),
    ],
)

con.commit()
con.close()
print(f"Built {DB}")
print("Login: admin / S3cr3tAdminPass!  (SQLi bypass no longer works here)")
