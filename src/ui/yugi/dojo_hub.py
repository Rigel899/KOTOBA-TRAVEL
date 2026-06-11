"""
ui/yugi/dojo_hub.py - Il percorso del Dojo.
"""
from __future__ import annotations

import src.core.compat
import flet as ft

from src.core.settings import KotobaTheme as T
from src.ui.components.stage import centered_stage, stage_width


class DojoHub:
    def __init__(self, page: ft.Page, navigate, state: dict):
        self.page = page
        self.navigate = navigate
        self.state = state

    def _section_title(self, title: str, color: str = T.GOLD) -> ft.Control:
        return ft.Row(
            [
                ft.Container(width=4, height=20, bgcolor=color, border_radius=3),
                ft.Text(title, size=18, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_700, color=T.TEXT),
            ],
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _belt(self, color: str, edge: str | None = None, width: int | None = None, thickness: int = 8) -> ft.Control:
        edge_color = edge or color
        side_width = max(32, int((width - 78) / 2)) if width is not None else None

        def band(expand: bool = False, width: int | None = None) -> ft.Control:
            return ft.Container(
                expand=expand,
                width=width,
                height=thickness,
                bgcolor=color,
                border=ft.border.all(1, edge_color),
                border_radius=4,
            )

        def tail(width: int) -> ft.Control:
            return ft.Container(
                width=width,
                height=7,
                bgcolor=color,
                border=ft.border.all(1, edge_color),
                border_radius=3,
            )

        return ft.Container(
            width=width,
            content=ft.Row(
                [
                    band(expand=width is None, width=side_width),
                    ft.Container(width=6),
                    ft.Column(
                        [tail(22), tail(14)],
                        spacing=2,
                        horizontal_alignment=ft.CrossAxisAlignment.END,
                    ),
                    ft.Container(
                        width=22,
                        height=18,
                        bgcolor=color,
                        border=ft.border.all(1, edge_color),
                        border_radius=4,
                    ),
                    ft.Column(
                        [tail(14), tail(22)],
                        spacing=2,
                        horizontal_alignment=ft.CrossAxisAlignment.START,
                    ),
                    ft.Container(width=6),
                    band(expand=width is None, width=side_width),
                ],
                spacing=0,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    def _module_card(self, title: str, subtitle: str, mark: str, route: str, color: str, width: int | None = None) -> ft.Control:
        def on_hover(e):
            is_hover = e.data == "true"
            e.control.border = ft.border.all(1.5 if is_hover else 1, color if is_hover else T.BORDER)
            e.control.bgcolor = T.BG_HOVER if is_hover else T.BG_CARD
            e.control.update()

        return ft.Container(
            expand=width is None,
            width=width,
            height=170,
            bgcolor=T.BG_CARD,
            border_radius=T.RADIUS,
            border=ft.border.all(1, T.BORDER),
            padding=ft.padding.all(18),
            animate=ft.Animation(150, ft.AnimationCurve.EASE_OUT),
            on_hover=on_hover,
            on_click=lambda e: self.navigate(route),
            ink=False,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Container(
                                width=48,
                                height=48,
                                alignment=ft.Alignment.CENTER,
                                border=ft.border.all(1.5, color),
                                border_radius=7,
                                content=ft.Text(
                                    mark,
                                    size=23,
                                    font_family=T.FONT_DISPLAY,
                                    color=color,
                                    weight=ft.FontWeight.W_700,
                                ),
                            ),
                            ft.Container(expand=True),
                            ft.Icon(ft.Icons.ARROW_FORWARD_IOS_ROUNDED, size=15, color=color, opacity=0.72),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Container(expand=True),
                    ft.Text(title, size=19, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_700, color=T.TEXT),
                    ft.Text(
                        subtitle,
                        size=12,
                        font_family=T.FONT_BODY,
                        color=T.TEXT_M,
                        max_lines=2,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    ft.Container(height=6),
                    ft.Row([self._belt(color, width=162), ft.Container(expand=True)], spacing=0),
                ],
                spacing=5,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            ),
        )

    def _boss_exam(self, route: str) -> ft.Control:
        def on_hover(e):
            is_hover = e.data == "true"
            e.control.border = ft.border.all(1.5 if is_hover else 1, T.GOLD)
            e.control.bgcolor = T.BELT_MASTER_HOVER if is_hover else T.BELT_MASTER
            e.control.update()

        return ft.Container(
            bgcolor=T.BELT_MASTER,
            border_radius=T.RADIUS,
            border=ft.border.all(1, T.GOLD),
            padding=ft.padding.all(24),
            height=160,
            animate=ft.Animation(180, ft.AnimationCurve.EASE_OUT),
            on_hover=on_hover,
            on_click=lambda e: self.navigate(route),
            ink=False,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Container(
                                width=58,
                                height=58,
                                alignment=ft.Alignment.CENTER,
                                border=ft.border.all(2, T.GOLD),
                                border_radius=8,
                                content=ft.Text("極", size=31, font_family=T.FONT_DISPLAY, color=T.GOLD, weight=ft.FontWeight.W_900),
                            ),
                            ft.Column(
                                [
                                    ft.Row(
                                        [
                                            ft.Text("Prova Kotoba", size=22, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_900, color=T.TEXT),
                                        ],
                                        spacing=12,
                                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                    ),
                                    ft.Text(
                                        "Prova completa su Kana, Kanji, Vocabolario e Grammatica.",
                                        size=13,
                                        font_family=T.FONT_BODY,
                                        color=T.TEXT_M,
                                    ),
                                ],
                                spacing=4,
                                expand=True,
                            ),
                            ft.Icon(ft.Icons.ARROW_FORWARD_IOS_ROUNDED, size=18, color=T.GOLD),
                        ],
                        spacing=16,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Container(height=12),
                    ft.Row([self._belt(T.BELT_MASTER, edge=T.GOLD, width=520, thickness=12)], alignment=ft.MainAxisAlignment.CENTER),
                ],
                spacing=8,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            ),
        )

    def build(self) -> ft.Control:
        masthead = ft.Container(
            content=ft.Row(
                [
                    ft.IconButton(
                        icon=ft.Icons.ARROW_BACK_IOS_NEW_ROUNDED,
                        icon_color=T.TEXT_M,
                        icon_size=16,
                        tooltip="Torna a Yugi",
                        on_click=lambda e: self.navigate("yugi"),
                    ),
                    ft.Text("Dojo", size=T.FS_TITLE, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_700, color=T.TEXT),
                    ft.Text("- Addestramento", size=T.FS_TITLE, font_family=T.FONT_DISPLAY, color=T.TEXT_M, italic=True),
                    ft.Container(expand=True),
                    ft.IconButton(
                        icon=ft.Icons.HOME_ROUNDED,
                        icon_color=T.TEXT_M,
                        icon_size=20,
                        tooltip="Home",
                        on_click=lambda e: self.navigate("dashboard"),
                    ),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.only(left=24, top=20, right=24, bottom=16),
            border=ft.border.only(bottom=ft.BorderSide(1, T.BORDER)),
        )

        module_defs = [
            ("Sillabari Kana", "Hiragana e Katakana", "仮", "dojo_kana", T.BELT_KANA),
            ("Kanji Base", "Caratteri essenziali", "漢", "dojo_kanji", T.BELT_KANJI),
            ("Vocabolario", "Letture e significati", "語", "dojo_vocab", T.BELT_VOCAB),
            ("Grammatica", "Particelle e strutture", "文", "dojo_grammar", T.BELT_GRAMMAR),
        ]
        current_stage_width = stage_width(self.page, max_width=1280, min_width=720)
        inner_width = max(320, current_stage_width - 48)
        gap = 14
        if inner_width >= 1040:
            card_width = int((inner_width - (gap * 3)) / 4)
            modules = [self._module_card(*definition, width=card_width) for definition in module_defs]
            training_rows = ft.Row(modules, spacing=gap)
        else:
            card_width = int((inner_width - gap) / 2)
            modules = [self._module_card(*definition, width=card_width) for definition in module_defs]
            training_rows = ft.Column(
                [
                    ft.Row(modules[:2], spacing=gap),
                    ft.Row(modules[2:], spacing=gap),
                ],
                spacing=gap,
            )

        body = ft.ListView(
            [
                self._section_title("Percorsi di allenamento", T.GOLD),
                ft.Container(height=12),
                training_rows,
                ft.Container(height=24),
                self._section_title("Sfida finale", T.GOLD),
                ft.Container(height=12),
                self._boss_exam("dojo_exam"),
            ],
            spacing=0,
            padding=ft.padding.only(left=24, right=24, top=28, bottom=28),
            expand=True,
        )

        return ft.Container(
            bgcolor=T.BG_MAIN,
            expand=True,
            content=ft.Column(
                [
                    masthead,
                    centered_stage(self.page, body, max_width=1280, min_width=720),
                ],
                spacing=0,
                expand=True,
            ),
        )
