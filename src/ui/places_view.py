"""
PlacesView – Esplorazione del Giappone: Luoghi Moderni, Antichi e Lavori Tipici
(Design System Sumi-e: Colori dinamici corretti e Hover reattivi)
"""
from __future__ import annotations
import flet as ft
from src.core.settings import KotobaTheme as T
from src.core.db_manager import DBManager
from src.core.app_state import get_current_user
from src.ui.components.loader import show_achievements
from src.ui.components.masthead import build_masthead

class PlacesView:
    def __init__(self, page: ft.Page, navigate, state: dict):
        self.page = page
        self.navigate = navigate
        self.state = state
        self.username = get_current_user(state)
        
        # Stato interno di navigazione
        self.active_category = "Giappone Moderno"
        self.selected_item: dict | None = None
        self.card_containers: list[ft.Container] = []
        self.explore_data: list[dict] = []
        
        self._load_data()
        
        # Componenti dell'interfaccia split
        self.left_list_container = ft.Container(expand=True)
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
        self.right_panel = ft.Container(expand=6, padding=ft.padding.all(24), content=self.right_switcher)
        self.tab_row = ft.Row(spacing=8)

    def _set_right_content(self, content: ft.Control, update: bool = True):
        self._detail_key += 1
        self.right_switcher.content = ft.Container(
            key=f"places-detail-{self._detail_key}",
            content=content,
            expand=True,
        )
        if update:
            try:
                self.right_switcher.update()
            except RuntimeError:
                pass

    def _load_data(self):
        explore = DBManager.load_json("explore.json") or []
        museums = DBManager.load_json("museums.json") or []
        self.explore_data = []
        if isinstance(explore, list):
            self.explore_data.extend(explore)
        if isinstance(museums, list):
            self.explore_data.extend(museums)

    def _select_item(self, item: dict, track_view: bool = True):
        self.selected_item = item
        self._refresh_list_view()
        self._set_right_content(self._build_right_content(item))
        if track_view:
            show_achievements(
                self.page,
                DBManager.increment_stat(self.username, "places_viewed", unique_id=item.get("name", "")),
            )

    def _get_category_style(self, category: str) -> tuple[str, str]:
        """Ritorna il Kanji e il colore tematico per la categoria specificata."""
        if category == "Giappone Moderno":
            return "新", T.INDIGO
        elif category == "Giappone Antico":
            return "古", T.RED  # Antico = Rosso Torii
        elif category == "Musei":
            return "博", T.GREEN
        elif category == "Lavori Tipici":
            return "職", T.GOLD # Lavori = Oro Maestria
        return "探", T.GOLD

    def _make_tab_button(self, label: str, cat_key: str) -> ft.Control:
        is_active = (self.active_category == cat_key)
        _, cat_color = self._get_category_style(cat_key)
        
        bg_color = T.BG_SURF if is_active else "transparent"
        border_color = cat_color if is_active else T.BORDER
        text_color = cat_color if is_active else T.TEXT_M

        def on_click(e):
            self.active_category = cat_key
            filtered = [x for x in self.explore_data if x.get("category") == self.active_category]
            self.selected_item = filtered[0] if filtered else None
            self._update_tabs_and_list()

        # Animazione di Hover per i bottoni delle categorie
        def on_hover(e):
            if is_active:
                return
            is_hover = e.data == "true"
            # Usare e.control garantisce che Flet trovi l'elemento corretto
            e.control.border = ft.border.all(1, cat_color if is_hover else T.BORDER)
            e.control.bgcolor = T.BG_HOVER if is_hover else "transparent"
            e.control.update()

        return ft.Container(
            content=ft.Text(
                label,
                size=11,
                color=text_color,
                font_family=T.FONT_BODY,
                weight=ft.FontWeight.W_600 if is_active else ft.FontWeight.NORMAL,
                overflow=ft.TextOverflow.ELLIPSIS,
                no_wrap=True,
            ),
            bgcolor=bg_color,
            expand=True,
            height=42,
            alignment=ft.Alignment.CENTER,
            padding=ft.padding.symmetric(horizontal=8, vertical=6),
            border_radius=14,
            border=ft.border.all(1, border_color),
            on_click=on_click,
            on_hover=on_hover,
            ink=False,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            animate=ft.Animation(150, ft.AnimationCurve.EASE_OUT)
        )

    def _place_card(self, item: dict, index: int) -> ft.Container:
        is_active = (self.selected_item == item)
        kanji, stamp_color = self._get_category_style(item.get("category", ""))
        
        default_border = ft.border.all(1.5, stamp_color) if is_active else ft.border.all(1, T.BORDER)
        default_bg = T.BG_SURF if is_active else T.BG_CARD

        # Animazione di Hover per le Card
        def on_hover(e):
            if is_active:
                return
            is_hover = e.data == "true"
            # Usare e.control risolve il bug di mancato aggiornamento
            e.control.border = ft.border.all(1, stamp_color if is_hover else T.BORDER)
            e.control.bgcolor = T.BG_HOVER if is_hover else T.BG_CARD
            e.control.update()

        hanko_stamp = ft.Container(
            width=26,
            height=26,
            border=ft.border.all(1.5, stamp_color),
            border_radius=4,
            alignment=ft.Alignment.CENTER,
            content=ft.Text(kanji, size=11, color=stamp_color, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_700)
        )

        return ft.Container(
            on_click=lambda e: self._select_item(item),
            on_hover=on_hover,
            bgcolor=default_bg,
            border_radius=T.RADIUS,
            border=default_border,
            margin=ft.Margin(bottom=8, left=0, right=0, top=0),
            padding=ft.padding.all(12),
            animate=ft.Animation(150, ft.AnimationCurve.EASE_OUT),
            ink=False,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            content=ft.Row([
                hanko_stamp,
                ft.Column([
                    ft.Row([
                        ft.Text(item.get("name", ""), size=13, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_700, color=T.TEXT),
                        ft.Container(expand=True),
                        ft.Text(item.get("tag", ""), size=10, color=T.TEXT_M, font_family=T.FONT_BODY)
                    ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.Text(f"{item.get('jp', '')} · {item.get('city', '')}", size=T.FS_SMALL, font_family=T.FONT_BODY, color=stamp_color if is_active else T.TEXT_M),
                ], expand=True, spacing=2),
                ft.Icon(ft.Icons.CHEVRON_RIGHT_ROUNDED, size=16, color=T.TEXT_M)
            ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER)
        )

    def _build_right_content(self, item: dict) -> ft.Control:
        _, stamp_color = self._get_category_style(item.get("category", ""))
        return ft.Column([
            ft.Row([
                ft.Column([
                    ft.Text(item.get("name", ""), size=24, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_700, color=T.TEXT),
                    # Il colore del sottotitolo richiama la categoria
                    ft.Text(f"{item.get('jp', '')} — {item.get('city', '')}", size=T.FS_BODY, font_family=T.FONT_DISPLAY, color=stamp_color, italic=True),
                ], spacing=2, expand=True),
                ft.Container(
                    content=ft.Text(item.get("tag", "").upper(), size=10, color=T.BG_MAIN, weight=ft.FontWeight.W_700, font_family=T.FONT_BODY),
                    bgcolor=T.TEXT_M,
                    padding=ft.padding.only(left=12, right=12, top=6, bottom=6),
                    border_radius=4,
                )
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            
            ft.Divider(color=T.BORDER, height=18),
            
            # Qui ho sostituito T.INDIGO con la variabile dinamica stamp_color
            ft.Text("概要 — Descrizione", size=14, color=stamp_color, font_family=T.FONT_DISPLAY),
            ft.Text(item.get("description", ""), size=13, color=T.TEXT, font_family=T.FONT_BODY, style=ft.TextStyle(height=1.4)),
            ft.Container(height=8),
            
            # Stessa cosa qui
            ft.Text("詳細 — Approfondimento", size=14, color=stamp_color, font_family=T.FONT_DISPLAY),
            ft.Container(
                content=ft.Text(item.get("detail", ""), size=13, color=T.TEXT, font_family=T.FONT_BODY, style=ft.TextStyle(height=1.4)),
                expand=True
            )
        ], scroll=ft.ScrollMode.AUTO, expand=True)

    def _build_right_placeholder(self) -> ft.Control:
        return ft.Column([
            ft.Container(
                expand=True,
                alignment=ft.Alignment.CENTER,
                content=ft.Column([
                    ft.Text("探", size=72, color=T.BG_SURF, font_family=T.FONT_DISPLAY),
                    ft.Container(height=8),
                    ft.Text("Seleziona una voce dall'elenco per esplorare il modulo", size=T.FS_SMALL, font_family=T.FONT_BODY, color=T.TEXT_M, italic=True)
                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            )
        ], expand=True)

    def _build_empty_list_message(self) -> ft.Control:
        return ft.Container(
            content=ft.Column([
                ft.Text("無", size=48, color=T.BG_SURF, font_family=T.FONT_DISPLAY),
                ft.Text("Nessun elemento trovato per questa categoria.", size=12, color=T.TEXT_M, font_family=T.FONT_BODY, italic=True)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER),
            expand=True,
            alignment=ft.Alignment(0, -0.5)
        )

    def _update_tabs_and_list(self):
        self.tab_row.controls.clear()
        self.tab_row.controls.append(self._make_tab_button("新 Moderno", "Giappone Moderno"))
        self.tab_row.controls.append(self._make_tab_button("古 Antico", "Giappone Antico"))
        self.tab_row.controls.append(self._make_tab_button("博 Musei", "Musei"))
        self.tab_row.controls.append(self._make_tab_button("職 Lavori", "Lavori Tipici"))
        try:
            self.tab_row.update()
        except RuntimeError:
            pass
        
        self._refresh_list_view()
        
        if self.selected_item:
            self._set_right_content(self._build_right_content(self.selected_item))
        else:
            self._set_right_content(self._build_right_placeholder())

    def _refresh_list_view(self):
        filtered_items = [x for x in self.explore_data if x.get("category") == self.active_category]
        if filtered_items and self.selected_item not in filtered_items:
            self.selected_item = filtered_items[0]
        
        if not filtered_items:
            self.left_list_container.content = self._build_empty_list_message()
        else:
            self.card_containers = [self._place_card(p, i) for i, p in enumerate(filtered_items)]
            self.left_list_container.content = ft.ListView(
                controls=self.card_containers,
                expand=True,
                spacing=0,
                padding=ft.padding.only(left=0, right=0, bottom=14, top=8)
            )
        try:
            self.left_list_container.update()
        except RuntimeError:
            pass

    def build(self) -> ft.Control:
        self.tab_row.controls.clear()
        self.tab_row.controls.append(self._make_tab_button("新 Moderno", "Giappone Moderno"))
        self.tab_row.controls.append(self._make_tab_button("古 Antico", "Giappone Antico"))
        self.tab_row.controls.append(self._make_tab_button("博 Musei", "Musei"))
        self.tab_row.controls.append(self._make_tab_button("職 Lavori", "Lavori Tipici"))
        
        filtered_items = [x for x in self.explore_data if x.get("category") == self.active_category]
        if filtered_items and self.selected_item not in filtered_items:
            self.selected_item = filtered_items[0]
        if not filtered_items:
            self.left_list_container.content = self._build_empty_list_message()
        else:
            self.card_containers = [self._place_card(p, i) for i, p in enumerate(filtered_items)]
            self.left_list_container.content = ft.ListView(
                controls=self.card_containers,
                expand=True,
                spacing=0,
                padding=ft.padding.only(left=0, right=0, bottom=14, top=8)
            )
            
        if self.selected_item:
            self._set_right_content(self._build_right_content(self.selected_item), update=False)
        else:
            self._set_right_content(self._build_right_placeholder(), update=False)

        masthead = build_masthead(
            title="Esplora il Giappone",
            subtitle="日本探索 – Nihon Tansaku",
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
                ft.Row([
                    ft.Container(
                        content=ft.Column([
                            ft.Container(content=self.tab_row, padding=ft.padding.only(top=12, bottom=8)),
                            self.left_list_container
                        ], spacing=0, expand=True),
                        expand=4,
                        padding=ft.padding.only(left=20, right=14, bottom=0, top=0),
                        border=ft.border.only(right=ft.BorderSide(1, T.BORDER))
                    ),
                    self.right_panel
                ], expand=True, spacing=0)
            ], spacing=0, expand=True)
        )
