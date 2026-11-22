import logging
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.alerts.health import HealthMonitor
from app.alerts.telegram import create_notifier
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
    logging.getLogger("httpx").setLevel(logging.WARNING)
    settings = Settings()
    engine = create_engine(settings.database_url())
    session_factory = sessionmaker(engine)
    watchlist = load_watchlist(WATCHLIST_PATH)
    provider = SkinportProvider(create_client())
    notifier = create_notifier(settings)
    if notifier is None:
        logger.info("Telegram is not configured: alerts are disabled")
        monitor = HealthMonitor(lambda text: None)
    else:
        monitor = HealthMonitor(notifier.send)

    def collect() -> str:
        with session_factory() as session:
            try:
                run = run_once(session, provider, watchlist)
            except Exception:
                session.rollback()
                monitor.record("crashed")
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
            monitor.record(run.status)
            return run.status

    logger.info("Collector started: %d teams in watchlist", len(watchlist.teams))
    monitor.announce(f"Collector started: {len(watchlist.teams)} teams in watchlist")
    try:
        run_forever(collect)
    except KeyboardInterrupt:
        logger.info("Collector stopped by user")


if __name__ == "__main__":
    main()