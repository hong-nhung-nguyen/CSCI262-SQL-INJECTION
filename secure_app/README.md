# secure_app — CSCI262 A3 SQL Injection demo (PATCHED)
Author: Harrel (secure_app + implementation section)

This is the fixed counterpart to `../vulnerable_app`. Same login form, same
search box, same database schema and credentials. The **only** change is that
both SQL statements use **parameterized queries** instead of string
concatenation — the primary defence the report recommends.

## Setup
```bash
pip install -r requirements.txt
python init_db.py      # builds app.db (identical schema to vulnerable_app)
python app.py          # http://127.0.0.1:5001   (vulnerable app is on :5000)
```
Login: `admin` / `S3cr3tAdminPass!`

## The one-line diff (this is your slide)
```
LOGIN
  vulnerable:  query = "... WHERE username = '" + username + "' AND password = '" + password + "'"
               con.execute(query)
  secure:      query = "SELECT * FROM users WHERE username = ? AND password = ?"
               con.execute(query, (username, password))

SEARCH
  vulnerable:  query = "SELECT name, price FROM products WHERE name LIKE '%" + q + "%'"
               con.execute(query)
  secure:      query = "SELECT name, price FROM products WHERE name LIKE ?"
               con.execute(query, ("%" + q + "%",))
```

## Proof: the same payloads now fail
Run every payload from `../vulnerable_app/README.md` against port **5001**:

| Attack | Payload | Vulnerable (:5000) | Secure (:5001) |
|--------|---------|--------------------|----------------|
| Auth bypass | `' OR '1'='1' --` | logs in as admin | "Invalid credentials" |
| UNION | `x' UNION SELECT username, password FROM users --` | dumps creds | no rows |
| Error-based | `'` | leaks SQL error | no error, no rows |
| Boolean-blind | `Laptop' AND '1'='1' -- ` | row returned | no rows |

Why: parameterization sends the query text and the data to the driver on
separate channels, so the payload is compared as a literal string
(`username = "' OR '1'='1' --"`) and matches nothing. The query structure the
attacker tried to inject never becomes part of the executed statement.

## Note for the report
Parameterized queries remove the *injection* vector. The `Welcome, {username}`
message reflects a value that came from the database, not raw user input, so it
is not an injection sink; escaping it would be XSS hygiene, outside this fix's
scope.
