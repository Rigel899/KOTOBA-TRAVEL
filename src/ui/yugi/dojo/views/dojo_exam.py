"""
ui/yugi/dojo/views/dojo_exam.py - Prova Kotoba del Dojo.
Combina Kana, Kanji, Vocabolario e Grammatica in una prova unica.
"""
from __future__ import annotations

import logging
import random

import flet as ft

from src.core.compat import icon_btn
from src.core.settings import KotobaTheme as T
from src.core.app_state import get_current_user
from src.core.db_manager import DBManager
from src.ui.components.loader import show_achievements
from src.ui.components.stage import centered_stage
from src.ui.yugi.dojo.quiz.quiz_utils import (
    answer_and_schedule_next,
    build_quiz_data_error,
    build_quiz_question_view,
    build_quiz_result_view,
    count_correct_answers,
    make_choice_options,
    max_correct_streak,
    percent_score,
)

TOTAL_QUESTIONS = 20
_log = logging.getLogger("kotoba.ui.dojo_exam")


class DojoExam:
    def __init__(self, page: ft.Page, navigate, state: dict):
        self.page = page
        self.navigate = navigate
        self.state = state

        kana_data = DBManager.load_json("sillabari.json") or []
        kanji_data = DBManager.load_json("kanji.json") or []
        vocab_data = DBManager.load_json("vocabolario.json") or []
        grammar_data = DBManager.load_json("grammatica.json") or []

        self.kana_pool = [
            (item.get("word", ""), item.get("pronunciation", ""))
            for item in kana_data
            if item.get("word") and item.get("pronunciation")
        ]
        self.kanji_pool = [
            (item.get("word", ""), item.get("meaning", ""), item.get("reading", ""))
            for item in kanji_data
            if item.get("word") and item.get("meaning")
        ]
        self.vocab_pool = [
            (item.get("word", ""), item.get("meaning", ""), item.get("reading", ""))
            for item in vocab_data
            if item.get("word") and item.get("meaning")
        ]
        self.grammar_pool = [
            (item.get("title", ""), item.get("example", ""), item.get("explanation", ""))
            for item in grammar_data
            if item.get("title") and item.get("example")
        ]

        self.questions: list[dict] = []
        self.user_answers: dict[int, str] = {}
        self.current_idx = 0
        self.content_area = ft.Container(expand=True)

    def _safe_update(self):
        try:
            self.content_area.update()
        except RuntimeError:
            pass

    def _is_mounted(self) -> bool:
        try:
            return self.content_area.page is not None
        except RuntimeError:
            return False

    def _belt(self, color: str, edge: str | None = None, width: int = 136, thickness: int = 7) -> ft.Control:
        edge_color = edge or color

        def band(width_value: int) -> ft.Control:
            return ft.Container(
                width=width_value,
                height=thickness,
                bgcolor=color,
                border=ft.border.all(1, edge_color),
                border_radius=4,
            )

        def tail(width_value: int) -> ft.Control:
            return ft.Container(
                width=width_value,
                height=6,
                bgcolor=color,
                border=ft.border.all(1, edge_color),
                border_radius=3,
            )

        side_width = max(28, int((width - 78) / 2))
        return ft.Container(
            width=width,
            content=ft.Row(
                [
                    band(side_width),
                    ft.Container(width=4),
                    ft.Column([tail(18), tail(12)], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.END),
                    ft.Container(
                        width=20,
                        height=16,
                        bgcolor=color,
                        border=ft.border.all(1, edge_color),
                        border_radius=4,
                    ),
                    ft.Column([tail(12), tail(18)], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.START),
                    ft.Container(width=4),
                    band(side_width),
                ],
                spacing=0,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    def _setup_screen(self) -> ft.Control:
        # ── progress data ─────────────────────────────────────────────
        _ud = DBManager.get_user_data(get_current_user(self.state)) or {}
        _st = _ud.get("stats", {})
        _mc = _st.get("quiz_mode_correct", {})
        _mt = _st.get("quiz_mode_total", {})

        def _pct(*keys: str) -> float:
            c = sum(int(_mc.get(k, 0) or 0) for k in keys)
            t = sum(int(_mt.get(k, 0) or 0) for k in keys)
            return c / t if t else 0.0

        categories: list[tuple[str, str, int, str, float]] = [
            ("Kana",        "仮", len(self.kana_pool),    T.BELT_KANA,    _pct("hiragana", "katakana", "mixed")),
            ("Kanji",       "漢", len(self.kanji_pool),   T.BELT_KANJI,   _pct("kanji")),
            ("Vocabolario", "語", len(self.vocab_pool),   T.BELT_VOCAB,   _pct("vocab")),
            ("Grammatica",  "文", len(self.grammar_pool), T.BELT_GRAMMAR, _pct("grammar")),
        ]

        # ── single row of 4 cards ──────────────────────────────────────
        def _stat_card(label: str, mark: str, count: int, color: str, pct: float) -> ft.Control:
            return ft.Container(
                content=ft.Column(
                    [
                        ft.Container(height=4, bgcolor=color),
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Text(mark, size=28, font_family=T.FONT_JP, color=color, weight=ft.FontWeight.W_700),
                                    ft.Text(label, size=13, font_family=T.FONT_DISPLAY, color=T.TEXT, weight=ft.FontWeight.W_700),
                                    ft.Text(f"{count} elementi", size=11, color=T.TEXT_M, font_family=T.FONT_BODY),
                                ],
                                spacing=2,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            expand=True,
                            alignment=ft.Alignment.CENTER,
                        ),
                    ],
                    spacing=0,
                    horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                ),
                bgcolor=T.BG_CARD,
                border_radius=T.RADIUS,
                border=ft.border.all(1, T.BORDER),
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                expand=True,
                height=100,
            )

        grid = ft.Row(
            [_stat_card(*cat) for cat in categories],
            spacing=12,
        )

        # ── progress bars ─────────────────────────────────────────────
        def _progress_row(label: str, color: str, pct: float) -> ft.Control:
            return ft.Row(
                [
                    ft.Text(label, size=12, font_family=T.FONT_DISPLAY, color=color,
                            weight=ft.FontWeight.W_700, width=90),
                    ft.Container(
                        content=ft.ProgressBar(value=pct, color=color, bgcolor=T.BORDER),
                        expand=True,
                        height=6,
                    ),
                    ft.Text(f"{int(pct * 100)}%", size=12, font_family=T.FONT_BODY,
                            color=color, weight=ft.FontWeight.W_700, width=34,
                            text_align=ft.TextAlign.RIGHT),
                ],
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )

        progress_section = ft.Container(
            content=ft.Column(
                [_progress_row(label, color, pct) for label, _, _, color, pct in categories],
                spacing=10,
            ),
            bgcolor=T.BG_CARD,
            border_radius=T.RADIUS,
            border=ft.border.all(1, T.BORDER),
            padding=ft.padding.all(16),
        )

        # ── CTA panel ─────────────────────────────────────────────────
        def on_start_hover(e):
            is_hover = e.data == "true"
            e.control.bgcolor = T.BG_SURF if is_hover else T.BG_CARD
            e.control.update()

        start_panel = ft.Container(
            content=ft.Row(
                [
                    ft.Container(
                        content=ft.Text("極", size=26, font_family=T.FONT_JP, color=T.GOLD,
                                       weight=ft.FontWeight.W_900),
                        width=52, height=52,
                        bgcolor=T.BG_SURF,
                        border_radius=10,
                        border=ft.border.all(1, T.GOLD),
                        alignment=ft.Alignment.CENTER,
                    ),
                    ft.Column(
                        [
                            ft.Text("Sfida finale — 20 domande", size=16, font_family=T.FONT_DISPLAY,
                                    weight=ft.FontWeight.W_900, color=T.GOLD),
                            ft.Text("Lettura, significato, grammatica", size=12, font_family=T.FONT_BODY,
                                    color=T.TEXT_M),
                        ],
                        spacing=3,
                        expand=True,
                        horizontal_alignment=ft.CrossAxisAlignment.START,
                    ),
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Icon(ft.Icons.PLAY_ARROW_ROUNDED, color="#FFFFFF", size=16),
                                ft.Text("Inizia", size=13, font_family=T.FONT_DISPLAY,
                                       weight=ft.FontWeight.W_700, color="#FFFFFF"),
                            ],
                            spacing=4,
                            tight=True,
                        ),
                        bgcolor=T.BELT_MASTER,
                        border_radius=8,
                        padding=ft.padding.symmetric(vertical=10, horizontal=16),
                    ),
                ],
                spacing=16,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=T.BG_CARD,
            border_radius=T.RADIUS,
            border=ft.border.all(2, T.GOLD),
            padding=ft.padding.symmetric(vertical=14, horizontal=18),
            animate=ft.Animation(150, ft.AnimationCurve.EASE_OUT),
            on_hover=on_start_hover,
            on_click=lambda e: self._start_exam(),
            ink=False,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        )

        return ft.Column(
            [
                grid,
                ft.Container(height=12),
                progress_section,
                ft.Container(height=12),
                start_panel,
            ],
            spacing=0,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        )

    def _make_options(self, correct: str, all_values: list[str]) -> list[str]:
        return make_choice_options(correct, all_values)

    def _start_exam(self):
        candidates: list[dict] = []

        kana_answers = [reading for _, reading in self.kana_pool]
        for kana, reading in random.sample(self.kana_pool, min(6, len(self.kana_pool))):
            candidates.append(
                {
                    "kind": "Kana",
                    "color": T.BELT_KANA,
                    "prompt": kana,
                    "detail": "Come si legge questo kana?",
                    "correct": reading,
                    "options": self._make_options(reading, kana_answers),
                }
            )

        kanji_answers = [meaning for _, meaning, _ in self.kanji_pool]
        for kanji, meaning, reading in random.sample(self.kanji_pool, min(5, len(self.kanji_pool))):
            candidates.append(
                {
                    "kind": "Kanji",
                    "color": T.BELT_KANJI,
                    "prompt": kanji,
                    "detail": f"Lettura: {reading}. Qual è il significato?",
                    "correct": meaning,
                    "options": self._make_options(meaning, kanji_answers),
                }
            )

        vocab_answers = [meaning for _, meaning, _ in self.vocab_pool]
        for word, meaning, reading in random.sample(self.vocab_pool, min(5, len(self.vocab_pool))):
            candidates.append(
                {
                    "kind": "Vocabolario",
                    "color": T.BELT_VOCAB,
                    "prompt": word,
                    "detail": f"Lettura: {reading}. Scegli la traduzione.",
                    "correct": meaning,
                    "options": self._make_options(meaning, vocab_answers),
                }
            )

        grammar_answers = [title for title, _, _ in self.grammar_pool]
        for title, example, _ in random.sample(self.grammar_pool, min(4, len(self.grammar_pool))):
            candidates.append(
                {
                    "kind": "Grammatica",
                    "color": T.BELT_GRAMMAR,
                    "prompt": example,
                    "detail": "Quale regola grammaticale riconosci?",
                    "correct": title,
                    "options": self._make_options(title, grammar_answers),
                }
            )

        random.shuffle(candidates)
        self.questions = candidates[:TOTAL_QUESTIONS]
        self.current_idx = 0
        self.user_answers = {}
        self._show_question()

    def _show_question(self):
        if self.current_idx >= len(self.questions):
            self._show_results()
            return

        question = self.questions[self.current_idx]
        already_answered = self.current_idx in self.user_answers
        chosen_opt = self.user_answers.get(self.current_idx)
        color = question["color"]
        prompt_size = 32 if "\n" in question["prompt"] else 48

        options = question["options"]
        screen = build_quiz_question_view(
            current_idx=self.current_idx,
            total=len(self.questions),
            prompt=question["prompt"],
            detail=question["detail"],
            badge=question["kind"],
            options=options,
            correct=question["correct"],
            chosen=chosen_opt,
            already_answered=already_answered,
            accent=color,
            on_select=self._check_answer,
            on_prev=self._prev_q,
            on_next=self._next_q,
            prompt_size=prompt_size,
            prompt_font=T.FONT_JP,
            prompt_color=color,
            answer_text_size=15,
        )

        self.content_area.content = centered_stage(self.page, screen, max_width=920, min_width=720)
        self._safe_update()

    def _check_answer(self, chosen: str):
        answer_and_schedule_next(
            self.page,
            get_current_idx=lambda: self.current_idx,
            user_answers=self.user_answers,
            chosen=chosen,
            render=self._show_question,
            is_mounted=self._is_mounted,
            advance=self._next_q,
            delay=0.65,
        )

    def _next_q(self):
        if self.current_idx < len(self.questions):
            self.current_idx += 1
            self._show_question()

    def _prev_q(self):
        if self.current_idx > 0:
            self.current_idx -= 1
            self._show_question()

    def _show_results(self):
        correct_count = count_correct_answers(self.questions, self.user_answers, lambda question: question["correct"])
        pct = percent_score(correct_count, len(self.questions))
        unlocked = []
        if self.questions:
            try:
                unlocked = DBManager.record_quiz_result(
                    get_current_user(self.state),
                    "exam",
                    correct_count,
                    total_questions=len(self.questions),
                    max_streak=max_correct_streak(self.questions, self.user_answers, lambda question: question["correct"]),
                )
            except Exception:
                _log.exception("Prova Kotoba result tracking failed")

        if pct >= 90:
            grade, color = "Maestro", T.GOLD
        elif pct >= 70:
            grade, color = "Promosso", T.GOLD
        else:
            grade, color = "Riprova", T.RED

        screen = build_quiz_result_view(
            title="Prova Kotoba completata",
            module_label="Prova Kotoba",
            mark="極",
            accent=T.GOLD,
            correct_count=correct_count,
            total_questions=len(self.questions),
            grade=grade,
            grade_color=color,
            primary_label="Riprova",
            on_primary=self._start_exam,
            secondary_label="Torna al Dojo",
            on_secondary=lambda: self.navigate("dojo_hub"),
        )
        self.content_area.content = centered_stage(self.page, screen, max_width=920, min_width=720)
        self._safe_update()
        try:
            show_achievements(self.page, unlocked)
        except Exception:
            _log.exception("Prova Kotoba achievement notification failed")

    def build(self) -> ft.Control:
        if not (self.kana_pool or self.kanji_pool or self.vocab_pool or self.grammar_pool):
            self.content_area.content = build_quiz_data_error("sillabari.json / kanji.json / vocabolario.json / grammatica.json")
        else:
            self.content_area.content = ft.Row(
                [
                    ft.Container(expand=1),
                    ft.Container(
                        content=self._setup_screen(),
                        expand=5,
                        alignment=ft.Alignment.CENTER,
                        padding=ft.padding.symmetric(vertical=24),
                    ),
                    ft.Container(expand=1),
                ],
                expand=True,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )
        masthead = ft.Container(
            content=ft.Row(
                [
                    icon_btn(ft.Icons.ARROW_BACK_IOS_NEW_ROUNDED, icon_color=T.TEXT_M, icon_size=16, on_click=lambda e: self.navigate("dojo_hub")),
                    ft.Column(
                        [
                            ft.Text("Prova Kotoba", size=T.FS_TITLE, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_900, color=T.GOLD),
                            ft.Text("総合試験 - Sougou shiken", size=T.FS_SMALL, font_family=T.FONT_DISPLAY, italic=True, color=T.TEXT_M),
                        ],
                        spacing=2,
                    ),
                ],
                spacing=16,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.only(left=24, top=20, right=24, bottom=16),
            border=ft.border.only(bottom=ft.BorderSide(1, T.BORDER)),
        )
        return ft.Container(
            bgcolor=T.BG_MAIN,
            expand=True,
            content=ft.Column(
                [
                    masthead,
                    ft.Container(content=self.content_area, expand=True, padding=ft.padding.all(28)),
                ],
                spacing=0,
                expand=True,
            ),
        )
