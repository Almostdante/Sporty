# Betting QA — Single Bet Placement Test Suite

Automation framework for the Single Bet Placement feature.

**Stack:** Python 3.11+ · Selenium WebDriver · pytest · requests

---

## Project Structure

```
Sporty/
├── conftest.py                      # Shared pytest fixtures
├── pytest.ini                       # Test runner configuration
├── requirements.txt                 # Python dependencies
│
├── pages/                           # Page Object Model
│   ├── match_list_page.py           # Match list interactions
│   └── bet_slip_page.py             # Bet slip, receipt, error modal
│
├── tests/
│   ├── ui/
│   │   └── test_place_bet_e2e.py   # E2E UI test (Selenium)
│   └── api/
│       └── test_place_bet_api.py   # API tests (requests)
│
├── utils/
│   ├── api_client.py               # HTTP client wrapper
│   └── config.py                   # Configuration constants
│
└── docs/
    ├── test_plan.md                # Prioritised scenarios
    ├── bug_reports.md              # Execution results + bug reports
    ├── strategy.md                 # Test strategy and improvement proposals
```

---

## Setup

```bash
# 1. Clone the repository
git clone <repo-url>
cd Sporty

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate       # macOS/Linux
.venv\Scripts\activate          # Windows

# 3. Install dependencies
pip install -r requirements.txt
```

ChromeDriver is managed automatically by `webdriver-manager`.

---

## Configuration

| Variable | Default | Description |
|---|---|---|
| `BASE_URL` | `https://qae-assignment-tau.vercel.app` | Application base URL |
| `USER_ID` | `candidate-O7q5FfY5jx` | Test user ID |
| `HEADLESS` | `true` | Set to `false` to watch the browser |

Set via a `.env` file in the project root (copy from `.env.example`):

```bash
cp .env.example .env
# then edit .env and set your USER_ID
```

---

## Running Tests

```bash
# All tests
pytest

# API tests only (fast, no browser)
pytest -m api

# UI / E2E tests
pytest -m ui

# Visible browser (useful for debugging)
HEADLESS=false pytest -m ui -v

# Single test file
pytest tests/api/test_place_bet_api.py -v

# Single test by name
pytest -k "test_missing_user_id" -v
```

HTML report is generated automatically at `reports/report.html`.

---

## Test Coverage

### UI Tests (`-m ui`)

| Test | What it verifies |
|---|---|
| `test_successful_single_bet_e2e` | Full happy path: select → stake → place → receipt fields → balance deduction via API |

### API Tests (`-m api`)

| Test Class | What it covers |
|---|---|
| `TestStakeValidation` | 10 parameterised boundary cases (€0, €0.99, €1.00, €50, €100, €100.01...) |
| `TestAuthAndProtocolValidation` | Missing auth (401), invalid selection (422), unknown match (422), malformed JSON (400), wrong method (405), missing fields (422) |
| `TestBalanceIntegrity` | Balance deducted by exact stake; response ↔ GET /api/balance consistency; reset persistence (documents BUG-010) |

---

## Known Bugs Captured in Tests

Tests are written against the **specified** behaviour. Tests that exercise known bugs are annotated with the bug ID and will fail against the current implementation — this is intentional, as failing tests document defects.

| Bug | Affected Test | Description |
|---|---|---|
| BUG-001 | `test_successful_single_bet_e2e` | Payout = stake × 2.0 instead of stake × actual odds |
| BUG-002 | `test_bet_exceeding_balance_is_rejected` | API accepts bets exceeding account balance |
| BUG-010 | `test_reset_balance_persists_correct_value` | Reset response claims 125.50, persists 120.00 |

---

## Design Decisions

**Page Object Model:** All selectors in `pages/`. Tests call business-level methods (`match_page.select_home_odds()`), not raw Selenium. Selector changes require editing one file.

**Function-scoped fixtures:** Each test gets a fresh browser. Tests are fully independent.

**No reset_balance in conftest:** BUG-010 means reset is unreliable for test isolation. Tests that need a known balance state handle it explicitly.

**API-based balance assertions in UI tests:** Because BUG-006 means the UI header does not update after a bet without a page reload, balance assertions use `api.get_balance_value()` rather than reading the screen.

**webdriver-manager:** Correct ChromeDriver version downloaded automatically on first run.
