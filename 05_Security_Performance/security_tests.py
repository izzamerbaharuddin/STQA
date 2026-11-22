"""
PyTodo Pro - Week 5 automated security regression checks.

Scope and safety notes
-----------------------
- Every request in this file targets the group's OWN local instance of
  PyTodo Pro (default http://127.0.0.1:5000). Do not point BASE_URL at
  any system you do not own or have written permission to test.
- These are DETECTION tests, not an exploit toolkit. The SQL-injection
  check (test_sql_injection_probe_on_search) stops at confirming the
  filter is bypassable with a classic boolean probe; it never attempts
  to extract data from other tables (e.g. no UNION SELECT against the
  users table). See the Week 5 report, Section 8, for the residual risk
  this leaves undemonstrated.
- The session-forgery check uses the literal SECRET_KEY value that is
  already visible in the group's own copy of app.py (and in the public
  course repository) - it is not "cracking" a secret, it is confirming
  that a secret committed to source control behaves as if it weren't
  secret at all.

Run with the app started locally first:
    python app.py                 # in one terminal
    python security_tests.py      # in another

Requires: requests, itsdangerous (itsdangerous ships as a Flask
dependency, so it is already installed if PyTodo Pro's requirements
are installed).
"""

import itertools
import time
import uuid

import requests

try:
    from itsdangerous import URLSafeTimedSerializer, TimestampSigner
except ImportError:
    URLSafeTimedSerializer = None

BASE_URL = "http://127.0.0.1:5000"
# Must match app.config["SECRET_KEY"] in app.py exactly.
SECRET_KEY = "pytodo-pro-dev-secret"

results = []


def record(case_id, description, passed, detail=""):
    status = "PASS (secure)" if passed else "FAIL (vulnerable / confirmed)"
    results.append((case_id, description, status, detail))
    print(f"[{case_id}] {description}: {status}")
    if detail:
        print(f"    {detail}")


def fresh_username(prefix="sec"):
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


def register_and_login(session, username=None, password="Test12345"):
    username = username or fresh_username()
    resp = session.post(
        f"{BASE_URL}/api/register",
        json={"username": username, "password": password},
    )
    return username, password, resp


# ---------------------------------------------------------------------------
# TC-SEC-001 - Cross-account task deletion (IDOR)
# ---------------------------------------------------------------------------

def test_idor_delete_cross_account():
    session_a = requests.Session()
    session_b = requests.Session()

    user_a, _, reg_a = register_and_login(session_a)
    user_b, _, reg_b = register_and_login(session_b)

    if reg_a.status_code != 201 or reg_b.status_code != 201:
        record("TC-SEC-001", "Cross-account task deletion (IDOR)", False,
               "Could not register test accounts; see raw responses: "
               f"A={reg_a.status_code} {reg_a.text}, B={reg_b.status_code} {reg_b.text}")
        return

    create = session_a.post(
        f"{BASE_URL}/api/tasks",
        json={"title": "IDOR probe task - do not delete manually"},
    )
    if create.status_code != 201:
        record("TC-SEC-001", "Cross-account task deletion (IDOR)", False,
               f"Could not create a task as account A: {create.status_code} {create.text}")
        return
    task_id = create.json()["id"]

    delete_as_b = session_b.delete(f"{BASE_URL}/api/tasks/{task_id}")
    still_there = session_a.get(f"{BASE_URL}/api/tasks/{task_id}")

    vulnerable = delete_as_b.status_code == 200 and still_there.status_code == 404
    record(
        "TC-SEC-001",
        "Cross-account task deletion (IDOR) on DELETE /api/tasks/<id>",
        passed=not vulnerable,
        detail=(f"DELETE as B -> {delete_as_b.status_code} {delete_as_b.text} | "
                f"GET as A afterwards -> {still_there.status_code} "
                f"(404 here means B's delete succeeded against A's task)"),
    )


# ---------------------------------------------------------------------------
# TC-SEC-002 - comparison case: GET/PUT should already be scoped correctly
# ---------------------------------------------------------------------------

def test_cross_account_read_and_update_are_blocked():
    session_a = requests.Session()
    session_b = requests.Session()
    register_and_login(session_a)
    register_and_login(session_b)

    create = session_a.post(f"{BASE_URL}/api/tasks", json={"title": "Comparison task"})
    task_id = create.json()["id"]

    get_as_b = session_b.get(f"{BASE_URL}/api/tasks/{task_id}")
    put_as_b = session_b.put(f"{BASE_URL}/api/tasks/{task_id}", json={"title": "tampered"})

    ok = get_as_b.status_code == 404 and put_as_b.status_code == 404
    record(
        "TC-SEC-002",
        "Cross-account GET/PUT (control case; expected to already be safe)",
        passed=ok,
        detail=f"GET as B -> {get_as_b.status_code}, PUT as B -> {put_as_b.status_code}",
    )


# ---------------------------------------------------------------------------
# TC-SEC-003 - SQL injection detection on the title search parameter
# ---------------------------------------------------------------------------

