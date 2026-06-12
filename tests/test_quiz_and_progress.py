"""
Test per quiz_utils (funzioni pure) e progress_service.
"""
import os
import tempfile
import unittest
from unittest.mock import patch

from src.core.app_state import GUEST_USERNAME
from src.core.db_manager import DBManager
from src.ui.yugi.dojo.quiz.quiz_utils import (
    count_correct_answers,
    make_choice_options,
    max_correct_streak,
    percent_score,
)


def _reset_db_singletons() -> None:
    DBManager._content_store = None
    DBManager._lockout_store = None
    DBManager._profile_store = None
    DBManager._progress_service = None
    DBManager._auth_service = None
    DBManager._profile_integrity = None
    DBManager._json_cache = {}
    DBManager._profiles_migrated = False
    DBManager.current_username = GUEST_USERNAME


# ── quiz_utils ────────────────────────────────────────────────────────────────

class MakeChoiceOptionsTests(unittest.TestCase):
    def test_correct_is_always_included(self):
        opts = make_choice_options("ramen", ["ramen", "sushi", "tempura", "udon"])
        self.assertIn("ramen", opts)

    def test_returns_four_options(self):
        opts = make_choice_options("a", ["a", "i", "u", "e", "o"])
        self.assertEqual(len(opts), 4)

    def test_no_duplicates_in_output(self):
        opts = make_choice_options("a", ["a", "i", "u", "e", "o"])
        self.assertEqual(len(opts), len(set(opts)))

    def test_correct_not_duplicated_when_pool_has_duplicates(self):
        opts = make_choice_options("a", ["a", "a", "a", "a", "i"])
        self.assertEqual(opts.count("a"), 1)

    def test_placeholder_fills_short_pool(self):
        opts = make_choice_options("a", ["a", "i"])
        self.assertEqual(len(opts), 4)
        self.assertIn("a", opts)
        self.assertIn("i", opts)
        self.assertIn("-", opts)

    def test_case_insensitive_deduplication(self):
        opts = make_choice_options("Ramen", ["ramen", "Ramen", "Sushi", "Udon", "Tempura"], case_sensitive=False)
        lower_opts = [o.lower() for o in opts]
        self.assertEqual(lower_opts.count("ramen"), 1)

    def test_empty_pool_fills_with_placeholders(self):
        opts = make_choice_options("only", [])
        self.assertIn("only", opts)
        self.assertEqual(len(opts), 4)


class CountCorrectAnswersTests(unittest.TestCase):
    QUESTIONS = [("あ", "a", []), ("い", "i", []), ("う", "u", [])]

    def _correct_fn(self, q):
        return q[1]

    def test_all_correct(self):
        answers = {0: "a", 1: "i", 2: "u"}
        self.assertEqual(count_correct_answers(self.QUESTIONS, answers, self._correct_fn), 3)

    def test_none_correct(self):
        answers = {0: "x", 1: "x", 2: "x"}
        self.assertEqual(count_correct_answers(self.QUESTIONS, answers, self._correct_fn), 0)

    def test_partial(self):
        answers = {0: "a", 1: "x", 2: "u"}
        self.assertEqual(count_correct_answers(self.QUESTIONS, answers, self._correct_fn), 2)

    def test_unanswered_question_counts_as_wrong(self):
        answers = {0: "a"}
        self.assertEqual(count_correct_answers(self.QUESTIONS, answers, self._correct_fn), 1)


class MaxCorrectStreakTests(unittest.TestCase):
    QUESTIONS = [("あ", "a", []), ("い", "i", []), ("う", "u", []), ("え", "e", [])]

    def _correct_fn(self, q):
        return q[1]

    def test_perfect_streak(self):
        answers = {0: "a", 1: "i", 2: "u", 3: "e"}
        self.assertEqual(max_correct_streak(self.QUESTIONS, answers, self._correct_fn), 4)

    def test_no_streak(self):
        answers = {0: "x", 1: "x", 2: "x", 3: "x"}
        self.assertEqual(max_correct_streak(self.QUESTIONS, answers, self._correct_fn), 0)

    def test_streak_resets_on_wrong(self):
        answers = {0: "a", 1: "i", 2: "x", 3: "e"}
        self.assertEqual(max_correct_streak(self.QUESTIONS, answers, self._correct_fn), 2)

    def test_streak_at_end(self):
        answers = {0: "x", 1: "u", 2: "u", 3: "e"}
        self.assertEqual(max_correct_streak(self.QUESTIONS, answers, self._correct_fn), 2)

    def test_empty_questions(self):
        self.assertEqual(max_correct_streak([], {}, self._correct_fn), 0)


class PercentScoreTests(unittest.TestCase):
    def test_perfect(self):
        self.assertEqual(percent_score(10, 10), 100)

    def test_zero(self):
        self.assertEqual(percent_score(0, 10), 0)

    def test_partial(self):
        self.assertEqual(percent_score(7, 10), 70)

    def test_zero_total_returns_zero(self):
        self.assertEqual(percent_score(0, 0), 0)


