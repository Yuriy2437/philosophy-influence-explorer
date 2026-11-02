"""Test execution budgets using controlled time without sleeping."""

from __future__ import annotations

import pytest

from philosophy_influence_explorer.time_budget import (
    ExecutionBudget,
    ExecutionBudgetExceededError,
)


class FakeClock:
    """Expose manually controlled monotonic time."""

    def __init__(self, now: float = 100.0) -> None:
        self.now = now

    def __call__(self) -> float:
        return self.now


@pytest.mark.parametrize(
    "value",
    [0, -1, float("inf"), float("-inf"), float("nan")],
)
def test_budget_rejects_invalid_timeout(value: float) -> None:
    with pytest.raises(
        ValueError,
        match="timeout_seconds must be positive and finite",
    ):
        ExecutionBudget(value)


def test_budget_reports_remaining_time() -> None:
    clock = FakeClock()
    budget = ExecutionBudget(10.0, clock=clock)

    assert budget.remaining_seconds() == pytest.approx(10.0)

    clock.now += 2.5

    assert budget.remaining_seconds() == pytest.approx(7.5)
    budget.check()


@pytest.mark.parametrize("elapsed", [10.0, 10.5])
def test_budget_expires_at_or_after_deadline(elapsed: float) -> None:
    clock = FakeClock()
    budget = ExecutionBudget(10.0, clock=clock)

    clock.now += elapsed

    with pytest.raises(ExecutionBudgetExceededError):
        budget.check()

    with pytest.raises(ExecutionBudgetExceededError):
        budget.remaining_seconds()


def test_checks_do_not_restart_budget() -> None:
    clock = FakeClock()
    budget = ExecutionBudget(10.0, clock=clock)

    clock.now += 6.0
    budget.check()

    clock.now += 4.0

    with pytest.raises(ExecutionBudgetExceededError):
        budget.check()


def test_budgets_have_independent_deadlines() -> None:
    clock = FakeClock()
    first = ExecutionBudget(5.0, clock=clock)

    clock.now += 3.0
    second = ExecutionBudget(5.0, clock=clock)

    clock.now += 2.0

    with pytest.raises(ExecutionBudgetExceededError):
        first.check()

    assert second.remaining_seconds() == pytest.approx(3.0)
