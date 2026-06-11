import os
import tempfile
import unittest
from unittest.mock import patch

from src.core.achievements import PLATINUM_ACHIEVEMENT, visible_achievement_ids
from src.core.app_state import GUEST_USERNAME, set_user
from src.core.db_manager import DBManager
from src.ui.achievements_view import AchievementsView


class DummyPage:
    def update(self):
        pass


def reset_db_singletons():
    DBManager._profile_store = None
    DBManager._auth_service = None
    DBManager._profile_integrity = None
    DBManager._progress_service = None
    DBManager._lockout_store = None
    DBManager._profiles_migrated = False
    DBManager.current_username = GUEST_USERNAME


class AchievementsViewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.env_patch = patch.dict(os.environ, {"APPDATA": self.tmp.name}, clear=False)
        self.env_patch.start()
        os.environ.pop("KOTOBA_MIGRATE_LEGACY_PROFILES", None)
        reset_db_singletons()
        DBManager.create_account("achuser", "password1", "q", "a")
        self.state = {}
        set_user(self.state, "achuser")

    def tearDown(self):
        self.env_patch.stop()
        self.tmp.cleanup()
        reset_db_singletons()

    def test_build_populates_achievement_grid(self):
        view = AchievementsView(DummyPage(), lambda *a, **k: None, self.state)

        control = view.build()

        self.assertIsNotNone(control)
        self.assertIsNotNone(view.grid)
        self.assertEqual(len(view.grid.controls), len(visible_achievement_ids(set())))

    def test_platinum_is_visible_even_when_locked(self):
        view = AchievementsView(DummyPage(), lambda *a, **k: None, self.state)

        locked_ids = visible_achievement_ids(set())
        unlocked_ids = visible_achievement_ids({PLATINUM_ACHIEVEMENT})

        self.assertIn(PLATINUM_ACHIEVEMENT, locked_ids)
        self.assertIn(PLATINUM_ACHIEVEMENT, unlocked_ids)
        self.assertEqual(len(unlocked_ids), len(locked_ids))


if __name__ == "__main__":
    unittest.main()
