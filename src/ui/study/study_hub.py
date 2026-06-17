"""
StudyHub – Hub di studio.
(Caricamento dinamico da JSON + Design System Sumi-e + Vocabolario a Griglia Verticale Impilata)
"""
from __future__ import annotations
import asyncio
import logging
import flet as ft
from src.core.app_state import get_current_user
from src.core.settings import KotobaTheme as T
from src.core.db_manager import DBManager
from src.core.progress_service import STUDY_REQUIRED_SECTIONS, STUDY_SECTION_STAT
from src.ui.components.loader import show_achievements
from src.ui.components.masthead import build_masthead
from src.ui.components.stage import centered_stage
from src.core.compat import open_dialog, close_dialog, icon_btn

_log = logging.getLogger("kotoba.ui.study")

class StudyHub:
    def __init__(self, page: ft.Page, navigate, state: dict):
        self.page = page
        self.navigate = navigate
        self.state = state
        self.username = get_current_user(state)
        
        # Caricamento dinamico dei dati (i 4 JSON)
        self.sillabari_data = DBManager.load_json("sillabari.json") or []
        self.vocabolario_data = DBManager.load_json("vocabolario.json") or []
        self.kanji_data = DBManager.load_json("kanji.json") or []
        self.grammar_data = DBManager.load_json("grammatica.json") or []
        
        self.active_tab = "hiragana"
        self.search_text = ""
        self.vocab_page = 0
        self.vocab_page_size = 40
        self.kanji_page = 0
        self.kanji_page_size = 40
        self._search_task: asyncio.Future | None = None

        self.tab_row = ft.Row(spacing=8, scroll=ft.ScrollMode.AUTO)
        self.content_area = ft.Container(expand=True)
        self.search_field = self._tf_search()

    def _track_study_section(self, key: str) -> None:
        if key not in STUDY_REQUIRED_SECTIONS:
            return
        try:
            unlocked = DBManager.increment_stat(
                self.username,
                STUDY_SECTION_STAT,
                unique_id=key,
            )
        except Exception:
            _log.exception("study section tracking failed for %s", key)
            return

        try:
            show_achievements(self.page, unlocked)
        except Exception:
            _log.exception("study achievement notification failed for %s", key)

    def _tf_search(self) -> ft.TextField:
        return ft.TextField(
            hint_text="Cerca parole, letture, significati o regole...",
            prefix_icon=ft.Icons.SEARCH_ROUNDED,
            bgcolor=T.BG_SURF,
            border_color=T.BORDER,
            focused_border_color=T.GOLD,
            color=T.TEXT,
            cursor_color=T.GOLD,
            height=42,
            text_size=13,
            border_radius=T.RADIUS_S,
            content_padding=ft.padding.only(left=12, right=12, top=0, bottom=0),
            hint_style=ft.TextStyle(color=T.TEXT_M, font_family=T.FONT_BODY),
            text_style=ft.TextStyle(font_family=T.FONT_BODY, size=T.FS_BODY),
            on_change=lambda e: self._on_search(e.control.value),
        )

    def _on_search(self, value: str):
        if self._search_task:
            self._search_task.cancel()
        self._search_task = self.page.run_task(self._debounced_search, value)

    async def _debounced_search(self, value: str):
        try:
            await asyncio.sleep(0.2)
        except asyncio.CancelledError:
            return
        self.search_text = value or ""
        self.vocab_page = 0
        self.kanji_page = 0
        self._update_ui(is_build_phase=False)

    def _matches_search(self, item: dict, keys: tuple[str, ...]) -> bool:
        q = self.search_text.lower().strip()
        if not q:
            return True
        text = " ".join(str(item.get(key, "")) for key in keys).lower()
        return all(part in text for part in q.split())

    def _tab_accent(self, key: str) -> str:
        if key in ("hiragana", "katakana"):
            return T.BELT_KANA
        if key == "kanji":
            return T.BELT_KANJI
        if key == "vocab":
            return T.BELT_VOCAB
        if key == "grammar":
            return T.BELT_GRAMMAR
        return T.GOLD

    def _make_tab_button(self, label: str, key: str) -> ft.Control:
        is_active = (self.active_tab == key)
        accent = self._tab_accent(key)
        
        bg_color = T.BG_SURF if is_active else "transparent"
        border_color = accent if is_active else T.BORDER
        text_color = accent if is_active else T.TEXT_M

        def on_click(e):
            self.active_tab = key
            self._update_ui(is_build_phase=False)
            self._track_study_section(key)

        def on_hover(e):
            if is_active: return
            is_hover = e.data == "true"
            e.control.border = ft.border.all(1, accent if is_hover else T.BORDER)
            e.control.bgcolor = T.BG_HOVER if is_hover else "transparent"
            e.control.update()

        return ft.Container(
            content=ft.Text(label, size=13, color=text_color, font_family=T.FONT_BODY,
                            weight=ft.FontWeight.W_600 if is_active else ft.FontWeight.NORMAL),
            bgcolor=bg_color,
            padding=ft.padding.only(left=14, right=14, top=6, bottom=6),
            border_radius=16,
            border=ft.border.all(1, border_color),
            on_click=on_click,
            on_hover=on_hover,
            ink=False,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            animate=ft.Animation(150, ft.AnimationCurve.EASE_OUT)
        )

    def _open_dialog(self, dialog: ft.AlertDialog) -> None:
        open_dialog(self.page, dialog)

    def _close_dialog(self, dialog: ft.AlertDialog) -> None:
        close_dialog(self.page, dialog)

    def _kana_cell(self, item: dict | None, accent: str, *, expand: bool = True) -> ft.Container:
        if not item:
            return ft.Container(
                expand=expand,
                height=60,
                bgcolor=T.BG_MAIN,
                border_radius=10,
                border=ft.border.all(1, T.BORDER),
                opacity=0.26,
                alignment=ft.Alignment.CENTER,
                content=ft.Text("—", size=14, color=T.TEXT_M, font_family=T.FONT_BODY),
            )

        return ft.Container(
            expand=expand,
            height=60,
            bgcolor=T.BG_CARD,
            border_radius=10,
            border=ft.border.all(1, accent),
            padding=ft.padding.symmetric(horizontal=8, vertical=7),
            alignment=ft.Alignment.CENTER,
            content=ft.Column(
                [
                    ft.Text(
                        item.get("word", ""),
                        size=23,
                        font_family=T.FONT_JP,
                        weight=ft.FontWeight.W_700,
                        color=accent,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        item.get("pronunciation", ""),
                        size=10,
                        font_family=T.FONT_BODY,
                        color=T.TEXT_M,
                        italic=True,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                spacing=2,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
        )

    def _kana_table_row(self, label: str, row_items: list[dict | None], accent: str) -> ft.Control:
        return ft.Row(
            [
                ft.Container(
                    width=58,
                    height=60,
                    alignment=ft.Alignment.CENTER_RIGHT,
                    content=ft.Text(label, size=11, color=T.TEXT_M, font_family=T.FONT_BODY, weight=ft.FontWeight.W_700),
                ),
                *[self._kana_cell(item, accent) for item in row_items],
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _kana_table(self, title: str, rows: list[tuple[str, str, list[str | None]]], lookup: dict[tuple[str, str], dict], accent: str) -> ft.Control:
        table_rows = [
            self._kana_table_row(
                row_label,
                [lookup.get((group_key, sound)) if sound else None for sound in sounds],
                accent,
            )
            for group_key, row_label, sounds in rows
        ]

        return ft.Container(
            bgcolor=T.BG_MAIN,
            border=ft.border.all(1, T.BORDER),
            border_radius=T.RADIUS,
            padding=ft.padding.all(14),
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Container(width=4, height=18, bgcolor=accent, border_radius=3),
                            ft.Text(title, size=14, color=T.TEXT, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_700),
                        ],
                        spacing=9,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    *table_rows,
                ],
                spacing=12,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            ),
        )

    def _kana_search_grid(self, items: list[dict], accent: str) -> ft.Control:
        return ft.GridView(
            controls=[self._kana_cell(item, accent, expand=False) for item in items],
            expand=True,
            max_extent=86,
            child_aspect_ratio=1.05,
            spacing=10,
            run_spacing=10,
            padding=ft.padding.only(top=2, bottom=16),
        )

    def _kana_tab(self, category: str) -> ft.Control:
        accent = T.BELT_KANA
        title_jp = "ひらがな" if category == "Hiragana" else "カタカナ"
        raw_items = [x for x in self.sillabari_data if x.get("category") == category]
        items = [
            x for x in raw_items
            if self._matches_search(x, ("word", "pronunciation", "group"))
        ]

        header = ft.Row(
            [
                ft.Container(width=5, height=24, bgcolor=accent, border_radius=3),
                ft.Text(category, size=20, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_700, color=T.TEXT),
                ft.Text(title_jp, size=15, font_family=T.FONT_JP, color=accent, italic=True),
                ft.Container(expand=True),
                ft.Text(f"{len(items)} segni", size=12, font_family=T.FONT_BODY, color=accent),
            ],
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        if not items:
            return ft.Container(content=ft.Text(f"Nessun dato trovato per {category} nel json.", color=T.TEXT_M), padding=16)

        if self.search_text.strip():
            body = self._kana_search_grid(items, accent)
        else:
            lookup = {(item.get("group", ""), item.get("pronunciation", "")): item for item in raw_items}
            base_rows = [
                ("vocali", "Vocali", ["a", "i", "u", "e", "o"]),
                ("k", "K", ["ka", "ki", "ku", "ke", "ko"]),
                ("s", "S", ["sa", "shi", "su", "se", "so"]),
                ("t", "T", ["ta", "chi", "tsu", "te", "to"]),
                ("n", "N", ["na", "ni", "nu", "ne", "no"]),
                ("h", "H", ["ha", "hi", "fu", "he", "ho"]),
                ("m", "M", ["ma", "mi", "mu", "me", "mo"]),
                ("y", "Y", ["ya", None, "yu", None, "yo"]),
                ("r", "R", ["ra", "ri", "ru", "re", "ro"]),
                ("w", "W", ["wa", None, None, None, "wo"]),
                ("n_singola", "N", ["n", None, None, None, None]),
            ]
            voiced_rows = [
                ("g", "G", ["ga", "gi", "gu", "ge", "go"]),
                ("z", "Z", ["za", "ji", "zu", "ze", "zo"]),
                ("d", "D", ["da", "ji", "zu", "de", "do"]),
                ("b", "B", ["ba", "bi", "bu", "be", "bo"]),
                ("p", "P", ["pa", "pi", "pu", "pe", "po"]),
            ]
            body = ft.ListView(
                [
                    self._kana_table("Base", base_rows, lookup, accent),
                    self._kana_table("Dakuten / Handakuten", voiced_rows, lookup, accent),
                ],
                expand=True,
                spacing=14,
                padding=ft.padding.only(top=2, bottom=16),
            )

        return ft.Column(
            [
                header,
                ft.Divider(color=T.BORDER, height=14),
                body,
            ],
            spacing=0,
            expand=True,
        )

    def _vocab_word_size(self, word: str) -> int:
        length = len((word or "").strip())
        if length <= 4:
            return 26
        if length <= 7:
            return 22
        if length <= 10:
            return 18
        return 16

    def _meta_chip(self, label: str, color: str = T.TEXT_M) -> ft.Control:
        return ft.Container(
            content=ft.Text(label, size=10, color=color, font_family=T.FONT_BODY, weight=ft.FontWeight.W_600),
            border=ft.border.all(1, T.BORDER),
            border_radius=12,
            padding=ft.padding.symmetric(horizontal=9, vertical=3),
        )

    def _split_example(self, example: str) -> tuple[str, str, str]:
        lines = [line.strip() for line in (example or "").splitlines() if line.strip()]
        jp = lines[0] if lines else ""
        romaji = lines[1] if len(lines) > 1 else ""
        translation = lines[2] if len(lines) > 2 else ""
        if translation.startswith("="):
            translation = translation[1:].strip()
        return jp, romaji, translation

    def _example_panel(self, example: str, *, compact: bool = False, accent: str = T.GOLD) -> ft.Control:
        jp, romaji, translation = self._split_example(example)
        jp_size = 17 if compact else 20
        romaji_size = 12 if compact else 13
        translation_size = 13 if compact else 15
        padding = ft.padding.all(12 if compact else 16)

        return ft.Container(
            bgcolor=T.BG_MAIN,
            border=ft.border.all(1, T.BORDER),
            border_radius=T.RADIUS,
            padding=padding,
            content=ft.Column(
                [
                    ft.Text(
                        jp,
                        size=jp_size,
                        color=accent,
                        font_family=T.FONT_JP,
                        weight=ft.FontWeight.W_700,
                        selectable=True,
                        style=ft.TextStyle(height=1.35),
                    ),
                    ft.Text(
                        romaji,
                        size=romaji_size,
                        color=T.TEXT_M,
                        font_family=T.FONT_BODY,
                        italic=True,
                        selectable=True,
                    ),
                    ft.Text(
                        translation,
                        size=translation_size,
                        color=T.TEXT,
                        font_family=T.FONT_BODY,
                        selectable=True,
                        style=ft.TextStyle(height=1.3),
                    ),
                ],
                spacing=8 if compact else 10,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            ),
        )

    def _study_entry_card(
        self,
        item: dict,
        *,
        accent: str = T.GOLD,
        on_click=None,
        show_chevron: bool = False,
    ) -> ft.Container:
        word = item.get("word", "")
        reading = item.get("reading", "")
        meaning = item.get("meaning", "").capitalize()
        group = item.get("group", "")
        category = item.get("category", "")
        meta = group or category

        def on_hover(e):
            if not on_click:
                return
            is_hover = e.data == "true"
            e.control.border = ft.border.all(1.5 if is_hover else 1, accent)
            e.control.bgcolor = T.BG_HOVER if is_hover else T.BG_CARD
            e.control.update()

        return ft.Container(
            content=ft.Row(
                [
                    ft.Container(
                        width=4,
                        height=68,
                        bgcolor=accent,
                        border_radius=3,
                        opacity=0.82,
                    ),
                    ft.Container(
                        width=190,
                        content=ft.Column(
                            [
                                ft.Text(
                                    word,
                                    size=self._vocab_word_size(word) + 6,
                                    font_family=T.FONT_JP,
                                    color=accent,
                                    weight=ft.FontWeight.W_700,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                    max_lines=1,
                                ),
                                ft.Text(
                                    reading,
                                    size=12,
                                    font_family=T.FONT_BODY,
                                    color=T.TEXT_M,
                                    italic=True,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                    max_lines=1,
                                ),
                            ],
                            spacing=3,
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                    ),
                    ft.Column(
                        [
                            ft.Text(
                                meaning,
                                size=20,
                                font_family=T.FONT_DISPLAY,
                                weight=ft.FontWeight.W_700,
                                color=T.TEXT,
                                overflow=ft.TextOverflow.ELLIPSIS,
                                max_lines=1,
                            ),
                            ft.Text(
                                meta,
                                size=11,
                                font_family=T.FONT_BODY,
                                color=T.TEXT_M,
                                overflow=ft.TextOverflow.ELLIPSIS,
                                max_lines=1,
                            ),
                        ],
                        spacing=3,
                        expand=True,
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    ft.Icon(ft.Icons.CHEVRON_RIGHT_ROUNDED, color=T.TEXT_M, size=18, visible=show_chevron),
                ],
                spacing=15,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=T.BG_CARD,
            border_radius=T.RADIUS,
            border=ft.border.all(1, accent),
            padding=ft.padding.symmetric(vertical=14, horizontal=16),
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            on_click=on_click,
            on_hover=on_hover if on_click else None,
            ink=False,
        )

    def _kanji_tab(self) -> ft.Control:
        filtered_data = [
            item for item in self.kanji_data
            if self._matches_search(item, ("word", "reading", "meaning", "group"))
        ]
        if not filtered_data:
            return ft.Container(content=ft.Text("Nessun Kanji trovato nel json.", color=T.TEXT_M), padding=16)

        total_items = len(filtered_data)
        max_page = max(0, (total_items - 1) // self.kanji_page_size)
        self.kanji_page = max(0, min(self.kanji_page, max_page))
        start = self.kanji_page * self.kanji_page_size
        end = min(start + self.kanji_page_size, total_items)
        page_items = filtered_data[start:end]

        def go_page(delta: int):
            self.kanji_page = max(0, min(self.kanji_page + delta, max_page))
            self.content_area.content = centered_stage(self.page, self._kanji_tab(), max_width=1040)
            try:
                self.content_area.update()
            except RuntimeError:
                pass

        return ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("Kanji base", size=18, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_700, color=T.TEXT),
                        ft.Container(expand=True),
                        ft.Text(f"{start + 1}-{end} di {total_items}", size=12, font_family=T.FONT_BODY, color=T.BELT_KANJI),
                        icon_btn(ft.Icons.CHEVRON_LEFT_ROUNDED, icon_color=T.TEXT_M, icon_size=18, tooltip="Pagina precedente", disabled=self.kanji_page <= 0, on_click=lambda e: go_page(-1)),
                        icon_btn(ft.Icons.CHEVRON_RIGHT_ROUNDED, icon_color=T.TEXT_M, icon_size=18, tooltip="Pagina successiva", disabled=self.kanji_page >= max_page, on_click=lambda e: go_page(1)),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Divider(color=T.BORDER, height=14),
                ft.GridView(
                    controls=[self._study_entry_card(item, accent=T.BELT_KANJI) for item in page_items],
                    expand=True,
                    max_extent=520,
                    child_aspect_ratio=4.45,
                    spacing=12,
                    run_spacing=12,
                    padding=ft.padding.only(top=2, bottom=16),
                ),
            ],
            spacing=0,
            expand=True,
        )

    def _show_vocab_detail(self, item: dict) -> None:
        accent = T.BELT_VOCAB
        word = item.get("word", "")
        reading = item.get("reading", "")
        meaning = item.get("meaning", "").capitalize()
        group = item.get("group", "")
        category = item.get("category", "")
        meta = [x for x in (group, category) if x]
        if len(meta) == 2 and meta[0].lower() == meta[1].lower():
            meta = meta[:1]

        example = item.get("example", "").strip()
        example_block = []
        if example:
            example_block = [
                ft.Container(height=14),
                self._example_panel(example, accent=accent),
            ]

        content = ft.Column(
            [
                ft.Container(
                    bgcolor=T.BG_MAIN,
                    border=ft.border.all(1, T.BORDER),
                    border_radius=T.RADIUS,
                    padding=ft.padding.all(18),
                    content=ft.Column(
                        [
                            ft.Text(
                                word,
                                size=max(34, self._vocab_word_size(word) + 10),
                                color=accent,
                                font_family=T.FONT_JP,
                                weight=ft.FontWeight.W_700,
                                max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                            ft.Text(reading, size=14, color=T.TEXT_M, font_family=T.FONT_BODY, italic=True),
                            ft.Divider(color=T.BORDER, height=18),
                            ft.Text(meaning, size=28, color=T.TEXT, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_700),
                            ft.Row(
                                [self._meta_chip(label, accent if idx == 0 else T.TEXT_M) for idx, label in enumerate(meta)],
                                spacing=8,
                                wrap=True,
                            ),
                        ],
                        spacing=8,
                    ),
                ),
                *example_block,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            spacing=0,
            tight=True,
        )

        dialog = ft.AlertDialog(
            modal=True,
            bgcolor=T.BG_CARD,
            title=ft.Text("Vocabolario", color=T.TEXT, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_700),
            content=ft.Container(content=content, width=500),
            actions=[
                ft.TextButton("Chiudi", style=ft.ButtonStyle(color=accent, mouse_cursor=ft.MouseCursor.CLICK), on_click=lambda e: self._close_dialog(dialog)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self._open_dialog(dialog)

    def _vocab_tab(self) -> ft.Control:
        filtered_data = [
            item for item in self.vocabolario_data
            if self._matches_search(item, ("word", "reading", "meaning", "group", "category", "example"))
        ]

        if not filtered_data:
            return ft.Container(content=ft.Text("Nessun vocabolo trovato nel json.", color=T.TEXT_M), padding=16)

        total_items = len(filtered_data)
        max_page = max(0, (total_items - 1) // self.vocab_page_size)
        self.vocab_page = max(0, min(self.vocab_page, max_page))
        start = self.vocab_page * self.vocab_page_size
        end = min(start + self.vocab_page_size, total_items)
        page_items = filtered_data[start:end]

        def go_page(delta: int):
            self.vocab_page = max(0, min(self.vocab_page + delta, max_page))
            self.content_area.content = centered_stage(self.page, self._vocab_tab(), max_width=980)
            try:
                self.content_area.update()
            except RuntimeError:
                pass

        return ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("Vocabolario", size=18, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_700, color=T.TEXT),
                        ft.Container(expand=True),
                        ft.Text(f"{start + 1}-{end} di {total_items}", size=12, font_family=T.FONT_BODY, color=T.BELT_VOCAB),
                        icon_btn(ft.Icons.CHEVRON_LEFT_ROUNDED, icon_color=T.TEXT_M, icon_size=18, tooltip="Pagina precedente", disabled=self.vocab_page <= 0, on_click=lambda e: go_page(-1)),
                        icon_btn(ft.Icons.CHEVRON_RIGHT_ROUNDED, icon_color=T.TEXT_M, icon_size=18, tooltip="Pagina successiva", disabled=self.vocab_page >= max_page, on_click=lambda e: go_page(1)),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Divider(color=T.BORDER, height=14),
                ft.GridView(
                    controls=[
                        self._study_entry_card(
                            item,
                            accent=T.BELT_VOCAB,
                            on_click=lambda e, selected=item: self._show_vocab_detail(selected),
                            show_chevron=True,
                        )
                        for item in page_items
                    ],
                    expand=True,
                    max_extent=520,
                    child_aspect_ratio=4.45,
                    spacing=12,
                    run_spacing=12,
                    padding=ft.padding.only(top=2, bottom=16),
                ),
            ],
            spacing=0,
            expand=True,
        )

    def _grammar_tab(self) -> ft.Control:
        accent = T.BELT_GRAMMAR
        items = []
        filtered_data = [
            topic for topic in self.grammar_data
            if self._matches_search(topic, ("title", "explanation", "example"))
        ]
        for topic in filtered_data:
            content = ft.Column([
                ft.Text(topic.get("title", ""), size=16, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.BOLD, color=accent),
                ft.Text(topic.get("explanation", ""), size=13, font_family=T.FONT_BODY, color=T.TEXT_M, style=ft.TextStyle(height=1.4)),
                self._example_panel(topic.get("example", ""), compact=True, accent=accent),
            ], spacing=12, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
            
            items.append(
                ft.Container(
                    content=content,
                    bgcolor=T.BG_CARD,
                    border_radius=T.RADIUS,
                    border=ft.border.all(1, accent),
                    padding=ft.padding.all(14),
                    margin=ft.Margin(bottom=10, left=0, right=0, top=0),
                )
            )

        if not items:
            return ft.Container(content=ft.Text("Nessuna regola grammaticale trovata nel json.", color=T.TEXT_M), padding=16)

        return ft.Column([
            ft.Text("Grammatica – 文法", size=18, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_700, color=T.TEXT),
            ft.Divider(color=T.BORDER, height=14),
            ft.ListView(items, expand=True, spacing=0),
        ], expand=True)

    def _update_ui(self, is_build_phase=False):
        self.tab_row.controls.clear()
        self.tab_row.controls.extend([
            self._make_tab_button("あ Hiragana", "hiragana"),
            self._make_tab_button("ア Katakana", "katakana"),
            self._make_tab_button("漢 Kanji", "kanji"),
            self._make_tab_button("語 Vocabolario", "vocab"),
            self._make_tab_button("文 Grammatica", "grammar"),
        ])
        
        if self.active_tab == "hiragana":
            self.content_area.content = centered_stage(self.page, self._kana_tab("Hiragana"), max_width=1040)
        elif self.active_tab == "katakana":
            self.content_area.content = centered_stage(self.page, self._kana_tab("Katakana"), max_width=1040)
        elif self.active_tab == "kanji":
            self.content_area.content = centered_stage(self.page, self._kanji_tab(), max_width=1040)
        elif self.active_tab == "vocab":
            self.content_area.content = centered_stage(self.page, self._vocab_tab(), max_width=980)
        elif self.active_tab == "grammar":
            self.content_area.content = centered_stage(self.page, self._grammar_tab(), max_width=1040)
            
        if not is_build_phase:
            try:
                self.tab_row.update()
            except RuntimeError:
                pass
            try:
                self.content_area.update()
            except RuntimeError:
                pass

    def build(self) -> ft.Control:
        self._update_ui(is_build_phase=True)
        self._track_study_section(self.active_tab)

        masthead = build_masthead(
            title="Hub di Studio",
            subtitle="勉強 – Benkyou",
            on_back=lambda e: self.navigate("dashboard"),
        )

        bg_path = T.bg_image()
        dec_image = ft.DecorationImage(src=bg_path, fit=ft.BoxFit.COVER, opacity=T.BG_OPACITY) if bg_path else None

        return ft.Container(
            bgcolor=T.BG_MAIN,
            image=dec_image,
            expand=True,
            content=ft.Column([
                masthead,
                ft.Container(
                    content=centered_stage(self.page, self.search_field, max_width=1040, expand=False, min_width=640),
                    padding=ft.padding.only(left=20, right=20, top=12, bottom=4),
                ),
                ft.Container(
                    content=centered_stage(self.page, self.tab_row, max_width=1040, expand=False, min_width=640),
                    padding=ft.padding.only(left=20, right=20, top=4, bottom=6)
                ),
                ft.Container(
                    content=self.content_area,
                    expand=True,
                    padding=ft.padding.only(left=20, right=20, bottom=18, top=6)
                )
            ], spacing=0, expand=True)
        )
