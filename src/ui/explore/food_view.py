"""
FoodView – catalogo cucina giapponese.
(Rifattorizzato con Layout Split-Screen Desktop, ricerca per ingredienti e lettura estesa)
"""
from __future__ import annotations
import asyncio
import logging
import flet as ft
from src.core.settings import KotobaTheme as T
from src.core.db_manager import DBManager
from src.core.app_state import get_current_user
from src.core.app_paths import AppPaths
from src.ui.components.loader import show_achievements
from src.ui.components.masthead import build_masthead

CATEGORIES = ["Tutte", "Primo", "Pesce", "Fritto", "Zuppa", "Street food", "Carne", "Dolce", "Bevanda"]
FOOD_CARD_COL = {"xs": 12, "sm": 6, "md": 4, "lg": 3}
FOOD_GRID_BREAKPOINTS = {
    ft.ResponsiveRowBreakpoint.XS: 0,
    ft.ResponsiveRowBreakpoint.SM: 760,
    ft.ResponsiveRowBreakpoint.MD: 1180,
    ft.ResponsiveRowBreakpoint.LG: 1560,
}

_log = logging.getLogger("kotoba.ui.food")

class FoodView:
    def __init__(self, page: ft.Page, navigate, state: dict):
        self.page = page
        self.navigate = navigate
        self.state = state
        self.username = get_current_user(state)
        self.search_text = ""
        self.active_category = "Tutte"
        self.food_data: list[dict] = []
        self._food_img_h = 166
        self._food_text_h = 82
        self._food_title_size = 17
        
        # Elemento attualmente selezionato per la colonna di destra
        self.selected_item: dict | None = None
        self._item_to_card: dict[int, ft.Container] = {}
        
        self._search_task: asyncio.Future | None = None

        self._load_data()

        self.grid = ft.ResponsiveRow(
            columns=12,
            spacing=14,
            run_spacing=14,
            breakpoints=FOOD_GRID_BREAKPOINTS,
        )
        self.grid_scroll = ft.Column(
            [self.grid],
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        )
        self.chips_row = ft.Row(scroll=ft.ScrollMode.AUTO, spacing=8)
        
        # Pannello di Lettura di Destra
        self._detail_key = 0
        self.right_switcher = ft.AnimatedSwitcher(
            content=ft.Container(expand=True),
            duration=260,
            reverse_duration=160,
            transition=ft.AnimatedSwitcherTransition.FADE,
            switch_in_curve=ft.AnimationCurve.EASE_OUT,
            switch_out_curve=ft.AnimationCurve.EASE_IN,
            expand=True,
        )
        self.right_panel = ft.Container(width=620, padding=ft.padding.all(24), content=self.right_switcher)

    # ── Caricamento e Ricerca Inversa per Ingredienti ─────────────────────────

    def _load_data(self):
        data = DBManager.load_json("food.json")
        if data:
            self.food_data = data

    def _set_right_content(self, content: ft.Control, update: bool = True):
        self._detail_key += 1
        self.right_switcher.content = ft.Container(
            key=f"food-detail-{self._detail_key}",
            content=content,
            expand=True,
        )
        if update:
            try:
                self.right_switcher.update()
            except RuntimeError:
                pass

    def _filtered(self) -> list[dict]:
        q = self.search_text.lower().strip()
        keywords = q.split() if q else []
        
        out = []
        for item in self.food_data:
            cat_ok = (self.active_category == "Tutte" or item.get("category") == self.active_category)
            if not cat_ok:
                continue
            
            if keywords:
                primary_text = " ".join([
                    item.get("word", ""),
                    item.get("meaning", ""),
                    item.get("pronunciation", ""),
                ]).lower()
                searchable_text = " ".join([
                    primary_text,
                    item.get("recipe", ""),
                    item.get("description", ""),
                    item.get("story", "")
                ]).lower()
                
                hit = all(kw in searchable_text for kw in keywords)
                if not hit:
                    continue

                exact = q in {
                    item.get("word", "").lower(),
                    item.get("meaning", "").lower(),
                    item.get("pronunciation", "").lower(),
                }
                starts = any(part.startswith(q) for part in primary_text.split())
                primary_hit = all(kw in primary_text for kw in keywords)
                rank = 0 if exact else 1 if starts else 2 if primary_hit else 3
                out.append((rank, item))
            else:
                out.append((0, item))

        if keywords:
            out.sort(key=lambda pair: (
                pair[0],
                pair[1].get("pronunciation", "").lower(),
                pair[1].get("meaning", "").lower(),
            ))
        return [item for _, item in out]

    # ── Selezione e Aggiornamento UI ──────────────────────────────────────────

    def _select_food(self, item: dict):
        prev_item = self.selected_item
        self.selected_item = item
        # O(1): aggiorna solo la card deselezionata e quella appena selezionata
        if prev_item is not None and prev_item is not item:
            prev_card = self._item_to_card.get(id(prev_item))
            if prev_card is not None:
                self._apply_food_card_style(prev_card, prev_item)
                try:
                    if prev_card.page:
                        prev_card.update()
                except RuntimeError:
                    pass
        new_card = self._item_to_card.get(id(item))
        if new_card is not None:
            self._apply_food_card_style(new_card, item)
            try:
                if new_card.page:
                    new_card.update()
            except RuntimeError:
                pass
        self._set_right_content(self._build_right_content(item))
        food_id = item.get("word") or item.get("pronunciation") or item.get("meaning", "")
        try:
            unlocked = DBManager.increment_stat(
                self.username,
                "food_viewed",
                unique_id=food_id,
                total_items=len(self.food_data),
            )
        except Exception:
            _log.exception("food stat tracking failed for %s", food_id)
            return

        try:
            show_achievements(self.page, unlocked)
        except Exception:
            _log.exception("food achievement notification failed for %s", food_id)

    def _apply_food_card_style(self, card: ft.Container, item: dict) -> None:
        is_active = self.selected_item == item
        card.border = ft.border.all(1.5, T.GOLD) if is_active else ft.border.all(1, T.BORDER)
        card.bgcolor = T.BG_SURF if is_active else T.BG_CARD

    def _refresh_grid(self):
        items = self._filtered()
        self.grid.controls.clear()
        self._item_to_card.clear()
        if items and self.selected_item not in items:
            self.selected_item = items[0]
            self._set_right_content(self._build_right_content(self.selected_item))
        elif not items:
            self.selected_item = None
            self._set_right_content(self._build_right_placeholder())
        
        if items:
            for item in items:
                card = self._food_card(item)
                self._item_to_card[id(item)] = card
                self.grid.controls.append(card)
        else:
            self.grid.controls.append(
                ft.Container(
                    col=12,
                    content=ft.Column([
                        ft.Text("無", size=48, font_family=T.FONT_DISPLAY, color=T.BG_SURF),
                        ft.Text("Nessun piatto o ingrediente trovato",
                                color=T.TEXT_M, font_family=T.FONT_BODY, italic=True),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=12),
                    alignment=ft.Alignment(0, 0),
                    expand=True,
                    padding=ft.padding.all(40),
                )
            )
            
        try:
            if self.grid.page:
                self.grid.update()
        except RuntimeError:
            pass

    # ── Chip Categorie (Filtri) ───────────────────────────────────────────────

    def _make_chip(self, cat: str) -> ft.Control:
        active = (cat == self.active_category)
        
        bg_color = T.RED if active else "transparent"
        border_color = T.RED if active else T.BORDER
        text_color = T.BG_MAIN if active else T.TEXT_M

        def on_click(e):
            self.active_category = cat
            self._rebuild_chips()
            self._refresh_grid()

        def on_hover(e):
            if active:
                return
            is_hover = e.data == "true"
            e.control.border = ft.border.all(1, T.RED if is_hover else T.BORDER)
            e.control.bgcolor = T.BG_HOVER if is_hover else "transparent"
            e.control.update()

        return ft.Container(
            content=ft.Text(
                cat, 
                size=12, 
                color=text_color, 
                font_family=T.FONT_BODY,
                weight=ft.FontWeight.W_600 if active else ft.FontWeight.NORMAL
            ),
            bgcolor=bg_color,
            padding=ft.padding.only(left=16, right=16, top=6, bottom=6),
            border_radius=16,
            border=ft.border.all(1, border_color),
            on_click=on_click,
            on_hover=on_hover,
            ink=False,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            animate=ft.Animation(150, ft.AnimationCurve.EASE_OUT)
        )

    def _rebuild_chips(self):
        self.chips_row.controls.clear()
        for cat in CATEGORIES:
            self.chips_row.controls.append(self._make_chip(cat))
        try:
            if self.chips_row.page:
                self.chips_row.update()
        except RuntimeError:
            pass

    # ── Food Card nella Griglia ───────────────────────────────────────────────

    def _food_card(self, item: dict) -> ft.Control:
        cat = item.get("category", "Tutte")
        img_src = AppPaths.food_image_abs(item.get("image", "")) or None
        img_h = self._food_img_h
        text_h = self._food_text_h
        title_size = self._food_title_size
        
        def on_hover(e):
            if self.selected_item == item:
                return # Se è attiva non la faccio lampeggiare
            is_hover = e.data == "true"
            e.control.border = ft.border.all(1, T.GOLD if is_hover else T.BORDER)
            e.control.bgcolor = T.BG_HOVER if is_hover else T.BG_CARD
            e.control.update()

        placeholder = ft.Container(
            expand=True,
            bgcolor=T.BG_INK,
            alignment=ft.Alignment(0, 0),
            content=ft.Text("食", size=48, color=T.BG_SURF, font_family=T.FONT_DISPLAY)
        )

        img_zone = ft.Container(
            height=img_h,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            border=ft.border.only(bottom=ft.BorderSide(1, T.BORDER)),
            content=ft.Stack([
                ft.Container(
                    left=0,
                    top=0,
                    right=0,
                    bottom=0,
                    content=ft.Image(
                        src=img_src,
                        fit=ft.BoxFit.COVER,
                        width=900,
                        height=img_h,
                        error_content=placeholder
                    ) if img_src else placeholder,
                ),
                
                ft.Container(
                    content=ft.Text(cat.upper(), size=9, color=T.TEXT, weight=ft.FontWeight.W_700, font_family=T.FONT_BODY),
                    bgcolor=ft.Colors.with_opacity(0.85, T.BG_INK),
                    padding=ft.padding.only(left=10, right=10, top=4, bottom=4),
                    border_radius=4,
                    right=8, top=8,
                ),
            ]),
        )

        text_zone = ft.Container(
            height=text_h,
            content=ft.Column([
                ft.Text(item.get("word", ""), size=title_size, font_family=T.FONT_DISPLAY,
                        weight=ft.FontWeight.W_700, color=T.TEXT,
                        overflow=ft.TextOverflow.ELLIPSIS, max_lines=1),
                ft.Text(item.get("pronunciation", ""), size=11, color=T.RED, font_family=T.FONT_BODY,
                        italic=True, overflow=ft.TextOverflow.ELLIPSIS, max_lines=1),
                ft.Text(item.get("meaning", ""), size=12, color=T.GOLD, font_family=T.FONT_BODY,
                        weight=ft.FontWeight.W_600, overflow=ft.TextOverflow.ELLIPSIS, max_lines=1),
            ], spacing=3, tight=True),
            padding=ft.padding.only(top=9, bottom=10, left=14, right=14),
        )

        card = ft.Container(
            col=FOOD_CARD_COL,
            content=ft.Column([img_zone, text_zone], spacing=0, tight=True),
            bgcolor=T.BG_CARD,
            border_radius=T.RADIUS,
            border=ft.border.all(1, T.BORDER),
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            animate=ft.Animation(150, ft.AnimationCurve.EASE_OUT),
            on_hover=on_hover,
            on_click=lambda e, it=item: self._select_food(it),
            ink=False,
        )
        self._apply_food_card_style(card, item)
        return card

    # ── Pannello Dettagli di Destra (Oshinagaki) ──────────────────────────────

    def _build_right_content(self, item: dict) -> ft.Control:
        cat = item.get("category", "Tutte")
        allergens = item.get("allergens", [])
        
        allergen_row = ft.Row(
            [ft.Container(
                content=ft.Text(a.upper(), size=10, color=T.BG_MAIN, weight=ft.FontWeight.W_700),
                bgcolor=T.RED,
                padding=ft.padding.only(top=4, bottom=4, left=8, right=8),
                border_radius=4,
             ) for a in allergens] if allergens else
            [ft.Text("Nessun allergene noto", size=12, color=T.TEXT_M, font_family=T.FONT_BODY, italic=True)],
            wrap=True, spacing=8, run_spacing=8,
        )

        def section_title(kanji: str, title: str) -> ft.Control:
            return ft.Row([
                ft.Text(kanji, size=14, color=T.INDIGO, font_family=T.FONT_DISPLAY),
                ft.Text(title, size=12, color=T.TEXT_M, weight=ft.FontWeight.W_700, font_family=T.FONT_BODY, italic=True),
            ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER)

        return ft.Column([
            ft.Row([
                ft.Column([
                    ft.Text(item.get("word", ""), size=32, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_700, color=T.TEXT),
                    ft.Text(f"/{item.get('pronunciation', '')}/", size=14, color=T.GOLD, font_family=T.FONT_BODY, italic=True),
                ], spacing=0, expand=True),
                ft.Container(
                    content=ft.Text(cat.upper(), size=10, color=T.BG_MAIN, weight=ft.FontWeight.W_700),
                    bgcolor=T.TEXT_M,
                    padding=ft.padding.only(top=6, bottom=6, left=12, right=12),
                    border_radius=4,
                ),
            ], vertical_alignment=ft.CrossAxisAlignment.START),
            
            ft.Divider(color=T.BORDER, height=18),
            
            section_title("説明", "Descrizione"),
            ft.Text(item.get("description", ""), size=13, color=T.TEXT, font_family=T.FONT_BODY, style=ft.TextStyle(height=1.4)),
            ft.Container(height=4),
            
            section_title("歴史", "Storia e Origini"),
            ft.Text(item.get("story", ""), size=13, color=T.TEXT, font_family=T.FONT_BODY, italic=True, style=ft.TextStyle(height=1.4)),
            ft.Container(height=4),
            
            section_title("材料", "Ingredienti / Ricetta Base"),
            ft.Container(
                content=ft.Text(item.get("recipe", ""), size=12, color=T.GOLD, font_family=T.FONT_BODY, style=ft.TextStyle(height=1.4)),
                bgcolor=T.BG_SURF,
                padding=ft.padding.all(12),
                border_radius=T.RADIUS,
                border=ft.border.only(left=ft.BorderSide(2, T.GOLD)),
            ),
            ft.Container(height=4),
            
            section_title("警告", "Allergeni"),
            allergen_row,
            
        ], spacing=10, tight=True, scroll=ft.ScrollMode.AUTO, expand=True)

    def _build_right_placeholder(self) -> ft.Control:
        return ft.Column([
            ft.Container(
                expand=True,
                alignment=ft.Alignment.CENTER,
                content=ft.Column([
                    ft.Text("食", size=72, color=T.BG_SURF, font_family=T.FONT_DISPLAY),
                    ft.Container(height=8),
                    ft.Text(
                        "Seleziona un piatto dalla griglia per scoprirne la storia e gli ingredienti", 
                        size=T.FS_SMALL, 
                        font_family=T.FONT_BODY, 
                        color=T.TEXT_M, 
                        italic=True
                    )
                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            )
        ], expand=True)

    # ── Costruzione Vista Principale ──────────────────────────────────────────

    def _on_search(self, value: str):
        if self._search_task:
            self._search_task.cancel()
        self._search_task = self.page.run_task(self._debounced_search, value)

    async def _debounced_search(self, value: str):
        try:
            await asyncio.sleep(0.2)
        except asyncio.CancelledError:
            return
        self.search_text = value
        self._refresh_grid()

    def build(self) -> ft.Control:
        self._rebuild_chips()
        self._refresh_grid()

        search_field = ft.TextField(
            hint_text="Cerca un piatto o inserisci gli ingredienti (es. 'riso uova')...",
            prefix_icon=ft.Icons.SEARCH,
            bgcolor=T.BG_SURF,
            border_color="transparent",
            focused_border_color=T.GOLD,
            color=T.TEXT,
            hint_style=ft.TextStyle(color=T.TEXT_M, font_family=T.FONT_BODY),
            text_style=ft.TextStyle(font_family=T.FONT_BODY),
            border_radius=T.RADIUS,
            expand=True,
            height=44,
            content_padding=ft.padding.only(left=16, right=16, top=0, bottom=0),
            on_change=lambda e: self._on_search(e.control.value),
        )

        masthead = build_masthead(
            title="Cibo Giapponese",
            subtitle="和食 – Washoku",
            on_back=lambda e: self.navigate("dashboard"),
            trailing=ft.Text(
                f"{len(self.food_data)} piatti disponibili",
                size=T.FS_SMALL,
                color=T.TEXT_M,
                font_family=T.FONT_BODY,
            ),
        )

        bg_path = T.bg_image()
        dec_image = None
        if bg_path:
            dec_image = ft.DecorationImage(
                src=bg_path,
                fit=ft.BoxFit.COVER,
                opacity=T.BG_OPACITY
            )

        return ft.Container(
            bgcolor=T.BG_MAIN,
            image=dec_image,
            expand=True,
            content=ft.Column([
                masthead,
                # Barra di ricerca e Filtri che occupano tutto lo schermo in alto
                ft.Container(
                    content=search_field,
                    padding=ft.padding.only(left=20, right=20, top=12, bottom=0),
                ),
                ft.Container(
                    content=self.chips_row,
                    padding=ft.padding.only(left=20, right=20, top=10, bottom=10),
                ),
                ft.Row(
                    [
                        ft.Container(
                            content=self.grid_scroll,
                            expand=True,
                            padding=ft.padding.only(left=20, right=20, top=0, bottom=18),
                            border=ft.border.only(right=ft.BorderSide(1, T.BORDER)),
                        ),
                        self.right_panel,
                    ],
                    expand=True,
                    spacing=0,
                )
            ], spacing=0, expand=True)
        )
