"""
ui/achievements_view.py - Galleria achievement.
"""
from __future__ import annotations

import flet as ft

from src.core.achievements import (
    MODULE_LABELS,
    MODULE_ORDER,
    PLATINUM_ACHIEVEMENT,
    RARITY_COLOR,
    RARITY_ORDER,
    platinum_required_achievement_ids,
    visible_achievement_ids,
    visible_achievement_items,
)
from src.core.db_manager import DBManager
from src.core.app_state import get_current_user
from src.core.settings import KotobaTheme as T
from src.ui.components.loader import show_achievements
from src.ui.components.masthead import build_masthead
from src.ui.components.stage import centered_stage


class AchievementsView:
    ACHIEVEMENT_ICONS = {
        "first_steps": ft.Icons.EXPLORE_ROUNDED,
        "streak_5": ft.Icons.LOCAL_FIRE_DEPARTMENT_ROUNDED,
        "streak_10": ft.Icons.DIAMOND_ROUNDED,
        "quiz_5": ft.Icons.TRACK_CHANGES_ROUNDED,
        "quiz_25": ft.Icons.SHIELD_ROUNDED,
        "study_first": ft.Icons.MENU_BOOK_ROUNDED,
        "study_all": ft.Icons.SCHOOL_ROUNDED,
        "hiragana_perfect": ft.Icons.TEXT_FIELDS_ROUNDED,
        "katakana_perfect": ft.Icons.TEXT_FIELDS_ROUNDED,
        "mixed_perfect": ft.Icons.LANGUAGE_ROUNDED,
        "kanji_first": ft.Icons.BRUSH_ROUNDED,
        "kanji_perfect": ft.Icons.ARTICLE_ROUNDED,
        "vocab_first": ft.Icons.CHAT_BUBBLE_ROUNDED,
        "vocab_50": ft.Icons.LIBRARY_BOOKS_ROUNDED,
        "vocab_perfect": ft.Icons.FORUM_ROUNDED,
        "grammar_first": ft.Icons.AUTO_STORIES_ROUNDED,
        "grammar_perfect": ft.Icons.ACCOUNT_TREE_ROUNDED,
        "exam_first": ft.Icons.FACT_CHECK_ROUNDED,
        "exam_perfect_1": ft.Icons.VERIFIED_ROUNDED,
        "exam_perfect_5": ft.Icons.CARD_MEMBERSHIP_ROUNDED,
        "exam_perfect_10": ft.Icons.STARS_ROUNDED,
        "exam_master": ft.Icons.SPORTS_MARTIAL_ARTS_ROUNDED,
        "food_10": ft.Icons.RAMEN_DINING_ROUNDED,
        "places_5": ft.Icons.TRAVEL_EXPLORE_ROUNDED,
        "culture_all": ft.Icons.THEATER_COMEDY_ROUNDED,
        "history_all": ft.Icons.ACCOUNT_BALANCE_ROUNDED,
        "exploration_all": ft.Icons.EXPLORE_ROUNDED,
        PLATINUM_ACHIEVEMENT: ft.Icons.EMOJI_EVENTS_ROUNDED,
    }
    ACHIEVEMENT_ASSETS = {
        "quiz_25": "image/icons/achievements/samurai.svg",
        "history_all": "image/icons/achievements/torii.svg",
        "exploration_all": "image/icons/achievements/journey_complete.svg",
        "exam_master": "image/icons/achievements/black_belt.svg",
    }
    ACHIEVEMENT_MARKS = {
        "hiragana_perfect": "あ",
        "katakana_perfect": "ア",
        "mixed_perfect": "かな",
        "kanji_perfect": "漢",
        "exam_master": "黒帯",
    }

    def __init__(self, page: ft.Page, navigate, state: dict):
        self.page = page
        self.navigate = navigate
        self.state = state
        self.username = get_current_user(state)
        self.user_data = DBManager.get_user_data(self.username) or {}
        self.sort_mode = "module"
        self.grid: ft.GridView | None = None
        self.sort_buttons: dict[str, ft.Button] = {}

    def _rarity_rank(self, rarity: str) -> int:
        try:
            return RARITY_ORDER.index(rarity)
        except ValueError:
            return len(RARITY_ORDER)

    def _module_rank(self, module: str) -> int:
        try:
            return MODULE_ORDER.index(module)
        except ValueError:
            return len(MODULE_ORDER)

    def _sync_platinum(self, unlocked_ids: set[str]) -> set[str]:
        if PLATINUM_ACHIEVEMENT in unlocked_ids:
            return unlocked_ids
        if not platinum_required_achievement_ids().issubset(unlocked_ids):
            return unlocked_ids
        if DBManager.unlock_achievement(self.username, PLATINUM_ACHIEVEMENT):
            unlocked_ids.add(PLATINUM_ACHIEVEMENT)
            self.user_data = DBManager.get_user_data(self.username) or self.user_data
            show_achievements(self.page, [PLATINUM_ACHIEVEMENT])
        return unlocked_ids

    def _sorted_items(self, unlocked_ids: set[str] | None = None) -> list[tuple[str, dict]]:
        items = visible_achievement_items(unlocked_ids)
        if self.sort_mode == "rarity":
            return sorted(
                items,
                key=lambda item: (
                    -(self._rarity_rank(item[1].get("rarity", "comune")) if item[1].get("rarity", "comune") in RARITY_ORDER else -1),
                    self._module_rank(item[1].get("module", "")),
                    item[1].get("title", item[0]),
                ),
            )
        return sorted(
            items,
            key=lambda item: (
                self._module_rank(item[1].get("module", "")),
                self._rarity_rank(item[1].get("rarity", "comune")),
                item[1].get("title", item[0]),
            ),
        )

    def _grid_controls(self, unlocked_ids: set[str]) -> list[ft.Control]:
        return [
            self._achievement_card(ach_id, data, ach_id in unlocked_ids)
            for ach_id, data in self._sorted_items(unlocked_ids)
        ]

    def _sort_button_style(self, active: bool) -> ft.ButtonStyle:
        return ft.ButtonStyle(
            bgcolor=T.GOLD if active else T.BG_SURF,
            color=T.BG_INK if active else T.TEXT,
            shape=ft.RoundedRectangleBorder(radius=6),
            side=ft.BorderSide(1, T.GOLD if active else T.BORDER),
            padding=ft.padding.symmetric(horizontal=14, vertical=10),
        )

    def _apply_sort_styles(self) -> None:
        for mode, button in self.sort_buttons.items():
            button.style = self._sort_button_style(mode == self.sort_mode)

    def _set_sort_mode(self, mode: str, unlocked_ids: set[str]) -> None:
        self.sort_mode = mode
        self._apply_sort_styles()
        if self.grid:
            self.grid.controls = self._grid_controls(unlocked_ids)
        self.page.update()

    def _achievement_badge_content(self, achievement_id: str, accent: str) -> ft.Control:
        asset = self.ACHIEVEMENT_ASSETS.get(achievement_id)
        if asset:
            return ft.Image(
                src=T.asset_path(asset),
                width=30,
                height=30,
                fit=ft.BoxFit.CONTAIN,
                color=accent,
                color_blend_mode=ft.BlendMode.SRC_IN,
                anti_alias=True,
            )
        mark = self.ACHIEVEMENT_MARKS.get(achievement_id)
        if mark:
            visual_length = len(mark.replace("\ufe0e", "").replace("\ufe0f", ""))
            return ft.Text(
                mark,
                size=23 if visual_length == 1 else 17,
                color=accent,
                font_family=T.FONT_JP,
                weight=ft.FontWeight.W_800,
            )
        icon = self.ACHIEVEMENT_ICONS.get(achievement_id, ft.Icons.MILITARY_TECH_ROUNDED)
        return ft.Icon(icon, color=accent, size=25)

    def _achievement_card(self, achievement_id: str, data: dict, unlocked: bool) -> ft.Control:
        rarity = data.get("rarity", "comune")
        accent = RARITY_COLOR.get(rarity, T.TEXT_M)
        module = MODULE_LABELS.get(data.get("module", ""), "Altro")
        opacity = 1.0 if unlocked else 0.45

        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Container(
                                width=44,
                                height=44,
                                alignment=ft.Alignment.CENTER,
                                bgcolor=T.BG_SURF,
                                border=ft.border.all(1.5, accent),
                                border_radius=8,
                                content=self._achievement_badge_content(achievement_id, accent),
                            ),
                            ft.Column(
                                [
                                    ft.Text(
                                        data.get("title", achievement_id),
                                        size=14,
                                        color=T.TEXT,
                                        font_family=T.FONT_DISPLAY,
                                        weight=ft.FontWeight.W_700,
                                        max_lines=2,
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                    ),
                                    ft.Text(
                                        f"{module} - {rarity.upper()}",
                                        size=10,
                                        color=accent,
                                        font_family=T.FONT_BODY,
                                        weight=ft.FontWeight.W_700,
                                    ),
                                ],
                                spacing=1,
                                expand=True,
                            ),
                            ft.Icon(
                                ft.Icons.CHECK_CIRCLE_ROUNDED if unlocked else ft.Icons.LOCK_OUTLINE_ROUNDED,
                                color=accent if unlocked else T.TEXT_M,
                                size=20,
                            ),
                        ],
                        spacing=12,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Text(
                        data.get("description", ""),
                        size=12,
                        color=T.TEXT_M,
                        font_family=T.FONT_BODY,
                        max_lines=3,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                ],
                spacing=12,
            ),
            bgcolor=T.BG_CARD,
            border=ft.border.all(1.5 if unlocked else 1, accent if unlocked else T.BORDER),
            border_radius=T.RADIUS,
            padding=ft.padding.all(16),
            opacity=opacity,
        )

    def _progress_masthead(self, unlocked_count: int, total: int, progress: float) -> ft.Control:
        return ft.Container(
            expand=True,
            bgcolor=T.BG_SURF,
            border=ft.border.all(1, T.BORDER),
            border_radius=T.RADIUS,
            padding=ft.padding.symmetric(horizontal=14, vertical=10),
            content=ft.Row(
                [
                    ft.Text(
                        f"{unlocked_count}/{total}",
                        size=22,
                        color=T.GOLD,
                        font_family=T.FONT_DISPLAY,
                        weight=ft.FontWeight.W_800,
                    ),
                    ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Text("Achievement sbloccati", size=13, color=T.TEXT, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_700),
                                    ft.Text(self.username, size=11, color=T.TEXT_M, font_family=T.FONT_BODY),
                                ],
                                spacing=10,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            ft.ProgressBar(value=progress, bar_height=6, color=T.GOLD, bgcolor=T.BORDER, border_radius=8),
                        ],
                        spacing=6,
                        expand=True,
                    ),
                ],
                spacing=14,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    def build(self) -> ft.Control:
        unlocked_ids = set(self.user_data.get("achievements", [])) if isinstance(self.user_data, dict) else set()
        unlocked_ids = self._sync_platinum(unlocked_ids)
        visible_ids = visible_achievement_ids(unlocked_ids)
        total = len(visible_ids)
        unlocked_count = len([ach_id for ach_id in visible_ids if ach_id in unlocked_ids])
        progress = unlocked_count / total if total else 0
        self.sort_buttons = {}

        def sort_button(label: str, mode: str, icon) -> ft.Button:
            button = ft.Button(
                label,
                icon=icon,
                style=self._sort_button_style(mode == self.sort_mode),
                on_click=lambda e, sort_mode=mode: self._set_sort_mode(sort_mode, unlocked_ids),
            )
            self.sort_buttons[mode] = button
            return button

        sort_controls = ft.Row(
            [
                ft.Text("Ordina per", size=12, color=T.TEXT_M, font_family=T.FONT_BODY),
                sort_button("Modulo", "module", ft.Icons.VIEW_MODULE_ROUNDED),
                sort_button("Rarità", "rarity", ft.Icons.MILITARY_TECH_ROUNDED),
            ],
            spacing=10,
            wrap=True,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        self.grid = ft.GridView(
            controls=self._grid_controls(unlocked_ids),
            max_extent=520,
            child_aspect_ratio=2.45,
            spacing=12,
            run_spacing=12,
            expand=True,
        )

        masthead = build_masthead(
            title="Achievement",
            subtitle="実績 - Jisseki",
            on_back=lambda e: self.navigate("dashboard"),
            trailing=self._progress_masthead(unlocked_count, total, progress),
            trailing_expand=True,
        )

        content = ft.Column([sort_controls, self.grid], spacing=18, expand=True)
        bg_path = T.bg_image()
        dec_image = ft.DecorationImage(src=bg_path, fit=ft.BoxFit.COVER, opacity=T.BG_OPACITY) if bg_path else None

        return ft.Container(
            bgcolor=T.BG_MAIN,
            image=dec_image,
            expand=True,
            content=ft.Column(
                [
                    masthead,
                    ft.Container(content=centered_stage(self.page, content, max_width=1440), expand=True, padding=ft.padding.all(24)),
                ],
                spacing=0,
                expand=True,
            ),
        )
