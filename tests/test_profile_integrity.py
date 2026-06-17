import unittest

from src.core.profile_integrity import ProfileIntegrity


class ProfileIntegrityTests(unittest.TestCase):
    def test_signed_profile_verifies_and_does_not_mutate_original(self):
        integrity = ProfileIntegrity()
        profile = {"username": "utente", "stats": {"total_quizzes": 0}}

        signed = integrity.signed_profile("Utente", profile)

        self.assertNotIn("_integrity", profile)
        self.assertIn("_integrity", signed)
        self.assertTrue(integrity.verify_profile("utente", signed))
        self.assertTrue(integrity.verify_profile("UTENTE", signed))

    def test_tampered_signed_profile_is_rejected(self):
        integrity = ProfileIntegrity()
        signed = integrity.signed_profile("utente", {"username": "utente", "stats": {"coins": 1}})

        signed["stats"]["coins"] = 999

        self.assertFalse(integrity.verify_profile("utente", signed))

    def test_unsigned_profile_policy_is_configurable(self):
        compatible = ProfileIntegrity(allow_unsigned_profiles=True)
        strict = ProfileIntegrity(allow_unsigned_profiles=False)
        profile = {"username": "legacy"}

        self.assertTrue(compatible.verify_profile("legacy", profile))
        self.assertFalse(strict.verify_profile("legacy", profile))


if __name__ == "__main__":
    unittest.main()
