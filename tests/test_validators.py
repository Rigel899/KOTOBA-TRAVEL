import unittest

from src.core.validators import CredentialValidator


class CredentialValidatorTests(unittest.TestCase):
    def test_username_is_normalized_and_validated(self):
        self.assertEqual(CredentialValidator.normalize_username(" Marco_1 "), "marco_1")
        self.assertIsNone(CredentialValidator.username_validation_error("Marco_1"))
        self.assertIsNotNone(CredentialValidator.username_validation_error(""))
        self.assertIsNotNone(CredentialValidator.username_validation_error("ma"))
        self.assertIsNotNone(CredentialValidator.username_validation_error("mar-co"))
        self.assertEqual(CredentialValidator.canonical_username_or_raise("USER_1"), "user_1")

    def test_password_minimum_length_is_enforced(self):
        self.assertIsNotNone(CredentialValidator.password_validation_error(""))
        self.assertIsNotNone(CredentialValidator.password_validation_error("short"))
        self.assertIsNone(CredentialValidator.password_validation_error("password1"))


if __name__ == "__main__":
    unittest.main()
