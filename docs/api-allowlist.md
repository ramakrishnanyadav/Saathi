# SAATH API Allowlist & Usage Contract

Every FastAPI backend endpoint in `api/saath/api/main.py` is explicitly documented below.

| Route | Method | Called By | Allowed / Contract Status |
| :--- | :--- | :--- | :--- |
| `/healthz` | GET | `lib/api.ts` (`getHealthz`) | Allowed |
| `/readyz` | GET | `routes/PrivacyFeature.tsx` | Allowed |
| `/metrics` | GET | `routes/PrivacyFeature.tsx` | Allowed |
| `/api/v1/house/members` | GET | `lib/api.ts` (`getMembers`) | Allowed |
| `/api/v1/messages` | POST | `lib/api.ts` (`sendMessage`) | Allowed |
| `/api/v1/messages/voice` | POST | `components/ui/MicOrb.tsx` | Allowed |
| `/api/v1/attention` | GET | `lib/api.ts` (`getAttention`) | Allowed |
| `/api/v1/commitments/{id}` | GET | `routes/ThreadDetail.tsx` | Allowed |
| `/api/v1/commitments/{id}/done` | POST | `lib/api.ts` (`markCommitmentDone`) | Allowed |
| `/api/v1/commitments/{id}/snooze` | POST | `lib/api.ts` (`snoozeCommitment`) | Allowed |
| `/api/v1/commitments/{id}/reschedule` | POST | `lib/api.ts` (`rescheduleCommitment`) | Allowed |
| `/api/v1/commitments/{id}/reply` | POST | `routes/ThreadDetail.tsx` | Allowed |
| `/api/v1/commitments/{id}/followup` | POST | `lib/api.ts` (`draftFollowup`) | Allowed |
| `/api/v1/followups/{id}/opened` | POST | `routes/ThreadDetail.tsx` | Allowed |
| `/api/v1/followups/{id}/sent` | POST | `lib/api.ts` (`markFollowupSent`) | Allowed |
| `/api/v1/events/confirm` | POST | `lib/api.ts` (`confirmExpense`) | Allowed |
| `/api/v1/events/{id}/undo` | POST | `lib/api.ts` (`undoEvent`) | Allowed |
| `/api/v1/reflection` | GET | `lib/api.ts` (`getReflection`) | Allowed |
| `/api/v1/history` | GET | `lib/api.ts` (`getHistory`) | Allowed |
| `/api/v1/expenses` | GET | `lib/api.ts` (`getExpenses`) | Allowed |
| `/api/v1/sync/outbox` | POST | `lib/outbox.ts` | Allowed |
| `/api/v1/demo/clock/advance` | POST | `lib/api.ts` (`advanceDemoClock`) | Allowed (Demo Only) |
| `/api/v1/demo/seed` | POST | `routes/LabFeature.tsx` | Allowed (Demo Only) |
