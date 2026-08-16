from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "skills/goldenwave-init/scripts"))

from gw_init import repair  # noqa: E402


class RepairRaceTest(unittest.TestCase):
    def test_file_created_after_plan_is_not_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "kb"
            (target / ".kb").mkdir(parents=True)
            (target / ".kb/goldenwave.json").write_text(
                json.dumps({"format_version": "gwkb/v0.1"}), encoding="utf-8"
            )
            planned = repair.plan(target)
            injected = target / ".kb/reliable-inject/active.json"

            def race(event: str, path: Path) -> None:
                if event == "before_create_file" and path == injected:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text("user-authored", encoding="utf-8")

            result = repair.apply(
                target,
                plan_digest=planned["plan_digest"],
                confirm=planned["plan_digest"],
                boundary_hook=race,
            )
            self.assertFalse(result["ok"])
            self.assertEqual("GW_REPAIR_TARGET_CHANGED", result["code"])
            self.assertEqual("user-authored", injected.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