def test_sql_injection_probe_on_search():
    session = requests.Session()
    register_and_login(session)
    session.post(f"{BASE_URL}/api/tasks", json={"title": "Totally unrelated title"})

    # Probe 1: a bare single quote should break the f-string query if the
    # value is not sanitised or parameterised.
    broken = session.get(f"{BASE_URL}/api/tasks", params={"q": "'"})

    # Probe 2: classic boolean-based OR condition. A safe implementation
    # treats this as a literal (no-match) search string. A vulnerable one
    # may return all of the user's tasks regardless of title.
    baseline = session.get(f"{BASE_URL}/api/tasks", params={"q": "zzz_no_such_title_zzz"})
    boolean_probe = session.get(
        f"{BASE_URL}/api/tasks", params={"q": "zzz' OR '1'='1"}
    )

    baseline_count = len(baseline.json()) if baseline.status_code == 200 else None
    probe_count = len(boolean_probe.json()) if boolean_probe.status_code == 200 else None

    server_error_on_quote = broken.status_code >= 500
    boolean_bypass = (
        baseline_count is not None
        and probe_count is not None
        and probe_count > baseline_count
    )

    vulnerable = server_error_on_quote or boolean_bypass
    record(
        "TC-SEC-003",
        "SQL injection detection on GET /api/tasks?q=",
        passed=not vulnerable,
        detail=(f"single-quote probe -> {broken.status_code}; "
                f"baseline unmatched-term count={baseline_count}, "
                f"boolean-OR probe count={probe_count} "
                "(probe_count > baseline means the filter was bypassed)"),
    )


# ---------------------------------------------------------------------------
# TC-SEC-004 - session cookie forgery using the known hardcoded secret
# ---------------------------------------------------------------------------

def _forge_flask_session_cookie(user_id, username, secret_key):
    """
    Flask's default session is a signed, itsdangerous-serialised cookie.
    This recreates one from scratch using the SAME secret the app already
    uses, to show the secret itself is the only thing protecting sessions.
    """
    from itsdangerous import URLSafeTimedSerializer, TimestampSigner
    from flask.sessions import TaggedJSONSerializer
    import hashlib

    signer_kwargs = {
        "key_derivation": "hmac",
        "digest_method": hashlib.sha1,
    }
    serializer = URLSafeTimedSerializer(
        secret_key,
        salt="cookie-session",
        serializer=TaggedJSONSerializer(),
        signer_kwargs=signer_kwargs,
    )
    return serializer.dumps({"user_id": user_id, "username": username})


def test_session_forgery_with_known_secret():
    if URLSafeTimedSerializer is None:
        record("TC-SEC-004", "Session cookie forgery", False,
                "itsdangerous is not installed; run `pip install itsdangerous`.")
        return

    # First, legitimately find out a real user_id to target by registering
    # one account normally (we do NOT need its password afterward).
    session = requests.Session()
    username, _, reg = register_and_login(session)
    if reg.status_code != 201:
        record("TC-SEC-004", "Session cookie forgery", False, "Could not register probe account.")
        return
    real_user_id = reg.json()["id"]

    forged_cookie = _forge_flask_session_cookie(real_user_id, username, SECRET_KEY)

    forged_session = requests.Session()
    forged_session.cookies.set("session", forged_cookie)
    resp = forged_session.get(f"{BASE_URL}/api/dashboard")

    vulnerable = resp.status_code == 200
    record(
        "TC-SEC-004",
        "Session cookie forged with the hardcoded SECRET_KEY grants access",
        passed=not vulnerable,
        detail=f"GET /api/dashboard with a self-signed cookie (no login/password used) -> {resp.status_code} {resp.text}",
    )


# ---------------------------------------------------------------------------
# TC-SEC-005 - debug mode / stack trace exposure
# ---------------------------------------------------------------------------

def test_debug_mode_exposes_traceback():
    session = requests.Session()
    register_and_login(session)

    # Malformed JSON body with a JSON content-type: get_json(silent=True)
    # is used everywhere so this alone likely won't crash the app - this
    # test mainly documents the static finding and checks a couple of
    # requests that are more likely to surface an unhandled exception.
    resp = session.post(
        f"{BASE_URL}/api/tasks",
        data="{not valid json",
        headers={"Content-Type": "application/json"},
    )
    werkzeug_debugger_markers = ("Werkzeug Debugger", "Traceback (most recent call last)")
    looks_like_debug_page = any(marker in resp.text for marker in werkzeug_debugger_markers)

    record(
        "TC-SEC-005",
        "Debug mode / Werkzeug traceback exposure (app.run(debug=True) in source)",
        passed=not looks_like_debug_page,
        detail=(f"Malformed-JSON POST -> {resp.status_code}. "
                f"{'A Werkzeug traceback page was returned.' if looks_like_debug_page else 'No traceback page observed for this specific request; the debug=True setting in source is still a configuration finding regardless of this one probe.'}"),
    )


# ---------------------------------------------------------------------------
# TC-SEC-006 - login brute force / rate limiting
# ---------------------------------------------------------------------------

def test_login_rate_limiting():
    session = requests.Session()
    username, password, reg = register_and_login(session)
    if reg.status_code != 201:
        record("TC-SEC-006", "Login rate limiting", False, "Could not register probe account.")
        return

    attempts = []
    start = time.time()
    for i in range(10):
        resp = session.post(
            f"{BASE_URL}/api/login",
            json={"username": username, "password": f"wrong-{i}"},
        )
        attempts.append(resp.status_code)
    elapsed = time.time() - start

    all_rejected_no_throttle = all(code == 401 for code in attempts) and elapsed < 5
    record(
        "TC-SEC-006",
        "Login brute-force / rate limiting on /api/login",
        passed=not all_rejected_no_throttle,
        detail=f"10 attempts in {elapsed:.2f}s, status codes: {attempts}",
    )


if __name__ == "__main__":
    print(f"Running Week 5 security regression checks against {BASE_URL}\n")
    test_idor_delete_cross_account()
    test_cross_account_read_and_update_are_blocked()
    test_sql_injection_probe_on_search()
    test_session_forgery_with_known_secret()
    test_debug_mode_exposes_traceback()
    test_login_rate_limiting()

    print("\nSummary")
    print("-------")
    for case_id, description, status, _ in results:
        print(f"{case_id}: {status} - {description}")
