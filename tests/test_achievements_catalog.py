import unittest
from pathlib import Path

from src.core.achievements import ACHIEVEMENTS, MODULE_ORDER, RARITY_COLOR
from src.core.progress_service import (
    EXAM_PERFECT_MILESTONES,
    EXPLORATION_ACHIEVEMENTS,
    QUIZ_FIRST_ACHIEVEMENTS,
    QUIZ_PERFECT_ACHIEVEMENTS,
    STUDY_ACHIEVEMENTS,
    STUDY_MASTERY_ACHIEVEMENT,
    STUDY_MASTERY_REQUIRED_ACHIEVEMENTS,
)
from src.ui.achievements_view import AchievementsView


class AchievementsCatalogTests(unittest.TestCase):
    def test_every_achievement_has_required_display_fields(self):
        for achievement_id, data in ACHIEVEMENTS.items():
            with self.subTest(achievement_id=achievement_id):
                self.assertTrue(data.get("title"))
                self.assertTrue(data.get("description"))
                self.assertTrue(data.get("emoji"))
                self.assertIn(data.get("rarity"), RARITY_COLOR)
                self.assertIn(data.get("module"), MODULE_ORDER)

    def test_progress_rules_only_reference_known_achievement_ids(self):
        generated_ids = {
            "first_steps",
            "streak_5",
            "streak_10",
            "quiz_5",
            "quiz_25",
            "vocab_50",
            *(achievement_id for _, achievement_id in EXAM_PERFECT_MILESTONES),
            *EXPLORATION_ACHIEVEMENTS.values(),
            *QUIZ_FIRST_ACHIEVEMENTS.values(),
            *QUIZ_PERFECT_ACHIEVEMENTS.values(),
            *STUDY_ACHIEVEMENTS.values(),
            STUDY_MASTERY_ACHIEVEMENT,
            *STUDY_MASTERY_REQUIRED_ACHIEVEMENTS,
        }

        self.assertFalse(generated_ids - set(ACHIEVEMENTS))

    def test_custom_achievement_assets_exist(self):
        asset_root = Path(__file__).resolve().parents[1] / "src" / "asset"

        for asset_path in AchievementsView.ACHIEVEMENT_ASSETS.values():
            with self.subTest(asset_path=asset_path):
                self.assertTrue((asset_root / asset_path).exists())

    def test_achievement_view_can_sort_by_module_or_rarity(self):
        view = AchievementsView.__new__(AchievementsView)

        view.sort_mode = "module"
        module_sorted = view._sorted_items()
        self.assertEqual(module_sorted[0][1]["module"], "account")

        view.sort_mode = "rarity"
        rarity_sorted = view._sorted_items()
        self.assertEqual(rarity_sorted[0][1]["rarity"], "platino")


if __name__ == "__main__":
    unittest.main()
