"""
ui/yugi/yugi_hub.py - Bivio del gioco: allenamento e giochi futuri.
"""
from __future__ import annotations

import src.core.compat
import flet as ft

from src.core.settings import KotobaTheme as T


class YugiHub:
    def __init__(self, page: ft.Page, navigate, state: dict):
        self.page = page
        self.navigate = navigate
        self.state = state

    def _build_door(self, title: str, kanji: str, subtitle: str, color: str, route: str | None = None) -> ft.Control:
        is_enabled = route is not None

        def open_route(e, target=route):
            if target is not None:
                self.navigate(target)

        def on_hover(e):
            if not is_enabled:
                return
            is_hover = e.data == "true"
            e.control.border = ft.border.all(2, color if is_hover else T.BORDER)
            e.control.bgcolor = f"{color}11" if is_hover else T.BG_CARD
            e.control.update()

        return ft.Container(
            expand=True,
            bgcolor=T.BG_CARD,
            border_radius=T.RADIUS,
            border=ft.border.all(1, T.BORDER),
            padding=ft.padding.all(40),
            alignment=ft.Alignment(0, 0),
            opacity=1 if is_enabled else 0.78,
            on_hover=on_hover if is_enabled else None,
            on_click=open_route if is_enabled else None,
            ink=False,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS if is_enabled else None,
            animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
            content=ft.Column(
                [
                    ft.Text(kanji, size=80, font_family=T.FONT_DISPLAY, color=color, weight=ft.FontWeight.W_700),
                    ft.Container(height=10),
                    ft.Text(title, size=32, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_700, color=T.TEXT),
                    ft.Text(subtitle, size=14, font_family=T.FONT_BODY, color=T.TEXT_M, text_align=ft.TextAlign.CENTER),
                    ft.Container(height=18),
                    ft.Icon(
                        ft.Icons.ARROW_FORWARD_IOS_ROUNDED if is_enabled else ft.Icons.LOCK_OUTLINE_ROUNDED,
                        color=color,
                        size=18,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
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
                        tooltip="Dashboard",
                        on_click=lambda e: self.navigate("dashboard"),
                    ),
                    ft.Text("Scegli la tua Via", size=T.FS_TITLE, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_700, color=T.TEXT),
                    ft.Container(expand=True),
                    ft.Text("遊戯", size=24, font_family=T.FONT_DISPLAY, color=T.GOLD),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.only(left=24, top=20, right=24, bottom=16),
        )

        split_screen = ft.Row(
            [
                self._build_door(
                    "Dojo",
                    "道場",
                    "Allenamento, disciplina, ripetizione.\nPreparati prima della battaglia.",
                    T.GOLD,
                    "dojo_hub",
                ),
                self._build_door(
                    "Giochi",
                    "遊",
                    "Mini-giochi in arrivo.\nQuesta sezione verra aggiornata a breve.",
                    T.RED,
                ),
            ],
            spacing=24,
            expand=True,
        )

        return ft.Container(
            bgcolor=T.BG_MAIN,
            expand=True,
            content=ft.Column(
                [
                    masthead,
                    ft.Container(
                        content=split_screen,
                        expand=True,
                        padding=ft.padding.only(left=32, right=32, bottom=32, top=0),
                    ),
                ],
                spacing=0,
                expand=True,
            ),
        )
