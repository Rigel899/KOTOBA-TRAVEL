import unittest

from src.core.auth_service import AuthService
from src.core.profile_factory import build_default_profile
from src.core.security import PasswordHasher


def _normalize(username: str) -> str:
    return (username or "").strip().lower()


def _canonical_or_raise(username: str) -> str:
    username = _normalize(username)
    if not username:
        raise ValueError("Inserisci un nome utente.")
    return username


def _password_error(password: str) -> str | None:
    if not password:
        return "Inserisci una password."
    if len(password) < 8:
        return "Password troppo corta."
    return None


class AuthServiceTests(unittest.TestCase):
    def setUp(self):
        self.profiles = {}
        self.prepared = False

        def get_user_data(username: str):
            return self.profiles.get(_normalize(username))

        def update_user_data(username: str, data: dict) -> None:
            self.profiles[_normalize(username)] = data

        def create_user_data(username: str, data: dict) -> None:
            username = _normalize(username)
            if username in self.profiles:
                raise ValueError(f"Il nome utente '{username}' e gia in uso.")
            self.profiles[username] = data

        def prepare_profiles() -> None:
            self.prepared = True

        self.service = AuthService(
            _normalize,
            _canonical_or_raise,
            _password_error,
            PasswordHasher.hash_string,
            PasswordHasher.verify_secret,
            PasswordHasher.is_legacy_hash,
            get_user_data,
            update_user_data,
            create_user_data,
            prepare_profiles,
        )

    def test_create_account_hashes_secrets_and_prepares_profiles(self):
        self.service.create_account(" Nuovo ", "password1", "Domanda?", "Risposta")

        profile = self.profiles["nuovo"]
        self.assertTrue(self.prepared)
        self.assertEqual(profile["username"], "nuovo")
        self.assertTrue(profile["password_hash"].startswith("pbkdf2_sha256$"))
        self.assertTrue(profile["recovery_answer_hash"].startswith("pbkdf2_sha256$"))
        self.assertTrue(self.service.verify_login("NUOVO", "password1"))
        self.assertFalse(self.service.verify_login("nuovo", "sbagliata"))

    def test_create_account_rejects_short_password_before_writing(self):
        with self.assertRaises(ValueError):
            self.service.create_account("utente", "short", "q", "a")

        self.assertEqual(self.profiles, {})

    def test_create_account_rejects_duplicate_without_overwriting(self):
        self.service.create_account("utente", "password1", "q", "a")
        original_hash = self.profiles["utente"]["password_hash"]

        with self.assertRaises(ValueError):
            self.service.create_account("utente", "password2", "q2", "a2")

        self.assertEqual(self.profiles["utente"]["password_hash"], original_hash)

    def test_verify_login_upgrades_legacy_hash(self):
        self.profiles["legacy"] = build_default_profile(
            "legacy",
            PasswordHasher.hash_v1("password1"),
            "q",
            "answer-hash",
        )

        self.assertTrue(self.service.verify_login("legacy", "password1"))
        self.assertTrue(self.profiles["legacy"]["password_hash"].startswith("pbkdf2_sha256$"))

    def test_export_safe_profile_removes_sensitive_fields(self):
        self.service.create_account("export", "password1", "q", "a")

        export = self.service.export_safe_profile("export")

        self.assertIsNotNone(export)
        self.assertNotIn("password_hash", export)
        self.assertNotIn("recovery_answer_hash", export)
        self.assertIn("_export_note", export)
        self.assertIn("_exported_at", export)


if __name__ == "__main__":
    unittest.main()
