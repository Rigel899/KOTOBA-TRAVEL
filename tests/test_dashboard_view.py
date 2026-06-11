import os
import tempfile
import unittest
from unittest.mock import patch

from src.core.app_state import GUEST_USERNAME, set_user
from src.core.db_manager import DBManager
from src.ui.home.dashboard_view import DashboardView


class DummyPage:
    def __init__(self):
        self.dialog = None
        self.width = 1200
        self.window = type("Window", (), {"width": 1200})()

    def update(self):
        pass

    def open(self, dialog):
        self.dialog = dialog

    def close(self, dialog):
        self.dialog = None


def reset_db_singletons():
    DBManager._profile_store = None
    DBManager._auth_service = None
    DBManager._profile_integrity = None
    DBManager._progress_service = None
    DBManager._lockout_store = None
    DBManager._profiles_migrated = False
    DBManager.current_username = GUEST_USERNAME


class DashboardViewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.env_patch = patch.dict(os.environ, {"APPDATA": self.tmp.name}, clear=False)
        self.env_patch.start()
        os.environ.pop("KOTOBA_MIGRATE_LEGACY_PROFILES", None)
        reset_db_singletons()
        DBManager.create_account("dashuser", "password1", "q", "a")
        self.state = {}
        set_user(self.state, "dashuser")
        self.page = DummyPage()

    def tearDown(self):
        self.env_patch.stop()
        self.tmp.cleanup()
        reset_db_singletons()

    def test_dashboard_logo_opens_large_preview_dialog(self):
        view = DashboardView(self.page, lambda *a, **k: None, self.state)
        logo = view._logo(96)

        self.assertIsNotNone(logo.on_click)
        logo.on_click(None)

        self.assertIsNotNone(self.page.dialog)
        self.assertEqual(self.page.dialog.title.controls[1].value, "Kotoba Travel")


if __name__ == "__main__":
    unittest.main()
