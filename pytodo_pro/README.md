# PyTodo Pro

A complete, ready-to-test Flask task manager — the target application
for the course testing project. **You do not need to write or modify
any application code.** Your job is to test it.

## Setup

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

The app creates `pytodo_pro.db` on first run and serves at
`http://127.0.0.1:5000/`. Register a new account from the web UI (or
via `POST /api/register`) to get started — there is no pre-seeded
login.

## What's here

### Web UI
- `/register`, `/login`, `/logout` — account management
- `/` — task list, with filters for category, status (open/done), and a title search box
- `/tasks/new`, `/tasks/<id>/edit` — create and edit tasks
- `/dashboard` — summary counters (total, open, overdue, due soon, completed in the last 7 days)

### JSON REST API (all under `/api`, session-cookie authenticated except register/login)
- `POST /api/register` — `{"username": ..., "password": ...}`
- `POST /api/login` — `{"username": ..., "password": ...}`
- `GET /api/categories`
- `GET /api/tasks?category=&status=&q=&page=&per_page=`
- `POST /api/tasks` — `{"title": ..., "description": ..., "category_id": ..., "due_date": "YYYY-MM-DD"}`
- `GET /api/tasks/<id>`
- `PUT /api/tasks/<id>` — partial updates accepted
- `DELETE /api/tasks/<id>`
- `GET /api/dashboard`

### Data model
- **users**: id, username, password_hash
- **categories**: id, name (seeded with Work, Personal, Study, Urgent)
- **tasks**: id, user_id, title, description, category_id, due_date, done, completed_at, created_at

### Task urgency
Each task is classified as one of: `No due date`, `Overdue`, `Due Today`,
`Due Soon` (due within 2 days), `Upcoming`, or `Done`. The exact rules
are implemented in `helpers.py` — a good place to start if you're
designing white-box test cases.

## A note on quality

This app was built to be tested, not audited by its author. Treat it
the way you would treat a real, working piece of software handed to a
QA team: it does what it's supposed to do in the common cases — your
job across the testing phases is to find out where that stops being
true.


## Note for Week 5 and 6 (for other testers)
## Week 5 — Security and Performance (`/05_Security_Performance/`)

Files: `security_tests.py`, `locustfile.py`, plus the Week 5 report
(exported to Word/PDF) and evidence screenshots/logs.

```bash
cd pytodo_pro
pip install -r requirements.txt
python app.py                        # terminal 1, leave running

# terminal 2 — automated security checks
pip install requests itsdangerous
python security_tests.py

# terminal 2 — performance test
pip install locust
python -m locust -f locustfile.py --host http://127.0.0.1:5000
# open http://localhost:8089, set Users=20, Spawn rate=2, run ~3 minutes
```

Console output and the Locust results screenshot are archived in
`/05_Security_Performance/evidence/`.

## Week 6 — Automation and Regression (`/06_Automation_Regression/`)

Files: `test_regression_api.py`, `test_ui_regression.py`, plus the Week 6
report and execution evidence.

```bash
# API regression suite — no server needs to be running, it uses Flask's
# test client directly. Run from the folder containing pytodo_pro/.
pip install pytest
python -m pytest test_regression_api.py -v
# Result: 20 passed, 4 xfailed, 0 failed
# (the 4 xfailed are confirmed, unfixed defects: DEF-001, DEF-003/DEF-006, DEF-005)

# UI regression — requires the app running separately (python app.py).
# Uses Microsoft Edge; Selenium auto-downloads a matching msedgedriver.
pip install selenium
python -m pytest test_ui_regression.py -v
# Result: 2 passed
```

Console output for both suites is archived in
`/06_Automation_Regression/evidence/`. Re-run both suites in Week 7 and
Week 8 as the regression gate before finalising metrics.
