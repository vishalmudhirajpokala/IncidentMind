"""Prompt loading.

Prompts live as dedicated files under ``backend/prompts/`` rather than being
inlined as giant strings in Python modules, so they can be reviewed, diffed and
tuned independently of application code.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Dict

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


class PromptNotFound(FileNotFoundError):
    pass


@lru_cache(maxsize=32)
def load_prompt(name: str) -> str:
    """Load a prompt template by file stem (e.g. ``incident_investigation``)."""
    path = PROMPTS_DIR / f"{name}.txt"
    if not path.is_file():
        raise PromptNotFound(f"Prompt template not found: {path}")
    return path.read_text(encoding="utf-8")


def render(name: str, **values: object) -> str:
    """Render a prompt template, substituting ``{placeholders}``.

    Unknown placeholders are left untouched so a partially rendered prompt is
    still visible in logs rather than silently crashing the request.
    """
    template = load_prompt(name)
    try:
        return template.format(**values)
    except KeyError:
        return _safe_render(template, values)


def _safe_render(template: str, values: Dict[str, object]) -> str:
    class _Default(dict):
        def __missing__(self, key: str) -> str:  # pragma: no cover - trivial
            return "{" + key + "}"

    return template.format_map(_Default(values))


def available_prompts() -> list[str]:
    if not PROMPTS_DIR.is_dir():
        return []
    return sorted(p.stem for p in PROMPTS_DIR.glob("*.txt"))
