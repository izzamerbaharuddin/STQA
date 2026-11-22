PS C:\Users\Wan Eismael\Downloads\STQA-main\STQA-main> python -m pytest test_regression_api.py -v
=================================================================== test session starts ===================================================================
platform win32 -- Python 3.15.0, pytest-9.1.1, pluggy-1.6.0 -- C:\Users\Wan Eismael\AppData\Local\Python\pythoncore-3.15-64\python.exe
cachedir: .pytest_cache
metadata: {'Python': '3.15.0', 'Platform': 'Windows-11-10.0.26200-SP0', 'Packages': {'pytest': '9.1.1', 'pluggy': '1.6.0'}, 'Plugins': {'locust': '2.47.0', 'html': '4.2.0', 'metadata': '3.1.1'}}
rootdir: C:\Users\Wan Eismael\Downloads\STQA-main\STQA-main
plugins: locust-2.47.0, html-4.2.0, metadata-3.1.1
collected 24 items

test_regression_api.py::test_register_username_boundaries[ab-False] PASSED                                                                           [  4%]
test_regression_api.py::test_register_username_boundaries[abc-True] PASSED                                                                           [  8%]
test_regression_api.py::test_register_username_boundaries[aaaaaaaaaaaaaaaaaaaa-True] PASSED                                                          [ 12%]
test_regression_api.py::test_register_username_boundaries[aaaaaaaaaaaaaaaaaaaaa-False] PASSED                                                        [ 16%]
test_regression_api.py::test_register_username_boundaries[user name-False] PASSED                                                                    [ 20%]
test_regression_api.py::test_register_username_boundaries[user@123-False] PASSED                                                                     [ 25%]
test_regression_api.py::test_register_password_boundaries[7-False] PASSED                                                                            [ 29%]
test_regression_api.py::test_register_password_boundaries[8-True] XFAIL (DEF-003/DEF-006: helpers.is_valid_password() uses `len(password) > 8` (...) [ 33%]
test_regression_api.py::test_register_password_boundaries[9-True] PASSED                                                                             [ 37%]
test_regression_api.py::test_duplicate_username_accepted PASSED                                                                                      [ 41%]
test_regression_api.py::test_login_decision_table PASSED                                                                                             [ 45%]
test_regression_api.py::test_blank_and_whitespace_title_rejected_by_api PASSED                                                                       [ 50%]
test_regression_api.py::test_urgency_boundaries[-1-Overdue] PASSED                                                                                   [ 54%]
test_regression_api.py::test_urgency_boundaries[0-Due Today] XFAIL (DEF-001: helpers.compute_urgency() uses `if due <= today: return 'Overdue'`,...) [ 58%]
test_regression_api.py::test_urgency_boundaries[1-Due Soon] PASSED                                                                                   [ 62%]
test_regression_api.py::test_urgency_boundaries[2-Due Soon] PASSED                                                                                   [ 66%]
test_regression_api.py::test_urgency_boundaries[3-Upcoming] PASSED                                                                                   [ 70%]
test_regression_api.py::test_no_due_date_label PASSED                                                                                                [ 75%]
test_regression_api.py::test_dashboard_open_soon_and_completed_counts PASSED                                                                         [ 79%]
test_regression_api.py::test_dashboard_overdue_count_excludes_due_today XFAIL (DEF-001: because compute_urgency() treats 'due today' as Overdue ...) [ 83%]
test_regression_api.py::test_task_lifecycle_done_reopen_delete PASSED                                                                                [ 87%]
test_regression_api.py::test_filter_and_pagination PASSED                                                                                            [ 91%]
test_regression_api.py::test_idor_delete_cross_account XFAIL (DEF-005: DELETE /api/tasks/<id> in app.py deletes by task id only and does not fil...) [ 95%]
test_regression_api.py::test_sql_injection_probe_on_search PASSED                                                                                    [100%]

============================================================== 20 passed, 4 xfailed in 3.23s ==============================================================