# ── progress_service ──────────────────────────────────────────────────────────

class ProgressServiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.env_patch = patch.dict(os.environ, {"APPDATA": self.tmp.name}, clear=False)
        self.env_patch.start()
        os.environ.pop("KOTOBA_MIGRATE_LEGACY_PROFILES", None)
        _reset_db_singletons()

    def tearDown(self):
        self.env_patch.stop()
        self.tmp.cleanup()
        _reset_db_singletons()

    def test_check_and_unlock_calls_notify_fn(self):
        DBManager.create_account("notifyuser", "password1", "q", "a")
        received = []
        DBManager.check_and_unlock("notifyuser", "first_steps", notify_fn=lambda ach: received.append(ach))
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]["title"], "Primo Passo")

    def test_check_and_unlock_no_notify_fn_does_not_crash(self):
        DBManager.create_account("quietuser", "password1", "q", "a")
        DBManager.check_and_unlock("quietuser", "first_steps")
        data = DBManager.get_user_data("quietuser")
        self.assertIn("first_steps", data["achievements"])

    def test_check_and_unlock_unknown_achievement_does_nothing(self):
        DBManager.create_account("badachuser", "password1", "q", "a")
        received = []
        DBManager.check_and_unlock("badachuser", "non_existent_id", notify_fn=lambda a: received.append(a))
        self.assertEqual(received, [])

    def test_platinum_requires_all_achievements(self):
        from src.core.achievements import PLATINUM_ACHIEVEMENT, platinum_required_achievement_ids
        DBManager.create_account("plattest", "password1", "q", "a")
        result = DBManager.unlock_achievement("plattest", PLATINUM_ACHIEVEMENT)
        self.assertFalse(result, "Platinum non deve sbloccarsi senza gli altri achievement")

    def test_study_mastery_requires_quiz_perfects(self):
        DBManager.create_account("masterytest", "password1", "q", "a")
        result = DBManager.unlock_achievement("masterytest", "study_all")
        self.assertFalse(result, "study_all richiede mixed_perfect, kanji_perfect, vocab_perfect, grammar_perfect")

    def test_exam_perfect_milestones_accumulate(self):
        DBManager.create_account("examperf", "password1", "q", "a")
        # Call 1: perfect_count becomes 1 → exam_first + exam_perfect_1
        unlocked = DBManager.record_quiz_result("examperf", "exam", 20, total_questions=20, max_streak=20)
        self.assertIn("exam_first", unlocked)
        self.assertIn("exam_perfect_1", unlocked)
        self.assertNotIn("exam_perfect_5", unlocked)

        # Calls 2,3,4: perfect_count becomes 2,3,4 → no new milestone
        for _ in range(3):
            DBManager.record_quiz_result("examperf", "exam", 20, total_questions=20, max_streak=20)

        # Call 5: perfect_count becomes 5 → exam_perfect_5 newly unlocked
        unlocked5 = DBManager.record_quiz_result("examperf", "exam", 20, total_questions=20, max_streak=20)
        self.assertIn("exam_perfect_5", unlocked5)

    def test_vocab_50_correct_unlocks_achievement(self):
        DBManager.create_account("vocab50user", "password1", "q", "a")
        for _ in range(5):
            DBManager.record_quiz_result("vocab50user", "vocab", 10, total_questions=10, max_streak=10)
        data = DBManager.get_user_data("vocab50user")
        self.assertIn("vocab_50", data["achievements"])

    def test_increment_stat_deduplicates_unique_views(self):
        DBManager.create_account("dedupuser", "password1", "q", "a")
        DBManager.increment_stat("dedupuser", "food_viewed", unique_id="ramen", total_items=100)
        DBManager.increment_stat("dedupuser", "food_viewed", unique_id="ramen", total_items=100)
        data = DBManager.get_user_data("dedupuser")
        self.assertEqual(data["stats"]["food_viewed"], 1, "La stessa voce non deve contare due volte")

    def test_increment_stat_counts_distinct_views(self):
        DBManager.create_account("distinctuser", "password1", "q", "a")
        DBManager.increment_stat("distinctuser", "food_viewed", unique_id="ramen", total_items=100)
        DBManager.increment_stat("distinctuser", "food_viewed", unique_id="sushi", total_items=100)
        data = DBManager.get_user_data("distinctuser")
        self.assertEqual(data["stats"]["food_viewed"], 2)

    def test_quiz_25_unlocks_at_25_quizzes(self):
        DBManager.create_account("quiz25user", "password1", "q", "a")
        for _ in range(24):
            DBManager.record_quiz_result("quiz25user", "hiragana", 5, total_questions=10)
        unlocked = DBManager.record_quiz_result("quiz25user", "hiragana", 5, total_questions=10)
        self.assertIn("quiz_25", unlocked)


if __name__ == "__main__":
    unittest.main()
