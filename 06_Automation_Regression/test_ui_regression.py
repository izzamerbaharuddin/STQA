"""
PyTodo Pro - Week 6 UI regression skeleton (Selenium).

Automates the two UI journeys judged most repetition-stable in the
Week 6 automation-candidate table: login, and creating a task.

IMPORTANT - verify before relying on this script:
Element locators below are GUESSED from the field names used server-side
in app.py (request.form.get("username"), "password", "title",
"description", "category_id", "due_date"). They assume the Jinja
templates use matching name="..." attributes on the real <input>/
<select> elements, which were NOT supplied with the source handed to
this report. Open the actual templates (or inspect the rendered page
in your browser's dev tools) and adjust the locators below if they
differ before trusting this as a real regression gate. This is flagged
explicitly in the Week 6 report, Section 4 and Section 7.

Requires the app running locally first:
    python app.py

Run:
    pip install selenium
    python -m pytest test_ui_regression.py -v

Uses Microsoft Edge (already installed on Windows). Selenium 4.6+
auto-downloads a matching msedgedriver the first time this runs, so no
manual driver install is needed.
"""

import uuid

import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "http://127.0.0.1:5000"


@pytest.fixture
def driver():
    # Microsoft Edge - already installed on Windows, and Selenium 4.6+
    # auto-downloads a matching msedgedriver, so no separate driver
    # install is needed.
    options = webdriver.EdgeOptions()
    # Comment out the next line if you want to watch the browser run live.
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,900")
    drv = webdriver.Edge(options=options)
    drv.implicitly_wait(2)
    yield drv
    drv.quit()


def test_register_then_login_journey(driver):
    """Covers the registration + login journey behind TC-BB-001..013."""
    username = f"ui_{uuid.uuid4().hex[:10]}"
    password = "Test12345"

    driver.get(f"{BASE_URL}/register")
    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.NAME, "username")))
    driver.find_element(By.NAME, "username").send_keys(username)
    driver.find_element(By.NAME, "password").send_keys(password)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']").click()

    # Registration logs the user straight in (per app.py), so we should
    # land on the task list.
    WebDriverWait(driver, 5).until(EC.url_contains(BASE_URL))
    assert "login" not in driver.current_url.lower()

    driver.get(f"{BASE_URL}/logout")
    driver.get(f"{BASE_URL}/login")
    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.NAME, "username")))
    driver.find_element(By.NAME, "username").send_keys(username)
    driver.find_element(By.NAME, "password").send_keys(password)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']").click()

    WebDriverWait(driver, 5).until(lambda d: "login" not in d.current_url.lower())


def test_create_task_journey(driver):
    """Covers the create-task journey behind TC-BB-014..017 / TC-WEB-003/004."""
    username = f"ui_{uuid.uuid4().hex[:10]}"
    password = "Test12345"

    driver.get(f"{BASE_URL}/register")
    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.NAME, "username")))
    driver.find_element(By.NAME, "username").send_keys(username)
    driver.find_element(By.NAME, "password").send_keys(password)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']").click()

    driver.get(f"{BASE_URL}/tasks/new")
    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.NAME, "title")))
    title_text = f"Selenium task {uuid.uuid4().hex[:6]}"
    driver.find_element(By.NAME, "title").send_keys(title_text)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']").click()

    # Wait for the actual title to appear, rather than just "a body tag
    # exists" (which is true on the New Task page too, before the redirect
    # to the task list has actually happened - that race caused this test
    # to read a stale page and fail even on a correct submission).
    try:
        WebDriverWait(driver, 5).until(lambda d: title_text in d.page_source)
    except Exception:
        pytest.fail(
            f"Created task title {title_text!r} did not appear on the task "
            f"list within 5s after submit. Current URL: {driver.current_url}"
        )
