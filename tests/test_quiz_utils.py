import unittest

import flet as ft

from src.ui.yugi.dojo.quiz.quiz_utils import (
    answer_and_schedule_next,
    build_quiz_result_view,
    color_with_alpha,
    count_correct_answers,
    make_choice_options,
    max_correct_streak,
    percent_score,
)


class DummyPage:
    def __init__(self):
        self.tasks = []

    def run_task(self, fn, *args):
        self.tasks.append((fn, args))


class QuizUtilsTests(unittest.TestCase):
    def test_make_choice_options_includes_correct_and_three_unique_distractors(self):
        options = make_choice_options("a", ["a", "b", "c", "d", "e"])

        self.assertEqual(len(options), 4)
        self.assertIn("a", options)
        self.assertEqual(len(set(options)), 4)

    def test_make_choice_options_pads_when_distractors_are_missing(self):
        options = make_choice_options("a", ["a", "b"], placeholder="—")

        self.assertEqual(len(options), 4)
        self.assertIn("a", options)
        self.assertIn("b", options)
        self.assertEqual(options.count("—"), 2)

    def test_make_choice_options_can_compare_case_insensitively(self):
        options = make_choice_options("Casa", ["casa", "CASA", "mare", "sole"], case_sensitive=False)

        self.assertIn("Casa", options)
        self.assertNotIn("casa", options)
        self.assertNotIn("CASA", options)

    def test_count_percent_and_streak_use_real_answers(self):
        questions = [
            {"correct": "a"},
            {"correct": "b"},
            {"correct": "c"},
            {"correct": "d"},
        ]
        answers = {0: "a", 1: "b", 2: "x", 3: "d"}

        self.assertEqual(count_correct_answers(questions, answers, lambda q: q["correct"]), 3)
        self.assertEqual(percent_score(3, 4), 75)
        self.assertEqual(percent_score(0, 0), 0)
        self.assertEqual(max_correct_streak(questions, answers, lambda q: q["correct"]), 2)

    def test_color_with_alpha_uses_flet_argb_format(self):
        self.assertEqual(color_with_alpha("#7FA88F", "22"), "#227FA88F")
        self.assertEqual(color_with_alpha("not-a-hex", "22"), "not-a-hex")

    def test_answer_and_schedule_next_records_answer_renders_and_schedules(self):
        page = DummyPage()
        answers = {}
        current_idx = 1
        calls = []

        answer_and_schedule_next(
            page,
            get_current_idx=lambda: current_idx,
            user_answers=answers,
            chosen="risposta",
            render=lambda: calls.append("render"),
            is_mounted=lambda: True,
            advance=lambda: calls.append("advance"),
            delay=0.1,
        )

        self.assertEqual(answers, {1: "risposta"})
        self.assertEqual(calls, ["render"])
        self.assertEqual(len(page.tasks), 1)

    def test_build_quiz_result_view_returns_control(self):
        control = build_quiz_result_view(
            title="Addestramento terminato",
            module_label="Kanji",
            mark="漢",
            accent="#7FA88F",
            correct_count=8,
            total_questions=10,
            grade="Ottimo lavoro",
            grade_color="#7FA88F",
            primary_label="Riprova",
            on_primary=lambda: None,
            secondary_label="Torna",
            on_secondary=lambda: None,
        )

        self.assertIsInstance(control, ft.Control)


if __name__ == "__main__":
    unittest.main()
