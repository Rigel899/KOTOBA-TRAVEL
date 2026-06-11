import unittest

from src.core.achievements import ACHIEVEMENTS, RARITY_COLOR
from src.core.progress_service import (
    EXAM_MASTER_ACHIEVEMENT,
    EXAM_PASS_ACHIEVEMENT,
    EXPLORATION_ACHIEVEMENTS,
    QUIZ_FIRST_ACHIEVEMENTS,
    QUIZ_PERFECT_ACHIEVEMENTS,
)


class AchievementsCatalogTests(unittest.TestCase):
    def test_every_achievement_has_required_display_fields(self):
        for achievement_id, data in ACHIEVEMENTS.items():
            with self.subTest(achievement_id=achievement_id):
                self.assertTrue(data.get("title"))
                self.assertTrue(data.get("description"))
                self.assertTrue(data.get("emoji"))
                self.assertIn(data.get("rarity"), RARITY_COLOR)

    def test_progress_rules_only_reference_known_achievement_ids(self):
        generated_ids = {
            "first_steps",
            "streak_5",
            "streak_10",
            "quiz_5",
            "quiz_25",
            "vocab_50",
            EXAM_PASS_ACHIEVEMENT,
            EXAM_MASTER_ACHIEVEMENT,
            *EXPLORATION_ACHIEVEMENTS.values(),
            *QUIZ_FIRST_ACHIEVEMENTS.values(),
            *QUIZ_PERFECT_ACHIEVEMENTS.values(),
        }

        self.assertFalse(generated_ids - set(ACHIEVEMENTS))


if __name__ == "__main__":
    unittest.main()
