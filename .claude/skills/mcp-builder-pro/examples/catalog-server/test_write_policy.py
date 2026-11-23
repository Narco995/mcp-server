import unittest
from concurrent.futures import ThreadPoolExecutor

from write_policy import Approval, FixtureWrites


class TestWritePolicy(unittest.TestCase):
    def setUp(self):
        self.writes = FixtureWrites()
        self.request = {
            "actor": "actor-1",
            "tenant": "tenant-a",
            "key": "once",
            "payload": "new-value",
            "approval": Approval("actor-1", "tenant-a", "new-value", 10),
            "now": 3,
        }

    def commit(self, **overrides):
        return self.writes.commit(**(self.request | overrides))

    def test_unapproved_requests_fail_closed(self):
        for misuse in (
            {"tenant": "tenant-b"},
            {"actor": "actor-2"},
            {"now": 10},
            {"approval": True},
            {"authorized": False},
            {"payload": "unapproved-value"},
        ):
            with self.subTest(misuse=misuse), self.assertRaises(PermissionError):
                self.commit(**misuse)
        self.assertEqual(self.writes.committed_count, 0)

    def test_concurrent_duplicates_commit_once(self):
        with ThreadPoolExecutor(max_workers=8) as pool:
            self.assertEqual(
                set(pool.map(lambda _: self.commit(), range(32))), {"committed"}
            )
        self.assertEqual(self.writes.committed_count, 1)

    def test_reconciliation_never_replays_ambiguous_write(self):
        self.assertEqual(self.commit(timeout=True), "unknown")
        self.assertEqual(self.commit(), "unknown")
        self.assertEqual(
            self.writes.reconcile(actor="actor-1", tenant="tenant-b", key="once"),
            "not_committed",
        )
        self.assertEqual(
            self.writes.reconcile(actor="actor-1", tenant="tenant-a", key="once"),
            "committed",
        )
        self.assertEqual(self.commit(), "committed")
        self.assertEqual(self.writes.committed_count, 1)

    def test_changed_payload_is_rejected_even_with_new_approval(self):
        self.commit()
        with self.assertRaisesRegex(ValueError, "idempotency"):
            self.commit(
                payload="changed",
                approval=Approval("actor-1", "tenant-a", "changed", 10),
            )


if __name__ == "__main__":
    unittest.main()
