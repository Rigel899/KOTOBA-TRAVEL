"""
Utility condivise dai quiz del Dojo.
"""
from __future__ import annotations

import asyncio
import random
from collections.abc import Callable

import src.core.compat  # Mantiene disponibili border/padding compat anche nei test isolati.
import flet as ft

from src.core.settings import KotobaTheme as T


def schedule_auto_next(
    page,
    delay: float,
    is_mounted: Callable[[], bool],
    should_advance: Callable[[], bool],
    advance: Callable[[], None],
) -> None:
    async def runner():
        await asyncio.sleep(delay)
        if is_mounted() and should_advance():
            advance()

    page.run_task(runner)


def max_correct_streak(
    questions,
    user_answers: dict[int, str],
    correct_value: Callable[[object], str],
) -> int:
    best = 0
    current = 0
    for index, question in enumerate(questions):
        if user_answers.get(index) == correct_value(question):
            current += 1
            best = max(best, current)
        else:
            current = 0
    return best


def make_choice_options(
    correct: str,
    all_values: list[str],
    *,
    option_count: int = 4,
    placeholder: str = "-",
    case_sensitive: bool = True,
) -> list[str]:
    distractor_count = max(0, option_count - 1)
    wrong_pool: list[str] = []
    seen: set[str] = set()

    def key_for(value: str) -> str:
        return value if case_sensitive else value.lower()

    correct_key = key_for(correct)
    for value in all_values:
        if not value:
            continue
        key = key_for(value)
        if key == correct_key or key in seen:
            continue
        seen.add(key)
        wrong_pool.append(value)

    wrong = random.sample(wrong_pool, min(distractor_count, len(wrong_pool)))
    while len(wrong) < distractor_count:
        wrong.append(placeholder)

    options = [correct] + wrong
    random.shuffle(options)
    return options


def count_correct_answers(
    questions,
    user_answers: dict[int, str],
    correct_value: Callable[[object], str],
) -> int:
    return sum(
        1
        for index, question in enumerate(questions)
        if user_answers.get(index) == correct_value(question)
    )


def percent_score(correct_count: int, total_questions: int) -> int:
    return int(correct_count / total_questions * 100) if total_questions else 0


def color_with_alpha(color: str, alpha: str) -> str:
    if isinstance(color, str) and color.startswith("#") and len(color) == 7:
        return f"#{alpha}{color[1:]}"
    return color


