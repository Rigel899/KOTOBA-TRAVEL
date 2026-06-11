import unittest

from src.core.profile_factory import build_default_profile


class ProfileFactoryTests(unittest.TestCase):
    def test_default_profile_contains_expected_progress_sections(self):
        profile = build_default_profile(
            "utente",
            "password-hash",
            "Domanda?",
            "answer-hash",
            timestamp="2026-01-02T03:04:05",
        )

        self.assertEqual(profile["username"], "utente")
        self.assertEqual(profile["password_hash"], "password-hash")
        self.assertEqual(profile["recovery_question"], "Domanda?")
        self.assertEqual(profile["recovery_answer_hash"], "answer-hash")
        self.assertEqual(profile["achievements"], [])
        self.assertEqual(profile["scores"]["hiragana"], 0)
        self.assertEqual(profile["stats"]["total_quizzes"], 0)
        self.assertEqual(profile["created_at"], "2026-01-02T03:04:05")
        self.assertEqual(profile["last_login"], "2026-01-02T03:04:05")

    def test_default_profile_returns_independent_nested_dicts(self):
        first = build_default_profile("a", "hash", "q", "answer-hash")
        second = build_default_profile("b", "hash", "q", "answer-hash")

        first["scores"]["hiragana"] = 9
        first["stats"]["quiz_modes"]["hiragana"] = 1

        self.assertEqual(second["scores"]["hiragana"], 0)
        self.assertEqual(second["stats"]["quiz_modes"], {})


if __name__ == "__main__":
    unittest.main()
