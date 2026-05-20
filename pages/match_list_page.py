from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait


class MatchListPage:
    _ODDS_BUTTON = (By.CSS_SELECTOR, "button.oddsButton")

    def __init__(self, driver: WebDriver, timeout: int = 15) -> None:
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout)

    def wait_for_matches(self) -> "MatchListPage":
        self.wait.until(ec.presence_of_element_located(self._ODDS_BUTTON))
        return self

    def select_home_odds(self) -> WebElement:
        btn = self.driver.find_elements(*self._ODDS_BUTTON)[0]
        btn.click()
        return btn
