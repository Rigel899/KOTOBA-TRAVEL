"""
Header riutilizzabile per le schermate principali.
Mantiene il look Sumi-e originale e centralizza titolo, sottotitolo e back button.
"""
from __future__ import annotations

from collections.abc import Callable

import src.core.compat  # Mantiene disponibili le API compat Flet anche nei test isolati.
import flet as ft

from src.core.settings import KotobaTheme as T


def build_masthead(
    title: str,
    subtitle: str | None = None,
    on_back: Callable | None = None,
    leading: ft.Control | None = None,
    trailing: ft.Control | None = None,
    trailing_expand: bool = False,
    title_color: str | None = None,
    title_weight: ft.FontWeight = ft.FontWeight.W_700,
) -> ft.Container:
    controls: list[ft.Control] = []

    if on_back:
        controls.append(
            ft.IconButton(
                icon=ft.Icons.ARROW_BACK_IOS_NEW_ROUNDED,
                icon_color=T.TEXT_M,
                icon_size=16,
                on_click=on_back,
            )
        )

    if leading:
        controls.append(leading)

    title_controls: list[ft.Control] = [
        ft.Text(
            title,
            size=T.FS_TITLE,
            font_family=T.FONT_DISPLAY,
            weight=title_weight,
            color=title_color or T.TEXT,
        )
    ]
    if subtitle:
        title_controls.append(
            ft.Text(
                subtitle,
                size=T.FS_SMALL,
                font_family=T.FONT_DISPLAY,
                italic=True,
                color=T.GOLD,
            )
        )

    controls.append(ft.Column(title_controls, spacing=2))

    if trailing:
        if trailing_expand:
            controls.append(trailing)
        else:
            controls.extend([ft.Container(expand=True), trailing])

    return ft.Container(
        content=ft.Row(
            controls,
            spacing=16,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.padding.only(left=22, top=14, right=22, bottom=12),
        border=ft.border.only(bottom=ft.BorderSide(1, T.BORDER)),
    )
