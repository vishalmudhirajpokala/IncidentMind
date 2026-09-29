"""The action vocabulary.

Both the analyst (which proposes an action) and the action layer (which
simulates an approved one) must agree on what kind of action a piece of text
describes. Keeping the mapping here means the two can never drift apart and
produce a "simulated rollback" for something the analyst called a scale-out.

Reminders retrieved from memory are written as past-tense prose ("Rolled back
checkout-api from v2.8.1 to v2.8.0"), so past-tense phrasings are recognised.
"""

from __future__ import annotations

import re

ACTION_TYPES = (
    "rollback",
    "connection_pool",
    "restart",
    "scale",
    "config_change",
    "traffic_shift",
    "investigate",
)

_VERSION_RE = re.compile(r"v?\d+\.\d+(?:\.\d+)?")

_VERB_MARKERS: tuple[tuple[tuple[str, ...], str], ...] = (
    (("rollback", "roll back", "rolled back", "roll-back", "revert", "reverted"), "rollback"),
    (("restart", "restarted"), "restart"),
    (("scale", "scaled", "capacity", "resource", "replica", "larger pool", "horizontal"), "scale"),
    (("pool", "connection", "connections"), "connection_pool"),
    (("config", "flag", "feature toggle"), "config_change"),
    (("traffic", "failover", "shift"), "traffic_shift"),
)

# Leading past-tense verb -> imperative form.
PAST_TO_PRESENT: dict[str, str] = {
    "rolled back": "Roll back",
    "increased": "Increase",
    "decreased": "Decrease",
    "raised": "Raise",
    "fixed": "Fix",
    "re-enabled": "Re-enable",
    "restarted": "Restart",
    "scaled": "Scale",
    "shifted": "Shift",
    "updated": "Update",
    "added": "Add",
    "removed": "Remove",
    "enabled": "Enable",
    "disabled": "Disable",
    "configured": "Configure",
    "applied": "Apply",
    "drained": "Drain",
    "cleared": "Clear",
    "warmed": "Warm",
}


def classify_action(action_text: str) -> str:
    """Return one of ``ACTION_TYPES`` for a piece of action text."""
    lowered = (action_text or "").lower()
    for markers, action_type in _VERB_MARKERS:
        if any(marker in lowered for marker in markers):
            return action_type
    return "investigate"


def to_present_tense(action_text: str) -> str:
    """Rewrite a leading past-tense verb into its imperative form."""
    text = (action_text or "").strip()
    if not text:
        return text
    lowered = text.lower()
    for past, present in PAST_TO_PRESENT.items():
        if lowered.startswith(past):
            return present + text[len(past) :]
    return text


def extract_target_version(action_text: str) -> str | None:
    """Pull the 'known-good' version out of a historical remedy.

    ``"Rolled back checkout-api from v2.8.1 to v2.8.0"`` -> ``"v2.8.0"``.
    Falls back to the last version mentioned when there is no "to" marker.
    """
    lowered = (action_text or "").lower()
    for marker in (" to ", "->", "→"):
        if marker in lowered:
            match = _VERSION_RE.search(lowered.split(marker)[-1])
            if match:
                return match.group(0)
    versions = _VERSION_RE.findall(action_text or "")
    return versions[-1] if len(versions) > 1 else None
