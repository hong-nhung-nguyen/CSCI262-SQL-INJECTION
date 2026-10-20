"""
vulnerable_app/app.py  —  DELIBERATELY INSECURE Flask app for the CSCI262 SQLi demo.

RUN ONLY on localhost inside your VM. Never expose this to a real network.

Every SQL statement here is built with raw Python string concatenation, which is
exactly the flaw the assignment demonstrates. The secure_app fixes the same two
endpoints with parameterized queries; the diff between them is the "one-line fix"
the slide deck shows.

Start:
    python init_db.py      # once, to build app.db
    python app.py          # serves on http://127.0.0.1:5000
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
# LOGIN  — vulnerable to authentication bypass  ( ' OR '1'='1' --  )
# ---------------------------------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        # *** THE VULNERABILITY ***  user input spliced straight into the SQL.
        query = (
            "SELECT * FROM users "
            "WHERE username = '" + username + "' "
            "AND password = '" + password + "'"
        )

        con = get_db()
        try:
            row = con.execute(query).fetchone()   # verbose errors reach the user
        except Exception as e:
            # Error-based disclosure: we hand the raw DB error back to the page.
            con.close()
            return render_template("login.html", error=f"SQL error: {e}", query=query)
        con.close()

        if row:
            session["user"] = row["username"]
            return redirect(url_for("search"))
        error = "Invalid credentials"

        # We also echo the built query so the audience can SEE the injection.
        return render_template("login.html", error=error, query=query)

    return render_template("login.html", error=error, query=None)


# ---------------------------------------------------------------------------
# SEARCH — vulnerable to UNION / error-based / blind injection via ?q=
# ---------------------------------------------------------------------------
@app.route("/search")
def search():
    if "user" not in session:
        return redirect(url_for("login"))

    q = request.args.get("q", "")
    results, error, query = [], None, None

    if q:
        # *** THE VULNERABILITY ***  again, raw concatenation.
        query = "SELECT name, price FROM products WHERE name LIKE '%" + q + "%'"
        con = get_db()
        try:
            results = [tuple(r) for r in con.execute(query).fetchall()]
        except Exception as e:
            error = f"SQL error: {e}"   # error-based disclosure
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
    # debug=True gives full stack traces — helpful for the error-based demo.
    app.run(host="127.0.0.1", port=5000, debug=True)
