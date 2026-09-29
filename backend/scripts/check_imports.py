"""Import smoke check. Run: python scripts/check_imports.py"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app  # noqa: E402

print("app imported OK")
for route in app.routes:
    methods = getattr(route, "methods", None)
    if methods:
        print(f"  {sorted(methods)!s:40} {route.path}")
