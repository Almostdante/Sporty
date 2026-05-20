# Test Execution Results & Bug Reports

**Feature:** Single Bet Placement  
**Platform:** Desktop Web Application  
**Author:** Andrey Dmitriev

---

## Execution Summary

| Scenario                               | Result | Bugs Found                                  |
|----------------------------------------|---|---------------------------------------------|
| TC-01 — Happy Path                     | ❌ FAIL | BUG-001, BUG-003, BUG-004, BUG-005, BUG-006 |
| TC-02 — Stake Boundaries               | ✅ PASS | —                                           |
| TC-05 — Selection Replace / Remove All | ✅ PASS | —                                           |
| TC-06 — Odds Filter Invalid Range      | ❌ FAIL | BUG-007, BUG-009                            |
| TC-07 — PAST Match Exposure            | ❌ FAIL | BUG-008                                     |
| Exploratory                            | ❌ FAIL | BUG-002, BUG-010, BUG-011                   |

---

## TC-01 Execution — Successful Single Bet (Happy Path)

**Status:** ❌ FAIL — multiple defects in receipt and balance sync

**Steps executed:**
1. Opened app — match list loaded
2. Selected **Seattle Sounders vs LAFC** (UPCOMING, MLS), clicked Home (odds 2.55)
3. Entered stake **€10.00** — bet slip showed Potential Payout **€25.50** ✅ (10 × 2.55)
4. Clicked **Place Bet** — button changed to **"Placing…"** ✅
5. After ~8 seconds — success receipt modal appeared
6. Receipt showed: Bet ID #B-26605 ✅, Stake €10.00 ✅, Odds 2.55 ✅
7. Receipt showed: Payout **€20.00** ❌ (expected €25.50), no Selection field ❌, teams reversed ❌, timestamp "TODAY, 13:13" ❌
8. Header balance: €120.00 — **unchanged** ❌ (deducted only after page reload)

**Bugs found:** BUG-001, BUG-003, BUG-004, BUG-005, BUG-006

---

## TC-02 Execution — Stake Boundary Values

**Status:** ✅ PASS

1. €0.50 → "Minimum stake is €1.00", Place Bet disabled ✅
2. €1.00 → accepted, Place Bet active ✅
3. €100.01 → "Maximum stake is €100.00", Place Bet disabled ✅
4. €100.00 → accepted ✅

---

## TC-05 Execution — Selection Replace / Remove All

**Status:** ✅ PASS

1. Clicked Home on match A → appeared in slip ✅
2. Clicked Draw on match B → replaced previous selection ✅
3. Clicked "Remove All" → slip cleared ✅
4. Per-selection × → works correctly ✅

---

## TC-06 Execution — Odds Filter Invalid Range

**Status:** ❌ FAIL

1. Set MIN=5, MAX=2 → applied without error, empty list, counter still "Showing 103 matches" ❌

**Bugs found:** BUG-007, BUG-009

---

## TC-07 Execution — PAST Match Exposure

**Status:** ❌ FAIL

1. Open main page
2. Scan the match list for any match marked PAST or with a kickoff date/time in the past

**Bugs found:** BUG-008

---

## Bug Reports

---

### BUG-001 — Potential Payout in receipt is calculated incorrectly (CRITICAL)

| Field | Value                                                                                |
|---|--------------------------------------------------------------------------------------|
| **Bug ID** | BUG-001                                                                              |
| **Title** | Potential Payout in receipt always equals stake × 2.0 instead of stake × actual odds |
| **Severity** | Critical                                                                             |
| **Reproduced on** | Any match with odds != 2.00                                                          |

**Steps to reproduce:**
1. Select any match with odds != 2.00, e.g. Seattle Sounders Home (2.55)
2. Enter stake €10.00
3. Bet slip shows Potential Payout **€25.50** (10 × 2.55) — correct
4. Click Place Bet
5. Check Potential Payout in the receipt

