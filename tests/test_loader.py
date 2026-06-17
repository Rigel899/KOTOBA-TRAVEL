import unittest

from src.ui.components.loader import show_achievements


class LoaderTests(unittest.TestCase):
    def test_unknown_achievement_id_is_logged(self):
        with self.assertLogs("kotoba.ui.loader", level="WARNING") as logs:
            show_achievements(page=None, achievement_ids=["missing_achievement"])

        self.assertIn("missing_achievement", logs.output[0])


if __name__ == "__main__":
    unittest.main()
