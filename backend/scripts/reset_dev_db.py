"""Reset the development database to the clean seeded state.

    python scripts/reset_dev_db.py

Wipes incidents, investigation runs and memory events, then restores the
reference corpus. Use this to get back to a known state between demo runs.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import create_all, session_scope  # noqa: E402
from seed.seed_incidents import reset_and_seed  # noqa: E402

create_all()
with session_scope() as session:
    cleared = reset_and_seed(session)

print(f"Reset complete: {cleared}")
