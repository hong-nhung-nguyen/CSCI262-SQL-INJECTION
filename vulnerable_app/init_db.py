"""
init_db.py — builds a fresh app.db for the VULNERABLE demo app.

Run once before starting app.py:   python init_db.py

Two tables so the UNION attack has something juicy to steal:
  users    -> the login table (what the login form checks against)
  secrets  -> a second table the search box should NEVER expose
"""
import sqlite3
import os

DB = os.path.join(os.path.dirname(__file__), "app.db")

# Start clean every time so the demo is repeatable.
if os.path.exists(DB):
    os.remove(DB)

con = sqlite3.connect(DB)
cur = con.cursor()

cur.executescript(
    """
    CREATE TABLE users (
        id       INTEGER PRIMARY KEY,
        username TEXT NOT NULL,
        password TEXT NOT NULL,   -- plaintext ON PURPOSE to make the leak obvious
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
        secret_hash TEXT NOT NULL   -- the "sensitive" column UNION will pull out
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
print("Login with admin / S3cr3tAdminPass!  (or just bypass it with SQLi)")
