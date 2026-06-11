import unittest

from src.core.profile_factory import build_default_profile
from src.core.achievements import PLATINUM_ACHIEVEMENT, platinum_required_achievement_ids
from src.core.progress_service import ProgressService


class ProgressServiceTests(unittest.TestCase):
    def setUp(self):
        self.profiles = {}
        self._add_profile("utente")
        self.service = ProgressService(
            lambda username: self.profiles.get(username),
            lambda username, data: self.profiles.__setitem__(username, data),
        )

    def _add_profile(self, username: str) -> None:
        self.profiles[username] = build_default_profile(username, "password-hash", "q", "answer-hash")

    def test_record_quiz_result_updates_stats_scores_and_achievements(self):
        unlocked = self.service.record_quiz_result(
            "utente",
            "grammar",
            score=6,
            total_questions=10,
            max_streak=5,
        )
        data = self.profiles["utente"]

        self.assertEqual(data["scores"]["grammar"], 6)
        self.assertEqual(data["stats"]["total_quizzes"], 1)
        self.assertEqual(data["stats"]["total_questions"], 10)
        self.assertEqual(data["stats"]["total_correct"], 6)
        self.assertEqual(data["stats"]["max_streak"], 5)
        self.assertIn("streak_5", unlocked)
        self.assertNotIn("streak_10", unlocked)

    def test_unique_increment_ignores_duplicate_views(self):
        self.assertEqual(
            self.service.increment_stat("utente", "places_viewed", unique_id="tokyo"),
            [],
        )
        self.assertEqual(
            self.service.increment_stat("utente", "places_viewed", unique_id="tokyo"),
            [],
        )

        data = self.profiles["utente"]
        self.assertEqual(data["stats"]["places_viewed"], 1)
        self.assertEqual(list(data["stats"]["unique_views"]["places_viewed"]), ["tokyo"])

    def test_unique_increment_unlocks_when_threshold_is_reached(self):
        unlocked = []
        for index in range(5):
            unlocked = self.service.increment_stat(
                "utente",
                "places_viewed",
                unique_id=f"place-{index}",
            )

        self.assertEqual(unlocked, ["places_5"])
        self.assertIn("places_5", self.profiles["utente"]["achievements"])

    def test_advanced_quiz_modes_unlock_first_and_perfect_achievements(self):
        cases = [
            ("kanji", {"kanji_first", "kanji_perfect"}),
            ("vocab", {"vocab_first", "vocab_perfect", "vocab_50"}),
            ("grammar", {"grammar_first", "grammar_perfect"}),
        ]

        for mode_key, expected in cases:
            username = f"{mode_key}user"
            self._add_profile(username)

            unlocked = set(
                self.service.record_quiz_result(
                    username,
                    mode_key,
                    score=50 if mode_key == "vocab" else 10,
                    total_questions=50 if mode_key == "vocab" else 10,
                    max_streak=4,
                )
            )

            self.assertTrue(expected.issubset(unlocked))
            self.assertTrue(expected.issubset(set(self.profiles[username]["achievements"])))

    def test_exam_unlocks_first_completion_and_perfect_milestones(self):
        self._add_profile("examuser")

        unlocked = self.service.record_quiz_result(
            "examuser",
            "exam",
            score=13,
            total_questions=20,
            max_streak=4,
        )

        self.assertIn("exam_first", unlocked)
        self.assertNotIn("exam_perfect_1", unlocked)

        unlocked = []
        for _ in range(4):
            unlocked = self.service.record_quiz_result(
                "examuser",
                "exam",
                score=20,
                total_questions=20,
                max_streak=4,
            )

        self.assertIn("exam_perfect_1", self.profiles["examuser"]["achievements"])
        self.assertNotIn("exam_perfect_5", unlocked)

        unlocked = self.service.record_quiz_result(
            "examuser",
            "exam",
            score=20,
            total_questions=20,
            max_streak=4,
        )
        self.assertIn("exam_perfect_5", unlocked)

        for _ in range(5):
            unlocked = self.service.record_quiz_result(
                "examuser",
                "exam",
                score=20,
                total_questions=20,
                max_streak=4,
            )
        self.assertIn("exam_perfect_10", unlocked)

        for _ in range(10):
            unlocked = self.service.record_quiz_result(
                "examuser",
                "exam",
                score=20,
                total_questions=20,
                max_streak=4,
            )
        self.assertIn("exam_master", unlocked)

    def test_exam_perfect_milestones_require_full_exam_length(self):
        self._add_profile("shortexam")

        unlocked = self.service.record_quiz_result(
            "shortexam",
            "exam",
            score=9,
            total_questions=10,
            max_streak=4,
        )

        self.assertIn("exam_first", unlocked)
        self.assertNotIn("exam_perfect_1", unlocked)
        self.assertNotIn("exam_master", unlocked)

    def test_unknown_achievement_ids_are_not_saved(self):
        with self.assertLogs("kotoba.progress", level="WARNING") as logs:
            unlocked = self.service.unlock_achievement("utente", "missing_achievement")

        self.assertFalse(unlocked)
        self.assertNotIn("missing_achievement", self.profiles["utente"]["achievements"])
        self.assertIn("missing_achievement", logs.output[0])

    def test_platinum_unlocks_only_after_every_required_achievement(self):
        self.assertFalse(self.service.unlock_achievement("utente", PLATINUM_ACHIEVEMENT))
        self.assertNotIn(PLATINUM_ACHIEVEMENT, self.profiles["utente"]["achievements"])

        required = sorted(platinum_required_achievement_ids())
        for achievement_id in required:
            self.service.unlock_achievement("utente", achievement_id)

        self.assertIn(PLATINUM_ACHIEVEMENT, self.profiles["utente"]["achievements"])


if __name__ == "__main__":
    unittest.main()
