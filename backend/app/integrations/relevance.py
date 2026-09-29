"""Deterministic local relevance scoring.

This exists because Hindsight's recall API does not return a similarity score.
Rather than fabricate one, IncidentMind computes its own transparent lexical
relevance and labels the result ``local_lexical_overlap``. The same function
scores locally mirrored memories and locally ranked Hindsight results, so both
paths are comparable.

The scoring is intentionally simple and auditable: it is keyword overlap with
weighted bonuses for service identity and failure-pattern similarity. It is not
a semantic model and does not claim to be one.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Set

STOPWORDS: Set[str] = {
    "a", "an", "and", "are", "as", "at", "be", "been", "but", "by", "for", "from",
    "has", "have", "in", "into", "is", "it", "its", "of", "on", "or", "that", "the",
    "their", "then", "there", "these", "this", "to", "was", "were", "when", "which",
    "with", "after", "before", "during", "since", "while", "about", "over", "under",
}

# Filler words that are not stopwords but explain nothing when quoted back to a
# human. They still count towards the score; they are just never used to justify
# a match, because "shared symptoms (every)" reads as noise.
_EXPLANATION_NOISE: Set[str] = {
    "all", "also", "already", "another", "around", "because", "been", "being", "both",
    "each", "either", "every", "everyone", "far", "few", "get", "got", "just", "keep",
    "kept", "like", "made", "make", "many", "more", "most", "much", "must", "near",
    "need", "never", "new", "none", "only", "other", "others", "own", "part", "per",
    "put", "rather", "really", "same", "seem", "seems", "several", "shall", "should",
    "since", "still", "such", "sure", "take", "taken", "tell", "thing", "things",
    "tried", "trying", "use", "used", "using", "very", "want", "way", "well", "went",
    "whether", "whole", "within", "without", "yet", "your",
    # elapsed-time and quantity units: two incidents always share these
    "minute", "minutes", "second", "seconds", "hour", "hours", "day", "days",
    "week", "weeks", "month", "months", "year", "years", "time", "times", "ms",
    "sec", "secs", "percent", "one", "two", "three", "ten",
}

# Terms that describe a *failure shape* rather than a service identity. Two
# incidents affecting different services can still share these.
FAILURE_PATTERN_TERMS: Set[str] = {
    # error classes
    "503", "502", "504", "500", "429", "timeout", "timeouts", "error", "errors",
    "failure", "failures", "crash", "crashes", "panic", "oom", "leak", "deadlock",
    # saturation / pressure
    "saturation", "saturated", "exhausted", "exhaustion", "pool", "backlog",
    "queue", "queues", "throttle", "throttling", "overload", "contention", "lock",
    # latency
    "latency", "slow", "degraded", "timeout", "p99", "p95", "tail",
    # availability / data
    "availability", "replication", "replica", "failover", "shard", "partition",
    "corrupt", "corruption", "disk", "cpu", "memory", "connection", "connections",
}

_TOKEN_RE = re.compile(r"[a-z0-9]+(?:\.[0-9]+)?")
_VERSION_RE = re.compile(r"v?(\d+)\.(\d+)(?:\.(\d+))?")


def tokenize(text: Optional[str]) -> Set[str]:
    """Lowercase word/number tokens with stopwords removed."""
    if not text:
        return set()
    return {
        t
        for t in _TOKEN_RE.findall(text.lower())
        if t not in STOPWORDS and len(t) > 1
    }


def version_family(version: Optional[str]) -> Optional[str]:
    """Extract the ``major.minor`` family of a version string.

    ``v2.8.3`` -> ``2.8``. Used to notice that two different builds belong to
    the same release line.
    """
    if not version:
        return None
    match = _VERSION_RE.search(version)
    if not match:
        return None
    return f"{match.group(1)}.{match.group(2)}"


@dataclass
class QueryProfile:
    """The salient features of the incident being investigated."""

    service: str = ""
    symptom_tokens: Set[str] = field(default_factory=set)
    pattern_tokens: Set[str] = field(default_factory=set)
    version_family: Optional[str] = None
    all_tokens: Set[str] = field(default_factory=set)

    @classmethod
    def from_incident(cls, incident: Dict[str, Any]) -> "QueryProfile":
        symptom_text = " ".join(
            filter(
                None,
                [
                    incident.get("description") or "",
                    incident.get("title") or "",
                    " ".join(incident.get("signals") or []),
                    " ".join(str(v) for v in (incident.get("metrics") or {}).values()),
                ],
            )
        )
        tokens = tokenize(symptom_text)
        return cls(
            service=(incident.get("service") or "").strip().lower(),
            symptom_tokens=tokens,
            pattern_tokens=tokens & FAILURE_PATTERN_TERMS,
            version_family=version_family(incident.get("deployment_version")),
            all_tokens=tokens,
        )


# Weights for the local lexical score. Sum of maximums is 1.0.
_W_SERVICE = 0.40
_W_SYMPTOM = 0.30
_W_PATTERN = 0.25
_W_VERSION = 0.05


@dataclass
class RelevanceResult:
    score: float
    matched_on: List[str] = field(default_factory=list)

    @property
    def method(self) -> str:
        return "local_lexical_overlap"


def _overlap_ratio(a: Set[str], b: Set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a)


def _is_readable(token: str) -> bool:
    """Terms worth quoting in a human explanation.

    A bare number matches across unrelated incidents by coincidence, and filler
    words match almost always, so both still contribute to the score but are
    never used to explain a match.
    """
    return (
        len(token) >= 3
        and not any(ch.isdigit() for ch in token)
        and token not in _EXPLANATION_NOISE
    )


def _explain_terms(tokens: Set[str], limit: int = 5) -> List[str]:
    """Pick the terms to quote, most diagnostic first.

    Longer words are the more specific ones ("connections" over "api"), so they
    lead. This only affects the wording of the explanation, never the score.
    """
    readable = sorted((t for t in tokens if _is_readable(t)), key=lambda t: (-len(t), t))
    return readable[:limit]


def score_relevance(
    profile: QueryProfile, document: Dict[str, Any]
) -> RelevanceResult:
    """Score how relevant a stored experience is to the current incident.

    ``document`` may expose any of: service, title, symptoms, root_cause,
    action_taken, outcome, lesson, content, deployment_version.
    """
    matched: List[str] = []
    score = 0.0

    # --- 1. service identity --------------------------------------------
    doc_service = (document.get("service") or "").strip().lower()
    if profile.service and doc_service and profile.service == doc_service:
        score += _W_SERVICE
        matched.append(f"the same service ({profile.service})")

    # --- 2. symptom / description overlap --------------------------------
    doc_tokens: Set[str] = set()
    for key in ("symptoms", "description", "title", "content", "lesson"):
        doc_tokens |= tokenize(document.get(key))
    for key in ("root_cause", "action_taken", "outcome"):
        doc_tokens |= tokenize(document.get(key))

    symptom_overlap = _overlap_ratio(profile.symptom_tokens, doc_tokens)
    if symptom_overlap > 0:
        score += _W_SYMPTOM * symptom_overlap
        shared = _explain_terms(profile.symptom_tokens & doc_tokens)
        matched.append(
            f"shared symptoms ({', '.join(shared)})" if shared else "shared symptoms"
        )

    # --- 3. failure-pattern similarity ------------------------------------
    doc_patterns = doc_tokens & FAILURE_PATTERN_TERMS
    pattern_overlap = _overlap_ratio(profile.pattern_tokens, doc_patterns)
    if pattern_overlap > 0:
        score += _W_PATTERN * pattern_overlap
        shared = _explain_terms(profile.pattern_tokens & doc_patterns)
        matched.append(f"same failure pattern ({', '.join(shared)})")

    # --- 4. release-line proximity ---------------------------------------
    doc_version = version_family(document.get("deployment_version"))
    if profile.version_family and doc_version and profile.version_family == doc_version:
        score += _W_VERSION
        matched.append(f"same release line {profile.version_family}.x")

    return RelevanceResult(score=round(min(score, 1.0), 4), matched_on=matched)


def explain(matched_on: Iterable[str]) -> str:
    """Human-readable one-liner explaining why a memory was retrieved.

    The matched fragments are already noun phrases, so the first one is given
    the connecting words and the rest are simply listed. Keeping this as a
    sentence means it can be shown to a human unedited.
    """
    items = [i.rstrip(".") for i in matched_on if i]
    if not items:
        return "Retrieved as a candidate; no strong signal overlap with the current incident."
    if len(items) == 1:
        return f"Relevant because it is {items[0]}."
    return f"Relevant because it is {items[0]}; and also {'; '.join(items[1:])}."


def contains_secret_like(value: str) -> bool:
    """Cheap guard used before anything is written to memory."""
    lowered = value.lower()
    markers = (
        "password=",
        "passwd=",
        "secret=",
        "api_key=",
        "apikey=",
        "authorization:",
        "bearer ",
        "private_key",
        "postgres://",
        "mysql://",
        "mongodb://",
        "redis://",
    )
    return any(marker in lowered for marker in markers)
