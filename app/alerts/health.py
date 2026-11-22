import logging
from collections.abc import Callable
from datetime import datetime, timedelta

from app.alerts.telegram import NotificationError
from app.analysis.window import MAX_RUN_GAP
from app.collectors.collector import utc_now

logger = logging.getLogger(__name__)

FAILURE_THRESHOLD = 3


class HealthMonitor:
    def __init__(
        self,
        notify: Callable[[str], None],
        failure_threshold: int = FAILURE_THRESHOLD,
        max_gap: timedelta = MAX_RUN_GAP,
        now: Callable[[], datetime] = utc_now,
    ) -> None:
        self._notify = notify
        self._failure_threshold = failure_threshold
        self._max_gap = max_gap
        self._now = now
        self._failures = 0
        self._alerted = False
        self._last_success: datetime | None = None

    def record(self, status: str) -> None:
        current = self._now()
        if status == "success":
            if self._alerted:
                self._send(f"Collection recovered after {self._failures} failed runs")
            elif self._last_success and current - self._last_success > self._max_gap:
                minutes = int((current - self._last_success).total_seconds() // 60)
                self._send(f"Collection resumed after a {minutes} min gap")
            self._failures = 0
            self._alerted = False
            self._last_success = current
            return

        self._failures += 1
        if self._failures >= self._failure_threshold and not self._alerted:
            self._send(
                f"Collection problem: {self._failures} failed runs in a row "
                f"(last status: {status})"
            )
            self._alerted = True

    def announce(self, text: str) -> None:
        self._send(text)

    def _send(self, text: str) -> None:
        try:
            self._notify(text)
        except NotificationError:
            logger.warning("Could not send Telegram notification")