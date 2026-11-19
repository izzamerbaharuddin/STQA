"""
Week 2 white-box tests for PyTodo Pro helpers.py (TEB3433 Group 7).

Expected results come from the SPEC written in each function's docstring,
not from what the code currently does. Tests marked xfail(strict=True)
document a known defect: they fail today because the code disagrees with
the spec. If the code is ever fixed, strict mode turns them into errors,
which tells us to remove the marker.

Run from this folder:
    python -m pytest -v
"""

import os
import sys
from datetime import date, datetime, timedelta

import pytest

# helpers.py lives in the sibling pytodo_pro folder
HELPERS_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "pytodo_pro"))
sys.path.insert(0, HELPERS_DIR)

from helpers import (  # noqa: E402
    completed_in_last_n_days,
    compute_urgency,
    is_valid_password,
    is_valid_username,
)

TODAY = date(2026, 11, 19)
NOW = datetime(2026, 11, 19, 12, 0, 0)


def due(offset_days):
    """Due-date string for TODAY + offset_days."""
    return (TODAY + timedelta(days=offset_days)).strftime("%Y-%m-%d")


def done(**delta):
    """completed_at string for NOW minus a timedelta."""
    return (NOW - timedelta(**delta)).strftime("%Y-%m-%d %H:%M:%S")


# ---------------------------------------------------------------------------
# compute_urgency  (decisions: today is None, no date, due <= today, delta <= 2)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("value", [None, ""])
def test_TC_WB_001_no_due_date(value):
    assert compute_urgency(value, today=TODAY) == "No due date"


def test_TC_WB_002_overdue_yesterday():
    assert compute_urgency(due(-1), today=TODAY) == "Overdue"


@pytest.mark.xfail(strict=True, reason="DEF-005: due today returns 'Overdue'; spec says 'Due Today'")
def test_TC_WB_003_due_today():
    assert compute_urgency(due(0), today=TODAY) == "Due Today"


@pytest.mark.parametrize("offset", [1, 2])
def test_TC_WB_004_due_soon(offset):
    assert compute_urgency(due(offset), today=TODAY) == "Due Soon"


def test_TC_WB_005_upcoming_three_days():
    assert compute_urgency(due(3), today=TODAY) == "Upcoming"


def test_TC_WB_006_default_today_is_used():
    # today omitted -> date.today(); a far-future date is always Upcoming
    assert compute_urgency("2999-12-31") == "Upcoming"


def test_TC_WB_007_bad_date_format_raises():
    # Spec is silent on malformed input; this records current behaviour.
    with pytest.raises(ValueError):
        compute_urgency("19/11/2026", today=TODAY)


# ---------------------------------------------------------------------------
# is_valid_password  (decisions: isinstance str, length)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("value", [None, 12345678])
def test_TC_WB_008_password_not_a_string(value):
    assert is_valid_password(value) is False


def test_TC_WB_009_password_seven_chars_rejected():
    assert is_valid_password("a" * 7) is False


@pytest.mark.xfail(strict=True, reason="DEF-006: 8-character password rejected; spec says at least 8")
def test_TC_WB_010_password_eight_chars_accepted():
    assert is_valid_password("a" * 8) is True


@pytest.mark.parametrize("length", [9, 20])
def test_TC_WB_011_password_longer_accepted(length):
    assert is_valid_password("a" * length) is True


# ---------------------------------------------------------------------------
# is_valid_username  (decisions: isinstance str, length 3-20, character check)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("value", [None, 123])
def test_TC_WB_012_username_not_a_string(value):
    assert is_valid_username(value) is False


@pytest.mark.parametrize("name,expected", [
    ("", False), ("ab", False), ("abc", True),
    ("a" * 20, True), ("a" * 21, False),
])
def test_TC_WB_013_username_length_boundaries(name, expected):
    assert is_valid_username(name) is expected


@pytest.mark.parametrize("name,expected", [
    ("user_1", True), ("user name", False), ("user@123", False),
])
def test_TC_WB_014_username_characters(name, expected):
    assert is_valid_username(name) is expected


# ---------------------------------------------------------------------------
# completed_in_last_n_days  (decisions: no value, now is None, age > 0, age.days < n)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("value", [None, ""])
def test_TC_WB_015_not_completed(value):
    assert completed_in_last_n_days(value, now=NOW) is False


def test_TC_WB_016_completed_yesterday():
    assert completed_in_last_n_days(done(days=1), now=NOW) is True


def test_TC_WB_017_just_inside_seven_days():
    assert completed_in_last_n_days(done(days=6, hours=23), now=NOW) is True


@pytest.mark.xfail(strict=True, reason="DEF-007: exactly 7 days ago excluded; spec says inclusive of exactly N days")
def test_TC_WB_018_exactly_seven_days_included():
    assert completed_in_last_n_days(done(days=7), now=NOW) is True


def test_TC_WB_019_eight_days_excluded():
    assert completed_in_last_n_days(done(days=8), now=NOW) is False


def test_TC_WB_020_completed_in_the_future_excluded():
    future = (NOW + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
    assert completed_in_last_n_days(future, now=NOW) is False


def test_TC_WB_021_default_now_is_used():
    an_hour_ago = (datetime.now() - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
    assert completed_in_last_n_days(an_hour_ago) is True


def test_TC_WB_022_custom_window():
    assert completed_in_last_n_days(done(days=2), n=1, now=NOW) is False
