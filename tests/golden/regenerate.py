"""Regenerate the golden provenance file.

Run as ``python -m tests.golden.regenerate`` after a deliberate change to the provenance schema,
then review the diff.
"""

from __future__ import annotations

import json
from pathlib import Path

from tests.conftest import FIXTURE_DIR, GOLDEN_DIR
from tests.integration.test_provenance_golden import GOLDEN_NAME, SCENARIO_NAME, run_scenario


def main() -> None:
    records = run_scenario(FIXTURE_DIR / SCENARIO_NAME)
    target: Path = GOLDEN_DIR / GOLDEN_NAME
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(records, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {len(records)} records to {target}")


if __name__ == "__main__":
    main()
