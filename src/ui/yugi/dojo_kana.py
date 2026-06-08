"""
ui/yugi/dojo_kana.py – Addestramento Kana (Dojo) con flusso a due step.
Layout 4 colonne, Nomenclatura Elegante e Dinamicità 3 Colori Totale (Titoli inclusi).
"""
from __future__ import annotations
import flet as ft
import random
from src.core.settings import KotobaTheme as T
from src.core.db_manager import DBManager
from src.ui.components.loader import show_achievements
from src.ui.components.stage import centered_stage
from src.ui.yugi.quiz_utils import build_quiz_data_error, build_quiz_question_view, max_correct_streak, schedule_auto_next

TOTAL_QUESTIONS = 10

GROUP_INFO: dict[str, str] = {
    "vocali":    "Vocali — 母音",
    "k":         "Serie Ka — か行",
    "s":         "Serie Sa — さ行",
    "t":         "Serie Ta — た行",
    "n":         "Serie Na — な行",
    "h":         "Serie Ha — は行",
    "m":         "Serie Ma — ま行",
    "y":         "Serie Ya — や行",
    "r":         "Serie Ra — ら行",
    "w":         "Serie Wa — わ行",
    "n_singola": "Nasale — ん",
    "g":         "Serie Ga — が行 dakuten",
    "z":         "Serie Za — ざ行 dakuten",
    "d":         "Serie Da — だ行 dakuten",
    "b":         "Serie Ba — ば行 dakuten",
    "p":         "Serie Pa — ぱ行 handakuten",
}

GROUP_ORDER = ["vocali", "k", "s", "t", "n", "h", "m", "y", "r", "w",
               "n_singola", "g", "z", "d", "b", "p"]


