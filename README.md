# PyTodo Pro: Software Testing and Quality Assurance Project

**Course:** TEB3433/TFB3433 Software Testing and Quality Assurance, Semester September 2026
**Lecturer:** Dr Abdullateef
**Group:** 7, Universiti Teknologi PETRONAS (UTP), Department of Computing
**Repository:** https://github.com/izzamerbaharuddin/STQA (branch `main`)

This repository holds our independent quality evaluation of **PyTodo Pro**, a Flask task-management web app. We did not change the application. We tested it with black-box, white-box, GUI, API, security, performance and automated regression testing, then summarised the results with metrics and a final quality verdict.

## Team

| No | Name | Student ID |
|---|---|---|
| 1 | Syahir Amri bin Mohd Azha | 22007728 |
| 2 | Adam Marwan bin Husin Albasri | 22009203 |
| 3 | Izzamer bin Baharuddin | 22005742 |
| 4 | Wan Eismael Zafry bin Wan Rizaidy | 22000614 |
| 5 | Xu Weikang | 24004647 |

## Repository structure

| Folder | Contents |
|---|---|
| `pytodo_pro/` | The application under test (`app.py`, `helpers.py`, templates). **Not modified.** |
| `01_Black_Box/` | Week 1 report (EP, BVA, decision table, state transition) and `evidence/` screenshots |
| `02_White_Box_Coverage/` | Week 2 report, `test_helpers.py`, `baseline_check.py` and `evidence/` coverage screenshots |
| `03_Special_Testing/` | Week 3 report: GUI, compatibility, usability and accessibility |
| `04_Web_API/` | Week 4 report: web and API testing |
| `05_Security_Performance/` | Week 5 report, `security_tests.py`, `locustfile.py` and `Evidence/` |
| `06_Automation_Regression/` | Week 6 report, `test_regression_api.py`, `test_ui_regression.py` and saved console output |
| `07_Test_Management/` | Week 7 workbook: RTM, test cases, defect log, regression status |
| `08_Final_QA_Report/` | Week 8 final QA report (PDF) and metrics workbook |
| `09_Presentation/` | Final presentation slides and the Week 9 standards integration report |

## Tools

| Tool | Used for |
|---|---|
| Python 3.12 or newer (tested on 3.13 and 3.15) | Running the app and all test scripts |
| Flask 3.0.3 | The application (installed from `pytodo_pro/requirements.txt`) |
| pytest, coverage | Unit and regression tests, coverage measurement |
| requests | Security checks (`security_tests.py`) |
| Locust | Performance test (`locustfile.py`) |
| Selenium and Microsoft Edge | UI regression test (`test_ui_regression.py`) |
| Git and GitHub Desktop | Version control |

## Setup

**Get the code.** Clone the repository from https://github.com/izzamerbaharuddin/STQA, or download it as a ZIP with **Code, Download ZIP** on that page:

```
git clone https://github.com/izzamerbaharuddin/STQA.git
cd STQA
```

Then run the following from the repository root.

**Windows (PowerShell)**
```
python -m venv venv
venv\Scripts\activate
pip install -r pytodo_pro/requirements.txt
pip install pytest coverage requests locust selenium
```

**macOS or Linux**
```
python3 -m venv venv
source venv/bin/activate
pip install -r pytodo_pro/requirements.txt
pip install pytest coverage requests locust selenium
```

If PowerShell says that running scripts is disabled, run `Set-ExecutionPolicy -Scope Process Bypass` and activate again. This setting only lasts for that terminal window.

## Run the application

```
cd pytodo_pro
python app.py
```

Open http://127.0.0.1:5000. There is no pre-made login, so click **Register** to create an account. The database file `pytodo_pro.db` is created on first run and is ignored by Git. To start fresh, stop the app and delete that file.

Keep this terminal open while you use the app or run the tests that need it.

## Run the automated tests

