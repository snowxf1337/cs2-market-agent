from app.collectors.scheduler import next_delay, run_forever


class MaxJitter:
    def uniform(self, low, high):
        return high


def test_next_delay_after_success_uses_normal_interval():
    assert next_delay("success", MaxJitter()) == 360


def test_next_delay_after_rate_limit_waits_longer_than_block_window():
    assert next_delay("rate_limited", MaxJitter()) == 390


def test_run_forever_sleeps_between_runs_and_stops():
    statuses = iter(["success", "rate_limited", "success"])
    sleeps = []

    run_forever(lambda: next(statuses), sleep=sleeps.append, max_runs=3, rng=MaxJitter())

    assert sleeps == [360, 390]


def test_run_forever_survives_crashed_run():
    calls = []

    def collect():
        calls.append(1)
        if len(calls) == 1:
            raise RuntimeError("database is down")
        return "success"

    sleeps = []
    run_forever(collect, sleep=sleeps.append, max_runs=2, rng=MaxJitter())

    assert len(calls) == 2
    assert sleeps == [360]