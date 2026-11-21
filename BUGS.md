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