class DojoKana:
    def __init__(self, page: ft.Page, navigate, state: dict):
        self.page = page
        self.navigate = navigate
        self.state = state

        self.mode = "hiragana"
        self.selected_group = "Tutte"

        raw_data = DBManager.load_json("sillabari.json") or []
        self.hiragana_pool = [(i["word"], i["pronunciation"], i.get("group", "Standard"))
                              for i in raw_data if i.get("category") == "Hiragana"]
        self.katakana_pool = [(i["word"], i["pronunciation"], i.get("group", "Standard"))
                              for i in raw_data if i.get("category") == "Katakana"]

        present = {item[2] for item in self.hiragana_pool + self.katakana_pool}
        self.available_groups = ["Tutte"] + [g for g in GROUP_ORDER if g in present]

        self.questions: list = []
        self.user_answers: dict = {}
        self.current_idx = 0
        self.content_area = ft.Container(expand=True)

    def _safe_update(self):
        try:
            self.content_area.update()
        except RuntimeError:
            pass

    def _is_mounted(self) -> bool:
        try:
            return self.content_area.page is not None
        except RuntimeError:
            return False

    @property
    def active_color(self) -> str:
        return T.BELT_KANA

    def _preview_for_group(self, group_key: str, max_chars: int = 5) -> str:
        if self.mode == "katakana":
            pool = self.katakana_pool
        elif self.mode == "mixed":
            hira = [w for w, _, g in self.hiragana_pool if g == group_key]
            kata = [w for w, _, g in self.katakana_pool if g == group_key]
            pairs = [f"{h}/{k}" for h, k in zip(hira[:max_chars], kata[:max_chars])]
            return " ".join(pairs)
        else:
            pool = self.hiragana_pool
        kana_list = [w for w, _, g in pool if g == group_key]
        return "  ".join(kana_list[:max_chars])

    def _count_for_mode(self) -> int:
        if self.mode == "hiragana": return len(self.hiragana_pool)
        if self.mode == "katakana": return len(self.katakana_pool)
        return len(self.hiragana_pool) + len(self.katakana_pool)

    def _setup_screen_mode(self) -> ft.Control:
        def make_mode_btn(label, mode_key, color, desc):
            def on_hover(e):
                is_hover = e.data == "true"
                e.control.border = ft.border.all(1.5, color if is_hover else T.BORDER)
                e.control.bgcolor = f"{color}11" if is_hover else T.BG_CARD
                e.control.update()

            return ft.Container(
                content=ft.Column([
                    ft.Text(label, size=22, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_700, color=color),
                    ft.Text(desc, size=12, font_family=T.FONT_BODY, color=T.TEXT_M),
                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=T.BG_CARD, border_radius=12, border=ft.border.all(1, T.BORDER),
                padding=ft.padding.symmetric(vertical=24, horizontal=16),
                alignment=ft.Alignment.CENTER, expand=True, animate=ft.Animation(150, ft.AnimationCurve.EASE_OUT), ink=False,
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                on_hover=on_hover,
                on_click=lambda e: self._go_to_group_selection(mode_key),
            )

        return ft.Column([
            ft.Container(height=20),
            ft.Text("仮", size=60, font_family=T.FONT_DISPLAY, color=T.BELT_KANA, text_align=ft.TextAlign.CENTER),
            ft.Text("Addestramento Kana", size=24, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_700, color=T.TEXT, text_align=ft.TextAlign.CENTER),
            ft.Container(height=30),
            ft.Row([
                make_mode_btn("Hiragana", "hiragana", T.BELT_KANA, "Forme curve"),
                make_mode_btn("Katakana", "katakana", T.BELT_KANA, "Tratti rigidi"),
                make_mode_btn("Misto",    "mixed",    T.BELT_KANA, "Sfida totale"),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=16),
            ft.Container(height=20),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True)

    def _go_to_group_selection(self, mode_key: str):
        self.mode = mode_key
        self.content_area.content = centered_stage(self.page, self._setup_screen_group(), max_width=1040)
        self._safe_update()

    def _go_back_to_mode(self):
        self.content_area.content = centered_stage(self.page, self._setup_screen_mode(), max_width=820, min_width=640, alignment=ft.Alignment.CENTER)
        self._safe_update()

    def _setup_screen_group(self) -> ft.Control:
        color = self.active_color

        def make_special_all_card() -> ft.Container:
            def on_hover(e):
                is_hover = e.data == "true"
                e.control.border = ft.border.all(1.5, color)
                e.control.bgcolor = f"{color}11" if is_hover else T.BG_SURF
                e.control.update()

            return ft.Container(
                content=ft.Row([
                    ft.Container(
                        width=40, height=40, alignment=ft.Alignment.CENTER,
                        border=ft.border.all(1.5, color), border_radius=6,
                        content=ft.Text("全", size=20, font_family=T.FONT_DISPLAY, color=color, weight=ft.FontWeight.W_700),
                    ),
                    ft.Column([
                        # TITOLO CON COLORE DINAMICO!
                        ft.Text("Tutto il sillabario", size=15, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_700, color=color),
                        ft.Text(f"全部 — {self._count_for_mode()} caratteri", size=11, font_family=T.FONT_DISPLAY, italic=True, color=color),
                    ], spacing=1, expand=True),
                    ft.Icon(ft.Icons.ARROW_FORWARD_IOS_ROUNDED, color=color, size=14),
                ], spacing=16, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=T.BG_SURF, border_radius=T.RADIUS, border=ft.border.all(1, color),
                padding=ft.padding.symmetric(vertical=12, horizontal=20),
                animate=ft.Animation(150, ft.AnimationCurve.EASE_OUT), ink=False, on_hover=on_hover,
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                on_click=lambda e: self._start_quiz_with_group("Tutte"),
            )

        def make_group_card(g_key: str) -> ft.Container:
            display_title = GROUP_INFO.get(g_key, g_key.capitalize())
            preview = self._preview_for_group(g_key)

            def on_hover(e):
                is_hover = e.data == "true"
                e.control.border = ft.border.all(1.5, color if is_hover else T.BORDER)
                e.control.bgcolor = f"{color}0A" if is_hover else T.BG_CARD
                e.control.update()

            return ft.Container(
                content=ft.Column([
                    # TITOLO CON COLORE DINAMICO!
                    ft.Text(display_title, size=14, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_700, color=color),
                    ft.Container(expand=True),
                    ft.Row([
                        ft.Text(preview, size=15, font_family=T.FONT_JP, color=T.TEXT_M, weight=ft.FontWeight.W_500),
                        ft.Container(expand=True),
                        ft.Icon(ft.Icons.ARROW_FORWARD_IOS_ROUNDED, color=color, size=12, opacity=0.4),
                    ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ], spacing=0, alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                bgcolor=T.BG_CARD, border_radius=T.RADIUS, border=ft.border.all(1, T.BORDER),
                padding=ft.padding.all(16),
                animate=ft.Animation(150, ft.AnimationCurve.EASE_OUT), ink=False, on_hover=on_hover,
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                on_click=lambda e, g=g_key: self._start_quiz_with_group(g),
            )

        group_cards = [make_group_card(g) for g in self.available_groups if g != "Tutte"]

        return ft.Column([
            ft.Row([
                ft.IconButton(icon=ft.Icons.ARROW_BACK_IOS_NEW_ROUNDED, icon_color=T.TEXT_M, icon_size=14, on_click=lambda e: self._go_back_to_mode()),
                ft.Text(f"Seleziona il gruppo", size=18, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_700, color=color),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Container(height=6),
            make_special_all_card(),
            ft.Container(height=8),
            ft.GridView(
                controls=group_cards,
                max_extent=270,
                child_aspect_ratio=2.15, 
                spacing=10,
                run_spacing=10,
                expand=True,
            ),
        ], expand=True)

    def _start_quiz_with_group(self, group_name: str):
        self.selected_group = group_name
        self._start_quiz()

    def _build_dataset(self) -> list[tuple]:
        pool = []
        if self.mode in ("hiragana", "mixed"): pool += self.hiragana_pool
        if self.mode in ("katakana", "mixed"): pool += self.katakana_pool

        if self.selected_group != "Tutte":
            pool = [it for it in pool if it[2] == self.selected_group]
        if not pool:
            return []

        shuffled = list(pool)
        random.shuffle(shuffled)
        return shuffled[:TOTAL_QUESTIONS]

    def _start_quiz(self):
        raw_qs = self._build_dataset()
        if not raw_qs: return

        self.questions = []
        all_pool = self.hiragana_pool + self.katakana_pool
        for kana, correct_romaji, _ in raw_qs:
            wrong_pool = list({r for _, r, _ in all_pool if r != correct_romaji})
            wrong = random.sample(wrong_pool, min(3, len(wrong_pool)))
            while len(wrong) < 3: wrong.append("—")
            opts = [correct_romaji] + wrong
            random.shuffle(opts)
            self.questions.append((kana, correct_romaji, opts))

        self.current_idx = 0
        self.user_answers = {}
        self._show_question()

    def _show_question(self):
        if self.current_idx >= len(self.questions):
            self._show_results()
            return

        kana, correct_romaji, options = self.questions[self.current_idx]
        already_answered = self.current_idx in self.user_answers
        chosen_opt = self.user_answers.get(self.current_idx)

        screen = build_quiz_question_view(
            current_idx=self.current_idx,
            total=len(self.questions),
            prompt=kana,
            detail="Scegli la lettura in romaji",
            badge=self.mode,
            options=options,
            correct=correct_romaji,
            chosen=chosen_opt,
            already_answered=already_answered,
            accent=self.active_color,
            on_select=self._check_answer,
            on_prev=self._prev_q,
            on_next=self._next_q,
            prompt_size=96,
            prompt_font=T.FONT_JP,
            prompt_color=self.active_color,
            answer_text_size=18,
            answer_font=T.FONT_DISPLAY,
        )

        self.content_area.content = centered_stage(self.page, screen, max_width=920, min_width=640)
        self._safe_update()

    def _check_answer(self, chosen: str):
        idx_at_schedule = self.current_idx
        self.user_answers[idx_at_schedule] = chosen
        self._show_question()

        schedule_auto_next(
            self.page,
            0.6,
            self._is_mounted,
            lambda: self.current_idx == idx_at_schedule and self.user_answers.get(idx_at_schedule) == chosen,
            self._next_q,
        )

    def _next_q(self):
        if self.current_idx < len(self.questions):
            self.current_idx += 1
            self._show_question()

    def _prev_q(self):
        if self.current_idx > 0:
            self.current_idx -= 1
            self._show_question()

    def _show_results(self):
        correct_count = sum(1 for i, (_, correct, _) in enumerate(self.questions) if self.user_answers.get(i) == correct)
        pct = int(correct_count / len(self.questions) * 100) if self.questions else 0
        unlocked = []
        if self.questions:
            unlocked = DBManager.record_quiz_result(
                DBManager.current_username,
                self.mode,
                correct_count,
                total_questions=len(self.questions),
                max_streak=max_correct_streak(self.questions, self.user_answers, lambda question: question[1]),
            )

        if pct == 100:
            grade, color, icon = "Perfezione", self.active_color, "極"
        elif pct >= 80:
            grade, color, icon = "Ottimo lavoro", T.TEXT, "良"
        else:
            grade, color, icon = "Devi allenarti", T.RED, "学"

        screen = ft.Column([
            ft.Container(expand=True),
            ft.Container(
                width=80, height=80, alignment=ft.Alignment.CENTER,
                border=ft.border.all(3, color), border_radius=12,
                content=ft.Text(icon, size=40, font_family=T.FONT_DISPLAY, color=color, weight=ft.FontWeight.W_700),
            ),
            ft.Container(height=16),
            ft.Text("Addestramento terminato", size=24, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_700, color=T.TEXT),
            ft.Text(f"Punteggio: {correct_count} / {len(self.questions)}", size=16, color=T.TEXT_M),
            ft.Text(grade, size=18, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_700, color=color),
            ft.Container(height=30),
            ft.Row([
                ft.ElevatedButton("Riprova gruppo", style=ft.ButtonStyle(bgcolor=T.BG_CARD, color=T.TEXT), on_click=lambda e: self._start_quiz()),
                ft.ElevatedButton("Torna alle scelte", style=ft.ButtonStyle(bgcolor=self.active_color, color=T.BG_MAIN), on_click=lambda e: self._go_back_to_mode()),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=16),
            ft.Container(expand=True),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8, expand=True)

        self.content_area.content = centered_stage(self.page, screen, max_width=820, min_width=640)
        self._safe_update()
        show_achievements(self.page, unlocked)

    def build(self) -> ft.Control:
        if not (self.hiragana_pool or self.katakana_pool):
            self.content_area.content = build_quiz_data_error("sillabari.json")
        else:
            self.content_area.content = centered_stage(self.page, self._setup_screen_mode(), max_width=820, min_width=640, alignment=ft.Alignment.CENTER)

        masthead = ft.Container(
            content=ft.Row([
                ft.IconButton(icon=ft.Icons.ARROW_BACK_IOS_NEW_ROUNDED, icon_color=T.TEXT_M, icon_size=16, on_click=lambda e: self.navigate("dojo_hub")),
                ft.Column([
                    ft.Text("Allenamento Kana", size=T.FS_TITLE, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_700, color=T.TEXT),
                    ft.Text("仮名 – Kana", size=T.FS_SMALL, font_family=T.FONT_DISPLAY, italic=True, color=T.BELT_KANA),
                ], spacing=2),
            ], spacing=16, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.only(left=24, top=20, right=24, bottom=16),
            border=ft.border.only(bottom=ft.BorderSide(1, T.BORDER)),
        )

        return ft.Container(
            bgcolor=T.BG_MAIN, expand=True,
            content=ft.Column([
                masthead,
                ft.Container(content=self.content_area, expand=True, padding=ft.padding.all(28)),
            ], spacing=0, expand=True),
        )
