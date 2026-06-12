import os
import tempfile
import unittest
from unittest.mock import patch

from src.core.app_state import GUEST_USERNAME, set_user
from src.core.db_manager import DBManager
from src.core.progress_service import STUDY_SECTION_STAT
from src.ui.explore.culture_view import CultureView
from src.ui.explore.food_view import FoodView
from src.ui.explore.history_view import HistoryView
from src.ui.explore.places_view import PlacesView
from src.ui.study.study_hub import StudyHub


class DummyPage:
    def update(self):
        pass

    def run_task(self, fn, *args):
        return None


def reset_db_singletons():
    DBManager._content_store = None
    DBManager._profile_store = None
    DBManager._auth_service = None
    DBManager._profile_integrity = None
    DBManager._progress_service = None
    DBManager._lockout_store = None
    DBManager._json_cache = {}
    DBManager._profiles_migrated = False
    DBManager.current_username = GUEST_USERNAME


class FoodViewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.env_patch = patch.dict(os.environ, {"APPDATA": self.tmp.name}, clear=False)
        self.env_patch.start()
        os.environ.pop("KOTOBA_MIGRATE_LEGACY_PROFILES", None)
        reset_db_singletons()
        DBManager.create_account("fooduser", "password1", "q", "a")
        self.state = {}
        set_user(self.state, "fooduser")

    def tearDown(self):
        self.env_patch.stop()
        self.tmp.cleanup()
        reset_db_singletons()

    def test_selecting_food_does_not_crash_if_stat_tracking_fails(self):
        view = FoodView(DummyPage(), lambda *a, **k: None, self.state)
        item = view.food_data[0]

        with self.assertLogs("kotoba.ui.food", level="ERROR"):
            with patch.object(DBManager, "increment_stat", side_effect=RuntimeError("achievement catalog error")):
                view._select_food(item)

        self.assertEqual(view.selected_item, item)
        self.assertIsNotNone(view.right_switcher.content)

    def test_selecting_food_does_not_crash_if_achievement_notification_fails(self):
        view = FoodView(DummyPage(), lambda *a, **k: None, self.state)
        item = view.food_data[0]

        with patch.object(DBManager, "increment_stat", return_value=["food_10"]):
            with self.assertLogs("kotoba.ui.food", level="ERROR"):
                with patch("src.ui.explore.food_view.show_achievements", side_effect=RuntimeError("toast failed")):
                    view._select_food(item)

        self.assertEqual(view.selected_item, item)
        self.assertIsNotNone(view.right_switcher.content)

    def test_selecting_place_does_not_crash_if_achievement_notification_fails(self):
        view = PlacesView(DummyPage(), lambda *a, **k: None, self.state)
        item = view.explore_data[0]

        with patch.object(DBManager, "increment_stat", return_value=["places_5"]):
            with self.assertLogs("kotoba.ui.places", level="ERROR"):
                with patch("src.ui.explore.places_view.show_achievements", side_effect=RuntimeError("toast failed")):
                    view._select_item(item)

        self.assertEqual(view.selected_item, item)
        self.assertIsNotNone(view.right_switcher.content)

    def test_selecting_culture_topic_does_not_crash_if_achievement_notification_fails(self):
        view = CultureView(DummyPage(), lambda *a, **k: None, self.state)

        with patch.object(DBManager, "increment_stat", return_value=["culture_all"]):
            with self.assertLogs("kotoba.ui.culture", level="ERROR"):
                with patch("src.ui.explore.culture_view.show_achievements", side_effect=RuntimeError("toast failed")):
                    view._select_topic(0)

        self.assertEqual(view.selected_index, 0)
        self.assertIsNotNone(view.right_switcher.content)

    def test_selecting_history_era_does_not_crash_if_achievement_notification_fails(self):
        view = HistoryView(DummyPage(), lambda *a, **k: None, self.state)

        with patch.object(DBManager, "increment_stat", return_value=["history_all"]):
            with self.assertLogs("kotoba.ui.history", level="ERROR"):
                with patch("src.ui.explore.history_view.show_achievements", side_effect=RuntimeError("toast failed")):
                    view._select_era(0)

        self.assertEqual(view.selected_index, 0)
        self.assertIsNotNone(view.right_switcher.content)

    def test_tracking_study_section_does_not_crash_if_achievement_notification_fails(self):
        page = DummyPage()
        view = StudyHub(page, lambda *a, **k: None, self.state)

        with patch.object(DBManager, "increment_stat", return_value=["study_first"]) as increment:
            with self.assertLogs("kotoba.ui.study", level="ERROR"):
                with patch("src.ui.study.study_hub.show_achievements", side_effect=RuntimeError("toast failed")):
                    view._track_study_section("kanji")

        increment.assert_called_once_with(
            "fooduser",
            STUDY_SECTION_STAT,
            unique_id="kanji",
        )


if __name__ == "__main__":
    unittest.main()
