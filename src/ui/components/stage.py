"""
ui/components/stage.py
Contenitori invisibili per mantenere i layout centrati e proporzionati
anche quando la finestra viene allargata.
"""
from __future__ import annotations

import flet as ft


def stage_width(page: ft.Page, max_width: int = 1040, gutter: int = 96, min_width: int = 720) -> int:
    page_width = getattr(page, "width", None)
    if not page_width and getattr(page, "window", None):
        page_width = getattr(page.window, "width", None)
    try:
        viewport = int(page_width or 1200)
    except (TypeError, ValueError):
        viewport = 1200
    available_width = max(320, viewport - gutter)
    if available_width < min_width:
        return available_width
    return min(max_width, available_width)


def centered_stage(
    page: ft.Page,
    content: ft.Control,
    max_width: int = 1040,
    gutter: int = 96,
    min_width: int = 720,
    expand: bool = True,
    alignment: ft.Alignment = ft.Alignment.TOP_CENTER,
) -> ft.Control:
    return ft.Container(
        expand=expand,
        alignment=alignment,
        content=ft.Container(
            width=stage_width(page, max_width=max_width, gutter=gutter, min_width=min_width),
            expand=expand,
            content=content,
        ),
    )


def scrollable_split_stage(
    page: ft.Page,
    content: ft.Control,
    *,
    min_width: int = 1100,
) -> ft.Control:
    """Mantiene leggibili i layout a due colonne sulle finestre strette."""
    width = max(
        min_width,
        stage_width(page, max_width=10000, gutter=0, min_width=min_width),
    )
    return ft.Row(
        [
            ft.Container(
                width=width,
                expand=False,
                content=content,
            )
        ],
        spacing=0,
        expand=True,
        scroll=ft.ScrollMode.AUTO,
    )
