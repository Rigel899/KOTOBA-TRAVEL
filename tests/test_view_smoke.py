import importlib
import os
import tempfile
import unittest
from unittest.mock import patch

import flet as ft

from src.core.app_state import GUEST_USERNAME, set_user
from src.core.db_manager import DBManager
from src.main import ROUTES


class DummyPage:
    def __init__(self):
        self.tasks = []
        self.overlay = []
        self.dialog = None
        self.window = type("Window", (), {})()

    def update(self):
        pass

    def run_task(self, fn, *args):
        self.tasks.append((fn, args))
        return None

    def open(self, dialog):
        self.dialog = dialog

    def close(self, dialog):
        self.dialog = None


def _reset_db_singletons():
    DBManager._profile_store = None
    DBManager._auth_service = None
    DBManager._profile_integrity = None
    DBManager._progress_service = None
    DBManager._lockout_store = None
    DBManager._profiles_migrated = False
    DBManager.current_username = GUEST_USERNAME


class ViewSmokeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.env_patch = patch.dict(os.environ, {"APPDATA": self.tmp.name}, clear=False)
        self.env_patch.start()
        os.environ.pop("KOTOBA_MIGRATE_LEGACY_PROFILES", None)
        _reset_db_singletons()
        DBManager.create_account("smokeuser", "password1", "q", "a")
        self.state = {}
        set_user(self.state, "smokeuser")
        self.page = DummyPage()

    def tearDown(self):
        self.env_patch.stop()
        self.tmp.cleanup()
        _reset_db_singletons()

    def test_registered_routes_build_without_crashing(self):
        def navigate(*args, **kwargs):
            pass

        for route, (module_path, class_name) in ROUTES.items():
            with self.subTest(route=route):
                module = importlib.import_module(module_path)
                view_cls = getattr(module, class_name)
                control = view_cls(self.page, navigate, self.state).build()

                self.assertIsInstance(control, ft.Control)


if __name__ == "__main__":
    unittest.main()
