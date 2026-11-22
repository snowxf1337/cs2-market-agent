# Bug Log

Every bug found in the project is recorded here. Fixed bugs are never deleted:
their status is changed to **Fixed**.

## Template

```
## BUG-XXX — Short title

- **Status:** Open | Fixed
- **Found:** YYYY-MM-DD
- **Description:** what is wrong
- **Steps to reproduce:** how to trigger it
- **Expected:** what should happen
- **Actual:** what happens instead
- **Cause:** why it happens
- **Fix:** what was changed
- **Test:** tests/test_xxx.py::test_name
```

## Bugs

## BUG-001 — Skinport API rejects `tradable=0`

- **Status:** Fixed
- **Found:** 2026-11-21
- **Description:** Request to `/v1/items` with `tradable=0` returns HTTP 400.
- **Steps to reproduce:** `GET https://api.skinport.com/v1/items?app_id=730&currency=EUR&tradable=0`
- **Expected:** 200 with the item list (the docs example uses `tradable: 0`).
- **Actual:** 400 `validation_error`: "Only the following parameters are allowed: app_id, currency, tradable".
- **Cause:** The API expects a boolean value; the docs example is outdated. The error message is misleading.
- **Fix:** Omit `tradable` (it defaults to `false`).
- **Test:** will be covered by the Skinport provider tests (request parameters).

## BUG-002 — Deprecated DISTINCT ON syntax in snapshot repository

- **Status:** Fixed
- **Found:** 2026-11-22
- **Description:** `get_latest_states` used `.distinct(column)` to build `DISTINCT ON`.
- **Steps to reproduce:** run `python -m pytest` with SQLAlchemy 2.1.
- **Expected:** tests pass without warnings.
- **Actual:** 11 × `SADeprecationWarning`: passing an expression to `distinct` is deprecated.
- **Cause:** SQLAlchemy 2.1 moved `DISTINCT ON` to the PostgreSQL dialect extension.
- **Fix:** use `.ext(distinct_on(...))` from `sqlalchemy.dialects.postgresql`.
- **Test:** tests/test_repository.py (any test calling `save_snapshots`)