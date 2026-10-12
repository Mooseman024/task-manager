# Task 1: Plan Mode Supervision Log

Feature: optional `priority` field on tasks (integer 1-5, default 3), accepted on
POST /tasks and PATCH /tasks/{id}, returned in all task responses, filterable with
GET /tasks?priority={n}.

| Session # | Prompt summary (≤15 words) | Did you amend the plan? | What you changed | Did output match amended plan? |
|---|---|---|---|---|
| 1 | | Yes / No | | Yes / Partially / No |
| 2 | | Yes / No | | Yes / Partially / No |
| 3 | | Yes / No | | Yes / Partially / No |
| 4 | | Yes / No | | Yes / Partially / No |
