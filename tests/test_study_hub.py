import unittest

from src.core.settings import KotobaTheme as T
from src.ui.study.study_hub import StudyHub


class DummyPage:
    def run_task(self, fn, *args):
        return None


class StudyHubTests(unittest.TestCase):
    def test_study_tabs_use_belt_accents_without_split_kana_palette(self):
        hub = StudyHub(DummyPage(), lambda *a, **k: None, {})

        self.assertEqual(hub._tab_accent("hiragana"), T.BELT_KANA)
        self.assertEqual(hub._tab_accent("katakana"), T.BELT_KANA)
        self.assertEqual(hub._tab_accent("kanji"), T.BELT_KANJI)
        self.assertEqual(hub._tab_accent("vocab"), T.BELT_VOCAB)
        self.assertEqual(hub._tab_accent("grammar"), T.BELT_GRAMMAR)


if __name__ == "__main__":
    unittest.main()
