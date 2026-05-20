from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait


class BetSlipPage:
    _STAKE_INPUT = (By.ID, "bet-slip-stake-input")
    _PLACE_BET_BTN = (By.ID, "bet-slip-place-bet")
    _RECEIPT_MODAL = (By.ID, "modal-success")
    _RECEIPT_BET_ID = (By.ID, "modal-success-bet-id")
    _RECEIPT_MATCH = (By.ID, "modal-success-match")
    _RECEIPT_STAKE = (By.ID, "modal-success-stake")
    _RECEIPT_ODDS = (By.ID, "modal-success-odds")
    _RECEIPT_PAYOUT = (By.ID, "modal-success-payout")
    _RECEIPT_CLOSE = (By.ID, "modal-success-close")

    def __init__(self, driver: WebDriver, timeout: int = 15) -> None:
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout)

    def enter_stake(self, amount: float) -> None:
        field = self.wait.until(ec.element_to_be_clickable(self._STAKE_INPUT))
        field.send_keys(str(amount))

    def click_place_bet(self) -> None:
        self.wait.until(ec.element_to_be_clickable(self._PLACE_BET_BTN)).click()

    def wait_for_receipt(self, timeout: int = 20) -> None:
        WebDriverWait(self.driver, timeout).until(
            ec.visibility_of_element_located(self._RECEIPT_MODAL)
        )

    def get_receipt_bet_id(self) -> str:
        return self.driver.find_element(*self._RECEIPT_BET_ID).text.strip()

    def get_receipt_match(self) -> str:
        return self.driver.find_element(*self._RECEIPT_MATCH).text.strip()

    def get_receipt_stake(self) -> str:
        return self.driver.find_element(*self._RECEIPT_STAKE).text.strip()

    def get_receipt_odds(self) -> str:
        return self.driver.find_element(*self._RECEIPT_ODDS).text.strip()

    def get_receipt_payout(self) -> str:
        return self.driver.find_element(*self._RECEIPT_PAYOUT).text.strip()

    def close_receipt(self) -> None:
        self.wait.until(ec.element_to_be_clickable(self._RECEIPT_CLOSE)).click()

    def wait_for_receipt_closed(self, timeout: int = 5) -> None:
        WebDriverWait(self.driver, timeout).until(
            ec.invisibility_of_element_located(self._RECEIPT_MODAL)
        )
