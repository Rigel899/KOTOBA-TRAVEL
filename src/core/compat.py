"""
core/compat.py  –  Helper e shim per Flet 0.85.x
Importato UNA VOLTA in main.py prima di tutto il resto.

Ripristina i helper di layout rimossi/mancanti nella 0.80+:
  ft.border.all / ft.border.only
  ft.padding.symmetric / ft.padding.all / ft.padding.only
  ft.margin.symmetric  / ft.margin.all  / ft.margin.only

Espone anche:
  icon_btn()    – ft.IconButton con mouse_cursor=CLICK preimpostato
  show_snack()  – mostra SnackBar senza inquinare il dialog stack
  open_dialog() – apre AlertDialog via page.show_dialog()
  close_dialog()– chiude il dialog corrente via page.pop_dialog()
"""
import flet as ft


# ── border ────────────────────────────────────────────────────────────────────

def _border_all(width: float = 1, color=None):
    s = ft.BorderSide(width=width, color=color)
    return ft.Border(top=s, right=s, bottom=s, left=s)

def _border_only(top=None, right=None, bottom=None, left=None):
    return ft.Border(top=top, right=right, bottom=bottom, left=left)

class _BorderNamespace:
    pass

if not hasattr(ft, "border"):
    ft.border = _BorderNamespace()

if not hasattr(ft.border, "all"):
    ft.border.all = _border_all
    ft.border.only = _border_only


# ── padding ───────────────────────────────────────────────────────────────────

class _PaddingHelper:
    @staticmethod
    def all(v):
        return ft.Padding(left=v, top=v, right=v, bottom=v)

    @staticmethod
    def symmetric(vertical=0, horizontal=0):
        return ft.Padding(top=vertical, bottom=vertical,
                          left=horizontal, right=horizontal)

    @staticmethod
    def only(left=0, top=0, right=0, bottom=0):
        return ft.Padding(left=left, top=top, right=right, bottom=bottom)

if not hasattr(ft, "padding") or not hasattr(ft.padding, "all"):
    ft.padding = _PaddingHelper()


# ── margin ────────────────────────────────────────────────────────────────────

class _MarginHelper:
    @staticmethod
    def all(v):
        return ft.Margin(left=v, top=v, right=v, bottom=v)

    @staticmethod
    def symmetric(vertical=0, horizontal=0):
        return ft.Margin(top=vertical, bottom=vertical,
                         left=horizontal, right=horizontal)

    @staticmethod
    def only(left=0, top=0, right=0, bottom=0):
        return ft.Margin(left=left, top=top, right=right, bottom=bottom)

if not hasattr(ft, "margin") or not hasattr(ft.margin, "all"):
    ft.margin = _MarginHelper()


# ── colors / icons alias ──────────────────────────────────────────────────────

if not hasattr(ft, "colors"):
    ft.colors = ft.Colors

if not hasattr(ft, "icons"):
    ft.icons = ft.Icons


# ── widget helpers ────────────────────────────────────────────────────────────

def icon_btn(
    icon,
    *,
    icon_color=None,
    icon_size: int = 24,
    tooltip: str | None = None,
    on_click=None,
    disabled: bool = False,
) -> ft.Control:
    return ft.IconButton(
        icon=icon,
        icon_color=icon_color,
        icon_size=icon_size,
        tooltip=tooltip,
        on_click=on_click,
        disabled=disabled,
        mouse_cursor=ft.MouseCursor.CLICK,
    )


# ── snackbar / dialog helpers ─────────────────────────────────────────────────
# page.show_dialog(dialog) → spinge sull'internal dialog stack
# page.pop_dialog()        → estrae dal dialog stack
# page.open(snack)         → mostra SnackBar senza toccare il dialog stack

def show_snack(page: ft.Page, snack: ft.SnackBar) -> None:
    """Mostra uno SnackBar senza inquinare il dialog stack."""
    page.open(snack)


def open_dialog(page: ft.Page, dialog) -> None:
    page.show_dialog(dialog)


def close_dialog(page: ft.Page, dialog) -> None:
    """Il param dialog è ignorato — pop_dialog chiude sempre il top dello stack."""
    page.pop_dialog()
