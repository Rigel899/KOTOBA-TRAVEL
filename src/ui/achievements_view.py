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
                                content=ft.Text(data.get("emoji", "?"), size=23),
                            ),
                            ft.Column(
                                [
                                    ft.Text(
                                        data.get("title", achievement_id),
                                        size=15,
                                        color=T.TEXT,
                                        font_family=T.FONT_DISPLAY,
                                        weight=ft.FontWeight.W_700,
                                        max_lines=1,
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

    def build(self) -> ft.Control:
        unlocked_ids = set(self.user_data.get("achievements", [])) if isinstance(self.user_data, dict) else set()
        unlocked_ids = self._sync_platinum(unlocked_ids)
        visible_ids = visible_achievement_ids(unlocked_ids)
        total = len(visible_ids)
        unlocked_count = len([ach_id for ach_id in visible_ids if ach_id in unlocked_ids])
        progress = unlocked_count / total if total else 0
        self.sort_buttons = {}

        summary = ft.Container(
            bgcolor=T.BG_SURF,
            border=ft.border.all(1, T.BORDER),
            border_radius=T.RADIUS,
            padding=ft.padding.symmetric(horizontal=18, vertical=16),
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text(
                                f"{unlocked_count}/{total}",
                                size=30,
                                color=T.GOLD,
                                font_family=T.FONT_DISPLAY,
                                weight=ft.FontWeight.W_800,
                            ),
                            ft.Column(
                                [
                                    ft.Text("Achievement sbloccati", size=15, color=T.TEXT, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_700),
                                    ft.Text(self.username, size=12, color=T.TEXT_M, font_family=T.FONT_BODY),
                                ],
                                spacing=1,
                                expand=True,
                            ),
                        ],
                        spacing=14,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.ProgressBar(value=progress, bar_height=7, color=T.GOLD, bgcolor=T.BORDER, border_radius=8),
                ],
                spacing=10,
            ),
        )

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
            max_extent=360,
            child_aspect_ratio=2.15,
            spacing=12,
            run_spacing=12,
            expand=True,
        )

        masthead = build_masthead(
            title="Achievement",
            subtitle="実績 - Jisseki",
            on_back=lambda e: self.navigate("dashboard"),
        )

        content = ft.Column([summary, sort_controls, self.grid], spacing=18, expand=True)
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
