"""
PyTodo Pro - Week 6 automated regression suite.

Uses Flask's built-in test_client() against the app object directly,
so this suite does NOT need `python app.py` running separately and is
CI-friendly (see Week 6 report, Section 4 and Section 6).

Each test registers its own uniquely-named account so tests do not
interfere with each other and the suite can be re-run freely without
resetting pytodo_pro.db, matching the approach already used manually
in the Week 4 report.

Run (from the repository root, with pytodo_pro/ containing app.py,
helpers.py and the templates folder):

    pip install pytest
    pytest test_regression_api.py -v

If this file lives outside the pytodo_pro/ folder, adjust SRC_PATH
below to point at it.
"""

import sys
import os
import uuid
from datetime import date, timedelta

import pytest

SRC_PATH = os.path.join(os.path.dirname(__file__), "pytodo_pro")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from app import app as flask_app, init_db  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _ensure_db():
    init_db()


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


def unique_username(prefix="reg"):
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


def register(client, username=None, password="Test12345"):
    username = username or unique_username()
    resp = client.post(
        "/api/register", json={"username": username, "password": password}
    )
    return username, password, resp


def get_category_id(client, name):
    resp = client.get("/api/categories")
    for cat in resp.get_json():
        if cat["name"] == name:
            return cat["id"]
    raise AssertionError(f"Category {name!r} not found in /api/categories")


# ---------------------------------------------------------------------------
# Registration: TC-BB-001 to 006 (username EP/BVA)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "username, should_pass",
    [
        ("ab", False),  # below min (2 chars)
        ("abc", True),  # at min (3 chars)
        ("a" * 20, True),  # at max (20 chars)
        ("a" * 21, False),  # above max (21 chars)
        ("user name", False),  # invalid char: space
        ("user@123", False),  # invalid char: @
    ],
)
def test_register_username_boundaries(client, username, should_pass):
    # No uniqueness check exists on username (see test_duplicate_username_accepted
    # / DEF-004), so re-running this with the same username on a later test run
    # is harmless - it will just succeed again rather than collide.
    resp = client.post(
        "/api/register", json={"username": username, "password": "Test12345"}
    )
    if should_pass:
        assert resp.status_code == 201, resp.get_json()
    else:
        assert resp.status_code == 400, resp.get_json()


# ---------------------------------------------------------------------------
# Registration: TC-BB-007 to 009 / TC-API-008 to 010 (password BVA)
# Regression-tests DEF-003 / DEF-006 (8-char boundary).
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "password_length, should_pass",
    [
        (7, False),
        pytest.param(
            8, True,
            marks=pytest.mark.xfail(
                reason=(
                    "DEF-003/DEF-006: helpers.is_valid_password() uses "
                    "`len(password) > 8` (strict greater-than) instead of >=8, "
                    "so the documented 8-character minimum is actually rejected. "
                    "Confirmed by source review of helpers.py. The project brief "
                    "says not to modify app code, so this is expected to persist."
                ),
                strict=True,
            ),
        ),
        (9, True),
    ],
)
def test_register_password_boundaries(client, password_length, should_pass):
    password = "a" * password_length
    username = unique_username("pw")
    resp = client.post(
        "/api/register", json={"username": username, "password": password}
    )
    if should_pass:
        assert resp.status_code == 201, (
            f"Expected password of length {password_length} to be accepted "
            f"(documented minimum is 8); got {resp.status_code} {resp.get_json()}."
        )
    else:
        assert resp.status_code == 400, resp.get_json()


# ---------------------------------------------------------------------------
# TC-BB-010: duplicate username accepted (DEF-004)
# ---------------------------------------------------------------------------

def test_duplicate_username_accepted(client):
    username = unique_username("dup")
    first = client.post(
        "/api/register", json={"username": username, "password": "Test12345"}
    )
    assert first.status_code == 201

    client.get("/logout")  # clear session before the second registration

    second = client.post(
        "/api/register", json={"username": username, "password": "Test99999"}
    )
    # Documents the current (defective) behaviour: this currently succeeds.
    # If the team fixes DEF-004, flip this assertion to expect 400/409 and
    # remove the xfail-style framing.
    assert second.status_code == 201, (
        "If this now fails, DEF-004 (duplicate username accepted) may have "
        "been fixed - update this test and the Week 1 defect log together."
    )


# ---------------------------------------------------------------------------
# Login: TC-BB-011 to 013 / TC-API-002/011/012 (decision table)
# ---------------------------------------------------------------------------

