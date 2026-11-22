import logging
import random
import time
from collections.abc import Callable

logger = logging.getLogger(__name__)

INTERVAL_SECONDS = 330
JITTER_SECONDS = 30
RATE_LIMIT_PAUSE_SECONDS = 360


def next_delay(status: str, rng=random) -> float:
    base = RATE_LIMIT_PAUSE_SECONDS if status == "rate_limited" else INTERVAL_SECONDS
    return base + rng.uniform(0, JITTER_SECONDS)


def run_forever(
    collect: Callable[[], str],
    sleep: Callable[[float], None] = time.sleep,
    max_runs: int | None = None,
    rng=random,
) -> None:
    runs = 0
    while True:
        try:
            status = collect()
        except Exception:
            logger.exception("Collection run crashed")
            status = "crashed"

        runs += 1
        if max_runs is not None and runs >= max_runs:
            return

        delay = next_delay(status, rng)
        logger.info("Next run in %.0f seconds", delay)
        sleep(delay)