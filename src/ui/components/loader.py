"""
ui/components/loader.py
Componenti riutilizzabili per notifiche e achievement.
"""
from __future__ import annotations

import logging

import flet as ft

from src.core.settings import KotobaTheme
from src.core.compat import show_snack


_log = logging.getLogger("kotoba.ui.loader")


def show_achievement(page: ft.Page, ach_data: dict) -> None:
    """
    Mostra un toast/snackbar stilizzato quando si sblocca un achievement.

    Parametri:
        page     - la pagina Flet corrente
        ach_data - dizionario dell'achievement da core.achievements.ACHIEVEMENTS
    """
    from src.core.achievements import RARITY_COLOR

    rarity = ach_data.get("rarity", "comune")
    accent = RARITY_COLOR.get(rarity, KotobaTheme.TEXT_M)
    emoji = ach_data.get("emoji", "🏆")
    title = ach_data.get("title", "Achievement sbloccato!")
    desc = ach_data.get("description", "")

    snack = ft.SnackBar(
        content=ft.Row(
            [
                ft.Container(
                    content=ft.Text(emoji, size=28),
                    width=44,
                    height=44,
                    bgcolor=KotobaTheme.BG_SURF,
                    border_radius=10,
                    border=ft.border.all(1, accent),
                    alignment=ft.Alignment(0, 0),
                ),
                ft.Column(
                    [
                        ft.Text(
                            f"🏆  {title}",
                            color=accent,
                            size=13,
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Text(desc, color=KotobaTheme.TEXT_M, size=11),
                    ],
                    spacing=2,
                    tight=True,
                ),
            ],
            spacing=14,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor=KotobaTheme.BG_CARD,
        duration=4000,
        show_close_icon=True,
        close_icon_color=KotobaTheme.TEXT_M,
    )
    show_snack(page, snack)


def show_achievements(page: ft.Page, achievement_ids: list[str]) -> None:
    """Mostra un toast per uno o piu achievement appena sbloccati."""
    if not achievement_ids:
        return

    from src.core.achievements import ACHIEVEMENTS, PLATINUM_ACHIEVEMENT

    unknown_ids = [ach_id for ach_id in achievement_ids if ach_id not in ACHIEVEMENTS]
    for ach_id in unknown_ids:
        _log.warning("unknown achievement id returned by progress logic: %s", ach_id)

    if PLATINUM_ACHIEVEMENT in achievement_ids:
        show_achievement(page, ACHIEVEMENTS[PLATINUM_ACHIEVEMENT])
        return

    unlocked = [ACHIEVEMENTS[ach_id] for ach_id in achievement_ids if ach_id in ACHIEVEMENTS]
    if not unlocked:
        return
    if len(unlocked) == 1:
        show_achievement(page, unlocked[0])
        return

    titles = ", ".join(item.get("title", "Trofeo") for item in unlocked[:3])
    if len(unlocked) > 3:
        titles += f" +{len(unlocked) - 3}"
    show_achievement(
        page,
        {
            "title": f"{len(unlocked)} trofei sbloccati",
            "description": titles,
            "emoji": "🏆",
            "rarity": "epico",
        },
    )
