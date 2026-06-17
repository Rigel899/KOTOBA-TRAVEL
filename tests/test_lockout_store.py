import tempfile
import unittest
from pathlib import Path

from src.core.lockout_store import LockoutStore


def _normalize(username: str) -> str:
    return (username or "").strip().lower()


class LockoutStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = LockoutStore(
            lambda: self.tmp.name,
            _normalize,
            max_failed_attempts=2,
            lockout_seconds=60,
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_failed_attempts_lock_user_and_track_remaining_attempts(self):
        self.assertFalse(self.store.record_failed_attempt("Utente", "login"))
        self.assertEqual(self.store.remaining_attempts("utente", "login"), 1)

        self.assertTrue(self.store.record_failed_attempt("utente", "login"))
        locked, remaining = self.store.is_locked_out("utente", "login")

        self.assertTrue(locked)
        self.assertGreater(remaining, 0)
        self.assertEqual(self.store.remaining_attempts("utente", "login"), 0)

    def test_failed_attempt_during_active_lock_does_not_extend_timer(self):
        self.store.record_failed_attempt("utente", "login")
        self.store.record_failed_attempt("utente", "login")
        first_locked_until = self.store.read()["utente:login"]["locked_until"]

        self.assertTrue(self.store.record_failed_attempt("utente", "login"))
        second_locked_until = self.store.read()["utente:login"]["locked_until"]

        self.assertEqual(first_locked_until, second_locked_until)

    def test_contexts_are_independent_and_clear_removes_only_requested_context(self):
        self.store.record_failed_attempt("utente", "login")
        self.store.record_failed_attempt("utente", "recovery")

        self.store.clear_failed_attempts("utente", "login")

        self.assertEqual(self.store.remaining_attempts("utente", "login"), 2)
        self.assertEqual(self.store.remaining_attempts("utente", "recovery"), 1)

    def test_corrupt_lockout_file_returns_empty_data_and_logs_warning(self):
        Path(self.store.path()).write_text("{not-json", encoding="utf-8")

        with self.assertLogs("kotoba.lockout", level="WARNING"):
            data = self.store.read()

        self.assertEqual(data, {})


if __name__ == "__main__":
    unittest.main()
