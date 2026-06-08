import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.core.db_manager import DBManager


class DBManagerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.env_patch = patch.dict(
            os.environ,
            {"APPDATA": self.tmp.name},
            clear=False,
        )
        self.env_patch.start()
        os.environ.pop("KOTOBA_MIGRATE_LEGACY_PROFILES", None)
        DBManager._profiles_migrated = False

    def tearDown(self):
        self.env_patch.stop()
        self.tmp.cleanup()
        DBManager._profiles_migrated = False

    def test_username_is_validated_before_profile_path(self):
        self.assertEqual(DBManager.normalize_username(" Marco_1 "), "marco_1")
        self.assertIsNone(DBManager.username_validation_error("Marco_1"))
        self.assertIsNotNone(DBManager.username_validation_error("ma"))
        self.assertIsNotNone(DBManager.username_validation_error("mar-co"))
        self.assertIsNotNone(DBManager.username_validation_error("!!!"))

        DBManager.create_account("Marco_1", "password1", "q", "a")

        self.assertTrue(DBManager.user_exists("marco_1"))
        self.assertTrue(DBManager.profile_path("MARCO_1").endswith("user_marco_1.json"))
        self.assertFalse(DBManager.user_exists("mar-co"))
        with self.assertRaises(ValueError):
            DBManager.profile_path("mar-co")

    def test_legacy_profiles_are_not_migrated_by_default(self):
        with tempfile.TemporaryDirectory() as legacy_dir:
            legacy_path = Path(legacy_dir) / "user_legacy.json"
            legacy_path.write_text(json.dumps({"username": "legacy"}), encoding="utf-8")

            with patch.object(DBManager, "legacy_profiles_dir", return_value=legacy_dir):
                DBManager.profile_path("validuser")

            migrated_path = Path(DBManager.profiles_dir()) / "user_legacy.json"
            self.assertFalse(migrated_path.exists())

    def test_partial_quiz_result_is_persisted_and_normalized(self):
        DBManager.create_account("quizuser", "password1", "q", "a")

        unlocked = DBManager.record_quiz_result(
            "quizuser",
            "hiragana",
            5,
            total_questions=5,
            max_streak=3,
        )
        data = DBManager.get_user_data("quizuser")

        self.assertEqual(unlocked, [])
        self.assertEqual(data["scores"]["hiragana"], 10)
        self.assertEqual(data["stats"]["total_quizzes"], 1)
        self.assertEqual(data["stats"]["total_questions"], 5)
        self.assertEqual(data["stats"]["total_correct"], 5)
        self.assertEqual(data["stats"]["max_streak"], 3)
        self.assertEqual(data["stats"]["perfect_quiz_modes"]["hiragana"], 1)
        self.assertNotIn("hiragana_perfect", data["achievements"])

    def test_streak_achievement_uses_real_streak(self):
        DBManager.create_account("streakuser", "password1", "q", "a")

        unlocked = DBManager.record_quiz_result(
            "streakuser",
            "grammar",
            6,
            total_questions=10,
            max_streak=5,
        )

        self.assertIn("streak_5", unlocked)
        self.assertNotIn("streak_10", unlocked)

    def test_quiz_mode_total_tracks_real_question_count(self):
        DBManager.create_account("examuser", "password1", "q", "a")

        DBManager.record_quiz_result(
            "examuser",
            "exam",
            15,
            total_questions=20,
            max_streak=4,
        )
        data = DBManager.get_user_data("examuser")

        self.assertEqual(data["scores"]["exam"], 8)
        self.assertEqual(data["stats"]["quiz_mode_correct"]["exam"], 15)
        self.assertEqual(data["stats"]["quiz_mode_total"]["exam"], 20)

    def test_unique_views_are_saved_as_dict_and_migrate_legacy_lists(self):
        DBManager.create_account("viewsuser", "password1", "q", "a")
        data = DBManager.get_user_data("viewsuser")
        data["stats"]["unique_views"] = {"food_viewed": ["ramen"]}
        data["stats"]["food_viewed"] = 1
        DBManager.update_user_data("viewsuser", data)

        DBManager.increment_stat("viewsuser", "food_viewed", unique_id="sushi")
        data = DBManager.get_user_data("viewsuser")

        viewed = data["stats"]["unique_views"]["food_viewed"]
        self.assertIsInstance(viewed, dict)
        self.assertIn("ramen", viewed)
        self.assertIn("sushi", viewed)
        self.assertEqual(data["stats"]["food_viewed"], 2)

    def test_content_totals_are_passed_to_increment_stat(self):
        DBManager.create_account("cultureuser", "password1", "q", "a")

        with patch.object(DBManager, "load_json", side_effect=AssertionError("content JSON should not be loaded")):
            unlocked = DBManager.increment_stat(
                "cultureuser",
                "culture_viewed",
                unique_id="topic-1",
                total_items=1,
            )

        self.assertEqual(unlocked, ["culture_all"])

    def test_short_password_is_rejected(self):
        self.assertIsNotNone(DBManager.password_validation_error("short"))
        with self.assertRaises(ValueError):
            DBManager.create_account("shortpw", "short", "q", "a")

    # ── Pacchetto 1: fix sicurezza ────────────────────────────────────────────

    def test_create_account_rejects_duplicate_username(self):
        DBManager.create_account("dupuser", "password1", "q", "a")
        with self.assertRaises(ValueError) as ctx:
            DBManager.create_account("dupuser", "password2", "q2", "a2")
        self.assertIn("già in uso", str(ctx.exception))
        data = DBManager.get_user_data("dupuser")
        self.assertTrue(DBManager.verify_secret("password1", data["password_hash"]),
                        "Il profilo originale non deve essere sovrascritto")

    def test_lockout_persists_independent_of_view_instance(self):
        DBManager.create_account("locktest", "password1", "q", "a")
        for _ in range(DBManager.MAX_FAILED_ATTEMPTS):
            DBManager.record_failed_attempt("locktest", "login")
        locked, remaining = DBManager.is_locked_out("locktest", "login")
        self.assertTrue(locked, "Dovrebbe essere bloccato dopo MAX_FAILED_ATTEMPTS tentativi")
        self.assertGreater(remaining, 0)
        locked2, remaining2 = DBManager.is_locked_out("locktest", "login")
        self.assertTrue(locked2, "Il blocco deve persistere alla seconda verifica (simula nuova istanza vista)")
        self.assertGreater(remaining2, 0)

    def test_lockout_clears_on_success(self):
        for _ in range(3):
            DBManager.record_failed_attempt("cleartest", "login")
        self.assertEqual(DBManager.remaining_attempts("cleartest", "login"), 2)
        DBManager.clear_failed_attempts("cleartest", "login")
        locked, _ = DBManager.is_locked_out("cleartest", "login")
        self.assertFalse(locked)
        self.assertEqual(DBManager.remaining_attempts("cleartest", "login"), DBManager.MAX_FAILED_ATTEMPTS)

    def test_lockout_contexts_are_independent(self):
        DBManager.create_account("ctxtest", "password1", "q", "a")
        for _ in range(DBManager.MAX_FAILED_ATTEMPTS):
            DBManager.record_failed_attempt("ctxtest", "login")
        login_locked, _ = DBManager.is_locked_out("ctxtest", "login")
        recovery_locked, _ = DBManager.is_locked_out("ctxtest", "recovery")
        self.assertTrue(login_locked, "Login deve essere bloccato")
        self.assertFalse(recovery_locked, "Recovery non deve essere bloccato")

    def test_export_safe_profile_excludes_sensitive_fields(self):
        DBManager.create_account("exporttest", "password1", "q", "a")
        export = DBManager.export_safe_profile("exporttest")
        self.assertIsNotNone(export)
        self.assertNotIn("password_hash", export, "password_hash non deve comparire nell'export")
        self.assertNotIn("recovery_answer_hash", export, "recovery_answer_hash non deve comparire nell'export")
        self.assertIn("username", export)
        self.assertIn("achievements", export)
        self.assertIn("stats", export)
        self.assertIn("_export_note", export)
        self.assertIn("_exported_at", export)


if __name__ == "__main__":
    unittest.main()
