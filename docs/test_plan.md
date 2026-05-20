# Test Plan — Single Bet Placement

**Feature:** Single Bet Placement  
**Platform:** Desktop Web Application  
**Author:** Andrey Dmitriev

---

## Scope

Covers the Single Bet Placement feature for pre-match football events on desktop.  
**Out of scope:** live betting, accumulators, mobile UX, other sports.

---

## Risk Assessment

Highest risk areas:
1. **Financial correctness** — payout calculation and balance deduction directly affect real money
2. **Stake boundary enforcement** — off-by-one errors at €1.00 / €100.00 are a classic defect source
3. **Balance integrity** — must stay consistent between header and bet slip, and update after each bet
4. **PAST match exposure** — bets on known results are a fraud and compliance risk
5. **Receipt accuracy** — all values post-placement must match pre-placement exactly

---

## Test Scenarios

---

### TC-01 — Successful Single Bet (Happy Path)

| Field | Value |
|---|---|
| **Priority** | Critical |
| **Type** | Happy path / E2E |

**Risk Rationale:** Core revenue-generating flow. Any failure here means the feature is broken for all users. Receipt values must exactly match pre-placement values (financial accuracy).

**Preconditions:** User authenticated, balance sufficient, at least one UPCOMING match visible.

**Steps:**
1. Open main page
2. Select an UPCOMING match, click the **1** (Home) odds button
3. Verify bet slip shows correct match, selection, and odds
4. Enter stake **€10.00**
5. Verify Potential Payout = stake × odds shown in slip
6. Note balance in header
7. Click **Place Bet**, verify button shows **"Placing…"**
8. Verify success receipt modal appears

**Expected Results:**
- Receipt shows: Bet ID (non-empty), match name (home team first), selection label (e.g. "HOME"), stake €10.00, odds matching pre-placement, payout = stake × odds, timestamp present
- Balance in header reduced by exactly €10.00
- No active selection after closing receipt

---

### TC-02 — Stake Boundary Values

| Field | Value |
|---|---|
| **Priority** | Critical |
| **Type** | Boundary / Negative |

**Risk Rationale:** Boundary conditions are the most common source of validation bugs. Off-by-one at €1.00 / €100.00 could block legitimate bets or allow policy violations.

> **Spec note:** §3 lists minimum stake as €1.00; §4.1 lists "Minimum €1.01 (positive values)". These steps use €1.00 per §3 and the UI error copy in §4.4 (`Minimum stake is €1.00`). Clarification from product needed — see also step 3a.

**Steps:**
1. Select a match
2. Enter **€0.99** → verify error "Minimum stake is €1.00", Place Bet disabled
3. Enter **€1.00** → verify accepted, Place Bet active
   - 3a. Enter **€1.01** → verify also accepted (covers §4.1 boundary; both should pass — if €1.00 is rejected, flag as spec conflict)
4. Enter **€100.00** → verify accepted
5. Enter **€100.01** → verify error "Maximum stake is €100.00", Place Bet disabled
6. Enter **€10.001** → verify rejected (max 2 decimal places)
7. Enter **abc** → verify rejected (non-numeric)

**Expected Results:** All boundaries enforced correctly with clear error messages.

---

### TC-03 — Stake Exceeds Available Balance

| Field | Value |
|---|---|
| **Priority** | Critical |
| **Type** | Negative / Financial |

**Risk Rationale:** Allowing a bet above balance would create a negative balance — direct financial risk.

**Steps:**
1. Make a few bets to have current balance below €100
2. Confirm current balance (e.g. €90)
3. Enter stake **€90.01** → verify "Insufficient balance" error, Place Bet disabled
4. Enter **€90** (exact balance) → verify accepted
5. Verify balance after bet = €0.00

**Expected Results:** UI and API both enforce balance limit. Balance correctly reduced after bet.

---

### TC-04 — Bet Placement Failure — Error Modal and Retry

| Field | Value |
|---|---|
| **Priority** | High |
| **Type** | Error handling |

**Risk Rationale:** Error recovery path must not silently deduct funds or leave stale state.

