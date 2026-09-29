"""Print the offending nodes for one Lighthouse accessibility audit.

Usage:  python scripts/read_lh.py <lighthouse.json> [audit-id]

Kept in the repo because the audits that matter here (target-size, colour
contrast) report no detail in the tool's own summary, and re-running the audit
to see which element is at fault is slow.
"""

import json
import sys


def main() -> None:
    path = sys.argv[1]
    want = sys.argv[2] if len(sys.argv) > 2 else "color-contrast"

    data = json.load(open(path, encoding="utf-8"))
    audit = data.get("audits", {}).get(want, {})

    print(f"audit: {want}  score: {audit.get('score')}")
    items = (audit.get("details") or {}).get("items", [])
    print(f"items: {len(items)}")
    for item in items:
        node = item.get("node", {})
        print("-" * 70)
        print("selector   :", node.get("selector"))
        print("snippet    :", (node.get("snippet") or "")[:200])
        print("explanation:", (node.get("explanation") or "").replace("\n", " ")[:300])


if __name__ == "__main__":
    main()
