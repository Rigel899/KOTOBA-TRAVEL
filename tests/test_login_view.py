import os
import tempfile
import unittest
from unittest.mock import patch

from src.core.app_state import GUEST_USERNAME, get_current_user
from src.core.db_manager import DBManager
from src.ui.auth.login_view import LoginView


class DummyPage:
    def __init__(self):
        self.updates = 0
        self.tasks = []

    def update(self):
        self.updates += 1

    def run_task(self, fn, *args):
        self.tasks.append((fn, args))


def reset_db_singletons():
    DBManager._profile_store = None
    DBManager._auth_service = None
    DBManager._profile_integrity = None
    DBManager._progress_service = None
    DBManager._lockout_store = None
    DBManager._profiles_migrated = False
    DBManager.current_username = GUEST_USERNAME


class LoginViewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.env_patch = patch.dict(os.environ, {"APPDATA": self.tmp.name}, clear=False)
        self.env_patch.start()
        os.environ.pop("KOTOBA_MIGRATE_LEGACY_PROFILES", None)
        reset_db_singletons()
        self.page = DummyPage()
        self.state = {}
        self.navigated = []
        self.view = LoginView(self.page, lambda route, **kwargs: self.navigated.append((route, kwargs)), self.state)

    def tearDown(self):
        self.env_patch.stop()
        self.tmp.cleanup()
        reset_db_singletons()

    def test_new_user_login_step_reveals_registration_fields(self):
        self.view.user_field.value = " Nuovo "
        self.view.pwd_field.value = "password1"

        self.view._on_login()

        self.assertEqual(self.view.user_field.value, "nuovo")
        self.assertEqual(self.view._pending_user, "nuovo")
        self.assertEqual(self.view._pending_pwd, "password1")
        self.assertTrue(self.view.register_btn.visible)
        self.assertFalse(self.view.primary_btn.visible)
        self.assertEqual(self.navigated, [])

    def test_registration_creates_account_sets_session_and_navigates(self):
        self.view.user_field.value = "nuovo"
        self.view.pwd_field.value = "password1"
        self.view._on_login()
        self.view.q_field.value = "Domanda?"
        self.view.a_field.value = "Risposta"

        self.view._on_register()

        self.assertTrue(DBManager.user_exists("nuovo"))
        self.assertEqual(get_current_user(self.state), "nuovo")
        self.assertTrue(self.state["just_registered"])
        self.assertEqual(self.navigated, [("dashboard", {})])
        self.assertIn("first_steps", DBManager.get_user_data("nuovo")["achievements"])

    def test_registration_still_navigates_if_first_achievement_unlock_fails(self):
        self.view.user_field.value = "nuovo"
        self.view.pwd_field.value = "password1"
        self.view._on_login()
        self.view.q_field.value = "Domanda?"
        self.view.a_field.value = "Risposta"

        with self.assertLogs("kotoba.ui.login", level="ERROR"):
            with patch.object(DBManager, "unlock_achievement", side_effect=RuntimeError("achievement catalog error")):
                self.view._on_register()

        self.assertTrue(DBManager.user_exists("nuovo"))
        self.assertEqual(get_current_user(self.state), "nuovo")
        self.assertEqual(self.navigated, [("dashboard", {})])

    def test_existing_user_login_sets_session_updates_last_login_and_clears_attempts(self):
        DBManager.create_account("utente", "password1", "q", "a")
        DBManager.record_failed_attempt("utente", "login")
        self.view.user_field.value = "UTENTE"
        self.view.pwd_field.value = "password1"

        self.view._on_login()

        data = DBManager.get_user_data("utente")
        self.assertEqual(get_current_user(self.state), "utente")
        self.assertEqual(self.navigated, [("dashboard", {})])
        self.assertEqual(DBManager.remaining_attempts("utente", "login"), DBManager.MAX_FAILED_ATTEMPTS)
        self.assertIn("last_login", data)

    def test_wrong_password_counts_attempt_and_shows_recovery(self):
        DBManager.create_account("utente", "password1", "q", "a")
        self.view.user_field.value = "utente"
        self.view.pwd_field.value = "wrongpass"

        self.view._on_login()

        self.assertTrue(self.view.recover_btn.visible)
        self.assertEqual(self.view._pending_user, "utente")
        self.assertEqual(DBManager.remaining_attempts("utente", "login"), DBManager.MAX_FAILED_ATTEMPTS - 1)
        self.assertEqual(self.navigated, [])

    def test_empty_recovery_answer_does_not_consume_attempt(self):
        DBManager.create_account("utente", "password1", "q", "a")
        self.view._pending_user = "utente"
        self.view._on_show_recovery()
        self.view.rec_ans_field.value = ""

        self.view._on_verify_recovery()

        self.assertEqual(DBManager.remaining_attempts("utente", "recovery"), DBManager.MAX_FAILED_ATTEMPTS)
        self.assertIn("Inserisci", self.view.msg.value)
        self.assertEqual(self.navigated, [])

    def test_recovery_success_can_save_new_password_and_login(self):
        DBManager.create_account("utente", "password1", "Domanda?", "Risposta")
        self.view._pending_user = "utente"
        self.view._on_show_recovery()
        self.view.rec_ans_field.value = "Risposta"

        self.view._on_verify_recovery()
        self.view.new_pwd_field.value = "newpass1"
        self.view._on_save_password()

        self.assertTrue(DBManager.verify_login("utente", "newpass1"))
        self.assertFalse(DBManager.verify_login("utente", "password1"))
        self.assertEqual(get_current_user(self.state), "utente")
        self.assertEqual(self.navigated, [("dashboard", {})])


if __name__ == "__main__":
    unittest.main()
