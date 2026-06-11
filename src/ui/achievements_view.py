"""
ui/achievements_view.py - Galleria achievement.
"""
from __future__ import annotations

import flet as ft

from src.core.achievements import ACHIEVEMENTS, RARITY_COLOR
from src.core.db_manager import DBManager
from src.core.app_state import get_current_user
from src.core.settings import KotobaTheme as T
from src.ui.components.masthead import build_masthead
from src.ui.components.stage import centered_stage


class AchievementsView:
    def __init__(self, page: ft.Page, navigate, state: dict):
        self.page = page
        self.navigate = navigate
        self.state = state
        self.username = get_current_user(state)
        self.user_data = DBManager.get_user_data(self.username) or {}

    def _achievement_card(self, achievement_id: str, data: dict, unlocked: bool) -> ft.Control:
        rarity = data.get("rarity", "comune")
        accent = RARITY_COLOR.get(rarity, T.TEXT_M)
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
                                        rarity.upper(),
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
        total = len(ACHIEVEMENTS)
        unlocked_count = len([ach_id for ach_id in ACHIEVEMENTS if ach_id in unlocked_ids])
        progress = unlocked_count / total if total else 0

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

        grid = ft.GridView(
            controls=[
                self._achievement_card(ach_id, data, ach_id in unlocked_ids)
                for ach_id, data in ACHIEVEMENTS.items()
            ],
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

        content = ft.Column([summary, grid], spacing=18, expand=True)
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
