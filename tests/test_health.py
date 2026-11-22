from datetime import UTC, datetime, timedelta

from app.alerts.health import HealthMonitor
from app.alerts.telegram import NotificationError

START = datetime(2026, 11, 22, 12, 0, tzinfo=UTC)


class Clock:
    def __init__(self):
        self.current = START

    def __call__(self):
        return self.current

    def advance(self, minutes):
        self.current += timedelta(minutes=minutes)


def make_monitor():
    sent = []
    clock = Clock()
    return HealthMonitor(sent.append, now=clock), sent, clock


def test_no_messages_while_runs_succeed():
    monitor, sent, clock = make_monitor()
    for _ in range(5):
        monitor.record("success")
        clock.advance(6)
    assert sent == []


def test_short_failure_streak_is_silent():
    monitor, sent, _ = make_monitor()
    for status in ["failed", "rate_limited", "success"]:
        monitor.record(status)
    assert sent == []


def test_alert_is_sent_once_after_three_failures():
    monitor, sent, _ = make_monitor()
    for status in ["failed", "rate_limited", "failed", "failed", "crashed"]:
        monitor.record(status)
    assert len(sent) == 1
    assert "3 failed runs in a row" in sent[0]


def test_recovery_message_after_alert():
    monitor, sent, _ = make_monitor()
    for _ in range(3):
        monitor.record("failed")
    monitor.record("success")
    assert len(sent) == 2
    assert "recovered" in sent[1]


def test_gap_between_successes_is_reported():
    monitor, sent, clock = make_monitor()
    monitor.record("success")
    clock.advance(194)
    monitor.record("success")
    assert sent == ["Collection resumed after a 194 min gap"]


def test_notification_error_does_not_break_collection():
    def broken_notify(text):
        raise NotificationError("Telegram is down")

    monitor = HealthMonitor(broken_notify)
    for _ in range(3):
        monitor.record("failed")