| Suite | Needs the app running? | Command | Expected result |
|---|---|---|---|
| White-box unit tests (Week 2) | No | `cd 02_White_Box_Coverage` then `python -m pytest -v` | 31 passed, 3 xfailed |
| API regression (Week 6) | No | See the note below | 20 passed, 4 xfailed |
| UI regression with Selenium (Week 6) | **Yes** | `cd 06_Automation_Regression` then `python -m pytest test_ui_regression.py -v` | 2 passed (result recorded in the Week 6 report) |
| Security checks (Week 5) | **Yes** | `cd 05_Security_Performance` then `python security_tests.py` | 2 PASS (secure), 4 FAIL (vulnerable, confirmed) |
| Performance test (Week 5) | **Yes** | `cd 05_Security_Performance` then `python -m locust -f locustfile.py --host http://127.0.0.1:5000` | See the Locust steps below |

**API regression command.** The test file looks for the application folder next to itself, so tell Python where the app is. From the repository root:

- Windows (PowerShell): `$env:PYTHONPATH="pytodo_pro"; python -m pytest 06_Automation_Regression/test_regression_api.py -v`
- macOS or Linux: `PYTHONPATH=pytodo_pro python -m pytest 06_Automation_Regression/test_regression_api.py -v`

The other option is to copy `test_regression_api.py` to the repository root and run `python -m pytest test_regression_api.py -v`.

**What "xfailed" means.** A test marked as an expected failure (xfail, strict) records a defect that is known and not fixed, because we did not change the application. If a developer fixes the defect, the test shows as an unexpected pass and fails the run. That is the signal to remove the marker.

**What "FAIL" means in `security_tests.py`.** A FAIL means the vulnerability is present in the app. A PASS means that check found the app secure.

**Coverage of `helpers.py`.** From `02_White_Box_Coverage`:

```
python -m coverage run --branch -m pytest -q
python -m coverage report -m --omit="test_*"
python -m coverage html --omit="test_*"
```

Expected: 100% statement and 100% branch coverage on `helpers.py`. Open `htmlcov/index.html` for the line-by-line view. `baseline_check.py` is a one-test-per-function run that reaches about 63%, used as the "before" measurement:

```
python -m coverage run --branch -m pytest -q baseline_check.py
python -m coverage report -m --omit="baseline_check.py"
```

**Locust steps.** After starting Locust, open http://localhost:8089, set **Users** to 20 and **Spawn rate** to 2, and run for about 6 minutes (the Week 5 report used this workload). The locust file only targets the local instance.

## Safety notes

- Run the security and performance scripts only against **your own local copy** of PyTodo Pro. Do not point them at any other system.
- The security checks only detect weaknesses. They do not extract data.
- The tests create accounts and tasks in the local database. Delete `pytodo_pro.db` to reset it.

## Results summary

The Week 7 workbook (`07_Test_Management/`) holds the master test cases (103), the consolidated defect log, the RTM and the regression status. The Week 8 report and metrics workbook (`08_Final_QA_Report/`) hold the metrics, the residual risks and the overall verdict. The final verdict is that PyTodo Pro is **not ready for production release**. Testing cannot prove the application is defect-free.

## Troubleshooting

| Problem | Fix |
|---|---|
| `python` is not recognized | Reinstall Python and tick "Add python.exe to PATH", then reopen the terminal |
| `No module named 'app'` when running the API regression test | Set `PYTHONPATH` to `pytodo_pro` as shown above |
| `No module named ...` for another package | Activate the virtual environment and run the `pip install` line from Setup |
| Port 5000 is already in use | Close the other copy of the app, then run it again |
| Selenium test cannot start the browser | Install Microsoft Edge, update Selenium (`pip install -U selenium`), and keep the app running |
| `pip install` fails on a brand-new Python version | Use Python 3.12 or 3.13 |
| Test results differ from the table | Delete `pytodo_pro.db`, restart the app and run again |