def build_quiz_result_view(
    *,
    title: str,
    module_label: str,
    mark: str,
    accent: str,
    correct_count: int,
    total_questions: int,
    grade: str,
    grade_color: str,
    primary_label: str,
    on_primary: Callable[[], None],
    secondary_label: str,
    on_secondary: Callable[[], None],
) -> ft.Control:
    pct = percent_score(correct_count, total_questions)
    return ft.Column(
        [
            ft.Container(expand=True),
            ft.Container(
                width=112,
                height=112,
                alignment=ft.Alignment.CENTER,
                bgcolor=color_with_alpha(accent, "22"),
                border=ft.border.all(2.5, accent),
                border_radius=18,
                content=ft.Text(
                    mark,
                    size=54 if len(mark) == 1 else 36,
                    font_family=T.FONT_JP,
                    color=accent,
                    weight=ft.FontWeight.W_800,
                    text_align=ft.TextAlign.CENTER,
                ),
            ),
            ft.Container(height=12),
            ft.Text(
                module_label,
                size=12,
                color=accent,
                font_family=T.FONT_BODY,
                weight=ft.FontWeight.W_700,
                text_align=ft.TextAlign.CENTER,
            ),
            ft.Text(
                title,
                size=25,
                font_family=T.FONT_DISPLAY,
                weight=ft.FontWeight.W_800,
                color=T.TEXT,
                text_align=ft.TextAlign.CENTER,
            ),
            ft.Container(
                width=360,
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Text(f"{correct_count}/{total_questions}", size=28, color=T.TEXT, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_800),
                                ft.Container(expand=True),
                                ft.Text(f"{pct}%", size=18, color=grade_color, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_800),
                            ],
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.ProgressBar(value=pct / 100, bar_height=7, color=grade_color, bgcolor=T.BORDER, border_radius=8),
                    ],
                    spacing=6,
                ),
            ),
            ft.Text(grade, size=18, font_family=T.FONT_DISPLAY, weight=ft.FontWeight.W_800, color=grade_color),
            ft.Container(height=24),
            ft.Row(
                [
                    ft.ElevatedButton(
                        primary_label,
                        style=ft.ButtonStyle(bgcolor=T.BG_CARD, color=T.TEXT, mouse_cursor=ft.MouseCursor.CLICK),
                        on_click=lambda e: on_primary(),
                    ),
                    ft.ElevatedButton(
                        secondary_label,
                        style=ft.ButtonStyle(bgcolor=accent, color=T.BG_INK, mouse_cursor=ft.MouseCursor.CLICK),
                        on_click=lambda e: on_secondary(),
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=16,
                wrap=True,
            ),
            ft.Container(expand=True),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=8,
        expand=True,
    )


def answer_and_schedule_next(
    page,
    *,
    get_current_idx: Callable[[], int],
    user_answers: dict[int, str],
    chosen: str,
    render: Callable[[], None],
    is_mounted: Callable[[], bool],
    advance: Callable[[], None],
    delay: float,
) -> None:
    idx_at_schedule = get_current_idx()
    user_answers[idx_at_schedule] = chosen
    render()

    schedule_auto_next(
        page,
        delay,
        is_mounted,
        lambda: get_current_idx() == idx_at_schedule and user_answers.get(idx_at_schedule) == chosen,
        advance,
    )


def _answer_button(
    option: str,
    correct: str,
    chosen: str | None,
    already_answered: bool,
    accent: str,
    on_select: Callable[[str], None],
    *,
    text_size: int = 15,
    font_family: str | None = None,
    height: int = 72,
) -> ft.Container:
    is_chosen = option == chosen
    is_correct = option == correct
    bg, border_color = T.BG_CARD, T.BORDER

    if already_answered:
        if is_correct:
            bg, border_color = T.QUIZ_CORRECT_BG, T.QUIZ_CORRECT_BORDER
        elif is_chosen and not is_correct:
            bg, border_color = T.QUIZ_WRONG_BG, T.RED

    button = ft.Container(
        content=ft.Text(
            option,
            size=text_size,
            font_family=font_family or T.FONT_BODY,
            weight=ft.FontWeight.W_600,
            color=T.TEXT,
            text_align=ft.TextAlign.CENTER,
            max_lines=3,
            overflow=ft.TextOverflow.ELLIPSIS,
        ),
        bgcolor=bg,
        border_radius=T.RADIUS,
        border=ft.border.all(1.5, border_color),
        alignment=ft.Alignment.CENTER,
        padding=ft.padding.symmetric(horizontal=14, vertical=8),
        height=height,
        expand=True,
        ink=False,
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        opacity=1.0 if (not already_answered or is_correct or is_chosen) else 0.32,
        animate=ft.Animation(150, ft.AnimationCurve.EASE_OUT),
    )

    def on_hover(e):
        if already_answered:
            return
        is_hover = e.data == "true"
        button.border = ft.border.all(1.5, accent if is_hover else T.BORDER)
        button.bgcolor = T.BG_HOVER if is_hover else T.BG_CARD
        button.update()

    if not already_answered:
        button.on_hover = on_hover
        button.on_click = lambda e, value=option: on_select(value)

    return button


def build_quiz_answer_grid(
    options: list[str],
    correct: str,
    chosen: str | None,
    already_answered: bool,
    accent: str,
    on_select: Callable[[str], None],
    *,
    text_size: int = 15,
    font_family: str | None = None,
) -> ft.Control:
    padded = list(options[:4])
    while len(padded) < 4:
        padded.append("-")

    return ft.Column(
        [
            ft.Row(
                [
                    _answer_button(padded[0], correct, chosen, already_answered, accent, on_select, text_size=text_size, font_family=font_family),
                    _answer_button(padded[1], correct, chosen, already_answered, accent, on_select, text_size=text_size, font_family=font_family),
                ],
                spacing=12,
            ),
            ft.Row(
                [
                    _answer_button(padded[2], correct, chosen, already_answered, accent, on_select, text_size=text_size, font_family=font_family),
                    _answer_button(padded[3], correct, chosen, already_answered, accent, on_select, text_size=text_size, font_family=font_family),
                ],
                spacing=12,
            ),
        ],
        spacing=12,
    )


def build_quiz_nav(
    current_idx: int,
    already_answered: bool,
    accent: str,
    on_prev: Callable[[], None],
    on_next: Callable[[], None],
) -> ft.Control:
    return ft.Row(
        [
            ft.TextButton(
                "Indietro",
                icon=ft.Icons.ARROW_BACK_ROUNDED,
                on_click=lambda e: on_prev(),
                disabled=current_idx == 0,
                style=ft.ButtonStyle(color=T.TEXT_M, mouse_cursor=ft.MouseCursor.CLICK),
            ),
            ft.Container(expand=True),
            ft.TextButton(
                "Avanti",
                icon=ft.Icons.ARROW_FORWARD_ROUNDED,
                on_click=lambda e: on_next(),
                disabled=not already_answered,
                style=ft.ButtonStyle(color=accent, mouse_cursor=ft.MouseCursor.CLICK),
            ),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )


def build_quiz_question_view(
    *,
    current_idx: int,
    total: int,
    prompt: str,
    options: list[str],
    correct: str,
    chosen: str | None,
    already_answered: bool,
    accent: str,
    on_select: Callable[[str], None],
    on_prev: Callable[[], None],
    on_next: Callable[[], None],
    detail: str = "",
    badge: str = "",
    prompt_size: int = 56,
    prompt_font: str | None = None,
    prompt_color: str | None = None,
    detail_color: str | None = None,
    answer_text_size: int = 15,
    answer_font: str | None = None,
) -> ft.Control:
    header_controls: list[ft.Control] = [
        ft.Text(f"Q: {current_idx + 1} / {total}", size=14, color=T.TEXT_M, font_family=T.FONT_BODY),
        ft.Container(expand=True),
    ]
    if badge:
        header_controls.append(
            ft.Container(
                content=ft.Text(badge.upper(), size=11, color=T.BG_MAIN, weight=ft.FontWeight.W_700, font_family=T.FONT_BODY),
                bgcolor=accent,
                border_radius=4,
                padding=ft.padding.symmetric(horizontal=10, vertical=4),
            )
        )

    prompt_controls: list[ft.Control] = [
        ft.Text(
            prompt,
            size=prompt_size,
            font_family=prompt_font or T.FONT_JP,
            color=prompt_color or accent,
            text_align=ft.TextAlign.CENTER,
            weight=ft.FontWeight.W_700,
            max_lines=3,
            overflow=ft.TextOverflow.ELLIPSIS,
        )
    ]
    if detail:
        prompt_controls.append(
            ft.Text(
                detail,
                size=14,
                font_family=T.FONT_BODY,
                color=detail_color or T.TEXT_M,
                text_align=ft.TextAlign.CENTER,
                max_lines=2,
                overflow=ft.TextOverflow.ELLIPSIS,
            )
        )

    return ft.Column(
        [
            ft.Row(header_controls, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Container(height=10),
            ft.Container(
                content=ft.Column(
                    prompt_controls,
                    spacing=12,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                bgcolor=T.BG_CARD,
                border=ft.border.all(1.5, accent),
                border_radius=T.RADIUS,
                padding=ft.padding.symmetric(horizontal=28, vertical=24),
                height=250,
                alignment=ft.Alignment.CENTER,
            ),
            ft.Container(height=18),
            build_quiz_answer_grid(
                options,
                correct,
                chosen,
                already_answered,
                accent,
                on_select,
                text_size=answer_text_size,
                font_family=answer_font,
            ),
            ft.Container(height=16),
            build_quiz_nav(current_idx, already_answered, accent, on_prev, on_next),
        ],
        spacing=0,
        expand=True,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
    )


def build_quiz_data_error(filename: str, title: str = "Dati quiz non disponibili") -> ft.Control:
    return ft.Container(
        expand=True,
        alignment=ft.Alignment.CENTER,
        content=ft.Column(
            [
                ft.Container(
                    width=78,
                    height=78,
                    alignment=ft.Alignment.CENTER,
                    border=ft.border.all(2, T.RED),
                    border_radius=10,
                    content=ft.Text("!", size=42, color=T.RED, weight=ft.FontWeight.W_900),
                ),
                ft.Text(
                    title,
                    size=22,
                    font_family=T.FONT_DISPLAY,
                    weight=ft.FontWeight.W_700,
                    color=T.TEXT,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    f"Controlla che asset/data/{filename} sia presente e contenga elementi validi.",
                    size=13,
                    font_family=T.FONT_BODY,
                    color=T.TEXT_M,
                    text_align=ft.TextAlign.CENTER,
                ),
            ],
            spacing=14,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
    )
