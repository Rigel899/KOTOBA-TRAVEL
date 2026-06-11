"""
HistoryView – vera timeline verticale interattiva con layout split-screen
(Rifattorizzato con Design System Sumi-e e asse cronologico continuo)
"""
from __future__ import annotations
import flet as ft
from src.core.settings import KotobaTheme as T
from src.core.db_manager import DBManager
from src.core.app_state import get_current_user
from src.ui.components.loader import show_achievements
from src.ui.components.masthead import build_masthead

class HistoryView:
    PERIOD_ORDER = [
        "Panoramica",
        "Origini",
        "Corte e Stato",
        "Eta samuraica",
        "Edo e contatti",
        "Modernizzazione",
        "Novecento e oggi",
        "Popoli e regioni",
    ]

    def __init__(self, page: ft.Page, navigate, state: dict):
        self.page = page
        self.navigate = navigate
        self.state = state
        self.username = get_current_user(state)
        self.history_data = self._load_data()
        
        self.selected_index: int | None = None
        self.timeline_stacks: list[ft.Control] = []
        self.timeline_refs: dict[int, dict[str, ft.Control]] = {}
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
        self.right_panel = ft.Container(expand=6, padding=ft.padding.all(32), content=self.right_switcher)

    def _set_right_content(self, content: ft.Control, update: bool = True):
        self._detail_key += 1
        self.right_switcher.content = ft.Container(
            key=f"history-detail-{self._detail_key}",
            content=content,
            expand=True,
        )
        if update:
            try:
                self.right_switcher.update()
            except RuntimeError:
                pass

    def _load_data(self) -> list[dict]:
        data = DBManager.load_json("history.json")
        if not data:
            return []
        if isinstance(data, dict) and "topics" in data:
            return data["topics"]
        elif isinstance(data, list):
            return data
        return []

    def _apply_era_style(self, refs: dict, is_active: bool) -> None:
        refs["card"].border = ft.border.all(1, T.GOLD) if is_active else ft.border.all(1, T.BORDER)
        refs["card"].bgcolor = T.BG_SURF if is_active else T.BG_CARD
        refs["dot"].bgcolor = T.GOLD if is_active else T.BG_MAIN
        refs["dot"].border = ft.border.all(4, T.GOLD) if is_active else ft.border.all(2, T.GOLD)

    def _select_era(self, index: int):
        prev_index = self.selected_index
        self.selected_index = index
        # O(1): aggiorna solo il nodo precedente e quello nuovo
        if prev_index is not None and prev_index != index:
            prev_refs = self.timeline_refs.get(prev_index)
            if prev_refs is not None:
                self._apply_era_style(prev_refs, is_active=False)
                try:
                    prev_refs["stack"].update()
                except RuntimeError:
                    pass
        new_refs = self.timeline_refs.get(index)
        if new_refs is not None:
            self._apply_era_style(new_refs, is_active=True)
            try:
                new_refs["stack"].update()
            except RuntimeError:
                pass
        
        # Aggiorna il pannello di lettura a destra
        era = self.history_data[index]
        self._set_right_content(self._build_right_content(era))
        
        show_achievements(
            self.page,
            DBManager.increment_stat(
                self.username,
                "history_viewed",
                unique_id=era.get("title", ""),
                total_items=len(self.history_data),
            ),
        )

    def _build_right_content(self, era: dict) -> ft.Control:
        return ft.Column([
            ft.Text(
                era.get("title", "Epoca Sconosciuta"), 
                size=24, 
                font_family=T.FONT_DISPLAY, 
                weight=ft.FontWeight.W_700, 
                color=T.TEXT
            ),
            ft.Text(
                era.get("subtitle", ""), 
                size=T.FS_BODY, 
                font_family=T.FONT_BODY, 
                color=T.INDIGO,
                italic=True
            ),
            ft.Container(height=12),
            ft.Divider(color=T.BORDER, height=1),
            ft.Container(height=16),
            ft.Container(
                content=ft.Text(
                    era.get("content", ""), 
                    size=14, 
                    font_family=T.FONT_BODY, 
                    color=T.TEXT, 
                    selectable=True,
                    style=ft.TextStyle(height=1.5)
                ),
                expand=True
            )
        ], scroll=ft.ScrollMode.AUTO, expand=True)

    def _build_right_placeholder(self) -> ft.Control:
        return ft.Column([
            ft.Container(
                expand=True,
                alignment=ft.Alignment.CENTER,
                content=ft.Column([
                    ft.Text("史", size=72, color=T.BG_SURF, font_family=T.FONT_DISPLAY),
                    ft.Container(height=8),
                    ft.Text(
                        "Seleziona un'epoca dalla timeline per esplorare la storia", 
                        size=T.FS_SMALL, 
                        font_family=T.FONT_BODY, 
                        color=T.TEXT_M, 
                        italic=True
                    )
                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            )
        ], expand=True)

    def _era_period(self, era: dict) -> str:
        period = era.get("period")
        if period in self.PERIOD_ORDER:
            return period
        return "Popoli e regioni"

    def _ordered_indices(self) -> list[int]:
        ordered: list[int] = []
        for period in self.PERIOD_ORDER:
            ordered.extend(
                idx for idx, era in enumerate(self.history_data)
                if self._era_period(era) == period
            )
        return ordered

    def _period_header(self, label: str) -> ft.Control:
        return ft.Container(
            padding=ft.padding.only(left=40, top=12, bottom=10),
            content=ft.Row(
                [
                    ft.Container(width=4, height=18, bgcolor=T.INDIGO, border_radius=3),
                    ft.Text(label, size=13, color=T.INDIGO, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_700),
                ],
                spacing=9,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    def _timeline_item(self, era: dict, index: int, is_last: bool = False) -> ft.Stack:

        def on_hover(e):
            if self.selected_index == index:
                return
            is_hover = e.data == "true"
            card.border = ft.border.all(1, T.GOLD) if is_hover else ft.border.all(1, T.BORDER)
            card.bgcolor = T.BG_HOVER if is_hover else T.BG_CARD
            card.update()

        # La Card interattiva
        card = ft.Container(
            on_click=lambda e: self._select_era(index),
            on_hover=on_hover,
            bgcolor=T.BG_SURF if self.selected_index == index else T.BG_CARD,
            border_radius=T.RADIUS,
            border=ft.border.all(1, T.GOLD if self.selected_index == index else T.BORDER),
            padding=ft.padding.all(14),
            animate=ft.Animation(150, ft.AnimationCurve.EASE_OUT),
            ink=False,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            content=ft.Row([
                ft.Column([
                    ft.Text(
                        era.get("title", "Epoca"), 
                        size=14, 
                        font_family=T.FONT_DISPLAY, 
                        weight=ft.FontWeight.W_700, 
                        color=T.TEXT
                    ),
                    ft.Text(
                        era.get("subtitle", ""), 
                        size=T.FS_SMALL, 
                        font_family=T.FONT_BODY,
                        color=T.TEXT_M, 
                        max_lines=1, 
                        overflow=ft.TextOverflow.ELLIPSIS
                    ),
                ], expand=True, spacing=2),
                ft.Icon(ft.Icons.CHEVRON_RIGHT_ROUNDED, size=16, color=T.TEXT_M)
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER)
        )

        # Il Wrapper che disegna la linea continua verticale
        line_border_color = "transparent" if is_last else T.BORDER
        line_wrapper = ft.Container(
            margin=ft.Margin(left=16, top=0, bottom=0, right=0),
            border=ft.border.only(left=ft.BorderSide(2, line_border_color)),
            padding=ft.padding.only(left=24, bottom=16), # Spazio a sinistra della card e sotto
            content=card
        )

        # Il Nodo (Cerchio sulla linea)
        dot = ft.Container(
            left=9,  # Posizionato esattamente al centro della linea di bordo
            top=22,  # Allineato visivamente al centro della card
            width=16,
            height=16,
            border_radius=8,
            bgcolor=T.GOLD if self.selected_index == index else T.BG_MAIN,
            border=ft.border.all(4, T.GOLD) if self.selected_index == index else ft.border.all(2, T.GOLD),
            animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT)
        )

        # Lo Stack unisce la linea di background, la card e il nodo in primo piano
        stack = ft.Stack([line_wrapper, dot])
        self.timeline_refs[index] = {"stack": stack, "card": card, "dot": dot}
        return stack

    def build(self) -> ft.Control:
        self.timeline_stacks.clear()
        self.timeline_refs.clear()
        
        if not self.history_data:
            left_content = ft.Container(
                content=ft.Text("Impossibile caricare history.json.", color=T.ERR),
                padding=16
            )
        else:
            if self.selected_index is None:
                self.selected_index = 0

            ordered_indices = self._ordered_indices()
            for period in self.PERIOD_ORDER:
                indices = [i for i in ordered_indices if self._era_period(self.history_data[i]) == period]
                if not indices:
                    continue
                self.timeline_stacks.append(self._period_header(period))
                for i in indices:
                    is_last = i == ordered_indices[-1]
                    self.timeline_stacks.append(self._timeline_item(self.history_data[i], i, is_last=is_last))
            
            left_content = ft.ListView(
                controls=self.timeline_stacks,
                expand=True,
                spacing=0,
                padding=ft.padding.only(left=16, right=16, bottom=24, top=16)
            )

        if self.history_data and self.selected_index is not None:
            self._set_right_content(self._build_right_content(self.history_data[self.selected_index]), update=False)
        else:
            self._set_right_content(self._build_right_placeholder(), update=False)

        # Masthead Superiore
        masthead = build_masthead(
            title="Storia del Giappone",
            subtitle="日本の歴史 – Nihon no rekishi",
            on_back=lambda e: self.navigate("dashboard"),
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
                ft.Row([
                    ft.Container(
                        content=left_content,
                        expand=4,
                        border=ft.border.only(right=ft.BorderSide(1, T.BORDER))
                    ),
                    self.right_panel
                ], expand=True, spacing=0)
            ], spacing=0, expand=True)
        )
