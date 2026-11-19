import os, sys
sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "pytodo_pro")))
from datetime import date, datetime
from helpers import compute_urgency, is_valid_password, is_valid_username, completed_in_last_n_days

def test_baseline():
    assert compute_urgency("2026-11-25", today=date(2026, 11, 19)) == "Upcoming"
    assert is_valid_password("abcdefghi")
    assert is_valid_username("abc")
    assert completed_in_last_n_days("2026-11-18 10:00:00", now=datetime(2026, 11, 19, 12, 0, 0))
