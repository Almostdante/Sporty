import pytest

from pages.match_list_page import MatchListPage
from pages.bet_slip_page import BetSlipPage

STAKE = 10.00


@pytest.mark.ui
def test_successful_single_bet_e2e(authenticated_driver, api):
    match = api.get_first_match()
    api.reset_balance()
    balance_before = api.get_balance_value()

    match_page = MatchListPage(authenticated_driver)
    bet_slip = BetSlipPage(authenticated_driver)

    match_page.wait_for_matches()
    match_page.select_home_odds()
    bet_slip.enter_stake(STAKE)
    bet_slip.click_place_bet()
    bet_slip.wait_for_receipt()

    receipt_match = bet_slip.get_receipt_match()
    assert bet_slip.get_receipt_bet_id(), "Bet ID missing from receipt"
    assert match["homeTeam"] in receipt_match and match["awayTeam"] in receipt_match, \
        "Both team names must be present in receipt"
    assert bet_slip.get_receipt_stake() == f"€{STAKE:.2f}", "Stake missing from receipt"
    assert bet_slip.get_receipt_odds() == str(match["odds"]["home"]), "Odds missing from receipt"

    # BUG-001: frontend uses hardcoded ×2.0 instead of actual match odds
    correct_payout = f"€{STAKE * match['odds']['home']:.2f}"
    actual_payout = bet_slip.get_receipt_payout()
    if actual_payout != correct_payout:
        pytest.xfail(f"BUG-001: payout shows {actual_payout}, expected {correct_payout}")

    bet_slip.close_receipt()
    bet_slip.wait_for_receipt_closed()

    # BUG-006: UI balance does not update after bet without page reload — verified via API
    assert api.get_balance_value() == balance_before - STAKE