**Steps:**
1. Select match, enter valid stake
2. Simulate API failure (DevTools → Network → block /api/place-bet)
3. Click Place Bet → verify error modal appears: title "Something went wrong"
4. Click **Rebet** → verify modal closes, placement retried (selection/stake preserved)
5. Click **Close** → verify modal closes, selection and stake cleared
6. Click **×** (top-right) → verify same as Close
7. Confirm balance unchanged after all failed attempts
8. *(API)* Send two concurrent `POST /api/place-bet` requests for the same user → verify second request returns **409** and only one bet is deducted

**Expected Results:** Correct modal copy, correct button behaviours, no funds deducted on failure. Concurrent duplicate request returns 409 with no double-deduction.

---

### TC-05 — Bet Slip: Selection Replace and Remove

| Field | Value |
|---|---|
| **Priority** | High |
| **Type** | Functional / UI state |

**Risk Rationale:** Bet slip must enforce single-selection at all times. Stale state breaks the single bet constraint.

**Steps:**
1. Click **1** on Match A → verify in slip
2. Click **X** on Match B → verify it **replaces** Match A (only one selection)
3. Click **2** on Match A → verify replaces again
4. Click **×** (per-selection remove) → verify slip empty
5. Select a match, enter stake, click **Remove All** → verify slip and stake cleared
6. Place a bet, close receipt → verify slip empty, no active selection

**Expected Results:** Only one selection active at any time. All removal paths clear slip completely.

---

### TC-06 — Filters: Odds and Date Range Validation

| Field | Value |
|---|---|
| **Priority** | Medium |
| **Type** | Validation / UI |

**Risk Rationale:** Spec §2.6 requires both filters to enforce range logic and produce clear feedback on invalid input. Silent empty lists or accepted invalid ranges look like crashes or data gaps.

**Odds filter steps:**
1. Open Odds filter
2. Set MIN=5.00, MAX=1.00 (min > max) → verify error feedback shown
3. Set MIN=1.50, MAX=3.00 → verify only matching matches shown
4. Set MIN=2.50, MAX=2.50 (equal, inclusive) → verify exact matches appear
5. Clear filter → verify full list restored
6. Verify match counter updates correctly after each filter change

**Date filter steps:**
7. Open Date filter, select a single day that has matches → verify only that day's matches shown
8. Set date range FROM=day1 TO=day3 (inclusive) → verify matches from all covered days are shown
9. Clear date filter → verify full list restored

**Expected Results:** Invalid ranges in both filters rejected with clear feedback. Valid ranges filter correctly and inclusively. Counter reflects filtered count after every change.

---

### TC-07 — PAST Match Exposure

| Field | Value |
|---|---|
| **Priority** | Critical |
| **Type** | Compliance / Negative |

**Risk Rationale:** Spec §1 restricts the platform to "upcoming/pre-match events only". If PAST matches are visible and bettable, users can wager on known results — a direct fraud and regulatory compliance risk regardless of UX intent.

**Preconditions:** User authenticated. At least one match with a past kickoff date is present in the API response (confirmed in current build).

**Steps:**
1. Open main page
2. Scan the match list for any match marked PAST or with a kickoff date/time in the past
3. Verify PAST matches are **not displayed** in the match list
4. If PAST matches are visible, verify their odds buttons are **disabled** and placement is blocked
5. Via API: `POST /api/place-bet` using the `id` of a known PAST match with a valid stake → verify the response is **422** (or equivalent rejection)

**Expected Results:**
- PAST matches are absent from the UI match list, OR their odds buttons are visually disabled and non-interactive
- API rejects a bet on a PAST match with a 422 error

---

## Prioritisation Summary

| ID    | Title | Priority     |
|-------|---|--------------|
| TC-01 | Successful Single Bet (Happy Path) | **Critical** |
| TC-02 | Stake Boundary Values | **Critical** |
| TC-03 | Stake Exceeds Available Balance | **Critical** |
| TC-07 | PAST Match Exposure | **Critical** |
| TC-04 | Bet Placement Failure — Error Modal and Retry | **High**     |
| TC-05 | Bet Slip: Selection Replace and Remove | **High**     |
| TC-06 | Filters: Odds and Date Range Validation | **Medium**   |
