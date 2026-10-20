# CSCI262 Assignment 3 — SQL Injection Demo

A single small web app shipped in **two versions** so the same attacks can be run
against both and the fix can be proven:

| Folder | Port | SQL built by | Purpose |
|--------|------|--------------|---------|
| `vulnerable_app/` | 5000 | string concatenation | gets broken by every attack |
| `secure_app/`     | 5001 | parameterized queries (the fix) | the same attacks fail |

Both apps have the **same** login form, search box, database schema and
credentials. The only difference is how each builds its SQL — that is the whole
point of the before/after demo.

> ⚠️ **Run on localhost inside your VM only.** `vulnerable_app` is intentionally
> insecure and must never be exposed to a real network.

---

## 1. Requirements

- **Python 3.8+** (tested on 3.13). Check: `python --version`
- **pip** (ships with Python)
- The only third-party dependency is **Flask** (in each app's `requirements.txt`)
- SQLite needs no install — it is built into Python
- Optional, for the automated attack: **sqlmap** (preinstalled on Kali Linux)

On Kali/Ubuntu the command is usually `python3` / `pip3`; on Windows it is
`python` / `pip`. Use whichever your system has.

---

## 2. Install dependencies

Installing in one app installs the same Flask for both, but doing each is fine:

```bash
# from the Assignment3 folder
cd vulnerable_app
pip install -r requirements.txt
cd ../secure_app
pip install -r requirements.txt
cd ..
```

(Optional but recommended — a virtual environment keeps this off your system
Python:)

```bash
python -m venv venv
# Windows:        venv\Scripts\activate
# Linux / macOS:  source venv/bin/activate
pip install -r vulnerable_app/requirements.txt
```

---

## 3. Build the databases (first time, and to reset)

Each app builds its own `app.db` from an init script. Re-run these any time you
want to reset the demo to a clean state.

```bash
cd vulnerable_app && python init_db.py && cd ..
cd secure_app     && python init_db.py && cd ..
```

Both create identical data:

- **users** — `admin / S3cr3tAdminPass!`, `nhung / hunter2`, `harrel / letmein`
- **products** — Laptop, Keyboard, Monitor, Webcam (the search target)
- **secrets** — `api_key`, `db_root_hash` (a second table for the UNION attack)

---

## 4. Run the apps

Each app runs in the foreground and holds its terminal, so use **two terminals** —
one per app. Different ports mean they run side by side without clashing.

**Terminal 1 — vulnerable app**
```bash
cd vulnerable_app
python app.py          # http://127.0.0.1:5000
```

**Terminal 2 — secure app**
```bash
cd secure_app
python app.py          # http://127.0.0.1:5001
```

Open both in the VM browser and log in as `admin / S3cr3tAdminPass!`:

- Vulnerable → http://127.0.0.1:5000
- Secure → http://127.0.0.1:5001

Stop an app with **Ctrl+C**. If you see "address already in use", a copy is still
running on that port — stop it first (or reboot the VM).

---

## 5. How to test it

The idea: run the **same payload** against both apps and screenshot the contrast.
Each page prints the SQL it executed, which makes the screenshots self-explaining.
Start by logging in normally and searching `Laptop` so you have a "normal
behaviour" baseline shot.

### Attack payloads

| # | Attack | Where | Payload |
|---|--------|-------|---------|
| 1 | Auth bypass | Login → username (password = anything) | `' OR '1'='1' --` |
| 2 | UNION — credentials | Search box | `x' UNION SELECT username, password FROM users --` |
| 3 | UNION — secrets table | Search box | `x' UNION SELECT label, secret_hash FROM secrets --` |
| 4 | Error-based disclosure | Search box | `'` |
| 5 | Boolean-blind | Search box | `Laptop' AND '1'='1' -- ` (rows) vs `Laptop' AND '1'='2' -- ` (none) |

### Expected results

| Attack | Vulnerable (:5000) | Secure (:5001) |
|--------|--------------------|----------------|
| Auth bypass | logs in as admin, no password | "Invalid credentials" |
| UNION | dumps usernames + passwords | no rows |
| Error-based | prints raw `SQL error: ...` | no error, no rows |
| Boolean-blind | row returned for the true case | no rows either way |

Each app's own `README.md` has the full playbook, the curl equivalents, and an
explanation of why the secure version is immune.

### Boolean-blind note
The search wraps your input as `LIKE '%<input>%'`, so blind payloads must end with
`-- ` to comment out the trailing `%'`. Extract a character like this:
```
Laptop' AND substr((SELECT password FROM users WHERE username='admin'),1,1)='S' -- 
```
returns the Laptop row only when the guessed letter is correct (it is `S`).

### Automated attack (sqlmap, on Kali)
`/search` needs a login session, so pass the cookie from your browser:
```bash
sqlmap -u "http://127.0.0.1:5000/search?q=Laptop" \
       --cookie="session=PASTE_FROM_BROWSER" --batch --dbs
sqlmap -u "http://127.0.0.1:5000/search?q=Laptop" \
       --cookie="session=..." --batch -D app -T users --dump
```
Point the same command at `:5001` and sqlmap reports the parameter is **not
injectable** — that contrast is the automated-attack slide.

---

## 6. The fix (one-line diff — your key slide)

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

Parameterized queries send the SQL text and the data to the driver on separate
channels, so whatever the attacker types is treated as a literal value and can
never change the structure of the query. That is the primary defence recommended
in the report.

---

## 7. Folder layout

```
Assignment3/
├── README.md              # this file
├── vulnerable_app/
│   ├── app.py             # login + search, SQL by string concatenation
│   ├── init_db.py         # builds app.db
│   ├── requirements.txt
│   ├── README.md          # attack playbook
│   └── templates/         # login.html, search.html
└── secure_app/
    ├── app.py             # same app, parameterized queries (port 5001)
    ├── init_db.py         # identical schema
    ├── requirements.txt
    ├── README.md          # fix + before/after proof
    └── templates/
```

---

## 8. Troubleshooting

- **`ModuleNotFoundError: flask`** — dependencies not installed, or the venv is
  not activated. Re-run the install step.
- **`no such table: users`** — you skipped `python init_db.py` in that folder.
- **"address already in use"** — an app is already running on that port; stop it
  with Ctrl+C.
- **`python` not found on Kali** — use `python3` and `pip3`.
- **Attacks "don't work" on the vulnerable app** — confirm you are on `:5000`
  (vulnerable), not `:5001` (secure), and that blind payloads end with `-- `.
