"""
ui/yugi/dojo_grammar.py - Addestramento Grammatica (Dojo).
Quiz rapido sulle particelle e sulle strutture base.
"""
from __future__ import annotations

import random

import flet as ft

from src.core.db_manager import DBManager
from src.core.settings import KotobaTheme as T
from src.ui.components.loader import show_achievements
from src.ui.components.stage import centered_stage
from src.ui.yugi.quiz_utils import build_quiz_data_error, build_quiz_question_view, max_correct_streak, schedule_auto_next

TOTAL_QUESTIONS = 10


class DojoGrammar:
    def __init__(self, page: ft.Page, navigate, state: dict):
        self.page = page
        self.navigate = navigate
        self.state = state

        raw_data = DBManager.load_json("grammatica.json") or []
        self.grammar_pool = [
            {
                "title": item.get("title", "").strip(),
                "emoji": item.get("emoji", "文").strip() or "文",
                "explanation": item.get("explanation", "").strip(),
                "example": item.get("example", "").strip(),
            }
            for item in raw_data
            if item.get("title") and item.get("explanation")
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

    def _setup_screen(self) -> ft.Control:
        topic_cards = []
        for item in self.grammar_pool:
            topic_cards.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Container(
                                width=36,
                                height=36,
                                alignment=ft.Alignment.CENTER,
                                border=ft.border.all(1.5, T.BELT_GRAMMAR),
                                border_radius=6,
                                content=ft.Text(
                                    item["emoji"],
                                    size=18,
                                    font_family=T.FONT_JP,
                                    color=T.BELT_GRAMMAR,
                                    weight=ft.FontWeight.W_700,
                                ),
                            ),
                            ft.Column(
                                [
                                    ft.Text(
                                        item["title"],
                                        size=14,
                                        font_family=T.FONT_DISPLAY,
                                        weight=ft.FontWeight.W_700,
                                        color=T.TEXT,
                                        max_lines=1,
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                    ),
                                    ft.Text(
                                        item["explanation"],
                                        size=11,
                                        font_family=T.FONT_BODY,
                                        color=T.TEXT_M,
                                        max_lines=2,
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                    ),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                        ],
                        spacing=12,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    bgcolor=T.BG_CARD,
                    border=ft.border.all(1, T.BORDER),
                    border_radius=T.RADIUS,
                    padding=ft.padding.symmetric(horizontal=14, vertical=12),
                )
            )

        start_card = ft.Container(
            content=ft.Row(
                [
                    ft.Container(
                        width=52,
                        height=52,
                        alignment=ft.Alignment.CENTER,
                        border=ft.border.all(2, T.BELT_GRAMMAR),
                        border_radius=8,
                        content=ft.Text("文", size=26, font_family=T.FONT_JP, color=T.BELT_GRAMMAR, weight=ft.FontWeight.W_700),
                    ),
                    ft.Column(
                        [
                            ft.Text("Allenamento Grammatica", size=20, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_700, color=T.TEXT),
                            ft.Text(
                                f"{len(self.grammar_pool)} regole disponibili - domande su esempi, particelle e uso.",
                                size=13,
                                font_family=T.FONT_BODY,
                                color=T.TEXT_M,
                            ),
                        ],
                        spacing=4,
                        expand=True,
                    ),
                    ft.ElevatedButton(
                        "Avvia",
                        icon=ft.Icons.PLAY_ARROW_ROUNDED,
                        style=ft.ButtonStyle(bgcolor=T.BELT_GRAMMAR, color=T.TEXT),
                        on_click=lambda e: self._start_quiz(),
                    ),
                ],
                spacing=16,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=T.BG_SURF,
            border_radius=T.RADIUS,
            border=ft.border.all(1.5, T.BELT_GRAMMAR),
            padding=ft.padding.all(20),
        )

        return ft.Column(
            [
                start_card,
                ft.Container(height=12),
                ft.GridView(
                    controls=topic_cards,
                    max_extent=520,
                    child_aspect_ratio=4.2,
                    spacing=10,
                    run_spacing=10,
                    expand=True,
                ),
            ],
            expand=True,
        )

    def _start_quiz(self):
        if not self.grammar_pool:
            return

        shuffled = list(self.grammar_pool)
        random.shuffle(shuffled)
        selected = shuffled[: min(TOTAL_QUESTIONS, len(shuffled))]
        titles = [item["title"] for item in self.grammar_pool]
        explanations = [item["explanation"] for item in self.grammar_pool]

        self.questions = []
        for idx, item in enumerate(selected):
            if idx % 2 == 0:
                correct = item["title"]
                wrong_pool = [title for title in titles if title != correct]
                wrong = random.sample(wrong_pool, min(3, len(wrong_pool)))
                while len(wrong) < 3:
                    wrong.append("-")
                options = [correct] + wrong
                random.shuffle(options)
                self.questions.append(
                    {
                        "label": "Riconosci la regola",
                        "prompt": item["example"],
                        "detail": "Quale punto grammaticale spiega questo esempio?",
                        "correct": correct,
                        "options": options,
                    }
                )
            else:
                correct = item["explanation"]
                wrong_pool = [exp for exp in explanations if exp != correct]
                wrong = random.sample(wrong_pool, min(3, len(wrong_pool)))
                while len(wrong) < 3:
                    wrong.append("-")
                options = [correct] + wrong
                random.shuffle(options)
                self.questions.append(
                    {
                        "label": item["title"],
                        "prompt": item["emoji"],
                        "detail": "Quale spiegazione è corretta?",
                        "correct": correct,
                        "options": options,
                    }
                )

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

        options = question["options"]
        screen = build_quiz_question_view(
            current_idx=self.current_idx,
            total=len(self.questions),
            prompt=question["prompt"],
            detail=question["detail"],
            badge=question["label"],
            options=options,
            correct=question["correct"],
            chosen=chosen_opt,
            already_answered=already_answered,
            accent=T.BELT_GRAMMAR,
            on_select=self._check_answer,
            on_prev=self._prev_q,
            on_next=self._next_q,
            prompt_size=30,
            prompt_font=T.FONT_JP,
            prompt_color=T.BELT_GRAMMAR,
            answer_text_size=14,
        )

        self.content_area.content = centered_stage(self.page, screen, max_width=920, min_width=640)
        self._safe_update()

    def _hover_btn(self, e, btn):
        if self.current_idx not in self.user_answers:
            is_hover = e.data == "true"
            btn.border = ft.border.all(1.5, T.BELT_GRAMMAR if is_hover else T.BORDER)
            btn.bgcolor = T.BG_HOVER if is_hover else T.BG_CARD
            btn.update()

    def _check_answer(self, chosen: str):
        idx_at_schedule = self.current_idx
        self.user_answers[idx_at_schedule] = chosen
        self._show_question()

        schedule_auto_next(
            self.page,
            0.65,
            self._is_mounted,
            lambda: self.current_idx == idx_at_schedule and self.user_answers.get(idx_at_schedule) == chosen,
            self._next_q,
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
        correct_count = sum(1 for i, q in enumerate(self.questions) if self.user_answers.get(i) == q["correct"])
        pct = int(correct_count / len(self.questions) * 100) if self.questions else 0
        if pct == 100:
            grade, color, mark = "Perfezione", T.BELT_GRAMMAR, "極"
        elif pct >= 80:
            grade, color, mark = "Ottimo lavoro", T.TEXT, "良"
        else:
            grade, color, mark = "Da ripassare", T.RED, "学"

        unlocked = []
        if self.questions:
            unlocked = DBManager.record_quiz_result(
                DBManager.current_username,
                "grammar",
                correct_count,
                total_questions=len(self.questions),
                max_streak=max_correct_streak(self.questions, self.user_answers, lambda question: question["correct"]),
            )

        screen = ft.Column(
            [
                ft.Container(expand=True),
                ft.Container(
                    width=80,
                    height=80,
                    alignment=ft.Alignment.CENTER,
                    border=ft.border.all(3, color),
                    border_radius=12,
                    content=ft.Text(mark, size=40, font_family=T.FONT_JP, color=color, weight=ft.FontWeight.W_700),
                ),
                ft.Container(height=16),
                ft.Text("Addestramento terminato", size=24, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_700, color=T.TEXT),
                ft.Text(f"Punteggio: {correct_count} / {len(self.questions)}", size=16, color=T.TEXT_M),
                ft.Text(grade, size=18, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_700, color=color),
                ft.Container(height=30),
                ft.Row(
                    [
                        ft.ElevatedButton("Riprova", style=ft.ButtonStyle(bgcolor=T.BG_CARD, color=T.TEXT), on_click=lambda e: self._start_quiz()),
                        ft.ElevatedButton("Torna alla bacheca", style=ft.ButtonStyle(bgcolor=T.BELT_GRAMMAR, color=T.TEXT), on_click=lambda e: self._go_back_to_start()),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=16,
                ),
                ft.Container(expand=True),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
            expand=True,
        )
        self.content_area.content = centered_stage(self.page, screen, max_width=820, min_width=640)
        self._safe_update()
        show_achievements(self.page, unlocked)

    def _go_back_to_start(self):
        self.content_area.content = centered_stage(self.page, self._setup_screen(), max_width=1040)
        self._safe_update()

    def build(self) -> ft.Control:
        if not self.grammar_pool:
            self.content_area.content = build_quiz_data_error("grammatica.json")
        else:
            self.content_area.content = centered_stage(self.page, self._setup_screen(), max_width=1040)
        masthead = ft.Container(
            content=ft.Row(
                [
                    ft.IconButton(icon=ft.Icons.ARROW_BACK_IOS_NEW_ROUNDED, icon_color=T.TEXT_M, icon_size=16, on_click=lambda e: self.navigate("dojo_hub")),
                    ft.Column(
                        [
                            ft.Text("Allenamento Grammatica", size=T.FS_TITLE, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_700, color=T.TEXT),
                            ft.Text("文法 - Bunpou", size=T.FS_SMALL, font_family=T.FONT_DISPLAY, italic=True, color=T.BELT_GRAMMAR),
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
