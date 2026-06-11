import json
import tempfile
import unittest
from pathlib import Path

from src.core.profile_integrity import ProfileIntegrity
from src.core.profile_store import ProfileStore


def _canonical(username: str) -> str:
    username = (username or "").strip().lower()
    if not username:
        raise ValueError("invalid username")
    return username


class ProfileStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.user_dir = Path(self.tmp.name) / "user"
        self.data_dir = Path(self.tmp.name) / "data"
        self.user_dir.mkdir()
        self.data_dir.mkdir()
        self.store = ProfileStore(
            lambda: str(self.user_dir),
            lambda: str(self.data_dir),
            _canonical,
            profile_integrity=ProfileIntegrity(allow_unsigned_profiles=True),
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_create_and_update_write_signed_profiles(self):
        self.store.create_user_data("utente", {"username": "utente", "stats": {"total": 0}})
        path = Path(self.store.profile_path("utente"))
        raw = json.loads(path.read_text(encoding="utf-8"))

        self.assertIn("_integrity", raw)
        self.assertEqual(self.store.get_user_data("utente")["stats"]["total"], 0)

        data = self.store.get_user_data("utente")
        data["stats"]["total"] = 1
        self.store.update_user_data("utente", data)

        updated = self.store.get_user_data("utente")
        self.assertEqual(updated["stats"]["total"], 1)

    def test_tampered_signed_profile_returns_none_and_logs_warning(self):
        self.store.create_user_data("utente", {"username": "utente", "stats": {"total": 0}})
        path = Path(self.store.profile_path("utente"))
        raw = json.loads(path.read_text(encoding="utf-8"))
        raw["stats"]["total"] = 999
        path.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")

        with self.assertLogs("kotoba.profile", level="WARNING") as logs:
            self.assertIsNone(self.store.get_user_data("utente"))

        self.assertIn("profile integrity check failed", logs.output[0])

    def test_unsigned_legacy_profile_still_loads(self):
        path = Path(self.store.profiles_dir()) / "user_legacy.json"
        path.write_text(
            json.dumps({"username": "legacy", "stats": {"total": 3}}, ensure_ascii=False),
            encoding="utf-8",
        )

        data = self.store.get_user_data("legacy")

        self.assertIsNotNone(data)
        self.assertEqual(data["stats"]["total"], 3)

    def test_non_object_profile_is_rejected(self):
        path = Path(self.store.profiles_dir()) / "user_bad.json"
        path.write_text(json.dumps(["not", "a", "profile"]), encoding="utf-8")

        with self.assertLogs("kotoba.profile", level="WARNING") as logs:
            self.assertIsNone(self.store.get_user_data("bad"))

        self.assertIn("expected object", logs.output[0])


if __name__ == "__main__":
    unittest.main()
