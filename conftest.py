"""
Shared pytest fixtures for the Single Bet Placement test suite.

Provides:
  - Selenium WebDriver (Chrome, headless-capable)
  - A pre-authenticated API client
  - Application URLs and user context
"""
import pathlib
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from utils.api_client import ApiClient
from utils.config import BASE_URL, USER_ID


def pytest_configure(config):
    """Ensure the reports directory exists before pytest-html writes to it."""
    pathlib.Path("reports").mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# Browser fixture
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def driver():
    """
    Yield a Chrome WebDriver instance for the duration of one test function.

    Set HEADLESS=false to watch the browser during debugging.
    """

    service = Service(ChromeDriverManager().install())
    browser = webdriver.Chrome(service=service)
    browser.implicitly_wait(10)

    yield browser
    browser.quit()


# ---------------------------------------------------------------------------
# API client fixture
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def api():
    """
    Yield an ApiClient instance.

    NOTE: We do NOT call reset_balance() here because BUG-009 means
    reset returns an incorrect value (claims 125.50, persists 120.00).
    Tests that need a known starting balance should handle setup explicitly.
    """
    client = ApiClient(base_url=BASE_URL, user_id=USER_ID)
    yield client


# ---------------------------------------------------------------------------
# Authenticated browser fixture
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def authenticated_driver(driver, api):
    """
    Yield a WebDriver already navigated to the authenticated app URL.
    """
    driver.get(f"{BASE_URL}?user-id={USER_ID}")
    yield driver
