import unittest

from src.core.security import PasswordHasher


class PasswordHasherTests(unittest.TestCase):
    def test_pbkdf2_hash_verifies_only_original_secret(self):
        stored = PasswordHasher.hash_string("segreto", iterations=1000)

        self.assertTrue(stored.startswith("pbkdf2_sha256$1000$"))
        self.assertTrue(PasswordHasher.verify_secret("segreto", stored))
        self.assertFalse(PasswordHasher.verify_secret("sbagliato", stored))
        self.assertFalse(PasswordHasher.is_legacy_hash("segreto", stored))

    def test_legacy_hashes_are_still_verified_and_detected(self):
        old_v1 = PasswordHasher.hash_v1("segreto")
        old_fixed = PasswordHasher.hash_fixed_salt("segreto")

        self.assertTrue(PasswordHasher.verify_secret("segreto", old_v1))
        self.assertTrue(PasswordHasher.verify_secret("segreto", old_fixed))
        self.assertTrue(PasswordHasher.is_legacy_hash("segreto", old_v1))
        self.assertTrue(PasswordHasher.is_legacy_hash("segreto", old_fixed))
        self.assertFalse(PasswordHasher.verify_secret("sbagliato", old_v1))

    def test_malformed_pbkdf2_hash_is_rejected(self):
        self.assertFalse(PasswordHasher.verify_secret("x", "pbkdf2_sha256$bad$hash"))
        self.assertFalse(PasswordHasher.verify_secret("x", ""))


if __name__ == "__main__":
    unittest.main()
