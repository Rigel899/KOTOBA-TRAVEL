"""
ui/splash_view.py — Splash screen integrata in Flet.

Vantaggi:
  • Una sola finestra → zero problemi di focus / ordinamento Windows
  • ft.Image supporta le GIF animate nativamente (metti asset/image/splash.gif)
  • Funziona nell'exe compilato con flet build
  • Transizione FADE fluida verso il login (AnimatedSwitcher in main.py)

Durata: SPLASH_DURATION secondi, poi naviga automaticamente a "/".
"""
from __future__ import annotations
import asyncio
import os
import flet as ft
from src.core.db_manager import DBManager
from src.core.settings import KotobaTheme as T

SPLASH_DURATION = 2.4          # tempo visibile dopo il primo frame
FIRST_FRAME_DELAY = 0.25       # evita che il timer parta prima del render
GIF_PATH        = "image/splash.gif"   # relativo alla assets_dir
ASSET_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "asset")


class SplashView:
    def __init__(self, page: ft.Page, navigate, state: dict):
        self.page      = page
        self.navigate  = navigate
        self.state     = state
        self._dot_ref  = ft.Ref[ft.Text]()
        self._msg_ref  = ft.Ref[ft.Text]()

    # ── animazione puntini e messaggi (solo se no GIF) ────────────────────────
    async def _animate_text(self):
        msgs = [
            "Carico i dizionari",
            "Preparo il Dojo",
            "Sigillo il passaporto",
            "Prendo posto sul Shinkansen",
            "Apro le porte scorrevoli",
        ]
        dots = ["", ".", "..", "..."]
        t = 0.0
        interval = 0.35
        while t < SPLASH_DURATION - 0.4:
            await asyncio.sleep(interval)
            t += interval
            msg_idx = int(t / (SPLASH_DURATION / len(msgs))) % len(msgs)
            dot_idx = int(t / interval) % len(dots)
            if self._msg_ref.current:
                self._msg_ref.current.value = msgs[msg_idx]
                self._msg_ref.current.update()
            if self._dot_ref.current:
                self._dot_ref.current.value = dots[dot_idx]
                self._dot_ref.current.update()

    # ── task principale: aspetta poi naviga al login ──────────────────────────
    def _preload(self):
        for filename in (
            "sillabari.json",
            "kanji.json",
            "vocabolario.json",
            "grammatica.json",
            "food.json",
            "culture.json",
            "history.json",
            "explore.json",
        ):
            DBManager.load_json(filename)

    async def _run(self):
        await asyncio.sleep(FIRST_FRAME_DELAY)
        await asyncio.gather(
            asyncio.sleep(SPLASH_DURATION),
            asyncio.to_thread(self._preload),
        )
        self.navigate("/")

    # ── build ─────────────────────────────────────────────────────────────────
    def build(self) -> ft.Control:
        self.page.run_task(self._run)

        # logo
        logo_path = os.path.join(ASSET_DIR, "image", "icons", "icona.png")
        if os.path.exists(logo_path):
            logo = ft.Image(
                src=T.asset_path("image/icons/icona.png"),
                width=156, height=156,
                fit=ft.BoxFit.CONTAIN,
            )
        else:
            logo = ft.Container(
                width=156, height=156,
                alignment=ft.Alignment.CENTER,
                border=ft.border.all(2, T.GOLD),
                border_radius=32,
                content=ft.Text("旅", size=55,
                                font_family=T.FONT_JP,
                                color=T.GOLD,
                                weight=ft.FontWeight.W_700),
            )

        # GIF se disponibile, altrimenti testo animato
        gif_abs = os.path.join(ASSET_DIR, *GIF_PATH.split("/"))
        if os.path.exists(gif_abs):
            animation_widget = ft.Image(
                src=T.asset_path(GIF_PATH),
                width=440, height=160,
                fit=ft.BoxFit.CONTAIN,
            )
            status_row = ft.Container()          # nessun testo aggiuntivo
        else:
            # avvia animazione testo
            self.page.run_task(self._animate_text)
            animation_widget = ft.Container()    # nessuna immagine
            status_row = ft.Row([
                ft.Text("", ref=self._msg_ref,
                        size=T.FS_SMALL, color=T.TEXT_M,
                        font_family=T.FONT_BODY, italic=True),
                ft.Text("", ref=self._dot_ref,
                        size=T.FS_SMALL, color=T.GOLD,
                        font_family=T.FONT_BODY, weight=ft.FontWeight.W_700),
            ], spacing=0, alignment=ft.MainAxisAlignment.CENTER)

        content = ft.Column(
            [
                logo,
                ft.Container(height=14),
                ft.Text("Kotoba Travel",
                        size=38, font_family=T.FONT_DISPLAY,
                        weight=ft.FontWeight.W_700, color=T.TEXT,
                        text_align=ft.TextAlign.CENTER),
                ft.Text("ことば旅",
                        size=18, font_family=T.FONT_JP,
                        color=T.GOLD, italic=True,
                        text_align=ft.TextAlign.CENTER),
                ft.Text("Il tuo viaggio in Giappone",
                        size=T.FS_SMALL, font_family=T.FONT_DISPLAY,
                        color=T.TEXT_M, italic=True,
                        text_align=ft.TextAlign.CENTER),
                ft.Container(height=28),
                animation_widget,
                ft.Container(height=16),
                status_row,
            ],
            spacing=0,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
        )

        bg_path = T.bg_image()
        kwargs: dict = dict(bgcolor=T.BG_MAIN, expand=True)
        if bg_path:
            kwargs["image_src"]     = bg_path
            kwargs["image_fit"]     = ft.BoxFit.COVER
            kwargs["image_opacity"] = T.BG_OPACITY

        return ft.Container(
            content=ft.Column(
                [ft.Container(expand=True),
                 content,
                 ft.Container(expand=True)],
                expand=True,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            **kwargs,
        )
