# CS2 Market Agent

A Python agent that monitors the Counter-Strike 2 skin market, stores price history
in PostgreSQL and detects unusual market activity.

The goal is to surface **suspicious signals with an explanation**, not to label every
price rise as manipulation.

> Status: data collection and change analysis work on real data. Anomaly detection,
> AI explanations and Telegram alerts are planned.

## How it works

```
Skinport API -> Provider -> Watchlist filter -> PostgreSQL (change-only snapshots)
                                                    |
                                    Analysis: price / listing changes over a window
                                    + coverage check (gaps in collection)
```

- **Provider** fetches all CS2 items, validates them with Pydantic and converts prices
  to integer cents. New marketplaces plug in through the `MarketProvider` protocol.
- **Watchlist** keeps ~2,800 items worth watching: major team stickers, agents, cases
  and low-supply Factory New / Minimal Wear skins.
- **Collector** runs every ~5.5 minutes and saves a snapshot only when an item's
  price, listing count or currency changes. Every run is logged in `collection_runs`,
  so "nothing changed" can be told apart from "the agent was not running".
- **Analysis** compares the market state at the start and the end of a time window
  and reports collection gaps that make the comparison unreliable.

## Data source and limitations

- Data comes from the public [Skinport API](https://docs.skinport.com/) (`/v1/items`).
  It is rate limited (8 requests per 5 minutes) and cached for 5 minutes.
- Skinport reports the **lowest listing price**, not trade prices. On thin markets,
  one purchase can make the "price" jump sharply.
- CSFloat was considered but not used: its terms of service do not allow automated
  data extraction for this use case.
- Some early major stickers (Katowice 2014, DreamHack 2014) are not listed on Skinport.

## Tech stack

Python 3.13, PostgreSQL, SQLAlchemy 2, Alembic, Pydantic, httpx, pytest.

## Getting started (Windows)

Requirements: Python 3.13+, PostgreSQL, pip 25.1+.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e . --group dev
copy .env.example .env
```

Fill in `.env`, then create the role and two databases in PostgreSQL:
`cs2_market` (data) and `cs2_market_test` (tests), both owned by the role from `.env`.

```powershell
alembic upgrade head        # create tables
python -m pytest            # run tests
python -m app.main          # start the collector (Ctrl+C to stop)
python -m app.report --hours 1 --top 10   # price changes over the last hour
```

## Project structure

```
app/
  providers/   marketplace API clients
  collectors/  single collection run and scheduler
  database/    SQLAlchemy models and queries
  analysis/    change calculations, gap detection, window comparison
  watchlist.py which items are tracked
  report.py    command-line report
config/        watchlist.toml (tracked teams and items)
migrations/    Alembic migrations
tests/         pytest tests (API responses are mocked)
scripts/       one-off data exploration scripts
BUGS.md        bug log
```

## Roadmap

- [x] Skinport provider with error handling
- [x] Scheduled collection with change-only storage and run journal
- [x] Price and listing change analysis with coverage check
- [ ] Telegram notifications
- [ ] Anomaly detection with confidence scores
- [ ] AI analyst that explains detected anomalies
- [ ] Deployment to a server

## Disclaimer

This is a learning and research project. Signals it produces are not financial advice
and are not proof of market manipulation.