import logging
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.collectors.collector import run_once
from app.collectors.scheduler import run_forever
from app.config import Settings
from app.providers.skinport import SkinportProvider, create_client
from app.watchlist import load_watchlist

logger = logging.getLogger(__name__)

WATCHLIST_PATH = Path("config/watchlist.toml")


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    engine = create_engine(Settings().database_url())
    session_factory = sessionmaker(engine)
    watchlist = load_watchlist(WATCHLIST_PATH)
    provider = SkinportProvider(create_client())

    def collect() -> str:
        with session_factory() as session:
            try:
                run = run_once(session, provider, watchlist)
            except Exception:
                session.rollback()
                raise
            logger.info(
                "Run finished: status=%s seen=%s tracked=%s skipped=%s written=%s error=%s",
                run.status,
                run.items_seen,
                run.items_tracked,
                run.items_skipped,
                run.snapshots_written,
                run.error,
            )
            return run.status

    logger.info("Collector started: %d teams in watchlist", len(watchlist.teams))
    try:
        run_forever(collect)
    except KeyboardInterrupt:
        logger.info("Collector stopped by user")


if __name__ == "__main__":
    main()