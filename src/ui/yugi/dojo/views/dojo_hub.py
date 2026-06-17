"""
ui/yugi/dojo/views/dojo_hub.py - Il percorso del Dojo.
"""
from __future__ import annotations

from src.core.compat import icon_btn  # noqa: F401
import flet as ft

from src.core.settings import KotobaTheme as T
from src.core.db_manager import DBManager
from src.core.app_state import get_current_user
from src.ui.components.stage import centered_stage, stage_width


class DojoHub:
    def __init__(self, page: ft.Page, navigate, state: dict):
        self.page = page
        self.navigate = navigate
        self.state = state
        username = get_current_user(state)
        user_data = DBManager.get_user_data(username) or {}
        self._stats: dict = user_data.get("stats", {}) if isinstance(user_data, dict) else {}

    def _quiz_accuracy(self, keys: list[str]) -> float:
        correct_map = self._stats.get("quiz_mode_correct", {})
        total_map = self._stats.get("quiz_mode_total", {})
        total_c = sum(int(correct_map.get(k, 0) or 0) for k in keys)
        total_q = sum(int(total_map.get(k, 0) or 0) for k in keys)
        return min(max(total_c / total_q, 0.0), 1.0) if total_q else 0.0

    def _perfect_count(self, keys: list[str]) -> int:
        perfect_map = self._stats.get("perfect_quiz_modes", {})
        return sum(int(perfect_map.get(k, 0) or 0) for k in keys)

    def _belts(self, count: int = 0, color: str = "") -> ft.Control:
        """5 segmenti: si riempiono con i completamenti perfetti usando il colore del modulo."""
        filled = min(max(count, 0), 5)
        return ft.Row(
            [
                ft.Container(
                    height=5,
                    border_radius=3,
                    expand=True,
                    bgcolor=color if i < filled else T.BORDER,
                )
                for i in range(5)
            ],
            spacing=5,
        )

    def _section_title(self, title: str, color: str = T.PURPLE) -> ft.Control:
        return ft.Row(
            [
                ft.Container(width=4, height=20, bgcolor=color, border_radius=3),
                ft.Text(title, size=18, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_700, color=T.TEXT),
            ],
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _module_card(self, title: str, subtitle: str, mark: str, route: str, color: str, quiz_keys: list[str], width: int | None = None) -> ft.Control:
        acc = self._quiz_accuracy(quiz_keys)
        acc_text = f"{int(acc * 100)}%" if acc > 0 else "—"
        perfects = self._perfect_count(quiz_keys)

        def on_hover(e):
            is_hover = e.data == "true"
            e.control.border = ft.border.all(1.5 if is_hover else 1, color if is_hover else T.BORDER)
            e.control.bgcolor = T.BG_HOVER if is_hover else T.BG_CARD
            e.control.update()

        return ft.Container(
            expand=width is None,
            width=width,
            height=180,
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
                    ft.Row(
                        [
                            ft.Text("PRECISIONE", size=9, color=T.TEXT_M, font_family=T.FONT_BODY),
                            ft.Container(expand=True),
                            ft.Text(acc_text, size=9, color=color, font_family=T.FONT_BODY, weight=ft.FontWeight.W_600),
                        ],
                    ),
                    ft.ProgressBar(value=acc, bar_height=4, color=color, bgcolor=T.BORDER, border_radius=3),
                    self._belts(perfects, color),
                ],
                spacing=4,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            ),
        )

    def _boss_exam(self, route: str) -> ft.Control:
        acc = self._quiz_accuracy(["exam"])
        acc_text = f"{int(acc * 100)}%" if acc > 0 else "—"
        perfects = self._perfect_count(["exam"])

        def on_hover(e):
            is_hover = e.data == "true"
            e.control.border = ft.border.all(2 if is_hover else 1.5, T.BELT_MASTER)
            e.control.bgcolor = T.BG_HOVER if is_hover else T.BG_CARD
            e.control.update()

        return ft.Container(
            bgcolor=T.BG_CARD,
            border_radius=T.RADIUS,
            border=ft.border.all(1.5, T.BELT_MASTER),
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
                                border=ft.border.all(2, T.BELT_MASTER),
                                border_radius=8,
                                content=ft.Text("極", size=31, font_family=T.FONT_DISPLAY, color=T.BELT_MASTER, weight=ft.FontWeight.W_900),
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
                            ft.Icon(ft.Icons.ARROW_FORWARD_IOS_ROUNDED, size=18, color=T.BELT_MASTER),
                        ],
                        spacing=16,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Row(
                        [
                            ft.Text("PRECISIONE", size=9, color=T.TEXT_M, font_family=T.FONT_BODY),
                            ft.Container(expand=True),
                            ft.Text(acc_text, size=9, color=T.BELT_MASTER, font_family=T.FONT_BODY, weight=ft.FontWeight.W_600),
                        ],
                    ),
                    ft.ProgressBar(value=acc, bar_height=4, color=T.BELT_MASTER, bgcolor=T.BORDER, border_radius=3),
                    self._belts(perfects, T.BELT_MASTER),
                ],
                spacing=8,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            ),
        )

    def build(self) -> ft.Control:
        masthead = ft.Container(
            content=ft.Row(
                [
                    icon_btn(ft.Icons.ARROW_BACK_IOS_NEW_ROUNDED, icon_color=T.TEXT_M, icon_size=16, tooltip="Torna a Yugi", on_click=lambda e: self.navigate("yugi")),
                    ft.Text("Dojo", size=T.FS_TITLE, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_700, color=T.TEXT),
                    ft.Text("- Addestramento", size=T.FS_TITLE, font_family=T.FONT_DISPLAY, color=T.TEXT_M, italic=True),
                    ft.Container(expand=True),
                    icon_btn(ft.Icons.HOME_ROUNDED, icon_color=T.TEXT_M, icon_size=20, tooltip="Home", on_click=lambda e: self.navigate("dashboard")),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.only(left=24, top=20, right=24, bottom=16),
            border=ft.border.only(bottom=ft.BorderSide(1, T.BORDER)),
        )

        module_defs = [
            ("Sillabari Kana", "Hiragana e Katakana", "仮", "dojo_kana", T.BELT_KANA,   ["hiragana", "katakana", "mixed"]),
            ("Kanji Base",     "Caratteri essenziali", "漢", "dojo_kanji", T.BELT_KANJI,  ["kanji"]),
            ("Vocabolario",    "Letture e significati", "語", "dojo_vocab", T.BELT_VOCAB,  ["vocab"]),
            ("Grammatica",     "Particelle e strutture", "文", "dojo_grammar", T.BELT_GRAMMAR, ["grammar"]),
        ]
        current_stage_width = stage_width(self.page, max_width=1280, min_width=720)
        inner_width = max(320, current_stage_width - 48)
        gap = 14
        if inner_width >= 1040:
            card_width = int((inner_width - (gap * 3)) / 4)
            modules = [self._module_card(*d, width=card_width) for d in module_defs]
            training_rows = ft.Row(modules, spacing=gap)
        else:
            card_width = int((inner_width - gap) / 2)
            modules = [self._module_card(*d, width=card_width) for d in module_defs]
            training_rows = ft.Column(
                [
                    ft.Row(modules[:2], spacing=gap),
                    ft.Row(modules[2:], spacing=gap),
                ],
                spacing=gap,
            )

        body = ft.ListView(
            [
                self._section_title("Percorsi di allenamento", T.PURPLE),
                ft.Container(height=12),
                training_rows,
                ft.Container(height=24),
                self._section_title("Sfida finale", T.PURPLE),
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
