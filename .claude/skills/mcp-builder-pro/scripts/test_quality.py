#!/usr/bin/env python3
"""Verify the deterministic contract and evidence controls using only synthetic data."""

import copy
import hashlib
import json
import subprocess
import sys
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

from contract_diff import compare
from evidence_gate import REQUIRED, assess, target_fingerprint
from validate_suite import validate as validate_suite

SCRIPTS = Path(__file__).resolve().parent
HUB = SCRIPTS.parent


def asset(name):
    return json.loads((HUB / "assets" / name).read_text(encoding="utf-8"))


class TestContracts(unittest.TestCase):
    def setUp(self):
        self.old = asset("mcp-contract.json")
        self.new = copy.deepcopy(self.old)
        self.tool = self.new["tools"][0]

    def test_same_contract(self):
        self.assertEqual(compare(self.old, self.new), [])

    def test_optional_input_and_required_input(self):
        self.tool["inputSchema"]["properties"]["region"] = {"type": "string"}
        self.assertEqual(
            {item["classification"] for item in compare(self.old, self.new)},
            {"additive"},
        )
        self.tool["inputSchema"]["required"].append("region")
        self.assertIn(
            "breaking", {item["classification"] for item in compare(self.old, self.new)}
        )

    def test_direction_of_bounds(self):
        self.tool["inputSchema"]["properties"]["item_id"]["maxLength"] = 12
        self.tool["outputSchema"]["properties"]["label"]["maxLength"] = 12
        findings = {
            item["path"]: item["classification"] for item in compare(self.old, self.new)
        }
        self.assertEqual(
            findings["tools/get_catalog_item.inputSchema.properties.item_id.maxLength"],
            "breaking",
        )
        self.assertEqual(
            findings["tools/get_catalog_item.outputSchema.properties.label.maxLength"],
            "additive",
        )

    def test_removal_and_new_field_for_closed_output(self):
        del self.tool["outputSchema"]["properties"]["category"]
        self.tool["outputSchema"]["required"].remove("category")
        self.tool["outputSchema"]["properties"]["extra"] = {"type": "string"}
        changed = compare(self.old, self.new)
        self.assertEqual(
            len([item for item in changed if item["classification"] == "breaking"]), 3
        )

    def test_scope_description_and_unsupported_composition(self):
        self.tool["requiredScopes"].append("catalog:private")
        self.tool["description"] = "Search catalog for relevant items"
        self.tool["inputSchema"]["allOf"] = [{"required": ["region"]}]
        findings = compare(self.old, self.new)
        self.assertEqual(len(findings), 3)
        self.assertEqual(
            {item["classification"] for item in findings}, {"manual-review"}
        )

    def test_read_cannot_become_write_and_removed_tool_breaks(self):
        self.tool["action"] = "write"
        self.assertEqual(compare(self.old, self.new)[0]["classification"], "breaking")
        self.new["tools"] = []
        self.assertEqual(compare(self.old, self.new)[0]["classification"], "breaking")

    def test_cli_exit_paths_and_stable_output(self):
        with TemporaryDirectory() as directory:
            paths = [Path(directory) / name for name in ("old.json", "new.json")]
            command = [
                sys.executable,
                str(SCRIPTS / "contract_diff.py"),
                *(str(path) for path in paths),
                "--format",
                "json",
            ]
            paths[0].write_text(json.dumps(self.old))
            for code in (0, 1, 2, 3):
                if code == 1:
                    self.tool["action"] = "write"
                if code == 2:
                    self.tool["action"] = "read"
                    self.tool["inputSchema"]["anyOf"] = [{}]
                paths[1].write_text(json.dumps(self.new) if code != 3 else "{")
                run = subprocess.run(
                    command, capture_output=True, text=True, check=False
                )
                self.assertEqual(run.returncode, code, run)
                self.assertEqual(
                    run.stdout,
                    subprocess.run(
                        command, capture_output=True, text=True, check=False
                    ).stdout,
                )


class TestEvidence(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.log = self.root / "local-test.txt"
        self.log.write_text("owned fixture verification\n")
        self.ledger = asset("mcp-evidence.json")
        self.candidate = "a" * 40
        self.ledger["candidate"] = self.candidate
        self.now = datetime(2026, 11, 23, tzinfo=UTC)
        self.fingerprint = target_fingerprint(self.ledger["target"])

    def fill(self, profile="local-readonly"):
        self.ledger["profile"] = profile
        self.ledger["checks"] = [
            {
                "id": check_id,
                "kind": kind,
                "candidate": self.candidate,
                "targetFingerprint": self.fingerprint,
                "command": "fixture check",
                "recordedAt": self.now.isoformat(),
                "outcome": "passed",
                "artifact": self.log.name,
                "sha256": hashlib.sha256(self.log.read_bytes()).hexdigest(),
            }
            for check_id, kind in REQUIRED[profile].items()
        ]

    def check(self, expected, **options):
        inputs = {
            "candidate": self.candidate,
            "target_id": self.ledger["target"]["id"],
            "target_digest": self.fingerprint,
            "profile": self.ledger["profile"],
            "now": self.now,
            "max_age_hours": 72,
        }
        result, code = assess(self.ledger, self.root, **(inputs | options))
        self.assertEqual(code, expected, result)
        return result

    def test_missing_current_and_failed(self):
        self.assertEqual(self.check(2)["verdict"], "not verified")
        self.fill()
        self.assertEqual(self.check(0)["verdict"], "ready")
        self.ledger["checks"][0]["outcome"] = "failed"
        self.assertEqual(self.check(1)["verdict"], "blocked")

    def test_stale_candidate_target_and_artifact_are_rejected(self):
        self.fill()
        self.check(2, now=self.now + timedelta(hours=73))
        self.check(2, candidate="f" * 40)
        self.check(2, target_digest="c" * 64)
        self.log.write_text("altered fixture output\n")
        self.check(2)

    def test_fixture_does_not_satisfy_staging_or_real_client(self):
        self.fill("remote-write")
        for check in self.ledger["checks"]:
            if check["kind"] in ("staging", "real-client"):
                check["kind"] = "fixture"
        result = self.check(2)
        self.assertTrue(
            any(
                entry["reason"] == "requires real-client evidence"
                for entry in result["checks"]
            )
        )
        self.assertTrue(
            any(
                entry["reason"] == "requires staging evidence"
                for entry in result["checks"]
            )
        )

    def test_traversal_and_skipped_are_not_evidence(self):
        self.fill()
        self.ledger["checks"][0]["artifact"] = "../outside.txt"
        self.ledger["checks"][1]["outcome"] = "skipped"
        self.check(2)


class TestSuite(unittest.TestCase):
    def test_complete_suite_and_eval_inventory(self):
        skills, links, cases = validate_suite(HUB.parent)
        self.assertEqual(skills, 9)
        self.assertGreaterEqual(links, 20)
        self.assertEqual(cases, 20)


if __name__ == "__main__":
    unittest.main()
