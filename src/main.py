# main.py
import src.core.compat  # Shim obbligatorio per ripristinare le vecchie API rimosse in Flet 0.80+
import importlib
import logging
import os
import flet as ft
from src.core.settings import KotobaTheme as T

APP_W = 1200
APP_H = 760
MIN_W = 1120
MIN_H = 680
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "asset")


def _apply_app_theme(page: ft.Page) -> None:
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = T.BG_MAIN
    page.padding = 0
    page.theme = ft.Theme(
        scrollbar_theme=ft.ScrollbarTheme(
            thumb_visibility=False,
            track_visibility=False,
            thickness={
                ft.ControlState.DEFAULT: 4,
                ft.ControlState.HOVERED: 7,
                ft.ControlState.DRAGGED: 7,
            },
            radius=8,
            thumb_color={
                ft.ControlState.DEFAULT: "#55D4AF5C",
                ft.ControlState.HOVERED: "#AAD4AF5C",
                ft.ControlState.DRAGGED: "#D4D4AF5C",
            },
            track_color="#001C1815",
            track_border_color="#001C1815",
            cross_axis_margin=2,
            main_axis_margin=8,
            min_thumb_length=48,
            interactive=True,
        )
    )


def _screen_size() -> tuple[int | None, int | None]:
    try:
        import ctypes
        user32 = ctypes.windll.user32
        return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
    except Exception:
        return None, None


def _primary_work_area() -> tuple[int, int, int, int] | None:
    """Return the primary monitor work area.

    Using the foreground window is fragile on multi-monitor setups: the
    foreground window can be the terminal/editor, which may place this app
    half off-screen on a secondary display.
    """
    try:
        import ctypes
        from ctypes import wintypes

        rect = wintypes.RECT()
        SPI_GETWORKAREA = 0x0030
        if ctypes.windll.user32.SystemParametersInfoW(SPI_GETWORKAREA, 0, ctypes.byref(rect), 0):
            return rect.left, rect.top, rect.right, rect.bottom
    except Exception:
        pass
    return None


def _current_monitor_work_area() -> tuple[int, int, int, int] | None:
    try:
        import ctypes
        from ctypes import wintypes

        class RECT(ctypes.Structure):
            _fields_ = [
                ("left", wintypes.LONG),
                ("top", wintypes.LONG),
                ("right", wintypes.LONG),
                ("bottom", wintypes.LONG),
            ]

        class MONITORINFO(ctypes.Structure):
            _fields_ = [
                ("cbSize", wintypes.DWORD),
                ("rcMonitor", RECT),
                ("rcWork", RECT),
                ("dwFlags", wintypes.DWORD),
            ]

        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        monitor = user32.MonitorFromWindow(hwnd, 2)  # MONITOR_DEFAULTTONEAREST
        info = MONITORINFO()
        info.cbSize = ctypes.sizeof(MONITORINFO)
        if user32.GetMonitorInfoW(monitor, ctypes.byref(info)):
            rect = info.rcWork
            return rect.left, rect.top, rect.right, rect.bottom
    except Exception:
        pass
    return None


def _fit_to_screen(w: int, h: int, area: tuple[int, int, int, int] | None = None) -> tuple[int, int]:
    if area:
        _, _, right, bottom = area
        left, top, _, _ = area
        sw, sh = right - left, bottom - top
    else:
        sw, sh = _screen_size()
    if not sw or not sh:
        return w, h
    max_w = sw - 80 if sw > MIN_W + 80 else sw - 24
    max_h = sh - 80 if sh > MIN_H + 80 else sh - 24
    return min(w, max(420, max_w)), min(h, max(520, max_h))