**Expected result:** €25.50

**Actual result:** €20.00 (= 10 × 2.0)


---

### BUG-002 — The user is able to place bets exceeding their account balance (CRITICAL)

| Field | Value                                       |
|---|---------------------------------------------|
| **Bug ID** | BUG-002                                     |
| **Title** | The user is able to place bets exceeding their account balance |
| **Severity** | Critical                                    |

**Steps to reproduce:**
1. Reset user balance
2. Select any match, e.g. "Seattle Sounders vs LAFC" 
3. Enter max bet €100.00
4. Click Place Bet
5. Repeat steps 2-5 without reloading a page

**Expected result:** Second bet is declined because of insufficient balance

**Actual result:** Both bets are accepted

**Note** The core reason of the issue is lack of validation in API, issue can be reproduced by posting bet directly from https://qae-assignment-tau.vercel.app/api/place-bet endpoint

### BUG-003 — Team order in receipt is reversed (HIGH)

| Field | Value                                                  |
|---|--------------------------------------------------------|
| **Bug ID** | BUG-003                                                |
| **Title** | Receipt shows "Away vs Home" instead of "Home vs Away" |
| **Severity** | High                                                   |

**Steps to reproduce:**
1. Select match "Seattle Sounders vs LAFC" (Sounders = Home)
2. Click Place Bet
3. Read the MATCH field in the receipt

**Expected result:** "Seattle Sounders vs LAFC" (home first — spec section "Match Ordering")

**Actual result:** "LAFC vs Seattle Sounders" (away first)

---

### BUG-004 — Selection field is missing from receipt (HIGH)

| Field | Value                                                |
|---|------------------------------------------------------|
| **Bug ID** | BUG-004                                              |
| **Title** | Receipt does not show Selection (HOME / DRAW / AWAY) |
| **Severity** | High                                                 |

**Steps to reproduce:**
1. Select any match, click Home odds
2. Place the bet
3. Inspect the receipt

**Expected result:** Selection field: HOME (required by spec, section 2.4)

**Actual result:** No Selection field. Receipt contains: Bet ID, Match, Stake, Odds, Potential Payout, Timestamp — Selection is absent.

**Business Impact:** The receipt does not confirm which outcome was wagered on. This is critical in any dispute resolution.

---

### BUG-005 — Timestamp in receipt is incomplete: no date and no timezone (MEDIUM)

| Field | Value                                                       |
|---|-------------------------------------------------------------|
| **Bug ID** | BUG-005                                                     |
| **Title** | Timestamp shows "TODAY, 13:13" — without a date or timezone |
| **Severity** | Medium                                                      |

**Expected result:** A full timestamp, e.g. "2026-05-19T13:13:00Z"

**Actual result:** "TODAY, 13:13"

"TODAY" becomes meaningless the following day. Without a timezone the timestamp cannot be precisely tied to an audit record.

---

### BUG-006 — UI does not update balance after a bet without a page reload (HIGH)

| Field | Value                                                                                       |
|---|---------------------------------------------------------------------------------------------|
| **Bug ID** | BUG-006                                                                                     |
| **Title** | Balance in header and bet slip does not update after a bet — only updates after page reload |
| **Severity** | High                                                                                        |

**Detailed investigation:**

| Moment | API /api/balance | UI Header | Expected |
|---|---|---|---|
| After €15 bet, receipt open | **€105.00** ✅ | **€120.00** ❌ | €105.00 |
| After receipt closed | **€105.00** ✅ | **€120.00** ❌ | €105.00 |
| After page reload | €105.00 ✅ | **€105.00** ✅ | €105.00 |

**Note:** The funds are correctly deducted on the backend immediately. 

**Business Impact:** The user sees a stale balance and may believe the stake was not deducted. They may attempt to place another bet against the false available balance.

---

### BUG-007 — Odds filter accepts invalid range (MIN > MAX) without an error (MEDIUM)

