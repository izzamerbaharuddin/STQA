PS C:\Users\Wan Eismael\Downloads\STQA-main\STQA-main> python -m pytest test_ui_regression.py -v
=================================================================== test session starts ===================================================================
platform win32 -- Python 3.15.0, pytest-9.1.1, pluggy-1.6.0 -- C:\Users\Wan Eismael\AppData\Local\Python\pythoncore-3.15-64\python.exe
cachedir: .pytest_cache
metadata: {'Python': '3.15.0', 'Platform': 'Windows-11-10.0.26200-SP0', 'Packages': {'pytest': '9.1.1', 'pluggy': '1.6.0'}, 'Plugins': {'locust': '2.47.0', 'html': '4.2.0', 'metadata': '3.1.1'}}
rootdir: C:\Users\Wan Eismael\Downloads\STQA-main\STQA-main
plugins: locust-2.47.0, html-4.2.0, metadata-3.1.1
collected 2 items

test_ui_regression.py::test_register_then_login_journey PASSED                                                                                       [ 50%]
test_ui_regression.py::test_create_task_journey PASSED                                                                                               [100%]

==================================================================== 2 passed in 9.24s ====================================================================