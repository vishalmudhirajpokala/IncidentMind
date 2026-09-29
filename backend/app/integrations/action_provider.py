"""Simulated action provider.

SAFETY CONTRACT
  * There is no method anywhere in this codebase that executes a real
    infrastructure change. No shell, no kubectl, no SSH, no cloud SDK.
  * Every action requires explicit human approval before it will even be
    simulated.
  * Telemetry is computed deterministically from the incident context, so the
    same incident and action always produce the same numbers.

The outcome is not random: it is derived from whether the action type actually
addresses the failure shape that was diagnosed. That makes the demo meaningful
- approving the right remedy recovers the service, approving an unrelated one
does not.
"""

from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Optional

from app.integrations.base import ActionOutcome, ActionProvider
from app.schemas.memory import ProviderStatus
from app.utils.logging import get_logger

log = get_logger("integrations.actions")

# Fraction of the error-rate EXCESS that each action type removes, when the
# approved action is the one the investigation recommended. The excess is
# measured against the healthy baseline, so "removed 94% of the excess" is a
# concrete, checkable statement rather than a vibe.
_ADDRESSING_EFFECT: Dict[str, float] = {
    "rollback": 0.94,
    "connection_pool": 0.93,
    "config_change": 0.75,
    "traffic_shift": 0.72,
    "restart": 0.70,
    "scale": 0.62,
    "investigate": 0.15,
}

# When the approved action is NOT the recommended one, recovery is partial.
_MISALIGNED_EFFECT: Dict[str, float] = {
    "rollback": 0.35,
    "connection_pool": 0.30,
    "restart": 0.28,
    "scale": 0.25,
    "config_change": 0.22,
    "traffic_shift": 0.30,
    "investigate": 0.10,
}

# An action counts as having recovered the service when it removed at least
# this fraction of the error-rate excess.
_RECOVERY_THRESHOLD = 0.90

# Realistic in-flight durations, in seconds.
_DURATION: Dict[str, float] = {
    "rollback": 142.0,
    "connection_pool": 38.0,
    "restart": 47.0,
    "scale": 215.0,
    "config_change": 64.0,
    "traffic_shift": 88.0,
    "investigate": 300.0,
}

# Healthy baselines the simulated recovery converges toward.
_BASELINE_ERROR_RATE = 0.4
_BASELINE_P99_MS = 180.0


def _stable_fraction(seed: str) -> float:
    """Deterministic 0.85-1.0 multiplier from a seed string."""
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return 0.85 + (int(digest[:8], 16) % 150) / 1000.0


def _round(value: float, places: int = 2) -> float:
    return round(value, places)


class SimulatedActionProvider(ActionProvider):
    """Produces deterministic simulated telemetry for an approved action."""

    name = "simulated"

    def is_configured(self) -> bool:
        return True

    def execute_simulated(
        self,
        *,
        incident_id: str,
        action: str,
        action_type: str,
        context: Dict[str, Any],
    ) -> ActionOutcome:
        metrics: Dict[str, Any] = context.get("metrics") or {}
        diagnosed_type: Optional[str] = context.get("diagnosed_action_type")

        # --- "before" comes from the incident's own recorded metrics --------
        before_error = _as_float(metrics.get("error_rate"), default=18.4)
        before_p99 = _as_float(metrics.get("p99_latency_ms"), default=2400.0)

        action_type = action_type if action_type in _ADDRESSING_EFFECT else "investigate"

        # --- was the approved action the one the agent recommended? --------
        if diagnosed_type and diagnosed_type == action_type:
            effect = _ADDRESSING_EFFECT[action_type]
            aligned = True
        else:
            effect = _MISALIGNED_EFFECT[action_type]
            aligned = False

        after_error = before_error + (_BASELINE_ERROR_RATE - before_error) * effect
        after_p99 = before_p99 + (_BASELINE_P99_MS - before_p99) * effect

        telemetry: List[Dict[str, Any]] = [
            {
                "metric": "error_rate",
                "before": _round(before_error),
                "after": _round(after_error),
                "unit": "percent",
            },
            {
                "metric": "p99_latency_ms",
                "before": _round(before_p99, 1),
                "after": _round(after_p99, 1),
                "unit": "ms",
            },
        ]

        # "Recovered" means the excess error rate was removed, not that a number
        # happened to fall. The threshold is explicit and deterministic.
        excess = before_error - _BASELINE_ERROR_RATE
        removed = (before_error - after_error) / excess if excess > 0 else 1.0
        recovered = removed >= _RECOVERY_THRESHOLD

        duration = _DURATION.get(action_type, 60.0)
        duration = _round(duration * _stable_fraction(f"{incident_id}:{action_type}:dur"), 1)

        if recovered:
            message = (
                f"Simulated {action_type} recovered the service: the error-rate excess above "
                f"the {_BASELINE_ERROR_RATE}% baseline fell by "
                f"{round(removed * 100)}% (error rate {telemetry[0]['before']}% -> "
                f"{telemetry[0]['after']}%)."
            )
        else:
            message = (
                f"Simulated {action_type} removed only {round(removed * 100)}% of the "
                f"error-rate excess (error rate {telemetry[0]['before']}% -> "
                f"{telemetry[0]['after']}%). "
                "This action did not address the diagnosed failure."
            )

        log.info(
            "simulated action",
            extra={
                "event_incident_id": incident_id,
                "event_action_type": action_type,
                "event_recovered": recovered,
                "event_aligned": aligned,
            },
        )

        return ActionOutcome(
            success=recovered,
            action_type=action_type,
            message=message,
            duration_seconds=duration,
            telemetry=telemetry,
        )

    def health(self) -> ProviderStatus:
        return ProviderStatus(
            name=self.name,
            mode="demo",
            available=True,
            detail="simulated action layer; no real execution path exists",
        )


def _as_float(value: Any, default: float) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default
