"""Browser test (Selenium). Needs Chrome installed and the site running:

    1. In one terminal:  python app.py
    2. In another:       set RUN_SELENIUM=1  (Windows)  or  RUN_SELENIUM=1 (Mac/Linux)
                         python -m pytest tests/test_selenium.py -v

Without RUN_SELENIUM=1 the test is skipped, so normal test runs stay fast.
"""
import os

import pytest

pytest.importorskip("selenium")

from selenium import webdriver  # noqa: E402
from selenium.webdriver.common.by import By  # noqa: E402
from selenium.webdriver.support.ui import Select  # noqa: E402

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:5000/")

pytestmark = [
    pytest.mark.selenium,  # custom marker registered in pytest.ini
    pytest.mark.skipif(
        os.environ.get("RUN_SELENIUM") != "1",
        reason="Set RUN_SELENIUM=1 and start app.py to run the browser test",
    ),
]


def test_register_search_and_book_flow_in_browser():
    import time

    driver = webdriver.Chrome()
    try:
        # 1. Create a patient account with a username unique to this run.
        driver.get(BASE_URL + "register/patient")
        username = f"selenium{int(time.time())}"
        driver.find_element(By.NAME, "full_name").send_keys("Selenium Patient")
        driver.find_element(By.NAME, "username").send_keys(username)
        driver.find_element(By.NAME, "password").send_keys("secret123")
        driver.find_element(By.CSS_SELECTOR, "form.book-form button").click()
        assert "Your account is ready" in driver.page_source

        # 2. Search for a doctor.
        search = driver.find_element(By.NAME, "q")
        search.send_keys("Pediatrics")
        search.submit()
        assert "Dr. Nusrat Jahan" in driver.page_source

        # 3. Book an appointment as the logged-in patient.
        driver.get(BASE_URL)
        Select(driver.find_element(By.NAME, "doctor")).select_by_value("Dr. Nusrat Jahan")
        Select(driver.find_element(By.NAME, "time")).select_by_value("16:00")
        driver.find_element(By.CSS_SELECTOR, "form.book-form button").click()

        page = driver.page_source
        # The first run books the slot; later runs show the double-booking error.
        assert "Booked Dr. Nusrat Jahan" in page or "already booked" in page
    finally:
        driver.quit()