def test_login_decision_table(client):
    username, password, reg = register(client)
    assert reg.status_code == 201
    client.get("/logout")

    valid = client.post("/api/login", json={"username": username, "password": password})
    assert valid.status_code == 200

    client.get("/logout")
    wrong_password = client.post(
        "/api/login", json={"username": username, "password": "WrongPass1"}
    )
    assert wrong_password.status_code == 401

    unknown_user = client.post(
        "/api/login", json={"username": "no_such_user_xyz", "password": "whatever1"}
    )
    assert unknown_user.status_code == 401

    unauthenticated = client.get("/api/tasks")
    assert unauthenticated.status_code == 401


# ---------------------------------------------------------------------------
# TC-API-005/006: blank/whitespace/missing title rejected by the API
# (DEF-002 is a Web-form-only defect; the API side is expected to pass.)
# ---------------------------------------------------------------------------

def test_blank_and_whitespace_title_rejected_by_api(client):
    register(client)

    whitespace = client.post("/api/tasks", json={"title": "   "})
    assert whitespace.status_code == 400
    assert "title" in whitespace.get_json().get("error", "")

    missing = client.post("/api/tasks", json={})
    assert missing.status_code == 400


# ---------------------------------------------------------------------------
# Urgency boundaries: TC-BB-019 to 024 (regression-tests DEF-001)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "offset_days, expected_label",
    [
        (-1, "Overdue"),
        pytest.param(
            0, "Due Today",
            marks=pytest.mark.xfail(
                reason=(
                    "DEF-001: helpers.compute_urgency() uses `if due <= today: "
                    "return 'Overdue'`, so a task due today can never reach the "
                    "'Due Today' branch. Confirmed by source review of "
                    "helpers.py. The project brief says not to modify app code, "
                    "so this is expected to persist."
                ),
                strict=True,
            ),
        ),
        (1, "Due Soon"),
        (2, "Due Soon"),
        (3, "Upcoming"),
    ],
)
def test_urgency_boundaries(client, offset_days, expected_label):
    register(client)
    due = (date.today() + timedelta(days=offset_days)).isoformat()
    create = client.post("/api/tasks", json={"title": "Urgency probe", "due_date": due})
    assert create.status_code == 201
    task = create.get_json()

    assert task["urgency"] == expected_label, (
        f"due_date offset {offset_days:+d} day(s) from today: expected "
        f"'{expected_label}', got '{task['urgency']}'."
    )


def test_no_due_date_label(client):
    register(client)
    create = client.post("/api/tasks", json={"title": "No due date probe"})
    assert create.get_json()["urgency"] == "No due date"


# ---------------------------------------------------------------------------
# TC-BB-032/033: dashboard counters must match the task list
# ---------------------------------------------------------------------------

def _seed_dashboard_tasks(client):
    """Creates Yesterday/Today/Soon tasks plus one completed task, returns the
    task ids in creation order. Shared by the two dashboard tests below."""
    today = date.today()
    tasks = [
        {"title": "Yesterday", "due_date": (today - timedelta(days=1)).isoformat()},
        {"title": "Today", "due_date": today.isoformat()},
        {"title": "Soon", "due_date": (today + timedelta(days=1)).isoformat()},
        {"title": "To complete", "due_date": None},
    ]
    ids = []
    for t in tasks:
        resp = client.post("/api/tasks", json=t)
        ids.append(resp.get_json()["id"])
    complete_resp = client.put(f"/api/tasks/{ids[-1]}", json={"done": True})
    assert complete_resp.status_code == 200
    return ids


def test_dashboard_open_soon_and_completed_counts(client):
    """The counters NOT affected by DEF-001 - kept as strict assertions."""
    register(client)
    _seed_dashboard_tasks(client)

    dash = client.get("/api/dashboard").get_json()
    assert dash["total"] == 4
    assert dash["open"] == 3
    assert dash["completed_this_week"] == 1
    assert dash["due_soon"] == 1


@pytest.mark.xfail(
    reason=(
        "DEF-001: because compute_urgency() treats 'due today' as Overdue "
        "(see test_urgency_boundaries), the dashboard's overdue counter also "
        "counts the 'Today' task, giving 2 instead of the correct 1 (matching "
        "Week 1 TC-BB-033 and Week 4 TC-WEB-006). The project brief says not "
        "to modify app code, so this is expected to persist."
    ),
    strict=True,
)
def test_dashboard_overdue_count_excludes_due_today(client):
    register(client)
    _seed_dashboard_tasks(client)

    dash = client.get("/api/dashboard").get_json()
    # Correct expected behaviour: only "Yesterday" is overdue; "Today" should
    # be excluded (it should be "Due Today", not "Overdue").
    assert dash["overdue"] == 1


