"""
secure_app/app.py  —  the PATCHED version of the CSCI262 SQLi demo app.
Author: Harrel (secure_app / implementation section)

This file is a line-for-line mirror of vulnerable_app/app.py. The ONLY security
difference is how the two SQL statements are built:

    vulnerable_app:  query = "... '" + user_input + "' ..."   (concatenation)
    secure_app:      query = "... = ?";  execute(query, (user_input,))

Parameterized queries send the SQL text and the data to the driver separately,
so whatever the attacker types is treated as a literal value and can never
change the structure of the query. That is the primary defence the report
recommends. Re-run every payload from vulnerable_app/README.md here: each one
now matches no rows instead of altering the query.

Runs on port 5001 so it can sit side by side with the vulnerable app (5000).

Start:
    python init_db.py      # once, to build app.db
    python app.py          # serves on http://127.0.0.1:5001
"""
from flask import Flask, request, render_template, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "demo-not-secret"  # fine for a local demo
DB = os.path.join(os.path.dirname(__file__), "app.db")


def get_db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


@app.route("/")
def home():
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# LOGIN  — SECURE: parameterized query, so ' OR '1'='1' -- is just a username.
# ---------------------------------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        # *** THE FIX *** placeholders, not concatenation.
        query = "SELECT * FROM users WHERE username = ? AND password = ?"

        con = get_db()
        try:
            row = con.execute(query, (username, password)).fetchone()
        except Exception as e:
            con.close()
            return render_template("login.html", error=f"SQL error: {e}", query=query)
        con.close()

        if row:
            session["user"] = row["username"]
            return redirect(url_for("search"))
        error = "Invalid credentials"
        return render_template("login.html", error=error, query=query)

    return render_template("login.html", error=error, query=None)


# ---------------------------------------------------------------------------
# SEARCH — SECURE: the search term is bound as a parameter, so UNION / blind /
# error payloads are matched literally and return nothing.
# ---------------------------------------------------------------------------
@app.route("/search")
def search():
    if "user" not in session:
        return redirect(url_for("login"))

    q = request.args.get("q", "")
    results, error, query = [], None, None

    if q:
        # *** THE FIX *** one placeholder; the % wildcards live in the bound value.
        query = "SELECT name, price FROM products WHERE name LIKE ?"
        con = get_db()
        try:
            results = [tuple(r) for r in con.execute(query, ("%" + q + "%",)).fetchall()]
        except Exception as e:
            error = f"SQL error: {e}"
        con.close()

    return render_template(
        "search.html", user=session["user"], results=results, error=error,
        q=q, query=query,
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=True)
