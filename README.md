# CS2 Market Agent

A Python agent for monitoring the Counter-Strike 2 skin market: it collects
price history from marketplaces, detects unusual market activity, and explains
the anomalies it finds.

> **Status:** early development. The features listed below are planned,
> not implemented yet.

## Planned features

- Price and listings history from marketplace APIs, stored in PostgreSQL
- Detection of sharp price changes, supply drops and unusual buying activity
- Confidence scoring for signals: an anomaly is not automatically manipulation
- AI-generated explanations of detected anomalies
- Telegram notifications

## Tech stack

Python 3.13, PostgreSQL, pytest. More tools are added only when needed.

## Getting started (Windows)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e . --group dev
copy .env.example .env
```

Then open `.env` and fill in your PostgreSQL credentials.

## Running tests

```powershell
python -m pytest
```

## Documentation

- [BUGS.md](BUGS.md): bug log