import tomllib
import unittest
from pathlib import Path

import flet
from PIL import Image

from src.main import APP_H, APP_W, ASSETS_DIR, MIN_H, MIN_W


ROOT = Path(__file__).resolve().parents[1]


class ProjectConfigTests(unittest.TestCase):
    def test_declared_dependencies_are_importable(self):
        self.assertTrue(flet.__version__)
        self.assertTrue(Image)

    def test_runtime_dependencies_are_pinned(self):
        requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
        runtime_lines = [line.strip() for line in requirements if line.strip() and not line.startswith("#")]

        self.assertIn("flet==0.85.1", runtime_lines)
        self.assertIn("pillow==12.2.0", runtime_lines)
        self.assertFalse(any(">=" in line or "~=" in line for line in runtime_lines))

    def test_flet_project_metadata_and_icon_exist(self):
        data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        app = data["tool"]["flet"]["app"]
        icon_path = ROOT / app["windows"]["icon"]

        self.assertEqual(app["name"], "Kotoba Travel")
        self.assertEqual(app["version"], "1.0.0")
        self.assertTrue(icon_path.exists())
        self.assertGreater(icon_path.stat().st_size, 0)

    def test_runtime_assets_dir_and_primary_icons_exist(self):
        assets_dir = Path(ASSETS_DIR)

        self.assertTrue(assets_dir.exists())
        self.assertTrue((assets_dir / "image" / "icons" / "icona.png").exists())
        self.assertTrue((assets_dir / "image" / "icons" / "icona.ico").exists())

    def test_window_constraints_are_consistent(self):
        self.assertGreaterEqual(APP_W, MIN_W)
        self.assertGreaterEqual(APP_H, MIN_H)
        self.assertGreaterEqual(MIN_W, 900)
        self.assertGreaterEqual(MIN_H, 600)


if __name__ == "__main__":
    unittest.main()
