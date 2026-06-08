"""
ui/stats_view.py - Statistiche dettagliate del profilo.
"""
from __future__ import annotations

import flet as ft

from src.core.db_manager import DBManager
from src.core.settings import KotobaTheme as T
from src.ui.components.masthead import build_masthead
from src.ui.components.stage import centered_stage


class StatsView:
    QUIZ_MODES = [
        ("Hiragana", "hiragana", T.RED),
        ("Katakana", "katakana", "#3b82f6"),
        ("Misto Kana", "mixed", T.GOLD),
        ("Kanji", "kanji", T.INDIGO),
        ("Vocabolario", "vocab", T.GREEN),
        ("Grammatica", "grammar", T.GOLD),
        ("Esamone", "exam", T.RED),
    ]
    MODE_DEFAULT_TOTALS = {"exam": 20}

    def __init__(self, page: ft.Page, navigate, state: dict):
        self.page = page
        self.navigate = navigate
        self.state = state
        self.username = state.get("user", DBManager.current_username)
        self.user_data = DBManager.current_user_data()

    def _metric(self, label: str, value: str, icon, color: str) -> ft.Control:
        return ft.Container(
            bgcolor=T.BG_CARD,
            border=ft.border.all(1, T.BORDER),
            border_radius=T.RADIUS,
            padding=ft.padding.all(16),
            expand=True,
            content=ft.Row(
                [
                    ft.Container(
                        width=42,
                        height=42,
                        alignment=ft.Alignment.CENTER,
                        bgcolor=f"#22{color[1:]}" if color.startswith("#") else T.BG_SURF,
                        border=ft.border.all(1.5, color),
                        border_radius=8,
                        content=ft.Icon(icon, color=color, size=22),
                    ),
                    ft.Column(
                        [
                            ft.Text(value, size=24, color=T.TEXT, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_800),
                            ft.Text(label, size=11, color=T.TEXT_M, font_family=T.FONT_BODY),
                        ],
                        spacing=0,
                    ),
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    def _mode_row(self, label: str, key: str, color: str, stats: dict, scores: dict) -> ft.Control:
        attempts = int(stats.get("quiz_modes", {}).get(key, 0) or 0)
        correct = int(stats.get("quiz_mode_correct", {}).get(key, 0) or 0)
        perfect = int(stats.get("perfect_quiz_modes", {}).get(key, 0) or 0)
        best = int(scores.get(key, scores.get(f"score_{key}", 0)) or 0)
        fallback_total = attempts * self.MODE_DEFAULT_TOTALS.get(key, 10)
        total_questions = int(stats.get("quiz_mode_total", {}).get(key, fallback_total) or fallback_total)
        accuracy = int((correct / total_questions) * 100) if total_questions else 0
        progress_value = min(max(accuracy / 100, 0), 1) if total_questions else 0

        return ft.Container(
            bgcolor=T.BG_CARD,
            border=ft.border.all(1, T.BORDER),
            border_radius=T.RADIUS_S,
            padding=ft.padding.symmetric(horizontal=14, vertical=12),
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text(label, size=14, color=T.TEXT, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_700, expand=True),
                            ft.Text(f"best {best}/10", size=12, color=color, font_family=T.FONT_BODY, weight=ft.FontWeight.W_700),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.ProgressBar(value=progress_value, bar_height=6, color=color, bgcolor=T.BORDER, border_radius=8),
                    ft.Row(
                        [
                            ft.Text(f"{attempts} quiz", size=11, color=T.TEXT_M, font_family=T.FONT_BODY),
                            ft.Text(f"{correct}/{total_questions} corrette", size=11, color=T.TEXT_M, font_family=T.FONT_BODY),
                            ft.Text(f"{perfect} perfetti", size=11, color=T.TEXT_M, font_family=T.FONT_BODY),
                            ft.Container(expand=True),
                            ft.Text(f"{accuracy}%", size=11, color=color, font_family=T.FONT_BODY, weight=ft.FontWeight.W_700),
                        ],
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ],
                spacing=8,
            ),
        )

    def build(self) -> ft.Control:
        if not self.user_data:
            self.navigate("/")
            return ft.Container(expand=True, bgcolor=T.BG_MAIN)

        stats = self.user_data.get("stats", {})
        scores = self.user_data.get("scores", {})
        total_quizzes = int(stats.get("total_quizzes", 0) or 0)
        total_questions = int(stats.get("total_questions", 0) or 0)
        total_correct = int(stats.get("total_correct", 0) or 0)
        accuracy = int((total_correct / total_questions) * 100) if total_questions else 0
        max_streak = int(stats.get("max_streak", 0) or 0)

        metrics = ft.Row(
            [
                self._metric("Quiz completati", str(total_quizzes), ft.Icons.QUERY_STATS_ROUNDED, T.GOLD),
                self._metric("Domande corrette", str(total_correct), ft.Icons.CHECK_CIRCLE_ROUNDED, T.GREEN),
                self._metric("Accuracy", f"{accuracy}%", ft.Icons.PERCENT_ROUNDED, T.INDIGO),
                self._metric("Streak massima", str(max_streak), ft.Icons.LOCAL_FIRE_DEPARTMENT_ROUNDED, T.RED),
            ],
            spacing=14,
        )

        mode_rows = [
            self._mode_row(label, key, color, stats, scores)
            for label, key, color in self.QUIZ_MODES
        ]

        exploration = ft.Container(
            bgcolor=T.BG_CARD,
            border=ft.border.all(1, T.BORDER),
            border_radius=T.RADIUS,
            padding=ft.padding.all(16),
            content=ft.Column(
                [
                    ft.Text("Esplorazione", size=18, color=T.TEXT, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_700),
                    ft.Row(
                        [
                            ft.Text(f"Cibo {stats.get('food_viewed', 0)}", size=12, color=T.TEXT_M, font_family=T.FONT_BODY),
                            ft.Text(f"Luoghi {stats.get('places_viewed', 0)}", size=12, color=T.TEXT_M, font_family=T.FONT_BODY),
                            ft.Text(f"Cultura {stats.get('culture_viewed', 0)}", size=12, color=T.TEXT_M, font_family=T.FONT_BODY),
                            ft.Text(f"Storia {stats.get('history_viewed', 0)}", size=12, color=T.TEXT_M, font_family=T.FONT_BODY),
                        ],
                        spacing=16,
                        wrap=True,
                    ),
                ],
                spacing=10,
            ),
        )

        content = ft.Column(
            [
                metrics,
                ft.Container(height=2),
                ft.Text("Modalità quiz", size=18, color=T.TEXT, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_700),
                *mode_rows,
                exploration,
            ],
            spacing=12,
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        )

        masthead = build_masthead(
            title="Statistiche",
            subtitle="記録 - Kiroku",
            on_back=lambda e: self.navigate("dashboard"),
        )
        bg_path = T.bg_image()
        dec_image = ft.DecorationImage(src=bg_path, fit=ft.BoxFit.COVER, opacity=T.BG_OPACITY) if bg_path else None

        return ft.Container(
            bgcolor=T.BG_MAIN,
            image=dec_image,
            expand=True,
            content=ft.Column(
                [
                    masthead,
                    ft.Container(content=centered_stage(self.page, content, max_width=1120), expand=True, padding=ft.padding.all(24)),
                ],
                spacing=0,
                expand=True,
            ),
        )
