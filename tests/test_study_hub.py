import unittest
from unittest.mock import patch

from src.core.db_manager import DBManager
from src.core.progress_service import STUDY_SECTION_STAT
from src.core.settings import KotobaTheme as T
from src.ui.study.study_hub import StudyHub


class DummyPage:
    def update(self):
        pass

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

    def test_study_section_tracking_uses_unique_section_ids(self):
        page = DummyPage()
        hub = StudyHub(page, lambda *a, **k: None, {"user": "studyuser"})

        with patch.object(DBManager, "increment_stat", return_value=["study_first"]) as increment:
            with patch("src.ui.study.study_hub.show_achievements") as notify:
                hub._track_study_section("kanji")

        increment.assert_called_once_with(
            "studyuser",
            STUDY_SECTION_STAT,
            unique_id="kanji",
        )
        notify.assert_called_once_with(page, ["study_first"])


if __name__ == "__main__":
    unittest.main()
