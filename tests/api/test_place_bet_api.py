"""
API Tests: Stake Validation, Business Rules, Balance Integrity

WHY THESE TESTS WERE CHOSEN FOR AUTOMATION:
--------------------------------------------
Stake validation is the primary financial guardrail. Testing directly
at API level (bypassing UI) verifies the backend is the authoritative
enforcement layer. Key reasons:

  1. A malicious or misconfigured client can bypass UI validation —
     the API must enforce all rules independently.
  2. Correct HTTP status codes (422, 401, 400, 405) are part of the
     API contract; wrong codes break downstream integrations silently.
  3. Fast, deterministic, no browser required — ideal for CI on every
     commit or PR.
  4. Parameterised boundary tests cover 10+ cases with zero duplication.
"""
import pytest
import requests

from utils.api_client import ApiClient
from utils.config import BASE_URL, USER_ID, MIN_STAKE, MAX_STAKE


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_headers(user_id: str | None = USER_ID) -> dict:
    h = {"Content-Type": "application/json"}
    if user_id is not None:
        h["x-user-id"] = user_id
    return h


# ---------------------------------------------------------------------------
# Stake boundary tests — parameterised
# ---------------------------------------------------------------------------

STAKE_BOUNDARY_CASES = [
    # (description,              stake,              expected_status)
    ("below_min",                MIN_STAKE - 0.01,   422),
    ("well_below_min",           0.01,               422),
    ("zero_stake",               0,                  422),
    pytest.param(
        "negative_stake", -1.00, 422,
        id="negative_stake",
        marks=pytest.mark.xfail(
            strict=False,
            reason="BUG: backend accepts negative stakes, returns 200 instead of 422",
        ),
    ),
    ("at_minimum",               MIN_STAKE,          200),
    ("above_minimum",            MIN_STAKE + 0.01,   200),
    ("mid_range",                50.00,              200),
    ("at_maximum",               MAX_STAKE,          200),
    ("above_maximum",            MAX_STAKE + 0.01,   422),
    ("well_above_maximum",       200.00,             422),
]


@pytest.mark.api
class TestStakeValidation:

    @pytest.fixture(autouse=True)
    def setup(self, api: ApiClient):
        """Reset balance and fetch a valid match ID before each case."""
        api.reset_balance()
        match = api.get_first_match()
        self.match_id = match["id"]
        self.api = api

    @pytest.mark.parametrize(
        "description,stake,expected_status",
        STAKE_BOUNDARY_CASES,
    )
    def test_stake_boundary(self, description: str, stake: float,
                            expected_status: int):
        """
        Verify the API enforces stake min/max boundaries with correct
        HTTP status codes. For 422 responses, body must be non-empty.
        """
        response = self.api.place_bet(
            match_id=self.match_id, selection="HOME", stake=stake
        )

        assert response.status_code == expected_status, (
            f"[{description}] stake={stake}: "
            f"expected HTTP {expected_status}, got {response.status_code}. "
            f"Body: {response.text[:300]}"
        )

        if expected_status == 422:
            assert response.text.strip(), (
                f"[{description}] 422 response has empty body — "
                f"clients cannot diagnose the error"
            )


# ---------------------------------------------------------------------------
# Payout calculation
# ---------------------------------------------------------------------------

@pytest.mark.api
class TestPayoutCalculation:

    def test_payout_equals_stake_times_odds(self, api: ApiClient):
        """
        Payout in the place-bet response must equal stake × odds,
        rounded to 2 decimal places (spec: Payout = stake × odds).
        """
        api.reset_balance()
        match = api.get_first_match()
        stake = 10.00

        response = api.place_bet(match_id=match["id"], selection="HOME", stake=stake)
        assert response.status_code == 200, (
            f"Bet placement failed: {response.status_code} — {response.text[:200]}"
        )

        data = response.json()
        expected_payout = round(stake * data["odds"], 2)
        assert data["payout"] == expected_payout, (
            f"Payout mismatch: expected {expected_payout} "
            f"(stake {stake} × odds {data['odds']}), got {data['payout']}"
        )


