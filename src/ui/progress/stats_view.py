"""
ui/stats_view.py - Statistiche dettagliate del profilo.
"""
from __future__ import annotations

import flet as ft

from src.core.achievements import visible_achievement_ids
from src.core.db_manager import DBManager
from src.core.progress_service import STUDY_REQUIRED_SECTIONS, STUDY_SECTION_STAT
from src.core.app_state import get_current_user
from src.core.settings import KotobaTheme as T
from src.ui.components.masthead import build_masthead
from src.ui.components.stage import centered_stage


class StatsView:
    QUIZ_MODES = [
        ("Hiragana", "hiragana", T.BELT_KANA),
        ("Katakana", "katakana", T.BELT_KANA),
        ("Misto Kana", "mixed", T.BELT_KANA),
        ("Kanji", "kanji", T.BELT_KANJI),
        ("Vocabolario", "vocab", T.BELT_VOCAB),
        ("Grammatica", "grammar", T.BELT_GRAMMAR),
        ("Prova Kotoba", "exam", T.GOLD),
    ]
    MODE_DEFAULT_TOTALS = {"exam": 20}
    EXPLORATION_ITEMS = [
        ("Cibo", "food_viewed", T.GOLD, ft.Icons.RAMEN_DINING_ROUNDED),
        ("Luoghi", "places_viewed", T.RED, ft.Icons.MAP_ROUNDED),
        ("Cultura", "culture_viewed", T.GREEN, ft.Icons.TEMPLE_BUDDHIST_ROUNDED),
        ("Storia", "history_viewed", T.INDIGO, ft.Icons.HISTORY_EDU_ROUNDED),
    ]
    STUDY_ITEMS = [
        ("Hiragana", "hiragana"),
        ("Katakana", "katakana"),
        ("Kanji", "kanji"),
        ("Vocabolario", "vocab"),
        ("Grammatica", "grammar"),
    ]

    def __init__(self, page: ft.Page, navigate, state: dict):
        self.page = page
        self.navigate = navigate
        self.state = state
        self.username = get_current_user(state)
        self.user_data = DBManager.get_user_data(self.username) or {}

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

    def _achievement_summary(self) -> ft.Control:
        unlocked_ids = set(self.user_data.get("achievements", [])) if isinstance(self.user_data, dict) else set()
        visible_ids = visible_achievement_ids(unlocked_ids)
        unlocked_count = len([ach_id for ach_id in visible_ids if ach_id in unlocked_ids])
        total = len(visible_ids)
        progress = unlocked_count / total if total else 0

        return ft.Container(
            bgcolor=T.BG_SURF,
            border=ft.border.all(1, T.BORDER),
            border_radius=T.RADIUS,
            padding=ft.padding.symmetric(horizontal=16, vertical=14),
            on_click=lambda e: self.navigate("achievements"),
            content=ft.Row(
                [
                    ft.Container(
                        width=42,
                        height=42,
                        alignment=ft.Alignment.CENTER,
                        bgcolor=T.BG_CARD,
                        border=ft.border.all(1.5, T.GOLD),
                        border_radius=8,
                        content=ft.Icon(ft.Icons.MILITARY_TECH_ROUNDED, color=T.GOLD, size=22),
                    ),
                    ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Text("Achievement", size=15, color=T.TEXT, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_700),
                                    ft.Text(f"{unlocked_count}/{total}", size=13, color=T.GOLD, font_family=T.FONT_BODY, weight=ft.FontWeight.W_700),
                                ],
                                spacing=10,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            ft.ProgressBar(value=progress, bar_height=6, color=T.GOLD, bgcolor=T.BORDER, border_radius=8),
                        ],
                        spacing=7,
                        expand=True,
                    ),
                    ft.Icon(ft.Icons.CHEVRON_RIGHT_ROUNDED, color=T.TEXT_M, size=22),
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    @staticmethod
    def _safe_int(value, default: int = 0) -> int:
        try:
            return int(value or default)
        except (TypeError, ValueError):
            return default

    def _content_total(self, filename: str) -> int:
        data = DBManager.load_json(filename)
        if isinstance(data, list):
            return len(data)
        if isinstance(data, dict) and isinstance(data.get("topics"), list):
            return len(data["topics"])
        return 0

    def _exploration_totals(self, stats: dict) -> dict[str, int]:
        stored = stats.get("exploration_totals", {}) if isinstance(stats, dict) else {}
        if not isinstance(stored, dict):
            stored = {}
        computed = {
            "food_viewed": self._content_total("food.json"),
            "places_viewed": self._content_total("explore.json") + self._content_total("museums.json"),
            "culture_viewed": self._content_total("culture.json"),
            "history_viewed": self._content_total("history.json"),
        }
        return {key: self._safe_int(stored.get(key), total) or total for key, total in computed.items()}

    def _exploration_row(self, label: str, key: str, color: str, icon, stats: dict, total: int) -> ft.Control:
        viewed = self._safe_int(stats.get(key, 0))
        clamped = min(viewed, total) if total else viewed
        progress = min(max(clamped / total, 0), 1) if total else 0
        return ft.Container(
            padding=ft.padding.symmetric(vertical=7),
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(icon, color=color, size=18),
                            ft.Text(label, size=13, color=T.TEXT, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_700, expand=True),
                            ft.Text(f"{clamped}/{total}" if total else str(clamped), size=12, color=T.TEXT_M, font_family=T.FONT_BODY),
                            ft.Text(f"{int(progress * 100)}%", size=12, color=color, font_family=T.FONT_BODY, weight=ft.FontWeight.W_700),
                        ],
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.ProgressBar(value=progress, bar_height=6, color=color, bgcolor=T.BORDER, border_radius=8),
                ],
                spacing=6,
            ),
        )

    def _exploration_summary(self, stats: dict) -> ft.Control:
        totals = self._exploration_totals(stats)
        total_items = sum(totals.values())
        viewed_items = sum(
            min(self._safe_int(stats.get(key, 0)), totals.get(key, 0))
            for _, key, _, _ in self.EXPLORATION_ITEMS
        )
        progress = min(max(viewed_items / total_items, 0), 1) if total_items else 0
        rows = [
            self._exploration_row(label, key, color, icon, stats, totals.get(key, 0))
            for label, key, color, icon in self.EXPLORATION_ITEMS
        ]

        return ft.Container(
            bgcolor=T.BG_CARD,
            border=ft.border.all(1, T.BORDER),
            border_radius=T.RADIUS,
            padding=ft.padding.all(16),
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text("Esplorazione", size=18, color=T.TEXT, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_700, expand=True),
                            ft.Text(f"{viewed_items}/{total_items}", size=13, color=T.GOLD, font_family=T.FONT_BODY, weight=ft.FontWeight.W_700),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.ProgressBar(value=progress, bar_height=7, color=T.GOLD, bgcolor=T.BORDER, border_radius=8),
                    *rows,
                ],
                spacing=8,
            ),
        )

    def _study_summary(self, stats: dict) -> ft.Control:
        unique_views = stats.get("unique_views", {}) if isinstance(stats, dict) else {}
        viewed_raw = unique_views.get(STUDY_SECTION_STAT, {}) if isinstance(unique_views, dict) else {}
        if isinstance(viewed_raw, dict):
            viewed_sections = set(viewed_raw)
        elif isinstance(viewed_raw, list):
            viewed_sections = set(viewed_raw)
        else:
            viewed_sections = set()

        fallback_count = self._safe_int(stats.get(STUDY_SECTION_STAT, 0))
        viewed_count = max(len(viewed_sections.intersection(STUDY_REQUIRED_SECTIONS)), fallback_count)
        viewed_count = min(viewed_count, len(STUDY_REQUIRED_SECTIONS))
        progress = viewed_count / len(STUDY_REQUIRED_SECTIONS) if STUDY_REQUIRED_SECTIONS else 0

        chips = []
        for label, key in self.STUDY_ITEMS:
            is_done = key in viewed_sections
            chips.append(
                ft.Container(
                    content=ft.Text(
                        label,
                        size=10,
                        color=T.BG_MAIN if is_done else T.TEXT_M,
                        font_family=T.FONT_BODY,
                        weight=ft.FontWeight.W_700 if is_done else ft.FontWeight.NORMAL,
                    ),
                    bgcolor=T.GOLD if is_done else T.BG_SURF,
                    border=ft.border.all(1, T.GOLD if is_done else T.BORDER),
                    border_radius=12,
                    padding=ft.padding.symmetric(horizontal=10, vertical=4),
                )
            )

        return ft.Container(
            bgcolor=T.BG_CARD,
            border=ft.border.all(1, T.BORDER),
            border_radius=T.RADIUS,
            padding=ft.padding.all(16),
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.AUTO_STORIES_ROUNDED, color=T.GOLD, size=19),
                            ft.Text("Studio", size=18, color=T.TEXT, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_700, expand=True),
                            ft.Text(f"{viewed_count}/{len(STUDY_REQUIRED_SECTIONS)}", size=13, color=T.GOLD, font_family=T.FONT_BODY, weight=ft.FontWeight.W_700),
                        ],
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.ProgressBar(value=progress, bar_height=7, color=T.GOLD, bgcolor=T.BORDER, border_radius=8),
                    ft.Row(chips, spacing=8, run_spacing=8, wrap=True),
                ],
                spacing=10,
            ),
        )

    def _best_score_label(self, key: str, stats: dict, scores: dict) -> str:
        best = self._safe_int(scores.get(key, scores.get(f"score_{key}", 0)))
        best_correct = self._safe_int(stats.get("quiz_mode_best_correct", {}).get(key, 0))
        best_total = self._safe_int(stats.get("quiz_mode_best_total", {}).get(key, 0))
        if best_correct and best_total:
            return f"PB {best_correct}/{best_total}"
        if key == "exam":
            return f"PB {round(best * 2)}/20"
        return f"PB {best}/10"

    def _mode_row(self, label: str, key: str, color: str, stats: dict, scores: dict) -> ft.Control:
        attempts = int(stats.get("quiz_modes", {}).get(key, 0) or 0)
        correct = int(stats.get("quiz_mode_correct", {}).get(key, 0) or 0)
        perfect = int(stats.get("perfect_quiz_modes", {}).get(key, 0) or 0)
        best_label = self._best_score_label(key, stats, scores)
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
                            ft.Text(best_label, size=12, color=color, font_family=T.FONT_BODY, weight=ft.FontWeight.W_700),
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

    async def _redirect_to_login(self):
        self.navigate("/")

    def build(self) -> ft.Control:
        if not self.user_data:
            self.page.run_task(self._redirect_to_login)
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

        content = ft.Column(
            [
                metrics,
                self._achievement_summary(),
                self._study_summary(stats),
                ft.Container(height=2),
                ft.Text("Modalità Quiz", size=18, color=T.TEXT, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_700),
                *mode_rows,
                self._exploration_summary(stats),
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
