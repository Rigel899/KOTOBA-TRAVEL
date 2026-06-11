"""
ui/dashboard_view.py - Dashboard principale.
Home compatta: due porte principali e sezioni viaggio centrate.
"""
from __future__ import annotations

import src.core.compat
import flet as ft

from src.core.db_manager import DBManager
from src.core.app_state import get_current_user
from src.core.settings import APP_VERSION, KotobaTheme as T


class DashboardView:
    QUIZ_MODES = [
        ("Hiragana", "hiragana"),
        ("Katakana", "katakana"),
        ("Misto Kana", "mixed"),
        ("Kanji", "kanji"),
        ("Vocabolario", "vocab"),
        ("Grammatica", "grammar"),
        ("Prova Kotoba", "exam"),
    ]
    LEGACY_PERFECT_ACHIEVEMENTS = {
        "hiragana": "hiragana_perfect",
        "katakana": "katakana_perfect",
        "mixed": "mixed_perfect",
        "kanji": "kanji_perfect",
        "vocab": "vocab_perfect",
        "grammar": "grammar_perfect",
    }

    def __init__(self, page: ft.Page, navigate, state: dict):
        self.page = page
        self.navigate = navigate
        self.state = state
        self.username = get_current_user(state)
        self.user_data = DBManager.get_user_data(self.username) or {}
        self._content_width_cache: tuple[int, int] | None = None
        self._scale_cache: tuple[int, float] | None = None

    def _page_width(self) -> int:
        page_width = getattr(self.page, "width", None)
        if not page_width and getattr(self.page, "window", None):
            page_width = getattr(self.page.window, "width", None)
        try:
            return int(page_width or 1200)
        except (TypeError, ValueError):
            return 1200

    def _dashboard_scale(self) -> float:
        page_width = self._page_width()
        if self._scale_cache is None or self._scale_cache[0] != page_width:
            scale = min(1.12, max(1.0, self._content_width(page_width) / 1120))
            self._scale_cache = (page_width, scale)
        return self._scale_cache[1]

    def _scaled(self, value: int | float) -> int:
        return int(round(value * self._dashboard_scale()))

    def _content_width(self, page_width: int | None = None) -> int:
        page_width = page_width if page_width is not None else self._page_width()
        if self._content_width_cache is not None and self._content_width_cache[0] == page_width:
            return self._content_width_cache[1]
        available_width = max(0, page_width - 96)
        growth = max(0, page_width - 1200) * 0.45
        target_width = min(1440, 1120 + growth)
        content_width = int(max(640, min(target_width, available_width)))
        self._content_width_cache = (page_width, content_width)
        return content_width

    def _tint(self, color: str, alpha: int = 24) -> str:
        """Flet usa #AARRGGBB, non #RRGGBBAA: crea una tinta trasparente corretta."""
        if isinstance(color, str) and color.startswith("#") and len(color) == 7:
            return f"#{alpha:02X}{color[1:]}"
        return color

    def _logo_asset(self, size: int = 54) -> ft.Control:
        fallback = ft.Container(
            width=size,
            height=size,
            alignment=ft.Alignment.CENTER,
            border=ft.border.all(1.5, T.GOLD),
            border_radius=max(10, size // 6),
            content=ft.Text("旅", size=max(27, size // 2), font_family=T.FONT_JP, color=T.GOLD, weight=ft.FontWeight.W_700),
        )
        return ft.Image(
            src=T.asset_path("image/icons/icona.png"),
            width=size,
            height=size,
            fit=ft.BoxFit.CONTAIN,
            error_content=fallback,
        )

    def _show_logo_preview(self, e=None) -> None:
        def close_dialog(ev=None):
            self._close_dialog(dialog)

        preview_size = min(620, max(360, self._page_width() - 220))
        dialog = ft.AlertDialog(
            modal=True,
            bgcolor=T.BG_CARD,
            title=ft.Row(
                [
                    ft.IconButton(
                        icon=ft.Icons.ARROW_BACK_ROUNDED,
                        icon_color=T.TEXT_M,
                        icon_size=22,
                        tooltip="Torna alla dashboard",
                        on_click=close_dialog,
                    ),
                    ft.Text("Kotoba Travel", size=22, color=T.TEXT, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_700),
                ],
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            content=ft.Container(
                width=preview_size,
                height=preview_size,
                alignment=ft.Alignment.CENTER,
                bgcolor=T.BG_INK,
                border=ft.border.all(1, T.BORDER),
                border_radius=T.RADIUS,
                padding=ft.padding.all(24),
                content=self._logo_asset(int(preview_size - 48)),
            ),
        )
        self._open_dialog(dialog)

    def _logo(self, size: int = 54) -> ft.Control:
        def on_hover(e):
            is_hover = e.data == "true"
            e.control.border = ft.border.all(1.5, T.GOLD if is_hover else "transparent")
            e.control.bgcolor = self._tint(T.GOLD, 12) if is_hover else "transparent"
            e.control.update()

        return ft.Container(
            width=size + 10,
            height=size + 10,
            alignment=ft.Alignment.CENTER,
            border=ft.border.all(1.5, "transparent"),
            border_radius=max(12, size // 6),
            bgcolor="transparent",
            content=self._logo_asset(size),
            tooltip="Ingrandisci immagine",
            on_click=self._show_logo_preview,
            on_hover=on_hover,
            ink=False,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            animate=ft.Animation(150, ft.AnimationCurve.EASE_OUT),
        )

    def _perfect_counts(self) -> dict[str, int]:
        stats = self.user_data.get("stats", {}) if isinstance(self.user_data, dict) else {}
        achievements = self.user_data.get("achievements", []) if isinstance(self.user_data, dict) else []
        perfect_modes = stats.get("perfect_quiz_modes", {}) if isinstance(stats, dict) else {}
        counts: dict[str, int] = {}

        for _, mode_key in self.QUIZ_MODES:
            value = int(perfect_modes.get(mode_key, 0) or 0) if isinstance(perfect_modes, dict) else 0
            legacy_id = self.LEGACY_PERFECT_ACHIEVEMENTS.get(mode_key)
            if legacy_id and legacy_id in achievements:
                value = max(value, 1)
            counts[mode_key] = value
        return counts

    def _trophy_state(self) -> tuple[int, str, str, int | None]:
        total = sum(self._perfect_counts().values())
        levels = [
            (50, "Platino", "#C7ECFF"),
            (25, "Oro", T.GOLD),
            (15, "Argento", "#C7CCD4"),
            (5, "Bronzo", "#B8793C"),
            (1, "Legno", "#8B5E3C"),
            (0, "Trofei", T.TEXT_M),
        ]
        label, color = "Trofei", T.TEXT_M
        for threshold, name, level_color in levels:
            if total >= threshold:
                label, color = name, level_color
                break
        next_target = next((target for target in (1, 5, 15, 25, 50) if total < target), None)
        return total, label, color, next_target

    def _trophy_button(self) -> ft.Control:
        total, label, color, _ = self._trophy_state()

        def on_hover(e):
            is_hover = e.data == "true"
            e.control.border = ft.border.all(1.5, color if is_hover else T.BORDER)
            e.control.bgcolor = self._tint(color, 18) if is_hover else T.BG_CARD
            e.control.update()

        return ft.Container(
            content=ft.Icon(ft.Icons.EMOJI_EVENTS_ROUNDED, color=color, size=28),
            width=54,
            height=54,
            alignment=ft.Alignment.CENTER,
            bgcolor=self._tint(color, 12) if total else T.BG_CARD,
            border=ft.border.all(1, T.BORDER),
            border_radius=27,
            ink=False,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            animate=ft.Animation(150, ft.AnimationCurve.EASE_OUT),
            tooltip=f"{total} trofei - {label}",
            on_click=self._show_trophy_progress,
            on_hover=on_hover,
        )

    def _open_dialog(self, dialog: ft.AlertDialog) -> None:
        if hasattr(self.page, "open"):
            self.page.open(dialog)
        elif hasattr(self.page, "show_dialog"):
            self.page.show_dialog(dialog)
        else:
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()

    def _close_dialog(self, dialog: ft.AlertDialog) -> None:
        if hasattr(self.page, "close"):
            self.page.close(dialog)
        elif hasattr(self.page, "pop_dialog"):
            self.page.pop_dialog()
        else:
            dialog.open = False
            self.page.update()

    def _best_score_label(self, mode_key: str, stats: dict, scores: dict) -> str:
        best = int(scores.get(mode_key, scores.get(f"score_{mode_key}", 0)) or 0)
        best_correct = int(stats.get("quiz_mode_best_correct", {}).get(mode_key, 0) or 0)
        best_total = int(stats.get("quiz_mode_best_total", {}).get(mode_key, 0) or 0)
        if best_correct and best_total:
            return f"PB {best_correct}/{best_total}"
        if mode_key == "exam":
            return f"PB {round(best * 2)}/20"
        return f"PB {best}/10"

    def _show_trophy_progress(self, e=None) -> None:
        counts = self._perfect_counts()
        total, label, color, next_target = self._trophy_state()
        scores = self.user_data.get("scores", {}) if isinstance(self.user_data, dict) else {}
        stats = self.user_data.get("stats", {}) if isinstance(self.user_data, dict) else {}

        rows: list[ft.Control] = []
        for mode_label, mode_key in self.QUIZ_MODES:
            rows.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Text(mode_label, size=13, color=T.TEXT, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_700, expand=True),
                            ft.Text(f"{counts.get(mode_key, 0)} perfetti", size=12, color=color, font_family=T.FONT_BODY),
                            ft.Text(self._best_score_label(mode_key, stats, scores), size=11, color=T.TEXT_M, font_family=T.FONT_BODY),
                        ],
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    bgcolor=T.BG_SURF,
                    border_radius=T.RADIUS_S,
                    padding=ft.padding.symmetric(horizontal=12, vertical=9),
                )
            )

        message = f"{total} quiz perfetti. Grado attuale: {label}."
        if next_target:
            message += f" Prossimo grado a {next_target}."
        progress_target = next_target or max(total, 1)
        progress_value = min(total / progress_target, 1) if progress_target else 0

        def close_dialog(ev=None):
            self._close_dialog(dialog)

        dialog = ft.AlertDialog(
            modal=True,
            bgcolor=T.BG_CARD,
            title=ft.Row(
                [
                    ft.IconButton(
                        icon=ft.Icons.ARROW_BACK_ROUNDED,
                        icon_color=T.TEXT_M,
                        icon_size=22,
                        tooltip="Torna alla dashboard",
                        on_click=close_dialog,
                    ),
                    ft.Container(
                        width=46,
                        height=46,
                        alignment=ft.Alignment.CENTER,
                        border=ft.border.all(1.5, color),
                        border_radius=12,
                        bgcolor=self._tint(color, 20),
                        content=ft.Icon(ft.Icons.EMOJI_EVENTS_ROUNDED, color=color, size=26),
                    ),
                    ft.Column(
                        [
                            ft.Text("Sala Trofei", size=22, color=T.TEXT, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_700),
                            ft.Text("quiz perfetti per categoria", size=12, color=T.TEXT_M, font_family=T.FONT_BODY),
                        ],
                        spacing=0,
                    ),
                    ft.Container(expand=True),
                ],
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            content=ft.Container(
                width=560,
                height=500,
                content=ft.Column(
                    [
                        ft.Container(
                            bgcolor=T.BG_SURF,
                            border=ft.border.all(1, T.BORDER),
                            border_radius=T.RADIUS,
                            padding=ft.padding.symmetric(horizontal=16, vertical=14),
                            content=ft.Column(
                                [
                                    ft.Row(
                                        [
                                            ft.Text(f"{total}", size=34, color=color, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_800),
                                            ft.Column(
                                                [
                                                    ft.Text(label, size=15, color=T.TEXT, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_700),
                                                    ft.Text(message, size=11, color=T.TEXT_M, font_family=T.FONT_BODY),
                                                ],
                                                spacing=1,
                                                expand=True,
                                            ),
                                        ],
                                        spacing=14,
                                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                    ),
                                    ft.ProgressBar(
                                        value=progress_value,
                                        bar_height=7,
                                        color=color,
                                        bgcolor=T.BORDER,
                                        border_radius=8,
                                    ),
                                ],
                                spacing=10,
                                tight=True,
                            ),
                        ),
                        ft.Container(height=10),
                        *rows,
                    ],
                    spacing=9,
                    scroll=ft.ScrollMode.AUTO,
                ),
            ),
        )
        self._open_dialog(dialog)

    def _maybe_show_onboarding(self) -> None:
        if not self.state.pop("just_registered", False):
            return

        def close_dialog(ev=None):
            self._close_dialog(dialog)

        def go(route: str):
            self._close_dialog(dialog)
            self.navigate(route)

        dialog = ft.AlertDialog(
            modal=True,
            bgcolor=T.BG_CARD,
            title=ft.Text("Benvenuto in Kotoba Travel", size=22, color=T.TEXT, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_700),
            content=ft.Container(
                width=520,
                content=ft.Column(
                    [
                        ft.Text("Scegli da dove iniziare il viaggio.", size=13, color=T.TEXT_M, font_family=T.FONT_BODY),
                        ft.Row(
                            [
                                ft.Button("Accademia", icon=ft.Icons.AUTO_STORIES_ROUNDED, style=ft.ButtonStyle(bgcolor=T.GOLD, color=T.BG_MAIN), on_click=lambda e: go("study")),
                                ft.Button("Yugi", icon=ft.Icons.SPORTS_MARTIAL_ARTS_ROUNDED, style=ft.ButtonStyle(bgcolor=T.RED, color=T.TEXT), on_click=lambda e: go("yugi")),
                                ft.Button("Achievement", icon=ft.Icons.MILITARY_TECH_ROUNDED, style=ft.ButtonStyle(bgcolor=T.BG_SURF, color=T.TEXT), on_click=lambda e: go("achievements")),
                            ],
                            spacing=10,
                            wrap=True,
                        ),
                    ],
                    spacing=16,
                    tight=True,
                ),
            ),
            actions=[
                ft.TextButton("Resto qui", style=ft.ButtonStyle(color=T.TEXT_M), on_click=close_dialog),
            ],
        )
        self._open_dialog(dialog)

    def _confirm_logout(self, e=None) -> None:
        def close_dialog(ev=None):
            self._close_dialog(dialog)

        def do_logout(ev=None):
            self._close_dialog(dialog)
            self.navigate("/")

        dialog = ft.AlertDialog(
            modal=True,
            bgcolor=T.BG_CARD,
            title=ft.Text("Disconnetti?", size=20, color=T.TEXT, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_700),
            content=ft.Text("Vuoi uscire dal profilo corrente e tornare al login?", size=13, color=T.TEXT_M, font_family=T.FONT_BODY),
            actions=[
                ft.TextButton("Annulla", style=ft.ButtonStyle(color=T.TEXT_M), on_click=close_dialog),
                ft.Button("Disconnetti", style=ft.ButtonStyle(bgcolor=T.RED, color=T.TEXT), on_click=do_logout),
            ],
        )
        self._open_dialog(dialog)

    def _build_header(self, width: int) -> ft.Control:
        greeting = "Benvenuto" if self.state.get("just_registered") else "Bentornato"
        return ft.Container(
            content=ft.Row(
                [
                    self._logo(self._scaled(96)),
                    ft.Column(
                        [
                            ft.Text("Kotoba Travel", size=self._scaled(36), weight=ft.FontWeight.W_700, color=T.TEXT, font_family=T.FONT_DISPLAY),
                            ft.Text(f"{greeting}, {self.username}  /  ことば旅", size=self._scaled(14), color=T.TEXT_M, italic=True, font_family=T.FONT_DISPLAY),
                        ],
                        spacing=1,
                    ),
                    ft.Container(expand=True),
                    ft.Text(f"v{APP_VERSION}", size=11, color=T.TEXT_M, font_family=T.FONT_BODY),
                    ft.IconButton(
                        icon=ft.Icons.MILITARY_TECH_ROUNDED,
                        icon_color=T.GOLD,
                        icon_size=24,
                        tooltip="Achievement",
                        on_click=lambda e: self.navigate("achievements"),
                    ),
                    ft.IconButton(
                        icon=ft.Icons.INSIGHTS_ROUNDED,
                        icon_color=T.INDIGO,
                        icon_size=24,
                        tooltip="Statistiche",
                        on_click=lambda e: self.navigate("stats"),
                    ),
                    ft.IconButton(
                        icon=ft.Icons.SETTINGS_ROUNDED,
                        icon_color=T.TEXT_M,
                        icon_size=23,
                        tooltip="Impostazioni",
                        on_click=lambda e: self.navigate("settings"),
                    ),
                    ft.IconButton(
                        icon=ft.Icons.LOGOUT_ROUNDED,
                        icon_color=T.TEXT_M,
                        icon_size=23,
                        tooltip="Disconnetti",
                        on_click=self._confirm_logout,
                    ),
                ],
                spacing=self._scaled(20),
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            width=width,
            padding=ft.padding.only(bottom=self._scaled(18)),
        )

    def _primary_action(self, title: str, jp: str, desc: str, icon, color: str, route: str) -> ft.Control:
        def on_hover(e):
            is_hover = e.data == "true"
            e.control.border = ft.border.all(1.5, color if is_hover else T.BORDER)
            e.control.bgcolor = self._tint(color, 16) if is_hover else T.BG_CARD
            e.control.update()

        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Container(
                                width=self._scaled(50),
                                height=self._scaled(50),
                                alignment=ft.Alignment.CENTER,
                                border=ft.border.all(1.5, color),
                                border_radius=12,
                                bgcolor=self._tint(color, 16),
                                content=ft.Icon(icon, color=color, size=self._scaled(26)),
                            ),
                            ft.Column(
                                [
                                    ft.Text(title, size=self._scaled(26), font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_700, color=T.TEXT),
                                    ft.Text(jp, size=self._scaled(13), font_family=T.FONT_DISPLAY, color=color, italic=True),
                                ],
                                spacing=0,
                                expand=True,
                            ),
                            ft.Icon(ft.Icons.ARROW_FORWARD_IOS_ROUNDED, color=color, size=self._scaled(16)),
                        ],
                        spacing=self._scaled(16),
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Container(height=self._scaled(14)),
                    ft.Text(desc, size=self._scaled(13), font_family=T.FONT_BODY, color=T.TEXT_M, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                ],
                spacing=0,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            bgcolor=T.BG_CARD,
            border_radius=T.RADIUS,
            border=ft.border.all(1, T.BORDER),
            padding=ft.padding.symmetric(horizontal=self._scaled(24), vertical=self._scaled(20)),
            height=self._scaled(144),
            expand=True,
            ink=False,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            animate=ft.Animation(150, ft.AnimationCurve.EASE_OUT),
            on_hover=on_hover,
            on_click=lambda e: self.navigate(route),
        )

    def _travel_link(self, title: str, jp: str, icon, color: str, route: str) -> ft.Control:
        def on_hover(e):
            is_hover = e.data == "true"
            e.control.border = ft.border.all(1.5, color if is_hover else T.BORDER)
            e.control.bgcolor = self._tint(color, 13) if is_hover else T.BG_CARD
            e.control.update()

        return ft.Container(
            content=ft.Row(
                [
                    ft.Container(
                        width=self._scaled(40),
                        height=self._scaled(40),
                        alignment=ft.Alignment.CENTER,
                        border_radius=10,
                        bgcolor=self._tint(color, 16),
                        content=ft.Icon(icon, color=color, size=self._scaled(22)),
                    ),
                    ft.Column(
                        [
                            ft.Text(title, size=self._scaled(16), font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_700, color=T.TEXT),
                            ft.Text(jp, size=self._scaled(11), font_family=T.FONT_DISPLAY, italic=True, color=T.TEXT_M),
                        ],
                        spacing=0,
                        expand=True,
                    ),
                    ft.Icon(ft.Icons.CHEVRON_RIGHT_ROUNDED, color=T.TEXT_M, size=self._scaled(18)),
                ],
                spacing=self._scaled(13),
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=T.BG_CARD,
            border_radius=T.RADIUS,
            border=ft.border.all(1, T.BORDER),
            padding=ft.padding.symmetric(horizontal=self._scaled(18), vertical=self._scaled(12)),
            height=self._scaled(76),
            expand=True,
            ink=False,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            animate=ft.Animation(150, ft.AnimationCurve.EASE_OUT),
            on_hover=on_hover,
            on_click=lambda e: self.navigate(route),
        )

    def build(self) -> ft.Control:
        content_width = self._content_width()
        main_actions = ft.Row(
            [
                self._primary_action(
                    "Accademia",
                    "勉強 - Benkyou",
                    "Sillabari, kanji, vocabolario e grammatica.",
                    ft.Icons.AUTO_STORIES_ROUNDED,
                    T.GOLD,
                    "study",
                ),
                self._primary_action(
                    "Yugi",
                    "遊戯 - Yuugi",
                    "Dojo di allenamento e giochi in arrivo.",
                    ft.Icons.SPORTS_MARTIAL_ARTS_ROUNDED,
                    T.RED,
                    "yugi",
                ),
            ],
            spacing=self._scaled(26),
        )
        main_actions_box = ft.Container(width=content_width, content=main_actions)

        travel_grid = ft.Container(
            width=content_width,
            content=ft.Column(
                [
                    ft.Row(
                        [
                            self._travel_link("Cibo", "和食 - Washoku", ft.Icons.RAMEN_DINING_ROUNDED, T.GOLD, "food"),
                            self._travel_link("Storia", "歴史 - Rekishi", ft.Icons.HISTORY_EDU_ROUNDED, T.INDIGO, "history"),
                        ],
                        spacing=self._scaled(18),
                    ),
                    ft.Row(
                        [
                            self._travel_link("Cultura", "文化 - Bunka", ft.Icons.TEMPLE_BUDDHIST_ROUNDED, T.GREEN, "culture"),
                            self._travel_link("Luoghi", "名所 - Meisho", ft.Icons.MAP_ROUNDED, T.RED, "places"),
                        ],
                        spacing=self._scaled(18),
                    ),
                ],
                spacing=self._scaled(18),
                tight=True,
            ),
        )

        dashboard_stage = ft.Container(
            width=content_width,
            content=ft.Column(
                [
                    main_actions_box,
                    ft.Container(height=self._scaled(34)),
                    travel_grid,
                ],
                spacing=0,
                tight=True,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

        body = ft.Container(
            expand=True,
            alignment=ft.Alignment.CENTER,
            content=dashboard_stage,
        )

        kwargs = dict(bgcolor=T.BG_MAIN, padding=ft.padding.symmetric(horizontal=34, vertical=32), expand=True)
        bg_img = T.bg_image()
        kwargs["image"] = ft.DecorationImage(src=bg_img, fit=ft.BoxFit.COVER, opacity=T.BG_OPACITY) if bg_img else None

        view = ft.Container(
            content=ft.Column(
                [
                    self._build_header(content_width),
                    body,
                ],
                spacing=0,
                expand=True,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            **kwargs,
        )
        self.page.run_task(self._show_onboarding_after_build)
        return view

    async def _show_onboarding_after_build(self):
        import asyncio
        await asyncio.sleep(0.15)
        self._maybe_show_onboarding()