| Field | Value                                                              |
|---|--------------------------------------------------------------------|
| **Bug ID** | BUG-007                                                            |
| **Title** | Odds filter applies MIN=5 / MAX=2 without showing an error message |
| **Severity** | Medium                                                             |

**Steps to reproduce:**
1. Open the Odds filter
2. Set MIN=5, MAX=2
3. Click Apply

**Expected:** An error message (spec section 2.6: "must reject invalid ranges with clear feedback")

**Actual:** Filter is applied, match list is empty, no error message is shown

---

### BUG-008 — PAST matches are displayed in the list and accept bets (CRITICAL)

| Field | Value                                                                                     |
|---|-------------------------------------------------------------------------------------------|
| **Bug ID** | BUG-008                                                                                   |
| **Title** | Past matches are visible under "Upcoming Football Matches" and bets can be placed on them |
| **Severity** | Critical                                                                                  |

**Steps to reproduce:**
1. Open the app — the top of the match list shows matches tagged "PAST" (Feb–May 2026)
2. Click an odds button on any PAST match (e.g. Man Utd vs Chelsea, Fri 27 Feb)
3. The match is added to the bet slip and the bet can be placed

**Expected result:** Only UPCOMING matches (spec: "Event Type: Upcoming/Pre-match events only"). PAST matches must not be displayed; their odds buttons must be non-interactive.

**Actual result:**
- The list opens with ~15 PAST matches (Feb–May 2026)
- Odds buttons on PAST matches are active and clickable
- A bet on a past match is accepted by the system
- The counter includes PAST matches in "Showing 103 matches"

---

### BUG-009 — Match counter does not update when filters are applied (MEDIUM)

| Field | Value                                                                |
|---|----------------------------------------------------------------------|
| **Bug ID** | BUG-009                                                              |
| **Title** | "Showing N matches" always displays 103 regardless of active filters |
| **Severity** | Medium                                                               |

**Steps to reproduce:**
- Odds filter MIN=5, MAX=2 → list empty, counter: "Showing 103 matches"
- Date filter 01/05/2026 → list empty, counter: "Showing 103 matches"
- Date range 01/05–30/05 → few matches shown, counter: "Showing 103 matches"


---

### BUG-010 — POST /api/reset-balance returns 125.50 but actually resets balance to 120.00 (HIGH)

| Field | Value                                                                          |
|---|--------------------------------------------------------------------------------|
| **Bug ID** | BUG-010                                                                        |
| **Title** | reset-balance response reports 125.50 but the persisted balance becomes 120.00 |
| **Severity** | High                                                                           |

**Detailed investigation:**

| Step | POST reset response | GET /api/balance | UI (no reload) | UI (after reload) |
|---|---|---|---|---|
| Before reset (after €15 bet) | — | 105.00 | €105.00 | — |
| After reset | **125.50** (in response) | **120.00** ❌ | **€105.00** ❌ | **€120.00** ❌ |

**Findings:**
1. Reset **partially works** — the balance does change (105 → 120)
2. However the response lies: it claims 125.50 but persists 120.00
3. UI does not update without a page reload (same pattern as BUG-005)
4. Spec states the initial balance is 125.50, but the actual server-side "initial value" is 120.00

**Business Impact:** Violates the spec ("Response body and persisted state must be consistent after reset"). The reset endpoint cannot be used for reproducible test scenarios.

---

### BUG-011 — Sunderland vs Watford match displays an incomplete date "Saturday" (MEDIUM)

| Field | Value                                                        |
|---|--------------------------------------------------------------|
| **Bug ID** | BUG-011                                                      |
| **Title** | Match date shown as "Saturday" without a day number or month |
| **Severity** | Medium                                                       |

**Expected:** "Sat 23 May" or a full date

**Actual:** "Saturday" — day of the week only, no date or month

All other matches display a full date (e.g. "Mon 01 Jun"). This is an isolated case of malformed data from the API.

---


