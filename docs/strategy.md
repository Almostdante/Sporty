# Strategy & Recommendations

**Feature:** Single Bet Placement  
**Author:** QA Engineer

---

## 1. Why These 2 Tests Were Selected for Automation

### Test 1 — E2E UI: Successful Single Bet Placement

**Selected because:** This is the single revenue-critical user journey. Every other feature (filters, error modals, balance display) exists to support this one flow. If it regresses, the product stops generating revenue.

**What it verifies that manual testing cannot do efficiently:**
- **Financial accuracy at scale** — payout = stake × odds must hold on every deployment, for every odds value returned by the API
- **Receipt completeness** — all seven required receipt fields (Bet ID, match, selection, stake, odds, payout, timestamp) must be present simultaneously
- **Balance deduction** — cross-referencing UI state with API-reported balance requires switching between browser and API; automation does this atomically

**Why it is a good automation candidate:** Deterministic (balance reset before each run), clear binary pass/fail, high change-detection value.

---

### Test 2 — API: Stake Validation & Business Rule Enforcement

**Selected because:** Stake boundaries and authentication enforcement are the primary financial and security guardrails. Testing at API level — bypassing the UI — verifies that the server is the authoritative enforcement layer.

**What it verifies that UI testing cannot:**
- **Backend-level enforcement** — a determined user or buggy client can bypass UI validation; API must enforce independently
- **Correct HTTP semantics** — status codes (401, 400, 405, 422) are part of the API contract; incorrect codes break integrations silently
- **Balance integrity as an invariant** — the `balance` field in place-bet response and in `/api/balance` must agree; cross-endpoint consistency is impossible to check cleanly via UI

**Why it is a good automation candidate:** Parameterised (10+ boundary cases, zero code duplication), extremely fast (no browser), ideal for CI on every commit.

---

## 2. What Was Intentionally Left as Manual-Only

### Error Modal — Failure Recovery (TC-04)

**Left manual because:** Reliably triggering a 500 or 409 response requires either network interception (fragile) or a dedicated test-error endpoint (doesn't exist). Manual execution with DevTools throttling is faster and more representative.

### Bet Slip State Management (TC-05)

**Left manual because:** Value here is in verifying visual state and UI transitions. The E2E happy-path test already implicitly validates correct slip state — if selection replacement were broken, the wrong match would appear in the receipt and fail TC-01.

### Odds Filter Validation (TC-06)

**Left manual because:** "Clear feedback" is a UX judgement that a human evaluates better than an element visibility assertion. Selector-fragile filter automation has high maintenance cost relative to its risk level.

### Exploratory Testing

**Always manual by definition.** 

## 3. Recommendations for Scale

### Recommendation 1 — CI/CD Pipeline with Layered Execution

```
Pull Request opened
  └── API tests only (~5s, no browser)
        └── PASS → merge allowed

Merge to main
  └── Full suite: API + E2E UI headless (~2 min)
        └── PASS → deploy to staging

Deploy to staging
  └── Smoke test against live environment (~30s)
        └── PASS → deploy to production
```

Fast feedback at each stage. API tests catch backend regressions before wasting CI time on browser automation. Tools: GitHub Actions, pytest-xdist for parallelism, Allure for historical trend reporting.

---

### Recommendation 2 — Test Data Strategy

**Current problem:** Tests depend on `POST /api/reset-balance`, which is broken (BUG-010 — returns 125.50 but persists 120.00). This makes test isolation unreliable.

**Recommended approach:**
1. **Contract with API team** — agree that any `user-id` starting with `test-` is treated as a test account with predictable initial state.
2. **Fix reset endpoint** — align response value with actual persisted value (fix BUG-010 first).

---

### Recommendation 3 — Spec Clarifications Required

Three ambiguities currently make fully deterministic tests impossible:

**A — Minimum stake: €1.00 or €1.01?**
Section 3 (Business Rules) says €1.00. Section 4.1 (Validation Rules) says €1.01. UI error copy says €1.00. API accepts €1.00. A product owner decision is needed to align all three.

**B — Receipt timestamp format and timezone**
Spec requires "Placement timestamp" but doesn't specify format or timezone. Recommend: ISO 8601 UTC (`2026-05-19T13:13:00Z`).

**C — Odds filter feedback copy**
Spec says "clear feedback" for invalid ranges but doesn't define the message or placement. Should be added to spec section 4.4 alongside stake error messages.

**D — PAST matches in the list**
Spec says "upcoming matches only" but the API returns PAST matches and the UI displays them with active odds buttons. Either the API needs a server-side filter, or the UI needs to hide/disable PAST entries. Needs explicit acceptance criteria.
