"""
Thin wrapper around the Betting API for use in tests.

Encapsulates base URL, authentication header injection, and response
parsing so tests stay focused on assertions rather than HTTP plumbing.
"""
import requests


class ApiClient:
    """HTTP client for the Single Bet Placement API."""

    def __init__(self, base_url: str, user_id: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.user_id = user_id
        self._session = requests.Session()
        self._session.headers.update({
            "x-user-id": user_id,
            "Content-Type": "application/json",
        })

    def place_bet(self, match_id: str, selection: str, stake: float) -> requests.Response:
        """POST /api/place-bet — places a single bet."""
        return self._session.post(
            f"{self.base_url}/api/place-bet",
            json={"matchId": match_id, "selection": selection, "stake": stake},
        )

    def reset_balance(self) -> requests.Response:
        """POST /api/reset-balance — resets balance to initial configured value."""
        response = self._session.post(f"{self.base_url}/api/reset-balance")
        response.raise_for_status()
        return response

    def get_balance_value(self) -> float:
        """Return the numeric balance, raising on non-200 responses."""
        response = self._session.get(f"{self.base_url}/api/balance")
        response.raise_for_status()
        return response.json()["balance"]

    def get_first_match(self) -> dict:
        """Return the first match regardless of status (for API-level tests)."""
        response = self._session.get(f"{self.base_url}/api/matches")
        response.raise_for_status()
        matches = response.json()
        if not matches:
            raise ValueError("No matches returned by the API")
        return matches[0]

