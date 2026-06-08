"""
ui/yugi/dojo_exam.py - Esamone misto del Dojo.
Combina Kana, Kanji, Vocabolario e Grammatica in una prova unica.
"""
from __future__ import annotations

import random

import flet as ft

from src.core.settings import KotobaTheme as T
from src.core.db_manager import DBManager
from src.ui.components.loader import show_achievements
from src.ui.components.stage import centered_stage
from src.ui.yugi.quiz_utils import build_quiz_data_error, build_quiz_question_view, max_correct_streak, schedule_auto_next

TOTAL_QUESTIONS = 20


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
        stats = [
            ("Kana", "仮", len(self.kana_pool), T.BELT_KANA),
            ("Kanji", "漢", len(self.kanji_pool), T.BELT_KANJI),
            ("Vocabolario", "語", len(self.vocab_pool), T.BELT_VOCAB),
            ("Grammatica", "文", len(self.grammar_pool), T.BELT_GRAMMAR),
        ]

        stat_cards = [
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text(mark, size=34, font_family=T.FONT_JP, color=color, weight=ft.FontWeight.W_700),
                        ft.Text(label, size=15, font_family=T.FONT_DISPLAY, color=T.TEXT, weight=ft.FontWeight.W_700),
                        ft.Text(f"{count} elementi", size=12, color=T.TEXT_M, font_family=T.FONT_BODY),
                        ft.Container(height=6),
                        self._belt(color, width=112),
                    ],
                    spacing=2,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                bgcolor=T.BG_CARD,
                border_radius=T.RADIUS,
                border=ft.border.all(1, T.BORDER),
                padding=ft.padding.all(16),
                expand=True,
                height=148,
            )
            for label, mark, count, color in stats
        ]

        def on_start_hover(e):
            is_hover = e.data == "true"
            e.control.border = ft.border.all(2 if is_hover else 1.5, T.GOLD)
            e.control.bgcolor = T.BELT_MASTER_HOVER if is_hover else T.BELT_MASTER
            e.control.update()

        start_panel = ft.Container(
            content=ft.Row(
                [
                    ft.Container(width=44),
                    ft.Column(
                        [
                            ft.Text("La Prova del Maestro", size=28, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_900, color=T.GOLD, text_align=ft.TextAlign.CENTER),
                            ft.Text(
                                "20 domande miste: lettura, significato e riconoscimento grammaticale.",
                                size=14,
                                font_family=T.FONT_BODY,
                                color=T.TEXT_M,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            ft.Container(height=8),
                            self._belt(T.BELT_MASTER, edge=T.GOLD, width=360, thickness=10),
                        ],
                        spacing=8,
                        expand=True,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Container(
                        width=44,
                        alignment=ft.Alignment.CENTER_RIGHT,
                        content=ft.Icon(ft.Icons.ARROW_FORWARD_IOS_ROUNDED, color=T.GOLD, size=22),
                    ),
                ],
                spacing=0,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=T.BELT_MASTER,
            border_radius=T.RADIUS,
            border=ft.border.all(1.5, T.GOLD),
            padding=ft.padding.all(28),
            animate=ft.Animation(150, ft.AnimationCurve.EASE_OUT),
            on_hover=on_start_hover,
            on_click=lambda e: self._start_exam(),
            ink=False,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        )

        return ft.Column(
            [
                ft.Row(stat_cards, spacing=14),
                ft.Container(expand=True),
                start_panel,
                ft.Container(expand=True),
            ],
            spacing=20,
            expand=True,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        )

    def _make_options(self, correct: str, all_values: list[str]) -> list[str]:
        wrong_pool = [value for value in set(all_values) if value and value != correct]
        wrong = random.sample(wrong_pool, min(3, len(wrong_pool)))
        while len(wrong) < 3:
            wrong.append("-")
        options = [correct] + wrong
        random.shuffle(options)
        return options

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
        unlocked = []
        if self.questions:
            unlocked = DBManager.record_quiz_result(
                DBManager.current_username,
                "exam",
                correct_count,
                total_questions=len(self.questions),
                max_streak=max_correct_streak(self.questions, self.user_answers, lambda question: question["correct"]),
            )

        if pct >= 90:
            grade, color, mark = "Maestro", T.GOLD, "極"
        elif pct >= 70:
            grade, color, mark = "Promosso", T.TEXT, "良"
        else:
            grade, color, mark = "Riprova", T.RED, "学"

        screen = ft.Column(
            [
                ft.Container(expand=True),
                ft.Container(
                    width=88,
                    height=88,
                    alignment=ft.Alignment.CENTER,
                    border=ft.border.all(3, color),
                    border_radius=12,
                    content=ft.Text(mark, size=42, font_family=T.FONT_JP, color=color, weight=ft.FontWeight.W_700),
                ),
                ft.Container(height=16),
                ft.Text("Esamone completato", size=25, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_900, color=T.TEXT),
                ft.Text(f"Punteggio: {correct_count} / {len(self.questions)}", size=16, color=T.TEXT_M),
                ft.Text(f"{grade} - {pct}%", size=18, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_700, color=color),
                ft.Container(height=30),
                ft.Row(
                    [
                        ft.ElevatedButton("Riprova esamone", style=ft.ButtonStyle(bgcolor=T.BG_CARD, color=T.TEXT), on_click=lambda e: self._start_exam()),
                        ft.ElevatedButton("Torna al Dojo", style=ft.ButtonStyle(bgcolor=T.GOLD, color=T.BG_INK), on_click=lambda e: self.navigate("dojo_hub")),
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
        self.content_area.content = centered_stage(self.page, screen, max_width=920, min_width=720)
        self._safe_update()
        show_achievements(self.page, unlocked)

    def build(self) -> ft.Control:
        if not (self.kana_pool or self.kanji_pool or self.vocab_pool or self.grammar_pool):
            self.content_area.content = build_quiz_data_error("sillabari.json / kanji.json / vocabolario.json / grammatica.json")
        else:
            self.content_area.content = centered_stage(self.page, self._setup_screen(), max_width=920, min_width=720, alignment=ft.Alignment.CENTER)
        masthead = ft.Container(
            content=ft.Row(
                [
                    ft.IconButton(icon=ft.Icons.ARROW_BACK_IOS_NEW_ROUNDED, icon_color=T.TEXT_M, icon_size=16, on_click=lambda e: self.navigate("dojo_hub")),
                    ft.Column(
                        [
                            ft.Text("La Prova del Maestro", size=T.FS_TITLE, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_900, color=T.GOLD),
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
