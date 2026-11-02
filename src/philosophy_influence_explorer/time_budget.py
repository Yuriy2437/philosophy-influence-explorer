"""Cooperative execution budget without background tasks or cancellation."""

from __future__ import annotations

import math
from collections.abc import Callable
from time import monotonic


class ExecutionBudgetExceededError(RuntimeError):
    """Raised when an operation's execution budget has expired."""


class ExecutionBudget:
    """Track one deadline and check it at explicit execution boundaries.

    This object does not interrupt an operation already in progress.
    """

    def __init__(
        self,
        timeout_seconds: float,
        *,
        clock: Callable[[], float] | None = None,
    ) -> None:
        if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive and finite.")

        self._clock = clock if clock is not None else monotonic
        self._deadline = self._clock() + timeout_seconds

    def remaining_seconds(self) -> float:
        """Return the remaining budget or raise if the deadline is reached."""
        remaining = self._deadline - self._clock()

        if remaining <= 0:
            raise ExecutionBudgetExceededError(
                "Execution time budget exceeded."
            )

        return remaining

    def check(self) -> None:
        """Raise if no execution time remains."""
        self.remaining_seconds()
