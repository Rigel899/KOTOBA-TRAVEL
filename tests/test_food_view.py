import os
import tempfile
import unittest
from unittest.mock import patch

from src.core.app_state import GUEST_USERNAME, set_user
from src.core.db_manager import DBManager
from src.ui.food_view import FoodView


class DummyPage:
    def update(self):
        pass

    def run_task(self, fn, *args):
        return None


def reset_db_singletons():
    DBManager._profile_store = None
    DBManager._auth_service = None
    DBManager._profile_integrity = None
    DBManager._progress_service = None
    DBManager._lockout_store = None
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


if __name__ == "__main__":
    unittest.main()
