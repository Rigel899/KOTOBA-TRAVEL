import unittest
from pathlib import Path


class FletCompatTests(unittest.TestCase):
    def test_deprecated_elevated_button_is_not_used(self):
        src_dir = Path(__file__).resolve().parents[1] / "src"
        deprecated_button = "ft." + "ElevatedButton("
        offenders = [
            str(path.relative_to(src_dir.parent))
            for path in src_dir.rglob("*.py")
            if deprecated_button in path.read_text(encoding="utf-8")
        ]

        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
