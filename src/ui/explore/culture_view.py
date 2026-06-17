"""
CultureView – cultura giapponese in layout split-screen a due colonne
(Rifattorizzato con Design System Sumi-e, Hanko stamps, Kintsugi hover ed ergonomia desktop)
"""
from __future__ import annotations
import logging
import flet as ft
from src.core.settings import KotobaTheme as T
from src.core.db_manager import DBManager
from src.core.app_state import get_current_user
from src.ui.components.loader import show_achievements
from src.ui.components.masthead import build_masthead

_log = logging.getLogger("kotoba.ui.culture")

class CultureView:
    CATEGORY_ORDER = [
        "Lingua e scrittura",
        "Studio pratico",
        "Societa e abitudini",
        "Tradizioni e stagioni",
        "Cultura quotidiana",
    ]

    def __init__(self, page: ft.Page, navigate, state: dict):
        self.page = page
        self.navigate = navigate
        self.state = state
        self.username = get_current_user(state)
        self.culture_data = self._load_data()
        
        # Stato interno per tracciare la selezione
        self.selected_index: int | None = None
        self.card_containers: dict[int, ft.Container] = {}
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
        
        self.kanji_single_nums = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十", "十一", "十二", "十三", "十四", "十五"]

    def _set_right_content(self, content: ft.Control, update: bool = True):
        self._detail_key += 1
        self.right_switcher.content = ft.Container(
            key=f"culture-detail-{self._detail_key}",
            content=content,
            expand=True,
        )
        if update:
            try:
                self.right_switcher.update()
            except RuntimeError:
                pass

    def _load_data(self) -> list[dict]:
        data = DBManager.load_json("culture.json")
        if not data:
            return []
        if isinstance(data, dict) and "topics" in data:
            return data["topics"]
        elif isinstance(data, list):
            return data
        return []

    @staticmethod
    def _kanji_number(number: int) -> str:
        digits = "零一二三四五六七八九"
        if number <= 0:
            return str(number)
        if number < 10:
            return digits[number]
        if number < 20:
            rest = number % 10
            return "十" + (digits[rest] if rest else "")
        if number < 100:
            tens, ones = divmod(number, 10)
            return f"{digits[tens]}十{digits[ones] if ones else ''}"
        return str(number)

    def _safe_control_update(self, control: ft.Control) -> None:
        if not getattr(control, "page", None):
            return
        try:
            control.update()
        except RuntimeError:
            pass

    def _select_topic(self, index: int):
        prev_index = self.selected_index
        self.selected_index = index
        # O(1): aggiorna solo la card precedente e quella nuova
        if prev_index is not None and prev_index != index:
            prev_card = self.card_containers.get(prev_index)
            if prev_card is not None:
                prev_card.border = ft.border.all(1, T.BORDER)
                prev_card.bgcolor = T.BG_CARD
                self._safe_control_update(prev_card)
        new_card = self.card_containers.get(index)
        if new_card is not None:
            new_card.border = ft.border.all(1, T.GOLD)
            new_card.bgcolor = T.BG_SURF
            self._safe_control_update(new_card)
        
        # Rigenera e aggiorna il contenuto del pannello di destra
        topic = self.culture_data[index]
        self._set_right_content(self._build_right_content(topic))
        
        # Incrementa le statistiche di lettura
        try:
            unlocked = DBManager.increment_stat(
                self.username,
                "culture_viewed",
                unique_id=topic.get("title", ""),
                total_items=len(self.culture_data),
            )
        except Exception:
            _log.exception("culture stat tracking failed for %s", topic.get("title", ""))
            return

        try:
            show_achievements(self.page, unlocked)
        except Exception:
            _log.exception("culture achievement notification failed for %s", topic.get("title", ""))

    def _topic_category(self, topic: dict) -> str:
        category = topic.get("category")
        if category in self.CATEGORY_ORDER:
            return category
        return "Cultura quotidiana"

    def _category_header(self, label: str) -> ft.Control:
        return ft.Container(
            padding=ft.padding.only(top=10, bottom=8),
            content=ft.Row(
                [
                    ft.Container(width=4, height=18, bgcolor=T.GOLD, border_radius=3),
                    ft.Text(label, size=13, color=T.GOLD, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_700),
                ],
                spacing=9,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    def _grouped_topic_indices(self) -> list[tuple[str, list[int]]]:
        grouped: list[tuple[str, list[int]]] = []
        for category in self.CATEGORY_ORDER:
            indices = [
                idx for idx, topic in enumerate(self.culture_data)
                if self._topic_category(topic) == category
            ]
            if indices:
                grouped.append((category, indices))
        return grouped

    def _build_right_content(self, topic: dict) -> ft.Control:
        """Costruisce il layout editoriale per il pannello di lettura destro."""
        return ft.Column([
            ft.Text(
                topic.get("title", "Titolo Sconosciuto"), 
                size=24, 
                font_family=T.FONT_DISPLAY, 
                weight=ft.FontWeight.W_700, 
                color=T.TEXT
            ),
            ft.Text(
                topic.get("subtitle", ""), 
                size=T.FS_BODY, 
                font_family=T.FONT_BODY, 
                color=T.GOLD, 
                italic=True
            ),
            ft.Container(height=12),
            ft.Divider(color=T.BORDER, height=1),
            ft.Container(height=16),
            ft.Container(
                content=ft.Text(
                    topic.get("content", ""), 
                    size=14, 
                    font_family=T.FONT_BODY, 
                    color=T.TEXT, 
                    selectable=True,
                    style=ft.TextStyle(height=1.5) # <-- Soluzione corretta per Flet 0.80+
                ),
                expand=True
            )
        ], scroll=ft.ScrollMode.AUTO, expand=True)

    def _build_right_placeholder(self) -> ft.Control:
        """Schermata di attesa quando nessun capitolo è ancora selezionato."""
        return ft.Column([
            ft.Container(
                expand=True,
                alignment=ft.Alignment.CENTER,
                content=ft.Column([
                    ft.Text("文", size=72, color=T.BG_SURF, font_family=T.FONT_DISPLAY),
                    ft.Container(height=8),
                    ft.Text(
                        "Seleziona un capitolo dall'elenco per iniziare la lettura", 
                        size=T.FS_SMALL, 
                        font_family=T.FONT_BODY, 
                        color=T.TEXT_M, 
                        italic=True
                    )
                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            )
        ], expand=True)

    def _topic_card(self, topic: dict, index: int) -> ft.Container:
        kanji_num = self._kanji_number(index + 1)
        num_size = 12 if len(kanji_num) <= 2 else 10

        def on_hover(e):
            if self.selected_index == index:
                return
            is_hover = e.data == "true"
            card.border = ft.border.all(1, T.GOLD) if is_hover else ft.border.all(1, T.BORDER)
            card.bgcolor = T.BG_HOVER if is_hover else T.BG_CARD
            self._safe_control_update(card)

        hanko_stamp = ft.Container(
            width=34,
            height=30,
            border=ft.border.all(1.5, T.RED),
            border_radius=5,
            alignment=ft.Alignment.CENTER,
            content=ft.Text(
                kanji_num,
                size=num_size,
                color=T.RED,
                font_family=T.FONT_DISPLAY,
                weight=ft.FontWeight.W_700
            )
        )

        card = ft.Container(
            on_click=lambda e: self._select_topic(index),
            on_hover=on_hover,
            bgcolor=T.BG_SURF if self.selected_index == index else T.BG_CARD,
            border_radius=T.RADIUS,
            border=ft.border.all(1, T.GOLD if self.selected_index == index else T.BORDER),
            margin=ft.Margin(bottom=10, left=0, right=0, top=0),
            padding=ft.padding.all(14),
            animate=ft.Animation(150, ft.AnimationCurve.EASE_OUT),
            ink=False,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            content=ft.Row([
                hanko_stamp,
                ft.Column([
                    ft.Text(
                        topic.get("title", "Titolo Sconosciuto"), 
                        size=14, 
                        font_family=T.FONT_DISPLAY, 
                        weight=ft.FontWeight.W_700, 
                        color=T.TEXT
                    ),
                    ft.Text(
                        topic.get("subtitle", ""), 
                        size=T.FS_SMALL, 
                        font_family=T.FONT_BODY,
                        color=T.TEXT_M, 
                        max_lines=1, 
                        overflow=ft.TextOverflow.ELLIPSIS
                    ),
                ], expand=True, spacing=2),
                ft.Icon(ft.Icons.CHEVRON_RIGHT_ROUNDED, size=16, color=T.TEXT_M)
            ], spacing=14, vertical_alignment=ft.CrossAxisAlignment.CENTER)
        )
        return card

    def build(self) -> ft.Control:
        self.card_containers.clear()
        
        if not self.culture_data:
            left_content = ft.Container(
                content=ft.Text("Impossibile caricare culture.json.", color=T.ERR),
                padding=16
            )
        else:
            if self.selected_index is None:
                self.selected_index = 0

            controls: list[ft.Control] = []
            for category, indices in self._grouped_topic_indices():
                controls.append(self._category_header(category))
                for i in indices:
                    card = self._topic_card(self.culture_data[i], i)
                    self.card_containers[i] = card
                    controls.append(card)
            
            left_content = ft.ListView(
                controls=controls,
                expand=True,
                spacing=0,
                padding=ft.padding.only(left=24, right=16, bottom=24, top=8)
            )

        if self.culture_data and self.selected_index is not None:
            self._set_right_content(self._build_right_content(self.culture_data[self.selected_index]), update=False)
        else:
            self._set_right_content(self._build_right_placeholder(), update=False)

        masthead = build_masthead(
            title="Cultura Giapponese",
            subtitle="日本文化 – Nihon bunka",
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
                ft.Row(
                    [
                        ft.Container(
                            content=left_content,
                            expand=4,
                            border=ft.border.only(right=ft.BorderSide(1, T.BORDER))
                        ),
                        self.right_panel,
                    ],
                    expand=True,
                    spacing=0,
                )
            ], spacing=0, expand=True)
        )
