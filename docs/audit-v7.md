# SAATH v7 Audit Report — "Make It True, Then Make It Smart"

## 1. Endpoint Usage Matrix

| Backend Route (`api/saath/api/main.py`) | Frontend Call Site (`web/src`) | Status | Action Needed |
| :--- | :--- | :--- | :--- |
| `GET /healthz` | `lib/api.ts` (`getHealthz`) | Used | Keep |
| `GET /readyz` | `routes/PrivacyFeature.tsx` | Unused in UI | Add to Local Proof panel |
| `GET /metrics` | None | Unused in UI | Add to Local Proof panel |
| `GET /api/v1/house/members` | `lib/api.ts` (`getMembers`) | Used | Keep |
| `POST /api/v1/messages` | `lib/api.ts` (`sendMessage`) | Used | Keep |
| `POST /api/v1/messages/voice` | `components/ui/MicOrb.tsx` (`/api/v1/voice/ingest`) | **Mismatched Path** | Fix MicOrb path to `/api/v1/messages/voice` |
| `GET /api/v1/attention` | `lib/api.ts` (`getAttention`) | Used | Keep |
| `GET /api/v1/commitments/{id}` | None | Unused in UI | Wire to ThreadDetail route loader |
| `POST /api/v1/commitments/{id}/done` | None | Unused in UI | Wire to Done button |
| `POST /api/v1/commitments/{id}/snooze` | None | Unused in UI | Wire to Snooze button |
| `POST /api/v1/commitments/{id}/reschedule` | None | Unused in UI | Wire to Reschedule date picker |
| `POST /api/v1/commitments/{id}/followup` | `lib/api.ts` (`draftFollowup`) | Used | Keep |
| `POST /api/v1/followups/{id}/opened` | None | Unused in UI | Wire to WhatsApp click handler |
| `POST /api/v1/followups/{id}/sent` | `lib/api.ts` (`markFollowupSent`) | Used | Keep |
| `POST /api/v1/events/confirm` | `lib/api.ts` (`confirmExpense`) | Used (via alias) | Canonicalize route |
| `POST /api/v1/events/{id}/undo` | `lib/api.ts` (`undoEvent`) | Used | Keep |
| `GET /api/v1/reflection` | `lib/api.ts` (`getReflection`) | Used | Keep |
| `GET /api/v1/history` | `lib/api.ts` (`getHistory`) | Used | Keep |
| `POST /api/v1/sync/outbox` | `lib/outbox.ts` | Unused in UI | Enqueue & flush IndexedDB outbox |
| `POST /api/v1/demo/clock/advance` | `lib/api.ts` (`advanceDemoClock`) | Used | Protect with `SAATH_DEMO=1` |
| `POST /api/v1/demo/seed` | None | Unused in UI | Add to Lab UI under `SAATH_DEMO=1` |
| *(None)* | `lib/api.ts` (`getExpenses` -> `GET /api/v1/expenses`) | **Non-existent Route** | Add `GET /api/v1/expenses` endpoint |

---

## 2. Dead Code & Duplicate Files

| File Path | Import Graph Analysis | Status | Action |
| :--- | :--- | :--- | :--- |
| `web/src/api.ts` | Duplicate of `lib/api.ts` | Unused | Delete |
| `web/src/outbox.ts` | Duplicate of `lib/outbox.ts` | Unused | Delete |
| `web/src/index.css` | Replaced by `design/tokens.css` | Unused | Delete |
| `web/src/components/AttentionPanel.tsx` | Legacy v3 component | Unused | Delete |
| `web/src/components/ConfirmationModal.tsx` | Legacy v3 component | Unused | Delete |
| `web/src/components/ErrorBanner.tsx` | Legacy v3 component | Unused | Delete |
| `web/src/components/ErrorModal.tsx` | Legacy v3 component | Unused | Delete |
| `web/src/components/HistoryTimeline.tsx` | Legacy v3 component | Unused | Delete |
| `web/src/components/OnboardingModal.tsx` | Legacy v3 component | Unused | Delete |
| `web/src/components/Toast.tsx` | Legacy v3 component | Unused | Delete |
| `web/src/components/UnderstandingCard.tsx` | Legacy v3 component | Unused | Delete |
| `web/src/components/UniversalComposer.tsx` | Legacy v3 component | Unused | Delete |

---

## 3. Interactive Control Audit (`web/src/routes/*`)

| Component / File | Control Element | Handler Status | Resolution |
| :--- | :--- | :--- | :--- |
| `routes/ThreadDetail.tsx` | Reply chips ("Nahi aaya", "Kal aayega", "Aa gaya", "Cancel") | `<span>` with NO handler | Add `POST /api/v1/commitments/{id}/reply` endpoint & click handler |
| `routes/TodayFeature.tsx` | DiyaCard actions | Only "Send check-in" wired | Add "Mark done" and "Snooze" action buttons |
| `components/ui/MicOrb.tsx` | Mic button | Posts to wrong URL `/api/v1/voice/ingest` | Fix URL to `/api/v1/messages/voice`, remove hardcoded `m-1` |
| `routes/PrivacyFeature.tsx` | "Process Outbox Sync" button | Calls mock outbox | Wire to real IndexedDB outbox & `/api/v1/sync/outbox` |
| `routes/LabFeature.tsx` | Clock Advance buttons | Calls `advanceDemoClock` | Protect with `SAATH_DEMO=1`, wire `/demo/seed` |

---

## 4. Baseline Metrics

- **Unit Tests**: 2 passing (`src/design/tokens.test.ts`)
- **Integration Tests**: 1 passing (`tests/integration/test_persistence_proven.py`)
- **Eval Benchmark**: 60 rules test cases passing (`evals/evaluate.py`)
- **Bundle Sizes (gz)**:
  - App Shell: `110.26 KB`
  - Critical CSS: `1.35 KB`
  - Total JS dist: `498.37 KB`