# ---------------------------------------------------------------------------
# Task lifecycle: TC-BB-026/027/029, TC-API-015/017/018
# ---------------------------------------------------------------------------

def test_task_lifecycle_done_reopen_delete(client):
    register(client)
    create = client.post("/api/tasks", json={"title": "Lifecycle probe"})
    task_id = create.get_json()["id"]

    mark_done = client.put(f"/api/tasks/{task_id}", json={"done": True})
    assert mark_done.status_code == 200
    assert mark_done.get_json()["done"] is True
    assert mark_done.get_json()["completed_at"] is not None

    reopen = client.put(f"/api/tasks/{task_id}", json={"done": False})
    assert reopen.status_code == 200
    assert reopen.get_json()["done"] is False
    assert reopen.get_json()["completed_at"] is None

    delete = client.delete(f"/api/tasks/{task_id}")
    assert delete.status_code == 200
    assert delete.get_json()["result"] == "ok"

    after_delete = client.get(f"/api/tasks/{task_id}")
    assert after_delete.status_code == 404


# ---------------------------------------------------------------------------
# Filter and pagination: TC-API-014/019
# ---------------------------------------------------------------------------

def test_filter_and_pagination(client):
    register(client)
    study_id = get_category_id(client, "Study")
    unique_title = f"PagedTask_{uuid.uuid4().hex[:8]}"

    create = client.post(
        "/api/tasks",
        json={"title": unique_title, "category_id": study_id},
    )
    assert create.status_code == 201

    page0 = client.get(
        "/api/tasks",
        query_string={
            "category": "Study",
            "status": "open",
            "q": unique_title,
            "page": 0,
            "per_page": 1,
        },
    )
    assert page0.status_code == 200
    results = page0.get_json()
    assert len(results) == 1
    assert results[0]["title"] == unique_title

    page1 = client.get(
        "/api/tasks",
        query_string={
            "category": "Study",
            "status": "open",
            "q": unique_title,
            "page": 1,
            "per_page": 1,
        },
    )
    assert page1.get_json() == []


# ---------------------------------------------------------------------------
# Security regressions ported from Week 5 (TC-SEC-001, 003, 004)
# ---------------------------------------------------------------------------

@pytest.mark.xfail(
    reason=(
        "DEF-005: DELETE /api/tasks/<id> in app.py deletes by task id only "
        "and does not filter by session['user_id'], so any authenticated "
        "user can delete any other user's task. Confirmed by running this "
        "test. The project brief says not to modify app code, so this is "
        "expected to persist."
    ),
    strict=True,
)
def test_idor_delete_cross_account(client):
    """Regresses DEF-005. Uses two separate test clients for two accounts."""
    # Plain test_client() instances (no 'with') - each request pushes and
    # pops its own clean app context, so the two accounts' requests don't
    # interfere with each other's database connection.
    client_a = flask_app.test_client()
    client_b = flask_app.test_client()
    register(client_a)
    register(client_b)

    create = client_a.post("/api/tasks", json={"title": "IDOR regression probe"})
    task_id = create.get_json()["id"]

    delete_as_b = client_b.delete(f"/api/tasks/{task_id}")
    still_there = client_a.get(f"/api/tasks/{task_id}")

    assert delete_as_b.status_code == 404, (
        f"Account B was able to delete account A's task "
        f"(got {delete_as_b.status_code}, then GET as A returned "
        f"{still_there.status_code}). This reproduces DEF-005."
    )


def test_sql_injection_probe_on_search(client):
    """Regresses DEF-007. Detection-only, per the Week 5 scope note."""
    register(client)
    client.post("/api/tasks", json={"title": "Unrelated title for SQLi probe"})

    baseline = client.get("/api/tasks", query_string={"q": "zzz_no_such_title_zzz"})
    boolean_probe = client.get("/api/tasks", query_string={"q": "zzz' OR '1'='1"})

    baseline_count = len(baseline.get_json()) if baseline.status_code == 200 else None
    probe_count = len(boolean_probe.get_json()) if boolean_probe.status_code == 200 else None

    assert not (
        baseline_count is not None
        and probe_count is not None
        and probe_count > baseline_count
    ), (
        f"Boolean-OR search probe returned more rows ({probe_count}) than "
        f"an unmatched search term ({baseline_count}), indicating the title "
        "filter is not safely parameterised. This reproduces DEF-007."
    )
