import os
import tempfile
import unittest
from unittest.mock import patch

from src.core.app_state import GUEST_USERNAME, set_user
from src.core.db_manager import DBManager
from src.ui.yugi.dojo_exam import DojoExam
from src.ui.yugi.dojo_grammar import DojoGrammar
from src.ui.yugi.dojo_kana import DojoKana
from src.ui.yugi.dojo_kanji import DojoKanji
from src.ui.yugi.dojo_vocab import DojoVocab


class DummyPage:
    def __init__(self):
        self.tasks = []
        self.overlay = []
        self.snack_bar = None

    def update(self):
        pass

    def run_task(self, fn, *args):
        self.tasks.append((fn, args))
        return None


def _reset_db_singletons():
    DBManager._profile_store = None
    DBManager._auth_service = None
    DBManager._profile_integrity = None
    DBManager._progress_service = None
    DBManager._lockout_store = None
    DBManager._profiles_migrated = False
    DBManager.current_username = GUEST_USERNAME


class DojoBehaviorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.env_patch = patch.dict(os.environ, {"APPDATA": self.tmp.name}, clear=False)
        self.env_patch.start()
        os.environ.pop("KOTOBA_MIGRATE_LEGACY_PROFILES", None)
        _reset_db_singletons()
        DBManager.create_account("dojouser", "password1", "q", "a")
        self.state = {}
        set_user(self.state, "dojouser")
        self.page = DummyPage()

    def tearDown(self):
        self.env_patch.stop()
        self.tmp.cleanup()
        _reset_db_singletons()

    def _prepare_view(self, view):
        view._safe_update = lambda: None
        view._is_mounted = lambda: True
        return view

    def _assert_tuple_dojo_flow(self, view, start_fn, mode_key: str, patch_target: str):
        start_fn()
        self.assertGreater(len(view.questions), 0)
        first_correct = view.questions[0][1]
        self.assertIn(first_correct, view.questions[0][2])

        view._check_answer(first_correct)
        self.assertEqual(view.user_answers[0], first_correct)
        self.assertEqual(len(self.page.tasks), 1)

        view.user_answers = {index: question[1] for index, question in enumerate(view.questions)}
        view.current_idx = len(view.questions)
        with patch(patch_target):
            view._show_results()

        data = DBManager.get_user_data("dojouser")
        self.assertEqual(data["stats"]["quiz_modes"][mode_key], 1)
        self.assertEqual(data["stats"]["quiz_mode_total"][mode_key], len(view.questions))
        self.assertEqual(data["stats"]["quiz_mode_correct"][mode_key], len(view.questions))

    def _assert_dict_dojo_flow(self, view, start_fn, mode_key: str, patch_target: str):
        start_fn()
        self.assertGreater(len(view.questions), 0)
        first_correct = view.questions[0]["correct"]
        self.assertIn(first_correct, view.questions[0]["options"])

        view._check_answer(first_correct)
        self.assertEqual(view.user_answers[0], first_correct)
        self.assertEqual(len(self.page.tasks), 1)

        view.user_answers = {index: question["correct"] for index, question in enumerate(view.questions)}
        view.current_idx = len(view.questions)
        with patch(patch_target):
            view._show_results()

        data = DBManager.get_user_data("dojouser")
        self.assertEqual(data["stats"]["quiz_modes"][mode_key], 1)
        self.assertEqual(data["stats"]["quiz_mode_total"][mode_key], len(view.questions))
        self.assertEqual(data["stats"]["quiz_mode_correct"][mode_key], len(view.questions))

    def test_kana_quiz_flow_records_perfect_result(self):
        view = self._prepare_view(DojoKana(self.page, lambda *a, **k: None, self.state))
        view.mode = "hiragana"
        view.selected_group = "Tutte"

        self._assert_tuple_dojo_flow(
            view,
            view._start_quiz,
            "hiragana",
            "src.ui.yugi.dojo_kana.show_achievements",
        )

    def test_kanji_quiz_flow_records_perfect_result(self):
        view = self._prepare_view(DojoKanji(self.page, lambda *a, **k: None, self.state))

        self._assert_tuple_dojo_flow(
            view,
            lambda: view._start_quiz_with_group("Tutti"),
            "kanji",
            "src.ui.yugi.dojo_kanji.show_achievements",
        )

    def test_vocab_quiz_flow_records_perfect_result(self):
        view = self._prepare_view(DojoVocab(self.page, lambda *a, **k: None, self.state))

        self._assert_tuple_dojo_flow(
            view,
            lambda: view._start_quiz_with_group("Tutti"),
            "vocab",
            "src.ui.yugi.dojo_vocab.show_achievements",
        )

    def test_grammar_quiz_flow_records_perfect_result(self):
        view = self._prepare_view(DojoGrammar(self.page, lambda *a, **k: None, self.state))

        self._assert_dict_dojo_flow(
            view,
            view._start_quiz,
            "grammar",
            "src.ui.yugi.dojo_grammar.show_achievements",
        )

    def test_grammar_start_card_click_starts_quiz(self):
        view = self._prepare_view(DojoGrammar(self.page, lambda *a, **k: None, self.state))
        start_screen = view._setup_screen()
        start_card = start_screen.controls[0]

        self.assertIsNotNone(start_card.on_click)
        start_card.on_click(None)

        self.assertGreater(len(view.questions), 0)

    def test_exam_quiz_flow_records_perfect_result(self):
        view = self._prepare_view(DojoExam(self.page, lambda *a, **k: None, self.state))

        self._assert_dict_dojo_flow(
            view,
            view._start_exam,
            "exam",
            "src.ui.yugi.dojo_exam.show_achievements",
        )


if __name__ == "__main__":
    unittest.main()