def _center_window_on_current_monitor(page: ft.Page, w: int, h: int, area: tuple[int, int, int, int] | None) -> None:
    if area:
        left, top, right, bottom = area
        page.window.left = left + max(0, (right - left - w) // 2)
        page.window.top = top + max(0, (bottom - top - h) // 2)
        return
    sw, sh = _screen_size()
    if sw and sh:
        page.window.left = max(0, (sw - w) // 2)
        page.window.top = max(0, (sh - h) // 2)


def _set_window(page: ft.Page, w: int, h: int, min_w: int, min_h: int, resizable: bool) -> None:
    monitor_area = _primary_work_area()
    fitted_w, fitted_h = _fit_to_screen(w, h, monitor_area)
    try:
        page.window.resizable = True
        page.window.maximized = False
        page.window.full_screen = False
    except Exception:
        pass
    page.window.max_width = None
    page.window.max_height = None
    page.window.maximizable = resizable
    page.window.min_width = min(min_w, fitted_w)
    page.window.min_height = min(min_h, fitted_h)
    page.window.width = fitted_w
    page.window.height = fitted_h
    page.window.focused = True
    page.window.resizable = resizable
    _center_window_on_current_monitor(page, fitted_w, fitted_h, monitor_area)


def _instant_splash() -> ft.Control:
    """Prima schermata leggerissima: deve renderizzare prima di font, cache e route."""
    bg_path = T.bg_image()
    kwargs: dict = dict(
        bgcolor=T.BG_MAIN,
        expand=True,
        alignment=ft.Alignment.CENTER,
    )
    if bg_path:
        kwargs["image_src"] = bg_path
        kwargs["image_fit"] = ft.BoxFit.COVER
        kwargs["image_opacity"] = T.BG_OPACITY

    return ft.Container(
        **kwargs,
        content=ft.Column(
            [
                ft.Image(
                    src=T.asset_path("image/icons/icona.png"),
                    width=156,
                    height=156,
                    fit=ft.BoxFit.CONTAIN,
                ),
                ft.Container(height=16),
                ft.Text(
                    "Kotoba Travel",
                    size=38,
                    color=T.TEXT,
                    weight=ft.FontWeight.W_700,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    "ことば旅",
                    size=18,
                    color=T.GOLD,
                    italic=True,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    "Il tuo viaggio in Giappone",
                    size=T.FS_SMALL,
                    color=T.TEXT_M,
                    italic=True,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(height=10),
                ft.ProgressRing(width=24, height=24, stroke_width=2, color=T.GOLD),
            ],
            spacing=0,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
    )


def main(page: ft.Page):
    page.title = "Kotoba Travel"
    _set_window(page, APP_W, APP_H, MIN_W, MIN_H, True)
    _apply_app_theme(page)

    app_state = {}
    root = ft.AnimatedSwitcher(
        content=_instant_splash(),
        duration=260,
        reverse_duration=160,
        transition=ft.AnimatedSwitcherTransition.FADE,
        switch_in_curve=ft.AnimationCurve.EASE_OUT,
        switch_out_curve=ft.AnimationCurve.EASE_IN,
        expand=True,
    )
    page.add(root)
    page.update()

    fonts_dir = os.path.join(ASSETS_DIR, "fonts")
    candidates = {
        "Shippori Mincho": "ShipporiMincho-Regular.ttf",
        "Inter": "Inter-VariableFont_opsz,wght.ttf",
        "Inter Italic": "Inter-Italic-VariableFont_opsz,wght.ttf",
        "Noto Sans JP": "NotoSansJP-VariableFont_wght.ttf",
    }
    available = {
        name: f"fonts/{file}"
        for name, file in candidates.items()
        if os.path.exists(os.path.join(fonts_dir, file))
    }
    if available:
        page.fonts = available

    from src.core.db_manager import DBManager

    DBManager.data_dir()
    try:
        log_path = os.path.join(DBManager.user_data_dir(), "kotoba.log")
        logging.basicConfig(
            filename=log_path,
            level=logging.WARNING,
            format="%(asctime)s %(name)s %(levelname)s %(message)s",
            encoding="utf-8",
        )
    except Exception:
        pass  # log setup failure must never crash the app

    routes = {
        "splash": ("src.ui.splash_view", "SplashView"),
        "dashboard": ("src.ui.dashboard_view", "DashboardView"),
        "study": ("src.ui.study.study_hub", "StudyHub"),
        "yugi": ("src.ui.yugi.yugi_hub", "YugiHub"),
        "dojo_hub": ("src.ui.yugi.dojo_hub", "DojoHub"),
        "dojo_kana": ("src.ui.yugi.dojo_kana", "DojoKana"),
        "dojo_kanji": ("src.ui.yugi.dojo_kanji", "DojoKanji"),
        "dojo_vocab": ("src.ui.yugi.dojo_vocab", "DojoVocab"),
        "dojo_grammar": ("src.ui.yugi.dojo_grammar", "DojoGrammar"),
        "dojo_exam": ("src.ui.yugi.dojo_exam", "DojoExam"),
        "achievements": ("src.ui.achievements_view", "AchievementsView"),
        "stats": ("src.ui.stats_view", "StatsView"),
        "settings": ("src.ui.settings_view", "SettingsView"),
        "food": ("src.ui.food_view", "FoodView"),
        "culture": ("src.ui.culture_view", "CultureView"),
        "history": ("src.ui.history_view", "HistoryView"),
        "places": ("src.ui.places_view", "PlacesView"),
    }

    def _error_view(route_name: str, exc: Exception) -> ft.Control:
        message = f"{route_name}: {type(exc).__name__}: {exc}"
        target_route = "/" if DBManager.current_username == "Viandante" else "dashboard"
        target_label = "Torna al login" if target_route == "/" else "Torna alla dashboard"
        return ft.Container(
            expand=True,
            bgcolor=T.BG_MAIN,
            alignment=ft.Alignment.CENTER,
            padding=ft.padding.all(32),
            content=ft.Column(
                [
                    ft.Container(
                        width=72,
                        height=72,
                        alignment=ft.Alignment.CENTER,
                        border=ft.border.all(2, T.ERR),
                        border_radius=12,
                        content=ft.Text("!", size=40, color=T.ERR, weight=ft.FontWeight.W_900),
                    ),
                    ft.Text("Errore caricamento vista", size=22, color=T.TEXT, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_700),
                    ft.Container(
                        width=620,
                        content=ft.Text(message, size=12, color=T.TEXT_M, selectable=True, text_align=ft.TextAlign.CENTER),
                    ),
                    ft.ElevatedButton(
                        target_label,
                        style=ft.ButtonStyle(bgcolor=T.RED, color=T.TEXT),
                        on_click=lambda e: navigate(target_route),
                    ),
                ],
                spacing=14,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
        )

    def build_view(route_name: str, module_path: str, class_name: str) -> ft.Control:
        try:
            module = importlib.import_module(module_path)
            view_cls = getattr(module, class_name)
            return view_cls(page, navigate, app_state).build()
        except Exception as exc:
            return _error_view(route_name, exc)

    def navigate(route, **kwargs):
        app_state.update(kwargs)
        route = "/" if route in ("", "/") else route

        if route == "/":
            DBManager.current_username = "Viandante"
            app_state.clear()
            app_state["_route"] = "/"
            app_state["_app_window_ready"] = False
            from src.ui.login_view import LoginView
            view = LoginView(page, navigate, app_state)
            root.content = view.build()
            page.update()
            return

        app_state["_route"] = route

        route_config = routes.get(route)
        if route_config:
            root.content = build_view(route, *route_config)
        else:
            root.content = build_view("dashboard", *routes["dashboard"])

        page.update()

    navigate("splash")

def before_main(page: ft.Page):
    page.title = "Kotoba Travel"
    _apply_app_theme(page)
    _set_window(page, APP_W, APP_H, MIN_W, MIN_H, True)


if __name__ == "__main__":
    ft.run(main, before_main=before_main, assets_dir=ASSETS_DIR)
