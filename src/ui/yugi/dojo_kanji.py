"""
ui/yugi/dojo_kanji.py – Addestramento Kanji (Dojo) 
Griglia a 4 colonne, protezione IndexError, card dorata e navigazione.
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

class DojoKanji:
    def __init__(self, page: ft.Page, navigate, state: dict):
        self.page = page
        self.navigate = navigate
        self.state = state
        self.selected_group = "Tutti"
        
        raw_data = DBManager.load_json("kanji.json") or []
        self.kanji_pool = [(i["word"], i["meaning"], i.get("group", "Essenziali")) for i in raw_data if "word" in i and "meaning" in i]
        
        groups_set = {k[2] for k in self.kanji_pool}
        self.available_groups = ["Tutti"] + sorted(list(groups_set))
        
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

    def _setup_screen_group(self) -> ft.Control:
        def make_special_all_card() -> ft.Container:
            def on_hover(e):
                is_hover = e.data == "true"
                e.control.border = ft.border.all(1.5, T.BELT_KANJI)
                e.control.bgcolor = f"{T.BELT_KANJI}11" if is_hover else T.BG_SURF
                e.control.update()

            return ft.Container(
                content=ft.Row([
                    ft.Container(
                        width=40, height=40, alignment=ft.Alignment.CENTER,
                        border=ft.border.all(1.5, T.BELT_KANJI), border_radius=6,
                        content=ft.Text("全", size=20, font_family=T.FONT_DISPLAY, color=T.BELT_KANJI, weight=ft.FontWeight.W_700),
                    ),
                    ft.Column([
                        ft.Text("Tutti i Kanji", size=15, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_700, color=T.TEXT),
                        ft.Text(f"全部 — {len(self.kanji_pool)} caratteri", size=11, font_family=T.FONT_DISPLAY, italic=True, color=T.BELT_KANJI),
                    ], spacing=1, expand=True),
                    ft.Icon(ft.Icons.ARROW_FORWARD_IOS_ROUNDED, color=T.BELT_KANJI, size=14),
                ], spacing=16, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=T.BG_SURF, border_radius=T.RADIUS, border=ft.border.all(1, T.BELT_KANJI),
                padding=ft.padding.symmetric(vertical=12, horizontal=20),
                animate=ft.Animation(150, ft.AnimationCurve.EASE_OUT), ink=False, on_hover=on_hover,
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                on_click=lambda e: self._start_quiz_with_group("Tutti"),
            )

        def make_group_card(g_name):
            def on_hover(e):
                is_hover = e.data == "true"
                e.control.border = ft.border.all(1.5, T.BELT_KANJI if is_hover else T.BORDER)
                e.control.bgcolor = f"{T.BELT_KANJI}0A" if is_hover else T.BG_CARD
                e.control.update()

            count = len([k for k in self.kanji_pool if k[2] == g_name])
            return ft.Container(
                content=ft.Column([
                    ft.Text(g_name, size=14, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_700, color=T.TEXT),
                    ft.Container(expand=True),
                    ft.Row([
                        ft.Text(f"{count} caratteri", size=13, color=T.TEXT_M),
                        ft.Container(expand=True),
                        ft.Icon(ft.Icons.ARROW_FORWARD_IOS_ROUNDED, color=T.BELT_KANJI, size=12, opacity=0.4),
                    ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                bgcolor=T.BG_CARD, border_radius=T.RADIUS, border=ft.border.all(1, T.BORDER),
                padding=ft.padding.all(16), animate=ft.Animation(150, ft.AnimationCurve.EASE_OUT), ink=False, on_hover=on_hover,
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                on_click=lambda e: self._start_quiz_with_group(g_name),
            )

        cards = [make_group_card(g) for g in self.available_groups if g != "Tutti"]

        return ft.Column([
            ft.Text("Seleziona la pergamena dei Kanji", size=18, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_700, color=T.BELT_KANJI),
            ft.Container(height=6),
            make_special_all_card(),
            ft.Container(height=8),
            ft.GridView(controls=cards, max_extent=270, child_aspect_ratio=2.15, spacing=10, run_spacing=10, expand=True)
        ], expand=True)

    def _start_quiz_with_group(self, group_name):
        self.selected_group = group_name
        pool = self.kanji_pool if group_name == "Tutti" else [k for k in self.kanji_pool if k[2] == group_name]
        
        if not pool: return

        all_meanings = list({k[1] for k in self.kanji_pool})

        shuffled = list(pool)
        random.shuffle(shuffled)
        target_qs = shuffled[:TOTAL_QUESTIONS]

        self.questions = []
        for kanji, correct, _ in target_qs:
            wrong_pool = [m for m in all_meanings if m.lower() != correct.lower()]
            wrong = random.sample(wrong_pool, min(3, len(wrong_pool)))
            # Sicurezza assoluta contro l'IndexError: se ci sono pochissimi kanji
            while len(wrong) < 3: wrong.append("—")
            opts = [correct] + wrong
            random.shuffle(opts)
            self.questions.append((kanji, correct, opts))

        self.current_idx = 0
        self.user_answers = {}
        self._show_question()

    def _show_question(self):
        if self.current_idx >= len(self.questions):
            self._show_results()
            return

        kanji, correct, options = self.questions[self.current_idx]
        already_answered = self.current_idx in self.user_answers
        chosen_opt = self.user_answers.get(self.current_idx)

        screen = build_quiz_question_view(
            current_idx=self.current_idx,
            total=len(self.questions),
            prompt=kanji,
            detail="Scegli il significato corretto",
            badge="kanji",
            options=options,
            correct=correct,
            chosen=chosen_opt,
            already_answered=already_answered,
            accent=T.BELT_KANJI,
            on_select=self._check_answer,
            on_prev=self._prev_q,
            on_next=self._next_q,
            prompt_size=88,
            prompt_font=T.FONT_JP,
            prompt_color=T.BELT_KANJI,
            answer_text_size=17,
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
                "kanji",
                correct_count,
                total_questions=len(self.questions),
                max_streak=max_correct_streak(self.questions, self.user_answers, lambda question: question[1]),
            )
        grade, color, icon = ("Perfezione", T.BELT_KANJI, "極") if pct == 100 else ("Ottimo lavoro", T.TEXT, "良") if pct >= 80 else ("Devi allenarti", T.RED, "学")

        screen = ft.Column([
            ft.Container(expand=True),
            ft.Container(width=80, height=80, alignment=ft.Alignment.CENTER, border=ft.border.all(3, color), border_radius=12, content=ft.Text(icon, size=40, font_family=T.FONT_DISPLAY, color=color, weight=ft.FontWeight.W_700)),
            ft.Container(height=16),
            ft.Text("Addestramento terminato", size=24, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_700, color=T.TEXT),
            ft.Text(f"Punteggio: {correct_count} / {len(self.questions)}", size=16, color=T.TEXT_M),
            ft.Text(grade, size=18, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_700, color=color),
            ft.Container(height=30),
            ft.Row([
                ft.ElevatedButton("Riprova pergamena", style=ft.ButtonStyle(bgcolor=T.BG_CARD, color=T.TEXT), on_click=lambda e: self._start_quiz_with_group(self.selected_group)),
                ft.ElevatedButton("Torna alle scelte", style=ft.ButtonStyle(bgcolor=T.BELT_KANJI, color=T.BG_MAIN), on_click=lambda e: self._go_back_to_mode()),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=16),
            ft.Container(expand=True),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8, expand=True)

        self.content_area.content = centered_stage(self.page, screen, max_width=820, min_width=640)
        self._safe_update()
        show_achievements(self.page, unlocked)

    def _go_back_to_mode(self):
        self.content_area.content = centered_stage(self.page, self._setup_screen_group(), max_width=1040)
        self._safe_update()

    def build(self) -> ft.Control:
        if not self.kanji_pool:
            self.content_area.content = build_quiz_data_error("kanji.json")
        else:
            self.content_area.content = centered_stage(self.page, self._setup_screen_group(), max_width=1040)
        masthead = ft.Container(
            content=ft.Row([
                ft.IconButton(icon=ft.Icons.ARROW_BACK_IOS_NEW_ROUNDED, icon_color=T.TEXT_M, icon_size=16, on_click=lambda e: self.navigate("dojo_hub")),
                ft.Column([
                    ft.Text("Allenamento Kanji", size=T.FS_TITLE, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_700, color=T.TEXT),
                    ft.Text("漢字 – Kanji", size=T.FS_SMALL, font_family=T.FONT_DISPLAY, italic=True, color=T.BELT_KANJI),
                ], spacing=2),
            ], spacing=16, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.only(left=24, top=20, right=24, bottom=16),
            border=ft.border.only(bottom=ft.BorderSide(1, T.BORDER)),
        )
        return ft.Container(bgcolor=T.BG_MAIN, expand=True, content=ft.Column([masthead, ft.Container(content=self.content_area, expand=True, padding=ft.padding.all(28))], spacing=0, expand=True))
