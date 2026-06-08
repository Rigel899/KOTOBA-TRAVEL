"""
ui/splash_view.py — Splash screen integrata in Flet.

Il treno avanza ad ogni file JSON caricato: quando raggiunge la stazione
finale l'app è pronta e la navigazione avviene automaticamente.
"""
from __future__ import annotations
import asyncio
import os
import time
import flet as ft
from src.core.db_manager import DBManager
from src.core.settings import KotobaTheme as T
from src.ui.components.loader import TrainProgress

ASSET_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "asset")

# Ogni coppia: (file da caricare, messaggio mostrato durante il caricamento)
FILES_TO_PRELOAD: list[tuple[str, str]] = [
    ("sillabari.json",   "Imparo i kana"),
    ("kanji.json",       "Studio i kanji"),
    ("vocabolario.json", "Costruisco il vocabolario"),
    ("grammatica.json",  "Analizzo la grammatica"),
    ("food.json",        "Preparo le ricette"),
    ("culture.json",     "Esploro la cultura"),
    ("history.json",     "Sfoglio i secoli"),
    ("explore.json",     "Preparo i luoghi"),
]

STEP_DELAY  = 0.55  # durata minima per ogni passo (8 passi × 0.55 ≈ 4.4s animazione)
MIN_VISIBLE = 5.0   # durata minima totale dello splash


class SplashView:
    def __init__(self, page: ft.Page, navigate, state: dict):
        self.page     = page
        self.navigate = navigate
        self.state    = state
        self._msg_ref = ft.Ref[ft.Text]()
        self._train = TrainProgress(
            page,
            total_steps=len(FILES_TO_PRELOAD),
            track_width=460,
            stations=["東京", "品川", "名古屋", "京都", "大阪", "広島", "小倉", "博多"],
            header="🗾  Tokaido · Sanyo",
        )

    async def _run(self):
        start = time.monotonic()
        await asyncio.sleep(0.1)  # attende il primo frame renderizzato

        for filename, msg in FILES_TO_PRELOAD:
            step_start = time.monotonic()
            if self._msg_ref.current:
                self._msg_ref.current.value = msg + "..."
                self._msg_ref.current.update()
            await asyncio.to_thread(DBManager.load_json, filename)
            self._train.advance()
            # Ogni passo dura almeno STEP_DELAY così l'animazione è visibile
            step_gap = STEP_DELAY - (time.monotonic() - step_start)
            if step_gap > 0:
                await asyncio.sleep(step_gap)

        if self._msg_ref.current:
            self._msg_ref.current.value = "Tutto pronto — buon viaggio! 🗾"
            self._msg_ref.current.update()

        # Garantisce MIN_VISIBLE secondi totali di splash
        elapsed = time.monotonic() - start
        remaining = MIN_VISIBLE - elapsed
        if remaining > 0:
            await asyncio.sleep(remaining)

        self.navigate("/")

    def build(self) -> ft.Control:
        self.page.run_task(self._run)

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
                ft.Container(height=32),
                ft.Text("", ref=self._msg_ref,
                        size=T.FS_SMALL, color=T.TEXT_M,
                        font_family=T.FONT_BODY, italic=True,
                        text_align=ft.TextAlign.CENTER,
                        height=18),
                ft.Container(height=10),
                self._train.build(),
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