# ---------------------------------------------------------------------------
# Authentication and protocol validation
# ---------------------------------------------------------------------------

@pytest.mark.api
class TestAuthAndProtocolValidation:

    @pytest.fixture(autouse=True)
    def setup(self, api: ApiClient):
        match = api.get_first_match()
        self.match_id = match["id"]

    def test_missing_user_id_returns_401(self):
        """
        x-user-id header is required (spec section 4.3).
        Omitting it must return 401 — verifies the auth guard
        cannot be bypassed by a headerless request.
        """
        response = requests.post(
            f"{BASE_URL}/api/place-bet",
            json={"matchId": self.match_id, "selection": "HOME", "stake": 10.00},
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 401, (
            f"Expected 401 for missing x-user-id, "
            f"got {response.status_code}. Body: {response.text[:200]}"
        )

    def test_invalid_selection_returns_422(self):
        """Selection must be HOME, DRAW, or AWAY (spec 4.2). 'WIN' → 422."""
        response = requests.post(
            f"{BASE_URL}/api/place-bet",
            json={"matchId": self.match_id, "selection": "WIN", "stake": 10.00},
            headers=make_headers(),
        )
        assert response.status_code == 422, (
            f"Expected 422 for invalid selection 'WIN', "
            f"got {response.status_code}. Body: {response.text[:200]}"
        )

    def test_unknown_match_id_returns_422(self):
        """Match ID must exist in catalog (spec 4.2). Unknown ID → 422, not 500."""
        response = requests.post(
            f"{BASE_URL}/api/place-bet",
            json={"matchId": "non-existent-xyz", "selection": "HOME", "stake": 10.00},
            headers=make_headers(),
        )
        assert response.status_code == 422, (
            f"Expected 422 for unknown matchId, "
            f"got {response.status_code}. Body: {response.text[:200]}"
        )

    @pytest.mark.xfail(
        strict=False,
        reason="BUG: server returns 500 instead of 400 for malformed JSON body",
    )
    def test_malformed_json_returns_400(self):
        """Non-object payload must return 400 (spec 4.3)."""
        response = requests.post(
            f"{BASE_URL}/api/place-bet",
            data="this is not json",
            headers={**make_headers(), "Content-Type": "application/json"},
        )
        assert response.status_code == 400, (
            f"Expected 400 for malformed JSON, "
            f"got {response.status_code}. Body: {response.text[:200]}"
        )

    @pytest.mark.xfail(
        strict=False,
        reason="BUG: GET /api/place-bet returns 200 instead of 405",
    )
    def test_get_method_not_allowed(self):
        """GET on /api/place-bet must return 405 (spec 4.3)."""
        response = requests.get(
            f"{BASE_URL}/api/place-bet",
            headers=make_headers(),
        )
        assert response.status_code == 405, (
            f"Expected 405 for GET on /api/place-bet, "
            f"got {response.status_code}."
        )

    def test_missing_match_id_returns_422(self):
        """matchId is required (spec 4.2). Omitting → 422."""
        response = requests.post(
            f"{BASE_URL}/api/place-bet",
            json={"selection": "HOME", "stake": 10.00},
            headers=make_headers(),
        )
        assert response.status_code == 422, (
            f"Expected 422 for missing matchId, "
            f"got {response.status_code}. Body: {response.text[:200]}"
        )

    def test_missing_selection_returns_422(self):
        """selection is required (spec 4.2). Omitting → 422."""
        response = requests.post(
            f"{BASE_URL}/api/place-bet",
            json={"matchId": self.match_id, "stake": 10.00},
            headers=make_headers(),
        )
        assert response.status_code == 422, (
            f"Expected 422 for missing selection, "
            f"got {response.status_code}. Body: {response.text[:200]}"
        )


# ---------------------------------------------------------------------------
# Balance integrity
# ---------------------------------------------------------------------------

@pytest.mark.api
class TestBalanceIntegrity:

    def test_balance_decreases_by_exact_stake(self, api: ApiClient):
        """
        After a successful bet, balance must decrease by exactly the stake.

        This is the most fundamental financial invariant of the system.
        Testing at API level eliminates display rounding as a confounding
        factor and gives us raw numbers from the source of truth.

        Also verifies that the balance in the place-bet response matches
        the balance returned by GET /api/balance immediately after
        (spec: response body and persisted state must be consistent).
        """
        api.reset_balance()
        match = api.get_first_match()
        stake = 25.00

        balance_before = api.get_balance_value()

        response = api.place_bet(
            match_id=match["id"],
            selection="HOME",
            stake=stake,
        )
        assert response.status_code == 200, (
            f"Bet placement failed: {response.status_code} — {response.text[:200]}"
        )

        data = response.json()
        balance_in_response = data.get("balance")
        assert balance_in_response is not None, \
            "place-bet response missing 'balance' field"

        expected_balance = balance_before - stake

        # Check response body
        assert balance_in_response == expected_balance, (
            f"Balance in place-bet response ({balance_in_response}) "
            f"≠ expected ({expected_balance}). "
            f"Before: €{balance_before}, Stake: €{stake}"
        )

        # Check persisted state via GET /api/balance
        balance_persisted = api.get_balance_value()
        assert balance_persisted == expected_balance, (
            f"Persisted balance ({balance_persisted}) "
            f"≠ response balance ({balance_in_response}). "
            f"State inconsistency between place-bet response and /api/balance."
        )

    @pytest.mark.xfail(
        strict=False,
        reason="BUG-002: API does not enforce balance check — second bet above remaining balance is accepted",
    )
    def test_bet_exceeding_balance_is_rejected(self, api: ApiClient):
        """
        After reset the persisted balance is €120. A €100 bet leaves €20.
        A second €100 bet must be rejected with 422 (insufficient balance).

        BUG-002: The API currently accepts the second bet because it does not
        validate the stake against the server-side balance. The UI bug (stale
        balance display after a bet) allows the same exploit without DevTools.
        """
        match = api.get_first_match()

        api.reset_balance()
        balance_after_reset = api.get_balance_value()
        assert balance_after_reset >= 100, (
            f"Balance after reset ({balance_after_reset}) is incorrect"
        )

        # First bet: €100 — must succeed
        first = api.place_bet(match_id=match["id"], selection="HOME", stake=100.00)
        assert first.status_code == 200, (
            f"First €100 bet failed unexpectedly: "
            f"{first.status_code} — {first.text[:200]}"
        )

        balance_after_first = api.get_balance_value()
        expected_after_first = balance_after_reset - MAX_STAKE
        assert balance_after_first == expected_after_first, (
            f"Balance after first bet: expected €{expected_after_first}, "
            f"got €{balance_after_first}"
        )

        # Second bet: €100 — must be rejected (remaining balance ≈ €20)
        second = api.place_bet(match_id=match["id"], selection="HOME", stake=100.00)
        assert second.status_code == 422, (
            f"Second €100 bet should be rejected with 422 "
            f"(balance after first bet: €{balance_after_first}), "
            f"got {second.status_code}. Body: {second.text[:200]}"
        )

    @pytest.mark.xfail(
        strict=False,
        reason="BUG-010: reset-balance response claims 125.50 but GET /api/balance returns 120.00",
    )
    def test_reset_balance_persists_correct_value(self, api: ApiClient):
        """
        POST /api/reset-balance must persist the value it reports in its response.

        BUG-010: Currently the response claims 125.50 but GET /api/balance
        returns 120.00 immediately after. This test documents the expected
        behaviour and will pass once the bug is fixed.
        """
        reset_response = api.reset_balance()
        reported_balance = reset_response.json()["balance"]

        persisted_balance = api.get_balance_value()

        assert persisted_balance == reported_balance, (
            f"[BUG-010] reset-balance reported {reported_balance} "
            f"but GET /api/balance returned {persisted_balance}. "
            f"Response and persisted state are inconsistent."
        )
